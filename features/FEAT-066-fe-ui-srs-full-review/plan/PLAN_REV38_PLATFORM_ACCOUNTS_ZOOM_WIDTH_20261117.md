# FEAT-066 Plan Rev38 — Platform Accounts zoom-width layout correction

- Product kind: authenticated web platform-administration console.
- Owner request: correct the Platform Accounts UX shown in codex-clipboard-bb8f33a9-6bb9-4a70-86cf-a96a61a56c74.png when the browser zoom reduces the effective content viewport.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation; codex/fe-ui-web-remediation.
- Requirement context: presentation-only correction to the previously implemented Platform Accounts page. Keep the current FEAT-063 canonical SRS authority (Rev60) and the user-selected Rev69 task record for Rev36 unchanged; this task adds no product requirements.
- Skills: debugger, ui-ux-pro-max, senior-frontend, frontend-design, clean-code and sketch2life-harness.

## Confirmed diagnosis

1. The shared web shell changes to a drawer at 820 CSS px, while the Platform Accounts table changes into labelled row cards only at 700 CSS px. The 701–820 range therefore has a drawer shell with a compressed five-column desktop table.
2. At reduced effective viewport width, the browser's automatic table layout allocates most available width to the account, role, status and revision columns. The action heading is visually hidden and the action cell can collapse, forcing button labels to wrap vertically or paint over the revision column.
3. The existing 1120px rule reduces padding but does not define column widths or protect the action column.

## Scope

- Update only the Platform Accounts table markup/style as needed.
- Keep the five-column semantic table at desktop widths. At 821–1120 CSS px, define stable column widths and a legible action layout; prevent email/select/action content from forcing a sibling column to overlap.
- Align the table-to-labelled-row-card breakpoint with the shared shell at 820px. Retain the existing small-screen single-column action layout at 390px.
- Show the action-column heading at desktop/tablet table widths; retain the existing visually hidden table header when rows are rendered as cards.
- Preserve every current account API call, field, role/state rule, permission gate, handler, and responsive account-card label.
- Preserve all existing dirty worktree changes. No backend, auth, API contract, dependency, SRS, route, other role, mobile app, commit or push change.

## Acceptance criteria

- AC1: At 1440px and 1120/1024/987 CSS px, table columns remain inside their container; Revision and Thao tác headings align with their cells; action buttons have readable text and do not overlap or clip.
- AC2: At 820px and below, the table renders as the existing labelled account cards, matching the shared shell drawer breakpoint. At 390px, actions stack with full labels.
- AC3: Account email/display name wraps without forcing the row beyond the available width. Role editor and active/disabled status remain legible and usable.
- AC4: All labels, accessible table/card semantics, 44px controls, focus styles and current permission/disabled states remain intact. No API/auth/data behavior changes.
- AC5: Inspect the live app at 1440×900, 1120×800, 1024×768, 987×600, 820×900, 768×1024 and 390×844; record available-session limits and screenshots. No horizontal page overflow at any width.
- AC6: Focused frontend production build, UsersPage lint and git diff --check pass. Do not run the automated application test suite.

## Workflow and risks

1. Record the dirty worktree baseline; write this plan and direct-owner approval before app source changes.
2. Reproduce the reported medium-width layout. Make the smallest responsive CSS/semantic-header adjustment.
3. Recheck all widths and retain the existing live data state. Do not inject account fixtures, credentials, or auth tokens.
4. Update FEAT-066 context, decision, evidence index and status.

The current in-app browser has an authenticated account row, but isolated headless browser review may not share that session. If no account data is available to the QA browser, verify the live page's error/empty viewport behavior and report that action-column data-state was not reauthenticated rather than fabricating rows.