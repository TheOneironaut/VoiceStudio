"""Contracts for the fork's rolling Windows Gemini installer."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "gemini-windows-msi.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
CONFIG = ROOT / "electron" / "electron-builder.gemini-windows.config.mjs"
ELECTRON_VITE = ROOT / "electron" / "electron.vite.config.ts"
ELECTRON_UPDATER = ROOT / "electron" / "src" / "main" / "updater.ts"
ELECTRON_RUNTIME = ROOT / "electron" / "src" / "main" / "runtime-project.ts"
PACKAGE_CONTRACT = ROOT / "electron" / "tests" / "gemini-windows-package-contract.mjs"
PACKAGED_SMOKE = ROOT / "electron" / "tests" / "packaged-smoke.mjs"
README = ROOT / "README.md"
DOCKER_WORKFLOW = ROOT / ".github" / "workflows" / "docker.yml"

MSI_NAME = "VoiceStudio-Gemini-Windows-x64.msi"
RELEASE_TAG = "gemini-windows"
DOWNLOAD_URL = (
    "https://github.com/TheOneironaut/VoiceStudio/releases/download/"
    f"{RELEASE_TAG}/{MSI_NAME}"
)


def test_gemini_windows_workflow_builds_and_publishes_fixed_msi():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "branches: [main]" in workflow
    assert "pull_request:" in workflow
    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert f"RELEASE_TAG: {RELEASE_TAG}" in workflow
    assert f"MSI_NAME: {MSI_NAME}" in workflow
    assert "electron-builder.gemini-windows.config.mjs" in workflow
    assert "bun run check:electron" in workflow
    assert "gemini-windows-package-contract.mjs --artifact" in workflow
    assert "packaged-smoke.mjs --install" in workflow
    assert "VOICESTUDIO_EXPECTED_TTS_ENGINE: gemini-3.1-flash-tts" in workflow
    assert "gh release upload" in workflow
    assert "--clobber" in workflow
    assert "tauri build" not in workflow
    assert "src-tauri/target" not in workflow


def test_gemini_windows_release_is_gated_by_electron_runtime_smoke():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    smoke = PACKAGED_SMOKE.read_text(encoding="utf-8")

    assert "paths:" in workflow
    assert '      - "package.json"' in workflow
    assert '      - "bun.lock"' in workflow
    assert '      - "README.md"' in workflow
    assert '      - "CHANGELOG.md"' in workflow
    assert workflow.index("Install managed runtime and verify Gemini default") < workflow.index(
        "Publish rolling Gemini release"
    )
    assert "if: failure()" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "VOICESTUDIO_EXPECTED_TTS_ENGINE" in smoke
    assert "'/api/engines/tts'" in smoke


def test_gemini_windows_bundle_uses_the_runtime_uv_version():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    runtime = ELECTRON_RUNTIME.read_text(encoding="utf-8")

    workflow_version = re.search(
        r'astral-sh/setup-uv@v6\s+with:\s+version: "([^"]+)"', workflow
    )
    runtime_version = re.search(r"UV_VERSION = '([^']+)'", runtime)

    assert workflow_version is not None
    assert runtime_version is not None
    assert workflow_version.group(1) == runtime_version.group(1)


def test_ci_cancels_only_superseded_non_main_runs():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "group: ci-${{ github.ref }}-" in workflow
    assert "github.ref == 'refs/heads/main' && github.sha || 'branch'" in workflow
    assert "cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}" in workflow


def test_fork_does_not_spend_minutes_on_upstream_owned_docker_images():
    workflow = DOCKER_WORKFLOW.read_text(encoding="utf-8")

    assert workflow.count("if: github.repository == 'debpalash/VoiceStudio'") == 2


def test_gemini_windows_bundle_is_electron_msi_with_isolated_updates():
    config = CONFIG.read_text(encoding="utf-8")
    vite = ELECTRON_VITE.read_text(encoding="utf-8")
    updater = ELECTRON_UPDATER.read_text(encoding="utf-8")
    contract = PACKAGE_CONTRACT.read_text(encoding="utf-8")

    assert "com.theoneironaut.voicestudio-gemini" in config
    assert "VoiceStudio Gemini" in config
    assert "target: 'msi'" in config
    assert "publish: null" in config
    assert "__VOICESTUDIO_EDITION__" in vite
    assert "edition !== 'gemini'" in updater
    assert "Gemini Electron Windows identity" in contract


def test_windows_uses_job_object_without_a_parent_pipe_thread():
    parent_liveness = (ROOT / "backend" / "core" / "parent_liveness.py").read_text(
        encoding="utf-8"
    )

    assert 'if sys.platform == "win32":' in parent_liveness
    assert "redundant Unix fallback" in parent_liveness


def test_readme_promotes_the_exact_rolling_release_asset():
    readme = README.read_text(encoding="utf-8")

    assert readme.count(DOWNLOAD_URL) >= 2
    assert "actions/workflows/gemini-windows-msi.yml/badge.svg" in readme
