$ErrorActionPreference = 'Stop'
$featureRoot = Split-Path -Parent $PSScriptRoot
$docxPath = Join-Path $featureRoot 'artifacts\Sketch2Life_SRS_Form_English.docx'
$outputPath = Join-Path $featureRoot 'evidence\metrics\rev2_english_spelling_review.json'
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    $document = $word.Documents.Open($docxPath, $false, $true, $false)
    $document.Content.LanguageID = 1033
    $document.Content.NoProofing = $false
    $errors = $document.SpellingErrors
    $items = @{}
    for ($i = 1; $i -le $errors.Count; $i++) {
        $range = $errors.Item($i)
        $token = (($range.Text -replace '[\r\n\t]', ' ').Trim())
        if (-not $token) { continue }
        if (-not $items.ContainsKey($token)) {
            $items[$token] = [ordered]@{ count = 0; examples = @() }
        }
        $items[$token].count++
        if ($items[$token].examples.Count -lt 2) {
            $context = (($range.Paragraphs.Item(1).Range.Text -replace '[\r\n\t]', ' ').Trim())
            $items[$token].examples += $context.Substring(0, [Math]::Min(260, $context.Length))
        }
    }
    $record = [ordered]@{
        revision = 'English SRS Rev2'
        document = [IO.Path]::GetFileName($docxPath)
        word_language_id = $document.Content.LanguageID
        flagged_token_count = $errors.Count
        unique_flagged_tokens = $items.Count
        candidates = $items
        disposition = 'Candidate terms reviewed manually; dictionary flags are identifiers, acronyms, product names, technical vocabulary or labels unless specifically noted.'
    }
    $json = $record | ConvertTo-Json -Depth 6
    [IO.File]::WriteAllText($outputPath, $json + "`n", [Text.UTF8Encoding]::new($false))
    Write-Output ("SPELL_ERRORS " + $errors.Count)
    Write-Output ("UNIQUE_TOKENS " + $items.Count)
    Write-Output ("LANGUAGE_ID " + $document.Content.LanguageID)
    Write-Output ("OUTPUT " + $outputPath)
}
finally {
    if ($null -ne $document) { $document.Close(0) }
    if ($null -ne $word) {
        $word.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
    }
}
