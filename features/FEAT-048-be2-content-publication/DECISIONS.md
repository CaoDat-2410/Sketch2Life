# Feature decisions

## D01 — mapping and baseline — 2026-10-17

BE2-12 maps to unused FEAT-048, not FEAT-012. Work on a dedicated branch from the
published foundation checkpoint 6dcc57e; do not assume dev contains this source.
Do not modify BE2-01, its approval, runner, migrations or shared contracts.

## D02 — pending implementation gate

Owner goal explicitly retains plan approval. No applicable BE2-12 approval was
found; status AWAITING_APPROVAL and runtime NOT_STARTED. Draft policies and
technical choices in revision 1 are PROPOSED until the owner adopts them.
Autonomous commits preserve reviewed documentation; they do not bypass approval.

## D03 — contract ownership

Use ExactContentReview candidate owned by BE2-05; report an amendment request if
the current record is insufficient, rather than rewriting owner code. BE2-12
owns DATA-33/CMD-48 dispatcher; preset/AI/core-policy only through typed delegate
ports to BE2-13/14/BE1. Unbound delegates fail explicitly, never mutate local
content as a substitute. No second governance command dispatcher.

## D04 — accurate readiness

Local unit/contract, durable runtime and cross-owner integration are separate.
No cloud/GPU/model/provider or service execution in planning. No completed-task,
production or runtime claim follows from plan/security/harness checks.
