# Task approval

- Status: APPROVED
- Approver: Project owner, by direct instruction in this conversation
- Approved scope: FEAT-047 plan revision 1, real FastAPI BE1 runtime for BE1-03 through BE1-15 using PostgreSQL-backed services and no fixture/in-memory request path; apply confirmed SRS policy only; keep consent pending until an approved verification path; use persistent filesystem for local development bytes with production object storage open. BE1-16 Phase 2 automatic grouping, BE2 providers, deployment, and full-stack freeze are excluded.
- Plan revision: 1
- Plan SHA-256: 452E8DAC726B763D8094EA34BA81C766B04A96BD337B18E018962EAF7718EF60
- Approved at: 2026-10-14 (Asia/Saigon)
- Approval evidence: The owner instructed: “làm real đi, ko làm fixture, implement 1 cái backend có khả năng làm những cái như trong srs của be 1 đi”. The owner then selected pending consent until an approved verifier exists and persistent filesystem storage for local development. This record limits approval to the exact FEAT-047 scope and preserves unresolved SRS gates.
- Notes: This approval authorizes implementation only; it does not adopt SRS `PROPOSED`/`TBD` semantics or approve credentials, real child data, production deployment, or BE1-16.

## FEAT-047 OpenAPI artifact-upload description correction — 2026-11-14

- **Status:** APPROVED / NOT LAUNCHED.
- **Approver:** Project owner (Person 2), by direct instruction in this conversation.
- **Approved task:** The bounded correction in `plan/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_DRAFT1_20261114.md`, with Section 3's source attribution corrected to identify `MOUNTED_OPERATIONS` as the exact wording source and `API_CONTRACT.md` as route/behavior evidence.
- **Approved plan pin:** 7,886 bytes; SHA-256 `235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B`.
- **Approval prefix:** Existing Plan Revision 1 history, 1,266 bytes; SHA-256 `F628501E19C00B71DF7954B2105DBF8C9E4B6B27476129E4604A15606265FC54`, is preserved unchanged above this entry.
- **Implementation scope:** Add only the exact `description` metadata `Tải một tệp kết quả hoặc tư liệu vào buổi học của tổ chức.` to the existing artifact-upload route decorator in `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py`. No route behavior, test, catalog, schema, status, authorization, persistence, SRS, or M2 scope changes are approved.
- **Verification budget:** One invocation of the owner-authorized combined S2 targeted pytest selection from `backend/` using the prepared Python 3.12 environment. The selection is the nine test files listed in the owner's approval prompt. No separate OpenAPI test invocation or retry is authorized by this approval.
- **Launch boundary:** This approval authorizes the one metadata edit and the one verification invocation only. It does not approve S2 completion, S3, database or migration work, deployment, provider or Modal calls, staging, commit, or push. `OWNER_MODAL_CALL_APPROVED=NO`.
