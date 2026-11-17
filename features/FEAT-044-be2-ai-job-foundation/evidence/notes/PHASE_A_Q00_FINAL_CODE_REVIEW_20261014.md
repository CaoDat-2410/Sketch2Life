# Q00 final code review — corrections closed

- Date: 2026-10-14, Asia/Saigon.
- Code review result: **PASS at Phase A fake/contract scope**.
- Original R01–R11: CLOSED_ORIGINAL_CASE; follow-ups R03a/R04a/A18a: CLOSED.
- Reviewers: Codex primary with independent q00a_claim_closure and q00a_copy_closure agents.
- Scope: latest three corrections and their directly affected regressions, not a new full-system audit or runtime/provider acceptance.
- Owning feature: FEAT-044; approved scope remains Phase A revision1. Original review, interim closure review and executor receipts retained.

## Independently reproduced checks

| Check | Actual result | Receipt |
|---|---|---|
| Current Phase A/follow-up tests plus planned targeted regressions | **255 passed, 1 skipped** (223 + 32); skip needs Pillow | raw/codex_q00a_final_pytest.txt |
| Standalone runner with HTTP | **222 checks, 0 failures**, digest matches executor | raw/codex_q00a_final_runner.txt and runner_report.json |
| Unchanged original R01–R11 repro script | **11/11 defects absent**, module origin correct | raw/codex_q00a_final_original_repro.json |
| Three follow-up repro script | **3/3 defects absent**, module origin correct | raw/codex_q00a_final_followup_repro.json |
| Independent claim review | 29 focused tests passed + malformed/canonical/admission probes | Reviewer q00a_claim_closure, read-only |
| Independent copy review | 7 focused tests passed + event-controlled interleavings | Reviewer q00a_copy_closure, read-only |
| Final documentation/repository gates | Harness, repository security and git diff --check PASS | raw/codex_q00a_final_{harness,security,diff}.txt |

Existing root backend/.venv was reused; PYTHONPATH pinned to BE2 worktree/backend/src and bytecode/pytest cache writes disabled. No dependency installs, provider calls or code edits by reviewers. Full backend suite not claimed. Exact commands/timestamps/environment in metrics/codex_q00a_final_*.json; frozen source hashes and review result in metrics/CODEX_Q00_FINAL_CODE_REVIEW_20261014.json.

Runner results_sha256: d17f58a3c9c535d45a2fe03ed0c1edad42a565422725aede21b22ba45af41f68. It reports 20 core criteria plus supplemental A-17-http (21 rows); core A-17 NOT_RUN marker remains while supplemental HTTP checks pass. This reporting limitation is preserved explicitly and is not an extra acceptance criterion.

## Closure evidence

### R03a — CLOSED

Service ai_jobs.py:584 skips artifact mutation for temporary INVALID_STATE/INPUT_MISMATCH. A later valid completion accepts the same owned output, and polling refs no longer remain quarantined. ArtifactDescriptor.quarantine_reason is checked at admission (service:636); pre-quarantined output rejects OUTPUT_MALFORMED rather than being silently released.

Regressions preserve unsafe/revoked/cancelled/malformed quarantine, organization/job/attempt lineage, foreign/unowned isolation, immutable accepted replay and genuine completion conflict. Scope/hash mismatch and already-quarantined output remain blocked. No real artifact delivery or storage-provider deletion is claimed.

### R04a — CLOSED

Service normalizer checks type before failure-code allowlist membership (ai_jobs.py:737). Nonstring list/dict/number/bool/bytes/set gives non-authoritative MALFORMED_CLAIM; job stays running and valid later completion succeeds. Secret-bearing malformed values stay out of public projection/audit except their digest. Invalid identity gives safe typed MALFORMED_REQUEST. Unknown strings keep the existing PROVIDER_ERROR mapping.

Canonical fallback no longer throws for tested malformed bytes/set/nested values; ordinary NFC/sorted JSON hashes remain stable. Reviewer tested repeated hashes in-process. This review does **not** assert arbitrary Python object repr or malformed-set representation is stable across processes; malformed inputs are not authoritative accepted outcomes.

### A18a — CLOSED

register_copy (:42), cancel_scope (:62) and purge_scope (:82) in provider_copy_lifecycle.py now use the existing per-scope lock through their read/dispatch/save sequences. Event-controlled tests demonstrate purge waits for in-flight cancel, then preserves final copy state/receipt. The inverse order also preserves purge state: cancel/register wait; original copy stays deleted with receipt; late new copy becomes purge_requested. Registering an old ID does not resurrect it.

Independent reviewer repeated original R05 with three concurrent callers across five fixture profiles: one dispatch, identical complete outcomes, matching receipt. R06 historical p1 pending/exception→p2 deletion replay preserves newer current state and receipt. This remains fake concurrency evidence and fixture deletion, not durable DB isolation or actual provider deletion.

## Gate state after code closure

| Gate | Current status | Remaining action |
|---|---|---|
| Original review corrections + three follow-ups | **CLOSED / code review PASS** | No further correction requested in this reviewed scope |
| P1/P2/P4 cross-review/schema/port/policy adoption | **PENDING** | Explicit version/owner/compatibility adoption incl. producer lineage/quarantine_reason/receipt/scope-lock semantics |
| Live app route negative test | **NOT_RUN / REQUIRES_LIGHTNINGAI_TEST** | Run in an existing compatible environment with Pillow, or record an explicit checkpoint acceptance deviation |
| Phase A overall acceptance | **PENDING external gates above** | Do not infer full acceptance from code review alone |
| Phase B/runtime | **NOT_STARTED / not approved** | Separate plan + ADR persistence/queue/transaction/recovery + BE1 ports + approval |
| Whole BE2-01 | **IN_PROGRESS** | Durable scope remains separate and outstanding |

Pending command:

```text
python -m pytest backend/tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route
```

ACTIVE Q00 remains for acceptance/adoption/environment disposition; there is no remaining code-fix item from this review. Next default roadmap slot is Q01 after its gates, and preparation of a reviewable Phase B plan must not activate runtime code. No new business card, implementation approval, model/stack adoption, Git publication or deployment is created by this review.
