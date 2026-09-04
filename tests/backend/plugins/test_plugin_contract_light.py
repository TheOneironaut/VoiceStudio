"""Model-light provider checks for the provider-only CI fast path."""
from __future__ import annotations

from services import plugin_sdk
from plugins import gemini_tts


def test_gemini_registers_once_through_the_shared_plugin_registry():
    assert plugin_sdk.PLUGINS["gemini-tts"] is gemini_tts.GeminiTTSPlugin
    assert issubclass(gemini_tts.GeminiTTSPlugin, plugin_sdk.TTSPlugin)


def test_registration_listener_receives_a_conforming_provider():
    received = []
    listener = received.append
    plugin_sdk.subscribe_to_registrations(listener)

    class ListenerTestPlugin(plugin_sdk.TTSPlugin):
        id = "listener-contract-test"
        display_name = "Listener contract test"

        @classmethod
        def is_available(cls):
            return True, "Ready"

        def generate(self, text, **kwargs):
            return plugin_sdk.AudioPayload(b"\x00\x00", 24000)

        def list_voices(self):
            return []

    try:
        plugin_sdk.register_plugin(ListenerTestPlugin)
        assert received[-1] is ListenerTestPlugin
    finally:
        plugin_sdk.PLUGINS.pop(ListenerTestPlugin.id, None)
        plugin_sdk._REGISTRATION_LISTENERS.remove(listener)
