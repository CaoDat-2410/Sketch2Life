# BE2-01 B3 independent review —2026-10-15

> Historical finding report. B3-R01 is now CLOSED_B3_SCOPE after the corrected20-file snapshot's
> reported71B2+B3/224PhaseAPASS and independent review. Current authority:
> PHASE_B_B3_CLOSURE_REVIEW_20261015.md. Original finding/probe remain preserved below.

- Result: **NEEDS_REVISION**, one P2 finding **B3-R01 OPEN**. B3 is not closed; B4 NOT_STARTED.
- Scope: existing approved Phase B revision 3, B3 repository/UoW, Δ1–Δ5, test-only
  ASSUMED_CONTRACT owner fence and relevant tests. No new card, approval or plan revision.
- Reviewers: Codex primary; independent SQL/fixture, service/ports/fakes and test audits.
- Workspace: `.worktrees/be2-01-ai-job-foundation`, branch `feature/be2-01-ai-job-foundation`,
  base `993a26cae78c0a4fe983033f03881838c886b176` plus existing dirty B2/B3 source.

## Reported Studio result

User supplied a successful result after the instructions for the latest B3 ZIP:

- B2+B3: **69 passed, 58 warnings, 62.06 seconds**, `b3_exit=0`, `b3_log_exit=0`, `b3_skips=0`.
  Matching local source collects 22 offline + 47 PostgreSQL cases: 14 B3 offline, 8 B2 offline,
  37 B3 PostgreSQL (21 repository, 6 multiprocess create-race, 10 owner-fence), 10 B2 PostgreSQL.
- Phase A: `phase_a_exit=0`, `phase_a_log_exit=0`, `phase_a_skip_gate=PASS`/`phase_a_skips=0`.
  The Phase A pytest count and duration were **NOT_REPORTED** in this pasted tail; do not invent
  a new count from the earlier B2 run's 224 passed.
- Fixture runner: 20 PASS/0 FAIL, 215 checks/0 failed, `not_run=1` for its optional HTTP surface.
  Digest `d17f58a3c9c535d45a2fe03ed0c1edad42a565422725aede21b22ba45af41f68` matches the baseline.
  This default fixture run does not newly prove HTTP/live-router integration.
- All fixture/log/outer/operator exits explicitly 0; `RUNNER_RESULT=PASS`.
- Provenance: **USER_REPORTED_REMOTE**. Codex did not execute PostgreSQL or access Studio.
  The pasted tail omits the source-provenance header, run timestamp and receipt directory.
  Attribution is to the instructed latest package, not an independently inspected remote receipt.
  Local verification confirms all 19 current source hashes and ZIP/manifest/runner bytes match:
  patch `a2e479d5ee8fc59c67568f5089cf981672b76315d7b0796c3bddc1d0d956e312`,
  manifest `ea5cf57e12058f48cbd6ef73b23ca9a8b60b78c374f655ba629623b6b308939f`,
  ZIP `4a7e5dd9a30ccdc1abc6d00cf95f82295f9aec0ed15f148ed9527e8ca06e050f`.

These results are retained as successful execution of the current tests. They do not cover the
read interleaving below. Missing pasted metadata alone creates no new owner question or gate.

## B3-R01 —P2: get_job can combine different committed aggregate versions

Location: `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py:248` (`get_job`,
especially lines 248–260). It reads the job row and attempt rows in separate, unlocked SELECTs
at READ COMMITTED when `for_update=False`, the default used by status/read paths.

Concrete schedule:
1. Reader's job SELECT observes `queued`, `job_revision=1`.
2. A concurrent `start_attempt` transaction commits `running`, revision 2 and the attempt's
   `started_at` together, correctly and atomically.
3. Reader's attempt SELECT observes that new `started_at`.
4. Repository returns a never-committed aggregate: `queued`, revision 1, with a started attempt.

The offline probe executes the actual repository row mapping, `project_job` and
`AsyncJobViewV1.model_validate` against simulated statement results for that permitted schedule.
It reproduces **`queued attempt cannot have started_at`**. Candidate polling serializes the
view at `interfaces/http/routers/ai_jobs.py:78` without handling this validation failure, so
the inferred HTTP effect is a 500 when that race occurs. Neither HTTP nor PostgreSQL was run
by this probe. A second independent probe confirms a retry interleaving can similarly combine
old `failed_retryable` revision 3 with the new attempt 2 from queued revision 4.

Fix direction: return the aggregate from a consistent SQL statement snapshot, or use a suitable
parent-row lock/version-stability retry that prevents mixed versions while preserving the
accepted READ COMMITTED/CAS and `for_update=True` semantics. Do not weaken the wire validator,
hide the exception or widen the isolation policy/approved plan to mask it.

Required regression: deterministic overlapping reader and writer on disposable PostgreSQL,
using a barrier/hook around the read boundary. Start/retry must never produce a mixed aggregate;
the projected result must validate against the existing candidate contract. The test must work
with the chosen synchronization strategy without requiring a blocked writer to commit first.
Keep timeouts/cleanup bounded and retain existing CAS/owner-fence behavior.

Probe: ignored `evidence/local/b3-codex-review-20261015/probe_torn_read.py` and its result JSON.
This is a new SQL adapter defect, not a pre-existing Phase A finding or a new business card.

## Other review results and next action

- Ports/service/fakes: no additional introduced actionable finding. Semantic NFC hashing,
  bounded whole-candidate rollback/fresh reread and fence-before-mutation behavior reviewed.
- SQL write path/fixture: no additional finding; write reads use `for_update=True`, owner holds
  use the UoW connection and contract/version/stale checks. B4/B5 hooks remain explicitly deferred.
- Existing tests cover meaningful create races, CAS, rollback and owner-fence orders; no current
  test exercises B3-R01's unlocked aggregate read boundary. Passing tests do not close this gap.
- Codex local combined Phase A/B2/B3 regression command exited 0. PostgreSQL cases remain skipped
  on Windows and the Pillow-dependent local HTTP test remains skipped; this is local evidence,
  separate from the user-reported successful Studio run. A peer also ran 14 B3 offline tests: PASS.
- No backend/test/runner implementation was changed by this review. Preserve original approvals,
  B2 schema/history and unrelated files. B2 remains CLOSED_REVIEW_PASS; 14 cards/WIP1/full-cardDONE0.

Claude's bounded next work order is `evidence/local/claude/prompts/CLAUDE_PHASE_B_B3_FIX_PROMPT.md`: fix B3-R01, add its
regression, rebuild a source-bound package that safely upgrades the known old B3 Studio snapshot,
then obtain new runtime evidence for the changed source and independent review before B4.
No repeated approval, provider, dependency install, service/volume recreation or commit/push/deploy.
