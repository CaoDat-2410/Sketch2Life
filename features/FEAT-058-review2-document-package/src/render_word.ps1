param(
    [Parameter(Mandatory=$true)][string]$InputDocx,
    [Parameter(Mandatory=$true)][string]$OutputPdf,
    [switch]$RefreshFields
)
$ErrorActionPreference = 'Stop'
$taskWord = $null
$taskDoc = $null
try {
    $taskWord = New-Object -ComObject Word.Application
    $taskWord.Visible = $false
    $taskWord.DisplayAlerts = 0
    $taskWord.AutomationSecurity = 3
    $taskWord.Options.SaveNormalPrompt = $false
    $taskDoc = $taskWord.Documents.Open($InputDocx, $false, (-not $RefreshFields.IsPresent), $false)
    if ($RefreshFields) {
        $taskDoc.Fields.Update() | Out-Null
        foreach ($taskToc in $taskDoc.TablesOfContents) { $taskToc.Update() }
        $taskDoc.Repaginate()
        $taskDoc.Save()
    }
    $taskDoc.ExportAsFixedFormat($OutputPdf, 17)
    Write-Output ('PDF ' + $OutputPdf)
    Write-Output ('PAGES ' + $taskDoc.ComputeStatistics(2))
    $taskDoc.Close(0)
    $taskDoc = $null
}
finally {
    if ($null -ne $taskDoc) { $taskDoc.Close(0) }
    if ($null -ne $taskWord) {
        $taskWord.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($taskWord) | Out-Null
    }
}
