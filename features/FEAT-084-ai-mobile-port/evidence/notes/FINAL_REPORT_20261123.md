# FEAT-084 final report — 2026-11-23

## Gate and authority

- Implemented on `codex/aiport2-mobile-ai-20261123`, based on `d8786b2b0bf14c940b1ae6df512dc89d7ae3dcee`.
- The approved plan hash matched `TASK_APPROVAL.md` before implementation. The approval record was not changed.
- Product behavior follows the FEAT-063 v2.7-draft SRS through `docs/context/SRS_AUTHORITY.md`. No SRS or authority files were changed.
- Backend request and response mapping was checked read-only against FEAT-083 at `283158a83aa08042832e41cb2a93b707e4ea9558`.

## Source work ported and adapted

The selected UI pieces were brought over from source commit `77635688deed0114ac62c28c3f936da62144d59c` and adapted to the current app flow:

- `apps/ui-mobile/src/parent/domain/svgGuide.ts`
- `apps/ui-mobile/src/parent/domain/topicMatching.ts`
- `apps/ui-mobile/src/parent/presentation/components/ParentAiLoadingState.tsx`
- `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/DrawingSubjectScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/LearningPathScreen.tsx`
- Topic and subject chooser portions of `apps/ui-mobile/src/parent/presentation/screens/TopicScreen.tsx`
- Added `apps/ui-mobile/tests/parentTopicMatching.test.ts` and `apps/ui-mobile/tests/parentSvgGuide.test.ts`.

`SketchGuideScreen.tsx` is a scoped implementation for the source-draft contract. It shows the guide as an adult-reviewed, non-persisted draft and always offers skip/continue; it does not bring in the source branch's retired catalog or modal response routes.

## Hand-merged integration

- Added topic, subject suggestion and custom-subject validation models in `domain/types.ts`.
- Added the three suggestion/validation ports through `ParentPorts.ts`, `ParentApplicationModule.ts` and `ParentLearningUseCases.ts`.
- Added exact topic/subject query paths and the versioned SVG guide request/response to `ParentApi.ts`. Exclusion arrays are capped at the backend limits; text inputs follow model lengths. Only bounded, control-character-free API copy for the two allowlisted topic errors reaches the UI through `safeDisplayMessage`.
- Added topic entry/selection, subject validation, optional guide review and safe fallback handling in `parentFlowV1.ts`, `workflowTypes.ts`, `useParentController.ts` and `ParentExpoApp.tsx`. When a lesson is pinned, the SVG draft is reviewed first and then the existing lesson guide remains available.
- Updated the visual preview harness only to supply the new required topic screen props. Phase A activity selection, run creation after photo, lifecycle, replay, and resume behavior remain on the existing wiring.
- No video-candidate, AI activity, auth provisioning, config, backend, Modal, SRS, or provider-call work was included.

## AIPORT1 models checked

- `ParentTopicSuggestionSetV1`
- `ParentDrawingSubjectSuggestionSetV1`
- `ParentCustomSubjectValidationRequestV1`
- `ParentCustomSubjectValidationV1`
- `SvgTopicStrokeGuideRequestV1`
- `SvgTopicStrokeGuideSourceDraftResponseV1`

The mobile request uses `{ contract: 'SvgTopicStrokeGuideRequestV1', topic, intended_subject?, difficulty: 'beginner' }`. The old `step_count` request and image response are retired. A `CURATED_SVG_GUIDE_NOT_FOUND` response is shown as an optional-guide condition, with no retry/fallback request.

## Tests

- Baseline on `d8786b2b`: 18 files, 228 tests passed.
- Current: 20 files, 239 tests passed.
- Added 11 tests: four topic matching, three SVG guide safety/behavior, and four API contract/error cases.
- Edited source-contract expectations in `parentSrsBehavior.test.ts`:
  - `keeps topic and lesson pin optional while showing server version and invitation states` now asserts backend topic cards and their selection callback.
  - `keeps camera and gallery alternatives, pre-upload limits, and one artwork per run` now asserts the typed source-draft guide integration and versioned contract instead of the retired image response shape.
- Four API cases appended to `parentApiI2Contract.test.ts`: topic/subject route fields, the versioned SVG request, the two safe Vietnamese topic messages, and the single-call 404 optional-guide path.

## Validation

- `node node_modules/vitest/vitest.mjs run tests`: **20 files / 239 tests passed**.
- `node scripts/validate-ui-copy.mjs`: **UI_COPY_AND_RECOVERY_VALID**.
- `tsc --noEmit -p tsconfig.typecheck.json`: **111 errors, 0 outside `packages/art-renderer`**, matching the 111-error baseline. The errors are caused by missing `zod` in the linked environment.
- `python tools/validate_repository_security.py`: **REPOSITORY_SECURITY_VALID**.
- `python tools/validate_architecture.py`: **ARCHITECTURE_VALID**.
- `python tools/validate_harness.py`: **HARNESS_VALID**.
- `git diff --check`: passed.

## Not run and open follow-ups

- `pnpm exec` attempted to reconcile modules and aborted before running; no install was performed. Direct binaries from the existing linked dependencies were used instead.
- No Android build, emulator/device visual review, live provider, Firebase, or paid API call was run.
- Existing owner questions remain: decide whether to adopt SRS Rev70–Rev73, and handle the video-candidate screen and AI-generated activity set as separately approved follow-ups. No new owner question was introduced.
- No commit or push was made.
