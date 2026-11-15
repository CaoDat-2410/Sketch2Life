Add-Type -AssemblyName PresentationCore, PresentationFramework, WindowsBase, System.Drawing

$evidenceRoot = $PSScriptRoot
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
$datasetRoot = Join-Path $repoRoot 'deployment\modal\srs_v23\data\openmoji'
$manifest = Get-Content -LiteralPath (Join-Path $datasetRoot 'parent-guide-manifest.json') -Raw | ConvertFrom-Json
$size = 512
$scale = $size / 72.0

foreach ($asset in $manifest.assets) {
    $sourcePath = Join-Path $datasetRoot $asset.black_filename
    $xml = New-Object System.Xml.XmlDocument
    $xml.XmlResolver = $null
    $xml.Load($sourcePath)
    $lineGroup = $xml.SelectSingleNode("//*[local-name()='g' and @id='line']")
    $sourcePaths = @($lineGroup.SelectNodes("./*[local-name()='path']"))
    $pathById = @{}
    for ($i = 0; $i -lt $sourcePaths.Count; $i++) {
        $pathById[('source-shape-{0:D3}' -f ($i + 1))] = $sourcePaths[$i].GetAttribute('d')
    }

    $visible = New-Object System.Collections.Generic.List[string]
    foreach ($stage in $asset.stages) {
        foreach ($pathId in $stage.path_ids) { $visible.Add($pathId) }

        $visual = New-Object System.Windows.Media.DrawingVisual
        $drawing = $visual.RenderOpen()
        $drawing.DrawRectangle([System.Windows.Media.Brushes]::White, $null, [System.Windows.Rect]::new(0, 0, 72, 72))
        $drawing.PushTransform([System.Windows.Media.ScaleTransform]::new($scale, $scale))
        $pen = [System.Windows.Media.Pen]::new([System.Windows.Media.Brushes]::DarkSlateBlue, 2.0)
        $pen.StartLineCap = [System.Windows.Media.PenLineCap]::Round
        $pen.EndLineCap = [System.Windows.Media.PenLineCap]::Round
        $pen.LineJoin = [System.Windows.Media.PenLineJoin]::Round
        foreach ($pathId in $visible) {
            $geometry = [System.Windows.Media.Geometry]::Parse($pathById[$pathId])
            $drawing.DrawGeometry($null, $pen, $geometry)
        }
        $drawing.Pop()
        $drawing.Close()

        $bitmap = [System.Windows.Media.Imaging.RenderTargetBitmap]::new($size, $size, 96, 96, [System.Windows.Media.PixelFormats]::Pbgra32)
        $bitmap.Render($visual)
        $encoder = New-Object System.Windows.Media.Imaging.PngBitmapEncoder
        $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
        $outputName = 'openmoji-{0}-stage-{1}.png' -f $asset.asset_id, $stage.step_index
        $outputPath = Join-Path $evidenceRoot $outputName
        $buffer = [System.IO.MemoryStream]::new()
        $encoder.Save($buffer)
        $buffer.Position = 0
        $sourceBitmap = [System.Drawing.Bitmap]::new($buffer)
        $flatBitmap = [System.Drawing.Bitmap]::new($size, $size, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
        $graphics = [System.Drawing.Graphics]::FromImage($flatBitmap)
        $graphics.Clear([System.Drawing.Color]::White)
        $graphics.DrawImage($sourceBitmap, 0, 0, $size, $size)
        $flatBitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose()
        $flatBitmap.Dispose()
        $sourceBitmap.Dispose()
        $buffer.Dispose()
    }
}
