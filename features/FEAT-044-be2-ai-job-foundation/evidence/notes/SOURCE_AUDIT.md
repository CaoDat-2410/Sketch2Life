# Read-only BE2 source audit

- Date: 2026-10-14, Asia/Saigon.
- Reviewer: Codex primary agent with independent task-inventory/source-readiness agents.
- Branch baseline: `feature/be2-01-ai-job-foundation`, `b9204d8c9eb4f8a1ee6d4db4de5ee23672e0392c`.
- Method: local Git/worktree inventory; `rg` source searches; context/register/governance/SRS/backlog/source reads. No network, provider calls, dependency installs or runtime edits.
- Existing change preserved: `apps/ui-mobile/android/gradle/wrapper/gradle-wrapper.properties`. Initial root worktree belongs to a different branch; all new documentation is in BE2 worktree.

## Source lineage

| Source | Used for |
|---|---|
| `AGENTS.md`, `docs/governance/WORKFLOW.md`, `APPROVAL_POLICY.md` | Feature plan/approval/evidence rules |
| `docs/context/PROJECT_CONTEXT.md`, `SOURCE_REGISTER.md` | Current SRS/staffing/environment authority; historical conflicts |
| `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md` | 14 BE2 cards, routes/DTO ownership, handoffs, runtime DAG; BE2-01 starts independently |
| `features/FEAT-040-four-person-delivery-plan/artifacts/drafts/BE_AI_TASKS.md` | Detailed AI/job scope and separately gated durable follow-on |
| `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` | DATA-25 at line 1660, CMD-44 at 1788, B19.10 at 948, B22.3 at 1833 |
| `docs/adr/ADR-0015-four-person-role-and-integration-allocation.md` | P3 BE2 ownership; fixture independence; P4 coordination |
| `docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md`, `CONTRACTS_AND_INTEGRATION.md` | Inward dependencies and versioned ports; old numeric defaults not automatically adopted |

Source IDs: collaborative-srs-v3-20261010, four-person-task-backlog-v1, owner-four-person-allocation-20261010, owner-foundation-answers-20261010. Source hashes are recorded in metrics to preserve provenance; originals are unchanged.

## Confirmed reuse and gaps

| Existing path | Finding | Planning implication |
|---|---|---|
| `backend/src/sketch2life/contracts/schemas/workflow_records.py` | Legacy WorkflowJobV1 states/timestamps/terminal validation | Reference patterns; DATA-25 job/attempt/disposition validator still needed |
| `backend/src/sketch2life/application/ports/session_storage.py` | Generic JobStore/IdempotencyStore/ArtifactStore | Reuse port conventions; specialize job/request/completion semantics |
| `backend/src/sketch2life/infrastructure/storage/in_memory.py` | Copy isolation and compare-before-replace fake JobStore | Fake CAS scaffold, not durable recovery evidence |
| `backend/tests/unit/test_ephemeral_storage_ports.py` | CAS/idempotency/opaque artifact checks | Targeted regression candidates after implementation |
| `backend/src/sketch2life/application/ports/ai_gateway.py` | Provider-neutral reference-only dataclasses/Protocol | New scope/attempt/consent context remains necessary |
| `backend/src/sketch2life/application/services/whiteboard_video_job.py` | Fake clock, bounded retry/history, source hash checks | Semantics references; historical numeric defaults remain unadopted |
| `backend/src/sketch2life/application/services/story_video_job.py` | Process-local dict + RLock, semantic dedup/expiration/failure patterns | No restart/outbox/transaction proof; keep legacy route compatible |
| `backend/src/sketch2life/interfaces/http/routers/story_video.py` | FastAPI BackgroundTasks dispatch | Not a durable BE2 worker/queue implementation |
| `backend/src/sketch2life/infrastructure/persistence/`, `infrastructure/queue/` | No durable implementation files identified in audit | Phase B needs BE2-owned adapters/migrations/receipts |
| `services/media-worker/README.md`, `services/gpu-orchestrator/README.md` | Boundary descriptions | Not working runtime ownership transfers to P4 |

Source search found no general DATA-25/CMD-44 job foundation or ProviderCopyLifecycle implementation. This is a repository audit finding, not a test result. Vision/media/catalog code exists; actual quality/generation/compliance in replacement scope requires separate evidence.

## Environment inventory and limits

Readiness agent checked default interpreter via import discovery: Python 3.12.10; Pydantic present; pytest, FastAPI, ruff, mypy, Redis, RQ unavailable. No suite was run by audit agents. New Phase A domain runner needs no GPU; HTTP/contract checks still require approved compatible dependencies. Default interpreter limitations do not prove that every other environment is unavailable.

Source facts vs proposal: existing paths/legacy gaps above are observed. Candidate files, transition guards, sequence priority and acceptance in plan are proposed implementation choices, pending scope/schema/policy review. FEAT-040 documentation approval does not authorize new runtime.
