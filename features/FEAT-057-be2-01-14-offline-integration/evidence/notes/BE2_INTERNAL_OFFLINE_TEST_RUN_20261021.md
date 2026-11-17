# BE2 internal offline test run — 2026-10-21

## Scope and result

- Purpose: measure the currently implemented offline seams between BE2-01–07 and BE2-08–14. This is a bounded regression run, not proof that the complete cross-lane graph is integrated.
- Worktree branch: feature/be2-backend-ai-integration.
- HEAD: 1649b72978877d82b4d7662040ff3555dee0a3a7.
- Python: 3.12.10 from backend/.venv.
- Result: 330 passed, 0 failed, 0 errors, 0 skipped.
- JUnit: ../raw/be2_internal_offline_test_20261021/junit.xml; SHA256 4AAF9563B5CF3F1B4774BCCC29300A33E9B7B9CF46BD97E68F1C9087C5D43695.
- No provider, database, server, Modal, Lightning or runtime was used.

## Command and coverage

Ran from backend:

    .\.venv\Scripts\python.exe -m pytest tests/integration/be2_cross_lane tests/unit/test_ai_job_video_dispatch.py tests/unit/test_ai_job_b5_capability.py tests/unit/test_knowledge_bundle_service.py tests/unit/test_knowledge_bundle_races.py tests/unit/test_knowledge_bundle_chain.py tests/unit/test_knowledge_bundle_adapters.py tests/unit/test_knowledge_video_media.py tests/unit/test_knowledge_video_create.py -q -rs --junitxml=..\features\FEAT-057-be2-01-14-offline-integration\evidence\raw\be2_internal_offline_test_20261021\junit.xml

The run covers the X01 producer-export/media-pipeline fixture, the edge registry, BE2-01 typed dispatch and B5 regression, and selected BE2-07/08 offline service and media regressions.

## Interpretation and limits

- X01 exercises a producer-created BE2-07 export consumed by the BE2-08 media pipeline and confirms exact-pin and invalidation cases in the fixture. It still uses a process-local coordinator; it does not prove a durable source fence held through BE2-08 finalization. X01 remains PARTIAL.
- The typed-dispatch tests confirm forwarding to a fake video target and fail-closed routing for unknown types. They do not compose a persisted job, run and source pin with the real VideoWorker. X09-08 remains NOT_IMPLEMENTED.
- Registry tests explicitly retain X02–X09 as NOT_IMPLEMENTED except X01 PARTIAL. A passing registry test is not behavior evidence for those edges.
- No card-owned source, tests, approvals, schemas or migrations were changed by this run. One raw JUnit artifact was added; no files were staged.

## Review context

The owner supplied a separate-session Rev5 re-review result of PASS_WITH_NOTES (no P1/P2, seven P3 notes) and chose to stop at Rev5. The reviewer report is in the session transcript, not pinned as a repository file. This review and this test run do not grant new implementation approval. P3-2 must be clarified before any BE2-08 implementation involving files outside its approved addendum; existing execution-manifest and contract gates remain open.
