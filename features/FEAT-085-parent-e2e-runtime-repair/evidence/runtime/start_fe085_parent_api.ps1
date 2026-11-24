[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateNotNullOrEmpty()]
  [string]$ModalProfile
)

$ErrorActionPreference = 'Stop'

# Keep the task API on the explicitly selected Modal profile. Read its token
# only into this process environment so Compose can pass it to the container;
# never persist or print either value and never rely on stale project .env data.
$modalConfigPath = Join-Path $env:USERPROFILE '.modal.toml'
if (-not (Test-Path -LiteralPath $modalConfigPath -PathType Leaf)) {
  throw 'Modal CLI profile config is missing; authenticate the selected profile first.'
}
$modalConfig = [System.IO.File]::ReadAllText($modalConfigPath)
$profileSectionPattern = "(?ms)^\[$([regex]::Escape($ModalProfile))\]\s*\r?\n(?<body>.*?)(?=^\[|\z)"
$profileSection = [regex]::Match($modalConfig, $profileSectionPattern)
if (-not $profileSection.Success) {
  throw 'The requested Modal profile is not present in the local CLI config.'
}
$tokenIdMatch = [regex]::Match($profileSection.Groups['body'].Value, '(?m)^\s*token_id\s*=\s*"([^"]+)"\s*$')
$tokenSecretMatch = [regex]::Match($profileSection.Groups['body'].Value, '(?m)^\s*token_secret\s*=\s*"([^"]+)"\s*$')
if (-not $tokenIdMatch.Success -or -not $tokenSecretMatch.Success) {
  throw 'The requested Modal profile does not have both token fields configured.'
}
$env:MODAL_TOKEN_ID = $tokenIdMatch.Groups[1].Value
$env:MODAL_TOKEN_SECRET = $tokenSecretMatch.Groups[1].Value

$repoRoot = (& git -C $PSScriptRoot rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $repoRoot) {
  throw 'Could not locate the active CAPSTONE worktree.'
}

# Worktrees intentionally do not copy the ignored project .env. Walk upward to
# reuse the single CAPSTONE .env; never create or print a second credential file.
$cursor = $repoRoot
$envPath = $null
for ($i = 0; $i -lt 4 -and $cursor; $i++) {
  $candidate = Join-Path $cursor '.env'
  if (Test-Path -LiteralPath $candidate -PathType Leaf) {
    $envPath = (Resolve-Path -LiteralPath $candidate).Path
    break
  }
  $cursor = Split-Path -Parent $cursor
}
if (-not $envPath) {
  throw 'Could not find the shared CAPSTONE .env. Place credentials only in the project root .env.'
}

$composeFile = Join-Path $repoRoot 'compose.yaml'
$overrideFile = Join-Path $repoRoot 'features/FEAT-085-parent-e2e-runtime-repair/evidence/runtime/compose.fe085.override.yaml'
foreach ($path in @($composeFile, $overrideFile)) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    throw "Required Compose file is missing: $path"
  }
}

# The Android app targets this one canonical local stack. Stop any other
# Compose project whose working directory is inside CAPSTONE, regardless of
# worktree/project name. Keep containers and volumes so their state can still
# be resumed deliberately later. Unrelated projects outside CAPSTONE are left
# untouched.
$canonicalProjectName = 'fe085-parent-api'
$capstoneRoot = (Split-Path -Parent $envPath).TrimEnd('\')
$runningContainerIds = @(& docker ps -q)
if ($LASTEXITCODE -ne 0) {
  throw 'Could not inspect running Docker containers.'
}
foreach ($containerId in $runningContainerIds) {
  $composeLabels = & docker inspect --format '{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.project.working_dir"}}' $containerId
  if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect Docker Compose labels for container $containerId."
  }
  $labelParts = $composeLabels -split '\|', 2
  if ($labelParts.Count -lt 2) { continue }
  $projectName = $labelParts[0].Trim()
  $workingDirectory = $labelParts[1].Trim()
  $insideCapstone = $workingDirectory.Equals($capstoneRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
    $workingDirectory.StartsWith("$capstoneRoot\", [System.StringComparison]::OrdinalIgnoreCase)
  if ($insideCapstone -and $projectName -ne $canonicalProjectName) {
    Write-Output "Stopping duplicate CAPSTONE Compose container: $containerId (project $projectName)"
    & docker stop $containerId
    if ($LASTEXITCODE -ne 0) {
      throw "Could not stop duplicate CAPSTONE Compose container: $containerId"
    }
  }
}

$composeArgs = @(
  '--env-file', $envPath,
  '--project-directory', $repoRoot,
  '-p', 'fe085-parent-api',
  '-f', $composeFile,
  '-f', $overrideFile
)
& docker compose @composeArgs up -d --build api
if ($LASTEXITCODE -ne 0) {
  throw 'Docker Compose failed to start the canonical FEAT-085 stack.'
}

$container = 'fe085-parent-api-20261123'
$deadline = [DateTime]::UtcNow.AddMinutes(3)
do {
  $health = (& docker inspect --format '{{.State.Health.Status}}' $container 2>$null).Trim()
  if ($health -eq 'healthy') { break }
  if ($health -eq 'unhealthy') { throw 'The isolated FEAT-085 API container is unhealthy.' }
  Start-Sleep -Seconds 3
} while ([DateTime]::UtcNow -lt $deadline)
if ($health -ne 'healthy') {
  throw 'Timed out waiting for the isolated FEAT-085 API health check.'
}

$probeOutput = & docker exec $container python -c "import os; from sketch2life.infrastructure.config.settings import get_settings; from sketch2life.infrastructure.identity.firebase_admin_app import get_firebase_admin_app; settings=get_settings(); get_firebase_admin_app(settings); print('auth_provider=' + str(settings.auth_provider)); print('firebase_project_configured=' + str(bool(settings.firebase_project_id))); print('firebase_admin_ready=True'); print('modal_token_id_configured=' + str(bool(os.getenv('MODAL_TOKEN_ID')))); print('modal_token_secret_configured=' + str(bool(os.getenv('MODAL_TOKEN_SECRET')))); print('database_url_configured=' + str(bool(settings.database_url)))"
if ($LASTEXITCODE -ne 0) {
  throw 'Could not verify the isolated API runtime configuration.'
}
$probeText = $probeOutput -join "`n"
Write-Output $probeText
if (($probeText -notmatch 'auth_provider=firebase') -or
    ($probeText -notmatch 'firebase_project_configured=True') -or
    ($probeText -notmatch 'firebase_admin_ready=True') -or
    ($probeText -notmatch 'modal_token_id_configured=True') -or
    ($probeText -notmatch 'modal_token_secret_configured=True') -or
    ($probeText -notmatch 'database_url_configured=True')) {
  throw 'The API is healthy but one or more required Firebase, Modal, or database settings are unavailable.'
}

try {
  $healthBody = Invoke-RestMethod -Uri 'http://127.0.0.1:18001/health' -TimeoutSec 10
} catch {
  throw 'The isolated FEAT-085 API health endpoint did not respond.'
}
if ($healthBody.status -ne 'ok') {
  throw 'The isolated FEAT-085 API returned a non-OK health state.'
}
Write-Output 'FEAT-085 API health=ok'
