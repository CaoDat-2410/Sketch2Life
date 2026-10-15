# Feature decisions

## D-01 — Real runtime request path

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for FEAT-047.
- Decision: BE1 runtime capabilities must execute through FastAPI application services and durable adapters. Fixture runners and in-memory state are not accepted runtime behavior.

## D-02 — Consent remains pending until an approved verifier exists

- Date: 2026-10-14 (Asia/Saigon).
- Status: owner-confirmed for FEAT-047.
- Decision: record consent evidence/status without treating it as effective. Child-data capture/processing remains denied until a separate approved verification procedure and purpose catalogue exist.

## D-03 — Persistent filesystem for local development artifacts

- Date: 2026-10-14 (Asia/Saigon).
- Status: owner-confirmed for local development only.
- Decision: store bytes under a configurable persistent local data root and return opaque references. Keep production object-storage provider unselected; Firebase Storage remains forbidden.

## D-04 — PostgreSQL-backed BE1 runtime

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for FEAT-047 only under ADR-0017.
- Decision: extend the approved FEAT-046 PostgreSQL/SQLAlchemy/Alembic adapter for new BE1 durable aggregates. PostgreSQL is authoritative; no in-memory fallback for runtime writes.

## D-05 — Preserve unresolved SRS labels

- Date: 2026-10-14 (Asia/Saigon).
- Status: adopted for FEAT-047.
- Decision: implement owner-confirmed facts only. B19/B21/B22 `PROPOSED`, `PROPOSED_UNADOPTED`, and `TBD` details remain disabled, pending, or out of scope until separately approved.

## D-06 — BE1 HTTP correlation and error contract

- Date: 2026-10-15 (Asia/Saigon).
- Status: adopted for FEAT-047 implementation API only.
- Decision: every `/api/be1/v1` response includes a safe `X-Request-ID`; errors use the versioned `{code, message, request_id}` object and OpenAPI documents it as `Be1Error`. Validation responses do not echo submitted values. This does not adopt the proposed SRS B22 DTOs as the product-wide contract.

## D-07 — Publish the feature-scoped BE1 v1 API contract

- Date: 2026-10-15 (Asia/Saigon).
- Status: adopted for FEAT-047 implementation API only.
- Decision: document all 47 operations across the 42 /api/be1/v1 paths in artifacts/API_CONTRACT.md and publish a BE1-only OpenAPI 3.1 artifact. Request bounds, response shapes, role/device scopes, status codes, and current consent/storage gates are explicit. This does not claim that proposed B22 routes or DTOs are adopted product-wide.
