<# Approved combined own10/11/13 SQL verification; no service/global PATH changes. #>
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
$python = Join-Path $repoRoot 'backend/.venv/Scripts/python.exe'
$runtimeBase = Join-Path $repoRoot '.runtime/be2-101113-pg'
$null = New-Item -ItemType Directory -Path $runtimeBase -Force
$runName = 'pg-' + [Guid]::NewGuid().ToString('N')
$runRoot = [IO.Path]::GetFullPath((Join-Path $runtimeBase $runName))
if (-not $runRoot.StartsWith($runtimeBase + [IO.Path]::DirectorySeparatorChar)) {
    throw 'Invalid exact runtime target'
}
$null = New-Item -ItemType Directory -Path $runRoot
$cluster = Join-Path $runRoot 'data'
$archive = Join-Path $runRoot 'postgres.zip'
$privateFile = Join-Path $runRoot 'bootstrap.secret'
$pgctl = Join-Path $runRoot 'pgsql/bin/pg_ctl.exe'
$port = $null
$result = 1
$cleanup = $false

function Invoke-HiddenNative([string]$File, [string[]]$NativeArgs, [string]$Label) {
    $stdout = Join-Path $runRoot ($Label + '.stdout.log')
    $stderr = Join-Path $runRoot ($Label + '.stderr.log')
    $escaped = @($NativeArgs | ForEach-Object { '"' + $_.Replace('"', '\"') + '"' })
    $process = Start-Process -FilePath $File -ArgumentList $escaped -WindowStyle Hidden `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    $process.WaitForExit() # Not -Wait: pg_ctl descendants include the server.
    if ($process.ExitCode -ne 0) { throw "$Label failed; private diagnostics retained" }
}

try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $acl = Get-Acl -LiteralPath $runRoot
    $acl.SetAccessRuleProtection($true, $false)
    $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new(
        $identity, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow'))
    Set-Acl -LiteralPath $runRoot -AclObject $acl
    [IO.File]::WriteAllText($privateFile,
        [Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(32)))
    $source = 'https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip'
    Write-Output "Runtime: $runRoot"
    Write-Output 'Downloading official portable PostgreSQL17 archive...'
    Invoke-WebRequest -Uri $source -OutFile $archive
    $archiveHash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($archiveHash -ne '80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f') {
        throw 'Archive bytes differ from reviewed previous17.11 receipt; stop for source review'
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        foreach ($entry in $zip.Entries) {
            $target = [IO.Path]::GetFullPath((Join-Path $runRoot $entry.FullName))
            if (-not $target.StartsWith($runRoot + [IO.Path]::DirectorySeparatorChar)) {
                throw 'Unsafe archive member'
            }
            # Extract only portable runtime prerequisites, not installers or tools.
            if ($entry.FullName -match '^pgsql/(bin|lib|share)/' -and -not $entry.FullName.EndsWith('/')) {
                $null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($target)) -Force
                [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $target, $false)
            }
        }
    } finally { $zip.Dispose() }
    Invoke-HiddenNative (Join-Path $runRoot 'pgsql/bin/initdb.exe') @(
        '-D', $cluster, '-U', 'be2_pg_bootstrap', '--pwfile', $privateFile,
        '--auth-host=scram-sha-256', '--auth-local=scram-sha-256', '--encoding=UTF8', '--locale=C') 'initdb'
    $socket = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
    $socket.Start()
    $port = $socket.LocalEndpoint.Port
    $socket.Stop()
    Invoke-HiddenNative $pgctl @('-D', $cluster, '-l', (Join-Path $runRoot 'private-server.log'),
        '-o', "-h 127.0.0.1 -p $port -c shared_buffers=32MB -c max_connections=20", '-w', '-t', '30', 'start') 'start'
    $env:BE2_SQL_RUN_ROOT = $runRoot
    $env:BE2_SQL_PORT = [string]$port
    $env:BE2_SQL_BOOTSTRAP_FILE = $privateFile
    Write-Output 'Fresh isolated loopback cluster ready; executing exact14/17/11 SQL suites...'
    & $python (Join-Path $PSScriptRoot 'run_local_pg_checks.py')
    $result = $LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $runRoot 'environment.json'), (@{
        version='17.11'; archive_sha256=$archiveHash; source=$source; bind='127.0.0.1';
        port=$port; run_exit=$result; global_service=$false; shared_db=$false
    } | ConvertTo-Json))
} finally {
    if ((Test-Path -LiteralPath $pgctl) -and (Test-Path -LiteralPath (Join-Path $cluster 'postmaster.pid'))) {
        Invoke-HiddenNative $pgctl @('-D', $cluster, '-m', 'fast', '-w', '-t', '30', 'stop') 'stop'
    }
    $ownProcesses = @(Get-Process postgres,pg_ctl,initdb -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -and $_.Path.StartsWith($runRoot + [IO.Path]::DirectorySeparatorChar) })
    if ($ownProcesses.Count -ne 0 -or (Test-Path -LiteralPath (Join-Path $cluster 'postmaster.pid'))) {
        throw 'Own cluster not fully stopped; refusing deletion'
    }
    foreach ($relative in @('data','pgsql','postgres.zip','bootstrap.secret','private-server.log')) {
        $target = Join-Path $runRoot $relative
        if (Test-Path -LiteralPath $target) {
            $resolved = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $target).Path)
            if ($resolved -ne [IO.Path]::GetFullPath($target) -or
                -not $resolved.StartsWith($runRoot + [IO.Path]::DirectorySeparatorChar) -or
                ((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
                throw 'Refusing cleanup outside exact new run directory'
            }
            Remove-Item -LiteralPath $resolved -Recurse -Force
        }
    }
    $cleanup = $true
    [IO.File]::WriteAllText((Join-Path $runRoot 'cleanup.json'), (@{
        stopped=$true; own_process_count=$ownProcesses.Count; removed_private_targets=$true;
        cleanup=$cleanup; isolated_port=$port
    } | ConvertTo-Json))
    foreach ($name in @('BE2_SQL_RUN_ROOT','BE2_SQL_PORT','BE2_SQL_BOOTSTRAP_FILE')) {
        Remove-Item -LiteralPath ('Env:' + $name) -ErrorAction SilentlyContinue
    }
    Write-Output "Cleanup complete; sanitized SQL receipts retained: $runRoot"
}
exit $result
