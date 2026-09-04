"""Google Gemini TTS provider.

All Google wire details stay here. Importing this module does not import the
Google SDK, torch, torchaudio, or a local model package.
"""
from __future__ import annotations

import base64
import importlib
import importlib.util
import os
import random
import time
from typing import Any

from services import settings_store
from services.plugin_sdk import (
    AudioPayload,
    ProviderBatchItem,
    ProviderBatchPoll,
    ProviderBatchResult,
    TTSPlugin,
    TTSProviderError,
    register_plugin,
)

MODEL_ID = "gemini-3.1-flash-tts-preview"
SAMPLE_RATE = 24_000
_SECRET_NAME = "tts_plugin.gemini-tts"

_VOICES = (
    ("Zephyr", "Bright"), ("Puck", "Upbeat"), ("Charon", "Informative"),
    ("Kore", "Firm"), ("Fenrir", "Excitable"), ("Leda", "Youthful"),
    ("Orus", "Firm"), ("Aoede", "Breezy"), ("Callirrhoe", "Easy-going"),
    ("Autonoe", "Bright"), ("Enceladus", "Breathy"), ("Iapetus", "Clear"),
    ("Umbriel", "Easy-going"), ("Algieba", "Smooth"), ("Despina", "Smooth"),
    ("Erinome", "Clear"), ("Algenib", "Gravelly"), ("Rasalgethi", "Informative"),
    ("Laomedeia", "Upbeat"), ("Achernar", "Soft"), ("Alnilam", "Firm"),
    ("Schedar", "Even"), ("Gacrux", "Mature"), ("Pulcherrima", "Forward"),
    ("Achird", "Friendly"), ("Zubenelgenubi", "Casual"), ("Vindemiatrix", "Gentle"),
    ("Sadachbia", "Lively"), ("Sadaltager", "Knowledgeable"), ("Sulafat", "Warm"),
)

_LANGUAGES = [
    "ar", "bn", "nl", "en", "fr", "de", "hi", "id", "it", "ja", "ko", "mr",
    "pl", "pt", "ro", "ru", "es", "ta", "te", "th", "tr", "uk", "vi", "af",
    "sq", "am", "hy", "az", "eu", "be", "bg", "my", "ca", "ceb", "cmn", "hr",
    "cs", "da", "et", "fil", "fi", "gl", "ka", "el", "gu", "ht", "he", "hu",
    "is", "jv", "kn", "kok", "lo", "la", "lv", "lt", "lb", "mk", "mai", "mg",
    "ms", "ml", "mn", "ne", "nb", "nn", "or", "ps", "fa", "pa", "sr", "sd",
    "si", "sk", "sl", "sw", "sv", "ur",
]


def resolve_api_key() -> str | None:
    return (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
        or settings_store.get_secret(_SECRET_NAME)
    ) or None


def save_api_key(api_key: str) -> None:
    settings_store.set_secret(_SECRET_NAME, api_key.strip())


def has_stored_api_key() -> bool:
    return _SECRET_NAME in settings_store.list_secret_names()


def _client():
    api_key = resolve_api_key()
    if not api_key:
        raise TTSProviderError(
            "Gemini TTS is not configured. Set GEMINI_API_KEY or save a key in Settings.",
            code="missing_credentials",
        )
    try:
        genai = importlib.import_module("google.genai")
    except ImportError as exc:
        raise TTSProviderError(
            "Gemini TTS support is not installed. Install the 'gemini' optional dependency.",
            code="missing_dependency",
        ) from exc
    return genai.Client(api_key=api_key)


def _getattr_path(value: Any, path: str, default=None):
    current = value
    for part in path.split("."):
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, (list, tuple)) and part.isdigit():
            index = int(part)
            current = current[index] if index < len(current) else None
        else:
            current = getattr(current, part, None)
    return default if current is None else current


def _decode_audio_data(data: Any, mime_type: str | None = None) -> AudioPayload:
    if isinstance(data, str):
        try:
            raw = base64.b64decode(data, validate=True)
        except ValueError as exc:
            raise TTSProviderError(
                "Gemini returned malformed base64 audio.", code="malformed_audio"
            ) from exc
    elif isinstance(data, (bytes, bytearray)):
        raw = bytes(data)
    else:
        raise TTSProviderError("Gemini returned no audio data.", code="empty_audio")
    if not raw:
        raise TTSProviderError("Gemini returned empty audio.", code="empty_audio", retryable=True)
    is_wav = raw.startswith(b"RIFF") or (mime_type or "").lower().startswith("audio/wav")
    return AudioPayload(raw, SAMPLE_RATE, encoding="wav" if is_wav else "pcm_s16le")


def _interaction_audio(interaction: Any) -> AudioPayload:
    output_audio = _getattr_path(interaction, "output_audio")
    data = _getattr_path(output_audio, "data")
    mime_type = _getattr_path(output_audio, "mime_type")
    return _decode_audio_data(data, mime_type)


def _generate_content_audio(response: Any) -> AudioPayload:
    parts = _getattr_path(response, "candidates.0.content.parts")
    if parts is None:
        candidates = _getattr_path(response, "candidates", []) or []
        parts = _getattr_path(candidates[0], "content.parts", []) if candidates else []
    for part in parts or []:
        inline = _getattr_path(part, "inline_data")
        if inline is not None:
            return _decode_audio_data(
                _getattr_path(inline, "data"), _getattr_path(inline, "mime_type")
            )
    raise TTSProviderError("Gemini batch returned no audio.", code="empty_audio", retryable=True)


def _status_code(exc: BaseException) -> int | None:
    for value in (
        getattr(exc, "status_code", None),
        getattr(exc, "code", None),
        _getattr_path(exc, "response.status_code"),
    ):
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _provider_error(exc: BaseException) -> TTSProviderError:
    status = _status_code(exc)
    if status in {401, 403}:
        code = "invalid_credentials" if status == 401 else "permission_denied"
        return TTSProviderError("Google rejected the Gemini credentials.", code=code)
    if status == 404:
        return TTSProviderError("The configured Gemini TTS model is unavailable.", code="model_unavailable")
    if status == 429:
        retry_after = _getattr_path(exc, "response.headers.retry-after")
        try:
            retry_after = float(retry_after)
        except (TypeError, ValueError):
            retry_after = None
        return TTSProviderError("Gemini rate limit reached.", code="rate_limited", retryable=True, retry_after_s=retry_after)
    if status is not None and status >= 500:
        return TTSProviderError("Gemini service is temporarily unavailable.", code="provider_5xx", retryable=True)
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return TTSProviderError("Gemini network request failed.", code="network", retryable=True)
    return TTSProviderError("Gemini TTS request failed.", code="provider_error")


def _speech_prompt(text: str, instruct: str | None, speed: float) -> str:
    directions = []
    if instruct:
        directions.append(instruct.strip())
    if speed != 1.0:
        directions.append(f"Speak at approximately {speed:.2f} times the normal pace.")
    notes = f"\nDirector's notes: {' '.join(directions)}" if directions else ""
    return f"Synthesize the following transcript exactly as speech.{notes}\nTranscript:\n{text}"


def _generate_config(voice_id: str, language: str | None) -> dict:
    voice_config = {"prebuilt_voice_config": {"voice_name": voice_id}}
    speech_config: dict[str, Any] = {"voice_config": voice_config}
    if language:
        speech_config["language_code"] = language
    return {"response_modalities": ["AUDIO"], "speech_config": speech_config}


def _max_attempts() -> int:
    try:
        requested = int(os.environ.get("GEMINI_TTS_MAX_ATTEMPTS", "3"))
    except ValueError:
        requested = 3
    return max(1, min(requested, 5))


@register_plugin
class GeminiTTSPlugin(TTSPlugin):
    id = "gemini-tts"
    display_name = "Google Gemini TTS"
    requires_api_key = True
    is_local = False
    supports_cloning = False
    supports_voice_design = False
    supports_streaming = True
    supports_provider_batch = True
    supported_languages_hint = _LANGUAGES
    default_voice_id = "Kore"
    default_model_id = MODEL_ID
    install_hint = "uv sync --extra gemini"
    models = ({"id": MODEL_ID, "name": "Gemini 3.1 Flash TTS Preview", "preview": True},)

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        try:
            sdk_available = importlib.util.find_spec("google.genai") is not None
        except (ImportError, ModuleNotFoundError):
            sdk_available = False
        if not sdk_available:
            return False, "Install VoiceStudio with the 'gemini' optional dependency."
        if not resolve_api_key():
            return False, "Set GEMINI_API_KEY or save a Gemini key in Settings."
        return True, "Ready"

    @classmethod
    def save_api_key(cls, api_key: str) -> None:
        save_api_key(api_key)

    @classmethod
    def has_stored_api_key(cls) -> bool:
        return has_stored_api_key()

    @classmethod
    def has_api_key(cls) -> bool:
        return resolve_api_key() is not None

    def list_voices(self) -> list[dict]:
        return [
            {"id": voice, "name": voice, "description": description, "language": "multi"}
            for voice, description in _VOICES
        ]

    def generate(
        self,
        text: str,
        *,
        voice_id: str | None = None,
        model_id: str | None = None,
        language: str | None = None,
        instruct: str | None = None,
        speed: float = 1.0,
        **kwargs,
    ) -> AudioPayload:
        if not text.strip():
            raise ValueError("Gemini TTS text must not be empty.")
        model = model_id or self.default_model_id
        voice = voice_id or self.default_voice_id
        attempts = _max_attempts()
        for attempt in range(attempts):
            try:
                interaction = _client().interactions.create(
                    model=model,
                    input=_speech_prompt(text, instruct, speed),
                    response_format={"type": "audio"},
                    generation_config={"speech_config": [{"voice": voice, **({"language": language} if language else {})}]},
                )
                return _interaction_audio(interaction)
            except TTSProviderError as exc:
                error = exc
            except Exception as exc:  # noqa: BLE001 - normalize SDK errors
                error = _provider_error(exc)
            if not error.retryable or attempt + 1 >= attempts:
                raise error
            delay = error.retry_after_s if error.retry_after_s is not None else 2 ** attempt + random.random()
            time.sleep(delay)
        raise AssertionError("unreachable")

    def submit_provider_batch(
        self,
        items: list[ProviderBatchItem],
        *,
        voice_id: str | None = None,
        model_id: str | None = None,
        language: str | None = None,
        instruct: str | None = None,
        speed: float = 1.0,
        **settings,
    ) -> str:
        model = model_id or self.default_model_id
        voice = voice_id or self.default_voice_id
        requests = [
            {
                "contents": [{"parts": [{"text": _speech_prompt(item.text, instruct, speed)}], "role": "user"}],
                "metadata": {"key": item.id},
                "config": _generate_config(voice, language),
            }
            for item in items
        ]
        try:
            batch = _client().batches.create(
                model=model,
                src=requests,
                config={"display_name": f"VoiceStudio TTS {items[0].id[:12]}"},
            )
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise _provider_error(exc) from exc
        name = _getattr_path(batch, "name")
        if not name:
            raise TTSProviderError("Gemini returned no batch job id.", code="malformed_response")
        return str(name)

    def poll_provider_batch(
        self,
        provider_batch_id: str,
        *,
        item_ids: tuple[str, ...] = (),
    ) -> ProviderBatchPoll:
        try:
            batch = _client().batches.get(name=provider_batch_id)
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise _provider_error(exc) from exc
        state = _getattr_path(batch, "state.name") or str(_getattr_path(batch, "state", ""))
        mapped = {
            "JOB_STATE_PENDING": "queued", "JOB_STATE_RUNNING": "running",
            "JOB_STATE_SUCCEEDED": "completed", "JOB_STATE_FAILED": "failed",
            "JOB_STATE_CANCELLED": "cancelled", "JOB_STATE_EXPIRED": "failed",
        }.get(state, "running")
        if mapped != "completed":
            error = None
            if mapped == "failed":
                error = {"code": "provider_batch_failed", "message": "Gemini batch failed."}
            return ProviderBatchPoll(status=mapped, error=error)

        inline = _getattr_path(batch, "dest.inlined_responses", []) or []
        results = []
        inline_by_id = {
            str(_getattr_path(entry, "metadata.key")): entry
            for entry in inline
            if _getattr_path(entry, "metadata.key")
        }
        for index, item_id in enumerate(item_ids):
            response_entry = inline_by_id.get(item_id)
            if response_entry is None:
                response_entry = inline[index] if index < len(inline) else None
            response = _getattr_path(response_entry, "response")
            error = _getattr_path(response_entry, "error")
            if error is not None or response is None:
                results.append(ProviderBatchResult(
                    id=item_id,
                    error={"code": "provider_item_failed", "message": "Gemini batch item failed."},
                ))
                continue
            try:
                audio = _generate_content_audio(response)
            except TTSProviderError as exc:
                results.append(ProviderBatchResult(id=item_id, error={"code": exc.code, "message": str(exc)}))
            else:
                results.append(ProviderBatchResult(id=item_id, audio=audio))
        return ProviderBatchPoll(status="completed", results=tuple(results))

    def cancel_provider_batch(self, provider_batch_id: str) -> None:
        try:
            _client().batches.cancel(name=provider_batch_id)
        except Exception as exc:  # noqa: BLE001 - normalize SDK errors
            raise _provider_error(exc) from exc
