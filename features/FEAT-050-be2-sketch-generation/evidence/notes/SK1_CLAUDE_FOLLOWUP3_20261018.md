# SK1 follow-up 3 — residual fixes and acceptance mapping (Claude)

## Disposition

Person 2 asked Claude to complete the independent SK1 residual work that is already inside the
approved SK1 acceptance (plan revision 5), using the residual table §5.2 of the local planning
proposal `BE2_01_07_CONSOLIDATION_PROPOSAL_REV3_20261018.md` (FEAT-049 ignored local planning,
SHA256 `e02ffafbef15c9375abccb832ada78d6f796b97c23e38365cf57105755cdb84b`). State after this
follow-up: **READY_FOR_CODEX_REVIEW**. SK1 remains **NOT_ACCEPTED**; BE2-04 remains
**IN_PROGRESS / NOT_DONE**. F-5 still needs owner disposition. Choosing a shared working branch for
BE2-01–07 is not an acceptance of F-5, of any residual, or of SK1.

## Identity and boundaries

- Worktree `D:\GitHub\Sketch2Life\.worktrees\be2-04-sketch-generation`, branch
  `feature/be2-04-sketch-generation`, HEAD/base `113cdf956a09336a0abf5561bd939f5e13b31ea0`,
  staged 0 before and after; SK1 source/tests remain uncommitted by design.
- Approval SHA256 `0f356d32b7cab883be6b3079400ada26495555cef160a6fb6a2a3b742a607d25` and approved
  plan SHA256 `461d06849899ea41f2c93432ed8b88c5a64428cf17bce5d2959a6d26ef4fa819` unchanged.
- Earlier review/receipt notes and ignored receipt directories are unchanged; this note and
  `metrics/SK1_CHECKS_FOLLOWUP3_20261018.json` are new. Raw receipts:
  ignored `evidence/local/claude-followup3-20261018/` (includes `baseline-hashes.txt`, the
  start-of-turn SHA256 of every SK1 file).
- No branch, stage, commit, push, merge, Studio, SQL/Redis, real provider, decoder, route, migration
  or dependency installation.

## Changes

| Item | Change | Files |
|---|---|---|
| P3 (`schedule()` lost-link cleanup reason) | The orphan job cleanup now passes the status reason of the proposal version the job was created for (for example `CONSENT_REVOKED`, `CANCELLED_BY_TEACHER`, `SUPERSEDED_BY_REVISION`), falling back to `SCHEDULE_REFUSED` (schedule-refused path and lost link without a terminal reason). Teacher cancel keeps `CANCELLED_BY_TEACHER`; owner-notice cleanup unchanged. | `backend/src/sketch2life/application/services/sketch_generation.py` |
| P3 regressions | `test_p3_lost_link_cleanup_cancels_orphan_with_proposal_reason[consent]`: job created, consent revoked + owner notice before link → proposal `stale` (`CONSENT_REVOKED`), orphan in `cleanup_job_ids`, job `cancelled` with `failure_code == CONSENT_REVOKED`, nothing dispatched, provider not run. `[teacher]`: same race with Teacher cancel → `CANCELLED_BY_TEACHER`. `test_p3_lost_reply_schedule_refusal_cleanup_keeps_schedule_refused`: lost reply then authorization revoked → cleanup requested with `SCHEDULE_REFUSED`, orphan cancelled with `SCHEDULE_REFUSED` at dispatch, provider not run. | `backend/tests/unit/test_sketch_generation_races.py` |
| R31 completion intent | `test_r31_real_completion_intent_sink_waits_for_c8_commit`: a real Sketch UNSAFE completion with a failing immediate sink leaves its quarantine intent pending; thread B (`h.jobs.deliver_side_effects`) claims it and pauses before the sink while thread A runs the C8 unit; observed order is `c8_commit_boundary → quarantine_applied → drain_returned`, refs untouched while the unit holds the lock, proposal `blocked_unsafe`, intent delivered, one `bumped=True` audit entry per ref from `h.jobs`, no `proposal_ready`. | same |
| R33 completion intents | `test_r33_real_vision_and_sketch_intents_drain_through_alternating_instances[h.jobs/sketch_jobs]`: a real Vision UNSAFE completion (through the router) and a real Sketch UNSAFE completion, each left pending by a failing immediate sink, drained by alternating job services; each intent applied once through the shared port by the draining instance; bumped refs equal exactly the union of both intents' refs. | same |
| P02 chain | `test_p02_chain_level_one_is_text_only_side_reference`: A1 `level_fx_1` request → text only, `overlay_asset_ref` null, display `side_reference`, result document artifact present with producer job/attempt lineage, provider rule forbids asset. | `backend/tests/unit/test_sketch_generation_chain.py` |
| P06 chain | `test_p06_chain_repeated_hint_and_id_opens_one_proposal_job_and_call`: hint, duplicate post-commit callback and three open-by-id calls → one proposal, inbox drained, one sketch job, generator called once across two worker runs. | same |
| C06 deterministic builder | `build_sketch_examples()` builds the H-AI-REVIEW bundle from the chain producer (promoted overlay record, its Child view, the blocked-unsafe event, the registry copy report). The committed example JSON was regenerated from the builder; `test_c06_committed_examples_match_deterministic_producer_build` asserts byte-level JSON equality and determinism. The previous hand-written example (SHA256 `16f3d1e5…a04`) contained inconsistent values (an overlay asset on a `level_fx_1` side-reference record, a non-closed reason `UNSAFE_OUTPUT`, an unquoted ETag); it is superseded, not edited in place by hand. | `backend/src/sketch2life/infrastructure/sketch_generation/harness.py`; `backend/tests/contract/test_sketch_proposal_contracts.py`; `fixtures/h_ai_review/sketch_proposal_examples.json` |

No other SK1 source changed (domain, ports, contracts, adapters, fakes unchanged since the second
follow-up; see `baseline-hashes.txt`).

## Residual status after this follow-up

| Residual (proposal Rev3 §5.2) | State | Evidence / reason |
|---|---|---|
| F-5 deviation from plan §6.5 (`SketchChainEligibility`) | **Pending owner disposition** | Unchanged; recorded in `DECISIONS.md` |
| P3 cleanup reason in `schedule()` | **Fixed; pending Codex review** | Change + three regressions above |
| R31/R33 synthetic intents | **Demonstrated with completion-generated intents; pending Codex review** | New R31/R33 tests; synthetic variants kept as additional coverage |
| P02/P06 chain | **Demonstrated; pending Codex review** | New chain tests |
| C06 static example | **Demonstrated (producer-built, compared); pending Codex review** | Builder + equality test |
| N04/N08/N11/N15 chain, C03/C03b/C09/N19/P09 contract column | See mapping below; partial rows stay partial | — |
| Callback A1 post-commit → `SketchStageAdapter` end to end | **Pending disposition / NOT_RUN** | Behaviour unchanged; plan §6.5 forwards via `RecordingSketchStage`; adapter tested directly (P05) |
| N16 Child cancel of an existing proposal → `FORBIDDEN_SCOPE` | **Pending owner acknowledgement** | Matches plan wording; behaviour unchanged |
| SK-NI01, Studio, PostgreSQL, Redis/RQ, provider/model, decoder | **NOT_IMPLEMENTED / NOT_RUN — outside SK1 acceptance** | Runtime gates of card BE2-04 |

## Exact mapping for partial chain/contract acceptance rows

| Plan row (test columns) | Executable assertions | State |
|---|---|---|
| SK-N04 (svc, chain) | svc `test_n04_not_applicable_analysis_opens_stale_without_job` (not accepted / meaning `not_applicable` / consent, scripted reader); adapter on the real chain composition `test_n04_lineage_mismatch_is_refused` (real BE2-03/02 records, lineage field tampered → `HANDOFF_MISMATCH`); chain `test_n06_owner_facts_changed_before_open_create_stale_without_job[age]` (real Vision `downstream_meaning` → `ANALYSIS_NOT_APPLICABLE`, no job) | **Partial**: a real BE2-02 analysis whose `accepted_status` is not `accepted` is not exercised in the chain |
| SK-N08 (svc, chain) | svc `test_n08_record_generation_refuses_before_provider` (unknown job, not running, wrong attempt, digest divergence, other job type), `test_n08_cancelled_proposal_refuses_after_start`; chain `test_r05_cancel_between_start_and_provider_prevents_generation`, `test_r10_duplicate_sketch_delivery_never_calls_provider_twice`, `test_c08_router_table_unknown_type_and_started_guard` | **Partial**: wrong-type / digest-mismatch variants only at service level |
| SK-N11 (dom, svc, chain) | dom `test_n11_malformed_outputs_are_refused` (all listed variants), `test_n11_byte_bound_is_enforced`; svc `test_n11_malformed_output_fails_without_staging`, `test_admission_refusal_is_output_malformed`; chain `test_n18_chain_rejects_canvas_operations_without_mutating_source` (`FAILED`/`OUTPUT_MALFORMED`, nothing staged) | **Partial at chain level**: one malformed variant in the chain; the rest is the pure domain validator plus service wiring |
| SK-N15 (svc, chain) | svc `test_n15_cancel_receipts_and_preconditions` (receipt replay, 409/412/400/428); chain `test_r23_cancelled_sketch_is_refused_then_vision_runs` (cancel before start → start refused `JOB_NOT_QUEUED`, no provider), `test_r04_cancel_after_job_create_before_link_cleans_orphan_job`, `test_r04_cancel_before_schedule_never_creates_job`, `test_r05_…`, `test_r11_cancel_commit_failure_leaves_no_receipt_or_event_and_retries` | **Demonstrated** (receipt rules at svc; cancel/job/start behaviour in chain) |
| SK-C03 (dom, contract) | dom `test_c03_generation_digest_golden_vector_and_sensitivity`, `test_c03_content_sha_golden_vector_sensitivity_and_no_timestamps` | **Partial**: no contract-file golden test |
| SK-C03b (dom, contract) | dom `test_c03b_versioned_golden_vectors_recompute_from_history`; chain `test_p08_p11_chain_revise_level_pins_policy_job_digest_and_content` recomputes v2 `content_sha256` | **Partial**: no contract-file golden test |
| SK-C09 (adp, contract) | adapter `test_c09_projection_analysis_and_cache_hit_paths`, AST `test_c09_domain_and_application_import_no_producer_types` | **Demonstrated** in the adapter test file (the AST check is the contract-level guard) |
| SK-N19 (dom, contract) | dom `test_n19_producer_never_writes_review_owned_values`; contract `test_c01_record_device_contracts_round_trip_and_reject_extra_fields` (extra field rejected) | **Demonstrated** |
| SK-P09 (svc, contract) | svc `test_p09_teacher_record_fields_and_minimal_device_view` (field set, device view at every state); contract `test_c01_…` (record + device view round trip, strict) | **Demonstrated** |

Partial rows are not converted to PASS; they need either extra tests or an explicit owner
acceptance of the mapping.

## Checks on the final snapshot

Interpreter: existing `D:\GitHub\Sketch2Life\backend\.venv\Scripts\python.exe` (CPython 3.12.10;
ruff 0.16.4, mypy 1.20.2, pytest 8.4.2). `PYTHONPATH` and `MYPYPATH` pinned to
`D:\GitHub\Sketch2Life\.worktrees\be2-04-sketch-generation\backend\src`; `sketch2life` imports from
this worktree. No package installed.

| Check | Command (cwd) | Exit | Result | JUnit SHA256 |
|---|---|---|---|---|
| Ruff, 14 SK1 Python files | `python -B -m ruff check <14 files>` (backend) | 0 | All checks passed | — |
| Strict mypy, 14 files | `python -B -m mypy --strict --config-file pyproject.toml --cache-dir <local> <14 files>` (backend) | 0 | no issues in 14 files | — |
| Focused SK1 (6 test files) | `python -B -m pytest -p no:cacheprovider -rs --junitxml … --basetemp <local> <6 files>` (backend) | 0 | **175 passed, 0 skipped** | `5393085d4f56f6fe186445ffe46857149588a925dae06d4a4b4c069b7754aacc` |
| X01 BE2-01 | same form, worktree root, file list as earlier follow-ups | 0 | 337 passed, 1 skipped | `205c33e8b55aec0f3a4f3fd5c4a0d1c85e424be44b4ad9a1014cad4343f4fa53` |
| X02 BE2-02 | same form | 0 | 411 passed, 1 skipped | `49e803d83cf3df0b41083e971f61c0c0eb36226c2667a69a965a8b618a56b23a` |
| X03 BE2-03 | same form | 0 | 127 passed, 1 skipped | `b2dcc2af132089694b854132231a06299f12279039166c85efabe0cc80cb22b6` |
| Validators + `git diff --check` | `python -B tools/validate_*.py`; `git diff --check` (worktree root) | see metrics | see metrics | — |

The three skips are the existing live-app contract tests requiring Pillow (not installed in the
permitted environment); they are skips, not passes. X01–X03 do not import SK1 code; they were run
as the approved regression set on the final snapshot. Previous receipts remain as history.

## Source fingerprints (final)

| File | Start of turn SHA256 | Final SHA256 | Bytes |
|---|---|---|---|
| `backend/src/sketch2life/application/services/sketch_generation.py` | `f7b3fd37…c388` | `47cfbebefc44e6257d7d7b34e6bd45a13ee6d7d437be86d5fd0533f57ae8c24f` | 51 815 |
| `backend/src/sketch2life/infrastructure/sketch_generation/harness.py` | `d9b15967…bbae` | `63c1eed9b71daef8e50ec8c7459588b5c88660a446921d49ed45650443cfdf68` | 35 470 |
| `backend/tests/unit/test_sketch_generation_races.py` | `21a19da5…9ba3` | `28f55bd5b7612f4861dbb5b5e7a4c68fd44227984d34eef45e3d6e0548b49bad` | 68 650 |
| `backend/tests/unit/test_sketch_generation_chain.py` | `f21c433c…7e9c` | `2071924f070e23052b0684a8e9cae84864d0667896e2ab7ac5ed26d0925f0a65` | 30 936 |
| `backend/tests/contract/test_sketch_proposal_contracts.py` | `cf361e5e…1a12` | `6c3a1be1bd02a46ae9a7dfcb8f69dbfdef28a6f584df0c7847b0350ddc7491ad` | 7 044 |
| `fixtures/h_ai_review/sketch_proposal_examples.json` | `16f3d1e5…6a04` | `96598b51c479c36672a88b1f295976f5d5bd32b53e728eeb2e09c3504fc5da5b` | 3 898 |

## Next

Codex review of the changes above. Owner decisions still open before SK1 closure: F-5 disposition;
acceptance or extra tests for the partial mapping rows; disposition of the A1 callback end-to-end
item and the N16 residual. Then SK1 acceptance and a separately authorized commit.
