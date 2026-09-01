"""Gemini 3.1 Flash TTS transport and audio conversion helpers."""

from __future__ import annotations

import base64
import binascii
import io
import os
import time
import wave
from typing import Any

import numpy as np
import torch

MODEL_ID = "gemini-3.1-flash-tts-preview"
SAMPLE_RATE = 24_000
DEFAULT_VOICE = "Kore"
VOICES = (
    "Achernar",
    "Achird",
    "Aoede",
    "Algenib",
    "Algieba",
    "Alnilam",
    "Autonoe",
    "Callirrhoe",
    "Charon",
    "Despina",
    "Enceladus",
    "Erinome",
    "Fenrir",
    "Gacrux",
    "Iapetus",
    "Kore",
    "Laomedeia",
    "Leda",
    "Orus",
    "Puck",
    "Pulcherrima",
    "Rasalgethi",
    "Sadachbia",
    "Sadaltager",
    "Schedar",
    "Sulafat",
    "Umbriel",
    "Vindemiatrix",
    "Zephyr",
    "Zubenelgenubi",
)

_MAX_ATTEMPTS = 3
_RETRY_BASE_SECONDS = 0.75


class GeminiTTSConfigurationError(RuntimeError):
    """The Gemini engine is not configured for use."""


class GeminiTTSResponseError(RuntimeError):
    """Gemini returned a response without usable audio."""


def resolve_api_key() -> str:
    """Resolve the key without persisting or logging it."""
    key = (
        os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
    ).strip()
    if not key:
        raise GeminiTTSConfigurationError(
            "Gemini TTS needs GEMINI_API_KEY or GOOGLE_API_KEY."
        )
    return key


def normalize_voice(voice: str | None) -> str:
    """Return the canonical voice name and reject unsupported values."""
    candidate = (voice or DEFAULT_VOICE).strip().casefold()
    by_folded_name = {item.casefold(): item for item in VOICES}
    try:
        return by_folded_name[candidate]
    except KeyError as exc:
        raise ValueError(f"Unknown Gemini TTS voice: {voice!r}") from exc


def create_client(*, api_key: str | None = None) -> Any:
    """Create the official SDK client lazily so other engines stay isolated."""
    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover - exercised without project deps
        raise GeminiTTSConfigurationError(
            "Gemini TTS needs google-genai. Run `uv sync`."
        ) from exc
    return genai.Client(api_key=api_key or resolve_api_key())


def build_prompt(text: str, *, instruct: str | None = None, speed: float = 1.0) -> str:
    """Build a steerable prompt while keeping the supplied text unchanged."""
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("Gemini TTS text cannot be empty.")
    guidance: list[str] = []
    if instruct and instruct.strip():
        guidance.append(instruct.strip())
    if speed > 0 and abs(speed - 1.0) > 0.01:
        guidance.append(f"Speak at approximately {speed:.2f} times normal pace.")
    if not guidance:
        return cleaned
    return f"Narration direction: {' '.join(guidance)}\n\nRead exactly:\n{cleaned}"


def _audio_data_from_interaction(interaction: Any) -> bytes:
    output_audio = getattr(interaction, "output_audio", None)
    data = getattr(output_audio, "data", None)
    if not data:
        raise GeminiTTSResponseError("Gemini returned no audio.")
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        try:
            return base64.b64decode(data, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise GeminiTTSResponseError("Gemini returned invalid audio data.") from exc
    raise GeminiTTSResponseError("Gemini returned an unsupported audio payload.")


def _is_retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status in {408, 409, 429}:
        return True
    if isinstance(status, int) and status >= 500:
        return True
    name = type(exc).__name__.casefold()
    return any(token in name for token in ("timeout", "connection", "transport"))


def generate_audio_bytes(
    text: str,
    *,
    voice: str = DEFAULT_VOICE,
    instruct: str | None = None,
    speed: float = 1.0,
    client: Any | None = None,
) -> bytes:
    """Generate one PCM/WAV payload through the current Interactions API."""
    canonical_voice = normalize_voice(voice)
    sdk_client = client or create_client()
    prompt = build_prompt(text, instruct=instruct, speed=speed)
    last_error: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            interaction = sdk_client.interactions.create(
                model=MODEL_ID,
                input=prompt,
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": canonical_voice}]},
            )
            return _audio_data_from_interaction(interaction)
        except Exception as exc:  # SDK exception classes vary across releases
            last_error = exc
            if attempt == _MAX_ATTEMPTS - 1 or not _is_retryable(exc):
                raise
            time.sleep(_RETRY_BASE_SECONDS * (2**attempt))
    raise RuntimeError("Gemini TTS generation failed.") from last_error


def decode_audio(audio_data: bytes) -> tuple[np.ndarray, int]:
    """Decode Gemini's WAV or raw signed-16-bit mono PCM response."""
    if audio_data.startswith(b"RIFF"):
        with wave.open(io.BytesIO(audio_data), "rb") as wav_file:
            if wav_file.getsampwidth() != 2:
                raise GeminiTTSResponseError("Gemini WAV must use 16-bit samples.")
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            pcm = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype="<i2")
            if channels > 1:
                pcm = pcm.reshape(-1, channels).mean(axis=1).astype(np.int16)
    else:
        if len(audio_data) % 2:
            raise GeminiTTSResponseError("Gemini returned truncated PCM audio.")
        sample_rate = SAMPLE_RATE
        pcm = np.frombuffer(audio_data, dtype="<i2")
    if pcm.size == 0:
        raise GeminiTTSResponseError("Gemini returned empty audio.")
    return pcm.astype(np.float32) / 32768.0, sample_rate


def audio_bytes_to_tensor(audio_data: bytes) -> torch.Tensor:
    samples, sample_rate = decode_audio(audio_data)
    if sample_rate != SAMPLE_RATE:
        raise GeminiTTSResponseError(
            f"Gemini returned {sample_rate} Hz audio; expected {SAMPLE_RATE} Hz."
        )
    return torch.from_numpy(samples.copy()).unsqueeze(0)
