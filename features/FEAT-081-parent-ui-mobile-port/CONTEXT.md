# FEAT-081 — Parent UI mobile port

- Owner: Person 2 (AnhKhoaa157)
- Date: 2026-11-12, Asia/Saigon
- Status: Wave 1 ACCEPTED / COMMITTED (3c75b10d, not pushed); Wave 2A LAUNCHED; Wave 2B NOT LAUNCHED
- Initial Wave 1 baseline: feature/fe-mobile-remediation at 1f5bb0b5b1ab501a7120598a7e6e0de75217ddb3; HEAD tree equaled local origin/dev at that baseline.
- Current commit: `3c75b10d602d6262dc428706c8bdae92c7a0a8ff` on `feature/fe-mobile-remediation`; not pushed.
- Approved Wave 2 plan: Revision 3, 34,224 bytes, SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`.

## Goal

Implement the approved FEAT-081 waves in `apps/ui-mobile`. Wave 1 P01/P02 is accepted and committed as `3c75b10d` (not pushed); Wave 2A passed coordinator post-run; Wave 2B is implemented and awaiting coordinator post-run. Wave 2 remains uncommitted and is intended as one commit after 2B. Later waves remain separately gated.

## Product and source context

The current product source is the unsigned FEAT-063 v2.7-draft SRS, routed by docs/context/SRS_AUTHORITY.md and docs/context/SOURCE_REGISTER.md. It is the canonical working baseline, not formal SRS sign-off. Requirements in older feature records and the web sample are not current product authority. Preserve missing or conflicting product requirements as open questions.

The target is the Expo SDK 52 Parent application in apps/ui-mobile, using React Native 0.76.9 and React 18.3.1. The web sample is in sibling worktree .worktrees/ui on feature/fe-ui-full-remediation at 30c94342. It is external read-only reference material; no sample code or visual assets are copied by this plan.

## Owner and merge context

CaoDat built the existing ui-mobile base. The owner will edit the Parent UI from here on, without per-file ownership reservations. CaoDat may later edit the same paths on dev, so overlapping changes carry merge risk and must be reconciled before merging. Git history does not establish current in-flight ownership.

## Approved boundary

Wave 1 is limited to the alternative allowlist pinned in approvals/TASK_APPROVAL.md: edit HomeScreen.tsx and LessonGalleryScreen.tsx, add catalogViewModel.ts and catalogViewModel.test.ts, and keep the listed hash-only files byte-identical. Shared components/ui.tsx is not edited. The new test uses synthetic fixtures only and the wave makes no API changes.

Waves 2-5 are outline only and require separate approvals. P08c, P14, and P15 remain held pending a recorded product requirement. The move to apps/mobile, Android applicationId / validate_skeleton repair, backend-route wiring, package installs, runtime/provider operations, and external publication are outside this feature. OWNER_MODAL_CALL_APPROVED=NO; no Modal action is authorized.

For the later, separately approved move to apps/mobile, the recorded portability constraints are in D-006. Any sample image, avatar, icon, or font must first pass the repository generated-asset, provenance, and visual approval gate recorded in D-007.
## Revision 2 target clarification — 2026-11-12

The owner-directed FEAT-081 location is apps/ui-mobile for Wave 1 and for any separately approved FEAT-081 follow-on UI wave, with no move to apps/mobile under this feature. ADR-0023 and appended D-009 record this as a feature-scoped implementation-location exception. The canonical SRS Rev60 and the broader apps/mobile product target remain unchanged. This clarification supersedes the older future-move wording only within FEAT-081.

## Wave 1 implementation update — 2026-11-12

This is the pre-acceptance snapshot; the later owner acceptance checkpoint below is current.

Wave 1 P01/P02 code is implemented within the approved four-path allowlist. Coordinator post-implementation tests and typecheck, owner Android review, and owner acceptance remain pending. See `evidence/IMPLEMENTATION_REPORT_WAVE1_20261112.md` and the ignored command ledger at `tmp/fe081-impl/COMMAND_LEDGER.md` for file hashes and results.

The sample P01 shows an active-child selector; HomeScreen has no selected-child input and does not receive the controller's profile. Adding it needs ParentExpoApp.tsx, which is outside the Wave 1 allowlist. Owner chose Option A on 2026-11-12: label deferred. The item moves to a later wave that is separately approved to touch ParentExpoApp.tsx (together with useParentController.ts / workflowTypes.ts if that wave needs them). The active-child label is not applicable to Wave 1 and is not marked passed.

## Wave 1 owner acceptance checkpoint — 2026-11-12

- Status: ACCEPTED (Wave 1 only); not committed.
- Accepted scope: FEAT-081 P01 Home and P02 Lesson gallery in `apps/ui-mobile`.
- Final code pins accepted from the implementation report:
  - `HomeScreen.tsx`: 4,349 bytes, SHA-256 `A09E8BC37C30DCFB293B68172119DB62C06DF93D1201C068BCC79958433B28E3`.
  - `LessonGalleryScreen.tsx`: 9,876 bytes, SHA-256 `35D75628DF9220FABA787010E5E40A895FA99AE3A3A34F325E7B752DDFB04003`.
  - `catalogViewModel.ts`: 1,962 bytes, SHA-256 `5BE1210C95C9F1CEBABADEE7DAD2169620B5B438BA85DE24941236DF018630F0`.
  - `catalogViewModel.test.ts`: 3,254 bytes, SHA-256 `8FAA29A92BD4D750C27E2109256611BA3DA8ECFE1BE72044127A81B78699C978`.
- H-pin files are unchanged.
- Coordinator runs: `pnpm run test` passed 4 files / 29 tests and printed `UI_COPY_AND_RECOVERY_VALID`; typecheck had no diagnostics.
- Owner-run confirmations on 2026-11-12 23:56 after the filtered reinstall had the same test and UI-copy results; typecheck had no diagnostics; both exited 0.
- Owner-run validators on final bytes all exited 0: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (7,239 files); `ARCHITECTURE_VALID`; `git diff --check` clean.
- Owner report: the app ran on the Pixel_6a emulator via `android:dev` and started and ran.
- The active-child label is deferred per Option A. Wave 2 plan R2 is a draft, not approved and not launched. `OWNER_MODAL_CALL_APPROVED=NO`.
- This acceptance does not cover backend/API wiring, Android runtime behavior beyond "ran", later waves, a move to `apps/mobile`, or any SRS change. No stage, commit, or push is authorized; the commit requires a separate owner instruction.
- `TASK_APPROVAL.md`: pre-append pin 7,823 bytes / SHA-256 `76AD28534A90FD0C9A6B6572B9A2588B0717ED78A2E679DCE22CA3D1E8B7BC79`; post-append pin 11,058 bytes / SHA-256 `CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266`.

## Wave 2 plan approval checkpoint - 2026-11-13

- Wave 2 API wiring is APPROVED / NOT LAUNCHED under Addendum 4. `plan/PLAN_REVISION_3.md` is an exact copy of R2, 34,224 bytes / SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`; its DRAFT header is superseded by Addendum 4.
- D-010 records the six adopted owner product decisions: require the lesson pin, keep drawing-understanding unchanged with no added `Idempotency-Key`, keep consent removed, use Activity skip instead of `activity-suggestions`, use synthetic profiles with restore through the list route, and keep `OWNER_MODAL_CALL_APPROVED=NO` with the owner-run flow stopping before drawing-understanding.
- 2A and 2B are separate launch gates. Each requires its own explicit owner instruction; 2B also waits until 2A passes. The pending S1a-P2 list/delete/role-gate contract is accepted as the working basis for 2A and may change slightly; changes after S1a-P2 acceptance require a new addendum.
- Baselines are the owner-run results of 2026-11-12 23:56 and 2026-11-13 00:15 on bytes identical to commit `3c75b10d`: `pnpm run test` passed 4 files / 29 tests with `UI_COPY_AND_RECOVERY_VALID`; typecheck had no diagnostics; `validate_harness`, `validate_repository_security`, `validate_architecture`, and `git diff --check` all exited 0. Baseline invocations are consumed under the R2 ceilings.
- D-010 pre-append DECISIONS prefix: 3,950 bytes / SHA-256 `3952CB3BCA12ABD21109B3F209A181CF3B91F3D1D01FAEEB5DA64ABFD64A3805`; after D-010: 6,312 bytes / SHA-256 `B1D747786B88AC0F0F4DCCE4221099687764752E45B2D90D6080C9E79FD165FC`.
- Addendum 4 pre-append TASK_APPROVAL pin: 11,058 bytes / SHA-256 `CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266`. Its final post-append pin, including the append-only ProfileSharingScreen hash correction, is 23,557 bytes / SHA-256 `D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE`.

## Wave 2A launch checkpoint - 2026-11-13

- Status: Wave 2A LAUNCHED / Wave 2B NOT LAUNCHED. 2B requires its own explicit owner launch instruction after 2A passes.
- Launch scope: the seven 2A E paths and two 2A N tests in Addendum 4 only. The sole added record path is `evidence/IMPLEMENTATION_REPORT_WAVE2A_20261113.md`, mode N, authorized by the owner; the 2B report path needs its own authorization.
- Addendum 5 pre-append approval pin: 23,557 bytes / SHA-256 `D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE`; post-append approval pin: 25,349 bytes / SHA-256 `9EAE14F557D8F650970294BF6E02AA658C9B5A4A316BAD2406F1803D3F17778B`.
- The Wave 2A evidence-path authorization is recorded verbatim in Addendum 5 and the command ledger. No implementation has been reported yet in this launch checkpoint.

## Wave 2A cold-review steering - 2026-11-13

- Review: `tmp/fe081-wave2/REVIEW_R2_ROUND1_20261113.md`, verdict `NEEDS REVISION`; the owner accepts the findings for 2A.
- Keep existing API methods/types/signatures and legacy `StoryRun` types unchanged; add new V1 methods/types. Preserve `authorization_state`, `authorization_policy_version`, and `authorization_current`.
- Add a distinct pre-drawing StoryRun create and context-confirm action without image, policy/consent, profile-revision, or `context_confirmed` inputs.
- Retain the same idempotency key for retries of one action and allocate a new key for a new action. Profile deletion stays `DELETE_PENDING`; reconcile by GET-by-ID, because list contains ACTIVE profiles only.
- Cover omitted/null patch interests, idempotent profile/run command retries, pending-delete replay/transition, and top-level plus defensive nested error parsing with synthetic fake ports/fetch only.
- The merged `app.py` error shape and usable lesson data on the scratch service remain NOT VERIFIED. The accepted 2B review findings are deferred to its own launch addendum.
- Addendum 5 launch pin: 23,557 bytes / SHA-256 `D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE`; immediate post-launch pin: 25,349 bytes / SHA-256 `9EAE14F557D8F650970294BF6E02AA658C9B5A4A316BAD2406F1803D3F17778B`; post-review-note pin: 25,709 bytes / SHA-256 `773B46FFFB1D30BFE6626A2363EE2EEB2DE9072EBCF16ECA54B3E39A8E4BE0D9`.

## Wave 2A implementation checkpoint - 2026-11-13

2A implementation is complete within its seven approved E paths and two N tests; it is awaiting coordinator post-run and has not been accepted. 2B remains NOT LAUNCHED and requires a separate owner instruction. The implementation report is `evidence/IMPLEMENTATION_REPORT_WAVE2A_20261113.md`, 9,315 bytes / SHA-256 `5288C3E0679237ED75F767ADB32BBF10F6AE75D17A2492D9431AAA92B41AAB7C`.

V1 profile and StoryRun methods/types are additive; the existing API surface, authorization fixture fields, and legacy StoryRun types remain intact. A pre-drawing use case requires the lesson pin and confirms the returned context. Profile delete reconciliation is GET-by-ID while pending; patch stale revision refreshes once without retry. Action keys are caller-retained for retries, error messages are mapped safely, drawing-understanding gets no added key, and activity-suggestions is not called.

The owner-run 29-test/typecheck baseline is consumed. The post-2A test and typecheck invocations are NOT RUN and remain coordinator-run. The merged `app.py` error shape and usable lesson data on the scratch service are NOT VERIFIED. No stage, commit, or push occurred.

## Wave 2A post-run rework checkpoint — 2026-11-13

Wave 2A remains LAUNCHED / not accepted; Wave 2B remains NOT LAUNCHED. The coordinator's consumed post-2A run reported 1 failed / 43 passed (44 tests, 6 files), plus one unhandled rejection; the 29 existing tests passed. Typecheck reported one TS2322 nullable active-run envelope error. Read-only diagnosis confirmed the lesson-pin guard rejects asynchronously while its test asserted synchronously. The test now awaits the rejection and confirms run creation is not called for absent or incomplete pins. A named nullable `ParentActiveStoryRunEnvelopeV1` now covers only the active-run read; non-null create/read envelopes remain intact, and recovery rethrows the original conflict when active-run is null.

The owner authorized one extra coordinator test and typecheck run for this rework only. Accounting: baseline 1/4, failed post-2A 2/4 consumed, rework run 3/4 pending, and the one post-2B run 4/4 remains. The implementation report is 13,980 bytes / SHA-256 `8DD31E5AC2881F5249D6B687E061571F50D45F2B81EDF39DB3BF32A2E0A1217E`. Addendum 6 changed the approval from its 25,709-byte / `773B46FFFB1D30BFE6626A2363EE2EEB2DE9072EBCF16ECA54B3E39A8E4BE0D9` pre-append pin to 27,265 bytes / `64ABD9A8D94B84731965F99324E1E481B14B6005B2E0FF32F2505CACAC7B3E62`. No checks were run by Codex; nothing was staged, committed, or pushed.
## Wave 2B launch checkpoint — 2026-11-13

The owner reports that 2A passed coordinator post-run: 6 files / 45 tests passed, typecheck had no diagnostics, and the 29 older tests remain intact. Wave 2B is LAUNCHED under Addendum 7. Its allowlist is seven existing E paths plus owner-authorized `parentFlowV1.ts`, `parentFlowV1.test.ts`, and the Wave 2B evidence report. H files remain frozen and R files remain read-only. `OWNER_MODAL_CALL_APPROVED=NO`; the owner flow stops after context confirmation, before drawing-understanding or story-revisions.

Addendum 7 changed `TASK_APPROVAL.md` from 27,265 bytes / `64ABD9A8D94B84731965F99324E1E481B14B6005B2E0FF32F2505CACAC7B3E62` to 30,117 bytes / `3123895D0E3122500EFAD65A9B93E551ADBBF6CC90F9EC2FA54B45B815CCACAB`. Wave 2 remains uncommitted and is intended as one commit after 2B. The older plan snapshot and Wave 1 status text are superseded by Wave 1 acceptance and commit `3c75b10d`.

One coordinator `pnpm run test` and one `pnpm run typecheck` remain for post-2B (4/4). Each validator and `git diff --check` has one owner-run final invocation remaining (2/2). No checks or runtime commands were run by Codex at launch.

## Wave 2B implementation checkpoint — 2026-11-13

The 2B source implementation is complete within the seven E paths and two owner-authorized pure-helper/test paths. The controller paginates V1 profile pages, performs create-then-GET-by-ID, preserves pending deletion through GET-by-ID reconciliation, and uses retained action identities for retries. ParentExpoApp wires the context-create/context-confirm flow without a photo or consent-policy gate and passes the selected profile explicitly to HomeScreen. Profile screens use V1 profile contracts and localized safe errors. The pure helper tests cover page merge/cursor handling, pending deletion, explicit selection, lesson-pin gating, and safe messages.

`evidence/IMPLEMENTATION_REPORT_WAVE2B_20261113.md` records per-file pins and the final source review (9,065 bytes / SHA-256 `841167C258CD9C7CFFD40BE48D4096E5EE1C7068F56B7B7F0F5F089FA37BAAA5`). The existing `TopicScreen.tsx` is outside the allowlist and remains unchanged; its current copy still describes a required photo and calls the next step a photo step, although ParentExpoApp now opens context directly. This is a known copy mismatch requiring separate authorization if changed.

No tests, typecheck, validators, `git diff --check`, install, Android/ADB/Gradle/emulator commands, or network commands were run by Codex. The final coordinator test/typecheck run and owner final validators/diff check remain pending. The owner-run scratch-service flow and usable lesson data remain NOT VERIFIED. The acceptance flow stops after context confirmation; `OWNER_MODAL_CALL_APPROVED=NO` remains. No code was staged, committed, or pushed.

## Wave 2B coordinator post-run and bounded rework — 2026-11-13

Coordinator post-2B invocation 4/5 passed 7 test files / 52 tests and printed `UI_COPY_AND_RECOVERY_VALID`, but typecheck found one TS2322: `ProfileScreen.tsx` passed a `busy` prop to the shared `SecondaryButton`, which supports only `label`, `onPress`, and `disabled`. The bounded fix expresses refresh state using `disabled` plus a changing Vietnamese label. The shared component prop declarations were re-read and all 2B screen usages checked; no other mismatch was found.

Addendum 8 authorizes one more coordinator `pnpm run test` and `pnpm run typecheck` for this 2B rework only (5/5 each); the final owner validators and `git diff --check` stay at one final invocation each. No rework checks were run by Codex. The post-2B result above predates the rework.

TopicScreen received the owner-authorized copy-only update: pre-edit 6,533 bytes / SHA-256 `A479B3D5F22E4E68133EB02CA419AE6D3BD7104E1E10BB342BCD7C37267CDC5F`; post-edit 6,509 bytes / SHA-256 `EA17130D3CB1FF397446820B22AEA8A9E32841DE81820009FF5BD90AD3D7F183`. Only text changed; the validator script was read but not run. The report is 11,767 bytes / SHA-256 `BD77ACEA43FF304480E58CB9843F941CBAFDC2CCF5B0DB7783218D65D895189D`.

Addendum 8 changed `TASK_APPROVAL.md` from its 30,117-byte / `3123895D0E3122500EFAD65A9B93E551ADBBF6CC90F9EC2FA54B45B815CCACAB` pre-append pin to 33,408 bytes / `DD0AE7A3E219EE4A6FF2DC362F07BDD3E45AADE8BE6EDA1FAE7CCD6A3A20E390`. Wave 2 remains uncommitted; nothing was staged, committed, or pushed.

## M2 no-Modal real-flow backlog proposals — 2026-11-13

**Status: PROPOSED BACKLOG ONLY.** Source evidence: `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_REAL_FLOW_NO_MODAL_TEST_LOG_20261113.md`. This append-only context note creates no implementation approval, launch, owner decision, or backend route contract. Current product requirements remain governed by the unsigned FEAT-063 v2.7-draft Rev60 SRS.

### Proposal 1 — State-aware resume of an active StoryRun

- **Placement:** Separate FEAT-081 follow-up task card for run-lifecycle recovery, kept outside the current P03–P06 draft scope unless the owner later revises that plan.
- **Scope:** Map the server-reported active `run_state` (and job stage when the API provides one) to a safe native screen on app launch and Home continuation. Preserve and reconcile the existing run identity. Define the `INPUT_PROCESSING` behavior while Modal work is disabled: do not imply that provider work will complete, invoke a provider, create a replacement run, or retry an uncertain mutation. Resolve with the BE lane whether this state has an active job and what progress/recovery operation is supported.
- **Acceptance criteria:** Known run states map to documented, localized screens or recovery states; unknown states have a safe fallback; relaunch and Home continuation restore the same run; `INPUT_PROCESSING` remains understandable and recoverable without a Modal call; the UI never creates a second run as a resume fallback.
- **Test plan:** Table-driven unit tests for every supported state plus unknown/null state; controller tests with fake active-run and job responses across relaunch; assert the original run ID is retained and no create/provider operation is issued; owner-run emulator walkthrough after separate approval.

### Proposal 2 — Reachable Home cancel/abandon action

- **Placement:** Separate FE/BE task card; the BE route contract is a blocking question for the BE lane. Do not fold it into P03–P06 without a new approved scope.
- **Scope:** Make cancellation of the active run reachable from Home and call only the method/path and request shape confirmed by BE. Do not infer the route from the unverified History-screen client call. The canonical SRS target says cancellation of an unfinished run enters `DELETE_PENDING`, releases the active-owner lock immediately, and starts the content purge lifecycle; response and reconciliation details still need the BE contract.
- **Acceptance criteria:** BE records the route, authorization, request/response schema, idempotency, and state-transition behavior; Home exposes an explicit adult-controlled action; pending/success/error UI follows server responses; repeated actions are safe; a failed request leaves the run visible and does not claim it was cancelled.
- **Test plan:** BE route/contract tests for authorization, idempotency, state and lock release; mobile fake-API tests for the exact approved route, duplicate press, success-to-pending reconciliation, and failure; owner-run integration walkthrough only after the route is verified and separately authorized.

### Proposal 3 — Fetch timeout and status-0 error handling

- **Placement:** Separate FEAT-081 mobile reliability task card, outside the current Wave 3 screen allowlist because it may touch authentication/API transport boundaries.
- **Scope:** Add a bounded timeout and normalize network-layer failures, including fetch status `0`, into readable localized app errors. Preserve meaningful HTTP status handling and avoid automatic retries for non-idempotent commands.
- **Acceptance criteria:** Network rejection, timeout, and status `0` no longer produce a raw red error box; HTTP errors remain distinguishable; messages omit raw response bodies, credentials, tokens, and implementation diagnostics; write actions are not silently retried.
- **Test plan:** Fake-fetch tests for network rejection/status `0`, timeout/abort, representative HTTP 4xx/5xx responses, safe message mapping, and proof that a write is not auto-retried.

## 2026-11-19 — Rev20 real Parent Android E2E checkpoint

- Evidence: `evidence/IMPLEMENTATION_REPORT_REV20_E2E_CHECKPOINT_20261119.md`; screenshot index and privacy note: `evidence/ANDROID_E2E_REV20_20261119/README.md`.
- The actual Expo app authenticated a synthetic Parent, created/selected a synthetic profile, exercised topic/object suggestions and custom-subject validation, rendered the catalog SVG guide through six steps, selected generated synthetic artwork, and created StoryRun `f9b29982-5472-4456-b2e8-2f44dc900382`.
- One live Modal drawing-understanding request failed after about 76 seconds. Worker logs show Qwen3.5-9B generated 512/512 tokens and terminated with invalid JSON (unterminated string at character 146); API returned generic 504 `MODAL_OUTCOME_UNKNOWN` because the terminal `RuntimeError` was misclassified.
- Corrected worker EOS/constrained-decoder alignment and added content-free truncation diagnostics; corrected backend terminal error classification/logging and Parent recovery copy. Offline tests passed, but no second live inference was sent, so the remote fix remains unverified.
- Activity/story/video were not produced; no fixture result or fake subject was inserted. M1–M3 have partial real-runtime evidence; M4–M5 are blocked at the VLM result; M6 video remains outside the verified path; M7 support screens are not fully verified. M8 evidence is partial, not acceptance-complete.
- Verification: backend focused suite 68 passed; Modal contract suite 29 passed; mobile suite 8 files / 94 passed. Mobile typecheck still fails with 594 diagnostics overall (247 in Parent paths). API health and route registration passed before task-local services were stopped.
- Task-local Compose project and drawing Modal app were stopped. The pre-existing video Modal app was untouched. Evidence was scanned and sensitive login/gallery captures were removed.
- No commit or push. Overall Plan Rev20 remains IN_PROGRESS; this checkpoint does not satisfy its E2E acceptance criteria.

## 2026-11-19 — Rev20B real Parent E2E result

- Evidence and sanitized diagnostics: `evidence/ANDROID_E2E_REV20B_20261119/README.md`; emulator captures are stored alongside it. The actual Android app used a synthetic Parent/profile and generated turtle artwork, not fixtures or the visual-preview harness.
- Profile, topic cards, object cards, custom-subject validation, catalog SVG guide (six steps), StoryRun create/read, and image selection worked. A task-local synthetic-pilot override was needed because the first profile create returned 409; the override was confined to the disposable task API container.
- One Qwen3.5-9B `drawing.analyze` Modal call returned terminal `MODAL_MODEL_OUTPUT_INVALID` in 30,197 ms. Output ended with EOS after 125 tokens, below the 512-token cap, while sanitized diagnostics showed incomplete JSON (`json_error_position=224`) and a decoder state that still allowed EOS. Backend surfaced HTTP 502 `DRAWING_OUTPUT_INVALID`; this was not a cold-start timeout.
- No valid drawing subject was available, so activity suggestion/persistence and story/revision were not called. No video/quota/payment call and no inference retry occurred.
- Old StoryRun `f9b29982-5472-4456-b2e8-2f44dc900382`: one authenticated GET using the local seed token returned 401; no cancellation was attempted and no database edit occurred. The UI client still has `cancelStoryRun` unavailable.
- Task-local Docker, Metro, Modal drawing, and Modal language/audio were stopped. The existing Modal video app remains deployed and untouched. No commit/push.
- Rev20B is **PARTIAL / BLOCKED**, not a completed E2E acceptance. Next work is decoder prefix/EOS contract diagnosis; any new live call needs a new bounded approval.

## 2026-11-19 — Post-parser one-shot rerun

- Real Parent Android flow reached one live Qwen3.5-9B drawing-understanding call after parser regression tests passed (33 passed, 2 warnings). Topic suggestions, `Động vật` subject suggestions, synthetic turtle image attachment, and StoryRun create/read succeeded.
- Modal call `fc-01M7SHBPCAKZDBDQ695P6NJ3EW` completed successfully in about 26 seconds after worker start; inference itself was 7.9 seconds. Parent API returned HTTP 502 `MODAL_OUTPUT_CONTRACT_INVALID` because the completed worker result omitted required numeric `confidence`. The Modal schema/parser only permits `candidate_subject` and `visible_features`, while SRS AT-14 requires candidate/confidence for adult review. This is a deterministic schema mismatch, not timeout/parser failure.
- No activity/story/video/quota/payment call was made; no retry. Screenshots and timing are in `evidence/ANDROID_E2E_REV20B_20261119/README.md` and its `screenshots/` folder.
- Compose and the exact task Metro process tree are stopped. No commit/push. Another live inference requires a new bounded approval.

## 2026-11-19 — Parent drawing confidence contract source fix

- Owner approved the narrow worker-contract fix with “fix cái đó đi”; Plan Revision 21 and TASK_APPROVAL Addendum 38 record the scope.
- `drawing_vlm_app.py` now requests confidence, requires it in the constrained drawing JSON, validates its numeric finite `[0,1]` range, and includes it in the returned result. The existing backend schema remains unchanged; SRS AT-14 requires confidence for adult review, and the backend already validates it.
- The score is an advisory, uncalibrated model estimate based only on the drawing. Adult confirmation remains mandatory. No threshold, auto-confirmation, child/profile input, or confidence fallback was added.
- Source review only. Tests, typecheck, Modal deploy/inference, Docker, database and migration were not run. Runtime status remains unverified; no commit/push. Evidence: `evidence/DRAWING_CONFIDENCE_CONTRACT_FIX_20261119.md`.

## 2026-11-19 — Rev22 drawing-confidence UI result

One approved, real Parent Android drawing-understanding request passed through the task API and Modal Qwen3.5-9B using generated synthetic turtle artwork. The backend returned HTTP 200; the UI showed `con rùa`, 95% advisory confidence, visible features, and adult confirmation. Worker result was `worker_succeeded` (30,301 ms); API/UI elapsed was 45.785 s. No retry or subsequent activity/story/video/quota call. Focused parser regression: 4 passed. The Modal app, task Docker stack, task Metro, and Parent app were stopped. Evidence: `evidence/ANDROID_DRAWING_CONFIDENCE_UI_REV22_20261119/README.md`. A short API log tail initially missed the terminal worker log; later retrieval by the same Modal Call ID confirmed success, so the remaining issue is log-tail timing. No commit/push.

## 2026-11-19 — Rev23 Parent E2E scope

Plan Revision 23 / TASK_APPROVAL Addendum 41 is approved from the owner's direct request to continue the real Parent Android flow through activity selection and video while ignoring quota. Continue from the existing synthetic turtle run at adult subject review; do not repeat drawing understanding or use a fixture. Preserve adult subject, activity-selection, script-confirmation and automated safety gates. The product target remains LTX-2.5 on Modal; no Wan or legacy session route substitution. Any no-quota admission is local-only, synthetic-only, server guarded and default off. First compare current served OpenAPI/runtime to the FEAT-063 Rev67 SRS; the previous source-only finding is that Parent video UI/API are unavailable and Modal video is an unconfigured scaffold. No Rev23 inference has been sent yet.

## 2026-11-20 — Rev41 Parent UI refresh and video flow

Plan Revision 41 / TASK_APPROVAL Addendum 67 is approved by the owner's direct request to refresh Parent screens still using the old visual tone and add the real Parent video path. Current product authority is the FEAT-063 v2.7-draft working SRS; the approved implementation keeps the server-owned adult story confirmation, real quota/compute admission, LTX-2.5 on Modal, silent output, fail-closed technical/consistency/safety checks, and private playback. No quota bypass or self-confirmation is authorized. M1 source changes and offline checks are complete. The authenticated app returned to sign-in after reload, so post-reload visual verification of the changed workflow screens remains incomplete. At the initial FEAT-081 check, its live API had no Parent video routes, so Parent video was not end to end in that worktree. The initial statement that the system-wide Modal LTX worker remained fail-closed was incorrect; a follow-up audit confirmed a deployed Modal worker and real candidates in FEAT-067. Parent product admission/dispatch/safety/playback remains incomplete. No new AI/video request, migration, quota change, deploy, commit or push was made. Details: `evidence/PARENT_UI_VIDEO_REV41_20261120/REV41_M1_IMPLEMENTATION_AND_VIDEO_BLOCKERS.md`.

## 2026-11-20 — Rev41 correction: existing Modal LTX worker

The owner pointed out that the video worker had already been implemented on Modal. Rechecking the `dev` Modal app confirmed `sketch2life-srs23-dev-video` deployed with `generate-silent-story-video` and `generate-video-scene` L40S functions. The separate FEAT-067 worktree has the corresponding LTX-2.5 source and recorded real candidate outputs: attempt 12 passed technical media validation; attempt 14 generated a technically valid candidate but failed visual review. The app currently has zero live tasks.

The boundary is integration: FEAT-067 has Parent request/status routes, but the service currently fails closed with `VIDEO_ADMISSION_DEPENDENCIES_UNAVAILABLE` and does not dispatch to Modal. The successful Modal candidate was requested directly after a synthetic Parent story was confirmed, bypassing product quota/admission; safety, private asset promotion and playback were not run. FEAT-081's mobile client has no video-generation request/status operations, and its current local `video_app.py` is only a scaffold. Therefore, reuse the existing Modal worker; continue the remaining Parent product integration and quality/safety gates. No GPU request or deploy was made during this audit.

## 2026-11-20 — Rev42 Parent Modal candidate connection

Plan Revision 42/Addendum 69 authorizes a local/test, synthetic-only technical candidate path that reuses the existing `sketch2life-srs23-dev-video` / `generate-silent-story-video` deployment. FEAT-081 now has authenticated Parent request/current/detail/preview routes, an idempotent durable candidate service and Modal adapter, an additive migration, and Expo request/progress/resume/technical-preview wiring. The path is default-off, quota-free only under explicit local/test synthetic gates, and never returns product `VIDEO_READY`; candidate metadata keeps safety `NOT_RUN` and product playback false.

Offline verification: backend focused tests **19 passed**; mobile typecheck passed; mobile suite **126 passed across 15 files**; Ruff and `git diff --check` passed. Migration `20261120_parent_video_candidate` is present as an Alembic head but was not applied. No Modal inference, deployment, emulator E2E, database mutation, `.env`/secret access, commit, or push occurred. Consequently, the UI→API→Modal→preview flow is connected in source but not yet proven at runtime. A real request still requires an eligible confirmed synthetic story. The current visual manifest also lacks general story-prop mapping, so visual fidelity is not guaranteed. Full evidence: `evidence/PARENT_MODAL_VIDEO_CANDIDATE_REV42_20261120/IMPLEMENTATION_REPORT.md`.

## 2026-11-20 — Rev43 Parent E2E runtime checkpoint

The real Android emulator (`emulator-5554`) was at Parent sign-in. Only the task API in Compose project `s2l-feat081-rev23` was rebuilt from this worktree; `/health` returned 200 and OpenAPI exposed all four candidate routes. The additive `20261120_parent_video_candidate` migration was applied to that task-local Postgres and the candidate table is present. Unauthenticated request correctly returned 401.

The run stopped before account creation or AI: the task API reports `auth_provider=development`, no Firebase project/Admin credential, and no Modal token ID/secret. The host Modal CLI still lists the existing LTX app as deployed, but the API container cannot authenticate to dispatch it. No Firebase account was created, no AI/Modal request was sent, and no quota was accessed. Evidence and exact root `.env` keys needed to resume: `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/RUN_REPORT.md`. The task services and Modal app remain running; no commit/push.

## Rev43 live E2E update — 2026-11-20

The earlier Rev43 auth/config checkpoint was superseded after the owner clarified that the single project-root .env was already present. Compose was restarted with that root file via the explicitly approved path; credential presence was reported only as booleans.

The real Expo app registered and logged in one synthetic Parent account, created a synthetic 60-month profile, loaded catalog topic/subject choices, and selected Đại dương → Rùa biển. The optional curated SVG guide lookup returned 404 because no source guide was found for that subject; the guide was disabled. A fresh synthetic turtle drawing was attached through the Android photo picker. Modal Qwen3.5-9B recognized “con rùa” at 90% in 42.34 seconds; the adult confirmed the subject and context.

Activity suggestions followed catalog-first behavior. The catalog had zero accessible/age-eligible candidates, so the UI invoked the Qwen fallback once. Modal raised NotFoundError before a call ID was created; API returned 504. The current dev Modal inventory has the drawing and video apps but lacks sketch2life-srs23-language-audio-dev, which serves this workload. No retry was made, and story/video were not called. No quota was read or changed. Evidence and exact IDs are in evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/RUN_REPORT.md.

## 2026-11-20 — Rev45 live continuation

Addenda 72–74 authorized deployment of the missing `sketch2life-srs23-language-audio-dev` app and resumption of the same synthetic Parent run. Deployment succeeded after a single terminal UTF-8 correction. Through the real emulator UI, the one allowed activity request succeeded, “Phân loại thẻ rùa” was persisted, one Qwen3.5 story request succeeded, and the adult confirmed the five-scene story. Read-only DB verification shows run `16002cde-42b1-4198-a7d0-a04de85fea9b` in `SCRIPT_REVIEW`, job `SUCCEEDED`, revision 1 `CONFIRMED`, with no video candidate yet. The story content is aligned with the selected activity.

The active Metro bundle includes the real video candidate screen and API route. During UI diagnostics, the Expo process was restarted to ensure it loaded the bundle from this worktree; it returned to sign-in. Manual sign-in is pending before resuming that same server-side run and making the single authorized silent LTX candidate request. No quota access/mutation, video attempt, retry, source fix, secret edit, commit, or push has occurred. See `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/RUN_REPORT.md` and `logs/run-events.md` for timings/correlation.

## 2026-11-20 — Rev46 real Parent E2E checkpoint

The real Android Parent UI reused the synthetic account, created/read back one 60-month synthetic profile, selected `Đại dương → Rùa biển`, and created StoryRun `ff1021f5-e9e6-4343-9da3-ced08ad9de69`. Drawing understanding passed through Modal Qwen3.5-9B (90% “con rùa”, 40.498 s); catalog-first activity lookup found no eligible catalog entries, so the single approved AI fallback produced three suggestions (134.546 s), and the UI persisted “Vận động mô phỏng rùa”. Story generation returned HTTP 200 through Qwen3.5-9B (134.394 s), but adult review found mixed Japanese/Chinese text (`các動作`) and unnatural age phrasing. Story was not confirmed; no video request was sent under the approval’s confirmation gate. No quota/payment access, retry, second account, fixture, commit, or push. Evidence: `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/RUN_REPORT.md`, `logs/run-events.md`, and `screenshots/rev46-story-review-mixed-language.png`.

## 2026-11-20 — Rev49 video loading UI and blocked candidate dispatch

Implemented the Parent video loading experience using the candidate API's actual states: four progress phases without fake percentages, separate initial status lookup and request dispatch copy, polling interval guidance, and explicit no-resubmit/reconciliation messaging. Failed or uncertain outcomes do not display a normal progress track.

Mobile typecheck passed; 133 tests across 16 files passed, including the new state-mapping tests; UI copy validation and `git diff --check` passed. The task API remained healthy (`/health` 200) and its local synthetic video-candidate flag remained `false`.

The real Android app was at sign-in. The two pre-existing synthetic credential sets from the earlier E2E session were rejected by Firebase with the app's generic invalid-credential response. No account was created; no more login attempts were made. The exact approved StoryRun could not be opened or confirmed, so no Parent video API or Modal LTX call was dispatched. No quota, environment, secret, or Modal app state was changed. Full sanitized checkpoint: `evidence/PARENT_VIDEO_LOADING_REV49_20261120/RUN_REPORT.md`.

## 2026-11-21 — Parent activity backend quality-gate defect

The real Android flow passed drawing recognition and subject/context confirmation, then called the catalog-first activity endpoint. No accessible published/shared lesson activities matched; the one authorized Modal fallback returned three Vietnamese drafts with incomplete sentence tails. The backend persisted and returned these drafts, so the defect is in the worker parser and backend quality gate as well as the visible UI payload. The flow stopped before selection/story/video and did not access quota. Backend and Modal source now reject the observed incomplete Vietnamese tails, and offline regressions pass. This source fix is not deployed or live-verified: Addendum 88 permits offline verification only and forbids another Modal activity inference. Full run, IDs, timings, test results, and evidence are in `evidence/PARENT_BACKEND_FRONTEND_FIX_E2E_20261121/RUN_REPORT.md`.

## 2026-11-21 — Rev55 lifecycle outbox blocker

After the approved migration, the existing synthetic Parent run was canceled through the real UI (HTTP 202). Read-only verification shows DELETE_PENDING, revision 9, and its active-owner lock released. Its sole cancellation outbox event remains pending because task Compose has no lifecycle worker. The worker's normal effect would purge this run's story content/assets; Addendum 91 requires those data to be preserved. No worker was started, no purge or new run occurred. Detailed evidence and passing test results: vidence/PARENT_LOADING_E2E_REV53_20261121/RUN_REPORT.md and screenshot 59-current-after-cancel.png. Await owner decision before lifecycle processing.

## 2026-11-21 — Rev55 lifecycle resolution and real Parent E2E checkpoint

Addendum 102 approved processing only the cancellation event for StoryRun `08657e31-ebd7-4a07-8f9b-5929b4dff23b`. The one-shot lifecycle consumer processed its single pending event; the run reached `DELETED`, its event was delivered, and the lifecycle receipt completed. No account, profile, seed data, or unrelated event was changed.

A new real Android run (`b05c2b46-e760-4643-824b-b30b5387453f`) passed topic selection, optional six-step SVG guide, synthetic image attachment, Qwen3.5 drawing understanding, adult subject/context confirmation, catalog-first activity lookup, one AI fallback (catalog had zero eligible rows), and persisted activity selection. Its one story inference failed the existing prose quality gate: JSON was complete, but `story.opening`, `middle`, scene actions, and narrations ended incomplete. Modal call `fc-01M7Y9SCQQP9RCJXARXQBDX25G` used 77.185 seconds inference / 102.295 seconds total worker time; API returned HTTP 502 `STORY_OUTPUT_INVALID`, not a timeout. No retry, video, quota/payment request, or gate bypass occurred. See `evidence/PARENT_LOADING_E2E_REV53_20261121/RUN_REPORT.md` and screenshots `82-story-inference-started.png` / `83-story-failure.png`.

The purple loading card and elapsed timer were visible; stage-by-stage progress is absent, and the terminal screen exposes a “Gửi lại cùng yêu cầu” button. It was not pressed under the one-story-inference cap. The task-used Modal language/audio and drawing apps were stopped at 12:47 +07 with zero tasks; the unrelated video app remains deployed and untouched. This is a partial E2E, not completion. Any further inference needs a new bounded approval after a worker fix and focused verification. No commit/push.

## Rev56 read-only eligibility result (2026-11-21)

- The exact Rev55 synthetic run is `FAILED` / `STORY_OUTPUT_INVALID`, revision 1 is `FAILED`, and one activity selection remains persisted.
- The backend does not accept a new story revision from `FAILED`; it permits reservation only from `PREPARATION_REVIEW` or `SCRIPT_REVIEW`. The canonical SRS also treats `FAILED` as terminal while BR-13 allows rewrites without specifying this failure case.
- The Parent Home/history UI does not expose a route back to the failed run. Screenshots 85–86 are in `evidence/PARENT_LOADING_E2E_REV53_20261121/screenshots/`.
- No rewrite request, Modal deploy, video, quota/payment call, or run mutation was made. API health is 200; task language/audio and drawing apps remain stopped.
- Plan Rev57 / Addendum 104 awaits an explicit decision on the narrow state-transition exception. Do not implement or infer until approved.

## 2026-11-21 — Rev57 approved rewrite outcome

- Plan Rev57/Addendum 104 were approved and implemented. Backend focused checks (21), mobile typecheck, 142 mobile tests, UI-copy validation, focused Ruff, and `git diff --check` passed.
- One same-run rewrite was submitted from the real Android UI after exact read-only eligibility checks. API returned 504 with `STORY_OUTCOME_UNKNOWN`, `modal_call_id=None`; Modal showed no worker logs and zero tasks. Do not retry this request.
- Run is now `SCRIPT_GENERATION_UNKNOWN`, job/revision 2 `AWAITING_RECONCILIATION`, retryable false, with the active-owner lock held. No confirmed story exists; no video or quota request was sent.
- The task-used Modal language/audio app v15 was stopped at 16:18:23 +07 after confirming zero tasks. Drawing remains deployed and video was untouched.
- Security validator still reports pre-existing findings in older FEAT-081 records; no commit/push. Full details: `evidence/PARENT_LOADING_E2E_REV53_20261121/RUN_REPORT.md`.

## 2026-11-21 — Rev58 Parent-to-video continuation

The owner authorized continued fixes and diagnosis-guided testing until a video runs. Plan Rev58/Addendum 106 is the approved plan pin. Read-only M0 verification found the old unknown story request still has no provider call ID, no Modal worker logs were returned, and its active-owner lock remains held; no request replay or run mutation occurred. The task video-candidate flag is disabled, FEAT-081’s Modal video worker is a scaffold, no video app is deployed, and the pinned LTX checkpoint is missing from the configured Volume path. A separate FEAT-067 worktree contains the pinned LTX-2.5 worker and historical synthetic candidate evidence. The goal is a real synthetic Parent Android UI path to a private authenticated silent MP4 candidate, not a production-ready video claim. Evidence: `evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/M0_DIAGNOSTICS.md`. No new inference has been sent.

## 2026-11-21 — Rev58 Firebase setup fixed; candidate owner mismatch

The owner then directed continuation with the current login. Its open `SyntheticTurtleRev22` run was opened through the real UI and remains `SCRIPT_GENERATION_UNKNOWN` / `AWAITING_RECONCILIATION`, non-retryable, without a provider job ID, and holds the Parent account's active-run lock. The UI prohibits resending and remained pending on status-only polling. No new request or state change was made. Evidence: `M5_ACCOUNT_SCOPE_CHECK.md` (`61`–`63`).

The emulator was rechecked after the owner said the account was already logged in: Home showed `SyntheticRev58Turtle`, and the real `Câu chuyện` tab showed “Chưa có buổi nào”. The redacted `.env` comparison remains mismatched, so the current session cannot access the saved video candidate. Evidence: `evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/M5_ACCOUNT_SCOPE_CHECK.md` (`59_current_ui.png`, `60_story_tab.png`).

After the owner selected the existing-account path, a redacted comparison confirmed the Parent email currently configured in root `.env` still resolves to a different Firebase Auth user than the owner of the saved video candidate. Both credential fields are present; no sign-in attempt or credential disclosure occurred.

The task API was recreated with the root `.env` explicitly loaded. Firebase Admin and Modal dev configuration now initialize; API health is 200; Android sign-in with the existing seed Parent succeeds. A read-only owner check found the saved silent-video candidate belongs to a different Firebase principal/profile than this seed account. The target profile's UI history is empty, so recovery was not called. A follow-up Firebase Admin read confirmed the target owner still has an enabled email/password Auth account; no account identifier or credential was recorded. A separate pending `SyntheticTurtleRev22` run was left unchanged. No new account/run, inference, quota call, or database write occurred. Evidence: `evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/M5_ACCOUNT_SCOPE_CHECK.md`. Resume after the existing owner account is made available in the root seed configuration, or with a separately approved new run/video inference.

## 2026-11-22 — Parent AI parser audit checkpoint

Rev117 activity/topic parser and catalog-context repairs are implemented and deployed to the task API/language Modal app. Offline suites passed (184 Modal, 278 backend); API health is ok; CPU readiness is ready for GPU-worker validation, with no active Modal tasks. The repaired activity output has not had a second live inference. Silent-video input-manifest duplicate-key hardening remains outside the approved file allowlist. See evidence/PARENT_AI_PARSER_AUDIT_REV117_20261122/PARSER_AUDIT_REPORT.md.

## 2026-11-22 — Local synthetic video route enabled

The owner asked to enable the video capability in the running system. The two local-only gates were added to the root CAPSTONE .env and only the API container was recreated. Runtime values and API health passed; Modal LTX-2.5 checkpoint is staged, with no GPU model loaded. No inference was sent. This is only a synthetic technical-preview route. Evidence: evidence/PARENT_VIDEO_LOCAL_ENABLE_REV117_20261122/CONFIGURATION_CHECK.md.

## 2026-11-22 — Rev59 video status response repair

An existing synthetic video candidate was already `CANDIDATE_READY`, but Parent status polling returned HTTP 500 because internal integrity fields (`output_sha256`, `output_size_bytes`, `output_manifest_sha256`) were passed to the strict public metadata schema. The mapper now projects the public contract fields before validation. Fourteen focused tests passed; only the API service was rebuilt; `/health` is `ok`; Android now shows the ready state and opens the existing private preview. No new inference or database mutation occurred. The candidate remains a technical preview with safety/consistency `NOT_RUN` and `product_playable=false`. See `evidence/PARENT_VIDEO_CANDIDATE_RESPONSE_FIX_REV59_20261122/RUN_REPORT.md`.

## 2026-11-22 — Rev60 Parent video player and copy

The video preview screen now has explicit Play/Pause/Replay controls, playback status and elapsed time, a visible safe error/reload path, and shorter user-facing copy. Mobile typecheck passed. The existing preview endpoint returned 200 and rendered a frame before the change, while native Play remained at `00:00`. Post-change playback is not yet verified: bundle reload cleared the in-memory Parent session; reauthentication resumed at activity selection, and history does not expose an action to reopen the stored candidate. No AI activity inference or video request was sent. See `evidence/PARENT_VIDEO_PLAYER_UI_REV60_20261122/RUN_REPORT.md`.

## Rev61 — bounded AI and video-player verification

The existing synthetic run already had an AI-generated activity set, selected activity, confirmed five-scene story, and a ready 30.209-second video candidate. On Android, one retry of activity suggestions returned HTTP 409 because the persisted run is already `SCRIPT_REVIEW`; no Modal inference was dispatched. After fresh login, the resume card returned to Activity instead of adopting the saved story/video. Source inspection indicates `adoptServerUnderstanding` treats the fresh client revision `0` as a server revision change and skips saved-story adoption; video candidate hydration on resume also needs verification. The updated Play/Pause controls remain unverified. All existing Modal `dev` apps were idle with zero tasks and were left untouched. No product code, DB state, quota, or safety gate was changed. Details: `evidence/PARENT_AI_VIDEO_PLAYBACK_REV61_20261122/RUN_REPORT.md`.

## 2026-11-22 — Rev62 cold-resume and candidate hydration completed

The owner approved Rev62 (“chạy fix đi”). A fresh Android controller now adopts the persisted confirmed story instead of treating its initial local revision as a stale server update. Opening video loads the current candidate first and shares the in-flight request with the screen's mount refresh. Mobile typecheck passed. On Android, cold login resumed the confirmed story, current-candidate and authenticated preview GETs returned HTTP 200, and Play/Pause/Resume worked against the existing synthetic candidate. API logs contained no generation POST; all three existing Modal dev apps remained deployed with zero tasks. The candidate is still only a technical preview, with safety/consistency not run and `product_playable=false`. The Story screen still shows an activity-selection warning because that prior selection is absent from the current run response; this remains a separate contract/UI follow-up. Full sanitized evidence: `evidence/PARENT_AI_VIDEO_PLAYBACK_REV62_20261122/RUN_REPORT.md`.
