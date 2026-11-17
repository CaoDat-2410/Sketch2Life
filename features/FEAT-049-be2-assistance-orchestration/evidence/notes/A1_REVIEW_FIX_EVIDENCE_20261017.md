# BE2-03 A1 code-review fixes A1-CR01–CR05 — 2026-10-17

State: **A1_FIXES_COMPLETE_PENDING_CODEX_REREVIEW**. The fixes stay inside the existing A1
approval (plan revision 3, SHA256 e1fce645…, unchanged); no new scope. The review record
`A1_CODEX_REVIEW_20261017.md` (NEEDS_REVISION, 0 P1 / 5 P2) and the original implementation
note/metrics are unchanged history. No component acceptance, Git action, install or Studio run.

Identity: worktree `.worktrees/be2-03-assistance-orchestration`, branch
`feature/be2-03-assistance-orchestration`, HEAD f120c4f, staged 0. Before editing, all 31
reviewed source/prerequisite hashes in `../metrics/A1_CODEX_REVIEW_20261017.json` matched.

## Regressions first (before fixes)

New file `backend/tests/unit/test_assistance_review_fixes.py` (16 tests) was written and run
against the reviewed source before any product edit. The only addition at that point was the
harness test helper `publish_owner_change` (fact change + owner-epoch bump through the existing
`request_publication`; no behavior fix). Result: **12 failed, 4 passed** — each failure on the
reviewed bug (cache hit after disclosure withdrawal; owner publication committing inside
another thread's start unit; deferred publication not serialized; analysis_ready + Sketch intent
after a pre-commit consent/age move; submit not re-deciding; intent/role change superseding
instead of debouncing; trimmed/NFD text rejected). The 4 passes were the unchanged guards
(same-scope cache hit; blank/control/oversize text refused). Raw log/JUnit: ignored
`../local/a1-review-fix-20261017/before.log`, `before-junit.xml`.

## Fixes (paths under `backend/src/sketch2life/`)

| Finding | Fix | Regressions |
|---|---|---|
| A1-CR01 cache bypasses disclosure withdrawal | `application/services/assistance.py` `_cache_candidate`: the requesting principal must currently `disclose` the original request before its provenance is used; the decision is kept current to commit by the CR03 decision epoch (a withdrawal publication between gate and commit re-decides) | `test_cr01_new_key_cache_hit_requires_current_disclosure`, `..._disclosure_withdrawn_between_cache_gate_and_commit`, `..._same_scope_cache_still_hits`; existing P08 |
| A1-CR02 owner publications bypass the coordinator | `infrastructure/assistance/fakes.py`: `request_publication` runs an immediate publication under the coordinator lock; `_run_deferred` runs each deferred publication under it too. Same-thread deferral, lock order (coordinator → store), release in `finally`, failure recording unchanged | `test_cr02_cross_thread_owner_publication_waits_for_foundation_commit` (other thread at post-hold/pre-commit), `..._deferred_publication_is_serialized_with_other_threads`; existing R15a/R15b/R16 |
| A1-CR03 handoff gate stale before commit | Decision-epoch protocol in the approved fake composition: new `AssistanceUnitOfWork.decision_epoch` (port + fake; the shared `eligibility:<org>` epoch bumped by every coordinated owner publication and terminal request transition). Submit (incl. cache), reconcile/handoff and cancel read the epoch before their owner/source/analysis/authority reads and commit only if it is unchanged, else re-decide (bounded rounds). The handoff gate now checks the owner-fact digest before the analysis read so revoked consent ends `stale`, not `failed`. Foundation services are never called inside an assistance unit | `test_cr03_consent_revoked_between_handoff_gate_and_commit`, `..._same_revision_fact_move_between_gate_and_commit`, `..._submit_redecides_when_consent_moves_before_commit` |
| A1-CR04 semantic change supersedes valid requests | `_commit_submit`: an active request on the same operation target is superseded only when its `assistance_context_digest` differs from the newly resolved one; a different intent/requester over the same facts stays active and the new request is debounced/budgeted | `test_cr04_changed_intent_same_facts_is_debounced_not_superseding`, `..._teacher_then_child_same_window_is_debounced`, `..._after_window_both_requests_stay_active`; existing N23–N25 unchanged and passing |
| A1-CR05 valid LongText rejected | `submit`: the command is rewritten once with the normalized (NFC, trimmed) intent before fingerprint, semantic identity and storage; blank/control/oversize/Teacher intent still 422 | `test_cr05_trimmed_and_nfc_intent_is_normalized_and_stored`, `..._canonical_equivalent_replay_and_dedup`, `test_cr05_invalid_intent_still_refused` ×3; API `test_cr05_api_normalizes_child_intent_and_replays_equivalent_text` |

The CR05 API test was added after the service fix; its pre-fix behavior is evidenced by the
service-level CR05 before-failures and the review's text-normalization probe. Two CR01 tests were
adjusted after the fix to state the correct expectation precisely (inside the window the
uncached request is debounced; after it the request is created without `cache_hit_of`); their
before-failures were on the cache hit itself.

## After results

Same runner as the implementation (ignored `../local/a1-review-fix-20261017/run_checks.py`;
existing venv; process-local base Pillow and existing multipart; external network blocked,
loopback allowed; import origin asserted to this worktree):

| Group | Files | Tests | Passed | Failed | Errors | Skipped |
|---|---|---|---|---|---|---|
| A1 (incl. 17 new CR tests) | 7 | 118 | 118 | 0 | 0 | 0 |
| BE2-01 regression | 11 | 338 | 338 | 0 | 0 | 0 |
| BE2-02 regression | 12 | 412 | 412 | 0 | 0 | 0 |

Codex probes re-run on copies (ignored `../local/a1-review-fix-20261017/after-probes/`; the
review's own probe outputs untouched): the cross-thread owner publication no longer commits
before the start commit; the age and consent handoff races end `stale` with 0 Sketch intents;
changed intent and Teacher→Child in the window raise `RATE_LIMITED`; the HTTP cache probe's
assertion of the old 202 cache hit now fails. These probes assert old behavior; their non-zero
exit is the expected "no longer reproduced" outcome, not a product PASS by itself.

Static and repository checks: ruff PASS (17 paths); `mypy --strict` PASS on 10 source files;
`mypy --strict --follow-imports=silent` PASS on 17 source+test files; harness, security,
architecture, skeleton VALID; `git diff --check` clean; 48 new files have no trailing
space/CR; no existing tracked source/test modified.

## Changed files and hashes (SHA256)

| File | SHA256 |
|---|---|
| `backend/src/sketch2life/application/services/assistance.py` | 0221686b482667dd… (full in metrics) |
| `backend/src/sketch2life/application/ports/assistance.py` | a1f1d83093b702fc… |
| `backend/src/sketch2life/infrastructure/assistance/fakes.py` | 4d499f35115623fc… |
| `backend/src/sketch2life/infrastructure/assistance/harness.py` | 0d082c5dffa7aa2c… |
| `backend/tests/unit/test_assistance_review_fixes.py` (new) | df2f7d39b058b20b… |
| `backend/tests/contract/test_assistance_requests_api.py` | 7dd80544c9fd6f14… |

All other reviewed A1 files, the handoff examples and `plan/PLAN_REV3_APPROVED.md` are unchanged.

## Remaining limits

The decision epoch is the fake composition's coarse org-wide epoch; it proves the protocol over
in-memory fakes, not production SQL owner fencing or real OwnerFence. Retries are bounded; under
heavy unrelated churn a reconcile may return without handing off and is retried later. All
other A1 limits in `A1_IMPLEMENTATION_EVIDENCE_20261017.md` remain. BE2-01 WAITING_STUDIO,
BE2-02 PARKED, BE2-03 IN_PROGRESS / NOT_DONE. Next: Codex re-review.
