# BE2-12 acceptance audit — NOT COMPLETE

## Current-source follow-up —2026-10-18 at16712de

Fresh original-goal audit:477 selected component PASS/source unchanged,51 AI-policy
HTTP binding checks PASS. F01 now has typed policy model/service and bind_ai_policy
through sole CMD-48 (supplied separately by14); historical no-AI-policy-delegate
statement superseded, not a reason to implement twice. Preset/core-policy/actual
owner adoption open. F02/F04 actual integration owner-deferred; F05 not achieved.
No new local defect or fresh SQL PASS. See C5B_CURRENT_GOAL_AUDIT_20261018.md.

## C4d follow-up — owned producer delivery implemented

F04's local producer send/ack gap is addressed: exact organization/event delivery,
PostgreSQL NOWAIT lock, matching strict ACK, mark only through successful commit,
failure pending and lost-ACK replay. 23 new unit cases; 477 component / 33 SQL PASS.
Actual delivery tests now set delivered_at only after accepted/duplicate ACK.
Older "all rows remain NULL/no delivery" statements apply to their earlier pure
projection test/checkpoint, not this new implementation. No production receiver
is bound; durable synthetic receiver is NOT BE1/P4 conformance. Fixed logical
destination/transport timeout, real authority, final delegate semantics and full
integrated closure remain unachieved. See OUTBOX_DELIVERY.md and C4D evidence.

## C4c follow-up — local consumer pack and actual producer path

Typed consumer query/reference/notice/sink-ack contracts, current resolution
projection and pure owned outbox adapter now have 25 new component cases and
actual HTTP/SQL/outbox conformance. 438 selected local / 24 owned SQL PASS.
The local F04/AC13 pack omission is addressed; this is NOT real delivery/durable
consumer dedup/session-start fencing or owner adoption. Delivered_at remains NULL
in SQL proof. Full integrated acceptance remains unachieved. See consumer handoff
and C4C_CONSUMERS evidence; prior source audit statements remain historical.

## C4b follow-up — fixed dispatcher component available

Following receiver ownership clarification, implemented fixed four-branch
routing, strict concrete owner-model binding and single HTTP factory with typed
unavailable slots. 59 new component cases / 413 selected local PASS. Local F01
dispatch/spy/unavailable omission is addressed; the routing selector is not the
final complete preset/policy semantic schema union, and actual owner model/
authority/consumer adoption remains pending. Original C4a absence statements
below are historical. See GOVERNANCE_BINDING_HANDOFF.md and C4B_DISPATCH evidence.

## P3 follow-up — reintroduction corrected

The reviewed plan already authorizes a new version after a retired head, with
fresh review; the earlier implementation was too restrictive. This local F05
subfinding is corrected (not a new policy approval): old version remains terminal,
new version starts draft and cannot borrow approvals. 354 selected local / 23
owned SQL tests PASS. See REINTRODUCTION_RULE.md and P3_REINTRODUCTION evidence.
F05 integrated closure, F01/F02/F04 remain OPEN; whole-card NOT COMPLETE.

## F03 follow-up — 2026-10-17, after audited source

F03 local projection omission is now CLOSED_COMPONENT_AND_OWNED_SQL. Added
ContentReviewHistory, parent-fenced all-context SQL history and pagination with
record-revision snapshot checks; original proof JSON unchanged. 24 new component
cases / 350 selected local PASS; expanded 21 SQL cases PASS. See
evidence/notes/F03_REVIEW_HISTORY_20261017.md. AC04's local history gap is addressed;
real owner conformance/revocation causes (F02), other findings and whole-card
acceptance remain OPEN. The original source audit below is historical, not a
claim that the gap is still absent at newer source.

Audit source: 89426fd, feature/be2-12-content-publication, 2026-10-17.
Type: executor self-review of current source/evidence, not independent owner sign-off.
Original plan revision 1/P1–P4 and full goal retained; no reduced success criterion.

## Decision

Whole-card acceptance is NOT achieved. Content component/owned PostgreSQL runtime
proof is useful but insufficient for full DATA-33 dispatcher and real owner
integration. No production route is mounted. A green local suite does not close
the missing contracts, adapters, consumer delivery or history projection gaps.

## Authoritative evidence inspected

- Canonical SRS v3.1 FR056/FR062, UC-035, DATA-24/33/35, CMD-48.
- FEAT-040 TEAM_TASK_BREAKDOWN BE2-12 and FEAT-044 BE2_08_14_TEAMMATE_HANDOFF.
- FEAT-048 plan/PLAN.md AC01–14, actual approvals/TASK_APPROVAL.md, status.
- Domain, command/schema, eligibility, SQL tables/repository/migration and HTTP
  source under backend; all owned test files, not only names/collection output.
- C2/C3a/C3b raw runtime receipts and sanitized source-bound metrics; C4a notes.
- Default app composition and shared review source diff against base: unchanged.

Historical C2/C3a hashes differ from later code where those checkpoints evolved;
they are historical evidence, not current-source proof for all later behavior.
C3b's final raw receipt pins all application/SQL dependencies before/after run.
No later application/SQL/shared-schema change occurred in C4a or this audit.

## Approved acceptance matrix

Paths below are relative to backend unless noted. "Component/owned SQL PASS"
does not imply product/integration PASS. Partial rows remain unachieved globally.

| AC | Current evidence | Result / missing proof |
|---|---|---|
| 01 | contracts/schemas/learning_content.py; domain lifecycle; contract/test_learning_content_commands.py; HTTP eight-action tests | PARTIAL: all content actions, not full preset/policy closed union. CR-C4-01 open |
| 02 | domain authorize; application current guard; unit command/eligibility negatives and HTTP spoof-denial | PARTIAL: assumed capabilities/scope; real BE1 adult/Child identity and commit-time revocation not adopted |
| 03 | immutable domain versions; SQL trigger; integration test edit/restart; fresh draft without approvals | Component/owned SQL PASS; real source/provenance owner adoption still separate |
| 04 | shared DATA-24 imported unchanged; exact context/audience/hash/version/CAS tests; SQL resubmit clears current reviews | PARTIAL: exact binding works; explicit stale-history state/reason projection absent (F03), real owner conformance open |
| 05 | two-proof domain checks; source/policy/reviewer current tests; SQL publish/replay | PARTIAL: assumes owner source/moderation/review-effectiveness port, not real service proof |
| 06 | default/exact resolver denies retired states; SQL v1/draft-v2/recall history case; atomic event/outbox | PARTIAL: owned resolution PASS; BE1 new-session consumer and impacted-reference delivery not proven |
| 07 | server-bound SourceAssessment, generic positive/child/unknown negatives; no fabricated session | PARTIAL: fail-closed fixture semantics, actual source/rights/consent authority unavailable |
| 08 | fingerprint, current replay, revocation/recall negatives; SQL duplicate create/submit and receipt rollback | Component/owned SQL PASS; real authority revocation consistency shares F02 gate |
| 09 | test_commands_sql.py edit_publish/review_publish/publish_recall and forced unique create race; C2 CAS race | Owned SQL cases PASS, not all external revocation races; publish_recall test starts from published state, not arbitrary delivery interleavings |
| 10 | frozen module Alembic branch; SQL upgrade/downgrade/rollback/immutability; C2 child-process restart | Owned disposable PostgreSQL PASS; not a shared/production migration authorization |
| 11 | one candidate content path inventory; default app unchanged | INCOMPLETE: no closed governance dispatcher or typed delegates/spy conformance. Content-only factory is not a substitute |
| 12 | safe errors/body/If-Match/admission; 33 ASGI tests; security/architecture scans | PARTIAL: candidate transport PASS; production verified identity/composition and HTTP-over-real-owner behavior NOT_RUN |
| 13 | CONTENT_HTTP_CANDIDATE sequence; runnable HTTP/SQL examples; immutable resolution metadata | PARTIAL: synthetic examples exist, real BE1/P4 published/recall consumer conformance and delivery/dedup unavailable |
| 14 | checkpoint notes/metrics, candid API limitations, this audit and handoff | Documentation checkpoint, not final closure: open findings and full-card acceptance remain |

## Findings requiring work, not waived

### F01 — full CMD-48 contracts/delegation (OPEN; external + implementation)

No complete preset/AI/core-policy schema or owner delegate exists. Current
content-only router rejects these record kinds with 422 and is not mounted.
Required shape/authority/error/transaction/adoption inputs and acceptance tests:
CR_C4_OWNER_DELEGATES.md. After contract adoption BE2-12 still must implement the
closed union/dispatcher/typed unavailable outcomes; a document alone cannot pass.

### F02 — actual owner authority/source/review fencing (OPEN; integration)

ContentBoundary is a candidate protocol with consistency obligations, not a real
BE1 adapter. Test AssumedBoundary uses thread-local scope, not durable revocation
fences. review_effective for newly recorded proofs also needs explicit owner
conformance: it must support authoritative current review decisions, not merely
assume a proof exists in a separate live service. Caller IDs/role claims must not
be accepted as verification. No permissive defaults may be added to mount routes.

### F03 — explicit stale-review history projection (OPEN; local work)

SRS DATA-24 requires preserved old review records with stale reason after
bytes/context/audience invalidation. SQL retains immutable original proof rows,
and effective-context loading/replay correctly excludes superseded reviews.
However there is no authorized application history projection exposing derived
stale state/reason, and retained original proof JSON still says effective at its
recording time. Do not describe retention alone as complete stale-history UX/API.
Implement an owned typed derived history view without mutating shared owner
schemas or rewriting immutable original proof, and prove resubmit/edit/replacement
and recall semantics. Real external revocation reasons still require owner port.

### F04 — consumer/notification adoption (OPEN; integration)

Owned transactions append safe metadata events/outbox with stable event IDs.
No actual delivery worker, acknowledged BE1 audit/consumer sink or impacted-ref
lookup/cancellation adapter is bound. Do not claim delivered/exactly-once or
active-copy deletion. Required consuming-owner conformance must prove dedup,
new-session denial and preserved pinned historical artifacts.

### F05 — integrated closure review (OPEN)

After F01–04 resolution, run source-pinned full acceptance including adopted
HTTP/auth/SQL/consumer paths. Current proof does not authorize generic production
readiness, foundation closure or dev merge. Clarify reintroduction/history
contract if owner expects same-record new versions after a terminal head: current
edit rejects retired versions and create makes a new record. Do not silently
invent restoration of a terminal version.

## Current revalidation

At audited source: 326 selected local tests PASS / 0 skip (5.42s), Mypy 8 owned
source files PASS. Prior latest real PostgreSQL consolidated run remains 18 PASS
(9 C2 + 1 C3a + 8 C3b), with assumed owner ports; runtime cleaned. SQL was not
rerun solely for documentation audit. No source behavior changed in this audit.

No full-card percent or DONE asserted. Continue local F03 work while owner
contracts are pending; completing this report does not mean the goal is blocked
or finished if safe scoped implementation remains.
