param([string]$CandidateDirectory = 'candidates')

Add-Type -AssemblyName PresentationCore, WindowsBase, System.Drawing

$evidenceRoot = $PSScriptRoot
$candidateRoot = Join-Path $PSScriptRoot $CandidateDirectory
$size = 640

function Convert-SvgColor([string]$value, [double]$opacity = 1.0) {
    if (-not $value -or $value -eq 'none' -or $value.StartsWith('url(')) { return $null }
    $color = $null
    if ($value -match '^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$') {
        $color = [System.Windows.Media.Color]::FromRgb([byte]$Matches[1], [byte]$Matches[2], [byte]$Matches[3])
    } elseif ($value -match '^rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)$') {
        $alpha = [Math]::Max(0, [Math]::Min(255, [int](255 * [double]$Matches[4] * $opacity)))
        $color = [System.Windows.Media.Color]::FromArgb([byte]$alpha, [byte]$Matches[1], [byte]$Matches[2], [byte]$Matches[3])
        return [System.Windows.Media.SolidColorBrush]::new($color)
    } else {
        try { $color = [System.Windows.Media.ColorConverter]::ConvertFromString($value) } catch { return $null }
    }
    if ($opacity -lt 1) {
        $alpha = [Math]::Max(0, [Math]::Min(255, [int]($color.A * $opacity)))
        $color = [System.Windows.Media.Color]::FromArgb([byte]$alpha, $color.R, $color.G, $color.B)
    }
    return [System.Windows.Media.SolidColorBrush]::new($color)
}

function Get-SvgStyle($node, [hashtable]$inherited) {
    $style = @{}
    foreach ($key in $inherited.Keys) { $style[$key] = $inherited[$key] }
    foreach ($attribute in @('fill','stroke','stroke-width','fill-opacity','stroke-opacity','stroke-linecap','stroke-linejoin','fill-rule')) {
        if ($node.HasAttribute($attribute)) { $style[$attribute] = $node.GetAttribute($attribute) }
    }
    $declarations = $node.GetAttribute('style') -split ';'
    foreach ($declaration in $declarations) {
        if ($declaration -match '^\s*([^:]+)\s*:\s*(.*?)\s*$') { $style[$Matches[1]] = $Matches[2] }
    }
    return $style
}

function Get-SvgTransform([string]$value) {
    if (-not $value) { return $null }
    $matrix = [System.Windows.Media.Matrix]::Identity
    $commands = [regex]::Matches($value, '([A-Za-z]+)\s*\(([^)]*)\)')
    foreach ($command in $commands) {
        $name = $command.Groups[1].Value
        $numbers = @([regex]::Matches($command.Groups[2].Value, '[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?') | ForEach-Object { [double]$_.Value })
        $part = [System.Windows.Media.Matrix]::Identity
        switch ($name) {
            'matrix' { if ($numbers.Count -eq 6) { $part = [System.Windows.Media.Matrix]::new($numbers[0],$numbers[1],$numbers[2],$numbers[3],$numbers[4],$numbers[5]) } }
            'translate' { if ($numbers.Count -ge 1) { $y = if ($numbers.Count -gt 1) { $numbers[1] } else { 0 }; $part = [System.Windows.Media.Matrix]::new(1,0,0,1,$numbers[0],$y) } }
            'scale' { if ($numbers.Count -ge 1) { $sy = if ($numbers.Count -gt 1) { $numbers[1] } else { $numbers[0] }; $part = [System.Windows.Media.Matrix]::new($numbers[0],0,0,$sy,0,0) } }
            'rotate' {
                if ($numbers.Count -ge 1) {
                    $part.Rotate($numbers[0])
                    if ($numbers.Count -ge 3) { $part.Translate($numbers[1],$numbers[2]); $undo = [System.Windows.Media.Matrix]::Identity; $undo.Translate(-$numbers[1],-$numbers[2]); $undo.Append($part); $part = $undo }
                }
            }
        }
        $matrix.Append($part)
    }
    return [System.Windows.Media.MatrixTransform]::new($matrix)
}

function Draw-SvgNode($node, $drawing, [hashtable]$inheritedStyle) {
    $tag = $node.LocalName
    if ($tag -in @('metadata','title','desc','defs','namedview','style','clipPath','symbol')) { return }
    $style = Get-SvgStyle $node $inheritedStyle
    $transform = Get-SvgTransform $node.GetAttribute('transform')
    if ($transform) { $drawing.PushTransform($transform) }

    if ($tag -in @('g','svg')) {
        foreach ($child in $node.ChildNodes) {
            if ($child.NodeType -eq [System.Xml.XmlNodeType]::Element) { Draw-SvgNode $child $drawing $style }
        }
    } elseif ($tag -eq 'path' -and $node.HasAttribute('d')) {
        try {
            $geometry = [System.Windows.Media.Geometry]::Parse($node.GetAttribute('d'))
            $fillOpacity = 1.0
            if ($style.ContainsKey('fill-opacity')) { $fillOpacity = [double]$style['fill-opacity'] }
            $strokeOpacity = 1.0
            if ($style.ContainsKey('stroke-opacity')) { $strokeOpacity = [double]$style['stroke-opacity'] }
            $fillValue = 'black'
            if ($style.ContainsKey('fill')) { $fillValue = $style['fill'] }
            $fill = Convert-SvgColor $fillValue $fillOpacity
            $strokeBrush = Convert-SvgColor $style['stroke'] $strokeOpacity
            $pen = $null
            if ($strokeBrush) {
                $width = if ($style['stroke-width']) { [double]$style['stroke-width'] } else { 1.5 }
                $pen = [System.Windows.Media.Pen]::new($strokeBrush, $width)
                switch ($style['stroke-linecap']) { 'round' { $pen.StartLineCap=[System.Windows.Media.PenLineCap]::Round; $pen.EndLineCap=[System.Windows.Media.PenLineCap]::Round } 'square' { $pen.StartLineCap=[System.Windows.Media.PenLineCap]::Square; $pen.EndLineCap=[System.Windows.Media.PenLineCap]::Square } }
                if ($style['stroke-linejoin'] -eq 'round') { $pen.LineJoin=[System.Windows.Media.PenLineJoin]::Round }
            }
            if ($fill -or $pen) { $drawing.DrawGeometry($fill, $pen, $geometry) }
        } catch { Write-Warning ("Skipping unsupported path in {0}: {1}" -f $node.OwnerDocument.BaseURI, $_.Exception.Message) }
    }

    if ($transform) { $drawing.Pop() }
}

foreach ($file in Get-ChildItem -LiteralPath $candidateRoot -Filter '*.svg') {
    $xml = New-Object System.Xml.XmlDocument
    $xml.XmlResolver = $null
    $xml.Load($file.FullName)
    $root = $xml.DocumentElement
    $values = @($root.GetAttribute('viewBox') -split '[ ,]+' | Where-Object { $_ } | ForEach-Object { [double]$_ })
    if ($values.Count -ne 4 -or $values[2] -le 0 -or $values[3] -le 0) { throw "Invalid viewBox: $($file.Name)" }
    $scale = [Math]::Min($size / $values[2], $size / $values[3])
    $offsetX = ($size - $values[2] * $scale) / 2 - $values[0] * $scale
    $offsetY = ($size - $values[3] * $scale) / 2 - $values[1] * $scale
    $visual = New-Object System.Windows.Media.DrawingVisual
    $drawing = $visual.RenderOpen()
    $drawing.DrawRectangle([System.Windows.Media.Brushes]::White, $null, [System.Windows.Rect]::new(0,0,$size,$size))
    $drawing.PushTransform([System.Windows.Media.MatrixTransform]::new([System.Windows.Media.Matrix]::new($scale,0,0,$scale,$offsetX,$offsetY)))
    Draw-SvgNode $root $drawing @{}
    $drawing.Pop()
    $drawing.Close()

    $render = [System.Windows.Media.Imaging.RenderTargetBitmap]::new($size,$size,96,96,[System.Windows.Media.PixelFormats]::Pbgra32)
    $render.Render($visual)
    $encoder = New-Object System.Windows.Media.Imaging.PngBitmapEncoder
    $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($render))
    $buffer = [System.IO.MemoryStream]::new()
    $encoder.Save($buffer)
    $buffer.Position = 0
    $source = [System.Drawing.Bitmap]::new($buffer)
    $flat = [System.Drawing.Bitmap]::new($size,$size,[System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    $graphics = [System.Drawing.Graphics]::FromImage($flat)
    $graphics.Clear([System.Drawing.Color]::White)
    $graphics.DrawImage($source,0,0,$size,$size)
    $output = Join-Path $evidenceRoot ($file.BaseName + '-preview.png')
    $flat.Save($output,[System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose(); $flat.Dispose(); $source.Dispose(); $buffer.Dispose()
    Write-Output $output
}
