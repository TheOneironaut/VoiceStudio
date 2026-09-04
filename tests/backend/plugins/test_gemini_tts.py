from __future__ import annotations

import base64
import os
from types import SimpleNamespace

import pytest

from plugins import gemini_tts
from services.plugin_sdk import ProviderBatchItem, TTSProviderError


def ns(**kwargs):
    return SimpleNamespace(**kwargs)


class FakeInteractions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class FakeBatches:
    def __init__(self):
        self.created = []
        self.cancelled = []
        self.job = None

    def create(self, **kwargs):
        self.created.append(kwargs)
        return ns(name="batches/test-1")

    def get(self, **kwargs):
        return self.job

    def cancel(self, **kwargs):
        self.cancelled.append(kwargs)


class FakeClient:
    def __init__(self, interaction=None):
        self.interactions = interaction or FakeInteractions()
        self.batches = FakeBatches()


def test_metadata_matches_verified_gemini_capabilities():
    plugin = gemini_tts.GeminiTTSPlugin
    assert plugin.default_model_id == "gemini-3.1-flash-tts-preview"
    assert plugin.supports_streaming is True
    assert plugin.supports_provider_batch is True
    assert plugin.supports_cloning is False
    assert plugin.supports_voice_design is False
    assert "he" in plugin.supported_languages_hint
    assert len(plugin().list_voices()) == 30


def test_missing_sdk_or_key_only_makes_gemini_unavailable(monkeypatch):
    monkeypatch.setattr(gemini_tts.importlib.util, "find_spec", lambda _name: None)
    assert gemini_tts.GeminiTTSPlugin.is_available()[0] is False

    monkeypatch.setattr(gemini_tts.importlib.util, "find_spec", lambda _name: object())
    monkeypatch.setattr(gemini_tts, "resolve_api_key", lambda: None)
    available, reason = gemini_tts.GeminiTTSPlugin.is_available()
    assert available is False
    assert "GEMINI_API_KEY" in reason


def test_standard_generation_maps_prompt_voice_language_and_raw_pcm(monkeypatch):
    pcm = b"\x00\x00\xff\x7f"
    interaction = FakeInteractions(
        ns(output_audio=ns(data=base64.b64encode(pcm).decode(), mime_type="audio/L16"))
    )
    client = FakeClient(interaction)
    monkeypatch.setattr(gemini_tts, "_client", lambda: client)

    result = gemini_tts.GeminiTTSPlugin().generate(
        "שלום", voice_id="Kore", language="he", instruct="Warm and calm", speed=1.1
    )

    assert result.data == pcm
    assert result.encoding == "pcm_s16le"
    call = interaction.calls[0]
    assert call["model"] == "gemini-3.1-flash-tts-preview"
    assert "Warm and calm" in call["input"]
    assert "1.10 times" in call["input"]
    assert call["generation_config"]["speech_config"] == [
        {"voice": "Kore", "language": "he"}
    ]


def test_wav_and_malformed_audio_are_classified():
    wav = b"RIFF" + b"\x00" * 40
    assert gemini_tts._decode_audio_data(wav).encoding == "wav"
    with pytest.raises(TTSProviderError, match="malformed base64"):
        gemini_tts._decode_audio_data("not base64!")
    with pytest.raises(TTSProviderError, match="empty audio"):
        gemini_tts._decode_audio_data(b"")


@pytest.mark.parametrize(
    ("status", "code", "retryable"),
    [
        (401, "invalid_credentials", False),
        (403, "permission_denied", False),
        (404, "model_unavailable", False),
        (429, "rate_limited", True),
        (500, "provider_5xx", True),
    ],
)
def test_http_errors_are_normalized(status, code, retryable):
    error = RuntimeError("secret provider detail")
    error.status_code = status
    normalized = gemini_tts._provider_error(error)
    assert normalized.code == code
    assert normalized.retryable is retryable
    assert "secret provider detail" not in str(normalized)


def test_provider_batch_submit_poll_and_cancel(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(gemini_tts, "_client", lambda: client)
    plugin = gemini_tts.GeminiTTSPlugin()
    items = [ProviderBatchItem(id="item-a", text="Hello"), ProviderBatchItem(id="item-b", text="World")]

    batch_id = plugin.submit_provider_batch(items, voice_id="Puck", language="en")
    assert batch_id == "batches/test-1"
    created = client.batches.created[0]
    assert created["model"] == gemini_tts.MODEL_ID
    assert len(created["src"]) == 2
    assert created["src"][0]["config"]["response_modalities"] == ["AUDIO"]

    def audio_response(value: bytes):
        return ns(candidates=[ns(content=ns(parts=[ns(inline_data=ns(data=value, mime_type="audio/L16"))]))])

    client.batches.job = ns(
        state=ns(name="JOB_STATE_SUCCEEDED"),
        dest=ns(inlined_responses=[
            ns(response=audio_response(b"\x00\x00"), error=None),
            ns(response=audio_response(b"\x01\x00"), error=None),
        ]),
    )
    poll = plugin.poll_provider_batch(batch_id, item_ids=("item-a", "item-b"))
    assert poll.status == "completed"
    assert [result.id for result in poll.results] == ["item-a", "item-b"]
    assert [result.audio.data for result in poll.results] == [b"\x00\x00", b"\x01\x00"]

    plugin.cancel_provider_batch(batch_id)
    assert client.batches.cancelled == [{"name": batch_id}]


def test_live_gemini_tts_only_when_explicitly_enabled():
    if os.environ.get("GEMINI_TTS_LIVE_TEST") != "1":
        pytest.skip("set GEMINI_TTS_LIVE_TEST=1 to authorize a paid live request")
    if not gemini_tts.resolve_api_key():
        pytest.skip("GEMINI_API_KEY is not configured")
    audio = gemini_tts.GeminiTTSPlugin().generate(
        "VoiceStudio live Gemini TTS smoke test.", voice_id="Kore", language="en"
    )
    assert audio.data
    assert audio.sample_rate == 24_000
