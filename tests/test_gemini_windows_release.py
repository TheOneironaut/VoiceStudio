"""Contracts for the fork's rolling Windows Gemini installer."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "gemini-windows-msi.yml"
CONFIG = ROOT / "frontend" / "src-tauri" / "tauri.gemini-windows.conf.json"
README = ROOT / "README.md"

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


def test_readme_promotes_the_exact_rolling_release_asset():
    readme = README.read_text(encoding="utf-8")

    assert readme.count(DOWNLOAD_URL) >= 2
    assert "actions/workflows/gemini-windows-msi.yml/badge.svg" in readme
