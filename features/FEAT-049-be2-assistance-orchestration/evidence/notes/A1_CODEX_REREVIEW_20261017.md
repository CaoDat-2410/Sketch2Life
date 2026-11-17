# BE2-03 A1 fixes: Codex re-review — 2026-10-17

Disposition: **NEEDS_REVISION — 0 P1 / 2 P2**, both residual parts of A1-CR03.
The original five findings are not counted again. The implementation's new tests
pass, but the current-decision guarantee still has the two independent gaps below.
This is an offline component review, not acceptance or a full-card closure.

## Identity and verification

- Branch `feature/be2-03-assistance-orchestration`, worktree
  `.worktrees/be2-03-assistance-orchestration`, HEAD
  `f120c4fce8f7853e5ab5e061eff4bf916d45603c`, staged 0.
- Actual A1 approval and frozen revision-3 plan remain unchanged. Plan SHA256:
  `e1fce645a5d8c98efe366865f5a8a1b9c81c8a48626723c4e73f0c646979d3e5`.
- All 19 hashes in `A1_REVIEW_FIX_CHECKS_20261017.json` match source, tests,
  golden fixture and approved plan. Six protected prerequisite records and seven
  prerequisite source anchors also match the previous review.
- Root independently ran **868 passed, 0 failures/errors/skips** across 30 files:
  A1 118, BE2-01 338, BE2-02 412. This includes the 17 new fix tests.
- Root ruff passed on 17 source/test paths; strict mypy passed on 10 source files.
  Repository validators and final invariants are recorded in the matching metrics.
- Existing venv, process-local existing Pillow/multipart, verified worktree import
  origin; no dependency installation, services, provider or Studio. External
  sockets blocked in the parent pytest process; local child Python tests allowed.
- Three delegated same-family targeted reviews supplement the root review. Their
  overlapping test subsets are not added to 868 and are not cross-role sign-off.
- Root reproduced the new violation probes on separate local copies. Exit 0 on
  these witness scripts means the undesired behavior was observed, not a product PASS.

## Disposition of the original findings

| Finding | Re-review result |
|---|---|
| A1-CR01 | Direct disclosure check is fixed: withdrawn access prevents ordinary cache reuse; successful same-scope cache remains. Its full decision lifetime still depends on the CR03 gaps below. |
| A1-CR02 | CLOSED at reviewed scope: immediate and deferred cross-thread owner publications hold the coordinator; original start ordering, failure and lock-release tests pass. |
| A1-CR03 | OPEN: the previous pre-transaction consent/age race now yields stale with no handoff. The two independent residual cases below remain. |
| A1-CR04 | CLOSED: same-fact intent/requester changes obey debounce and do not stale the previous valid request. A changed intent after the window can create a separate request. Fact-change supersession tests still pass. |
| A1-CR05 | CLOSED: trim/NFC normalization precedes fingerprint/semantic identity/storage. Equivalent text replays; meaningful changes conflict; malformed/blank/oversize inputs and Teacher intent remain refused. API regression passes. |

## A1-CR03-F1 — P2: reentrant owner publication inside assistance commit

Primary location: `backend/src/sketch2life/infrastructure/assistance/fakes.py`
lines 123–134, especially 127–133. Related callers: `application/services/assistance.py`
epoch comparisons at 477 and 874–879; event callback at 1039.

`request_publication()` defers only while foundation depth is positive. During an
assistance UoW, its `RLock` can be reacquired by the same thread. A public owner
publication requested by an injected event-clock callback therefore runs immediately
after the epoch comparison but before the staged assistance state is published.
There is no later check or deferral preventing that ordering.

Two reproduced manifestations share this root cause:

1. **Consent/handoff:** callback uses `publish_owner_change` and the coherent
   `revoke_consent` helper. It observes committed request `scheduled` and zero
   committed intents, publishes consent=false and advances the epoch, and returns
   immediately. The outer unit then publishes `analysis_ready` and one Sketch intent.
   Thus revocation actually commits before handoff; this is not merely a later
   revocation of an already committed handoff.
2. **Disclosure/cache:** the corresponding callback withdraws original-resource
   disclosure. Epoch advances 1→2 and disclosure is already false, yet the outer
   transaction commits `cache_hit` and returns original assistance/job/analysis refs.

The approved plan explicitly spells out *foundation* callback deferral. This
finding concerns the new assistance decision protocol's incomplete protection;
it does not misquote that original rule as an explicit assistance-depth requirement.

Fix direction: prevent owner publication inside either coordinated atomic unit.
For example, defer while foundation or assistance depth is positive and drain only
after the outermost unit exits, on commit or rollback. Keep independent callbacks
serialized, failure recording and lock release. Do not merely add another epoch
comparison before an event callback or replace the reentrant lock and deadlock reads.

Regression expectations must distinguish actual commit order: a publication
requested inside a committing assistance unit may run afterward, observe the
committed handoff, and leave `analysis_ready` plus one intent legitimately. Test
deferred/immediate result and observed committed state. A publication committed
before the decision must still block stale handoff. Also test rollback with queued
publication: no staged request/receipt/intent/request epoch escapes; the independent
callback sees old committed state; subsequent operations acquire the lock normally.

## A1-CR03-F2 — P2: Vision invalidation is absent from the decision epoch

Primary locations: `backend/src/sketch2life/application/services/assistance.py`
lines 477 and 604–640 (cache decision and consumption); the composition in
`infrastructure/assistance/harness.py` gives Vision an independent
`InMemoryAnalysisStore`. `VisionAnalysisOutcomes.current` in `adapters.py`
lines 221–248 reads through the existing Vision APIs without a commit-bound token.

A second probe lets the current-analysis read finish, then invokes the existing
public `VisionAnalysisService.apply_invalidation` with an `INTENT_CHANGED` notice
before cache acceptance. The real Vision service commits the analysis stale and
its invalidation intent. Assistance's epoch stays **1→1**. The new submission still
commits **cache_hit**, while a fresh `downstream_meaning` is **not_applicable**.
No raw fake-state mutation or private Vision write is used.

This is separate from F1: it occurs before the assistance transaction and persists
even if reentrant publications are deferred correctly. A token covering only
coordinated owner/request changes cannot validate an independent analysis read.

Fix direction: make relevant Vision commits participate in the A1 composition's
decision/commit protocol, or expose and validate an equivalent analysis version
through a protected boundary. Implement this through new A1 adapters/composition
and existing ports; preserve foundation/Vision source and approved records. A
second unprotected read or teaching only the test to wrap the mutation is not
sufficient. Cover cache and handoff using actual Vision invalidation/correction
service commits, including commit-after-decision and rollback behavior. Do not
claim PostgreSQL/production fencing from this fake protocol.

## Evidence and next step

Publishable metrics: `../metrics/A1_CODEX_REREVIEW_20261017.json`.
Raw scripts, JUnit and receipts are intentionally ignored under
`../local/codex-a1-rereview-20261017/`:

- `root-1792246309396908000/{junit.xml,result.json}` and `root_pytest.log`;
- `root-probes/semantics_probe.py` and `probe_result.json`;
- `root-probes/cache_probe.py` and `cache_in_unit_publication_result.json`;
- `root-probes/vision_invalidation_probe.py` and `cache_analysis_invalidation_result.json`;
- delegated `contracts/`, `coordinator/`, `semantics/` receipts; root static/validator logs.

Original implementation, review and fix evidence remain unchanged. Next is a
bounded fix of F1/F2 with failing-before/passing-after regressions and another
Codex review, under the existing A1 approval. BE2-03 stays IN_PROGRESS / NOT_DONE;
BE2-02 PARKED; BE2-01 WAITING_STUDIO. No component acceptance, installation,
provider/Studio run or stage/commit/push/merge/deploy was performed by this review.
