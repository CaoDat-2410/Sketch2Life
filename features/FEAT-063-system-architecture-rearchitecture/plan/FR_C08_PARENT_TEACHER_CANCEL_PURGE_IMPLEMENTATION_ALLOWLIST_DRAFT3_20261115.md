# FR-C-08 Parent/Teacher Cancellation, Deletion, and Purge — Exact-Path Implementation Allowlist Draft 3

**Status: PROPOSED / BLOCKED FOR IMPLEMENTATION / NOT APPROVED / NOT LAUNCHED.** This is an allowlist proposal for a separate FR-C-08 task. It is not a Task Approval, implementation approval, launch prompt, command authorization, database/migration approval, or transfer of M2 scope. `OWNER_MODAL_CALL_APPROVED=NO`.

## Revision note

Draft 3 preserves Draft 2 and its independent review as historical records. It corrects the three review findings without changing the Rev68/D-208 lifecycle scope: named accountable-person assignment is a governance gate before launch, while unresolved technical ownership and contracts remain implementation blockers; the approval ledger is described with its separate FEAT-047 and one-time S2 verification entries; and Draft 1 is described only as not selecting a completed-delete route. The lifecycle gates and any future dates remain proposals, not commitments.

## 1. Purpose, authority, and boundary

This file proposes an exact candidate path set for a future, separately approved FR-C-08 implementation. Its scope is no broader than the reviewed Specification Draft 3 and Lifecycle Plan Draft 3. It does not modify or extend M2 S2. Draft 18, D-205, D-207, the M2 allowlist, M2 command ceilings, and M2 launch authorization apply only to the bounded S2 task and do not transfer here.

The canonical working requirements baseline is FEAT-063 v2.7-draft Rev68 under D-203 and D-208. Rev68 is unsigned; “canonical working” does not mean signed or formally approved. The DTR is a companion logical/physical data-model source and has not been changed. The exact-path rows below are proposals only. A future owner-issued launch prompt must re-pin every selected path, account for the current dirty baseline, close the blockers in §5, and authorize the exact scope and commands. Any needed path, field, route, state, event, owner, schema change, retention rule, or command not listed here stops work for a reviewed allowlist revision.

No implementation, source/test edit, database access, migration, DDL, server, Docker, install, network, provider, Modal, Android/emulator, staging, commit, push, approval, gate, or launch is authorized by this draft. No live database contents or runtime behavior are claimed.

## 2. Pinned planning inputs

Pins below are current observations made for Draft 2. The Rev68/D-208 entries supersede older Rev67/D-207 snapshot values only because the repository now contains the newer authoritative records. Earlier approval and decision pins remain valid as historical records; they are not rewritten. The dirty implementation pins are observations, not a clean launch baseline.

| Input | Bytes | SHA-256 | Use and status |
|---|---:|---|---|
| `docs/context/SRS_AUTHORITY.md` | 4,313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` | Current authority pointer; Rev68 remains unsigned. |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 639,948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` | Canonical working Rev68 under D-203/D-208; unsigned. |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` | 171,609 | `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2` | Companion model reference; unchanged. |
| `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 216,212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` | Current ledger contains D-203–D-208; no edit proposed. D-208 controls planning direction. |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 410,676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` | The ledger includes historical approvals, the D-205/D-207 M2 S2 specification and bounded implementation approvals, and a separate limited FEAT-047 metadata overlay plus one-time S2 verification authorization. Neither latter record nor either M2 approval authorizes FR-C-08 implementation. Frozen. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT3_20261115.md` | 19,897 | `1D680D04D1B06ED827F0FFD71A30D5E2C2AFC09828158997276D1F8424F37313` | Current specification proposal; DRAFT / NOT APPROVED / NOT LAUNCHED. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT3_20261115.md` | 13,246 | `832D3653A38BAF8E3D82D75C319D7BA275B7628510074932DF726F459EB8A95E` | Current lifecycle plan proposal; DRAFT / NOT APPROVED / NOT LAUNCHED. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_DRAFT3_COLD_REVIEW_20261115.md` | 10,047 | `83270D1A6FE19FAE42CB4C405A9DDB3B2298E181261C9B740F0DA9F0F5C26658` | Independent review: READY WITH NOTES, 0 P1, 0 P2, 1 P3 on proposed timing language. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261115.md` | 44,643 | `82978E82A2A07A94007E7574BC43FA45663CA3B03D72FAEFDD24C15964D01800` | Historical proposal. Section 3, the `parent_story_runs.py` E-path row, says no completed-delete route was selected; this is a route-selection boundary, not deletion eligibility. Rev68/D-208 control this draft. Spec Draft 3 section 9 repeats a completed-run-only attribution that Draft 1 section 3 does not support; that separate document is unchanged and is not relied on here. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT2_20261115.md` | 24,996 | `300BEC5A0716B8CFC09896E52B9752F5D6EBF499C4BB86822A71AF9D29A41310` | Frozen planning baseline; its §7 questions are carried into §5. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` | M2 specification only; not FR-C-08 approval. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_DRAFT18_COLD_REVIEW_20261114.md` | 5,169 | `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` | M2 review only; not FR-C-08 approval. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md` | 14,768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` | M2-only approved allowlist; no path/ceiling transfers. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_ALLOWLIST_COLD_REVIEW_R2_20261114.md` | 2,715 | `6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D` | M2-only review. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | S2 is PARTIAL / NOT COMPLETE; verification is not a completed FR-C-08 baseline. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md` | 20,115 | `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA` | Historical M5/M6 sequencing context only; not current SRS authority. |
| `docs/context/PROJECT_CONTEXT.md` | 83,919 | `B53D00641590E5B0DB7D6D19603AB796F19658F9F3F6AD8BC31076FDF51D631D` | Current dirty worktree snapshot; preserve and do not overwrite. |
| `docs/context/SOURCE_REGISTER.md` | 116,802 | `AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B` | Current dirty worktree snapshot; preserve and do not overwrite. |
| `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | 113,670 | `7137B59263B7B886F3EB5A18D741DB08F976E3E08947C7BE80679ED3FE50EDEF` | Current feature context reference. |
| `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md` | 66,896 | `08A0AE379D87CD237A923F921E2FC7F1385BAAE63C74F264FEBD24721FC1EED1` | Current feature source register reference. |

The SRS authority, SRS, decisions, and project/source context pins differ from the older Draft 1 snapshot because Rev68/D-208 and their associated context updates are now present. This is a documented newer baseline, not an instruction to repair the old draft. Every current E/N path below has also been rehashed. Dirty M2 values match the current M2 report/Draft 3 observations; D-207-era pins are retained as historical collision evidence in §7.

## 3. Required lifecycle policy for any later implementation

Rev68 §6.1.1, FR-C-08, UC-07/UC-11, BR-26/BR-40, §§9.8, 21.2, 21.4, 21.6, NFR-34, the deletion/cancellation event contracts, and §31.10(17) control. D-208 records the planning dispositions. The following matrix is the exact operation eligibility; no new StoryRun state is proposed.

| Rev68 StoryRun state | Cancel unfinished run | Explicit user-requested DELETE | Required disposition |
|---|---|---|---|
| `DRAFT` | Yes | No | Cancel only while eligible under UC-11. |
| `INPUT_PROCESSING` | Yes | No | Cancel and fence late processing output. |
| `INPUT_REVIEW` | Yes | No | Cancel only while eligible. |
| `SUBJECT_REVIEW` | Yes | No | Cancel only while eligible. |
| `PREPARATION_REVIEW` | Yes | No | Cancel only while eligible. |
| `STORY_GENERATING` | Yes | No | Cancel and fence late results. |
| `SCRIPT_REVIEW` | Yes | No | Cancel only while eligible. |
| `VIDEO_ADMISSION_PENDING` | Yes | No | Fence admission/dispatch. |
| `VIDEO_QUEUED` | Yes | No | Request best-effort job cancellation. |
| `VIDEO_GENERATING` | Yes | No | Provider/job interruption is best-effort; fence output. |
| `VIDEO_SAFETY_VALIDATING` | Yes | No | Output remains non-playable and is purged. |
| `VIDEO_READY` | Yes, if still unfinished | No | Apply UC-11 eligibility. |
| `SAFETY_BLOCKED` | Yes | No | Cancel only while eligible. |
| `COMPLETED` | No | Yes | Deletion requires an authorized explicit request. |
| `FAILED` | No | Yes | Never auto-purge; content remains until authorized user request. |
| `ABANDONED` | No | Yes | Never auto-purge; content remains until authorized user request. |
| `DELETE_PENDING` | No | No | Keep public pending until purge verification; reject new user delete/cancel. |
| `DELETED` | No | No | Reach only after required purge has been verified. |

The 13 cancel states are exactly `DRAFT`, `INPUT_PROCESSING`, `INPUT_REVIEW`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `STORY_GENERATING`, `SCRIPT_REVIEW`, `VIDEO_ADMISSION_PENDING`, `VIDEO_QUEUED`, `VIDEO_GENERATING`, `VIDEO_SAFETY_VALIDATING`, `VIDEO_READY`, and `SAFETY_BLOCKED`. UC-11 excludes `COMPLETED`, `FAILED`, `ABANDONED`, `DELETE_PENDING`, and `DELETED`. `SCRIPT_GENERATION_UNKNOWN` is not one of Rev68’s 18 StoryRun states and must not be added or silently treated as a valid state.

Any later implementation must also preserve these D-208 requirements:

- Authorize the current Parent owner or the Teacher currently assigned to the class using the current BE1 assignment/version. Former Teacher status and creator provenance alone confer no authority. Named accountable owners remain OPEN and are required before launch.
- Story owns the StoryRun transition, active-lock release, cancellation event, and late-result fence. BE1 coordinates the lifecycle request. Core Asset owns asset/reference resolution and deletion. AI Jobs receives best-effort cancellation. Lesson-owned Teacher occurrence changes must clear the run/media pointer while preserving `SAMPLE_USED` and claim time; never reopen the slot.
- Fence API, download, playback/token, cache/stream, upload/partial-upload, and job-dispatch access immediately when cancellation is accepted. Best-effort job/provider cancellation does not delay lock release. Late results must be fenced, non-playable, and purged.
- Purge all required run-owned content, private derivatives, and incomplete upload data through the owning modules. A shared asset may remain only after the run reference is removed and a valid independent reference is verified. Retry idempotently. Keep `DELETE_PENDING` while any required content remains or deletion is unverified; only then may public status become `DELETED`.
- Preserve consumed quota usage and the successful Teacher sample claim. Audit is metadata-only and excludes child media/content, transcripts, prompts, and profile-support details. Only SRS-permitted audit, quota, and successful sample-claim metadata may remain by default. Do not claim provider-copy or backup deletion without evidence.
- Use typed `PARENT_ACCOUNT`; never fabricate `organization_id`. Do not invent a route, field, receipt schema, event, state, progress percentage, owner, physical mapping, DDL, or retention exception. Keep M2 as a separate coordination gate.

## 4. Candidate exact-path inventory

### 4.1 Proposed E paths — existing-to-edit candidates

These are candidate paths only. Domain responsibilities are derived from D-208/DTR; named accountable persons and several adapter owners are OPEN. The acceptance references point to the numbered criteria in Spec Draft 3 §7: (1) eligibility, (2) authorization, (3) atomic acceptance, (4) immediate revocation, (5) best-effort cancellation/fencing, (6) purge/retry, (7) terminal read, (8) quota/sample preservation, (9) audit/retention, (10) evidence boundary. No path below is cleanly authorized for editing while it contains pre-existing M2 work.

| Class / exact path | Purpose and trace | Module owner (named owner) | Future acceptance evidence | Current status / observed bytes / SHA-256 |
|---|---|---|---|---|
| E `backend/src/sketch2life/application/ports/parent_story_runs.py` | Story lifecycle command/read boundary; Rev68 §6.1.1, UC-07/UC-11; DTR Story. | Story (person OPEN). | Spec §7 items 1–3, 5, 7; typed port review, no cross-owner SQL. | DIRTY M2; 6,601; `6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4` |
| E `backend/src/sketch2life/application/services/parent_story_runs.py` | Coordinate only the approved Parent StoryRun lifecycle commands; Rev68 UC-07/UC-11. | Story (person OPEN). | Spec §7 items 1–3; service contract/unit evidence. | No current worktree modification; 7,630; `FED7AC29F02C34F19F093AF471017447F5E5FA3453D399E2A155067609958B14` |
| E `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | Express only separately approved request/read types; Rev68 §§9.8/21.2 and D-199–D-208. No field/receipt inferred. | Story/API contract (person OPEN). | Spec §7 items 1–3, 7; schema contract and exact response assertions. | DIRTY M2; 7,889; `1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749` |
| E `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | Story-owned state/lock/fence writes only through mapped fields; Rev68 §6.1.1/UC-11, D-199–D-208. | Story (person OPEN). | Spec §7 items 3, 5–8; transaction, replay, race, no-resurrection and restart evidence. | DIRTY M2; 69,489; `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` |
| E `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | Align existing Parent routes with the approved §21.2 contract; no additional route chosen by this row. | BE1 HTTP / Story API (person OPEN). | Spec §7 items 1–3, 7; owner-scope, eligibility, error, response, route evidence. | DIRTY M2; 14,626; `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` |
| E `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | Forward only approved callback outcomes to the Story late-result fence; Rev68 §21.6. | Story and AI Jobs (both persons OPEN). | Spec §7 item 5; every success/failure/unknown result is refused after the fence. | DIRTY M2; 23,082; `E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30` |
| E `backend/src/sketch2life/interfaces/http/router_composition.py` | Preserve or compose only routes already selected by Rev68 §21.2; no route is added by inference. | BE1 HTTP (person OPEN). | Spec §7 items 1, 2, 7; composition inventory matches approved contract. | No current worktree modification; 3,743; `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` |
| E `backend/src/sketch2life/interfaces/http/app.py` | Apply existing safe error handling only to approved lifecycle responses; Rev68 §9.8. | HTTP platform (person OPEN). | Spec §7 items 2–5, 7, 10; public envelope, correlation, safe messages and status. | DIRTY M2; 74,637; `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` |
| E `backend/src/sketch2life/application/ports/ai_jobs.py` | Use an approved existing best-effort cancellation port; do not add job states. | AI Jobs (person OPEN). | Spec §7 items 5–6; port contract and job/run state separation. | No current worktree modification; 19,923; `ACC3E27EA6B3A70E3DE267E4BD892D97FACF02D2B9F994817771BED3F584B3E3` |
| E `backend/src/sketch2life/domain/ai_jobs/model.py` | Preserve the independent AiJob state machine; change only against an approved contract. | AI Jobs (person OPEN). | Spec §7 items 5–6; no StoryRun state leakage into AiJob. | No current worktree modification; 17,113; `512B604636C1A22E231AC3276D3E537AE0DEAE4D9BB6652CCB064FAB7314DB99` |
| E `backend/src/sketch2life/application/services/ai_jobs.py` | Coordinate only the approved best-effort cancellation notice; no provider call in this plan. | AI Jobs (person OPEN). | Spec §7 items 5–6; idempotent notice and late-result evidence. | No current worktree modification; 72,962; `15DCD532D56EFF811A7DE937938E8D5F942AC7B29CDE26043A3B572DB02E08AE` |
| E `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | Persist cancellation using existing mapped contracts only; stop if schema is insufficient. | AI Jobs (person OPEN). | Spec §7 items 5–6; receipt/notice and restart evidence without DDL. | No current worktree modification; 37,723; `07695F0E6817B1057A38482D2D869D871A77CE77594D170642C00EBC2709724A` |
| E `backend/src/sketch2life/infrastructure/ai_jobs/worker.py` | Fence queued dispatch/acceptance after approved cancellation where current contract supports it. | AI Jobs (person OPEN). | Spec §7 items 4–5; synthetic queued/running late callback evidence. | No current worktree modification; 7,164; `A54725329F8643FB0AF9D821F9861BE34980C3DA3E28E201203630EA691785F6` |
| E `backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py` | Preserve cancellation fence during existing reconciliation; add no job/purge state. | AI Jobs (person OPEN). | Spec §7 items 5–6; uncertain-outcome/restart evidence. | No current worktree modification; 1,084; `2B36FACBB1C08560BE258F1FF69B07354BCCB45D7672A33A86317E9D5E02EE5E` |
| E `backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py` | Deliver only the approved durable notice under existing outbox semantics. | AI Jobs (person OPEN). | Spec §7 items 3, 5; duplicate delivery/restart evidence. | No current worktree modification; 707; `7B2DC13CCFA94C5BD09BA7679AB4DFAB194AEE6B32D8AB651AAB92FBCECB6115` |
| E `backend/src/sketch2life/infrastructure/persistence/outbox.py` | Reuse an existing outbox contract only; do not invent event fields. | Story/BE1 (persons OPEN). | Spec §7 items 3, 5; approved event payload and duplicate-consumer evidence. | No current worktree modification; 6,653; `0C09BA3B69B1C2EC0D71133C6307BCBFC2902287B287DAF11E1AF8BA9DC9281B` |
| E `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | Existing lifecycle request model may be used only for a scope it can represent; its organization field is non-null and Parent must remain typed `PARENT_ACCOUNT`. No fake organization or column edit. | BE1 (person OPEN). | Spec §7 items 2–3, 9; approved mapping; no-schema-change evidence. | No current worktree modification; 28,152; `515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666` |
| E `backend/src/sketch2life/infrastructure/story_run_lite/tables.py` | Use existing Story/Core references only; no table, column, or constraint change. | Story (person OPEN). | Spec §7 items 3, 5–8; reference closure and no-DDL evidence. | No current worktree modification; 26,995; `703018AE4BF81D51C565EFC4626ED07C973823E5FB582EF69DA7BB490923F034` |
| E `backend/src/sketch2life/infrastructure/lesson_library/tables.py` | Clear only an existing occurrence run/media pointer if mapped; preserve `SAMPLE_USED` and claim time. | Lesson (person OPEN). | Spec §7 item 8; pointer cleared, claim/time retained, slot remains closed. | No current worktree modification; 16,009; `FE43AD061B69D4D1B8191AB52705A72C59BAA42605AB9167F4AADF3EF74EFDAF` |
| E `backend/src/sketch2life/infrastructure/lesson_library/service.py` | Apply only an approved Teacher occurrence pointer change; never reopen slot or delete shared source. | Lesson (person OPEN). | Spec §7 items 6, 8; duplicate/restart and claim-retention evidence. | No current worktree modification; 91,446; `68EDDED6CC374EE954FF98C2F558883E5B6887EA721638ACD64D166825D1D4D6` |
| E `backend/src/sketch2life/application/video_playback.py` | Enforce the approved lifecycle fence for new/current playback grants through an owner port. | Video/Story (persons OPEN). | Spec §7 items 4–6; old token/cache and late-output evidence. | No current worktree modification; 6,188; `EEB251839FAA384E68824A4DD79EF55CE5FD553F5ED8FFA72B308082E0CD57A2` |
| E `backend/src/sketch2life/application/ports/video_playback.py` | Express only an approved revocation check; do not invent token fields or expiry. | Video (person OPEN). | Spec §7 item 4; port review and deny-after-revocation evidence. | No current worktree modification; 3,436; `7621F128D136853F3C9E815A6A70BE250D8D222865861F1F94E03F79023ABE79` |
| E `backend/src/sketch2life/interfaces/http/routers/story_video.py` | Apply current authorization/revocation checks to existing playback/download operations only. | Video/BE1 (persons OPEN). | Spec §7 item 4; API/download/token paths fail closed after revocation. | No current worktree modification; 4,576; `C7FEFFEAD0393444BC9CB8A518E471C0D6F64F3D33D3B540002CA1DC51F48F31` |
| E `backend/src/sketch2life/application/video_review_lifecycle.py` | Fence late video-review/provider outcomes without changing public StoryRun states. | Video/Story (persons OPEN). | Spec §7 items 5–6; late/duplicate output stays non-playable and enters purge. | No current worktree modification; 4,386; `E5A1A17C3D9580FDABF16E55864C18D10C67A6A03A54BA0CD34980691E0514E4` |
| E `backend/src/sketch2life/application/ports/object_storage.py` | Reuse existing byte-delete boundary only after owner contract defines metadata ownership/reference closure. | Storage/Core (persons OPEN). | Spec §7 items 4, 6; idempotent byte deletion plus owner-verifiable reference handling. | No current worktree modification; 1,060; `CEC4214DDF3488D2C996368813B2B74D24C525ED86371E70D89F8AA9FA6EC9A4` |
| E `backend/src/sketch2life/infrastructure/storage/s3_compatible.py` | Implement object deletion only through the existing storage adapter after Core contract approval; no provider call in planning. | Storage (person OPEN). | Spec §7 items 4, 6; synthetic deletion/retry evidence under separate approval. | No current worktree modification; 3,568; `43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B` |
| E `backend/tests/contract/test_app_composition.py` | Verify the approved lifecycle route composition only; preserve pre-existing M2 tests/edits. | BE test owner OPEN. | Spec §7 items 1, 2, 7; route is owner-scoped and only approved operations are mounted. | DIRTY M2; 13,507; `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` |
| E `backend/tests/contract/test_openapi_contract_catalog.py` | Read-only contract verification only; any change to fix the known shared mapper/tag issue is expressly out of scope. | API-contract test owner OPEN. | Spec §7 items 1, 7; only after separate mapper issue is resolved under separate approval. | DIRTY M2; 18,753; `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` |
| E `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` | Update only a separately approved route inventory if its documented baseline requires it; no unrelated route changes. | FEAT-059 evidence maintainer OPEN. | Spec §7 items 1, 7; exact approved route inventory and reproducible source. | DIRTY M2; 9,248; `689023BE3130F156CC6C458242DD11F68FDFBC9CC19E0AAC7174B21F9BBB34E5` |
| E `docs/context/PROJECT_CONTEXT.md` | Append a verified FR-C-08 status reference only after implementation/review; retain current local work. | Project context maintainer OPEN. | Spec §7 item 10; status matches pinned evidence and keeps open gates. | DIRTY (M2/Rev68 context); 83,919; `B53D00641590E5B0DB7D6D19603AB796F19658F9F3F6AD8BC31076FDF51D631D` |
| E `docs/context/SOURCE_REGISTER.md` | Add verified source/evidence pointers only after separately approved work; retain current local work. | Source-register maintainer OPEN. | Spec §7 item 10; every cited pin resolves and is classified. | DIRTY (M2/Rev68 context); 116,802; `AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B` |
| E `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | Record only later approved task status/outcome; no edit in planning. | FEAT-063 coordinator OPEN. | Spec §7 item 10; report agrees with reviewed evidence. | No current worktree modification; 113,670; `7137B59263B7B886F3EB5A18D741DB08F976E3E08947C7BE80679ED3FE50EDEF` |
| E `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md` | Add later verified lifecycle source and evidence entries only. | FEAT-063 coordinator OPEN. | Spec §7 item 10; exact source/report pins resolve. | No current worktree modification; 66,896; `08A0AE379D87CD237A923F921E2FC7F1385BAAE63C74F264FEBD24721FC1EED1` |

The E list is a candidate list, not permission to change every file. A future launch must narrow the selected rows to the resolved contract. The two M2-dirty context files, M2 code/tests, route baseline, and approval/evidence overlays are collisions that must be frozen/reconciled first; see §7. No missing Core-owned metadata/reference-resolution path is guessed or added.

### 4.2 Proposed N paths — new-file candidates

Every N path was absent at this observation; a future launch must repeat the absence check and stop if any path exists. No new route, API schema, migration, audit table, or provider adapter is proposed.

| Class / exact path | Purpose and trace | Module owner (named owner) | Future acceptance evidence | Current status |
|---|---|---|---|---|
| N `backend/src/sketch2life/application/ports/story_run_lifecycle.py` | Candidate Story boundary only if an approved design assigns lifecycle orchestration there; Rev68 FR-C-08/event catalog. | Story (person OPEN). | Spec §7 items 3, 5–8; typed contract, no cross-owner SQL or invented fields. | ABSENT |
| N `backend/src/sketch2life/application/services/story_run_lifecycle.py` | Candidate coordinator for approved cancel/DELETE sequencing; does not choose routes, receipts or states. | Story/BE1 (persons OPEN). | Spec §7 items 1–5, 7; authorization, transaction and idempotency evidence. | ABSENT |
| N `backend/src/sketch2life/application/services/story_run_purge_worker.py` | Candidate worker only after BE1/Core/Lesson contracts and retry ownership are approved; no status/progress model implied. | BE1 coordinator with owner modules (persons OPEN). | Spec §7 items 5–9; retry, partial failure, shared-reference, restart, and terminal predicate evidence. | ABSENT |
| N `backend/tests/contract/test_parent_story_lifecycle_contract.py` | Synthetic contract coverage only for routes/fields selected by approved Rev68 contract. | BE/API test owner OPEN. | Spec §7 items 1–4, 7–10; status, auth, replay, revocation, and audit assertions. | ABSENT |
| N `backend/tests/unit/test_parent_story_lifecycle_service.py` | Fake-port sequencing, transaction boundary, authorization and failure tests. | Story/BE1 test owner OPEN. | Spec §7 items 2–5; no cross-owner call leakage. | ABSENT |
| N `backend/tests/unit/test_parent_story_lifecycle_repository.py` | Synthetic lifecycle fence/receipt tests only if approved repository boundary requires this file. | Story test owner OPEN. | Spec §7 items 3, 5, 7; replay, concurrency and no-write-after-fence evidence. | ABSENT |
| N `backend/tests/unit/test_parent_story_purge_worker.py` | Fake-only owner-module deletion traversal, retry, shared-reference and restart tests. | BE1/Core/Lesson test owners OPEN. | Spec §7 items 6–9; no shared/unrelated object deletion and correct DELETED predicate. | ABSENT |
| N `backend/tests/integration/test_parent_story_lifecycle_synthetic.py` | Synthetic isolated integration only after separate database/storage approval and exact environment pin. | Integration owner OPEN. | Spec §7 items 1–10; isolated persistence/restart and cross-module evidence. | ABSENT |
| N `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_REPORT_20261115.md` | Record a later authorized launch, exact pins, actual outputs and remaining gaps. | FEAT-063 coordinator OPEN. | Spec §7 item 10; reproducible output and accurate status. | ABSENT |

No candidate E/N path resolves the missing Core Asset metadata/lineage deletion and independent-reference contract or the Parent-scope receipt/schema blocker. If resolving either requires an additional file, stop and obtain an owner-reviewed allowlist revision; do not add the path ad hoc.

### 4.3 H paths — frozen or read-only

These are not editable under this proposal. The exact reference files include:

| Exact H path | Current bytes / SHA-256 | Boundary |
|---|---|---|
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 639,948 / `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` | Frozen unsigned canonical Rev68. |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` | 171,609 / `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2` | Frozen companion model source; no schema change. |
| `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 216,212 / `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` | Frozen through D-208. |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 410,676 / `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` | Frozen M2-only approvals; no FR-C-08 approval. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 / `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | Frozen PARTIAL / NOT COMPLETE M2 report. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 / `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` | Frozen M2 specification only. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_DRAFT18_COLD_REVIEW_20261114.md` | 5,169 / `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` | Frozen M2 review only. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md` | 14,768 / `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` | Frozen M2 paths/ceilings; no transfer. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_ALLOWLIST_COLD_REVIEW_R2_20261114.md` | 2,715 / `6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D` | Frozen M2 review; no transfer. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261115.md` | 44,643 / `82978E82A2A07A94007E7574BC43FA45663CA3B03D72FAEFDD24C15964D01800` | Historical proposal, unchanged. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_DRAFT3_COLD_REVIEW_20261115.md` | 10,047 / `83270D1A6FE19FAE42CB4C405A9DDB3B2298E181261C9B740F0DA9F0F5C26658` | Frozen independent review evidence. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md` | 20,115 / `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA` | Historical M5/M6 context only. |
| `backend/src/sketch2life/application/ports/core_foundation.py` | 5,512 / `2F6F55A0C576AF78DCB24219254DE6DE3C9063C4A868D0B27F2D91356268FB13` | Read-only evidence; `CoreAssetMetadataPort` exposes save/get but no reference-resolution/delete operation. |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py` | 24,471 / `AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94` | Read-only evidence; current store exposes metadata save/get but no lifecycle deletion/reference-closure operation. |
| `backend/src/sketch2life/infrastructure/persistence/core_models.py` | 11,578 / `47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A` | Read-only evidence; Core deletion/reference-resolution contract is absent. |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | 12,426 / `12F6CE1EDAB047EFDD81D495B44DF08DC6F990692860621F37FC73778006F888` | Read-only mapped job/notice evidence; no DDL. |
| `backend/src/sketch2life/infrastructure/persistence/be1_parent_role_adapter.py` | 1,507 / `1B83B95341D7AD98360CC98AF640CFAF5750A21FCE4CE971F0EE2D1DF66795E1` | Read-only; production BE1 role adapter remains NOT COVERED under D-190. |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 / `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` | Read-only; shared OpenAPI mapper/tag issue has separate scope. |
| `backend/src/sketch2life/interfaces/http/routers/ai_jobs.py` | 3,872 / `8F90789FE6BC5ABBD5B1F2D489C201DD99DEF252AD2182D591A2BECBBC7641B6` | Read-only; no separate `/jobs` route selected by this task. |
| `backend/tests/contract/test_parent_story_run_cancel_route.py` | 3,601 / `98B4522D441F223F4BC6A17256982B4E3E9484D7EE1692A753162DDBF17CBBDE` | Existing untracked M2 test; preserve; not purge-lifecycle coverage. |
| `backend/tests/unit/test_parent_story_run_cancel_repository.py` | 10,111 / `A7CE542F352E9E51A0C5B32444240E6A84866C7452293BFBE15EB38E02689D9E` | Existing untracked M2 test; preserve; not purge-lifecycle coverage. |
| `backend/tests/contract/test_parent_ai_late_result_guards.py` | 3,467 / `7C9EF0E89B77E1566A33C386854174A56E9BABB88732A94BDB499898D42D2BEC` | Existing untracked M2 test; preserve; does not prove video/job lifecycle coverage. |
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | 17,501 / `7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF` | Separate FEAT-047 overlay; never edit under FR-C-08. |

### Frozen migration references — no migration is E or N

| Exact H path | Static revision relationship | Current bytes / SHA-256 |
|---|---|---|
| `backend/alembic/versions/20261014_0001_core_persistence.py` | `20261014_0001`, base | 11,186 / `55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C` |
| `backend/alembic/versions/20261014_0002_be1_runtime.py` | `20261014_0002` after `20261014_0001` | 10,959 / `08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520` |
| `backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py` | `20261015_ai_0001`, separate base | 13,321 / `D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714` |
| `backend/alembic/versions/20261028_ll_0001_lesson_library.py` | `20261028_ll_0001`, separate base | 19,803 / `733836723A95834C721E6CD0CA3527D73EA6EFE089B2F109A956EA484DFE1D83` |
| `backend/alembic/versions/20261102_story_run_lite.py` | `20261102_story_run_lite`, separate base | 28,335 / `D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143` |
| `backend/alembic/versions/20261104_story_revisions.py` | `20261104_story_revisions` after `20261103_story_upload_compat` | 8,529 / `3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8` |
| `backend/alembic/versions/20261112_parent_story_context.py` | `20261112_parent_story_context` after `20261104_story_revisions`; source has empty-`story.runs` baseline guard | 8,251 / `CFC7A92436066191134E27F1579B54109057CBAC43ABEB72B84C0F2D6CBFD9DF` |

These are file/source observations only. No migration graph/head, applied revision, or task-database contents were queried. If the resolved design needs a lifecycle work-item/checkpoint, typed Parent-scope row, audit mapping, ownership/refcount field, retention field, or state value not already represented, that is a blocker for DTR amendment and a separately approved migration task. Do not add DDL or run Alembic under this proposal.

## 5. Open issues, blockers, and exact owner questions

The ten rows below carry all nine issue themes from Lifecycle Plan Draft 2 section 7 and Specification Draft 3 section 8; the former ownership issue is split into technical contract ownership and named-person accountability. D-208 resolves only the policy directions it states. It does not supply missing technical contracts, schemas, module owners, or evidence. Evidence labels distinguish document/decision observations, static source/DTR inspection, and test output recorded in the pinned M2 report. Runtime, database, token/cache, purge, and provider behavior are not inferred from static inspection.

**Gate definitions:** **B-IMPLEMENTATION** is a missing behavior/contract that prevents safe implementation of the affected work and prevents an approval from authorizing it. **G-IMPLEMENTATION** is a separate coordination prerequisite before implementation may rely on a baseline. **G-LAUNCH** is a governance/accountability condition required before launch, but not by itself a technical design blocker. A technical ownership or contract gap remains B even when named-person assignment is separately G-LAUNCH.

| # / open issue | (a) Verified facts and evidence class | (b) Missing decision or contract | (c) Gate effect | (d) Precise owner question |
|---|---|---|---|---|
| 1. Lifecycle read: existing owner-scoped read is the default; no new route is selected by inference. | **Document/decision:** Rev68 section 21.2 and D-208 select `GET /v1/story-runs/{id}` by default and permit proposing another read only if it is insufficient. **Static source:** Draft 2 section 4 inventories the Parent route and response schema; no runtime purge/read proof is recorded. | Confirm whether the existing response distinguishes `DELETE_PENDING` from `DELETED` backed by verified purge evidence, and which owner-owned evidence establishes that predicate. If insufficient, an exact response/route contract is needed. | **B-IMPLEMENTATION:** read contract and terminal predicate must be settled before implementing or approving this behavior. No route or field is inferred. | Can the owner accept the existing owner-scoped GET contract as exposing `DELETE_PENDING` until required purge is verified and `DELETED` only afterward? If not, what exact read-contract change is approved for a later allowlist? |
| 2. Internal lifecycle model: public StoryRun remains `DELETE_PENDING` until verified purge, then `DELETED`; BE1 lifecycle-request, AiJob, and purge-worker states remain separate. | **Document/decision:** Rev68 and D-208 prohibit inventing public states or progress percentages. **Static source:** Draft 2 section 4 inventories distinct StoryRun and AiJob models; worker/reconciliation runtime behavior is not verified. | Identify existing internal values and durable evidence for queued, running, retryable failure, unresolved external deletion, and completion. If missing, a separately reviewed SRS/DTR contract is needed. | **B-IMPLEMENTATION:** safe progression and reconciliation cannot be implemented or approved by guessing; DTR/schema review is separate if needed. | Which already-defined internal values and persisted evidence represent each purge phase and retry/reconciliation outcome? If none fit, what owner-approved contract/DTR revision should be prepared before implementation? |
| 3. Parent scope, receipt, and cross-module contract | **Document/decision:** D-208 requires typed `PARENT_ACCOUNT`, forbids fabricated `organization_id`, and assigns BE1 coordination, Story transition/event, and Core Asset deletion/reference resolution. **Static source/DTR:** Draft 2 section 4 records no approved physical Parent-scope mapping or durable receipt contract; existing BE1 lifecycle-request mapping may not represent Parent scope. No database was queried. | Versioned cross-module request contract, physical Parent-scope representation, durable receipt owner/schema, and exact module boundary remain unresolved. Any unmapped field/table requires separate DTR/schema review and approval. | **B-IMPLEMENTATION:** blocks request/receipt implementation and approval for it; possible separate DTR/schema gate. No route, receipt field, organization ID, or DDL is inferred. | Which existing versioned contract carries typed `PARENT_ACCOUNT` without `organization_id`, and which module owns the durable request and receipt? If none fits, what exact DTR/schema proposal should be reviewed separately? |
| 4. Named accountable owners | **Document/decision:** D-208 assigns domain responsibilities but not people and requires named accountable module owners before launch. Draft 2 sections 3 and 4 record responsibility boundaries. | Names for BE1 coordination, Story transition/event/fence, Core Asset deletion/reference resolution, AI Jobs cancellation, Lesson occurrence update, and HTTP/test integration remain OPEN. This does not resolve or downgrade technical contracts in issue 3 or other B rows. | **G-LAUNCH only:** named-person assignment is required before launch. By itself it does not block drafting, technical design, or implementation approval; technical ownership/contracts remain separate blockers. | Which named accountable individual accepts each D-208 responsibility area (BE1, Story, Core Asset, AI Jobs, Lesson, and HTTP/test integration), and where will that assignment be recorded before launch? |
| 5. Teacher authorization | **Document/decision:** D-208 requires current Parent owner or currently assigned Teacher, checked against current BE1 assignment/version; former Teacher and creator provenance grant no authority. **Static source:** Draft 2 section 4 records production BE1 role adapter as NOT COVERED under D-190. | Exact assignment/version source, route/application adapter, recheck points across commands/reads, and revocation evidence are not established. | **B-IMPLEMENTATION:** authorization cannot be safely implemented or approved until the enforcing adapter and evidence are selected. | Which BE1 assignment/version source and adapter authorize cancel, DELETE, lifecycle reads, playback/download, upload, and dispatch, and what evidence proves denial after reassignment? |
| 6. Immediate access revocation | **Document/decision:** Rev68/D-208 require immediate fencing of API, download, playback-token, cache/stream, upload/partial-upload, and job-dispatch access on accepted cancellation. **Static source:** Draft 2 inventories related code paths, but records no runtime revocation evidence. | Per-path invalidation for issued grants/tokens, cached/streaming responses, active upload sessions/parts, and queued dispatch remains unresolved, including fail-closed behavior on delay. | **B-IMPLEMENTATION:** blocks implementing and approving acceptance-time revocation; static path presence is not proof of revocation. | What existing owner contract invalidates each active access path at acceptance, what is the fail-closed rule for delay/failure, and what synthetic evidence demonstrates denial? |
| 7. State/action mapping | **Document/decision:** D-208 permits cancel only for the 13 unfinished Rev68 UC-11 states; explicit user DELETE for `COMPLETED`, `FAILED`, and `ABANDONED`; no auto-purge for the latter two; neither command for `DELETE_PENDING`/`DELETED`. Rev68 has an 18-state inventory. | Mapping existing source/adaptor states to cancel, explicit delete, or neither must be confirmed. `SCRIPT_GENERATION_UNKNOWN` is outside Rev68's 18 states and must not be invented as a replacement. | **B-IMPLEMENTATION if current mapping cannot meet the contract:** resolve using existing values; if a new public/domain state is needed, stop for separate owner/SRS decision. | How do existing adapters map all 18 states to these actions, and handle `SCRIPT_GENERATION_UNKNOWN` as an existing compatibility condition without adding a state? If impossible, what separate owner decision is required? |
| 8. Storage, sharing, retry, and retention | **Document/decision:** D-208 requires owner-module purge, removal of run reference before retaining a shared asset, positive verification of a valid independent reference, idempotent retry, and no unsupported provider/backup deletion claim. **Static source:** Draft 2 section 4 records object-byte deletion, while current Core metadata port/store lack deletion/reference-closure operations. No object/provider deletion was run. | Exact Core reference enumeration, metadata/lineage deletion and closure, incomplete-upload deletion, retry/reconciliation evidence, and provider-copy/backup treatment remain unresolved. | **B-IMPLEMENTATION:** Core reference/deletion contract blocks safe purge implementation/approval. **Separate DTR/schema gate** if required mappings/work state are absent. Provider/backup claims stay unverified. | Which exact owner ports enumerate/remove run-owned references/objects, prove closure, classify retries, and verify an independent shared reference? What separately approved evidence/policy is required for provider copies and backups? |
| 9. M2 baseline | **Test output in pinned report:** M2 is PARTIAL / NOT COMPLETE; combined targeted pytest exited 1 with 81 passed, one OpenAPI tag failure, and an app-composition `tmp_path` `WinError 5`; report records 335 mypy errors in 63 files and 17 Ruff diagnostics. No FR-C-08 lifecycle test is established. | Reconcile and pin the dirty M2 baseline and record which S2 code/evidence may be relied on. M2 approvals, allowlist, and command ceilings do not transfer. | **G-IMPLEMENTATION coordination gate:** do not rely on M2 as a ready baseline before separate reconciliation. FR-C-08 contract gaps remain independent blockers. | Who will freeze/reconcile the current M2 worktree, identify reusable code without treating S2 as complete, and pin which evidence is accepted for FR-C-08? |
| 10. Audit and retention | **Document/decision:** Rev68 section 31.10(17) defines metadata-only audit and 180/365-day targets; D-208 preserves categories/exclusions and leaves permissions/mapping OPEN-TECHNICAL. **Static DTR/source:** no approved physical audit mapping or record-type-to-duration map is identified. | Exact field allowlist, audit readers, physical storage/owner mapping, and mapping of record types to 180 versus 365 days remain unresolved. | **B-IMPLEMENTATION** for required audit behavior; **G before completion** until access and retention mapping is evidenced. No field, permission, storage, or duration exception is inferred. | Which exact audit fields/readers are approved, which existing physical owner stores them, and which record types map to 180 versus 365 days? Where will the owner-approved mapping be recorded? |

The pinned M2 implementation report records that the final authorized combined test invocation exited 1: 81 passed, one OpenAPI catalog tag assertion failed, and the app-composition test errored during `tmp_path` setup with `WinError 5`. It also records 335 mypy errors in 63 files and 17 Ruff diagnostics. These are non-passing M2 results, not FR-C-08 verification; no M2 command ceiling or approval transfers.

All proposed gate ordering and dates remain proposals, not commitments. D-208 requires M2 baseline reconciliation as a separate coordination gate before FR-C-08 implementation and named accountable owners before launch. The launch-only named-person gate does not waive the implementation blockers listed above.

## 6. Migration and schema disposition

No migration is E or N. The seven migration files in §4.3 are frozen references, not a complete graph audit and not proof of applied database state. The existing StoryRun Lite migration has an empty-`story.runs` baseline guard; no migration command or database access is authorized. Current DTR rows identify BE1 lifecycle requests, Core asset metadata/lineage, upload data, Lesson occurrences, and typed owner scope, but they do not close the physical Parent-scope/receipt or Core deletion/reference contract.

If an approved lifecycle requires unmapped request fields, durable work-item/checkpoint state, actor/scope constraints, Core reference/lineage deletion, audit fields/permissions, or a new state, stop before code. First obtain the required owner contract and DTR amendment, then a separate exact migration plan and database authorization. Do not infer that current task data is empty or compatible.

## 7. Pre-existing dirty-path collision register

All rows below were already dirty before Draft 2 and must remain untouched during planning. The D-207 pins show the older M2-approved baseline; the “current observation” column was rehashed for this draft. A changed dirty-source pin is a changed implementation snapshot, not a reason to repair or reset it. Reconcile/freeze the branch before any FR-C-08 edit.

| Path | D-207 M2 baseline | Current observed | Disposition |
|---|---|---|---|
| `backend/src/sketch2life/application/ports/parent_story_runs.py` | 6,140 / `374E2B4003164C90A2C55F06DE8A9FE8F970BE393806D143C9DF4BF6E06BF77F` | 6,601 / `6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4` | DIRTY M2; includes cancel contract; freeze/reconcile. |
| `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | 7,309 / `C026A1566500EE7B7C2705DFCE6C4E0D0EC7B397E9FE93F11A237A416F768B19` | 7,889 / `1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749` | DIRTY M2; freeze/reconcile. |
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 64,452 / `407D2843A93C31BD54202A1E504DE938FB085E67730C199FD4E9B9505E72B832` | 69,489 / `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` | DIRTY M2; cancel and selected late-result guards; no purge worker. |
| `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | 12,698 / `32C707515032FC7BEF08A12D0B1D8E6DD4271FF1B9C55891072BA76E150D6B60` | 14,626 / `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` | DIRTY M2; cancel route only; freeze/reconcile. |
| `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | 21,869 / `8EEDD486148E16350885DBD737C5A3A0F7A4E0906AD473165FBEDB84C7CAC1FE` | 23,082 / `E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30` | DIRTY M2; selected story/artwork guards only; video lifecycle remains separate. |
| `backend/src/sketch2life/interfaces/http/app.py` | 73,534 / `262CB4583ED545F92DF784B69D426C834D5D7BD23179A61C5C818E6C50F4C298` | 74,637 / `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` | DIRTY M2 plus separate FEAT-047 overlay; do not alter unrelated formatter scope. |
| `backend/tests/contract/test_app_composition.py` | 13,451 / `B738F3BF89D233544FB062D5DB50AED6A8B6DD7A92C0B7020E72E138569D877B` | 13,507 / `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` | DIRTY M2; prior `WinError 5` setup recorded; use only future proposed temp/cache mitigation. |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,721 / `B585C2A87DC50FE6B9571B0AA5DDFB0D0F2918FE69D04749EAE5C9BAEC998255` | 18,753 / `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` | DIRTY M2; OpenAPI mapper/tag discrepancy is separately scoped and not fixed here. |
| `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` | 9,157 / `A0CB85E214E80BED8EE9AEEF665CC9979F579553BD9117D0D8D682DF641AD8F5` | 9,248 / `689023BE3130F156CC6C458242DD11F68FDFBC9CC19E0AAC7174B21F9BBB34E5` | DIRTY M2 route baseline; preserve until coordinated. |
| `docs/context/PROJECT_CONTEXT.md` | 83,183 / `317D947803D78F1F78D2DA9BEA8E9DF3F718DE8965DFD57E1A665A0A5F1BE612` | 83,919 / `B53D00641590E5B0DB7D6D19603AB796F19658F9F3F6AD8BC31076FDF51D631D` | DIRTY context update for Rev68/current work; preserve, no overlapping edit. |
| `docs/context/SOURCE_REGISTER.md` | 115,027 / `0093F8CCE26A526D72C8B940BE8CCE250DB78A9AE852B4834F3ABB639965081A` | 116,802 / `AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B` | DIRTY context update for Rev68/current work; preserve, no overlapping edit. |

Other pre-existing M2 source/tests, FEAT-047 approvals/evidence, FEAT-059 route data, checkpoint and all untracked evidence remain untouched. In particular, `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py`, the OpenAPI mapper/tag correction, and mobile paths are out of scope. There is no implementation approval for this candidate set.

## 8. Proposed future verification commands and ceilings

Every command in this section is **PROPOSED / NOT AUTHORIZED / NOT RUN**. These are fresh FR-C-08 suggestions; they are not inherited from D-207 or any consumed S2 ceiling. An owner launch prompt must pin the interpreter and final command selections. Use only already-installed local tools. No command below was executed for Draft 2.

### Pytest temp/cache handling

The proposed `--basetemp` parent is the existing ignored repository-root directory `tmp/m2-s2-validation`; each invocation gets a new GUID child. Before running, check that the parent directory and pinned Python executable exist. Do not create a replacement parent, change ACLs, use the default Windows temp location, or retry elsewhere. Use `-p no:cacheprovider` to prevent `.pytest_cache` writes. Existence does not prove effective write permission; stop if the parent is missing or inaccessible. Do not print credential/environment values.

Run these from the M2 worktree root only after separate implementation approval, with an independent new GUID per invocation:

```powershell
$runId = [guid]::NewGuid().ToString('N')
$scratchParent = '..\..\tmp\m2-s2-validation'
$python = '..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $scratchParent -PathType Container)) { throw 'Approved pytest basetemp parent is missing' }
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Pinned Python environment is missing' }
$base = Join-Path $scratchParent "frc08-contract-$runId"
& $python -m pytest -q --basetemp $base -p no:cacheprovider backend/tests/contract/test_parent_story_lifecycle_contract.py backend/tests/contract/test_app_composition.py backend/tests/contract/test_openapi_contract_catalog.py
```

**Contract selection ceiling: 2 combined invocations total** (one initial, one final after an approved fix). The OpenAPI catalog test has a recorded shared mapper/tag failure; this lifecycle allowlist does not fix it. That test remains a known prerequisite/expected failure until a separate authorized mapper resolution exists. The recorded `tmp_path` `WinError 5` is addressed only by the proposed unique basetemp and disabled cache; stop if access is denied.

```powershell
$runId = [guid]::NewGuid().ToString('N')
$scratchParent = '..\..\tmp\m2-s2-validation'
$python = '..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $scratchParent -PathType Container)) { throw 'Approved pytest basetemp parent is missing' }
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Pinned Python environment is missing' }
$base = Join-Path $scratchParent "frc08-unit-$runId"
& $python -m pytest -q --basetemp $base -p no:cacheprovider backend/tests/unit/test_parent_story_lifecycle_service.py backend/tests/unit/test_parent_story_lifecycle_repository.py backend/tests/unit/test_parent_story_purge_worker.py
```

**Unit selection ceiling: 2 combined invocations total** (one initial, one final after an approved fix).

```powershell
$runId = [guid]::NewGuid().ToString('N')
$scratchParent = '..\..\tmp\m2-s2-validation'
$python = '..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $scratchParent -PathType Container)) { throw 'Approved pytest basetemp parent is missing' }
if (!(Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Pinned Python environment is missing' }
$base = Join-Path $scratchParent "frc08-integration-$runId"
& $python -m pytest -q --basetemp $base -p no:cacheprovider backend/tests/integration/test_parent_story_lifecycle_synthetic.py
```

**Integration ceiling: 1 invocation**, only after separate owner approval for an isolated synthetic database/storage environment and exact environment pin. No shared/task database is authorized by this draft.

### Typecheck and lint

Run from `backend/`, after separate implementation approval:

| Check | Exact command | Proposed ceiling | Status |
|---|---|---:|---|
| Mypy | `& ..\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe -m mypy src/sketch2life` | 1 | PROPOSED / NOT AUTHORIZED / NOT RUN; compare with recorded M2 baseline, never call that baseline a pass. |
| Ruff | `& ..\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe -m ruff check src/sketch2life` | 1 | PROPOSED / NOT AUTHORIZED / NOT RUN; do not auto-fix. |

### Final repository checks

Run from the M2 worktree root only after a future implementation approval:

| Check | Exact command | Proposed ceiling | Status |
|---|---|---:|---|
| Harness | `& .\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe tools/validate_harness.py` | 1 final | PROPOSED / NOT AUTHORIZED / NOT RUN |
| Architecture | `& .\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe tools/validate_architecture.py` | 1 final | PROPOSED / NOT AUTHORIZED / NOT RUN |
| Repository security | `& .\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe tools/validate_repository_security.py` | 1 final | PROPOSED / NOT AUTHORIZED / NOT RUN |
| Whitespace | `git diff --check` | 1 final | PROPOSED / NOT AUTHORIZED / NOT RUN |

No Alembic/migration, database query, server, Docker, install, network, provider, Modal, Android, emulator, stage, commit, or push command is proposed as authorized. These ceilings are proposals; the owner must separately authorize exact commands. `OWNER_MODAL_CALL_APPROVED=NO`.

## 9. Stop conditions and implementation gates

Stop before any implementation edit if any strict input pin changes without a clearly authoritative newer source; if the branch, worktree ownership, or path state differs; if an E path still contains M2/FEAT-047 edits that cannot be safely isolated; if an N path is present; if any owner/contract blocker in §5 remains unresolved for the behavior being implemented; if an unlisted path is needed; if typed Parent scope cannot be represented without a fake organization; if Core Asset cannot resolve references/delete metadata under an approved contract; if existing reads cannot prove pending versus verified deletion; if current Teacher assignment/revocation, immediate access fencing, late-result behavior, shared-asset safety, or the `DELETED` predicate cannot be evidenced; if the design needs unapproved schema/DDL, a new state/field/event/route, invented retention mapping, or real-data/provider/Modal access; or if a command/environment is outside §8.

Implementation may be considered only after all of the following separate gates pass:

1. A fresh independent review accepts this allowlist proposal and identifies no actionable P1/P2 or implementation blocker.
2. The owner resolves implementation-blocking questions in §5 through authoritative pinned sources; the Parent-scope and Core Asset contracts are explicit, and DTR/schema work is separately authorized if required.
3. Named accountable module owners are recorded before launch, as D-208 requires. This is a governance gate, not a waiver or reclassification of the technical ownership/contract blockers in section 5.
4. The M2 partial/dirty baseline is reconciled as a separate coordination gate; M2 approvals, paths, and command ceilings are not reused.
5. A separate FEAT-063 implementation Task Approval records exact reviewed allowlist pins, selected E/N paths, and exact command ceilings; a pinned owner launch prompt follows.

None of these gates is satisfied by this document or by the owner’s conditional task instruction. No code work may begin on a clean document review alone.

## 10. Changes from Allowlist Draft 2

- **P2-01, named-owner timing:** section 5 classifies named-person assignment as G-LAUNCH, as D-208 requires, while Parent-scope, receipt, module-contract, and other technical ownership gaps remain B-IMPLEMENTATION blockers. Section 9 keeps the launch gate separate.
- **P2-02, approval ledger:** section 2 describes the D-205/D-207 M2 approvals and separate FEAT-047 overlay plus one-time S2 verification authorization. None authorizes FR-C-08 implementation.
- **P3-01, Draft 1 history:** section 2 cites Draft 1 section 3's parent-router E-path row as a path-selection boundary: it did not select a completed-delete route and did not define DELETE eligibility. This draft derives eligibility from Rev68/D-208 only. Specification Draft 3 section 9 contains a completed-run-only characterization not supported by Draft 1 section 3; Specification Draft 3 is unchanged and that characterization is not used as historical evidence here.
- Replaces the open-issue table with ten rows that separate verified facts, missing decisions/contracts, gate effects, and precise owner questions. All nine carried issue themes remain; technical ownership and named-person accountability are separate.
- Preserves Rev68/D-208 lifecycle rules: exactly 13 cancel states; explicit DELETE for COMPLETED/FAILED/ABANDONED; no automatic purge of FAILED/ABANDONED; DELETE_PENDING until verified; and all authorization, revocation, purge, sharing, quota/sample, and audit limits.
- Retains M2 as a separate partial/dirty coordination gate. No M2 approval, allowlist, or command ceiling transfers.
- No source, test, SRS, DTR, decision, approval record, prior allowlist, or prior review was changed. No implementation or launch is authorized.

## 11. Status

**PROPOSED / BLOCKED FOR IMPLEMENTATION / NOT APPROVED / NOT LAUNCHED.** This allowlist draft does not authorize implementation, tests, typecheck, lint, validators, database/migration work, DDL, provider/Modal calls, gates, staging, commit, push, or launch. FR-C-08 is NOT STARTED. `OWNER_MODAL_CALL_APPROVED=NO`.
