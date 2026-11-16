# Web UI rebuild Rev24 — School Manager checkpoint

Date: 2026-11-11
Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`
Branch: `codex/fe-ui-web-remediation`
SRS authority: FEAT-063 v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; unsigned. Target requirements are §§1–31; §32 remains environment evidence only.

## Implementation

- Replaced the active School Manager shell with the accepted paper-and-crayon visual system, monochrome line navigation, grouped routes, responsive drawer, accessible focus behavior, a visible logout action, and an inbox link without an unread dot.
- Replaced the active dashboard fixtures with API-scoped class reads and explicit states for local preview, authorization/configuration errors, loading, and empty results. Local preview sends no Firebase/backend requests and shows no sample records.
- Added the School Manager route map for overview, teachers/groups, classes, roster, public review, finance, subscription, quota, inbox, feedback, and settings.
- Class and roster reads use the existing assignment, classes, and class-profile endpoints after checking for an active `school_admin` assignment. Roster output stays scoped to the selected returned class and does not display media/story.
- Public review uses the existing PUBLIC `PENDING_REVIEW` access-grant list, current lesson detail, and decision command. It only unlocks a decision after current `version_id` exactly matches the grant's immutable `version_id` and structured content is present. A stale version remains unavailable because no get-by-version API exists.
- The queue count is explicitly the number displayed on the current API page. The UI labels Approved and Changes requested separately and states that no API aggregate is available; it does not derive either total from the pending queue.
- Teacher directory/provisioning/reassignment, Parent groups, capacity-safe class create/archive/suspend, invoice/payment, subscription/renewal/downgrade, school quota/top-up, canonical inbox/read state, feedback threads/replies, and organization profile settings are represented as unavailable with missing contract dependencies. No prices, policies, transactions, fake success, or fake unread state are shown.

## Manual local review

- Reused the loopback Vite preview at `http://127.0.0.1:5173/`; Chrome requests were restricted to `127.0.0.1:5173`. The only session state was a synthetic `MANAGER` role flag in local `sessionStorage`; no credentials or backend API were configured or called.
- Captured 11 routes at 1440×900 and 390×844 (22 PNGs) under `evidence/screenshots/manager-rev24/` and inspected overview, roster, review, teachers/groups, and classes at narrow/desktop widths.
- Across all captures: zero horizontal overflow, Vite overlays, runtime exceptions, console errors, fabricated organization names, fake amounts/quota totals, or unread-dot indicators.
- Keyboard pass at 390px: first Tab focuses the menu button; Enter opens the drawer and focuses the active navigation link; Escape closes it and restores focus to the menu button. Current navigation exposes `aria-current="page"`.
- No authenticated API, real organization/class/child data, screen-reader device, tests, or build was used. Live authorization, API payload behavior, and server decisions remain unverified here.

## Remaining API dependencies and next section

The blocked flows above require versioned FE/backend contracts and the SRS-required authorization, audit, lifecycle, capacity, and reconciliation behavior. School Manager is complete for this section's FE-only scope. Continue to Platform Admin only after this checkpoint; do not change Parent/mobile, backend, or provider behavior.
