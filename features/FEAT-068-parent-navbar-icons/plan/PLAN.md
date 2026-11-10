# FEAT-068 — Parent navbar icon refresh

- Status: APPROVED
- Plan revision: 1
- Implementation status: COMPLETE

## Goal

Replace the five glyphs in the Parent navigation with a cohesive, clearer SVG icon set that better distinguishes home, history, capture, creation credits, and settings.

## Scope

- Target the Parent bottom navigation and the same navigation when it becomes the tablet landscape rail.
- Refresh the home, history, create-camera, creation-credit, and settings glyphs using the existing inline SVG component and visual tokens.
- Keep the five tab labels, routes, order, active-state treatment, and hit areas unchanged.
- Add no icon package or generated image assets; keep the icons as accessible decorative SVGs in the existing icon system.
- Do not change other uses of the shared icon names, product behavior, API/backend, or other portals.

## Acceptance criteria

- AC1: All five navigation symbols are visibly refreshed and form one rounded outline style with consistent optical weight.
- AC2: Each glyph is recognizable from its Parent navigation label; the history icon indicates history, the credit icon indicates available creation uses, and settings is distinct from a sun/weather symbol.
- AC3: Labels, routes, ordering, active selection, create-action accessible name, and responsive navigation layout remain unchanged.
- AC4: The icons render clearly in phone portrait, tablet portrait, and tablet landscape sizes without clipping or shifting the navigation.
- AC5: Source changes and local screenshots are recorded under this feature. Do not run a test suite or build for this visual-only request.

## Steps

1. Inspect the existing Parent icon mapping and navbar usage; choose internal SVG paths that do not alter icons elsewhere.
2. Implement the new five-glyph set in the shared Parent icon component and map only the navbar to it.
3. Review screenshots at phone portrait, iPad portrait, and iPad landscape sizes, then record evidence and status.

## Product authority

This is a presentation-only change to the existing Parent web preview. The canonical working SRS is FEAT-063 v2.7-draft Rev57 and remains unsigned. No product requirement or Parent Android target behavior is changed.
