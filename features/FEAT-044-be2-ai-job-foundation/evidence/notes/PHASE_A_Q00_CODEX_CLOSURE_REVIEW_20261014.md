# Q00 — independent closure review of Claude's R01–R11 fixes

- Date: 2026-10-14, Asia/Saigon.
- Overall review: **NEEDS_REVISION — three focused Phase A follow-ups**.
- Original R01–R11 repros: all resolved; closure of original scenarios is distinguished from remaining regressions/invariants below.
- Scope: approved BE2-01 Phase A revision1, ACTIVE Q00. No new business card or Phase B work.
- Reviewers: Codex primary, q00_lifecycle_closure, q00_copy_closure, q00_contract_http_closure; read-only implementation review.
- Original independent review and Claude before/after receipts remain unchanged.

## Checks reproduced independently

- New Q00 regressions + Phase A tests + targeted legacy regressions: **236 passed, 1 skipped**. This is 204 current Phase A tests plus 32 targeted regressions. Skip remains live app route check requiring Pillow.
- Runner with HTTP: **217 checks, 0 failures**; core results_sha256 matches Claude's 308b4c93b9ae1b9d8ba7e656aef3dc932ff0e72c457a8ad01592038a20b1f791.
- Original repro script rerun unchanged: **11/11 original defect_present=false**; module origin confirmed inside BE2 worktree.
- Scope: existing venv, pinned PYTHONPATH, bytecode/pytest cache disabled. No installs/provider calls/code fixes/commit/push/deploy.

Raw receipts: codex_q00_closure_pytest.txt, codex_q00_closure_runner.txt, codex_q00_closure_runner_report.json, codex_q00_closure_original_repro.json. Metadata: metrics/codex_q00_closure_*.json. New targeted observations: raw/codex_q00_closure_followup_probes.json.

## Original finding closure

| Finding | Original case result | Evidence and remaining qualification |
|---|---|---|
| R01 | CLOSED | Org/job/attempt lineage validation prevents foreign/unowned quarantine; valid own rejected outputs still scoped |
| R02 | CLOSED | Semantic key includes target/purpose/session/subjects; matching/reordered subjects and authorized principals still dedup |
| R03 | CLOSED original receipt-slot defect | Guard failures no longer reserve authoritative completion; valid later claim succeeds, genuine accepted conflict retained. **R03a remains** for artifact state |
| R04 | CLOSED original malformed-string/poll500 defect | Unknown/sensitive codes map to safe PROVIDER_ERROR; polling succeeds. **R04a remains** for unhashable codes |
| R05 | CLOSED original concurrent same-key purge | Per-scope lock + stored receipt; three concurrent callers across five fixture profiles dispatch once and return consistent complete outcomes |
| R06 | CLOSED | Old p1 pending/exception receipt replay does not overwrite newer p2 deletion state/receipt; no extra dispatch |
| R07 | CLOSED | Type guard; independent enum/non-object probes across all shape enum fields return validation errors |
| R08 | CLOSED | Non-success refs/disposition rejected; accepted/stale success projections valid |
| R09 | CLOSED | Current eligibility before dispatch; denied message cancelled/dropped; queue outage/recovery/replay remains correct |
| R10 | CLOSED | Public hint affects ETag; time changes yield 200/new hint, unchanged hint304, revoked caller404. Independent fractional retry wait verifies rounding directly |
| R11 | CLOSED | Shared Child/full terminal/failure/poll invariants; minimal field projection retained |

Independent HTTP/contracts checks included 89 type probes, state/ref/Child matrices and actual HTTP projections for Teacher/Admin/Device. Retry rounding probe used 5501ms: 6000 hint → after1ms304 → after501ms200/5000 → queued2000 after due retry. This verifies a case not actually exercised by the executor's default1000ms timeout test (below min polling2000); it is not an additional blocker.

## Remaining corrections — same Q00 scope

### R03a [P2] A valid later completion exposes an artifact that remains quarantined

Location: backend/src/sketch2life/application/services/ai_jobs.py:579 (guard quarantine), 625–631 (output admission), 699 (owned-ref filtering); fake quarantine storage retains reason.

Fresh repro:

1. Create queued job, produce own valid fixture output, submit success before start.
2. Guard rejects INVALID_STATE and quarantines that output.
3. Start attempt, resubmit identical valid claim. Receipt accepted, job succeeded, Teacher polling returns that artifact in result_refs.
4. FakeArtifacts.quarantined still holds the same artifact with INVALID_STATE.

INPUT_MISMATCH followed by the corrected same output has the same result, with INPUT_MISMATCH quarantine retained. Original R03 is fixed; this inconsistent availability/exposure is directly enabled by the fix allowing later completion. Candidate spec records temporary INVALID_STATE as leaving state unchanged, not an irreversible output quarantine.

Fix expectation: temporary guard rejection should not quarantine valid bytes merely because lifecycle order is wrong; accepted output must have coherent availability after correction. For mismatched input, explicitly choose safe corrected-result revalidation/release or a clean admitted result according to the source contract; no blind unquarantine of unsafe/revoked/foreign output. Add assertions that accepted projected refs are not still quarantined, preserving R01 scoping and unsafe/revocation quarantine tests. Actual storage-delivery failure is not claimed here; the verified contradiction is in fake artifact state and public status refs.

### R04a [P2] Unhashable failure code escapes new boundary normalization

Location: backend/src/sketch2life/application/services/ai_jobs.py:720–724, specifically allowlist lookup at721.

Fresh claim replace(failure_claim, failure_code=[]) or {} causes TypeError: unhashable type list/dict. Job stays running; no safe typed fallback/non-authoritative rejection is returned. This does not recreate original poisoned-job poll500; it is residual malformed-input handling in the new normalizer.

Fix expectation: type-check before set membership, then safe PROVIDER_ERROR mapping or non-authoritative MALFORMED_CLAIM. Diagnostic stays redacted. Test list/dict + appropriate other nonstring values and later valid completion, without changing accepted receipt replay/conflict semantics.

### A18a [P2] Cancellation can overwrite completed purge — pre-existing uncovered gap

Location: backend/src/sketch2life/application/services/provider_copy_lifecycle.py:56–62; purge atomic scope at77–94; registry save is unconditional.

**This gap predates Q00; it is not reported as a newly introduced regression.** It directly violates the existing A-18 no-resurrection/final-receipt invariant, so remains a focused Phase A correction.

Deterministic event-controlled repro: cancel reads a DISCOVERED copy and pauses inside request_cancel adapter; purge runs under its scope lock and stores fixture DELETED with receipt; cancel resumes and saves its stale CANCEL_REQUESTED copy. Current registry becomes cancel_requested with receipt None. Old purge key replay returns historical deleted outcome (correct R06 behavior) while discover still shows cancel_requested.

Observed tuple: purge=deleted, current=cancel_requested, current_receipt=null, replay=deleted. No failed thread or timeout.

Fix expectation: coordinate cancellation read/dispatch/save through the **existing** atomic scope boundary or equivalent current-state CAS. No new database/framework/service; a completed copy and receipt must not be overwritten by stale cancellation. Add this interleaving and preserve existing concurrent purge/replay/lifecycle tests. Broader privacy/provider features remain outside Q00.

## What this review accepts and what remains pending

The original fixes are acknowledged with reproducible evidence; no reimplementation of R01–R11 is requested. Next Claude turn targets only **R03a, R04a, A18a** and their directly affected regressions/handoff. Q00 stays ACTIVE; whole BE2-01 IN_PROGRESS.

P1/P2/P4 schema/port/policy adoption remains pending, including producer lineage and new receipt/lock contracts. Missing Pillow live-route check remains NOT_RUN. This review does not grant Phase B/runtime/model/deletion/integration readiness or any new approval. Original record remains preserved; updated closure evidence belongs to this document.

## Reproducibility and review limits

Primary fresh probe source recorded in raw/codex_q00_closure_followup_probe_source.txt, piped to existing backend venv python -B - with PYTHONPATH=<be2-worktree>/backend/src, PYTHONDONTWRITEBYTECODE=1 and cwd BE2 worktree. All calls use deterministic synthetic fakes, no network/storage-provider access. Code hashes and command receipts are recorded in metrics/CODEX_Q00_CLOSURE_REVIEW_20261014.json. Current gate/approval state is unchanged; documentation updates only.
