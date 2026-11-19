# FR-C-08 Parent StoryRun lifecycle — implementation allowlist Draft 11

**Status: PROPOSED / DRAFT / NOT APPROVED / NOT LAUNCHED.**
**Date:** 2026-11-19.
**Purpose:** the exact paths, classes and command ceiling for the first, Parent-only FR-C-08
implementation under Contract Draft 9. It authorizes nothing; the owner's implementation approval
is a separate record.

**Change from Draft 10:** the base is the owner-confirmed `03342207` (D-216 item 2) instead of the
provisional `2dddc607`; D-218 moved the schema delta, migration, response schema, Core port and
the delete route **into** scope, so the exclusions of Draft 10 §7 that D-215 to D-218 settled are
removed and their paths become E or N; the AI Jobs worker, reconciler and dispatcher and the video
paths move to H (no Parent AI job or video exists at the base); `app.py` moves to H (the delete
route lives in the existing Parent router). R5-F5: "now" removed from the authority text, and
`bounded_image_upload.py` is described as a frozen 413-envelope reference listed only because
CONV-1 modifies it. Every pin was recomputed with `git show 03342207:<path>`; the register is the
local, git-ignored `tmp/frc08-cp9/pins.tsv`.

## 1. Authority and base

- Contract: `plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT9_20261119.md`.
- Decisions D-214 to D-218 (FEAT-063 `DECISIONS.md` working tree, 260,722 bytes,
  `6F6DC3291E9AF96FD26400AFD8F4837F02FB7B9856086F79F19485CD6E6E9AE0`).
- DTR Draft 6 (`E4B25542…`) and Core port design Draft 6 (`C8EDD923…`), approved as directions
  by D-218 A-1.
- Base: local branch `feature/feat066-conv1`, commit `03342207ab10379e6c53449274edaf4d9bcf60e4`
  (owner-confirmed, D-216 item 2). Implementation runs on a new local branch cut from that commit;
  if the branch moves before launch, every pin is recomputed.

## 2. E — existing files that may be edited (34)

| Exact path | Bytes / SHA-256 at `03342207` | Purpose and boundary |
|---|---:|---|
| `backend/src/sketch2life/application/ports/parent_story_runs.py` | 6,601 / `6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4` | Lifecycle record type with optional profile fields; projection record (DTR §5.8). |
| `backend/src/sketch2life/application/services/parent_story_runs.py` | 7,630 / `FED7AC29F02C34F19F093AF471017447F5E5FA3453D399E2A155067609958B14` | Cancel and delete service calls; projection responses. |
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 69,989 / `5E33C076A4A13439AB0D02A8D8088D543D277758E78076D709E23CB386CFBDA8` | Cancel/delete command transaction (event, audit, aggregate, receipt); projection read before input/profile access; replay rules; S16 writers refuse DELETE_PENDING and DELETED (DTR §6.1, §6.5, §7). |
| `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | 14,626 / `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` | New `DELETE /v1/story-runs/{run_id}`; cancel and delete keys via the CONV-1 parser (1-128); lifecycle envelope responses; GET union (Contract §3). |
| `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | 23,082 / `E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30` | State re-check before the first `put_object`; lifecycle error for `read_current_input`; replay branch of `generate_story_revision` (DTR §5.8). |
| `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | 7,889 / `1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749` | `run_state` enum = 18 SRS states + 2 extensions; `ParentStoryRunLifecycleEnvelopeV1` and projection; cancel envelope replaced (D-218 A-3). |
| `backend/src/sketch2life/infrastructure/story_run_lite/tables.py` | 26,995 / `703018AE4BF81D51C565EFC4626ED07C973823E5FB582EF69DA7BB490923F034` | `ck_story_run_state` + DELETED; `ck_story_receipt_operation` + DELETE_RUN; `profile_ref` nullable (DTR §5.4). |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | 28,152 / `515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666` | `DataLifecycleRequestModel` owner scope, nullable organization, Parent completed CHECK (DTR §5.1). |
| `backend/src/sketch2life/infrastructure/persistence/core_models.py` | 11,578 / `47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A` | Owner scope on audit, outbox event and aggregate revision models; NULL ORM default for `owner_scope_ref` (DTR rule 1). |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py` | 24,471 / `AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94` | Scope-keyed aggregate revision and outbox-state reads (DTR §5.8). |
| `backend/src/sketch2life/infrastructure/persistence/outbox.py` | 6,653 / `0C09BA3B69B1C2EC0D71133C6307BCBFC2902287B287DAF11E1AF8BA9DC9281B` | `claim_ready` event-type filter; `renew_lease`; `attempt_count` on the claimed envelope (DTR §5.8, §6.3). |
| `backend/src/sketch2life/application/ports/core_foundation.py` | 5,512 / `2F6F55A0C576AF78DCB24219254DE6DE3C9063C4A868D0B27F2D91356268FB13` | Optional organization plus scope on Core records; Core asset purge port and Core upload port types (port design §5). |
| `backend/src/sketch2life/application/ports/ai_jobs.py` | 19,923 / `ACC3E27EA6B3A70E3DE267E4BD892D97FACF02D2B9F994817771BED3F584B3E3` | `CancellationNotice` optional organization, scope, `story_run_ref` (DTR §5.2). |
| `backend/src/sketch2life/application/services/ai_jobs.py` | 72,962 / `15DCD532D56EFF811A7DE937938E8D5F942AC7B29CDE26043A3B572DB02E08AE` | Record a Parent notice that matches no job (DTR §5.2). |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py` | 12,426 / `12F6CE1EDAB047EFDD81D495B44DF08DC6F990692860621F37FC73778006F888` | `cancellation_notice` scope columns and CHECKs (DTR §5.2). |
| `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py` | 37,723 / `07695F0E6817B1057A38482D2D869D871A77CE77594D170642C00EBC2709724A` | `jobs_for_notice` empty for a Parent notice; `record_notice` with scope (DTR §5.2). |
| `backend/src/sketch2life/infrastructure/ai_jobs/fakes.py` | 32,728 / `F1318E236694002BE238FD8CF73BD54D5C27B952A085C8EB9A798EC8E65957E0` | Fake repository parity with the notice change. |
| `backend/src/sketch2life/application/ports/object_storage.py` | 1,060 / `CEC4214DDF3488D2C996368813B2B74D24C525ED86371E70D89F8AA9FA6EC9A4` | `list_keys(prefix)` (port design §5.3). |
| `backend/src/sketch2life/infrastructure/storage/s3_compatible.py` | 3,568 / `43BE1BF9ACC454CF3A027F3AD4D6A5893ED266EB7171B45D0B4EEE9E891E1E8B` | `list_keys` via ListObjectsV2, fail closed (port design §5.3). |
| `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | 54,803 / `4267901AEC9D8F874F035B69FF63F54D965D8A3E4E56CEC739C5C7E019511D4F` | OpenAPI amendments for the FR-C-08 operations only. |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,379,096 / `35801B20DC67630B9AAEEFDD46F82886CD91F34990BA2CCE6C2B3E67B6A989B7` | Backend OpenAPI contract for the FR-C-08 operations only; no unrelated change. |
| `backend/alembic/README.md` | 1,552 / `A2DFEAB8DD7FD0811D91BEDF58510431838E88B012C721D6CF34A47CDAB546FC` | One line: deploy with `upgrade heads`; per-module `upgrade <branch>@head` skips the FR-C-08 revision (DTR §9). |
| `backend/tests/contract/test_parent_story_run_cancel_route.py` | 3,601 / `98B4522D441F223F4BC6A17256982B4E3E9484D7EE1692A753162DDBF17CBBDE` | Cancel route contract under the new envelope and key range. |
| `backend/tests/contract/test_parent_ai_late_result_guards.py` | 3,467 / `7C9EF0E89B77E1566A33C386854174A56E9BABB88732A94BDB499898D42D2BEC` | Late-result guards against DELETE_PENDING and DELETED. |
| `backend/tests/contract/test_parent_story_run_request_contract.py` | 12,286 / `FD2634034ABE6C22536D2D7C7DA5787772B91A9F4D4AAA81420B749D67248FAA` | Request contract for cancel and delete. |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 24,100 / `2B89C3E9CB65BE16E8C4F463023CBF3B3B63A4E89A92BEECE95963242F0F29B4` | Catalog entries for the FR-C-08 operations only. |
| `backend/tests/contract/test_openapi_schema_catalog_mapping.py` | 10,597 / `102B7D26C7E5E791592A953A8EEB0BF3DDA0AAE765BDEB05AE5D12094497BF50` | Schema mapping for the new envelope and projection only. |
| `backend/tests/unit/test_parent_story_run_cancel_repository.py` | 10,111 / `A7CE542F352E9E51A0C5B32444240E6A84866C7452293BFBE15EB38E02689D9E` | Cancel repository behaviour under DTR §6.1. |
| `backend/tests/unit/test_parent_story_repository_postgres_nulls.py` | 7,605 / `63C58CF2201966E4C912B6FF924DFD3BD712A5F84590FFBFDCC1DD9C7756A076` | Nullable `profile_ref` and projection read. |
| `backend/tests/unit/test_ai_job_application.py` | 23,855 / `8488BBFE6FB0B55B189B4E22D385A13C9DD218E66681FCD40AE75EED8E670D80` | Parent notice cases. |
| `backend/tests/unit/test_ai_job_b5_effects.py` | 27,242 / `26D7B18360585AA0B5CD7A2239ED1863524D6D66D286882CE6FE9273D64E794F` | Notice construction parity. |
| `backend/tests/integration/ai_jobs/test_notice_coverage.py` | 9,526 / `999CEF97DA6D0B34E8303F8DE754C7372184D526138E32B1B72934889857EB9F` | Notice coverage with the scope columns. |
| `backend/tests/integration/lesson_library/test_lesson_library_api.py` | 51,393 / `C351BA5ED6A432EA2F6C7F69CC3BADD0EC2CC3A9FE9380A344D1120F6AD1CC94` | Storage fake gains `list_keys` only. |
| `backend/tests/integration/test_m2_s2_g1_parent_story_postgres.py` | 47,847 / `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2` | `_EXPECTED_VERSION_ROWS` and the cancel/GET body assertions (lines 746, 1026, 1039). |

## 3. N — new files (15)

All 15 paths were checked absent at `03342207`, in the `.worktrees/conv1` working tree and in
the root working tree.

| Exact path | Purpose |
|---|---|
| `backend/alembic/versions/20261120_frc08_lifecycle_scope.py` | The single migration of DTR §9 (date set at approval). |
| `backend/src/sketch2life/application/ports/story_run_lifecycle.py` | Story lifecycle port, `RunAssetReferencePort`, `LIFECYCLE_NS` (DTR rule 6, §5.8). |
| `backend/src/sketch2life/infrastructure/persistence/story_lifecycle_store.py` | Story lifecycle adapter (plan, purge content, finalize, state, references). |
| `backend/src/sketch2life/infrastructure/persistence/core_lifecycle_store.py` | Core asset purge and upload-close adapters (port design §5-§6). |
| `backend/src/sketch2life/application/services/be1_lifecycle_consumer.py` | BE1 lifecycle consumer: steps 0-6, token rule, leases, CAS, retry (DTR §6.2-§6.3). |
| `backend/tools/run_be1_lifecycle_consumer.py` | Process entry point for the consumer (owner-run only). |
| `backend/tools/frc08_reconcile_delete_pending.py` | One-time, re-runnable reconciliation of pre-existing DELETE_PENDING runs (DTR §6.4). |
| `backend/tests/unit/test_lifecycle_token_rule.py` | Token rule and every crash point (DTR T1-T7, §10). |
| `backend/tests/unit/test_be1_lifecycle_consumer.py` | Consumer steps, leases, CAS, retry bound, exception path. |
| `backend/tests/unit/test_core_run_asset_purge.py` | Plan, all-or-nothing, sweep, verify (port design §12). |
| `backend/tests/unit/test_story_lifecycle_store.py` | Story purge content, finalize, projection reads, fence. |
| `backend/tests/unit/test_s3_list_keys_error_mapping.py` | `list_keys` fails closed on 403, NoSuchBucket, 5xx. |
| `backend/tests/contract/test_parent_story_lifecycle_contract.py` | Cancel, delete and GET contract (Contract §3). |
| `backend/tests/integration/test_frc08_lifecycle_postgres.py` | Owner-run PostgreSQL + MinIO test on a disposable target (§7). |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_IMPLEMENTATION_REPORT_20261120.md` | Implementation evidence report. |

## 4. H — frozen references, read-only (29)

| Exact path | Bytes / SHA-256 at `03342207` | Purpose and boundary |
|---|---:|---|
| `backend/src/sketch2life/interfaces/http/app.py` | 70,828 / `43483014A1D40E05668D4CB0994E136C355D2920E99E7B8224121D2DEC604728` | No composition change: the delete route lives in the existing Parent router. |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | 3,743 / `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` | Parent router mounting unchanged. |
| `backend/src/sketch2life/interfaces/http/api_conventions.py` | 6,387 / `D2F4A3274723D232ABE00366C30B7004C312E01383D5EB2602A0F2AF19E7C790` | CONV-1 key and revision parsers, used as is. |
| `backend/src/sketch2life/interfaces/http/error_envelope.py` | 12,231 / `B39870B5C918670BDEDA77E34A779D62EFD3F866B0DEDE882F5A72975A5ECB0D` | CONV-1 error body, used as is. |
| `backend/src/sketch2life/interfaces/http/middleware/bounded_image_upload.py` | 8,146 / `B3D60B810B1262BC175B10536DCF69C1A01F44FEF43F2DBD06D80F84F61AD20F` | Listed only because CONV-1 modifies it; frozen reference for the 413 envelope (R5-F5). |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py` | 16,944 / `529CA7F569F61520DEBF8EE1220433C6DD1102F71AD0E15352C9C96359D32A40` | Assignment helper; Teacher adapter deferred. |
| `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` | 20,567 / `080AD7C4298E720B3E759309419FC802B5934D05BEC282E85F9227425E628040` | Assignment routes; Teacher adapter deferred. |
| `backend/src/sketch2life/interfaces/http/routers/be1_records.py` | 16,381 / `05A9EB9A1C1E732EB3801213798A3DEE74B96E52517545513B42886DA392D9CF` | School Admin data-request route; must behave as before. |
| `backend/src/sketch2life/infrastructure/persistence/be1_worker.py` | 8,475 / `F6C908B45B2099BF9B93DEBB7BAA87A64582EE1AEB7ADABC2325A581D99C1DD5` | BE1 retention worker; must behave as before. |
| `backend/src/sketch2life/interfaces/http/routers/story_run_lite.py` | 13,453 / `5676E1FAD9D615BDFF512D6C39EF002FD9933DA86BFBE485E95F4BE72B07F381` | Demo-profile cancel; outside FR-C-08. |
| `backend/src/sketch2life/infrastructure/story_run_lite/repository.py` | 132,748 / `58952C2A210785DBC6459C6FAC6203C5F5460DFEDD7852CD1375E12821E709D5` | Demo-path writers; not part of the fence (DTR §7). |
| `backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py` | 26,071 / `11EE7C14ACA93DD6FA2DEF30BFFC129E661CD9439C3425BEDC636F452DF246E9` | Demo photo bridge; technical organization stays as is. |
| `backend/src/sketch2life/infrastructure/story_run_lite/quarantine.py` | 7,375 / `B39B459F5ABA072EDB164D25D4986261EF14D04F13C13108F04BCA5EF3F86EA1` | Demo-path files; out of scope (port design §4). |
| `backend/src/sketch2life/infrastructure/vision_analysis/ledger.py` | 6,240 / `54A3640D180D5FB317A8E674D661E35A2A8047DCA90490F21C45F29BD9ADB198` | Pilot/demo invocation ledger; not purged by FR-C-08. |
| `backend/src/sketch2life/infrastructure/lesson_library/service.py` | 91,447 / `F37DB928B3C7CA5115A537D9E82D740D4BF9B23F34C02A0CBEE3C30BB995255D` | Teacher sample claim and Lesson storage; untouched. |
| `backend/src/sketch2life/infrastructure/lesson_library/tables.py` | 16,009 / `FE43AD061B69D4D1B8191AB52705A72C59BAA42605AB9167F4AADF3EF74EFDAF` | Lesson schema; untouched. |
| `backend/src/sketch2life/domain/ai_jobs/model.py` | 17,113 / `512B604636C1A22E231AC3276D3E537AE0DEAE4D9BB6652CCB064FAB7314DB99` | AI Job states stay independent from run states. |
| `backend/src/sketch2life/infrastructure/ai_jobs/worker.py` | 7,164 / `A54725329F8643FB0AF9D821F9861BE34980C3DA3E28E201203630EA691785F6` | No Parent AI job exists at the base. |
| `backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py` | 1,084 / `2B36FACBB1C08560BE258F1FF69B07354BCCB45D7672A33A86317E9D5E02EE5E` | No Parent AI job exists at the base. |
| `backend/src/sketch2life/infrastructure/ai_jobs/outbox_dispatcher.py` | 707 / `7B2DC13CCFA94C5BD09BA7679AB4DFAB194AEE6B32D8AB651AAB92FBCECB6115` | AI Jobs dispatch outbox; not the Core outbox. |
| `backend/src/sketch2life/application/video_playback.py` | 6,188 / `EEB251839FAA384E68824A4DD79EF55CE5FD553F5ED8FFA72B308082E0CD57A2` | No Parent video at the base. |
| `backend/src/sketch2life/application/ports/video_playback.py` | 3,436 / `7621F128D136853F3C9E815A6A70BE250D8D222865861F1F94E03F79023ABE79` | No Parent video at the base. |
| `backend/src/sketch2life/interfaces/http/routers/story_video.py` | 4,576 / `C7FEFFEAD0393444BC9CB8A518E471C0D6F64F3D33D3B540002CA1DC51F48F31` | No Parent video at the base. |
| `backend/src/sketch2life/application/video_review_lifecycle.py` | 4,386 / `E5A1A17C3D9580FDABF16E55864C18D10C67A6A03A54BA0CD34980691E0514E4` | No Parent video at the base. |
| `backend/src/sketch2life/infrastructure/persistence/be1_parent_role_adapter.py` | 1,507 / `1B83B95341D7AD98360CC98AF640CFAF5750A21FCE4CE971F0EE2D1DF66795E1` | Parent role lookup used as is. |
| `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | 11,122 / `29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3` | SRS-derived OpenAPI source; not edited. |
| `backend/tests/contract/test_app_composition.py` | 13,755 / `E18FA7478B0C7CB0D7369D3089CB07F139F7AE2670C7865AC4098480D61505B2` | Composition unchanged. |
| `backend/alembic/versions/20261112_parent_story_context.py` | 8,251 / `CFC7A92436066191134E27F1579B54109057CBAC43ABEB72B84C0F2D6CBFD9DF` | Story head the new revision depends on. |
| `backend/alembic/versions/20261102_story_run_lite.py` | 28,335 / `D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143` | Owner-scope pattern precedent. |

Governance and authority files are also H for the implementation: the canonical SRS (`B9B1F42D…`),
`artifacts/DATA_TABLE_REGISTER.md`, FEAT-063 `DECISIONS.md` and `approvals/TASK_APPROVAL.md`
(appended only by the coordinator, on the owner's word, outside the code change), and the DTR,
port design and SRS-edit drafts.

## 5. D — documentation after a verified result

`docs/context/PROJECT_CONTEXT.md`, `docs/context/SOURCE_REGISTER.md`,
`features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`, `.../SOURCE_REGISTER.md` and
`.../status/STATUS.md`: append verified outcome and links only, after the implementation result
is accepted; re-pinned at that time.

## 6. Exclusions

- Teacher authorization and Teacher routes (P2).
- Client code (mobile FEAT-081, web) and the frozen client-facing OpenAPI projection on `dev`
  (Contract §7): separate FE lane and approval.
- Any path not listed; any route other than the Parent cancel, delete and GET; any table other
  than the DTR's seven; video, playback, audio and AI Jobs worker changes.
- The SRS wording edit (applied last, by the owner or a separate session).
- The owner-review re-open command (DTR §6.6) and a least-privilege storage principal.

## 7. Proposed command ceiling (for the owner's implementation approval)

Coordinator, without a database, from `backend/` of the implementation worktree (PowerShell),
with `PYTHONPATH` pinned to that worktree's `src` and `backend`:
1. `ruff check` on the E and N Python paths;
2. `mypy` on the changed `src` modules (MYPYPATH=src), recording the base errors as baseline;
3. `pytest` on the unit and contract tests in E and N;
4. from the repository root: `validate_harness.py`, `validate_repository_security.py`,
   `validate_architecture.py`, `validate_skeleton.py`, then `git add -N` on the N paths and
   `git diff --check`.

Owner-run only, in the owner's terminal, against a **fresh disposable** PostgreSQL database whose
name contains `frc08` on a loopback port other than 5432 and 5433, plus a local MinIO bucket
created for the test:
5. `alembic upgrade heads`, then downgrade and upgrade again;
6. the integration test `tests/integration/test_frc08_lifecycle_postgres.py`;
7. the reconciliation command once and a second time (no new event).

Never against `sketch2life_m2_s1a`, `be1_acceptance`, the seed database or ports 5432 and 5433;
no provider, Modal or network call; `D:\s2l-gate-secrets` is never read.

## 8. Path counts and reconciliation with Draft 10

Draft 10: 57 base-pinned rows (22 E, 6 D, 29 H) and 9 N. Draft 11: 34 E, 29 H, 5 D
(listed in §5 without pins; they are re-pinned when edited) and 15 N.
- Moved from H to E: `story_run_lite/tables.py`, `be1_models.py`, `core_models.py`,
  `core_store.py`, `core_foundation.py`, `openapi_contract.py`, `openapi_contract_amendments.py`
  and the three frozen Parent tests.
- New in E (not in Draft 10): `contracts/schemas/parent_story_runs.py`, `ai_jobs/sql/tables.py`,
  `ai_jobs/fakes.py`, `alembic/README.md` and nine further test files.
- Moved from E to H: `app.py`, `router_composition.py`, the AI Jobs worker, reconciler and
  dispatcher, `test_app_composition.py` and the four video paths.
- New in H: `be1_records.py`, `be1_worker.py`, the StoryRun-lite repository, photo bridge and
  quarantine store, the vision ledger and the two migration precedents.
- Governance and authority files (SRS, register, `DECISIONS.md`, `TASK_APPROVAL.md`, M2 evidence)
  are named in §4 prose instead of pinned rows; the M2 evidence files and the historical spec
  draft are no longer listed. The Draft 10 N set is replaced by the files
the DTR and port design name. `FEAT-059 baseline_routes.json` is dropped (no route inventory
change is required for one new method on an existing path; if the route-baseline check fails,
stop and add it by a revision).

## 9. Verification and acceptance

The implementation maps every Contract Draft 9 §8 condition, every DTR Draft 6 §10 check and every
port design Draft 6 §12 check to a test or an owner-run result, and reports static facts
separately from runtime facts. Independent review on Sonnet 5.5 high before the owner's
acceptance; one task commit on the owner's word; no push.

## 10. Stop rules

Stop before or during implementation if: the base differs from `03342207` and pins were not
recomputed; any E or H pin differs; any N path exists; work needs an unlisted path, table, route
or public state; a decision beyond D-214 to D-218 is needed; a command is outside §7; or any real
data, provider or network operation would be required.

**FR-C-08 remains DRAFT / NOT APPROVED / NOT LAUNCHED. This allowlist authorizes no edit,
command, approval, implementation, test, launch, provider operation, push or merge.**
