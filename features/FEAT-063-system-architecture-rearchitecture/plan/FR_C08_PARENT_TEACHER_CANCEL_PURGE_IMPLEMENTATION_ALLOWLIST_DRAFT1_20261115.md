# FR-C-08 Parent/Teacher Cancellation, Deletion, and Purge — Exact-Path Implementation Allowlist Draft 1

**Status: PROPOSED / NOT APPROVED / NOT LAUNCHED.** This is an exact-path planning proposal only. It authorizes no implementation, database/migration work, test/check command, provider or Modal call, gate, approval, stage, commit, push, or launch. `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Scope and authority

This allowlist proposal is for a separate future task to implement the full Rev67 FR-C-08 lifecycle described in `FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT1_20261115.md`. It does not modify or extend M2 S2. D-205 and D-207 retain their exact M2-only scopes. D-194 through D-207, Draft 18, the SRS, DTR, prior M2 approvals/reviews, and all existing evidence are frozen.

All S2 source, test, documentation, and route-baseline changes below are already dirty or untracked in the shared M2 worktree. They are **not clean files** and their current pins are not a launch baseline. The owner must first freeze/reconcile the M2 worktree, resolve the open decisions in the specification, and issue a new reviewed launch approval with fresh pins. Any new route, field, state, event, owner, retention rule, or schema need outside these exact proposed paths stops work and requires a reviewed allowlist revision.

## 2. Pin classes and preflight rules

- **E — existing-to-edit proposal:** only the stated purpose could be edited in a future separately approved task. Every E row has a current observation and hash. At launch, rehash it and stop on any mismatch. `DIRTY (M2)` means the bytes include uncommitted M2 work; it is not a cleanliness or approval claim.
- **N — new-file proposal:** the exact path must be absent at a future launch. Its current `ABSENT` state is recorded here. If present, stop; do not overwrite it.
- **H — hard-frozen/out of scope:** read-only reference only. It may not be edited by this proposed task. A need to change it requires an owner-approved revision or separate task.

All pins below were observed in the M2 worktree on 2026-11-15. Paths are repository-relative. Current pins do not replace a future launch prompt's hard pins. Ownership is recorded at the domain level from Rev67/DTR; **named accountable people and several cross-domain service owners remain OPEN**.

## 3. Proposed E paths — existing files

| Class and exact path | Purpose, trace, and owner | Future acceptance evidence | Current state and pin |
|---|---|---|---|
| E `backend/src/sketch2life/application/ports/parent_story_runs.py` | Carry only the approved Story lifecycle command/read boundary; Rev67 §6.1.1, UC-07/UC-11; DTR Story. Domain owner: Story; named owner OPEN. | FR08-01/02/05; port contract review; no direct cross-owner table access. | DIRTY (M2). 6,601 B; `6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4` |
| E `backend/src/sketch2life/application/services/parent_story_runs.py` | Coordinate the existing Parent StoryRun commands only where required by the finalized lifecycle contract; Rev67 UC-07/UC-11; DTR Story. Named owner OPEN. | FR08-01/02; contract and unit evidence. | Clean at observation. 7,630 B; `FED7AC29F02C34F19F093AF471017447F5E5FA3453D399E2A155067609958B14` |
| E `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | Reconcile only owner-approved lifecycle request/read types. Preserve D-204's exact cancel success body and route-specific `purge_state`; no new response fields by inference. Rev67 §§9.8/21.2; D-199–D-204/D-206. Owner OPEN. | FR08-02/07; schema contract review and exact response assertions. | DIRTY (M2). 7,889 B; `1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749` |
| E `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | Implement only Story-owned transactional fence/lock and lifecycle-intent writes using mapped fields; Rev67 §6.1.1/UC-11, D-199–D-204. Story owner/person OPEN. | FR08-02/05; concurrency, replay, rollback, late-result and restart evidence. | DIRTY (M2). 69,489 B; `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` |
| E `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | Reconcile the existing Parent-only route with the separately approved lifecycle contract; no Teacher route, completed-delete route, progress route, or new path is selected here. Rev67 §21.2; D-199–D-204/D-206. Route owner OPEN. | FR08-01/02/07; owner-scope, response, error-envelope, route-composition tests. | DIRTY (M2). 14,626 B; `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` |
| E `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | Add or preserve only callback forwarding needed by the late-result fence; Rev67 §21.6, D-201/D-202. Story/AI Jobs owners OPEN. | FR08-05; all success/failure/unknown callback paths prove guard-before-write and public error code. | DIRTY (M2). 23,082 B; `E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30` |
| E `backend/src/sketch2life/interfaces/http/router_composition.py` | Mount only routes later selected by an owner-approved §21.2 contract. No route is specified by this row. HTTP/Story owners OPEN. | FR08-07; app composition and route inventory match the approved contract. | Clean at observation. 3,743 B; `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` |
| E `backend/src/sketch2life/interfaces/http/app.py` | Reuse the safe public error mapping for approved lifecycle responses only; Rev67 §9.8; domain/HTTP owner OPEN. Do not broaden unrelated legacy formatting. | FR08-02/03/05/07/10; public envelope, safe message, correlation, retryability, and no-content assertions. | DIRTY (M2). 74,637 B; `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` |
| E `backend/src/sketch2life/application/ports/ai_jobs.py` | Add no job state; use an owner-approved cancellation notice/port if existing contract supports it. Rev67 UC-11, event catalog; AI Jobs owner/person OPEN. | FR08-04/05; notice idempotency and result fence contract review. | Clean at observation. 19,923 B; `ACC3E27EA6B3A70E3DE267E4BD892D97FACF02D2B9F994817771BED3F584B3E3` |
| E `backend/src/sketch2life/domain/ai_jobs/model.py` | Preserve separate AiJob state machine; change only if owner-approved existing cancellation contract requires it. Rev67 §6.1.1/§21.6; AI Jobs owner/person OPEN. | FR08-04/05; job/run state separation and late callback tests. | Clean at observation. 17,113 B; `512B604636C1A22E231AC3276D3E537AE0DEAE4D9BB6652CCB064FAB7314DB99` |
| E `backend/src/sketch2life/application/services/ai_jobs.py` | Connect only the agreed idempotent cancellation notice to current AI Jobs behavior; no provider call during planning. Rev67 UC-11; AI Jobs owner/person OPEN. | FR08-04/05; notice replay, cancellation and late-result evidence using synthetic jobs. | Clean at observation. 72,962 B; `15DCD532D56EFF811A7DE937938E8D5F942AC7B29CDE26043A3B572DB02E08AE` |
| E `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | Persist the approved use of existing job/cancellation-notice records only; if the mapped schema is insufficient, stop rather than add DDL. Rev67 UC-11; AI Jobs owner/person OPEN. | FR08-04/05; transactional receipt/notice and restart evidence. | Clean at observation. 37,723 B; `07695F0E6817B1057A38482D2D869D871A77CE77594D170642C00EBC2709724A` |
| E `backend/src/sketch2life/infrastructure/ai_jobs/worker.py` | Fence dispatch/acceptance of work after approved cancellation where the existing worker contract permits it. Rev67 §21.6; AI Jobs owner/person OPEN. | FR08-04/05; queued/running synthetic callback and no-resurrection tests. | Clean at observation. 7,164 B; `A54725329F8643FB0AF9D821F9861BE34980C3DA3E28E201203630EA691785F6` |
| E `backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py` | Preserve the cancellation fence through existing reconciliation; no new AiJob or purge states. Rev67 §21.6; AI Jobs owner/person OPEN. | FR08-05/08; uncertain-outcome and restart tests. | Clean at observation. 1,084 B; `2B36FACBB1C08560BE258F1FF69B07354BCCB45D7672A33A86317E9D5E02EE5E` |
| E `backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py` | Keep agreed durable notice delivery idempotent using existing outbox contracts. Rev67 event catalog/§21.6; AI Jobs owner/person OPEN. | FR08-04/05; duplicate-delivery and restart tests. | Clean at observation. 707 B; `7B2DC13CCFA94C5BD09BA7679AB4DFAB194AEE6B32D8AB651AAB92FBCECB6115` |
| E `backend/src/sketch2life/infrastructure/persistence/outbox.py` | Reuse existing transactional outbox only if its current mapped contract supports the owner-approved event; do not invent event fields. Rev67 event catalog; Story/BE1 owners OPEN. | FR08-02/04/08; exact event payload and duplicate consumer evidence. | Clean at observation. 6,653 B; `0C09BA3B69B1C2EC0D71133C6307BCBFC2902287B287DAF11E1AF8BA9DC9281B` |
| E `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | Reuse existing `DataLifecycleRequestModel` only for a scope whose approved representation fits its current fields. Its `organization_id` is non-null; the DTR prohibits representing Parent as a fake organization and requires `PARENT_ACCOUNT` scope. Do not assume this model can store Parent lifecycle requests, do not alter mapped columns here absent DTR/migration approval, and keep Parent request writes blocked until a valid mapping is approved. Rev67 UC-07/UC-11, DTR BE1 and §2.2. BE1 owner/person OPEN. | FR08-02/07/08 for an approved compatible scope only; owner-reviewed request state/scope mapping and no-schema-change evidence. | Clean at observation. 28,152 B; `515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666` |
| E `backend/src/sketch2life/infrastructure/story_run_lite/tables.py` | Read/write only existing Story/Core references needed by the accepted lifecycle contract; no table/column/constraint changes. Rev67 §§6.1.1/21.3; DTR Story/Core. Owner OPEN. | FR08-03/05/06/08; reference closure and no-DDL assertions. | Clean at observation. 26,995 B; `703018AE4BF81D51C565EFC4626ED07C973823E5FB582EF69DA7BB490923F034` |
| E `backend/src/sketch2life/infrastructure/lesson_library/tables.py` | Clear the run/media pointer only if the current mapped occurrence fields support it; preserve `SAMPLE_USED` and claim time. Rev67 BR-26/§6.1.1, DTR Lesson. Lesson owner/person OPEN. | FR08-09; teacher sample pointer cleared while claim state/time unchanged and slot remains closed. | Clean at observation. 16,009 B; `FE43AD061B69D4D1B8191AB52705A72C59BAA42605AB9167F4AADF3EF74EFDAF` |
| E `backend/src/sketch2life/infrastructure/lesson_library/service.py` | Implement only the owner-approved occurrence pointer action; never reopen the sample slot or delete shared source documents. Rev67 BR-26/UC-07; Lesson owner/person OPEN. | FR08-06/09; duplicate/restart and claim-retention tests. | Clean at observation. 91,446 B; `68EDDED6CC374EE954FF98C2F558883E5B6887EA721638ACD64D166825D1D4D6` |
| E `backend/src/sketch2life/application/video_playback.py` | Enforce the selected run-deletion playback fence for new and current grants through an approved port. Rev67 FR-C-08/§21.3/NFR-34; Story/video owner OPEN. | FR08-03/05; old-token, cache, authorization and late-output tests. | Clean at observation. 6,188 B; `EEB251839FAA384E68824A4DD79EF55CE5FD553F5ED8FFA72B308082E0CD57A2` |
| E `backend/src/sketch2life/application/ports/video_playback.py` | Express only an owner-approved revocation check; do not invent token fields or expiry semantics. Rev67 §21.3/NFR-34; video owner OPEN. | FR08-03; port contract review and denied-after-revocation evidence. | Clean at observation. 3,436 B; `7621F128D136853F3C9E815A6A70BE250D8D222865861F1F94E03F79023ABE79` |
| E `backend/src/sketch2life/interfaces/http/routers/story_video.py` | Apply only the selected existing playback route check; no new download/export route. Rev67 §21.3/NFR-34; HTTP/video owner OPEN. | FR08-03; route-level old-token and cross-owner denial tests. | Clean at observation. 4,576 B; `C7FEFFEAD0393444BC9CB8A518E471C0D6F64F3D33D3B540002CA1DC51F48F31` |
| E `backend/src/sketch2life/application/video_review_lifecycle.py` | Keep late video-result lifecycle changes behind an explicit Story fence; if this module is not the actual writer after C0 inventory, stop and revise the allowlist. Rev67 §6.1.1/§21.6; video owner OPEN. | FR08-05/08; writer inventory completeness and late result tests. | Clean at observation. 4,386 B; `E5A1A17C3D9580FDABF16E55864C18D10C67A6A03A54BA0CD34980691E0514E4` |
| E `backend/src/sketch2life/application/ports/object_storage.py` | Reuse the existing `delete_object` boundary for object bytes only; it does not delete Core metadata/lineage or resolve shared references. Amend only if an owner-approved idempotent result/error contract is needed. Rev67 UC-07/§21.3, DTR Core. Core owner/person OPEN. | FR08-06/08 object-byte portion only; duplicate delete, missing object, and retry classification tests. Core metadata and reference closure remain blocked by §7. | Clean at observation. 1,060 B; `CEC4214DDF3488D2C996368813B2B74D24C525ED86371E70D89F8AA9FA6EC9A4` |
| E `backend/src/sketch2life/infrastructure/storage/s3_compatible.py` | Adapt only the owner-approved deletion failure mapping; no storage/provider/network call is authorized by this plan. Rev67 UC-07; Core owner/person OPEN. | FR08-06/08; synthetic adapter contract tests without live provider access. | Clean at observation. 3,568 B; `43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B` |
| E `backend/tests/contract/test_app_composition.py` | Add route composition assertions only after OQ-1 selects the route surface. Rev67 §21.2; HTTP owner OPEN. | FR08-07; approved route set is composed exactly once. | DIRTY (M2). 13,507 B; `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` |
| E `backend/tests/contract/test_openapi_contract_catalog.py` | Update only an owner-approved lifecycle route contract if required; do not fix the separate shared mapper/tag issue under this scope. Rev67 §21.2; contract owner OPEN. | FR08-02/07; approved operation maps to its catalog contract. | DIRTY (M2). 18,753 B; `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` |
| E `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` | Reconcile a route baseline only after a new route is explicitly selected; no path can be added by inference. Rev67 §21.2; test coordinator OPEN. | FR08-07; exact approved operation delta. | DIRTY (M2). 9,248 B; `689023BE3130F156CC6C458242DD11F68FDFBC9CC19E0AAC7174B21F9BBB34E5` |
| E `docs/context/PROJECT_CONTEXT.md` | Append implementation status only after separately authorized work/evidence; preserve the M2-local edit. Repo context owner OPEN. | FR08-01–10; status matches pinned evidence. | DIRTY (M2). 83,909 B; `56DC16E4802A6598E6232D3A4B3361F802BDB54F461C3AE27B9AF2E31D63D061` |
| E `docs/context/SOURCE_REGISTER.md` | Add source/evidence pointers only after separately authorized implementation; preserve the M2-local edit. Repo context owner OPEN. | FR08-01–10; all referenced pins resolve. | DIRTY (M2). 115,881 B; `39D8BD4F68ECCB75FF16BBFE775A9BBDB13151E7BD948EE1791071A0DA0B39FC` |
| E `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | Record only the approved task and verified outcome after implementation. FEAT-063 coordinator/person OPEN. | FR08-01–10; current status and blockers are accurate. | Clean at observation. 113,670 B; `7137B59263B7B886F3EB5A18D741DB08F976E3E08947C7BE80679ED3FE50EDEF` |
| E `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md` | Add lifecycle evidence/source records only after implementation and review. FEAT-063 coordinator/person OPEN. | FR08-01–10; exact source/report pins resolve. | Clean at observation. 66,896 B; `08A0AE379D87CD237A923F921E2FC7F1385BAAE63C74F264FEBD24721FC1EED1` |

**Scope stop:** route choice, Teacher authorization path, lifecycle request owner, and progress fields are OPEN. E rows for route composition, schemas, catalog and baseline are conditional review targets, not permission to invent or mount a route. If the accepted design needs a different file or a new public schema, stop and obtain an allowlist revision.

## 4. Proposed N paths — new files

All paths below were absent on 2026-11-15. They are candidates only. Each requires the future launch prompt to repeat the absence check and provide a hard pin/status. Named owners remain OPEN.

| Class and exact path | Purpose, trace, and owner | Future acceptance evidence | Current state / pin |
|---|---|---|---|
| N `backend/src/sketch2life/application/ports/story_run_lifecycle.py` | Candidate application boundary for lifecycle work, only if C1 assigns that responsibility to Story. Rev67 FR-C-08/event catalog; Story owner OPEN. | FR08-02/04/07/08; contract review proves no cross-owner SQL and no invented field/state. | ABSENT; no hash |
| N `backend/src/sketch2life/application/services/story_run_lifecycle.py` | Candidate application coordinator for owner-approved cancel/delete request sequencing. Does not choose route or lifecycle states. Rev67 UC-07/UC-11; Story/BE1 ownership OPEN. | FR08-01/02/04/05/07; idempotency, authorization and durable-intent tests. | ABSENT; no hash |
| N `backend/src/sketch2life/application/services/story_run_purge_worker.py` | Candidate worker only after BE1/Core/Lesson ownership and retry contract are approved. No schema or progress-state choice implied. Rev67 FR-C-08/§21.6; owner OPEN. | FR08-06/08; partial failure, shared refs, duplicate/restart and late-output tests. | ABSENT; no hash |
| N `backend/tests/contract/test_parent_story_lifecycle_contract.py` | Synthetic contract tests for only the routes and fields selected by the owner; no route is implied by filename. Rev67 §§9.8/21.2/21.3/21.4. Test owner OPEN. | FR08-01/02/03/07; auth, status/envelope, replay, revision and progress assertions. | ABSENT; no hash |
| N `backend/tests/unit/test_parent_story_lifecycle_service.py` | Application-level command sequencing, transaction boundary and owner-port fakes. Rev67 UC-07/UC-11/event catalog. Test owner OPEN. | FR08-02/04/05; no call leaks across owner boundary. | ABSENT; no hash |
| N `backend/tests/unit/test_parent_story_lifecycle_repository.py` | Synthetic Story lifecycle receipt/fence persistence tests if new use-case repository boundary is selected. Rev67 §21.4, D-199–D-204. Story test owner OPEN. | FR08-02/05/08; replay, stale/duplicate and no-write-on-fence assertions. | ABSENT; no hash |
| N `backend/tests/unit/test_parent_story_purge_worker.py` | Fake-only purge traversal, retry, shared asset and restart cases. Rev67 UC-07/BR-26 and DTR Core/Lesson. Test owner OPEN. | FR08-06/08/09; no shared or unrelated content deleted; terminal predicate respected. | ABSENT; no hash |
| N `backend/tests/integration/test_parent_story_lifecycle_synthetic.py` | Isolated synthetic integration for storage/database transaction and restart behavior, only under a separate owner-authorized task-owned environment. Rev67 FR-C-08 and M5/M6 roadmap context. Integration owner OPEN. | FR08-02–10; full synthetic audit log and isolated DB/storage evidence. | ABSENT; no hash |
| N `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_REPORT_20261115.md` | Record launch pins, actual checks, evidence and limitations after future work. FEAT-063 coordinator/person OPEN. | All FR08 acceptance and command output references are reproducible and accurately scoped. | ABSENT; no hash |

This proposed list intentionally has no new API schema or route file because OQ-1/OQ-4 have not selected the route/actor contract. It has no migration, audit, mobile, or provider file. Those are blockers or out of scope, not implied omissions to be filled ad hoc.

## 5. H paths — frozen or read-only references

Do not edit these files under this proposal. Current pins are shown where relied upon. Any H-path change requires a separate owner-approved task or a reviewed allowlist revision.

| Exact H path | Current bytes / SHA-256 | Read-only purpose / boundary |
|---|---|---|
| `docs/context/SRS_AUTHORITY.md` | 4,054 / `E3783924BCDF0327CCCDA8806773FB4407ED311C7074289D74AB9B9124EAF662` | Authority pointer; Rev67 under D-203. |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 634,291 / `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` | Canonical unsigned Rev67; frozen. |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` | 171,609 / `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2` | Matching logical table/owner reference; amendment required for unmapped schema. |
| `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 212,068 / `191D68D7344FE2146E75F339185065234D092887C341AB487FB2DBEA8511C2BF` | D-194–D-207 preserved; no append in this task. |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 410,676 / `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` | Existing M2 approval history, frozen. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 / `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` | M2 approved specification only; not this task's implementation authorization. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_DRAFT18_COLD_REVIEW_20261114.md` | 5,169 / `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` | Historical M2 review, frozen. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md` | 14,768 / `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` | M2-only allowlist; do not reuse. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_ALLOWLIST_COLD_REVIEW_R2_20261114.md` | 2,715 / `6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D` | M2-only review; no broader authorization. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 / `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | Current M2 PARTIAL / NOT COMPLETE evidence; do not rewrite. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT1_20261115.md` | 22,501 / `2F879E24BCD50849B2CC826D5E6F510C9173C92C1595503F6BCDA0D40F045D9C` | Historical lifecycle planning input. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT2_20261115.md` | 24,996 / `300BEC5A0716B8CFC09896E52B9752F5D6EBF499C4BB86822A71AF9D29A41310` | Frozen baseline for these two drafts. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md` | 20,115 / `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA` | Historical M5/M6 sequencing context only; it cites an older SRS baseline and is not current requirements authority. |
| `backend/src/sketch2life/infrastructure/persistence/core_models.py` | 11,578 / `47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A` | Core physical-model read-only evidence; no DDL/model expansion authorized. |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | 12,426 / `12F6CE1EDAB047EFDD81D495B44DF08DC6F990692860621F37FC73778006F888` | Existing cancellation-notice table mapping; no table/column/state changes authorized. |
| `backend/src/sketch2life/infrastructure/persistence/be1_parent_role_adapter.py` | 1,507 / `1B83B95341D7AD98360CC98AF640CFAF5750A21FCE4CE971F0EE2D1DF66795E1` | D-190 production BE1 role-adapter coverage remains NOT COVERED; Teacher authority unresolved. |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | Current pin must be captured at a separate launch preflight | Shared mapper/tag discrepancy has its own planning record and is outside this task. Do not expand this allowlist to fix it. |
| `backend/src/sketch2life/interfaces/http/routers/ai_jobs.py` | Current pin must be captured at a separate launch preflight | D-199 defers a separate `/jobs` read from M2; no AI Jobs route is selected here. |
| `backend/tests/contract/test_parent_story_run_cancel_route.py` | 3,601 / `98B4522D441F223F4BC6A17256982B4E3E9484D7EE1692A753162DDBF17CBBDE` | Existing untracked M2 test; preserve it and do not treat it as a lifecycle purge suite. |
| `backend/tests/unit/test_parent_story_run_cancel_repository.py` | 10,111 / `A7CE542F352E9E51A0C5B32444240E6A84866C7452293BFBE15EB38E02689D9E` | Existing untracked M2 test; preserve it. |
| `backend/tests/contract/test_parent_ai_late_result_guards.py` | 3,467 / `7C9EF0E89B77E1566A33C386854174A56E9BABB88732A94BDB499898D42D2BEC` | Existing untracked M2 test; preserve it and separately inventory all video/job writers. |
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | 17,501 / `7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF` | Separate FEAT-047 overlay; never modify under this FR-C-08 proposal. |

### Frozen migrations (no migration is allowlisted)

| Exact H path | Revision evidence | Bytes / SHA-256 |
|---|---|---|
| `backend/alembic/versions/20261014_0001_core_persistence.py` | `20261014_0001`, base | 11,186 / `55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C` |
| `backend/alembic/versions/20261014_0002_be1_runtime.py` | `20261014_0002` after `20261014_0001` | 10,959 / `08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520` |
| `backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py` | `20261015_ai_0001`, separate base | 13,321 / `D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714` |
| `backend/alembic/versions/20261028_ll_0001_lesson_library.py` | `20261028_ll_0001`, separate base | 19,803 / `733836723A95834C721E6CD0CA3527D73EA6EFE089B2F109A956EA484DFE1D83` |
| `backend/alembic/versions/20261102_story_run_lite.py` | `20261102_story_run_lite`, separate base | 28,335 / `D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143` |
| `backend/alembic/versions/20261104_story_revisions.py` | `20261104_story_revisions` after `20261103_story_upload_compat` | 8,529 / `3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8` |
| `backend/alembic/versions/20261112_parent_story_context.py` | `20261112_parent_story_context` after `20261104_story_revisions`; source has an empty-`story.runs` baseline guard | 8,251 / `CFC7A92436066191134E27F1579B54109057CBAC43ABEB72B84C0F2D6CBFD9DF` |

No Alembic graph/head command was run. These relevant file headers are not a full graph audit. Current applied migrations and task-database contents remain **NOT VERIFIED**. If the accepted lifecycle requires an unmapped field, request, work-item checkpoint, or retention table, it is a blocker until the DTR and an independently approved migration task define it.

## 6. M2 dirty-path collision register

The prior D-207 M2 E pins are shown only to make the collision visible. Their differences are expected from the M2 implementation working copy; they are not silently refreshed here. The future FR-C-08 task cannot use these files as clean inputs until the coordinator freezes a baseline.

| Path | D-207 M2 pin | Current observed worktree pin | Disposition |
|---|---|---|---|
| `backend/src/sketch2life/application/ports/parent_story_runs.py` | 6,140 B / `374E2B4003164C90A2C55F06DE8A9FE8F970BE393806D143C9DF4BF6E06BF77F` | 6,601 B / `6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4` | DIRTY M2; freeze/reconcile before future edit. |
| `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | 7,309 B / `C026A1566500EE7B7C2705DFCE6C4E0D0EC7B397E9FE93F11A237A416F768B19` | 7,889 B / `1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749` | DIRTY M2; freeze/reconcile. |
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 64,452 B / `407D2843A93C31BD54202A1E504DE938FB085E67730C199FD4E9B9505E72B832` | 69,489 B / `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` | DIRTY M2; freeze/reconcile. Draft 2's informational pin matches current, but D-207's earlier baseline does not. |
| `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | 12,698 B / `32C707515032FC7BEF08A12D0B1D8E6DD4271FF1B9C55891072BA76E150D6B60` | 14,626 B / `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` | DIRTY M2; freeze/reconcile. Draft 2's informational pin matches current, but D-207's earlier baseline does not. |
| `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | 21,869 B / `8EEDD486148E16350885DBD737C5A3A0F7A4E0906AD473165FBEDB84C7CAC1FE` | 23,082 B / `E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30` | DIRTY M2; freeze/reconcile. |
| `backend/src/sketch2life/interfaces/http/app.py` | 73,534 B / `262CB4583ED545F92DF784B69D426C834D5D7BD23179A61C5C818E6C50F4C298` | 74,637 B / `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` | DIRTY M2; freeze/reconcile. |
| `backend/tests/contract/test_app_composition.py` | 13,451 B / `B738F3BF89D233544FB062D5DB50AED6A8B6DD7A92C0B7020E72E138569D877B` | 13,507 B / `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` | DIRTY M2; recorded setup `WinError 5` remains a future test-environment risk. |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,721 B / `B585C2A87DC50FE6B9571B0AA5DDFB0D0F2918FE69D04749EAE5C9BAEC998255` | 18,753 B / `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` | DIRTY M2; separate OpenAPI mapper/tag issue remains outside this allowlist. |
| `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` | 9,157 B / `A0CB85E214E80BED8EE9AEEF665CC9979F579553BD9117D0D8D682DF641AD8F5` | 9,248 B / `689023BE3130F156CC6C458242DD11F68FDFBC9CC19E0AAC7174B21F9BBB34E5` | DIRTY M2; route baseline is not clean. |
| `docs/context/PROJECT_CONTEXT.md` | 83,183 B / `317D947803D78F1F78D2DA9BEA8E9DF3F718DE8965DFD57E1A665A0A5F1BE612` | 83,909 B / `56DC16E4802A6598E6232D3A4B3361F802BDB54F461C3AE27B9AF2E31D63D061` | DIRTY M2; preserve local status edits. |
| `docs/context/SOURCE_REGISTER.md` | 115,027 B / `0093F8CCE26A526D72C8B940BE8CCE250DB78A9AE852B4834F3ABB639965081A` | 115,881 B / `39D8BD4F68ECCB75FF16BBFE775A9BBDB13151E7BD948EE1791071A0DA0B39FC` | DIRTY M2; preserve local status edits. |

Other unrelated M2 modifications, the FEAT-047 approval/evidence overlay, `features/FEAT-059` baseline file, and all untracked M2 tests remain untouched. Do not stage or clean them as part of any future lifecycle task.

## 7. Migration disposition and hard blocker

No migration is E or N. The static source has existing lifecycle, asset, upload, AI cancellation-notice, and occurrence mappings, but this does not prove the current task database has them applied or that their fields represent the full FR-C-08 workflow. The StoryRun Lite migration source has an empty-`story.runs` baseline requirement. No database was inspected and no migration command was run.

If the resolved design requires a lifecycle work-item table, per-item progress/checkpoint fields, a new actor/reference constraint, an audit field/retention mapping, asset ownership/refcount field, or a state value not already mapped, this proposal is **BLOCKED**. Do not add DDL to an implementation branch. First amend the DTR, obtain owner approval for the exact schema and migration task, independently review it, and obtain separate database authorization. No migration can be smuggled into this allowlist.

### Core Asset owner boundary — hard blocker

The inspected `CoreAssetMetadataPort` and `CoreStore` expose save/get operations only. The E path `ObjectStoragePort.delete_object` deletes object bytes; it does not remove Core asset metadata/lineage or establish whether a valid independent reference remains. `core_models.py` is H/read-only, and this E/N list contains no Core-owned metadata/lineage deletion or reference-resolution operation. Consequently this allowlist cannot implement FR08-06/08 or establish `DELETED` for the full FR-C-08 scope. Do not bypass Core ownership with direct Story writes to Core tables.

Before any future implementation launch, the Core Asset owner must define the reference-resolution, eligible run-owned metadata/lineage removal, object-deletion ordering, and idempotent result contract. An owner-approved allowlist revision must then name the exact Core-owned paths and acceptance evidence. If the contract requires unmapped schema, the DTR amendment and separate migration/database approval remain mandatory. Until the contract and paths are approved, C5 and any claim of full FR-C-08 completion are **BLOCKED**; this paragraph authorizes no separate Core task or DDL.

### Parent lifecycle-request scope — hard blocker

The DTR requires Parent-owned rows to use typed `PARENT_ACCOUNT` scope and forbids a fake organization. The current BE1 `DataLifecycleRequestModel` has a non-null `organization_id`; this allowlist does not define an approved Parent-scoped request mapping or authorize a DTR/schema change. Do not write Parent cancellation/deletion requests through this organization-scoped model by fabricating an organization ID. Before Parent lifecycle-request writes, the owner must approve the accountable owner and a valid Parent-scope representation through an existing typed contract/mapping; if current schema cannot support it, stop for DTR amendment and separate migration/database approval. Until resolved, Parent lifecycle-request implementation and any full Parent-and-Teacher FR-C-08 completion claim are **BLOCKED**. This paragraph authorizes no separate task or DDL.

## 8. Proposed future commands and fresh ceilings

Every command below is **PROPOSED / NOT AUTHORIZED / NOT RUN**. These ceilings are new suggestions for an eventual FR-C-08 launch, not inherited from D-207 or any consumed M2 run. The owner must pin interpreter and final selections in the launch prompt. No tests, typecheck, lint, validator, diff check, backend, database, migration, Docker, install, network, provider, or Modal command was run for these drafts.

### Pytest temp/cache handling

The repository-root ignored parent `tmp/m2-s2-validation` existed at planning time, and the previously prepared Python 3.12 executable existed at `tmp/m2-s2-validation/python312/.venv/Scripts/python.exe`. Existence does not prove effective write permission. A future run must check the parent and interpreter before invocation, generate a new GUID child for every run, and stop if the parent is absent/inaccessible. Do not fall back to the Windows default temp directory, change ACLs, install packages, or create a replacement parent under this plan. Use `-p no:cacheprovider` to avoid writes to `.pytest_cache`.

From the M2 worktree root, each future owner-run test invocation must use its own fresh GUID child (not executed). The unique `--basetemp` moves pytest `tmp_path` away from the denied Windows default temp path; `-p no:cacheprovider` avoids `.pytest_cache`. This is a mitigation, not proof that the selected parent has effective write permission. Stop on access denial; do not retry elsewhere.

```powershell
$runId = [guid]::NewGuid().ToString('N')
$scratchParent = '..\..\tmp\m2-s2-validation'
$python = '..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $scratchParent -PathType Container)) { throw 'Approved pytest basetemp parent is missing' }
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Pinned Python environment is missing' }
$base = Join-Path $scratchParent "frc08-contract-$runId"
& $python -m pytest -q --basetemp $base -p no:cacheprovider backend/tests/contract/test_parent_story_lifecycle_contract.py backend/tests/contract/test_app_composition.py backend/tests/contract/test_openapi_contract_catalog.py
```

If an access-denied result occurs, stop and report it. Do not retry under a different temp path without a new owner instruction.

### Test commands

Each proposed pytest command below uses a new GUID child under the existing repository-root ignored parent `tmp/m2-s2-validation`. These commands are examples for a future owner-approved launch and are **PROPOSED / NOT AUTHORIZED / NOT RUN**. From the M2 worktree root:

Contract selection — maximum 2 combined invocations total (one initial, one final after fixes):

```powershell
$runId = [guid]::NewGuid().ToString('N')
$scratchParent = '..\..\tmp\m2-s2-validation'
$python = '..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $scratchParent -PathType Container)) { throw 'Approved pytest basetemp parent is missing' }
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Pinned Python environment is missing' }
$base = Join-Path $scratchParent "frc08-contract-$runId"
& $python -m pytest -q --basetemp $base -p no:cacheprovider backend/tests/contract/test_parent_story_lifecycle_contract.py backend/tests/contract/test_app_composition.py backend/tests/contract/test_openapi_contract_catalog.py
```

The known shared mapper/tag discrepancy must be separately resolved and authorized before this selection can be expected to pass; do not widen this lifecycle allowlist to fix it.

Unit selection — maximum 2 combined invocations total (one initial, one final after fixes):

```powershell
$runId = [guid]::NewGuid().ToString('N')
$scratchParent = '..\..\tmp\m2-s2-validation'
$python = '..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $scratchParent -PathType Container)) { throw 'Approved pytest basetemp parent is missing' }
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Pinned Python environment is missing' }
$base = Join-Path $scratchParent "frc08-unit-$runId"
& $python -m pytest -q --basetemp $base -p no:cacheprovider backend/tests/unit/test_parent_story_lifecycle_service.py backend/tests/unit/test_parent_story_lifecycle_repository.py backend/tests/unit/test_parent_story_purge_worker.py
```

Purpose: offline synthetic authorization, receipts, late-result fence, retry, shared-asset and sample-claim behavior.

Integration selection — maximum 1 owner-authorized invocation, only after separate isolated database/storage approval and exact environment pin:

```powershell
$runId = [guid]::NewGuid().ToString('N')
$scratchParent = '..\..\tmp\m2-s2-validation'
$python = '..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $scratchParent -PathType Container)) { throw 'Approved pytest basetemp parent is missing' }
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Pinned Python environment is missing' }
$base = Join-Path $scratchParent "frc08-integration-$runId"
& $python -m pytest -q --basetemp $base -p no:cacheprovider backend/tests/integration/test_parent_story_lifecycle_synthetic.py
```

Purpose: synthetic-only persistence/restart integration against a task-owned disposable database/storage fixture. No shared task DB and no real child data. The integration selection is blocked until separate infrastructure/database approval and an exact environment pin are supplied. Every invocation requires a fresh GUID child. Do not rerun any selection beyond its proposed ceiling.

### Typecheck and lint

| Check | Exact command from `backend/` | Ceiling | Status |
|---|---|---:|---|
| Mypy | `& ..\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe -m mypy src/sketch2life` | 1 run | From `backend/`; PROPOSED / NOT AUTHORIZED / NOT RUN; compare against the recorded 335-error baseline without claiming the baseline is a pass. |
| Ruff | `& ..\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe -m ruff check src/sketch2life` | 1 run | From `backend/`; PROPOSED / NOT AUTHORIZED / NOT RUN; compare against recorded diagnostics and do not auto-fix. |

### Final repository checks

| Check from the M2 worktree root | Exact command | Ceiling | Status |
|---|---|---:|---|
| Harness | `& .\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe tools/validate_harness.py` | 1 final run | From the worktree root; PROPOSED / NOT AUTHORIZED / NOT RUN |
| Architecture | `& .\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe tools/validate_architecture.py` | 1 final run | From the worktree root; PROPOSED / NOT AUTHORIZED / NOT RUN |
| Repository security | `& .\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe tools/validate_repository_security.py` | 1 final run | From the worktree root; PROPOSED / NOT AUTHORIZED / NOT RUN |
| Whitespace | `git diff --check` | 1 final run | PROPOSED / NOT AUTHORIZED / NOT RUN |

No Alembic command, migration, backend server, database query, Docker, provider, network, install, or Modal command is proposed as authorized. A future launch prompt must resolve any required runtime/database evidence separately.

## 9. Stop conditions

Stop before any future edit if the branch/HEAD, any pinned E/H input, N-path absence, or working-tree ownership differs; if an E path is still mixed with uncommitted M2/FEAT-047 work that cannot be safely partitioned; if OQ-1–OQ-9 remain unresolved for the behavior under change; if any handler/writer is outside this list; if the Parent request cannot be represented with an approved typed `PARENT_ACCOUNT` scope without fabricating `organization_id`; if the Core Asset owner contract, exact Core-owned operation paths, metadata/lineage deletion, or valid-reference resolution is not approved and included in a revised allowlist; if authorization, existing-token revocation, late-result fencing, shared-asset safety, or the `DELETED` predicate cannot be demonstrated; if existing schema/mapped ports cannot support the accepted behavior; or if a route, field, state, event, owner, DDL, retention mapping, command, or ceiling would need to be invented. Report the exact blocker and obtain an owner-approved allowlist revision. No partial implementation may be called complete.

## 10. Completion boundary

This allowlist draft remains **PROPOSED / NOT APPROVED / NOT LAUNCHED**. It is not a launch prompt and does not approve implementation. Full FR-C-08 implementation is **BLOCKED** pending both an approved Parent-scoped lifecycle-request mapping and the Core Asset owner contract/revised allowlist; C5 specifically remains blocked on Core paths. The M2 implementation status remains **PARTIAL / NOT COMPLETE**. No pre-existing source, test, decision, approval, or evidence file was modified; this allowlist and its companion specification are planning documents. No checks or external actions were run.

## 11. Post-review correction — 2026-11-15

The independent cold review found P1: the prior allowlist covered low-level object-byte deletion but no Core-owned operation to delete eligible asset metadata/lineage or resolve valid shared references. Static source inspection confirms `CoreAssetMetadataPort` and `CoreStore` currently expose save/get only. This draft now explicitly blocks C5 and any full FR-C-08/`DELETED` claim until the Core Asset owner defines the required contract and an owner-approved allowlist revision adds the exact Core paths and acceptance evidence. No Story-owned direct Core-table write, route, schema change, migration, or implementation authorization was added. The companion specification records the same dependency. The prior cold-review verdict applies to the prior pins; both corrected documents require a fresh independent review before they can be considered ready.

## 12. Post-review correction 2 — 2026-11-15

The next independent cold review found that the current BE1 lifecycle-request model requires non-null `organization_id`, while the DTR requires Parent-owned rows to use `PARENT_ACCOUNT` and forbids a fake organization. This allowlist now blocks Parent lifecycle-request writes and full FR-C-08 completion until the owner approves a valid Parent-scoped mapping (or separate DTR/schema/migration work under its own approval), and adds this mismatch to the stop conditions. No Parent scope, owner contract, route, field, schema change, migration, or implementation authorization was invented. The companion specification records the same blocker; a fresh independent review is required for these revised pins.
