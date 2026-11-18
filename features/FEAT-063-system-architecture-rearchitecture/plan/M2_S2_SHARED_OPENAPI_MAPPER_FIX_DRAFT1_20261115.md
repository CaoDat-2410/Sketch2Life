# FEAT-063 M2 S2 Shared OpenAPI Catalog Mapper Correction — Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED.
- **Task type:** Plan-only proposal for a shared OpenAPI metadata-mapping defect found during M2 S2 verification.
- **Date:** 2026-11-15.
- **Scope owner:** Not assigned in this draft.
- **Approval boundary:** This document is not a Task Approval, implementation allowlist, launch signal, test authorization, or amendment to D-207. It authorizes no code, test, validator, database, migration, provider, network, Modal, staging, commit, or push action.
- **OWNER_MODAL_CALL_APPROVED:** NO.

## 1. Problem and diagnostic evidence

The coordinator's authorized in-memory diagnostic verified that `sketch2life.__file__` and the imported app factory resolved from the M2 worktree. Before generating the schema, `app.openapi_schema` was not populated. The diagnostic found zero direct path-and-POST matches for the artifact-upload operation in `application.routes`; after one `app.openapi()` call, the runtime tag remained `BE1 artifacts`. This is the evidence for the mapper miss and rules out reuse of an already-populated schema cache in that diagnostic. The route is nested under FastAPI's internal `_IncludedRouter` representation, which is not itself the concrete leaf route expected by the mapper's flat lookup.

The source location to address is the route lookup in backend/src/sketch2life/interfaces/http/app.py:1125-1153. It filters application.routes by exact path and method, compares the endpoint name with the catalog handler suffix, continues when the names differ, and otherwise applies catalog metadata.

The recorded FEAT-047/S2 failure showed that the description assertion passed after the separately approved description-only correction, then the catalog assertion at backend/tests/contract/test_openapi_contract_catalog.py:308 saw runtime tag BE1 artifacts where the mapped catalog tag is Session Artifacts. The coordinator's in-memory diagnostic supplies the runtime evidence above; this plan does not claim a second reproduction.

The exact public tag is a code-catalog and test contract: MOUNTED_OPERATIONS supplies BE1 — Session Artifacts and public_tag_name maps it to Session Artifacts. This plan creates no product requirement and makes no SRS change.

## 2. Authority and existing boundaries

- D-207 approves only the pinned M2 S2 implementation allowlist and its enumerated behavior. Listing app.py in that allowlist for the route-specific Parent error-envelope work does not authorize a generic OpenAPI mapper change.
- The FEAT-047 approval and the one-time FEAT-063 overlay cover only adding the exact catalog description to the existing artifact-upload route and one combined S2 test invocation. That invocation has been consumed. They do not cover tag mapping, generic route discovery, catalog changes, or a retry.
- The existing FEAT-063 approval for Draft 18 and D-207 remain unchanged. S2 remains incomplete and this proposal does not approve S2 or S3.
- Preserve the router decorators, MOUNTED_OPERATIONS, PUBLIC_TAG_RENAMES, mounted/unmounted operation sets, and product route surface. Do not edit FEAT-047 approval records, FEAT-063 decisions or approvals, the SRS, or the existing FEAT-047 description plan.
- No code, test, validator, or runtime command was run for this planning task.

## 3. Proposed implementation scope

The following is a proposed file allowlist only. It is not effective until separately reviewed and approved.

| Class | Path | Proposed permitted change |
|---|---|---|
| E | backend/src/sketch2life/interfaces/http/app.py | Replace the mapper's flat route lookup with concrete mounted-route resolution that reaches endpoints nested below included routers. Retain the exact method, effective OpenAPI path, and handler identity checks. Apply existing catalog metadata only after those checks succeed. Do not alter application route composition or the catalog. |
| E | backend/tests/contract/test_openapi_contract_catalog.py | Keep the catalog assertions intact. Make only the runtime_openapi fixture deterministic and isolated: disable dotenv loading for Settings and CoreDatabaseSettings, clear any database URL, use local synthetic settings, put the LocalArtifactStore root beneath pytest tmp_path, and disable AWS metadata/config credential discovery for this in-memory schema test. |
| N | backend/tests/contract/test_openapi_nested_route_mapper.py | Add a focused regression test using nested FastAPI routers. Assert that the metadata resolver reaches the concrete endpoint and applies the catalog description and public tag only to the matching method/path/handler. The test must not start a server, invoke lifespan, use a database, or contact a provider. |

### Read-only references

The following remain outside the proposed edit scope: backend/src/sketch2life/interfaces/http/openapi_contract.py; backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py; backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py; backend/src/sketch2life/interfaces/http/routers/be1_runtime.py; backend/src/sketch2life/interfaces/http/router_composition.py; backend/tests/contract/test_app_composition.py; backend/pyproject.toml; backend/uv.lock; the FEAT-047 plan, approval and evidence; the FEAT-063 decisions, approvals, M2 plans and reviews; and docs/context/PROJECT_CONTEXT.md and docs/context/SOURCE_REGISTER.md.

No other path may be added without a revised plan, fresh pin review, independent review, and separate owner approval. If a safe implementation requires a FastAPI dependency change, catalog/tag change, router/decorator edit, or another path, stop and return the scope question to the owner.

## 4. Proposed implementation behavior

1. Resolve a concrete mounted endpoint for each OpenAPI method/path before comparing it with the handler recorded in MOUNTED_OPERATIONS.
2. Support nested included routes only through a documented public route-resolution API that returns the concrete leaf route. Do not inspect or depend on FastAPI's private _IncludedRouter internals under this draft; if the pinned FastAPI version has no suitable public API, stop for explicit owner choice as stated below.
3. Compare the effective route method and path used by OpenAPI, then compare the resolved endpoint name with the catalog handler suffix. A failed or ambiguous match must not apply metadata to a different operation.
4. Preserve the existing skip behavior for absent catalog entries and genuine handler mismatches. Do not guess a handler from tag, description, or route order.
5. After a verified match, preserve the existing metadata behavior for catalog purpose, public_tag_name(contract.tag), and published response metadata. Keep route-specific exceptions and additions unchanged.
6. Do not change routes, HTTP behavior, authorization, request/response schemas, operation IDs, SRS requirements, provider behavior, database behavior, or mounted/unmounted candidate membership.

FastAPI's `_IncludedRouter` is a private implementation detail, not a supported public route type. Before implementation, check whether the pinned FastAPI version provides a documented public route-resolution API that returns concrete included leaf routes with effective paths and methods. The current evidence does not establish such an API. If no suitable public API is available, stop and obtain an explicit owner choice before relying on `_IncludedRouter` internals or changing the FastAPI version; do not make either choice implicitly.

## 5. Acceptance criteria — future evidence only

- **OA-MAP-01:** A focused nested-router regression test proves that a concrete leaf route is found below an included-router container using its effective path, method, and endpoint.
- **OA-MAP-02:** The resolver applies metadata only when the method, path, and handler all match the catalog entry; an absent route, wrong handler, or ambiguous match remains skipped.
- **OA-MAP-03:** The existing runtime catalog test passes all MOUNTED_OPERATIONS description and public-tag assertions, including POST /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts with tag Session Artifacts.
- **OA-MAP-04:** The OpenAPI operation count, paths, operation IDs, request/response schemas, mounted/unmounted sets, and route-composition surface remain unchanged. Only metadata already defined for a matching catalog operation is applied.
- **OA-MAP-05:** The existing app-composition smoke test passes when run with the isolated pytest base described in Section 6. No database connection, server lifespan, provider/network call, or Modal call is part of acceptance.
- **OA-MAP-06:** The catalog test fixture loads no .env, receives no database URL or real credentials, and places its local artifact-store directory beneath pytest's isolated temporary base.

All criteria are planned checks. None was run in this plan-only task.

## 6. Test plan and pytest temp/cache isolation

The prior recorded selection failed while pytest created its default per-user temporary root and also reported cache-provider writes denied under backend/.pytest_cache/v/cache. The next separately approved test run should use the existing ignored tmp/m2-s2-validation directory as the basetemp parent, a fresh GUID child for each invocation, and disable pytest's cache provider:

1. Run from the worktree backend directory with the already-prepared Python 3.12 environment; do not install or sync dependencies.
2. Confirm tmp/m2-s2-validation exists and can be traversed before invocation. Use a new GUID child below it for --basetemp; check that the child does not already exist. Pytest may clear the supplied basetemp, so never reuse a directory or put user files there. If the parent is missing or inaccessible, stop before invoking pytest. If pytest cannot create the fresh child, the single invocation is consumed; stop without retrying or changing ACLs.
3. Pass -p no:cacheprovider so pytest does not write the repository backend/.pytest_cache.
4. Clear PYTEST_ADDOPTS for the child process so hidden basetemp or plugin options cannot override the reviewed command.
5. For the test process, temporarily remove inherited AWS credential and provider-selection variables. Snapshot their values opaquely and only in process memory for restoration in a finally block; do not examine, branch on, print, or log them. Clear access-key and secret-key forms, session/security tokens, the legacy credential-file variable, profile selectors, web-identity variables, role-session selectors, and container-credential variables. Set AWS_EC2_METADATA_DISABLED=true, AWS_CONFIG_FILE=NUL, and AWS_SHARED_CREDENTIALS_FILE=NUL. Do not supply or use secrets. Restore every changed process variable in finally, including PYTEST_ADDOPTS; do not persist environment changes.
6. In the approved test fixture, disable Settings and CoreDatabaseSettings dotenv loading; clear SKETCH2LIFE_DATABASE_URL; set only local synthetic flags; and place SKETCH2LIFE_BE1_ARTIFACT_ROOT below pytest's tmp_path. Do not inspect or print environment values. If the basetemp parent is missing or inaccessible, stop before invoking pytest. Do not create a permission probe, change ACLs, clear caches, or retry; if the fresh child cannot be created by pytest, the single invocation is consumed.

Proposed single combined targeted invocation, after a separate approval, from backend:

    $pytestBaseParent = '..\..\..\tmp\m2-s2-validation'
    if (-not (Test-Path -LiteralPath $pytestBaseParent -PathType Container)) { throw 'Approved basetemp parent is missing' }
    Get-ChildItem -LiteralPath $pytestBaseParent -ErrorAction Stop | Out-Null
    $pytestBase = Join-Path $pytestBaseParent ('openapi-mapper-' + [guid]::NewGuid().ToString('N'))
    if (Test-Path -LiteralPath $pytestBase) { throw 'Select a fresh pytest base directory' }
    $processVars = @('PYTEST_ADDOPTS', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_ACCESS_KEY', 'AWS_SECRET_KEY', 'AWS_SESSION_TOKEN', 'AWS_SECURITY_TOKEN', 'AWS_CREDENTIAL_FILE', 'AWS_PROFILE', 'AWS_DEFAULT_PROFILE', 'AWS_ROLE_ARN', 'AWS_ROLE_SESSION_NAME', 'AWS_WEB_IDENTITY_TOKEN_FILE', 'AWS_CONTAINER_CREDENTIALS_RELATIVE_URI', 'AWS_CONTAINER_CREDENTIALS_FULL_URI', 'AWS_CONTAINER_AUTHORIZATION_TOKEN', 'AWS_CONTAINER_AUTHORIZATION_TOKEN_FILE', 'AWS_CONFIG_FILE', 'AWS_SHARED_CREDENTIALS_FILE', 'AWS_EC2_METADATA_DISABLED')
    $savedProcessVars = @{}
    try {
        foreach ($name in $processVars) {
            $savedProcessVars[$name] = [System.Environment]::GetEnvironmentVariable($name, 'Process')
            [System.Environment]::SetEnvironmentVariable($name, $null, 'Process')
        }
        [System.Environment]::SetEnvironmentVariable('PYTEST_ADDOPTS', '', 'Process')
        [System.Environment]::SetEnvironmentVariable('AWS_EC2_METADATA_DISABLED', 'true', 'Process')
        [System.Environment]::SetEnvironmentVariable('AWS_CONFIG_FILE', 'NUL', 'Process')
        [System.Environment]::SetEnvironmentVariable('AWS_SHARED_CREDENTIALS_FILE', 'NUL', 'Process')
        & ..\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider ("--basetemp=" + $pytestBase) tests/contract/test_openapi_nested_route_mapper.py tests/contract/test_openapi_contract_catalog.py::test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate
    }
    finally {
        foreach ($name in $processVars) {
            if ($savedProcessVars.ContainsKey($name)) { [System.Environment]::SetEnvironmentVariable($name, $savedProcessVars[$name], 'Process') }
        }
    }

## 7. Proposed command ceilings

These ceilings are proposals for a future separately approved implementation task. They do not revive the consumed FEAT-047/S2 pytest authorization or extend D-207.

| Check | Proposed maximum | Scope |
|---|---:|---|
| Targeted pytest | 1 combined invocation | The exact three selections in Section 6; no separate rerun or alternate selection. |
| Mypy | 1 run | Exact command from backend: & ..\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe -B -m mypy src/sketch2life/interfaces/http/app.py tests/contract/test_openapi_contract_catalog.py tests/contract/test_openapi_nested_route_mapper.py. |
| Ruff | 1 run | Exact command from backend: & ..\..\..\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe -B -m ruff check src/sketch2life/interfaces/http/app.py tests/contract/test_openapi_contract_catalog.py tests/contract/test_openapi_nested_route_mapper.py. |
| Harness validator | 1 final run | From the worktree root, only after implementation approval. |
| Repository-security validator | 1 final run | From the worktree root, only after implementation approval. |
| Architecture validator | 1 final run | From the worktree root, only after implementation approval. |
| git diff --check | 1 final run | From the worktree root, only after implementation approval. |

No full test suite, dependency installation/synchronization, database or migration command, server, Docker, network/provider/Modal command, staging, commit, or push is included. If a command is unavailable, stop and provide a ready-to-run command card; do not exceed a ceiling or substitute a check.

## 8. Stop conditions and owner approvals needed

Stop and return to the owner if:

- Current pins no longer match the input snapshot in Section 9 before any future implementation.
- The mapper cannot resolve nested routes while preserving exact path/method/handler identity within the proposed E/N paths.
- A route, catalog, public tag rename, dependency, OpenAPI operation surface, or any file outside the proposed allowlist would need to change.
- The regression test requires a database, provider, network, Modal, server lifespan, real secret, or a non-isolated filesystem path.
- The unique pytest basetemp cannot be used without ACL or filesystem changes.
- The targeted test fails or is unavailable; no retry is proposed by this draft.

Before implementation, the owner must separately approve this plan and an exact implementation allowlist with fresh pins, and provide an explicit launch instruction. Any later test invocation requires that approval; previous D-207 and FEAT-047 test authorization is not reusable. A separate independent cold review of the final implementation plan/allowlist is proposed before approval.

## 9. Input pins observed 2026-11-15

These pins describe the current planning inputs, including files already modified in the M2 worktree. They are not implementation approval. A future task must rehash its approved inputs and stop on any hard-pin mismatch.

| Input path | Bytes | SHA-256 |
|---|---:|---|
| backend/src/sketch2life/interfaces/http/app.py | 74,637 | E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031 |
| backend/src/sketch2life/interfaces/http/openapi_contract.py | 1,377,229 | 175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE |
| backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py | 49,654 | E16DE02140E7977A014F32D9CF131DAC8FC63EA622CEDD26B702958D7B92BB09 |
| backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py | 17,501 | 7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF |
| backend/src/sketch2life/interfaces/http/routers/be1_runtime.py | 1,014 | 89C54AC8EDB63FD2DC9A92910BE817645D9429B8A54E0485F86A826BA6A863A7 |
| backend/src/sketch2life/interfaces/http/router_composition.py | 3,743 | 2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463 |
| backend/tests/contract/test_openapi_contract_catalog.py | 18,753 | BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198 |
| backend/tests/contract/test_app_composition.py | 13,507 | 1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52 |
| backend/pyproject.toml | 3,383 | 35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2 |
| backend/uv.lock | 398,117 | 830842CFAC04B5CA1EBDAA733E281F7D0AB9A4C94B19CFDF2B93E66854DBFB13 |
| features/FEAT-047-be1-runtime-backend/plan/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_DRAFT1_20261114.md | 7,886 | 235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B |
| features/FEAT-047-be1-runtime-backend/approvals/TASK_APPROVAL.md | 3,023 | 67A69DF8CEE0344D8F5D8D79B5F0D432490FE0D7F1486ED8A58C806ADD451063 |
| features/FEAT-047-be1-runtime-backend/evidence/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_EVIDENCE_20261114.md | 13,596 | 0CF2C87996252058544D5F943967AB9F3A4E7A292D28CF1F6413620BFA6D8871 |
| features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md | 212,068 | 191D68D7344FE2146E75F339185065234D092887C341AB487FB2DBEA8511C2BF |
| features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md | 410,676 | C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088 |
| features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md | 14,768 | 7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_ALLOWLIST_COLD_REVIEW_R2_20261114.md | 2,715 | 6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D |
| features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md | 101,153 | 5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_DRAFT18_COLD_REVIEW_20261114.md | 5,169 | 4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md | 3,456 | D2C84E356C45653AB9973D94DFD09E4A8DB8439EA01BE4DA2D64B0849B80E5B2 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md | 25,879 | F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55 |
| docs/context/SOURCE_REGISTER.md | 115,881 | 39D8BD4F68ECCB75FF16BBFE775A9BBDB13151E7BD948EE1791071A0DA0B39FC |
| features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md | 113,670 | 7137B59263B7B886F3EB5A18D741DB08F976E3E08947C7BE80679ED3FE50EDEF |

## 10. Work performed for this draft

This revised document is the sole output of the current planning task. No source or test file, other plan, context file, SRS, decision, approval, or prior evidence was changed. No test, validator, typecheck, linter, OpenAPI generation, backend/app execution, database/migration, Docker, network, provider, or Modal command was run. Nothing was staged, committed, or pushed.

End status remains DRAFT / NOT APPROVED / NOT LAUNCHED. OWNER_MODAL_CALL_APPROVED=NO.
