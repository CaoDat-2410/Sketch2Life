# Feature decisions

## D07 — C3b atomic commands and current replay — 2026-10-17

Implement approved lifecycle application orchestration over existing storage and
candidate outer owner guard. Shared DATA-24 source remains unchanged; its review
record is preserved in the atomic receipt with DATA-33 response metadata. Stable
server IDs derive from organization/principal/request; request fingerprint also
binds full command and If-Match. Non-create receipt lookup is repeated after
parent UPDATE; unique create conflicts recover the winner only after rollback,
not by retrying arbitrary writes. Replays check current authority and effective
content/review context, never authorize new usage from a cached success.

Moderation is required for approval/publication, not a prerequisite for entering
review or writing a negative review. Negative remediation and recall/archive do
not require unsafe source content to pass publication eligibility. Current
capability, exact target and CAS still apply. This follows P1–P3, not a new
moderation/provider choice. SQL application tests use explicit ASSUMED owner
ports; they prove content transactions/races, not real cross-owner fencing.

## D06 — C3a current eligibility before command orchestration — 2026-10-17

Split C3 into cohesive application checkpoints, not function-level commits.
C3a provides guarded eligible published-content resolution and SQL enumeration;
C3b still owns mutation orchestration and receipts. Both remain within approved
revision 1. Source assessments bind organization/id/version/hash/policy; current
source/review decisions cannot be supplied by callers or permissive defaults.
Keep the outer owner guard through storage commit. Real adapter/fencing is a
candidate integration gate, not proven by in-process component fixtures.

Default resolution can skip an audience-ineligible published version but fails
closed on policy/source/review/dependency denial. Never mask such denial by
silently falling back. Explicit version/hash never substitutes another version.
This conservative implementation of P2/P3 does not invent owner policy.
Portable PostgreSQL setup/test/cleanup authorization is reused for a consolidated
C2 + C3a SQL regression run; no GPU/service install/push/merge is inferred.

## D05 — actual implementation approval — 2026-10-17

Owner explicitly approved plan revision 1 including P1–P4 and instructed
continuation. Preserve reviewed plan hash; earlier D02 is historical, no longer
the active gate. Execute BE2-12 independently on its branch; other owners'
approvals/foundation closure are not changed. P1–P4 adopted only for this card.

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
