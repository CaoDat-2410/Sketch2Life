# MGR-8 diagnostic run — 2026-11-18

Status: diagnostic run incomplete. The owner decides whether the observed results satisfy the MGR-8 verification gate.

## Preflight

- Worktree: feature/feat066-manager-api-contracts at 1c9148e88600a101887e477541c4c4893ba1c7df; 72 status paths and 0 staged before the run.
- All ten source, test and record pins listed by the diagnostic prompt matched.
- Environment checks: BE1_TEST_DATABASE_URL set: yes; database name contains be1_acceptance: yes; import path inside the worktree backend src: yes. PYTHONPATH=src and PYTHONUNBUFFERED=1.
- No database URL was recorded. Output scan found no 127.0.0.1:5434 or postgresql string; no redaction was needed.

## Commands and results

D1 — root backend/.venv python -X faulthandler -m pytest -p no:cacheprovider -o addopts="" -vv -s --durations=20 -o faulthandler_timeout=120 tests/unit/test_lesson_library_receipt_compatibility.py

- Exit code: 0.
- Result: 8 passed, 0 failed, 0 skipped.
- Pytest summary: 8 passed in 0.91s.
- The 20 slowest duration rows reported by pytest are listed below. Durations display as 0.00s after rounding.
0.00s call     tests/unit/test_lesson_library_receipt_compatibility.py::test_legacy_receipt_replay_reconstructs_revision_without_writes[POST /organizations/synthetic-org-01/parent-groups/synthetic-group-01/invitations-payload0-legacy0-ParentGroupInvitationV1]
0.00s call     tests/unit/test_lesson_library_receipt_compatibility.py::test_legacy_receipt_replay_reconstructs_revision_without_writes[POST /me/parent-group-invitations/synthetic-membership-01/accept-payload1-legacy1-ParentGroupMembershipV1]
0.00s call     tests/unit/test_lesson_library_receipt_compatibility.py::test_legacy_receipt_without_current_membership_is_typed_failure
0.00s setup    tests/unit/test_lesson_library_receipt_compatibility.py::test_current_receipt_is_returned_unchanged_without_inferred_provenance
0.00s call     tests/unit/test_lesson_library_receipt_compatibility.py::test_current_receipt_is_returned_unchanged_without_inferred_provenance
0.00s call     tests/unit/test_lesson_library_receipt_compatibility.py::test_reused_key_with_different_fingerprint_is_invalid_idempotency_key
0.00s call     tests/unit/test_lesson_library_receipt_compatibility.py::test_receipt_from_another_organization_or_principal_is_not_visible[synthetic-other-org-01-synthetic-manager-01-POST /organizations/synthetic-other-org-01/parent-groups/synthetic-group-01/invitations]
0.00s call     tests/unit/test_lesson_library_receipt_compatibility.py::test_malformed_receipt_response_is_typed_failure
0.00s call     tests/unit/test_lesson_library_receipt_compatibility.py::test_receipt_from_another_organization_or_principal_is_not_visible[synthetic-org-01-synthetic-other-principal-01-POST /organizations/synthetic-org-01/parent-groups/synthetic-group-01/invitations]
0.00s teardown tests/unit/test_lesson_library_receipt_compatibility.py::test_current_receipt_is_returned_unchanged_without_inferred_provenance
0.00s setup    tests/unit/test_lesson_library_receipt_compatibility.py::test_legacy_receipt_replay_reconstructs_revision_without_writes[POST /me/parent-group-invitations/synthetic-membership-01/accept-payload1-legacy1-ParentGroupMembershipV1]
0.00s setup    tests/unit/test_lesson_library_receipt_compatibility.py::test_legacy_receipt_replay_reconstructs_revision_without_writes[POST /organizations/synthetic-org-01/parent-groups/synthetic-group-01/invitations-payload0-legacy0-ParentGroupInvitationV1]
0.00s setup    tests/unit/test_lesson_library_receipt_compatibility.py::test_receipt_from_another_organization_or_principal_is_not_visible[synthetic-other-org-01-synthetic-manager-01-POST /organizations/synthetic-other-org-01/parent-groups/synthetic-group-01/invitations]
0.00s setup    tests/unit/test_lesson_library_receipt_compatibility.py::test_receipt_from_another_organization_or_principal_is_not_visible[synthetic-org-01-synthetic-other-principal-01-POST /organizations/synthetic-org-01/parent-groups/synthetic-group-01/invitations]
0.00s setup    tests/unit/test_lesson_library_receipt_compatibility.py::test_malformed_receipt_response_is_typed_failure
0.00s teardown tests/unit/test_lesson_library_receipt_compatibility.py::test_legacy_receipt_replay_reconstructs_revision_without_writes[POST /organizations/synthetic-org-01/parent-groups/synthetic-group-01/invitations-payload0-legacy0-ParentGroupInvitationV1]
0.00s setup    tests/unit/test_lesson_library_receipt_compatibility.py::test_reused_key_with_different_fingerprint_is_invalid_idempotency_key
0.00s teardown tests/unit/test_lesson_library_receipt_compatibility.py::test_receipt_from_another_organization_or_principal_is_not_visible[synthetic-org-01-synthetic-other-principal-01-POST /organizations/synthetic-org-01/parent-groups/synthetic-group-01/invitations]
0.00s setup    tests/unit/test_lesson_library_receipt_compatibility.py::test_legacy_receipt_without_current_membership_is_typed_failure
0.00s teardown tests/unit/test_lesson_library_receipt_compatibility.py::test_legacy_receipt_replay_reconstructs_revision_without_writes[POST /me/parent-group-invitations/synthetic-membership-01/accept-payload1-legacy1-ParentGroupMembershipV1]
D2 — root backend/.venv python -X faulthandler -m pytest -p no:cacheprovider -o addopts="" -vv -s --durations=20 -o faulthandler_timeout=120 tests/contract/test_openapi_contract_catalog.py

- Interrupted at about 12 minutes total after the output file had not grown for 10 minutes. The shell session returned exit code 1 when interrupted; a pytest exit status and final summary were not captured. Test pass/fail/skip counts are unavailable.
- The 120-second faulthandler dump shows the test at test_openapi_contract_catalog.py line 170, test_swagger_ui_and_openapi_json_are_published, blocked in Starlette TestClient handling an httpx2 GET while AnyIO starts its blocking portal. The main thread waits on the portal-start future; the portal thread is in Windows asyncio Proactor self-pipe creation, blocked in socket.accept via _fallback_socketpair. This identifies the observed wait site, not the root cause.
- The last 60 lines at interruption were preserved in d2.txt in the temporary output folder.

D3 — root backend/.venv python -X faulthandler -m pytest -p no:cacheprovider -o addopts="" -vv -s --durations=20 -o faulthandler_timeout=120 tests/integration/lesson_library/test_lesson_library_api.py

- NOT RUN because D2 was interrupted. No retry was made.

## Source and test pins before and after

| File | Bytes | SHA-256 | Post-run |
|---|---:|---|---|| backend/src/sketch2life/interfaces/http/routers/lesson_library.py | 28784 | 732DB7C469B9900C94A8B85E92A530934A346AA3BABE4D88C4CB61358DFC9400 | unchanged |
| backend/src/sketch2life/infrastructure/lesson_library/service.py | 91447 | F37DB928B3C7CA5115A537D9E82D740D4BF9B23F34C02A0CBEE3C30BB995255D | unchanged |
| backend/src/sketch2life/interfaces/http/openapi_contract.py | 1379096 | 35801B20DC67630B9AAEEFDD46F82886CD91F34990BA2CCE6C2B3E67B6A989B7 | unchanged |
| backend/tests/integration/lesson_library/test_lesson_library_api.py | 48196 | BD0FEE18BD3C1F71462C42C2C46E7BFB204B4CEF32425340026E3D5FF635DF6D | unchanged |
| backend/tests/unit/test_lesson_library_receipt_compatibility.py | 8798 | B2DAFF304574DB55ABA438783567BAE2EE9F5BEE1237A3F2CF3FF6F3CD384E5C | unchanged |
| backend/tests/contract/test_openapi_contract_catalog.py | 21114 | 7D242528CC5BD3AACDE5EF2C1106B734B710D67E8D88C33AEB2A14D2237D428B | unchanged |
## Output artifacts
- d1.txt: 6286 bytes; SHA-256 D8E788A283CBA4C6CCB47641878BBC2674F77320679F9AB2860BFA395A587F29
- d2.txt: 7414 bytes; SHA-256 150A4EFD3FD08F127802FA24E027BDE00F27A8DED6EF69419013C03CFEC99C64
- exit-codes.txt: 133 bytes; SHA-256 B8F64076EFC9699B1D4515E1EB9DEC999A6ED47B7E497D5C4ED4E7E7390D237D
## Limits and disposition

One diagnostic attempt on one machine used the owner-prepared local throwaway database. Pytest flags changed verbosity, output capture, cache behavior and hang traceback reporting; test selection and semantics were unchanged. No retry, D3 run, build, typecheck, lint, validator, OpenAPI generation, app runtime, or implementation was performed. Whether this diagnostic satisfies MGR-8 remains for the owner to decide.
