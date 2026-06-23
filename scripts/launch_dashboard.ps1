param(
    [int]$Port = 8044,
    [int]$MaxPort = 8054
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $RepoRoot "logs"
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$PythonExe = if (Test-Path -LiteralPath $VenvPython) { $VenvPython } else { "python" }

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-FeintLexHealth {
    param([int]$CandidatePort)

    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:$CandidatePort/health" -TimeoutSec 2
        return $health.app -eq "FeintLex"
    }
    catch {
        return $false
    }
}

function Start-FeintLexServer {
    param([int]$CandidatePort)

    $stdout = Join-Path $LogDir "dashboard-$CandidatePort.out.log"
    $stderr = Join-Path $LogDir "dashboard-$CandidatePort.err.log"
    $arguments = @(
        "-m",
        "uvicorn",
        "feintlex.app:app",
        "--host",
        "127.0.0.1",
        "--port",
        "$CandidatePort"
    )

    return Start-Process `
        -FilePath $PythonExe `
        -ArgumentList $arguments `
        -WorkingDirectory $RepoRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
}

for ($candidate = $Port; $candidate -le $MaxPort; $candidate++) {
    if (Test-FeintLexHealth -CandidatePort $candidate) {
        Start-Process "http://127.0.0.1:$candidate/dashboard"
        exit 0
    }

    $process = Start-FeintLexServer -CandidatePort $candidate
    for ($attempt = 0; $attempt -lt 24; $attempt++) {
        if (Test-FeintLexHealth -CandidatePort $candidate) {
            Start-Process "http://127.0.0.1:$candidate/dashboard"
            exit 0
        }
        if ($process.HasExited) {
            break
        }
        Start-Sleep -Milliseconds 500
    }

    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
}

throw "FeintLex dashboard did not start on ports $Port through $MaxPort."
