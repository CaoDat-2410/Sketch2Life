# BE2-10 receiver handoff / later verification

2026-10-19, feature/be2-08-14, approved revision1 SHA256
8d0162c6f78b019406910927952c3d85b435a81d50de80874b023fa3a9cfb420.
Internal implementation/local verification complete; full10 acceptance pending.
See HTTP_CONTRACT_HANDOFF.md (payloads/errors/effect protocol), ACCEPTANCE_AUDIT.md
(A1–A7 and real remaining gaps), DEPENDENCY_REGISTER.md (owners/CRs).

## Code delivered

domain/video_failure: exact FailureTarget/Choice/Context, RetryAuthorization,
NewLifecycle/EffectReceipt/Intent and scoped body/key/claim digests. Domain has no
framework/storage/provider imports. application/ports/video_failure and
application/video_failure: held-authority guards, exact failure and current retry
authorization, intent-first decide, authenticated execute/lookup receipt recovery.

infrastructure/video_failure: strict closed JSON graph codec +PostgreSQL rows/store,
own schema intent/history/event; immutable history, pending1->receipt2 only, scoped
unique actor key and unique FAILED LIFECYCLE CLAIM across actor/action/key/revisions.
Single UoW append/CAS, advisory own-session lock, no cross-owner SQL/FK. New frozen
20261019_vf_0001 migration +own metadata in existing env. No published migration edits.

contracts/schemas/video_failure and interfaces/http/routers/video_failure: strict
DATA-28/CMD-43 candidate using existing09 transport-only primitives. Explicit server
identity and size configuration, run If-Match independent of review/job/session.
Missing actual service503; not registered in production app. End checkpoint required,
retry consumption+new lifecycle required, unknown effect202 not fake confirmed.

## One local command

From repo root, existing backend interpreter, no installation/provisioning:

```powershell
backend/.venv/Scripts/python.exe features/FEAT-052-be2-video-failure-disposition/src/run_component_checks.py
```

Linux equivalent backend/.venv/bin/python. Exact pins in src/TEST_INVENTORY.json.
253 owned +2352 regressions PASS;14 own SQL collected only. Runner strips all
*_TEST_ALLOW_SCHEMA_DDL/*_TEST_DATABASE_URL subprocess opt-ins and NEVER executes
SQL. Existing fixture helpers reused, no nested runner main. Exact test names/JUnit,
approved plan, source closure unchanged and all checks must pass; no skips/duplicate/
missing/extra/nonzero accepted. Output ignored .runtime/video-failure-component/UTC-run
has summary/source map/collection logs/JUnit/hashes/quality checks; sanitized metrics
and evidence note tracked. Status always LOCAL_COMPONENT_ONLY/full_card_complete=false.

Do not update pins just to hide failure. Review legitimate node additions and rerun
against unchanged source. Source map includes transitive backend and all feature
runner helpers/manifests +own frozen plan/approval; mutable evidence prose excluded.

## Actual own SQL — separately authorized environment only

Prepared14 tests/integration/video_failure/test_owned_sql.py cases cover frozen3
tables, all three pending->receipt paths and reconnect/scope, full intent/claim/
history/event rollback, cross-actor competing action claim race, immutable history/
event UPDATE/DELETE, terminal overwrite/delete denial, duplicate claim abort,
original claim mutation guard, receipt settlement rollback. Collection NOT PASS.

After explicit10 environment approval, use NEW dedicated disposable loopback PG17
vf10_* database (length>=12), driver postgresql+psycopg. Secrets only runtime private
environment VF10_TEST_DATABASE_URL +VF10_TEST_ALLOW_SCHEMA_DDL=1; never print value/
credentials/argv. No inherited09 approval. Fixture refuses existing schema; creates
only own video_failure schema and frozen downgrade removes exact objects, no CASCADE.
No server/database auto-start from tests or local runner.

Collect exact14 nodes/approved pins +source before, run with existing interpreter
in backend using -m pytest -o addopts= tests/integration/video_failure/test_owned_sql.py
--junitxml=<ignored-own-runtime>/junit.xml. Re-enumerate source after; same strict
classifier used by local pack must see0 fail/error/skip, exact nodes and unchanged
source before OWN10_SQL_PASS. Preserve failures; fix scoped defects, no weakening/
count-only acceptance. Actual disposable setup/stop/cleanup planned only on approval.

## Actual owner adoption matrix

| Gate | Owner / concrete requirement |
|---|---|
|CR10-01 failed/new lifecycle|01/08/P4 authenticates final failed history/attempt/policy/current pin; maps retry to new video+job lifecycle. Existing08 run_one_semantic prevents plain same-pin create; needs adopted retry-aware dedup/forward evolution, not fake pin change/terminal reset|
|CR10-03 bounded retry|14/current budget +01/08 atomically dedup/consume exact auth reference+budget revision with new-run submission; check current expiry/kill/purpose/rights, no free-text grant, no unbounded loop|
|CR10-02 session|BE1/P4 authenticates Teacher explicit action and expected_session_revision, permitted skip destination; end receipt must prove early outcome+checkpoint; no local guessed stage/revision or sequential commits sold atomic|
|Current authority|BE1/07/08/14 holds actual current source/context/audience/consent/session fences through own commit/effect; acquire owner guards before own store; no network in own UoW|
|Recovery|Original actor/org/session/key/body/failure/disposition binding; late/foreign/partial receipts, lookup absence/outage and restart. Pending claim reserved; safe explicit reconciliation/proven no-effect required before release/new decision|
|Late result|01/08/session ingress rejects old terminal completion after skip/end/retry; no reversal/copied approval/playback. Synthetic08 domain check not real gateway proof|

Actual execute outside10 DB transaction. Retry receipt NewLifecycle is initial queued/
pending_media snapshot, not fabricated current player/job state. Same content version
retained; editing content elsewhere changes version/review instead. Skip/end receipt
video_run_revision stays original failed run; retry result returns NEW run revision.
Confirmed replay is historical receipt only, current authority must still gate any
NEW action/access. Late guards denying dispatch do not silently free pending claim.

## Combined later runtime batch

Use prior08/09/12/14 actual SQL receipts only for their own proven scope. Select/
approve actual environment/provider/model/profile/license/budget before Lightning;
no Wan/L4/TTS/voice/duration defaults inferred from old demos. Run failed08 actual
lifecycle ->each explicit10 action ->actual01/BE1/14 receipts, reviewed-library or
selected generator inputs as applicable;10 needs no actual Sketch generation.
Negatives: queued/running/retryable, Child/wrong scope, stale versions/If-Match,
budget denied/stop/expiry, concurrent different actor/action, lost insert/effect/ACK,
unknown lookup/partial checkpoint/foreign receipt, actual restart, late old completion.
Count real effect/consumption/transition once; preserve old failure/policy/reason,
compare actual before/after states and checkpoint. Sanitize receipts/logs; never
commit secrets/media. Full10 closure requires own SQL+actual adopted owner proof/
consumer acceptance, not just one successful Lightning invocation.
