from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.dependencies import require_admin_action
from api.routers import engines
from core import db
from plugins import gemini_tts  # noqa: F401 - registers the provider


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "provider.db"))
    db.ensure_schema()
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    app = FastAPI()
    app.include_router(engines.router)
    app.dependency_overrides[require_admin_action] = lambda: None
    with TestClient(app) as test_client:
        yield test_client


def test_provider_configuration_encrypts_key_and_persists_voice(client):
    response = client.put(
        "/engines/tts/gemini-tts/configuration",
        json={
            "voice_id": "Puck",
            "model_id": "gemini-3.1-flash-tts-preview",
            "api_key": "test-secret-value",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["voice_id"] == "Puck"
    assert body["credential_configured"] is True
    assert body["credential_stored"] is True
    assert "test-secret-value" not in response.text

    with db.db_conn() as connection:
        rows = connection.execute("SELECT key, value FROM settings").fetchall()
    serialized = " ".join(str(value) for row in rows for value in row)
    assert "test-secret-value" not in serialized


def test_provider_voice_catalogue_and_validation(client):
    voices = client.get("/engines/tts/gemini-tts/voices")
    assert voices.status_code == 200
    assert len(voices.json()["voices"]) == 30

    invalid = client.put(
        "/engines/tts/gemini-tts/configuration",
        json={"voice_id": "not-a-real-voice"},
    )
    assert invalid.status_code == 422
