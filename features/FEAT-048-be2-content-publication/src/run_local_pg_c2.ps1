<#
Owner-approved portable PostgreSQL 17 C2 tests; no service/Docker/GPU install.
Downloads official EDB archive, runs loopback only and removes this run's cluster.
Secrets remain in the isolated runtime directory, never command arguments/logs.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RuntimeParent,
    [Parameter(Mandatory=$true)][string]$Python
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$runtimeBase = [IO.Path]::GetFullPath($RuntimeParent)
if (-not $runtimeBase.Contains('.runtime')) { throw 'Use an explicit .runtime directory' }
$runName = 'lc-pg-' + [Guid]::NewGuid().ToString('N')
$runRoot = [IO.Path]::GetFullPath((Join-Path $runtimeBase $runName))
if (-not $runRoot.StartsWith($runtimeBase + [IO.Path]::DirectorySeparatorChar)) {
    throw 'Runtime path escaped parent'
}
$null = New-Item -ItemType Directory -Path $runRoot
$clusterPath = Join-Path $runRoot 'data'
$archive = Join-Path $runRoot 'postgres.zip'
$pgctl = $null
$started = $false
$result = 1
$port = $null
$preserved = Join-Path $repoRoot ('.runtime/local-pg-c2/' + $runName)
$null = New-Item -ItemType Directory -Path $preserved -Force

function Invoke-HiddenNative([string]$File, [string[]]$NativeArgs, [string]$Label) {
    $stdout = Join-Path $runRoot ($Label + '.stdout.log')
    $stderr = Join-Path $runRoot ($Label + '.stderr.log')
    $escapedArgs = @($NativeArgs | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' })
    # -Wait waits for descendants on Windows and deadlocks on pg_ctl's server.
    # Wait only for this exact helper process, not the server it starts.
    $process = Start-Process -FilePath $File -ArgumentList $escapedArgs -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) {
        throw "$Label failed: exit $($process.ExitCode); private diagnostics at $runRoot"
    }
    if (Test-Path -LiteralPath $stdout) { Get-Content -LiteralPath $stdout }
}

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $acl = Get-Acl -LiteralPath $runRoot
    $acl.SetAccessRuleProtection($true, $false)
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
        $identity, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow'))
    Set-Acl -LiteralPath $runRoot -AclObject $acl
    $bootstrapPassword = Join-Path $runRoot 'bootstrap.secret'
    $runnerPassword = Join-Path $runRoot 'runner.secret'
    [IO.File]::WriteAllText($bootstrapPassword,
        [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)))
    [IO.File]::WriteAllText($runnerPassword,
        [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)))
    Write-Output 'Downloading official PostgreSQL 17.11 portable archive (about 364 MiB)...'
    $source = 'https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip'
    Invoke-WebRequest -Uri $source -OutFile $archive
    $archiveHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash
    Write-Output ('Archive SHA256: ' + $archiveHash)
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        foreach ($entry in $zip.Entries) {
            $target = [IO.Path]::GetFullPath((Join-Path $runRoot $entry.FullName))
            if (-not $target.StartsWith($runRoot + [IO.Path]::DirectorySeparatorChar)) {
                throw 'Unsafe archive member'
            }
        }
    } finally { $zip.Dispose() }
    Write-Output 'Extracting portable binaries...'
    [IO.Compression.ZipFile]::ExtractToDirectory($archive, $runRoot)
    $bin = Join-Path $runRoot 'pgsql/bin'
    $pgctl = Join-Path $bin 'pg_ctl.exe'
    Invoke-HiddenNative (Join-Path $bin 'postgres.exe') @('--version') 'version'
    Invoke-HiddenNative (Join-Path $bin 'initdb.exe') @(
        '-D', $clusterPath, '-U', 'lc_bootstrap', '--pwfile', $bootstrapPassword,
        '--auth-host=scram-sha-256', '--auth-local=scram-sha-256',
        '--encoding=UTF8', '--locale=C') 'initdb'
    $socket = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
    $socket.Start()
    $port = $socket.LocalEndpoint.Port
    $socket.Stop()
    Write-Output "Starting isolated PostgreSQL on 127.0.0.1:$port..."
    Invoke-HiddenNative $pgctl @('-D', $clusterPath, '-l', (Join-Path $runRoot 'server.log'),
        '-o', "-h 127.0.0.1 -p $port -c shared_buffers=32MB -c max_connections=20",
        '-w', '-t', '30', 'start') 'start'
    $started = $true
    $env:LC_TEST_PG_HOST = '127.0.0.1'
    $env:LC_TEST_PG_PORT = [string]$port
    $env:LC_TEST_PG_USER = 'lc_test_runner'
    $env:LC_TEST_PG_PASSWORD_FILE = $runnerPassword
    $env:LC_PG_BOOTSTRAP_PASSWORD_FILE = $bootstrapPassword
    $env:LC_TEST_ALLOW_CREATE = '1'
    Invoke-HiddenNative $Python @((Join-Path $PSScriptRoot 'bootstrap_local_pg.py')) 'bootstrap'
    Write-Output 'Running actual C2 migration/storage/race suite...'
    & $Python (Join-Path $PSScriptRoot 'run_c2_sql_checks.py')
    $result = $LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $preserved 'environment.json'), (
        @{source=$source; archive_sha256=$archiveHash; version='17.11';
          bind='127.0.0.1'; port=$port; c2_runner_exit=$result} | ConvertTo-Json))
} finally {
    if ($pgctl -and (Test-Path -LiteralPath (Join-Path $clusterPath 'postmaster.pid'))) {
        Invoke-HiddenNative $pgctl @('-D', $clusterPath, '-m', 'fast', '-w', '-t', '30', 'stop') 'stop'
        $started = $false
    }
    foreach ($log in (Get-ChildItem -LiteralPath $runRoot -Filter '*.log' -File)) {
        Copy-Item -LiteralPath $log.FullName -Destination $preserved
    }
    if (-not $started -and -not (Test-Path -LiteralPath (Join-Path $clusterPath 'postmaster.pid'))) {
        $resolvedTarget = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $runRoot).Path)
        if ($resolvedTarget -ne $runRoot -or -not $resolvedTarget.StartsWith(
            $runtimeBase + [IO.Path]::DirectorySeparatorChar) -or
            [IO.Path]::GetFileName($resolvedTarget) -ne $runName) {
            throw 'Refusing cleanup: exact runtime path check failed'
        }
        Remove-Item -LiteralPath $resolvedTarget -Recurse
        Write-Output 'Temporary PostgreSQL cluster, credentials, archive and binaries removed.'
    }
    foreach ($name in @('LC_TEST_PG_HOST','LC_TEST_PG_PORT','LC_TEST_PG_USER',
        'LC_TEST_PG_PASSWORD_FILE','LC_PG_BOOTSTRAP_PASSWORD_FILE','LC_TEST_ALLOW_CREATE')) {
        Remove-Item -LiteralPath ("Env:" + $name) -ErrorAction SilentlyContinue
    }
}
exit $result
