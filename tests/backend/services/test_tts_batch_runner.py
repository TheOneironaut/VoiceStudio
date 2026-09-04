from __future__ import annotations

import pytest
import torch
import wave

from core import db
from services import tts_backend, tts_batch_runner as runner, tts_batch_store as store
from services.plugin_sdk import AudioPayload, ProviderBatchPoll, ProviderBatchResult
from services.tts_backend import TTSBackend


class FakeBatchBackend(TTSBackend):
    id = "fake-batch"
    display_name = "Fake batch"
    is_local = False
    calls: list[str] = []

    @property
    def sample_rate(self):
        return 8000

    @property
    def supported_languages(self):
        return ["en"]

    @classmethod
    def is_available(cls):
        return True, "Ready"

    def generate(self, text, **kwargs):
        self.calls.append(text)
        if text == "bad":
            raise ValueError("bad input")
        return torch.full((1, 80), 0.25)


class FakeNativeBatchBackend(FakeBatchBackend):
    id = "fake-native-batch"
    supports_provider_batch = True
    submitted = []
    cancelled = []

    def submit_provider_batch(self, items, **settings):
        self.submitted.append((items, settings))
        return "provider/jobs/1"

    def poll_provider_batch(self, provider_batch_id, **context):
        assert provider_batch_id == "provider/jobs/1"
        results = tuple(
            ProviderBatchResult(
                id=item.id,
                audio=AudioPayload((b"\x00\x00" * 80), 8000),
            )
            for item in self.submitted[-1][0]
        )
        return ProviderBatchPoll(status="completed", results=results)

    def cancel_provider_batch(self, provider_batch_id):
        self.cancelled.append(provider_batch_id)


@pytest.fixture
def runner_env(monkeypatch, tmp_path):
    def save_wav(path, audio, sample_rate):
        samples = (
            audio.detach().cpu().clamp(-1, 1).mul(32767).to(torch.int16).numpy()
        )
        with wave.open(path, "wb") as handle:
            handle.setnchannels(samples.shape[0])
            handle.setsampwidth(2)
            handle.setframerate(sample_rate)
            handle.writeframes(samples.T.tobytes())

    def load_wav(path):
        with wave.open(path, "rb") as handle:
            sample_rate = handle.getframerate()
            channels = handle.getnchannels()
            data = handle.readframes(handle.getnframes())
        samples = torch.frombuffer(bytearray(data), dtype=torch.int16).clone()
        audio = samples.reshape(-1, channels).T.float() / 32768.0
        return audio, sample_rate

    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "batch.db"))
    monkeypatch.setattr(runner, "OUTPUTS_DIR", str(tmp_path / "outputs"))
    monkeypatch.setattr(runner, "_get_backend_class", tts_backend.get_backend_class)
    monkeypatch.setattr(runner, "_get_engine_instance", tts_backend.get_engine_instance_for)
    monkeypatch.setattr(runner, "_save_wav", save_wav)
    monkeypatch.setattr(runner, "_load_wav", load_wav)
    db.ensure_schema()
    saved_registry = dict(tts_backend._REGISTRY)
    saved_instances = dict(tts_backend._ENGINE_INSTANCES)
    FakeBatchBackend.calls = []
    FakeNativeBatchBackend.submitted = []
    FakeNativeBatchBackend.cancelled = []
    tts_backend._REGISTRY[FakeBatchBackend.id] = FakeBatchBackend
    tts_backend._REGISTRY[FakeNativeBatchBackend.id] = FakeNativeBatchBackend
    tts_backend._ENGINE_INSTANCES.clear()
    try:
        yield tmp_path
    finally:
        tts_backend._REGISTRY.clear()
        tts_backend._REGISTRY.update(saved_registry)
        tts_backend._ENGINE_INSTANCES.clear()
        tts_backend._ENGINE_INSTANCES.update(saved_instances)


@pytest.mark.asyncio
async def test_standard_batch_persists_items_and_joined_output(runner_env):
    job = store.create_job(
        engine_id=FakeBatchBackend.id,
        texts=["one", "two"],
        model_id="pinned-model",
        voice_id="pinned-voice",
        settings={"concurrency": 4, "join_gap_ms": 10},
    )

    await runner.run_job(job["id"])
    completed = store.get_job(job["id"])

    assert completed["status"] == "completed"
    assert completed["progress"] == {"completed": 2, "total": 2, "fraction": 1.0}
    assert all(item["checksum"] for item in completed["items"])
    assert (runner_env / "outputs" / completed["output_path"]).is_file()
    assert FakeBatchBackend.calls == ["one", "two"]

    await runner.run_job(job["id"])
    assert FakeBatchBackend.calls == ["one", "two"]


@pytest.mark.asyncio
async def test_failure_is_partial_and_completed_output_is_preserved(runner_env):
    job = store.create_job(
        engine_id=FakeBatchBackend.id,
        texts=["good", "bad"],
        max_attempts=3,
    )

    await runner.run_job(job["id"])
    partial = store.get_job(job["id"])

    assert partial["status"] == "partial", partial
    assert [item["status"] for item in partial["items"]] == ["completed", "failed"]
    assert partial["items"][0]["checksum"]
    assert partial["items"][1]["attempt_count"] == 1
    assert partial["items"][1]["error"]["retryable"] is False


@pytest.mark.asyncio
async def test_provider_native_batch_uses_same_store_and_outputs(runner_env):
    job = store.create_job(
        engine_id=FakeNativeBatchBackend.id,
        texts=["one", "two"],
        execution_mode="provider_batch",
        voice_id="voice-a",
        model_id="model-a",
    )

    await runner.run_job(job["id"])
    completed = store.get_job(job["id"])

    assert completed["status"] == "completed", completed
    assert completed["provider_batch_id"] == "provider/jobs/1"
    assert all(item["status"] == "completed" for item in completed["items"])
    submitted_items, settings = FakeNativeBatchBackend.submitted[0]
    assert [item.text for item in submitted_items] == ["one", "two"]
    assert settings["voice_id"] == "voice-a"
    assert settings["model_id"] == "model-a"
