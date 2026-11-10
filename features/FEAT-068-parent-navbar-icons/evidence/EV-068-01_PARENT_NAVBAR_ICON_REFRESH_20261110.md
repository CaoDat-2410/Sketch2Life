# EV-068-01 — Parent navbar icon refresh

- Date: 2026-11-10 (Asia/Bangkok)
- Status: COMPLETE
- Approved plan: FEAT-068 plan revision 1
- Source worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`
- Local preview: `http://127.0.0.1:5171/p01-lesson-library`

## Change

Added five navigation-only SVG paths to `apps/parent-ui/src/components/Icon.tsx` and mapped the Parent navbar to them in `MobileLayout.tsx`:

- Trang chủ: house with a chimney.
- Lịch sử: clock with a rewind arrow.
- Tạo: camera with a plus mark.
- Lượt tạo: stacked coins.
- Cài đặt: horizontal adjustment sliders.

All paths use the existing 24×24 SVG viewBox and shared rounded outline style. Generic icon mappings elsewhere are unchanged. No icon dependency, generated asset, or backend/API behavior was added. Tab labels, route order, active state, and the create button's accessible name remain intact.

## Visual review

Captured the local demo at:

- 390×844 phone portrait.
- 834×1194 iPad portrait.
- 1194×834 iPad landscape.

All screenshots show five SVGs in the navbar with no horizontal page/nav overflow. The landscape image confirms the same glyph set in the vertical tablet rail. Metrics and screenshots are in [`screenshots/navbar-icon-metrics.json`](screenshots/navbar-icon-metrics.json) and [`screenshots/`](screenshots/).

No automated test suite or production build was run for this visual-only request.
