# Stop only what Addendum 36 started. Leaves the Modal video app and volumes untouched.
$wt = (& git -C $PSScriptRoot rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $wt) { throw 'Could not locate the FEAT-081 worktree from this script.' }
$projectRoot = $wt
while (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) {
  $parent = Split-Path -Parent $projectRoot
  if (-not $parent -or $parent -eq $projectRoot) { throw 'Could not locate the ignored project .env above the worktree.' }
  $projectRoot = $parent
}
$envFile = Join-Path $projectRoot '.env'
$venvModal = Join-Path $projectRoot '.venv-modal\Scripts'
if (Test-Path (Join-Path $venvModal 'modal.exe')) { $env:PATH = "$venvModal;$env:PATH" }
Set-Location $wt
Start-Transcript -Path (Join-Path $PSScriptRoot 'stop_rev20b.log') -Force | Out-Null
foreach ($line in Get-Content $envFile) {
  if ($line -match '^(MODAL_TOKEN_ID|MODAL_TOKEN_SECRET)=(.*)$') { Set-Item -Path "env:$($Matches[1])" -Value $Matches[2] }
}
docker compose --env-file $envFile -p s2l-feat081-rev20 stop
modal app stop --env=dev --yes sketch2life-srs23-drawing-vlm-dev
modal app stop --env=dev --yes sketch2life-srs23-language-audio-dev
modal app list --env=dev
$metroPidPath = Join-Path $PSScriptRoot 'metro.pid'
if (Test-Path -LiteralPath $metroPidPath) {
  $metroPid = 0
  if ([int]::TryParse((Get-Content -LiteralPath $metroPidPath -Raw), [ref]$metroPid)) {
    $metro = Get-CimInstance Win32_Process -Filter "ProcessId = $metroPid" -ErrorAction SilentlyContinue
    if ($metro -and $metro.CommandLine -match 'start:android-reverse') {
      & taskkill.exe /PID $metroPid /T /F | Out-Null
    } elseif ($metro) {
      Write-Warning "PID $metroPid no longer matches the task Metro command; leaving it running."
    }
  }
  Remove-Item -LiteralPath $metroPidPath -Force
}
Stop-Transcript | Out-Null
