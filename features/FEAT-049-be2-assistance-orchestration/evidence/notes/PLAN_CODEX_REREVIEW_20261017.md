# BE2-03 A1 plan revision 2 re-review — 2026-10-17

Disposition: **NEEDS_REVISION — 0 P1 / 1 P2**. The original five issues are
substantially addressed; the remaining item is the fake commit-order contract
under A1-PR01. No BE2-03 application implementation exists or is approved.

## Reviewed identity

- Branch `feature/be2-03-assistance-orchestration`, HEAD
  `f120c4fce8f7853e5ab5e061eff4bf916d45603c`, staged 0.
- `plan/PLAN.md` revision 2: SHA256
  `0894c39b286ca7d52335bc8e55a39e13aa7f1e0d53d8dc0623c631df9ab95d2e`, 48409 bytes.
- The original draft/review and C1/C2 approved artifacts are preserved. D1–D11
  remain recommendations; TASK_APPROVAL remains AWAITING_APPROVAL.
- Root Codex review plus three delegated same-family source audits, not a
  different-model review or BE1/P1/P4 sign-off. BE2-01 remains WAITING_STUDIO and
  BE2-02 remains IN_PROGRESS / NOT_DONE.

Python paths below are relative to `backend/src/sketch2life/`; feature paths are
relative to FEAT-049. Plan line numbers refer to the unchanged revision 2.

## Closure map

| Item | Re-review |
|---|---|
| A1-PR01 late-create cancellation | Retained identity, late-id cleanup, trusted lookup and settlement are addressed at lines 217–265. The remaining fence/commit atomicity item below must be specified before this finding fully closes. The original missing-cleanup P1 is addressed; the remaining specification issue is P2. |
| A1-PR02 semantic pin equivalence | CLOSED_AT_PLAN_LEVEL: lines 275–298 include resolved source hash, exact audience, purpose, policy and owner-fact digest; N23–N25 cover same-revision movement. |
| A1-PR03 retry budget refund | CLOSED_AT_PLAN_LEVEL: lines 340–355 use any started attempt, monotonic consumption, unknown evidence holds and settlement-gated release; R06/R12/R13 cover the relevant orderings. |
| A1-PR04 cancel/completion contradiction | CLOSED_AT_PLAN_LEVEL: lines 154–180 and 300–320 specify handoff commit ordering; R03a/R03b distinguish observation acceptance from handoff already committed. |
| A1-PR05 queue boundary | CLOSED_AT_PLAN_LEVEL: lines 267–271 and R08a/R08b separate creation reply loss from broker publication failure. |
| Cache clarification | CLOSED_AT_PLAN_LEVEL: lines 366–376 use supported current reads and retain original provenance; no terminal worker replay. |
| CMD-33 clarification | CLOSED_AT_PLAN_LEVEL: lines 128–129 and 205–213 define its scope/fingerprint and accepted replay; N16/N20–N22 cover negative/replay cases. |

These are plan closures, not implementation test results or owner acceptance.

## A1-PR01-F1 — P2: share the fake commit boundary, not only the epoch

**Location:** `plan/PLAN.md` lines 232–244, supported by the fake concurrency
description at 324–328 and acceptance R09/R10.

The plan concludes that the common organization epoch prevents any start from
committing after cancellation. Existing `FakeOwnerFences.hold()` only compares the
epoch at that instant (`infrastructure/ai_jobs/fakes.py` lines 94–98, forwarded by
the unit of work at 230–231). `InMemoryAiJobStore.transaction()` publishes its
staged state later, at line 479, under its own repository lock (471–479).

With separate module critical sections the following ordering remains possible:

1. Foundation passes the epoch hold using the live request decision.
2. Assistance cancellation publishes its state and increments the shared epoch.
3. The foundation transaction publishes RUNNING without another epoch check.

The request-aware decision is useful but does not itself exclude this gap. Root
ran a controlled witness against the unchanged foundation: an injected callback
published synthetic cancellation state/epoch immediately after a successful hold;
`start_attempt` still returned `started=True` and the stored job was RUNNING. This
is a prerequisite fake-contract witness, not an executed BE2-03 cancellation test
and not evidence of real SQL/runtime behavior. No provider was invoked.

**Required planning correction:** explicitly serialize each entire foundation fake
write transaction through its underlying commit with assistance state-plus-epoch
publication. A new composition/repository decorator sharing a coordinator can do
this without editing foundation source. Alternatively, explicitly define those
units as indivisible in the controlled fake interleaving model, including how
attempted cancellation at the post-hold/pre-commit seam is deferred until commit.
Simply sharing an epoch counter or placing an additional mutex only around the
request update is insufficient.

Require a regression at that exact seam, in addition to R09/R10: a cancellation
that commits first makes the start refuse/re-decide; a start that commits first
may run and consumes budget. Do not implement a fixture that publishes cancellation
in the middle of a unit labelled atomic while claiming the opposite commit order.
This is the fake protocol's required linearization, not a demand for the excluded
production SQL owner-fence work.

## Non-blocking implementation notes

- The Vision current-read methods require an explicitly authorized scoped Teacher
  principal (`application/services/vision_analysis.py` lines 878–892). Define the
  injected reader authority in the adapter/fixture and independently recheck the
  requesting device's scope; do not manufacture authority from request fields or
  pass a Child principal directly to a Teacher-only read method.
- D2's lineage revision is not a full representation cache validator. If a later
  increment adds conditional GET for a changing status body, use an appropriate
  representation version; this A1 plan does not add that query.
- Preserve the more specific monotonic budget rule: an already consumed unit stays
  consumed while settlement remains open; unknown/open retains a hold only when
  that reservation has not already been consumed.

## Verification and next action

Existing harness, repository security, architecture, skeleton and diff checks
passed. The controlled foundation witness reproduced the epoch-only gap. Source
hashes, raw-witness hash and actual validator exits are recorded in
`../metrics/PLAN_CODEX_REREVIEW_20261017.json`; raw output remains under ignored
`evidence/local/codex-plan-rereview-20261017/`.

Revision 2 bytes and approval are unchanged by review. No application source/test
edit, install, service/provider/Studio execution, staging or Git publication.

Next: a small planning revision 3 adding the shared fake commit boundary and its
regression, then re-review. Keep implementation NOT_STARTED and approval
AWAITING_APPROVAL. Do not reopen the resolved requirements or rewrite historical
review evidence.
