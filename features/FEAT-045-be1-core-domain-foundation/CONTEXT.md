# BE1-01 core domain foundation context

- Status: COMPLETED for isolated BE1-01 under approved plan revision 1.
- Created: 2026-10-14 (Asia/Saigon).
- Goal: deliver the first independent P2/BE1 core foundation card from the current four-person allocation.
- Owner request: “làm task người 1, be 1, làm các cái core”. Interpreted using ADR-0015 as P2/BE1 and bounded to BE1-01.
- Current authority: canonical Master SRS v3.1, ADR-0015, BE1-01 task card, and the direct request above.
- Scope: pure backend domain types/rules, application ports, closed versioned core handoff schemas, synthetic fixtures, and a standalone in-memory runner.
- Constraints: no database/provider/live service, HTTP wiring, BE1-02 durable adapters, production stack freeze, real child data, or changes to FEAT-037 work in progress. Preserve SRS proposal/TBD status.
- Dependencies: none on live services or other people’s work; fixture-only and independently runnable.
- Approval: `approvals/TASK_APPROVAL.md`, approved 2026-10-14 19:20:03 (Asia/Saigon), plan SHA-256 recorded there.
- Delivered: domain/application policies, inward-facing ports, strict v1 candidate schemas, status-labeled synthetic fixture pack, and feature-local in-memory runner.
- Review: 20 domain fixtures and 1 unknown-field probe pass; Ruff check/format check pass; dependency scan confirms framework-independent domain and inward-facing ports. See `evidence/README.md`.
- Limits: contracts remain `PROPOSED_UNADOPTED`; no durable adapter, HTTP/auth integration, provider/database, policy finalization, load proof, or production readiness is included.
