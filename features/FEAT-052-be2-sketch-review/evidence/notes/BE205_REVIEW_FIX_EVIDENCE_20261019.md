# BE2-05 review-fix evidence — RV-CR01..RV-CR05 (2026-10-19)

- Status: **READY_FOR_CODEX_REREVIEW**. Component NOT_ACCEPTED; card BE2-05 IN_PROGRESS / NOT_DONE.
- Scope: same-scope fixes inside the approved K1–K7 (TASK_APPROVAL, plan `PLAN_R2_APPROVED.md`
  SHA256 ab295305…). No new approval requested; no stage/commit/push/merge.
- Input review: `BE205_CODEX_REVIEW_20261019.md` SHA256
  0091e8e7fcdab235beee98f28fefc6919decd2b94e43d2c2f721416e4a91194a (+ metrics 3964d566…).
- Pre-fix identity: branch `feature/be2-05-sketch-review`, HEAD
  58293f1a29ec630e2603c2860b6a2337fadfa713, staged 0; all 19 references of
  `BE205_CHECKS_20261019.json` matched SHA256/bytes before any edit (no drift).
- Preserved unchanged: approval, approved plan, `PLAN.md`, original implementation note/metrics,
  Codex review note/metrics and every Codex probe/receipt under `local/codex-review-20261019/`.
- Metrics: `../metrics/BE205_REVIEW_FIX_CHECKS_20261019.json`. Raw logs/JUnit/probe outputs:
  ignored `../local/fix-20261019/` (`before/`, `after/`, `checks/`).

## 1. Disposition per finding

| Finding | Status | Fix (file:line at the new snapshot) | Regression | Before → after (actual) |
|---|---|---|---|---|
| RV-CR01 (P1) old PASSED overrides new BLOCKED | FIXED | Moderation records keyed by complete identity — content, pinned ref hashes and moderation policy: `domain/sketch_review.py:300-337` (`ModerationRecord.key`, `moderation_key`, `target_moderation_key`); store keyed by it `infrastructure/sketch_review/coordination.py` (`get_moderation(key)`/`put_moderation`); service uses only the current-policy assessment for commit, `moderate`, queue, projection and eligibility `application/services/sketch_review.py:275-282, 729-738`; quarantine intent id includes the policy | `test_sketch_review_review_fixes.py::test_rv_cr01_moderate_uses_current_policy_not_old_passed`, `::test_rv_cr01_direct_approve_after_policy_block`, `::test_rv_cr01_existing_approval_closes_when_policy_blocks` | Probe case `policy_changed_reuses_old_moderation`: before 201 + Child `available` with stored PASSED@v1; after `SketchReviewError INVALID_STATE`, v1 PASSED kept + v2 BLOCKED appended, one quarantine intent |
| RV-CR02 (P2) authority/policy read before token | FIXED | Early checks are preliminary; decisive authority + policy (and the 05 generation) are read after the token in `_prepare` and in `moderate`, then the final hold verifies their epochs: `application/services/sketch_review.py:177-181, 212-224, 366-376` | `::test_rv_cr02_policy_disabled_during_preliminary_read[record_review/moderate]`, `::test_rv_cr02_grant_revoked_during_preliminary_read[record_review/moderate]` | Probe cases `policy_read_before_token` / `grant_read_before_token`: before 201 with stored review; after `POLICY_UNRESOLVED` / `RESOURCE_NOT_FOUND`, no entry and no moderation stored |
| RV-CR03 (P2) warm cache serves quarantined content | FIXED | `FakeChildCache` reauthorizes every hit through 05 eligibility (same review ref + unchanged 05 epoch), else evicts and recomputes: `infrastructure/sketch_review/fakes.py:169-201`; wired in `harness.py` | `::test_rv_cr03_warm_cache_never_serves_after_denial[quarantine/consent/policy/context/device]` | Probe `cache_after_quarantine`: before cache `available` with text+asset, misses 1; after `unavailable`, no text/asset, misses 2 |
| RV-CR04 (P2) approval revives on restored values | FIXED | Monotonic 05 invalidation generation (review-policy + review-context epochs) pinned on each entry at commit (`domain/sketch_review.py:258-261`, read after the token and protected by the final hold); `_applicable` refuses when the generation moved (`application/services/sketch_review.py:719-722`); a fresh decision from an older generation is not a semantic duplicate and replaces the same-key entry (`:290-295`); port/impl `ReviewTokenPort.generation` (`ports/sketch_review.py:142`, `coordination.py:91-100`) | `::test_rv_cr04_policy_restoration_does_not_revive` (incl. fresh approve reopens), `::test_rv_cr04_context_restoration_does_not_revive` | Probe `policy_restoration` / `audience_restoration`: before restore → `available` with the SAME old review; after restore → `pending` (no content), old review not usable; no refresh call needed |
| RV-CR05 (P2) fingerprint on raw input | FIXED | `canonical_review_command` (NFC/trim reason, sorted participants/groups/consent refs; duplicates kept for the binder) used for the receipt fingerprint: `contracts/schemas/sketch_reviews.py:93-113`, `application/services/sketch_review.py:166-168`. Live binding checks after a missed receipt unchanged | `::test_rv_cr05_normalized_reason_replays[typed/json]`, `::test_rv_cr05_reordered_audience_replays[typed/json]` (both also assert a different semantic payload with the same key → 409) | Probe 4 cases: before retry 409 `IDEMPOTENCY_PAYLOAD_MISMATCH`; after retry 201 `replayed=true`, same review id |

Probe evidence: before = Codex's unmodified probes run on the pre-fix snapshot (all three scripts
exit 0 = counterexamples reproduced, `local/fix-20261019/before/`). After = same unmodified
probes on the fixed source (`after/`); the fence probe aborts at its first case after the fix, so
`local/fix-20261019/run_fence_probe_cases.py` imports it and runs each of its 3 cases separately
(`after/fence_cases.json`: all three `counterexample_reproduced: false`). The new regression
tests were written after the fix; they were not executed against the pre-fix bytes (those
untracked bytes were overwritten in place; their hashes are the 19 references above).

## 2. Evidence-strength notes from the review

- **RV-C02** now compares the shared pack and its test literally (`read_bytes() == git show`),
  without EOL normalization (`tests/contract/test_sketch_review_contracts.py`).
- **RV-N15c** now asserts the whole allowlist: only lifecycle fields of the current version change
  (`pipeline_state`, `status_reason`, `moderation_state`, `cleanup_job_ids`), `record_version` and
  `review_revision` +1, all other proposal fields and earlier versions equal, exactly one
  `CONSENT_REVOKED` event for the proposal, and the `eligibility:{org}` epoch bumped
  (`tests/unit/test_sketch_review_chain.py`).

## 3. Checks actually run for this fix (new runs)

Environment: Windows 11, root checkout `backend/.venv` CPython 3.12.10, no installs, no network;
`PYTHONPATH`/`MYPYPATH` = this worktree's `backend/src`; pytest from `backend/` with a separate
`--basetemp` per suite, run sequentially by `local/fix-20261019/run_fix_checks.sh`.

| Check | Exit | Result |
|---|---|---|
| focused05 (7 files incl. new regression file) | 0 | 117 passed, 0 skipped |
| X01 SK1 focused | 0 | 175 passed |
| X02 `tests/contract` minus 7 Pillow-importing modules | 0 | 400 passed, 3 skipped (Pillow); 7 modules NOT_RUN (Pillow absent) |
| X03 BE2-02/BE2-03 unit (14 files) | 0 | 405 passed |
| X04 all `tests/unit` | 1 | 2444 passed, 18 failed, 34 errors, 37 skipped (2533 cases) |
| X04 vs baseline receipt | — | failed/error/skipped case sets identical to the kept baseline receipt; 104 new cases (86 earlier + 18 regressions) all pass; no baseline case missing or changed |
| Ruff from `backend/` cwd (16 files) | 1 → 0 | first run: 1 I001 import order in the chain test (introduced by this fix); fixed; rerun exit 0 |
| chain test after the import-order fix | 0 | 6 passed (only the import order of that file changed after focused05/X04) |
| mypy project config (9 source files) | 0 | no issues |
| mypy `--strict` (9 source files) | 0 | no issues |
| validate_harness / repository_security / architecture / skeleton | 0 | pass |
| `git diff --check` | 0 | clean |
| races + eligibility + regressions repeated 5× | 0 | 48 passed each run |

Kept receipts (not rerun): baseline `local/checks-20261019/x04_unit_all_baseline_58293f1.xml`
(base commit 58293f1 unchanged; baseline failures: missing Pillow/imageio, local-only semantic
catalog, `tools.*` import path). NOT_RUN: Pillow-dependent contract modules, Studio/runtime,
providers, network, SQL, HTTP routes, UI.

## 4. Residuals and interpretation notes

1. The 05 invalidation generation is session/organization-wide: any coordinated review-policy or
   review-context publication makes older approvals unusable (fail closed), even if the change
   did not affect them; a fresh decision is then required.
2. After a moderation-policy change, a target not yet re-moderated shows moderation `pending` and
   the Child payload `pending` without content; access stays closed until a current-policy PASSED
   assessment and a current approval exist.
3. `FakeChildCache` remains a fixture consumer; the guarantee is that it cannot reuse content
   without a current 05 grant. A real BE1 gateway/read model is still an integration gate.
4. Unchanged scope limits: single-process fake coordinator; DI-18 unbumped owner facts caught only
   at the next pull read; database fencing, BE1 authority/ticket, BE2-14 policy, runtime 01/04.
