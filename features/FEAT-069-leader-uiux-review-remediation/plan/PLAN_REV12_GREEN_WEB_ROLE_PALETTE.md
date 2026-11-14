# Plan Rev12 — Green palette for the three web roles

## Goal

Extend the green interaction palette already applied to Parent across Teacher, School Manager, and Platform Admin web previews so the project's four user-facing role experiences feel like one product. Keep the shared role-entry/sign-in preview consistent with the same green palette.

## Scope

- Inspect the last-loaded shared web color layer and the role-specific accent overrides for Teacher, School Manager, Platform Admin, and the shared role-entry/sign-in preview.
- Replace the blue, teal-blue, and purple brand/action accents in those surfaces with coordinated greens aligned to Parent's `#3f7559` action color.
- Update primary actions, selected navigation/tabs/chips, links, focus rings, role-specific hero accents, and corresponding soft surfaces so selected states remain clear and readable.
- Preserve warm yellow decorative accents and semantic warning, danger, and status colors. Do not recolor data-series states solely because they have a blue label unless they are actually used as a brand/action accent.
- Keep the change to UI colors in `UI_Project/shared/rev8ColorSystem.css`; do not alter role layouts, route behavior, business flows, or data.
- Build all five workspaces and visually inspect the Teacher, School Manager, Platform Admin, and shared web previews.
- Record findings, evidence, status, and source register updates in FEAT-069.

## Acceptance criteria

1. Teacher, School Manager, Platform Admin, and the shared role-entry preview use the same green family for primary/selected brand interactions.
2. Blue/teal-blue/purple brand colors no longer override those interactions in the last-loaded color layer.
3. Role titles, control labels, focus indicators, and selected states remain readable; warm decorative accents and semantic warning/danger colors remain intact.
4. `npm run build` from `UI_Project/` passes all five workspaces, and all four relevant web previews are visually inspected.
5. No API, backend, SRS, business-flow, or data behavior changes are introduced.

## Verification

- `npm run build` from `UI_Project/`.
- Manual visual review of Teacher, School Manager, Platform Admin, and shared web preview.
- `git diff --check` and `python tools/validate_repository_security.py` before every commit/push.

## Explicit exclusions

No API/network/auth/backend/schema/SRS/data/flow changes; no real user/child data; no changes to Parent UI or role-specific web layouts; no generated assets; no automated tests; no force push/history rewrite.

## Approval basis

The owner asked that the displayed colors become green and then asked about the other three web roles. This plan interprets the follow-up as a request to extend the green brand/action palette to the three web roles and their shared entry preview while preserving semantic status colors.
