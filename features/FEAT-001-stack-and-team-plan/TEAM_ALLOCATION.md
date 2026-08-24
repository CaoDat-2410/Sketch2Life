# Four-person Sprint 1 workstream allocation

This allocation is revised by FEAT-012 and governed by `docs/adr/ADR-0006-parallel-sprint-allocation.md`.

Sprint 1 targets four balanced, independently executable component workstreams. It does not assign the integrated application to one person. Every workstream consumes versioned synthetic fixtures, publishes a versioned contract, and must run without another person's live service.

| Person | Primary Sprint 1 ownership | Deliverables and evidence | Not owned in Sprint 1 |
|---|---|---|---|
| Person 1 — BA / Montessori | Montessori domain, Activity Catalog, Learning Objective taxonomy, prerequisite/safety/material rules | Versioned specifications and catalogs, positive/negative fixtures, deterministic expected-result harness, acceptance criteria | Recommendation runtime, Gate B UI, backend wiring |
| Person 2 — AI Understanding | Media validation, Whisper, VLM, fusion, `RawUnderstandingResult` | Standalone fixture runner, provider-neutral adapter contract, schema/provenance/error fixtures, Lightning/Runpod benchmark | Gate A UI, session/job orchestration, integrated API |
| Person 3 — Art Animation | PixiJS, GSAP, Motion DSL, `DRAW_REVEAL`, preservation, fallback | Standalone animation player, bridge protocol fixtures, visual/performance/preservation/fallback evidence | Entire Android app, capture, Gate UI, auth |
| Person 4 — Learning Media | Cache, resolver, video-generation adapter, validation, still+narration fallback | Standalone fixture runner, request/result contract, cache/fallback cases, quality/latency/cost benchmark | Backend orchestration, DB/S3/Redis/RQ wiring, deployment, E2E |

## Parallel-execution contract

Each workstream must provide:

1. a versioned input fixture manifest;
2. a versioned output schema;
3. a standalone runner or test harness;
4. success, invalid-input, timeout/failure, and fallback evidence where applicable;
5. a compatibility note for the later Integration Sprint.

Cross-review is allowed and required, but a handoff cannot be a live-service prerequisite during Sprint 1. Contract changes are proposed through versioned fixtures and reviewed at the shared contract-freeze milestone.

## Integration Sprint — separate allocation

Only after Sprint 1 evidence is reviewed does the team create and approve a new allocation for:

- Android app shell, capture/playback, Gate A/B UI;
- backend API/orchestration and session/job state;
- Firebase auth and authorization;
- PostgreSQL, S3, Redis/RQ, and workers;
- contract wiring, observability, deployment, and E2E.

No single person is the default integration owner. In particular, Person 4 does not inherit backend/infra/deployment/E2E, and Person 3 does not inherit the complete Android application. Workload is re-estimated and rebalanced from Sprint 1 evidence before approval.

## Planning rule

`PROJECT ROADMAP` is dependency-driven and explains what the complete system eventually needs in technical order.

`TEAM SPRINT TASK` is workstream-driven and explains what four people can execute concurrently with controlled contracts and fixtures.

The project roadmap must never be copied directly into the team assignment sequence.
