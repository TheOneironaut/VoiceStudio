from __future__ import annotations

import pytest

from core import db
from services import tts_batch_store as store


@pytest.fixture
def batch_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "batch.db"))
    db.ensure_schema()


def test_job_creation_pins_configuration_and_is_idempotent(batch_db):
    first = store.create_job(
        engine_id="fake-cloud",
        texts=["one", "two"],
        model_id="model-a",
        voice_id="voice-a",
        settings={"speed": 1.2, "instruct": "Warm"},
        execution_mode="provider_batch",
        idempotency_key="request-1",
    )
    duplicate = store.create_job(
        engine_id="different",
        texts=["ignored"],
        idempotency_key="request-1",
    )

    assert duplicate["id"] == first["id"]
    assert first["engine_id"] == "fake-cloud"
    assert first["model_id"] == "model-a"
    assert first["voice_id"] == "voice-a"
    assert first["settings"] == {"instruct": "Warm", "speed": 1.2}
    assert [item["input_text"] for item in first["items"]] == ["one", "two"]


def test_restart_requeues_running_only_and_preserves_completed_output(batch_db):
    job = store.create_job(engine_id="fake", texts=["done", "interrupted"])
    done, interrupted = job["items"]
    store.set_item_result(
        done["id"], "completed", output_path="job/item-0.wav", checksum="abc"
    )
    store.set_item_running(interrupted["id"])
    store.set_job_status(job["id"], "running")

    assert store.jobs_to_resume() == [job["id"]]
    restored = store.get_job(job["id"])

    assert restored["status"] == "queued"
    assert restored["items"][0]["status"] == "completed"
    assert restored["items"][0]["output_path"] == "job/item-0.wav"
    assert restored["items"][0]["checksum"] == "abc"
    assert restored["items"][1]["status"] == "queued"
    assert restored["items"][1]["attempt_count"] == 1


def test_retry_failed_only_requeues_items_with_attempts_remaining(batch_db):
    job = store.create_job(engine_id="fake", texts=["retry", "spent", "done"], max_attempts=2)
    retry_item, spent_item, done_item = job["items"]
    store.set_item_running(retry_item["id"])
    store.set_item_result(retry_item["id"], "failed", error={"code": "timeout"})
    for _ in range(2):
        store.set_item_running(spent_item["id"])
    store.set_item_result(spent_item["id"], "failed", error={"code": "quota"})
    store.set_item_result(done_item["id"], "completed", output_path="done.wav", checksum="ok")
    store.set_job_status(job["id"], "partial")

    assert store.retry_failed(job["id"]) == 1
    refreshed = store.get_job(job["id"])
    assert [item["status"] for item in refreshed["items"]] == [
        "queued", "failed", "completed"
    ]
    assert refreshed["status"] == "queued"


def test_retry_failed_starts_a_fresh_provider_batch(batch_db):
    job = store.create_job(
        engine_id="fake",
        texts=["retry"],
        execution_mode="provider_batch",
        max_attempts=2,
    )
    item = job["items"][0]
    store.set_item_running(item["id"])
    store.set_item_result(
        item["id"],
        "failed",
        error={"code": "provider_error"},
        provider_item_id="old-item",
    )
    store.set_job_status(job["id"], "failed", provider_batch_id="old-batch")

    assert store.retry_failed(job["id"]) == 1
    refreshed = store.get_job(job["id"])
    assert refreshed["provider_batch_id"] is None
    assert refreshed["items"][0]["provider_item_id"] is None


def test_list_jobs_returns_progress_summaries_without_item_text(batch_db):
    job = store.create_job(engine_id="fake", texts=["secret-sized input", "two"])
    store.set_item_result(
        job["items"][0]["id"],
        "completed",
        output_path="one.wav",
        checksum="abc",
    )

    listed = store.list_jobs()

    assert len(listed) == 1
    assert "items" not in listed[0]
    assert "input_text" not in repr(listed[0])
    assert listed[0]["progress"] == {"completed": 1, "total": 2, "fraction": 0.5}


def test_pause_resume_and_cancel_are_durable(batch_db):
    job = store.create_job(engine_id="fake", texts=["one", "two"])
    store.pause_job(job["id"])
    assert store.get_job(job["id"])["status"] == "paused"
    store.resume_job(job["id"])
    assert store.get_job(job["id"])["status"] == "queued"
    store.cancel_job(job["id"])
    cancelled = store.get_job(job["id"])
    assert cancelled["status"] == "cancelled"
    assert {item["status"] for item in cancelled["items"]} == {"cancelled"}


@pytest.mark.parametrize("texts", [[], [""], ["ok", "  "]])
def test_empty_batch_items_are_rejected(batch_db, texts):
    with pytest.raises(ValueError, match="non-empty"):
        store.create_job(engine_id="fake", texts=texts)


def test_credentials_cannot_be_persisted_in_batch_settings(batch_db):
    with pytest.raises(ValueError, match="Secrets are not allowed"):
        store.create_job(
            engine_id="fake",
            texts=["hello"],
            settings={"provider": {"api_key": "must-not-be-stored"}},
        )
