# Leader review UI/UX remediation

- **Feature:** FEAT-069
- **Revision:** 1
- **Status:** APPROVED for this exact scope.
- **Approval basis:** User's direct instruction on 2026-11-14: “bạn làm sao cho đáp ứng yêu cầu của leader cho tôi đi”. The task is limited to leader feedback that can be reconciled with FEAT-063 SRS v2.5-draft and the mounted API surface.

## Goal

Improve the Parent mobile and Teacher web experiences against the provided leader transcript while preserving canonical product flow, privacy boundaries, and truthful preview/API states.

## Sources reviewed

- `docs/context/SRS_AUTHORITY.md`
- `docs/context/PROJECT_CONTEXT.md`
- `docs/context/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §§5, 7, 31–32
- `features/FEAT-068-project-uiux-coverage/CONTEXT.md`, `DECISIONS.md`, `evidence/notes/API_UI_CROSSWALK.md`, `evidence/notes/EXECUTION.md`
- User-provided leader-review transcript (local-only attachment).
- Current Parent/Teacher UI source and mounted API client/route crosswalk.

## Scope

### Parent Android/WebView UI

1. Expand the lesson picker by default at story setup and show explicit public-system and school/teacher-shared sections. Keep selection in the story flow and preserve the in-place details dialog.
2. Improve the optional pre-capture guide as a short, stepwise illustration keyed only to a generic lesson/topic. Keep skip available and label the guide as static preview until the approved API is connected; do not send child/profile/media data.
3. Ensure the lesson direction choice appears only after capture and subject review. Do not add a mismatch modal without a defined API state.
4. Simplify recording/upload/error copy. Remove redundant duration and transcript-confirmation helper prose from the main screen, but retain an editable adult transcript/review control and state that ASR is not connected where needed to avoid implying automatic transcription.
5. Present the minimal context snapshot in a compact confirmation dialog rather than a separate “choose context” page. Continue to require adult confirmation before story generation, as FR-P-06 requires.
6. Compact the home hero so the create action is visible without scrolling on a normal phone viewport. Keep the center “+” as the primary shortcut, and avoid dynamic story-card dependencies on the home screen.
7. Keep settings available from the global gear and keep the profile view focused on child profiles.

### Teacher web UI

8. Adjust text/surface contrast using the existing design system; retain the existing absence of a duplicate dashboard notification card and the centered lesson-detail modal.
9. Present the session sequence clearly: choose assigned class → choose lesson/version/activity → start session → optional step-by-step Sketch Deck and activity interaction → open the distinct sample-story flow when needed. Do not mix the sample video run into the reusable classroom occurrence or claim server persistence.
10. Keep dashboard data visibly preview-only until an authenticated principal, organization context, and supported connected client are present. Do not invent tenant IDs or call a shared API with fixture identity. Record this as an integration blocker against the leader’s “dashboard matches API” request.

## Product conflicts / open questions

- Parent outdoor activities before video conflict with SRS §5.1 / FR-P-05 / FR-PL-16. Keep the SRS order until owner changes it.
- The requested child gender field is not in the canonical SRS/API model. Keep it out of persistent profile UI until owner approves a data-model change.
- The leader’s conditional lesson-deviation modal has no defined mounted analysis result/contract. Keep the supported subject correction and post-capture lesson direction choice; record the desired modal as an open product/API question.
- Parent line-sketch must use a generic topic/difficulty and cannot use a child’s photo, profile, voice, or drawing. This UI revision may show a static topic illustration only; it must not claim AI generation.
- Teacher dashboard cannot be genuinely data-connected because current login expects `window.sketch2lifeAuth` and `GET /api/auth/v1/me`, neither of which is implemented in this checkout; the current dashboard/API methods are not called by the role pages.
- “Show Slide” generated content and the full occurrence workflow are not available in the mounted API surface. Keep static step previews visibly labeled and the sample run separate.

## Acceptance criteria

- **AC1:** Story setup shows the lesson library and distinct system-public and school/teacher-shared categories without navigating away; details open in a modal.
- **AC2:** Optional guide has a clear 3-step sequence, generic-topic illustration, previous/next/skip behavior, and honest static-preview status; it does not use child data.
- **AC3:** Lesson direction selection is only reachable after capture and subject review; the screen does not promise AI comparison or fabricate a mismatch decision.
- **AC4:** Audio controls and errors use concise copy; transcript editing remains available and no ASR success is implied.
- **AC5:** Context confirmation remains required but is compact and not shown as a separate context-selection page.
- **AC6:** Parent home places the create action and center plus within the initial phone viewport, with no dynamic story-card feed; settings remain global.
- **AC7:** Teacher text contrast is improved; lesson details remain centered; session selection and presentation order are clear, with optional deck and sample story kept distinct.
- **AC8:** All disconnected role data and API actions remain honestly preview-only; unresolved API needs are documented rather than hidden.
- **AC9:** Parent Android bundle and the affected web workspaces build; Parent UI is inspected at emulator-sized dimensions and all three role entry points are checked in browser; screenshots/commands/results are stored in FEAT-069 evidence.
- **AC10:** Feature context/decisions/evidence/status and root source register are updated; `git diff --check` and `python tools/validate_repository_security.py` pass before a normal commit/push to the authorized branch.

## Implementation steps

1. Update Parent lesson picker, topic guide, audio copy and compact context confirmation.
2. Reduce the Parent landing-page vertical footprint without replacing the existing approved visual system.
3. Tune Teacher contrast and make the session sequence easier to scan while preserving its SRS boundary.
4. Build the Parent/web workspace outputs and inspect the changed screens. Do not add or run automated tests.
5. Record evidence and open product/API questions. Update feature and source-register state.
6. Run diff/security checks. Commit and push only the scoped, reviewed changes, using normal fast-forward behavior.

## Risks and mitigations

- **Leader feedback diverges from SRS:** implement only the compatible work; list conflicts and do not silently change product behavior.
- **Missing ASR/guide/occurrence/auth integration:** use clearly labeled preview states and no false success.
- **Compact UI could obscure required confirmation:** keep consent/context confirmation visually prominent in a dialog and verify on phone-sized layout.
- **Four role workspaces are shared-code coupled:** limit changes to Parent UI and shared Teacher components; inspect the other role entry points for regressions.

## Verification and evidence

- Build commands: `npm run build` from `UI_Project`; `pnpm typecheck` from `UI_Project/parent-android`; `pnpm --dir apps/mobile android:apk:debug` from `UI_Project/parent-android`.
- Manually inspect Parent home, lesson selection/details, guide, audio transcript, and context confirmation on the supplied Android emulator or current app viewport.
- Open Teacher, School Manager, and Platform Admin workspaces and inspect contrast/entry points; inspect Teacher session sequence and lesson modal.
- Store evidence in `features/FEAT-069-leader-uiux-review-remediation/evidence/`.
- Run `git diff --check` and `python tools/validate_repository_security.py` before commit/push. No automated test suite is authorized by this plan.

## Explicit exclusions

Backend/API/database/auth/schema/SRS/provider/deployment changes; API writes; live ASR/AI/provider calls; child data; new persisted profile fields; pre-video Parent activities; removal of adult context/script confirmation; release signing; force push/history rewrite; changes to the Child Expo workspace; generated raster asset creation.
