"""Native VoiceStudio adapter for Gemini 3.1 Flash TTS Preview."""

from __future__ import annotations

import os
from typing import Optional

import torch

from services.gemini_tts import (
    DEFAULT_VOICE,
    MODEL_ID,
    SAMPLE_RATE,
    VOICES,
    audio_bytes_to_tensor,
    generate_audio_bytes,
    normalize_voice,
)
from services.tts_backend import TTSBackend


class GeminiTTSBackend(TTSBackend):
    id = "gemini-3.1-flash-tts"
    display_name = "Gemini 3.1 Flash TTS Preview"
    supports_cloning = False
    supports_voice_design = True
    applies_own_mastering = True
    gpu_compat = ("cpu",)

    @property
    def sample_rate(self) -> int:
        return SAMPLE_RATE

    @property
    def supported_languages(self) -> list[str]:
        return ["multi"]

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        try:
            from google import genai as _genai  # noqa: F401
        except ImportError:
            return False, "google-genai is not installed; run `uv sync`."
        if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
            return False, "Set GEMINI_API_KEY or GOOGLE_API_KEY to enable Gemini TTS."
        return True, "ready"

    def model_identity(self) -> str:
        return MODEL_ID

    def _voice(self, requested: str | None) -> str:
        if requested:
            return normalize_voice(requested)
        from core import prefs

        selected = prefs.resolve(
            "gemini_tts_voice",
            env="GEMINI_TTS_VOICE",
            default=DEFAULT_VOICE,
        )
        return normalize_voice(selected)

    def generate(
        self,
        text: str,
        *,
        ref_audio: Optional[str] = None,
        ref_text: Optional[str] = None,
        instruct: Optional[str] = None,
        language: Optional[str] = None,
        duration: Optional[float] = None,
        description: Optional[str] = None,
        num_step: int = 16,
        guidance_scale: float = 2.0,
        speed: float = 1.0,
        **extras,
    ) -> torch.Tensor:
        del ref_text, language, duration, num_step, guidance_scale
        if ref_audio:
            raise ValueError(
                "Gemini 3.1 Flash TTS uses preset voices and cannot clone reference audio."
            )
        direction = instruct or description
        audio_data = generate_audio_bytes(
            text,
            voice=self._voice(extras.get("voice")),
            instruct=direction,
            speed=speed,
        )
        return audio_bytes_to_tensor(audio_data)


__all__ = ["DEFAULT_VOICE", "GeminiTTSBackend", "MODEL_ID", "VOICES"]
