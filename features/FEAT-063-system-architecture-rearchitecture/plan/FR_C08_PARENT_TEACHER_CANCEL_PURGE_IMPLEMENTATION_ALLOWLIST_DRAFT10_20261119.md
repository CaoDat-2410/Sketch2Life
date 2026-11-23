# FR-C-08 Parent StoryRun lifecycle — implementation allowlist Draft 10

**Status: PROPOSED / DRAFT / NOT APPROVED / NOT LAUNCHED.**
**Date:** 2026-11-19.
**Purpose:** Candidate paths for a later exact, owner-approved Parent-only implementation task. This is not authorization to edit any path or run any command.

## 1. Authority, scope, and provisional base

The canonical unsigned SRS is the D-209 working copy at features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, 701,157 bytes, SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5. D-214 is the current owner planning disposition. Older SRS copies are historical only.

D-214 selects a Parent-only first implementation scope while keeping the lifecycle design shared. The Teacher authorization adapter is deferred. This is a documented scope limit against SRS language that names Parent and Teacher.

The provisional code base is local branch feature/feat066-conv1 at commit 2dddc6076c793b44cbcd5c0fa3e02a4ccc9902df, parent 08439b22fc3c1f34786a3f45f34530075a3914e0. These pins are from git show at that commit, not from a working-tree file. D-214 requires owner confirmation of CONV-1 and says the exact commit will be named when the base is fixed. Recompute every path pin if the owner selects a later commit.

D-214 itself is a working-tree change in the root checkout and is not present in the DECISIONS.md blob at provisional base 2dddc607. The base row for that file is historical through the parent decisions; the current D-214 working-tree bytes are separately pinned in PIN_AUDIT_R6.md, a local, git-ignored scratch register that is not a durable repository record (the same bytes are also given in Lifecycle Contract Draft 8). Resolve and pin the final governance-record relationship before any implementation approval.

At commit 2dddc607, CONV-1 decision D-066-71, its approval entry, and its implementation evidence are recorded on the local branch. They are not represented by root-checkout records. This statement is grounded in D-214 and local read-only branch inspection; it does not approve CONV-1 or choose an implementation integration action.

## 2. CONV-1 path overlaps

The overlap was recomputed from git diff --name-only 08439b22 2dddc607 and intersected with this draft's E and H path sets; it now lists eight paths (two E and six H).

| Exact path | Class | Evidence and boundary |
|---|---|---|
| backend/src/sketch2life/interfaces/http/app.py | E | Exact edit-path overlap; re-derive after the owner fixes the base. |
| backend/tests/contract/test_openapi_contract_catalog.py | E | Exact edit-path overlap; re-derive after the owner fixes the base. |
| backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py | H | Frozen OpenAPI reference changed by CONV-1; re-pin after the owner fixes the base. |
| backend/src/sketch2life/interfaces/http/routers/be1_common.py | H | Frozen assignment-source reference changed by CONV-1; re-pin after the owner fixes the base. |
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py | H | Frozen assignment-source reference changed by CONV-1; re-pin after the owner fixes the base. |
| backend/src/sketch2life/interfaces/http/api_conventions.py | H | Added by CONV-1 and absent at HEAD; frozen convention reference; its pin is the base blob. |
| backend/src/sketch2life/interfaces/http/error_envelope.py | H | Added by CONV-1 and absent at HEAD; frozen error-body reference; its pin is the base blob. |
| backend/src/sketch2life/interfaces/http/middleware/bounded_image_upload.py | H | Frozen upload-middleware reference modified by CONV-1; re-pin after the owner fixes the base. |

Draft 6 listed four model/table sources as E. Draft 7 moved them to H, and Draft 8 kept them H. Draft 8 added be1_common.py, be1_registry.py, openapi_contract_amendments.py, and openapi_srs_v22.py as H references. Draft 10 adds api_conventions.py, error_envelope.py, and bounded_image_upload.py as H references, because CONV-1 adds or modifies them and the E row for app.py (error and correlation behavior) depends on them.

## 3. E — existing edit candidates

Each size and digest below was recomputed from git show at provisional base 2dddc6076c793b44cbcd5c0fa3e02a4ccc9902df. These are candidates only; future approval must select an exact subset and re-pin it.

### E source and test candidates

| Exact path | Bytes / SHA-256 from provisional base | Purpose and boundary |
|---|---:|---|
| backend/src/sketch2life/application/ports/parent_story_runs.py | 6,601 / 6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4 | Story command/read boundary; only approved fields and existing domain states. |
| backend/src/sketch2life/application/services/parent_story_runs.py | 7,630 / FED7AC29F02C34F19F093AF471017447F5E5FA3453D399E2A155067609958B14 | Coordinate only owner-approved Parent lifecycle operations. |
| backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py | 69,989 / 5E33C076A4A13439AB0D02A8D8088D543D277758E78076D709E23CB386CFBDA8 | Story-owned transition, revision, lock, and replay behavior within an approved mapping. |
| backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py | 14,626 / A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD | Align selected Parent endpoints with the approved contract; no route inferred from this row. |
| backend/src/sketch2life/interfaces/http/routers/parent_ai.py | 23,082 / E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30 | Forward approved late-result outcomes to a lifecycle fence only after owner contract. |
| backend/src/sketch2life/interfaces/http/router_composition.py | 3,743 / 2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463 | Compose only separately approved routes and profiles. |
| backend/src/sketch2life/interfaces/http/app.py | 70,828 / 43483014A1D40E05668D4CB0994E136C355D2920E99E7B8224121D2DEC604728 | Apply approved error/correlation behavior only; re-pin after base selection. |
| backend/src/sketch2life/application/ports/ai_jobs.py | 19,923 / ACC3E27EA6B3A70E3DE267E4BD892D97FACF02D2B9F994817771BED3F584B3E3 | Use a reviewed best-effort cancellation boundary without conflating job and run states. |
| backend/src/sketch2life/application/services/ai_jobs.py | 72,962 / 15DCD532D56EFF811A7DE937938E8D5F942AC7B29CDE26043A3B572DB02E08AE | Coordinate only an approved cancellation notice; no provider call is authorized here. |
| backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py | 37,723 / 07695F0E6817B1057A38482D2D869D871A77CE77594D170642C00EBC2709724A | Persist only within existing approved mappings; stop if schema changes are required. |
| backend/src/sketch2life/infrastructure/ai_jobs/worker.py | 7,164 / A54725329F8643FB0AF9D821F9861BE34980C3DA3E28E201203630EA691785F6 | Fence dispatch/acceptance only under a reviewed versioned cancellation contract. |
| backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py | 1,084 / 2B36FACBB1C08560BE258F1FF69B07354BCCB45D7672A33A86317E9D5E02EE5E | Preserve an approved fence during existing reconciliation; add no state by analogy. |
| backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py | 707 / 7B2DC13CCFA94C5BD09BA7679AB4DFAB194AEE6B32D8AB651AAB92FBCECB6115 | Deliver only an approved durable notice using existing outbox semantics. |
| backend/src/sketch2life/infrastructure/persistence/outbox.py | 6,653 / 0C09BA3B69B1C2EC0D71133C6307BCBFC2902287B287DAF11E1AF8BA9DC9281B | Reuse only a reviewed event contract; do not infer payload fields. |
| backend/src/sketch2life/application/video_playback.py | 6,188 / EEB251839FAA384E68824A4DD79EF55CE5FD553F5ED8FFA72B308082E0CD57A2 | Check approved lifecycle fence before new playback authorization. |
| backend/src/sketch2life/application/ports/video_playback.py | 3,436 / 7621F128D136853F3C9E815A6A70BE250D8D222865861F1F94E03F79023ABE79 | Express only a reviewed revocation check; do not invent token fields. |
| backend/src/sketch2life/interfaces/http/routers/story_video.py | 4,576 / C7FEFFEAD0393444BC9CB8A518E471C0D6F64F3D33D3B540002CA1DC51F48F31 | Enforce approved current authorization on existing playback/download surfaces. |
| backend/src/sketch2life/application/video_review_lifecycle.py | 4,386 / E5A1A17C3D9580FDABF16E55864C18D10C67A6A03A54BA0CD34980691E0514E4 | Fence late outcomes without changing public StoryRun states. |
| backend/src/sketch2life/application/ports/object_storage.py | 1,060 / CEC4214DDF3488D2C996368813B2B74D24C525ED86371E70D89F8AA9FA6EC9A4 | Use byte deletion only after Core ownership/reference closure is approved. |
| backend/src/sketch2life/infrastructure/storage/s3_compatible.py | 3,568 / 43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B | Implement through existing storage adapter only after Core contract approval; no provider action. |
| backend/tests/contract/test_app_composition.py | 13,755 / E18FA7478B0C7CB0D7369D3089CB07F139F7AE2670C7865AC4098480D61505B2 | Change only for the approved lifecycle router composition; preserve unrelated composition coverage. |
| backend/tests/contract/test_openapi_contract_catalog.py | 24,100 / 2B89C3E9CB65BE16E8C4F463023CBF3B3B63A4E89A92BEECE95963242F0F29B4 | Use only after the separate OpenAPI P3 is dispositioned; no mapper repair in FR-C-08. |

## 4. D — conditional documentation candidates

These documentation paths are candidate updates only after a separately approved implementation result exists. No governance, approval, SRS, context, or status update is authorized by this draft.

### D documentation candidates

| Exact path | Bytes / SHA-256 from provisional base | Purpose and boundary |
|---|---:|---|
| docs/context/PROJECT_CONTEXT.md | 84,270 / EDF3F54CED54CA0C6E8E9F0E526B76B1B24AB4DA84C7FEF3C93A3FE3A50C2E9D | Append verified outcome and links only; do not assert runtime or approval absent evidence. |
| docs/context/SOURCE_REGISTER.md | 117,896 / 6ED2B13BF01C273E75FD834AA458B3260D193B3C06D3FBD8C8D0B045AB8C6363 | Add verified source/evidence records only. |
| features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md | 125,587 / C77C9CF3664B1885C2CB945F6D7343FABC26B814BA00EFD2F29738A06A17EF1A | Record only approved and evidenced status. |
| features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md | 71,808 / F3F3581E50914A409E5E48915AF75D4E04133D1B1896927A0D7E4454004E022F | Add exact, verified artifact/source pointers only. |
| features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md | 126,250 / 9F5D706D07424BEC2ADB19A24D36A643DE1D183916AF5E6701B42DE7A6C25938 | Update only after a separately approved review/implementation event. |
| features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json | 9,248 / 689023BE3130F156CC6C458242DD11F68FDFBC9CC19E0AAC7174B21F9BBB34E5 | Conditional evidence only if a separately approved route inventory requires change; otherwise excluded. |

## 5. H — frozen references

H paths are read-only. They cannot be edited under this allowlist.

### H frozen paths

| Exact path | Bytes / SHA-256 from provisional base | Purpose and boundary |
|---|---:|---|
| backend/src/sketch2life/infrastructure/lesson_library/service.py | 91,447 / F37DB928B3C7CA5115A537D9E82D740D4BF9B23F34C02A0CBEE3C30BB995255D | Frozen Teacher sample-claim source; no edits in the Parent-only first scope. |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md | 701,157 / B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5 | Canonical unsigned working SRS; no edit. |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md | 171,609 / 7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2 | Companion model; schema changes require separate review. |
| features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md | 233,645 / 7EA82DB5D94D0B0457091E6F9D1E568E50BABB77CAC2533E18F1467791EF4C2D | D-209 through D-213 provenance; no append in this task. |
| features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md | 513,391 / C718F2D9FB9268A8515F60F893EF2D5072AC1C352419F0AF96584359504CE378 | Contains the M2 closure entry at lines 3243-3247; no FR-C-08 approval. |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md | 25,879 / F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55 | Historical S2 execution evidence; not an FR-C-08 approval. |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S3_CLOSEOUT_REPORT_20261118.md | 15,704 / CECC65FEF458BF1A0D6664C851BB3F43FF6E585FEC1D4B93F5D9D08E87BCDA84 | Snapshot predating owner acceptance; not authority for current M2 status. |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S3_LIMITATION_LEDGER_20261118.md | 17,463 / A82335ECBB3AE1BD600956FEFD75D0885CFE7EF095BA9BBD64303DBD91B5CF4A | Records M2 debt; no lifecycle implementation permission. |
| features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT4_20261115.md | 20,897 / BC268E2354AED6FDC142CCD58BFDF89BACF6585F15B7ED75C8AE7C4C41ED9B70 | Historical input; not the adopted SRS. |
| backend/src/sketch2life/application/ports/core_foundation.py | 5,512 / 2F6F55A0C576AF78DCB24219254DE6DE3C9063C4A868D0B27F2D91356268FB13 | Read-only: no current Core reference-closure/delete operation. |
| backend/src/sketch2life/infrastructure/persistence/core_store.py | 24,471 / AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94 | Read-only: metadata operations do not prove lifecycle closure. |
| backend/src/sketch2life/infrastructure/persistence/core_models.py | 11,578 / 47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A | Read-only: no approved physical Parent lifecycle mapping. |
| backend/src/sketch2life/infrastructure/persistence/be1_parent_role_adapter.py | 1,507 / 1B83B95341D7AD98360CC98AF640CFAF5750A21FCE4CE971F0EE2D1DF66795E1 | Read-only Parent-role lookup only; it is not a Teacher assignment/version resolver. |
| backend/src/sketch2life/interfaces/http/openapi_contract.py | 1,379,096 / 35801B20DC67630B9AAEEFDD46F82886CD91F34990BA2CCE6C2B3E67B6A989B7 | M2 OpenAPI P3 is separately scoped. |
| backend/src/sketch2life/infrastructure/persistence/be1_models.py | 28,152 / 515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666 | Read-only BE1 model; current organization_id mapping cannot be used as fabricated Parent scope. |
| backend/src/sketch2life/infrastructure/story_run_lite/tables.py | 26,995 / 703018AE4BF81D51C565EFC4626ED07C973823E5FB582EF69DA7BB490923F034 | Read-only mapped Story tables; no DDL or inferred lifecycle column. |
| backend/src/sketch2life/infrastructure/lesson_library/tables.py | 16,009 / FE43AD061B69D4D1B8191AB52705A72C59BAA42605AB9167F4AADF3EF74EFDAF | Read-only Lesson schema; preserve successful sample claims. |
| backend/src/sketch2life/domain/ai_jobs/model.py | 17,113 / 512B604636C1A22E231AC3276D3E537AE0DEAE4D9BB6652CCB064FAB7314DB99 | Read-only AI Job domain state; independent from public StoryRun state. |
| backend/src/sketch2life/interfaces/http/routers/be1_common.py | 16,944 / 529CA7F569F61520DEBF8EE1220433C6DD1102F71AD0E15352C9C96359D32A40 | Read-only unversioned active-assignment check; CONV-1 changes this file. Re-pin at the chosen base. |
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py | 20,567 / 080AD7C4298E720B3E759309419FC802B5934D05BEC282E85F9227425E628040 | Read-only wrapper/current-assignment route; CONV-1 changes this file. Re-pin at the chosen base. |
| backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py | 54,803 / 4267901AEC9D8F874F035B69FF63F54D965D8A3E4E56CEC739C5C7E019511D4F | Read-only OpenAPI amendments; CONV-1 changes this file. Route/projection changes require a separate allowlist revision. |
| backend/src/sketch2life/interfaces/http/openapi_srs_v22.py | 11,122 / 29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3 | Read-only OpenAPI source; route/projection changes require a separate allowlist revision. |
| backend/tests/contract/test_parent_story_run_cancel_route.py | 3,601 / 98B4522D441F223F4BC6A17256982B4E3E9484D7EE1692A753162DDBF17CBBDE | Frozen Parent cancel regression evidence; no edit unless separately selected. |
| backend/tests/unit/test_parent_story_run_cancel_repository.py | 10,111 / A7CE542F352E9E51A0C5B32444240E6A84866C7452293BFBE15EB38E02689D9E | Frozen repository regression evidence; no edit unless separately selected. |
| backend/tests/contract/test_parent_ai_late_result_guards.py | 3,467 / 7C9EF0E89B77E1566A33C386854174A56E9BABB88732A94BDB499898D42D2BEC | Frozen late-result regression evidence; no edit unless separately selected. |
| backend/src/sketch2life/interfaces/http/routers/story_run_lite.py | 13,453 / 5676E1FAD9D615BDFF512D6C39EF002FD9933DA86BFBE485E95F4BE72B07F381 | Separate demo-profile cancel implementation; H only, outside the Parent product route scope. |
| backend/src/sketch2life/interfaces/http/api_conventions.py | 6,387 / D2F4A3274723D232ABE00366C30B7004C312E01383D5EB2602A0F2AF19E7C790 | Read-only CONV-1 convention parsers (single Idempotency-Key of 1-128 visible ASCII, STALE_REVISION helper). Added by CONV-1; absent at HEAD. Idempotency-Key range differs from the Parent routes. No edit under this allowlist. |
| backend/src/sketch2life/interfaces/http/error_envelope.py | 12,231 / B39870B5C918670BDEDA77E34A779D62EFD3F866B0DEDE882F5A72975A5ECB0D | Read-only CONV-1 error-body builder (correlation_id, retryable, field_errors, current_version for STALE_REVISION). Added by CONV-1; absent at HEAD. No edit under this allowlist. |
| backend/src/sketch2life/interfaces/http/middleware/bounded_image_upload.py | 8,146 / B3D60B810B1262BC175B10536DCF69C1A01F44FEF43F2DBD06D80F84F61AD20F | Read-only upload-size middleware that builds error bodies through the CONV-1 error envelope; CONV-1 modifies it. Outside FR-C-08 scope; no edit under this allowlist. |

## 6. N — proposed new files

All nine paths were verified ABSENT in the provisional base tree and current root working tree. They are candidates only; each must be rechecked at the exact approved base. No route, public schema, migration, or DTR file is included.

| Exact path | Purpose and boundary |
|---|---|
| backend/src/sketch2life/application/ports/story_run_lifecycle.py | Story lifecycle port, only if selected by the reviewed architecture. |
| backend/src/sketch2life/application/services/story_run_lifecycle.py | Coordinator for approved lifecycle commands and receipts. |
| backend/src/sketch2life/application/services/story_run_purge_worker.py | Owner-acknowledgement and retry worker after contracts exist. |
| backend/tests/contract/test_parent_story_lifecycle_contract.py | Contract tests for the separately approved Parent API. |
| backend/tests/unit/test_parent_story_lifecycle_service.py | Service tests for sequencing and failure handling. |
| backend/tests/unit/test_parent_story_lifecycle_repository.py | Repository tests only after schema and receipt mapping approval. |
| backend/tests/unit/test_parent_story_purge_worker.py | Worker tests for restart-safe retries and reference closure. |
| backend/tests/integration/test_parent_story_lifecycle_synthetic.py | Synthetic integration tests after separate disposable-database approval. |
| features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_REPORT_20261118.md | Evidence report for a separately approved implementation. |

## 7. Explicit exclusions and blockers

- Migrations and DDL are excluded entirely; no migration paths appear in E, D, H, or N.
- Request and response schema changes are excluded from E, D, H, and N; they require separate design review and approval.
- New HTTP routes and client-facing OpenAPI projection changes are excluded. If the SRS operation is not already implemented in source, stop for a separate reviewed path scope.
- The DTR/schema delta for PARENT_ACCOUNT (covering the lifecycle request and the organization-scoped AI Jobs cancellation notice), per-owner acknowledgement, retry, completion evidence, and audit mapping is excluded and must receive separate review and approval.
- No Core Asset reference-closure or storage-ownership path is known; do not invent one. This is a blocker.
- Teacher-specific lifecycle authorization and Teacher route changes are excluded from the first Parent-only implementation slice.
- The response-schema decision for ABANDONED and DELETED, the source-only state compatibility map, and exact GET projection remain open.
- SRS wording alignment for explicit DELETE eligibility across UC-07, §21.2, and BR-26, named owners, real-data retention, and backup/DSR evidence remain gates.

## 8. Reconciliation to predecessor path counts

Allowlist Draft 8 contained 58 path pins in tables plus three inline frozen-test pins. Draft 9 contained 54 base-pinned path rows: 22 E, 6 D, and 26 H. That change removed seven migration references and the public response-schema path from the allowlist, added the separate demo router as H, folded the three inline frozen tests into H, and moved the Teacher sample-claim service from E to H. The two previously omitted audit targets, openapi_contract.py and M2_S2_IMPLEMENTATION_REPORT_20261114.md, are explicit H rows.

This draft contains 57 base-pinned path rows: 22 E, 6 D, and 29 H. Relative to Draft 9 it adds only the three CONV-1 H references named in section 2; the E, D, and N sets are unchanged. The recomputed register is PIN_AUDIT_R6.md, a local, git-ignored scratch file that is not a durable repository record.

Draft 8 also carried two root-checkout FEAT-066 pins (its DECISIONS.md and TASK_APPROVAL.md). They are not carried here, because CONV-1 changes both files and the root-checkout pins no longer describe the provisional base.

## 9. Proposed acceptance and verification boundary

A later separately approved task must map every acceptance condition in Lifecycle Contract Draft 8 to an exact approved path and evidence. It must distinguish static source/composition/OpenAPI facts from runtime behavior; prove state and response compatibility; demonstrate access/worker fencing, retries, owner acknowledgements, positive reference closure, truthful terminal state, quota/sample-claim preservation, and approved audit mapping.

No command ceiling is approved by this document. Any test, typecheck, lint, OpenAPI generation, database, migration, runtime, provider, or network operation requires its own exact approval and launch instruction. No M2 command ceiling transfers.

## 10. Stop rules

Stop before implementation if the exact base is not named; D-214 provenance is unresolved; any E/D/H pin differs from the approved base; any N path is present; required work touches an excluded schema, migration, route, DTR, Core reference-closure path, Teacher adapter, or other unlisted file; a product or module contract remains unresolved; a command lacks explicit approval; or any real-data/provider operation is required.

**FR-C-08 remains DRAFT / NOT APPROVED / NOT LAUNCHED. This allowlist authorizes no edit, command, approval, implementation, test, launch, provider operation, push, or merge.**
