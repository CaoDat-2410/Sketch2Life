# FEAT-084 — Parent mobile UI polish

## Goal

Review the full Parent Expo mobile UI and make the topic/drawing-subject suggestions and the densest Parent drawing-flow screens easier to scan, more visual, and consistent with the existing mobile component system.

## Authority

- Current product requirements come from the FEAT-063 canonical SRS v2.7-draft, currently recorded through Rev75 and still unsigned.
- Parent topic and subject suggestions follow §§5.1 and 31.20/31.22: three rotating catalog cards, separate text inputs, custom-topic object entry and validation, with suggestions remaining distinct from the VLM-confirmed drawing subject.
- The current mobile code is the source of as-built UI behavior. This task does not claim the API, Modal, or emulator works.

## Scope and constraints

- Mobile Parent UI only. No Teacher Web, backend, API contracts, AI prompts, database, business rules, or SRS changes.
- Preserve the current component library, creative palette, touch/accessibility behavior, confirmations, error states, safety information, and workflow transitions.
- Keep all suggestion content data-driven. Only visual metadata such as icons and artwork may be mapped locally.
- Reuse existing approved topic artwork and Ionicons; create no new image assets.
- Do not run tests, typecheck, API calls, inference, emulator, or commit/push for this task.

## Current status

The approved source changes are applied. Topic cards now use topic-appropriate imagery or icon/color fallbacks, and object cards use subject cues; catalog content remains server-driven. Activity and capture copy were shortened without removing safety, instructions, or transfer transparency. `git diff --check` and static asset/icon reference checks are clean. No tests or device verification were run during source implementation; the later screenshot-only run is recorded below.

## Android screenshot run — 2026-11-23

The real Expo app was launched on Pixel_10. The original synthetic Parent login was rejected by Firebase before the backend role check. Only the sign-in, sign-up, and password-recovery forms were captured. Docker showed existing healthy backend containers, but the root `.env` mobile URL pointed to an inactive port; it was corrected to the running Parent auth API. After the owner-requested retry, the login form remained with no visible result; the submit callback was not observed in app logs. No authenticated flow, backend record creation, AI/Modal call, or test was performed. See `evidence/ANDROID_UI_SCREENSHOTS_20261123.md`.
