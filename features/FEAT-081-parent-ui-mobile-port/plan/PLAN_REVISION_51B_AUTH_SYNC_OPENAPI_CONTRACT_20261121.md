# FEAT-081 — Plan Revision 51B: publish Parent identity synchronization in OpenAPI

**Status:** APPROVED by the owner's 2026-11-21 request to fix the real backend sign-up/sign-in and Google flows. This supplements approved Plan Revision 51 and 51A.  
**Product authority:** FEAT-063 v2.7-draft through Rev71; unsigned.

## Scope

The task adds `POST /api/auth/v1/registrations/complete` for a verified Firebase identity to idempotently synchronize a server-assigned Parent row. The repository projects only allowlisted operations into its published OpenAPI document, so the route must be added to that projection and contract catalog.

1. Add the operation to `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` and any minimal projection wiring required in `backend/src/sketch2life/interfaces/http/openapi_contract.py`.
2. Add contract assertions in `backend/tests/contract/test_openapi_contract_catalog.py` for bearer authentication, response schema/statuses, and absence of client-controlled role/UID fields.
3. Run only the focused OpenAPI contract tests. Do not change unrelated API routes or the product SRS.

## Acceptance

- `/openapi.json` includes the new route with the declared response contract and authentication requirement.
- OpenAPI cannot advertise a client-supplied role, UID, or account scope for this operation.
- Plans 51 and 51A limits remain in effect.

## Authorized paths

- `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py`
- `backend/src/sketch2life/interfaces/http/openapi_contract.py`
- `backend/tests/contract/test_openapi_contract_catalog.py`
- FEAT-081 plan, approval, evidence, status/context paths already approved under Addenda 81/82
