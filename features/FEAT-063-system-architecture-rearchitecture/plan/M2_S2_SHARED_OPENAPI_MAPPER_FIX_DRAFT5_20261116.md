# FEAT-063 M2 S2 Shared OpenAPI Catalog Mapper — Draft 5

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.** This is a planning-only successor to Draft 4. It records the owner's Option A direction and incorporates Draft 4's cold-review corrections. It grants no source or test edits, dependency changes, installation/synchronization, test or validator runs, database/runtime/network/provider/Modal activity, staging, commit, or push. Drafts 1–4 and the Draft 2 cold-review thread remain unchanged. `OWNER_MODAL_CALL_APPROVED=NO`.

**Date:** 2026-11-16  
**Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`.  
**Purpose:** Record the owner's contract-identity choice and correct the proposed acceptance criteria for a future bounded OpenAPI catalog mapper change. This does not authorize implementation, tests, or claim a new defect reproduction or M2 S2 completion.

## 1. Authority and current state

- The active BE worktree's `docs/context/SRS_AUTHORITY.md` selects unsigned FEAT-063 v2.7-draft Rev68 as the current working SRS. Rev68 remains a draft. The root checkout's SRS authority still points to unsigned Rev60; the two worktrees have different SRS bytes. This plan follows the BE worktree's Rev68 authority and does not change either pointer.
- SRS §21 describes API contract shape and states that route shape is to be frozen in OpenAPI. The mapper issue concerns how the existing code applies an existing catalog; it adds no product endpoint or SRS requirement.
- D-207 authorizes only its pinned S2 allowlist and enumerated behavior. Its inclusion of `app.py` for the Parent error-envelope task does not authorize a general OpenAPI mapper change. The FEAT-047 artifact-upload overlay and the combined S2 verification invocation were one-time and are consumed. This plan has no implementation or test-run authority.
- On 2026-11-16, the owner selected Option A: for this mapper, exact public OpenAPI method/path plus a preserved, unique `operationId` is sufficient contract identity; Python callable binding is not required. This is a planning direction only. It does not create a DECISIONS.md record, implementation approval, test approval, or launch instruction.
- The current S2 implementation report remains **PARTIAL / NOT COMPLETE**. It records the catalog assertion failure, a later combined invocation exiting 1 with a tag mismatch and an app-composition `tmp_path` setup error, 335 mypy errors, and 17 Ruff diagnostics. Command ceilings are consumed. Nothing here upgrades those results or closes S2.
- M2 S3 Draft 6 is a separate planning draft. S3 remains closed until S2 is accepted and committed and S3 receives its own review, approval, and launch. Neither plan substitutes for the other's gate.

## 2. Current source behavior and evidence boundary

Static inspection of the pinned `backend/src/sketch2life/interfaces/http/app.py` confirms this sequence:

1. `build_runtime_openapi_schema()` calls FastAPI's `get_openapi(..., routes=application.routes, ...)` to generate a schema.
2. The custom mapper iterates the generated schema's `paths` and HTTP methods and first looks up `MOUNTED_OPERATIONS[(method.lower(), path)]`.
3. For a catalog hit, it then scans `application.routes` for the first route with the same direct `.path` and `.methods`, reads `route.endpoint.__name__`, and compares that function name with the last `::` component of the catalog's `handler` string. A mismatch skips the catalog mapping.
4. A passing entry applies the catalog description and tag, then the existing catalog response projection. A later pass also supplies the existing `X-Request-ID` parameter/response header contract. Other runtime-schema example amendments remain separate.

The proposed schema-keyed approach would remove only the mapper's additional endpoint lookup. FastAPI would still receive `application.routes` when it generates OpenAPI; Draft 5 does not propose flattening that route collection or inspecting `_IncludedRouter`.

The current check is narrower than “handler identity”: it compares only `__name__` with the catalog function-name suffix. It does not compare the module-qualified callable or the function object. The catalog is a dict keyed by `(method, path)` and its values also contain `handler`, `purpose`, `tag`, authorization notes, and response metadata.

The existing catalog test independently builds OpenAPI operation keys from `(method, path)`. Its pinned profile currently has 151 runtime operations, 134 catalog operations over 118 paths, and 17 explicitly classified runtime-only operations (`PILOT_ONLY_OPERATIONS` plus `PR22_UNCATALOGUED_OPERATIONS`). It checks catalog descriptions/tags, authorization, operation IDs, response sets, and response schemas. A dict literal can silently overwrite a duplicate key before a test inspects the resulting mapping; a separate duplicate-source check is needed if duplicate catalog declarations must be ruled out.

These are source and prior-test-record observations only. The earlier diagnostic recorded the artifact-upload description passing and the catalog tag failing (`BE1 artifacts` versus `Session Artifacts`); its raw route-match diagnostic was not preserved. Draft 4 makes no new runtime claim and does not treat the old zero-direct-match observation as a new reproduction or proven root cause. The cited FastAPI release-notes URL was supplied by the owner; it was not fetched or independently verified because this task is offline.

## 3. Options and recommendation

| Option | Proposed behavior | Benefits | Risks and gate |
|---|---|---|---|
| **A — map by public OpenAPI `(method, path)` key** | Apply each `MOUNTED_OPERATIONS` entry to the generated schema operation at the exact lower-case method and exact path. Do not traverse `application.routes` from the mapper and do not use FastAPI private route classes. Preserve the current response/header projection rules and generated `operationId` values. | Matches the catalog's existing key and OpenAPI's operation slot; avoids route-tree flattening, private router internals, and a dependency change. | Does not verify that the Python endpoint matches the catalog's `handler`; this is the contract-identity tradeoff the owner accepted for planning. A stale catalog entry can apply metadata to a new handler that reuses the same method/path and `operationId`. Exact keys, unique/preserved `operationId` values, and catalog metadata checks remain required. Not verified to fix runtime behavior until separately approved and tested. |
| **B — route-resolution adapter retaining the handler check** | Resolve nested included routers to concrete leaf routes, then compare the effective method/path and the current handler-name value before applying metadata. | Retains a code-to-catalog binding check, subject to its current limitation that it compares names rather than module/callable identity. | A solution based on FastAPI internals is version-sensitive; the currently recorded local package is 0.162.7 while `backend/uv.lock` pins 0.162.0. The exact public/internal surface in the locked version is not verified. The plan must not claim nested route behavior without exact-version evidence. |
| **C — dependency/version change** | Separately review a FastAPI version or dependency strategy that provides a documented route-resolution API for the binding requirement, then update the project constraint/lock only under approval. | Could avoid private internals while preserving stronger implementation binding if the selected, documented API provides it. | Broad backend compatibility and lock changes, installation/synchronization, and version-wide verification. No version is selected; no lock edit or network/package action is authorized. |

**Plan direction selected by the owner:** proceed with Option A at the planning level. Contract identity is the exact method/path key plus the existing generated `operationId` preserved and checked for stability and uniqueness. The mapper may remove its handler-name lookup when a separate exact implementation allowlist and Task Approval authorize the change. This does not claim Python callable identity or authorize implementation. If a future owner decision reverses this direction and requires callable binding, stop and prepare a separately reviewed B/C approach; Option B's current name-suffix check is not a stronger identity proof.

## 4. Proposed scope and allowlist — not approved

This proposed allowlist is for a future, separate task approval. The owner has selected contract identity for planning, but no implementation path is authorized by Draft 5. `E` means proposed edit, `N` proposed new file, and `R` read-only input.

| Mode | Repository path | Proposed use |
|---|---|---|
| E | `backend/src/sketch2life/interfaces/http/app.py` | If Option A is approved, move the existing catalog-to-schema mapping into a schema-only helper using exact `(method, path)` keys. Preserve the current response projection, request-ID header/parameter normalization, and unrelated example amendments. The helper must not access `application.routes` or FastAPI private route objects. |
| E | `backend/tests/contract/test_openapi_contract_catalog.py` | Extend exact operation-set, metadata, `operationId`, and schema-invariant checks against the current explicit exception sets. |
| N | `backend/tests/contract/test_openapi_schema_catalog_mapping.py` | Add isolated tests for exact key mapping, a nested-router-produced schema fixture, duplicate catalog declarations, missing/stale keys, and unrelated-operation preservation. No server/lifespan/database/network/provider is needed for the pure mapper test. |
| R | `backend/src/sketch2life/interfaces/http/openapi_contract.py` | Current catalog keys, handler provenance, and metadata. Do not edit under this proposal. |
| R | `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | Current public tag and response-projection rules. |
| R | `backend/src/sketch2life/interfaces/http/router_composition.py`, `backend/src/sketch2life/interfaces/http/routers/be1_runtime.py`, `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | Composition and route-source context only; no mount/decorator change. |
| R | `backend/tests/contract/test_app_composition.py` | Pin and inspect the exact app-composition test node for a future authorized verification run. |
| R | `backend/pyproject.toml`, `backend/uv.lock` | Verify exact locked environment and preserve dependency files. |
| R | Current FEAT-047 overlay approval/evidence, FEAT-063 decisions/approval, S2 report, S2 Draft 18, Drafts 1–3 and the Draft 2 review thread listed in §8 | Authority, prior limitations, pins, and review history. |

No edit is proposed to `openapi_contract.py`, router composition, route decorators, tag catalog, SRS, DTR, `DECISIONS.md`, `TASK_APPROVAL.md`, old evidence, FEAT-047 records, lock, or project dependency constraints. Any such need stops this scope and requires a reviewed successor plan and owner approval.

## 5. Acceptance criteria proposed for Option A

All items remain proposals. Draft 5 is not evidence or authorization.

1. The mapping helper accepts the generated OpenAPI schema and catalog and addresses an operation only by exact `(method.lower(), path)`. The mapper does not enumerate `application.routes`, flatten the route tree, inspect `_IncludedRouter`, or require a handler-name or callable-identity match. FastAPI may continue to use its public route collection to generate the input schema.
2. Every catalog key exists exactly once in the runtime schema. For the approved profile, the runtime-only key set remains exactly `PILOT_ONLY_OPERATIONS | PR22_UNCATALOGUED_OPERATIONS`. Missing/stale catalog keys and unexpected runtime-only keys fail closed. Compare method/path sets, not counts alone; preserve the current 151 runtime operations, 134 catalog operations, 118 catalog paths, and 17 explicitly classified runtime-only operations as pinned profile expectations.
3. A source-level test parses the `MOUNTED_OPERATIONS` declaration and rejects duplicate `(method, path)` literal keys before Python dict construction can overwrite one. It fails closed if the declaration is no longer a literal mapping the checker understands; runtime uniqueness alone is insufficient.
4. For each catalog key, the public tag equals `public_tag_name(contract["tag"])`. Descriptions follow the existing catalog test contract: exact purpose equality for ordinary keys and `startswith(purpose)` for exactly the five current exception keys: POST `/v1/sessions`, POST `/v1/sessions/{session_id}/media/image`, `RESTORE_CHECKPOINT_OPERATION_KEY`, `PORTFOLIO_OPERATION_KEY`, and GET `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio`. Preserve the restore route's appended Access paragraph and its existing `RESTORE_CHECKPOINT_RESPONSE_DESCRIPTIONS` behavior. Do not force those descriptions to equal purpose or change unrelated descriptions.
5. Catalog response projection matches `published_responses` for exact statuses, media types, schemas, and descriptions, including the restore-specific response descriptions and existing status-pruning rules. Preserve all existing response headers other than the explicit `X-Request-ID` addition/normalization. The current request-ID pass continues to add its optional parameter and response header only under `/api/be1/v1/` and `/v1/parent/profiles` paths.
6. Compare the post-fix runtime schema to a byte-pinned pre-fix runtime schema generated from the same route composition, profile, lock-matched environment, and existing non-mapper amendments. The future Task Approval must pin that baseline and its artifact digest before implementation. Allowed changes are limited to catalog tag/description/response projection on catalog keys, the restore-specific text/response-description behavior above, and the already-defined `X-Request-ID` parameter/header normalization on its existing path prefixes. Existing example amendments remain unchanged.
7. Outside those allowed fields, preserve the exact path and method set, each operation's `operationId` value and uniqueness, security metadata, request parameters, request-body schemas, `components.schemas`, and all other existing response headers. Uncatalogued operations are byte-equivalent at the operation-field level except for the existing `X-Request-ID` normalization when their paths are in scope. The SRS projection's path/method membership remains unchanged; this mapper task adds no endpoint or product schema.
8. A regression identifies catalog operations whose metadata was previously skipped and confirms their exact-key catalog metadata is now present, without claiming route or endpoint behavior changed. A neighboring operation must not receive another key's metadata.
9. A future lock-matched test run demonstrates the pure mapper and the exact app-composition node without database connection/lifespan, dotenv loading, provider credential discovery, network, Modal, or real secrets. The separate approval must pin exact pytest base/cache paths before launch.

The mapper fix alone does not close S2. Existing 81/82, later exit-1, 335-mypy-error, and 17-Ruff-diagnostic results remain in the S2 ledger. S2 closure requires all applicable owner-approved evidence and acceptance; S3 is a later separate gate.

## 6. Future environment and command card — approval required

The local Python 3.12 virtual environment previously inspected reports FastAPI 0.162.7; `backend/uv.lock` pins 0.162.0. The environment is not lock-equivalent. Do not use it to claim locked-version behavior. A future owner approval must provide or authorize an exact lock-matched environment, and any install/sync or network access needs its own explicit scope.

Command template for a separate owner-reviewed command card only. The angle-bracketed pytest paths are placeholders, not launchable values; the future Task Approval must replace them with exact approved absolute paths, pin those paths, and record a direct launch instruction:

```text
python -m pytest -q --basetemp "<PINNED_ABSOLUTE_PYTEST_BASETEMP>" -o "cache_dir=<PINNED_ABSOLUTE_PYTEST_CACHE>" tests/contract/test_openapi_schema_catalog_mapping.py tests/contract/test_openapi_contract_catalog.py tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate
python -m mypy src/sketch2life
python -m ruff check src/sketch2life/interfaces/http/app.py tests/contract/test_openapi_contract_catalog.py tests/contract/test_openapi_schema_catalog_mapping.py
```

Proposed maximum ceilings, all requiring new owner approval: two targeted pytest invocations (initial plus at most one fix-driven rerun); two mypy invocations (fresh baseline and post-edit comparison); two Ruff invocations (initial plus at most one fix-driven rerun). The earlier D-207/FEAT-047 ceilings are consumed and cannot be reused. Preserve the prior 335 mypy errors and 17 Ruff diagnostics as existing debt; a fresh check must report deltas and must not call the old baseline a pass. Any validator, diff check, app/OpenAPI generation, or additional command must be separately named and approved. No command above has run under this plan.

The future Task Approval must replace both placeholders with exact absolute pytest base/cache paths inside the approved isolated temporary root, pin them, disable dotenv, prevent database/provider credential discovery, keep any settings/artifact root inside that root, and specify failure handling. Use pytest `--basetemp` and `-o cache_dir=...` explicitly. The prior Windows `tmp_path` access-denied error remains unexplained; stop on another access denial. Do not probe or change permissions under this plan. No retry is authorized.

## 7. Review and owner gates

The Draft 2 independent cold review returned **ACCEPT WITH CORRECTIONS** and remains planning-only. Draft 3 recorded its evidence qualifications and the locked-version public API feasibility question. Draft 4's independent cold review returned **ACCEPT WITH CORRECTIONS** in thread 01a1e0a2-8fb0-79a2-8e36-b4b1d185ddba, turn 01a1e0a2-954b-72b2-a3bd-79c85dbf8c22, final item msg_0ef7cfb3638fe164016afa069b15e887d082efc23ab4e37309. It identified the five description-prefix exceptions, the restore text/response special cases, the pre-fix comparison baseline and allowed deltas, and explicit pytest base/cache paths. The owner then selected Option A in this conversation. That choice guides planning only; it is not implementation approval. At the time of the Draft 5 review pin, Draft 5 has not been independently reviewed or approved.

Required owner gates before implementation:

1. The owner resolved this proposal's identity direction as Option A: exact method/path plus preserved, unique `operationId` is sufficient. If an implementation later requires Python callable binding or a different identity rule, stop and obtain new owner direction before expanding scope.
2. Approve an exact future allowlist, including any acceptance-test additions, and explicitly scope the generic mapper outside D-207.
3. Provide/approve a lock-matched FastAPI 0.162.0 environment and exact command ceilings, isolation paths, expected evidence, and launch instruction. Do not infer authorization from planning acceptance or the cold-review verdict.

Stop before implementation if the proposed allowlist, exact input pins, lock-matched environment, approved pytest isolation paths, command ceilings, evidence requirements, or direct launch instruction are missing; if a route/catalog/dependency change exceeds §4; if the public schema lacks a unique exact-key operation; or if acceptance would require changing endpoint semantics, routes, method/path, `operationId`, request schemas, component schemas, SRS, DTR, or approval scope.

## 8. Current input pins

Pins below were rechecked from the active worktree and named historical/review sources for this pre-review. All 27 file pins in Draft 3 §9 and all file rows from Draft 4 §8 match their recorded bytes and SHA-256; branch/HEAD still match. The initial Draft 4 values for docs/context/PROJECT_CONTEXT.md and the FEAT-063 SOURCE_REGISTER.md did not match the current files; those initial observations are CHANGED SINCE OBSERVATION and the current rehashed values are recorded below. The FEAT-047 plan's initial SHA-256 was a transcription error and is corrected below. No source file was changed by this recheck. The Draft 2 review observed 69 paths (24 modified, 45 untracked, 0 staged). Later additions of Mapper Draft 3 and S3 Draft 6 brought the pre-Draft-4 snapshot to 71 (24 modified, 47 untracked, 0 staged); Draft 4 brought it to 72 (24 modified, 48 untracked, 0 staged); this Draft 5 file makes the current snapshot 73 (24 modified, 49 untracked, 0 staged): CHANGED SINCE OBSERVATION. This status is not an implementation or clean-baseline claim.

The Draft 2 cold-review result is not stored as a repository evidence file. Its persisted final answer is pinned by thread `01a1e066-0aba-75c3-b9de-40a55c201c97`, turn `01a1e066-109e-77b1-b27e-82d5b11f50dd`, item `msg_00863208b4f239e8016af9f75d98d487d096ac16ac75eac5b2`: 5,702 UTF-8 bytes, SHA-256 `DC9E34062AF4E5F194DCDB4BE536418201554AC94BF5328167818CA0842CC79B`.
The Draft 4 cold-review final answer is in thread 01a1e0a2-8fb0-79a2-8e36-b4b1d185ddba, turn 01a1e0a2-954b-72b2-a3bd-79c85dbf8c22, item msg_0ef7cfb3638fe164016afa069b15e887d082efc23ab4e37309. It returned ACCEPT WITH CORRECTIONS; it remains a chat-only planning review and is not an implementation approval. The owner's direct response on 2026-11-16 selected Option A; this is planning direction, not a Task Approval or launch instruction.

| Input | Bytes | SHA-256 | Authority / limit |
|---|---:|---|---|
| Active worktree `AGENTS.md` | 3,406 | `89ACC84AA4D838730205A03917B40DEB37E9622AAF7092E982476D934EC29A61` | Repository workflow. |
| Root `.codex/sketch2life-harness.md` | 2,178 | `0364DD280483D7AB56EAAF7F0B2CEF56A86D627393CA9996FC88A14E3318E12F` | Worktree has no `.codex/`; applicable root harness read-only. |
| Worktree `docs/context/SRS_AUTHORITY.md` | 4,313 | `D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60` | Current BE lane authority; Rev68 unsigned. |
| Active worktree: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (Rev68) | 639,948 | `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944` | Canonical working requirements source for this lane. |
| Root `docs/context/SRS_AUTHORITY.md` | 4,054 | `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F` | Historical root authority points to Rev60. |
| Root checkout: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (Rev60) | 553,948 | `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B` | Historical root copy; not the BE lane baseline. |
| `docs/context/PROJECT_CONTEXT.md` | 83,919 | `B53D00641590E5B0DB7D6D19603AB796F19658F9F3F6AD8BC31076FDF51D631D` | Current rehash after the initial Draft 4 row mismatch; dated implementation evidence only. |
| `docs/context/SOURCE_REGISTER.md` | 116,802 | `AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B` | Source routing and evidence register. |
| `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md` | 117,511 | `BBE6098147F8507C5B5C9489F9C5ADBA2DB725BBBDE4F54A67F9DD36D9B940E9` | Feature history, not an alternate SRS. |
| `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md` | 69,902 | `1CBA1C341185CA2F635E73B4CCE6E5F862F854EFCA3B0003EA29AD4F9E66206F` | Current rehash after the initial Draft 4 row mismatch; FEAT-063 implementation/evidence index. |
| `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md` | 216,212 | `52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F` | Current decision record through D-208. |
| `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md` | 410,676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` | Existing approvals only; D-207 remains S2-allowlist scoped. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md` | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` | S2 scope source; no mapper approval. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md` | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` | Current S2 result: PARTIAL / NOT COMPLETE. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_IMPLEMENTATION_ALLOWLIST_DRAFT1_20261114.md` | 14,768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` | D-207 exact S2 scope; generic mapper is excluded. |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md` | 3,456 | `D2C84E356C45653AB9973D94DFD09E4A8DB8439EA01BE4DA2D64B0849B80E5B2` | Prior failure evidence, not new reproduction. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT1_20261115.md` | 20,784 | `48B7A95133BDEAB9D14EE947BAF44D5B475ED60B99D118EAC24B51C9E0561BD6` | Historical plan, unchanged. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT2_20261116.md` | 15,345 | `9F9BD0C40FBEAA38515F92A4FBAB92F30535C3BC0150C94B986DE7F32192E803` | Reviewed target, unchanged. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT3_20261116.md` | 17,569 | `47FBBDA1B3C21FFA6CCD4DFE4322BD1C6B9C8D4851A1B584699EA694E4019525` | Current predecessor plan, unchanged. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S2_SHARED_OPENAPI_MAPPER_FIX_DRAFT4_20261116.md` | 26,271 | `2EA7A344CF016FDBC3546967288B5B6628E15AB48920C14F7DBF8C68880A5DB8` | Cold-reviewed predecessor; ACCEPT WITH CORRECTIONS, planning only. |
| `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S3_TASK_APPROVAL_DRAFT6_20261116.md` | 17,317 | `BF7792925F06ED66720850CEE916EFBF2F724100B84D3B2BF3545F11E19108C4` | Separate S3 plan; does not authorize S3 or substitute for S2. |
| `backend/src/sketch2life/interfaces/http/app.py` | 74,637 | `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` | Mapper source, unmodified since Draft 3 observation. |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 | `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` | Generated Rev37 catalog, read-only. |
| `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | 49,654 | `E16DE02140E7977A014F32D9CF131DAC8FC63EA622CEDD26B702958D7B92BB09` | Existing response/tag amendments, read-only. |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | 3,743 | `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` | Composition source, read-only. |
| `backend/src/sketch2life/interfaces/http/routers/be1_runtime.py` | 1,014 | `89C54AC8EDB63FD2DC9A92910BE817645D9429B8A54E0485F86A826BA6A863A7` | Nested-router context, read-only. |
| `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` | 17,501 | `7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF` | Prior overlay path, read-only. |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18,753 | `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` | Catalog contract test, read-only in this task. |
| `backend/tests/contract/test_app_composition.py` | 13,507 | `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` | App-profile test input; no run authorized. |
| `backend/pyproject.toml` | 3,383 | `35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2` | Project constraint `fastapi>=0.141,<1`. |
| `backend/uv.lock` | 398,117 | `830842CFAC04B5CA1EBDAA733E281F7D0AB9A4C94B19CFDF2B93E66854DBFB13` | Lock pins FastAPI 0.162.0. |
| `features/FEAT-047-be1-runtime-backend/plan/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_DRAFT1_20261114.md` | 7,886 | `235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B` | Prior one-time overlay only; authorization consumed. Hash corrected from the initial Draft 4 transcription. |
| `features/FEAT-047-be1-runtime-backend/approvals/TASK_APPROVAL.md` | 3,023 | `67A69DF8CEE0344D8F5D8D79B5F0D432490FE0D7F1486ED8A58C806ADD451063` | Prior one-time overlay only; authorization consumed. |
| `features/FEAT-047-be1-runtime-backend/evidence/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_EVIDENCE_20261114.md` | 13,596 | `0CF2C87996252058544D5F943967AB9F3A4E7A292D28CF1F6413620BFA6D8871` | Prior one-time overlay only; evidence is historical and authorization is consumed. |

## 9. Work performed for Draft 5

Draft 5 incorporates the Draft 4 cold-review corrections and records the owner's Option A planning direction. It creates no implementation approval or launch authority and changes no source, test, SRS, decision, approval, or historical evidence. Drafts 1–4 remain preserved. No tests, validators, typecheck, lint, diff check, OpenAPI generation, runtime, database/migration, install/sync, network, provider, Modal, stage, commit, or push command was run. At the time of the Draft 5 review pin, this plan had not been independently reviewed; any future implementation still requires a separate review, exact Task Approval, and direct launch instruction.
