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
    $profileDirectory = Join-Path $env:TEMP ('sketch2life-svg-render-' + [guid]::NewGuid().ToString('N'))
    $sourceUrl = 'file:///' + ($sourcePath -replace '\\', '/')
    $arguments = @(
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu',
        '--no-first-run',
        ('--user-data-dir=' + $profileDirectory),
        '--window-size=1024,1024',
        '--virtual-time-budget=1000',
        ('--screenshot=' + $outputPath),
        $sourceUrl
    )
    $process = Start-Process -FilePath $edgeExecutable -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $outputPath)) {
        throw ('SVG screenshot failed: ' + $sourceFilename + ' (exit ' + $process.ExitCode + ')')
    }
}

for ($stepIndex = 1; $stepIndex -le 8; $stepIndex++) {
    Invoke-SvgScreenshot `
        -sourceFilename ('parent-chicken-v6-step-' + $stepIndex + '.svg') `
        -outputFilename ('parent-chicken-v6-step-' + $stepIndex + '-1024.png')
}

Invoke-SvgScreenshot `
    -sourceFilename 'parent-chicken-v6-final-strokes.svg' `
    -outputFilename 'parent-chicken-v6-final-strokes-1024.png'
Invoke-SvgScreenshot `
    -sourceFilename 'parent-chicken-v6-reference-separate.svg' `
    -outputFilename 'parent-chicken-v6-reference-separate-1024.png'

Write-Output 'Rendered eight API-derived stroke stages, final strokes and separate reference at 1024x1024.'
