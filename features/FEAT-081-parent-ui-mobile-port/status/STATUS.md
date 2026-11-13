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
