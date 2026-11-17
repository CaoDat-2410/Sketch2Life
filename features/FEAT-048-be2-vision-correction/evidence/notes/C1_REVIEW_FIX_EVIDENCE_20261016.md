# BE2-02 C1 review-fix evidence (C1-R01–R06) — 2026-10-16

- Input: Codex review `notes/C1_CODEX_REVIEW_20261016.md` (NEEDS_REVISION, 2 P1/4 P2) and its
  ignored probes under `evidence/local/codex-review-20261016/`.
- Authority: existing C1 approval (approvals/TASK_APPROVAL.md) and unchanged plan snapshot
  `plan/PLAN_REV1_APPROVED.md` SHA256 `f4733c88…`. Fixes stay inside D01–D11/V01–V17.
- Disposition written by Claude: **FIXED_PENDING_CODEX_REVIEW** for R01–R06. Not CLOSED; review
  acceptance is Codex's. Full BE2-02 remains NOT_DONE; nothing staged, committed or pushed.
- Historical reports (`C1_IMPLEMENTATION_EVIDENCE.md`, the Codex review and its metrics) are
  kept unchanged.

## Environment and identity

Worktree `.worktrees/be2-02-vision-correction`, branch `feature/be2-02-vision-correction`,
HEAD = base `6dcc57ee…`, 0 staged paths. Before editing, all 18 C1 source/test files matched the
hashes recorded at implementation (= the hashes Codex reviewed). Shared Python 3.12.10 venv with
`PYTHONPATH`/`MYPYPATH` pinned to this worktree's `backend/src` (`sketch2life.__file__` verified);
`PYTHONDONTWRITEBYTECODE=1`, `-B`, fresh `--basetemp` under ignored
`evidence/local/claude-fix-20261016/`. No installs, network, provider, model or services.

## Before / after (regression file `backend/tests/unit/test_vision_analysis_review_fixes.py`)

| Run (UTC) | Source | Result |
|---|---|---|
| 13:22:32Z before | unfixed (= reviewed hashes) | 37 collected: **28 failed**, 9 passed (the 9 are boundary/positive/unchanged-semantics guards). JUnit + log: `evidence/local/claude-fix-20261016/before/` |
| 13:26:52Z after | fixed | 37 collected: **37 passed** |
| Codex service probes after | fixed | `test_service_probes.py -k "full_eligibility or observation_replay"`: **6 passed**, 3 deselected (before: 6 failed) |
| Codex bridge probe, observe-only variant after | fixed | 121-char id → `failed/OUTPUT_MALFORMED`, no analysis; 257 entities → same; wrong foundation scope → `rejected/JOB_SCOPE_MISMATCH`, 0 provider calls. The unmodified probe now aborts at `analysis_record(..., None)` because no analysis exists — the intended effect |
| Codex domain probe after | fixed | history probe: 257 corrections, revision 258, `schema_result: accepted`; store now has `provider_results` |

Before-fix failure categories: R01 replay returned `accepted/authoritative` after context, source,
consent, session or age change and in the raced-winner path; R02 stored accepted after session end
or age unknown/35/156 and for an ineligible group member; R03 accepted every foundation scope
mismatch; R04 accepted 121-char ids and 257-item collections; R05 record failed `too_long`;
R06 had no resolver/retained document (AttributeError/ImportError/TypeError on the new API).

## Changes per finding

| ID | Change | Regression tests (all in the fix file unless noted) |
|---|---|---|
| R01 (P1) | `_observation_replay` judges current authority: full gate → `rejected`; stored stale; context revision → `stale/context_changed`; source hash → `stale/source_changed`. Early and raced-winner paths. No provider call, no mutation; CMD-34 receipt replay untouched | `test_r01_early_replay_rechecks_current_applicability` ×5, `test_r01_unchanged_replay_stays_authoritative`, `test_r01_raced_winner_replay_rechecks_applicability`, `test_r01_accepted_correction_receipt_replay_keeps_original_semantics` |
| R02 (P1) | Post-provider acceptance runs the complete `eligibility_code` (consent, purpose, session, every audience age 36–155); failure = `rejected`, nothing stored; context/source movement still `stale` | `test_r02_full_eligibility_is_rechecked_after_provider` ×4, `test_r02_age_boundaries_after_provider_stay_accepted` (36, 155), `test_r02_group_audience_ineligible_after_provider_is_rejected`; existing consent/stale tests unchanged |
| R03 (P2) | `JobLineageView` carries `session_id/subject_refs/purpose_code/target_id`; `AiJobRepositoryLineage` maps the foundation `JobScope`; `job_scope_matches` + `JOB_SCOPE_MISMATCH` in `check_lineage` (before provider; also on the post-provider re-check). BE2-01 code/state unchanged | `test_r03_foundation_job_scope_mismatch_is_rejected_before_provider` ×6 (session wrong/None, subject wrong/extra, purpose, target), `test_r03_matching_foundation_scope_is_accepted_order_insensitive`; domain `test_v07_*` extended |
| R04 (P2) | Domain `OBSERVATION_REF_MAX=120`, `OBSERVATION_COLLECTION_MAX=256` shared with contracts; `observation_bounds_violation` (ref pattern/length, ShortText labels, candidates, unknown-confidence refs, ambiguous regions) in bridge (typed detail) and service (any provider), before persistence | `test_r04_contract_incompatible_mapped_output_is_malformed_before_storage` ×4 (real bridge, scripted transport; API then 404 with no commit), `test_r04_boundary_outputs_survive_cmd34_and_replay_end_to_end` ×4 (120 chars, 256 entities, 256 null-confidence, 256 ambiguous: CMD-34 200 + replay 200 + record/candidate DTOs valid), `test_r04_service_rejects_contract_incompatible_output_from_any_provider` |
| R05 (P2) | `AnalysisRecordV1.corrections` uncapped (complete append-only history); rationale in DECISIONS | `test_r05_history_beyond_256_corrections_stays_complete_and_valid` (260 corrections, versions 2..261, all receipts kept, first receipt replay identical) |
| R06 (P2) | `ObservationSucceeded.result_document` (canonical full typed result); hash must equal evidence; immutable `ProviderResultRecord` `result:<analysis_id>` inserted in the same unit as observation/head; `resolve_provider_result` Teacher/internal resolver with hash re-check | `test_r06_full_typed_provider_result_is_retained_and_resolvable` (real bridge; rebuilt `VisionUnderstandingSuccessV2` equals original incl. correlation; unchanged after corrections), `…resolver_is_teacher_only_and_concealed`, `…failed_commit_leaves_no_dangling_result_ref`, `…result_record_hash_must_match_content`, `…provider_document_must_match_reported_result_hash`; contract `test_v16_r06_provider_result_example_resolves_the_emitted_ref` |

Existing tests updated only where the fix intentionally changes shape: domain lineage view
constructor (+ scope mismatch asserts), V11 store field set (+`provider_results`), V15 group test
now aligns the foundation job audience with the pin (required by R03). Golden examples: the six
existing files are byte-identical; one new `fixtures/h_ai_review/provider_result_record.json`.

## Final checks (UTC 2026-10-16)

| Check | Result |
|---|---|
| Focused C1 suite 13:27:41Z (8 files) | 214 collected: **213 passed, 1 skipped** (Pillow, NOT_RUN), 0 failed |
| Legacy Vision regression 13:26:53Z | 238: 233 passed, 5 pre-existing skips |
| BE2-01 regression 13:26:55Z | 338: 337 passed, 1 skipped (Pillow) |
| ruff / mypy strict 13:27:43Z (19 paths) | PASS / PASS |
| Validators | see `metrics/C1_REVIEW_FIX_CHECKS_20261016.json` |

One intermediate focused run failed (213/214): the golden-example path check `":\\" not in text`
matched an escaped quote inside the new embedded JSON document; replaced by a Windows drive-path
regex, then 213 passed/1 skipped. Recorded here; no assertion was weakened for behaviour.

## Still NOT_RUN / not changed

- Pillow-dependent live-app route walk and `test_lightning_vision_v2_server.py` (Pillow absent).
- N01 (P3): body is buffered before the 32 KiB check — recorded limitation, unchanged.
- Not promoted by review and not changed: real owner-fence correction TOCTOU, mutated foundation
  input hash, hash-coverage/typing suggestions. Legacy F-01 remains contained, not fixed.
- Real provider/model, typed provider context, BE1/BE2-03 adapters, SQL, delivery, live composition.
