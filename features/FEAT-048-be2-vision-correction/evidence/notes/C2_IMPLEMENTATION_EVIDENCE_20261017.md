# BE2-02 C2_TYPED_CONTEXT_OFFLINE — implementation evidence, 2026-10-17

**C2_CODE_COMPLETE_PENDING_CODEX_REVIEW.** Offline component candidate only. Not owner
acceptance, not full BE2-02/FR022 completion, not real inference, serving, model quality,
real owner adapters, persistence or production privacy/adoption. Full card IN_PROGRESS/NOT_DONE.

## Authority and identity

- Approval: ../../approvals/C2_TASK_APPROVAL.md (verbatim, 2026-10-17 11:20 +07:00), plan
  revision2 SHA256 `4b339514d3d5bf01b9a8c23f0a15ea5e71b4d2f1389db9e141e31aa322cd57c2`, approved
  bytes ../../plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md (saved before any status change). Owner
  selected Q1–Q5 as recommended. C1 approval (`ebe826ce…`), C1 approved plan (`f4733c88…`) and C1
  acceptance unchanged.
- Worktree/branch `.worktrees/be2-02-vision-correction` / `feature/be2-02-vision-correction`,
  HEAD `98876fe762a61e64b61980cd0634415e6f5e1dfb`, staged paths 0 before and after. Pre-existing
  uncommitted planning edits preserved. Nothing staged/committed/pushed.
- Executor Claude; reviewer Codex. Source/test/fixture hashes: ../metrics/C2_IMPLEMENTATION_CHECKS_20261017.json.

## What changed and why (C2.1–C2.4)

| Batch | Change | Why |
|---|---|---|
| C2.1 | `domain/vision_context.py`: strict owner snapshot (`VisionContextSnapshot`, member/topic/request facts), `verify_context_snapshot`, FIXTURE band policy, allowlisted `ProviderContextProjection`, `payload_digest`/`context_digest`, `pin_context`, static `ContextCapability`; `VisionContextSourcePort` | Trusted, coherent, member-by-member typed context; identity removed only after every member passed; two distinct canonical digests |
| C2.2 | `contracts/schemas/vision_context.py` (`VisionTypedContextV1`, `LightningVisionContextRequestV1/ResultV1`, 0.1-candidate); `contracts/schemas/analysis_context_results.py` (typed DATA-22 records 0.2-candidate); additive domain `TypedContextBinding`, `EvidenceKind.offline_context_adapter`, evidence/head binding fields | Strict versioned wire; image_only 0.1 DTOs/goldens untouched and reject typed records |
| C2.3 | `application/services/vision_analysis.py`: capability → snapshot gate → pinned projection/binding before the one call; echo check; post-call re-verification (refusal = discard, revision/digest movement = stale); typed replay/applicability; duplicate refusal in the shared eligibility gate; typed 0.2 projections. Fakes: `FakeVisionContextSource`, provider capability/binding echo, immutable binding in CAS. Harness: typed wiring, `EchoContextTransport`, typed example | Binding atomic with head/observation/result in the fake UoW; moved/revoked context never authoritative, never rebound |
| C2.4 | `infrastructure/vision_analysis/context_adapter.py`: offline adapter; pure helpers extracted from `legacy_v2.py` (bridge behaviour unchanged) | Exact minimized request to candidate `/v1/vision/context` once; strict wrapper echo + nested V2 checks; whole wrapper retained/hashed; truthful `offline_context_adapter` |

Candidate details (enums, field-use names, null semantics, digest inputs, gate order) are in
../../DECISIONS.md "C2 candidate technical choices".

## Actual checks (fresh C2 run, 2026-10-17 ~04:44Z; C1 counts in older notes are history)

Run with the existing Python 3.12.10 venv, import root asserted to this worktree's
`backend/src`; existing base Pillow 12.1.0 and the already-present ignored python-multipart 0.0.32
loaded process-locally; nothing installed; shared venv unchanged; in-process external networking
blocked; no PostgreSQL/Redis/Studio/model/provider. Wrapper and raw JUnit/logs: ignored
`evidence/local/c2-typed-context-20261017/` (old C1 wrapper untouched).

| Group | Collected | Passed | Failed | Errors | Skipped |
|---|---|---|---|---|---|
| C2 focused (4 new files) | 179 | 179 | 0 | 0 | 0 |
| C1 focused 8 files + V2 server (incl. production route walk) | 240 | 240 | 0 | 0 | 0 |
| Legacy Vision/V2/Qwen (6 files) | 238 | 233 | 0 | 0 | 5 (pre-existing parametrised skips) |
| BE2-01 non-service (`test_ai_job_*`, 11 files) | 338 | 338 | 0 | 0 | 0 |

Setup history: BE2-01 attempt 1 under a subprocess-blocking guard reported 323/15 failed — all in
`test_ai_job_b6_conformance.py`, whose runner collects suites via a local `pytest` subprocess that
the wrapper blocked. Not a SUT failure; rerun with local subprocess allowed for that group (network
guard kept) passed 338/338. Attempt-1 receipts kept locally.

Static/validators: ruff PASS and `mypy --strict` PASS on 16 changed/new paths;
`tools/validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`,
`validate_skeleton.py` exit 0; `git diff --check` exit 0 (tracked) and no trailing
whitespace/CRLF in new files.

## C2-A01–A14 mapping (tests in backend/tests/; all PASS in the run above)

| ID | Evidence |
|---|---|
| A01 | unit/test_vision_context_domain.py `test_c2_a01_member_facts_reject_coercion_bypasses` (14), `…topic_and_request_facts…`, `…snapshot_and_binding_reject_malformed_values`; contract/test_vision_context_contracts.py `test_c2_a01_domain_projection_and_wire_contract_agree_exactly`, `test_c2_a01_a04_typed_context_rejects_extras_coercion_and_unbounded_values` (18), `…topic_key_is_required_even_when_null` |
| A02 | domain `test_c2_a02_*` (scope/request/source/policy/revision 15, audience missing/extra/duplicate, port disagreement 6, coherent fixture); service `test_c2_a02_untrusted_or_incoherent_context_refuses_before_invocation` (9, zero calls/writes), `…conflicting_old_and_new_ports…`, `…unavailable_or_malformed…`, `…old_port_duplicate_age_facts_are_refused_in_c1_gate_too` |
| A03 | domain `test_c2_a03_fixture_bands_cover_36_to_155_exactly_once`, `…band_policy_rejects_overlap_gaps_and_partial_coverage` (6), `…projection_is_per_member_sorted_bands_without_identity_or_mean`, `test_c2_a03_a04_one_member_failing_refuses_the_whole_context` (7); service `test_c2_a03_one_ineligible_member_refuses_the_call` (4), `…group_projection_keeps_one_band_per_member` |
| A04 | domain `test_c2_a03_a04_*` (field denial), `test_c2_a04_absent_topic_is_null_never_empty`; adapter `test_c2_a04_a05_serialized_bytes_carry_no_internal_or_child_data` (wire bytes + captured logs); contract extras test; service `test_c2_a10_child_projection_stays_0_1_refs_only_for_typed_analyses` |
| A05 | adapter `test_c2_a05_exact_context_request_is_posted_once_to_the_candidate_path`, `test_c2_a04_a05_serialized_bytes…`, `test_c2_a05_v2_endpoint_and_payload_are_unchanged_for_image_only` |
| A06 | service `test_c2_a06_capability_mismatch_or_missing_dependencies_refuse_without_call`; adapter `test_c2_a06_no_image_only_fallback_and_no_derived_input`, `…inconsistent_pinned_context_refuses_before_image_load` (5), `…context_pinned_to_another_image…`, `…real_http_transport_is_refused_and_capability_is_static` (0 image loads, 0 posts). Real serving: NOT_RUN (no endpoint exists) |
| A07 | adapter `test_c2_a07_wrong_or_missing_echo_or_nested_identity_is_malformed_and_unstored` (13), `…whole_wrapper_is_retained_and_hashed`, `…transport_failures_map_once_without_retry` (2); service `test_c2_a07_a10_provider_must_echo_the_pinned_binding` |
| A08 | service `test_c2_a08_same_revision_same_band_exact_age_drift_is_stale`, `…revision_or_digest_movement_stores_stale` (4), `…revocation_or_ineligibility_after_the_call_discards_everything` (7, zero writes), `…source_and_lineage_movement_keep_c1_behaviour` |
| A09 | service `test_c2_a09_same_revision_digest_drift_blocks_current_authority_not_history` (replay stale, downstream not_applicable, new correction STALE_CONTEXT, receipts replay, meaning not revived), `…transfer_revocation_after_acceptance…`, `…revoked_disclosure_blocks_receipt_replay` |
| A10 | full C1 focused suite 240/240 (incl. all C1 guards, golden bytes, route walk); adapter `test_c2_a10_unsafe_nested_text_is_blocked_by_the_reused_policy`, bounds/strict-confidence rows of the A07 test; service `test_c2_a10_child_projection…`. Two seam tests changed and explained below |
| A11 | Documentation: H_AI_REVIEW_HANDOFF.md "C2 typed-context candidate" section (consumers, candidate contracts, deferred FR022/runtime, ASSUMED_CONTRACT/B-12 labels unchanged) — document evidence, not a test |
| A12 | domain `test_c2_a12_*` (reorder stability, 10 internal movements change context digest with unchanged payload digest where internal-only, projection changes move both, recomputable payload digest/no self-time fields, strict hash refusals 6, projection rejects) |
| A13 | service `test_c2_a13_failed_commit_leaves_no_partial_binding_or_record`, `…binding_is_immutable_under_cas`, `…sequential_replay_makes_zero_new_calls`, `…concurrent_first_submissions_keep_one_atomic_winner` (2 calls, 1 stored winner; no global exactly-once claim) |
| A14 | contract `test_c2_a14_typed_records_are_0_2_and_old_strict_dtos_reject_them`, `…head_binding_must_equal_the_evidence_copy`, `…typed_provenance_is_truthful` (6), `…domain_evidence_kind_and_mode_stay_truthful`, `…image_only_goldens_are_still_the_0_1_build`, typed golden `test_c2_typed_golden_example_*`; C1 `test_v16_*` golden equality unchanged; C1 golden blob hashes equal HEAD |

## Changed C1 seam tests (narrow, not weakened)

- `unit/test_vision_analysis_service.py::test_v15_provider_never_receives_age_or_child_content`:
  the C1 fake-only `ObservationContext` field set is superseded by the pinned
  `ProviderTypedContext`; the test still asserts an exact allowlist (projection and binding field
  sets, request field set unchanged) and absence of Child text, ids and exact ages. Actual
  serialized provider bytes are checked in `test_vision_context_adapter.py`.
- `unit/test_vision_analysis_legacy_bridge.py::test_v14_typed_context_is_refused_before_any_call`:
  constructs the new typed context; its refusal/no-call assertions are unchanged.
- No other C1 test, golden fixture or image_only DTO changed. The new typed golden is
  ../../fixtures/h_ai_review/typed_context_example.json (image bytes elided to their hash).

## Points for Codex review

1. Snapshot gate order and post-call split (any refusal → discard; revision/digest → stale) in
   `application/services/vision_analysis.py` (`_typed_current`, `_typed_status`, `_applicable`).
2. context_digest input set and strict pre-hash walk in `domain/vision_context.py`; whether
   anything internal belongs in or out (e.g. session_active, admission receipt not included).
3. Adapter interception of the unchanged V2 adapter, JSON-mode strict wrapper validation and
   whole-wrapper retention (`context_adapter.py`); nested V2 stays lax except raw confidences.
4. Shared-gate duplicate hardening also affects image_only (behaviour change only for malformed
   owner data).
5. Transfer-permission revoke blocks current authority but not the Child's own receipt replay
   (disclosure unchanged) — confirm this matches CMD-34/DATA-21 intent.
6. Concurrency evidence is a deterministic nested-call interleaving in the fake store, not a
   real multi-process race; real DB isolation remains a later gate.

## Remaining gates (not provided by C2)

Real provider endpoint/server/prompt and model consumption of context (echo ≠ use); model/profile/
serving/license/budget adoption and quality; adopted pedagogical age-band policy; real BE1/BE2-03
owner adapters (context revision, transfer/field-use permission, topic provenance, request enums),
OwnerFence (ASSUMED_CONTRACT) and B-12 HANDOFF; FR022/UC-018 deferred inputs (Child text, Teacher
feedback, confirmed meaning, action summaries); durable persistence/outbox, live composition,
independent sign-off. BE2-01 stays WAITING_STUDIO, CR01 open; Lightning recovery not confirmed.
