## 2026-11-23 — Parent E2E publication authorization

- Owner directly authorized commit and push of the completed Parent workflow work on feature/fe-mobile-remediation.
- Implementation and synthetic E2E evidence are included in the publication commit.
- The synthetic Android → backend → Modal E2E and its limits are recorded in FEAT-082.
- Publication does not imply video safety clearance or production acceptance; temporary pytest/model fixtures and deployment-local test output are excluded.

# FEAT-081 status

- Status: Wave 1 ACCEPTED / COMMITTED (3c75b10d, not pushed); Wave 2A PASSED coordinator post-run; Wave 2B bounded rework complete / AWAITING COORDINATOR REWORK POST-RUN; Wave 2 uncommitted
- Wave 1 plan revision: 2
- Wave 1 Plan Revision 2 SHA-256: DA807873F2AFEA2BC9A86457AE9BB13A3C4CE90F5E9388B816A5676EEACE3ECC
- Approved Wave 2 plan: Revision 3, 34,224 bytes, SHA-256 73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E

## Wave 2B implementation checkpoint — 2026-11-13

- Status: Wave 2B implementation complete and awaiting coordinator post-run; not accepted. Wave 1 remains accepted/committed as `3c75b10d`; Wave 2A passed coordinator post-run with 6 test files / 45 tests and no typecheck diagnostics. Wave 2 remains uncommitted and one commit is planned after 2B.
- The seven 2B E paths were updated. The two owner-authorized N paths `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts` and `apps/ui-mobile/tests/parentFlowV1.test.ts` provide pure, offline-testable flow decisions. The separately authorized report is `evidence/IMPLEMENTATION_REPORT_WAVE2B_20261113.md`.
- The report records final 2B source hashes, all nine rechecked H pins, acceptance criteria, limits, and NOT RUN / NOT VERIFIED items. The old TopicScreen copy about photo being required remains unchanged because TopicScreen is outside the 2B allowlist.
- 2B implementation report: 9,065 bytes / SHA-256 `841167C258CD9C7CFFD40BE48D4096E5EE1C7068F56B7B7F0F5F089FA37BAAA5`.
- Bootstrap paginates V1 profiles; profile creation is followed by GET-by-ID; deletion remains visibly pending and reconciles by GET-by-ID; Home receives the selected profile by explicit prop; the no-photo/no-policy context path displays and confirms server context. The owner-run acceptance must stop immediately after successful context confirmation while `OWNER_MODAL_CALL_APPROVED=NO`.
- Coordinator post-2B `pnpm run test` is the final invocation 4/4; one `pnpm run typecheck` remains (4/4). One owner-run final invocation remains for each validator and `git diff --check` (2/2). None was run by Codex.
- No code was staged, committed, or pushed. Wave 2 remains uncommitted; no 2B acceptance record exists.

## Wave 2B post-run rework checkpoint — 2026-11-13

- Coordinator invocation 4/5: `pnpm run test` passed 7 files / 52 tests and printed `UI_COPY_AND_RECOVERY_VALID`; `pnpm run typecheck` found TS2322 because `ProfileScreen.tsx` passed unsupported `busy` to `SecondaryButton`. The coordinator log hashes and diagnosis are in the command ledger and 2B report.
- Rework: ProfileScreen now uses `disabled` and a changing localized label for pending GET-by-ID refresh. The `components/ui.tsx` prop types were read and all shared-component usages in the 2B files were reviewed; no other mismatch was found. The H file remains unchanged.
- Owner authorized text-only TopicScreen updates. Before pin: 6,533 bytes / `A479B3D5F22E4E68133EB02CA419AE6D3BD7104E1E10BB342BCD7C37267CDC5F`; after pin: 6,509 bytes / `EA17130D3CB1FF397446820B22AEA8A9E32841DE81820009FF5BD90AD3D7F183`. No logic, prop, or layout changed. The UI-copy validator was read but not run.
- Addendum 8 pre-append approval pin: 30,117 bytes / `3123895D0E3122500EFAD65A9B93E551ADBBF6CC90F9EC2FA54B45B815CCACAB`; post-append pin: 33,408 bytes / `DD0AE7A3E219EE4A6FF2DC362F07BDD3E45AADE8BE6EDA1FAE7CCD6A3A20E390`.
- The owner-authorized test/typecheck rework invocation is 5/5 for each. The post-2B test result is pre-rework; no post-rework checks have run. Each validator and `git diff --check` still has one owner-run final invocation remaining (2/2).
- Updated 2B report: `evidence/IMPLEMENTATION_REPORT_WAVE2B_20261113.md`, 11,767 bytes / SHA-256 `BD77ACEA43FF304480E58CB9843F941CBAFDC2CCF5B0DB7783218D65D895189D`.
- No tests, typecheck, validators, `git diff --check`, install, Android, or network commands were run by Codex; no stage, commit, or push occurred.
- Architecture decision: ADR-0023-feat081-mobile-ui-target.md, SHA-256 8EABECC21A95B21FB6C15198749BCFBF5EE3FF1C64834FBD8FBDF0E3A2C436C6
- Wave 1 decision log after D-009: SHA-256 3952CB3BCA12ABD21109B3F209A181CF3B91F3D1D01FAEEB5DA64ABFD64A3805
- Wave 1 approval: Addendum 3 appended to approvals/TASK_APPROVAL.md; pre-append pin 7,823 bytes / 76AD28534A90FD0C9A6B6572B9A2588B0717ED78A2E679DCE22CA3D1E8B7BC79; post-append pin 11,058 bytes / CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266
- Decision log after D-010: 6,312 bytes, SHA-256 B1D747786B88AC0F0F4DCCE4221099687764752E45B2D90D6080C9E79FD165FC
- Wave 2 Addendum 4 approval: `APPROVED / NOT LAUNCHED`; pre-append pin 11,058 bytes / CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266; final post-append pin 23,557 bytes / D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE
- Wave 2A Addendum 5 launch: pre-append pin 23,557 bytes / D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE; post-append pin 25,349 bytes / 9EAE14F557D8F650970294BF6E02AA658C9B5A4A316BAD2406F1803D3F17778B
- Implementation report: evidence/IMPLEMENTATION_REPORT_WAVE1_20261112.md, 8804 bytes, SHA-256 01A6760B4800F810F03D3C6C6CCDE4BE78472821B88FA74BF6E3A0F404738796
- Updated: 2026-11-13, Asia/Saigon

The following implementation note is a historical pre-acceptance snapshot; the Wave 1 owner acceptance checkpoint below is current.

The owner approved the final FEAT-081 target, source boundary, and two-run AC2 policy and explicitly launched Wave 1. The four allowlisted code paths are implemented. The coordinator's baseline test and typecheck passed; coordinator post-runs, owner Android review, and owner acceptance remain pending. No acceptance record has been written. See `evidence/IMPLEMENTATION_REPORT_WAVE1_20261112.md`.

The sample P01 shows an active-child selector; HomeScreen has no selected-child input and does not receive the controller's profile. Adding it needs ParentExpoApp.tsx, which is outside the Wave 1 allowlist. Owner chose Option A on 2026-11-12: label deferred. The item moves to a later wave that is separately approved to touch ParentExpoApp.tsx (together with useParentController.ts / workflowTypes.ts if that wave needs them). The active-child label is not applicable to Wave 1 and is not marked passed.

## Wave 1 owner acceptance checkpoint - 2026-11-12

- Status: ACCEPTED (Wave 1 only); not committed.
- Accepted scope: P01 Home and P02 Lesson gallery in `apps/ui-mobile`, based on the four final code hashes in Addendum 3. The H-pin files are unchanged.
- Coordinator post-runs: `pnpm run test` reported 4 files / 29 tests passed and `UI_COPY_AND_RECOVERY_VALID`; typecheck had no diagnostics.
- Owner-run confirmation on 2026-11-12 23:56 after the filtered reinstall: same test and UI-copy results; typecheck had no diagnostics; both exited 0.
- Owner-run final-byte validators all exited 0: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (7,239 files); `ARCHITECTURE_VALID`; `git diff --check` clean.
- Owner report: the app ran on the Pixel_6a emulator via `android:dev` and started and ran.
- Active-child label: deferred per Option A; not accepted as Wave 1 work. Wave 2 plan R2 remains a draft, not approved and not launched. `OWNER_MODAL_CALL_APPROVED=NO`.
- This acceptance does not cover backend/API wiring, Android behavior beyond "ran", later waves, a move to `apps/mobile`, or any SRS change. It authorizes no stage, commit, or push; the commit needs a separate owner instruction.
- `TASK_APPROVAL.md` post-append pin: 11,058 bytes / SHA-256 `CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266`.

## Wave 2 plan approval checkpoint - 2026-11-13

- Wave 1 is committed as `3c75b10d` on `feature/fe-mobile-remediation`; it is not pushed.
- Wave 2 is APPROVED / NOT LAUNCHED under Addendum 4. `PLAN_REVISION_3.md` is an exact copy of the 34,224-byte R2 draft with SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`; Addendum 4 supersedes its DRAFT header.
- D-010 records the six owner product decisions, separate 2A/2B launch gates, S1a-P2 working-basis disposition, and baseline results. The previous DECISIONS prefix was 3,950 bytes / SHA-256 `3952CB3BCA12ABD21109B3F209A181CF3B91F3D1D01FAEEB5DA64ABFD64A3805`; after D-010 it is 6,312 bytes / SHA-256 `B1D747786B88AC0F0F4DCCE4221099687764752E45B2D90D6080C9E79FD165FC`.
- Owner baselines are the 2026-11-12 23:56 and 2026-11-13 00:15 runs on bytes identical to `3c75b10d`: 4 test files / 29 tests passed, `UI_COPY_AND_RECOVERY_VALID`, no typecheck diagnostics, and all three validators plus `git diff --check` exited 0. Baseline invocation accounting is consumed under the R2 ceilings.
- 2A and 2B each require a separate explicit launch instruction; 2B additionally waits for 2A to pass. Wave 2 remains not launched.
- Addendum 4 pre-append `TASK_APPROVAL.md` pin: 11,058 bytes / SHA-256 `CFD32E6B3B3053F150AA6A73028051760A5B7AEEDBD6420DB7895BC3CCF4B266`. Its final post-append pin, including the append-only ProfileSharingScreen hash correction, is 23,557 bytes / SHA-256 `D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE`.

## Wave 2A launch checkpoint - 2026-11-13

- Status: Wave 2A LAUNCHED; Wave 2B NOT LAUNCHED and requires its own explicit owner instruction after 2A passes.
- Scope is limited to the seven 2A E paths and two 2A N tests in Addendum 4. The only extra record path is the owner-authorized N path `evidence/IMPLEMENTATION_REPORT_WAVE2A_20261113.md`; no other path was added to scope.
- Addendum 5 pre-append `TASK_APPROVAL.md` pin: 23,557 bytes / SHA-256 `D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE`; post-append pin: 25,349 bytes / SHA-256 `9EAE14F557D8F650970294BF6E02AA658C9B5A4A316BAD2406F1803D3F17778B`.
- Authorization for the Wave 2A implementation report path is recorded verbatim in Addendum 5 and the command ledger. The 2B report path is not authorized by this entry.

## Wave 2A cold-review steering - 2026-11-13

- Review report: `tmp/fe081-wave2/REVIEW_R2_ROUND1_20261113.md`; verdict `NEEDS REVISION`. The owner accepts the findings and directs their application within the existing 2A allowlist.
- 2A keeps all legacy APIs and types source-compatible, adds separately named V1 methods/types, and preserves the three authorization fixture fields and legacy StoryRun types.
- Add the pre-drawing run-create/context-confirm use case without photo or consent/policy/profile-revision/context-confirmed request fields. Retain action keys across same-action retries; use new keys for new actions. Reconcile DELETE_PENDING through GET-by-ID; list remains ACTIVE-only.
- Patch tests cover omitted and null `interests_summary`; fake-fetch tests cover retry identity and delete replay/state transition. Errors retain safe metadata and map to safe messages without exposing raw bodies.
- The merged `app.py` error shape and usable lesson data on scratch remain NOT VERIFIED. The 2B offline UI path, photo/policy gate and snapshot wording findings are reserved for the separate 2B launch addendum.
- Addendum 5 launch pin: 23,557 bytes / SHA-256 `D6BFFDDC0009A3C02347C65EC74D732D257253EDFFC5F5EBABE068F358D931CE`; immediate post-launch pin: 25,349 bytes / SHA-256 `9EAE14F557D8F650970294BF6E02AA658C9B5A4A316BAD2406F1803D3F17778B`; post-review-note pin: 25,709 bytes / SHA-256 `773B46FFFB1D30BFE6626A2363EE2EEB2DE9072EBCF16ECA54B3E39A8E4BE0D9`.

## Wave 2A implementation checkpoint - 2026-11-13

- Status: implementation complete; awaiting coordinator post-run. Wave 2A is not yet accepted. Wave 2B remains NOT LAUNCHED and needs its own explicit instruction.
- Evidence: `evidence/IMPLEMENTATION_REPORT_WAVE2A_20261113.md`, 9,315 bytes / SHA-256 `5288C3E0679237ED75F767ADB32BBF10F6AE75D17A2492D9431AAA92B41AAB7C`.
- The seven approved 2A E code paths and two N fake-based tests are implemented. Existing UI/controller call contracts and legacy types remain source-compatible; all nine R2 H pins were re-hashed and match.
- Owner-run baseline remains 4 test files / 29 tests passed with `UI_COPY_AND_RECOVERY_VALID`, and typecheck had no diagnostics. Post-2A tests and typecheck are NOT RUN and remain coordinator-run acceptance steps.
- Merged `app.py` error shape and usable lesson data on the scratch service are NOT VERIFIED. No code was staged, committed, or pushed.

## Wave 2A post-run rework checkpoint — 2026-11-13

- State: Wave 2A remains LAUNCHED but is not accepted. The coordinator post-run found one test failure/unhandled rejection and one typecheck error. The bounded fixes are applied within the existing 2A E/N allowlist; a coordinator re-run is pending. Wave 2B remains NOT LAUNCHED.
- The failed coordinator run is consumed as test invocation 2/4 and typecheck invocation 2/4. The owner-authorized rework coordinator run is invocation 3/4; the single post-2B run remains invocation 4/4 for each command.
- Diagnosis: the lesson-pin guard throws from an async use case, so the assertion must await a rejected Promise; the synchronous assertion caused the test failure and unhandled rejection. The active-run GET can return null, so it now uses a separate nullable envelope while create/read remain non-null.
- The test now awaits the lesson-pin rejection and verifies no create call for absent/incomplete pins. Null active-run response and null conflict-recovery behavior are also covered. Tests were not run by Codex.
- Addendum 6 pre-append approval pin: 25,709 bytes / SHA-256 `773B46FFFB1D30BFE6626A2363EE2EEB2DE9072EBCF16ECA54B3E39A8E4BE0D9`; post-append pin: 27,265 bytes / SHA-256 `64ABD9A8D94B84731965F99324E1E481B14B6005B2E0FF32F2505CACAC7B3E62`.
- Updated implementation report: `evidence/IMPLEMENTATION_REPORT_WAVE2A_20261113.md`, 13,980 bytes / SHA-256 `8DD31E5AC2881F5249D6B687E061571F50D45F2B81EDF39DB3BF32A2E0A1217E`. The command ledger records the failure review, steering, ceiling wording, and command accounting.
- No test, typecheck, validator, `git diff --check`, install, Android, or network command was run by Codex. No files were staged, committed, or pushed.
## Wave 2B launch checkpoint — 2026-11-13

- Status: Wave 2A has passed its coordinator post-run (6 test files / 45 tests passed; typecheck no diagnostics; 29 older tests intact). Wave 2B is LAUNCHED under Addendum 7. Wave 2A is implemented and uncommitted; no commit has been made. Wave 2 will be one commit after 2B.
- Addendum 7 pre-append approval pin: 27,265 bytes / SHA-256 `64ABD9A8D94B84731965F99324E1E481B14B6005B2E0FF32F2505CACAC7B3E62`; post-append pin: 30,117 bytes / SHA-256 `3123895D0E3122500EFAD65A9B93E551ADBBF6CC90F9EC2FA54B45B815CCACAB`.
- 2B scope: seven E paths from Addendum 4, plus the owner-authorized pure helper and fake-data Vitest paths; the implementation report path is separately authorized. H pins remain frozen; no R path is writable. `OWNER_MODAL_CALL_APPROVED=NO`.
- Post-2B command accounting: one coordinator test run remains (4/4) and one coordinator typecheck run remains (4/4); one owner final run remains for each validator and `git diff --check` (2/2).
- The plan's descriptions of snapshot `1f5bb0b5` and Wave 1 as uncommitted/awaiting acceptance are superseded by Wave 1 acceptance and commit `3c75b10d`. No 2B check or runtime command has been run by Codex.

## M2 test-log and Wave 3 gate review — 2026-11-13

- Backlog proposals for state-aware active-run resume, a Home cancel/abandon action, and fetch timeout/status-0 handling are recorded as proposals only in `CONTEXT.md`; no approval or owner decision was changed.
- Wave 3 / P03–P06 has no entry in `approvals/TASK_APPROVAL.md`. The latest approval is Addendum 8, limited to Wave 2B post-run rework. The only Wave 3 plan found is the draft under `tmp/fe081-wave3/`; `D-011` and `plan/PLAN_REVISION_4.md` are absent.
- Wave 3 was not launched or implemented. Wave 2B remains subject to its Addendum 8 coordinator rework test/typecheck and owner final checks; no Wave 3 command budget is consumed by this review.
- Re-sync discrepancy for owner reconciliation: current HEAD `3386d7e0` is the Wave 2A+2B commit and matches the cached `origin/feature/fe-mobile-remediation` ref, while older FEAT-081 context/status prose says Wave 2 is uncommitted and names `3c75b10d` as current. This review does not infer that the Addendum 8 post-rework checks or acceptance are complete.

## Parent UI alignment review against owner-supplied SRS Rev67 — 2026-11-15

- Review input: owner-supplied `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 634,291 bytes / SHA-256 `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996`. This feature review does not update the repository-wide SRS authority register or imply formal SRS sign-off.
- Plan Revision 17: 5,277 bytes / SHA-256 `1E166E3D6DE16F5D784626C03715E59F1C4B0281150755EF91F5446632B523D`. Addendum 32 was appended to `TASK_APPROVAL.md`; its post-append pin is 88,094 bytes / SHA-256 `69357AB7E419D607612CDE41879222C405E7C53B96CD6E26F1131F5C78EE7E3A`.
- FE corrections: unknown/pending/unavailable consent no longer opens learning; Activity no longer bypasses main-activity selection; story generation, retry, rewrite, and confirmation are gated on explicit activity confirmation. No activity selection/API behavior was fabricated.
- Remaining gaps: the current application has no effective-consent or activity-selection service; no-preset Parent flow is blocked by the existing lesson-pin requirement; voice transcription, video/playback, post-video activities, and run lifecycle/history routes remain unavailable or unverified. See `evidence/IMPLEMENTATION_REPORT_SRS_REV67_UI_ALIGNMENT_20261115.md` for source references and limits.
- Evidence report: 5,196 bytes / SHA-256 `9062E7A65A02BCB540AD43B0C6ABD9C882799B268FDBD72AB05D3B483C06781B`.
- Static source review only. Tests, typecheck, validators, diff-check, install, network, backend, Android build, emulator, and Modal were not run. Nothing was staged, committed, or pushed. HEAD at the review snapshot: `af2dfc317e6d9a473b9288d1396ba5d1ece1a97c`.

## Parent API layer aligned to the dev /v1 routes; consent gate follows the canonical SRS — 2026-11-18

- Context: owner decision D-066-70 D-C merged `origin/dev` (local ref `1c9148e8`) into the mobile line on a local side branch `feature/fe-mobile-dev-align`, and the owner chose the dev route family (`/v1/parent/profiles`, `/v1/story-runs`) for mobile. Commits on the side branch: merge `e94cacbc`; API alignment `65e0332e`; consent gate `9ae5696e`; Alembic restore `2e61b369`. Not pushed; `feature/fe-mobile-remediation` is unchanged at `401ded3c`.
- API layer: `ParentApi.ts` returns to the `/v1` implementation. Profiles: create sends only `display_name`, `age_months`, `interests_summary` and returns the reference (the profile is read back), patch sends `expected_revision`, delete returns the pending view. Story runs: create, active, detail, context-confirmation, subject-confirmation, script-confirmation under `/v1/story-runs`. The `/api/parent/v1/child-profiles`, `/consent-policy`, `/story-runs` family and the data-authorization routes are no longer used. Plan Revision 19 and Addendum 34 (15 operations on that family) are superseded by this alignment; their files were moved out of the worktree to a local archive and were never committed.
- Fail-closed (no dev route): consent policy, authorization grant and revoke, activity suggestions. The profile form no longer loads or sends a consent policy.
- Consent gate: the Rev67-based rule that every learning start needs server-confirmed consent (Addendum 32 line of the 2026-11-15 review) is replaced for synthetic profiles by the canonical SRS (D-209, SRS lines 832 and 1095: consent is required only for real child data; a synthetic profile carries none). A profile whose `data_origin` is `SYNTHETIC_DEV` or `SYNTHETIC_TEST` may start a run; every other or missing origin still needs server-confirmed consent and stays blocked while consent is unavailable. The profile screen text that claimed an eligible profile could continue without consent was wrong and is corrected. Naming gap to record: the SRS names `SYNTHETIC_TEST`, the dev backend writes `SYNTHETIC_DEV`.
- Tests: the teammate's redesigned UI copy no longer matched ten `parentSrsBehavior` assertions; they were updated to the current wording and to the dev routes. Four pieces of old wording were not replaced by an equivalent statement (account-screen sign-out warning; "chưa được gửi, lưu" in the gender note; the handoff note that completion is not yet server-confirmed; the "no empty data is inferred" sentences of the history and lesson screens).
- Verification: owner run at `65e0332e`: `pnpm run typecheck` exit 0, `pnpm run test` 8 files / 92 tests passed and `UI_COPY_AND_RECOVERY_VALID`; before the alignment (at `401ded3c`, and after the dev merge at `e94cacbc`) the same test command gave 82 passed / 10 failed in `parentSrsBehavior.test.ts` and the validator did not run. Owner run after `9ae5696e` and `2e61b369`: typecheck exit 0, 8 files / 93 tests passed, `UI_COPY_AND_RECOVERY_VALID`. Owner-run validators on the side branch before the later two commits: `HARNESS_VALID`, `REPOSITORY_SECURITY_VALID` (7,429 files), `ARCHITECTURE_VALID`; `git diff --check origin/dev HEAD` reports trailing whitespace only in older FEAT-081 Markdown files, not in the files changed here.
- Open owner items: (1) a backend consent source for real data (SRS OI-05 keeps real child data blocked); (2) no dev route for activity suggestions or saving the chosen activity, so the activity and story steps stay blocked (SRS FR-P-05 makes the main activity mandatory); (3) the SRS step 7 context snapshot names a consent version that the dev schema does not carry; (4) `POST /v1/story-runs/{run_id}/cancel` exists on the M2 branch, not on `origin/dev`.
- Not done: no push, no move to `feature/fe-mobile-remediation`, no change to `TASK_APPROVAL.md`, no backend change except returning two Alembic files to their `origin/dev` content.

## Latest dev synchronization — 2026-11-19

- Status: local merge completed on `feature/fe-mobile-remediation`; merge commit `7863ca33d2401a1b53735f10109186691d970757` has feature start `5aa9443a772462d247a6018a62aab4e37d2092ae` and fetched `origin/dev` tip `ba295f1113129fa233ddc762ef29fadd92b996e8` as its two parents.
- The sole `.gitattributes` conflict was resolved by retaining the incoming dev rules and FEAT-081 pinned-plan rules. Plan Revision 5 and 7 SHA-256 values match their pre-merge values.
- Repository security validator passed (7,684 files scanned). Product tests and runtime/API/AI checks were not run. No push was performed.
- Evidence: `evidence/DEV_SYNC_20261119.md`; plan and approval: `plan/PLAN_REVISION_19.md`, Addendum 34 in `approvals/TASK_APPROVAL.md`.
## 2026-11-19 — Plan Rev20 approved: Parent Expo real end-to-end integration

- Plan: plan/PLAN_REVISION_20_PARENT_UI_E2E_INTEGRATION_20261119.md
- Status: APPROVED via Addendum 35; implementation in progress.
- Review uses the 32-screen annotated preview capture from UI commit 5aa9443a as layout/API mapping only, plus the post-merge source at f90226f3 and canonical FEAT-063 v2.7-draft SRS adopted by D-209.
- Scope excludes quota/payment. Video integration may use only the actual admission contract delivered by the quota workstream; no bypass is authorized.
- No source, API, database, environment, Firebase, Modal, UI runtime, emulator, or test changes were made for this planning step.

## 2026-11-19 — Owner steering added to Plan Rev20

- Added the two-stage topic path: three changing topic suggestions plus a separate topic text field; after topic selection, three suggested drawing subjects within that topic plus a separate subject text field.
- Added random-set stability for back/resume, catalog-first suggestions with Qwen draft fallback, and a blocking correction path for off-topic or ambiguous custom input.
- Marked the subject-before-capture flow as an SRS amendment gate because the adopted SRS currently says Parent does not preselect the drawing subject. Plan was approved via Addendum 35; the SRS amendment remains to be made before enabling subject suggestions.

## 2026-11-19 — M0 contract freeze completed; implementation started

- Plan Rev20 and its Addendum 35 approval pins were rechecked; source work remains in `feature/fe-mobile-remediation` at `f90226f37b265a8a35b02c95da5daa74146ad0a9`.
- Completed the two-stage topic/object owner amendment in the FEAT-063 working SRS as Rev70 and recorded D-214. Updated `docs/context/SRS_AUTHORITY.md` to point agents to the current Rev70 bytes. SRS remains unsigned.
- Source and read-only served-OpenAPI comparison is recorded in `evidence/M0_CONTRACT_CROSSWALK_REV20_20261119.md` (10,198 bytes; SHA-256 `0826D586A900F4A308E52E1701C63C01BEFDD2AE96E69FF5B3660BACBDC8F57D`).
- M0 findings: Parent profile/lesson/StoryRun routes exist in source; SVG guide remains the FLUX/raster 3-step legacy handler; VLM and story use synchronous base64 requests; the activity selection service exists but has no mounted Parent route or persistence; the story endpoint applies a butterfly lifecycle validator to every subject; story-run-lite uploads are explicitly unauthenticated loopback demo routes and cannot be reused for real Parent identity. Live OpenAPI at ports 58000 and 8000 is a projected environment snapshot whose activity/SVG routes do not match the current source tree; no mutation request was sent.
- Implementation state: M0 closed. M1–M5 are active. M6 video remains blocked pending real quota admission handoff and separate bounded approval. M7 screen APIs will be connected only where the real Parent contract exists; quota/payment remains excluded. M8 E2E evidence has not yet been collected.
- Verification: no test suite, typecheck, emulator, Docker mutation, Modal inference, database migration, commit, or push has been run in this checkpoint.

## 2026-11-19 — Rev20 implementation/E2E checkpoint (partial)

- **Overall:** IN_PROGRESS; not acceptance-complete. The implementation report is `evidence/IMPLEMENTATION_REPORT_REV20_E2E_CHECKPOINT_20261119.md`; Android screenshots are indexed in `evidence/ANDROID_E2E_REV20_20261119/README.md`.
- **Verified in real app:** synthetic Parent auth/profile, topic/object suggestions and custom validation, six-step catalog SVG guide, synthetic artwork selection, and StoryRun creation.
- **Blocking failure:** the sole bounded Qwen3.5 drawing inference ended with malformed/truncated JSON at 512/512 tokens. Modal worker terminal code was `MODAL_MODEL_OUTPUT_INVALID`; API surfaced 504 `MODAL_OUTCOME_UNKNOWN`. The worker EOS/LMFE and backend classification/logging fixes pass offline tests but have not been validated with another live inference.
- **Not reached:** valid drawing subject, activity selection, story generation/rewrite/confirmation, and video. No successful AI output is claimed; no fixture was used.
- **Checks:** backend focused tests 68 passed; Modal tests 29 passed; mobile tests 8 files / 94 passed; Python compile passed; API `/health` and relevant route registration passed. Mobile typecheck failed with 594 diagnostics total, 247 in Parent paths.
- **Cleanup:** task-local Compose stack and `sketch2life-srs23-drawing-vlm-dev` stopped; the existing video Modal app remains untouched. No shared/production migration, commit, or push.
- **Next gate:** one new bounded live drawing inference is required to validate the decoder fix before proceeding to activity/story E2E. Plan Addendum 35's consumed inference is not silently repeated.

## 2026-11-19 — Rev20B bounded Parent Android E2E result

- **Status: PARTIAL / BLOCKED; not acceptance-complete.** Detailed request/timing diagnostics and screenshot index: `evidence/ANDROID_E2E_REV20B_20261119/README.md`.
- Real Expo app, task-local API, authenticated synthetic Parent/profile, generated synthetic turtle artwork, and one live Qwen3.5-9B Modal drawing call were used. Topic and subject APIs, custom-subject validation, six-step catalog SVG guide, image picker, StoryRun creation, and post-failure run retrieval succeeded (profile POST 201/GET 200; topic/subject/guide 200; StoryRun POST 201/GET 200).
- Drawing worker completed in 30,197 ms, not a timeout. It generated 125 tokens, emitted EOS below the 512-token limit, but final JSON was incomplete at decoded position 224 while decoder diagnostics said EOS was allowed and the parser could end. Backend returned 502 `DRAWING_OUTPUT_INVALID`. UI displayed a safe failure; no automatic retry occurred.
- Activity selection/persistence, story/rewrite/confirmation and video were **not reached**. No activity/story inference, video call, quota call, fixture, or second inference was sent.
- Checked old run `f9b29982-5472-4456-b2e8-2f44dc900382` once using the authenticated local seed Parent token; API returned 401. No run state was disclosed and no cancellation was attempted. The client `ParentApi.cancelStoryRun` remains unavailable. No direct database edit was made.
- Cleanup completed: task-local Compose services stopped; Modal drawing and language/audio apps stopped with 0 tasks; Modal video app remains deployed and was untouched; task Metro was stopped. No commit or push.
- Earlier static checks remain: mobile typecheck 0 errors, 94 mobile tests passed, 29 drawing contract tests passed, and 68 focused backend tests passed. They do not establish a live drawing pass.
- **Next gate:** fix the mismatch between constrained-decoder EOS eligibility and the exact decoded/validated JSON prefix. A new live inference is not authorized by the consumed Rev20B one-shot; request separately bounded approval before another call.

## 2026-11-19 — Rev20B drawing decoder root cause (offline)

- Root cause identified for `DRAWING_OUTPUT_INVALID`: byte-fragment tokens became empty LMFE prefix-tree entries and were allowed after the JSON object closed. Fixed in `drawing_vlm_app.py`; regression test `test_drawing_lmfe_byte_fragments.py` passes (4/4) and fails against the old builder. Details: `evidence/ANDROID_E2E_REV20B_20261119/README.md`.
- Pending: re-run `test_qwen35_lesson_suggestion_contract.py`, redeploy the drawing app, and one new bounded live drawing call (needs owner approval). No commit/push.

## 2026-11-19 — Post-parser Parent rerun

- **Status: PARTIAL / BLOCKED at drawing output contract; not E2E complete.** One real emulator request reached Modal Qwen3.5-9B; worker succeeded, but the backend rejected its result with HTTP 502 `MODAL_OUTPUT_CONTRACT_INVALID` because required numeric `confidence` was missing. The Modal schema/parser only permits `candidate_subject` and `visible_features`, while SRS AT-14 requires candidate/confidence for adult review. Timing and sanitized evidence: `evidence/ANDROID_E2E_REV20B_20261119/README.md`.
- Parser regression tests: 33 passed, 2 warnings. The live call was not a timeout and did not reproduce the earlier malformed/trailing JSON failure.
- Topic/subject selection (`Động vật` → `Rùa con`), synthetic artwork attachment, and StoryRun create/read succeeded. Activity selection/persistence and story generation were not reached. No video, quota, payment, fixture, retry, or additional inference.
- Task Compose and task Metro are stopped; Modal drawing and language/audio are stopped; video app was untouched. No commit/push.
- **Next:** align worker schema/parser and backend with SRS AT-14, defining confidence semantics before emitting it; cover the worker/API contract offline. The approved one-shot is consumed; request a new bounded approval before another live inference.

## 2026-11-19 — Drawing confidence contract source fix

- **Source fix applied; runtime unverified.** Plan Revision 21 / TASK_APPROVAL Addendum 38 authorized adding the missing advisory confidence field to the Qwen drawing worker.
- The worker prompt/schema/parser/result now include a finite numeric confidence in `[0,1]`; the parser rejects malformed values. Mandatory adult confirmation remains true. The backend was not relaxed because its contract already matches SRS AT-14.
- No tests/typecheck, deploy, live Modal inference, Docker, database, or migration were run. The approved one-shot inference was already consumed; no repeat call is authorized here.
- Details: `evidence/DRAWING_CONFIDENCE_CONTRACT_FIX_20261119.md`. No commit/push.

## 2026-11-19 — Rev22 Android drawing-confidence verification

- **PASS for the bounded drawing-understanding UI check only.** Real Expo Parent UI on `emulator-5554` submitted one generated synthetic turtle image through the task-local backend to Modal Qwen3.5-9B. API returned HTTP 200; UI displayed `con rùa`, 95% advisory confidence, four visible features, and the adult **Xác nhận chủ thể** gate. The adult confirmation was intentionally not pressed; no activity, story, video, quota, or payment path was run.
- Modal Call ID `fc-01M7SVM2RR3035ZYNXRGARQ89F`; worker terminal event `worker_succeeded` in 30,301 ms; full UI/API elapsed 45.785 s. The same call's sanitized logs are in `evidence/ANDROID_DRAWING_CONFIDENCE_UI_REV22_20261119/logs/modal-worker-events.json`.
- The backend's immediate short log tail temporarily labeled the call `worker_started_without_terminal_event`; a later read of that same call returned 25 events ending in `worker_succeeded`. This is a log-indexing/tail-delay diagnostic gap, not a failed inference; track as a logging follow-up.
- Focused parser test: 4 passed, 2 deprecation warnings. Drawing Modal app, task Docker stack, task Metro, and Parent app were stopped after the test. The emulator was already running and remains on; local persistent synthetic profile/run data remains in its volume. No commit/push.
- Full evidence and limitations: `evidence/ANDROID_DRAWING_CONFIDENCE_UI_REV22_20261119/README.md`. Earlier Rev20B failure records are superseded only for this drawing-confidence contract check; they remain valid history for the wider, incomplete Parent workflow.

## 2026-11-19 — Rev23 Parent activity/story/video E2E authorized

- Owner directly requested completing the Parent workflow through activity selection and video, with product quota ignored for this run. Plan Revision 23 and TASK_APPROVAL Addendum 41 record the approved, bounded scope.
- Existing Rev22 Android run is the starting point at adult subject review; drawing inference is not to be repeated. Intended order: adult confirms subject → catalog-first activity selection receipt → story generation and adult confirmation → local synthetic-only no-quota admission → silent LTX-2.5 video → automated safety/validation → Parent playback and post-video activities.
- Source review found the Parent UI currently marks video unavailable, the Parent video client has no live operation, and video_app.py is a fail-closed scaffold. Existing session-video routes and Wan candidate are not valid substitutes for the SRS LTX target.
- Next: M0 served-contract/runtime comparison, then implement only the missing real Parent video/API/UI path if the current runtime cannot execute it. No live activity/story/video call has been made under Rev23 yet. No commit/push.

## 2026-11-19 — Rev23 execution amendment A1: Parent signup

- The owner requested the full Parent flow and authorized signup after the real Expo app opened at login. A synthetic Parent account was created through the real Android UI; the current-source backend returned HTTP 201 and the app reached the Parent home screen. Signup credentials were ephemeral and are not recorded.
- The new account cannot own/read the prior Rev22 run because it is a different Parent principal. No ownership transfer or direct DB edit was attempted. Plan Rev23 A1 / TASK_APPROVAL Addendum 42 now authorize one synthetic profile and a fresh UI-created run using the existing synthetic turtle drawing input, with one live call each for drawing understanding, activity suggestion, story, and video.
- Current state: authenticated Parent home, no profile yet; task-local Rev23 API/Postgres/MinIO/ClamAV and Metro remain running. No new AI inference has been sent under Addendum 42. Next: create a synthetic profile through the UI, verify its synthetic eligibility/consent gate, then proceed one stage at a time.

## 2026-11-19 — Rev20C drawing contract + recovery UI fixes (offline)

- Run `5ebfe11d…` failure root-caused: LMFE 0.11.3 ignores numeric min/max, so `confidence` out of range passed the decoder; now a closed enum. UI now shows terminal FAILED runs as failed and closes them without a cancel call. Worker tests 15/15 (real LMFE); mobile typecheck 0 errors. Details: `evidence/ANDROID_E2E_REV20C_20261119/README.md`.
- Pending: `pnpm --dir apps/ui-mobile test`, full Modal/backend test files, redeploy drawing app, one approved bounded live drawing call with `synthetic_turtle_lineart.png`. No commit/push.

## 2026-11-19 — Rev24 seed-account inspection

- `origin/dev` was already merged into this branch. Its new FEAT-066 seed package creates five synthetic Parent database principals plus profiles/lessons/runs, but does not create Firebase Auth users or provide login credentials. The current Rev23 database contains zero rows for those seed principals.
- The seed guard requires development auth, disabled AI providers, and a separate seed database. The active Firebase/Modal stack does not meet those conditions; no seed write or guard bypass was attempted.
- Parent API health and core routes are present. The cancel route is reachable at runtime but absent from served OpenAPI. No new emulator E2E or AI request was run: no usable Firebase seed account exists, and `adb` was not found in this shell.
- Detailed evidence: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/README.md`. No commit/push.

## 2026-11-20 — Rev24 real emulator rerun

- **Partial / blocked at Parent activity suggestion.** The Android emulator `emulator-5554` was online and used. The FEAT-066 seed from `dev` contains PostgreSQL development principals/content, not Firebase sign-in credentials; its guard was preserved. A fresh synthetic Firebase Parent account was registered through the real Android app; no credentials were saved.
- Real UI/API passes: signup/auth (`201`/`200`), Parent profile (`201`), topic and drawing-subject suggestions (`200`), StoryRun create/read (`201`/`200`), Qwen3.5 drawing understanding (`200`, Modal `fc-01M7TE95BG3GAJXK1CWM0TXV3K`, 66.203s), subject confirmation (`200`), context confirmation (`200`). The optional SVG guide was skipped.
- Activity stage: first request had no Modal call because the app was not deployed (`504`); second call failed before model load at `input_envelope` with `MODAL_WORKLOAD_NOT_ALLOWED` (`502`); added the missing L4 allowlist entry and a focused regression test (`3 passed`), deployed the app, then made exactly one UI recovery request. That call (`fc-01M7TEYCN2MXMSY61WJN09TRRQ`) remained in `model_inference` until the 1,800s backend wait expired (`504 PARENT_ACTIVITY_OUTCOME_UNKNOWN`, elapsed 1,800.048s, no terminal event/output). Modal warned that `causal_conv1d` and `flash-linear-attention` were absent and reference PyTorch implementations would be slower; this is a possible contributor, not a proven sole cause.
- Per Addendum 47, no further activity inference was sent. Activity selection, story generation, and video were not reached because no valid activity selection exists. Quota/payment were untouched; no fixture or real child data was used.
- Stopped the task language/audio app at 01:22:15 +07 and drawing app at 01:23:42 +07; both have zero tasks. Stopped task Compose containers and Metro at 01:27 +07 without deleting volumes; Android emulator remains online at the failure screen. The video app was not used and remains deployed. Final UI and sanitized logs are in `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`; see `API_WORKFLOW_RESULT_20261120.md`. No commit/push.

## 2026-11-20 — Rev25 Qwen3.5 activity recovery authorized

- Owner directly authorized continued fixing and resumption through the real Parent workflow. Plan Revision 25 and TASK_APPROVAL Addendum 48 now authorize a bounded recovery of the actual Qwen3.5 activity worker.
- Current evidence points to missing `flash-linear-attention`/`causal-conv1d` fast kernels and a silent 1,800-second inference. The runtime fix will keep the pinned Qwen3.5 model, add fail-fast kernel checks and privacy-safe token-count progress, and cap activity inference at 8 minutes.
- No implementation or new inference is reported yet. Preserve the existing dirty worktree. Next: validate pinned dependency compatibility, implement focused worker/backend diagnostics, run offline checks, then make one UI-driven recovery request; proceed to activity selection/story and optional silent LTX-2.5 only as gates pass.
- Plan: `plan/PLAN_REVISION_25_QWEN35_ACTIVITY_INFERENCE_RECOVERY_20261120.md`; approval: Addendum 48. Evidence stays in `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/`. No commit/push.

## 2026-11-20 — Rev25 activity recovery attempts; Rev33 performance amendment

- **Still blocked before activity selection.** The first post-kernel call (`fc-01M7V4JFQ43TP51RR9CJH4S2N4`) failed in `model_inference` with `NameError: StoppingCriteriaList is not defined`; review also found `progress` had no binding. Both were fixed and the focused activity-wiring/L4 tests passed (`3 passed`).
- The second real Android call (`fc-01M7V4WKRXR151Q8RXR77GJP4G`) used Qwen3.5-9B and verified FLA/causal-conv1d/Triton on CUDA 12.6, capability 8.9. Model load took 20.756s; constrained-decoder setup 3.733s; inference produced 104/1,000 tokens by 424.778s. Backend returned 502 `FunctionTimeoutError`; Modal ended the worker with `KeyboardInterrupt` at 450.006s. No activity JSON/receipt was produced; UI remained on the activity retry screen.
- This confirms a slow/stalled inference after model load and successful kernel checks. The actual GPU type, device-map offload, cache and per-token constrained-decoder cost were not recorded. The text worker currently loads a multimodal model for text-only activity/story work; Rev33 is approved to use Qwen3.5's text-only loader and add safe diagnostics before one more bounded UI activity call.
- Plan: `plan/PLAN_REVISION_33_PARENT_ACTIVITY_TEXT_ONLY_INFERENCE_20261120.md`; approval: Addendum 57. Current evidence directory: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`. Story/activity selection/video remain unverified. No quota/payment, commit, or push.

## 2026-11-20 — Rev33 terminal input mismatch; Rev34 bounded correction

- The one Rev33 UI activity attempt (`fc-01M7V6B8Z31YNHR5SPSERRMTHE`) confirmed the text-only model loads on the Modal GPU in 16.886s, but generation failed immediately because `AutoProcessor` supplied `mm_token_type_ids`, which `Qwen3_5ForCausalLM.generate()` rejects. No tokens or activity result were produced. Full sanitized Modal logs and diagnosis: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/13-rev33-activity-failure-analysis.md` and `12-modal-activity-terminal-error.log`.
- Implemented a shared generation-input filter for all seven text-only Qwen generation call sites; it removes only `mm_token_type_ids` and preserves text IDs/mask. Focused offline verification: Python compilation passed; 13 tests passed, 44 deselected.
- Rev34 is approved under the owner's continuing direct instruction. Next: deploy language/audio app, run CPU-only readiness, then at most two distinct UI-driven activity attempts after code fixes, 8-minute cap each; stop on success or second failure. Existing catalog, safety, age, consent and quality gates remain enabled.
- Plan: `plan/PLAN_REVISION_34_QWEN35_TEXT_INPUT_COMPAT_20261120.md`; approval: Addendum 58. No story/video is attempted until an activity is successfully persisted. No quota/payment, fixture, DB mutation, commit or push.

## 2026-11-20 — Rev34 activity input fixed; decoder bottleneck found; Rev35 approved

- The Rev34 UI attempt (`fc-01M7V6NPS2G9298TK1W0EZ554R`) passed `mm_token_type_ids` filtering and ran Qwen3.5-9B text-only on an NVIDIA A10 with cache enabled and no CPU/disk offload. It produced 100 tokens in 195s; LMFE callbacks at tokens 98–100 each took ~50s while allowing ~246.5K tokens. The call was cancelled at ~231s total to limit GPU use. No activity result/receipt was persisted.
- Root cause found in LMFE 0.11.3 behavior: bounded regex prose fields bypass the JSON free-text fast path. The generation schema now uses the same string min/max bounds; existing worker parser continues to enforce required text, exact limits and ending punctuation. A CPU-only parser check confirms the new fast path; focused tests pass (`15 passed, 31 deselected`).
- Rev35 authorizes one remaining real Android UI activity request after redeploy/readiness, capped at eight minutes, with no retry. On success continue the existing approved flow; otherwise stop and report.
- Plan: `plan/PLAN_REVISION_35_LMFE_PARENT_ACTIVITY_DECODER_PERFORMANCE_20261120.md`; approval: Addendum 59. Detailed logs and screenshots: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/16-rev34-decoder-performance-analysis.md`. No quota/payment, fixture, direct DB mutation, commit or push.

## 2026-11-20 — Rev37 Unicode filter passed its gate; punctuation contract remains

- Rev37's single real Parent UI request used the existing synthetic StoryRun and Modal call `fc-01M7V9SVGD1WXFXD4FS07TSYA2`. Qwen3.5-9B generated 746 tokens in 111.629s; the activity-only Unicode filter blocked non-Latin candidates and the output passed JSON completion, but the unchanged sentence-punctuation gate rejected at least one text field with `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT`. No suggestion set was persisted; activity selection, story and video remain untested.
- The API's generic terminal code was observed before Modal's specific terminal log was indexed; this was not a wait timeout. No timeout or quality-gate change was made.
- Worker events and screenshots: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/23-rev37-activity-failure-analysis.md` and `23-rev37-modal-activity-sanitized.json`. Focused tests passed (`8 passed, 39 deselected`); Modal CPU readiness passed without loading weights.
- Rev38 needs a stronger field-specific punctuation instruction and safe field-path diagnostics before one new UI request. No retry under Rev37. No quota/payment change, database edit, fixture flow, video call, commit or push.

## 2026-11-20 — Rev38 punctuation failure; Rev39 token-level correction approved

- Rev38's one real Parent UI request (`fc-01M7VAJFS2C69SNHZSZA3J0FQ1`) generated 693 tokens in 112.178s and completed JSON/EOS, but failed the unchanged punctuation gate at `fallback_activities[0].objective`; no suggestion was persisted. This was not a timeout. Detailed sanitized result: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/27-rev38-activity-failure-analysis.md`.
- LMFE 0.11.3 source review showed its cached free-text token allowlist includes tokens ending in a quote; a character-level parser wrapper alone would not enforce the terminal punctuation rule. Rev39 instead filters quote-ending token IDs in the existing Parent activity candidate-filter pass, limited to the four fields already checked by the parser.
- Rev39 offline verification: focused Parent activity tests **21 passed, 40 deselected**; compilation and `git diff --check` passed. The complete worker contract module reported **60 passed, 1 unrelated existing drawing-parser test failure** because that test expects a response without the now-required `confidence` property. No drawing code/test was changed.
- An offline LMFE 0.11.3 CPU probe confirmed quote-ending tokens (including a combined text+quote token) are blocked before punctuation and a standalone quote is allowed after the period. No model, GPU, or Modal inference was used.
- Task API container is healthy and Android emulator is connected. Plan Revision 39/Addendum 63 authorize deploy + CPU readiness and exactly one fresh real Parent UI activity request capped at eight minutes, with no retry. Activity selection/story can continue only after a successful persisted result under prior approvals; video remains conditional on its exact prior authorization and gates. No quota/payment changes or bypass, DB changes, fixture, secret/SRS edit, commit, or push.

## 2026-11-20 — Rev39 activity failure; Rev40 approved

- Rev39's bounded real UI attempt failed at the existing punctuation validator, not by timeout. It did not persist an activity suggestion; activity selection, story and video were not reached. The ineffective quote-token filter is superseded by Rev40's typed internal sentence representation; public/backend contracts and quality gates remain unchanged.
- The code reached the catalog-backed path, but runtime logs did not expose catalog/candidate counts. Rev40 adds safe integer-only counts for lesson access/age, renderability/exclusions, relevance filtering, and worker input size.
- Plan Revision 40 and TASK_APPROVAL Addendum 64 authorize offline tests, deployment/readiness, and exactly one fresh activity request through the existing authenticated synthetic Parent UI. No retry. Selection/story may continue only under prior active approvals; video is not newly authorized.
- Plan: `plan/PLAN_REVISION_40_PARENT_ACTIVITY_TYPED_SENTENCES_AND_CATALOG_COUNTS_20261120.md`; evidence: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`. No commit/push.
- Rev40A/Addendum 65 additionally authorizes rebuilding only the task-local `api` service with the existing Compose files and `--no-deps`; inspection showed the healthy container has no source bind mount. No other service restart, migration, seed or volume change is permitted. This adds no AI request.

## 2026-11-20 — Rev40 catalog source verified; Rev40B fallback copy

- The Parent activity request did query the catalog through `LessonLibraryParentActivityCatalogAdapter` → `LessonLibraryService.list_parent_activity_catalog`, restricted to lesson versions the authenticated Parent can currently access. Runtime counts were all zero (`accessible_lesson_count=0`, age/access-eligible lesson/activity counts `0`, relevance matches `0`, candidates sent `0`); Qwen therefore returned and the backend persisted three AI fallback drafts. This was a catalog miss, not a skipped catalog query.
- The repository also contains `data/activity-catalog`, but the canonical Parent source in SRS Rev63/67 is Parent-accessible PUBLIC/SHARED lesson versions (or the exact pinned lesson version). The static ACT/demo dataset is provisional and is not the Parent product source. No static dataset was loaded into the Parent request.
- Catalog source and live run details: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/38-rev40-catalog-source-check.md`; raw sanitized API/Modal logs remain `36-rev40-api-activity-log.txt` and `36-rev40-modal-activity-log.txt`.
- Rev40B/Addendum 66 changes only user-facing fallback explanation and suppresses model-authored `match_reason` for AI drafts. It does not change catalog lookup, API/persistence, selection behavior, or activity gates. Next: run approved mobile tests/typecheck, verify the saved result via Expo Fast Refresh, then continue the existing one-selection/one-story allowance. No additional activity inference, video, quota change, commit or push.
- Rev40B mobile checks passed: **125 tests across 15 files**, typecheck passed, and Metro's Android bundle contains the safe copy (not the old copy or `candidate_activities`). The emulator's loaded React Native runtime did not apply Fast Refresh or the supported dev reload action; screenshot `39-rev40b-activity-result.png` therefore still shows the old internal reason. No app reinstall/restart was done because it would discard the in-memory saved activity suggestions and could provoke an unauthorized second inference.
- The existing persisted activity was selected in the real UI and `POST .../activity-selection` returned **200**. One real story request then returned **200** through the UI. Modal call `fc-01M7VEYF77EX3HV1MM80K4TC27` used Qwen3.5-9B on NVIDIA A10: 14.614s model load, 132.886s generation, 1,371 tokens, no CPU/disk offload; JSON parsing and business-rule validation succeeded. Story is a draft with **5 scenes**, shown on the adult review screen. It was not confirmed; no video request was sent. Screenshots/XML and correlated sanitized API/Modal logs: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/45–50-rev40-*`.
- Observability follow-up: the API's wait-completion snapshot said `worker_started_without_terminal_event`, while the correlated Modal log later emitted `worker_succeeded` and the UI/API returned the story. Functional result succeeded; the API diagnostic snapshot appears to have missed the later terminal log. The generated story UI also visibly appends numeric fragments to some scene text (for example `68`/`69`), which needs a separate story-output/UI review. No out-of-scope fix was made.
- After capturing evidence, stopped the task's `sketch2life-srs23-language-audio-dev` Modal app in `dev`; Modal lists it as stopped with zero tasks. Drawing and video apps were not touched. The Android emulator remains on the story review screen.

## 2026-11-20 — Rev41 Parent UI/video baseline

- Plan Revision 41 / TASK_APPROVAL Addendum 67 is approved under the owner's direct request to refresh remaining Parent screens and add video.
- M0 confirms the real Expo app is online on `emulator-5554`; task API health is HTTP 200 at port 58100 and Metro is running. The task Docker project is `s2l-feat081-rev23`; unrelated Docker projects remain untouched.
- Updated the six stale-tone screens: Context, Handoff, DrawingGuide, LessonPicker, TranscriptReview, and SketchGuide. Existing handlers/routes were preserved.
- Fixed story output count-metadata leakage at the Modal prompt/parser boundary and corrected backend classification when a successful remote call has a delayed terminal log.
- Offline checks passed: Modal story contract 64; backend Modal story client 10; mobile 125 tests across 15 files; mobile typecheck passed.
- Reloaded the real Android app. Metro and API health remained good; app reached Parent sign-in, but the authenticated session did not resume. No account was created and no AI inference was triggered. The six screen changes are not yet visually verified in an authenticated post-reload run.
- The persisted story shown before reload still contains count fragments (`68`, `69`). It was not rewritten, stripped, or sent to video.
- Correction from the 2026-11-20 Modal audit: LTX-2.5 is implemented and deployed in Modal app `sketch2life-srs23-dev-video`; FEAT-067 has real five-scene silent MP4 candidates, including a technically validated candidate. The earlier statement that the system-wide Modal worker was a scaffold was wrong: only the FEAT-081 checked-out `video_app.py` is a scaffold. FEAT-067 evidence also records a later visual-quality failure, and neither candidate passed video safety or product playback.
- Rev41 remains **PARTIAL / BLOCKED at Parent API admission, worker dispatch, safety and playback integration**, not at LTX worker availability. FEAT-081 served OpenAPI had 0 Parent video routes. FEAT-067 has fail-closed request/status routes whose service returns `VIDEO_ADMISSION_DEPENDENCIES_UNAVAILABLE`; the mobile client has no video-generation request/status operations. The real FEAT-067 Modal candidate call was direct and did not complete the product flow.
- Evidence: `evidence/PARENT_UI_VIDEO_REV41_20261120/REV41_M1_IMPLEMENTATION_AND_VIDEO_BLOCKERS.md`, the FEAT-067 result report referenced there, and captures `00-before.png` through `03-after-wait.png`. No new LTX call, quota mutation/bypass, migration, deploy or app stop was made for this audit.

## 2026-11-20 — Rev42 Parent Modal candidate integration

- **Source integration: COMPLETE.** Parent API/client, application boundary, candidate status/progress UI, and authenticated private preview are connected to the existing Modal LTX-2.5 function. Candidate path is local/test and synthetic-only, default-off, idempotent, and explicitly not product-ready; no quota path is used.
- **Offline verification: PASS.** Backend focused unit/contract suite: 19 passed. Mobile typecheck passed; 126 tests across 15 files passed. Ruff and `git diff --check` passed.
- **Runtime/E2E: NOT VERIFIED.** No eligible confirmed synthetic story was established for this pass, so no Modal request or new MP4 was generated. No emulator walkthrough or DB migration was performed. Migration `20261120_parent_video_candidate` is source-only and remains unapplied.
- **Quality limitation:** the worker visual manifest currently lacks general mapping for story-mentioned props. A technically valid candidate can omit required scene objects; safety/consistency remain `NOT_RUN`, and product playback remains false.
- Evidence: `evidence/PARENT_MODAL_VIDEO_CANDIDATE_REV42_20261120/IMPLEMENTATION_REPORT.md`. No deploy, Modal app stop, shared DB change, commit, or push.

## 2026-11-20 — Rev43 Parent E2E checkpoint

- **API runtime:** refreshed only task API `s2l-feat081-rev23-api-1`; `/health` 200 and all 4 video candidate routes registered.
- **DB:** applied additive `20261120_parent_video_candidate` to the task-local FEAT-081 Postgres; table verified. No business rows seeded/edited.
- **Stopped at auth/config gate:** emulator is at sign-in; backend `auth_provider=development`, Firebase project/Admin credential absent; Modal token ID/secret absent in API container. Unauthenticated candidate POST returned 401 as expected.
- **AI/video:** no account creation, no provider inference, no Modal dispatch, no video artifact, no quota access. Existing Modal video app stays deployed with 0 tasks. Nothing was retried.
- Evidence and setup keys: `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/RUN_REPORT.md` and `00-parent-sign-in-blocker.png`. The task stack remains running; no commit/push.

## Rev43 live Parent E2E result — 2026-11-20

- **Partial; stopped at activity suggestions.** Root <local-machine-path> was explicitly loaded into the task API without printing or copying its values. Parent registration created one synthetic Firebase account; the first /me token check returned 401, while a later login and /me returned 200.
- Synthetic E2EChild profile (60 months) and a new synthetic sea-turtle drawing were used. Catalog topic/subject requests passed. The curated SVG guide returned 404 for Rùa biển; the optional guide was disabled.
- Drawing Qwen3.5-9B inference passed in 42.34 seconds; UI showed “con rùa” at 90%, and subject/context were confirmed.
- Activity catalog returned no eligible candidates. The single Qwen fallback failed before Modal call creation: NotFoundError, API HTTP 504. Current Modal dev inventory lacks sketch2life-srs23-language-audio-dev; no retry was sent.
- Story and video were not requested. No quota was read or mutated. The task services remain running. Full correlation and screenshots: evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/RUN_REPORT.md. No commit or push.

## 2026-11-20 — Rev45 continuation after deploy

- Deployed the missing language/audio Modal app to `dev` with one UTF-8-corrected retry; inventory confirms deployed, zero tasks.
- Resumed the same real Android Parent run. Activity inference passed and saved “Phân loại thẻ rùa”; story inference passed, produced a 5-scene Vietnamese draft, and the adult confirmed it through the UI. The selected activity matches the story.
- StoryRun `16002cde-42b1-4198-a7d0-a04de85fea9b` is `SCRIPT_REVIEW` / `SUCCEEDED`; story revision 1 is `CONFIRMED`. The API contract/runtime and Modal video worker are present. No video request or quota access has occurred yet.
- Expo app was restarted while checking why the video card was not visible and returned to sign-in. Manual Parent sign-in is pending so the same server-side run can be resumed and video can be requested once from the UI.
- Detailed IDs, durations, and sanitized status: `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/RUN_REPORT.md` and `logs/run-events.md` in that folder. No source change, commit, or push.

## Rev46 — Parent UI E2E (2026-11-20)

- **PASS:** Firebase Parent login; synthetic profile create/read-back; topic and subject selection; synthetic image pick; context confirmation; drawing inference; activity fallback and persisted selection; story API/model response.
- **BLOCKED at adult story review:** generated Vietnamese story contains mixed-script text (`các動作`) and unnatural age phrasing. Do not confirm, regenerate, or call video without a new bounded approval.
- **Video:** not requested; approval required a suitable confirmed story. No quota/payment state accessed.
- **Evidence:** `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/RUN_REPORT.md`, sanitized `logs/run-events.md`, and story-review screenshot. Emulator remains on the review screen; Docker/API and Modal apps were left running.

## Rev49 — Parent video loading and candidate attempt (2026-11-20)

- **Loading UI: PASS.** Added state-specific progress phases, clear request-versus-status messaging, 30-second polling guidance, and no-resubmit copy. Failed/reconciliation states do not show a false progress indicator.
- **Verification: PASS.** Mobile typecheck; 133 tests across 16 files; UI copy/recovery validator; `git diff --check`.
- **Video E2E: BLOCKED BEFORE DISPATCH.** The Android app returned invalid credentials for the two pre-existing synthetic Parent credential sets. No candidate request or Modal inference was sent. Candidate flag remains false; API health is 200.
- **Next:** restore valid login for the already-created synthetic account, then resume only the approved StoryRun and one LTX candidate request. No second account, quota access, retry, Modal lifecycle change, commit, or push.
- **Evidence:** `evidence/PARENT_VIDEO_LOADING_REV49_20261120/RUN_REPORT.md`.

## 2026-11-21 — Rev52 Parent backend + UI E2E checkpoint

- Real Android Parent UI, task API, and Modal were exercised without the preview harness. Drawing recognition and adult subject/context confirmation passed for a synthetic turtle image.
- Catalog-first lookup returned zero accessible/eligible published/shared lesson activities. The single AI fallback call completed but returned three Vietnamese activity drafts with truncated clauses. Backend persisted them and the UI displayed them, exposing a backend/worker quality-gate defect.
- Stopped before activity selection, story, and video; quota/payment was not accessed. No repeat inference was sent.
- Added a Vietnamese incomplete-sentence-tail validator to the backend fallback gate and Modal worker parser, shortened structured body limits, and strengthened the prompt. Updated regression tests to the current `{body, terminator}` worker contract.
- Offline verification: backend 36 tests passed; Modal activity subset 24 passed (40 deselected); mobile drawing terminal 6 tests and typecheck passed; `git diff --check` passed. Ruff was unavailable in the active environment.
- **Runtime remains unverified after the fix:** no API rebuild or Modal deploy/re-inference was allowed by Addendum 88. The persisted malformed suggestion set was preserved and not selected. See `evidence/PARENT_BACKEND_FRONTEND_FIX_E2E_20261121/RUN_REPORT.md` and `screenshots/parent-activity-result.png`.
- No quota changes, DB edits, fixture-based E2E, commit, or push.

## Rev55 — awaiting lifecycle purge scope decision (2026-11-21)

- Parent loading UI fix is source-complete; mobile typecheck and 141 tests pass; focused backend checks 68 pass.
- Exact existing run cancellation returned 202 via Android UI after migration. Run is DELETE_PENDING; active-owner lock is released; one lifecycle outbox event remains pending (attempt 0).
- Task Docker stack has no lifecycle worker. Processing the event purges run-owned content/assets. Addendum 91 says preserve them, so no worker/purge/new StoryRun was started.
- Full Parent E2E is paused at this boundary pending owner approval to process only this cancellation event. Quota/payment and Modal/video were not called. Report: vidence/PARENT_LOADING_E2E_REV53_20261121/RUN_REPORT.md.

## Rev55 E2E result after Addendum 102 (2026-11-21)

- The exact approved cancellation event for run `08657e31-ebd7-4a07-8f9b-5929b4dff23b` was processed by the one-shot lifecycle consumer. Run `DELETED`, event delivered, lifecycle receipt completed; no unrelated records touched.
- Fresh real UI run `b05c2b46-e760-4643-824b-b30b5387453f` passed topic, SVG guide, synthetic image, drawing understanding, adult confirmations, catalog-first activity query (0 eligible), one AI activity fallback, and activity selection.
- Story call `fc-01M7Y9SCQQP9RCJXARXQBDX25G` failed the prose-completion gate (`STORY_TEXT_INCOMPLETE` / API `502 STORY_OUTPUT_INVALID`), after 77.185 s inference and 102.295 s worker time. This was not a timeout. The one-story cap was consumed; no retry, video, quota/payment call, or gate bypass.
- Loading card/timer was visible, but stage-level progress is absent. Failure screen still exposes “Gửi lại cùng yêu cầu”; not pressed. Screenshots: `evidence/PARENT_LOADING_E2E_REV53_20261121/screenshots/82-story-inference-started.png` and `83-story-failure.png`.
- Stopped only the task-used drawing and language/audio Modal apps at 12:47 +07 after confirming 0 tasks. Video Modal app remains untouched. Full report: `evidence/PARENT_LOADING_E2E_REV53_20261121/RUN_REPORT.md`.
- Overall workflow remains PARTIAL; story review/video were not reached. Additional inference requires a new bounded approval after a worker correction and focused verification. No commit/push.
- **Rev56 stop:** read-only check found run `b05c2b46-e760-4643-824b-b30b5387453f` terminal `FAILED` / `STORY_OUTPUT_INVALID`, latest story revision failed, activity selection persisted. Backend disallows revision reservation from `FAILED`; current SRS says terminal, so the conditional rewrite in Addendum 103 is not eligible. Android Home/history also lacks a recovery route. No inference, deploy, mutation, video, or quota call was sent. API health 200; Modal apps remain stopped. See RUN_REPORT screenshots 85–86.
- **Next:** Addendum 104 / Plan Rev57 awaits owner decision on a narrowly guarded SRS/backend recovery transition. No implementation or inference before approval.

## Rev57 approved one-shot rewrite — 2026-11-21

- **Implementation/offline verification:** complete for the approved recovery path. Backend focused tests 21/21; mobile typecheck and 142/142 tests pass; UI-copy validator, focused Ruff, and `git diff --check` pass.
- **Live result:** one real Android UI rewrite was submitted on the existing synthetic run. API returned 504 and recorded `STORY_OUTCOME_UNKNOWN`, with no Modal call ID. Modal logs had no worker entry and inventory remained at zero tasks; exact dispatch-versus-GPU-start cause is unproven.
- **Current run state:** `SCRIPT_GENERATION_UNKNOWN`; job and story revision 2 are `AWAITING_RECONCILIATION`; retryable false; active-owner lock held. No second request, video, quota/payment, fixture, or gate bypass.
- **Cleanup:** stopped only the task-used Modal language/audio app after confirming zero tasks. Drawing app remains deployed with zero tasks; video app untouched.
- **Security validation:** failed on pre-existing findings in older FEAT-081 artifacts; no commit or push. Evidence/report: `evidence/PARENT_LOADING_E2E_REV53_20261121/RUN_REPORT.md`.
- **Next:** obtain a separate decision for reconciling this unknown outcome. Do not retry or start another run while the active-owner lock is held.

## Rev58 approved Parent-to-video continuation — 2026-11-21

- Owner directly instructed: “fix nếu có bug, nào chạy đc vid thì mới dừng.” Plan Rev58 is approved and pinned in Addendum 105.
- Initial runtime check: task API is healthy; candidate flag is disabled. The current FEAT-081 video Modal file is a scaffold; no video app is deployed in Modal `dev`. Pinned LTX-2.5 implementation is available in the separate FEAT-067 worktree and has historical synthetic candidate evidence, but needs review/port/deploy in this worktree.
- Run `b05c2b46-e760-4643-824b-b30b5387453f` remains `SCRIPT_GENERATION_UNKNOWN` with revision 2 `AWAITING_RECONCILIATION`, no call ID and active-owner lock held. It will not be replayed or manually changed.
- Scope: reconcile read-only; improve story dispatch diagnostics; deploy/verify the pinned LTX-2.5 worker; enable only the existing synthetic local candidate path; complete Parent Android UI flow to authenticated private MP4 preview/playback; preserve `product_playable=false` and `safety_validation=NOT_RUN`.
- No quota/payment mutation or bypass, production-gate bypass, real-child media, blind retry, model/GPU substitution, commit or push. Evidence belongs under `evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/`.
- **M0 complete:** read-only DB, API, Modal logs/inventory, model Volume metadata and source review are recorded in `evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/M0_DIAGNOSTICS.md`. The old story outcome remains unresolved, so its run/lock remain untouched.
- **Current phase:** M1/M2 implementation and verification. No new inference has been sent.

## 2026-11-21 — Rev58 Firebase setup fixed; candidate owner mismatch

The owner then directed continuation with the current login. Its open `SyntheticTurtleRev22` run was opened through the real UI and remains `SCRIPT_GENERATION_UNKNOWN` / `AWAITING_RECONCILIATION`, non-retryable, without a provider job ID, and holds the Parent account's active-run lock. The UI prohibits resending and remained pending on status-only polling. No new request or state change was made. Evidence: `M5_ACCOUNT_SCOPE_CHECK.md` (`61`–`63`).

The emulator was rechecked after the owner said the account was already logged in: Home showed `SyntheticRev58Turtle`, and the real `Câu chuyện` tab showed “Chưa có buổi nào”. The redacted `.env` comparison remains mismatched, so the current session cannot access the saved video candidate. Evidence: `evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/M5_ACCOUNT_SCOPE_CHECK.md` (`59_current_ui.png`, `60_story_tab.png`).

Follow-up redacted comparison after the owner selected the existing-account path: Parent email/password are present in root `.env`, but the configured email resolves to a different Firebase Auth user from the saved candidate owner. No sign-in attempt, account mutation, inference, or credential disclosure occurred.

The task API was recreated with the root `.env` explicitly loaded. Firebase Admin and Modal dev configuration now initialize; API health is 200; Android sign-in with the existing seed Parent succeeds. A read-only owner check found the saved silent-video candidate belongs to a different Firebase principal/profile than this seed account. The target profile's UI history is empty, so recovery was not called. A follow-up Firebase Admin read confirmed the target owner still has an enabled email/password Auth account; no account identifier or credential was recorded. A separate pending `SyntheticTurtleRev22` run was left unchanged. No new account/run, inference, quota call, or database write occurred. Evidence: `evidence/PARENT_SILENT_VIDEO_E2E_REV58_20261121/M5_ACCOUNT_SCOPE_CHECK.md`. Resume after the existing owner account is made available in the root seed configuration, or with a separately approved new run/video inference.

## 2026-11-22 — Addendum 117 Parent AI parser/content repair

- Implemented the approved bounded activity-text and duplicate-key parser repairs; catalog excerpts now stop at word boundaries without modifying source lessons.
- Offline verification: 184 Modal contract tests and 278 backend parser/service tests passed; changed Python files compile; scoped git diff --check passed.
- Rebuilt task API image s2l-feat081-rev23-api:parent-ai-parser-rev117; container is running and /health is ok. Modal language/audio is deployed and CPU readiness is ready_for_gpu_worker_validation; Modal inventory showed zero active tasks.
- The one approved real activity inference returned HTTP 200, three fallback activities in 104.515 seconds, but one pre-fix materials field was truncated and accepted. No inference was sent after repair, so live corrected wording remains unverified.
- Read-only parser audit found silent-video input manifests use ordinary JSON parsing but are backend-produced, not model-authored. video_app.py is outside Addendum 117's allowlist and was not changed. Full audit: evidence/PARENT_AI_PARSER_AUDIT_REV117_20261122/PARSER_AUDIT_REPORT.md.
- No quota/payment operation, gate bypass, video inference, commit, or push.

## 2026-11-22 — Local synthetic video candidate gates enabled

At the owner's request, added the two local-only synthetic video flags to the single root CAPSTONE .env and recreated only the FEAT-081 API container. Effective environment is local with Modal dev provider; both required flags are true. API is healthy. The deployed LTX-2.5 checkpoint reports staged, but no GPU model is loaded and no video request was sent. This is a technical-preview route, not product-ready video. Evidence: evidence/PARENT_VIDEO_LOCAL_ENABLE_REV117_20261122/CONFIGURATION_CHECK.md.

## 2026-11-22 — Rev59 Parent video candidate status response

- Fixed the HTTP 500 on status polling: persisted integrity fields were being passed into the strict public metadata schema. The response now projects only contract fields; persistence and integrity metadata remain unchanged.
- Focused tests: 14 passed. Python compilation, scoped diff checks, API rebuild, and `/health` passed.
- Android fetched the already-ready synthetic candidate and opened its existing private preview. API logs showed zero instances of the prior validation error after rebuild.
- No new inference, candidate, run, database mutation, quota/payment call, gate bypass, commit, or push. Safety/consistency are still `NOT_RUN`; the candidate is not product-playable.
- Evidence: `evidence/PARENT_VIDEO_CANDIDATE_RESPONSE_FIX_REV59_20261122/RUN_REPORT.md` and screenshots.

## 2026-11-22 — Rev60 Parent video playback UI

- Replaced native-only controls with explicit accessible Play/Pause/Replay actions, playback status/timeline, visible errors, and retry of the existing preview. Reduced repeated warning and technical metadata copy.
- `pnpm --dir apps/ui-mobile typecheck` passed.
- The pre-change emulator showed HTTP 200 and the first frame but Play remained at `00:00`.
- Post-change playback is not yet verified on-device: the full bundle reload dropped the in-memory Parent session; after reauthentication, resume returned to activity selection and history has no open-video action. No activity inference or new video request was sent.
- Task remains partial until the existing candidate can be reopened without new inference and Play/Pause is verified. Evidence: `evidence/PARENT_VIDEO_PLAYER_UI_REV60_20261122/RUN_REPORT.md`.

## 2026-11-22 — Rev61 bounded Parent AI and player check

- API health is `ok`; the three existing Modal `dev` apps are deployed with zero tasks. This check did not deploy, warm, or stop Modal apps.
- Read-only inspection confirms existing AI output for one synthetic run: activity fallback set, selected activity, confirmed five-scene story, and a `CANDIDATE_READY` 30.209-second 1280×720 video candidate (4,289,168 bytes; Modal call reference present).
- One Android UI activity-suggestion request returned HTTP 409 because the run was already `SCRIPT_REVIEW`; the backend rejected the stale action before Modal dispatch. No new AI inference or video generation occurred, and no retry was sent.
- Cold resume returned to Activity rather than the saved story/video. Source inspection points to `adoptServerUnderstanding` treating the fresh client revision `0` as a changed server revision and skipping saved-story adoption. The current-candidate hydration path also needs checking on resume.
- The Rev60 Play/Pause change is still **not verified on-device**. Rev61 permits no product-code change; a separate approved amendment is needed to repair resume/hydration and replay this candidate in the real UI.
- Evidence: `evidence/PARENT_AI_VIDEO_PLAYBACK_REV61_20261122/RUN_REPORT.md` and its Android screenshots. No DB mutation, quota/payment operation, gate bypass, commit, or push.

## 2026-11-22 — Rev62 cold resume and candidate hydration

- Implemented the approved fix: initial hydration no longer mistakes local revision `0` for stale server state; opening video performs a deduplicated current-candidate GET before exposing generation.
- Mobile typecheck passed. Android cold restart/login resumed the existing confirmed story; candidate GET and authenticated preview GET both returned HTTP 200. Play advanced, Pause held, and Resume advanced playback. API logs showed no video-generation/activity POST; Modal inventory remained at 0 tasks for all 3 existing apps.
- The restored story still shows an activity-selection warning because its previous selection is not returned by the current run response and the review UI resets on hydration. This is recorded as follow-up outside Rev62 scope.
- Candidate remains a private technical preview (`safety/consistency NOT_RUN`, `product_playable=false`). No new inference, DB mutation, quota/payment operation, gate bypass, commit, or push.
- Evidence: `evidence/PARENT_AI_VIDEO_PLAYBACK_REV62_20261122/RUN_REPORT.md` and Android screenshots.
