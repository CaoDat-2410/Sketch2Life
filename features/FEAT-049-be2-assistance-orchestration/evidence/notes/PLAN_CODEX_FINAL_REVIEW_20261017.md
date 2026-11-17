# BE2-03 A1 plan revision 3 final review — 2026-10-17

Disposition: **PLAN_REVIEW_PASS — 0 blocking findings** in the proposed
ASSISTANCE_COMPONENT_OFFLINE scope. All original findings and A1-PR01-F1 are
closed at plan level. Implementation is NOT_STARTED and approval remains
AWAITING_APPROVAL; a plan review is not owner selection or runtime evidence.

## Reviewed identity and evidence

- Branch `feature/be2-03-assistance-orchestration`; HEAD
  `f120c4fce8f7853e5ab5e061eff4bf916d45603c`, staged 0.
- `plan/PLAN.md` revision 3, SHA256
  `e1fce645a5d8c98efe366865f5a8a1b9c81c8a48626723c4e73f0c646979d3e5`, 55475 bytes.
- Root Codex source/plan/diff review plus two delegated same-family targeted
  reviews (foundation composition and authority). Not a different-model review,
  BE1/P1/P4 sign-off, policy adoption or user approval.
- Prior reviews and metrics remain historical, unchanged. Ignored draft copies of
  revisions 1 and 2 match their reviewed hashes. Approved C1/C2 bytes are unchanged.
- Actual validation results and source hashes:
  `../metrics/PLAN_CODEX_FINAL_REVIEW_20261017.json`.

Python paths below are relative to `backend/src/sketch2life/`; plan/evidence paths
are relative to this feature.

## Finding closure

**A1-PR01-F1 CLOSED_AT_PLAN_LEVEL.** Plan lines 244–259 require one shared
coordinator spanning the underlying foundation repository context manager through
its exit, including commit/rollback. Lines 260–268 atomically publish assistance
state/epoch and read matching decision/epoch snapshots. Lines 270–284 specify lock
ordering, deferred same-thread publication, exception-safe release and no lock
across provider execution.

This addresses the actual fake's former gap: `FakeOwnerFences.hold` only compares
at an instant, while `InMemoryAiJobStore.transaction` publishes later. The new
repository decorator is feasible through the existing `AiJobRepository.transaction`
port (`application/ports/ai_jobs.py` lines 468–469), without foundation source edits.
R15a/R15b now test both valid commit orders at the post-hold/pre-commit seam; R16
requires rollback and coordinator-release behavior. Those are required future
implementation tests, not tests claimed to have run in this planning review.

The original findings remain closed at plan level:

| Finding | Resolution retained in revision 3 |
|---|---|
| A1-PR01 | Frozen scheduling identity, late-job cleanup, trusted lookup, request-aware eligibility, settlement and shared fake commit coordination. |
| A1-PR02 | Full resolved source/audience/purpose/policy/context equivalence and same-revision movement cases. |
| A1-PR03 | Any-started-attempt evidence, monotonic consumption, unknown evidence retaining an unconsumed hold, no release before settlement. |
| A1-PR04 | Handoff commit is the linearization point; cancel-before and handoff-before have different explicit outcomes. |
| A1-PR05 | Lost create reply versus broker dispatch outage are separate recovery boundaries. |

Cache uses current authorized reads and original provenance, not worker replay
on a completed job. CMD-33 has its own command identity, fingerprint and accepted
receipt replay coverage. The injected Teacher reader is explicit and scoped, with
requesting-device authorization/disclosure checked independently (lines 357–363).
The D2 lineage revision is explicitly not a representation cache validator.

## Non-blocking notes and limits

- Plan line 558 still says routine candidates TC-01 through TC-10 although
  DECISIONS also has TC-11. The coordinator is fully specified in the plan, file
  inventory and acceptance; this bookkeeping omission does not change scope or
  require another plan revision. Keep the reviewed plan hash stable for approval.
- Shared coordinator behavior, exceptions, same-thread deferral, dedup/budget CAS
  and full service-chain compatibility still need implementation tests. No new
  component implementation/prototype was written in this review.
- Real SQL/Redis/provider/owner-fence/API integration and policy adoption remain
  outside A1. Offline completion cannot mark BE2-01/02/03 fully DONE. BE2-01 remains
  WAITING_STUDIO, B-12 HANDOFF; OwnerFence ASSUMED_CONTRACT.
- D1–D11 remain owner recommendations. In particular D3 includes Child cancellation
  of a Teacher-initiated individual request targeting that Child's bound participant;
  D5 restricts Teacher requests to a valid contributor; D6 uses semantic-stage
  budget units; D11 rejects a new cancel after the handoff commit. Review does not
  select these policies on the owner's behalf.

## Verification and next action

Root reran the existing harness, repository security, architecture, skeleton and
diff checks: all passed. New feature markdown whitespace checks and the historical
draft/protected-source hashes passed. Product pytest/ruff/mypy were not rerun:
there is no application source/test change or A1 implementation to test.

No application code/test, dependency installation, service/provider/Studio run,
Git staging/commit/push/merge or approval edit occurred in this review.

Next: the user may approve this exact revision/hash and explicitly select D1–D11.
Only after that real approval should Claude freeze the approved bytes, record the
actual instruction, set the work order and implement A1.1–A1.5. Stop after
implementation checks/evidence for Codex code review; publication is separate.
