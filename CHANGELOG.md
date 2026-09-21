Warning: truncated output (original token count: 72288)
Total output lines: 2240

# Changelog

All notable changes to VoiceStudio.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).
`frontend/package.json` is the maintained app-version source of truth; Python
metadata and the backend fallback mirror it. Archived Tauri manifests stay frozen.

## [Unreleased]

**Highlights**

- Keep Gemini 3.1 Flash TTS Preview as the default engine while retaining every upstream local engine.
- Publish and smoke-test the Gemini Windows MSI from the synchronized application.
- Carry the fork's Gemini integration and automation through the Electron 0.5.4 upstream release.

### Added

- Gemini Windows releases package and smoke-test the maintained Electron desktop with the Gemini engine active before publishing the rolling MSI. (#13) — thanks @TheOneironaut!

### Fixed

- Gemini Electron builds keep upstream desktop updates disabled and bundle the runtime-pinned uv binary instead of falling back to first-run PowerShell installation. (#13) — thanks @TheOneironaut!
- Gemini Windows relies on the shell's Job Object instead of a redundant parent-pipe thread that blocked native imports and later API workers. — thanks @TheOneironaut!
- Gemini Windows native imports stay on Python's main thread so later API worker threads start normally after cold setup. — thanks @TheOneironaut! (#8)
- The Gemini Windows backend avoids a Windows native-import/thread-start deadlock that left Uvicorn listening while setup timed out after 300 seconds. — thanks @TheOneironaut!

## [0.5.4] — 2026-09-20

**Working engines, smoother long-form audio, and useful local integrations.** CosyVoice repairs its runtime and preserves speech context with newer Transformers. Stories and audiobooks gain cleaner audio joins, better script controls, and more reliable EPUB imports. Electron setup and diagnostics make failures easier to recover from without discarding downloaded models or existing projects.

**Download**

| Platform | Installer |
| --- | --- |
| Windows x64 | [Installer](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.4/VoiceStudio-Electron-0.5.4-win-x64.exe) |
| macOS Apple Silicon | [DMG](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.4/VoiceStudio-Electron-0.5.4-mac-arm64.dmg) |
| macOS Intel | [DMG](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.4/VoiceStudio-Electron-0.5.4-mac-x64.dmg) |
| Linux x64 | [AppImage](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.4/VoiceStudio-Electron-0.5.4-linux-x64.AppImage) · [deb](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.4/VoiceStudio-Electron-0.5.4-linux-x64.deb) |

Already using Electron? Install over your existing app and keep your data. If prompted, choose **Install local runtime** to refresh its dependencies. Moving from Tauri? Back up your data directory with the app closed, install Electron, then verify your voices and projects before removing Tauri. Follow the [migration guide](https://github.com/debpalash/VoiceStudio/blob/v0.5.4/docs/electron-migration.md). Tauri v0.5.3 remains the final Tauri release; its updater cannot install Electron.

**Highlights**

- Repair CosyVoice generation and several engine installation paths without deleting downloaded models (#2258, #2240, #2243)
- Cleaner story and audiobook joins, script controls, and EPUB imports (#2259, #2216, #2203, #2228)
- Export local n8n speech workflows and configure Claude Code or Cursor through MCP (#2261, #2257)
- More reliable Electron setup, dictation, and actionable crash reports (#2221, #2245, #2123, #2262)
- Preserve dialogue, timing, and background audio through dubbing and subtitle imports (#2222, #2224, #2242)

### Changed

- The main sidebar (navigation, voice library, status) stays in place on Settings instead of being swapped for a separate panel; the Settings sections now sit in a column beside it (#2209) — thanks @jaketame!
- The main navigation sits directly under the sidebar header, above the voice library, so it no longer moves with the library's height (#2210) — thanks @jaketame!

### Added

- Claude Code and Cursor integration pages offer MCP setup for the current backend, and duplicate catalog routes are consolidated (#2257)

- Settings → Appearance → Keep sidebar expanded: stops the sidebar shrinking to a rail when Projects, Transcribe, Tools or another workspace opens its own panel on a narrower window (#2211) — thanks @jaketame!
- Stories and Audiobook: a Clear script button empties the whole script — every line and chapter, imported or typed — in one confirmed step instead of one trash icon at a time; the cast is kept (#2203) — thanks @jaketame!
- Stories' Paste & Split can now split by Sentences, Paragraphs (the new default) or whole Chapters, so a single narrator is no longer chopped into one take per sentence (#2217) — thanks @jaketame!

### Fixed

- Preserve completed generation results when worker completion races with the timeout check (#2264)

- CosyVoice repairs missing runtime dependencies and preserves speech context with newer Transformers (#2096) — thanks @martinezpl!
- Electron native-crash reports retain the faulting thread instead of losing it behind long stacks and extension lists (#2262)

- Electron setup normalizes Windows proxy addresses while preserving explicit overrides and localhost exclusions (#2114)
- Web API-reference recovery keeps the selected backend and credentials; AudioSeal embedding and detection normalize model sample rates without changing exported audio dimensions (#2252) — thanks @joseedson18jc!

- LM Studio discovery respects the selected model and dictation refinement preserves literal text while handling unsupported reasoning options (#2252) — thanks @joseedson18jc!
- CosyVoice uses matching float32 weights and inputs without CUDA, preventing a worker-thread dtype failure while preserving CUDA precision (#2096)
- Source Electron launches reuse the prepared Python runtime instead of downloading dependencies inside the startup timeout (#2184)
- Clone, Stories and Audiobook disable unsupported output-language choices for engines with a declared language list (#2104)

- Stories and Audiobook: Generate, the chapter tracker and the render status are pinned in the setup pane instead of sitting below the last line of the script, and a disabled Generate now says why (#2229) — thanks @jaketame!
- EPUB import no longer turns an unmarked teaser page, a "Works by" list, a publisher's address page or a stray footnotes page into chapters — the book's declared start and its contents decide what is front and back matter (#2228) — thanks @jaketame!
- Retry temporary media-tool installation locks and report failed cleanup instead of hiding it (#2214) — thanks @baoyu0!

- The desktop app points the backend at the `uv` it already ships, so one-click engine installs stop failing preflight with "uv was not found" on a clean install — the packaged binary sits in the app's own resources directory, which is on no `PATH`, and a GUI launch inherits none of the shell's `PATH` additions either (#2221, #2215) — thanks @shivsin25 for the fix and @baoyu0 for the diagnosis!
- IndexTTS installs with Python 3.11 and repairs incompatible environments on retry without removing downloaded weights (#2098) — thanks @martinezpl!
- VoxCPM2 voice design uses its native control format, and style requests no longer inherit the reference transcript’s delivery (#2093) — thanks @nevilbutani and @martinezpl!
- Dubbing background preservation and long exports work with newer FFmpeg builds that removed the legacy filter-file option (#2236) — thanks @quan0pek!

- Stories: the book-wide reading speed moved from the bottom of the collapsed Cast card to the setup card beside voice and language, shows how many lines override it, and resets them in one click (#2230) — thanks @jaketame!
- Projects: a finished Story or Audiobook shows its title and how it was made (voice, speed, engine, length, settings) instead of a bare filename (#2233) — thanks @jaketame!
- Audiobook and Stories renders no longer sound broken between lines: each line's engine padding is trimmed and a deliberate, adjustable gap goes between lines and paragraphs instead (#2216) — thanks @jaketame!
- Repair dots.tts dependency pins and paths containing spaces, with OpenFst build guidance for source installs (#2101) — thanks @martinezpl!

- Reject unsupported synthesis languages before model loading, including named picker choices and per-item batch languages (#2219) — thanks @rollroyces!
- EPUB import narrates the book, not its print furniture: page numbers no longer glue onto words or appear as lone lines, cover/title/dedication/copyright/contents pages are skipped, and chapters are titled from the book's table of contents (#2208) — thanks @jaketame!
- Stories: a long script no longer paints over the generation progress panel and the Generate/Stop footer while an audiobook renders (#2213) — thanks @jaketame!
- Keep macOS dictation keyboard operations on the main thread to prevent paste-delivery crashes (#2123)
- Prevent reference voice cloning from silently downloading a second speech recognizer (#2116)
- Dubbing from a video's downloaded rolling captions speaks each line once while preserving intentional repeated dialogue (#2222) — thanks @kevin9327!

- Bundle Linux native helper libraries so dictation and clipboard support start without distribution-specific libxdo packages (#2196)
- Forward saved Hugging Face tokens when downloading gated model weights and dependencies (#2173) — thanks @shivsin25!
- Explain unsupported saved-profile languages consistently in Electron, web, and streaming generation (#2175) — thanks @shivsin25!
- List every installed Kokoro language and accept its displayed name, including British English (#2174) — thanks @drakeo338!

- Validate Python dependencies before reusing a desktop runtime and offer setup for incomplete environments (#2176)
- Check active model cloning support before starting voice conversion (#2147)
- Accept both valid SIGKILL diagnostics in the desktop lifecycle regression check (#2170)

- Repair CTranslate2 loading safely across ASR and translation, and retain the loaded Whisper model during CPU fallback (#2165) — thanks @guruthechosen!
- Avoid pedalboard wheels that crash on unsupported CPU instructions (#2080) — thanks @D3nii!
- Include cuDNN 8 compatibility libraries for CTranslate2 in CUDA containers (#2072) — thanks @basil-k-aji-dev!
- Preserve audio reads, writes, and reference amplitude without TorchCodec (#2083) — thanks @Moep90!
- Give isolated engines request-sized deadlines, validate timeout overrides, and distinguish hangs from crashes (#2109) (#2111) — thanks @SurefireStudios and @LMGXENON!
- Keep dubbing streams alive during quiet steps and delay model cleanup until native refinement ends (#2138) — thanks @denemon!
- Locate ffprobe beside ffmpeg without changing parent directory names (#2107) — thanks @kapelame!
- Resample MLX output chunks to the declared rate before joining them (#2106) — thanks @kapelame!
- Read database migration configuration on Chinese, Japanese, and Korean Windows (#2075) — thanks @kevin9327!
- Preserve milliseconds and carry rounded subtitle timestamps across second boundaries (#2074) — thanks @kevin9327!
- Decode UTF-16 and Windows-1252 subtitle and manuscript imports in Electron, web, and backend routes (#2073) — thanks @kevin9327!
- Preserve numeric subtitle dialogue while recognizing mixed indexed and unindexed cues (#2151) — thanks @shivsin25!
- Parse pasted WebVTT cues while separating metadata, identifiers, empty cues, and complete timing lines (#2077) — thanks @kevin9327!
- Normalize Argos language aliases without silently changing Traditional Chinese to Simplified (#2143, #2152) — thanks @gyanu2507 and @rollroyces!
- Clarify Blackwell import-crash diagnostics without blaming missing kernels (#2084) — thanks @Moep90!
- Distinguish architecture preflight rejection from independent compile-stack failures (#2085) — thanks @Moep90!
- Require the pinned Apple Silicon GGUF build to pass and document runtime preflight conditions (#2115) — thanks @LMGXENON and @martinezpl!
- Correct the Windows Rustup installation command in tooling and documentation (#2066) — thanks @Rukhaam!
- Show local setup guidance when remote native engine installation is unavailable (#2166)
- Show scrubbed native error tails and exit codes for failed dubbing extraction (#2167)

### Docs

- Install with prompt targets Electron, and active scripts, CI and contributor guidance treat Tauri as archived (#2220)
- Load installed IndexTTS checkpoints when the upstream config names missing training-cluster paths, without rewriting user files (#2097) — thanks @martinezpl!
- Cloning errors name the active mlx-audio model and recommend CSM while retaining alternative engines as a fallback (#2204, #2201) — thanks @shivsin25!
- Exported WebVTT subtitles and transcriptions keep a cue like "I <3 you" or one containing `-->` whole in players, instead of cutting or emptying it (#2226) — thanks @kevin9327!
- EPUB imports preserve accents and wide-character documents using their declared encoding or byte-order mark (#2191) — thanks @kevin9327!
- Video watermark exports and dubbing keyframes use the bundled FFmpeg without requiring a system install (#2192) — thanks @kevin9327!
- Restore the backend error class in auto-filed bug reports — the Electron app files through the shared report builder, which never carried it, so every report of an otherwise-generic failure was indistinguishable from the next (#2197) — thanks @shivsin25!
- A streaming generation failure carries its backend error class to the report instead of dropping it at the stream boundary (#2197) — thanks @shivsin25!
- Release cached Ascend NPU memory and recognize its dedicated VRAM when switching engines (#2194) — thanks @li-lizhe!
- Downloaded and pasted WebVTT captions read `&`, `<` and `>` instead of `&amp;`, `&lt;` and `&gt;`, in the editor and in the dub (#2223) — thanks @kevin9327!
- Source installs on Chinese, Japanese and Korean Windows read bundled data as UTF-8, preventing startup and generation failures (#2190) — thanks @kevin9327!
- MOSS-TTS-Nano installs its audio backend and offers dependency repair for older managed installs without deleting cached models (#2182, #2100) — thanks @rollroyces and @martinezpl!
- Resolve Confucius4 model assets from its clone while preserving relative configuration, cache, and reference paths, and reject missing reference clips (#2181, #2099) — thanks @rollroyces and @martinezpl!
- GPT-SoVITS can use an explicitly configured default voice and avoids server-side re-splitting that can drop clauses (#2200) — thanks @jaketame!
- Tabbing through a Dub segment's start or end time without typing no longer moves it to the nearest tenth of a second or changes its speed (#2224) — thanks @kevin9327!

- Connect GPT-SoVITS to its api_v2 endpoint, accept healthy probe responses, and require a reference clip before generation (#2180, #2102) — thanks @rollroyces, @martinezpl and @jaketame!

- A streaming generation that fails on an unsupported GPU, a Windows app-control block, or an audio-file error now says so and what to do, instead of only "Generation failed. Check the selected engine and try again." (#2195, #2177) — thanks @shivsin25!
- A failure that cannot succeed on a retry — an unsupported GPU build, a blocked file — is reported as final, so the app stops re-rendering the whole passage to reach the same error (#2195, #2177) — thanks @shivsin25!
- Importing an .srt into Stories keeps cues whose dialogue is only a number, such as a countdown (#2225) — thanks @kevin9327!

### CI

- Electron packaging rehearsals install and start a fresh managed runtime on Linux, Windows and Apple Silicon before passing (#2263)

- Make the native ASR timeout regression reliable on slow runners and wait for its worker cleanup (#2202)

- Handle missing Electron signing credentials and retry packaging fixes without moving release tags (#2157)

### Contributors

- @D3nii — compatibility with CPUs unsupported by newer pedalboard wheels.
- @LMGXENON — engine deadlines, timeout diagnostics, and Apple Silicon build documentation.
- @Moep90 — audio I/O fallbacks and GPU compatibility guidance.
- @Rukhaam — Windows toolchain setup guidance.
- @Shivendra-Coherent and @shivsin25 — numeric subtitle dialogue, gated downloads, and profile-language errors.
- @SurefireStudios — request-sized sidecar generation deadlines.
- @basil-k-aji-dev — cuDNN compatibility libraries in CUDA containers.
- @denemon — dubbing stream keepalives and cancellation cleanup.
- @guruthechosen — CTranslate2 repair and Whisper CPU recovery.
- @gyanu2507 and @rollroyces — Argos language normalization and regression coverage.
- @kapelame — ffprobe discovery and MLX audio resampling.
- @kevin9327 — subtitle timing, text encodings, WebVTT, and Windows database migrations.
- @drakeo338 — Kokoro supported-language reporting.
- @debpalash — integration, Electron runtime recovery, localization, regression coverage, and release maintenance.
- @jaketame — sidebar navigation, script controls, EPUB imports, long-form audio, and GPT-SoVITS compatibility.
- @joseedson18jc — API recovery, LM Studio discovery, dictation refinement, and AudioSeal sample-rate handling.
- @li-lizhe — Ascend NPU memory cleanup and device detection.

### Bug reports

- Thanks to @YChhunsann, @martinezpl, @denemon, @adeelahmadsiddique, @TehSmoo, @kmsitcomputer, @raya-mansouri, @infinitete, and @kor1998 for the reports behind the fixes above.
- Thanks to @daniilganiev, @nevilbutani, @quan0pek, @baoyu0, @moonjoke001, @Splintercell89, @OtterBeWorking, and @iOSDevSK for additional setup, engine, dubbing, and dictation reports.

## [0.5.3] — 2026-09-17

**A new look. A new desktop app. Still your voices, on your machine.**

VoiceStudio moves to **Electron** with v0.5.3: a redesigned workspace for voice cloning, voice design, stories, dubbing, and transcription. Electron is now the primary desktop app on Windows, macOS, and Linux. Local voice creation still runs on your own hardware, without a required account or API key.

![VoiceStudio's new Electron interface: voice cloning, saved voices, workspace navigation, and synthesis controls](https://raw.githubusercontent.com/debpalash/VoiceStudio/v0.5.3/docs/media/electron/voice-cloning.png)

**Highlights**

- A redesigned desktop with dedicated workspaces, collapsible navigation, and resizable sidebars (#1823, #2129)
- Four-step setup with model packs and optional dictation configuration (#2129)
- Better dubbing: zoomable timelines, saved translation direction, and background sound preserved around dialogue (#2129)
- A simpler Model Catalogue and one-click installs for VoxCPM2, MOSS-TTS-Nano, and CosyVoice 3 (#2013, #2021, #2022, #2025)
- More reliable generation on older NVIDIA GPUs and live remote-worker CPU, GPU, and memory readings (#2135, #2155)

![The Electron dubbing workspace with source and translated demos, language controls, and synchronized playback](https://raw.githubusercontent.com/debpalash/VoiceStudio/v0.5.3/docs/media/electron/dubbing.png)

**Get the new desktop app**

| Platform | Electron installer |
| --- | --- |
| Windows x64 | [Download EXE](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.3/VoiceStudio-Electron-0.5.3-win-x64.exe) |
| macOS Apple Silicon | [Download DMG](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.3/VoiceStudio-Electron-0.5.3-mac-arm64.dmg) |
| macOS Intel | [Download DMG](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.3/VoiceStudio-Electron-0.5.3-mac-x64.dmg) |
| Linux x64 | [AppImage](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.3/VoiceStudio-Electron-0.5.3-linux-x64.AppImage) · [DEB](https://github.com/debpalash/VoiceStudio/releases/download/v0.5.3/VoiceStudio-Electron-0.5.3-linux-x64.deb) |

**Moving from Tauri? Install Electron separately.**

v0.5.3 is also the final Tauri update. The Tauri updater will not switch you to Electron; choose a **VoiceStudio-Electron** installer above. Legacy Tauri assets remain available for existing installations.

1. Close Tauri and back up its entire data directory, plus any reference audio stored elsewhere.
2. Install Electron and check its storage/backend configuration points to your existing data before generating. Never run both apps against that directory at once.
3. Verify your voices, projects, history, and model locations; generate a short clip before removing Tauri.
4. Recheck devices, shortcuts, theme, backend address, permissions, and credentials. Desktop preferences and credentials are not guaranteed to transfer.

[Read the migration guide](https://github.com/debpalash/VoiceStudio/blob/v0.5.3/docs/electron-migration.md) · [Compare all changes since v0.5.2](https://github.com/debpalash/VoiceStudio/compare/v0.5.2...v0.5.3)

### Changed

- Electron becomes the primary desktop app; Tauri retains a separate final update path (#2157)
- Workspace sidebars resize and remember their width; video previews show thumbnails and keep playback controls in view (#2129)
- Model Catalogue groups speech, transcription, and language models with engine details and downloadable weights together (#2013, #2020)
- Models and voice previews move to Settings → Storage; the Hugging Face mirror moves to Network (#2013)
- Integrations gets a searchable workspace covering 100+ tools, with provider details and configuration guidance (#2129)
- Support pages gain donation cards, a workspace shortcut, and sponsor contact details (#2129)
- README adds an Electron UI tour and refreshed screenshots; installable agent skills follow the new desktop workflow (#2129, #2157)
- README explains the desktop transition and keeps contributions welcome (#2153) — thanks @cyberspace-cs!

### Added

- VoxCPM2, MOSS-TTS-Nano, and CosyVoice 3 install in isolated environments without disrupting other engines (#2021, #2022, #2025)
- Remote workers report CPU, GPU, and memory usage; unavailable readings stay distinct from zero (#2155) — thanks @velixio!
- Dubbing translation shows live logs, supports cancellation and retries, and remembers custom tone instructions (#2129)

### Fixed

- Older NVIDIA GPUs, including Tesla T4, no longer kill the backend on first generation (#2135) — thanks @Shivendra-Coherent!
- Disabling torch.compile works across desktop platforms and through the environment override; native crashes leave diagnostic stacks (#2135) — thanks @Shivendra-Coherent!
- Dubbing keeps short segments proportional, supports timeline zoom, and removes duplicate transcription context (#2129)
- Dubs preserve original sound outside dialogue, keep replacement speech complete, repair missing speech caches, and reject incomplete output (#2129)
- Dubbing demos keep playback aligned across languages and can open a sample in the editor (#2131, #2157)
- Pressing Play before a video finishes loading now starts it when ready (#2129)
- Native dictation, watch folders, and Wayland shortcuts share desktop contracts; focused paste stays ordered (#2122)
- macOS sidebar controls clear the window buttons; Linux and Windows sidebar headers expand and collapse consistently (#2126, #2129)
- Stopping an already-exiting process on macOS no longer reports a permissions failure (#2032)
- YouTube bot-check errors explain how to supply signed-in cookies in Dub (#2036, #2034) — thanks @celvintr!
- Engine startup failures distinguish timeouts, crashes, and invalid responses (#2037, #2026) — thanks @dajiaohuang!
- PyTorch Whisper transcribes M4A files and uses a model-appropriate VRAM budget on 6 GB NVIDIA cards (#2042, #2039, #2044, #2041) — thanks @xabiherdz-svg!
- MCP transcription waits follow the backend timeout instead of failing after 120 seconds (#2043, #2040) — thanks @xabiherdz-svg!
- CosyVoice 3 dependency updates address five security advisories (#2030, #2031)

### CI

- Release publication waits for platform artifacts and checksums; unsigned Electron builds require an explicit owner dispatch (#2029, #2157)
- Desktop integration checks cover current dubbing, navigation, and model workflows; worker teardown tests tolerate slower Windows runners (#2157, #2038)

### Contributors

- @debpalash — Electron migration, redesigned workspaces, release engineering, and integration of community fixes.
- @Shivendra-Coherent — the older-NVIDIA generation fix and compile/crash diagnostics (#2135).
- @velixio — remote-worker telemetry and reliability improvements (#2155).
- @cyberspace-cs — documentation for the Electron transition (#2153).
- Thanks to @ShimeKano, @celvintr, @dajiaohuang, and @xabiherdz-svg for the bug reports behind this release's GPU, download, startup, transcription, and MCP fixes.
- Dependency updates supplied by @dependabot[bot] (#2030, #2031).

## [0.5.2] — 2026-09-10

**Highlights**

- Show estimated and measured model, dependency, cache, and temporary disk costs in the engine catalogue (#1718)
- Preview builds now stay newer than Stable even when automatic post-release version bumps are disabled (#1762)
- CosyVoice setup guidance now separates downloaded model files from the runtime that makes the engine available (#1761)
- MCP tools can now keep audio out of agent context by returning files and accepting base-path-confined file inputs (#1760) — thanks @agudmund!
- Studio gains a Convert method: re-say any clip in one of your saved voices, speech to speech, fully local (#1765) — thanks @mvanhorn!
- Hardsub video export gains an opt-in karaoke word-highlight caption style (#1764) — thanks @mvanhorn!
- The dub editor gains a casting board: drag voice chips onto speakers, dropdowns stay in sync (#1767) — thanks @mvanhorn!

### Changed

- New installations default to Gemini 3.1 Flash TTS, avoiding local TTS checkpoint downloads until a local engine is explicitly selected. — thanks @TheOneironaut!
- The Gemini Windows edition stays on its dedicated rolling MSI instead of consuming standard upstream updater manifests. — thanks @TheOneironaut!

### Added

- Gemini 3.1 Flash TTS Preview is available as a native preset-voice engine with persistent immediate and provider-batch jobs. — thanks @TheOneironaut!
- The dub CAST strip expands into a project-level casting board: drag voice chips (clone profiles, design presets, Default) onto speaker rows — or pick from a keyboard listbox — writing the same per-speaker cast fields as the existing dropdowns (#1767) — thanks @mvanhorn!
- Studio's new Convert method turns a dropped or recorded clip into an existing voice profile's voice, with optional source-duration matching (#1765) — thanks @mvanhorn!
- Hardsub export can now burn karaoke word-highlight captions: an opt-in Line | Karaoke control renders a word-timed ASS sweep from timings persisted at transcription, with an even-split fallback for older jobs and translated tracks, plus a `GET /dub/ass/{job_id}` sidecar (#1764) — thanks @mvanhorn!
- Windows releases now include an independently updatable per-user MSI that installs and uninstalls without elevation (#1713)
- Engine status and diagnostic bundles now record loaded execution provider, device, precision, fallback stage, accelerator identity, runtime versions, and parent-process memory visibility (#1717)

### Docs

- The Gemini TTS guide covers API-key setup, voice selection, long-form resume, provider batch, and upstream synchronization. — thanks @TheOneironaut!
- Local gigastt is now documented as a supported OpenAI-compatible ASR endpoint, with loopback privacy distinguished from remote servers (#1736) — thanks @ekhodzitsky!
- The CosyVoice guide now states that packaged builds have no one-click runtime installer and records the exact readiness checks exposed by [Discussion 1631](https://github.com/debpalash/VoiceStudio/discussions/1631) (#1761)
- A production private-API guide now covers pinned containers, root credentials, network isolation, streaming proxies, health checks, upgrades, and benchmark evidence (#1720)
- RX 6700 XT/gfx1031 over WSL2 ROCDXG is now explicitly unverified until a published end-to-end GPU workload proves the mapped path (#1716)

### Fixed

- OpenAI-compatible ASR now requires HTTPS outside loopback and refuses redirects so audio stays on the configured origin (#1736)
- Windows isolated engines now retain direct Job ownership without an extra Python supervisor process that can deadlock the child loader (#1734)
- The setup splash now waits through the backend's full startup budget instead of reporting slow Windows CUDA initialization as stuck after two minutes (#1749)
- Dubbing jobs can now reuse every source-language code produced by automatic ASR detection without a 400 error on the next upload (#1737)
- Incomplete Sherpa-ONNX model snapshots now self-repair before recognizer startup instead of failing on a missing ONNX file (#1733)
- OmniVoice subprocess startup now allows slow packaged Windows Python runtimes to signal readiness before termination (#1711)
- SRT files selected during source analysis now wait for speaker cloning, then replace transcript text without losing voices (#1709)
- Windows MSI deployments can now prohibit WebView2 bootstrap with `DISABLEWEBVIEW2BOOTSTRAP=1`, and `AUTOLAUNCHAPP=0` reliably suppresses first launch (#1714)
- Subtitle rows now provide 100 ms timing steppers and flag adjacent overlaps without requiring precise timeline dragging (#1710)
- Repair-sync failures now retain uv's final dependency error instead of reporting only an opaque exit status (#1705)
- YouTube ingest now retries yt-dlp's transient “page needs to be reloaded” response (#1706)
- Dictation model readiness now follows the live Hugging Face cache selected in Settings (#1707)
- Dictation capture now queues native events whenever its webview listener unmounts or reloads instead of emitting them to nobody (#1707)
- Desktop-contained backends now exit when their owning app disappears instead of surviving as stale port-3900 processes (#1707)

## [0.5.1] — 2026-08-28

**Highlights**

- OmniVoice generation on Apple Silicon now runs in a crash-isolated child, so fatal MPS memory exits no longer take down the local backend (#1697, #1698) — thanks @ndntran14!
- Model-load GPU exhaustion now returns a sanitized, actionable dubbing error, and readiness correctly attributes the shared model status to TTS (#1695)
- Source-mode development now restarts an isolated backend crash without tearing down the UI, while repeated crash loops still stop loudly with diagnostics (#1690)
- Dubbing playback now keeps an audible companion source when a WebView can render the preview picture but cannot decode its audio (#1692)
- Model Catalogue engine rows now use the available desktop width and keep identity, runtime state, and actions from crowding one another (#1689)
- VoiceStudio now acts as a local speech platform: other apps can trigger its native dictation or connect through versioned HTTP, WebSocket, JSON-RPC, CLI, and MCP transports (#1646)
- A timed-out in-process dub transcription no longer starts a second WhisperX/CTranslate2 call over the abandoned native worker, preventing the overlapping access that preceded Windows `0xC0000005` exits (#1669)
- Windows debugger termination code `0x40010004` is no longer misreported as a backend crash or charged against automatic restart recovery (#1663)
- Studio now keeps one generation reservation across page changes, preventing a remount from stacking native jobs until the backend reports capacity busy or is killed under memory pressure (#1670)
- Uploaded dubbing videos are normalized to browser-safe H.264/AAC before preview, preventing valid VP9, AV1, or Opus media from failing with “no supported sources” (#1644)
- Dubbing now separates spoken and target languages, preserves translations through segment cleanup, and lets failed translations be retried or skipped without restarting the batch (#1654) — thanks @Number16BusShelter!
- Importing replacement SRT subtitles now keeps each cue bound to the best-overlapping source speaker and clone instead of resetting every line to a random default voice (#1660) — thanks @invio-a11y!
- Uploading a Dub preview no longer blocks every backend request while ffmpeg extracts its audio (#1667) — thanks @tfreyd!
- Docker quick starts now require the administrator key needed through container NAT instead of starting a UI whose protected actions return 403 (#1651) — thanks @wd357dui!
- WSL2 AMD containers now use the `/dev/dxg` ROCDXG bridge with actionable GPU diagnostics instead of silently falling back to CPU (#1655) — thanks @wd357dui!
- Ad-hoc voice-clone references now stay alive until cancelled or timed-out GPU work actually stops reading them, so prompt caching can finish instead of failing on a deleted temp file (#1668) — thanks @tfreyd!
- Dictation now stays bound to the app where it started and recovers locally from silent recognizer output (#1175)
- The backend now answers within a second of launch and narrates its startup step by step (#1550)
- Reporting a bug from an outdated build now offers the latest release first (#1547)
- The backend is only announced ready once it can actually serve, and crash-loop restarts now pace themselves (#1548)
- Invisible watermarking no longer stalls — or silently skips — the first take of a session (#1615)
- Dub subtitles can be retimed, inserted, and merged in either direction from the segment table (#1612) — thanks @invio-a11y!

### Changed
- Model Catalogue now uses one breathable workspace canvas with simpler pane and engine-family navigation instead of nested cards and scroll regions (#1685)
- Linux source launchers now catch missing libxdo and GStreamer audio plugins before they can cause a linker error or an aborted, blank WebKit renderer (#1680, #1682)
- Dictation now carries one native output session from shortcut-down through final delivery, restores text, HTML, image, or file-list clipboards only when untouched, keeps Wayland copy-safe unless current-focus insertion is explicitly enabled, and retries silent Sherpa speech only through an already-installed local ASR model (#1175)
- The backend binds its port immediately and reports startup progress live — `/health` answers 503-with-step and a new `/startup/progress` endpoint lists every step while PyTorch, API routes, and database migrations load in the background, so "starting at step X" is never mistakable for "dead"; the desktop splash narrates each step (#1550)

### Added
- A bundled Rust loopback sidecar exposes dictation start/stop/toggle, focused-output sessions, discovery, and JSON-RPC; the backend adds versioned streaming events and a dependency-free CLI bridge for Herdr, coding agents, editors, desktop apps, and TUIs (#1646)
- Headless NVIDIA and ROCm machines can now join as worker-only Docker Compose services with no published UI and durable protocol-v2 enrollment; update both machines together before reconnecting (#1638) — thanks @jkrogers9862!
- Linux ARM64 (Asahi Apple Silicon) support for the OmniVoice GGUF engine — a `linux-aarch64` binary built with GGML Vulkan where the toolchain allows it, so Apple GPUs accelerate generation through the open-source Honeykrisp driver instead of falling back to CPU-only (#1641)
- One-command install on every desktop OS: `curl -fsSL https://voicestudio.sh/install | sh` (macOS/Linux/WSL) or `irm https://voicestudio.sh/install | iex` (Windows) — the URL serves the right script per platform, and Windows gains a source installer (`scripts/install.ps1`) with a 3-OS CI smoke (#1626)
- Per-line subtitle management in the dub table: a line's end time is editable alongside its start (typing a time and dragging its timeline edge now take the same path), lines merge with the previous row as well as the next (`Ctrl/Cmd+Shift+M`), and a new line can be inserted into the gap after any row (#1612) — thanks @invio-a11y!
- CI now enforces performance regression budgets on the hot paths — operation-count tests pin streaming TTS to one synthesis per sentence and cached dub re-mixes to zero re-synthesis; fast-path guards cover zero re-decoding and ⌈N/W⌉ native batch calls when enabled (#1594)
- Default-engine dubbing now synthesizes several segments per forward pass instead of one call per line — the width follows the host's device headroom (1 on CPU and low-VRAM cards, up to 8), `OMNIVOICE_DUB_BATCH_WIDTH` overrides it, and engines without native batching keep the single-segment path (#1594)
- `/ws/tts` now reports real time-to-first-audio, and its RTF measures synthesis alone so a slow client can't inflate it (#1594)
- The locally cached AudioSeal watermark generator warms on a background thread ~35s after boot (`OMNIVOICE_PRELOAD_WATERMARK=0` opts out; explicitly setting `=1` may download it), so the first synthesis no longer serializes the audioseal import + model load inline — measured at ~42s on a cold filesystem, 3s short of a 90s client timeout (#1576) — thanks @paoloantinori!
- Voices you've cloned stay "warm" across restarts — encoded references now persist to disk (~10 KB each), so the first generation of a session skips the re-encode and any transcription pass; `OMNIVOICE_PROMPT_DISK_CACHE=0` opts out (#1565)
- Optional FlashInfer acceleration for the default engine on CUDA (`OMNIVOICE_FLASHINFER=1`, ~2.2x measured) — needs the optional `flashinfer-python` package; missing package or kernel failure logs why and falls back to the standard path (#1565)
- The bug reporter notices when you're on an outdated build and offers the latest release before filing — with a "File anyway" escape hatch — and stamps a `Build status` line into every report so up-to-date reports are tellable from stale ones (#1547)
- Settings → Performance & Device gains a compute-device override (Auto / CUDA / ROCm / XPU / MPS / CPU, or `OMNIVOICE_DEVICE`) — pin the device when auto-detect picks wrong; only devices your machine actually has are offered (#1557)
- Opt-in 24-layer PocketTTS checkpoints via `OMNIVOICE_POCKETTTS_24L` — better prosody for it/de/es/pt at roughly 2x render time (still faster than real-time); the fast 6-layer model stays the default (#1613) — thanks @paoloantinori!

### Docs
- Supported-version and install guidance now identifies 0.5.1 as the stable desktop and container release (#1687)
- The Docker Hub overview now shows the current engine-switching demo, Model Catalogue, and gallery voice workflow (#1593)
- The Docker Hub overview and install guide now show the v0.5 tags and the built-in API-key/share-PIN security model instead of obsolete v0.4 and no-authentication guidance (#1592)
- The READMEs now lead with download buttons and a three-step first-clone walkthrough, and a new benchmarks page anchors measured per-engine/per-device numbers on the in-repo harness (#1555)
- Every engine now has its own guide — 21 new pages under docs/engines plus an index covering all 16 TTS and 11 ASR engines, linked from both READMEs (#1556)
- The OmniVoice guide now covers combining style attributes with a reference clip (consistent instruct stabilizes cloning; the reference wins conflicts), inline pronunciation control (pinyin / CMU phonemes), and corrects the claim that the default engine can't do voice design — it can, from attributes (#1565)

### Fixed
- Workspaces now measure their responsive width when the post-bootstrap shell actually mounts, so native UI scaling reflows Projects and History instead of crushing the Dubbing demo into unreadable columns (#1683)
- Dubbing keeps the source-language selector visible after a local file is chosen, so ASR can be pinned before transcription starts (#1678) — thanks @Lonki-lomki-cloud!
- First-run media-engine downloads become available to TTS immediately without a restart, and missing media-process failures now point to repair controls (#1677) — thanks @farhataligpt-dev!
- Source installs on AMD GPUs honour `OMNIVOICE_TORCH_VARIANT=rocm`: `bun run desktop` now swaps in the ROCm torch wheel after `uv sync` and launches the backend without re-syncing, instead of silently reverting to the CPU-only CUDA build on every start (#1665) — thanks @uberclokr!
- `bun run desktop` on a fresh clone no longer fails with "resource path `../../frontend/dist` doesn't exist" — the dev launcher creates the placeholder Tauri resource directory before compiling (#1664) — thanks @uberclokr!
- macOS no longer loses TTS after the first request when Python lacks `os.waitid`; subprocess ownership now uses a safe `waitpid` fallback without risking reused process groups (#1656) — thanks @paoloantinori!
- Desktop startup, Retry, reset, uninstall, shutdown, and crash recovery now share one backend lifecycle owner; quitting interrupts first-run installers and gracefully drains then force-cleans the full backend process tree, so overlaps cannot duplicate or orphan it (#1635) — thanks @Xohaibxobi!
- Large Stories and Audiobook projects now persist in IndexedDB instead of overflowing the `omnivoice.app` localStorage envelope, with quota-safe migration and orderly exit/reload flushing (#1636) — thanks @leodzai!
- OmniVoice and its crash-isolated subprocess now route to AMD ROCm GPUs instead of warning and falling back to CPU (#1629) — thanks @j4r3kb!
- Dictation now cancels pending startup work, capture resources, sockets, and timers when the capture widget closes, preventing late work against a destroyed webview (#1645)
- Streaming generation failures now show recognized recovery guidance and appear in Diagnostics instead of only returning a generic error (#1607)
- The worker-capacity transport test no longer races its own setup: the 1-slot limit now goes through the enrollment handshake instead of mutating client config after connect, where the server's stream-open ConfigUpdate (carrying the registered capacity of 2) could overwrite it and fake an over-accept; failed CI twice on 2026-08-21 (#1630)
- Moving words across a speaker boundary in a dub — merging two lines and splitting them again — no longer dubs the second half in the first speaker's voice; each half now keeps the speaker, voice, direction, gain, and language of whoever actually says it (#1612) — thanks @invio-a11y!
- Dictation on a WebView that refuses a 16 kHz audio context (WKWebView) now low-passes before downsampling, so frequencies above 8 kHz stop folding into the speech the recognizer is fed (#1610)
- A microphone context that cannot be resumed now reports a mic error instead of leaving the dictation pill on "Listening" while capturing nothing (#1610)
- Dictation no longer retains a whole session's audio for silent-model recovery — an open mic grew that buffer by ~115 MB an hour; the recent two minutes are kept instead (#1610)
- The clipboard-delivery status is now translated in all 21 languages, so Wayland users — where clipboard delivery is the default — no longer see an English string (#1610)
- A native sherpa-onnx load failure of any exception type now degrades to "engine unavailable" instead of taking the dictation WebSocket down (#1610)
- Dictation now ships Whisper Tiny as its one cross-platform default, avoiding Parakeet's measured empty decoding on Windows while keeping Parakeet selectable behind runtime fallback (#1175)
- Re-mixing a dub no longer decodes, rewrites, and re-reads every cached segment — same-rate cached audio is reused directly (and rejected if truncated), switching timing modes can't reuse slot-truncated audio as natural-rate, and RVC respects natural-rate modes (#1594)
- PocketTTS French works again — pocket-tts only ships a 24-layer French model and rejected the name the sidecar asked for, so every French request failed at model load; French now always loads `french_24l` (#1613) — thanks @paoloantinori!
- Installing IndexTTS 2.5 no longer fails claiming an interrupted download — the weights repo ships `config.yaml` and VoiceStudio demanded a `config_v2_5.yaml` that exists in no upstream release; both names are accepted, so a hand-renamed checkout keeps working (#1611) — thanks @zuiaiyutu!
- IndexTTS 2.5 no longer has long-text generation killed at 60 seconds — the sidecar now proves it is alive every 5 seconds while `infer()` runs, and its deadline rises to 900s (`OMNIVOICE_INDEXTTS_RECV_TIMEOUT_S`) (#1611) — thanks @zuiaiyutu!
- The OpenAI-compatible `/v1/audio/speech` route now reuses the shared cached engine for explicit `model` ids instead of constructing a fresh engine — and its sidecar/model load, a ~28s floor per call for subprocess engines — on every request, with the same single-engine-resident discipline `/generate` applies (#1614) — thanks @paoloantinori!
- The setup wizard's RAM check no longer blocks 8 GB machines whose OS reports ~7.8 GB usable — the thresholds now tolerate reserved memory, and `OMNIVOICE_RAM_PREFLIGHT=0` turns a genuine block into a warning for those who accept the OOM risk (#1618)
- Invisible watermarking now runs eagerly instead of through `torch.compile` — AudioSeal's lazy compile sent the first embed of every session into Inductor's C++ codegen, which failed outright on macOS hosts whose toolchain couldn't serve it and shipped the audio unmarked after a 30-40s wait; first embed drops from 9.70s to 0.26s (#1615) — thanks @paoloantinori!
- The macOS Accessibility blocker now rechecks while visible and closes as soon as the grant is enabled instead of keeping a stale permission prompt on screen (#1609)
- The dubbing editor's video and transcript columns can now be resized by pointer or keyboard, and the chosen split persists across launches (#1571) — thanks @invio-a11y!
- CPU-only synthesis now gets a bounded ten-minute execution budget, and a render that exhausts it is reported as a compute timeout instead of misleading "generation capacity is busy" queue pressure (#1588) — thanks @ChienNguyen1111!
- Rapid Launchpad ↔ Dub navigation now replaces the workspace DOM owner cleanly, so late media/waveform cleanup cannot trigger React's `insertBefore` crash (#1590) — thanks @nicolas-jacques!
- Watermark embedding failures now log the full traceback instead of just the exception message, so a silently-unmarked-audio incident (audio passes through unmarked by design) is diagnosable from the log alone (#1576) — thanks @paoloantinori!
- Dubbing now recovers rapid two-speaker exchanges when diarization collapses them, defaults new projects to lip sync without overwriting saved timing choices, and keeps the editor usable on narrow screens (#1584) — thanks @victordonat0!
- `OMNIVOICE_ASR_BACKEND=omnivoice` now selects the PyTorch-native Whisper path, so the documented ROCm escape hatch no longer fails as an unknown engine (#1582) — thanks @patmansk!
- Network Sharing from Windows MSI/portable installs now serves the bundled web interface to LAN devices instead of redirecting them to their own `localhost` (#1589) — thanks @TWIISTED-STUDIOS!
- Exported dubbed videos now mark the dubbed language as the default audio stream while keeping Original available as an explicit choice (#1575) — thanks @invio-a11y!
- Cloning references can no longer exhaust system memory: transcript-free clips up to 75 seconds are searched in five bounded passages, longer clips ask to be trimmed, and supplied transcripts remain capped at 20 seconds to preserve alignment (#1578) — thanks @ACKAPOB!
- Stored artifact subpaths now resolve after moving a data directory between Windows, macOS, Linux, and Docker, while traversal and symlink escapes remain blocked (#1559) — thanks @Eman-Yousaf!
- A remote browser hitting an API-key-configured server's admin 403 now gets the API-key login form instead of endless console 403s, while desktop and PIN-only/no-key servers keep the plain loopback error so guests are never offered a login no key can satisfy (#1568) — thanks @paoloantinori!
- The crash-isolated ASR sidecar and its download preflight now agree on which model to load — setting the shared faster-whisper model variable applies to both variants instead of the sidecar quietly using a different one (#1556)
- "Ready" now requires the deep health probe (a working database-backed route), not just the identity probe — a backend whose install broke underneath can no longer be announced up while every real request fails (#1548)
- Supervisor restarts after repeat crashes now back off (immediate, then 5s, then 15s) instead of respawning back-to-back, so a tight crash loop can't burn the whole restart budget in seconds (#1548)
- The Linux desktop cleanup regression test now isolates build artifacts, so an existing developer build can no longer change its result (#1566)

- Renaming, deleting, or revoking consent on a voice (and starring/clearing history, recording exports) now live-updates every open tab again — the sync routes' WebSocket events were silently dropped, which could look like "all my voices are gone" (#1561) — thanks @paoloantinori!

### CI
- Project agents now share pinned Vite and FastAPI skills from skills.sh (#1594)
- Weekly full-history secret scans no longer mistake the Ed25519 private-key type name for committed key material (#1591)

## [0.5.0] — 2026-08-13

**Highlights**

- The app is now **VoiceStudio** (previously OmniVoice-Studio) — one waveform-and-spark identity across the app, docs and installers. Your data folder, settings and Docker image paths stay put.
- **Model Catalogue** — engines and models in one workspace: every TTS, transcription and LLM engine with its device routing and install state, defaults picked there.
- Switch TTS, ASR and LLM engines from the status bar or any workspace — ready-only choices, memory status, environment-pin protection, `Ctrl/Cmd+E`. (#1530)
- Lend another machine's GPU with a join code and a QR scan — a Compute control in the status bar picks where jobs run, and several people can share one GPU box with revocable, certificate-pinned connections. (#1516, #1496)
- Server mode is locked down: admin actions require an API key (#1525), and the remote UI exchanges it for short-lived sessions that never sit in browser storage or WebSocket URLs (#1528) — thanks @bultodepapas!
- A faster, cleaner Dub workspace for multilingual production, with a production command bar and per-language cards. (#1489)
- The demo audio and video the app always advertised now actually ship, rendered by VoiceStudio's own engine. (#1517)
- Dictation works on Wayland now — the portal shortcut actually fires (#1490, #1526) — and the recording pill is back on every desktop.
- The Launchpad wears the project's signal-field waveform artwork over a quieter, borderless layout. (#1533)
- The catalogue reads as headroom, not breakage: available engines sort first, uninstalled ones say what they need (#1531), and the LLM row names the provider that actually answers (#1538).
- Gallery voices can be saved as local profiles — audio lands in your profile store with validated, content-addressed references. (#1542)

<img src="https://raw.githubusercontent.com/debpalash/VoiceStudio/main/docs/media/0.5.0/quick-switch.gif" alt="Switching TTS engines from the status bar" width="820" />

| The Model Catalogue | The Voice Gallery |
| --- | --- |
| <img src="https://raw.githubusercontent.com/debpalash/VoiceStudio/main/docs/media/0.5.0/catalogue.png" alt="Model Catalogue — engines pane" width="420" /> | <img src="https://raw.githubusercontent.com/debpalash/VoiceStudio/main/docs/media/0.5.0/gallery-save.png" alt="Voice Gallery — save a voice as a profile" width="420" /> |

### Changed

- Gallery personas now preview through the local backend, retain their complete voice-design recipe, and open directly in Voice, Stories, or Audiobook. (#1542)
- Typing and large workspace edits no longer serialize and rewrite persisted documents on every input; writes are coalesced off the interaction path — thanks @bultodepapas! (#1541)
- Support amount choices now use every theme's shared card, accent and focus tokens. (#1530)
- Sponsoring, commercial licensing and getting in touch are one page now. They answered the same question between them and each used to live somewhere else, so they are three sections on a single scroll — the footer heart, the commercial-licence links and Contact all land on it, at the section you asked for. (#1522)
- Model Catalogue switches panes with tabs instead of a two-state toggle, and the Engine Compatibility Matrix's TTS / ASR / LLM switcher is now tabs too — arrow-key navigable, and each tab still shows the engine it would use. (#1522)
- Engines you can actually use sort to the top of the compatibility matrix, and an unavailable engine's name recedes instead of the whole row fading — the status badge and GPU chips that say *why* it is unavailable stay legible. (#1522)
- Remote workers reads as a device list: status dot, address, latency, a live task meter, resident models and last-seen per machine, with housekeeping actions revealed on hover and a three-step empty state. (#1516)
- The GPU picker and the new status-bar control paint their status dots and menu surfaces from themed tokens instead of fixed palette classes, so they stop showing Gruvbox colours on Midnight and Catppuccin. (#1516)
- Dictation shows the pill again: a capture puts a small always-on-top capsule near the bottom of the screen you are working on — listening, transcribing, the result, and any error — and takes it away when the session ends. It never takes focus, so the text still lands in the app you were typing into. On Wayland the compositor decides where it sits; everywhere else it is bottom-centred.
- Engines and models moved out of Settings into a new Model Catalogue workspace, reachable from the icon rail (or the title-bar tabs); Settings → Engines and Settings → Models now point there, and Settings keeps the models directory and Hugging Face mirror.
- The Settings sidebar is keyboard-navigable: ⌘K / Ctrl+K jumps to the filter, ↑/↓ and Home/End move between categories, and Enter or ↓ from the filter drops into the list. Matching text in a filtered category name is highlighted, and group headers stay pinned while the list scrolls.
- The Launchpad has a quieter, more spacious look: borderless feature tiles that light up on hover or keyboard focus, plain-numeral counts, hairline section rules, and one shared page column for the hero, tiles, recent files and project lists.
- Linux release smoke now validates linuxdeploy's wrapped custom launcher instead of rejecting a healthy AppImage. (#1506)
- Remote GPU workers render audiobooks chapter by chapter, with automatic per-chapter local fallback and one combined notice if the worker drops out. (#1478)
- Remote GPU workers can now run a job to completion: long renders no longer die at two minutes, a worker that drops and reconnects mid-render keeps its work, and a timed-out job no longer takes the worker offline for good. Placing a job still needs the development-only `POST /workers/tasks`; wiring the app's own Synthesize button to it comes next.
- Voice, Stories, Audiobook, Gallery, Settings, profiles, and Launchpad now use compact, responsive layouts with accessible controls. (#1491)
- Dubbing's Generate Dub, Verify, and Export actions now use a compact hierarchy with visible labels, responsive reflow, and motion-safe feedback. (#1493)
- The Dub workspace now has a compact production command bar, responsive flag-based language cards, media previews in Dub History, and a narrower Projects rail. (#1489)
- VoiceStudio now uses one waveform-and-spark mark across the title bar, About screen, README, browser favicon, and every desktop/platform icon. (#1487)
- PocketTTS now asks you to review its code license, model license and gated-access conditions before first use, and explains how to unlock the model instead of showing a raw download failure — thanks @paoloantinori! (#1442)
- The repository moved to github.com/debpalash/VoiceStudio. Every link in the app, docs and scripts now points there; GitHub redirects the old URLs, and the Docker image paths, the app bundle identifier and your data folder are all deliberately unchanged. (#1394)
- The app is now **VoiceStudio** (previously OmniVoice-Studio). Only the name you see changes — your data folder, settings and the Docker image paths stay put, so upgrading needs nothing from you. On Linux the .deb is now `voicestudio`; remove the old `omnivoice-studio` package once.
- macOS floor raised to 13.3 (Ventura) — the frontend has required Safari 16.4 for some time, so macOS 12 was a promise the stack could not keep (#1268)
- The first-run setup screen no longer overpromises. It claimed "no account, no cloud, no telemetry" without qualification — untrue for anyone who opts into analytics — and now says what actually holds either way: your voices, recordings and projects never leave the machine, and no processing happens in the cloud.
- Dictation no longer shows a floating pill. The hotkey records, transcribes and pastes with nothing on screen; the tray icon still marks recording, and anything needing your attention (Accessibility, microphone, a failed transcription) now arrives as a notification in the main window.

### Added

- Gallery personas preview through the local backend, keep their full voice-design recipe, and open directly in Voice, Stories, or Audiobook — and can be saved as local profiles with validated audio references. (#1542)
- The demo audio the app has always advertised now actually ships: previews for all seven voice-design presets, the three dictation replay clips, and the dubbing demo's source video plus four dubbed languages with subtitles. Every one of those was a dead link before — the tooling that renders them required macOS, so on Windows and Linux the files were never built. (#1517)
- Demo assets are rendered by VoiceStudio's own engine, so the tooling runs wherever the app does, and the demos are made by the thing they demonstrate. (#1517)
- A machine can now join a control plane from the app: Settings → System → Remote workers → **Lend this machine's GPU**, paste the join code, done — no environment variables and no restart. The address travels with the code, so the machine reconnects on its own afterwards. (#1516)
- Join codes and connection strings are shown as a **QR code** alongside the text, with a live expiry countdown — scan it from the other machine instead of retyping forty characters. (#1516)
- A **Compute** control in the status bar: pick local or a remote machine, turn remote workers on or off, and mint a join code without opening Settings. It appears only once you have opted in or enrolled a machine. (#1516)
- A worker waiting for approval can be approved from its row. The panel labelled that state before but offered no way out of it. (#1516)
- **Model Catalogue** — a workspace of its own for engines and models: browse every TTS, transcription and LLM engine with its device routing and install state, pick the default for each, and install or remove model weights, all from one screen instead of two Settings categories.
- Remote GPU machines can now accept connections instead of dialling out, so several people can use the same box at once — each gets their own revocable connection string, with certificate-pinned TLS, a live list of who is connected, and a disconnect button. (#1496)
- Remote GPU model downloads now use the normal Models install flow and show per-worker progress. (#1478)
- Settings → System → **Remote workers** sends individual jobs to GPUs on your other machines while everything else stays here. Off by default; each machine is added with a singl…42288 tokens truncated…es the
  existing local-first, user-reviewed report stricter. (#856)

- **A hung TTS generate can no longer brick the backend ("Can't reach the local
  backend").** A GPU job that wedges on some Windows + CUDA setups occupies its
  worker forever — Python can't cancel the thread — so on the 1–2 worker pools we
  ship, one stuck job starved every other request and the next action surfaced as
  the misleading "Can't reach the local backend" even though the process was
  alive. ASR/dub/model-load already bounded and reset the pool on hang (#730); but
  **every generate path** — Studio synthesis, the streaming path, batch, the dub
  per-segment + preview render, archetype previews, and the OpenAI-compatible
  `/v1/audio/speech` API — was still an unguarded GPU dispatch, and the residual
  reports all failed on `generate:start (audio)`. Every one is now bounded by the
  same wall-clock guard (`OMNIVOICE_GENERATE_TIMEOUT_S`, default 300s) that
  abandons the wedged worker and rebuilds the pool, so capacity is restored
  automatically and you get an actionable timeout instead of a dead backend.
  Closes the whole class of GPU-job-hang reports (#851 — #850, #802, #755, #723,
  #721, and the 0.3.7 cohort, all tracked in #730).

- **An unsupported GPU now falls back to CPU instead of 500-ing every generate.**
  When the installed PyTorch build has no kernels for your GPU's compute
  capability — a too-old card (Pascal / GTX 10-series) or a too-new one
  (Blackwell RTX 50-series on pre-cu128 wheels) — CUDA failed at launch with the
  cryptic `CUDA error: no kernel image is available for execution`. The backend
  now detects that up front and runs on CPU (slower, but it works), and any raw
  occurrence is reported as "your GPU isn't supported — switch to CPU or install a
  matching PyTorch," not a Flush-the-memory dead end. Force the GPU anyway with
  `OMNIVOICE_FORCE_CUDA=1`. (#756)

- **The "TRANSLATION FAILED" banner now dismisses and clears itself.** The Dub
  translation-error banner used to be sticky — it survived a successful re-try and
  never went away. It now has a close (×), auto-clears on the next corrective
  action (re-translating, changing the engine, or installing the package), and
  self-clears after a short timeout — fixing the whole class of translate/pipeline
  banners that outlived the state that caused them.

- **Dubbing a video URL no longer fails with "ffmpeg is not installed."** yt-dlp
  downloads video and audio as separate streams and muxes them with ffmpeg, but
  it only looked on PATH — so on Windows (where VoiceStudio's ffmpeg is a bundled
  sidecar / `imageio-ffmpeg` binary off PATH) the merge aborted before the dub
  could start. yt-dlp is now pointed at the same ffmpeg VoiceStudio resolves. (#712)
- **A synth that succeeded no longer 500s because of a history-logging hiccup.**
  If the local database somehow missed schema init, recording the clip to
  generation history failed with *"no such table: generation_history"* and
  surfaced as a 500 — even though the audio had already been generated and saved.
  The write now self-heals the schema and retries, and a history-logging failure
  never fails the generation: you get your audio regardless. (#710)
- **Long-video dubs no longer spike RAM during assembly.** Dub generation used
  to hold every segment's audio in memory until the whole track was mixed, so a
  50-video batch or a single feature-length dub could exhaust RAM and crash. Each
  segment now streams to disk as it's rendered and the final track is assembled
  from those files via a 30s-chunk memmap writer, keeping memory flat regardless
  of video length. Per-segment download WAVs and the final track stay correctly
  watermarked (marked once at synthesis, no double-mark), and zero/negative-length
  segments no longer crash the run. (#639)
- **A corrupt or wrong-architecture native component no longer masquerades as
  "out of memory."** A synth failure caused by a bad `.dll`/`.pyd`/`.exe` on
  Windows (`[WinError 193] %1 is not a valid Win32 application` — e.g. torch,
  ffmpeg, or an engine binary) was labelled *"ran out of memory — try Flush,"*
  sending users down the wrong path. It now says the component is corrupt or
  built for the wrong architecture and to reinstall/repair it. (#705)
- **A "[Errno 32] Broken pipe" mid-generation no longer poses as "out of
  memory."** When the desktop app that launched the backend closes or relaunches,
  the backend's output pipe breaks and a synth can fail with `[Errno 32] Broken
  pipe`. That was labelled *"ran out of memory — try Flush,"* which never helps;
  it now tells you the backend lost its pipe and to restart the app. (#715)
- **Settings content no longer sprawls or spills out of view.** The content
  column capped at 1280px, so on wide windows rows stretched edge-to-edge with a
  big empty gap between each label and its control ("too spread out"), and a few
  panels (API keys, the shared button rows, appearance scale) used rigid pixel
  widths that pushed controls past the card's padding on narrow content. Now the
  content sits at a readable measure (a single `--settings-measure` token), the
  shared button/badge rows wrap instead of overflowing, rigid widths can shrink,
  and rows decide whether to sit side-by-side or stack based on their **actual**
  width (a container query) — not the viewport, which the 168px nav rail skews.
  Everything stays inside its padding, edge to edge, on every width. (#696)
- **File drag-and-drop works on macOS again.** The app's drop zones use HTML5
  file drops, but Tauri intercepts OS drag-and-drop by default (`dragDropEnabled`)
  and swallowed the files before the webview saw them — most visibly on macOS
  WKWebView, and fully broken on macOS 26 (Tahoe), where dropping a file did
  nothing. Disabled the interception so the webview handles native HTML5 drops
  on every platform. (#700)
- **A misconfigured `OMNIVOICE_MODEL` no longer bricks model load with a 500.**
  A stale or leaked TTS *engine id* (e.g. `omnivoice`) reaching the model loader
  used to fail every launch with *"omnivoice is not a local folder and is not a
  valid model identifier."* It now self-heals — only a real HF repo id
  (`org/repo`) or an explicit local path is honored; anything else falls back to
  the default with a logged warning. Every consumer of the setting routes through
  the same resolver, so a bad value also can't silently disable model warm-up,
  mislabel the Settings checkpoint, or get baked into an exported persona bundle.
  (#693)
- **ASR no longer crashes the dub/transcribe preflight when CTranslate2's native
  library can't load.** On hardened kernels / newer glibc (e.g. WSL2) the
  CTranslate2 `.so` is rejected with *"cannot enable executable stack"* — an
  OSError the WhisperX/faster-whisper checks didn't catch, so it took down the
  whole preflight. They now report the engine as unavailable and auto-detect
  falls back to PyTorch-Whisper instead of dead-ending. (#692)
- **A wedged transcription can no longer take the whole backend offline ("Can't
  reach the local backend").** On some Windows + CUDA setups a whisperx/CTranslate2
  transcribe hangs hard and never returns. Because ASR shares a small (1–2 worker)
  GPU pool with TTS, one stuck worker starved every other request — so the next
  thing you did (often a TTS *generate*) failed with "can't reach backend" even
  though the process was alive. Two fixes: every transcribe path — whole-file
  (dub whole-file, batch, live dictation) **and** the chunked dub stream — is now
  wall-clock **bounded** like the dub QC / dictation / OpenAI paths already were;
  and on timeout the poisoned GPU worker is **abandoned and the pool rebuilt**, so
  capacity is restored without restarting the app. You still get an actionable
  message (Flush VRAM / pick a smaller ASR model) for the durable fix. (#730)
- **The stale-dub-session recovery now also covers the first upload/ingest, not
  just retry/import.** A dubbing job that vanished server-side during the initial
  transcribe flow showed the scary *"Job not found … report a bug"* toast; it
  now resets gracefully and invites a fresh upload, like the other paths. (#695)
- **In-app preview of finished audiobooks/stories now plays on Windows.**
  The preview decoded the entire render into one in-memory PCM buffer via Web
  Audio `decodeAudioData`, which fails on long-form `.m4b`/AAC under WebView2
  (`EncodingError: Unable to decode audio data`), and the blob-URL fallback can't
  play in a Tauri `<audio>` element — so nothing played. The fallback now uploads
  to the preview endpoint (ffmpeg-extracts a streamable WAV) and plays the HTTP
  URL, the same path video previews use. Short TTS previews are unchanged. (#653)

- **First-run setup splash no longer shows a raw `bootstrap.lines` key in English.**
  The log-line counter string was present in 4 locales but missing from the `en`
  reference, so English (and 16 other locales falling back to it) rendered the
  literal key instead of "{{count}} lines". Added it to `en`. Also removed 160
  dead `gallery.cat_*` keys (renamed to `archetypes.use_*` long ago) orphaned
  across 20 non-English locales, clearing the i18n orphan-key advisory.

- **Backend no longer hangs on startup (unreachable, no error) on Apple-Silicon Macs.**
  The MCP session manager could hang on its anyio task group during lifespan
  startup (observed on M1, #632); because that start was awaited before the server
  began serving, "Application startup complete" never fired and the whole backend
  was unreachable. The MCP start is now timeout-bounded (`OMNIVOICE_MCP_START_TIMEOUT_S`,
  default 30s) — a hang becomes a logged warning and the backend serves normally
  without MCP, instead of wedging. (#632)

- **Dubbing a URL no longer fails with `[Errno 22] Invalid argument` on Windows.**
  yt-dlp stamps the downloaded file's modified-time with the video's upload
  date; an out-of-range/invalid timestamp makes the `os.utime` call raise
  `[Errno 22]` and aborts the whole URL ingest. VoiceStudio downloads to a throwaway
  file and never uses its mtime, so it now skips the stamp entirely
  (`updatetime=False`). (#642)

- **Dubbing a YouTube link that 403s now retries with a different player
  client.** Some videos serve their formats signature-protected to the default
  player client, so the media download fails with `HTTP Error 403: Forbidden`
  even though extraction worked — and a plain retry keeps 403ing. The URL
  download now escalates the YouTube player client (tv → android → web_safari)
  on a 403, which commonly bypasses it, before surfacing the actionable error.
  (#625)
- **A synth glitch that produced unreadable audio is now caught instead of a
  misleading "out of memory".** A numerical glitch in the model (seen on Apple
  Silicon/MPS) could leave NaN/∞ samples, which wrote a WAV that then failed
  decoding with an opaque `ffmpeg returned error code: 183 / Invalid data` — and
  the generic error handler labelled it "ran out of memory". Non-finite samples
  are now sanitized to silence before any encode (so the WAV is always
  decodable), and a genuine decode failure is reported as "unreadable audio —
  Flush and regenerate", not OOM. (#629)
- **A silent startup hang now leaves a diagnostic instead of nothing.** On some
  setups the backend could load all model weights and then hang forever before
  "Application startup complete" — no error, no crash, an unusable app (reported
  as a Mac M1 hang after `Loading weights: 527/527`, #632). A startup watchdog
  now dumps every thread's stack to the error log if startup stalls past a
  window (default 5 min, `OMNIVOICE_STARTUP_WATCHDOG_S` to tune, `0` to disable),
  so the deadlock is captured rather than invisible. It's disarmed the instant
  startup finishes, so a normal (even slow-first-download) boot never trips it.
  (#632)
- **First-run demo voice is back.** The bundled demo clip
  (`backend/assets/samples/demo_voice.wav`) was a build artifact that never got
  committed, so it shipped absent — onboarding logged "Demo audio not found" and
  seeded nothing, leaving a brand-new install with an empty Launchpad and no
  `/demo_audio` route. The clip is now committed (it's already un-ignored and
  bundled via the Tauri `backend` resource), so first-run seeds the demo voice
  on every platform; onboarding still degrades gracefully (with a regenerate
  hint) if it's ever absent. (#621)
- **Multi-speaker dubbing: two speakers' turns merged onto one line are now
  split apart.** Segmentation groups words into sentences *before* diarization
  runs, so a back-and-forth exchange could land in a single segment; the speaker
  pass then only *relabelled* that segment with its majority speaker, losing the
  turn boundary (the second half of #486; the per-speaker voice auto-assign was
  fixed earlier in #490). A new post-diarization pass re-splits any segment whose
  words span more than one speaker at the word-level boundary, assigning each
  piece its own speaker. Single-speaker segments pass through **byte-for-byte
  unchanged**, so single-speaker dubs and their timing never move, and a lone
  mis-attributed word (diarization noise) is smoothed rather than causing a
  spurious split. (#486)
- **Designed voices saved with a bad style no longer render wrong or crash
  generation.** A designed voice could persist an `instruct` the engine
  validator rejects — either the literal `"[object Object]"` from an old build,
  or freeform prose typed into the style field — which made every generation or
  dub that used the voice fail with `Unsupported instruct items found in …`
  (surfacing to users as a 400/500 and, when it tore down mid-render, "Can't
  reach the local backend"). The previous fix only *blanked* `"[object Object]"`,
  which silently dropped the design — so an Indonesian **female** voice came out
  **male**. Now the stored instruct is sanitized down to valid tags at every
  seam (save, edit, and when a profile drives Generate or Dub), and when the
  stored value is unusable the tags are **rebuilt from the design's saved
  category picks (`vd_states`)** so the intended gender/age/pitch/accent survive.
  A migration (0007) heals existing poisoned profiles in place — no reinstall,
  no manual fix. (#550 #571 #594 #596)
- **"Transcribe stream dropped … Likely ASR backend failed to load" now shows
  the *real* reason.** When transcription failed to load its ASR model (the
  reported case was WhisperX on Windows — typically a faster-whisper /
  CTranslate2-cuDNN mismatch, a missing model download, or the torch-2.6
  weights-only VAD regression), the UI dead-ended on a generic "stream dropped"
  message with no actionable cause. Two root causes: (1) WhisperX loads lazily
  *inside* transcription, so the load failure was buried in per-chunk errors and
  retried on every chunk; the transcribe pre-flight now eagerly loads the ASR
  model (new `ASRBackend.ensure_loaded()`), surfacing the genuine cause once, up
  front, as a structured error. (2) Pre-flight and audio-load errors closed the
  SSE stream with a bare `error` and no terminal `done`, so the browser's native
  EventSource connection-drop could race and win against the structured error —
  discarding the real cause and falling back to the generic message; every
  terminal error now emits `done`, and the frontend latches the structured cause
  so a connection drop can't overwrite it. Net: WhisperX load failures are
  diagnosable instead of a silent dead-end. Fail-before/pass-after regression
  test included. (#578)
- **Dubbing: the PLAY button on the dubbed-video preview did nothing.** Same
  autoplay-policy trap that #510 fixed for the standalone audio player, but the
  dub editor's timeline player was missed. WaveSurfer builds its `AudioContext`
  at mount — before any user gesture — so on Windows WebView2 (and Linux
  Firefox/Chrome, Android Chrome) it stays `"suspended"`; `playPause()` then
  resolves with no sound and the preview just sits there. Every playback entry
  point in the dub timeline (the toolbar Play button and the per-segment "play
  this slot") now resumes the context via the shared `unlockAudio()` on the
  click before starting playback, and swallowed play() rejections are logged
  instead of hidden. A source-contract regression test pins the invariant so a
  future refactor can't quietly reintroduce a silent play path. macOS is
  unaffected (its context was never blocked). (#595)
- **Voice design: the script text field couldn't be expanded.** The Script
  textarea was a `flex: 1` item inside a flex column, so flex-grow recomputed
  its height on every reflow and snapped the user's drag back — `resize:
  vertical` is silently ignored on a flex-grown item in Chromium/WebView2. The
  field now owns its own height (starts taller, and the corner grip grows it
  reliably on every platform). (#595)
- **An interrupted model download now self-repairs instead of dead-ending.**
  When the VoiceStudio TTS cache was missing weight shards (the usual aftermath of
  an interrupted first download), the next synthesize failed with a 500 and a
  "delete the model and install it again" instruction — a manual dead-end. The
  backend now detects the truncated-cache error on load, re-fetches just the
  missing files via `snapshot_download` (already-present blobs are skipped, so a
  near-complete cache repairs in seconds and a healthy cache is never touched),
  and retries the load automatically. Offline mode (`HF_HUB_OFFLINE`) is
  respected — repair never makes a network call the user opted out of — and if
  the re-fetch still can't fix it, the actionable delete-and-reinstall message
  is preserved as the fallback. (#581) The repair now also **retries** the
  re-fetch (3 attempts, resuming each time) so a single transient blip — the very
  thing that interrupts a download in the first place — doesn't bounce you back
  to a manual reinstall; tune with `OMNIVOICE_MODEL_REPAIR_RETRIES`. And if a
  resume-repair still won't load — the signature of a *corrupt* file that kept
  its size, which a resume trusts and never re-fetches — it now **force
  re-downloads** the model files once before giving up, so even a bit-rotted
  cache self-heals without a manual reinstall. (#739)
- **Dubbing a YouTube URL no longer dies on a transient "Broken pipe."**
  Pasting a video link could fail outright with `download: Unable to download
  video: [Errno 32] Broken pipe` — a broken pipe raised while the write side of
  a pipe closes mid-stream (a killed ffmpeg merge child, a CDN reset during
  muxing). yt-dlp's own per-fragment retries don't cover that case, so a single
  transient blip aborted the whole ingest. The URL download now retries up to
  twice on broken-pipe / network-drop failures, wiping the partial download
  between attempts, and only surfaces the (already-actionable) "connection
  dropped — just retry" hint after the retries are exhausted. Unsupported links
  still fail fast with their own hint — no wasted retries. (#579, #598)
- **`No module named 'omnivoice'` on installs whose venv lost its editable
  record.** An interrupted or offline `uv sync` (common during an in-place
  upgrade) could install all dependencies yet never lay the editable install of
  the project's own `omnivoice` package — or an antivirus quarantine could
  remove it. The venv still started uvicorn, so the bootstrap's health gate
  passed it through, and the app only failed at the first generate/dub with
  `No module named 'omnivoice'`. The bootstrap now also verifies `omnivoice` is
  importable (via a cheap `find_spec`, no torch load) and forces a repair
  `uv sync` that re-lays the editable install when it isn't; the backend also
  resolves `omnivoice` from its bundled source tree at runtime as a safety net.
  No reinstall needed — relaunch and it self-repairs. (#564)
- **"cannot schedule new futures after shutdown" no longer breaks generate/dub
  after a slow first load.** When a model load timed out, the backend reset its
  GPU worker pool to recover — but several request handlers had captured the old
  pool object at import time and kept submitting to it, so every subsequent
  generate, dub, transcribe, or translate failed with `cannot schedule new
  futures after shutdown` (a 500, or "Can't reach the local backend" when it
  took the worker down). The GPU pool is now a single self-healing handle whose
  worker pool is rebuilt on demand, so a reset can never strand an in-flight or
  later request. No settings change; the recovery is automatic. (#589 #599)
- **Transcription / dubbing works on Windows again.** WhisperX failed to load on
  Windows because speechbrain's guard that suppresses stray optional-integration
  imports used a POSIX-only path check, so a `k2_fsa` import error aborted the
  whole transcription. Fixed cross-platform — covers the entire class of optional
  integrations, not just k2. (#630 #611 #647)
- **A slow transcription no longer looks like a dead backend.** Whole-file
  transcribe paths (dub QC, dictation, OpenAI-compat) ran unbounded, so a
  VRAM-starved `large-v3` could spin for minutes and hold a GPU worker — surfacing
  as "Can't reach the local backend". They're now time-bounded and return a clear,
  actionable 504 (free VRAM / pick a smaller ASR model / use CPU) instead of
  hanging. New troubleshooting section documents it. (#656)
- **Windows preview playback fixed.** The audiobook/clone preview's streaming
  fallback fetched `localhost`, which on Windows resolves to IPv6 and missed the
  IPv4-only backend — so previews failed with "decode error" / "no supported
  sources". The preview API now targets `127.0.0.1` (matching the main client),
  and the expected decode→stream fallback is logged calmly instead of as a scary
  error. (#653 #659)
- **A stale dub session resets cleanly instead of erroring.** Reopening the Dub
  tab after the backend restarted tried to resume a job that no longer existed and
  surfaced "Job not found" as a bug-report error. It now quietly clears the dead
  session and invites a fresh upload. (#660)
- **A bad voice-style instruct is a clear 400, not a scary 500.** Typing free-form
  prose (or a non-English description) into the style/instruct field returned a
  500 telling you to Flush for memory you never ran out of; it now returns a clean
  400 that lists the valid style tags. The Voice Clone UI also drops unrecognized
  style text locally and generates anyway. (#664 #612)
- **The ⊕ Insert token popover stays on screen.** On Voice Clone it could grow
  tall enough to clip off the top of the window; it's now a compact, scrollable
  box anchored above the button. (#672)
- **First-run no longer hangs on Apple Silicon.** The MCP session-manager startup
  is now timeout-bounded so a slow/stuck mount can't wedge the whole backend boot
  on M1. (#632)

### CI

- **Feature-coverage test system.** A backend route-inventory test diffs all 213
  HTTP/WebSocket endpoints against a committed snapshot (plus a critical-endpoint
  guard and a route-count floor), and a frontend feature-coverage test asserts
  every app mode is wired to a page and every feature has its i18n namespace — so
  an endpoint or page silently disappearing now fails CI on every PR.
- **`bun desktop` no longer kills its own dev backend.** The dev launcher runs the
  API and the Tauri app side-by-side, but the app's backend manager would "take
  ownership" of port 3900 and kill the API the moment it booted (before it was
  healthy), tearing the whole session down. The dev app now sets
  `TAURI_SKIP_BACKEND` so it attaches to the running API instead of fighting it —
  production launch is unaffected. (#745)

## [0.3.7] — 2026-06-20

A stabilization release that clears the wave of issues reported on the 0.3.6
line — across voice design, dubbing, transcription, install, and the Linux/web
UI — and lands two more opt-in cloning engines. The throughline is **non-English
correctness and cross-platform playback**: cloned and designed voices now hold
their language end-to-end, and audio plays inline in Linux/Android browsers,
not just macOS. It also carries the v0.3.6 startup-crash fixes, so anyone still
hitting "Can't reach the local backend" on v0.3.5/v0.3.6 only needs to update.

### Added

- **Two opt-in heavyweight TTS engines: MOSS-TTS-v1.5 (8B) and dots.tts (2B).**
  Both are zero-shot voice-cloning engines, each running in its own isolated
  subprocess venv (they pin a `transformers` version that conflicts with the
  parent's `>=5.3` — MOSS `==5.0`, dots.tts `==4.57`) via the same dedicated-venv
  pattern as IndexTTS-2, so they can't disturb the default install or its
  lockfile. Point `OMNIVOICE_MOSS_TTS_V15_DIR` / `OMNIVOICE_DOTS_TTS_DIR` at a
  local clone to enable. CUDA/CPU only — neither claims Apple-Silicon MPS, and
  dots.tts is gated off on Windows (upstream is Linux/macOS only). See
  [docs/engines/moss-tts-v15.md](docs/engines/moss-tts-v15.md) and
  [docs/engines/dots-tts.md](docs/engines/dots-tts.md). (#498)

### Fixed

- **Non-English voices drifted to English / the wrong language.** Three
  independent root causes, all in the language path: (1) a voice profile's
  stored language was never read back into generation, so a German archetype
  that *previewed* in German *generated* in English (the preview passed the
  language; the user's Generate call didn't); (2) the audiobook/longform synth
  hardcoded `language=None`, letting the engine re-autodetect per chunk so a
  non-English clone could flip language mid-render on short/ambiguous lines; and
  (3) the duration estimator weighted Unicode combining marks at zero, so
  decomposed (NFD) diacritic text — common for Vietnamese — under-allocated
  frames and came out rushed. The profile/request language is now threaded
  through both the single-shot and longform paths (request wins, profile fills
  the gap), and text is NFC-normalized before duration estimation. Each fix has
  a fail-before/pass-after regression test. (#533, #505, #502)
- **Audio playback on Linux Firefox/Chrome and Android Chrome.** Two separate
  root causes both masquerade as "the play button doesn't work" on non-macOS
  browsers — and both are invisible when developing on macOS, which is why they
  shipped. (1) The backend served `.wav` / `.flac` with Python's default
  `audio/x-wav` / `audio/x-flac` (vendor-experimental, never IANA-registered);
  macOS CoreAudio MIME-sniffs leniently and plays anyway, but Linux FFmpeg and
  Android ExoPlayer strictly honor the declared type and prompt to download.
  Fixed by registering the canonical `audio/wav` / `audio/flac` types before
  any `StaticFiles` mount. (2) WaveSurfer's `AudioContext` is constructed at
  component-mount time — i.e. before any user gesture — so on Linux FF/Chrome
  and Android Chrome it stays `suspended`, `decodeAudioData` hangs, the
  `ready` event never fires, and the play button never enables. macOS
  Safari/Chrome auto-resume on first interaction. Fixed by patching
  `window.AudioContext` to track every instance and resuming them on the first
  `pointerdown` / `keydown` / `touchstart`, plus resuming inline on the play
  click itself. The MIME fix has a backend regression test; the unlock path
  has a Vitest unit test covering idempotency, post-unlock contexts, and
  error isolation. (#510)
- **Voice Studio "Save design as profile" poisoned the profile with
  "[object Object]" and then 400'd every generation** ("Unsupported instruct
  items found in [object Object]"). The save passed the instruct *builder
  object* to the form instead of its string. Fixed at the source + defended with
  a coercion helper; the engine now tolerates the sentinel, and a migration
  heals already-saved profiles. (#550, #545, #542, #537, #530, #525)
- **Profile / persona / consent endpoints 500'd with `no such column:
  consent_audio_path`** (and the same class for `kind`/`vd_states`/…) after an
  in-place upgrade. The alembic migration existed but couldn't always apply
  (stamped at a removed revision, or alembic not importable) and the failure was
  swallowed. The runtime schema now self-heals — it ADDs any missing additive
  column from the canonical schema on startup. (#552, #547)
- **Stories: the global reading-speed slider was ignored by preview and stem
  export.** The #415 global speed only flowed through the full longform export;
  per-segment preview and stem export still resolved a hardcoded `track.speed ||
  1.0`, so audio played at 1.0× even with the global set to e.g. 0.70×. A shared
  `effectiveSpeed(track, global)` helper (per-line override → global → engine
  default) now drives all three generation paths. (#508)
- **Generate / Settings / Clone buttons were missing / unpressable on Linux.**
  The UI-scale fix round-trips correctly on Chromium, but older WebKitGTK treats
  `zoom` as a layout no-op, leaving a ~23% black band that pushed the bottom CTAs
  off-screen. The shell now probes the engine and fills the window when `zoom`
  doesn't lay out. (#523, #524)
- **Settings tabs with little content rendered as a stunted box in a black
  void** (reported on Appearance). The page is now a flex column with a
  min-height floor — short tabs fill the panel, tall tabs grow and scroll
  exactly as before. The Appearance panel's previously hardcoded English
  strings ("UI scale", "Color theme", "Font") were also routed through i18n,
  per the localization rule. (#507)
- **The engine "Install" button 500'd with "No virtual environment found."**
  `uv pip install` now targets the running interpreter (`--python
  sys.executable`) instead of relying on a venv it couldn't auto-discover.
  (#529, #527)
- **Transcription failed with "no segments" on GPUs without efficient float16.**
  Both CTranslate2 ASR backends now fall back float16 → int8 instead of crashing
  at model load; a transcribe stream can no longer close without a terminal
  error event; and an incomplete `transformers` install reports an actionable
  message instead of "Could not import module 'AutoFeatureExtractor'".
  (#551, #549, #516)
- **Audiobook import 500'd** with `'AudiobookPlan' object has no attribute
  'chapter_count'` for every format (.txt/.md/.epub/.pdf). (#543)
- **Windows: generated audio auto-played in a separate, un-closeable black
  window.** Renders now play in-app through the shared playback manager. (#532)
- **Cryptic video-download errors** now carry actionable hints: an unsupported
  link shape ("paste a direct video page, not a share/feed link") vs a transient
  network drop ("just retry — the partial download was cleaned up"). (#554, #536)
- **A relocated, copied, or restored backend venv ("No module named
  'encodings'") now self-heals** (rebuilds once) instead of failing on every
  launch.
- **The donate goal bar showed fabricated progress** ($137.50 / $200, 23
  sponsors). It now reflects the real figures ($10 / $200, 1 sponsor) in both the
  runtime JSON and the TypeScript fallback. (#513)
- The **"Can't reach the local backend" startup-crash wave** (pkg_resources
  #248, `scalar_fastapi` #307, exit-106 broken venv) was fixed in v0.3.6 — this
  release carries those fixes, so updating from v0.3.5/older resolves them.

### Changed

- **Version is now single-sourced from `frontend/package.json`.** Five
  hand-maintained literals drifting is exactly what shipped a 0.3.6 build that
  called itself 0.3.5. `package.json` is canonical (vite already injects it as
  `__APP_VERSION__`), `tauri.conf.json` reads its bundle version from it
  (`"version": "../package.json"`), and the remaining toolchain-required mirrors
  (Cargo.toml, pyproject.toml, the frozen-backend fallback) are CI-guarded to
  stay in lockstep. (#503)
- **Updater: the Preview channel actually tracks `main` again.** It was stuck at
  `0.3.5-41` because its only build trigger was a manual dispatch; a nightly
  rebuild now enforces "preview = main" (no-opping on days `main` didn't move).
  Two latent hazards are closed: the `preview` release is re-asserted as a
  prerelease every run (a non-prerelease preview could hijack the Stable
  channel's "Latest"), and its manifest can no longer silently drop the
  Intel-Mac (darwin-x86_64) target. (#500)

### Internal

- **The frozen desktop backend reported `0.3.5` regardless of its real version.**
  In a synced env, `core.version.APP_VERSION` resolves from package metadata
  (correct, so CI stayed green), but the PyInstaller-frozen build has no
  `.dist-info`, hit `PackageNotFoundError`, and fell back to a hardcoded literal.
  The spec now bundles `omnivoice` metadata so the primary path works frozen too,
  and the resolution chain is metadata → pyproject → named fallback. This also
  fixes **About → Version rendering blank** in the web/Pinokio build (no Tauri,
  backend idle), which now falls back to the build-time version. (#501)

## [0.3.6] — 2026-06-16

A large release (168 commits since v0.3.5). The headline is the **Longform
suite** — produce full audiobooks and multi-voice stories from text, EPUB, or
PDF — alongside a real **engine-routing** layer that tells you up front when an
engine will fall back to CPU instead of finding out mid-synth. Dubbing,
first-run, and install reliability all get a pass too.

### Added

- **Longform: Stories + Audiobook editors.** Two new tabs turn long text into
  finished audio. **Audiobook** takes a script (or imports plain text / EPUB /
  PDF), auto-splits it into chapters, and renders a chaptered `.m4b` with
  metadata, cover art, and per-chapter preview/resume. **Stories** is a
  multi-voice editor — assign a different voice per line, preview, and export
  the whole thing through the same server-side renderer. Both share one render
  core (loudness, metadata, cover art) and one live SSE progress stream, and
  you can convert a project between Story and Audiobook in place.
  (#402, #403, #404, #408, #409, #411, #412, #413, #426, #435, #436, #447)
- **Longform: PDF & EPUB ingest.** "Import" on the Audiobook tab accepts EPUB
  and PDF (not just plain text) and auto-chapters the result, so an existing
  ebook becomes an audiobook without manual copy-paste. (#412, #459)
- **Longform: two-pass loudnorm mastering.** Audiobook/Story exports now run a
  measure-then-normalize loudnorm pass for accurate ACX/podcast loudness
  targets. A slow or broken measure pass degrades gracefully to single-pass
  rather than aborting the render. (#449, #455)
- **Longform: crash-resume.** An interrupted render is resumable without
  re-submitting the original input — the compiled plan is persisted to the job
  dir and finished chapters are reused, so a crash mid-book doesn't cost you the
  whole render. (#470)
- **Longform: pronunciation control + SSML-lite prosody.** A per-render
  pronunciation lexicon (word respelling) plus an in-app pronunciation editor
  and markup reference, and inline prosody markers — `[slow]` / `[fast]` /
  `[emphasis]` / `[spell]` — for fine-grained delivery. (#419, #421, #422)
- **Stories: global reading-speed control.** A toolbar slider (0.5–2.0×) sets
  one speed for every line that doesn't have its own per-line override; the
  per-line slider still wins. Persisted as a UI preference. (#415, #416)
- **Unified LongformProject store.** Audiobook metadata, scripts, and prefs
  persist in a single project store (with a `v4→v5` migration), and finished
  books/stories now show up alongside other work in **Projects**. (#417, #443,
  #444)
- **Portable personas (`.ovsvoice`).** Export any voice as a self-contained,
  fully-local persona bundle — identity, optional reference clip, consent
  attestation, SPDX license, and a watermarked preview — and import it back into
  another VoiceStudio install. A privacy toggle ships a **preview-only** bundle so
  no raw recording of your voice has to travel. Verified-own-voice status can't
  be forged by hand-editing a bundle (real recording + consent text + attestation
  required). Legacy `.omnivoice` files still import. See
  [docs/persona-format.md](docs/persona-format.md). (#29)
- **Engine routing — no more silent CPU fallback.** A host device probe and
  routing resolver now decide where each engine actually runs, and the verdict
  is surfaced before you hit Synthesize: the **Settings → Engines** picker shows
  a per-engine compatibility matrix, and **preflight** / **diagnose** report the
  active engine's GPU verdict (accelerated / caveat / CPU-fallback /
  unavailable). At synth time every TTS entry point (`/generate`,
  `/v1/audio/speech`) enforces the same routing — an engine that can't use this
  host's GPU returns an explicit error or an `X-VoiceStudio-Routing` header instead
  of silently dropping to CPU or dying mid-synth. (#21)
- **Diagnostics suite.** New self-check tooling for when something's wrong: a
  `/system/diagnose` report (and matching backend `--diagnose`), a persistent
  **error journal** surfaced in Settings, and a scrubbed **diagnostic bundle**
  (home dirs stripped to `~/`, no tokens/keys) you can attach to a bug report.
  Paired with structured GitHub **Issue Forms** (bug / install / feature) for
  cleaner reports. (#433, #456)
- **Dubbing: multi-speaker per-speaker voice assignment.** When diarization
  detects multiple speakers, each segment is now bound to its speaker's cloned
  voice automatically instead of landing on "Default" and needing manual fixes;
  per-segment reference clips are still preferred for quality where present. Also
  adds an optional speaker-count hint for diarization. (#275, #486, #490)
- **Dubbing: Smart Fit timing + second-pass QC.** A Smart Fit timing strategy
  (planner, fingerprints, per-segment video retime + drift absorption + fitted
  subtitles) plus a second-pass ASR QC that flags lines whose dub drifts from the
  target timing — wired into the dub editor UI. Includes a timeline segment
  editor (drag, snap-to-onset, keyboard a11y), speech-onset alignment, regional
  dialect targeting, and per-segment clone references. (#280, #347, #350, #369,
  #370, #458)
- **Dubbing: dedicated Dub home.** A projects/history landing for dubbing with
  project rename. (#435)
- **Voice Console workspace.** Clone and Design are consolidated into one Voice
  workspace with right-side panels, a shared waveform player, an identity recipe
  line / Active-voice card, and a free-text "describe your voice" field that maps
  natural language to design parameters. (#317, #374, #376, #378, #395, #396,
  #397)
- **Unified first-run setup.** Nothing installs until you confirm a plan: pick an
  install mode (installed / portable), a storage location, and (on restricted
  networks) custom PyPI/HF/python-build-standalone mirrors — with a
  minimum-free-space gate before anything downloads. Followed by a guided
  studio-console wizard with platform-aware hints, resume reassurance, and
  download ETAs. (#286, #295, #297, #298)
- **Dictation: local-LLM refinement.** Opt-in local-LLM cleanup of final
  transcripts (collapsing Whisper hallucination loops), available on both live
  dictation and the REST `/transcribe` path; plus opt-in NLMS acoustic echo
  cancellation for dictating over playback. Configure a remote LLM endpoint
  (Ollama / vLLM / LM Studio) in Settings. (#356, #357, #363, #399, #400, #457)
- **Unlimited-length TTS + streaming.** Sentence-boundary chunking with
  crossfade removes the per-generation length cap, and a new sentence-by-sentence
  `/ws/tts` streams audio as it's produced. An inline `[pause Nms]` marker
  inserts measured silence in generated speech. (#276, #357, #358)
- **MCP server v1.** VoiceStudio mounts an MCP server on `/mcp` (with a stdio shim
  and per-agent voice binding) so it can act as a local TTS/STT provider for
  agentic pipelines. (#368)
- **Remote-backend access.** Point the desktop UI at a remote backend URL with a
  bearer key (Tailscale-documented), and an opt-in Hugging Face token field in
  the setup flow. (#303, #364)
- **"Fund Claude Max" support experience.** The donate page gets a real goal bar
  with a "Join N supporters" social-proof line and suggested amounts, plus Pip
  the mascot and a non-blocking "postcard" toast that appears only *after* a
  success (a finished dub, a saved clone, a longform export) — never on errors,
  setup, or first run — with escalating cooldowns and a one-click "don't ask
  again". (#494)

### Fixed

- **Transcription/dubbing failed when ffmpeg wasn't on `PATH`** (notably on
  Windows). WhisperX now decodes audio through VoiceStudio's own validated ffmpeg
  binary instead of a bare `PATH` lookup, so ASR works without a system ffmpeg
  install. (#479)
- **Translation defaulted the source language to English.** Dubbing/translation
  now guesses the source language from the text instead of assuming `en`,
  fixing wrong-direction translations. (#478)
- **Cinematic / LLM dubbing features failed out of the box** because `openai`
  wasn't bundled. The client is now a runtime dependency, so those paths work on
  a fresh install. (#484)
- **`pkg_resources missing` install dead-end (#248).** The auto-repair ran
  `uv pip install setuptools`, which `uv` treated as a no-op when setuptools
  *metadata* was present but its files had been removed (commonly by Windows
  Defender quarantine or a partial extract). Both repair sites now use
  `--reinstall` to force re-extraction, and the error/hint text suggests the
  working command plus an antivirus-exclusion note. (#248)
- **A stuck backend trapped users on a buttonless splash (#474).** The bootstrap
  splash now has a per-stage stall watchdog: if a non-terminal stage sits past
  its budget (20 min for dep install, 120 s otherwise), it flips to the failed
  state with actionable hints, the live log, and Retry / Clean-&-Retry — instead
  of polling forever with no way out. (#474)
- **Changing the model-download location in Settings had no effect (#480).** The
  desktop launcher injected a stale models dir that overrode the per-user value,
  so new downloads kept going to the old folder and "Effective location" stayed
  wrong. The per-user env file now wins, so the in-app Settings path is
  authoritative. (#480)
- **Backend crashed on app upgrade with a stale venv (#307).** Dependencies are
  now synced on upgrade, and a structurally broken venv self-heals instead of
  exiting `106`. `scalar_fastapi` is now optional so its absence can't break
  startup. (#307, #314)
- **`/generate` ignored the selected TTS engine (#312)** and GGUF speech-control
  parameters weren't forwarded — both now honored. (#306, #312)
- **TTS generation failed on some GPUs.** `torch.compile` failures now fall back
  to eager execution so generation never hard-fails on unsupported GPUs, and
  cudagraph-compiled inference is pinned to one dedicated thread to avoid
  crashes. (#278, #315)
- **Re-dub ignored transcript edits (#281).** Fingerprints are canonicalized, the
  preview cache is busted, and the mux is atomic, so editing the transcript and
  re-dubbing actually reflects your changes. Translated subtitles now burn in
  correctly and subtitle save no longer throws a JSON error. (#281, #309)
- **macOS: app wouldn't open without using Terminal.** Builds are now ad-hoc
  signed (with signing/notarization verification), so the app launches normally.
  (#290)
- **macOS dictation auto-paste stole focus**; it now writes the clipboard
  natively without grabbing focus, and microphone-permission handling adds OS
  usage descriptions, a WebView grant handler, and an actionable denied-state UI.
  (#287, #323)
- **Clone-reference transcription was broken** (it used a removed transformers
  pipeline); it now routes through the ASR registry. A crash-isolated
  faster-whisper subprocess backend keeps an ASR crash from taking down the app.
  (#308, #393)
- **Realtime status probe hit a gated route.** It now probes the auth-exempt
  `/health` instead of the gated `/model/status`, and the UI polls the backend
  over HTTP before opening the WebSocket to avoid startup `ECONNREFUSED`. (#439,
  #450)
- **Non-executable or unreachable engine binaries showed cryptic errors** — these
  now produce actionable messages. (#437, #438, #454, #466)
- **Design-profile save was coupled to a TTS render (#476)**, so saving a profile
  needlessly triggered synthesis; the two are now decoupled. (#476)
- **UI scale / black bands.** The app shell now scales via `transform: scale` and
  always fills the viewport, fixing the WebKitGTK black-band issue on Linux and
  cramped/black layouts at narrow widths — a permanent fix across platforms.
  (#445, #452)
- **Clone popover/CTA clipping and a non-resizable textarea** are fixed, the
  WaveformPlayer no longer pauses itself on play or ignores clicks, and several
  layout/history-display issues (phantom sidebar gap, title clamping, flicker)
  are cleaned up. (#379, #384, #398, #481)
- **Windows: `desktop-prod` now runs from cmd/PowerShell** via a cross-platform
  launcher, `tqdm` is disabled on non-TTY to avoid an `OSError`, and ffmpeg
  validation guards against `WinError 193`. (#282, #305, #377)
- **MLX import hardened** against PyInstaller dylib failures, with a proper
  platform gate so it's only loaded where it works. (#390)

### Changed

- **Restricted-network support.** A Hugging Face mirror (`HF_ENDPOINT`) setting,
  custom PyPI / HF / python-build-standalone mirrors in first-run setup, and
  region presets help installs complete behind restrictive networks. (#286, #391)
- **Engine memory management.** Subprocess-engine sidecars now unload on demand
  and idle-reap to free VRAM. (#401, #406)
- **Faster, more accurate model downloads** via a Xet fast path with accurate
  progress reporting, plus a model-management cleanup pass. (#424, #428)
- **Voice profiles unified** under one model with a `kind` discriminator and
  stored design params, and consent-locked profiles (`verified_own_voice` +
  spoken-consent flow). (#354, #376)
- **Updater** preview channel now offers the newest build across channels, and
  preview versions carry an MSI-legal numeric pre-release stamp. (#293, #326)
- **Performance.** Voice-clone prompt embeddings are cached, and dub retime
  batches seek to their window instead of decoding from frame 0. (#387, #427)

### License

- **Relicensed from FSL-1.1-ALv2 to AGPL-3.0 (open-core).** The project is now
  under the GNU Affero General Public License v3, with a paid commercial license
  retained for proprietary/closed-source use without AGPL obligations. The
  bundled `omnivoice/` TTS model package stays Apache-2.0 upstream
  (AGPL-compatible). Manifests declare `AGPL-3.0-only`; the in-app Commercial
  License copy and README are updated, and the old "converts to Apache 2.0 after
  two years" FAQ is removed. In-app commercial-license strings are translated
  across all 20 locales. (#292)

### CI

- **macOS Intel (x86_64) build target reinstated** on `macos-15-intel`, so Intel
  Mac users get installers again. (#342)
- **Docker Hub publishing.** Images now also publish to Docker Hub
  (`palashdeb/omnivoice-studio`), with the Docker Hub overview maintained in-repo
  and auto-synced from `main` (sync is non-fatal so it can't redden a build).
  (#375, #410, #414)
- **Docs-drift guard.** A daily job compares the canonical feature inventory
  against README / docs / registries to catch stale docs. (#353)
- **Security scans never cancel on `main`,** so merge trains no longer leave red
  ✗ on intermediate commits. (#340)

## [0.3.5] — 2026-06-03

### Fixed
- **Speaker diarization failed on PyTorch ≥ 2.6** (`Weights only load failed …
  Unsupported global: torch.torch_version.TorchVersion`) even with the pyannote
  license accepted. PyTorch 2.6 made `torch.load` default to
  `weights_only=True`, whose secure unpickler rejects the pyannote checkpoint's
  metadata globals. The diarization loader now registers the same safe-globals
  allowlist the WhisperX VAD load already uses, so the secure load succeeds.
  (#270)

## [0.3.4] — 2026-06-03

### Fixed
- **Transcription on Windows + NVIDIA failed with `Could not locate
  cudnn_ops_infer64_8.dll`.** WhisperX/faster-whisper need cuDNN 8 (via
  CTranslate2); when the side-loaded `cudnn8_compat` libs are missing, the
  **PyTorch Whisper** backend (Settings → Models) now works as a drop-in
  fallback — it builds its own transformers pipeline on PyTorch's cuDNN-9
  stack, with no CTranslate2/cuDNN-8 dependency and no
  `OMNIVOICE_PRELOAD_TTS_ASR=1` required. (#255)

## [0.3.3] — 2026-06-03

### Fixed
- **Settings → About showed the wrong architecture in the Docker/web build.**
  The "Architecture" row rendered the *client browser's* platform
  (`navigator.platform` → e.g. "Win32"); it now reports the **server's** CPU
  architecture from the backend (`platform.machine()`), correct for both the
  desktop app and Docker. The blank version/GPU/RAM/VRAM in the same report
  were the loopback-gate 403s already fixed in v0.3.2. (#262)

### CI
- The release SHA-256 checksum step no longer uses `mapfile` (a bash 4+
  builtin) — it broke on the macOS runner's bash 3.2 and dropped the macOS
  `SHA256SUMS` for v0.3.1/v0.3.2. Now portable to bash 3.2.

## [0.3.2] — 2026-06-03

### Fixed
- **"Loopback origin required" all over the Docker UI** (and a blank version).
  The `/system/*` and `/api/settings/*` routes are restricted to a loopback
  origin, but Docker's NAT makes every request look non-loopback, so the gate
  403'd the operator out of the admin UI — including `/system/info` (blanking
  the version) and HF-token entry. The Docker image now runs with
  `OMNIVOICE_SERVER_MODE=1`, which relaxes the gate for the headless
  deployment; exposure is governed by the `-p` port mapping plus the optional
  share PIN. Desktop builds are unaffected — their loopback boundary (and the
  denial of admin routes to LAN share guests) is unchanged. (#261)

## [0.3.1] — 2026-06-03

First tagged build of the 0.3 line off `main` — it ships the accumulated
`[0.3.0]` work below plus the fixes here. (The `[0.3.0]` milestone heading is
kept for the qualitative "actually useful" release.)

### Fixed
- **Voice-clone / export download crashed in the Docker & browser build** with
  `TypeError: Cannot read properties of undefined (reading 'invoke')`. The
  export button called the Tauri save dialog unconditionally; outside the
  desktop shell it now falls back to a standard browser download of the file
  served at `/audio/<path>`. (#256)
- **Docker container showed no version** (a dash) in Settings → About, and the
  desktop-only update-channel toggle appeared in the web build. The running
  version is now read from the backend (`/system/info` `app_version`, `/health`
  `version`); the updater UI is hidden outside Tauri. Also corrected the
  version-check command in the Docker docs (`omnivoice`, not
  `omnivoice-studio`). (#249)
- **Transcription failures were masked** by a generic "Transcribe stream
  dropped" message. The transcribe SSE stream now surfaces the real, sanitized
  cause (with an actionable hint) instead of silently dropping when model load
  or VRAM offload fails. (#255)

## [0.3.0] — Unreleased

### Added
- **Frameless dictation widget.** Global dictation upgraded from an in-app FAB to a true OS-level floating widget that hovers over any application. Transparent, decorations-free, always-on-top secondary Tauri window activated by `⌘+⇧+Space`. Auto-hides 2.5 s after a successful paste.
- **Standalone `CaptureWidget` component.** Refactored `CaptureButton` into `CaptureWidget`, running on an isolated route (`/?window=widget`).
- **Social preview image.** Added `social-preview.png` for GitHub SEO.

### Changed
- **README overhaul.** Compact 3-column feature grid, reorganized Quickstart (one-command install, Docker, Desktop App tips), updated comparison table, roadmap, and footer CTA.
- **Docker Compose profiles are mutually exclusive.** CPU service now requires `--profile cpu` (was the implicit default). Prevents port 3900 conflict when running `--profile gpu`. Usage: `docker compose --profile cpu up` or `docker compose --profile gpu up`.

### Fixed
- **Docker GPU detection false negative.** Preflight reported "No compatible GPU detected" inside Docker containers because `nvidia-smi` isn't present in the PyTorch base image. The GPU probe now falls back to `torch.cuda.is_available()` and `torch.cuda.get_device_name()`, correctly showing CUDA as available in containerized deployments.

---

## [0.2.6] — Unreleased

### License
- **Relicensed Studio under [Functional Source License (FSL-1.1-ALv2)](https://fsl.software/).** Free for personal, educational, internal-team, and non-commercial use. Each release converts automatically to Apache License, Version 2.0 on the second anniversary of its publication.
- The bundled `omnivoice/` Python TTS model package remains separately licensed under Apache 2.0 by its upstream authors — not relicensed here.
- In-app **Commercial License** page no longer publishes pricing tiers. Pricing is being finalized; the page now invites quote requests and links the FSL terms.

### Added
- **Single-instance enforcement.** Launching a second copy now focuses the existing window instead of starting a second backend that races for port 3900. Powered by `tauri-plugin-single-instance`.
- **Close-to-tray.** Clicking the window X (or `Cmd+W` on macOS) now hides the window and keeps the backend + tray menu alive. The tray "Quit" item is the only path that fully exits and shuts down the Python backend (cleanup moved to `RunEvent::ExitRequested`).
- **Recording-state tray icon.** Tray icon flips to a red-dot variant while a dictation recording is active and reverts when it stops or errors out.
- **Customizable global dictation hotkey.** New **Settings → Capture** tab. Record any modifier-plus-key combo, save it, and it's persisted in `config.json` and re-registered on every launch. Failed registrations (combo already taken by the OS) roll back to the previously-working binding instead of leaving the user with no shortcut.
- **WebSocket-final dictation path.** Capture now treats the streaming `final` message as the source of truth and skips the duplicate HTTP `POST /transcribe` that used to run on every dictation. Audio is transcribed once instead of twice — typical dictation latency roughly halved. New EOF text-frame protocol (server also accepts an empty binary frame as EOF). HTTP POST kept as fallback for WS error / timeout / WS-never-opened.
- **Chunk queueing during WS handshake.** The first 250 ms of audio is no longer dropped from the server's `final` transcript. `MediaRecorder` chunks captured while the WebSocket is still in `CONNECTING` state are queued and drained in `ws.onopen`.

### Changed
- **Docker default bind is loopback.** `docker-compose.yml` now publishes `127.0.0.1:3900:3900` instead of `3900:3900` — the API is no longer reachable from the LAN out of the box. To expose it deliberately, change the mapping to `0.0.0.0:3900:3900`. README documents the trade-off and recommends a reverse proxy with auth (Caddy `basic_auth`, nginx + htpasswd, Tailscale) for any non-loopback exposure.
- **Donate page trimmed.** Removed Patreon and the Bitcoin / Ethereum / Solana cryptocurrency cards. Removed the bundled `qrcode.react` dependency. The "Commercial License" CTA moves from the bottom of the page to the top-right of the page header.
- **WS dictation hostname** now derived from the configured `API_BASE` instead of a hardcoded `localhost:3900`, so deployments behind reverse proxies route correctly.
- **HTTP POST fallback timeout** scales with recording length (`max(15s, recordedMs + 10s)`) so long-form dictations don't trip the fallback and run the model twice.

### Fixed
- **Backend was killed on every window close** even if the user only intended to dismiss the window. Backend shutdown now fires only on real-quit (`RunEvent::ExitRequested`), not on the close-to-hide path.
- **Hotkey rollback.** `set_dictation_shortcut` previously left the user with no global shortcut if `register(new)` failed after `unregister(old)` succeeded. The previous binding is now restored on failure.
- **WebSocket dictation pipeline lost the first audio chunk.** `MediaRecorder` was started before the WebSocket finished its handshake, so the first 250 ms chunk — which carries the WebM EBML header — was dropped from the WS stream. Every subsequent server-side ffmpeg conversion then failed with `exit status 183` ("Invalid data found when processing input"), partials never appeared, and the HTTP fallback only fired after the full timeout. The WebSocket is now constructed before the recorder, every chunk is queued through `wsPendingRef` until `ws.onopen` drains it, and a server `error` message (or unexpected `onclose` after the recorder has stopped) fires the HTTP fallback immediately instead of waiting out the timeout.
- **Microphone access prompt on macOS.** Added an `Info.plist` with `NSMicrophoneUsageDescription` (and `NSCameraUsageDescription` for forward-compat) so getUserMedia no longer fails silently on macOS 10.14+ TCC. Tauri's bundler auto-merges the file at bundle time. Mic-denial toasts now also include platform-specific recovery hints (Settings paths for macOS/Windows, audio-group check for Linux).

### Infrastructure
- **uv bundled per-platform.** Release installers now ship the `uv` binary as a Tauri sidecar (`bundle.externalBin`). First launch no longer requires network access for the uv-download step — bootstrap uses the bundled binary directly. Adds ~12-15 MB per platform installer; falls back to PATH lookup, then standalone download, when the bundled file isn't present (dev builds, future targets). Pinned at `UV_VERSION = "0.11.7"`; bump the constant in [lib.rs](frontend/src-tauri/src/lib.rs) and the matching env var in [release.yml](.github/workflows/release.yml) together to refresh.
- **ffmpeg fetch removed from Tauri bootstrap.** The redundant download from `eugeneware/ffmpeg-static` (saved to `app_data/bin/`) was never used by the backend, which already resolves ffmpeg via `imageio_ffmpeg.get_ffmpeg_exe()` from the pip wheel pulled by `uv sync`. Net effect: one fewer first-run network round-trip, one fewer splash-screen stage, and the splash no longer shows the misleading "Downloading ffmpeg…" line.
- **CI cross-platform check.** PRs now run `cargo check` against the Tauri shell on macOS (Apple Silicon), Windows, and Linux in parallel — surfaces platform-specific Rust regressions before tag push without paying the full ~15 min/platform tauri-bundle cost (full bundling stays in `release.yml` on tag push).
- **Release notes from CHANGELOG.** `release.yml` now extracts the matching `## [X.Y.Z]` section from `CHANGELOG.md` and uses it as the GitHub Release body, replacing the prior placeholder "Auto-generated release. See commit log for changes."
- **Tests:** `tests/test_capture_ws.py` (3 cases) covers the EOF text-frame, empty-binary-frame, and legacy disconnect-finalize paths for `/ws/transcribe`.

### Internal
- New Tauri commands: `quit_app`, `set_tray_recording`, `get_dictation_shortcut`, `set_dictation_shortcut`.
- New Tauri state: `AppFlags { quitting }`, `TrayHandle { tray }`, `DictationShortcutState { current }`.
- New deps: `tauri-plugin-single-instance` 2.x, `tauri/image-png` feature flag (enables `Image::from_bytes` for in-memory tray-icon swap).

---

## [0.2.5] — 2026-04-29

Region selector, realtime download speed, retry buttons, recheck top-right, HF mirror support, splash bootstrap-log backfill. See git log `v0.2.4..v0.2.5` for the full set.

## Earlier releases

See [GitHub Releases](https://github.com/debpalash/VoiceStudio/releases) for prior versions.
