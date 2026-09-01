# P2-T3 Phase A implementation evidence

- Evidence ID: EV-003-T3-01
- Date: 2026-09-01
- Approved scope: P2-T3 Phase A only; see `../../approvals/TASK_APPROVAL.md` ("Current approved
  scope — P2-T3 Phase A") and `P2_T3_PHASE_A_APPROVAL.md`.
- Data policy: synthetic fixture bytes, synthetic fixture text, and a synthetic-only prohibited
  lexicon. No real child data, credentials, provider call, model, weight, or GPU/cloud execution.

## Delivered artifacts

- `backend/src/sketch2life/contracts/schemas/vision.py`: `VisionImageReferenceV1`,
  `ImageDerivationProvenanceV1`, `VisionMediaValidationProvenanceV1` (defined independently of
  P2-T2, per the plan); `ObservedTextV1`/`TextLanguageDeclarationV1`; `VisionProfileId`/
  `VisionProfileV1`/`VisionProfileCatalogV1` with one deterministic fake entry only;
  `vision_profile_config_hash`/`vision_profile_catalog_hash`; `VisionUnderstandingRequestV1`;
  the shared `VisionResultEnvelopeV1`; the five candidate schemas
  (`EntityCandidateV1`/`ActionCandidateV1`/`RelationCandidateV1`/`ThemeCandidateV1`/
  `AmbiguousRegionCandidateV1`); the discriminated `VisionUnderstandingSuccessV1` /
  `VisionUnderstandingFailureV1` union; the disjoint `VisionProhibitedClaimCategory` /
  `VisionNonPolicyErrorDetail` detail enums; `ProhibitedLexiconEntryV1`/`ProhibitedLexiconV1`;
  the `vision-policy-match-view-v2` derived-view function; and
  `VisionFixtureManifestEntryV1`. Every model is frozen and `extra="forbid"`.
- `backend/src/sketch2life/application/ports/vision_understanding.py`: interface-only
  `VisionUnderstandingPort` (no file, byte, or hash operation).
- `backend/src/sketch2life/application/ports/vision_content_policy.py`: the replaceable
  `ObservableContentPolicyV1` port.
- `backend/src/sketch2life/infrastructure/ai/vision_lexical_policy.py`:
  `LexicalRegressionContentPolicy` (the Phase A known-violation lexical implementation) and
  `synthetic_prohibited_lexicon()`, a synthetic-only fixture lexicon with exactly one entry per
  closed prohibited-claim category.
- `backend/src/sketch2life/infrastructure/ai/fake_vision.py`:
  `DeterministicFixtureVisionAdapter`. Owns ingress verification (resolved profile, linked P2-T1
  `PASS`, real source-image read and SHA-256 comparison) before any simulated inference; maps a
  simulated raw-output string through the lossless-fence-unwrap-only repair rule and the typed
  error/retry matrix; runs the policy layer last, after schema and reference-integrity validation.
- `data/fixtures/manifests/vision-phase-a-v1.json`: synthetic Phase A fixture-scenario metadata
  (no image payload).
- `backend/tests/unit/test_vision_phase_a_contracts.py`,
  `backend/tests/unit/test_vision_content_policy.py`,
  `backend/tests/unit/test_vision_phase_a_adapter.py`,
  `backend/tests/unit/test_vision_fixture_manifest.py`: the Phase A contract/policy/adapter/fixture
  test suite (170 focused tests after the 2026-09-01 correction below; 114 at initial delivery).

## Correction — 2026-09-01

A follow-up review found three defects in the initial Phase A delivery. All three are fixed in
`backend/src/sketch2life/contracts/schemas/vision.py`, with focused proving tests; no adapter
behavior, fixture data, or approved scope changed.

| # | Defect | Structural rule now enforced | Proving tests |
|---|---|---|---|
| 1 | `VisionImageReferenceV1.artifact_ref` accepted an absolute machine path (POSIX, Windows drive, or UNC), which could leak a local filesystem layout into a shared artifact reference. | A new `field_validator` rejects `artifact_ref` values matching a host-OS-independent absolute-path check (`_is_absolute_machine_path`): a POSIX leading `/`, a Windows drive-absolute prefix (`^[A-Za-z]:[\\/]`), or a UNC prefix (`\\\\` or `//`). Non-empty relative/artifact references (e.g. `fixture:vision:v1`, `fixtures/drawings/sample.png`) remain accepted. | `test_absolute_machine_paths_are_rejected` (parametrized over POSIX/Windows-drive/UNC forms), `test_relative_artifact_reference_is_accepted` |
| 2 | `VisionUnderstandingFailureV1` only checked the prohibited-claim-vs-non-policy detail split and the coarse `policy_execution_state`; it did not enforce `retryable`, `attempt_number`, or `repair_attempted` against the approved per-row matrix, and did not reject a detail token paired with the wrong `error_code` family (e.g. `INPUT_NOT_VALIDATED` with `MODEL_LOAD_FAILED`). | A closed per-`VisionNonPolicyErrorDetail` rule table (`_NON_POLICY_DETAIL_RULES`) now fixes, for every one of the twelve non-policy detail tokens, its required `error_code`, `retryable`, and `attempt_number`, plus the allowed `repair_attempted` set (`{False}` for every row except the three `VISION_SCHEMA_INVALID` details, which allow `{True, False}` — `repair_attempted=true` is legitimate there only for the already-approved lossless fenced-unwrap case). The `PROHIBITED_CLAIM_DETECTED` branch additionally now fixes `retryable=false`, `attempt_number=1`, and `repair_attempted=false`. Every field in the shared envelope is checked in one `model_validator`, so no invalid combination is constructible. | `test_each_matrix_row_valid_combination_constructs`, `test_schema_invalid_permits_repair_attempted_true_for_any_of_its_three_details`, `test_invalid_failure_matrix_combinations_are_rejected` (24 cross-code/retry/attempt/repair perturbations), `test_prohibited_claim_detected_valid_combination_constructs`, `test_prohibited_claim_detected_rejects_invalid_attempt_repair_retry_combinations` |
| 3 | `ProhibitedLexiconEntryV1.term_normalized` was documented as "already in `vision-policy-match-view-v2` form" but nothing enforced it; an entry with mismatched case, punctuation, or whitespace could be stored and would silently under-match at evaluation time. | A `model_validator` now rejects construction unless `vision_policy_match_view(term_normalized) == term_normalized` and the term tokenizes to at least one token. The value is never silently normalized — a non-canonical entry is a construction error, not a coercion. | `test_canonical_lexicon_entry_is_accepted`, `test_non_canonical_lexicon_entry_forms_are_rejected` (case/hyphen/comma/underscore/leading-trailing-space/double-space/tab variants), `test_lexicon_entry_that_tokenizes_to_nothing_is_rejected`, `test_lexicon_entry_term_is_never_silently_normalized`, `test_canonical_entry_matching_behavior_is_preserved` |

All three fixes are additive validators on the frozen contracts already delivered; no field was
added, removed, or renamed, and `synthetic_prohibited_lexicon()`'s six existing entries were
already in canonical form, so no adapter or lexicon behavior changed for any previously-passing
fixture case.

## Required-behavior to test mapping

| Required behavior | Test(s) |
|---|---|
| Success (with observations) | `test_adapter_success_is_schema_valid_and_preserves_source` |
| All-empty valid success | `test_all_five_collections_present_and_empty_is_a_valid_success`, `test_adapter_all_empty_collections_is_a_valid_technical_success` |
| Missing collection -> `VISION_SCHEMA_INVALID` | `test_a_missing_required_collection_is_schema_invalid_not_an_implicit_empty_tuple`, `test_missing_collection_in_raw_output_is_schema_invalid` |
| Confidence presence/value rules | `test_entity_confidence_missing_key_and_explicit_null_are_distinguishable`, `test_entity_confidence_accepts_boundary_and_null_values`, `test_entity_confidence_rejects_out_of_range_values`, `test_ambiguous_region_has_no_confidence_field` |
| Unknown fields (top-level and nested) | `test_unknown_top_level_field_is_rejected`, `test_unknown_nested_candidate_and_observed_text_field_is_rejected`, `test_unknown_top_level_field_in_raw_output_is_schema_invalid` |
| Bad references / duplicate IDs | `test_duplicate_observation_id_across_candidate_kinds_is_rejected`, `test_relation_endpoints_must_resolve_to_entity_or_action_and_not_self_reference`, `test_theme_evidence_refs_reject_ambiguous_region_and_theme_targets`, `test_duplicate_observation_id_in_raw_output_is_schema_invalid`, `test_dangling_reference_in_raw_output_is_schema_invalid` |
| Raw unknown profile string rejected before the port | `test_unknown_profile_string_is_rejected_at_request_construction`, `test_unknown_profile_string_never_reaches_the_port` |
| P2-T1 / hash / unreadable failures | `test_missing_media_validation_is_input_not_validated`, `test_media_validation_not_passed_is_input_not_validated`, `test_source_image_unreadable_is_input_not_validated`, `test_source_image_hash_mismatch_is_input_not_validated` |
| Lossless fence unwrap | `test_fenced_complete_json_succeeds_with_repair_attempted_true`, `test_plain_complete_json_succeeds_with_repair_attempted_false`, `test_fenced_complete_json_failing_schema_has_repair_attempted_true` |
| Malformed / truncated output | `test_truncated_json_is_schema_invalid_with_repair_attempted_false` (fenced and plain) |
| Timeout | `test_timeout_never_retries_and_has_no_retry_branch` |
| Transient retry | `test_transient_failure_can_retry_once_and_then_succeed`, `test_transient_failure_can_retry_once_and_still_fail` |
| Model/device unavailable, permanent failure | `test_model_and_device_unavailable_never_retry`, `test_permanent_provider_failure_does_not_retry` |
| Policy block for each category | `test_policy_blocks_each_prohibited_claim_category_and_never_discloses_the_text` (parametrized over all six categories), `test_synthetic_lexicon_blocks_its_own_category_and_no_other` |
| Policy state / provenance | `test_succeeded_requires_passed_policy_state`, `test_failure_policy_execution_state_must_match_the_outcome_table`, `test_prohibited_claim_detected_rejects_a_non_policy_detail_token`, `test_non_policy_error_code_rejects_a_prohibited_claim_category_detail`, `test_schema_invalid_output_never_reaches_the_policy_layer`, `test_input_failure_envelope_carries_every_shared_envelope_field` |
| Source / hash preservation | `test_source_image_reference_is_preserved_on_success_and_every_failure`, `test_catalog_snapshot_hash_is_present_on_both_success_and_failure`, `test_success_provenance_matches_the_resolved_profile` |
| Match-view mechanics (case, punctuation, boundaries, substring negative, diacritics, symbols, immutability, version mismatch) | `backend/tests/unit/test_vision_content_policy.py` |

## Verified behaviors

- `source_image_ref` (the nested artifact-ref-plus-hash object) is unchanged on every success and
  every failure branch, including `INPUT_NOT_VALIDATED` at `attempt_number=0`.
- The adapter, not the port, verifies the resolved profile, the linked P2-T1 `PASS`, and the real
  source-image bytes' SHA-256 before any simulated inference; `VisionUnderstandingPort` declares
  only `understand(request) -> result` and exposes no file/hash operation.
- `profile_catalog_hash` is present and correct on both branches, including on
  `INPUT_NOT_VALIDATED`; `config_hash`/`adapter_version` exist only on `SUCCEEDED` and are rejected
  by `extra="forbid"` on a failure; no Phase A success carries `model_identifier`, `model_revision`,
  or `runtime_version`, not even as `null`.
- `policy_execution_state` is a structural invariant enforced by model validators:
  `SUCCEEDED` <=> `PASSED`; `PROHIBITED_CLAIM_DETECTED` <=> `BLOCKED`; every other failure <=>
  `NOT_EXECUTED`. No other combination is constructible.
- Repair is lossless-unwrap-only: a complete JSON object inside a Markdown fence succeeds with
  `repair_attempted=true`; a truncated payload (fenced or plain) is `VISION_SCHEMA_INVALID` with
  `repair_attempted=false`; a complete-but-invalid fenced payload is `VISION_SCHEMA_INVALID` with
  `repair_attempted=true`.
- `VISION_TIMEOUT` never retries (`attempt_number=1`, no retry branch exists); exactly one
  transient-provider retry is permitted (`attempt_number=2` on both the retry-then-succeed and
  retry-then-fail-again fixtures); `VISION_MODEL_UNAVAILABLE` and non-transient
  `VISION_PROVIDER_FAILURE` never retry.
- `ObservableContentPolicyV1`'s Phase A implementation runs only after schema and
  reference-integrity validation succeed; a schema-invalid payload never reaches it
  (`policy_execution_state=NOT_EXECUTED`). It returns only a closed
  `VisionProhibitedClaimCategory` token; the matched string never appears in the serialized
  result (asserted for all six categories).
- `vision-policy-match-view-v2` matches case-insensitively, treats Unicode punctuation/separator
  categories as token boundaries (including at and between phrase boundaries), never matches a
  substring inside a larger token, preserves and matches Vietnamese diacritics, treats symbol
  characters as content rather than boundaries, never mutates the stored `ObservedTextV1.value`,
  and fails lexicon construction deterministically on a `match_view_version` mismatch.
- `TextLanguageDeclarationV1` enforces `DECLARED`/`MIXED`/`NOT_DETERMINED` tag-count rules, rejects
  duplicate tags including case variants, canonicalizes tag order to byte-identical serialization,
  and per-result language tags never alter the static `vision_profile_config_hash`.
- `vision_profile_config_hash` and `vision_profile_catalog_hash` are deterministic and change with
  any profile-field or catalog-membership change; neither hash is stored inside the value it hashes.
- A raw unknown `requested_profile_id` string is rejected at `VisionUnderstandingRequestV1`
  construction, before `VisionUnderstandingPort` is ever invoked.

## Commands and results

| Command | Result |
|---|---|
| `backend/.venv/Scripts/python.exe -m pytest tests/unit/test_vision_phase_a_contracts.py tests/unit/test_vision_content_policy.py tests/unit/test_vision_phase_a_adapter.py tests/unit/test_vision_fixture_manifest.py` | 170 passed |
| `backend/.venv/Scripts/python.exe -m pytest` | 308 passed |
| `backend/.venv/Scripts/python.exe -m ruff check --no-cache src tests` | passed |
| `backend/.venv/Scripts/python.exe -m mypy src` | passed, 45 source files |
| `python tools/validate_harness.py` | `HARNESS_VALID` |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID` |
| `python tools/validate_skeleton.py` | `SKELETON_VALID` |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID` |
| `git diff --check` | passed |

## Boundaries respected

No Qwen/faster-whisper/transformers dependency, model or weight download, GPU/cloud/provider call,
runtime configuration, `.env` change, credentials, real child data, API/UI/mobile/database/queue/
storage integration, P2-T4/P2-T5 work, CLI, profile freeze, or Phase B approval work occurred.
`approvals/TASK_APPROVAL.md` was not edited. The uncommitted P2-T3 Phase B preparation note
(`P2_T3_PHASE_B_PREPARATION.md`) was preserved unchanged. No commit, push, or PR was created.

## Remaining gate

P2-T3 Phase B (real Qwen3-VL adapter, isolated runtime configuration, structured-output mapping
study, controlled benchmark, and the semantic-safety mechanism for unknown paraphrases) remains
unapproved, per `approvals/TASK_APPROVAL.md` and `P2_T3_PHASE_B_PREPARATION.md`.
