from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import require_desktop
from api.routers import tts_batches
from core import db
from services.tts_backend import TTSBackend


class ApiTestBackend(TTSBackend):
    id = "api-test"
    display_name = "API test"
    default_model_id = "model-default"
    default_voice_id = "voice-default"

    @property
    def sample_rate(self):
        return 24000

    @property
    def supported_languages(self):
        return ["en"]

    @classmethod
    def is_available(cls):
        return True, "Ready"

    def generate(self, text, **kwargs):
        raise NotImplementedError


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "api.db"))
    db.ensure_schema()
    scheduled = []
    monkeypatch.setattr(tts_batches, "get_backend_class", lambda _engine_id: ApiTestBackend)
    monkeypatch.setattr(tts_batches.tts_batch_runner, "schedule", scheduled.append)
    app = FastAPI()
    app.include_router(tts_batches.router)
    app.dependency_overrides[require_desktop] = lambda: None
    with TestClient(app) as test_client:
        yield test_client, scheduled


def test_create_get_and_list_pin_provider_configuration(client):
    test_client, scheduled = client
    response = test_client.post(
        "/tts/batches",
        json={
            "engine_id": "api-test",
            "items": [{"text": " one "}, {"text": "two"}],
            "settings": {"speed": 1.1},
            "idempotency_key": "same-request",
        },
    )

    assert response.status_code == 202
    job = response.json()
    assert job["model_id"] == "model-default"
    assert job["voice_id"] == "voice-default"
    assert [item["input_text"] for item in job["items"]] == ["one", "two"]
    assert scheduled == [job["id"]]
    assert test_client.get(f"/tts/batches/{job['id']}").status_code == 200
    assert test_client.get("/tts/batches").json()[0]["id"] == job["id"]


def test_pause_resume_cancel_lifecycle(client):
    test_client, scheduled = client
    job = test_client.post(
        "/tts/batches", json={"engine_id": "api-test", "items": [{"text": "one"}]}
    ).json()
    assert test_client.post(f"/tts/batches/{job['id']}/pause").json()["status"] == "paused"
    assert test_client.post(f"/tts/batches/{job['id']}/resume").status_code == 202
    assert scheduled == [job["id"], job["id"]]
    cancelled = test_client.post(f"/tts/batches/{job['id']}/cancel").json()
    assert cancelled["status"] == "cancelled"
    assert cancelled["items"][0]["status"] == "cancelled"


def test_provider_batch_requires_capability(client, monkeypatch):
    test_client, _ = client
    response = test_client.post(
        "/tts/batches",
        json={
            "engine_id": "api-test",
            "execution_mode": "provider_batch",
            "items": [{"text": "one"}],
        },
    )
    assert response.status_code == 422
    assert "does not support provider batch" in response.json()["detail"]


def test_blank_item_and_missing_job_are_rejected(client):
    test_client, _ = client
    response = test_client.post(
        "/tts/batches", json={"engine_id": "api-test", "items": [{"text": "  "}]}
    )
    assert response.status_code == 422
    assert test_client.get("/tts/batches/not-found").status_code == 404
