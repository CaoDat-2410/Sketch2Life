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
