param(
    [Parameter(Mandatory = $true)]
    [string]$MsiPath,
    [string]$LogDir = "dist/smoke-logs",
    [int]$ReadyTimeoutSeconds = 1200
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$resolvedMsi = (Resolve-Path $MsiPath).Path
$resolvedLogDir = [System.IO.Path]::GetFullPath($LogDir)
$appData = Join-Path $env:LOCALAPPDATA "com.theoneironaut.voicestudio-gemini"
$backendLogs = Join-Path $env:LOCALAPPDATA "OmniVoice\Logs"
$temporaryRoot = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [System.IO.Path]::GetTempPath() }
$modelsDir = Join-Path $temporaryRoot "voicestudio-gemini-models"
$healthUrl = "http://127.0.0.1:3900/health"
$progressUrl = "http://127.0.0.1:3900/startup/progress"
$enginesUrl = "http://127.0.0.1:3900/engines"
$appProcess = $null
$installed = $false
$smokeSucceeded = $false

function Invoke-SmokeJson([string]$Url) {
    return Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 5 -UseBasicParsing
}

function Copy-SmokeDiagnostics {
    New-Item -ItemType Directory -Force $resolvedLogDir | Out-Null
    $sources = @(
        # Never recurse through appData/project/.venv: that can contain tens
        # of thousands of package metadata files and exhaust the smoke budget.
        @{ Path = (Join-Path $appData "logs"); Prefix = "desktop" },
        @{ Path = $backendLogs; Prefix = "backend-default" }
    )
    foreach ($source in $sources) {
        if (-not (Test-Path $source.Path)) { continue }
        Get-ChildItem -LiteralPath $source.Path -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Extension -in ".log", ".txt", ".json" } |
            ForEach-Object {
                $relative = $_.FullName.Substring($source.Path.Length).TrimStart("\")
                $target = Join-Path (Join-Path $resolvedLogDir $source.Prefix) $relative
                New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
                Copy-Item -LiteralPath $_.FullName -Destination $target -Force -ErrorAction SilentlyContinue
            }
    }
}

try {
    New-Item -ItemType Directory -Force $modelsDir | Out-Null

    $install = Start-Process msiexec.exe -Wait -PassThru -ArgumentList @(
        "/i", "`"$resolvedMsi`"", "/qn", "/norestart",
        "ALLOWWEBVIEW2BOOTSTRAP=1", "AUTOLAUNCHAPP=0"
    )
    if ($install.ExitCode -notin 0, 3010) {
        throw "MSI install exited $($install.ExitCode)"
    }
    $installed = $true

    $exeCandidates = @(
        (Join-Path $env:ProgramFiles "VoiceStudio Gemini/omnivoice-studio.exe"),
        (Join-Path $env:LOCALAPPDATA "VoiceStudio Gemini/omnivoice-studio.exe")
    )
    $exe = $exeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $exe) {
        throw "Installed VoiceStudio Gemini executable was not found"
    }

    New-Item -ItemType Directory -Force $appData | Out-Null
    $escapedModelsDir = $modelsDir.Replace("\", "\\")
    $config = @"
{
  "region": "global",
  "setup_complete": true,
  "install_mode": "installed",
  "models_dir": "$escapedModelsDir",
  "torch_variant": "auto"
}
"@
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Join-Path $appData "config.json"), $config, $utf8WithoutBom)

    # Exercise the real packaged bootstrap and backend, but prohibit model
    # downloads and delayed warm-ups. Dependency installation is still real.
    $env:HF_HUB_OFFLINE = "1"
    $env:OMNIVOICE_PRELOAD_TTS_ASR = "0"
    $env:OMNIVOICE_PRELOAD_CAPTURE_ASR = "0"
    $env:OMNIVOICE_PRELOAD_WATERMARK = "0"
    $env:OMNIVOICE_DISABLE_ANALYTICS = "1"
    # The shell and this harness must agree on the same deadline; otherwise
    # the backend could answer after the shell already declared startup failed.
    $env:OMNIVOICE_STARTUP_BUDGET_S = $ReadyTimeoutSeconds.ToString()
    $env:OMNIVOICE_LOG_DIR = $resolvedLogDir
    $env:UV_HTTP_TIMEOUT = "120"
    $env:UV_HTTP_RETRIES = "5"
    $env:GEMINI_API_KEY = $null
    $env:GOOGLE_API_KEY = $null

    $appProcess = Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe -Parent) -PassThru
    $deadline = [DateTime]::UtcNow.AddSeconds($ReadyTimeoutSeconds)
    $lastStep = ""
    $health = $null

    while ([DateTime]::UtcNow -lt $deadline) {
        if ($appProcess.HasExited) {
            throw "VoiceStudio Gemini exited before its backend became ready (exit $($appProcess.ExitCode))"
        }
        try {
            $health = Invoke-SmokeJson $healthUrl
            if ($health.status -eq "ok") { break }
        }
        catch {
            try {
                $startup = Invoke-SmokeJson $progressUrl
                if ($startup.step -and $startup.step -ne $lastStep) {
                    $lastStep = $startup.step
                    Write-Host "Backend startup: $($startup.step) - $($startup.label)"
                }
            }
            catch {
                # The desktop may still be installing Python dependencies.
            }
        }
        Start-Sleep -Seconds 2
    }

    if (-not $health -or $health.status -ne "ok") {
        throw "Backend did not become healthy within $ReadyTimeoutSeconds seconds"
    }

    $engines = Invoke-SmokeJson $enginesUrl
    if ($engines.tts.active -ne "gemini-3.1-flash-tts") {
        throw "Expected Gemini TTS by default, got '$($engines.tts.active)'"
    }

    $checkpoint = Get-ChildItem -LiteralPath $modelsDir -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in ".safetensors", ".ckpt", ".pt", ".pth", ".bin" } |
        Select-Object -First 1
    if ($checkpoint) {
        throw "Local model checkpoint was downloaded unexpectedly: $($checkpoint.FullName)"
    }

    Write-Host "Installed MSI reached /health with Gemini active and no local model checkpoint."
    $smokeSucceeded = $true
}
finally {
    Copy-SmokeDiagnostics

    if ($appProcess -and -not $appProcess.HasExited) {
        Stop-Process -Id $appProcess.Id -Force -ErrorAction SilentlyContinue
        Wait-Process -Id $appProcess.Id -Timeout 15 -ErrorAction SilentlyContinue
    }

    $listener = Get-NetTCPConnection -LocalPort 3900 -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
    }

    if ($installed) {
        $uninstall = Start-Process msiexec.exe -Wait -PassThru -ArgumentList @(
            "/x", "`"$resolvedMsi`"", "/qn", "/norestart"
        )
        if ($uninstall.ExitCode -notin 0, 1605, 3010) {
            Write-Warning "MSI cleanup exited $($uninstall.ExitCode)"
        }
    }
}

if (-not $smokeSucceeded) {
    throw "VoiceStudio Gemini installed-app smoke failed"
}
