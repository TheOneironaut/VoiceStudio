from __future__ import annotations

import base64
from types import SimpleNamespace

import numpy as np
import pytest

from engines.gemini_tts import GeminiTTSBackend
from services import gemini_tts


class _Interactions:
    def __init__(self, audio: bytes):
        self.audio = audio
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            output_audio=SimpleNamespace(
                data=base64.b64encode(self.audio).decode("ascii")
            )
        )


def test_generate_is_locked_to_gemini_31_and_selected_voice():
    pcm = np.array([0, 1000, -1000], dtype="<i2").tobytes()
    interactions = _Interactions(pcm)
    client = SimpleNamespace(interactions=interactions)

    result = gemini_tts.generate_audio_bytes(
        "Hello", voice="puck", instruct="Calm documentary", client=client
    )

    assert result == pcm
    assert interactions.calls == [
        {
            "model": "gemini-3.1-flash-tts-preview",
            "input": "Narration direction: Calm documentary\n\nRead exactly:\nHello",
            "response_format": {"type": "audio"},
            "generation_config": {"speech_config": [{"voice": "Puck"}]},
        }
    ]


def test_raw_pcm_decodes_to_voice_studio_tensor():
    pcm = np.array([-32768, 0, 32767], dtype="<i2").tobytes()

    tensor = gemini_tts.audio_bytes_to_tensor(pcm)

    assert tuple(tensor.shape) == (1, 3)
    assert tensor[0, 0].item() == pytest.approx(-1.0)
    assert tensor[0, 2].item() == pytest.approx(32767 / 32768)


def test_api_key_is_resolved_without_fallback_persistence(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "secret-from-env")

    assert gemini_tts.resolve_api_key() == "secret-from-env"


def test_backend_rejects_reference_audio():
    with pytest.raises(ValueError, match="cannot clone"):
        GeminiTTSBackend().generate("Hello", ref_audio="voice.wav")


def test_unknown_voice_is_rejected():
    with pytest.raises(ValueError, match="Unknown Gemini TTS voice"):
        gemini_tts.normalize_voice("not-a-voice")
