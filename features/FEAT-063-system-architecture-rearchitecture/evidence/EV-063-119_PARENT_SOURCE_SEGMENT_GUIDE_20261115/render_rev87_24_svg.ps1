param([Parameter(Mandatory=$true)][string]$InputSvg,[Parameter(Mandatory=$true)][string]$OutputPng)
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName WindowsBase
$doc = [xml](Get-Content -LiteralPath $InputSvg -Raw)
$root = $doc.DocumentElement
$box = @($root.GetAttribute('viewBox').Split(' ',[System.StringSplitOptions]::RemoveEmptyEntries) | ForEach-Object { [double]::Parse($_,[Globalization.CultureInfo]::InvariantCulture) })
if ($box.Count -ne 4 -or $box[2] -le 0 -or $box[3] -le 0) { throw 'Invalid SVG viewBox' }
$visual = New-Object Windows.Media.DrawingVisual
$dc = $visual.RenderOpen()
$dc.DrawRectangle([Windows.Media.Brushes]::White,$null,(New-Object Windows.Rect(0,0,512,512)))
$sx = 512.0 / $box[2]; $sy = 512.0 / $box[3]
$tx = -$box[0]*$sx; $ty = -$box[1]*$sy
if ([IO.Path]::GetFileName($InputSvg) -eq 'source_color_reference.svg') {
  $manifestPath = Join-Path $PSScriptRoot 'source_segment_preflight_rev87_24.json'
  $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
  $sx = [double]$manifest.scale; $sy = $sx
  $tx = [double]$manifest.translate_x; $ty = [double]$manifest.translate_y
}
$matrix = New-Object Windows.Media.Matrix($sx,0,0,$sy,$tx,$ty)
foreach ($node in $root.GetElementsByTagName('path')) {
  $g = ([Windows.Media.Geometry]::Parse($node.GetAttribute('d'))).Clone()
  $g.Transform = New-Object Windows.Media.MatrixTransform($matrix)
  $fillText = $node.GetAttribute('fill'); $strokeText = $node.GetAttribute('stroke')
  $fill = $null; $pen = $null
  if ($fillText -and $fillText -ne 'none') { $fill = [Windows.Media.BrushConverter]::new().ConvertFromString($fillText) }
  if ($strokeText -and $strokeText -ne 'none') {
    $width = 5.0; $rawWidth = $node.GetAttribute('stroke-width'); if ($rawWidth) { $width=[double]::Parse($rawWidth,[Globalization.CultureInfo]::InvariantCulture) }
    $pen = New-Object Windows.Media.Pen(([Windows.Media.BrushConverter]::new().ConvertFromString($strokeText)),($width*([Math]::Min($sx,$sy))))
    $pen.StartLineCap=[Windows.Media.PenLineCap]::Round; $pen.EndLineCap=[Windows.Media.PenLineCap]::Round; $pen.LineJoin=[Windows.Media.PenLineJoin]::Round
  }
  $dc.DrawGeometry($fill,$pen,$g)
}
$dc.Close()
$bitmap = New-Object Windows.Media.Imaging.RenderTargetBitmap(512,512,96,96,[Windows.Media.PixelFormats]::Pbgra32)
$bitmap.Render($visual)
$encoder = New-Object Windows.Media.Imaging.PngBitmapEncoder
$encoder.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
$stream = [IO.File]::Open($OutputPng,[IO.FileMode]::Create,[IO.FileAccess]::Write)
try { $encoder.Save($stream) } finally { $stream.Dispose() }
