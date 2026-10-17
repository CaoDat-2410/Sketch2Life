# BE2-03 A1: final Codex code review — 2026-10-17

Disposition: **CODE_REVIEW_PASS — 0 P1 / 0 P2; no new actionable finding**
in the approved ASSISTANCE_COMPONENT_OFFLINE (A1) scope. State:
**A1_CODE_REVIEW_PASS_PENDING_OWNER_ACCEPTANCE**. All original A1-CR01–CR05
and residual CR03-F1/F2 close at this reviewed component scope. Owner acceptance,
Git publication and full-card closure are separate decisions; none is recorded here.

## Reviewed identity and authority

- Branch `feature/be2-03-assistance-orchestration`, worktree
  `.worktrees/be2-03-assistance-orchestration`, HEAD
  `f120c4fce8f7853e5ab5e061eff4bf916d45603c`, staged 0.
- Approval `approvals/TASK_APPROVAL.md` SHA256
  `f6a266c9a01c6a6c2432765ff50a866618bb05221aed933e4113e2bff8a23501`:
  A1.1–A1.5, revision-3 acceptance, D1–D11 as recommended; offline scope only.
- Frozen plan `plan/PLAN_REV3_APPROVED.md` SHA256
  `e1fce645a5d8c98efe366865f5a8a1b9c81c8a48626723c4e73f0c646979d3e5` unchanged.
- All 21 source/test/golden/approved-record hashes reported in
  `../metrics/A1_CR03_FOLLOWUP_CHECKS_20261017.json` match. Six protected prerequisite
  records and seven prerequisite source anchors also match. Previous implementation,
  review, re-review and fix evidence remains historical and unchanged.

## Closure evidence

| Finding | Final disposition and verified behavior |
|---|---|
| A1-CR01 | CLOSED: cache requires current disclosure of the original request. Owner/disclosure changes committed before acceptance force a fresh decision; same-scope cache remains valid. |
| A1-CR02 | CLOSED: immediate/deferred owner callbacks serialize under the shared coordinator; cross-thread publication cannot commit inside a held unit. |
| A1-CR03 / F1 | CLOSED: publication requested inside foundation, Vision or assistance units is deferred until the outermost unit exits. It drains on commit or rollback, each callback independently serialized. The callback observes the actual committed state, not staged handoff/cache state. |
| A1-CR03 / F2 | CLOSED: Vision service and outcome reads use the new A1 `CoordinatedAnalysisRepository`. Committed writes advance a separate analysis epoch before releasing the coordinator; submit/cache, handoff and cancel compare the combined owner/request and analysis token. |
| A1-CR04 | CLOSED: same-fact semantic changes obey debounce/budget and preserve the previous valid request; changed-fact supersession remains covered. |
| A1-CR05 | CLOSED: trim/NFC normalization drives fingerprint, semantic identity and stored intent. Canonical-equivalent replay, meaningful-change conflict and malformed-input refusal remain covered, including HTTP regression. |

The new Vision decorator forwards all 16 current `AnalysisUnitOfWork` methods and
marks every mutator as a write. Read-only units move no token. Actual Teacher
correction moves analysis revision and its epoch; accepted correction replay moves
neither. Actual invalidation moves the analysis epoch; repeated notice does not.
Injected failed Vision commit leaves state/token unchanged. The owner eligibility
epoch used by BE2-01 does not change merely because Vision committed.

Root independently reran positive assertion probes with these results:

- Coherent consent withdrawal committed before the handoff decision: `stale`, zero intents.
- Withdrawal requested inside the assistance unit: immediate=false; callback observes
  committed `analysis_ready` and one committed intent. This is valid handoff-first order.
- Teacher correction between analysis read and handoff commit: the decision sees revisions
  1 then 2; both handoff and Sketch intent reference revision 2.
- Device grant withdrawn between cancel authorization and commit: `GRANT_REVOKED`, request
  remains scheduled, zero cancellation events.
- Analysis token sequence for read/correction/replay/rollback/invalidation:
  `(1,1)` → unchanged on reads → `(1,2)` after correction → unchanged on replay and
  rollback → `(1,3)` after invalidation. Duplicate invalidation moves nothing.

Rollback regressions verify no staged assistance state, receipt, intent or request
epoch leaks; a queued independent publication sees old committed state and advances
only its own epoch. Deferred failures are recorded, and subsequent operations can
acquire the coordinator. A delegated 24-case coordinator matrix also passes nested
unit, exception, cross-thread blocking and deferred-failure checks.

## Independent verification

Root ran **878 passed, 0 failures, 0 errors, 0 skipped** across 31 test files:

| Suite | Files | Tests passed |
|---|---|---|
| A1, including all review/follow-up regressions | 8 | 128 |
| BE2-01 offline regression | 11 | 338 |
| BE2-02 offline regression | 12 | 412 |

Root ruff passed on 18 source/test paths; strict mypy passed on 10 source files.
Harness/security/architecture/skeleton and diff checks passed; final receipts are
in the matching metrics. The reported follow-up baseline JUnit was independently
checked: 10 tests, 8 failures, 2 passes before the fixes. Two previously passing
guards are not misrepresented as before-failures.

Three delegated same-family targeted reviews supplement the root review. Their
62/26/13-test subsets overlap the 878 total and are not added to it. The 24-case
coordinator matrix and positive protocol probes are separate assertions, not new
pytest totals or cross-role sign-off.

The existing venv was used with worktree import origin asserted. Existing Pillow
and multipart were loaded process-locally; no installation or shared-environment
edit occurred. Parent pytest external sockets were blocked; local Python child
tests were permitted. No provider, database, queue service or Studio was run.

## Evidence and remaining boundaries

Full source hashes and machine-readable results:
`../metrics/A1_CODEX_FINAL_REVIEW_20261017.json`.
Raw receipts are ignored in `../local/codex-a1-final-review-20261017/`:

- `root-1792253950180160800/{junit.xml,result.json}`, `root_pytest.log`;
- `root-probes/analysis_protocol_probe.py`, `analysis_epoch_protocol_result.json`;
- `root-probes/semantics_probe.py`, `probe_result.json`;
- delegated `coordinator/`, `contracts/`, `semantics/` receipts;
- static checks, validator logs and protected-record checks.

This verifies synthetic in-memory composition: one coordinator lock, coarse
organization epochs and bounded re-decision. It does not establish SQL isolation,
real OwnerFence, durable delivery, actual BE1 owner adapters, adopted policy values,
live routes/auth, real provider quality or deployment. Policy remains FIXTURE_ONLY;
Sketch is SIMULATED_NO_PRODUCER; C2 mapping, downstream review/release and live
integration remain outside A1. Earlier implementation handoff limits still apply.

BE2-03 remains IN_PROGRESS / NOT_DONE. BE2-01 WAITING_STUDIO and BE2-02 PARKED are
unchanged. Next: the owner may accept this A1 component and request a publication
inventory/commit plan. This review creates no owner acceptance, commit/push/merge
authorization or new-card implementation authorization.
