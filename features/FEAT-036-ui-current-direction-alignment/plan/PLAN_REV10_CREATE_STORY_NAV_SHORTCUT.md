# FEAT-036 plan revision 10 — Centered create-story navigation shortcut

- Revision: 10
- Status: `APPROVED`
- Prepared: 2026-11-10
- Type: Parent navigation shortcut
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 (unsigned), routed by
  `docs/context/SRS_AUTHORITY.md`
- Parent Web target-client scope remains an open SRS question; this is a bounded local UI change.

## Objective

Add a large, visually prominent camera shortcut at the center of the Parent bottom navigation so
the user can enter the existing create-story capture flow from primary navigation screens.

## Scope

1. Keep existing navigation destinations and place a raised camera action in the center slot.
2. Use the current Parent palette and accessible touch target; label it “Tạo”.
3. Route to the existing `/p04-capture-subject-confirmation` capture-first entry and set the same
   optional-setup skip state used by the Home hero CTA.
4. Preserve the existing no-quota behavior: warn when quota is exhausted but allow capture to start.
5. Support both the four-item local-preview nav and the two-item product nav, centering the camera
   between the remaining destinations.
6. Update FEAT-036 context, decision, status, and evidence.

## Acceptance criteria

1. The desktop/mobile bottom navigation contains a prominent center camera control between the
   existing destinations.
2. Activating it enters the existing capture-first story flow and skips the optional drawing setup,
   matching the Home hero behavior.
3. Existing tab links and active states continue to work in local preview and product-nav modes.
4. The control has a descriptive accessible name, visible keyboard focus, and a touch target of at
   least 44 CSS pixels.
5. Vite serves the affected module/styles and `git diff --check` passes. No automated tests/builds
   are authorized by this plan.

## Out of scope

- Changes to story flow screens, backend/quota logic, other portals, native navigation, deployment,
  publishing, commit, or push.

## Authorization

The project owner explicitly requested a large camera icon in the center of this navbar as a
shortcut into the story-creation flow. This is the approval for the bounded implementation above.
