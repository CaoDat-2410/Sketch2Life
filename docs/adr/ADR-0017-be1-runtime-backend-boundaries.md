# ADR-0017 — BE1 real runtime backend boundaries

- Date: 2026-10-14 (Asia/Saigon)
- Status: Accepted for FEAT-047 only
- Decision owners: Project owner and BE1 implementation
- Supersedes: None
- Related: ADR-0003, ADR-0005, ADR-0006, ADR-0014, ADR-0015, ADR-0016; FEAT-045, FEAT-046, FEAT-047; Master SRS v3.1 B17, B19–B26

## Context

BE1-01 and BE1-02 provide a framework-independent foundation and PostgreSQL adapter, but do not provide a running BE1 application API. The owner requested a real backend instead of fixture-only behavior. The canonical SRS confirms FastAPI as the backend framework and Firebase Authentication as the adult identity source; PostgreSQL was selected for FEAT-046 and Docker PostgreSQL is available for this runtime task.

Many B19/B21/B22 mechanics remain `PROPOSED`, `PROPOSED_UNADOPTED`, or `TBD`. The SRS also leaves consent verification, purpose taxonomy, production object storage, some retention classes, exact client contracts, and provider-copy purge guarantees unresolved.

## Decisions

1. Use the existing FastAPI modular monolith and extend FEAT-045/046 inward-facing application/domain/persistence boundaries. This decision does not freeze the full product stack.
2. Use PostgreSQL 17 with SQLAlchemy 2.x/Alembic as the authoritative BE1 runtime database for this feature. Database-backed endpoints fail closed; fixture/in-memory stores are not a runtime fallback.
3. Verify adult identity through Firebase Authentication. The backend resolves role assignments, enrollment, purpose, and resource scope. Firebase Storage, Firestore, and Realtime Database are forbidden.
4. Use durable PostgreSQL outbox/worker state. Redis/RQ are not authoritative and are not selected by this ADR.
5. Use a persistent filesystem adapter only for local development media. Production object storage remains open pending a separate decision.
6. Keep consent pending and deny child-data paths until an approved consent verification procedure and purpose catalogue exist.
7. Implement only owner-confirmed or separately approved SRS behavior. Proposed API routes and field semantics are not adopted wholesale; FEAT-047's versioned endpoints are feature-scoped until client-contract approval.
8. Exclude BE1-16 automatic grouping as Phase 2 and require a separate allocation/approval.

## Open questions retained

- Consent verification authority, evidence requirements, purpose catalogue, and revocation workflow beyond the owner-confirmed school-mediated collection model.
- Production object storage/provider, transient copies, backup expiry, and verifiable provider purge.
- Retention classes outside the owner-confirmed 90-day session/artwork default.
- Exact adopted B22 routes/DTOs and mobile compatibility policy.
- Firebase project ID and runtime credential/revocation-check configuration.

These questions do not authorize invented behavior. The runtime must expose pending/unavailable states or deny the dependent operation until the answer is approved and recorded.

## Consequences

- BE1 can be exercised locally against PostgreSQL and durable local files without seed accounts or child fixtures.
- Production deployment remains blocked on secrets, external storage, consent policy, and environment-specific operations; local verification is not a production-readiness claim.
- The project may later change providers behind ports without changing domain ownership or treating this ADR as a global stack freeze.
