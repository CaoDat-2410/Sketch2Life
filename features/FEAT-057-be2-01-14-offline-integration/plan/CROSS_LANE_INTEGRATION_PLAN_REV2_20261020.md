# BE2-01–14 cross-lane integration plan

- Status: `APPROVED FOR OFFLINE CROSS-LANE COMPOSITION AND INTEGRATION-OWNED ADAPTERS; EDGE RESULTS EVIDENCE-GATED`
- Revision: 2
- Owner: repository owner; implementation executor to be assigned after approval
- Candidate base observed: `feature/be2-backend-ai-integration` at
  `1649b72978877d82b4d7662040ff3555dee0a3a7`
- Updated: 2026-10-20 (Asia/Saigon)

This revision records the owner's direct instruction to review and connect the
BE2-01–07 and BE2-08–14 lanes. It authorizes offline composition and
integration-owned adapters/tests on the existing integration candidate. It does
not replace the branch-combination plan or change any card acceptance. Existing
card-owned source/contracts, shared SQL/migrations, HTTP routes, live services,
providers, Lightning, deployment, and publication remain outside this scope.
When a public contract or owner adoption is missing, that edge remains
`NOT_IMPLEMENTED`; the integration layer must not invent a substitute and call
it connected.

## 1. Goal

Prove that the BE2-01–07 and BE2-08–14 lanes exchange real outputs through their
public, versioned application contracts on one pinned offline candidate. A test
must begin with an output produced by the owning service, deliver that output
through the consumer's public port, and assert the consumer's committed result
and stale/revocation behavior. A hand-written DTO that imitates a producer is
not cross-lane integration evidence.

The deliverable is a reviewed `CROSS_LANE_OFFLINE_INTEGRATION_PASS` (or a
precisely scoped failure/blocked report), not full-card acceptance. Per-card
owners retain their existing acceptance and status authority.

## 2. Verified starting point and limits

- The candidate is clean at `1649b72978877d82b4d7662040ff3555dee0a3a7` on
  `feature/be2-backend-ai-integration` and matches its local remote-tracking
  ref. Recheck the actual remote tip before implementation or publication.
- The latest local and remote-tracking `feature/be2-01-07` ref observed is
  `a3c5b1c078a0772873f23468b3b064c8014532ae`. Its delta from the task-07 source
  already in this candidate changes FEAT-056 documentation/evidence only;
  `backend/src` and `backend/tests` compare equal to the pinned task-07 source.
  Before freezing a new candidate, review the evidence cleanup and record
  whether that docs/evidence delta is adopted. Do not silently restore or delete
  archived review evidence as part of a code fix.
- Existing component runners prove component behavior. Existing BE2-01–06
  offline chain tests prove some connections inside that lane. Neither proves
  the cross-lane edges listed below.
- The current application composition root does not mount BE2-01–14 HTTP
  routers. The AI-job outbox dispatcher is not wired into the live application.
  This plan adds offline composition only; it must not imply that production
  routes or background workers exist.
- The combined Alembic graph has nine heads. This plan does not invent a merge
  migration, run a shared 01–14 database, or replace the separately owned SQL
  receipts with an aggregate claim.
- BE2-02 typed-context serving, real BE1 authority/context adapters, durable
  BE2-03 budget/outbox, selected providers/models, production policy adoption,
  and real worker/queue wiring remain open. `/v2/vision` rejects extra fields;
  this plan must not send typed or child context to that endpoint.
- A `ProviderCopyLifecycle` record from the foundation fake is evidence of a
  simulated lifecycle only. It does not prove provider-side deletion.

## 3. Scope

### Included

- Offline composition tests that call the owning services and their public
  versioned ports with deterministic in-memory adapters for external owners.
- Cross-lane producer/consumer wiring for the edges in §4, including exact
  identity, version/hash, deduplication, authorization, stale state, and
  publication/fence behavior.
- Small adapter or contract corrections required for those edges, only after
  the affected card owner approves the change and its tests.
- A pinned source manifest, focused cross-lane suite, relevant component
  regression reruns, validators, and a report distinguishing PASS, FAIL,
  NOT_RUN, and NOT_IMPLEMENTED.

### Excluded

- Lightning/Studio, model/provider calls, GPU/decoder execution, live service
  startup, deployment, `dev`/`main` merge, and production adoption.
- Shared PostgreSQL/migration composition or edits to already published
  migrations.
- Marking BE2-01–14 cards DONE or changing their acceptance records.
- Adding an HTTP route solely to make the offline test appear end-to-end.
- Replacing a missing owner port with a test-only shortcut and calling it
  integrated. If a required public contract is absent, stop that edge and raise
  a contract-change request for its owner.

## 4. Required cross-lane edges

The integration is a graph of owned handoffs, not one artificial chain in which
every card calls every other card. Each row must use the producer's real output
and the consumer's public contract.

| Edge | Producer → consumer | Required proof |
|---|---|---|
| X01 | BE2-07 knowledge-script → BE2-08 generation | Resolve an exact published script through BE2-07's public `resolve_exact`/export contract. BE2-08 consumes the resulting immutable content and source identity. Hold/assert the BE2-07 validity fence across BE2-08's commit. A source/basis/audience invalidation between read and commit must prevent promotion. |
| X02 | BE2-07 invalidation → BE2-09 review/playback | A real source invalidation from X01 reaches the BE2-09 consumer and invalidates or blocks the exact dependent output. A previously valid playback decision cannot survive a stale source. |
| X03 | BE2-12 publication → BE2-08 generation | BE2-08 resolves a producer-created, published version with exact version and hash. Draft, recalled, superseded, unauthorized, or stale content is denied before job dispatch. No direct table read. |
| X04 | BE2-12 publication → BE2-09 and BE2-11 | BE2-09 and BE2-11 each consume the exact published version through their public contracts. Revoke/recall and audience or authority changes invalidate current eligibility; no test-only shared database access. |
| X05 | BE2-08 successful output → BE2-09 review/playback | A successful BE2-08 attempt creates the artifact/lineage consumed by BE2-09. Review is explicit and scoped to exact source/output identity. Playback is available only after the required review and current authorization; wrong hash/version and stale/revoked source fail closed. |
| X06 | BE2-08 exhausted/failed output → BE2-10 disposition | A controlled failed BE2-08 completion reaches BE2-10 through a typed public event/port. A Teacher's explicit retry/skip/end decision is idempotent. Duplicate delivery, lost acknowledgement, and late success cannot create a second run or override a terminal disposition. No automatic retry or stage advancement is introduced. |
| X07 | BE2-13 preset/automation → BE2-01 job foundation, gated by BE2-14 | An approved immutable preset and explicit dispatch intent become one correctly scoped foundation job. Current policy/limits and kill/disable generation are checked before side effects. A policy change racing dispatch prevents new work; duplicate scheduler events deduplicate. The test invokes an explicit scheduler/dispatch port; it does not start a timer or claim BE1 scheduler adoption. |
| X08 | BE2-14 policy/copy contracts → BE2-03, 04, 08, and 13 consumers | Where the consumer already has an approved public policy port, prove allow/deny, budget/limit, generation-change, and stop-before-side-effect behavior using the BE2-14 service/contract. Where no approved port exists, record `NOT_IMPLEMENTED` and stop; do not silently wire a fixture. Copy purge tests assert only the fake receipt unless a real provider operation is separately approved and available. |
| X09 | BE2-01 job/attempt lineage → BE2-02/03/04 and BE2-08/13 | Route each supported `job_type` to its owning consumer using the actual foundation job service/queue contract. Verify job, attempt, subject, artifact, and idempotency lineage survive dispatch and completion. Unknown or unsupported types fail closed without provider invocation. This is offline routing, not live worker deployment. |

BE2-03→04→05→06 already has offline chain coverage in the candidate. Preserve
and rerun the relevant existing chain tests as regression; do not rewrite that
lane unless a cross-lane change breaks it. BE2-02's typed-context server route
is not an edge this offline plan can claim as implemented.

## 5. Execution phases and gates

### G0 — Re-pin and contract inventory (planning gate)

1. Record candidate commit/tree, actual remote refs, task-07 tip, task-08–14
   source tip, and per-card source manifests. Reconcile the FEAT-056
   docs/evidence-only delta described in §2.
2. Read each affected card's current plan, approval, status, and handoff again.
   Build a contract table naming producer type/version, consumer port, exact
   identity fields, fence owner, invalidation event, and test owner for X01–X09.
3. For each edge, classify the existing contract as `IMPLEMENTED_PUBLIC`,
   `CANDIDATE_NOT_ADOPTED`, or `MISSING`. Attach exact source paths and lines.
   No implementation starts while an edge relies on a missing or unapproved
   contract.
4. Obtain owner decisions on the choices in §10 and a scoped implementation
   approval in the feature record. The existing FEAT-057 approval does not by
   itself approve new adapters or card behavior.

**Gate:** no code changes until G0 is accepted and the new approval names the
allowed files/cards, branch, test environment, and stop conditions.

### G1 — Offline composition harness

1. Add one FEAT-057-owned composition fixture that instantiates the real
   producer and consumer application services. It may provide deterministic
   fakes only for BE1, storage, queue transport, provider, or other external
   systems that have no implementation in this candidate.
2. Fakes must implement the same public contract/version as the intended
   adapter. They must not manufacture producer outputs, bypass eligibility,
   skip a fence, or mutate another feature's repository directly.
3. Add one contract audit per cross-lane adapter that checks version, required
   fields, stable identifiers, and rejection of unknown fields/versions.
4. Add harness teardown assertions for outbox delivery, artifact/policy fence
   mutations, and pending effects, so a passing scenario cannot leave hidden
   work behind.

**Gate:** demonstrate that a deliberately wrong contract version and a sink
that bypasses its fence both fail the relevant test.

### G2 — Source and publication into generation (X01, X03)

1. Produce and publish the source through BE2-07 and BE2-12 services; capture
   the returned canonical reference, version, audience/policy identity, and
   content hash.
2. Pass those returned values to BE2-08 through its public resolver/eligibility
   ports. Assert the generated job pins those exact values and the result
   lineage points back to them.
3. Pause after resolve, invalidate/revoke the source, then resume commit. The
   held validity check must reject promotion and leave no playable/approved
   output. Repeat the negative cases for wrong version/hash and wrong audience.
4. Verify that a source that is draft, recalled, superseded, or not authorized
   never reaches the worker/provider port.

**Gate:** each successful output is derived from an actual producer result;
each changed source fails closed at the consumer's commit boundary.

### G3 — Video output consumers (X02, X04, X05, X06)

1. Feed a successful BE2-08 result to BE2-09 using its public review contract.
   Prove pending review, explicit approval, exact playback authorization, and
   denial after source/output invalidation.
2. Feed a real BE2-07 invalidation and a BE2-12 recall through their public
   delivery contracts. Prove BE2-09 blocks the exact dependent item and
   deduplicates replay.
3. Feed a controlled exhausted BE2-08 job result to BE2-10. Test each explicit
   disposition, duplicate event, lost ACK/replay, and late completion. Assert
   one winning decision and no hidden retry or automatic advancement.
4. Assert BE2-11 consumes the exact published version from X04 and refuses an
   invalid/recalled source without recording activity completion.

**Gate:** outputs and failure events originate from the BE2-08 application
service/foundation completion path; BE2-09/10/11 make their own decisions.

### G4 — Preset dispatch and shared policy (X07, X08, X09)

1. Resolve an approved immutable BE2-13 preset and issue a deterministic
   explicit dispatch intent. Assert the resulting BE2-01 job contains the
   exact preset/version/session refs and uses the normal job/attempt lineage.
2. Invoke the approved BE2-14 policy contract before dispatch. Test deny,
   exhausted limit, kill/disable, generation change between eligibility and
   enqueue, and duplicate intent. No denied case may call the worker/provider
   port or create an accepted job.
3. Exercise only policy ports already present and approved by their owners for
   BE2-03/04/08/13. Missing adoption is recorded as `NOT_IMPLEMENTED`; raise a
   card-owned contract change instead of adding undocumented direct imports.
4. Exercise provider-copy lifecycle only with the existing fake operation
   boundary and state explicitly that this proves receipt/reconciliation
   semantics, not remote deletion.
5. Route foundation jobs for every supported type through the same offline
   consumer registry and assert unsupported types are rejected without effects.

**Gate:** policy and current-owner decisions occur before every protected
side-effect boundary; no real timer, provider, or background worker starts.

### G5 — Final pinned offline verification and review

1. Freeze a clean commit/tree and source hash manifest after all changes.
2. Run the new cross-lane suite and the directly affected owner suites. Rerun
   the full approved offline component batch once on the final snapshot if any
   production source or shared contract changed; otherwise use only receipts
   whose source hashes exactly match the final manifest.
3. Run harness, repository security, architecture, skeleton, Ruff, strict
   mypy, and `git diff --check`. Preserve each command's exit code and JUnit.
4. Inventory Alembic heads and migration tests for reporting only. Do not run a
   shared database or alter migration history under this plan.
5. Review every edge against the acceptance matrix. Any missing edge remains
   `NOT_IMPLEMENTED`; any skipped/unavailable check remains `NOT_RUN`, never
   PASS by inference.
6. Obtain review from the owners of changed producer and consumer cards. Record
   the cross-lane result in FEAT-057 without changing per-card acceptance or
   DONE status.

## 6. Acceptance criteria

| ID | Acceptance |
|---|---|
| A01 | Final source/tree and each producer/consumer source pin are recorded and match the executed tests. |
| A02 | X01–X09 each have an edge result: PASS with producer-created input and consumer assertion, or a documented `NOT_IMPLEMENTED`/`NOT_RUN` with owner and next gate. No edge is silently omitted. |
| A03 | All claimed successful inputs originate from the owning producer service; no manually constructed substitute output is used as integration proof. |
| A04 | Version/hash/audience/authorization mismatch, recall/revocation, stale source, duplicate delivery, late result, and policy-generation races fail closed at the specified edge. |
| A05 | Consumer commit boundaries hold/recheck the producer's validity fence for edges X01–X05; contract owners explicitly approve the fence mechanism. |
| A06 | BE2-08 success, BE2-10 disposition, and BE2-13 dispatch use real application services and foundation lineage. External systems alone may be deterministic fakes. |
| A07 | No direct cross-feature database access, undocumented internal domain import, real provider call, production route claim, or hidden scheduler/worker effect is introduced. |
| A08 | New cross-lane tests and required affected regressions pass with zero unreported failures/skips; all not-run items carry exact reasons. |
| A09 | Required validators pass and final evidence includes source hashes, command/exit/JUnit inventory, edge matrix, and owner review. |
| A10 | All existing card approvals, statuses, and runtime gates remain unchanged. The result is integration evidence only. |
| A11 | Overall result is `PASS` only if every required edge X01–X09 passes. If any edge is `NOT_IMPLEMENTED`, `NOT_RUN`, or failed, report `PARTIAL`, `BLOCKED`, or `FAIL` as appropriate; do not label the whole integration passed. |

If any acceptance row cannot be met without changing a card-owned contract,
stop at that edge, record the gap, and request a separately scoped owner change.

## 7. Evidence to produce

Under `features/FEAT-057-be2-01-14-offline-integration/evidence/`:

- `notes/CROSS_LANE_INTEGRATION_REPORT_<date>.md`: edge-by-edge outcome,
  source pins, contract/fence notes, review disposition, and remaining gates.
- `metrics/CROSS_LANE_INTEGRATION_<date>.json`: machine-readable source hashes,
  command arguments/exits, test counts, skip/failure counts, JUnit hashes, and
  status for A01–A10 and X01–X09.
- `raw/cross-lane-<date>/`: non-secret logs and JUnit outputs.

Keep any owner-specific runtime or SQL receipt under that card's own evidence
directory and link it; do not copy private credentials or real child data.

## 8. Work and commit organization after approval

Use one dedicated integration worktree based on the freshly pinned candidate;
do not create it before G0 approval. Keep per-edge changes reviewable:

1. `X01/X03` producer-to-08 contracts and tests.
2. `X02/X04/X05` source invalidation, publication consumers, and 09 review.
3. `X06` 08-to-10 failure disposition.
4. `X07/X08/X09` preset, policy, and foundation routing.
5. Cross-lane evidence and final verification.

If a change belongs to a card-owned source/contract, implement and review it on
that card's authorized branch/worktree first, then integrate its reviewed SHA.
FEAT-057 may own only the composition harness and integration evidence. Do not
cherry-pick unpublished fixes or bypass owner approval to keep the integration
branch green. No commit count is prescribed; commit boundaries follow ownership
and reviewable behavior.

## 9. Stop conditions

Stop the affected edge if its contract is absent, its owner approval is unclear,
source authority changes during the test, a fence cannot cover the consumer
commit, a migration change is required, or the test needs a live provider,
Lightning, shared SQL, or an unapproved dependency install. Preserve the failing
attempt and report the exact unresolved decision. Do not weaken the producer or
consumer check to turn the edge green.

## 10. Owner decisions and implementation scope

The owner answered the requested scope by directing Codex to review and connect
the two BE2 lanes. The recorded choices for this revision are:

1. A separate offline cross-lane scope is approved under FEAT-057; existing
   component acceptance and card statuses remain unchanged.
2. Use the existing `feature/be2-backend-ai-integration` worktree and candidate
   branch. Do not create a second branch while this candidate has prior
   uncommitted scaffold work that must be preserved.
3. FEAT-057 may own integration composition and adapters in
   `backend/src/sketch2life/infrastructure/cross_lane/` plus behavior tests in
   `backend/tests/integration/be2_cross_lane/`. Do not edit card-owned source,
   versioned contracts, or migrations in this increment. If an edge needs such a
   change, record the exact missing contract and stop that edge for separate
   owner review.
4. Retain the already merged FEAT-056 documentation/evidence snapshot as part of
   the current candidate; do not restore or delete it during this work.
5. Keep verification offline and process-local where required. No shared SQL,
   database provisioning, HTTP route mounting, live service, provider/Lightning,
   card acceptance/status change, `dev`/`main` merge, commit, push, or deploy.

The authorization is limited to the existing public candidate contracts and the
integration-owned composition/adapters/tests listed above. It does not turn a
candidate port or fixture into production adoption. Every edge still requires
its producer-created input, consumer state assertion, and source-pinned test
evidence before it may be marked `PASS`.

## 11. Previously approved test-scaffold sub-scope

The earlier 2026-10-20 instruction approved this narrow first increment. Rev2
preserves that scaffold and expands the authorized work only as recorded in §10
and the matching approval addendum.

Allowed files:

- `backend/tests/integration/be2_cross_lane/README.md`
- `backend/tests/integration/be2_cross_lane/edge_registry.py`
- `backend/tests/integration/be2_cross_lane/test_edge_registry.py`
- `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_SCAFFOLD_20261020.md`
- `features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_SCAFFOLD_20261020.json`
- This plan, `approvals/TASK_APPROVAL.md`, FEAT-057 `DECISIONS.md`, `CONTEXT.md`,
  `status/STATUS.md`, `evidence/README.md`, and the root source register to
  record this sub-scope.

Scaffold acceptance:

- S01: all nine X01–X09 edges are represented once with producer, consumer,
  expected test module, and the scenarios that a later behavior test must prove.
- S02: each edge starts `NOT_IMPLEMENTED`; registry metadata is not presented
  as a passing integration test.
- S03: a registry marked `PASS` must identify its behavior-test module and
  source-bound evidence reference; incomplete or duplicate IDs fail the test.
- S04: documentation states that later edge tests must instantiate real
  producer and consumer services, pass producer-created values through public
  ports, and use fakes only for unavailable external systems.
- S05: focused registry tests, Ruff, and applicable repository validators pass;
  no product code, card contract, service, route, database, or provider changes.

The scaffold completion alone does not satisfy A01–A11 or X01–X09 and cannot be
reported as cross-lane integration PASS.

## 12. G0 source review and current contract disposition

The source review confirmed that the existing component runners are not a
cross-lane composition. The current registry directory has only registry tests;
no X01–X09 behavior modules exist. The following classifications are based on
the candidate source and current public ports, not on card acceptance:

| Edge | Current disposition | Source-level finding and implementation consequence |
|---|---|---|
| X01 | `CANDIDATE_NOT_ADOPTED` | BE2-07 exposes `KnowledgeBundleService.resolve_exact`; BE2-08 exposes `VideoSourceResolver` and `VideoMediaPipeline`. Its existing fixture source resolver does not call BE2-07. A FEAT-057 resolver can pass the exact producer script to the real BE2-08 generation boundary and recheck the BE2-07 source around external work. The downstream foundation/run finalization transaction is a separate open X05/X09 adoption seam. |
| X02 | `MISSING` | BE2-09 has current-source checks in its candidate review boundary, but no adopted invalidation delivery from BE2-07. Do not treat a local status mutation as source invalidation delivery. |
| X03 | `CANDIDATE_NOT_ADOPTED` | BE2-12 exposes current published-content eligibility and BE2-08 accepts an exact library-asset reference, but no adapter resolves BE2-12 output into the BE2-08 pin. Compose only if both public contracts can be used without changing either card. |
| X04 | `CANDIDATE_NOT_ADOPTED` | BE2-12's current-content service exists; BE2-09/11 expose candidate authority/eligibility boundaries. No shared consumer adapter currently delivers the exact publication pin or recall state. |
| X05 | `CANDIDATE_NOT_ADOPTED` | BE2-08 create/worker services and BE2-09 review ports exist, but the fixture submission writes synthetic job intents and no default BE2-01 bridge is supplied. Integration may connect the real services only if it preserves the required atomic job/run boundary. |
| X06 | `MISSING` | BE2-10's `FailureBridge` is an open adoption seam; BE2-08 has no delivered typed failure event to that bridge. Do not synthesize completion as if it came from foundation. |
| X07 | `MISSING` | BE2-13's `SessionCommands` is explicitly BE1-owned. No approved dispatch adapter connects BE2-13 intent to BE2-01, and BE2-14 policy adoption is not implied by the candidate `QueuePolicy`. |
| X08 | `CANDIDATE_NOT_ADOPTED` | BE2-14 current-use/accounting services exist, but BE2-03/04 identify fixture-only/assumed policy adapters and BE2-08/13 lack a default binding. Only consumers with an existing public policy port may be composed; others stay `NOT_IMPLEMENTED`. |
| X09 | `PARTIAL` | BE2-01's job service is real in the component harness; BE2-04 has a test router for its own Vision/Sketch job types. BE2-08/13 are not registered consumers, so this is not shared routing. |

X01 is the first implementation slice because it has a producer public
resolver, a consumer source-resolver port and media pipeline, and a
process-local validity coordinator that can be composed without modifying
either card. Its test may prove exact source delivery and stale-before-provider
rejection, but it cannot claim foundation/run finalization. The remaining edges
are implemented only where existing contracts satisfy their card-owned
boundaries; otherwise their exact blockers remain in the final edge matrix.
