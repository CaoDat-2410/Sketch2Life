[CmdletBinding()]
param(
  [ValidateSet('lan', 'reverse')]
  [string]$Mode = 'lan',
  [ValidateRange(1, 65535)]
  [int]$Port = 8081,
  [switch]$LaunchAndroid
)

$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = (Resolve-Path -LiteralPath (Join-Path $appRoot '..\..')).Path
$rootEnvPath = $null
$searchDirectory = $workspaceRoot
while ($searchDirectory) {
  if ((Test-Path -LiteralPath (Join-Path $searchDirectory 'pnpm-workspace.yaml')) -and
      (Test-Path -LiteralPath (Join-Path $searchDirectory '.env'))) {
    $rootEnvPath = Join-Path $searchDirectory '.env'
    break
  }
  $parentDirectory = Split-Path -Parent $searchDirectory
  if (-not $parentDirectory -or $parentDirectory -eq $searchDirectory) { break }
  $searchDirectory = $parentDirectory
}

if (-not $rootEnvPath) {
  throw 'Could not find the canonical root .env beside a pnpm-workspace.yaml.'
}

$apiLine = Get-Content -LiteralPath $rootEnvPath |
  Where-Object { $_ -match '^\s*(?:export\s+)?SKETCH2LIFE_MOBILE_API_BASE_URL\s*=' } |
  Select-Object -Last 1
if (-not $apiLine -or $apiLine -notmatch '^\s*(?:export\s+)?SKETCH2LIFE_MOBILE_API_BASE_URL\s*=\s*(.*?)\s*$') {
  throw 'SKETCH2LIFE_MOBILE_API_BASE_URL is missing from the root .env file.'
}

$apiBaseUrl = $matches[1].Trim()
if (($apiBaseUrl.StartsWith('"') -and $apiBaseUrl.EndsWith('"')) -or
    ($apiBaseUrl.StartsWith("'") -and $apiBaseUrl.EndsWith("'"))) {
  $apiBaseUrl = $apiBaseUrl.Substring(1, $apiBaseUrl.Length - 2)
}
if ($apiBaseUrl -notmatch '^https?://[^/]+') {
  throw 'SKETCH2LIFE_MOBILE_API_BASE_URL in the root .env must be an absolute HTTP(S) URL.'
}

# Ensure both Expo's manifest config and runtime API URL are derived from the
# single canonical .env and cannot be shadowed by stale inherited shell values.
Remove-Item Env:SKETCH2LIFE_MOBILE_API_BASE_URL -ErrorAction SilentlyContinue
$env:SKETCH2LIFE_MOBILE_API_BASE_URL = $apiBaseUrl
Remove-Item Env:EXPO_PUBLIC_API_URL -ErrorAction SilentlyContinue
$env:EXPO_PUBLIC_API_URL = $apiBaseUrl

function Resolve-Adb {
  $onPath = Get-Command adb.exe -ErrorAction SilentlyContinue
  if ($onPath) {
    return $onPath.Source
  }

  $sdkRoots = @(
    $env:ANDROID_HOME,
    $env:ANDROID_SDK_ROOT,
    $(if ($env:LOCALAPPDATA) { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }),
    'D:\AndroidStudio'
  ) | Where-Object { $_ } | Select-Object -Unique

  foreach ($sdkRoot in $sdkRoots) {
    $candidate = Join-Path $sdkRoot 'platform-tools\adb.exe'
    if (Test-Path -LiteralPath $candidate) {
      return $candidate
    }
  }

  throw 'ADB was not found. Install Android SDK Platform-Tools or use -Mode lan for a physical device.'
}

function Resolve-AdbServerPort {
  param([string]$AdbPath)

  foreach ($candidate in @(5037, 5038)) {
    $previousErrorAction = $ErrorActionPreference
    try {
      $ErrorActionPreference = 'Continue'
      $probe = @(& $AdbPath -P $candidate devices 2>$null)
      $probeExitCode = $LASTEXITCODE
    } finally {
      $ErrorActionPreference = $previousErrorAction
    }
    if ($probeExitCode -eq 0 -and ($probe -notmatch 'cannot connect|failed to check server version')) {
      return $candidate
    }
  }

  throw 'No healthy ADB server was found on ports 5037 or 5038. Start Android Studio or the ADB server, then retry.'
}

function Resolve-AdbDevice {
  param(
    [string]$AdbPath,
    [int]$ServerPort
  )

  $deviceLine = @(& $AdbPath -P $ServerPort devices 2>$null) |
    Where-Object { $_ -match '^\S+\s+device\s*$' } |
    Select-Object -First 1

  if (-not $deviceLine) {
    throw "ADB server $ServerPort has no ready device. Start an emulator or connect an Android device, then retry."
  }

  return (($deviceLine.ToString().Trim()) -split '\s+')[0]
}

function Resolve-LanAddress {
  $addresses = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object {
      $_.AddressState -eq 'Preferred' -and
      $_.IPAddress -notlike '127.*' -and
      $_.IPAddress -notlike '169.254.*'
    })

  $privateAddress = $addresses |
    Where-Object { $_.IPAddress -match '^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[0-1])\.)' } |
    Select-Object -First 1 -ExpandProperty IPAddress

  if ($privateAddress) {
    return $privateAddress
  }

  return $addresses | Select-Object -First 1 -ExpandProperty IPAddress
}

$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
if (-not $pnpm) {
  throw 'pnpm was not found on PATH. Install pnpm 11 or activate the repository toolchain.'
}

# The native dev client requests the app's `index` entry. In this monorepo,
# Expo's workspace-root detection would resolve that entry from the repository root.
$env:EXPO_NO_METRO_WORKSPACE_ROOT = '1'

$adb = $null
$adbServerPort = $null
$adbDevice = $null
if ($Mode -eq 'reverse' -or $LaunchAndroid) {
  $adb = Resolve-Adb
  $adbServerPort = Resolve-AdbServerPort -AdbPath $adb
  $adbDevice = Resolve-AdbDevice -AdbPath $adb -ServerPort $adbServerPort
  $env:ADB_SERVER_SOCKET = "tcp:127.0.0.1:$adbServerPort"
  Write-Host "ADB device: $adbDevice via server port $adbServerPort"
}

if ($Mode -eq 'reverse') {
  & $adb -P $adbServerPort -s $adbDevice reverse "tcp:$Port" "tcp:$Port"
  if ($LASTEXITCODE -ne 0) {
    throw "ADB could not reverse tcp:$Port. Start an emulator or connect an Android device, then retry."
  }
  Write-Host "ADB reverse is active on ${adbDevice}: tcp:$Port -> tcp:$Port"
  $hostMode = '--localhost'
  $env:REACT_NATIVE_PACKAGER_HOSTNAME = '127.0.0.1'
  $env:EXPO_PACKAGER_PROXY_URL = "http://127.0.0.1:$Port"
} else {
  $lanAddress = Resolve-LanAddress
  if ($lanAddress) {
    $env:REACT_NATIVE_PACKAGER_HOSTNAME = $lanAddress
    if ($env:EXPO_PACKAGER_PROXY_URL -match '^(https?://)?(localhost|127\.0\.0\.1)(:|/)') {
      Remove-Item Env:EXPO_PACKAGER_PROXY_URL -ErrorAction SilentlyContinue
    }
    Write-Host "Metro host override: $lanAddress"
  } else {
    Write-Warning 'No LAN IPv4 address was found; Expo will choose its own host.'
  }
  Write-Host 'Starting Expo in LAN mode. Use the host IP shown by Expo on the Android device.'
  $hostMode = '--lan'
}

if ($LaunchAndroid) {
  & $pnpm.Source --dir $appRoot exec expo run:android --variant debug --port $Port
} else {
  & $pnpm.Source --dir $appRoot exec expo start --dev-client $hostMode --port $Port
}
exit $LASTEXITCODE
