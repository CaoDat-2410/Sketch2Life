$ErrorActionPreference = "Stop"

$iconPath = "F:\Github\Sketch2Life-worktrees\fe-ui-full-remediation\apps\parent-ui\src\components\Icon.tsx"
$layoutPath = "F:\Github\Sketch2Life-worktrees\fe-ui-full-remediation\apps\parent-ui\src\components\MobileLayout.tsx"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Replace-Once([string]$text, [string]$old, [string]$new, [string]$label) {
  $first = $text.IndexOf($old, [System.StringComparison]::Ordinal)
  if ($first -lt 0) { throw "Expected source text not found: $label" }
  $second = $text.IndexOf($old, $first + $old.Length, [System.StringComparison]::Ordinal)
  if ($second -ge 0) { throw "Expected source text is ambiguous: $label" }
  return $text.Substring(0, $first) + $new + $text.Substring($first + $old.Length)
}

$icon = [System.IO.File]::ReadAllText($iconPath)
$layout = [System.IO.File]::ReadAllText($layoutPath)
$iconNewline = if ($icon.Contains("`r`n")) { "`r`n" } else { "`n" }
$layoutNewline = if ($layout.Contains("`r`n")) { "`r`n" } else { "`n" }
$icon = $icon.Replace("`r`n", "`n")
$layout = $layout.Replace("`r`n", "`n")

$oldNames = '  | "volume" | "volume-off" | "help" | "edit";'
$newNames = '  | "volume" | "volume-off" | "help" | "edit" | "nav-home" | "nav-history" | "nav-create" | "nav-credits" | "nav-settings";'
$icon = Replace-Once $icon $oldNames $newNames "IconName union"

$oldTail = @'
  edit: (<path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5Z" />),
};
'@
$newTail = @'
  edit: (<path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5Z" />),
  "nav-home": (<><path d="M4 10.4 12 4l8 6.4" /><path d="M6.4 9v9.1A1.9 1.9 0 0 0 8.3 20h7.4a1.9 1.9 0 0 0 1.9-1.9V9" /><path d="M10 20v-5.6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1V20" /><path d="M16 6.7v-2h2v3.6" /></>),
  "nav-history": (<><path d="M3.5 11a8.5 8.5 0 1 1 .2 2.5" /><path d="M3.5 4.5V11H10" /><path d="M12 7.5v4.8l3.2 2" /></>),
  "nav-create": (<><path d="M4 8.5A2.5 2.5 0 0 1 6.5 6h1.2a1 1 0 0 0 .8-.4L9.6 4h4.8l1.1 1.6a1 1 0 0 0 .8.4h1.2A2.5 2.5 0 0 1 20 8.5v8A2.5 2.5 0 0 1 17.5 19h-11A2.5 2.5 0 0 1 4 16.5v-8Z" /><circle cx="12" cy="12.5" r="3.1" /><path d="M18.5 2.8v4.4M16.3 5h4.4" /></>),
  "nav-credits": (<><ellipse cx="12" cy="6.5" rx="7.2" ry="3.2" /><path d="M4.8 6.5v5.4c0 1.8 3.2 3.3 7.2 3.3s7.2-1.5 7.2-3.3V6.5" /><path d="M4.8 11.9v5.3c0 1.8 3.2 3.3 7.2 3.3s7.2-1.5 7.2-3.3v-5.3" /><path d="M12 8v4" /></>),
  "nav-settings": (<><path d="M4 6h7M15 6h5M4 12h3M11 12h9M4 18h9M17 18h3" /><circle cx="13" cy="6" r="2" /><circle cx="9" cy="12" r="2" /><circle cx="15" cy="18" r="2" /></>),
};
'@
$icon = Replace-Once $icon $oldTail $newTail "icon map tail"

$layout = Replace-Once $layout '{ path: "/p01-lesson-library", label: "Trang chủ", icon: "home" }' '{ path: "/p01-lesson-library", label: "Trang chủ", icon: "nav-home" }' "home nav mapping"
$layout = Replace-Once $layout '{ path: "/p09-history-feedback", label: "Lịch sử", icon: "book" }' '{ path: "/p09-history-feedback", label: "Lịch sử", icon: "nav-history" }' "history nav mapping"
$layout = Replace-Once $layout '{ path: "/p12-video-quota", label: "Lượt tạo", icon: "star" }' '{ path: "/p12-video-quota", label: "Lượt tạo", icon: "nav-credits" }' "credits nav mapping"
$layout = Replace-Once $layout '{ path: "/p13-settings", label: "Cài đặt", icon: "settings" }' '{ path: "/p13-settings", label: "Cài đặt", icon: "nav-settings" }' "settings nav mapping"
$layout = Replace-Once $layout '<Icon name="camera" size={25} strokeWidth={2.2} />' '<Icon name="nav-create" size={25} strokeWidth={2.2} />' "create nav mapping"

[System.IO.File]::WriteAllText($iconPath, $icon.Replace("`n", $iconNewline), $utf8NoBom)
[System.IO.File]::WriteAllText($layoutPath, $layout.Replace("`n", $layoutNewline), $utf8NoBom)
Write-Output "Updated five navbar SVG mappings; existing labels, paths, and unrelated icon mappings were preserved."
