# Feature decisions

## D13 — typed consumer metadata, not fake delivery — 2026-10-17

Complete the planned receiver-owned consumer pack now: current query projection,
published exact ref/review set, lifecycle notice matching existing owned outbox,
candidate sink/ack obligations and executable conformance. No source/body/media
or caller scope assertion in refs/queries; metadata is not a grant/reservation.
Each new usage rechecks eligibility; BE1 session-start commit needs its adopted
cross-transaction fence. Notices do not authorize use or delete/replace pinned
history. Memory duplicate/conflict sink is fixture-only; no ack/delivered_at is
fabricated in SQL evidence. Actual consumer delivery/dedup/authentication belongs
to bound real adapters, not this pure projection or another owner's table writes.

## D12 — do available receiver-owned contract work now — 2026-10-17

Direct user clarification: this receiver handles 08–14, teammate handles 01–07
then consumes this branch. Correct prior interpretation that 13/14 must arrive
from another person before all dispatch work. Approved plan already covers
candidate typed delegate seams: implement fixed routing, strict concrete-model
binding, explicit unavailable behavior and conformance now. Do not invent final
stage/policy payload semantics or implement other business cards without their
plans/approval. Routing selection is not semantic payload validation; only a
bound extra-forbid strict frozen model may reach an owner handler. Real authority
and consumer readiness remain distinct from fixture/component readiness.

## D11 — enforce approved P3 new-version reintroduction — 2026-10-17

The reviewed plan already explicitly permits reintroduction by a new version
with fresh review. No additional owner decision is needed to correct code that
rejected all editing from a retired head. Terminal applies to the old version,
not a permanent ban on new versions under that record. Keep current head/CAS/
source/policy/author checks; clear all new-version review/publication/recall
metadata. Never transition old version back to active or reuse its approvals.
Correct earlier restrictive tests rather than treating them as product policy.
Exact old refs and original publish receipts remain ineffective even after v2
legitimately publishes. No new restore action, route, migration or shared schema.

## D10 — immutable original vs derived review-history status — 2026-10-17

Resolve local F03 with a BE2-12 read-only projection, not a new review authority
or mutation of shared DATA-24/original proofs. Current scoped READ and outer guard
remain mandatory through transaction. History can remain readable after unsafe
source/recall because it contains review metadata, not permission/media for usage.
Bound pages to 100 as technical admission and require unchanged global record
revision for continuation. Do not mix snapshot-derived statuses across pages.
Use explicit stale reason priority documented in REVIEW_HISTORY_CANDIDATE.md;
an older published version stays effective unless a separate current condition
invalidates it. Boolean owner effectiveness cannot identify external revocation
cause, so label owner_ineffective and keep real cause/adoption as F02. No schema
migration, shared-contract rewrite, default route mount or consumer shortcut.

## D09 — audit preserves unfinished requirements — 2026-10-17

C5a is a self-review/handoff checkpoint, not permission to mark BE2-12 complete.
Audit every approved AC01–14 and preserve missing proof as unachieved. F03
stale-history projection is local actionable work: immutable proof retention
and current-context filtering do not alone expose derived stale state/reason.
Implement an owned read projection without rewriting original review evidence
or shared owner schemas. Full dispatcher/real owner integration remain F01/F02/
F04/F05 gates; do not redefine the task to avoid them or manufacture sign-off.
No blocked status while meaningful scoped F03 implementation remains available.

## D08 — C4a transport without inventing owner payloads — 2026-10-17

Provide the planned content HTTP integration seam and all-eight-action consumer
examples using injected verified server scope; do not mount candidate code in the
default application before owner adoption. Use existing shared error envelope,
bounded streaming admission supplied by composition, strong quoted record
If-Match and no raw validation/adapter error echo. Keep BE1 CMD-59/60 as delivery
gateway rather than adding a competing content GET route.

Inspected schema/application source contains only DATA-33 lightweight ShapeSpec
for preset/policy. SRS names fields but does not supply complete stage/notification
rule or allowlisted AI/core-policy payloads. Do not invent them, pass untyped
dicts or substitute arbitrary reference payloads. C4 remains incomplete with
explicit CR-C4-01 owner schemas/typed port and real authority adoption request.
Non-content bodies currently fail 422 in the candidate content seam, NOT final
delegate-unavailable behavior. Do not claim full action/branch union acceptance.

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
