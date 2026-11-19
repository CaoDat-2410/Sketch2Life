# FEAT-063 M2 S2 bounded implementation report

**Status: PARTIAL / NOT COMPLETE.** Required test, typecheck and lint evidence remains unavailable. S2 is not declared complete, accepted, or launched. D-207's bounded implementation launch signal was supplied; OWNER_MODAL_CALL_APPROVED=NO.

## Preflight

- Worktree branch: `feature/feat063-m2-s2`.
- HEAD: `5de30674bc826591ad4b3cc00fca53c7597ead51`.
- No paths were staged. The pre-existing `evidence/BE_SESSION_CHECKPOINT_20261114.md` remains untouched.
- The decision and approval pins, Rev67, Draft 18 and its cold review, Allowlist Draft 1, independent Allowlist R2, and SRS authority pin matched the owner-provided values.
- All 15 allowlist E pins matched before editing; all 6 R references still match. All 4 N paths were absent at preflight. Only allowlisted E/N paths were changed or created.

## Changes

- Added output-only `run_revision` from `story.runs.revision` to the shared Parent response and both existing response mappings.
- Added only `POST /v1/story-runs/{run_id}/cancel`. The operation stores and replays the exact 202 response body in a `CANCEL_RUN` receipt; a shared principal/key advisory lock and receipt lookup detect reuse across runs. Replay is checked before `expected_revision`; stale revision returns 409 `STALE_REVISION` with cancel-only top-level `current_version`. Successful cancel updates `DELETE_PENDING`, increments the existing revision/version, and clears the active-owner column in the same session transaction.
- Added pre-write `DELETE_PENDING` guards to story completion, story failure/unknown, and artwork failure/unknown. The artwork-success path remains protected by its existing `INPUT_PROCESSING` check and existing error code.
- Added the exact artwork-route error formatter boundary and forwarded the new guard errors through the existing safe message map/fallback.
- Added create-age boundary tests, cancel and late-result tests, the status-read compatibility test, route-composition/OpenAPI baseline adjustments, and concise context/source-register status entries.
- No DDL, migration, new state, additional route, mobile change, provider call, job cancellation, or purge worker was added.

## Changed file pins

Byte counts and SHA-256 values below were read after the edits. The report's own pin is included in the session's final response because a file cannot contain its own final digest.

| Path | Bytes | SHA-256 |
|---|---:|---|
| `backend/src/sketch2life/application/ports/parent_story_runs.py` | 6601 | `6A75485D52E173490BCC274284DF7621766A4557B8ACFA22986FFB20D16BFCC4` |
| `backend/src/sketch2life/contracts/schemas/parent_story_runs.py` | 7889 | `1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749` |
| `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py` | 69489 | `237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C` |
| `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py` | 14626 | `A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD` |
| `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` | 23082 | `E99E54122DB81539577E66328052AE1B2231B7B929A9F31372B5381EF3EE3B30` |
| `backend/src/sketch2life/interfaces/http/app.py` | 74637 | `E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031` |
| `backend/tests/contract/test_parent_story_run_request_contract.py` | 12286 | `FD2634034ABE6C22536D2D7C7DA5787772B91A9F4D4AAA81420B749D67248FAA` |
| `backend/tests/contract/test_app_composition.py` | 13507 | `1ED234FD8B75847F2668A2B23C9325C1D229CA679943B65166E96144A4463B52` |
| `backend/tests/contract/test_assistance_request_contracts.py` | 7358 | `AB3D9E98A81EEBD53EF65A526FDA6BC8F65CD37A6E4E0D20F82AE90EC66C2A14` |
| `backend/tests/contract/test_assistance_requests_api.py` | 10748 | `73C286AB56CD14E26DC7EEA5D2FA3D4F73946F99F4F969C08FD73EFB32DED4E4` |
| `backend/tests/unit/test_parent_story_run_create_service.py` | 4581 | `145F327DB6502667C2E6FC56305EF3DE736E556BAE2AE0C37677BBBA1C4DF46E` |
| `backend/tests/contract/test_openapi_contract_catalog.py` | 18753 | `BB798EF399168F2466470AA81F74B88E5304442BAB2EE88F87D24CA70C43B198` |
| `features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json` | 9248 | `689023BE3130F156CC6C458242DD11F68FDFBC9CC19E0AAC7174B21F9BBB34E5` |
| `docs/context/PROJECT_CONTEXT.md` | 83909 | `56DC16E4802A6598E6232D3A4B3361F802BDB54F461C3AE27B9AF2E31D63D061` |
| `docs/context/SOURCE_REGISTER.md` | 115881 | `39D8BD4F68ECCB75FF16BBFE775A9BBDB13151E7BD948EE1791071A0DA0B39FC` |
| `backend/tests/unit/test_parent_story_run_cancel_repository.py` | 10111 | `A7CE542F352E9E51A0C5B32444240E6A84866C7452293BFBE15EB38E02689D9E` |
| `backend/tests/contract/test_parent_story_run_cancel_route.py` | 3601 | `98B4522D441F223F4BC6A17256982B4E3E9484D7EE1692A753162DDBF17CBBDE` |
| `backend/tests/contract/test_parent_ai_late_result_guards.py` | 3467 | `7C9EF0E89B77E1566A33C386854174A56E9BABB88732A94BDB499898D42D2BEC` |

## Check results

- Targeted pytest selection: did not start; Python reported `No module named pytest`. No tests were collected or run. One of two allowed invocations was consumed.
- `python -m mypy src/sketch2life`: unavailable; Python reported `No module named mypy`. One of two allowed runs was consumed.
- Allowlisted Ruff selection: unavailable; Python reported `No module named ruff`. One of two allowed runs was consumed.
- Harness validator: `HARNESS_VALID`.
- Architecture validator: `ARCHITECTURE_VALID`.
- Repository security validator: `REPOSITORY_SECURITY_VALID`; 7,283 publishable files scanned and no absolute machine paths found.
- `git diff --check`: exit 0. It was run once after tracked edits; Git does not include untracked files in this check.

No database, migration, Docker, install, network, provider, Modal, Android, emulator, staging, commit or push command was run. The validators ran after code and test edits but before a final documentation-only status update in the two context files and before this report was written. `git diff --check` ran after the final tracked edits and before this report; untracked tests and the report are not included in that Git check.

## Outstanding command cards

Run from `backend/` with already-installed tools only, then paste the exact output for review:

```text
python -m pytest -q tests/contract/test_parent_story_run_request_contract.py tests/contract/test_parent_story_run_cancel_route.py tests/contract/test_parent_ai_late_result_guards.py tests/contract/test_app_composition.py tests/contract/test_assistance_request_contracts.py tests/contract/test_assistance_requests_api.py tests/contract/test_openapi_contract_catalog.py tests/unit/test_parent_story_run_create_service.py tests/unit/test_parent_story_run_cancel_repository.py
python -m mypy src/sketch2life
python -m ruff check src/sketch2life/application/ports/parent_story_runs.py src/sketch2life/contracts/schemas/parent_story_runs.py src/sketch2life/infrastructure/persistence/parent_story_repository.py src/sketch2life/interfaces/http/routers/parent_story_runs.py src/sketch2life/interfaces/http/routers/parent_ai.py src/sketch2life/interfaces/http/app.py
```

The broader-route stale-version P3 from Allowlist R2 remains a separate follow-up outside this allowlist. S2 remains incomplete until the missing test/typecheck/lint evidence is reviewed; no Task Approval, gate, or launch authorization is created.
## Owner-authorized environment setup and additional validation — 2026-11-14

The owner instructed the coordinator to install the backend development dependencies and run whichever approved checks can run. This instruction narrowly overrides the earlier no-install restriction and exhausted run ceilings for the following only: install the backend project dependencies plus the `dev` extra into the dedicated Python 3.13.5 environment under `tmp/m2-s2-validation/`, then perform one new invocation each of the allowlist's targeted pytest selection, mypy command, and Ruff command. The previous invocations that stopped with missing-module errors remain recorded; this is a new post-install attempt. Further attempts require another owner authorization.

Do not install into the repository-root `.venv` or system Python. Do not edit implementation source in this verification step. No validator rerun, database/migration, Docker, provider, Modal, staging, commit, or push is authorized here. Record actual install and check outputs below; a missing or failed command is not a PASS.
## Optional import dependencies needed for targeted collection — 2026-11-14

The first owner-authorized post-install pytest invocation stopped during collection with four import errors for the optional `av` module. Mypy also reported missing `av` and `numpy` imports. The project declares `av==18.1.0` under `image-admission` and `numpy>=1.26,<2` under its image/video extras. Under the same owner instruction to install and test what can run, the coordinator authorizes only these two runtime imports in the dedicated venv, followed by one additional invocation of the exact targeted pytest selection and one additional mypy invocation. Ruff already ran once with dependencies and is not repeated. No code edits or further attempts are authorized by this extension; further runs need a new owner instruction.

## Owner-authorized Python 3.12 fallback — 2026-11-14

The owner explicitly instructed the coordinator to install dependencies and run the checks that can be run, recording actual results. After the isolated Python 3.13.5 attempt could not prepare NumPy because no Windows compiler was available, this instruction authorizes one compatible Python 3.12 environment under `tmp/m2-s2-validation/python312/`, installation of the backend `dev` and `image-admission` extras plus the already-declared `numpy>=1.26,<2` import, and one additional invocation of the exact targeted pytest selection and `python -m mypy src/sketch2life`. Python 3.12 is within the backend's declared supported range. The existing Python 3.13 environment is preserved. Do not rerun Ruff, validators, or source checks, edit implementation files, or retry these commands again without a new owner instruction.
## Post-install validation results — 2026-11-14

### Isolated Python 3.13.5 attempt

- Installing the backend project with the `dev` extra succeeded in `tmp/m2-s2-validation/.venv` and installed 108 packages.
- The targeted pytest selection exited 1 during collection with four import errors because the optional `av` module was missing; no tests executed. The affected collection files were `test_parent_story_run_request_contract.py`, `test_parent_ai_late_result_guards.py`, `test_app_composition.py`, and `test_openapi_contract_catalog.py`.
- `python -m mypy src/sketch2life` exited 1 with 330 errors in 67 files. Missing `av` and `numpy` imports were among the diagnostics.
- The allowlisted Ruff command exited 1 with 17 diagnostics; one was marked fixable and four had unsafe fix suggestions. No automatic fixes were applied.
- Installing `av==18.1.0` and `numpy>=1.26,<2` in this environment failed while preparing NumPy 1.26.4 from source because no Windows compiler was available. No follow-up check was run in this environment.

### Isolated Python 3.12.10 fallback

- The first package-download attempt failed at DNS while fetching wheel metadata. The same install was then rerun with the owner-authorized package-download permission and succeeded: 110 packages installed for `.[dev,image-admission]` plus `numpy>=1.26,<2`, including pytest 8.4.2, mypy 1.20.2, Ruff 0.17.5, av 18.1.0, and NumPy 1.26.4. The environment is `tmp/m2-s2-validation/python312/.venv`.
- The exact targeted pytest selection started but produced no output or summary. It remained active for approximately 3 minutes 15 seconds and was interrupted; exit code 1. No test count or pass/fail summary was produced, so this is INCOMPLETE and not a pass.
- `python -m mypy src/sketch2life` exited 1: 335 errors in 63 files, with 597 source files checked. The captured terminal output was truncated; this record therefore states the aggregate result and does not claim a complete diagnostic inventory.
- Ruff was not repeated under Python 3.12, per the authorized run limit; the Python 3.13 Ruff result above is the only run recorded.

### Scope and remaining evidence

- Dependency installation used the package index only. No application API, backend server, database, migration, Docker, provider, or Modal call was made; `OWNER_MODAL_CALL_APPROVED=NO` remains in force.
- No implementation source was changed. No validators or `git diff --check` were run in this follow-up. No files were staged, committed, or pushed.
- Backend validation remains incomplete: the targeted tests did not produce a completed result, and mypy failed with the aggregate errors above. Do not claim these checks passed; any further test or typecheck invocation requires a new owner instruction.
## Owner-supplied targeted pytest result — 2026-11-14

The owner ran the exact targeted pytest selection in the isolated Python 3.12.10 environment and pasted the complete output. Pytest collected 82 tests: 81 passed and 1 failed in 16.17 seconds. The pasted output did not include the shell's process exit code.

Failure: `tests/contract/test_openapi_contract_catalog.py::test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates` raised `KeyError: 'description'` at line 307, where the test requires each mounted catalog operation to have a description matching its contract purpose.

Read-only triage: the mounted-operation list includes `POST /v1/story-runs/{run_id}/cancel`; its route decorator has a summary but no explicit description, and the handler has no docstring. This is a likely explanation for the missing OpenAPI `description`; the traceback does not print the operation key at failure, so the exact key is NOT VERIFIED. No source was changed and no test was rerun after the owner's output.

This result supersedes the earlier coordinator pytest attempt that was interrupted without a summary. The targeted pytest check is now complete with 81 passing and 1 failing test; it is not a pass gate.
## Correction after ASCII-safe OpenAPI diagnostic — 2026-11-14

This entry supersedes the earlier read-only triage paragraph that speculated the cancel route might lack the description causing the catalog-test failure. The diagnostic identified the first missing-description operation as `POST /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts`, expected purpose `Tải một tệp kết quả hoặc tư liệu vào buổi học của tổ chức.`, actual description `MISSING`.

The test's failing loop iterates `MOUNTED_OPERATIONS`; the cancel route is in `PR22_UNCATALOGUED_OPERATIONS`, which is asserted disjoint from `MOUNTED_OPERATIONS`. The BE1 artifact route file is outside the exact S2 implementation allowlist and was not modified. The full diagnostic output was truncated after the first missing entry, so later anomalies remain unverified. The detailed out-of-scope record is `evidence/M2_S2_OUT_OF_SCOPE_OPENAPI_FINDING_20261114.md`.

No source or test was changed by this correction. The targeted test result remains 81 passed and 1 failed; mypy and Ruff remain failed at their previously recorded aggregate counts. The approved command ceilings have been consumed; further checks require a new owner instruction. S2 remains incomplete and is not marked ready.

## Owner-authorized FEAT-047 metadata overlay and combined S2 targeted run — 2026-11-14

The owner authorized one temporary integration-verification overlay for the separate FEAT-047 artifact-upload OpenAPI description and one fresh invocation of the combined S2 targeted selection. This does not change M2 product scope or the M2 implementation allowlist; D-207 remains controlling for all other paths and checks.

The BE1 artifact-upload route now has the exact catalog description. This task changed only its decorator metadata; it did not change request handling, authorization, persistence, schemas, status, or error behavior.

The source was 17,386 bytes with SHA-256 B336C729C0D791F3DEA8F282F30EB0E7FF41B503F50798B24C98DC70DB00D3CC before the edit and 17,501 bytes with SHA-256 7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF afterward. The FEAT-047 plan was 7,858 bytes / 22A163E093C3A85CB7BBC6EA67F40D98E885148FFE4232945F666ADC755CFA5F before its Section 3 attribution correction and 7,886 bytes / 235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B afterward.

The FEAT-047 Task Approval prefix was 1,266 bytes / F628501E19C00B71DF7954B2105DBF8C9E4B6B27476129E4604A15606265FC54 and is preserved; after appending the task-specific approval it is 3,023 bytes / 67A69DF8CEE0344D8F5D8D79B5F0D432490FE0D7F1486ED8A58C806ADD451063. The FEAT-063 Task Approval prefix was 408,373 bytes / 2E750F089382B70578AA0BDC9F6B206D4D5443F93EB6EF43D725658EC0C995A0 and is preserved; after appending the one-time D-207 verification addendum it is 410,676 bytes / C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088.

At initial observation, this report was 14,198 bytes / 239558E15E2C934C007BBD3AD9F17C5B78CE5C0C72F2EDFA3C149C56DD1C2E77. Before this append it was 15,504 bytes / C6CE183612927B2F11F6B1E7B6729E87E2BBE4BA73A6AF6743CC04C27C754A26; its original 14,198-byte prefix still hashes to 239558E15E2C934C007BBD3AD9F17C5B78CE5C0C72F2EDFA3C149C56DD1C2E77. The intervening suffix was preserved.

The single authorized invocation used the prepared Python 3.12 environment under tmp/m2-s2-validation/python312/.venv from backend/ and the nine-file selection recorded in the owner addendum. It exited 1. The OpenAPI test passed the description comparison for the artifact-upload operation and then failed at the next catalog assertion: actual tag BE1 artifacts versus expected Session Artifacts. A separate app-composition test errored during tmp_path setup because the Windows temporary directory denied access. No retry, follow-up diagnostic, or further source edit was performed. S2 remains incomplete and not approved or launched; the earlier 335 mypy errors and 17 Ruff diagnostics remain outstanding and were not rerun.

Complete captured pytest output follows. Absolute machine-specific paths are normalized to repository-relative or environment placeholders; the failure text and traceback content are otherwise preserved.

    ..................................E...............................F..... [ 87%]
    ..........                                                               [100%]
    =================================== ERRORS ====================================
    _ ERROR at setup of test_real_app_composes_pilot_only_for_valid_local_synthetic_gate _

    fixturedef = <FixtureDef argname='tmp_path' scope='function' baseid=''>
    request = <SubRequest 'tmp_path' for <Function test_real_app_composes_pilot_only_for_valid_local_synthetic_gate>>

        @pytest.hookimpl(wrapper=True)
        def pytest_fixture_setup(fixturedef: FixtureDef, request) -> object | None:
            if (
                fixturedef.argname == "event_loop_policy"
                and fixturedef.func.__module__ != __name__
            ):
                warnings.warn(
                    PytestDeprecationWarning(_EVENT_LOOP_POLICY_FIXTURE_DEPRECATION_WARNING),
                )
            asyncio_mode = _get_asyncio_mode(request.config)
            if not _is_asyncio_fixture_function(fixturedef.func):
                if asyncio_mode == Mode.STRICT:
                    # Ignore async fixtures without explicit asyncio mark in strict mode
                    # This applies to pytest_trio fixtures, for example
    >               return (yield)
                            ^^^^^
    E               PermissionError: [WinError 5] Access is denied: '<TEMP>\\pytest-of-<owner>'

    <python312-venv>\\Lib\\site-packages\\pytest_asyncio\\plugin.py:934: PermissionError
    ================================== FAILURES ===================================
    _ test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates _

    runtime_openapi = {'components': {'schemas': {'AccountCreateRequest': {'additionalProperties': False, 'properties': {'display_name': {'m...'422': {'content': {...}, 'description': 'Validation Error', 'headers': {...}}}, 'summary': 'Cancel', ...}}, ...}, ...}

        def test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates(
            runtime_openapi: dict[str, Any],
        ) -> None:
            spec = runtime_openapi
            operations = {
                (method.lower(), path): operation
                for path, path_item in spec["paths"].items()
                for method, operation in path_item.items()
                if method.lower() in HTTP_METHODS
            }

            assert spec["openapi"] == "3.1.0"
            assert spec["tags"] == public_tags(TAG_DESCRIPTIONS)
            assert len(operations) == 151
            catalog_operations = set(MOUNTED_OPERATIONS)
            catalog_paths = {path for _method, path in catalog_operations}
            assert len(catalog_paths) == 118
            assert len(catalog_operations) == MOUNTED_OPERATION_COUNT == 134
            assert set(operations) - catalog_operations == (
                PILOT_ONLY_OPERATIONS | PR22_UNCATALOGUED_OPERATIONS
            )
            assert PILOT_ONLY_OPERATIONS.isdisjoint(MOUNTED_OPERATIONS)
            assert PR22_UNCATALOGUED_OPERATIONS.isdisjoint(MOUNTED_OPERATIONS)
            profile_lookup = operations[
                (
                    "get",
                    "/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles",
                )
            ]
            assert "x-contract-surface" not in profile_lookup
            assert len(PILOT_ONLY_OPERATIONS) == 5
            assert len(PR22_UNCATALOGUED_OPERATIONS) == 12

            assert (
                "post",
                "/api/be1/v1/organizations/{organization_id}/assignments",
            ) not in operations
            assert (
                "delete",
                "/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}",
            ) not in operations
            assignment_key = ("post", "/api/be1/v1/classes/{class_id}/assignments")
            assert assignment_key in operations
            assignment_body = operations[assignment_key]["requestBody"]["content"][
                "application/json"
            ]
            assignment_schema_name = next(iter(_schema_refs(assignment_body["schema"])))
            assert set(spec["components"]["schemas"][assignment_schema_name]["properties"]) == {
                "subject"
            }

            profile_key = (
                "post",
                "/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles",
            )
            profile_body = operations[profile_key]["requestBody"]["content"][
                "application/json"
            ]
            profile_schema_name = next(iter(_schema_refs(profile_body["schema"])))
            profile_schema = spec["components"]["schemas"][profile_schema_name]
            assert set(profile_schema["properties"]) == {
                "class_id",
                "display_name",
                "age_months",
            }
            assert profile_schema["properties"]["age_months"]["minimum"] == 36
            assert profile_schema["properties"]["age_months"]["maximum"] == 120

        for key, contract in MOUNTED_OPERATIONS.items():
            operation = operations[key]
            if key in {
                ("post", "/v1/sessions"),
                ("post", "/v1/sessions/{session_id}/media/image"),
                RESTORE_CHECKPOINT_OPERATION_KEY,
                PORTFOLIO_OPERATION_KEY,
                (
                    "get",
                    "/api/be1/v1/organizations/{organization_id}/classes/"
                    "{class_id}/profiles/{child_id}/portfolio",
                ),
            }:
                assert operation["description"].startswith(contract["purpose"])
            else:
                assert operation["description"] == contract["purpose"]
        >       assert operation["tags"] == [public_tag_name(contract["tag"])]
    E       AssertionError: assert ['BE1 artifacts'] == ['Session Artifacts']
    E         
    E         At index 0 diff: 'BE1 artifacts' != 'Session Artifacts'
    E         Use -v to get more diff

    tests\\contract\\test_openapi_contract_catalog.py:308: AssertionError
    ============================== warnings summary ===============================
    <python312-venv>\\Lib\\site-packages\\_pytest\\cacheprovider.py:475
      backend/.pytest_cache/v/cache/nodeids: PytestCacheWarning: could not create cache path backend/.pytest_cache/v/cache/nodeids: [WinError 5] Access is denied: 'backend/.pytest_cache/v/cache'
        config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

    <python312-venv>\\Lib\\site-packages\\_pytest\\cacheprovider.py:429
      backend/.pytest_cache/v/cache/lastfailed: PytestCacheWarning: could not create cache path backend/.pytest_cache/v/cache/lastfailed: [WinError 5] Access is denied: 'backend/.pytest_cache/v/cache'
        config.cache.set("cache/lastfailed", self.cache.get("cache/lastfailed", {}))

    -- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
    =========================== short test summary info ===========================
    FAILED tests/contract/test_openapi_contract_catalog.py::test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates
    ERROR tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate
