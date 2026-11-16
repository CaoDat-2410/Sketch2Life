# T7b same-transaction BE1 owner fence — GA2

Status: **XONG-CHƯA REVIEW**, synthetic-only implementation evidence. No co-owner signature or independent acceptance is recorded by this report.

## Authority

- V4 SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; GOAL A2 REV2 SHA-256 `47CEA408AA9A4984C2EFD9E71A2EF0CDB2DF02C46E56FD7281086EBAE574AE10`.
- Approved plan: `plan/T7B_OWNER_FENCE_UOW_PLAN_GA2_20261102.md`; SHA-256 `FDA943CE81C207F51616032A05AC1FB976934178A019BDCEF95DA73478A40C46`. Approval was appended before source changes. It and the frozen plan remain unchanged.
- Branch/HEAD remain `feature/feat063-be-foundation` / `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`; index empty. Baseline is the post-A1 GA2 launch snapshot, not an older HEAD/hash list.

## Behavior and layer acceptance

| Layer | Evidence |
| --- | --- |
| L1 contract consumption | `build_owner_fence(facts)` serializes a strict canonical `be1-resolved-facts-owner-fence-v1` scope, including owner identity, source, target, audience, proof refs and the full resolved-facts digest. Malformed/unknown/missing/duplicate/cross-org input is stale. |
| L2 acceptance boundary | `owner_fence_factory(resolver)(connection)` implements the existing candidate `OwnerFenceV1` protocol without changing the AI Jobs port or repository. Unknown or failed facts never become current. |
| L3 locking | Requires an active PostgreSQL transaction; sets transaction-local `lock_timeout` (default 1000 ms, accepted range 1–5000 ms). Locks existing session/canvas aggregate revisions, session, group, audience memberships, profiles and proofs with `FOR SHARE` in sorted table/PK order. No connection, transaction or commit is opened by the adapter. |
| L4 freshness | Calls the injected resolver with the exact supplied connection after locking. Compares the full canonical scope/digest and the 31-bit epoch from the existing `context_revision` helper. Unit test forces an integer epoch collision and still obtains stale from differing full digests. |
| L6 UI | DEFERRED-BY-OWNER. |
| L7 concurrency | Real PG writer cannot UPDATE a locked profile until fence transaction release; observer verifies `pg_blocking_pids`, rather than relying on sleep ordering. It then completes and the original fence becomes stale. |
| L7 phantom/timeout | While existing rows are held, a new synthetic membership INSERT succeeds under a 500 ms lock timeout. Rechecking the old fence sees changed full-roster/context digest and returns stale. A separate real PG test holds a conflicting profile lock; fence's 100 ms lock timeout returns stale. |

`FOR SHARE` does not prevent membership INSERTs after a successful `hold()` returns. The test establishes that an insertion present before the subsequent check is detected, and does not claim serializable exclusion after that point. Locks end with the accepting transaction and must never be held across provider work.

## Actual verification

- T7b focused unit matrix: **21 passed**. Cases cover canonical encoding, unknown versions/scope, exact connection, lock order, required rows, duplicate/cross-org fences, changed digest with collided integer epoch, transaction/read/resolver failure, lock timeout bounds and synthetic eligibility scope.
- Combined final GA2 offline suite: **396 passed, 0 failed, 0 skipped**, exit 0. New A2 unit modules contain **50 tests** (23 source, 6 digest/profile, 21 fence). Existing assistance and Sketch-chain tests are included unchanged. Exact file list/arguments/output are in the final snapshot.
- Final entire `tests/integration/test_be1_synthetic_pilot_postgres.py`: **68 passed, 0 failed, 0 skipped in 81.61s**, exit 0. This includes **12 new GA2 PG cases** (valid scoped facts/source/context, eight invalid-fact variants, UPDATE blocking, phantom membership digest and actual lock timeout) and all 56 pre-existing cases.
- Earlier focused PG checkpoint: 11 passed / 56 deselected before the final timeout case was added. Earlier entire-module checkpoint: 67 passed. These counts are distinct runs, not summed as unique cases.
- T12 safety gate: connection file read only by the authorized local procedure; database name/host/query checks and connection checks succeeded. All **108** visible user tables belong to repository metadata plus `alembic_version`; no unknown tables. No schema or migration was applied. All writes are isolated synthetic test rows cleaned by the existing fixture; no DROP/TRUNCATE or unrelated row deletion.
- Ruff check/format, source mypy and repository validators are logged in the final GA2 snapshot. Source mypy on 11 affected files succeeds; including the existing harness reports one old protocol error, also reproduced from its HEAD bytes. Zero new mypy errors; no suppression or AI Jobs change was introduced to hide it.

The T7b unit tests were added with implementation in the delegated subtask; an independently captured original red count is unavailable. It is not described as a completed red-green cycle. T2C's earlier red regression and runner corrections are recorded in `T2C_IMPLEMENTATION_REPORT_GA2_20261102.md`.

## Scope and delivery limits

Only `infrastructure/assistance/owner_fence.py`, its new focused unit test, GA2 additions to the existing synthetic PG module and task records implement T7b. No `ai_jobs` source/table/contract, migration, route, composition or provider code was edited. The PG test uses real BE1 owner/source adapters with the existing in-memory assistance request repository; durable pilot composition is a later goal. No Modal/GPU/provider/external call, Alembic, real-child data, stage, commit or push occurred.

Seven protected file prefixes remain unchanged: SOURCE_REGISTER `0B43E4BA`; FEAT-063 CONTEXT `E7C8143A`; STATUS `F1ADB793`; REMAINING_AI `8BBFD0ED`; REV36_DELTA `B61B0607`; VIDEO_FLOW `93374E96`; S1_DECISION_CARD `4D95D303`.

T7b code is **XONG-CHƯA REVIEW**. GOAL A2 overall is **TẠM DỪNG** at the exact-path scope gate documented in the T2C report: the existing A2 fake-owner keyword change was omitted from its frozen plan. Do not treat the passing tests as closing that approval gap. Independent review is still required; this report does not start the next goal or authorize a live call.

## Owner scope decision — subsequent update

The owner approved the narrow fake-owner scope described in the T2C supplementary approval, pinning addendum `E04F41D3F765C24DDB1E59A36ED2E24A0287A40AD8CC5FF1215B054287E15857`. This resolves the overall scope hold above. All 16 GA2 source/test files match the test snapshot; previously recorded 396 offline / 68 PostgreSQL results remain applicable. No runtime test was rerun for this documentation-only change. **GOAL A2 XONG-CHƯA REVIEW**; an independent review is still required.
