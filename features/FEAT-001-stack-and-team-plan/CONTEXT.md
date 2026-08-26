# FEAT-001 Stack and team plan context

- Status: AWAITING_APPROVAL
- Owner: Project owner + four-person team
- Goal: Convert project answers into an implementation-ready stack proposal, MVP boundary, and workstream ownership.
- Scope: Mobile client, backend/data plane, Lightning AI plane, fixture-only development, and four-person delivery split.
- Non-goals: Product code, model integration, cloud provisioning, real child-data collection, or frontend visual generation.
- Planning update (2026-08-26): the detailed Sprint 1 allocation is recorded in `SPRINT_1_TASK_ALLOCATION.md`. It is a proposed execution split consistent with ADR-0006, not implementation authorization.

## Inputs confirmed by owner

- Mobile-only product.
- Four people with broad/full-stack ability.
- Lightning AI required for real-model testing.
- Backend may later be deployed to AWS or another provider.
- Fixtures/synthetic data only.
- MVP must cover the complete experience.

## Governing reference sources

- Handbook v7: source register entry `handbook-v7`; especially codebase organization, tech-stack baseline, state machine, and validation/fallback rules.
- Sprint task workbook: source register entry `sprint-task-breakdown`; especially four workstreams and acceptance/evidence expectations.

## Key risk

React Native does not natively provide the handbook's PixiJS + GSAP runtime. The proposal isolates that runtime in a small WebView/bridge module so the product remains mobile-only while preserving the deterministic renderer. This must be validated with a thin spike before the art feature is approved for full implementation.
