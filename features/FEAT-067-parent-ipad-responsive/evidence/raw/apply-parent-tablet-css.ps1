$ErrorActionPreference = 'Stop'

$worktree = 'F:\Github\Sketch2Life-worktrees\fe-ui-full-remediation'
$sourceCss = Join-Path $worktree 'features\FEAT-067-parent-ipad-responsive\src\parent-tablet.css'
$targetCss = Join-Path $worktree 'apps\parent-ui\src\styles\tablet.css'
$mainPath = Join-Path $worktree 'apps\parent-ui\src\main.tsx'
$layoutPath = Join-Path $worktree 'apps\parent-ui\src\components\MobileLayout.tsx'

if (-not (Test-Path -LiteralPath $sourceCss)) { throw "Missing authored tablet stylesheet: $sourceCss" }
if (Test-Path -LiteralPath $targetCss) { throw "Refusing to overwrite existing stylesheet: $targetCss" }

$mainText = [System.IO.File]::ReadAllText($mainPath)
$mainAnchor = 'import "../../shared/ui-primitives.css";'
if ([regex]::Matches($mainText, [regex]::Escape($mainAnchor)).Count -ne 1) { throw 'Expected one shared UI stylesheet import in main.tsx.' }
if ($mainText.Contains('import "./styles/tablet.css";')) { throw 'Tablet stylesheet import already exists.' }

$layoutText = [System.IO.File]::ReadAllText($layoutPath)
$navTags = [regex]::Matches($layoutText, '<nav className="tabbar"[^>]*>')
if ($navTags.Count -ne 1 -or -not $navTags[0].Value.Contains('gridTemplateColumns')) { throw 'Expected one tab bar with an inline grid count in MobileLayout.tsx.' }
$oldNav = $navTags[0].Value
$newNav = [regex]::Replace($oldNav, '\sstyle=\{\{.*\}\}', ' data-tab-count={visibleTabs.length + 1}')
if ($newNav -eq $oldNav) { throw 'Could not replace the inline tab count in MobileLayout.tsx.' }

Copy-Item -LiteralPath $sourceCss -Destination $targetCss
$mainText = $mainText.Replace($mainAnchor, $mainAnchor + [Environment]::NewLine + 'import "./styles/tablet.css";')
$layoutText = $layoutText.Replace($oldNav, $newNav)
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($mainPath, $mainText, $utf8NoBom)
[System.IO.File]::WriteAllText($layoutPath, $layoutText, $utf8NoBom)

Write-Output "Applied Parent tablet CSS to: $targetCss"
Write-Output "Updated stylesheet import in: $mainPath"
Write-Output "Made tab count responsive in: $layoutPath"
