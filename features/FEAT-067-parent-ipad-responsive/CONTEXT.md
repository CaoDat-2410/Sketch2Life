# FEAT-067 — Current context

## Product authority

Use the canonical working SRS recorded in `docs/context/SRS_AUTHORITY.md`: FEAT-063's `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev57, still awaiting formal owner sign-off. The SRS does not prescribe iPad CSS breakpoints or this web preview's layout. This feature changes responsive presentation only.

FR-P-01 names `apps/mobile` as the Parent Android target and `apps/ui-mobile` as reference. This feature updates the existing `apps/parent-ui` web preview and does not claim to complete or replace the Android target.

## Scope and source

- Approved scope: Parent UI tablet/iPad portrait and landscape proportions, navigation, spacing, and route-specific layouts.
- Active source worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`.
- Feature-owned style source and review artifacts live under this FEAT-067 folder.
- Product flow, authentication behavior, API contracts, backend services, and non-Parent portals are outside the change.

## Current status

Responsive styles are implemented and the local Parent preview at `http://127.0.0.1:5171` has been reviewed with synthetic preview data. Evidence covers the auth routes and all implemented Parent screens in both representative orientations, eleven iPad viewport shapes, two touch-emulated tablet sizes, and two desktop comparison sizes. The recorded viewport checks found no horizontal overflow.

See `evidence/EV-067-01_PARENT_TABLET_RESPONSIVE_20261110.md` and `status/STATUS.md` for the current implementation record.
