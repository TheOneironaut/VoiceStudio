from __future__ import annotations

import sys
import importlib
from types import ModuleType

import numpy as np
import pytest

from services import plugin_sdk, tts_backend
from services.plugin_sdk import AudioPayload, TTSPlugin


@pytest.fixture
def plugin_registry_sandbox():
    saved_plugins = dict(plugin_sdk.PLUGINS)
    saved_registry = dict(tts_backend._REGISTRY)
    try:
        yield
    finally:
        plugin_sdk.PLUGINS.clear()
        plugin_sdk.PLUGINS.update(saved_plugins)
        tts_backend._REGISTRY.clear()
        tts_backend._REGISTRY.update(saved_registry)


def test_one_registration_reaches_production_catalogue_and_generation(
    plugin_registry_sandbox,
):
    @plugin_sdk.register_plugin
    class ContractPlugin(TTSPlugin):
        id = "contract-test"
        display_name = "Contract test"
        is_local = False
        requires_api_key = True
        supported_languages_hint = ["en", "he"]
        supports_streaming = True
        default_voice_id = "voice-a"
        default_model_id = "model-a"
        models = ({"id": "model-a", "name": "Model A"},)

        @classmethod
        def is_available(cls) -> tuple[bool, str]:
            return True, "Ready"

        def generate(self, text: str, **kwargs) -> AudioPayload:
            assert text == "hello"
            assert kwargs["voice_id"] == "voice-a"
            assert kwargs["model_id"] == "model-a"
            samples = np.array([-32768, 0, 32767], dtype="<i2")
            return AudioPayload(samples.tobytes(), 24000)

        def list_voices(self) -> list[dict]:
            return [{"id": "voice-a", "name": "Voice A", "language": "multi"}]

    backend_cls = tts_backend.get_backend_class("contract-test")
    backend = backend_cls()
    audio = backend.generate("hello")

    assert audio.shape == (1, 3)
    assert audio.dtype == tts_backend.torch.float32
    assert audio[0, 0].item() == -1.0
    assert audio[0, 1].item() == 0.0
    assert audio[0, 2].item() == pytest.approx(32767 / 32768)

    entry = next(item for item in tts_backend.list_backends() if item["id"] == "contract-test")
    assert entry["available"] is True
    assert entry["is_local"] is False
    assert entry["requires_api_key"] is True
    assert entry["supports_streaming"] is True
    assert entry["default_voice_id"] == "voice-a"
    assert entry["models"] == [{"id": "model-a", "name": "Model A"}]


def test_duplicate_and_invalid_plugin_ids_fail_clearly(plugin_registry_sandbox):
    class First(TTSPlugin):
        id = "duplicate-test"
        display_name = "First"

        @classmethod
        def is_available(cls):
            return True, "Ready"

        def generate(self, text, **kwargs):
            raise NotImplementedError

        def list_voices(self):
            return []

    plugin_sdk.register_plugin(First)

    class Duplicate(First):
        display_name = "Duplicate"

    with pytest.raises(ValueError, match="Duplicate TTS plugin id"):
        plugin_sdk.register_plugin(Duplicate)

    class Invalid(First):
        id = "Not Valid"

    with pytest.raises(ValueError, match="lowercase, hyphenated"):
        plugin_sdk.register_plugin(Invalid)


def test_plugin_discovery_failure_is_isolated(monkeypatch, caplog):
    real_import_module = importlib.import_module

    def import_module(name: str) -> ModuleType:
        if name == "plugins.broken_test_plugin":
            raise RuntimeError("private discovery detail")
        return real_import_module(name)

    class FakePath:
        name = "broken_test_plugin.py"
        stem = "broken_test_plugin"

    class FakePluginsDir:
        def exists(self):
            return True

        def glob(self, pattern):
            return [FakePath()]

    class FakeServicePath:
        parent = None

        def __init__(self):
            self.parent = self

        def __truediv__(self, _part):
            return FakePluginsDir()

    fake_pathlib = ModuleType("pathlib")
    fake_pathlib.Path = lambda _value: FakeServicePath()
    monkeypatch.setitem(sys.modules, "pathlib", fake_pathlib)
    monkeypatch.setattr("importlib.import_module", import_module)

    plugin_sdk.discover_plugins()

    assert "Failed to load plugin plugins.broken_test_plugin" in caplog.text
