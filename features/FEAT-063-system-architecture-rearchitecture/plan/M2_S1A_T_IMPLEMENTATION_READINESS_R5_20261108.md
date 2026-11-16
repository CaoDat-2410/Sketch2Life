# M2 S1a-T implementation readiness — R5 — 2026-11-08

**Status: READY FOR OWNER DECISION TO START IMPLEMENTATION.** This is a readiness note based on the approved R5 package and recorded decisions. It is not a new approval, does not start implementation, and does not launch the owner runner. The owner has not yet given the start decision in this step.

## Predecessor Draft 4 readiness note

The earlier Draft 4-based readiness note was not found as a repository file in the current checkout, including the FEAT-063 plan/evidence areas, `.claude/handoff/`, and `tmp/`. Its repository path is **NOT FOUND** and its SHA-256 is **NOT AVAILABLE / NOT VERIFIED**. No prior file was edited. This R5 note supersedes the earlier Draft 4 readiness guidance; because the predecessor file is absent, its directory cannot be confirmed. This new note is placed in `features/FEAT-063-system-architecture-rearchitecture/plan/` beside the pinned R5 specification and launch instruction.

## Approval, baseline and pinned package

The operative records currently state:

- `approvals/TASK_APPROVAL.md`, entry “M2 S1a-T Approval — 2026-11-08” at line 920: **APPROVED / NOT LAUNCHED**, with the three R5 artifacts pinned. This note does not substitute for the owner's separate decision to start implementation.
- The accepted prerequisite “M2 Baseline Closure Acceptance — 2026-11-08” is at line 909 and accepts only the pinned Baseline Closure Record. It closes the baseline record, not S1a-T execution.
- The R5 independent review was a fresh cold, read-only round 3 (final) and returned **READY, 0 P1 / 0 P2 / 1 P3**. Session: `01a1badf-4d36-7c02-8a4c-e7ab2ae6c998`. The P3 is inherited launcher-version wording at R5 specification lines 64 and 79 (`R2` / `R4` references); the reviewer found the corresponding behavior in the R5 launcher and did not consider it blocking. Do not modify R5 as part of this readiness note.

The following SHA-256 values were recalculated from the current files while preparing this note; every value matched the approval/pin record:

| Artifact | Repository-relative path | Recalculated SHA-256 | Result |
|---|---|---|---|
| S1a-T specification R5 | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R5.md` | `934D2E69DAEA293CC68BDD55EED8713CE59E0EAB0E1CA758FB9420B34EAC9345` | MATCH |
| S1a-T launch instruction R5 | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_LAUNCH_INSTRUCTION_20261107_R5.md` | `9CBCE84B4AB579D0857AC153DC2FC59DAFB255468E1AFC29D338566B9EDAFAAC` | MATCH |
| Guarded owner launcher R5 | `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_t_owner_run_20261107_r5.py` | `DA7F4A4D6502F927C7EC1F29F112A283E7960F831F2183CD07C09E61EE488FA0` | MATCH |
| Task approval record | `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | `E5171D74539712AF265423772175310050EB0ABED39227B1B5B3AEAD815BB5F8` | MATCH |
| Owner decisions | `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | `C23CE511F14F10C886245DB855DD181A19AD818D9259CDC04D3DCCDD0F79A67F` | MATCH |
| Accepted baseline closure record | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_BASELINE_CLOSURE_RECORD_20261108.md` | `65588C6876F653F3A0B17E227B8845E63EA2F6C77FB78756A91925DEBA9626D6` | MATCH |
| Baseline specification | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_BASELINE_RUN_APPROVAL_FINAL_20261107.md` | `A671DBD85B9622CB754C5CECB807BBBBA2C920CD76F0A22ABBA44F4A12DC1A18` | MATCH |
| Baseline launch instruction R2 | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_BASELINE_LAUNCH_INSTRUCTION_20261107_R2.md` | `C132EF91AD7C06A82EB27D09D82B0662E77CDD795B9BC2F935B281822EAA9178` | MATCH |

The R5 specification is the detailed authority for scope, file modes, command ceilings and stop conditions. Its file-level pins must be recalculated again before any implementation edit; this note does not replace that gate.

## Approved S1a-T scope

S1a-T covers only the Teacher/organisation side. It uses `sketch2life_m2_s1a`, PostgreSQL 17 on loopback port 5433 as user `postgres`. The database was reported as a schema-only copy with 117 tables, zero rows and an empty Alembic version table when created; its current identity and contents are **NOT VERIFIED** by this note and must pass the R5 owner-launcher checks before pytest. Never write to, migrate, restore, drop, truncate or clean up `sketch2life`.

The three S1a-T operations are:

1. `POST /api/be1/v1/organizations/{organization_id}/classes`.
2. `POST /api/be1/v1/classes/{class_id}/assignments`.
3. `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles`.

The old organization-scoped assignment POST and DELETE operations are removed from the router and OpenAPI catalogue; no blocked stub or writable alias remains. Assignment derives organization from the class, accepts only `subject` in the request, fixes role to `teacher`, and returns the specified assignment contract. Only one active Teacher per class is allowed; the class row is locked while counting and creating in the same transaction. A second active Teacher receives HTTP 409 `CLASS_TEACHER_EXISTS` without identity disclosure. Missing class, cross-organization class and missing assignment are indistinguishable HTTP 403 `SCOPE_DENIED` on M2 routes only. Do not change global `authorize_adult` behavior.

Teacher-created profiles store `SYNTHETIC_DEV` with both consent references NULL; `REAL` and `LEGACY_UNCLASSIFIED` remain blocked. HTTP creation is allowed only in `local` or `test` with `synthetic_pilot_enabled` enabled. Return the stored `SYNTHETIC_DEV` value; document its mapping to SRS `SYNTHETIC_TEST`, without changing the enum. The server creates `child_id` as `synthetic-` plus `secrets.token_hex(12)`, links it to test runs through the approved markers, and sets `age_source=SYNTHETIC_FIXTURE`. The separate existing route using `ADULT_DECLARED` remains unchanged.

New age values use the shared validator and request schema range 36–120. Preserve existing 121–155 values; do not clamp/rewrite rows, change the BE1 database check of 36–155, use `child_age.py`, or change the separate learning-content 155 boundary. Expected OpenAPI counts are 128 runtime operations / 123 mounted catalog operations / 110 paths / 18 tags; any difference is a stop gate. Capacity, `CLASS_CAPACITY_REACHED`, expected class revision, assignment revision in response, idempotency key, StoryRun and Parent read-isolation are not covered by S1a-T. AT-05..09 are not run because S1b is deferred.

## Owner decisions D-155 through D-162

These decisions set directions and boundaries; they do not expand the file allowlist or authorize an action omitted by R5.

- **D-155:** split S1a into S1a-T (Teacher/organisation on existing `be1_*`, no migration) and S1a-P (Parent tables and separately scoped migration); each requires its own approval.
- **D-156:** run S1a-T before S1a-P on the same task database, sequentially; recompute inventory and mypy baseline between phases. No parallel run.
- **D-157:** remove the old organisation-scoped assignment POST/DELETE routes; add the class-scoped Teacher assignment behavior; preserve the owner-approved 409, `child_id`, `SYNTHETIC_DEV`, and age directions; remaining fields stay open only where later approval records leave them open.
- **D-158:** records detailed route, denial, marker, command, allowlist, acceptance-test and stop-gate directions folded into R5. In particular, requests, response codes/messages, synthetic IDs and row markers must follow R5 exactly; unresolved matters are not to be improvised.
- **D-159:** controls artifact revisions, review rounds, owner approval recording, all-table count-only inventory, no-cleanup behavior, official pytest summary handling and process-termination stop gates. It permits no wider scope.
- **D-160:** Teacher-created synthetic profiles use `age_source=SYNTHETIC_FIXTURE`; the separate existing `be1_registry.py` route that uses `ADULT_DECLARED` is unchanged.
- **D-161:** `taskkill /T /F` exit 128 means `PROCESS_TERMINATION_UNCONFIRMED`: do not run post-inventory and do not claim children stopped. Exit 0 still requires bounded wait/poll for the root process; child enumeration remains unverified.
- **D-162:** permits only the final R5 artifact set and round-3 independent review as a narrow exception to D-159's R2–R4 label limit. It opens no launch, database action, implementation beyond the separately recorded approval, or later phase.

## R5 implementation file boundary

R5 §5 contains 76 unique allowlist paths: 71 existing, hash-pinned paths and five paths expected absent. Modes are exactly **E=7**, **R/E=11**, **R=34**, **H=19**, **N=5**. Thus 18 existing files are edit candidates, 53 existing files are read-only, and five are new-file candidates. `R/E` means readable and eligible for a scoped edit; it does not mean every part of the file may be changed. Recheck every current hash and absent-path state in R5 §5 before editing.

### Existing edit candidates — E (7)

- `backend/src/sketch2life/contracts/schemas/be1_runtime.py`
- `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py`
- `backend/src/sketch2life/interfaces/http/openapi_contract.py`
- `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`
- `backend/tests/contract/test_be1_synthetic_pilot.py`
- `backend/tests/unit/test_age_provenance_columns.py`

### Existing edit candidates — read and edit R/E (11)

- `backend/src/sketch2life/domain/core_foundation.py`
- `backend/tests/contract/test_app_composition.py`
- `backend/tests/contract/test_openapi_contract_catalog.py`
- `backend/tests/integration/test_be1_postgres_api.py`
- `backend/tests/unit/test_assistance_domain.py`
- `backend/tests/unit/test_assistance_service.py`
- `backend/tests/unit/test_be1_fact_reader.py`
- `backend/tests/unit/test_vision_analysis_review_fixes.py`
- `backend/tests/unit/test_vision_analysis_service.py`
- `backend/tests/unit/test_vision_context_domain.py`
- `backend/tests/unit/test_vision_context_service.py`

### New-file candidates — N (5; currently absent)

- `backend/tests/contract/test_m2_s1a_teacher_routes.py`
- `backend/tests/integration/test_m2_s1a_teacher_postgres.py`
- `backend/tests/unit/test_m2_s1a_teacher_service.py`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md`

### Read-only R (34)

- `.claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json`
- `backend/alembic/env.py`
- `backend/alembic/versions/20261103_story_upload_compat.py`
- `backend/alembic/versions/20261104_story_revisions.py`
- `backend/src/sketch2life/application/ports/identity.py`
- `backend/src/sketch2life/application/services/be1_runtime.py`
- `backend/src/sketch2life/application/services/vision_analysis.py`
- `backend/src/sketch2life/domain/assistance.py`
- `backend/src/sketch2life/domain/child_age.py`
- `backend/src/sketch2life/domain/vision_context.py`
- `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py`
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py`
- `backend/src/sketch2life/infrastructure/persistence/be1_models.py`
- `backend/src/sketch2life/infrastructure/persistence/core_models.py`
- `backend/src/sketch2life/infrastructure/persistence/core_store.py`
- `backend/src/sketch2life/infrastructure/persistence/database.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/src/sketch2life/interfaces/http/be1_runtime.py`
- `backend/src/sketch2life/interfaces/http/router_composition.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_common.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_records.py`
- `backend/tests/contract/test_learning_content_commands.py`
- `backend/tests/unit/test_ai_policy_persistence_shape.py`
- `backend/tests/unit/test_profile_age_invariant.py`
- `backend/tests/unit/test_synthetic_eligibility.py`
- `backend/tests/unit/test_t2c_digest_pin.py`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT11_20261107.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P_TASK_APPROVAL_DRAFT1_20261107.md`
- `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_TASK_APPROVAL_DRAFT1_20261107.md`

### Historical read-only H (19)

- `features/FEAT-047-be1-runtime-backend/artifacts/API_CONTRACT.md`
- `features/FEAT-047-be1-runtime-backend/artifacts/API_MAP.md`
- `features/FEAT-047-be1-runtime-backend/artifacts/openapi-v1.json`
- `features/FEAT-058-review2-document-package/evidence/metrics/be2_route_inventory.json`
- `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json`
- `features/FEAT-060-classroom-integration-and-review-remediation/evidence/notes/SRS_STAGE_API_TRACEABILITY_20261023.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/API_INVENTORY_FEAT063_REV31_20261028.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/API_COVERAGE.csv`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/organizations-classes/004-create-assignment-api-be1-v1-organizations-organization-id.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/organizations-classes/005-revoke-assignment-api-be1-v1-organizations-organization-id.bru`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/openapi.runtime.json`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/OPENAPI_FEAT063_REV37_20261030.json`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/OPENAPI_FEAT063_REV45_20261101.json`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/B0_openapi_combined_storage-off_20261030.json`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/B0_openapi_combined_storage-on_20261030.json`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.csv`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/REV34_LEGACY_ROUTE_SMOKE_20261029.csv`

Do not edit any R or H item. In particular, Alembic files are read-only for S1a-T, and historical Bruno/OpenAPI artifacts are not updated in this phase. Do not create a new migration or change schema; R5 says S1a-T has no Alembic migration.

The separate Draft 4 §1.3 pin set has **31 pins: 30 source/test pins and one read-only tool pin**. The independent round-3 reviewer reported all 31 matched. These are a separate pin set from the 76 unique R5 §5 paths. Before an implementation edit, recheck the full existing-file hashes in the R5 allowlist as specified there.

## Recommended execution and ownership sequence

1. **Owner decision to start:** owner explicitly decides to begin implementation. This note is only readiness; without that decision, do not start.
2. **Executor (Codex or Claude, separate implementation session):** reread this note, R5 spec/launch, D-155..D-162 and the approved entry; recheck branch, HEAD, index, every existing allowlist hash, and each N path is absent. Do source-only K4 before editing; label owner-reported facts, source facts, inference and unknowns separately. Implement only the approved S1a-T behavior and files. Run only the R5-authorized offline checks within their exact command, cwd, count and timeout ceilings. Do not run the PostgreSQL test or launcher.
3. **Independent code reviewer:** a fresh cold read-only session reviews the exact implementation diff, allowlist, contracts, test coverage, results and evidence. It does not run the launcher or make the owner decision.
4. **Owner-only PostgreSQL launch:** only after implementation and independent review, the owner may run the pinned R5 launcher **one time** using the exact owner-only command in the R5 launch instruction. The owner enters the DB password through its hidden terminal prompt. Do not send a password/URL into chat or logs. The launcher must confirm the real database identity and an empty all-table pre-inventory before pytest; a separate guard is not a substitute for the app-engine identity check.
5. **Owner log review:** the owner reads the complete raw run logs and provides the evidence needed for a closure record. Keep owner-run provenance explicit. Do not infer PASS from progress dots, a process exit alone, or a partial log.
6. **S1a-T closure record:** prepare a separate evidence record from complete owner-provided outputs, explicitly distinguishing PASS, FAIL, SKIP, timeout and NOT RUN. A missing official summary is not a pass. Closure/acceptance is a later record; this readiness note closes nothing.

## Authorized check boundaries and stop gates

R5 specifies a one-use pre-code offline pytest baseline from the separate Baseline Approval package; its accepted closure is already recorded, so do not rerun that baseline. Post-code checks remain governed by R5 §3:

- Offline pytest: the same 11 baseline modules plus the two new S1a-T service/routes modules, one invocation, at most 1,800 seconds. Exclude only `test_head_counts_by_both_methods_match_the_derived_expectation`; it is **NOT RUN**, not PASS.
- Composition/OpenAPI pytest: only `test_app_composition.py` and `test_openapi_contract_catalog.py`, after code and only with seam A and both dotenv guards installed/asserted. Do not read `.env` or enable a live database seam.
- PostgreSQL acceptance: only `test_m2_s1a_teacher_postgres.py`, exactly once via the owner R5 launcher, at most 1,800 seconds. Identity must be verified on the app's actual engine: `current_database=sketch2life_m2_s1a`, `current_user=postgres`, port 5433, loopback address, PostgreSQL major 17.
- Strict mypy: one package invocation, no incremental cache, new cache only under the approved ignored temp directory, at most 900 seconds. Ruff: one check with the approved selectors and exact paths, at most 300 seconds; no format/autofix. Each named repository validator and `git diff --check` runs once, at most 300 seconds. The launcher/spec provide exact command/capture details; do not improvise or retry.

Stop on any pin/HEAD/index mismatch; unexpected file or migration; database identity mismatch; any pre-run row; output or cache path not approved/ignored; attempted `.env` read; secret/URI in output; command/timeout deviation; missing safety verdict; or failed launch guard. Do not read environment contents, switch shells, alter flags/selections, retry, run Alembic CLI, migrate, clean up rows, change database, contact Modal/provider or use external network.

## Known baseline limits and NOT VERIFIED items

- The accepted baseline closure records pytest as **NOT RUN / NO VERDICT** because the baseline output lacked an official aggregate summary. Do not infer a passed count. If the S1a-T pytest run lacks its official summary, record exactly `NOT RUN: no official pytest summary`, make no post-run database connection and do not claim PASS.
- The baseline closure records mypy 255 diagnostics across 50 files, Ruff 202 findings, and `git diff --check` exit 2 as baseline data, not PASS. It also discloses that validators and whitespace check ran after the pytest output lacked a summary, and that some R3 files were written during the owner-run interval. Preserve those facts when comparing results; do not rewrite them as clean baseline verdicts.
- Current state of `sketch2life_m2_s1a` (identity, row counts, contents and empty version table) is **NOT VERIFIED** by this note. The owner-reported initial condition is not runtime proof; the R5 launcher must perform its pinned checks.
- The launcher does not clean up test-created rows and is single-use until the owner separately decides row handling. Preserve synthetic run markers; no broad cleanup.
- `PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED` remains. After timeout, taskkill exit 128, an incomplete bounded root-process check, or a second Ctrl+C during termination, the outcome is `PROCESS_TERMINATION_UNCONFIRMED`; do not inventory or claim child processes stopped. Never retry.
- R5 spec lines 64 and 79 retain R2/R4 launcher-version wording although the approved launch pins R5. The independent reviewer recorded this as one non-blocking P3; behavior was found in the R5 launcher. This note records the condition without altering R5.
- No implementation, post-code test, PostgreSQL launch, database verification or S1a-T closure has happened in this readiness step: **NOT RUN / NOT VERIFIED**.

## Prohibitions and phase boundary

No work on `sketch2life`; no Alembic command or migration in S1a-T; no S1a-P, S1b, S2, S3 or M3–M6; no Modal, GPU, provider or network call; no cleanup of test rows; no stage/commit/push. `OWNER_MODAL_CALL_APPROVED=NO` remains unchanged. Every later phase requires its own decision and approval.

**Final status: READY FOR OWNER DECISION TO START IMPLEMENTATION.**
