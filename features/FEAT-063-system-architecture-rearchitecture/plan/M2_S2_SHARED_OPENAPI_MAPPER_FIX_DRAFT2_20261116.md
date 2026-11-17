# FEAT-063 M2 S2 Shared OpenAPI Catalog Mapper Correction — Draft 2

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED.
- **Task type:** Planning reconciliation for the shared OpenAPI metadata-mapping defect recorded during M2 S2 verification.
- **Observation:** 2026-11-15 17:57 UTC.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`.
- **Owner approval:** None for this correction. D-207 and the one-time FEAT-047/S2 verification authorization do not authorize this work.
- **OWNER_MODAL_CALL_APPROVED:** NO.

Draft 2 supersedes Draft 1 only for current input pins, environment facts, and the readiness gates below. Draft 1 remains historical evidence. The proposed source/test scope and acceptance intent are retained, subject to independent review and a separate implementation approval.

## 1. Problem and evidence boundary

The previously recorded combined S2 verification reported that the artifact-upload description assertion passed, then the OpenAPI catalog assertion at `backend/tests/contract/test_openapi_contract_catalog.py:308` observed tag `BE1 artifacts` where the catalog-derived public tag is `Session Artifacts`. The authorized in-memory diagnostic recorded zero direct path-and-POST matches in `application.routes` before schema generation and the tag remained `BE1 artifacts` after one `app.openapi()` call. This draft does not claim a new reproduction.

Current static source at the pinned `backend/src/sketch2life/interfaces/http/app.py` assigns catalog metadata only after it finds an exact path/method route and confirms the endpoint handler name. The artifact router is nested through the BE1 router composition. This supports the recorded mapper-miss explanation; runtime behavior remains based on the earlier diagnostic, not a run performed for Draft 2.

This is a shared OpenAPI catalog/code-test contract issue, not a new product API or SRS requirement. The existing catalog and assertion require the public tag `Session Artifacts`; no route, tag catalog entry, router decorator, operation surface, or SRS text is proposed to change.

## 2. Authority and scope boundaries

- FEAT-063's active working requirements baseline is the unsigned Rev68 in the active worktree. Rev68 remains a draft and does not turn this OpenAPI metadata issue into a product requirement.
- D-207 approves only the exact M2 S2 allowlist and enumerated behavior. Although `app.py` appears there for Parent error-envelope work, that does not authorize a generic OpenAPI mapper change.
- The FEAT-047 approval and one-time overlay authorize only the artifact-upload description correction and one combined S2 test invocation. That invocation is consumed. They do not authorize tag mapping, route discovery, dependency/environment changes, or another test run.
- The existing implementation approval does not approve this plan, any new code, or S3. M2 S2 remains incomplete; S3 remains separately gated.
- No edit to `DECISIONS.md`, `TASK_APPROVAL.md`, SRS, DTR, router composition, route decorators, catalog metadata, FEAT-047 records, or lock/manifest is proposed.

## 3. Updated environment and pin findings

Immediately before adding Draft 2, the worktree was observed at the identity above with 68 status paths (24 modified, 44 untracked) and zero staged paths. The previously prepared interpreter exists at `D:\GitHub\Sketch2Life\tmp\m2-s2-validation\python312\.venv\Scripts\python.exe`; the proposed relative path from `backend/` in Draft 1 resolves to this repository-root `tmp` environment.

The installed package metadata in that environment reports FastAPI **0.162.7**. The current `backend/uv.lock` pins FastAPI **0.162.0**; `backend/pyproject.toml` permits `>=0.141,<1`. Thus the environment is allowed by the broad project range but is **not resolved to the committed lock**. The prior diagnostic and the Draft 1 test command use this non-lock-resolved environment. Do not treat its behavior as verification of the locked dependency set.

Before a future test run, the owner must approve or provide a dedicated environment synchronized to the exact current lock. No installation or synchronization command is authorized by this draft. Do not silently change `uv.lock`, reuse the 0.162.7 environment as lock-equivalent, or install packages into another environment.

The installed 0.162.7 source contains FastAPI's private `_IncludedRouter` class and methods on that private class. The local inspection did not establish a documented public FastAPI API that resolves nested included routers to concrete leaf routes. The corresponding API availability in locked FastAPI 0.162.0 is **NOT VERIFIED**. Do not infer that a public API exists or does not exist from this limited source search.

## 4. Proposed implementation scope — unchanged, not approved

| Class | Path | Proposed permitted change |
|---|---|---|
| E | `backend/src/sketch2life/interfaces/http/app.py` | Resolve a concrete mounted route for each OpenAPI method/path, then retain the exact effective method/path and handler identity checks before applying existing catalog metadata. Do not alter route composition or catalog contents. |
| E | `backend/tests/contract/test_openapi_contract_catalog.py` | Keep assertions intact. Isolate the schema-only fixture from dotenv/database credentials, use local synthetic settings, place the artifact root under `tmp_path`, and prevent provider credential discovery. |
| N | `backend/tests/contract/test_openapi_nested_route_mapper.py` | Add a focused nested-router regression that proves matching method, effective path, and endpoint identity before metadata is applied. It must not start a server/lifespan or use a database, network, provider, or Modal. |

The proposed scope excludes route/catalog/lock changes and all other files. If a solution needs a FastAPI dependency change, private router internals, a route/decorator/composition edit, a catalog change, or any additional path, stop and return a written scope/options question to the owner. No implementation direction is selected here.

## 5. Readiness gate for route resolution

Before this plan can be approved for implementation, a read-only feasibility review must identify the exact documented public API, if one exists, for the locked FastAPI 0.162.0 dependency and show that it provides the concrete leaf endpoint, effective path, and method needed by the mapper.

If no such documented public API is available, stop. Present the owner with the evidence and bounded options, including whether to authorize a narrowly tested dependency-internal approach or a separately reviewed dependency/version change. Do not choose between those options, inspect private internals in implementation, or change a dependency without explicit owner direction.

The current environment does not pass this gate: it is FastAPI 0.162.7, and the public-API question for 0.162.0 remains unverified.

## 6. Future acceptance evidence

These are proposed checks only; none was run for Draft 2.

- **OA-MAP-01:** A nested-router regression proves the intended concrete leaf route can be resolved using the approved route-resolution approach.
- **OA-MAP-02:** Catalog metadata is applied only when method, effective path, and handler all match; missing, mismatched, or ambiguous routes remain untouched.
- **OA-MAP-03:** The existing runtime catalog test passes description and public-tag assertions, including the artifact-upload operation with `Session Artifacts`.
- **OA-MAP-04:** Paths, methods, operation IDs, schemas, responses, route-composition surface, and mounted/unmounted operation sets remain unchanged.
- **OA-MAP-05:** The app-composition test passes using an owner-approved isolated pytest base; no database connection, lifespan, provider, network, or Modal call occurs.
- **OA-MAP-06:** The catalog test fixture loads no `.env`, receives no database URL or real credentials, and stores its local artifact root beneath pytest's isolated temporary directory.
- All command output must identify the exact Python/FastAPI environment. A run against FastAPI 0.162.7 is not evidence for the lock-pinned 0.162.0 baseline.
- These checks do not by themselves close M2 S2. The prior report also records 335 mypy errors and 17 Ruff diagnostics, and the authorized S2 command ceilings are consumed. Any required S2-wide evidence needs its own current, approved scope and fresh ceilings; do not represent the proposed focused checks as resolving the prior aggregate results.

## 7. Environment and command authorization

Draft 1's proposed isolated pytest base under repository-root `tmp/m2-s2-validation`, unique child directory, disabled pytest cache provider, and synthetic/offline fixture boundaries remain candidate safeguards. They are not authorization to invoke tests. The prior `tmp_path` setup failure was an access-denied result; its underlying filesystem cause is **NOT VERIFIED**. Do not probe ACLs, delete caches, or change permissions.

The proposed command ceilings from Draft 1 remain proposals only: one combined targeted pytest invocation, one focused mypy run, one focused Ruff run, and one final run of each validator plus `git diff --check`. Before use, an implementation allowlist and exact command/environment approval must be independently reviewed and explicitly approved by the owner. A missing environment, failed preflight, unavailable tool, or failed command consumes the approved attempt and stops; no retry or substitution is implied.

No tests, validators, typecheck, lint, diff-check, app/OpenAPI generation, backend/runtime, database/migration, Docker, install/sync, network, provider, Modal, staging, commit, or push command was run for Draft 2.

## 8. Required review and owner gates

1. Obtain a separate fresh-context cold review of Draft 2 and the updated pins. Draft 1 has no independent cold-review report; no review is claimed here.
2. Resolve the locked-version public route-resolution feasibility gate above.
3. If the owner elects to continue, prepare an exact implementation allowlist and an approved lock-matched environment/command plan with fresh input pins. Obtain separate Task Approval and a direct launch instruction.
4. After implementation, report actual per-command outputs and preserve all failures. Do not claim S2 complete from the mapper test alone; S2 closure and S3 remain distinct owner gates.

## 9. Current input pins

Pins were re-read on 2026-11-15 17:59:07 UTC. Compared with Draft 1, 20 of its 23 values still match and three have changed; those three rows are updated below. The table also adds current SRS authority, SRS, and Draft 1 pins. All 26 listed values matched at the stated observation time. Future implementation must re-hash every selected input and stop on any hard-pin difference.

| Input path | Bytes | SHA-256 |
|---|---:|---|
| `backend/src/sketch2life/interfaces/http/app.py` | 74,637 | `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 | `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` |
| `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | 49,654 | `E16DE02140E7977A014F32D9CF131DAC8FC63EA622CEDD26B702958D7B92BB09` |
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | 17,501 | `7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF` |
| `backend/src/sketch2life/interfaces/http/routers/be1_runtime.py` | 1,014 | `89C54AC8EDB63FD2DC9A92910BE817645D9429B8A54E0485F86A826BA6A863A7` |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | 3,743 | `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,753 | `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` |
| `backend/tests/contract/test_app_composition.py` | 13,507 | `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` |
| `backend/pyproject.toml` | 3,383 | `35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2` |
| `backend/uv.lock` | 398,117 | `830842CFAC04B5CA1EBDAA733E281F7D0AB9A4C94B19CFDF2B93E66854DBFB13` |
| `features/FEAT-047-be1-runtime-backend/plan/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_DRAFT1_20261114.md` | 7,886 | `235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B` |
| `features/FEAT-047-be1-runtime-backend/approvals/TASK_APPROVAL.md` | 3,023 | `67A69DF8CEE0344D8F5D8D79B5F0D432490FE0D7F1486ED8A58C806ADD451063` |
| `features/FEAT-047-be1-runtime-backend/evidence/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_EVIDENCE_20261114.md` | 13,596 | `0CF2C87996252058544D5F943967AB9F3A4E7A292D28CF1F6413620BFA6D8871` |
| `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 216,212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 410,676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md` | 14,768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_ALLOWLIST_COLD_REVIEW_R2_20261114.md` | 2,715 | `6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_DRAFT18_COLD_REVIEW_20261114.md` | 5,169 | `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md` | 3,456 | `D2C84E356C45653AB9973D94DFD09E4A8DB8439EA01BE4DA2D64B0849B80E5B2` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| `docs/context/SOURCE_REGISTER.md` | 116,802 | `AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B` |
| `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | 117,511 | `BBE6098147F8507C5B5C9489F9C5ADBA2DB725BBBDE4F54A67F9DD36D9B940E9` |
| `docs/context/SRS_AUTHORITY.md` | 4,313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` |
| `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 639,948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT1_20261115.md` | 20,784 | `48B7A95133BDEAB9D14EE947BAF44D5B475ED60B99D118EAC24B51C9E0561BD6` |

## 10. Work performed for Draft 2

This file is a planning-only reconciliation. No code, test, approval, decision, SRS, or prior evidence was changed. No test, validator, typecheck, lint, diff-check, app/OpenAPI generation, backend/runtime, database/migration, Docker, install/sync, network, provider, Modal, staging, commit, or push command was run. Draft 2 remains DRAFT / NOT APPROVED / NOT LAUNCHED.
