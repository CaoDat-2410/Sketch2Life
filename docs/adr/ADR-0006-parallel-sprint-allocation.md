# ADR-0006: Parallel Sprint 1 allocation and separate integration sprint

- Status: ACCEPTED
- Date: 2026-08-24
- Owner: Sketch2Life project owner
- Supersedes: the ownership table in FEAT-001 revision 1

## Context

The previous four-person allocation made Person 4 responsible for backend orchestration, session/job state, PostgreSQL, S3, Redis/RQ, learning media, deployment, and E2E, while Person 3 owned the full Android app and art renderer. It also created sequential runtime chains such as AI understanding -> backend orchestration -> Gate UI. That contradicted the owner's requirement that four broadly capable people make balanced progress in parallel.

The technical project roadmap remains dependency-driven, but a team sprint plan must be workstream-driven. These are separate planning views.

## Decision

Sprint 1 has four standalone component workstreams:

1. BA/Montessori specifications, catalogs, taxonomies, deterministic rule fixtures, harness, and acceptance criteria.
2. AI Understanding media validation, ASR/VLM adapters, fusion, `RawUnderstandingResult`, and fixture benchmarks.
3. Art Animation PixiJS/GSAP runtime, Motion DSL, `DRAW_REVEAL`, preservation/fallback, and standalone player.
4. Learning Media cache/resolver, generation adapter, validation, still+narration fallback, and fixture benchmarks.

Each workstream consumes versioned synthetic fixtures, emits versioned schemas/artifacts, and has a standalone runner or test harness. No workstream depends on another person's live service in Sprint 1.

Android application integration, backend orchestration, auth, DB/storage/queue wiring, Gate UI, deployment, and E2E form a separate Integration Sprint. That sprint is estimated and allocated after Sprint 1 evidence; no person inherits it by default.

## Consequences

- Sprint 1 can proceed as four parallel branches of evidence-producing work.
- Person 1 does not implement recommendation runtime in Sprint 1.
- Person 3 does not own the entire Android application in Sprint 1.
- Person 4 does not own backend/infra/deployment/E2E in Sprint 1.
- Integration risk stays visible in a dedicated backlog instead of being hidden inside one workstream.
- Contract and fixture quality become the primary Sprint 1 coordination mechanism.
- The dependency-driven roadmap remains valid but cannot be used as the team assignment order.

## Evidence

- Owner correction recorded in `features/FEAT-012-parallel-workstream-reallocation/`.
- Revised allocation: `features/FEAT-001-stack-and-team-plan/TEAM_ALLOCATION.md`.
