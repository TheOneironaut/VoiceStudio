from __future__ import annotations

import asyncio
import pytest
import torch
import wave

from core import db
from services import (
    tts_backend,
    tts_batch_runner as runner,
    tts_batch_store as store,
    watermark,
)
from services.plugin_sdk import (
    AudioPayload,
    ProviderBatchPoll,
    ProviderBatchResult,
    TTSProviderError,
)
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


class FakeLocalBatchBackend(FakeBatchBackend):
    id = "fake-local-batch"
    is_local = True


class FlakyPollBatchBackend(FakeNativeBatchBackend):
    id = "flaky-native-batch"
    poll_calls = 0

    def poll_provider_batch(self, provider_batch_id, **context):
        type(self).poll_calls += 1
        if type(self).poll_calls == 1:
            raise TTSProviderError("temporary", code="provider_5xx", retryable=True)
        return super().poll_provider_batch(provider_batch_id, **context)


@pytest.fixture
def runner_env(monkeypatch, tmp_path):
    watermark_calls = []

    async def mark_synthetic(audio, sample_rate, *, context, **_kwargs):
        watermark_calls.append((sample_rate, context))
        return audio

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
    monkeypatch.setattr(watermark, "mark_synthetic_async", mark_synthetic)
    db.ensure_schema()
    saved_registry = dict(tts_backend._REGISTRY)
    saved_instances = dict(tts_backend._ENGINE_INSTANCES)
    FakeBatchBackend.calls = []
    FakeNativeBatchBackend.submitted = []
    FakeNativeBatchBackend.cancelled = []
    FlakyPollBatchBackend.submitted = []
    FlakyPollBatchBackend.poll_calls = 0
    tts_backend._REGISTRY[FakeBatchBackend.id] = FakeBatchBackend
    tts_backend._REGISTRY[FakeNativeBatchBackend.id] = FakeNativeBatchBackend
    tts_backend._REGISTRY[FakeLocalBatchBackend.id] = FakeLocalBatchBackend
    tts_backend._REGISTRY[FlakyPollBatchBackend.id] = FlakyPollBatchBackend
    tts_backend._ENGINE_INSTANCES.clear()
    try:
        yield tmp_path, watermark_calls
    finally:
        tts_backend._REGISTRY.clear()
        tts_backend._REGISTRY.update(saved_registry)
        tts_backend._ENGINE_INSTANCES.clear()
        tts_backend._ENGINE_INSTANCES.update(saved_instances)


@pytest.mark.asyncio
async def test_standard_batch_persists_items_and_joined_output(runner_env):
    tmp_path, watermark_calls = runner_env
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
    assert (tmp_path / "outputs" / completed["output_path"]).is_file()
    assert FakeBatchBackend.calls == ["one", "two"]
    assert watermark_calls == [(8000, "tts_batch.item")] * 2

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


@pytest.mark.asyncio
async def test_provider_batch_poll_retries_transient_failures(runner_env, monkeypatch):
    async def no_delay(_seconds):
        return None

    monkeypatch.setattr(runner.asyncio, "sleep", no_delay)
    job = store.create_job(
        engine_id=FlakyPollBatchBackend.id,
        texts=["one"],
        execution_mode="provider_batch",
    )

    await runner.run_job(job["id"])

    assert store.get_job(job["id"])["status"] == "completed"
    assert FlakyPollBatchBackend.poll_calls == 2


@pytest.mark.asyncio
async def test_local_batch_uses_shared_gpu_guard_and_drains_on_shutdown(
    runner_env, monkeypatch
):
    from services import model_manager

    started = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def guarded(fn, **kwargs):
        calls.append(kwargs)
        started.set()
        await release.wait()
        return fn()

    monkeypatch.setattr(model_manager, "run_on_gpu_pool_guarded", guarded)
    monkeypatch.setattr(model_manager, "generate_timeout_s", lambda *_args, **_kwargs: 12.0)
    job = store.create_job(engine_id=FakeLocalBatchBackend.id, texts=["one"])
    runner.schedule(job["id"])
    await started.wait()

    stopping = asyncio.create_task(runner.shutdown())
    await asyncio.sleep(0)
    assert not stopping.done()
    release.set()
    await stopping

    assert calls == [{"what": "TTS batch generate", "timeout": 12.0}]
    assert store.get_job(job["id"])["items"][0]["status"] == "queued"
