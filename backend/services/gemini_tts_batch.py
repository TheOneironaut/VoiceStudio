"""Persistent immediate and provider-batch jobs for Gemini TTS."""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import uuid
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import DATA_DIR
from services.gemini_tts import (
    MODEL_ID,
    SAMPLE_RATE,
    build_prompt,
    create_client,
    decode_audio,
    generate_audio_bytes,
    normalize_voice,
)

JOBS_DIR = Path(DATA_DIR) / "gemini_tts_batch"
_LOCK = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def split_text(text: str, *, max_chars: int = 1800) -> list[str]:
    """Split without dropping or reordering a single source character."""
    if max_chars < 100:
        raise ValueError("max_chars must be at least 100.")
    if not text.strip():
        raise ValueError("Batch text cannot be empty.")
    tokens = re.findall(r"\s+|\S+", text)
    chunks: list[str] = []
    current = ""
    for token in tokens:
        while len(token) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(token[:max_chars])
            token = token[max_chars:]
        if current and len(current) + len(token) > max_chars:
            chunks.append(current)
            current = token
        else:
            current += token
    if current:
        chunks.append(current)
    return chunks


def _job_dir(job_id: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise KeyError(job_id)
    return JOBS_DIR / job_id


def _manifest_path(job_id: str) -> Path:
    return _job_dir(job_id) / "manifest.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        temp_path = Path(handle.name)
    os.replace(temp_path, path)


def load_job(job_id: str) -> dict[str, Any]:
    path = _manifest_path(job_id)
    if not path.exists():
        raise KeyError(job_id)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _save_job(job: dict[str, Any]) -> None:
    job["updated_at"] = _now()
    _write_json(_manifest_path(job["id"]), job)


def create_job(
    text: str,
    *,
    voice: str,
    instruct: str | None,
    mode: str,
    max_chars: int = 1800,
) -> dict[str, Any]:
    if mode not in {"immediate", "provider_batch"}:
        raise ValueError("mode must be immediate or provider_batch.")
    canonical_voice = normalize_voice(voice)
    chunks = split_text(text, max_chars=max_chars)
    job_id = uuid.uuid4().hex
    directory = _job_dir(job_id)
    (directory / "chunks").mkdir(parents=True, exist_ok=False)
    (directory / "source.txt").write_text(text, encoding="utf-8")
    created_at = _now()
    job = {
        "id": job_id,
        "model": MODEL_ID,
        "mode": mode,
        "voice": canonical_voice,
        "instruct": instruct or "",
        "status": "created",
        "provider_job": None,
        "created_at": created_at,
        "updated_at": created_at,
        "output_file": None,
        "chunks": [
            {
                "index": index,
                "status": "pending",
                "attempts": 0,
                "error": None,
                "audio_file": None,
            }
            for index in range(len(chunks))
        ],
    }
    _write_json(directory / "chunks.json", {"chunks": chunks})
    _save_job(job)
    return job


def _load_source_chunks(job_id: str) -> list[str]:
    with (_job_dir(job_id) / "chunks.json").open(encoding="utf-8") as handle:
        return json.load(handle)["chunks"]


def _write_wav(path: Path, audio_data: bytes) -> None:
    samples, sample_rate = decode_audio(audio_data)
    pcm = (samples.clip(-1.0, 1.0) * 32767.0).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(pcm)


def _join_wavs(job_id: str, chunk_count: int) -> Path:
    directory = _job_dir(job_id)
    output_path = directory / "narration.wav"
    with wave.open(str(output_path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        for index in range(chunk_count):
            with wave.open(
                str(directory / "chunks" / f"chunk_{index:05d}.wav"), "rb"
            ) as source:
                if source.getframerate() != SAMPLE_RATE:
                    raise ValueError("All Gemini chunks must use 24 kHz audio.")
                output.writeframes(source.readframes(source.getnframes()))
    return output_path


def run_immediate(job_id: str, *, client: Any | None = None) -> dict[str, Any]:
    """Resume an immediate job, processing only chunks not already complete."""
    with _LOCK:
        job = load_job(job_id)
        if job["mode"] != "immediate":
            raise ValueError("This is not an immediate job.")
        job["status"] = "running"
        _save_job(job)
    chunks = _load_source_chunks(job_id)
    sdk_client = client or create_client()
    for chunk_record, text in zip(job["chunks"], chunks, strict=True):
        if chunk_record["status"] == "completed":
            continue
        chunk_record["attempts"] += 1
        try:
            audio = generate_audio_bytes(
                text,
                voice=job["voice"],
                instruct=job["instruct"],
                client=sdk_client,
            )
            filename = f"chunk_{chunk_record['index']:05d}.wav"
            _write_wav(_job_dir(job_id) / "chunks" / filename, audio)
            chunk_record.update(
                status="completed", error=None, audio_file=f"chunks/{filename}"
            )
        except Exception as exc:
            chunk_record.update(status="failed", error=str(exc)[:500])
        with _LOCK:
            _save_job(job)
    failed = [chunk for chunk in job["chunks"] if chunk["status"] != "completed"]
    if failed:
        job["status"] = "failed"
    else:
        output = _join_wavs(job_id, len(chunks))
        job.update(status="completed", output_file=output.name)
    with _LOCK:
        _save_job(job)
    return job


def _provider_request(text: str, *, voice: str, instruct: str) -> Any:
    from google.genai import types

    return types.InlinedRequest(
        contents=build_prompt(text, instruct=instruct),
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )


def submit_provider_batch(job_id: str, *, client: Any | None = None) -> dict[str, Any]:
    with _LOCK:
        job = load_job(job_id)
        if job["mode"] != "provider_batch":
            raise ValueError("This is not a provider batch job.")
        if job["provider_job"]:
            return job
    chunks = _load_source_chunks(job_id)
    sdk_client = client or create_client()
    requests = [
        _provider_request(text, voice=job["voice"], instruct=job["instruct"])
        for text in chunks
    ]
    provider = sdk_client.batches.create(
        model=MODEL_ID,
        src=requests,
        config={"display_name": f"VoiceStudio Gemini TTS {job_id[:8]}"},
    )
    job.update(status="submitted", provider_job=provider.name)
    _save_job(job)
    return job


def _response_audio(response: Any) -> bytes:
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        for part in getattr(content, "parts", None) or []:
            inline = getattr(part, "inline_data", None)
            data = getattr(inline, "data", None)
            if data:
                return (
                    data
                    if isinstance(data, bytes)
                    else __import__("base64").b64decode(data)
                )
    raise ValueError("Provider batch response contained no audio.")


def refresh_provider_batch(job_id: str, *, client: Any | None = None) -> dict[str, Any]:
    job = load_job(job_id)
    if not job["provider_job"]:
        raise ValueError("Provider batch has not been submitted.")
    sdk_client = client or create_client()
    provider = sdk_client.batches.get(name=job["provider_job"])
    state = str(provider.state or "").casefold()
    if "succeeded" not in state:
        job["status"] = (
            "failed"
            if any(word in state for word in ("failed", "expired", "cancel"))
            else "submitted"
        )
        _save_job(job)
        return job
    responses = (
        getattr(getattr(provider, "dest", None), "inlined_responses", None) or []
    )
    if len(responses) != len(job["chunks"]):
        raise ValueError("Provider batch returned an unexpected number of responses.")
    for record, inlined in zip(job["chunks"], responses, strict=True):
        record["attempts"] += 1
        error = getattr(inlined, "error", None)
        if error:
            record.update(status="failed", error=str(error)[:500])
            continue
        filename = f"chunk_{record['index']:05d}.wav"
        _write_wav(
            _job_dir(job_id) / "chunks" / filename, _response_audio(inlined.response)
        )
        record.update(status="completed", error=None, audio_file=f"chunks/{filename}")
    if all(record["status"] == "completed" for record in job["chunks"]):
        output = _join_wavs(job_id, len(job["chunks"]))
        job.update(status="completed", output_file=output.name)
    else:
        job["status"] = "failed"
    _save_job(job)
    return job


def cancel_provider_batch(job_id: str, *, client: Any | None = None) -> dict[str, Any]:
    job = load_job(job_id)
    if not job["provider_job"]:
        raise ValueError("Provider batch has not been submitted.")
    (client or create_client()).batches.cancel(name=job["provider_job"])
    job["status"] = "cancelled"
    _save_job(job)
    return job


def list_jobs() -> list[dict[str, Any]]:
    if not JOBS_DIR.exists():
        return []
    jobs = []
    for manifest in JOBS_DIR.glob("*/manifest.json"):
        try:
            with manifest.open(encoding="utf-8") as handle:
                jobs.append(json.load(handle))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(jobs, key=lambda item: item.get("created_at", ""), reverse=True)
