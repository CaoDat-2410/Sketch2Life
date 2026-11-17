# BE2-02 C1_COMPONENT_OFFLINE implementation evidence — 2026-10-16

- Approval: approvals/TASK_APPROVAL.md (verbatim, 2026-10-16 19:18 +07:00), planrev1 bytes
  plan/PLAN_REV1_APPROVED.md SHA256 `f4733c88797edbcce225ecd63700634f929ca75789362c7f3a58a2b57f19df30`.
- Branch/base: feature/be2-02-vision-correction at `6dcc57ee0b3d053f071c8c92e72aaaee2e98d899`
  (HEAD = base; all work is uncommitted in this worktree). Executor Claude; review Codex.
- Result: **C1 REVIEW_READY** (component evidence only). Full BE2-02 is **NOT_DONE**.
- Evidence kind: synthetic fixtures + fake ports + the real legacy V2 adapter code over an
  injected in-memory transport. No real provider, network, model, weights, GPU, install,
  service, SQL migration, queue or production route. Fake proof ≠ runtime ≠ integration.

## Environment

Shared Python 3.12.10 venv in the root checkout (`backend/.venv`); its editable `.pth` points at
the root checkout's `backend/src` (FEAT-018 branch), so every command pinned `PYTHONPATH` (and
`MYPYPATH`) to this worktree's `backend/src`. Verified `sketch2life.__file__` resolves to
`.worktrees/be2-02-vision-correction/backend/src/...`. pydantic 2.13.4, fastapi 0.141.1,
pytest 8.4.2, ruff 0.16.4, mypy 1.20.2. Pillow is **not installed** (see NOT_RUN).
pytest ran with `-p no:cacheprovider`, isolated `--basetemp` in the session scratchpad and
`PYTHONDONTWRITEBYTECODE=1`; JUnit XML is kept locally under ignored `evidence/local/junit/`.

## Delivered modules (`backend/src/sketch2life/`)

| Batch | Path | Role |
|---|---|---|
| C1.1 | domain/vision_analysis.py | Pure rules: text/confidence bounds, checkpoint/render/admission bindings, lineage guards, immutable observation + hash, append-only Child proposal / Teacher confirmation, head CAS revision, stale/invalidation, ETag |
| C1.1 | contracts/schemas/analysis_results.py | Strict DATA-22 worker candidate, CMD-34 command, Teacher/Child projections, H-AI-REVIEW record (`0.1-candidate`) |
| C1.2 | application/ports/vision_analysis.py | Source, admission, authority, context, assistance-request, job-lineage, observation-provider, repository/UoW ports |
| C1.2 | application/services/vision_analysis.py | Observation recording, CMD-34 use case, owner invalidation, downstream meaning, projections |
| C1.2 | infrastructure/vision_analysis/fakes.py, harness.py | Staged all-or-nothing fake UoW with CAS and commit-failure injection; owner fakes; synthetic world and handoff example builder |
| C1.2 | infrastructure/vision_analysis/job_lineage.py | Read-only BE2-01 lineage over the foundation `AiJobRepository` port |
| C1.3 | infrastructure/vision_analysis/legacy_v2.py | Offline bridge reusing `LightningVisionV2Adapter` unchanged; image_only; stricter identity/provenance/confidence checks |
| C1.4 | interfaces/http/routers/analysis_corrections.py, interfaces/http/analysis_corrections_fixture_app.py | CMD-34 POST handler and isolated fixture composition (not mounted by app.py) |

Tests: `tests/unit/test_vision_analysis_{domain,service,legacy_bridge,job_lineage}.py`,
`tests/contract/test_analysis_result_contracts.py`, `test_analysis_corrections_api.py`,
`test_h_ai_review_handoff_examples.py`. Golden synthetic consumer examples:
`features/FEAT-048-be2-vision-correction/fixtures/h_ai_review/*.json` (deterministic build from
`harness.build_handoff_examples`, enforced by a test). No existing file under `backend/` was
modified.

## Commands and actual results (UTC 2026-10-16)

Run from `backend/` of this worktree with the pinned paths above.

| Check | Command (abbreviated) | Result |
|---|---|---|
| Focused C1 suite 12:55:38Z | `python -B -m pytest <7 new test files> --junitxml …/be2_02_c1_focused.xml` | 175 collected: **174 passed, 1 skipped** (NOT_RUN below), 0 failed; JUnit sha256 `51970459…a4902` |
| Legacy Vision regression 12:55:39Z | `pytest tests/unit/test_lightning_vision_v2_adapter.py test_qwen_vision_adapter.py test_vision_phase_a_contracts.py test_vision_phase_b_b1_contracts.py test_vision_content_policy.py test_lightning_client.py` | 238: **233 passed, 5 skipped** (pre-existing parametrised skips "input details are covered by the attempt-zero row"), 0 failed; sha256 `c29f72e7…1ed348` |
| BE2-01 regression 12:55:41Z | `pytest tests/unit/test_ai_job_*.py tests/contract/test_ai_job_*.py` (11 files) | 338: **337 passed, 1 skipped** (Pillow), 0 failed; sha256 `ff768b2a…1ade2b` |
| Lint 12:55:59Z | `ruff check` on the 18 new source/test paths | PASS |
| Types 12:55:59Z | `mypy --strict` (project config) on the same 18 paths | PASS, no issues in 18 files |
| Repository checks | see "Validators" | PASS after F-03 fix |

`ruff format --check` was not used as a gate: the repository does not apply it (existing BE2-01
files such as routers/ai_jobs.py also report "would reformat"); new code follows the surrounding
hand-wrapped style.

Mutation sanity (scratch only, nothing written to the repo; pytest in-process with
monkeypatches): M1 fake store skips CAS → V10 race test fails; M2 no disclosure check before
replay → V09 revoke tests fail; M3 child proposal moves current meaning → V04 test fails;
M4 bridge skips raw confidence re-check → V13 test fails; M5 no post-provider lineage re-check →
V07 in-flight cancel test fails. **5/5 killed**; unmutated control passes.

## Acceptance mapping V01–V17 (component evidence)

| ID | Evidence (test functions) | Result |
|---|---|---|
| V01 | contracts: `test_v01_*` (valid/normalised command, omitted≡null explanation, 12 server-owned fields refused, 14 invalid values, required fields, strict candidate with null confidence, bool/string/NaN/Inf/out-of-range confidence refused, missing confidence key, distinct bindings, no `live`/typed-bridge provenance); domain: `test_v01_*` | PASS |
| V02 | service: `test_v02_wrong_or_missing_binding_calls_no_provider_and_stores_nothing` (5 cases), `test_v02_admission_bound_to_another_render_is_not_accepted`, `test_v02_v07_input_hash_must_bind_the_resolved_source`; domain: `test_v02_checkpoint_render_and_admission_are_independent_bindings` (incl. checksum passed off as image hash) | PASS |
| V03 | service: `test_v03_valid_snapshot_yields_traceable_uncertain_candidate`; domain: `test_v03_*`; bridge: `test_v13_valid_result_maps_whole_original_with_image_only_provenance` | PASS |
| V04 | service: `test_v04_cat_child_tiger_teacher_confirmation_keeps_cat_and_authors`; domain: `test_v04_*`; bridge: `test_v13_v04_wrong_label_is_corrected_without_touching_the_bridge_observation`; contracts: `test_v04_*` | PASS |
| V05 | service: `test_v05_out_of_scope_principals_are_denied_and_concealed` (other org/class teacher, other child's device, other canvas, admin), `…wrong_group_and_closed_or_unbound_turn…`, `…revoked_grant_purpose_or_consent…`, `…device_cannot_confirm_or_act_as_teacher`, `…teacher_cannot_author_the_childs_explanation`, `…basis_must_be_a_child_proposal_of_the_same_analysis`, `test_v05_v07_consent_revoked_during_provider_call_discards_result`; API 404/422 cases | PASS |
| V06 | service: `test_v06_context_change_in_flight_stores_pinned_original_as_stale`, `test_v06_snapshot_change_in_flight_is_stale`, `test_v06_at_cs_008_newer_confirmed_meaning_is_not_overwritten` | PASS |
| V07 | service: `test_v07_wrong_lineage_never_creates_an_authoritative_analysis` (8 cases), `…cancel_or_supersede_during_provider_call…`, `…same_attempt_replays…`; lineage: `test_v07_*` over the BE2-01 fake store (job revision/outbox/receipts unchanged); domain: `test_v07_*` | PASS |
| V08 | service: `test_v08_same_key_replays_original_and_changed_payload_conflicts`, `test_v08_key_scope_isolates_principal_and_target`; API: `test_v12_v08_v09_replay_and_payload_mismatch` | PASS |
| V09 | service: `test_v09_accepted_replay_with_old_if_match_returns_original` (also closed turn), `…revoked_actor_cannot_read_private_receipt` (grant and consent), `…unseen_command_needs_if_match…` (428; 412 for other family/id/revision/garbage); domain: `test_v09_etag_family_and_revision_parsing` (strong comparison) | PASS |
| V10 | service: `test_v10_two_writers_one_revision_one_cas_winner`, `…injected_storage_failure_rolls_back_every_staged_effect` (retry with same key succeeds), `…observation_commit_failure_stores_nothing` | PASS |
| V11 | service: `test_v11_corrections_emit_versioned_invalidation_and_no_teacher_review`, `test_v11_owner_invalidation_is_idempotent_and_keeps_history`; domain: `test_v06_v11_*` | PASS |
| V12 | API: `test_v12_*` (Teacher/Child positive, replay, 18 typed negative codes with leak checks, field errors not echoing input, current revision only for authorised caller, turn/storage/stale, route surface = one POST); production app: `test_v12_production_app_source_does_not_import_cmd34` PASS; `test_v12_production_app_routes_do_not_mount_cmd34` **NOT_RUN** (Pillow) | PASS + 1 NOT_RUN |
| V13 | bridge: valid/wrong label/null confidence, 11 identity/provenance/shape mismatch cases (correlation, image, catalog, config, adapter version, model provenance, policy version, string/bool confidence, over-long label, malformed), timeout/provider/transient no-retry, F-01 containment, prohibited output → UNSAFE_CONTENT | PASS |
| V14 | bridge: typed context refused before call (and service fail-closed when typed required), derived input, unbound/RECAPTURE admission, unsupported media, render bytes hash mismatch/unreadable, `understand_with_narration` never used / no `narration_context`, real `UrllibJsonTransport` refused; service: `test_v14_*` | PASS |
| V15 | service: `test_v15_unsafe_or_malformed_provider_output_stores_nothing`, `…authoritative_age_window_not_legacy_under_nine_helper` (35/36/120/155/156/unknown), `…group_audience_checks_every_participant_age_and_consent`, `…provider_never_receives_age_or_child_content`; API/contracts Child projection leak checks | PASS |
| V16 | DECISIONS C1 choices + field map (plan §4 + record views); `fixtures/h_ai_review/` examples validated and pinned by `test_h_ai_review_handoff_examples.py`; consumer handoff `notes/H_AI_REVIEW_HANDOFF.md` with missing owner/provider/persistence/runtime/adoption list | PASS (documentary + test) |
| V17 | Legacy Vision 233/238 (+5 pre-existing skips) and BE2-01 337/338 (+1 Pillow skip) green; `tests/unit/test_lightning_vision_v2_server.py` **NOT_RUN** | PASS + NOT_RUN listed |

## Findings

- **F-01 (pre-existing legacy defect, not changed in C1).** `LightningVisionV2Adapter` maps an
  `OSError` from the transport to `TRANSIENT_RUNTIME_FAILURE` with `attempt_number=1`, but the
  V2 failure matrix only permits attempt 2 for that detail, so the adapter raises a pydantic
  `ValidationError` instead of returning a typed failure. The existing adapter tests do not
  exercise `OSError`. The approved plan preserves legacy behaviour, so the bridge contains it as
  `PROVIDER_ERROR` / `LEGACY_ADAPTER_CONTRACT_ERROR`, never retried, nothing stored
  (`test_v13_legacy_adapter_transient_branch_defect_is_contained`). A legacy fix needs its own
  owner decision.
- **F-02.** Pillow is absent from the venv, so the live-app route walk and the V2 server test
  are NOT_RUN. Installing it is outside C1 authority.
- **F-03 (fixed, failure preserved).** First `validate_repository_security.py` run returned
  `REPOSITORY_SECURITY_INVALID` (non-placeholder secret assignment) because a test module-level
  map was named `TOKENS = {...}`; renamed to `FIXTURE_PRINCIPALS`, re-run PASS.
- Fixture fidelity: the fake store's injected commit failure fires only for a unit of work that
  staged a write (a read-only unit cannot fail at commit in the fake). The deterministic CAS race
  uses a one-shot context-port hook to commit the competing writer between the loser's read and
  write; no thread timing is relied on.

## NOT_RUN (exact reason)

| Item | Reason |
|---|---|
| `test_v12_production_app_routes_do_not_mount_cmd34` (route walk of `create_app()`) | `pytest.importorskip("PIL")`: Pillow not installed; install not authorized. Static check that app.py does not import the router ran and passed |
| `tests/unit/test_lightning_vision_v2_server.py` | Collection imports `tools/lightning_vision_v2_server.py`, which imports Pillow (not installed) |
| `tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route` | Same Pillow skip (pre-existing BE2-01 behaviour) |
| Real provider/model inference, quality, latency, budget | Not authorized in C1 |
| Real BE1/BE2-03 owner adapters, SQL persistence, event delivery, live/P4 composition | Not in C1 scope; ports are ASSUMED_CONTRACT |
| Studio / Postgres / Redis runtime of any kind | Not in C1 scope |

## Validators (repository root)

See `evidence/metrics/C1_COMPONENT_CHECKS_20261016.json` for the final run (harness, repository
security, architecture, skeleton, `git diff --check`).
