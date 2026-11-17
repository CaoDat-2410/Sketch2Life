# BE2-01 B4 independent review — 2026-10-15

- Result: **NEEDS_REVISION**, one P2 finding **B4-R01 OPEN** (retry sweep starvation).
- **B4-RT01 CLOSED_FOR_REPORTED_SNAPSHOT**: the empty-RQ-queue correction passed its exact-source
  Studio run. This does not close the separate B4-R01 identified in the full review.
- ACTIVE **Q01/B4_NEEDS_REVISION**; B2/B3 remain closed, B5 NOT_STARTED. Existing plan revision3
  B1–B6 approval applies; exactly14cards/WIP1/full-cardDONE0, parent BE2-01 IN_PROGRESS.
- Codex primary plus independent SQL and tests/security reviewers inspected the current B4
  service/domain, SQL lease/ack/recovery, RQ adapter, fixture parity and relevant tests. This
  review changed documentation/evidence only. Backend, approvals, approved plans and packages
  are preserved. Claude remains the backend executor.

## Attributable corrected-source runtime

The user supplied the full log: **USER_REPORTED_REMOTE**, not direct Codex cloud execution.
Local source/package hashes match the reported32-file manifest.

| Item | Result |
|---|---|
| Run UTC | 2026-10-15T12:32:39Z (19:32:39 Asia/Saigon) |
| Receipt | evidence/local/b4rt01-runtime-20261015/run-20261015T123237Z-23051/ |
| Base | 993a26cae78c0a4fe983033f03881838c886b176 |
| Transition | previous_b4_snapshot; all32correctedsourcefiles verified before suites |
| Previous manifest | 70b2a1600682aec3cfe2dabd80608d45c107f88d24ed25dd18d0e804aff8ef4d |
| Delta | 44f3a80db776430b9d693388f2196fb79a2a20ec89c5e28867edc12c2810ec58 |
| Corrected manifest | 444cfeadd3d7d0d0e1f23663b576270f46692e870fe532071f6cf025ffd9ff01 |
| Runner, local binding | 54a1d99e6c9ad887d12689fbf7152740fd039c1f4108245f15ccd4f42a10fbf3 |
| B2–B4 | **97passed/0failed/0skipped**,73warnings,64.38s; suite/log exit0 |
| Source-matched split | 35offline +62PG/Redis; runtime =10B2 +39B3 +13B4 |
| Phase A | **224passed/0skipped**,4.30s; suite/log exit0 |
| Default fixture | 20PASS/0FAIL,215checks/0failed, optional HTTP NOT_RUN1; exit/log0 |
| Fixture digest | d17f58a3c9c535d45a2fe03ed0c1edad42a565422725aede21b22ba45af41f68 |
| Final statuses | outer_runner_exit=0, RUNNER_RESULT=PASS, studio_command_exit=0 |

Python3.12.15, SQLAlchemy2.1.4, psycopg3.3.6, Alembic1.20.0, pytest8.4.2,
redis-py6.4.0/RQ2.12.0, Redis8.10.2. Alembic heads remain be1_core/ai_jobs.
The73warnings are the known Alembic path_separator deprecation, not test failures. The original
95case/88PASS/7FAIL run remains historical failure evidence for its old source. Build-time
package.json NOT_RUN is an immutable earlier checkpoint, superseded by this attributed result.

## B4-R01 — P2 — deferred first page starves independent due retries

Locations: application/services/ai_jobs.py:746–769 and retry_job:784–804;
infrastructure/ai_jobs/sql/repository.py:692–704. Paths are relative to backend/src/sketch2life/.

`_sweep` repeatedly queries the first limited page and returns when no handler yields an output.
`due_retries` orders by retry_not_before/job_id with LIMIT. `retry_job` returns False after its
bounded stale-owner-decision retries, leaving the due row unchanged. A missing owner decision
is a supported case: FixtureEligibility returns a denied decision without a fence, and `_hold`
correctly refuses to authorize a write. Such rows can remain unresolved across sweep invocations.

Reproduction on the actual current service/fake repository:51duejobs, claim_limit50, the oldest50
receive that missing-decision shape, job51has a valid decision. Three `run_due_retries()` calls
all return empty; the healthy job receives **zero eligibility calls** and stays failed_retryable.
Calling `retry_job` directly for that same job succeeds, producing queued/attempt2. Thus a problem
in older scopes blocks unrelated healthy work indefinitely; the current single-page happy-path
test does not cover it. The new B4 LIMIT paging introduces this behavior compared with Phase A's
all-due traversal. Codex primary reran the independent probe and confirmed the result.

Proof is **DIRECT_LOCAL_FAKE_SERVICE_PROBE**, not a PostgreSQL reproduction. Script and JSON:
evidence/local/b4-codex-review-20261015/service/probe_retry_page_starvation.{py,json}.
The real SQL query has the matching deterministic LIMIT ordering; new SQL-adapter regression
evidence is required for the correction, without claiming it has already been run.

Bounded correction: traverse past deferred rows within the invocation using targeted pagination
or another bounded traversal that actually reaches later pages. Preserve owner fences, retry
budget/CAS and rollback, leave unavailable scopes deferred, retain repeatability. Do not just
remove the no-progress guard and spin, increase the limit, truncate blocked work, weaken the
fence or persist a seen-marker. No general scheduler or new business card is needed.

Regression must exceed claim_limit, place unresolved scopes first, and prove later healthy work
is processed while deferred rows are unchanged. Include more than one healthy page, all-deferred
termination and existing start/recovery/retry races. If the generic sweep changes, check its
other two callers. Preserve Phase A fixture semantics and current B2/B3/B4 regressions.

## Other reviewed boundaries

No additional actionable B4 correctness issue was found. SQL acknowledgement rechecks pending
owner/generation on UPDATE before any attempt bookkeeping; takeover makes the entire bundle a
no-op. Recovery rechecks active attempt/state/revision/timeout/pending intent under the job lock.
Existing tests genuinely exercise Redis/RQ enqueue, broker outage, lease takeover, enqueue/mark
process death, same-attempt loss/bounds, start-vs-loss and competing reconciler serialization.

RQ worker execution is still B5. Its default failure logger can put job.args in structured
LogRecord.arguments; B5 must redact/drop those token-bearing fields and test worker error paths.
B4 proves dispatcher/queue log safety only. Capability binding, incident/quarantine intents,
atomic notices remain B5; full conformance/crash matrix B6; real owner-fence/provider integration
B-12 deferred. No additional task or approval is introduced by these existing obligations.

Traceability note, not a second runtime finding: historical ADR proposal/G3-D3 says broker job id
equals message_id; the adopted ADR and plan Δ14 require description=message_id and SQL attempt
dedup. Current RQ IDs are generated separately. Do not silently edit immutable decisions or
change broker identity as part of B4-R01; state this implementation detail in the eventual handoff.

## Next step

Claude fixes **B4-R01 only**, under the existing approval, using the ignored local prompt
evidence/local/claude/prompts/CLAUDE_PHASE_B_B4_FIX_PROMPT.md. Studio currently has exact
manifest444cfead. A future correction package must start from that snapshot or verify its own
corrected state; old RT01 ZIP is not a package for the new fix. Obtain source-bound runtime
evidence and focused closure review before B5. Do not repeat the unchanged97case run now.

Raw user log, protected514-path snapshot and review probes stay in ignored feature-local
evidence/local/b4-codex-review-20261015/. Public structured result is the matching review metric.
Documentation checks: harness/security/git diff --check exit0. All514protectedpaths and the Git
index are unchanged;32currentmanifesthashes match, packages preserved, operator prompts and
handover remain Git-ignored. Independent B4 unit check13passed; no full suite was repeated.
No backend edits, installs, service recreation, provider calls, staging, commit, push or deploy.
