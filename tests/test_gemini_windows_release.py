"""Contracts for the fork's rolling Windows Gemini installer."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "gemini-windows-msi.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
CONFIG = ROOT / "frontend" / "src-tauri" / "tauri.gemini-windows.conf.json"
README = ROOT / "README.md"
SMOKE = ROOT / "scripts" / "smoke-gemini-windows.ps1"

MSI_NAME = "VoiceStudio-Gemini-Windows-x64.msi"
RELEASE_TAG = "gemini-windows"
DOWNLOAD_URL = (
    "https://github.com/TheOneironaut/VoiceStudio/releases/download/"
    f"{RELEASE_TAG}/{MSI_NAME}"
)


def test_gemini_windows_workflow_builds_and_publishes_fixed_msi():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "branches: [main]" in workflow
    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert f"RELEASE_TAG: {RELEASE_TAG}" in workflow
    assert f"MSI_NAME: {MSI_NAME}" in workflow
    assert "tauri.gemini-windows.conf.json" in workflow
    assert "verify-windows-msi.ps1" in workflow
    assert "gh release upload" in workflow
    assert "--clobber" in workflow


def test_gemini_windows_release_is_gated_by_installed_app_smoke():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    smoke = SMOKE.read_text(encoding="utf-8")

    assert "paths:" in workflow
    assert '      - "package.json"' in workflow
    assert '      - "bun.lock"' in workflow
    assert '      - "README.md"' in workflow
    assert '      - "CHANGELOG.md"' in workflow
    assert "smoke-gemini-windows.ps1" in workflow
    assert workflow.index("Smoke-test installed Gemini app") < workflow.index(
        "Publish rolling Gemini release"
    )
    assert "if: failure()" in workflow
    assert "actions/upload-artifact@v4" in workflow
    assert "msiexec.exe" in smoke
    assert '"setup_complete": true' in smoke
    assert 'http://127.0.0.1:3900/health' in smoke
    assert 'http://127.0.0.1:3900/engines' in smoke
    assert "gemini-3.1-flash-tts" in smoke
    assert "Local model checkpoint" in smoke
    assert "OMNIVOICE_LOG_DIR" in smoke
    assert '"OmniVoice\\Logs"' in smoke
    assert 'Join-Path $appData "logs"' in smoke
    assert 'Get-ChildItem -LiteralPath $appData -Recurse' not in smoke


def test_ci_cancels_only_superseded_non_main_runs():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "group: ci-${{ github.ref }}-" in workflow
    assert "github.ref == 'refs/heads/main' && github.sha || 'branch'" in workflow
    assert "cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}" in workflow


def test_gemini_windows_bundle_is_msi_only_without_unsigned_updater_payloads():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))

    assert config["productName"] == "VoiceStudio Gemini"
    assert config["identifier"] == "com.theoneironaut.voicestudio-gemini"
    assert config["bundle"]["targets"] == ["msi"]
    assert config["bundle"]["createUpdaterArtifacts"] is False


def test_gemini_bundle_cannot_install_upstream_updates():
    updater = (ROOT / "frontend" / "src-tauri" / "src" / "updater_channel.rs").read_text(
        encoding="utf-8"
    )

    assert 'GEMINI_BUNDLE_IDENTIFIER: &str = "com.theoneironaut.voicestudio-gemini"' in updater
    assert "if !updater_enabled(app)" in updater


def test_gemini_bundle_uses_windows_safe_eager_backend_startup():
    backend = (ROOT / "frontend" / "src-tauri" / "src" / "backend.rs").read_text(
        encoding="utf-8"
    )
    assert 'app.config().identifier == "com.theoneironaut.voicestudio-gemini"' in backend
    assert 'env.push(("OMNIVOICE_EAGER_INIT".into(), "1".into()))' in backend


def test_readme_promotes_the_exact_rolling_release_asset():
    readme = README.read_text(encoding="utf-8")

    assert readme.count(DOWNLOAD_URL) >= 2
    assert "actions/workflows/gemini-windows-msi.yml/badge.svg" in readme
