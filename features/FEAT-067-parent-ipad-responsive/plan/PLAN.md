# FEAT-067 — Parent UI iPad responsive redesign

- Status: APPROVED
- Plan revision: 2
- Implementation status: COMPLETE

## Goal

Make the Parent portal visibly fit iPad/tablet portrait and landscape viewports across its complete route set. Replace the current phone-scaled appearance on tablets with deliberate content proportions, navigation, spacing, and layouts for tablet dimensions.

## Scope

- Work in the Parent UI files in `F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation`: `apps/parent-ui` and only Parent-specific styling under `apps/parent-ui/src/styles`.
- Cover login, recovery, registration, lesson library/detail, story creation/review/status, video/activities/feedback, history, quota, settings, and child profile routes.
- Cover 700–1440 CSS px tablet viewports, including common iPad dimensions from 744×1133 through the 13-inch iPad Pro candidate viewport of 1376×1032. Apply the landscape composition to touch devices and tablet-like viewport ratios; keep wide desktop ratios on the existing desktop layout.
- Use viewport shape and orientation breakpoints, with touch capability as an additional tablet signal. This allows iPad-sized browser previews without touch emulation while avoiding tablet navigation on wide desktop screens. Respect safe areas, touch targets, readable line lengths, and the current Parent visual system.
- Keep product flow, SRS behavior, authentication, API contracts, and desktop/phone behavior unchanged.

## Acceptance criteria

- AC1: Tablet portrait uses a tablet-sized shell and centered reading width, with appropriate two-column card/form layouts where content benefits from them.
- AC2: Tablet landscape has a visibly distinct, balanced navigation/content composition rather than a stretched phone layout; the content remains readable and primary actions remain easy to reach.
- AC3: All Parent routes remain within the viewport width with no unintended horizontal scrolling; forms, dialogs, media, tabs, and long text wrap safely.
- AC4: Touch controls have comfortable tablet hit areas; top/bottom safe areas and both orientations are handled.
- AC5: Phone layouts below tablet breakpoints preserve their existing composition and SRS-defined flow.
- AC6: Record source changes and viewport evidence in this feature folder. Do not run a test suite or modify unrelated apps.

## Steps

1. Inspect the Parent route/component structure and existing style cascade; identify why previous tablet rules have little visible effect.
2. Implement app-scoped responsive rules and only the small component adjustments needed to support tablet navigation/layout.
3. Review the rendered Parent routes at representative portrait and landscape iPad viewports, including the wider 13-inch landscape candidate, when the local preview/browser is available; record unavailable states honestly.
4. Update this feature's evidence, context, decisions, and status. Do not alter product requirements or backend behavior.

## Product authority

Use FEAT-063 SRS v2.7-draft Rev57 as the canonical working baseline. It requires Parent Android on `apps/mobile` and classifies `apps/ui-mobile` as reference (FR-P-01); this task is a presentational responsive improvement to the existing Parent Web preview surface and does not claim to complete the Android client. The SRS remains unsigned. No new product behavior is inferred.
