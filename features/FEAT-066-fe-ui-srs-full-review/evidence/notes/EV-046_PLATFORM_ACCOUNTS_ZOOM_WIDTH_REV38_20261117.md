# FEAT-066-EV-046 — Platform Accounts zoom-width correction

- Date: 2026-11-17 (Asia/Bangkok).
- Owner screenshot/before state: codex-clipboard-bb8f33a9-6bb9-4a70-86cf-a96a61a56c74.png, /platform/accounts.
- Plan: PLAN_REV38_PLATFORM_ACCOUNTS_ZOOM_WIDTH_20261117.md; SHA-256 DD3BC84855986B15C8FAA4356A4231B93E4096D4F6A0FC3C4316FD73C79ABC79.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation; codex/fe-ui-web-remediation.
- Baseline before plan/approval/source edits: EV-045_PLATFORM_ACCOUNTS_ZOOM_WIDTH_BASELINE_REV38_20261117.md.

## Root cause and change

The shared shell moves to a drawer at 820px while the account page remained a five-column table to 700px. In the gap, automatic table sizing could squeeze the last action column and wrap the button labels over the Revision area.

Changed apps/web/src/modules/platform-admin/styles/accounts-page.css to use fixed column percentages and a dedicated stacked action column through 1120px, and to render the existing labelled account cards through 900px. The action table header is now visible above the desktop table in UsersPage.tsx; the mobile table header remains visually hidden when row labels are shown. API and permission behavior were not changed.

## Browser viewport review

Used a fresh headless Chrome profile at /platform/accounts. Session storage was set only to render the client-side Platform Admin portal; no Firebase credential/ID token or account fixture was added. Without the user's Firebase session, the page correctly showed its authentication recovery state and did not render an account row.

At 1440×900, 1120×800, 1024×768, 987×600, 900×600, 820×900, 768×1024 and 390×844, the document width equaled the viewport's usable width and no horizontal overflow was reported. The 900px card breakpoint toggled as expected; no runtime exceptions were observed. Screenshots in screenshots/rev38-accounts-zoom/ record this no-auth page state.

**Limit:** The populated row/actions from the owner's screenshot were not rendered in the isolated QA browser because it had no Firebase session. No fake row or credential was injected. Thus the live action-column appearance on populated data was not independently captured after the change; the owner's active local page can hot-reload the CSS, but that session is not exposed to this QA browser.

## Checks

- npm run build: passed.
- npx oxlint src/modules/platform-admin/pages/UsersPage.tsx: passed with exit 0.
- git diff --check: passed; Git printed CRLF normalization warnings only.
- No application test suite, account mutation, commit, or push.