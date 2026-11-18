# Out-of-scope OpenAPI catalog finding — FEAT-063 M2 S2

**Recorded:** 2026-11-14  
**Disposition:** Confirmed in the current worktree; outside the current M2 S2 implementation file allowlist; not fixed.

## Scope determination

The current `M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md`, Section 2, is an exact file allowlist. It does not include `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py`. That route file has no current working-tree modification. The route surfaced while running an M2 targeted selection because the selection includes the repository-wide OpenAPI contract catalog test; this does not make the BE1 route an authorized S2 implementation path. The finding is not evidence that M2 introduced the issue.

The allowlist pin observed for the scope check is 14,768 bytes, SHA-256 `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8`.

## Observed failure

The owner-run targeted pytest selection collected 82 tests: 81 passed and 1 failed in 16.17 seconds. The failure was `test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates` at `backend/tests/contract/test_openapi_contract_catalog.py:307`, where the runtime operation is accessed through `operation["description"]`.

The first missing description identified by the in-memory diagnostic was:

- Method: `post`
- Path: `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts`
- Expected purpose: `Tải một tệp kết quả hoặc tư liệu vào buổi học của tổ chức.`
- Actual description: `MISSING`

`MOUNTED_OPERATIONS` contains this purpose in `backend/src/sketch2life/interfaces/http/openapi_contract.py` at line 80. The source route is `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py:278`; its current decorator declares the path and status code without an explicit description.

The cancel operation is not the cause identified here. It is listed in `PR22_UNCATALOGUED_OPERATIONS` at `backend/tests/contract/test_openapi_contract_catalog.py:93`; the test asserts that set is disjoint from `MOUNTED_OPERATIONS` at line 246.

## Pins observed

| File | Bytes | SHA-256 |
|---|---:|---|
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | 17,386 | `B336C729C0D791F3DEA8F282F30EB0E7FF41B503F50798B24C98DC70DB00D3CC` |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 | `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,753 | `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md` | 14,768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` |

## Limits and follow-up

The diagnostic output was truncated after the first missing entry, so any additional missing or mismatched descriptions remain unverified. No source or test was changed, and no test or other check was rerun for this note. The worktree had zero staged paths at recording time; no commit or push was made.

Do not edit `be1_artifacts.py` as part of the current S2 implementation. Handle the documentation-only BE1 route correction in a separate BE1 task, or formally revise the S2 allowlist and obtain its required review and approval before editing that file. Do not weaken the catalog test to hide this finding.