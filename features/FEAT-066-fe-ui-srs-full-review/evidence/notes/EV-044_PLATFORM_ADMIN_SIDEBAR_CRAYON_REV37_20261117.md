# FEAT-066-EV-044 — Platform Admin sidebar crayon redesign

- Date: 2026-11-17 (Asia/Bangkok).
- Owner request: redesign the Platform Admin sidebar shown in screenshot codex-clipboard-94427364-8cf5-47ba-8441-0e4b0c85f0e1.png and apply frontend design skills.
- Plan: PLAN_REV37_PLATFORM_ADMIN_SIDEBAR_CRAYON_REDESIGN_20261117.md; SHA-256 A3F276D0EB8D163F35B107A9CC154D448437A4F5F6BFAF65EE49F82DB399940C.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation; codex/fe-ui-web-remediation.
- Baseline: EV-043_PLATFORM_ADMIN_SIDEBAR_BASELINE_REV37_20261117.md.

## Implementation

Only apps/web/src/modules/platform-admin/styles/admin-rebuild.css changed for this revision. Added portal-scoped CSS using existing crayon tokens. Ordinary links use ink colors; group headings use sentence case; the active route has a mint surface and edge marker; waiting API state has a separate amber badge; verified session and account actions are visually grouped. Keyboard focus, 44px nav/action targets, reduced motion, responsive drawer, scrollable nav, and footer behavior are preserved.

No JSX, route, API, auth, permission, or other-role styles changed.

## Visual review

An isolated temporary headless Chrome profile rendered /platform/a02-platform-operations. Presentation-only sessionStorage values were set so the client-rendered shell could display; no Firebase credential or ID token was entered. The existing overview can perform its read-only GET /health probe when the configured bridge is available; the screenshot shows its API response. No account action or protected mutation was initiated.

| Viewport | Result |
| --- | --- |
| 1440×900 | Sidebar 264px; heading 12px/sentence case; links 13px; active route “Tổng quan”; no horizontal overflow. |
| 768×1024 | Drawer opened; no horizontal overflow; navigation/footer fit. |
| 390×844 | Drawer opened; no horizontal overflow; nav content 576px in a 553px scroll area; footer remains anchored. |

No browser runtime exceptions were observed. Captures:
- screenshots/rev37-platform-sidebar/platform-admin-sidebar-desktop-1440x900.png
- screenshots/rev37-platform-sidebar/platform-admin-sidebar-tablet-open-768x1024.png
- screenshots/rev37-platform-sidebar/platform-admin-sidebar-mobile-open-390x844.png

## Checks and limits

- npm run build: passed.
- npx oxlint src/shared/WebAppShell.tsx: exit 0; existing Fast Refresh and set-state-in-effect warnings remain in the unchanged file. CSS validation is included in the production build.
- git diff --check: passed; Git emitted CRLF normalization warnings only.
- No application test suite, credentials, protected account action, commit, or push.
- Visual review does not replace a screen-reader audit or verify real authenticated capabilities.