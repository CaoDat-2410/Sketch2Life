# Plan Rev11 — Parent primary actions use the green palette

## Goal

Align the Parent mobile preview's primary/start action colors with the green selected-state palette shown in the owner's screenshots. The current “Bắt đầu kể” action is blue/teal while the selected “Tất cả” control is green; primary actions and their selected/focus/hover variants should read as one consistent green interaction system.

## Scope

- Inspect the Parent stylesheet cascade and identify the effective rules for the main “Bắt đầu kể” action and comparable primary/selected controls.
- Replace blue/teal primary-action and selected-control colors in `UI_Project/parent-ui/` with coordinated green shades that retain readable contrast and visible interaction states.
- Preserve layout, labels, flow behavior, warning/danger colors, and the existing yellow/gold arrow accent unless a shown primary control uses it as part of its icon treatment.
- Keep the change local to Parent UI styling; do not alter role workspaces or shared business behavior.
- Build the Parent workspace and visually inspect the relevant preview at desktop and mobile widths.
- Record the actual source, review evidence, decision, and completion status in FEAT-069 and update the source register.

## Acceptance criteria

1. “Bắt đầu kể” uses the same green family as the selected “Tất cả” control, including hover/focus interaction shades.
2. No blue/teal primary-action fill remains on the Parent screens in this scope; unrelated semantic/info colors and warm accents remain intentional.
3. Text and icons remain legible, and the gold arrow accent remains visible.
4. Parent preview builds successfully and the updated interaction states are visually inspected at desktop and mobile widths.
5. No API, backend, SRS, data, or flow behavior changes are introduced.

## Verification

- `npm run build` from `UI_Project/`.
- Manual visual review of the Parent preview for the hero action and selected filter state.
- `git diff --check` and `python tools/validate_repository_security.py` before commit/push.

## Explicit exclusions

No API/network/auth/backend/schema/SRS/data/flow changes; no real child or user data; no changes to other role workspaces, legacy `apps/`, or Child Expo; no generated raster assets; no automated tests; no force push or history rewrite.

## Approval basis

The project owner directly requested that the shown colors be changed to green. This plan interprets the green selected control in the second screenshot as the target interaction family and keeps unrelated gold accents intact.
