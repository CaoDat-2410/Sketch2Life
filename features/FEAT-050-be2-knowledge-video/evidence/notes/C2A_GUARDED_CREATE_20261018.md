# E03 — C2a guarded create component (P2 partial)

- Date:2026-10-18, Asia/Saigon; reviewer Codex author self-review.
- Base C1:a3946e7; existing Windows backend venv; no installations/provisioning.
- Own create suite: tests/unit/test_knowledge_video_create.py,21 PASS.
- Own total164 (143 C1 +21 create). Combined existing205 gives369 PASS /0 skip
  in3.92s on final invocation.
- Exact command from backend: `.venv/Scripts/python.exe -m pytest` followed by
  tests/unit/test_knowledge_video_domain.py,
  tests/contract/test_knowledge_video_contract.py,
  tests/unit/test_knowledge_video_create.py,
  tests/unit/test_ai_job_application.py,
  tests/unit/test_ai_job_review_regressions.py,
  tests/unit/test_ai_job_q00_followups.py,
  tests/unit/test_learning_content_domain.py,
  tests/unit/test_ai_policy_domain.py.
- Ruff: three own test files, domain/knowledge_video, schemas/knowledge_video.py,
  application/knowledge_video_create.py, application/ports/knowledge_video.py,
  infrastructure/knowledge_video: PASS. Initial line-length and nested-with lint
  findings corrected; final invocation clean.
- Mypy same seven owned source files, `--follow-imports=silent`: PASS.
- Cases: all three strategies submit only waiting fixture intents; current rights
  on replay; scoped idempotency/body conflict; cross-teacher authorized semantic
  dedup; original pin not rewritten; exact scope/bundle/audience/profile matching;
  failed staging and changed lease discard all fixture effects; process-local24
  concurrent request cases; closed-lease generation cannot revive; context-bound
  lease cannot submit for a different principal.
- Source-set order canonicalization reviewed across replay/dedup; compare exact
  canonical pin digest rather than incidental tuple ordering.
- Limits: FixtureVideoOwner is NOT actual07/BE1/policy registry. Job/dispatch maps
  contain synthetic INTENTS, not real foundation jobs or messages. No actual
  SQL/cross-process/restart/worker/provider/media decoder evidence. No live HTTP
  route added. See CR_ATOMIC_VIDEO_SUBMISSION.md; P2 remains partial.
