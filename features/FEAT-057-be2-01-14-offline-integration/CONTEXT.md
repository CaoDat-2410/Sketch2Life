# FEAT-057 / BE2-01–14 offline integration context

- Status: ACTIVE
- Owner: repository owner / Codex executor
- Goal: build and verify a reviewable offline integration candidate containing the accepted BE2-01–07 branch snapshot and the BE2-08–14 branch snapshot.
- Scope: branch-level integration and offline validation only.
- Non-goals: feature-card acceptance, owner/runtime adoption, provider activation, Lightning execution, deployment, or merge to `dev`/`main`.
- Dependencies: `feature/be2-01-07` at `9d1ed184f31ab6b1f18337a1e29bb04fd59aa1b5`; `origin/feature/be2-08-14` at `42a6d3122259e6b33133673a2e444deefa45d387`; existing card plans, approvals, status records, handoffs, and evidence.
- Risks: divergent shared history, conflicting shared documentation and dependency/migration registries, cross-card assumptions not covered by isolated component suites, and incomplete external owner/runtime adoption.

## Context snapshot

The BE2-01–07 task branch and BE2-08–14 receiver branch share base
`6dcc57ee0b3d053f071c8c92e72aaaee2e98d899` and have diverged. The task 7 snapshot
is already present on `feature/be2-01-07`; a task-7-to-that-branch PR has no diff.
The receiver branch contains seven card areas (BE2-08 through BE2-14) with their
own approvals and offline/owned-PostgreSQL evidence. Their current status records
still say `IN_PROGRESS` or `IN_PROGRESS_PENDING_EXTERNAL`, with external adoption
and runtime gates open. Those records remain authoritative for their card status.

The direct user instruction in this Codex conversation authorizes creating and
checking an integration branch for BE2-01–14, starting offline integration and
testing now, and deferring live testing until Lightning works normally again.
See the matching approval record and source-register entry for the exact scope.

## Source register references

- `feature/be2-01-07` FEAT-056 acceptance/publication records: accepted offline BE2-07 snapshot and branch publication; runtime/integration remain separate.
- `feature/be2-08-14` `docs/context/SOURCE_REGISTER.md`: individual BE2-08–14 approvals and owned component/SQL evidence; explicit external integration deferrals remain in force.
- `docs/adr/ADR-0006` and FEAT-040 allocation records: fixture/component work and integration work have separate scopes; this new direct owner instruction authorizes this bounded integration candidate only.
