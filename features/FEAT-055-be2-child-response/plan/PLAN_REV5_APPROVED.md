# BE2-06 Child response — component plan draft

**Status:** DRAFT REV5 / CLAUDE_NOTES_ADDRESSED / READY_FOR_OWNER_DECISION
**Prepared against:** feature/be2-01-07 at 818ec0778ffb044a77d95c425193f4f02fc3aa44 (same as local origin tracking ref when prepared).
**Revision:** 5, successor to exact Rev4 SHA256 1e450ceb30a4f9727a9a9aea97f0142854b79e99ec93af345a240b4f4b5c4d1f. Rev1–Rev4 remain unchanged. Claude PASS_WITH_NOTES (2 P2 / 4 P3) is preserved verbatim: SHA256 e58805915f8bf871529fe638362de8da41dd4dbe8174c0f26805f955b23b17e6. This revision also adopts an explicit proposal for the missing CMD-36 If-Match requirement.
**Temporary location:** FEAT-052 evidence/local/be206-preparation/; ignored by Git. This is not the future owning FEAT plan and does not allocate a FEAT number. A planning-only branch/worktree was created on owner instruction; this does not authorize BE2-06 implementation.

## 1. Purpose

Plan the offline Child-agency component for BE2-06: a child in the current authorized turn can view, hide, or decline an exact currently approved Sketch proposal and continue drawing. A response is attributable to the server-bound participant and turn, applies to one proposal version, and never changes the child's canvas source, Teacher review history, or learning assessment.

The task card defines the component seams as CMD-36, a DATA-23 child-response projection, response idempotency/attribution, and a Teacher response event. The runtime route, mobile UI, durable infrastructure, and external event delivery remain separate gates.

## 2. Source baseline and authority

The current project context and source register were read before planning. These sources provide requirements; this draft does not turn unapproved runtime or integration work into authorization.

| Source | Current anchor | What it establishes |
|---|---|---|
| features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md | BE2-06, lines 570–577 | Scope, CMD-36, DATA-23 projection, response idempotency/attribution, Teacher event, dependency on BE2-05 and current turn/grant fixtures; no UI ownership |
| features/FEAT-044-be2-ai-job-foundation/plan/BE2_ROADMAP.md | §4, lines 184–189; dependency table line 133 | Exact approved item/turn; idempotency; original hash unchanged; revoke/duplicate/late response must not open access or call model; 05/current-turn gates |
| features/FEAT-044-be2-ai-job-foundation/plan/BE2_EXECUTION_TRACKER.md | Q08, current-state lines 3–8 | BE2-05 offline accepted and published; BE2-06 planning only followed publication; 06 needs its own plan and approval |
| features/FEAT-039-collaborative-learning-scope/artifacts/Collaborative_Learning_SRS_v3.1.md | UC-021 lines 1298–1310; DATA-23 line 1652; CMD-36 line 1780; receipt/idempotency rules lines 978, 1630, 1712–1716; command notation lines 1739–1741 | Child choice is separate from approval and artwork; response history binds actor/proposal/version/time; revoked content is unavailable; same command key and payload replays one receipt, key reuse with another payload conflicts |
| features/FEAT-052-be2-sketch-review/plan/PLAN_R2_APPROVED.md | §8.1–8.2 | Intended handoff from 05: eligibility, review_ref, child payload, and eligibility-changed intent; current-turn/grant remains owned by its source |
| features/FEAT-052-be2-sketch-review/approvals/COMPONENT_ACCEPTANCE.md and evidence/notes/BE205_CODEX_REREVIEW_20261019.md | Acceptance and review disposition | 05 is accepted at offline component scope only; runtime, BE1 authority/ticket, durable persistence, BE2-14 adoption, and integration remain open |

### Verified source facts at the plan base

- FEAT-052 is SKETCH_REVIEW_COMPONENT_OFFLINE, accepted PASS_WITH_NOTES; BE2-05 remains IN_PROGRESS / NOT_DONE.
- DATA-23 already defines ChildResponseV1 with actions available/viewed/hidden/declined, participant_id, turn_id, and responded_at; BE2-04 leaves child_response null.
- FEAT-052 code exposes SketchReviewService.eligibility(principal, proposal_id, asset_ref, content_sha256, review_ref) and child_payload(principal, proposal_id).
- No named SketchAccessEligibilityPort protocol exists in the published source at this base, despite being listed as a planned consumer seam in FEAT-052 §8.1. The plan must not claim the symbol is already implemented.
- Current child-turn/grant authority is not owned by BE2-06. The source record must come from the existing P2/BE1 contract or a synthetic fixture implementing that contract; caller-provided participant_id is never identity proof.
- BE2-06 code and an HTTP CMD-36 route do not exist at this base.

### Additional source verification for Rev5

- Public `SketchReviewService.eligibility` (`application/services/sketch_review.py:119–124,514–556`) returns server participant, effective review reference and a target with **proposal_version**, content hash and organization/session/canvas. A 06-owned adapter can bind exact version without a default 05 follow-up. The full target includes text/provider/job metadata; project an allowlisted DTO immediately.
- The target audience is the producer audience, possibly broader than the effective approval audience. Eligibility authorizes only the requesting participant. Never authorize other viewers from that tuple.
- Published fixture names are `AssistanceOwnerPort.canvas/current_turn` and `AssistanceAuthorityPort.decide` (`application/ports/assistance.py:164–191`), ASSUMED_CONTRACT. `current_turn` is canvas-only and used for Teacher attribution. Device authority comes from `decide(principal, canvas)`; its participant must match the participant authorized by 05.
- `EligibilityDecision` itself has no epoch/fencing token. Epoch-related protocols do exist elsewhere in 05 ports; they do not establish a 05→06 transaction.
- `ChildResponseV1` requires participant/turn/aware timestamp even for available (`contracts/schemas/sketch_proposals.py:27–33`); initial choice must stay null rather than use fake attribution.
- SRS:1739–1741 defines D as verified device/current grant plus an active bound turn for new child-authored mutations, K as Idempotency-Key, M as primary-aggregate If-Match. CMD-36:1780 is D K M. SRS:978,1630,1716 separates accepted receipt replay from new mutation guards.
- Fresh branch-tip inventory (29 actual remote heads, 18 local heads, 26 unique tips; no unreadable tips) found 052 also used by the other lane and 053 already used. Candidate FEAT-054 is unallocated. Other-lane tip inspected: f821cc28a6b7460afd2ad649ac46bb0163ca7cfc. See BE206_FEAT_INVENTORY_20261019.json; no dependency on that lane's code is introduced.

## 3. Proposed checkpoint

CHILD_RESPONSE_COMPONENT_OFFLINE only:

- Add a typed CMD-36 application command and DATA-23-compatible child-specific response projection.
- Use FEAT-052's public review eligibility behavior through a narrow consumer-facing port/adapter; use the current-turn/grant contract through a separate port.
- Persist append-only response history, an idempotency receipt, audit attribution, and an idempotent Teacher-response outbox event in an in-memory fake.
- Demonstrate the complete fixture chain against the actual BE2-05 service and current-turn fixture.
- Keep the result explicitly offline. No claim of live child authority, route, durable storage, real media ticket, UI behavior, or production delivery.

## 4. Command, public adapters and projection

### 4.1 CMD-36 contract

A response command returns only a typed receipt/projection; never Sketch content, asset references or media URLs. Content read is a separate explicit operation.

| Field | Proposed rule |
|---|---|
| proposal_id | Path selector; resolved through public 05 eligibility. |
| action | Strict viewed / hidden / declined enum. |
| expected_proposal_version | Required positive integer; compare with target.proposal_version. |
| review_ref | Required selector, checked against effective 05 reference; never permission proof. |
| turn_id | Required original command attribution; a new operation matches the active server-bound turn. Accepted replay may refer to a now-closed turn. |
| idempotency_key | Application envelope, future Idempotency-Key header. Scope: organization + verified principal + contract + target + key. |
| if_match | Viewer-response ETag from authorized 06 projection. New operations require it; accepted replay bypasses current equality. |
| participant / organization / content hash / audience overrides | Forbidden command fields. Derive server-side. |

The server generates a semantic response_id, distinct from the client operation key. Fingerprint the validated semantic command (contract version, proposal ID, action, expected proposal version, review reference, original turn ID) using canonical typed JSON. JSON whitespace/property order is irrelevant; preserve opaque ID values exactly. If-Match and the idempotency key are envelope/precondition data, excluded from the semantic fingerprint and stored separately. Same key with changed semantic fields conflicts.

### 4.2 Exact public 05 adapter and device authority

A 06-owned adapter invokes `SketchReviewService.eligibility(principal, proposal_id, review_ref=...)` once; when disclosing a stored response, also pass its known content hash. Compare the returned `target.proposal_version` to the expected version and validate proposal/organization/scope. Immediately project `ReviewAccessSnapshotV1`: organization/session/canvas, proposal ID/version, content hash, requesting server-authorized participant, effective review_ref (source snapshot/hash only if audit needs them). The command service receives this allowlist, never the full target/text/asset/provider/job object. Do not log, cache or serialize the full target. No default 05 source/schema change or private repository/UoW/fake-store reads.

The producer target audience is not the effective reviewed audience; each requesting child must independently pass 05 eligibility. All absent/ineligible/inaccessible/exact-identity-mismatch results map to a single 06-owned application reason `SKETCH_UNAVAILABLE`, with no target details. Do not pretend that 05 raises REVIEW_REQUIRED. HTTP mappings remain deferred with the route.

For every new command/read: resolve CanvasFacts through `AssistanceOwnerPort.canvas` using the pinned target organization/canvas, check organization/session/canvas consistency and require CanvasFacts.session_active, then call `AssistanceAuthorityPort.decide` for this DEVICE principal. Require allowed, a contributor with non-null turn_id, contributor participant equal to 05's authorized participant, and command turn_id equal to that verified turn. Record turn_revision if exposed; it is not a distributed fence. Canvas-only current_turn and the proposal's original contributor must never substitute for the responding device participant.

Receipt disclosure uses a separate 06-owned fixture port: verify current principal/grant/device binding to the stored participant and read scope, without requiring the old turn to remain active. Its real BE1/P2 implementation remains an integration gate. BE2-03 disclose(principal, AssistanceRequest) illustrates the policy, but is not a generic API accepting another resource type.

### 4.3 Explicit read projection and viewer aggregate

For offline chain coverage, a separate read adapter may map the existing SketchChildPayloadV0 shape plus a 06 exact-version envelope from that same successful 05 eligibility result. Never take metadata from one decision and then independently call child_payload for another snapshot's content. Only an explicit read projection may carry authorized Child content; CMD-36/history/receipt/audit/event remain content-free. No HTTP/media delivery/ticket path is introduced; runtime fetch still needs BE1 integration.

Current device-turn checks and viewer visibility apply to each read. Passive reads suppress hidden/declined content. Proposed OD-06 allows an explicit re-view read of still-authorized hidden content, without itself clearing hidden state; a later viewed acknowledgement records the change. Declined content stays suppressed for that participant/version.

Before any actual response, return top-level availability plus `child_response=null`; do not fabricate available response events/turn/time. After an action, emit strict ChildResponseV1 from real server attribution/time. Keep visibility/availability separate from historical choice, and never write the shared 04 record.

**Owner proposal OD-08:** the CMD-36 primary aggregate is the 06 viewer response keyed by `(organization,participant,proposal_id,proposal_version)`, independent of turn/review_ref. An authorized projection issues a family-qualified ETag binding that identity, the current exact hash/review_ref, and local response revision. Initial state has virtual revision 1 without a read-side write; semantic changes increment it. New operations perform final local CAS, including conditional first-write initialization. This refines the SRS-required M primary aggregate; it does not reuse producer/review ETags or fence 05/BE1.

## 5. Transition and side-effect rules

New responses require current review and device-turn authority. A viewed action records a client's explicit acknowledgement after authorized payload read, not proof that pixels were rendered or observed. Hide affects only the current viewer. Decline never deletes canvas strokes, changes assessment, forces another suggestion or calls a model. Existing drawing operations continue independently; source snapshot/hash, strokes, document epoch and accepted operations remain unchanged.

History is append-only and each event retains its originating turn. Current viewer state and terminal decline are scoped by participant/proposal/version, not turn or review_ref; a later turn/review must not reopen declined same-version content. New proposal version has independent initial state.

The table is an **owner proposal**; SRS does not already prescribe hide→view restore. Every new operation uses current disclosure, active-turn/review guards and its viewer ETag. Accepted same-key replay is handled before this table.

| Prior state | viewed | hidden | declined |
|---|---|---|---|
| No response (null) | Record viewed acknowledgement | Record hidden | Record decline + terminal marker |
| viewed | Semantic no-op | Record hidden | Record decline + terminal marker |
| hidden | Record viewed only after explicit authorized re-view (OD-06) | Semantic no-op | Record decline + terminal marker |
| declined | RESPONSE_TERMINAL | RESPONSE_TERMINAL | Existing disposition; no semantic event |

Fresh keys repeating the current semantic state create at most an immutable alias receipt and one operation audit, without response history/Teacher event/revision increment. Reference original response ID/turn/time without relabeling to the new turn. Repeated viewed acknowledgements are proposed as no-ops rather than new observations. Same-key replay creates no records. Denied/replayed/no-op actions never generate jobs/provider calls; denied calls create no successful response/event.

## 6. Guard order, replay and transaction boundary

06 owns only viewer state, terminal marker, history, receipts/audit and Teacher outbox. Its transaction publishes them atomically. There is no 05/BE1 private lock or cross-repository transaction.

1. Parse strict command/limits and verify principal/current read-disclosure authority before exposing receipt, conflict, ETag or current revision. A private lookup is not an existence-disclosure channel.
2. Inspect accepted scoped receipt/canonical fingerprint. An identical accepted command replays its immutable original participant/turn/time/status/body despite old-turn closure or stale original If-Match, provided current device/grant/read binding still matches its participant/scope. Proposed fail-closed OD-07 additionally requires current 05 eligibility for the stored exact version/hash/review. SRS mandates current disclosure; this extra exact-review policy is a named 06 proposal. No history/audit/outbox/state duplication. Revoked grant/binding/eligibility yields generic unavailable, without receipt or target details.
3. Authorized same key/different semantic payload yields IDEMPOTENCY_PAYLOAD_MISMATCH, never a fresh command. Only unseen operations advance to mutation guards.
4. Unseen operation: current exact 05 snapshot, allowed device-bound active turn with matching participant/canvas, and If-Match. Missing -> PRECONDITION_REQUIRED; stale/foreign viewer ETag -> STALE_AGGREGATE after authorized disclosure, without sensitive foreign revisions or success writes. Record observed review_ref/proposal_version/hash, not a fictional 05 epoch. Accepted replay bypasses this active-turn/CAS gate.
5. Final 06 unit rechecks receipt uniqueness, local viewer revision/terminal marker and transition. A semantic change atomically writes state/revision, history, receipt, audit and one stable Teacher event; a semantic no-op writes alias receipt/operation audit only. Rollback publishes nothing. A concurrent duplicate goes through current disclosure replay. Conditional initialization protects two first writes at revision 1.
6. Cross-feature ordering: revoke/turn-close completed before validation denies new operation/read; a previously observed allowed decision followed by a later change may leave one historical response. It never grants later fetch/ticket/canvas/provider access. Reauthorize every future read; cover both orderings without asserting SQL/multi-process fencing.

Teacher event: versioned stable event/response/operation identity; organization/class/session/canvas, proposal/version/hash/review, participant, original turn, action and server time. Neutral wording only, no deficit/assessment inference. Exclude Sketch text, asset refs/URLs, full target, provider metadata and credentials. Only real semantic transitions generate events; none for replay/no-op/denial. A scoped fake consumer demonstrates Teacher-only current class/session visibility; real assignments, broker/delivery and tickets remain open. Events are historical attribution, never approval/access authority.

## 7. Candidate acceptance matrix (not executed)

| ID | Scenario | Required assertion |
|---|---|---|
| B6-P01 | Approved item/current turn/viewed | Version/hash/ref-consistent authorized read, then content-free response receipt. |
| B6-P02 | Explicit restore after hidden (OD-06) | Authorized re-view read; stays hidden until explicit viewed acknowledgement; other viewers unchanged. |
| B6-P03 | Hide | Viewer-only visibility change; artifacts/04/05 history/canvas unchanged. |
| B6-P04 | Decline | Terminal participant/version marker; no generation/assessment side effect. |
| B6-P05 | Two viewers | Independent state and separately authorized requesting participants. |
| B6-P06 | New approved proposal version | Independent initial state; old history/decline unchanged. |
| B6-I01 | Same key/canonical body | Original immutable receipt; zero new state/history/audit/event. |
| B6-I02 | Same key/changed action/turn/version/review | Authorized mismatch; no second mutation. |
| B6-I03 | New key/repeat viewed/hidden/declined | Alias receipt/audit only; no revision/history/event change or relabeled attribution. |
| B6-I04 | Lost ack then old turn closes/stale original ETag | Original receipt replays when current disclosure/binding/exact review allow; active turn not required. |
| B6-I05 | Replay after grant revoke/participant rebind/review revoke/version replacement | Generic denial; no receipt/content/ETag/target details. |
| B6-I06 | Replay after later 06 state change | Original receipt rather than current state; never restores access/visibility. |
| B6-N01 | Missing/pending/rejected/unsafe/stale/revoked/outside-review-audience | Uniform SKETCH_UNAVAILABLE; no diagnostic target fields or response writes. |
| B6-N02 | New operation with closed/revoked/mismatched turn | Denied without mutation; accepted replay remains I04. |
| B6-N03 | Caller injects participant/hash/audience/organization | Strict schema rejects overrides; server binding wins. |
| B6-N04 | Unseen key after invalidation | No response/access/event/provider work. |
| B6-N05 | 05 participant differs from allowed turn participant | Denied even when fixtures independently allow both. |
| B6-N06 | Canvas/organization/session mismatch, inactive CanvasFacts.session_active or null turn | Denied even if 05 and the turn fixture separately allow; no new content/response. current_turn/original contributor cannot substitute. |
| B6-N07 | New operation missing If-Match | PRECONDITION_REQUIRED; zero success records. |
| B6-N08 | Stale/foreign viewer/target ETag | STALE_AGGREGATE safely; no foreign state/revisions. |
| B6-N09 | View/hide after decline, including later turn/review_ref | Terminal version remains closed; no state reset/re-show. |
| B6-N10 | Producer audience A/B, approval only A | B unavailable; broad target audience does not authorize B. |
| B6-N11 | Passive hidden/declined fetch | No automatic restoration; declined content suppressed. |
| B6-R01 | Review revoke before/after decision | Before denies; after may preserve history but future access denies; no content in command result. |
| B6-R02 | Turn close/rebind before/after decision | Before denies new operation; after preserves old attribution only; replay follows I04/I05. |
| B6-R03 | Faults between state/history/receipt/audit/outbox | Atomic rollback; retry gives one outcome. |
| B6-R04 | Competing transitions/same ETag | One local CAS wins; no last-write-wins. |
| B6-R05 | Competing first writes/virtual revision 1 | Conditional initialization prevents duplicate state transitions. |
| B6-R06 | Concurrent identical key | One semantic response/event; duplicate uses authorized replay. |
| B6-C01 | Actual 04→05→06 fixture chain | Producer proposal, actual review/eligibility, device-turn fixture; no handcrafted approved record. |
| B6-C02 | Teacher event | Stable typed neutral event, scoped Teacher consumer, no content/URLs, only semantic transitions. |
| B6-C03 | Initial/real DATA-23 response | Initial null, no invented attribution/time; real strict ChildResponseV1 and viewer isolation. |
| B6-C04 | Mutation boundary | Only public adapters and 06 writes; no direct canvas/job/04/05 mutation. |
| B6-C05 | Metadata/version boundary | Actual proposal_version mapping; full target cannot enter command/log/receipt/event/history; no inferred epochs. |
| B6-C06 | Canonical fingerprint | JSON whitespace/order equivalent; semantic changes conflict; If-Match separate from semantic fingerprint. |

These are planned assertions, not passing tests. Full BE1 authority/Teacher assignment, route/UI, SQL/Redis, delivery worker, tickets and distributed revocation remain NOT_RUN / NOT_IMPLEMENTED. Do not call BE2-06 DONE from this offline component.

## 8. Implementation sequence and candidate commit slices

Only after formal plan/owner approval. These are logical review units, not authority to commit now or a promised count. Include meaningful tests with each behavior; avoid non-building intermediate snapshots.

1. B6-C1 — Owning feature records and strict command/result/metadata contracts.
2. B6-C2 — Viewer/version identity, immutable history, transition rules and terminal decline.
3. B6-C3 — Public05 metadata/read adapters, device-turn and separate disclosure ports.
4. B6-C4 — Fake repository, initial revision/CAS/uniqueness and transaction fault injection.
5. B6-C5 — Authorized viewer projection/ETag, initial null and same-decision payload mapping.
6. B6-C6 — Viewed acknowledgement with exact binding, receipt/audit/event.
7. B6-C7 — Hide plus owner-approved explicit restore.
8. B6-C8 — Terminal decline across turns/reviews and semantic no-op outcomes.
9. B6-C9 — Canonical idempotency, accepted replay and current disclosure revocation.
10. B6-C10 — Actual04/05 chain harness, scoped Teacher consumer and deterministic examples.
11. B6-C11 — Race/first-writeCAS/rollback/subset-audience/no-side-effect assertions.
12. B6-C12 — Focused and01–05 regressions, Ruff/mypy, harness/security/architecture/skeleton/diff checks, evidence and review handoff.

Candidate paths: domain/child_response.py; contracts/schemas/child_responses.py; application/ports/child_response.py; application/services/child_response.py; infrastructure/child_response/{adapters,fakes,harness,examples}.py; focused domain/service/adapter/chain/race/contract tests and synthetic fixtures. Only adapters import producer public types; domain/service depend on 06 ports/contracts. No source edits to 04/05/foundation/BE1, SRS, production router/UI/migrations or the other lane. Owning feature and shared routing docs are the approved record scope. Use existing environment; record interpreter/commands/source hashes and report actual failures.

## 9. Branch, allocation and publication

Branch/worktree: feature/be2-06-child-response, .worktrees/be2-06-child-response, base818ec0778ffb044a77d95c425193f4f02fc3aa44. Local/shared/task-remote refs were inspected at the same base; no task-specific commits. The shell branch is not implementation approval.

Propose **FEAT-054-be2-child-response**, currently absent from inspected tips. Other lane f821cc28 contains FEAT-052-be2-video-failure-disposition and FEAT-053-be2-activity-execution. 052 is now also a known collision with our task05; keep history and resolve cross-lane mapping later, not by renaming in task06. Inventory is not a permanent reservation or proof about unpublished work. Obtain owner allocation and recheck current tips before creating the formal feature folder; no external confirmation is claimed or required by this proposal.

Before code: resolve OD-01–10, create allocated feature records, freeze exact plan/acceptance and record verbatim explicit task approval in approvals/TASK_APPROVAL.md. Set ACTIVE/substitution/WIP1 only on that direction; Claude PASS_WITH_NOTES is not owner approval. If shared tip moves, inspect ancestry/diff and revalidate base before updating the empty planning branch. Preserve unrelated worktrees.

After accepted implementation and a separately approved publication plan, verify actual remote tips, push task branch and carry accepted commits into feature/be2-01-07 under that Git instruction. Security before every commit/push; no force/dev merge or runtime closure inferred.

## 10. Owner decision package

All choices remain **PROPOSED / NOT_SELECTED**. One explicit approval may select this package.

| ID | Recommendation | Limit |
|---|---|---|
| OD-01 | Allocate FEAT-054-be2-child-response after final current-tip inventory recheck. | Owner allocation, no permanent reservation; existing cross-lane collisions mapped later. |
| OD-02 | CHILD_RESPONSE_COMPONENT_OFFLINE with actual04→05 fixtures. | No route/UI/durable/provider/runtime or full-card claim. |
| OD-03 | 06-owned allowlisted adapters over one public05 eligibility result; no producer change. | Compare actual proposal_version; authorize requesting participant only. |
| OD-04 | Device-bound canvas authority matches05 participant; separate replay disclosure port. | Real BE1/P2 contracts stay assumed/integration-gated. |
| OD-05 | Append-only history and viewer/version state/terminal marker, receipt/audit/outbox in06 fake transaction. | Turn is attribution, not decline uniqueness. |
| OD-06 | Explicit authorized hide→view refinement; decline terminal per participant/version; fresh-key same-state no-ops. | Owner refinement; not claimed as already-adopted restore policy. |
| OD-07 | Canonical idempotency; replay despite closed turn/staleETag under current same-participant disclosure and exact05 eligibility. | Exact-review replay rule is fail-closed06 proposal; no content/events duplicated. |
| OD-08 | 06 viewer-response primary aggregate ETag, virtual revision1, final localCAS. | Named SRS-M refinement; no05/BE1 fence or producer revision edits. |
| OD-09 | Stable neutral Teacher event; atomic fake outbox/scoped fake consumer. | Real assignments/broker/delivery/ticket stay open. |
| OD-10 | Task06 single ACTIVE offline slot on dedicated branch; task07 PARKED, BE2-01 WAITING_STUDIO. | Existing offline acceptances/runtime gates remain; implementation approval grants no Git publication. |

Next: owner selects this package or names changed OD items. Formal feature allocation/plan freeze/TASK_APPROVAL then precede implementation. See BE206_REVIEW_DISPOSITION_REV5_20261019.md for Claude finding mapping and additional source corrections.
