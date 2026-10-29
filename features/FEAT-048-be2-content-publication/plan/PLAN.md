# BE2-12 — Content authoring, publication review and recall

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Date: 2026-10-17 (Asia/Saigon).
- Owner: second BE2 executor.
- Feature: FEAT-048-be2-content-publication.
- Branch/base: feature/be2-12-content-publication / 6dcc57e.
- Scope: whole BE2-12 card; no other business card activated.

## 1. Goal, authority and source mapping

Deliver versioned library content/activity/video metadata, exact safety and
pedagogical review, explicit publication and reasoned recall/archive with
new-session eligibility and immutable history. Scope includes domain/contracts,
durable storage, HTTP dispatcher and consumer conformance, not only a fake demo.

Sources:
- Canonical SRS v3.1: FR056, FR062; UC-035; DATA-33/shared DATA-24/35;
  B19 state/concurrency, B21/B22 field/command, B24 provenance and B26 acceptance.
- FEAT-040 TEAM_TASK_BREAKDOWN.md BE2-12, H-CONTENT-PRESET/H-ADMIN-POLICY.
- FEAT-044 roadmap, latest tracker and BE2_08_14_TEAMMATE_HANDOFF.md.
- Shared schema: contracts/schemas/ai_contract_candidates.py:
  ExactContentReviewCommandV1 and ExactContentReviewRecordV1 (0.1-candidate).
- ADR-0015 ownership; ADR-0018 job foundation reference, not authority for
  adopting all its infrastructure for BE2-12.

Plan approval must explicitly cover scoped decisions below. Preparation is
authorized by the active owner goal; current code approval is absent.

## 2. Deliverables and exclusions

Deliver:
1. DATA-33 typed content commands/records and domain lifecycle.
2. ContentVersionRepository/UoW, schema, forward migration, CAS and receipts.
3. Exact review integration using shared DATA-24 without inventing a duplicate.
4. One CMD-48 router/closed union, content implementation and typed delegates.
5. Published eligibility/read projections, recall event/cancellation intent.
6. Unit/contract/SQL/race/HTTP tests, fixtures and H-CONTENT-PRESET examples.
7. API contract, test/runtime instructions, source-bound evidence and handoff.

Exclude: real Sketch/video generation, model/provider configuration, media bytes
ingestion/player/UI, general CMS/workflow engine, preset/AI/core-policy business
logic, direct BE1/job-table writes, active-copy purge/replacement policy,
infrastructure deployment, package installs and changing published migrations.

## 3. Proposed decisions for owner approval (not adopted yet)

### P1 — authority and separation

Use versioned, organization-scoped author, safety-review, pedagogical-review,
publisher and recall/archive capabilities. Actor role alone grants none.
Author cannot approve either dimension or publish their own authored version.
A non-author reviewer can review both dimensions only with both capabilities;
the reviewer may also publish only with independent publisher capability.
This does NOT mandate three different people. Cross-school and Child actions
are denied. Current authority is checked on mutations, reads and receipt replay.

Capability names and adapters are candidate contracts, not new powers inferred
from Teacher/Super Admin. Real BE1 adoption is a gate. Component tests use
explicitly labelled authority fixtures, never HTTP client-supplied identity.

### P2 — review and supported content

Default review set: effective safety AND pedagogical approvals for exact
version/hash/context/audience and pinned review-policy version. No exceptions
without a separate adopted content-kind policy. DATA-24 generic_library has no
fabricated child session/consent. Source classification is server-validated,
not a caller boolean. Generic authored knowledge/activity/video metadata can
proceed; child-derived publication fails closed pending approved consent/usage
authority, with explicit outstanding integration acceptance.

A moderation/safety policy port must pass before an approve is effective.
No model-based safety or claim verification is fabricated in this card. Source/
asset rights and applicable usage must be validated by their owning contracts.
Missing real contract is an explicit gate, not permissive production defaults.

### P3 — version and recall behavior

Content bytes/metadata hash and authored versions are immutable. Lifecycle
metadata has a separate record revision/CAS. Each edit makes a new draft version;
its approval set is empty. Superseded unpublished versions cannot be published
by replaying old commands. Already published v1 stays historically addressable
unless recalled/archived or current authority/policy denies use; editing v2 does
not rewrite v1 or authorize v2. New default resolution selects only an eligible
published version, never an unreviewed draft. Explicit-version resolution
never silently substitutes another version.

Recall/archive target an exact version, require reason and authority, and block
new-session resolution immediately at transaction commit. History/reviews/
provenance remain queryable to authorized users. Recalled/archived versions
are terminal for this card; reintroduction creates a new version with fresh
review. Emit a deterministic impacted-reference notice/outbox event, but do
not silently delete/replace active-session/portfolio artifacts. Their policy
and delivery adapter remain with BE1/P4.

### P4 — scoped architecture and integration

Propose PostgreSQL + SQLAlchemy in a separately owned learning_content schema,
reusing the existing Alembic environment with a new module branch. This needs
explicit scoped approval; ADR-0018 is not blanket authorization. Keep domain
stdlib-only; Pydantic in contract/interface layer, SQL in infrastructure.
No database foreign keys/writes into BE1 or ai_jobs.

One atomic transaction covers lifecycle CAS, review linkage, receipt, history
and outbox. Unique keys and locks serialize edit/publish/recall, review-policy
changes and publication eligibility; never use an in-process lock as SQL proof.
Outbox delivery is at-least-once with stable event IDs and idempotent consumers,
not an exactly-once claim.

Authorization/consent/current policy checks need a versioned consistency contract
for commit-time revocation races. Use a typed port; propose compatible owner
fencing where adopted. If real BE1 fence/adapters are missing, prove component
semantics with labelled fixtures and keep integration NOT_RUN; do not invent
cross-owner tables or call the whole task DONE.

## 4. Lifecycle and invariants

- create -> draft; edit -> new draft version.
- draft/changes_requested -> submitted through submit_review.
- submitted + exact approved review in one dimension -> remains submitted;
  publication still needs complete effective review set.
- reject/request_changes -> changes_requested, reason required; superseded
  effective reviews cannot authorize an edited or newly submitted context.
- submitted -> published only by authorized independent publisher.
- published -> recalled/archive with reason; draft/submitted/changes_requested
  may archive when permitted; no content deletion in these transitions.
- reject invalid transitions, unknown actions/record kinds and mismatched review
  targets; no knowledge in_review state substituted for submitted.
- Content revision, content version, review revision and job/session revision
  are distinct; record_review checks both record If-Match and named review CAS.
- Hash covers canonical content payload and lineage/context affecting review;
  versioned canonicalization and fixtures avoid key-order/Unicode ambiguity.
  Receipt request fingerprint includes action/target/body/scope/precondition;
  no unreviewed equivalence/canonicalization widening.
- Duplicate command with same scoped key/body returns recorded result only
  after current authorization; changed body/preconditions conflicts. Old
  publication receipt never re-enables recalled content.
- Missing dependency/identity/policy blocks safely, not fabricated readiness.
- Errors/logs contain safe codes/correlation only, never raw content/secrets.

## 5. Contract, API and dispatcher proposal

Primary command: SRS CMD-48 POST /governance/records, using the existing app
prefix convention chosen at composition; no second competing command router.
Create has no record If-Match; other actions require exact record revision.
Idempotency/correlation follow adopted common envelopes; no new CMD identifiers.

Closed branches:
- learning_content -> this feature's content service.
- preset -> BE2-13 typed delegate.
- policy -> closed policy-kind discriminator AI/core -> BE2-14/BE1 delegate.
Unknown branch/action is a validation error; missing delegated implementation
returns a typed unavailable result. No permissive passthrough dict or substitute
local mutation for unimplemented owners. Exact delegate shape is reviewed with
owners; preserve DATA-33 compatibility with the existing candidate envelope.

record_review embeds ExactContentReviewCommandV1 from BE2-05; response uses
its record type. Any binding gap requires a versioned amendment request to
owner05, not changing shared source under this card.

Read/eligibility is an application projection port consumed by BE1 CMD-59/60,
not a competing delivery gateway. A test-only app may demonstrate HTTP
composition with injected verified-authority dependency; it is not a production
route adoption. Real composition uses existing backend verification, never a
demo header/client role as identity. Production adoption remains a separate
evidence gate; complete card deliverables include the typed integration seam.

Error catalogue to refine against shared codes: unauthenticated, forbidden,
invalid action/type, missing precondition, stale record/review, command conflict,
review required/ineffective/mismatched, transition denied, recalled/archived,
source/rights/consent unavailable and delegate unavailable. Contract tests must
prove HTTP status and safe envelope rather than expose exception text.

## 6. Field rationale and ownership

All candidate physical names below require implementation review; no spare fields.

| Fields / family | Source and purpose | Producer / consumer | Constraints / checks |
|---|---|---|---|
| record_id, organization_id, record_kind | DATA-33 identity/ownership | server -> service/consumers | opaque IDs; organization derived from verified authority; immutable scope |
| version, revision, hash | DATA-33, B19 CAS/exact review | server -> reviewers/resolvers | positive monotonic version/revision; SHA256; distinct from review revision |
| content_kind, title | DATA-33 content schema | author -> library | bounded typed fields; allowlist tied to adopted content policy |
| asset_refs, source_refs | DATA-33 lineage/rights | validated author refs -> content consumers | immutable refs/version/hash where required; no raw URLs/secrets or cross-scope refs |
| age_eligibility, purpose_codes | DATA-33, generic audience | author + policy validator -> resolver/review | no inferred age or invented numeric policy; current policy eligibility |
| editorial_note | DATA-33 | author -> authorized reviewer | bounded content; no telemetry echo |
| state, authored_by, created_at | DATA-33 server metadata | server -> authorized views | actor derived, UTC-aware time, allowed transition only |
| context/audience + policy refs | DATA-24 generic library | validated context -> exact review | organization boundary; exact projection/hash/version; no fake session |
| review IDs, dimension, reviewer/review_revision, policy_version | shared DATA-24 | review service -> publication | safety/pedagogical, exact target/context, effective current approvals |
| publication_review_ref | DATA-33 | publisher service -> consumers | both review IDs + policy version; not caller assertion |
| recalled_at, recall_reason | DATA-33/UC-035 | recall service -> history/resolver | time/reason required; original/version kept |
| command receipt key/fingerprint/result | technical B19 duplicate/concurrency | service/UoW -> retries | scoped uniqueness; no contradictory body under same key |
| lifecycle audit/history | shared DATA-35 requirement | service -> versioned BE1 audit sink | append-only local intent + receipt; raw child/media excluded |
| outbox event_id/version/payload/delivery metadata | technical atomic notification | UoW -> BE1/P4 consumer | stable dedup; bounded payload/retry; not independent broker platform |

Classification is derived using artifact/source authority, not merely content_kind.
Never store provider tokens, file bytes or future unused policy columns here.

## 7. Persistence and migration proposal

Tables/families (final normalized design reviewed before code):
content identity/current revision, immutable content versions, exact review
binding/effectiveness history, command receipts, lifecycle events and outbox.
Persist exact shared-review evidence necessary to restart without loss; no
claim that a separate BE2-05 live service already exists.

Add a forward Alembic learning_content branch; include metadata and schema in
existing env.py managed allowlist without reflecting/dropping BE1/ai_jobs.
Do not edit prior migrations. Inspect heads/revisions at implementation time
to avoid colliding with teammate commits. Offline SQL/static validation first;
upgrade/downgrade/restart/race tests only in a disposable authorized database.
Never downgrade/migrate a shared environment without explicit authority.

## 8. Acceptance and evidence matrix

| ID | Required behavior | Proof |
|---|---|---|
| AC01 | all eight DATA-33 actions and closed delegate branches; invalid input denied | unit/contract fixtures + HTTP action-union tests |
| AC02 | current scoped authority; author cannot self-review/publish; Child/cross-school denied | positive/negative role/capability matrix |
| AC03 | create/edit immutable versions; new bytes/context never inherit review | hash/version/history regressions + SQL restart |
| AC04 | generic DATA-24 exact dimensions/context/audience/policy, record/review CAS | shared schema compatibility + mismatched/stale cases |
| AC05 | only both effective required approvals allow publish | missing/revoked/old policy/old hash/source tests |
| AC06 | recall/archive block new resolution and preserve immutable provenance | exact/new-default queries + outbox/history checks |
| AC07 | generic source needs no fabricated session; child-derived cannot bypass purpose/consent | source-classification positive/negative fixtures; real port acceptance separate |
| AC08 | duplicates/conflicts and replay after revoke/recall are safe | receipt/body/precondition/authority tests |
| AC09 | edit/publish, review/publish, publish/recall and receipt races have one consistent winner | real PostgreSQL barriers + CAS/unique checks |
| AC10 | durable restart, atomic rollback and migration module isolation | disposable DB upgrade/rollback/restart; metadata isolation |
| AC11 | one CMD-48 dispatcher, delegates do not mutate content or require live Sketch | spy/delegate conformance and route inventory |
| AC12 | safe HTTP auth/errors, no content/secret leaks, no production auth bypass | API tests, architecture/security scans |
| AC13 | H-CONTENT-PRESET published/recall consumer pack and current read eligibility | versioned positive/negative examples + BE1/P4 port conformance |
| AC14 | docs/commands/evidence truthful, unresolved gates explicit | final review/traceability and handoff audit |

Full-card completion requires the approved acceptance and applicable runtime
proof, not only fake/component tests. Missing real owner port/adoption remains
an integration limitation and must not be reported as passed.

## 9. Checkpoints and commit boundaries

C0 documentation/approval -> C1 domain/contracts + tests -> C2 persistence/
migration + SQL tests -> C3 exact review/publication/recall + tests -> C4 HTTP/
dispatcher/consumer fixtures -> C5 closure/handoff. Split/merge checkpoints only
by logical cohesion, not by function; no unrelated files or giant final commit.
Security and git diff --check before every commit; runtime NOT_RUN clearly WIP.
No push/merge/rebase/deploy. One card on this branch.

## 10. Test execution plan and owner assistance

Local existing Python venv: syntax, unit/contract, focused Ruff/Mypy if available,
architecture/security/harness; no dependency install to conceal missing checks.
Inventory binaries/packages without exposing environment secrets. Do not start
Docker/cloud/DB/Redis or call provider without environment-specific authority.

Durable runtime needs PostgreSQL but no GPU or model; Redis is NOT a new
requirement for content outbox tests. If no authorized existing DB is usable,
prepare one source-pinned consolidated command pack with:
- exact Git/source manifest;
- disposable DB preconditions and known mutation/cleanup scope;
- migration/unit/contract/SQL/race commands and exit guards;
- expected case inventories, no skipped mandatory checks counted as PASS;
- safe raw logs, JUnit and summary to return.
Do not invent commands for tests that do not yet exist. Request execution when
that pack is ready, review root errors before retries and keep fail receipts.

## 11. Decisions and approval request

Owner review requested for whole revision 1, specifically P1 separation rules,
P2 exact two-review set/generic-vs-child-derived gate, P3 version/recall behavior,
P4 scoped PostgreSQL/transaction/port architecture and boundaries. Approval may
authorize this card's implementation and second executor checkpoint coordination,
but cannot supply another owner's contract sign-off or runtime evidence.
Real BE1/BE2-05/P4 compatibility is still verified separately.

Stop before code until actual approval is recorded with plan hash. Next action
after approval: source inventory refresh and C1 domain/contracts implementation.
No cloud/service/model activation or publication rights are inferred.
