# FEAT-047 OpenAPI artifact-upload description correction — Evidence

**Date:** 2026-11-14  
**Status:** Implemented as a narrow metadata correction; verification failed; S2 remains incomplete and unapproved.

## Authority and scope

The canonical working SRS is FEAT-063 v2.7-draft Rev67, still unsigned. Rev67 §9.6 treats the proposed resource routes as non-final; §32 is an as-built snapshot, not target requirements. This change adopts no product requirement.

The exact description is from the existing shared MOUNTED_OPERATIONS catalog. FEAT-047 API_CONTRACT.md corroborates the route and behavior but does not contain that exact sentence.

Owner approval is recorded as a task-specific entry in FEAT-047 approvals/TASK_APPROVAL.md. A one-time FEAT-063 verification addendum records the temporary integration overlay and the single authorized S2 targeted pytest invocation. D-207 remains controlling for all other paths and checks.

## Preflight and pins

Worktree: .worktrees/m2-s2  
Branch: feature/feat063-m2-s2  
HEAD: 5de30674bc826591ad4b3cc00fca53c7597ead51  
Staged path count: 0 before and after. Existing worktree changes were preserved.

| File | Before bytes / SHA-256 | After bytes / SHA-256 |
|---|---|---|
| backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py | 17,386 / B336C729C0D791F3DEA8F282F30EB0E7FF41B503F50798B24C98DC70DB00D3CC | 17,501 / 7126EDF1193C547026CFD3388D2893FC0B726D0DBA2B42D3B60FF5BFD8F28CAF |
| plan/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_DRAFT1_20261114.md | 7,858 / 22A163E093C3A85CB7BBC6EA67F40D98E885148FFE4232945F666ADC755CFA5F | 7,886 / 235C19EF66BDD36BAEC03A89548D96B8172126EBADEA86202A48692ED976308B |
| FEAT-047 approvals/TASK_APPROVAL.md | 1,266 / F628501E19C00B71DF7954B2105DBF8C9E4B6B27476129E4604A15606265FC54 | 3,023 / 67A69DF8CEE0344D8F5D8D79B5F0D432490FE0D7F1486ED8A58C806ADD451063 |
| FEAT-063 approvals/TASK_APPROVAL.md | 408,373 / 2E750F089382B70578AA0BDC9F6B206D4D5443F93EB6EF43D725658EC0C995A0 | 410,676 / C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088 |
| FEAT-063 evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md | 15,504 / C6CE183612927B2F11F6B1E7B6729E87E2BBE4BA73A6AF6743CC04C27C754A26 before this task's append | 25,879 / F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55 |

The M2 implementation report initially measured 14,198 bytes / 239558E15E2C934C007BBD3AD9F17C5B78CE5C0C72F2EDFA3C149C56DD1C2E77 during preflight. Before this task appended its result, it had gained a 1,306-byte suffix; the original 14,198-byte prefix still matched that hash. The newer report contents were preserved.

Related approval pins verified before edits:

- DECISIONS.md with D-207: 212,068 bytes / 191D68D7344FE2146E75F339185065234D092887C341AB487FB2DBEA8511C2BF.
- M2 Task Approval through D-207: 408,373 bytes / 2E750F089382B70578AA0BDC9F6B206D4D5443F93EB6EF43D725658EC0C995A0.
- Draft 18: 101,153 bytes / 5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331.
- Draft 18 cold review: 5,169 bytes / 4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B.
- Implementation Allowlist Draft 1: 14,768 bytes / 7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8.
- Independent allowlist review R2: 2,715 bytes / 6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D.
- Rev67 SRS: 634,291 bytes / B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996.

## Change made

The only source change adds this exact description to the existing POST artifact-upload route decorator:

    description="Tải một tệp kết quả hoặc tư liệu vào buổi học của tổ chức.",

The plan's Section 3 source-attribution sentence now says that MOUNTED_OPERATIONS supplies the exact wording and FEAT-047 API_CONTRACT.md corroborates route and behavior. No other plan text was changed.

## Single authorized test invocation

From backend/, the prepared Python 3.12 environment ran the owner's one authorized combined selection:

    python -m pytest -q tests/contract/test_parent_story_run_request_contract.py tests/contract/test_parent_story_run_cancel_route.py tests/contract/test_parent_ai_late_result_guards.py tests/contract/test_app_composition.py tests/contract/test_assistance_request_contracts.py tests/contract/test_assistance_requests_api.py tests/contract/test_openapi_contract_catalog.py tests/unit/test_parent_story_run_create_service.py tests/unit/test_parent_story_run_cancel_repository.py

Exit status: 1. The output reports one failure and one setup error. The catalog test passed its description comparison for the artifact-upload operation, then failed the tag assertion: actual tag BE1 artifacts, expected Session Artifacts. The app-composition test test_real_app_composes_pilot_only_for_valid_local_synthetic_gate errored while setting up tmp_path due to a Windows permission failure. The captured quiet output did not include an overall collected/pass count line; no count is inferred.

The output below is complete as captured, with absolute machine-specific paths normalized to repository-relative or environment placeholders. The error and failure details are preserved.

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

## Changed paths for this owner task

- backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py — the one source metadata edit.
- features/FEAT-047-be1-runtime-backend/plan/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_DRAFT1_20261114.md — Section 3 source-attribution correction.
- features/FEAT-047-be1-runtime-backend/approvals/TASK_APPROVAL.md — appended FEAT-047 task approval.
- features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md — appended one-time D-207 verification addendum.
- features/FEAT-047-be1-runtime-backend/evidence/OPENAPI_ARTIFACT_UPLOAD_DESCRIPTION_FIX_EVIDENCE_20261114.md — this report.
- features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md — appended the same test result separately from M2 implementation changes.

No other paths were changed by this task. Nothing was staged, committed, or pushed. No retry, typecheck, Ruff, validator, or diff-check was run. S2 remains incomplete and is not approved or launched.
