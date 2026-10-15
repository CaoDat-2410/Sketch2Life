# BE1 real runtime backend context

- Status: APPROVED for implementation under plan revision 1.
- Created: 2026-10-14 (Asia/Saigon).
- Owner request: replace fixture-only BE1 implementation with a real backend capable of the BE1 SRS scope.
- Allocation: P2 / BE1 core, following FEAT-040 and ADR-0015. The runtime project builds on FEAT-045 BE1-01 domain/contracts and FEAT-046 BE1-02 PostgreSQL persistence.
- Runtime decisions: FastAPI remains the existing confirmed framework; PostgreSQL 17 is the task-scoped durable authority; Firebase Authentication is the adult identity source; filesystem storage is local-dev only. See ADR-0017.
- Consent: owner selected keeping consent pending and blocking child-data paths until a verification procedure is separately approved.
- Scope: real request/worker paths for BE1-03 through BE1-15, shipped in vertical slices. BE1-16 automatic grouping remains Phase 2 and separately gated.
- Constraints: no fixture/in-memory implementation on the runtime request path; no real child data or seeded accounts in repository/evidence; no Firebase data products; do not adopt SRS `PROPOSED`/`TBD` details by implication.
- 2026-10-15 implementation increment: BE1 device grant refresh now proves possession of the previous key and rotates it; group lock closes active turns and blocks device canvas access; moves invalidate active turns and re-admission does not restore old group membership. HTTP success/error responses propagate a safe request ID, and errors share the OpenAPI `Be1Error` contract. Live Firebase-token acceptance remains gated by project configuration.
- 2026-10-15 acceptance increment: the feature now has a detailed 47-operation / 42-path BE1 v1 contract plus a BE1-only OpenAPI 3.1 artifact. A disposable PostgreSQL 17 database verified real HTTP persistence, revisions, assignment scopes, audit/outbox, data-request status, pending-consent denial, local artifact durability, and retention purge behavior. The full backend suite collected 2,173 tests: 2,167 passed, 6 skipped, 0 failed; the focused BE1 database suite passed 3 tests. Live Firebase credentials and the approved consent/purpose verifier remain unavailable by design.
- Remaining decisions: consent verifier/purpose catalogue, production object storage, non-session retention classes, exact adopted B22 client contract, Firebase project runtime configuration, and provider purge evidence.
