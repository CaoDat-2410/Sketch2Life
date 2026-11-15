$ErrorActionPreference = 'Stop'

$evidenceDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$edgeExecutable = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path -LiteralPath $edgeExecutable)) {
    throw 'Microsoft Edge was not found at the expected Windows installation path.'
}

function Invoke-SvgScreenshot {
    param(
        [Parameter(Mandatory = $true)][string]$sourceFilename,
        [Parameter(Mandatory = $true)][string]$outputFilename
    )

    $sourcePath = Join-Path $evidenceDirectory $sourceFilename
    $outputPath = Join-Path $evidenceDirectory $outputFilename
    if (Test-Path -LiteralPath $outputPath) {
        return
    }
    $profilePath = Join-Path $env:TEMP ('sketch2life-svg-v7-' + [guid]::NewGuid().ToString('N'))
    $tempRoot = [System.IO.Path]::GetFullPath($env:TEMP).TrimEnd('\') + '\'
    $resolvedProfilePath = [System.IO.Path]::GetFullPath($profilePath)
    if (-not $resolvedProfilePath.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'Temporary browser profile resolved outside the system temp directory.'
    }
    $sourceUrl = 'file:///' + ($sourcePath -replace '\\', '/')
    $arguments = @(
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu',
        '--no-first-run',
        ('--user-data-dir=' + $resolvedProfilePath),
        '--window-size=1024,1024',
        '--virtual-time-budget=1000',
        ('--screenshot=' + $outputPath),
        $sourceUrl
    )
    try {
        $process = Start-Process -FilePath $edgeExecutable -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
        if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $outputPath)) {
            throw ('SVG screenshot failed: ' + $sourceFilename + ' (exit ' + $process.ExitCode + ')')
        }
    }
    finally {
        if (Test-Path -LiteralPath $resolvedProfilePath) {
            Remove-Item -LiteralPath $resolvedProfilePath -Recurse -Force
        }
    }
}

for ($stepIndex = 1; $stepIndex -le 8; $stepIndex++) {
    Invoke-SvgScreenshot `
        -sourceFilename ('parent-chicken-v7-step-' + $stepIndex + '.svg') `
        -outputFilename ('parent-chicken-v7-step-' + $stepIndex + '-1024.png')
}

Invoke-SvgScreenshot `
    -sourceFilename 'parent-chicken-v7-final-line-guide.svg' `
    -outputFilename 'parent-chicken-v7-final-line-guide-1024.png'
Invoke-SvgScreenshot `
    -sourceFilename 'parent-chicken-v7-reference.svg' `
    -outputFilename 'parent-chicken-v7-reference-1024.png'

Write-Output 'Rendered eight API-derived source-path stages, final line guide and separate color reference at 1024x1024.'
