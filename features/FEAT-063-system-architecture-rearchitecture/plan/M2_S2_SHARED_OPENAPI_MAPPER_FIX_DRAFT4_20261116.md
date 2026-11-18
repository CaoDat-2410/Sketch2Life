# FEAT-063 M2 S2 Shared OpenAPI Catalog Mapper — Draft 4

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.** This is a plan-only successor to Draft 3. It grants no source or test edits, dependency changes, installation/synchronization, test or validator runs, database/runtime/network/provider/Modal activity, staging, commit, or push. Drafts 1–3 and the Draft 2 cold-review thread remain unchanged. `OWNER_MODAL_CALL_APPROVED=NO`.

**Date:** 2026-11-16  
**Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`.  
**Purpose:** Plan the next owner decision and a bounded implementation option for the shared OpenAPI catalog mapper. This does not declare the defect reproduced or M2 S2 complete.

## 1. Authority and current state

- The active BE worktree's `docs/context/SRS_AUTHORITY.md` selects unsigned FEAT-063 v2.7-draft Rev68 as the current working SRS. Rev68 remains a draft. The root checkout's SRS authority still points to unsigned Rev60; the two worktrees have different SRS bytes. This plan follows the BE worktree's Rev68 authority and does not change either pointer.
- SRS §21 describes API contract shape and states that route shape is to be frozen in OpenAPI. The mapper issue concerns how the existing code applies an existing catalog; it adds no product endpoint or SRS requirement.
- D-207 authorizes only its pinned S2 allowlist and enumerated behavior. Its inclusion of `app.py` for the Parent error-envelope task does not authorize a general OpenAPI mapper change. The FEAT-047 artifact-upload overlay and the combined S2 verification invocation were one-time and are consumed. This plan has no implementation or test-run authority.
- The current S2 implementation report remains **PARTIAL / NOT COMPLETE**. It records the catalog assertion failure, a later combined invocation exiting 1 with a tag mismatch and an app-composition `tmp_path` setup error, 335 mypy errors, and 17 Ruff diagnostics. Command ceilings are consumed. Nothing here upgrades those results or closes S2.
- M2 S3 Draft 6 is a separate planning draft. S3 remains closed until S2 is accepted and committed and S3 receives its own review, approval, and launch. Neither plan substitutes for the other's gate.

## 2. Current source behavior and evidence boundary

Static inspection of the pinned `backend/src/sketch2life/interfaces/http/app.py` confirms this sequence:

1. `build_runtime_openapi_schema()` calls FastAPI's `get_openapi(..., routes=application.routes, ...)` to generate a schema.
2. The custom mapper iterates the generated schema's `paths` and HTTP methods and first looks up `MOUNTED_OPERATIONS[(method.lower(), path)]`.
3. For a catalog hit, it then scans `application.routes` for the first route with the same direct `.path` and `.methods`, reads `route.endpoint.__name__`, and compares that function name with the last `::` component of the catalog's `handler` string. A mismatch skips the catalog mapping.
4. A passing entry applies the catalog description and tag, then the existing catalog response projection. A later pass also supplies the existing `X-Request-ID` parameter/response header contract. Other runtime-schema example amendments remain separate.

The proposed schema-keyed approach would remove only the mapper's additional endpoint lookup. FastAPI would still receive `application.routes` when it generates OpenAPI; Draft 4 does not propose flattening that route collection or inspecting `_IncludedRouter`.

The current check is narrower than “handler identity”: it compares only `__name__` with the catalog function-name suffix. It does not compare the module-qualified callable or the function object. The catalog is a dict keyed by `(method, path)` and its values also contain `handler`, `purpose`, `tag`, authorization notes, and response metadata.

The existing catalog test independently builds OpenAPI operation keys from `(method, path)`. Its pinned profile currently has 151 runtime operations, 134 catalog operations over 118 paths, and 17 explicitly classified runtime-only operations (`PILOT_ONLY_OPERATIONS` plus `PR22_UNCATALOGUED_OPERATIONS`). It checks catalog descriptions/tags, authorization, operation IDs, response sets, and response schemas. A dict literal can silently overwrite a duplicate key before a test inspects the resulting mapping; a separate duplicate-source check is needed if duplicate catalog declarations must be ruled out.

These are source and prior-test-record observations only. The earlier diagnostic recorded the artifact-upload description passing and the catalog tag failing (`BE1 artifacts` versus `Session Artifacts`); its raw route-match diagnostic was not preserved. Draft 4 makes no new runtime claim and does not treat the old zero-direct-match observation as a new reproduction or proven root cause. The cited FastAPI release-notes URL was supplied by the owner; it was not fetched or independently verified because this task is offline.

## 3. Options and recommendation

| Option | Proposed behavior | Benefits | Risks and gate |
|---|---|---|---|
| **A — map by public OpenAPI `(method, path)` key** | Apply each `MOUNTED_OPERATIONS` entry to the generated schema operation at the exact lower-case method and exact path. Do not traverse `application.routes` from the mapper and do not use FastAPI private route classes. Preserve the current response/header projection rules. | Matches the catalog's existing key and OpenAPI's operation slot; avoids route-tree flattening, private router internals, and a dependency change. | Selects the public operation slot but does not verify that its Python endpoint matches the catalog's `handler`. Removing the current name comparison changes an implementation-binding guard. It can apply stale catalog purpose/tag/response metadata to a new handler reusing the same path and method. Owner must explicitly decide whether contract identity is sufficient and whether handler binding may be dropped or redefined. This approach is preferred for planning only; it is not verified to fix the observed runtime mismatch. |
| **B — route-resolution adapter retaining the handler check** | Resolve nested included routers to concrete leaf routes, then compare the effective method/path and the current handler-name value before applying metadata. | Retains a code-to-catalog binding check, subject to its current limitation that it compares names rather than module/callable identity. | A solution based on FastAPI internals is version-sensitive; the currently recorded local package is 0.162.7 while `backend/uv.lock` pins 0.162.0. The exact public/internal surface in the locked version is not verified. The plan must not claim nested route behavior without exact-version evidence. |
| **C — dependency/version change** | Separately review a FastAPI version or dependency strategy that provides a documented route-resolution API for the binding requirement, then update the project constraint/lock only under approval. | Could avoid private internals while preserving stronger implementation binding if the selected, documented API provides it. | Broad backend compatibility and lock changes, installation/synchronization, and version-wide verification. No version is selected; no lock edit or network/package action is authorized. |

**Plan recommendation:** carry Option A forward as the preferred design to review because it applies catalog data at the public OpenAPI operation key and avoids private router internals and a dependency change. This is not a decision that method/path replaces handler identity. `MOUNTED_OPERATIONS` already contains handler provenance, and the mapper currently checks a handler-name suffix. The owner must decide whether to redefine the binding as contract-level identity (exact method/path, with the generated `operationId` preserved and checked) or require an implementation-handler match. An `operationId` invariant can detect an operation contract rename, but cannot prove Python callable identity. If the owner requires callable binding, stop Option A and select/review B or C; do not silently remove the current guard.

## 4. Proposed scope and allowlist — not approved

This proposed allowlist is for a future, separate task approval after the owner resolves the identity question. `E` means proposed edit, `N` proposed new file, and `R` read-only input. No path is authorized by Draft 4.

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

All items are proposals, not current evidence or authorization.

1. The mapping helper accepts the generated OpenAPI schema and catalog; it addresses each operation only by exact `(method.lower(), path)`. It does not enumerate `application.routes`, call route-flattening code, or reference `_IncludedRouter`.
2. Every catalog key must exist exactly once in the runtime schema. The runtime-only key set must remain exactly the explicitly permitted `PILOT_ONLY_OPERATIONS | PR22_UNCATALOGUED_OPERATIONS` for the approved profile. Any missing catalog key, stale catalog key, or unexpected runtime-only key fails closed.
3. A source-level test parses the `MOUNTED_OPERATIONS` mapping declaration and rejects duplicate `(method, path)` literal keys before Python dict construction can overwrite one. Runtime uniqueness alone is not sufficient evidence for duplicate source declarations.
4. For every mapped operation, tag and description values match the catalog entry for that exact key. Catalog response/status/media/schema projection continues to match `published_responses`; response headers and the optional `X-Request-ID` parameter retain the existing contract. A neighboring operation must not receive another key's metadata.
5. Before/after mapping evidence asserts an identical path set, HTTP-method set, and per-key `operationId` values; operation IDs remain non-empty and unique. Request-body schemas and `components.schemas` do not change. Response schemas are checked against the existing exact catalog projection because the current mapper intentionally normalizes declared responses; no broader response or schema delta is allowed. Only the catalog's explicit description/tag and response projection, plus the already-defined request-ID header/parameter normalization, may differ. The regression must record the intended correction for the previously missed catalog operation without implying routes or product schemas changed.
6. Uncatalogued operations retain their prior metadata and schema, and the published SRS projection remains unchanged. Tests compare the before/after operation sets rather than relying on counts alone; the current 151/134/118/17 counts remain pinned expectations for this profile until an approved source change says otherwise.
7. The accepted report describes Option A as contract-key identity and explicitly records the owner's handler-binding disposition. If the owner requires handler equivalence, Option A does not pass acceptance by weakening or deleting the check; stop and return to B/C review.
8. A future lock-matched test run demonstrates the app-composition node and schema mapper without DB connection/lifespan, dotenv loading, provider credential discovery, network, Modal, or real secret use. The profile and exact command are pinned in the separate Task Approval.

The mapper fix alone does not close S2. Existing 81/82, later exit-1, 335-mypy-error, and 17-Ruff-diagnostic results remain in the S2 ledger. S2 closure requires all applicable owner-approved evidence and acceptance; S3 is a later separate gate.

## 6. Future environment and command card — approval required

The local Python 3.12 virtual environment previously inspected reports FastAPI 0.162.7; `backend/uv.lock` pins 0.162.0. The environment is not lock-equivalent. Do not use it to claim locked-version behavior. A future owner approval must provide or authorize an exact lock-matched environment, and any install/sync or network access needs its own explicit scope.

Suggested commands for a separate owner-reviewed command card only, to be run from `backend/` after exact pins, environment, isolation, approval, and a direct launch instruction are recorded:

```text
python -m pytest -q tests/contract/test_openapi_schema_catalog_mapping.py tests/contract/test_openapi_contract_catalog.py tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate
python -m mypy src/sketch2life
python -m ruff check src/sketch2life/interfaces/http/app.py tests/contract/test_openapi_contract_catalog.py tests/contract/test_openapi_schema_catalog_mapping.py
```

Proposed maximum ceilings, all requiring new owner approval: two targeted pytest invocations (initial plus at most one fix-driven rerun); two mypy invocations (fresh baseline and post-edit comparison); two Ruff invocations (initial plus at most one fix-driven rerun). The earlier D-207/FEAT-047 ceilings are consumed and cannot be reused. Preserve the prior 335 mypy errors and 17 Ruff diagnostics as existing debt; a fresh check must report deltas and must not call the old baseline a pass. Any validator, diff check, app/OpenAPI generation, or additional command must be separately named and approved. No command above has run under this plan.

The future Task Approval must name the exact isolated pytest base/cache locations, disable dotenv, prevent database/provider credential discovery, keep any settings/artifact root inside the approved temp path, and specify failure handling. The prior Windows `tmp_path` access-denied error remains unexplained; do not probe or change permissions under this plan. No retry is authorized.

## 7. Review and owner gates

The independent cold review of Draft 2 returned **ACCEPT WITH CORRECTIONS**. It is a planning review only. Draft 3 incorporated its evidence qualifications and recorded the public API feasibility question for FastAPI 0.162.0. Draft 4 requests one new fresh-context, read-only review of this exact pinned plan and its listed inputs; no reviewer may edit files, write an evidence report, change approvals, or run checks. The review verdict will be returned in its own thread only.

Required owner decisions before implementation:

1. Does API identity for this mapper mean exact method/path (with `operationId` preserved/checked) and may the current handler-name guard be removed? If not, require implementation binding and choose a separately reviewed B or C direction.
2. Approve an exact future allowlist, including any acceptance-test additions, and explicitly scope the generic mapper outside D-207.
3. Provide/approve a lock-matched FastAPI 0.162.0 environment and exact command ceilings, isolation paths, expected evidence, and launch instruction. Do not infer authorization from planning acceptance or the cold-review verdict.

Stop before implementation if the identity decision remains open; a requested route/catalog/dependency change exceeds §4; the exact input pins drift; the lock-matched environment is unavailable; the public schema lacks a unique exact-key operation; or acceptance would require changing endpoint semantics, routes, method/path, `operationId`, request schemas, component schemas, SRS, DTR, or approval scope.

## 8. Current input pins

Pins below were rechecked from the active worktree and the named historical/review sources for this pre-review. All 27 file pins in Draft 3 §9 still match their recorded bytes and SHA-256, and branch/HEAD still match Draft 3. The initial Draft 4 values for `docs/context/PROJECT_CONTEXT.md` and the FEAT-063 `SOURCE_REGISTER.md` did not match the current files; treat those initial observations as **CHANGED SINCE OBSERVATION** and use the rehashed values below. The FEAT-047 plan's initial SHA-256 was a transcription error and is corrected below. No source file was changed by this recheck. The Draft 2 review observed 69 paths (24 modified, 45 untracked, 0 staged). Later addition of Mapper Draft 3 and S3 Draft 6 brought the pre-Draft-4 snapshot to 71 (24 modified, 47 untracked, 0 staged); this new Draft 4 file makes the current snapshot 72 (24 modified, 48 untracked, 0 staged): **CHANGED SINCE OBSERVATION**. This status is not an implementation or clean-baseline claim.

The Draft 2 cold-review result is not stored as a repository evidence file. Its persisted final answer is pinned by thread `01a1e066-0aba-75c3-b9de-40a55c201c97`, turn `01a1e066-109e-77b1-b27e-82d5b11f50dd`, item `msg_00863208b4f239e8016af9f75d98d487d096ac16ac75eac5b2`: 5,702 UTF-8 bytes, SHA-256 `DC9E34062AF4E5F194DCDB4BE536418201554AC94BF5328167818CA0842CC79B`.

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

## 9. Work performed for Draft 4

Draft 4 records a proposed schema-keyed approach and its unresolved handler-binding decision. It changes no source, test, SRS, decision, approval, or historical evidence. No tests, validators, typecheck, lint, diff check, OpenAPI generation, runtime, database/migration, install/sync, network, provider, Modal, stage, commit, or push command was run. Review of this exact Draft 4 is pending in one fresh-context thread; the review verdict is not implementation approval.
