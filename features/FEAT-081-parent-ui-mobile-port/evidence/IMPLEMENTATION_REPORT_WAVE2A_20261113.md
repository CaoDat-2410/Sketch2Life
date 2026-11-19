# FEAT-081 Wave 2A implementation report

**Status:** Implementation complete; awaiting coordinator post-run. Wave 2B is NOT LAUNCHED.
**Date:** 2026-11-13
**Branch / HEAD:** `feature/fe-mobile-remediation` / `3c75b10d602d6262dc428706c8bdae92c7a0a8ff` before edits.
**Authority:** Addendum 5 of `approvals/TASK_APPROVAL.md`; approved plan `plan/PLAN_REVISION_3.md` (34,224 bytes, SHA-256 `73A5873DB1F37366A7A4C69C97ED2F4A81B565C3777E10C3C0F63341FF41DA1E`).

## Scope and review steering

Wave 2A changed only its seven approved E paths and added its two approved N tests. No 2B, R, or H code path was edited. The only additional documentation path is this report, authorized by the owner in Addendum 5. The existing `ParentApiPort` methods and legacy profile and `StoryRun` types remain available with their original signatures; the three `authorization_*` fields remain in `domain/types.ts`. New route contracts use separately named V1 methods and types.

The independent review at `tmp/fe081-wave2/REVIEW_R2_ROUND1_20261113.md` returned **NEEDS REVISION**. Person 2 accepted the findings and directed the corrections recorded in the command ledger. The 2B review items (offline UI coverage, the photo/policy gate before `ContextScreen`, and stale snapshot wording) remain outside this launch and require the separate 2B launch addendum.

## What changed

- Added V1 profile list/read/create/patch/deletion-request operations. List pagination uses `URLSearchParams`; profile mutations require a caller-supplied action identity that is retained for retries. `GET` by ID returns active or `DELETE_PENDING`; a stale patch performs one GET-by-ID refresh and returns a `STALE` result for adult review without retrying the patch.
- Added V1 StoryRun read/create and context, subject, script, and story-revision operations. The story-revision command keeps its existing `/api/parent/v1/ai/story-runs/{run_id}/story-revisions` route and takes a retained 1–200 character action key. StoryRun creation requires a nested lesson-version pin and sends only profile ID, topic, adult-confirmed idea, and pin. It sends no image, consent/policy field, profile-revision ID, or `context_confirmed`. A separate use case confirms the server-returned context revision and snapshot hash. `ACTIVE_RUN_EXISTS` triggers one active-run read, never a second create.
- Added action-key generation and explicit key inputs: profile actions validate 1–128 printable ASCII characters; StoryRun and confirmations validate 1–256 characters; story revisions validate 1–200. A retry reuses the same supplied key; a new action supplies a new key. There is no automatic retry for an unknown Modal outcome. `drawing-understandings` has no added key, and `activity-suggestions` is not called.
- Added safe error metadata for status, code, request/correlation IDs, retry metadata, current version, and allowlisted field errors. User messages are mapped locally; raw server messages and unrecognized field names are discarded. The parser accepts top-level envelopes and retains defensive support for nested `detail` errors. The merged integration `app.py` error shape is **NOT VERIFIED**; nested detail is not the documented StoryRun contract.
- Added fake-fetch tests for route/body/query/header contracts, retry identity, pending deletion and GET-by-ID reconciliation, safe error parsing, and the no-key drawing-understanding path. Added fake-port tests for the required lesson pin, no-photo pre-drawing create, context confirmation, and active-run recovery. Test fixtures are synthetic.

The route exists in the integration route inventory. Whether usable lesson data exists on the owner's scratch service is **NOT VERIFIED**.

## 2A file pins

The “before” pins below are the 2A E rows in the approved R2 plan, rechecked during launch preflight. The two N test paths were absent at preflight.

| Mode | Path | Before bytes / SHA-256 | After bytes / SHA-256 |
|---|---|---|---|
| E | `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` | 16,805 / `B448B9F13A153D2F90E1BAD6A284488117B4458223C1239FC2865F850438B918` | 25,554 / `4C901AE396BB7DC51BF22FC95751206244B036942B0E8B0A4B07C72322E1814F` |
| E | `apps/ui-mobile/src/parent/application/ports/ParentPorts.ts` | 6,318 / `52041644201401DB3CEDCBC7E9C34B7954B715FA80505990ACCB9897CC87D284` | 8,467 / `A2571978506A9F2FFADFE0C02B850D83D16D89FA4710764B41E5EBAD4B2D07C2` |
| E | `apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts` | 1,766 / `0635F3E3C3278C8582C071A57E18C0ACB3EA3A766BD6A89167C5DA6D36E6F73B` | 2,038 / `2F8DE48FB9B73F31FE6C6F5C3F40B960A979C9BD2BF88FCC5A02192F7CE6437E` |
| E | `apps/ui-mobile/src/parent/application/ParentApplicationError.ts` | 252 / `B62AC222CF5CDE6915ED23EE7052A82AA636BD1F1B7603E5D3E4413D0E7E4165` | 1,027 / `3087B87025511877F983BF0A9331E11DF110078F938354C87800E61CFF4BD2AF` |
| E | `apps/ui-mobile/src/parent/domain/types.ts` | 7,338 / `76293E25E2F3157A7EC4053703CED9F25D9213DB0347FF2B59DDE44FFD18AD24` | 10,040 / `43FDABCD651F08B823D215A2306743402DC0C1B8CEBD4F2AA32AFEA93B3BD107` |
| E | `apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts` | 1,472 / `9035F49E23B8077131B1EC6AB8386FF8833CB5E6908AD7C595E79219C2E8DED1` | 2,994 / `C3A88AB853C6EE96882ABF950EAC76032E68D97D6E52D7A42EF63C869E99CCC2` |
| E | `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts` | 3,563 / `F24500EF6F17C105F723B9B6EAC83924A66056C3F9608E418EB546BE4050E464` | 6,540 / `3383C989A65580C6549824761B405F26BD5CB1FAF6EA5DA965F882C067BD2DA3` |
| N | `apps/ui-mobile/tests/parentApiI2Contract.test.ts` | Absent | 17,286 / `525C69755D752FA19157FCA3499E384B3EA93570C396057C0E55674E8409CE00` |
| N | `apps/ui-mobile/tests/parentLearningI2.test.ts` | Absent | 4,773 / `A11EE5EFA7182CB9073A1757A7C4A2AC7C97195E6F72CDED06968845D7262C04` |

## H pin recheck

All nine shared H rows were re-hashed after implementation and still match the R2 pins:

| Path | Bytes | SHA-256 |
|---|---:|---|
| `apps/ui-mobile/package.json` | 2,081 | `AC8C5AB17D61B4DD126D28D9918CB4E4EB5C40EEFD3B4C965D9597294B9CD9FF` |
| `pnpm-lock.yaml` | 470,780 | `5D778524730134CAFE360564408CBF45030B476C99A69CCD32897BAB55559A72` |
| `apps/ui-mobile/app.json` | 1,560 | `9489E92A02306F6F0C1F575F3FF1C1FB9331BCB58ED2FD52E49880781F2D0651` |
| `apps/ui-mobile/app.config.js` | 1,578 | `8D78BFAE71EF705299603BD4F6FBE74388756BBEEE93A1C6F1C4D99341ED1F43` |
| `apps/ui-mobile/metro.config.js` | 2,145 | `068C704CC6F14F15178424B584DF4FD36169C221A57C534FD39D59C209E7B5A1` |
| `apps/ui-mobile/tsconfig.json` | 147 | `B16D29C183DA613864125B17F2C6EC4E19419EF3E47E7C207FD8E7622F941130` |
| `apps/ui-mobile/src/parent/presentation/components/ui.tsx` | 11,444 | `722636038EE8CBDFA36A90F6D102ABB4F69A43DC5B6848978EEC8795DFFDB773` |
| `apps/ui-mobile/src/parent/infrastructure/config.ts` | 1,049 | `F0C1E0198460E9A432E81D9E8724BCC35CD030CA8C411F2050503F1C87C0FF07` |
| `apps/ui-mobile/src/parent/infrastructure/auth/ParentAuth.ts` | 10,305 | `BBFEEF77C3CABD2632AFE7EE96D6996509C809BB8521FBD80326223961DD6077` |

## Baseline, commands, and acceptance

The owner-run baseline on bytes identical to commit `3c75b10d` remains the only completed Wave 2 test/typecheck invocation: `pnpm run test` reported 4 test files / 29 tests passed and `UI_COPY_AND_RECOVERY_VALID`; `pnpm run typecheck` had no diagnostics. The owner also reported `validate_harness`, `validate_repository_security`, `validate_architecture`, and `git diff --check` exit 0 at baseline. These baseline invocations are consumed; see `tmp/fe081-impl/COMMAND_LEDGER.md` for the command accounting and supplied log evidence. No post-2A command has been run.

| Criterion | Status | Evidence / remaining step |
|---|---|---|
| 2A-AC1 | NOT RUN | Fake-fetch coverage is written; coordinator must execute the post-2A test suite. |
| 2A-AC2 | NOT RUN | Fake error/deletion coverage is written; coordinator must execute the post-2A test suite. |
| 2A-AC3 | NOT RUN | Fake-port lesson/context coverage is written; coordinator must execute the post-2A test suite. |
| 2A-AC4 | OWNER-COORDINATOR RUN PENDING | Post-2A `pnpm run test` and `pnpm run typecheck` remain to be run outside the sandbox. |
| 2A-AC5 | VERIFIED BY SOURCE/PIN REVIEW | Git path review shows only the seven E and two N code paths changed; all nine H pins match. The owner-authorized report and existing Wave 2 governance records are the only documentation paths in scope. |

Command accounting after this implementation: tests 1/3 consumed by baseline, post-2A pending (2/3), post-2B pending (3/3); typecheck the same. Each validator and `git diff --check` is 1/2 consumed by baseline; one final post-2B invocation remains. Codex ran no tests, typecheck, validators, `git diff --check`, install, Android/ADB/Gradle/emulator, or network command.

## Owner acceptance boundary

This report does not claim runtime verification against the integration backend or scratch database. The merged `app.py` error shape and usable scratch-service lesson data remain **NOT VERIFIED**. 2B remains **NOT LAUNCHED**. No code was staged, committed, or pushed.

`OWNER_MODAL_CALL_APPROVED=NO` remains in effect. This implementation authorizes no Modal call; the owner-run path stops before `drawing-understandings` unless the owner records separate bounded approval.

## Coordinator post-run review and bounded 2A rework — 2026-11-13

This update supersedes the earlier report statements that the post-2A run was pending or not run. The coordinator completed test invocation 2/4 and typecheck invocation 2/4 from `apps/ui-mobile`; both are consumed.

### Coordinator result and read-only diagnosis

Logs: `tmp/fe081-impl/coordinator_post2A_20261113T013247/`.

- `pnpm run test` (run 2/4): 1 failed and 43 passed (44 tests across 6 files), plus 1 unhandled-rejection error. The 29 existing tests passed. Test stdout: 1,254 bytes / SHA-256 `73CEF8FD2CEAA89F694F476DE1AFAB3D4EC9556D1C6FD23B4A7DD99D633D2FE8`.
- `pnpm run typecheck` (run 2/4): 1 error. Typecheck stdout: 460 bytes / SHA-256 `E82F8D4EA4E79C715E3CEC72027BA21D49DFAB72B1490A4352313092675D7071`.

The lesson-pin guard already rejected an incomplete pin. `createRunBeforeDrawingV1` is async, so the guard throws as a rejected Promise; the test used synchronous `toThrow`, leaving that rejection unhandled. The test now awaits `.rejects.toThrow` and checks that no run-create API call occurs for both an absent pin and an incomplete pin. The separate type error arose because the active-run endpoint can return `story_run: null`, while create/read use the non-null `ParentStoryRunEnvelopeV1`. A new `ParentActiveStoryRunEnvelopeV1` now represents only the nullable active endpoint. The active-run use case and application boundary use that type; create/read remain non-null. Conflict recovery returns a non-null envelope only when the active response contains a run, and otherwise rethrows the original `ACTIVE_RUN_EXISTS` error. Tests now cover the null endpoint response and the null recovery branch.

### Final 2A code-path pins after rework

| Mode | Path | Bytes | SHA-256 |
|---|---|---:|---|
| E | `apps/ui-mobile/src/parent/infrastructure/http/ParentApi.ts` | 25,559 | `182EBB83A8A9A284444FAADE68740C5DD50CDD0F387393A4577A2C7AD626F7DE` |
| E | `apps/ui-mobile/src/parent/application/ports/ParentPorts.ts` | 8,472 | `62CDC570BEEE074D1BD4558A5567E37CD2911DC7041D4689F231CC2884182551` |
| E | `apps/ui-mobile/src/parent/application/ports/ParentApplicationModule.ts` | 2,164 | `0373643C8C92C9EA6D144C22F27202D8A09163FB03D369A786982E9413CBB9A3` |
| E | `apps/ui-mobile/src/parent/application/ParentApplicationError.ts` | 1,027 | `3087B87025511877F983BF0A9331E11DF110078F938354C87800E61CFF4BD2AF` |
| E | `apps/ui-mobile/src/parent/domain/types.ts` | 10,152 | `990FA43EF6E04874FD72E9E62AC7CCAD9332F687BFE92A64586A87A7010A0240` |
| E | `apps/ui-mobile/src/parent/application/use-cases/ParentProfileUseCases.ts` | 2,994 | `C3A88AB853C6EE96882ABF950EAC76032E68D97D6E52D7A42EF63C869E99CCC2` |
| E | `apps/ui-mobile/src/parent/application/use-cases/ParentLearningUseCases.ts` | 6,766 | `8812D4AB0DAB6DB7C35CDA9F14EEEB953201AC0157DDE1C4C2216A8FD40C43AE` |
| N | `apps/ui-mobile/tests/parentApiI2Contract.test.ts` | 17,370 | `C7FC2FB9421AF32553EDABB4F633547C842A825161FA41AB524CA8DCAC541075` |
| N | `apps/ui-mobile/tests/parentLearningI2.test.ts` | 5,841 | `E92C927657EE1AF2AD3152DEEE6519AF56B866BDECCDB00E7A7BD5BC03884892` |

The nine H pins remain unchanged and were rechecked after the source correction. The accepted 2A manifest is unchanged. Neither `ParentApplicationError.ts` nor `ParentProfileUseCases.ts` required rework edits; their approved implementation pins remain as shown above.

### Acceptance and command status after rework

| Criterion | Status | Evidence / next step |
|---|---|---|
| 2A-AC1 | NOT VERIFIED | Fake-fetch tests remain in scope; coordinator rerun is pending. |
| 2A-AC2 | NOT VERIFIED | Error and deletion tests remain in scope; coordinator rerun is pending. |
| 2A-AC3 | NOT VERIFIED | Lesson-pin and nullable active-run tests were corrected/added; coordinator rerun is pending. |
| 2A-AC4 | COORDINATOR-RUN PENDING | The prior post-2A run failed; one additional test and typecheck run is authorized for this rework. |
| 2A-AC5 | VERIFIED BY SOURCE/PIN REVIEW | Only approved 2A paths changed; all nine H pins match. |

Addendum 6 records the owner-authorized ceiling increase. Test and typecheck invocation 1/4 is the owner baseline, invocation 2/4 is the failed post-2A run above, invocation 3/4 is reserved for the coordinator rework run, and invocation 4/4 remains the single post-2B run. Each validator and `git diff --check` remains 1/2 consumed by the owner baseline, with the single post-2B run remaining. Codex ran no tests, typecheck, validators, `git diff --check`, install, Android/ADB/Gradle/emulator, or network command during this rework. Wave 2A remains unaccepted pending the coordinator rerun; Wave 2B remains NOT LAUNCHED.