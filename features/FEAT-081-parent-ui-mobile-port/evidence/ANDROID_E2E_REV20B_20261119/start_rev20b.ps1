# FEAT-081 Addendum 36 - start the second bounded Parent E2E path (no inference is sent by this script).
$ErrorActionPreference = 'Stop'
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
$composeOverride = Join-Path $PSScriptRoot 'compose.rev20b.override.yaml'
if (Test-Path (Join-Path $venvModal 'modal.exe')) { $env:PATH = "$venvModal;$env:PATH" }
# Modal's CLI emits Unicode status glyphs. Force Python's stdio encoding so
# Windows PowerShell 5's legacy code page cannot abort a successful deploy.
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$log = Join-Path $PSScriptRoot 'start_rev20b.log'
Set-Location $wt
Start-Transcript -Path $log -Force | Out-Null
try {
  # Modal CLI credentials come only from the ignored root .env and stay in this process.
  foreach ($line in Get-Content $envFile) {
    if ($line -match '^(MODAL_TOKEN_ID|MODAL_TOKEN_SECRET)=(.*)$') { Set-Item -Path "env:$($Matches[1])" -Value $Matches[2] }
  }

  function Invoke-Pnpm { param([Parameter(ValueFromRemainingArguments)]$a)
    if (Get-Command pnpm -ErrorAction SilentlyContinue) { & pnpm @a }
    elseif (Get-Command corepack -ErrorAction SilentlyContinue) { & corepack pnpm @a }
    else { throw 'pnpm/corepack not found on PATH' }
    if ($LASTEXITCODE -ne 0) { throw "pnpm $a failed ($LASTEXITCODE)" } }
  foreach ($tool in 'docker','modal') { if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "$tool not found on PATH" } }

  Write-Host '== 1/5 mobile tests + typecheck'
  Invoke-Pnpm --dir apps/ui-mobile test
  Invoke-Pnpm --dir apps/ui-mobile typecheck

  Write-Host '== 2/5 deploy Modal non-video apps (scale-to-zero, no call)'
  foreach ($app in 'drawing_vlm_app.py','language_audio_app.py') {
    modal deploy --env=dev "deployment/modal/srs_v23/$app"
    if ($LASTEXITCODE -ne 0) { throw "modal deploy $app failed" }
  }
  modal app list --env=dev
  if ($LASTEXITCODE -ne 0) { throw 'modal app list failed' }

  Write-Host '== 3/5 rebuild + start task-local backend'
  if (-not (Test-Path -LiteralPath $composeOverride)) { throw "Missing Compose override: $composeOverride" }
  $composeFile = Join-Path $wt 'compose.yaml'
  docker compose --env-file $envFile -f $composeFile -f $composeOverride -p s2l-feat081-rev20 up -d --build
  if ($LASTEXITCODE -ne 0) { docker ps --format '{{.Names}}  {{.Ports}}'; throw 'docker compose up failed - see port owners above' }
  $apiState = docker inspect -f '{{.State.Status}}' s2l-feat081-rev20-api-1
  if ($apiState -ne 'running') { throw "task API container is $apiState, not running" }

  $apiPort = 0
  foreach ($line in Get-Content $envFile) {
    if ($line -match '^SKETCH2LIFE_API_PORT=(\d+)$') { $apiPort = [int]$Matches[1] }
  }
  if ($apiPort -lt 1) { throw 'SKETCH2LIFE_API_PORT is missing or invalid in the root .env' }
  $mobileBaseUrl = ''
  foreach ($line in Get-Content $envFile) {
    if ($line -match '^SKETCH2LIFE_MOBILE_API_BASE_URL=(.*)$') { $mobileBaseUrl = $Matches[1] }
  }
  if ($mobileBaseUrl -notmatch ":$apiPort/?$") { throw 'SKETCH2LIFE_MOBILE_API_BASE_URL does not target the configured API port' }

  Write-Host '== 4/5 wait for API health'
  $ok = $false
  foreach ($i in 1..40) {
    try { if ((Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$apiPort/health" -TimeoutSec 3).StatusCode -eq 200) { $ok = $true; break } } catch {}
    Start-Sleep -Seconds 5
  }
  if (-not $ok) { throw 'API /health did not become ready' }
  $containerHealth = docker exec s2l-feat081-rev20-api-1 python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read().decode())"
  if ($LASTEXITCODE -ne 0) { throw 'API container-local /health failed' }
  Write-Host "Host and container API health OK on port ${apiPort}: $containerHealth"

  Write-Host '== 5/5 start Metro for the Android dev client (separate window)'
  # Metro runs from this linked worktree, while the single ignored .env is in
  # the main project root. Forward only the public Expo/Firebase config.
  $publicExpoKeys = @(
    'VITE_FIREBASE_API_KEY',
    'VITE_FIREBASE_AUTH_DOMAIN',
    'VITE_FIREBASE_PROJECT_ID',
    'VITE_FIREBASE_APP_ID',
    'SKETCH2LIFE_MOBILE_API_BASE_URL',
    'SKETCH2LIFE_GOOGLE_WEB_CLIENT_ID',
    'SKETCH2LIFE_GOOGLE_ANDROID_CLIENT_ID'
  )
  foreach ($line in Get-Content $envFile) {
    if ($line -match '^([A-Z0-9_]+)=(.*)$' -and $Matches[1] -in $publicExpoKeys) {
      $name = $Matches[1]
      $value = $Matches[2].Trim()
      if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
        $value = $value.Substring(1, $value.Length - 2)
      }
      if ($value) { Set-Item -Path "Env:$name" -Value $value }
    }
  }
  foreach ($requiredKey in @('VITE_FIREBASE_API_KEY','VITE_FIREBASE_PROJECT_ID','VITE_FIREBASE_APP_ID','SKETCH2LIFE_MOBILE_API_BASE_URL')) {
    if (-not (Get-Item -Path "Env:$requiredKey" -ErrorAction SilentlyContinue)) { throw "Required public Expo setting $requiredKey is missing from the root .env." }
  }
  $env:EXPO_PUBLIC_API_URL = $env:SKETCH2LIFE_MOBILE_API_BASE_URL
  # Modal credentials are needed only by the deploy CLI; do not pass them to Metro.
  Remove-Item Env:MODAL_TOKEN_ID,Env:MODAL_TOKEN_SECRET -ErrorAction SilentlyContinue
  Write-Host 'Forwarded public Firebase/API settings to Metro; provider credentials cleared from the Metro environment.'
  $pn = Get-Command pnpm -ErrorAction SilentlyContinue
  if ($pn -and $pn.CommandType -eq 'Alias') { $pn = Get-Command $pn.Definition }
  if ($pn -and $pn.Source) { $env:PATH = "$(Split-Path $pn.Source);$env:PATH" }
  $metroProcess = Start-Process -FilePath (Get-Process -Id $PID).Path -PassThru -ArgumentList '-NoExit','-NoProfile','-Command',"Set-Location '$wt'; pnpm --dir apps/ui-mobile start:android-reverse"
  Set-Content -LiteralPath (Join-Path $PSScriptRoot 'metro.pid') -Value $metroProcess.Id -NoNewline
  Write-Host 'DONE - open the Sketch2Life dev app on the emulator.'
} finally { Stop-Transcript | Out-Null }
