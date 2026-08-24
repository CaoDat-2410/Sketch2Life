# FEAT-012 parallel workstream reallocation

- Status: DONE
- Owner: project owner + four-person team
- Goal: correct the four-person allocation so Sprint 1 has balanced, independently executable workstreams and integration is planned as a separate sprint.
- Scope: team-allocation documentation, system baseline Section 21, roadmap-versus-assignment clarification, project context, and an accepted ADR.
- Non-goals: product implementation, runtime integration, provider provisioning, personnel naming, calendar estimation, frontend visual generation, or changing the accepted technical architecture.
- Dependencies: FEAT-001 allocation proposal, current system baseline, and direct owner correction on 2026-08-24.
- Risks: accidentally treating the dependency-driven project roadmap as a sequential staffing plan, or assigning shared integration debt to one person.

## Context snapshot

The owner rejected the previous allocation because Person 4 carried backend, infrastructure, learning media, deployment, and E2E integration, while Person 3 carried the entire Android app plus rendering. The resulting P2 -> P4 -> P3 handoff chain violated the intended four-way parallel delivery model.

The owner supplied the approved Sprint 1 split: Person 1 owns BA/Montessori specifications and harnesses, Person 2 owns standalone AI understanding, Person 3 owns standalone art animation, and Person 4 owns standalone learning media. Android, backend orchestration, auth, persistence, queues, Gate UI, and E2E move to a later Integration Sprint with a new allocation.
