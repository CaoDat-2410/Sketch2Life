# Pixi story intro and topic directions implementation — 2026-09-23

Evidence ID: `EV-018-PIXI-STORY-INTRO-20260923`

## Scope completed

- Added at most three distinct, complete Vietnamese topic directions linked to exact understanding
  claim IDs, with image/narration coverage and confidence bands.
- Kept the owner-approved one-requery rule when a non-primary direction is selected.
- Preserved Gate A and Gate B meanings and the reviewed-catalog activity boundary.
- Split the visible journey into adult activity review, landscape Pixi story intro, landscape main-
  video placeholder, portrait outdoor activity and feedback.
- Added renderer play, pause, replay, relative/absolute seek and progress envelopes with strict
  instance, sequence and range validation.
- Added a four-beat original-art animation plan and synchronized Vietnamese captions. The source
  image and SHA-256 remain authoritative; no replacement image or real video is generated.
- Added stage-aware understanding and renderer loading copy, bounded timeout, source-image
  fallback and friendly recovery controls.
- Added `expo-screen-orientation`, enabled both Android orientations and restored portrait before
  the outdoor activity.
- Rebuilt the ignored Vite renderer bundle locally before starting the backend. Clean deployments
  must continue to run `pnpm --filter @sketch2life/art-renderer build:demo` as documented in
  `apps/ui-mobile/BACKEND_INTEGRATION.md`.

## Verification

| Check | Result |
|---|---|
| Backend focused Ruff | Passed |
| Backend focused mypy (3 changed services) | Passed |
| Backend focused unit/contract suite | 24 passed |
| Full backend suite with an isolated `--basetemp` | Reached 100%, no failures; expected skips only |
| Workspace TypeScript | Passed |
| Workspace JS tests | Renderer 10 passed; legacy mobile 7 passed; UI copy/recovery guard passed |
| Renderer Vite production build | Passed; `/renderer/mobile.html` and bundled JS returned HTTP 200 |
| Architecture validator | `ARCHITECTURE_VALID` |
| Repository security validator | `REPOSITORY_SECURITY_VALID` |
| `git diff --check` | Passed |
| Android x86_64 debug build | Passed, 387 tasks executed |
| Android install/boot | Passed on `emulator-5554`; no fatal React Native/Android runtime log found |

The first Android Gradle attempt exposed two machine-local cache issues: project-cache rename failed
on the workspace drive and stale `expo-av` CMake state looped for arm64. A fresh project cache under
the user temp directory plus the emulator's x86_64 architecture produced a successful build. These
were build-environment issues, not product-code failures.

## Evidence artifacts

- `evidence/screenshots/pixi-flow-android-smoke-20260923.png`: newly built app booted in portrait on
  the Android emulator.
- Backend health, OpenAPI and renderer mobile bundle all returned HTTP 200 after restart.

## Remaining owner-run acceptance

Codex did not invoke the live Lightning endpoint or spend the owner's credits. The owner still needs
to run one synthetic/non-child image through the complete live flow and verify the actual transition
portrait → landscape Pixi → landscape video placeholder → portrait outdoor activity, all timeline
controls, fallback/back behavior and the quality of the returned topic directions. No real-video
acceptance is expected in this increment.

The unrelated untracked `FEAT-026-current-system-srs` files were not modified or staged. The global
harness validator still reports only that feature's pre-existing missing `evidence/raw` and
`evidence/metrics` paths; FEAT-018 architecture and security checks pass.
