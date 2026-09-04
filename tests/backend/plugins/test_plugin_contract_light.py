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
    try:
        plugin_sdk.register_plugin(gemini_tts.GeminiTTSPlugin)
        assert received[-1] is gemini_tts.GeminiTTSPlugin
    finally:
        plugin_sdk._REGISTRATION_LISTENERS.remove(listener)
