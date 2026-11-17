# E02 — playback intent and guarded start/recovery component

2026-10-18 Asia/Saigon; parent aa10fe5, feature/be2-08-14. Approved revision1
unchanged SHA256eca121bb1ce17943936bb68cbbbce62777f6a3867c5ef4cf70594ba9838d82e7.

## Delivered / API meanings

- Pure PlaybackRequest/Intent/Receipt/State: exact internal resolved09 ReviewSubject,
  review ID/revision, expected_session_revision, principal/scoped idempotency key,
  created_at, own revision/state and exact immutable receipt. No new client HTTP
  schema or requirement for client-supplied authority/subject is introduced.
- Request digest binds subject (org/video/version/final artifact/pin/context/
  audience/consent/policy), exact review and expected session revision. Operation
  key binds org/session/principal/client key, body is separate; same key changed
  body conflicts, no second operation. Timestamp/progress not part of key.
- Intent PENDING revision1 ->PLAYING/REJECTED revision2 only with matching native
  revalidated authoritative receipt. Accepted receipt binds original key/body/
  principal/session-before and advances session revision; rejected keeps expected
  revision. Historical PLAYING is NOT proof a player is still playing now, nor
  current access authority. Identical receipt replay no-op; different receipt
  cannot overwrite terminal history. No URL/capability/grant TTL selected.
- Candidate PlaybackBoundary/Access/Store/Transaction/Bridge ports; actual
  implementations absent. Actual current Teacher/session/grant/consent/moderation/
  recall/source/review/policy/deadline held guards required; native booleans alone
  are never claimed as actual cross-owner authentication or effect fencing.
- VideoPlaybackService: read scoped original intent; compatible replay authenticates
  original recovery scope and only queries receipt, never reruns start. New intent
  requires current effective exact head then authorization before/after insert
  under same own transaction; dispatch check and external start OUTSIDE own DB tx.
  CAS receipt/history recording separately, with explicit recoverable-intent
  semantics, NOT two commits called atomic. Actual BE1 bridge must atomically bind
  session/access effect +receipt/current session CAS and durable external dedup.
- Missing/outage/timeout/malformed foreign receipt or post-effect storage/guard
  uncertainty stays Pending, no hidden retry/fallback/rollback/cancel claim. Lost
  insert ACK after commit also never guesses a second dispatch. Known absent
  receipt stays pending: actual authorized reconciliation/scheduler must handle
  never-sent intents; request service does not manufacture retry permission.
- Outcome confirmed/rejected is historical receipt reference only, no mediated
  access ref/current-state/URL. Actual gateway must check current fetch/range/resume
  on each use. Historical recovery after revocation does not resurrect review.

## Remaining adopters / implementation

CR09-01 canonical head/projection and CR09-02 actual BE1 session/access receipt,
current invalidation/use fences and atomic expected-session handling OPEN. Distinct
keys with same expected_session_revision must race through actual session CAS,
not duplicated effects. MEMORY tests do not establish that actual race guarantee.
Actual owner guards must prevent effect between revocation/deadline/current-review
change and dispatch, not simply repeat stale prechecks. Actual store requires
scoped unique key/body, CAS/rollback +intent/history/audit/outbox consistency;
concurrent insert loser recover after rollback, no re-dispatch from failed insert.

P1 intent/result terms and P2 playback composition available at component level.
P2 review-write/current target/application integration still next; P3 own durable
adapter/forward migration/HTTP and P4 source-pinned runner/audit remain. Shared24,
08/BE1/foundation tables/contracts/migrations unchanged. No production route/default
auth/provider/DB/runtime/Lightning calls. Full09 IN_PROGRESS, not DONE.

## Verification

- 52 new tests/unit/test_video_playback.py; cumulative136 own with prior84 review
  tests. Transactional MEMORY/ASSUMED guards + synthetic bridge only. Covers exact
  intent-before-effect/outside-DB order, invalidated/rejected/mismatched head,
  teacher/consent phase denial, same-key conflict, lost insert/start/receipt ACK,
  no resend on unknown/absent proof, wrong/forged native receipts, late/foreign
  response binding, rejected immutable result, rollback and guard-exit uncertainty.
- Initial collection failed due missing future annotations on self-return type;
  corrected import before execution. Initial41 playback passed, added11 adverse
  cases then52 PASS. No skipped/suppressed tests or provider fake PASS claims.
- Final broad56 unit/contract files matching ai_policy_/learning_content_/
  knowledge_video_/video_review_/video_playback plus existing3 foundation suites:
  2030 PASS,0 failures/errors/skips,15.595s, exit0.136 own +1894 regression cases.
  Existing backend venv pytest -q --disable-warnings --tb=short --junitxml=...
- Ignored receipt `.runtime/video-review/C1b-20261018/regression.xml`, SHA256
  d139473fb7487d0185910cb7f839889afd399b3fe0d263fd03c994b67c984d85.
- 655 backend inventory files (sorted unique rg --files src tests alembic -g '*.py'
  plus pyproject.toml/alembic.ini), names/hash map re-enumerated before/after,
  unchanged=True. Aggregate SHA256 UTF8 newline-joined sorted Windows relative
  path=UPPERCASE_FILE_SHA256 lines:
  12b0d7937f7717df91eebf2fa4fc5fd994538d811c48027ed3721a4729801587.
- Ruff6 owned source modules +three own suites PASS; Mypy6 sources with
  --follow-imports=silent PASS. Architecture/harness/diff PASS; security before
  commit. Feature docs updated together after tests, not in backend inventory.
