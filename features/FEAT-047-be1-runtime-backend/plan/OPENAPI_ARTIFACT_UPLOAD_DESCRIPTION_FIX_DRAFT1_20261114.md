# FEAT-047 BE1 OpenAPI Artifact Upload Description — Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED.
- **Task type:** Separate BE1 documentation-metadata correction discovered during FEAT-063 M2 S2 verification.
- **Feature owner:** FEAT-047 — BE1 Runtime Backend.
- **Date:** 2026-11-14.
- **Implementation worktree:** Must be a dedicated BE1 task branch/worktree. This planning draft is stored in the FEAT-047 plan folder within the current M2 worktree to retain the verified Rev67 context; do not include it in an M2 S2 implementation commit.

## 1. Goal

Add the missing OpenAPI `description` to the existing BE1 session artifact upload route so the runtime OpenAPI operation matches the already-published `MOUNTED_OPERATIONS` purpose exactly:

`Tải một tệp kết quả hoặc tư liệu vào buổi học của tổ chức.`

This is an API-documentation metadata correction only. It must not change route behavior, persistence, authorization, request or response schemas, status codes, or product workflow.

## 2. Context and evidence

The owner-run M2 targeted pytest selection collected 82 tests: 81 passed and 1 failed in 16.17 seconds. The failing test was `test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates`; it raised `KeyError: 'description'` at `backend/tests/contract/test_openapi_contract_catalog.py:307`.

The first missing-description operation identified by the ASCII-safe runtime OpenAPI diagnostic was:

- `POST /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts`
- Expected purpose: the exact Vietnamese sentence above.
- Actual description: missing.

The route source is `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py:278`. Its decorator currently specifies the route and status code without an explicit description. The shared catalog contains the purpose at `backend/src/sketch2life/interfaces/http/openapi_contract.py:80`.

The diagnostic output was truncated after the first missing entry, so additional missing or mismatched operations remain unverified. This plan authorizes no automatic expansion to those items. The cancel route is excluded from the failing comparison: it is in `PR22_UNCATALOGUED_OPERATIONS`, which the test asserts is disjoint from `MOUNTED_OPERATIONS`.

This route appeared in a shared catalog test run during S2 verification. That does not establish that M2 introduced the omission. The finding is outside the approved M2 S2 implementation file allowlist.

## 3. Requirement authority and interpretation

- The current product authority is FEAT-063 v2.7-draft Rev67, unsigned, routed by `docs/context/SRS_AUTHORITY.md`.
- This plan does not add or alter a product requirement and does not claim that the exact route or description sentence is mandated by Rev67. The exact wording comes from the existing shared `MOUNTED_OPERATIONS` catalog; FEAT-047's feature-local `API_CONTRACT.md` corroborates the route and behavior.
- FEAT-047's approved Plan Revision 1 and existing `TASK_APPROVAL.md` authorize its historical BE1 runtime scope; they do not by themselves approve this new bounded correction. This Draft 1 requires a separate owner approval before implementation.

## 4. Exact implementation scope

### E — May edit after separate approval

| Path | Last-observed bytes | Last-observed SHA-256 | Permitted change |
|---|---:|---|---|
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | 17,386 | `B336C729C0D791F3DEA8F282F30EB0E7FF41B503F50798B24C98DC70DB00D3CC` | Add only the exact `description` metadata to the existing artifact-upload route decorator. Stop before editing if the pin differs. |

### R — Read-only references

| Path | Bytes | SHA-256 | Use |
|---|---:|---|---|
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 | `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` | Source of the expected `MOUNTED_OPERATIONS` purpose. |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,753 | `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` | Existing regression test and explicit catalog/un-cataloged boundary; do not edit. |
| `features/FEAT-047-be1-runtime-backend/artifacts/API_CONTRACT.md` | 23,512 | `DAB6A73D041B41D31EC4D5A7599BABBAB9B3EA1F25DDDCCF01470CE3F0815994` | Existing BE1 route behavior and response contract. |
| `features/FEAT-047-be1-runtime-backend/plan/PLAN.md` | 9,153 | `452E8DAC726B763D8094EA34BA81C766B04A96BD337B18E018962EAF7718EF60` | Historical approved FEAT-047 Plan Revision 1; preserve unchanged. |
| `features/FEAT-047-be1-runtime-backend/approvals/TASK_APPROVAL.md` | 1,266 | `F628501E19C00B71DF7954B2105DBF8C9E4B6B27476129E4604A15606265FC54` | Historical approval; preserve unchanged until a separate approval is explicitly requested. |
| `docs/context/SRS_AUTHORITY.md` | 4,054 | `E3783924BCDF0327CCCDA8806773FB4407ED311C7074289D74AB9B9124EAF662` | Current SRS source routing. |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 634,291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` | Canonical working SRS Rev67; read-only. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md` | 3,456 | `D2C84E356C45653AB9973D94DFD09E4A8DB8439EA01BE4DA2D64B0849B80E5B2` | Originating M2 verification finding; read-only. |

No test, catalog, SRS, decision, approval, M2 allowlist, or unrelated BE1 path may be edited under this task.

## 5. Acceptance criteria

- **AC-01:** The existing `POST /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts` OpenAPI operation has a `description` exactly equal to its `MOUNTED_OPERATIONS` purpose.
- **AC-02:** The route's runtime behavior, request and response shape, authorization, persistence, consent, status code, and error behavior remain unchanged.
- **AC-03:** `test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates` is run once after the fix under this task's separate approval. If it fails on another operation outside this task, record the full failure and stop; do not edit or exclude that operation without a separate scope decision.
- **AC-04:** Evidence records the changed file's before/after bytes and SHA-256, the exact test output, and confirmation that no other path changed.

## 6. Proposed command budget and environment

This is a proposal only; it grants no command permission. After task approval, allow at most one focused pytest invocation for AC-03 from `backend/` using the already-prepared isolated Python 3.12 environment. Do not install or sync dependencies. If the environment is unavailable, return a PowerShell command card to the owner. No mypy or Ruff run is proposed because the only permitted code change is a decorator string; M2's separate command ceilings remain unchanged.

No backend server, database, migration, Docker, provider, network, Modal, real child data, staging, commit, or push is needed or authorized for this metadata-only task. `OWNER_MODAL_CALL_APPROVED=NO`.

## 7. Sequence and approval boundary

1. Owner reviews and explicitly approves this separate BE1 task and its one-test command budget.
2. Implementation starts in a dedicated BE1 worktree after preflight re-hashes the E path and all read-only references.
3. Add only the route description; capture exact diff and file pins.
4. Run the one approved focused test and record actual output. If another catalog operation fails, stop and report it rather than expanding this task.
5. Leave FEAT-047 implementation status and existing approvals unchanged unless the owner separately authorizes an update.

This draft does not approve implementation, change the M2 S2 allowlist, satisfy M2's remaining mypy/Ruff gates, approve S2, or authorize S3.
