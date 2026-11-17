# BE2-09 — Final video review và authorized playback

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED

- Date:2026-10-18 Asia/Saigon
- Branch: feature/be2-08-14
- Planning baseline:07159ce
- Owner: receiver BE2-08–14; shared DATA-24 owner BE2-05, session/access authority BE1.

## 1. Goal / sources

Implement CMD-41/42: Teacher review exact final video và explicit authorized
playback; ready/rendered/library-published không tự approve/play. Reuse shared
DATA-24 candidate session_content; DATA-27 review/playback extension owned09.

Sources: canonical FEAT-029 artifacts/Sketch2Life_Master_SRS.md v3.1,
FR035/036/040, UC-024, DATA-24/27, CMD-41/42, AT-CS-010; FEAT-040
TEAM_TASK_BREAKDOWN card BE2-09; FEAT-044 BE2_08_14_TEAMMATE_HANDOFF.md,
BE2_ROADMAP/BE2_EXECUTION_TRACKER; ADR-0015/0018; FEAT-050 current08 handoffs.
FR040 script/TTS refinement remains PROPOSED: no mandatory pre-render approval,
selected model/voice/duration or new script editing product workflow inferred.

Owner approved proceeding to next-card planning and batching later Lightning
tests. This does not close08 actual-runtime/adoption gates or approve this
not-yet-presented revision's implementation. Exact revision1 approval required.

## 2. Scope / stop boundaries

- Pure review/playback rules, strict own commands/projections around shared24,
  application guards/ports/services, own durable rows/forward migration, injected
  thin HTTP routes, explicit component fixtures and source-pinned verification.
- No duplicated/forked DATA-24, real Sketch dependency, player/frontend, permanent
  bucket/provider URLs, credentials, storage gateway reimplementation or direct
  writes to BE1/foundation/08-owned tables. No automatic session advance.
- Real BE1/P4 composition stays teammate-deferred. Own adapters/tests/handoff are
  implemented, actual adopters tracked OPEN; fixture success not integration proof.
- Editing source/script/audio/media creates a new version via07/08 owner flow,
  invalidates old applicability and requires re-render/re-review as applicable;
 09 does not mutate approved bytes or implement07/render engines itself.
- No provider/model/packages/GPU/Lightning activation. Prepare shared final batch
  requirements; current actual08 SQL evidence does not provision09 test DB.

## 3. P1 — exact review contract/domain and dependencies

1. Reuse ExactContentReviewCommandV1/RecordV1; native revalidation + owned09
   refinement requires target_kind knowledge_video, session_content/teaching_delivery,
   matching authorized session and audience subset. Reject/request_changes require
   reason; generic publication review never becomes session approval.
2. Bind exact video_id/video_version/final artifact bytes hash and immutable
   artifact ref plus source/bundle/script/context/audience/policy lineage. Distinguish
   media hash from pin digest/catalog hash; no substituted hash namespaces.
3. Independent content version, render/job/run revision, review head/CAS and
   session/playback revisions. CMD-41 If-Match is canonical video_review_revision,
   not job/run/session revision. Strict idempotency/replay/current eligibility.
4. Pure approve/reject/request_changes/invalidate and playback intent/result
   transitions; no acceptance solely from native allowed/effective booleans.
5. Inventory current08/BE1/shared contracts; record CR09-01 canonical review head/
   combined DATA-27 projection and CR09-02 session/access atomicity/receipt semantics.
  08 row participant freezes review_revision: do not silently rewrite08 rows or
   change its published migration to work around that. Adoption required.

## 4. P2 — guarded review/start/access composition

1. Resolve ready final08 artifact/current lineage through scoped authoritative
   read port, current moderation/usage/publication/recall/rights/content/profile
   eligibility. Apply purpose/classification-specific consent; do not fabricate
   child consent for unrelated generic content.
2. Verify Teacher action-specific current principal/org/session/grant/audience,
   source/context and policy fences held through own transaction. Child cannot
   review/start. Conflicts/replays recheck current authority, no role-only bypass.
3. CMD-41 persists exact shared review + independent own head/history/idempotency/
   audit/outbox consistently. Invalidation preserves history and stale reason;
   old approval cannot authorize changed content/audience/context or revoked use.
4. CMD-42 requires explicit Teacher start, exact effective review/target/audience
   and expected_session_revision. Additional playback CAS fields remain candidate
   definitions with trace/tests, not invented shared requirements. Persist original
   scoped play intent/key before external access/session work, outside DB tx.
5. Adopted BE1 session/access port returns exact authoritative receipt. Pending/
   timeout/lost ACK stays pending and recovers original intent, never guessed
   playing/rollback/new side effect. Receipt must bind original target/review/
   audience/session outcome; no sequential commits marketed atomic.
6. Mediated access metadata only after current gate. Fetch/range/resume/old-reference
   use must be rechecked by actual BE1 access gateway; start-time check or stale
   URL alone insufficient. No token TTL/config default selected by09. Missing
   adopted authority/bridge =>closed unavailable/pending, not public media grant.

## 5. P3 — own persistence and CMD-41/42 HTTP

1. Own review/history/head/playback-intent/receipt rows with exact scope, CAS,
   dedup and provenance; new forward migration only. No cross-owner foreign keys
   or direct08/BE1/foundation SQL; actual combined09 head adoption stays CR09-01.
2. Routes POST /knowledge-videos/{video_id}/reviews and /playback consume verified
   server identity/session, explicit body limits/idempotency and correct revision
   preconditions; do not mount production default auth/routes. Shared review DTO
   reused, own playback request/projection field reasons documented.
3. Closed safe responses/errors, no source/script/child/provider diagnostic echoes
   or permanent/raw storage URL. Review approval and play receipt separate axes.
4. Prepare own SQL migration/rollback/scope/idempotency/CAS/race/immutability tests.
   Actual SQL runs only on separately approved isolated test environment; never
   reuse08 permission automatically or claim fixture locks are durable fences.

## 6. P4 — verification, acceptance and delayed runtime handoff

1. Source/node-pinned local runner: own unit/contract/application/HTTP/row tests,
  08/12/14/foundation targeted regression, Ruff/Mypy/architecture/harness/security.
   Source before/after, exact JUnit identities, no skipped-as-PASS or invented count.
2. Positive: reviewed-library fixture with exact ready artifact ->Teacher session
   approval ->explicit start ->adopted-receipt fixture; no real Sketch/generation
   dependency. Clearly ASSUMED_CONTRACT, not actual BE1/provider proof.
3. Negatives: wrong target/media hash/version/script/context/audience/consent,
   missing moderation, recall/revoke/current grant, child/generic review reuse,
   stale review/run/job/session ETag mix-ups, replay/conflicting key, concurrent
   invalidation/start, late/foreign/malformed receipt, lost ACK and old access refs.
4. Publish payload/errors, owner/CR matrix, acceptance audit and batch conformance
   steps for actual BE1 access/session adapters and eventual08 generated artifacts.
   Local fixtures/own SQL evidence separate from integrated playback evidence.
5. Track deferred work08+09 in final batch, not one unchecked success call. Provider/
   GPU/profile/license/budget selection and environment approval before Lightning.
   Full09 DONE requires actual adopted review/access/session/revocation conformance,
   not waiting for Lightning alone or counting postponed integration as waived.

## 7. Acceptance criteria

| ID | Required |
|---|---|
| A1 | Shared DATA-24 reused; exact final version/hash/source/audience bound; no generic publication shortcut |
| A2 | Only authorized Teacher/current moderation/context/purpose/consent/grant can review; independent revision CAS/dedup/history |
| A3 | Explicit start after effective session review; exact session/audience; no auto-play from ready/render/library publish |
| A4 | Edit/context/audience/recall/revoke invalidates applicability; old reference/fetch/range/resume cannot bypass actual current gateway |
| A5 | Durable own review/play intent/receipt and authorized cross-owner protocol; races/lost ACK/restart/replay do not duplicate or fake playing |
| A6 | Thin safe HTTP/projection, no raw URL/credentials/diagnostics, missing actual adapters fail closed |
| A7 | Source-pinned local/actual SQL/integrated batch evidence separated, open owner CRs explicit; full completion only with actual required adoption |

## 8. Risks / checkpoints / authorization

CR09-01/02 may prevent durable combined projection/start, not pure/fixture work.
Never resolve them with direct SQL or permissive gateway. Existing08 domain/codec
invariants and shared24 migration/schema remain untouched without coordinated CR.

Checkpoints: C0 plan; C1 P1; C2 guarded P2; C3 storage/HTTP; C4 consolidated audit.
One functional checkpoint may span several focused test/fix commits, not one
commit per function. Docs updated together after meaningful test checkpoints.
C0 planning commit under current routing approval; implementation commits only
after exact revision1 approval. No push/merge/deploy. No new broad goal,
provider configuration/SQL provisioning or BE1/P4 implementation authority inferred.

Implementation blocked until exact revision1 approval recorded separately.
