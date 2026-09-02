# Gemini 3.1 Flash TTS Preview

Gemini is this fork's default cloud TTS engine for steerable, multilingual narration. It
is locked to `gemini-3.1-flash-tts-preview`; the UI does not expose other Gemini
models. Text and narration instructions leave the machine only after you start
generation with Gemini selected. Existing saved engine choices still win over
the default.

## Setup

Install the locked dependencies and set a key in the shell that starts VoiceStudio:

```powershell
uv sync
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "YOUR_GOOGLE_API_KEY", "User")
```

`GOOGLE_API_KEY` is accepted as a fallback. The key is read from the environment;
it is not written to preferences, manifests, logs, or generated project files.
Restart VoiceStudio after setting it so the installed app receives the new value.

The engine row includes Google's preset voice picker. `GEMINI_TTS_VOICE` can pin
the same choice for headless use. Gemini does not clone reference audio, so
VoiceStudio rejects clone-dependent flows instead of silently changing voices.
No local TTS checkpoint is downloaded unless you explicitly select a local TTS
engine. `OMNIVOICE_TTS_BACKEND` can still override the default for headless use.

## Long-form and provider batch

The persistent API lives under `/batch/gemini-tts`:

- `POST /batch/gemini-tts/jobs` creates an `immediate` or `provider_batch` job.
- `GET /batch/gemini-tts/jobs/{id}` reads state and refreshes provider jobs.
- `POST /batch/gemini-tts/jobs/{id}/retry` retries only unfinished immediate chunks.
- `POST /batch/gemini-tts/jobs/{id}/cancel` cancels a submitted provider batch.
- `GET /batch/gemini-tts/jobs/{id}/audio` downloads the completed WAV.

Jobs are stored under `omnivoice_data/gemini_tts_batch/<job-id>/`. Source text,
chunk state, provider job ID, attempts, errors, and completed WAV files survive a
restart. The API key is never stored there. Immediate mode returns sooner and is
suited to interactive work; provider batch is asynchronous and can take up to 24
hours, but Google prices it below standard synchronous generation.

Gemini emits 24 kHz mono PCM. VoiceStudio validates the payload, converts WAV or
raw PCM into its shared tensor format, and joins completed chunks in source order.
Google recommends chunking outputs longer than a few minutes because voice quality
can drift on very long generations.

## Upstream updates

The adapter is isolated in `backend/services/gemini_tts*.py` and
`backend/engines/gemini_tts/`; the existing registry and router list contain only
small connection points. Use `scripts/sync-upstream.sh` or the weekly
`sync-upstream.yml` workflow to merge `debpalash/VoiceStudio` updates through a
reviewable pull request.
