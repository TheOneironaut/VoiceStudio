"""
Plugin SDK — abstract interface for third-party TTS engines.

Allows community contributors to add support for ElevenLabs, XTTS, Bark,
Fish TTS, etc. without modifying core VoiceStudio code.

Usage:
    1. Create a Python file in backend/plugins/  (e.g. elevenlabs.py)
    2. Subclass `TTSPlugin` and implement the 4 abstract methods
    3. Register via `@register_plugin` decorator or add to PLUGINS dict
    4. The engine will appear in the frontend Settings → TTS Engine picker

Example:
    from services.plugin_sdk import TTSPlugin, register_plugin

    @register_plugin
    class ElevenLabsPlugin(TTSPlugin):
        id = "elevenlabs"
        display_name = "ElevenLabs"
        ...
"""
from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Literal, Optional

logger = logging.getLogger("omnivoice.plugins")


class TTSProviderError(RuntimeError):
    """Normalized provider failure used by generic retry and batch layers."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "provider_error",
        retryable: bool = False,
        retry_after_s: float | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.retry_after_s = retry_after_s

# ── Plugin registry ──────────────────────────────────────────────────

PLUGINS: dict[str, type["TTSPlugin"]] = {}
_REGISTRATION_LISTENERS: list[Callable[[type["TTSPlugin"]], None]] = []
_PLUGIN_ID_RE = re.compile(r"^[a-z0-9]+(?:[a-z0-9-]*[a-z0-9])?$")


@dataclass(frozen=True)
class AudioPayload:
    """Provider-neutral audio returned by a plugin.

    Cloud plugins stay independent of torch and local model libraries.  The
    production TTS adapter owns conversion from this transport-safe payload to
    VoiceStudio's tensor contract.
    """

    data: bytes
    sample_rate: int
    encoding: Literal["pcm_s16le", "wav", "mp3"] = "pcm_s16le"
    channels: int = 1


@dataclass(frozen=True)
class ProviderBatchItem:
    id: str
    text: str


@dataclass(frozen=True)
class ProviderBatchResult:
    id: str
    audio: Optional[AudioPayload] = None
    error: Optional[dict] = None


@dataclass(frozen=True)
class ProviderBatchPoll:
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    results: tuple[ProviderBatchResult, ...] = ()
    error: Optional[dict] = None


def register_plugin(cls: type["TTSPlugin"]) -> type["TTSPlugin"]:
    """Decorator: register a TTS plugin class by its `id`."""
    if not isinstance(cls, type) or not issubclass(cls, TTSPlugin):
        raise TypeError("TTS plugins must subclass TTSPlugin.")
    if not _PLUGIN_ID_RE.fullmatch(cls.id or ""):
        raise ValueError(
            f"Plugin class {cls.__name__} must define a lowercase, hyphenated `id`."
        )
    existing = PLUGINS.get(cls.id)
    if existing is not None and existing is not cls:
        raise ValueError(f"Duplicate TTS plugin id: {cls.id!r}.")
    PLUGINS[cls.id] = cls
    for listener in tuple(_REGISTRATION_LISTENERS):
        listener(cls)
    logger.info("Registered TTS plugin: %s (%s)", cls.id, cls.display_name)
    return cls


def subscribe_to_registrations(listener: Callable[[type["TTSPlugin"]], None]) -> None:
    """Notify a production registry when plugins register after import."""
    if listener not in _REGISTRATION_LISTENERS:
        _REGISTRATION_LISTENERS.append(listener)


def get_plugin(plugin_id: str) -> "TTSPlugin":
    """Instantiate and return a plugin by id."""
    cls = PLUGINS.get(plugin_id)
    if cls is None:
        available = ", ".join(sorted(PLUGINS.keys())) or "none"
        raise KeyError(f"Unknown TTS plugin '{plugin_id}'. Available: {available}")
    return cls()


def list_plugins() -> list[dict]:
    """Return metadata for all registered plugins (for the frontend)."""
    out = []
    for pid, cls in sorted(PLUGINS.items()):
        ok, msg = cls.is_available()
        out.append({
            "id": pid,
            "display_name": cls.display_name,
            "requires_api_key": cls.requires_api_key,
            "is_local": cls.is_local,
            "available": ok,
            "availability_message": msg,
            "supported_languages": cls.supported_languages_hint,
            "supports_cloning": cls.supports_cloning,
            "supports_voice_design": cls.supports_voice_design,
            "supports_streaming": cls.supports_streaming,
            "supports_provider_batch": cls.supports_provider_batch,
            "models": list(cls.models),
            "default_model_id": cls.default_model_id,
            "default_voice_id": cls.default_voice_id,
        })
    return out


# ── Abstract base class ─────────────────────────────────────────────


class TTSPlugin(ABC):
    """Base class for all TTS engine plugins.

    Subclass this and implement the abstract methods to add support for
    a new TTS engine (cloud API or local model).
    """

    #: Unique identifier (lowercase, no spaces). Used in API requests.
    id: str = ""

    #: Human-readable name for the UI.
    display_name: str = "Unnamed Plugin"

    #: Whether this engine needs an API key (cloud providers).
    requires_api_key: bool = False

    #: Whether this engine runs locally (no network calls).
    is_local: bool = False

    #: Hint for the UI — list of commonly supported languages.
    supported_languages_hint: list[str] = ["en"]

    #: Truthful, provider-owned capabilities surfaced through the generic
    #: production engine catalogue.
    supports_cloning: bool = False
    supports_voice_design: bool = False
    supports_streaming: bool = False
    supports_provider_batch: bool = False

    #: Static model metadata. Providers whose roster is dynamic may override
    #: ``list_models`` without forcing a network call during app startup.
    models: tuple[dict, ...] = ()
    default_model_id: Optional[str] = None
    default_voice_id: Optional[str] = None
    install_hint: Optional[str] = None

    @classmethod
    @abstractmethod
    def is_available(cls) -> tuple[bool, str]:
        """Check if the engine can run in the current environment.

        Returns:
            (True, "Ready") if available.
            (False, "pip install ...") with actionable fix instructions.
        """

    @abstractmethod
    def generate(
        self,
        text: str,
        *,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        language: Optional[str] = None,
        instruct: Optional[str] = None,
        speed: float = 1.0,
        **kwargs,
    ) -> AudioPayload:
        """Generate speech from text.

        Args:
            text: The text to synthesize.
            voice_id: Provider-specific voice identifier.
            language: ISO 639 language code.
            speed: Speech speed multiplier.

        Returns:
            Audio bytes plus their explicit encoding and format metadata.
        """

    @abstractmethod
    def list_voices(self) -> list[dict]:
        """Return available voices for this engine.

        Returns:
            List of dicts with at least: {"id": str, "name": str, "language": str}
        """

    def get_sample_rate(self) -> int:
        """Output sample rate. Override if not 24000."""
        return 24000

    @classmethod
    def list_models(cls) -> list[dict]:
        return [dict(model) for model in cls.models]

    @classmethod
    def save_api_key(cls, api_key: str) -> None:
        raise NotImplementedError(f"TTS plugin {cls.id!r} does not support stored credentials.")

    @classmethod
    def has_stored_api_key(cls) -> bool:
        return False

    @classmethod
    def has_api_key(cls) -> bool:
        return cls.has_stored_api_key()

    def submit_provider_batch(
        self,
        items: list[ProviderBatchItem],
        *,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        language: Optional[str] = None,
        instruct: Optional[str] = None,
        **settings,
    ) -> str:
        raise NotImplementedError(f"TTS plugin {self.id!r} has no provider batch support.")

    def poll_provider_batch(
        self,
        provider_batch_id: str,
        *,
        item_ids: tuple[str, ...] = (),
    ) -> ProviderBatchPoll:
        raise NotImplementedError(f"TTS plugin {self.id!r} has no provider batch support.")

    def cancel_provider_batch(self, provider_batch_id: str) -> None:
        raise NotImplementedError(f"TTS plugin {self.id!r} has no provider batch support.")


# ── Built-in plugin: ElevenLabs (example) ────────────────────────────


@register_plugin
class ElevenLabsPlugin(TTSPlugin):
    """ElevenLabs cloud TTS — high-quality voice synthesis.

    Requires: ELEVENLABS_API_KEY environment variable.
    Install:  pip install elevenlabs
    """

    id = "elevenlabs"
    display_name = "ElevenLabs"
    requires_api_key = True
    is_local = False
    install_hint = "uv pip install elevenlabs"
    supported_languages_hint = [
        "en", "es", "fr", "de", "it", "pt", "pl", "hi", "ar", "zh",
        "ja", "ko", "nl", "tr", "ru", "sv", "id", "fil", "ms", "ro",
        "uk", "el", "cs", "da", "fi", "bg", "hr", "sk", "ta",
    ]

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        import os
        if not os.environ.get("ELEVENLABS_API_KEY"):
            return False, "Set ELEVENLABS_API_KEY environment variable."
        try:
            import elevenlabs  # noqa: F401
            return True, "Ready"
        except ImportError:
            return False, "pip install elevenlabs"

    def generate(self, text, *, voice_id=None, language=None, speed=1.0, **kw) -> AudioPayload:
        import os
        from elevenlabs import ElevenLabs

        client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
        audio_iter = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id or "JBFqnCBsd6RMkjVDRZzb",  # George default
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )
        return AudioPayload(
            data=b"".join(audio_iter), sample_rate=44100, encoding="mp3"
        )

    def list_voices(self) -> list[dict]:
        import os
        try:
            from elevenlabs import ElevenLabs
            client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY", ""))
            voices = client.voices.get_all()
            return [
                {"id": v.voice_id, "name": v.name, "language": "multi"}
                for v in voices.voices
            ]
        except Exception as e:
            logger.warning("ElevenLabs list_voices failed: %s", e)
            return []

    def get_sample_rate(self) -> int:
        return 44100


# ── Built-in plugin: Bark (local) ────────────────────────────────────


@register_plugin
class BarkPlugin(TTSPlugin):
    """Suno Bark — open-source local TTS with music/effects support.

    Install: pip install suno-bark
    """

    id = "bark"
    display_name = "Bark (Suno)"
    requires_api_key = False
    is_local = True
    install_hint = "uv pip install suno-bark"
    supported_languages_hint = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"]

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        try:
            from bark import SAMPLE_RATE  # noqa: F401
            return True, "Ready"
        except ImportError:
            return False, "pip install suno-bark"

    def generate(self, text, *, voice_id=None, language=None, speed=1.0, **kw) -> AudioPayload:
        import io
        import numpy as np
        from bark import generate_audio, SAMPLE_RATE
        import scipy.io.wavfile

        speaker = voice_id or "v2/en_speaker_6"
        audio_array = generate_audio(text, history_prompt=speaker)

        buf = io.BytesIO()
        scipy.io.wavfile.write(buf, SAMPLE_RATE, (audio_array * 32767).astype(np.int16))
        return AudioPayload(data=buf.getvalue(), sample_rate=SAMPLE_RATE, encoding="wav")

    def list_voices(self) -> list[dict]:
        return [
            {"id": f"v2/en_speaker_{i}", "name": f"English Speaker {i}", "language": "en"}
            for i in range(10)
        ]

    def get_sample_rate(self) -> int:
        return 24000


# ── Auto-discover plugins from backend/plugins/ directory ────────────

def discover_plugins():
    """Import all .py files in backend/plugins/ to trigger @register_plugin."""
    import importlib
    import pathlib

    plugins_dir = pathlib.Path(__file__).parent.parent / "plugins"
    if not plugins_dir.exists():
        return

    for path in plugins_dir.glob("*.py"):
        if path.name.startswith("_"):
            continue
        module_name = f"plugins.{path.stem}"
        try:
            importlib.import_module(module_name)
            logger.info("Loaded plugin module: %s", module_name)
        except Exception as e:
            logger.warning("Failed to load plugin %s: %s", module_name, e)


# Run discovery on import
discover_plugins()
