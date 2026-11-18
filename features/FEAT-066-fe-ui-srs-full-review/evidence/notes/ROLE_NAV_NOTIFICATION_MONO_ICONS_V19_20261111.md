# Monochrome line navbar and notification icons — Rev19

- Date: 2026-11-11 (Asia/Bangkok).
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Authorization: direct user correction “navbar icon kiểu nét ko màu á”; Plan revision 19 and its matching approval were recorded before changing the shared icon source. Plan SHA-256: FABD3A9230620BE08F7E4B6D04FA178C3EAC372377F760F37C266182BB9F1141.
- Product baseline: canonical FEAT-063 SRS v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; still awaiting owner sign-off. This is a visual-only correction.

## Change

The shared RoleDashboardIcon navigation and notification variants now render the existing local SVG paths as single-color outline glyphs, with no emoji glyphs or multicolor fills. The SVG uses the shell's current foreground color and rounded stroke caps/joins. All three notification/inbox controls use the same bell outline. Existing active/inactive foreground colors, unread count/status marks, accessible names, aria-hidden decorative behavior, layout, routes and actions remain in place. Non-shell/page-content icons retain their previous Rev17 styling. No package, asset, API, backend, or other portal source was changed for this revision.

## Manual preview

EV-022 includes nine isolated loopback captures: Teacher, School Manager and Platform Admin at 1440x900 and 390x844, plus one dark 1440x900 capture for each role. The capture helper allowed requests only to 127.0.0.1 on ports 5172, 5173 and 5174 and restored the browser storage it temporarily used.

- Each of the nine captures reports the bell-outline notification icon and at least nine rendered line icons.
- No capture reports horizontal overflow or a Vite error overlay; the browser reported zero runtime exceptions.
- Representative screenshots were visually inspected for the Teacher narrow layout, School Manager desktop, and Platform Admin dark desktop; the icons render as outline glyphs with no emoji rendering.
- No automated tests/builds or screen-reader device audit were run. Source semantics and accessible names were preserved, but assistive-technology behavior was not independently exercised.
- No credentials, production data, backend, or external provider was used.

The result is left uncommitted and unpushed for user review.
