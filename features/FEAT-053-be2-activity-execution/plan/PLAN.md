# BE2-11 — Activity discovery, adaptation and execution

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Date:2026-10-19 Asia/Saigon
- Branch: feature/be2-08-14
- Baseline:7b49a1b
- Owner: receiver08–14; BE1 session/outcome/reflection/portfolio, P4 composition.

## 1. Goal, sources and authority

Deliver DATA-29/CMD-45 activity assignment from authorized reviewed activity
discovery/recommendations through explicit Teacher selection/local adaptation/
preparation/start/finish/skip/interrupt. Preserve exact source, effective snapshot,
age/safety policy, objective/provenance and truthful off-screen outcomes.

Sources: FEAT-029 Master SRS v3.1 FR041/042/043/shared044, UC-027/028, DATA-29/
shared33, CMD-45/59, FIX-UX-06; FEAT-040 BE2-11; FEAT-044 receiver handoff/order;
ADR0015/0018; existing catalog/semantic/ranking/preparation code and12 published
content contracts. Requirements are sources, not execution authority.

FR041 library/recommendation and Teacher selection/adaptation CONFIRMED. FR042
field details and FR043 preparation workflow remain PROPOSED product refinements;
use versioned candidate DATA-29 shapes and explicit owner policy ports, not falsely
adopted numeric age/material/prerequisite/ranking rules. UC-028 reflection/evidence
format PROPOSED/TBD; never auto-enable mic/camera or infer psychological assessment.

Current user "task tiếp" authorizes planning only. Exact revision1 approval required
before code. Prior10 internal tests/14 SQL prepared do not approve11 implementation,
database provisioning or real integration.

## 2. Scope and exclusions

Own catalog/recommendation mapping candidate, immutable effective assignment/domain,
versioned DTO/guards/application services, own persistence/migration, injected thin
CMD-45 HTTP, result-reference/event handoff to BE1, reproducible tests/audit/handoff.
BE2 owns source projection for BE1 CMD-59, NOT a second primary CMD-59 endpoint.

No master catalog mutation/publication workflow duplication, direct BE1/12/foundation
SQL/FKs, competing CMD-46/47 observation/reflection/portfolio endpoints or fabricated
individual achievements. No new generalized rule/agent engine or actual provider/
model/ranking weights/thresholds/automation. Legacy route rules not silently changed.
No frontend/device/media capture/production mount/default auth, package installation,
SQL provisioning, Lightning/provider/GPU, push/merge/deploy. Actual BE1/P4 authority/
consumer composition stays teammate-deferred, NOT waived acceptance.

## 3. P1 — discovery/source contracts and immutable assignment rules

1. Inventory candidate full-topic/exact-age/ranking/preparation adapters. Explicit
   mapping to authorized reviewed activity source refs/versions/hashes and objective/
   instructions/materials/safety/provenance definitions. Legacy IDs/curated metadata
   do NOT imply current12 published status or actual school eligibility.
2. Discovery projection for CMD-59 preserves broad topic/exact-age/preference
   semantics under adopted content/age policy. NO added hard filtering by missing
   readiness/history/materials/prerequisites or silently importing legacy resolver
   readiness options. Expose relevant warnings separately from execution eligibility.
   Optional recommendation remains bounded candidate with source/reason, never
   Teacher choice/approval; missing ranker truthful unavailable/fallback only when
   explicitly specified, not hidden provider activation or invented scores.
3.12 ContentWrite currently generic activity fields, not full DATA-29 instructions/
   material/objective schema. Define own typed exact-source activity projection/
   resolver overlay; absent reviewed definition fails closed. Do not parse title/
   editorial_note into trusted safety data, fork DATA-33 or rewrite published schema
   without adopted CR11-01.
4. Model immutable source_activity_ref +objective refs +effective_activity_snapshot
   and Teacher adaptations; exact org/session/resolved class/group audience, policy/
   context membership revision and attribution. Adaptation creates assignment
   revision/snapshot, never master mutation; reset preparation after relevant edits/
   audience/source/policy changes. Safety-critical edits need renewed review via
   explicit owning policy boundary, not self-approved safe because Teacher edited.
5. DATA-29 state enum proposed/teacher_selected/preparation_required/ready/
   in_progress/completed/skipped/interrupted separate from command action enum.
   Define full valid action-state matrix and monotonic revisions/timestamps; no
   auto-start, terminal resurrection or automatically completed group participants.

## 4. P2 — current eligibility, preparation and guarded lifecycle

1. Authenticate actual action-specific Teacher/org/session/control and audience
   membership; resolve current reviewed/published source/recall/usage/policy/consent
   as applicable. Pure refs/boolean/type checks not real authority. Hold current
   owner fences through own commit; no network/outer-lock acquisition under own UoW.
2. Mixed-age execution checks EVERY resolved child using authoritative exact-age
   context +approved policy, not average/old age buckets or client birthdate assertions.
   No default age/preparation/prerequisite thresholds. Missing policy/current age/
   safety proof cannot grant execution; broad discovery remains distinct.
3. CMD-45 select creates teacher_selected/preparation_required candidate assignment
   with no If-Match. Existing assignment reselection/local adaptation uses select
   +assignment_id/If-Match as documented candidate refinement; do not invent an
   upstream `adapt` action. Change only allowed pre-start states; stale/new source
   or adaptation resets confirmations, never modifies old immutable snapshots.
4. confirm_ready/start require nonnull feasibility_confirmation(materials_available,
   safety_checked,note) per candidate DATA-29. True checkboxes alone not authority:
   current source/policy/per-child/adaptation review must pass; missing/hazardous/
   unprepared remains non-startable. start rechecks freshness even after ready.
5. finish only appropriate started assignment, preserves actual execution/source/
   reason/evidence refs. skip/interrupt require nonblank reason and explicit Teacher;
   define pre-start skip vs in-progress interrupt/finish matrix. No finish implies
   every child achieved objective, reflection recorded or observation authored.
6. Persist assignment revision/history/actor-key-body receipt/audit/outcome handoff
   intent atomically. Independent assignment/session/source revisions; same key/body
   replay reauthorizes, no repeated side effect; different body conflicts and
   concurrent lifecycle commands have one CAS winner. No implicit session advance.
7. Versioned BE1 result-reference/lifecycle event+authenticated ACK consumer port,
   original-key delivery/recovery/idempotency with no DB tx across transport. Failed/
   lost save/ACK leaves pending handoff, not false portfolio saved/completed. Never
   write BE1 tables or return fake reflection/observation success. Explicitly scope
   own execution state vs external result save/delivery state as independent axes.
8. Recall/source/audience/policy change invalidates future start/confirm as actual
   policy dictates; retain history, flag existing assignment stale/nonexecutable.
   Define in-progress intervention via actual owner policy/notice, no invented
   automatic session reversal or claiming outbox itself stopped children/activity.

## 5. P3 — own storage, CMD-45 and consumer boundary

1. Add own assignment/history/idempotency/outcome-delivery intent/receipt rows and
   new frozen forward migration under existing scoped PostgreSQL/Alembic conventions.
   Strict codec/hash/scope, CAS/unique scoped keys, original source/adaptation
   immutability and transactional event history. No cross-owner FK/direct SQL or
   published migration edits; local locks not advertised BE1 revocation fences.
2. Inject POST /activity-assignments with closed action union select/confirm_ready/
   start/finish/skip/interrupt, verified server identity/session, explicit bounded
   strict JSON/headers/scalars. Select create no If-Match; existing assignment requires
   assignment_id+strong own assignment-revision If-Match, not session/source ETag.
   Required fields per action, native input/output revalidation, safe pagination/
   bounded projections where applicable; no unbounded child/profile/source echo.
3. Return truthful DATA-29 source/effective snapshot/objective/state/revisions/
   actor/timestamps, preparation/stale reasons authorized to scope and separate
   external outcome handoff status. Private participant data/notes protected; closed
   fixed errors, no raw provider/source diagnostic echoes, no Child mutation route.
   No production default app mounting or duplicate CMD-59/46/47 implementation.
4. Expose typed scoped catalog/recommendation and immutable assignment/outcome
   reference adapters for BE1/P4 consumption, not remote fetch from untrusted URL.
   Bounded retry/delivery policy and lease/ACK semantics explicit; no hidden scheduler,
   unlimited retries or exactly-once claim without adopted consumer dedup.
5. Prepare isolated actual SQL migration/rollback/reconnect/CAS/race/immutability/
   handoff ACK/outbox tests. Running/provisioning actual11 DB requires separate
   environment approval, not inherited10/09 authority.

## 6. P4 — full internal tests, acceptance audit and handoff

1. Discovery parity/full-topic/exact-age mapping tests; warnings vs execution;
   no readiness/history/material hard-filter additions. Catalog/12 source immutable
   hashes, published/recall/version and ranker/adaptation provenance tests.
2. Positive group adaptation ->confirm_ready ->start ->finish ->synthetic BE1 ACK,
   plus truthful skip/interrupt. All action-state pairs/invalid transitions;
   per-child mixed ages, unknown policy/profile/safety/preparation, stale source/
   audience/adaptation/review, hazards/recall, missing confirmations, Child/wrong
   session, CAS/concurrent commands, duplicate/conflicting key/body/revisions.
3. Atomic receipt/history/outcome rollback, lost ACK/restart/redelivery/foreign ACK/
   consumer unavailable. Group result not automatically copied to each child;
   missing reflection stays absent/NOT_OBSERVED as owner contract specifies, not a
   negative assessment. No automatic camera/mic/session completion/portfolio claim.
4. Source/node/JUnit-pinned one-batch local runner, own tests +relevant legacy
   catalog/preparation and08/09/10/12/14/foundation regressions; no skip-as-PASS.
   Ruff/Mypy/architecture/harness/security/diff and source unchanged before/after.
   SQL collection/mock evidence separate from actual PG and real owner effects.
5. Publish HTTP payload/errors, source/policy/preparation/BE1 consumer CR matrix,
   A1–A7 acceptance audit, reproducible own SQL and delayed runtime/owner conformance
   steps. Full11 DONE only after required actual adoption/evidence/owner acceptance.

## 7. Acceptance criteria

| ID | Required |
|---|---|
|A1|Authorized reviewed catalog/recommendation mapping, broad discovery not silently readiness/material-filtered; candidate reasons/provenance truthful|
|A2|Teacher local adaptation/group immutable effective snapshot/objective/source versions; never edits/publishes master catalog implicitly|
|A3|Every audience child exact-age/safety/preparation under approved policy, renewal after edits; hazard/unprepared/recall cannot start|
|A4|All six explicit actions/valid states/CAS/timestamps; no auto-start/resurrection/false group or individual completion|
|A5|Durable atomic own history/dedup/outcome intent +original authenticated consumer ACK/recovery, no fake BE1 save/reflection/portfolio or session advance|
|A6|Strict scoped injected CMD-45 and typed CMD-59 source provider, no competing BE1 endpoints/default auth/diagnostic/privacy leaks|
|A7|Source-pinned positive/negative/parity/race/immutability evidence, honest SQL/actual owner gaps and handoff; no fixtures-as-production acceptance|

## 8. Sequence and stop conditions

C0 plan; P1 mapping/contracts/domain; P2 current guards/lifecycle/handoff protocol;
P3 storage/HTTP/consumer adapter; P4 consolidated verification/audit/handoff.
After exact revision1 approval complete ALL internal P1–P4 continuously, meaningful
functional commits and grouped docs, no approval stop per function/checkpoint.
Missing actual owner wiring is already deferred, not permission to replace owners
or repeat unavailable-branch questions; material new policy/scope choice still stop.

Current PLANNING ONLY, implementation NOT_STARTED; present exact revision1 first.
CR11-01 reviewed activity definition/source mapping, CR11-02 per-child policy/safety/
preparation/adaptation-review, CR11-03 BE1 result ACK/CMD-59/session composition all
OPEN_CANDIDATE. No runtime/policy default inferred or new persistent goal created.
