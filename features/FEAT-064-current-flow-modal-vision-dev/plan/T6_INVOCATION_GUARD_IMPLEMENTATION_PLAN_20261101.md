# T6 — Invocation guard and observation provenance

- Status: **BLOCKED before implementation**.
- Group: G3. Owner authorized the G2–G6 no-commit run through the goal prompt and its §E. This task plan records the exact implementation gate; it does not widen the goal scope.
- Parent: `plan/PLAN.md`, T6; source freeze: `evidence/T0_CONTRACT_FREEZE_20261031.md` §6; T0 manifest O08–O12/O14/O15.
- Database: none for T6. Provider/network calls: prohibited in this run.

## Inventory and blocker

The existing service validates request/job lineage, source, admission, context and eligibility before calling `VisionObservationPort.observe`. The current C1/C2 adapters reject the real `UrllibJsonTransport`; the offline adapters count their injected transport calls and never retry. No `InvocationGuardPort` exists in source.

T0 §6 says the enforceable total HTTP wall deadline and completion margin are `NEEDS_OWNER`, and explicitly says the timeout/late-response policy must be frozen before T6/T13. The known 12-second client limit and 120-second `urlopen` timeout do not establish a full-call deadline. Implementing a “known not sent” or “complete response” classification without that decision could incorrectly release a call cap. T0 also has no frozen invocation identity/guard handshake connecting `ObservationClaim` to the exact transport send boundary. This plan therefore does not invent a deadline, late-response rule, or guard protocol.

## Owner questions

1. What total HTTP wall deadline and completion margin should the pilot enforce, including cold-start allowance?
2. What is the allowed handling of a complete response arriving after the request/job deadline: discard as `UNKNOWN/HOLD`, or another explicit disposition?
3. Which immutable invocation identity and guard handshake must reach the transport boundary so durable T7c can record possible-send before bytes leave?

## Layers and acceptance

| Layer | Planned scope | Status |
|---|---|---|
| L1 contracts/domain | Typed guard decision and outcome classification; C1/C2 preserved | BLOCKED: questions 1–3 |
| L2 application | Require guard before observation, with no guard/refusal/error causing zero sends | BLOCKED: no frozen guard/claim contract |
| L3 persistence/migration | None in T6 | NOT RUN |
| L4 adapters | Record possible-send/provenance exactly at transport boundary; no real transport | BLOCKED: depends on the frozen invocation handshake |
| L5 HTTP | No route change in T6 | NOT RUN |
| L6 UI | DEFERRED-BY-OWNER | DEFERRED |
| L7 integration | Transport-count tests after L1–L4 | NOT RUN |

## Allowlist and exclusions

Candidate source boundaries only: `backend/src/sketch2life/domain/vision_analysis.py`; `backend/src/sketch2life/application/ports/vision_analysis.py`; `backend/src/sketch2life/application/services/vision_analysis.py`; manifest O11/O12 adapter files; selected O14 retry/recovery files; and O15 test fakes. Potential tests: `backend/tests/unit/test_invocation_guard_policy.py` and `backend/tests/contract/test_invocation_guard_port.py`. For this blocked disposition, the actual write allowlist is only this plan, the G3 blocker report, the append-only FEAT-064 approval entry, and the goal ledger.

No code or test was run for T6 because the explicit contract gate is unresolved. No provider, Modal, or network call is authorized.
