# BE2-05 implementation evidence — SKETCH_REVIEW_COMPONENT_OFFLINE (K1–K7)

- Date: 2026-10-19 (Asia/Saigon). Author: Claude, under the approval in `../../approvals/TASK_APPROVAL.md`.
- Status: **READY_FOR_CODEX_REVIEW**. Not accepted; nothing staged, committed, pushed or merged.
- Plan: `../../plan/PLAN_R2_APPROVED.md` (SHA256 ab295305…) with selections in `../../plan/PLAN.md`.
- Branch `feature/be2-05-sketch-review`, worktree `.worktrees/be2-05-sketch-review`, base
  58293f1a29ec630e2603c2860b6a2337fadfa713 (no upstream). Metrics:
  `../metrics/BE205_CHECKS_20261019.json`. Raw logs/JUnit: ignored `../local/checks-20261019/`.

## 1. What was built (offline component only)

| Plan | Module | Content |
|---|---|---|
| K1 | `backend/src/sketch2life/domain/sketch_review.py` | ReviewTarget + identity/ref-set, exact review key, append-only entries, terminal marker, D-1 global revoke, D-3 current-entry projection, composite ETag |
| K2 | `backend/src/sketch2life/contracts/schemas/sketch_reviews.py` | Sketch binder over unchanged DATA-24 V1 (ShortText ≤128/NFC, OD-02), `SketchReviewResultV0`, queue view, child payload, error→status table |
| K3 | `backend/src/sketch2life/application/ports/sketch_review.py`; `infrastructure/sketch_review/coordination.py`, `fakes.py` | Ports; store/UoW; `CoordinatedSketchReviewRepository` on the shared coordinator; token port; fixtures (policy, moderation, authority, context, ticket/cache/dispatcher) |
| K4 | `infrastructure/sketch_review/adapters.py` | ReviewTarget from public `revalidate()` (content hash re-checked with the public `content_sha256`); Teacher-only `get_record`; coordinated describe/quarantine |
| K5–K6 | `backend/src/sketch2life/application/services/sketch_review.py` | CMD-35, moderate, queue/projection, eligibility, child payload, notices/refresh, quarantine delivery after commit |
| K7 | `infrastructure/sketch_review/harness.py`; 6 test files; examples fixture | Real SK1 chain + 05 on the same coordinator/fences; `fixtures/h_ai_review/sketch_review_examples.json` (generated, LF) |

No SK1 source/test/fixture, no DATA-24 pack/test/fixture and no other lane's code was changed
(Git status: only the four routing/ignore documents are modified; everything else is new).

## 2. Acceptance → test mapping (§10 of the approved plan)

| ID | Test(s) | Result |
|---|---|---|
| RV-P01 | `test_sketch_review_service.py::test_rv_p01_real_proposal_approved_exactly` | PASS |
| RV-P02 | `…::test_rv_p02_only_reviewed_audience_receives` | PASS |
| RV-P03 | `…::test_rv_p03_replay_and_semantic_duplicate` | PASS |
| RV-P04 | `…::test_rv_p04_reject_and_request_changes_recorded[reject/request_changes]` | PASS |
| RV-P05 | `…::test_rv_p05_approve_then_reject_same_key_revokes` | PASS |
| RV-P06 | `…::test_rv_p06_new_version_reviewable_after_reject` | PASS |
| RV-P07 | `…::test_rv_p07_views_and_composed_projection_conform`; contract C04 | PASS |
| RV-P08 | `…::test_rv_p08_audit_sample_without_content` | PASS |
| RV-P09 | `…::test_rv_p09_text_only_fences_result_document`; domain `test_target_ref_set_includes_result_document_and_text_only` | PASS |
| RV-P10 | `…::test_rv_p10_reject_policy_change_then_new_version_approved` | PASS |
| RV-N01 | `test_sketch_review_eligibility.py::test_rv_n01_child_sees_status_only_until_approved`, `test_rv_n01b_blocked_and_stale_status_only` | PASS |
| RV-N02 | `…::test_rv_n02_guessed_artifact_ref_gets_no_ticket` | PASS |
| RV-N03 | service `test_rv_n03_blocked_moderation_has_no_bypass`, `test_rv_n03b_blocked_detected_on_approve_without_prior_moderation` | PASS |
| RV-N04 | service `test_rv_n04_admin_device_and_no_preset_path` | PASS |
| RV-N05 | service `test_rv_n05_other_class_and_other_org_are_not_found` | PASS |
| RV-N06 | service `test_rv_n06_if_match_required_and_current` | PASS |
| RV-N07 | service `test_rv_n07_target_mismatch_and_path` | PASS |
| RV-N08 | service `test_rv_n08_reason_required_and_generic_context_refused`; contract C01 | PASS |
| RV-N09 | service `test_rv_n09_audience_and_consent` | PASS |
| RV-N10 | service `test_rv_n10_target_not_pending` | PASS |
| RV-N11 | eligibility `test_rv_n11_access_closes_and_stays_closed[consent/quarantine/context/policy]` | PASS |
| RV-N12 | service `test_rv_n12_payload_mismatch_and_replay_after_scope_loss`, `test_rv_n12b_malformed_key` | PASS |
| RV-N13 | service `test_rv_n13_policy_unresolved_and_policy_change_stales` | PASS |
| RV-N14 | eligibility `test_rv_n14_cache_and_subscription_do_not_leak_after_revoke` | PASS |
| RV-N15a | chain `test_rv_n15a_only_allowlisted_public_calls`, `test_rv_n15a_static_no_producer_store_access` | PASS |
| RV-N15b | chain `test_rv_n15b_content_source_provenance_unchanged` | PASS |
| RV-N15c | chain `test_rv_n15c_public_revalidation_mutation_is_bounded` | PASS |
| RV-N16 | service `test_rv_n16_terminal_blocks_reapproval[reject/request_changes]` | PASS |
| RV-N17 | eligibility `test_rv_n17_device_never_reaches_producer_teacher_read` | PASS |
| RV-N18/N19 | service `test_rv_n18_n19_terminal_survives_05_policy_stale[reject/request_changes]` | PASS |
| RV-N20 | service `test_rv_n20_other_audience_and_context_keys_still_terminal` | PASS |
| RV-N21 | domain `test_marker_history_equivalence_rv_n21`, `test_no_current_entry_keeps_version_terminal_rv_n24` | PASS |
| RV-N22 | eligibility `test_rv_n22_terminal_decision_on_audience_b_revokes_audience_a[reject/request_changes]` | PASS |
| RV-N23 | service `test_rv_n23_request_changes_then_reject_same_key`; domain `test_request_changes_then_reject_keeps_marker_and_moves_current_d3` | PASS |
| RV-N24 | service `test_rv_n24_no_current_entry_never_reopens[reject/request_changes]` | PASS |
| RV-R01/R02 | races `test_rv_r01_r02_publication_after_hold_waits_for_review_commit[quarantine/consent]` | PASS |
| RV-R03 | races `test_rv_r03_sketch_policy_change_before_hold_restarts` | PASS |
| RV-R04 | races `test_rv_r04_vision_write_before_hold_restarts` | PASS |
| RV-R05 | races `test_rv_r05_result_document_quarantine_before_hold_restarts` | PASS |
| RV-R06 | races `test_rv_r06_05_policy_change_before_hold_decides_on_new_policy`, `test_rv_r06b_grant_revoked_before_hold` | PASS |
| RV-R07 | races `test_rv_r07_every_04_mutation_of_pending_bumps_eligibility` | PASS |
| RV-R08 | races `test_rv_r08_identity_change_between_snapshot_and_read` | PASS |
| RV-R09 | races `test_rv_r09_same_thread_publication_is_deferred_to_unit_exit` | PASS |
| RV-R10 | races `test_rv_r10_rollback_bumps_nothing_and_deferred_still_runs` | PASS |
| RV-R11 | races `test_rv_r11_exception_releases_the_coordinator` | PASS |
| RV-R12 | races `test_rv_r12_same_etag_race_and_fresh_retry_d2` | PASS |
| RV-R13 | races `test_rv_r13_two_approvals_one_review` | PASS |
| RV-R14 | races `test_rv_r14_same_key_concurrently_commits_once` | PASS |
| RV-R15 | races `test_rv_r15_unstable_token_gives_up` | PASS |
| RV-R16 | races `test_rv_r16_duplicate_notice_is_idempotent` | PASS |
| RV-R17 | races `test_rv_r17_reject_and_05_policy_interleavings[2]` | PASS |
| RV-C01 | contract `test_rv_c01_*` (binder on shared fixtures; 7 shared negatives rejected by V1) | PASS |
| RV-C02 | contract `test_rv_c02_shared_pack_bytes_unchanged_from_baseline` | PASS |
| RV-C03 | contract `test_rv_c03_error_codes_exist_in_srs` | PASS |
| RV-C04 | contract `test_rv_c04_examples_regenerate_byte_identically` | PASS |

## 3. Checks actually run (Windows, CPython 3.12.10, `backend/.venv` of the root checkout,
`PYTHONPATH`/`MYPYPATH` pinned to this worktree's `backend/src`; validators from repo root)

| Check | Result |
|---|---|
| Focused 05 (6 files) | 99 passed, 0 failed, 0 skipped |
| X01 SK1 focused (same 6 files as SK1 acceptance) | 175 passed |
| X02 `tests/contract` without 7 Pillow-importing modules | 400 passed, 3 skipped (all "live app import needs Pillow"); the 7 modules: NOT_RUN (Pillow absent) |
| X03 BE2-02/BE2-03 unit (14 files) | 405 passed |
| X04 all `tests/unit`, task branch | 2426 passed, 18 failed, 37 skipped, 34 errors |
| X04 all `tests/unit`, baseline 58293f1 (shared worktree, read-only run) | 2340 passed, 18 failed, 37 skipped, 34 errors |
| X04 comparison | failed/error/skipped sets **identical**; the 86 new 05 unit tests all pass; no baseline test changed status. Causes: missing Pillow/imageio, local-only semantic activity catalog, `tools.*` import path |
| Races + eligibility repeated 5× | 30 passed each run |
| Ruff (9 source + 6 test files) | All checks passed |
| mypy (9 source files) | no issues |
| `validate_harness`, `validate_repository_security`, `validate_architecture`, `validate_skeleton` | all exit 0 |
| `git diff --check` | exit 0 |

An earlier X04 attempt ran concurrently with the contract run and collided on the temporary
basetemp (568 setup `FileNotFoundError`); it was discarded and rerun alone. Not run: Studio,
providers, network, database, HTTP routes, UI, any runtime.

## 4. Notes and interpretations for review

1. **Protocol (OD-05).** Every 05 unit runs as an `assistance` unit of the chain's coordinator.
   Reads of the producer (`revalidate`, `get_record`) happen only outside the unit; inside, only
   `coordinator.read`, `fences.hold` and the 05 store. The 05 eligibility epoch is bumped after
   the inner commit, inside the hold. Guarantees are single-process/fake only.
2. **Guard order inside the final unit:** hold → receipt (same key → restart → replay) → head CAS
   (losing same-ETag command → 412, D-2) → moderation insert if absent → marker/blocked check →
   entry/marker/revocations/head/intents/audit/receipt. The early marker read outside the unit
   also checks the head revision and receipt first, so it never turns a D-2 loser into 409.
3. **R03/R04/R05 error code.** After the final hold sees a moved epoch, round 2 re-reads the
   producer, whose `review_revision` moved with its own invalidation; the composite ETag then
   yields 412 `STALE_AGGREGATE` (guard order: If-Match before target state). The tests assert one
   stale hold, the producer's stale reason and no effective approval.
4. **Child payload status.** Eligibility denial is one generic outcome. The payload shows
   `pending` only while the target is pending with no terminal marker and no blocked moderation,
   otherwise `unavailable` (no content in either case), mirroring SK1 `device_view`. Flag if the
   reviewer wants a single status for every non-eligible case.
5. **Record V1 `policy_version`** is an OpaqueId; the 05 label (`review policy@version|producer
   policy@version`) is mapped to `rp_<sha256[:32]>`. The full label stays in the 05 entry.
6. **Structural simplifications** (same responsibilities as plan §6): the queue source is
   `SketchReviewTargetReader.queue_record`; token hold is `SketchReviewUnitOfWork.hold`.
7. **RV-N15c** uses an owner fact changed without an epoch bump (DI-18 residual): 04's public
   revalidation catches it at the next read; mutation stays within the allowed lifecycle fields.
8. **Moderation fixture** additionally blocks when a descriptor hash differs from the pinned
   AssetRef hash; a missing/quarantined descriptor refuses the decision as `STALE_CONTEXT`.
9. **Harness constraint:** within one harness each `pending()` needs a distinct A1 request
   (level/canvas); an identical request is an A1 cache hit without a new job (SK1 behaviour).

## 5. Open gates (unchanged by this checkpoint)

Runtime BE2-01/04; adopted moderation/reviewer policy (BE2-14) and real moderation; BE1 teaching
authority, consent/membership, CMD-60 ticket/gateway, read model/realtime; database fencing and
transaction boundary; SQL; event delivery; HTTP; FE-06/T07/C04 UI; INTG-05; CR-01/03/04/05 if
chosen. Card BE2-05 stays IN_PROGRESS / NOT_DONE; reviews by P2/P1/P4 still required.
