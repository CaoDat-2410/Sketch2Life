$ErrorActionPreference = 'Stop'

$edgePath = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path -LiteralPath $edgePath)) {
    throw 'Microsoft Edge headless renderer was not found.'
}

$directory = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$profilePath = Join-Path $directory '.edge-render-profile'
New-Item -ItemType Directory -Path $profilePath -Force | Out-Null

try {
    $sources = @(
        Get-ChildItem -LiteralPath $directory -Filter 'parent-chicken-v3-step-*.svg' | Sort-Object Name
    ) + @(
        Get-Item -LiteralPath (Join-Path $directory 'parent-chicken-v3-final-overlay.svg')
    ) + @(
        Get-Item -LiteralPath (Join-Path $directory 'parent-chicken-v3-reference.svg')
    )

    foreach ($source in $sources) {
        $target = [System.IO.Path]::ChangeExtension($source.FullName, '.png')
        $uri = [System.Uri]::new($source.FullName).AbsoluteUri
        $arguments = @(
            '--headless=new',
            '--disable-gpu',
            '--hide-scrollbars',
            '--no-first-run',
            '--no-default-browser-check',
            '--window-size=1024,1024',
            "--user-data-dir=$profilePath",
            "--screenshot=$target",
            $uri
        )
        $process = Start-Process -FilePath $edgePath -ArgumentList $arguments -WindowStyle Hidden -PassThru -Wait
        if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $target)) {
            throw "Failed to render $($source.Name) (exit $($process.ExitCode))."
        }
        $image = Get-Item -LiteralPath $target
        Write-Output "$($source.Name) -> $($image.Length) bytes"
    }
}
finally {
    if (Test-Path -LiteralPath $profilePath) {
        Remove-Item -LiteralPath $profilePath -Recurse -Force
    }
}
