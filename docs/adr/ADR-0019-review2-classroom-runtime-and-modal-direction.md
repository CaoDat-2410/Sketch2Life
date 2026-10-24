# ADR 0019 Classroom runtime composition and Modal hosting direction

- Date: 2026-10-22
- Status: ACCEPTED for target documentation; runtime implementation is a separately scoped change.
- Authority: direct owner answers in FEAT-058, decisions D08 and D09.
- Supersedes: incompatible legacy provider/deployment target assumptions in earlier ADRs for the current collaborative classroom product only.

## Context

The supplied registration v1.2 and canonical Master SRS v3.1 describe collaborative classroom learning. Current dev exposes durable BE1 alongside process-local legacy/demo services. The latest BE2 and Admin UI branches are not contained in dev. Modal evidence found in the BE2 branch proves a selected offline CPU test package, not GPU inference or a product endpoint.

## Decision

The product target uses a classroom runtime with durable application ports and explicit composition. Legacy Parent/Guide flows and in-memory demos use separate demo entrypoints. Integrate BE2 and Admin through versioned application contracts, scoped authorization and reproducible acceptance evidence. Do not rename legacy aggregates into classroom semantics or make demo stores production fallbacks.

The owner selects Modal for AI hosting. Client applications call the application backend, which owns provider credentials and policy checks. Provider jobs/results use application-owned ports, pinned source/configuration versions and typed failures. Keep current Lightning adapters as an existing research/test lane until a separately approved migration disposes them.

## Open implementation details

Modal application/environment, endpoint shape and authentication, model versions/licenses, GPU type/count, scaling/warm capacity, timeout/retry/budget controls, artifact delivery, secret management, content retention/copy deletion and measured latency/capacity are not supplied. Record them before claiming deployment or publishing a runtime profile. Modal selection does not change consent/review/provenance requirements or guarantee request speed.

## Consequences

Report target design and actual implementation separately. Add runtime cleanup and integration cards before code changes. Preserve existing state/history and test runners. Existing component/test receipts do not establish whole-product integration or authorize provider calls. Other technology selections remain governed by their applicable ADR and feature scope.
