from __future__ import annotations

import pytest
import sys
import sqlite3
from fastapi import FastAPI
from fastapi.testclient import TestClient

@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("OMNIVOICE_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    for module_name in list(sys.modules):
        if module_name in {"core", "services", "api", "plugins"} or module_name.startswith(
            ("core.", "services.", "api.", "plugins.")
        ):
            del sys.modules[module_name]

    from api.dependencies import require_admin
    from api.routers import engines
    from core import config, db
    from plugins import gemini_tts  # noqa: F401 - registers the provider

    db.init_db()
    app = FastAPI()
    app.include_router(engines.router)
    app.dependency_overrides[require_admin] = lambda: None
    with TestClient(app) as test_client:
        yield test_client, config.DB_PATH


def test_provider_configuration_encrypts_key_and_persists_voice(client):
    test_client, database_path = client
    response = test_client.put(
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

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute("SELECT key, value FROM settings").fetchall()
    serialized = " ".join(str(value) for row in rows for value in row)
    assert "test-secret-value" not in serialized


def test_provider_voice_catalogue_and_validation(client):
    test_client, _database_path = client
    voices = test_client.get("/engines/tts/gemini-tts/voices")
    assert voices.status_code == 200
    assert len(voices.json()["voices"]) == 30

    invalid = test_client.put(
        "/engines/tts/gemini-tts/configuration",
        json={"voice_id": "not-a-real-voice"},
    )
    assert invalid.status_code == 422
