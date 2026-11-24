param(
    [Parameter(Mandatory=$true)][string]$InputDocx,
    [Parameter(Mandatory=$true)][string]$OutputPdf
)
$ErrorActionPreference = 'Stop'
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $word.Options.SaveNormalPrompt = $false
    $document = $word.Documents.Open($InputDocx, $false, $false, $false)
    $document.Fields.Update() | Out-Null
    foreach ($toc in $document.TablesOfContents) { $toc.Update() }
    $document.Repaginate()
    $document.Save()
    $document.ExportAsFixedFormat($OutputPdf, 17)
    Write-Output ('PDF ' + $OutputPdf)
    Write-Output ('PAGES ' + $document.ComputeStatistics(2))
    $document.Close(0)
    $document = $null
}
finally {
    if ($null -ne $document) { $document.Close(0) }
    if ($null -ne $word) {
        $word.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }
}
