# E05 — owned09 persistence component / prepared SQL verification

2026-10-18 Asia/Saigon, feature/be2-08-14, parent09a707b. Owner "tiếp" continues
approved revision1 P1–P4. Frozen plan SHA256 unchanged:
eca121bb1ce17943936bb68cbbbce62777f6a3867c5ef4cf70594ba9838d82e7.

## Delivered / boundaries

- Owned schema video_review: head, shared review/change receipt, history, playback,
  playback_history, event. No cross-owner FK or08/BE1/foundation/shared05 writes.
- JSON codec fixed type graph, exact fields/scalars/envelope, aware datetimes and
  domain constructors including strict shared record. No arbitrary object/class
  loading. Reads reject relational scope/revision/digest/state disagreement.
- ReviewRows write/change: expected before-head +CAS, exact deterministic domain
  transition, head/immutable history/receipt/minimal audit event in caller UoW.
  Receipt retains change before+archived+after, never copies approval on rebind.
  Initial revision explicit from authorized context, not inferred from08 run.
- Actor/key scope shared across review/change operation kinds, conflict not replay.
  Playback org/session/actor/key excludes video; changed target cannot reuse key.
  Intent-first pending1, exact original receipt terminal2, no terminal overwrite.
- SqlVideoReviewStore/SqlVideoPlaybackStore use PostgreSQL engine.begin and bound
  own session advisory lock, serializing first head insert as well as CAS. Caller
  must hold actual current authority before own store; no network under own UoW.
  Own advisory lock is NOT a BE1/source-owner revocation fence. No auto retries.
- SQL error aborts enclosing transaction; rows never commit/rollback independently.
  Candidate audit events contain identifiers/revision/digest, no reasons/script/
  audience/provider diagnostics. Event intent is not dispatch/delivery proof.
- New independent 20261018_vr_0001 migration, frozen literal DDL +append-only and
  transition triggers. Existing migration bytes untouched; env adds own metadata.
  No production mount, database connection or schema applied by this checkpoint.
  Raw DB constraints do not replace domain validation or current authorization.

## Verification actually run

-70 tests/unit/test_video_review_persistence.py PASS: JSON roundtrips of all root
  graphs and playback outcomes, corrupt nested/envelope/native values, relational
  mismatches, scoped SQL/CAS/unique-error handling, shared-kind conflicts, terminal
  preservation, caller UoW, PG-only engine, offline frozen upgrade/downgrade and
  six-table keys/no cross-owner FK. Mock SQL/offline only, NOT PostgreSQL proof.
- Initial focused test54 PASS/1 FAIL: fixture moved intent creation after receipt,
  so native receipt validation correctly rejected before SQL CAS. Fixed fixture to
  earlier creation time to exercise immutable-intent mismatch; final70 PASS.
-59-suite targeted regression2213 PASS,0 failed/errors/skips,15.157s, exit0:
  319 own09 (23 contract +61 domain +52 playback +53 write +60 lifecycle +70 store)
  +1894 existing08/policy/content/foundation tests. No actual integration claim.
- Command: existing backend venv pytest -q --disable-warnings --tb=short on unit/
  contract prefixes ai_policy_/learning_content_/knowledge_video_/video_review_/
  video_playback, plus test_ai_job_application, test_ai_job_q00_followups and
  test_ai_job_review_regressions; JUnit under ignored runtime path below.
- JUnit `.runtime/video-review/C3a-20261018/regression.xml`, SHA256
  62922e10311901b2403b6f35ee6881ad3d6d9640deef4d6c4625cf1870426afd.
-669 backend inventory files re-enumerated names/hashes before/after, unchanged=True.
  Sorted unique rg --files src tests alembic -g '*.py' +pyproject.toml/alembic.ini;
  UTF8 newline-joined sorted Windows relative path=UPPERCASE_FILE_SHA256 aggregate
  9f98f5f4baa8e82a629472120884d60f2a5263196237a54a87c3b536019d086b.
- Ruff all15 owned source modules +six own unit/contract suites +prepared SQL suite/
  new migration/env PASS; Mypy15 sources --follow-imports=silent PASS. Architecture/
  harness PASS; diff/security checked before checkpoint commit.

## Prepared only / next

10 actual PG17 cases in tests/integration/video_review/test_owned_sql.py collected
successfully, NOT_RUN. Covers migration exact tables, reconnect/scope/receipts,
rollback, first-write race, history/event/head trigger refusal, invalidate/rebind
archives and shared-key conflict, playback terminal persistence/raw overwrite.
No server/database provisioning, no auto dependency install, no provider effect.

Future run needs separately authorized disposable loopback database vr09_* (name
length>=12), driver postgresql+psycopg, PG17; explicit VR09_TEST_DATABASE_URL and
VR09_TEST_ALLOW_SCHEMA_DDL=1. Refuses existing schema. Fixture creates only own
schema and frozen downgrade removes exactly its own objects, no CASCADE. Never
echo secrets or reuse08 authorization. Skip is NOT PASS. Broader durable CAS/race/
restart/revocation acceptance remains pending actual runs and actual owner adoption.

Next internal work: P3 injected safe CMD-41/42 routes/HTTP tests, then P4 consolidated
acceptance/handoff/delayed batch steps. Actual canonical head/source authority and
BE1 current session/access/fetch/range/resume bridge adoption CR09-01/02 OPEN.
Own storage availability does not close those gates. Full09 remains IN_PROGRESS.
