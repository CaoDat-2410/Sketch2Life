# C2b — owned HTTP/storage participant, NOT integrated runtime

2026-10-18; parent9292bad; approved revision1 unchanged.

## CMD-40 edge

- Candidate POST `/api/collaboration/v1/knowledge-videos`,202 DATA-27 snapshot and
  meta.outcome created/replayed/deduplicated. Not registered in production app.
- Composition must inject VideoCreateService, verified VideoIdentity resolver and
  explicit max_body_bytes. Resolver owns authenticated principal/org/authorized
  target session; no client org/session/role headers are treated as authority.
  Exact target-session transport/adoption remains D02, no default selected here.
- Exactly one valid Idempotency-Key required; generated correlation ID; no-store.
  JSON only; bytes counted from stream, not trusted Content-Length. Duplicate
  JSON keys/nonfinite/malformed/extra/secret/legacy shortcut fields rejected.
- Submission adapter supplies full KnowledgeVideoView snapshot, including actual
  attempt metadata. Service revalidates/binds it inside current creation lease,
  and normalizes to native closed DTO before outer serialization. No guessed
  history/current job state, no projection =>503. Snapshot is not later playback
  authority and no endpoint/player URL is exposed.
- Unknown dependency exceptions/messages become generic503, not raw error text.
  Identity and owner bindings in HTTP tests are explicitly synthetic fixtures.

## Owned rows / migration

- Application VideoRunParticipant and VideoCommandReceipt; infrastructure
  VideoRunRows accepts an existing PostgreSQL Connection plus fixed server org.
- Caller MUST already be in a transaction. Adapter never begins/commits/rolls
  back, creates foundation jobs or calls providers. It is NOT AtomicVideoSubmission.
- Frozen own branch `20261018_kv_0001` (`knowledge_video@head`), down_revision None,
  two tables: run/receipt. No cross-owner FK; independent Alembic env metadata
  registration added without modifying existing published migrations.
- Scope/CAS, immutable pin/video version/review revision/job/created time,
  artifact immutability and terminal no-resurrection checks. Receipts bind exact
  org/session/principal/key/body/pin/run. Native codec validates field shapes,
  domain invariants and relational/envelope correspondence before returning rows.
- Uniqueness conflicts abort enclosing transaction; caller must roll back whole
  participant/foundation work before recovery. There is no silent upsert/rewrite.
- Actual foundation authorized same-transaction bridge still CR08-01. Do NOT
  attach rows after AiJobService.create_job commits or call pure create_job from
  production code to bypass foundation guards. Fixture job maps are intents only.

## Verification and next work

256 own local cases (143 C1 +21 create +46 HTTP +46 persistence/codec mocks).
Broad local pack1691 PASS: own256 +1435 existing policy/content/foundation cases.
Ruff/Mypy11 source files PASS. Mock SQL/compiler tests are not actual PostgreSQL.

Prepared actual SQL pack11 collected, NOT_RUN:
`backend/tests/integration/knowledge_video/test_run_rows_sql.py`.
It never provisions PostgreSQL. Requires separately approved PG17 environment,
explicit KV08_TEST_ALLOW_SCHEMA_DDL=1 and private KV08_TEST_DATABASE_URL pointing
to a new dedicated loopback kv08_* database. Refuses existing owned schema;
fixture creates/downgrades only its exact own schema/tables, no CASCADE. No secret
URL in tracked examples. No opt-in or runtime actions taken in this checkpoint.

P2 still partial: explicit library/generator/media-validation strategy surfaces
and use cases outstanding; actual atomic bridge adoption/SQL evidence open.
P3 worker/finalization/provider hooks and P4 consolidated runner/handoff remain.
P5 provider/profile/provisioning/actual generation remains separately gated. No
BE2-07/BE1/P4 authority adoption or full-card completion inferred.
