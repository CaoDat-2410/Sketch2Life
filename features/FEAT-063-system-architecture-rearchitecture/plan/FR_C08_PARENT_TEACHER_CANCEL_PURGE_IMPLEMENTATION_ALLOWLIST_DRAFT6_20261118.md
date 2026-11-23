# FR-C-08 Parent and Teacher cancel/delete lifecycle — implementation allowlist Draft 6

**Status: PROPOSED / DRAFT / NOT APPROVED / NOT LAUNCHED.**  
**Date:** 2026-11-18.  
**Purpose:** identify bounded candidate paths and verification ceilings for a later owner-reviewed implementation task. This is not an authorization to edit any listed path. Every selected path must be re-pinned at the approved implementation base. If CONV-1 is separately reviewed, approved, committed, and integrated first, re-pin after that commit; otherwise the owner must select another explicit base. The latest CONV-1 package is an unreviewed draft and is not a dependency.

## 1. Authority and scope

The adopted unsigned SRS is D-209's canonical working copy, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`. Earlier Rev60/Rev68 plans are historical. Deletion eligibility of FAILED and ABANDONED remains OPEN under D-209 Q-A. The associated Contract Draft 4 and `FR_C08_OWNER_QUESTIONS_20261118.md` record the current gaps.

M2 is closed with recorded debt and deviations. Its bounded cancel implementation and verification authority do not transfer. In particular, the OpenAPI P3 remains open, M2-AT-09 is deferred, and the cancel operation is absent from the client-facing projection. This allowlist does not authorize client integration.

The path classes below are **candidate scope only**. Before implementation, owner decisions, module contracts, any DTR/schema review, selected base branch, exact path subset, and a separate Task Approval and launch instruction are required. Re-pin every selected file and verify new-file absence at that base. If a required change falls outside these candidates, stop and request a reviewed allowlist revision.

## 2. Existing source candidates — E

All rows below were present in the root checkout during the R2 planning preflight. Their pins are observations at that base, not implementation-base pins. Do not edit a row unless the future approval selects it.

| Exact path | Bytes / SHA-256 at planning base | Candidate purpose and guard |
|---|---:|---|
| `backend/src/sketch2life/application/ports/parent_story_runs.py` | 6,601 / `6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4` | Story command/read boundary; only approved fields and existing domain states. |
| `backend/src/sketch2life/application/services/parent_story_runs.py` | 7,630 / `FED7AC29F02C34F19F093AF471017447F5E5FA3453D399E2A155067609958B14` | Coordinate only owner-approved Parent lifecycle operations. |
| `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | 7,889 / `1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749` | Approved request/read/error schemas only; no inferred state or receipt. |
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 69,989 / `5E33C076A4A13439AB0D02A8D8088D543D277758E78076D709E23CB386CFBDA8` | Story-owned transition, revision, lock, and replay behavior within an approved mapping. |
| `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | 14,626 / `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` | Align selected Parent endpoints with the approved contract; no route inferred from this row. |
| `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | 23,082 / `E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30` | Forward approved late-result outcomes to a lifecycle fence only after owner contract. |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | 3,743 / `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` | Compose only separately approved routes and profiles. |
| `backend/src/sketch2life/interfaces/http/app.py` | 74,569 / `1387A59354DCCED45A74872721E3BA9ECEDEDE8CC44DE43A1BF33CBEDDCCC439` | Apply approved error/correlation behavior only; re-pin after base selection. |
| `backend/src/sketch2life/application/ports/ai_jobs.py` | 19,923 / `ACC3E27EA6B3A70E3DE267E4BD892D97FACF02D2B9F994817771BED3F584B3E3` | Use a reviewed best-effort cancellation boundary without conflating job and run states. |
| `backend/src/sketch2life/domain/ai_jobs/model.py` | 17,113 / `512B604636C1A22E231AC3276D3E537AE0DE4D9BB6652CCB064FAB7314DB99` | Preserve the independent AI Job state model. |
| `backend/src/sketch2life/application/services/ai_jobs.py` | 72,962 / `15DCD532D56EFF811A7DE937938E8D5F942AC7B29CDE26043A3B572DB02E08AE` | Coordinate only an approved cancellation notice; no provider call is authorized here. |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | 37,723 / `07695F0E6817B1057A38482D2D869D871A77CE77594D170642C00EBC2709724A` | Persist only within existing approved mappings; stop if schema changes are required. |
| `backend/src/sketch2life/infrastructure/ai_jobs/worker.py` | 7,164 / `A54725329F8643FB0AF9D821F9861BE34980C3DA3E28E201203630EA691785F6` | Fence dispatch/acceptance only under a reviewed versioned cancellation contract. |
| `backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py` | 1,084 / `2B36FACBB1C08560BE258F1FF69B07354BCCB45D7672A33A86317E9D5E02EE5E` | Preserve an approved fence during existing reconciliation; add no state by analogy. |
| `backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py` | 707 / `7B2DC13CCFA94C5BD09BA7679AB4DFAB194AEE6B32D8AB651AAB92FBCECB6115` | Deliver only an approved durable notice using existing outbox semantics. |
| `backend/src/sketch2life/infrastructure/persistence/outbox.py` | 6,653 / `0C09BA3B69B1C2EC0D71133C6307BCBFC2902287B287DAF11E1AF8BA9DC9281B` | Reuse only a reviewed event contract; do not infer payload fields. |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | 28,152 / `515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666` | Read existing BE1 lifecycle mappings; no Parent-to-organization substitution or schema edit. |
| `backend/src/sketch2life/infrastructure/story_run_lite/tables.py` | 26,995 / `703018AE4BF81D51C565EFC4626ED07C973823E5FB582EF69DA7BB490923F034` | Use existing mapped Story references only; no DDL or invented constraints. |
| `backend/src/sketch2life/infrastructure/lesson_library/tables.py` | 16,009 / `FE43AD061B69D4D1B8191AB52705A72C59BAA42605AB9167F4AADF3EF74EFDAF` | Preserve successful sample claim; clear a pointer only if the approved mapping supports it. |
| `backend/src/sketch2life/infrastructure/lesson_library/service.py` | 91,447 / `F37DB928B3C7CA5115A537D9E82D740D4BF9B23F34C02A0CBEE3C30BB995255D` | Apply only an approved occurrence pointer change; never reopen a consumed sample slot. |
| `backend/src/sketch2life/application/video_playback.py` | 6,188 / `EEB251839FAA384E68824A4DD79EF55CE5FD553F5ED8FFA72B308082E0CD57A2` | Check approved lifecycle fence before new playback authorization. |
| `backend/src/sketch2life/application/ports/video_playback.py` | 3,436 / `7621F128D136853F3C9E815A6A70BE250D8D222865861F1F94E03F79023ABE79` | Express only a reviewed revocation check; do not invent token fields. |
| `backend/src/sketch2life/interfaces/http/routers/story_video.py` | 4,576 / `C7FEFFEAD0393444BC9CB8A518E471C0D6F64F3D33D3B540002CA1DC51F48F31` | Enforce approved current authorization on existing playback/download surfaces. |
| `backend/src/sketch2life/application/video_review_lifecycle.py` | 4,386 / `E5A1A17C3D9580FDABF16E55864C18D10C67A6A03A54BA0CD34980691E0514E4` | Fence late outcomes without changing public StoryRun states. |
| `backend/src/sketch2life/application/ports/object_storage.py` | 1,060 / `CEC4214DDF3488D2C996368813B2B74D24C525ED86371E70D89F8AA9FA6EC9A4` | Use byte deletion only after Core ownership/reference closure is approved. |
| `backend/src/sketch2life/infrastructure/storage/s3_compatible.py` | 3,568 / `43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B` | Implement through existing storage adapter only after Core contract approval; no provider action. |

## 3. Migration scope

**No migration is E or N.** No migration graph, applied revision, or database state was inspected. Seven migration files were read-only frozen references in the predecessor allowlist; their current pins are in `tmp/frc08-wave1/PIN_AUDIT.md`.

If an owner-approved design requires a typed Parent-scope request, durable lifecycle checkpoint, audit fields, reference/ownership field, retention field, constraint, or new state absent from the current mapping, stop before implementation. First obtain a DTR/schema review and a separate exact migration plan and approval. Do not add DDL or run Alembic under this proposal.

## 4. Test scope

Existing test candidates, if a future approval selects the related behavior:

| Exact path | Bytes / SHA-256 at planning base | Conditional boundary |
|---|---:|---|
| `backend/tests/contract/test_app_composition.py` | 13,755 / `E18FA7478B0C7CB0D7369D3089CB07F139F7AE2670C7865AC4098480D61505B2` | Change only for the approved lifecycle router composition; preserve unrelated composition coverage. |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 23,667 / `B7CF9F8CB6E05D3E584E6D95FBC9D221441448C530A2F0A596754ABB1AAB0CF0` | Use only after the separate OpenAPI P3 is dispositioned; no mapper repair in FR-C-08. |

Existing cancellation tests are frozen regression evidence, not approved edit targets: `backend/tests/contract/test_parent_story_run_cancel_route.py` (3,601 / `98B4522D441F223F4BC6A17256982B4E3E9484D7EE1692A753162DDBF17CBBDE`), `backend/tests/unit/test_parent_story_run_cancel_repository.py` (10,111 / `A7CE542F352E9E51A0C5B32444240E6A84866C7452293BFBE15EB38E02689D9E`), and `backend/tests/contract/test_parent_ai_late_result_guards.py` (3,467 / `7C9EF0E89B77E1566A33C386854174A56E9BABB88732A94BDB499898D42D2BEC`).

New-file candidates, all **ABSENT** at this planning observation; recheck absence at the implementation base:

| N path | Purpose if later approved |
|---|---|
| `backend/src/sketch2life/application/ports/story_run_lifecycle.py` | Story lifecycle boundary only if selected by the reviewed architecture. |
| `backend/src/sketch2life/application/services/story_run_lifecycle.py` | Coordinator for approved state/receipt sequencing; no inferred route or state. |
| `backend/src/sketch2life/application/services/story_run_purge_worker.py` | Purge/retry worker only after owner contracts and durable phase mapping are resolved. |
| `backend/tests/contract/test_parent_story_lifecycle_contract.py` | Contract tests for the exact approved lifecycle API. |
| `backend/tests/unit/test_parent_story_lifecycle_service.py` | Fake-port sequencing, authorization, and failure tests. |
| `backend/tests/unit/test_parent_story_lifecycle_repository.py` | Receipt, revision, concurrency, and fence tests if this boundary is selected. |
| `backend/tests/unit/test_parent_story_purge_worker.py` | Retry, shared-reference, and restart tests with owner fakes. |
| `backend/tests/integration/test_parent_story_lifecycle_synthetic.py` | Isolated synthetic integration only after separate disposable-database approval. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_REPORT_20261118.md` | Evidence report for a separately approved implementation run. |

Any additional test path is outside this proposal. A new schema or migration test is not authorized by the N list.

## 5. Documentation and evidence scope

These are candidate documentation paths for a later, separately approved update after evidence exists. This R2 task does not edit them:

| Exact path | Bytes / SHA-256 at planning base | Boundary |
|---|---:|---|
| `docs/context/PROJECT_CONTEXT.md` | 84,270 / `EDF3F54CED54CA0C6E8E9F0E526B76B1B24AB4DA84C7FEF3C93A3FE3A50C2E9D` | Append verified outcome and links only; do not assert runtime or approval absent evidence. |
| `docs/context/SOURCE_REGISTER.md` | 117,896 / `6ED2B13BF01C273E75FD834AA458B3260D193B3C06D3FBD8C8D0B045AB8C6363` | Add verified source/evidence records only. |
| `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | 125,587 / `C77C9CF3664B1885C2CB945F6D7343FABC26B814BA00EFD2F29738A06A17EF1A` | Record only approved and evidenced status. |
| `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md` | 71,808 / `F3F3581E50914A409E5E48915AF75D4E04133D1B1896927A0D7E4454004E022F` | Add exact, verified artifact/source pointers only. |
| `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md` | 126,250 / `9F5D706D07424BEC2ADB19A24D36A643DE1D183916AF5E6701B42DE7A6C25938` | Update only after a separately approved review/implementation event. |
| `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` | 9,248 / `689023BE3130F156CC6C458242DD11F68FDFBC9CC19E0AAC7174B21F9BBB34E5` | Conditional evidence only if a separately approved route inventory requires change; otherwise excluded. |

## 6. Frozen read-only references — H

All paths not selected under a later approval remain frozen. The following are especially relevant and were read-only in this planning pass:

| Exact path | Bytes / SHA-256 at planning base | Reason frozen |
|---|---:|---|
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 / `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` | Canonical unsigned working SRS; no edit. |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` | 171,609 / `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2` | Companion model; schema changes require separate review. |
| `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 233,645 / `7EA82DB5D94D0B0457091E6F9D1E568E50BABB77CAC2533E18F1467791EF4C2D` | D-209 through D-213 provenance; no append in this task. |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 513,391 / `C718F2D9FB9268A8515F60F893EF2D5072AC1C352419F0AF96584359504CE378` | Contains M2 closure; no FR-C-08 approval. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 / `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | Historical S2 execution evidence; not an FR-C-08 approval. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S3_CLOSEOUT_REPORT_20261118.md` | 15,704 / `CECC65FEF458BF1A0D6664C851BB3F43FF6E585FEC1D4B93F5D9D08E87BCDA84` | Snapshot predating owner acceptance; not authority for current M2 status. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S3_LIMITATION_LEDGER_20261118.md` | 17,463 / `A82335ECBB3AE1BD600956FEFD75D0885CFE7EF095BA9BBD64303DBD91B5CF4A` | Records M2 debt; no lifecycle implementation permission. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT4_20261115.md` | 20,897 / `BC268E2354AED6FDC142CCD58BFDF89BACF6585F15B7ED75C8AE7C4C41ED9B70` | Historical input; not the adopted SRS. |
| `backend/src/sketch2life/application/ports/core_foundation.py` | 5,512 / `2F6F55A0C576AF78DCB24219254DE6DE3C9063C4A868D0B27F2D91356268FB13` | Read-only: no current Core reference-closure/delete operation. |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py` | 24,471 / `AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94` | Read-only: metadata operations do not prove lifecycle closure. |
| `backend/src/sketch2life/infrastructure/persistence/core_models.py` | 11,578 / `47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A` | Read-only: no approved physical Parent lifecycle mapping. |
| `backend/src/sketch2life/infrastructure/persistence/be1_parent_role_adapter.py` | 1,507 / `1B83B95341D7AD98360CC98AF640CFAF5750A21FCE4CE971F0EE2D1DF66795E1` | Read-only; production current-assignment resolver remains unproven. |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,379,096 / `35801B20DC67630B9AAEEFDD46F82886CD91F34990BA2CCE6C2B3E67B6A989B7` | M2 OpenAPI P3 is separately scoped. |

The full input and source pin audit, including all seven frozen migration references and historical review evidence, is in `tmp/frc08-wave1/PIN_AUDIT.md`.

## 7. Future verification ceilings — proposed, not authorized

Only a later exact approval and launch instruction can authorize commands. Proposed ceilings for that later task:

1. At most one owner-run in-process TestClient contract invocation for the exact approved contract/composition test paths.
2. At most one owner-run unit-test invocation for the exact approved lifecycle service/repository/worker tests.
3. At most one owner-run synthetic database integration invocation, only after a disposable database, migration plan, and isolation evidence are separately approved.
4. No live application server, external network, provider, Modal, or real-data operation. The current sandbox can hang on loopback sockets; TestClient and any database-bound command must run only in the owner-approved environment, not this planning sandbox.
5. Any OpenAPI generation, typecheck, lint, validator, migration, or additional test command needs its own explicit ceiling and approval. No existing M2 ceiling transfers.

## 8. Acceptance and stop rules for later approval

Acceptance must demonstrate the criteria in Lifecycle Contract Draft 4: owner-approved state eligibility; current Parent/Teacher authorization; acceptance-time lock and access fence; idempotent typed request/receipt; worker and late-result fencing; owner-owned purge/retry and positive shared-reference proof; truthful pending-to-DELETED transition; preserved quota/sample claim; and approved metadata-only audit/retention. OpenAPI/static composition evidence must remain separate from runtime evidence.

Stop before code if Q-A or any required owner contract remains unresolved; if a required physical mapping, state, migration, or path is absent from the approved scope; if CONV-1 status or implementation base is unclear; if existing M2 changes collide; if a current file differs from its re-pinned base; or if any verification requires an unapproved command or real data. Do not infer ownership, `organization_id`, a route, status, purge proof, or a migration.

**No implementation, formal approval, or launch is granted by this draft.**
