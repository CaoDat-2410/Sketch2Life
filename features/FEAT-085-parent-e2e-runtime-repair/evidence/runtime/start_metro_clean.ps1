param(
  [ValidateRange(1, 65535)]
  [int]$Port = 8081
)

$ErrorActionPreference = 'Stop'
$workspace = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..\..\..')).Path
$launcher = Join-Path $workspace 'apps\ui-mobile\scripts\start-android-dev.ps1'
if (-not (Test-Path -LiteralPath $launcher)) {
  throw "Android dev launcher is missing: $launcher"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcher -Mode lan -Port $Port
exit $LASTEXITCODE
