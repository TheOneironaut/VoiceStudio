from __future__ import annotations

import json
import wave
from types import SimpleNamespace

import numpy as np

from services import gemini_tts_batch


class _Interactions:
    def __init__(self, *, fail_on_call: int | None = None):
        self.calls = 0
        self.fail_on_call = fail_on_call

    def create(self, **_kwargs):
        self.calls += 1
        if self.calls == self.fail_on_call:
            raise RuntimeError("synthetic provider failure")
        pcm = np.array([self.calls, -self.calls] * 20, dtype="<i2").tobytes()
        return SimpleNamespace(output_audio=SimpleNamespace(data=pcm))


def _client(*, fail_on_call: int | None = None):
    return SimpleNamespace(interactions=_Interactions(fail_on_call=fail_on_call))


def test_split_text_preserves_every_character():
    text = " First paragraph.\n\nSecond paragraph has many words. " * 8

    chunks = gemini_tts_batch.split_text(text, max_chars=100)

    assert "".join(chunks) == text
    assert all(len(chunk) <= 100 for chunk in chunks)


def test_immediate_job_persists_and_resumes_only_missing_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(gemini_tts_batch, "JOBS_DIR", tmp_path)
    text = "word " * 60
    job = gemini_tts_batch.create_job(
        text, voice="Kore", instruct="Natural", mode="immediate", max_chars=100
    )
    first_client = _client(fail_on_call=2)

    failed = gemini_tts_batch.run_immediate(job["id"], client=first_client)

    assert failed["status"] == "failed"
    completed_before_retry = sum(c["status"] == "completed" for c in failed["chunks"])
    retry_client = _client()
    completed = gemini_tts_batch.run_immediate(job["id"], client=retry_client)
    assert completed["status"] == "completed"
    assert (
        retry_client.interactions.calls
        == len(completed["chunks"]) - completed_before_retry
    )
    output = tmp_path / job["id"] / "narration.wav"
    with wave.open(str(output), "rb") as wav_file:
        assert wav_file.getframerate() == 24_000
        assert wav_file.getnframes() > 0


def test_manifest_never_contains_api_key(tmp_path, monkeypatch):
    monkeypatch.setattr(gemini_tts_batch, "JOBS_DIR", tmp_path)
    monkeypatch.setenv("GEMINI_API_KEY", "must-not-be-written")

    job = gemini_tts_batch.create_job(
        "Hello", voice="Kore", instruct=None, mode="provider_batch"
    )
    manifest = (tmp_path / job["id"] / "manifest.json").read_text(encoding="utf-8")

    assert "must-not-be-written" not in manifest
    assert "api_key" not in json.loads(manifest)


def test_provider_batch_submission_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(gemini_tts_batch, "JOBS_DIR", tmp_path)
    monkeypatch.setattr(gemini_tts_batch, "_provider_request", lambda text, **_kw: text)
    created = gemini_tts_batch.create_job(
        "Hello world", voice="Kore", instruct=None, mode="provider_batch"
    )
    batches = SimpleNamespace(
        calls=0,
        create=lambda **_kwargs: SimpleNamespace(name="batches/provider-1"),
    )
    client = SimpleNamespace(batches=batches)

    submitted = gemini_tts_batch.submit_provider_batch(created["id"], client=client)
    submitted_again = gemini_tts_batch.submit_provider_batch(
        created["id"], client=client
    )

    assert submitted["provider_job"] == "batches/provider-1"
    assert submitted_again["provider_job"] == "batches/provider-1"
