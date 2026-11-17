# EV-063-31 — Swagger navigation and role grouping

## Request and rationale

- The owner asked why Swagger was not grouped by role and requested a clearer, more professional organization.
- The previous four tags were derived from broad API surfaces. The contract itself declares Bearer or no OpenAPI security scheme, so it does not provide enough role detail to label every API safely.
- Route guards in the Lesson Library source explicitly establish Teacher, School Manager, Parent, Platform Admin, shared staff, and authenticated upload-owner scopes. Those routes now use role-oriented tags. Remaining BE1 and Demo routes are grouped by handler/domain workflow; these tags do not assert access roles.
- The custom OpenAPI builder had not passed FastAPI's configured tag definitions and app description into `get_openapi`, so the tag descriptions were absent from the published document. It now includes both.

## Delivered

- Swagger now has 18 descriptive groups. Lesson Library role groups follow current source guards; upload-session operations are labeled by owner scope. BE1/Demo groups follow domain/workflow; health and local storage examples are separate.
- Every mounted Rev37 operation has exactly one defined tag. The OpenAPI `tags` section contains the full descriptions. Route set and all Rev37 request, security, response, and mounted/unmounted declarations remain unchanged.
- Local Swagger remains available at `http://127.0.0.1:8000/docs`; OpenAPI JSON is at `http://127.0.0.1:8000/openapi.json`.
- Snapshot: `../artifacts/OPENAPI_FEAT063_REV37_20261030.json`; SHA-256 `27BB19AC8A5938D239A300DB4BFC5028AA205A675AE9B09EE00CCD35CB3D3453`.
- Approved Plan Rev39 SHA-256: `1E0244E9D43F3F3B46361D66711D413293F2B7E50DB30DEE5B353BAA2474834F`.

## Verification

- `backend/tests/contract/test_openapi_contract_catalog.py`: 2 passed, including Swagger UI/JSON availability and full contract parity.
- Snapshot exporter passed with 124 mounted operations, 111 paths, and 11 unmounted candidates.
- Targeted Ruff and formatting checks passed; compile check passed for changed Python files.
- This was a documentation/navigation change only. It did not alter endpoint authorization or behavior. The Rev38 upload 413 mismatch remains recorded in EV-063-30.
