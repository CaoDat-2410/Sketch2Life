# SK1 Codex follow-up to independent review

## Disposition

Claude's independent review found two P2 defects and multiple acceptance-coverage gaps. Codex
implemented fixes and targeted tests within the already approved SK1 offline scope. This is a
response for independent re-review, not owner acceptance: SK1 remains **NOT_ACCEPTED**, and
BE2-04 remains **IN_PROGRESS / NOT_DONE**.

## Identity and authorization

- Worktree: `D:\GitHub\Sketch2Life\.worktrees\be2-04-sketch-generation`.
- Branch: `feature/be2-04-sketch-generation`.
- HEAD/base: `113cdf956a09336a0abf5561bd939f5e13b31ea0`.
- Approval SHA256 remains `0f356d32b7cab883be6b3079400ada26495555cef160a6fb6a2a3b742a607d25`.
- Approved plan SHA256 remains `461d06849899ea41f2c93432ed8b88c5a64428cf17bce5d2959a6d26ef4fa819`.
- No staging, commit, push, merge, deploy, Studio, SQL/Redis, live provider, decoder, migration,
  route, or dependency installation was performed.

## Findings addressed

- **F-1 — no-op CAS in `schedule()`:** if cleanup already contained the same job ID, the adapter
  returned the unchanged proposal and service still attempted CAS with the old revision. `schedule`
  now CASes/adds an event only when `add_cleanup_job` returns a changed proposal. A race regression
  covers a worker linking the job before cancellation wins and schedule resumes.
- **F-2 — Child existence leak:** non-Teacher READ now returns `RESOURCE_NOT_FOUND` before checking
  whether the proposal exists. N17 checks the same outcome for an existing and a missing proposal ID.
- **F-4 — owner notice left a job active:** `apply_owner_notice` commits stale/invalidation state,
  then attempts job cleanup outside that transaction. A chain regression checks the queued job is
  cancelled.
- **F-5 — A1 retry sweep used the wrong eligibility:** the SK1 chain now supplies a typed
  `SketchChainEligibility` to the A1-facing job service. Sketch retries use `SketchEligibility`;
  Vision continues through A1 `AssistanceEligibility`. A regression checks the stale job cannot be
  requeued by the A1 instance.
- **F-6 — retryable job create had no recovery:** replaying open by assistance ID schedules again
  when the proposal remains REQUESTED with no linked job. A regression verifies one job is linked.
  Recovery is caller-driven; this does not add a durable scheduler.
- **R03 — orphan cleanup on revoked requester:** the test now reads job state after dispatch. The
  orphan is stored in `cleanup_job_ids`; the A1-facing dispatch sweep cancels it with
  `SCHEDULE_REFUSED`, and no second job or provider call occurs. No service-principal limitation
  remains for this fixture path.
- **Owner-notice cancellation reason:** `SketchJobPort.cancel` accepts a reason code and owner
  notice cleanup passes the actual status reason. The consent-revocation regression checks
  `failure_code=CONSENT_REVOKED` on the cancelled job.
- **Source immutability assertions:** P01 and N18 resolve the pinned source through
  `h.sources.resolve(...)` and compare its input hash, render hash and canvas `document_epoch`.

## Acceptance gaps closed in the second follow-up

- **R11:** separate fault-injection regressions fail the proposal/job link commit, staged-generation
  commit, cancel commit and owner-notice commit. Each checks no partial 04 row/receipt/event and that
  replay or retry completes the operation once.
- **P08/P11:** chain test promotes v1, revises to level 2 under a changed policy, and checks v1
  history, v2 level provenance, policy/profile, job input hash, provider request digest and promoted
  content hash.
- **N23:** chain coverage changes consent, Teacher-confirmed meaning, source render, or policy after
  C8. Each changed case withholds content without mutating the proposal, records a revalidation hint,
  then becomes stale on revalidation; the unchanged case continues to show content.
- **C05:** a contract report is assembled from the live fake registry after purge and validated as
  `ProviderCopyLifecycleReportV1`; fixture evidence never claims actual deletion.
- **R03:** post-dispatch state and cleanup-job identity are both asserted, correcting the earlier
  snapshot timing error.

## Coverage added or strengthened

- **P07:** retryable attempt 1 followed by successful attempt 2; only attempt 2 is promoted.
- **R12:** a dropped hint leaves no proposal until the request is opened by ID.
- **N13:** retry policy exhaustion records `PROVIDER_TIMEOUT`; the late-expired-attempt path remains
  covered separately.
- **N12/R30:** chain assertion covers `blocked_unsafe`, moderation `blocked`, Teacher reason,
  unsafe event, Child `unavailable`, and quarantine redelivery through the A1-facing sink.
- **N18:** chain rejects `canvas_operations`; proposal fails with `OUTPUT_MALFORMED`, no staged or
  promoted output is retained, and resolved input/render hashes plus canvas `document_epoch` are
  unchanged.
- **SK-C10:** autouse teardown in chain and race test modules checks the shared port identity,
  artifact audit, and deferred publication failures. An adapter regression verifies a direct raw
  artifact mutation is detected.
- **R06/R31/R32/R33:** the race tests now assert the nested-unit error and deferred cancel ordering;
  outbox claim-before-sink waiting for C8; stale lease and same-event deduplication through outbox
  plus C9; and alternating drainers over Vision and Sketch intents.

## Remaining partial acceptance and review questions

The coverage table in `SK1_IMPLEMENTATION_EVIDENCE_20261018.md` is the current case-by-case summary.
These gaps remain open and must not be treated as accepted:

- **R31/R33:** coordination and redelivery are covered, but these race tests inject synthetic
  quarantine intents rather than using an intent produced by a real completion side effect.
- **Other chain/contract variants:** N04/N08/N11/N15 and P02/P06 are covered indirectly across
  related chain/service/adapter cases, not as separate full chain cases. C06 still validates the
  static example bundle without comparing it to generated producer output; C03/C03b/C09/N19/P09
  still need a line-by-line contract mapping audit.
- **N-2 original review observation:** the real A1 post-commit callback to `SketchStageAdapter` is
  not exercised end to end in this offline component harness.
- **N16:** Child cancel of an existing proposal remains `FORBIDDEN_SCOPE` while a missing ID is not
  found. This is the approved plan's behavior and is recorded as a residual existence signal; no
  contract change is made in SK1.
- **F-5 plan deviation:** the additional `SketchChainEligibility` wrapper is recorded in
  `DECISIONS.md` as requiring owner disposition. The approved plan bytes remain unchanged.
- **Runtime/non-goals:** SK-NI01 durable multi-process behavior, SQL/Redis, Studio, live provider and
  decoder remain NOT_IMPLEMENTED/NOT_RUN under the approved SK1 scope.

## Verification

All follow-up checks used the existing `D:\GitHub\Sketch2Life\backend\.venv\Scripts\python.exe`
(CPython 3.12.10), with `PYTHONPATH` and `MYPYPATH` pinned to this worktree's `backend/src`. No
package was installed.

| Check | Result |
|---|---:|
| Focused SK1 domain/service/adapter/chain/race/contracts | 166 passed, 0 skipped |
| X01 BE2-01 | 337 passed, 1 skipped |
| X02 BE2-02 | 411 passed, 1 skipped |
| X03 BE2-03 | 127 passed, 1 skipped |
| Ruff on 14 new Python files | PASS |
| strict mypy on 14 new Python files | PASS |
| harness/security/architecture/skeleton validators | PASS |

Each X suite has one pre-existing live-app contract skip because Pillow is unavailable. The first
X01 attempt hit a Windows permission error when `tmp_path` used the default profile Temp directory
(17 setup errors, 320 passed, 1 skipped). It was rerun with a fresh ignored `--basetemp` and passed
337 tests with the same one Pillow skip. Both attempts' logs are retained in
`evidence/local/codex-followup-20261018/`; this follow-up's final receipts are in
`evidence/local/codex-followup2-20261018/`.

The local receipts, JUnit XML, validator output, and Claude re-review prompt are under the Git-ignored
`evidence/local/codex-followup2-20261018/`. The LF-normalized metrics JSON SHA256 is
`8d93f9072ba1a1ec50fb5bfc642e6bcc582d9d819b32824cbcc24e18ffaa532d`.
