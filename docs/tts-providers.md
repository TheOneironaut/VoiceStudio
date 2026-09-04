# TTS provider and batch contracts

VoiceStudio has one production TTS registry. Provider plugins are discovered
from `backend/plugins/` and registered once with `@register_plugin`. The bridge
in `services.tts_backend` adapts each plugin into the existing engine catalogue,
selection, generation, workflow and batch paths.

## Adding a provider

Create one module under `backend/plugins/` and subclass
`services.plugin_sdk.TTSPlugin`. Define stable identity and truthful capability
metadata, then implement availability, single-item generation and voices.

```python
from services.plugin_sdk import AudioPayload, TTSPlugin, register_plugin


@register_plugin
class ExampleTTSPlugin(TTSPlugin):
    id = "example-tts"
    display_name = "Example TTS"
    is_local = False
    requires_api_key = True
    supports_cloning = False
    default_voice_id = "voice-a"

    @classmethod
    def is_available(cls):
        ...

    def list_voices(self):
        return [{"id": "voice-a", "name": "Voice A", "language": "multi"}]

    def generate(self, text, **settings):
        return AudioPayload(pcm_bytes, sample_rate=24000, encoding="pcm_s16le")
```

Plugins return `AudioPayload`, never a torch tensor. The shared production
adapter is the only plugin bytes-to-tensor boundary. Supported encodings are
16-bit little-endian PCM, WAV and MP3; sample rate and channel count must be
explicit. A missing optional SDK or credential makes only that provider
unavailable and must not break discovery or application startup.

Provider credentials should use `services.settings_store.set_secret`; never log,
return or persist plaintext keys in jobs. Static imports of cloud SDKs and local
model libraries are forbidden in provider modules. Import provider SDKs only
when availability or a provider operation needs them.

## Generic TTS batch

`services.tts_batch_store` owns durable job and item state in VoiceStudio's main
SQLite database. `services.tts_batch_runner` owns execution, retry, resume,
cancellation, output checksums and joining. Public routes live only under
`/tts/batches`.

A batch pins:

- engine/provider ID;
- model and voice;
- generation settings;
- standard or provider-native execution mode;
- stable item IDs, text, attempt limits and output records.

Providers must not create their own queue, database, router, UI, chunker or
output joiner. An asynchronous provider API is an optional execution adapter:
implement `submit_provider_batch`, `poll_provider_batch` and
`cancel_provider_batch`, and set `supports_provider_batch = True`. Provider
results map back to the generic stable item IDs.

The Batch API submission itself may not be idempotent. Persist the returned
provider job ID immediately and keep the provider's response mapping stable;
the generic runner will resume polling that ID after a restart.

## Required tests

A provider change should cover registration, availability without its optional
dependency/key, request mapping, canonical audio, voices/capabilities, safe
errors, and provider batch hooks when present. Network calls and paid provider
requests are mocked in normal CI. A real-key smoke test must remain explicitly
opt-in.

