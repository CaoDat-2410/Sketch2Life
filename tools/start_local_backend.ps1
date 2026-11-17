param(
    [int]$Port = 8000,
    [switch]$SourceOnly
)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot 'backend/.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Backend virtual environment is missing. Follow backend/README.md setup.'
}

# These are server-only local preview controls. Provider configuration remains
# in ignored local settings; starting the API does not submit an inference job.
$env:SKETCH2LIFE_ENV = 'local'
$env:SKETCH2LIFE_PIXI_SHOW_PLANNER_ENABLED = (-not $SourceOnly).ToString().ToLowerInvariant()
$env:SKETCH2LIFE_PIXI_SPRITE_CYCLE_DEV_PREVIEW_ENABLED = (-not $SourceOnly).ToString().ToLowerInvariant()
Write-Host "Starting local API on port $Port; Pixi sprite preview: $(-not $SourceOnly)"
Push-Location $taskRoot
try {
    & $taskPython -m uvicorn sketch2life.interfaces.http.app:create_app --factory --app-dir backend/src --host 0.0.0.0 --port $Port
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
