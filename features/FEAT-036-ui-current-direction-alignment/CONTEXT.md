# FEAT-036 — UI direction alignment

## Goal

Turn the current UI review into a traceable, prioritized remediation plan for the Sketch2Life
product direction recorded in the owner-approved SRS and current ADRs.

## Current state

- Status: `AWAITING_APPROVAL` for product changes.
- This work is limited to runtime screenshot evidence and review; product implementation is not
  authorized. No product UI, application code, API contract, generated art, or runtime configuration
  was changed.
- The active visual app entry is `apps/ui-mobile/App.tsx` → `BaoApp.tsx` with 15 mobile screens.
  `apps/mobile` contains a fixture-flow screen; `packages/art-renderer` contains the separate Pixi
  demo/player. `apps/parent-web` and `apps/child-app` contain boundary READMEs, not product UIs.
- Review authority: `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` (owner-approved
  operational surfaces and B30–B33 changes), ADR-0012 (complete topic+age activity set), and
  ADR-0013 (Pixi subject-only behavior and reviewed companions).
- The original `ui-current-20261005` album is preserved. A separate `ui-full-20261005` album now
  contains 13 fresh emulator PNGs with no exact duplicate hashes: 11 active route components
  (Splash through Pixi Intro), one inline voice-recording state, and one activity-prerequisite
  state. The standalone Voice route and the Video Placeholder, Outdoor Activity, and Feedback routes
  were not reachable in the native flow. Gate A and Gate B were completed with synthetic input;
  Pixi renderer preparation then failed on retry, blocking the final three routes. The app's native
  React Native Dev Menu has runtime tools but no app-screen quick switch; the 15-screen switcher and
  `?screen=<id>` selector are Web-only, and Expo Web still leaves the root empty. The selected
  drawing is clear in the live Story Preview; the default-state thumbnail contrast finding remains
  only partially verified. Details, route coverage, and hashes are in
  `evidence/screenshots/ui-full-20261005/README.md`.

## Constraints

- Do not interpret UI visibility as authorization; backend policy remains authoritative.
- Do not revive the old readiness/material questionnaire for normal activity discovery.
- Do not label missing video as `READY`, conflate Pixi with illustrated video, or let a placeholder
  bypass required gates.
- Parent Web and Guide Console are target product surfaces in the current SRS. Their implementation
  needs their own scoped/approved work and must not receive an assumed team allocation here.
- Keep external providers, credentials, production data, asset-rights promotion, and deployment out
  of this task.

## Dependencies and open questions

- Video player/status UX depends on an approved versioned video contract and its owning runtime task.
- Parent Web / Guide Console scope and any web stack choice must be reconciled with the project
  context and recorded in an ADR before implementation.
- Current Android screenshots do not establish every screen or device size. A fresh device matrix is
  part of the proposed verification plan.
