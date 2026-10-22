# BE2-07 → BE2-01 → BE2-08 persisted flow handoff

Date: 2026-10-22 (Asia/Saigon)  
Disposition: **DRAFT / NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION**

This is a factual handoff of the bounded BE2 persisted-video seam and its test evidence. It gives BE1 visibility into what now works and what remains gated. It is not a request for BE1 to integrate against this candidate, not an implementation approval, and it has not been sent to anyone.

## Candidate and approved boundary

- Worktree branch: `feature/be2-backend-ai-integration`
- Candidate HEAD: `1649b72978877d82b4d7662040ff3555dee0a3a7`
- Approved FEAT-057 scope: `plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_REV2_DRAFT_20261022.md`
- Scope SHA256: `1C199CF6CD1E7C2F2D5981D253256278079D840197CB1B05D304E2620FD2E90D`
- Adopted boundary contract: `BE2-VIDEO-LIFECYCLE/1`, limited to A (submit), S (start), B (accepted finalization), and identity failure as specified by the hash-pinned scope.
- Exact approval manifests were verified before implementation: FEAT-044 7/7 paths, FEAT-050 14/14 paths, FEAT-057 1/1 path. FEAT-057's added path is `backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py`.

The scope excludes BE2-09, BE2-14, D4/budget work, BE1 implementation, schema/migration changes, and the durable BE2-07 source fence. It permits only a dedicated test-created loopback PostgreSQL 17 database with synthetic data and already-approved migrations.

## What the flow does

1. **BE2-07 producer:** the integration fixture creates a synthetic knowledge bundle through the real `KnowledgeBundleService`, resolves its exact export, and checks the exported bundle hash plus source lineage against the video pin.
2. **BE2-01 submission and dispatch:** the real AI-job service persists the job, dispatch intent, and BE2-08 video run/receipt through boundary A. The existing typed dispatcher forwards the original `WorkerDispatchEnvelope`; the envelope shape is unchanged.
3. **BE2-08 start:** the configured real `VideoWorker` calls the foundation-backed admission. BE2-01 owns the SQL unit of work and commits the job/run start together; the BE2-08 participant mutates only its own rows and does not begin, commit, or roll back the unit of work.
4. **BE2-08 work and BE2-01 finalization:** the real worker pipeline consumes the exact persisted pin using synthetic generator/media/staging ports. The foundation finalizer commits the accepted BE2-01 job/result/receipt and BE2-08 run/artifact/receipt in one B transaction. A new repository read verifies their identities and the authoritative receipt.
5. **Failure/replay checks:** the fixture checks duplicate delivery, mismatched job ID, attempt ID and request pin, staged pin/hash mismatch, and injected participant failures at A/S/B. Failure injection leaves no split job/run state or fabricated successful receipt.

The real BE2-07 bundle service, BE2-01 SQL repository/dispatcher, BE2-08 admission/finalizer, and `VideoWorker` are exercised. The generator, external artifact storage, and queue transport are synthetic/offline fixtures. No provider is called.

## Test environment and result

The final integration run used Python 3.12.10 and local PostgreSQL 17.11 on loopback. The test created a new random `be2_xlane_...` database per case, applied only the two existing approved migrations, and dropped each database in fixture cleanup. A post-run query found no leftover test databases.

`backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py` passed **9/9**: 0 failures, 0 errors, 0 skipped. The earlier 325 focused unit/contract tests also passed in the implementation checkpoint. Initial database runs exposed test-fixture assertion mistakes (staging key versus completion key and aggregation of dispatch/audit outbox rows); those assertions were corrected, and job/attempt mismatch cases were added. No production-source fix was needed during the PostgreSQL verification.

Final evidence:

- [PostgreSQL 17 test receipt](BE2_01_07_08_POSTGRESQL17_FLOW_TEST_20261022.md)
- [Machine-readable metrics and hashes](../metrics/BE2_01_07_08_POSTGRESQL17_FLOW_TEST_20261022.json)
- [Final pytest log](../raw/be2-video-lifecycle-20261022/postgres17-integration-final2.log)
- [Final JUnit XML](../raw/be2-video-lifecycle-20261022/postgres17-integration-final2.xml)

Harness, repository-security, architecture, skeleton, and `git diff --check` validations passed. Nothing was staged, committed, pushed, merged, or sent externally.

## What this proves—and what it does not

The approved persisted A/S/B seam now has passing P01–P07 evidence for this bounded scope: exact producer-to-consumer pin lineage, persisted paired job/run lifecycle, unchanged-envelope dispatch, accepted authoritative receipt, replay/mismatch behavior, participant rollback, and isolated PostgreSQL evidence.

This does **not** prove the durable BE2-07 source fence remains valid through BE2-08 finalization. The current source-currentness coordination is process-local and the approved seam scope explicitly left the durable fence separate. Therefore:

- X01 remains `PARTIAL`.
- X09-08 remains `NOT_IMPLEMENTED` in the cross-lane edge registry; this approved A/S/B persistence test is bounded evidence and does not change the registry's edge status.
- X05d remains `BLOCKED`; X05c/CR09-02 remain `OPEN`.
- FEAT-057 and the full BE2-01–14 graph are not complete.
- BE1 handoff remains `NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION`.

## Gate before an implementation handoff

Prepare and approve an exact owner-card scope/manifest for a durable BE2-07 source fence that is held or revalidated through the BE2-08 finalization commit. Its tests must cover source invalidation/races and prove that stale source cannot produce an accepted final artifact. After that implementation and evidence pass, update X01 and this handoff. Until then, BE1 may use this document as a status/evidence review only and should not treat the seam as ready to integrate.

The broader X05c/X05d, BE2-09, BE2-14, D4, and remaining BE1-owned adoption work stay outside this narrow handoff and require their own decisions and approvals.
