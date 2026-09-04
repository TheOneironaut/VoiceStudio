# Google Gemini TTS

VoiceStudio includes Google Gemini TTS as an optional cloud provider. It is
never selected automatically: a fresh install keeps VoiceStudio's normal local
TTS default, and no text leaves the computer until you select Gemini and start
a generation.

## Enable and configure

The Windows installer enables the generic `bundled-providers` dependency set
during its normal dependency setup; that set currently includes the small
`google-genai` SDK. The desktop bootstrap does not name Gemini or any other
individual provider. A source checkout can enable only Gemini with:

```bash
uv sync --extra gemini
```

Open **Model Catalogue → Engines**, expand **Google Gemini TTS**, paste a Gemini
API key, choose a model and voice, save, and then select the engine. Keys saved
in the UI are encrypted in VoiceStudio's existing per-install secrets store and
are never returned by the API. Power users can instead set `GEMINI_API_KEY` (or
the Google SDK's `GOOGLE_API_KEY` fallback) in the process environment.

When selected, transcript text and style instructions are sent to Google's
Gemini API and may incur Google API charges. The Gemini provider does not
download a local AI model or checkpoint.

## Capabilities

The initial model is configured once in `backend/plugins/gemini_tts.py` as
`gemini-3.1-flash-tts-preview`.

| Capability | VoiceStudio support | Notes |
|---|---:|---|
| Text to speech | Yes | Text input, 24 kHz mono audio output |
| Built-in voices | Yes | 30 Google voices |
| Languages | Yes | Uses Google's documented multilingual roster, including Hebrew |
| Style, accent, pace and tone instructions | Yes | Natural-language directions and expressive tags |
| Voice cloning / reference audio | No | Gemini TTS exposes preset voices, not arbitrary reference-voice cloning |
| Voice design | No | Instructions steer delivery; they do not create a reusable arbitrary voice |
| Streaming | Yes | Gemini 3.1 supports streaming; VoiceStudio's existing chunk-preview path remains provider-neutral |
| Standard batch | Yes | Durable VoiceStudio queue with bounded concurrency and retries |
| Google Batch API | Yes | Optional asynchronous mode behind the same VoiceStudio batch job |
| Long-form | Yes | VoiceStudio chunks and joins items generically; Google recommends chunks shorter than a few minutes |
| Multi-speaker | Not exposed yet | The Google model supports it, but the generic VoiceStudio provider UI currently pins one voice per item |
| Voice-preserving dubbing | No | Dubbing that requires cloned reference voices rejects non-cloning engines clearly |

The model is a preview. Google may rename it, change quotas, or return an
occasional transient server error. VoiceStudio retries only transient network,
rate-limit and server failures; authentication, permission, model and invalid
input failures are not retried.

## Batch modes

The Batch workspace has one provider-neutral TTS queue:

- **Standard API** runs persisted items with bounded provider concurrency.
- **Provider Batch API** submits the same persisted items to Google's
  asynchronous Batch API. Google documents a target turnaround of up to 24
  hours and lower batch pricing.

Both modes pin the engine, model, voice and settings at job creation. Completed
files have checksums, survive restarts, are not regenerated silently, and can be
joined into one WAV. Pause, cancel and retry-failed operate on the generic job,
not a Gemini-specific database or endpoint.

## Official references

- [Gemini TTS generation guide](https://ai.google.dev/gemini-api/docs/speech-generation)
- [Gemini 3.1 Flash TTS model](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview)
- [Gemini Batch API](https://ai.google.dev/gemini-api/docs/batch-api)
- [Gemini pricing](https://ai.google.dev/gemini-api/docs/pricing)
