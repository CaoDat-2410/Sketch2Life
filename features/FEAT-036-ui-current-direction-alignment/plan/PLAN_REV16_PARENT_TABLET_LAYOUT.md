# FEAT-036 plan revision 16 — Optimize Parent UI for iPad

- Revision: 16
- Status: APPROVED
- Prepared / approved: 2026-11-10
- Type: Parent responsive UI refinement for tablets
- Product baseline: FEAT-063 SRS v2.7-draft from the main checkout; unsigned working baseline.
- Requirement boundary: responsive presentation only. Parent Web target-client scope remains open in the SRS.

## Objective

Make the Parent demo comfortable to use on iPad in portrait and landscape instead of stretching phone-oriented content across the full tablet width.

## Scope

1. Add a touch-first tablet breakpoint for the Parent app shell, page content, and bottom navigation.
2. Keep long-form content centered at a readable maximum width on landscape tablets; use safe-area-aware page spacing and preserve the existing full-screen tablet shell.
3. Improve the Home and quota layouts for landscape space where existing content can use columns without changing the task flow.
4. Preserve auth layout from revision 14, auth/session behavior from revision 15, and existing phone styling below tablet width.
5. Keep buttons and navigational controls at least 44 px where practical; prevent horizontal overflow in the reviewed screens.
6. Review Home, history, capture, quota, and settings on iPad-sized touch viewports. Store local screenshot evidence and measured widths under FEAT-036.

## Acceptance criteria

1. At 820×1180 portrait and 1180×820 landscape, reviewed Parent screens use deliberate tablet spacing and do not stretch long text or controls edge-to-edge.
2. The landscape content column and bottom navigation remain centered and bounded; the portrait layout uses the available width with safe margins.
3. Home, history, capture, quota, and settings have no horizontal overflow. Primary controls remain usable at tablet touch sizes.
4. Existing 320×568 and 375×812 phone layouts remain unchanged and usable; auth routes retain their revision 14 two-column tablet design.
5. The local Vite Parent UI and reviewed routes render. Visual evidence, viewport metrics, and limitations are recorded in FEAT-036.
6. No authentication/API/backend behavior, SRS requirement, asset, or dependency changes.

## Out of scope

- Changing Parent product scope or any portal other than Parent.
- Authentication, account recovery/registration, backend/API contracts, or Firebase configuration.
- New/generated assets, dependency changes, automated tests/builds, deployment, publishing, commit, or push.

## Verification approach

Manually inspect touch-emulated iPad portrait/landscape and phone browser viewports using local demo data only. Confirm viewport/document widths, route rendering, and touch target sizes. Automated tests/builds are outside this authorization.