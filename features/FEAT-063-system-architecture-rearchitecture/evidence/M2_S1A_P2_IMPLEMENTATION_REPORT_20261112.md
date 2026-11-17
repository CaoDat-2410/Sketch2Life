# M2 S1a-P2 Close-out Update — 2026-11-13 (Draft)

**Current disposition:** Gate P2 attempt 1 `FAILED`; approval `CONSUMED`; no second M2 task-database attempt is authorized. Coordinator pytest run 4: `1 failed, 125 passed in 75.59s`, only the unchanged baseline OpenAPI catalog failure. Targeted mypy and Ruff on the two changed files: 0 diagnostics, exit 0. Formal closure awaits explicit owner `ACCEPTED`. No PostgreSQL PATCH, DELETE, or list verification is claimed.

Owner-run counts show only create committed (+1 profile, +1 revision, +1 receipt). The transaction-boundary explanation is an `INFERENCE` from code because runner safety scanning withheld pytest output. The ownership-check fix and two offline regressions do not prove real-PostgreSQL behavior. Three extra synthetic rows remain; do not clean them up.

Changed pins: `backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py` = 19813 bytes / `1AF38B44ACBB40C94BD0B77F54A1BF0B1C90AE5F8C9F9D9A95DA055B5F4D1742` (R5 `4D9C502FEA7E482607CF485CB11767C5280FFF3BA1F9E4055353978EB7424751`; pre-rework Gate P2 `680FF349F7ED340EDE4C80AE085EFB0CC8DE788EA0620993115F617FA5488D63`); `backend/tests/unit/test_parent_profiles_service.py` = 10243 bytes / `99A82152F2DA3D72BB085FB7A967EB3113FB98CF743637EC6FB0681DEF57989C` (R5 `B9B3346B766E821B2712FFED1B7CA858AD5C29284D107B8175480DECDD44F218`; pre-rework Gate P2 `49FB5493AFD8544A36617F09B701510D87978388698D5B2B164A072823CCCB7B`).

Run-4 pytest stdout: `tmp/m2-s1a-p2-impl/coordinator_post_run4_20261113T093225/pytest.stdout.txt`, 38,358 bytes / `D440DA6E8353E7CD9E3486D081DF5FFFCC081C7F4F44CB4C4F8AA28B84CD2009`. Targeted mypy stdout 44 bytes / `0C37C4158C91EF55C724BA017BF6465F26018199BADB08E3FF13F98ACDF056C2`; Ruff stdout 19 bytes / `82B3E6A6C090A57601D22943BD23FCA9218D1031DBE5A7B754092F9A156B4F18`. The widening is consumed. No separate pytest exit-code receipt was present in the listed folder.

Scratch append pins only: DECISIONS 182,704 B / `3F326E490BF6ECA10B516631F151368F8C5F59D43D24F16F3C66CFE0A3C30B59` -> 184,622 B / `E6199F504B5DF2EB4B375996F951D5C19E6690D319E4BF1BD47279CB0066E39D` after D-193; TASK_APPROVAL 398,562 B / `1D90D1DE5B8F25606318F31144B6859ADE9DF679F1F9F6F7AF6FBF51E2C9A0C7` -> 401,733 B / `F009A6298B3B1857F825FAE57287B76B24F074E5D66BAE26BA1CBAB6AEC1C1B2` after the draft addendum. No live file changed.

NOT RUN / NOT VERIFIED: real-PostgreSQL PATCH, DELETE, and list; second Gate P2 attempt; cleanup; post-final-edit validators and `git diff --check`; formal acceptance and closure-record installation. Production BE1 adapter on PostgreSQL is NOT COVERED under D-190. OWNER_MODAL_CALL_APPROVED=NO.

---

> Historical implementation report from the live predecessor follows unchanged. Its earlier current-state statements are dated history and superseded by this update.

> Owner-authorized canonical report update: records coordinator pytest run 3 and is installed under the 2026-11-13 authorization.

# M2 S1a-P2 Implementation Report — 2026-11-12

**Status: IMPLEMENTED / POST-IMPLEMENTATION PYTEST RUN 3 COMPLETE / NOT ACCEPTED.** Gate P2 is APPROVED (Gate P2 only) and NOT LAUNCHED. This report records implementation and offline command evidence; it is not a closure record or a phase-acceptance statement.

## Authority and repository state

- Approved specification: `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_P2_TASK_APPROVAL_DRAFT7_20261112.md`, SHA-256 `49B5352CA552DEC9C53C4B155C196C64FD0CE9115E844FC0CBFB8BF3613B66A1`.
- Approved implementation allowlist: `tmp/m2-s1a-p2/ALLOWLIST_DRAFT_20261112_R5.md`, SHA-256 `4C891112CB894ADF265927F392A437D66BE9DFDF5B1B06DF162ABD1264188DFA`.
- Original report-drafting-time decision record pin: `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`, 180,350 bytes, SHA-256 `6D6994F1504E811A7AC547D40E34146ABF6AFC46F20696C6B11B7008061C5F95`.
- Original report-drafting-time feature approval record pin: `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`, 379,871 bytes, SHA-256 `AE6E05C71330DF6F1389A4E69CEE49245F040067795732CF5673AE81884B4A02`.
- Branch and base: `feature/feat063-m2-parent-teacher-foundation`, HEAD `c32d0b060e9625854dbdb781d7f8b11467bdca34`; the index is empty.
- Canonical repository requirement source remains unsigned SRS Rev60. Owner-supplied Rev62 is local and unsigned; it did not replace the repository pin. `OWNER_MODAL_CALL_APPROVED=NO`.

## Implemented scope

The implementation follows Draft 7 and the exact R5 path set. Fifteen existing allowlisted files have source/test edits. The approved `router_composition.py` path has no diff. New allowlisted artifacts created for implementation are the Parent role port and BE1 adapter, the offline role-adapter test, the Gate P2 PostgreSQL test, the Gate P2 runner, this implementation report, and the Gate P2 launch instruction. The owner checklist is created alongside this report. The allowlisted closure-record path remains absent and forbidden until the owner explicitly records `ACCEPTED`.

The implementation adds an application `ParentRolePort`, a BE1 identity adapter for `be1_adult_identities.account_role`, and route-level role enforcement for all five Parent operations. Collection POST/list role failures use generic 403 `ACTION_NOT_ALLOWED`. Profile-targeted GET/PATCH/DELETE first parse the raw `profile_id`, perform an issuer-and-subject owner lookup, and return the same 404 `PROFILE_NOT_FOUND` for missing or non-owned profiles; role denial is 403 only after ownership is established. The route parser preserves the specified validation order and generic `field_errors` vocabulary. This route-level placement is the documented, intentional deviation from SRS section 9.9 rule 2; repository ownership and transaction checks remain in place.

The Parent list uses an owner-scoped keyset over (`created_at`, `profile_id`), defaults to 25 items, rejects limits above 100, emits an opaque versioned cursor, and omits non-active profiles. The DELETE operation requests `DELETE_PENDING`, returns a minimal 202 view, and uses the existing Parent command-receipt table. A pending profile is shown as a status-only view; a new PATCH or DELETE key is rejected with 409 `INVALID_STATE_TRANSITION`; same-key replay returns the stored result. Existing receipt-first ordering and payload fingerprints are preserved. Revision hashing retains `age_band_ref` and `age_band_version` as JSON null; Rev62 age-band values and catalog behavior remain deferred.

OpenAPI operation/catalog and SRS-projection edits cover the two added Parent operations and the specified response schemas. Tests were updated for the route mount matrix, role and error precedence, field errors, cursor/list behavior, receipts, and the exact route catalog. The round-5 P3 carry-forwards are implemented: the fake-role-adapter failure case asserts 503 `PARENT_STORE_UNAVAILABLE` and no writes; implementation and future closure evidence must cite Draft 6 sections 5, 8, and 9 as the historical absent-column references and must leave pinned Draft 6 and Draft 7 bytes unchanged.

No Parent migration or schema alteration was added. The owner's read-only preflight reported that `account_id`, `account_role`, and `role_revision` are absent from `public.be1_adult_identities`; Codex did not query the database. Therefore, production BE1-adapter behavior against PostgreSQL remains **NOT COVERED** under D-190. Offline route tests use a fake role adapter. Gate P2 uses an application-layer role stub and covers Parent-owned list, deletion-request, and receipt behavior only; it does not seed BE1 identities or call the production adapter.

## Acceptance traceability and execution state

Draft 7 defines eight criteria. R5 maps seven to the exact offline pytest selection and three to the separately owner-run Gate P2, with P2-AT-02 and P2-AT-05 covered by both forms of evidence. The production BE1-adapter/PostgreSQL subpath of P2-AT-01 is explicitly NOT COVERED. Run 2 executed and produced the two failures described below. The new route error-envelope failure was caused by a missing fake-role dependency override in the test setup and is corrected in the allowlisted test file. Coordinator-run pytest run 3 is complete; its official result is recorded below.

| Criterion | Evidence defined by Draft 7 / R5 | Current execution state |
|---|---|---|
| P2-AT-01 | Offline route and fake-adapter tests; production adapter on PostgreSQL excluded under D-190 | Run 3 complete; only the unchanged OpenAPI baseline failure remains; PostgreSQL adapter path NOT COVERED |
| P2-AT-02 | Route/service pagination tests and Gate P2 Parent-owned pagination evidence | Run 3 complete; Gate P2 NOT LAUNCHED |
| P2-AT-03 | Gate P2 Parent-owned deletion lifecycle | NOT RUN; requires separate current owner-run approval |
| P2-AT-04 | Route tests for `field_errors`, path UUID errors, and validation precedence | Run 3 complete |
| P2-AT-05 | Route/service receipt tests and Gate P2 receipt/replay evidence | Run 3 complete; Gate P2 NOT LAUNCHED |
| P2-AT-06 | Existing route/service/migration compatibility plus role fixture update | Run 3 complete; migration test is mode H and read-only |
| P2-AT-07 | App composition and OpenAPI operation/catalog tests | Run 3 complete; the unchanged baseline `142 == 131` catalog mismatch is the only failure |
| P2-AT-08 | Domain/service/route canonical revision-hash tests | Run 3 complete |

The unchanged baseline failure is `backend/tests/contract/test_openapi_contract_catalog.py::test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates`, which reports `assert 142 == 131` for the 11 PR #22 operations not catalogued. Run 2 also failed `backend/tests/contract/test_parent_profiles_routes.py::test_parent_unhandled_errors_keep_the_safe_error_envelope`: the test overrode only the principal and profile service, so the real Parent role dependency attempted its fail-closed path with `database_url=None` and returned 503 before the test service could raise its expected 500. The allowlisted test now overrides `get_parent_role_reader` with `_FakeRoleReader()`, matching the same file's other route setups. Coordinator-run pytest run 3 completed on the same ten files: 124 collected, official summary `1 failed, 123 passed in 11.84s`. Its sole failure is the unchanged OpenAPI catalog baseline case; the error-envelope test now passes. The `ERROR sketch2life.api ... parent_unhandled_exception` line is expected captured output from that passing test, not a failure. The launcher supplied no exit-code receipt, so no exit code is asserted. Run 3 evidence: `tmp/m2-s1a-p2-impl/coordinator_post_run3_20261112T222614/pytest.stdout.txt` is 37,810 bytes, SHA-256 `FA76C7DD28D95C5A9E22A13D14E4F2FB5B79C5FD82424482E97EDEEAC90A5CAB`; companion `status.txt` is 266 bytes, SHA-256 `00B5B9F0085F09D94D5B66C34A62A96A1B3B5C84227A37846F04598A4B273C45`. No exit-code receipt was supplied; the official summary is the verdict. Do not add the 11 OpenAPI operations or edit `test_openapi_contract_catalog.py`; no further pytest run is authorized.

## Verification record

### Pytest

The first sandbox attempt stalled and had no official summary; under the owner's clarification it is recorded as INTERRUPTED (sandbox), NOT RUN, and not counted. The coordinator ran the exact nine-file baseline outside the Codex sandbox as pytest run 1: exit 1, official summary `1 failed, 108 passed in 10.89s`, 109 collected, 0 skipped. The single failure is the known OpenAPI baseline mismatch above; `test_parent_routes_return_contract_shapes` passed. Log `tmp/m2-s1a-p2-impl/coordinator_baseline_run1_20261112T191154/pytest.stdout.txt` is 33,716 bytes, SHA-256 `CC6ACE4C1043E17580941DE36494024923FC530D2BE8100332D01FF29B0E5AC1`; `status.txt` SHA-256 is `2D7FE17631F974A8FB4C2955619CD6170A41674494716CB6AB28225BC8F37E39`.

Pytest run 2 was coordinator-run using the exact ten-file post-implementation selection in Draft 7 section 7 and R5 section 10: the nine baseline files plus `backend/tests/unit/test_be1_parent_role_adapter.py`. It contains no PostgreSQL integration test. Official summary: `2 failed, 122 passed in 28.69s`. Stdout `tmp/m2-s1a-p2-impl/coordinator_post_run2_20261112T220702/pytest.stdout.txt` is 40,050 bytes, SHA-256 `3897FB6D93D4944F7C7F97AD9110C262ABE8E5D481DC38A55E13D51FF3292232`; `status.txt` is 287 bytes, SHA-256 `D542ED597215FB89D4772A2297B69291D165BD5F49ECAFFF5AD9815F89E1184C`. Safety scan found 0 scheme, userinfo, or credential-assignment matches. The two failures were the unchanged OpenAPI baseline issue and the test-setup issue described above. The owner then widened the two-run ceiling to three for that test-only correction and authorized one coordinator-run run 3 on the same ten files. Run 3 produced `1 failed, 123 passed in 11.84s`; only the unchanged OpenAPI baseline test failed. The corrected error-envelope test passed. The launcher supplied no exit-code receipt. No further pytest is authorized.

### Mypy

All runs used strict mypy on `src/sketch2life tests`. Exit 1 is not a PASS; the comparison criterion is no diagnostic signature absent from baseline, ignoring line numbers.

| Run | Official result | Comparison and record |
|---|---|---|
| Baseline run 1 | `Found 6748 errors in 313 files (checked 975 source files)`; exit 1 | `tmp/m2-s1a-p2-impl/baseline-mypy_20261112T120311Z_b87e92ca/stdout.txt`, 991,128 bytes, SHA-256 `D4FA27B17E87122424BFB884DAF8264BE5978F481C70187EE5425199E238B51D` |
| Post-implementation run 2 | `Found 6750 errors in 315 files (checked 979 source files)`; exit 1 | Two new signatures were corrected afterward: repository local-name redefinition and adapter `Any` return. Stdout SHA-256 `55DA4B9C322CEFE97A34E81949419806594A5CF9515B1D6F652F9C22FDF0328C` |
| Post-fix run 3 (owner-authorized) | `Found 6749 errors in 314 files (checked 979 source files)`; exit 1 | One new `no-redef` signature remained in `delete_profile`; the adapter `no-any-return` signature was gone. Stdout SHA-256 `80B949BE0B5224828F098B68AE6B86A652FF8107B83C4F38C8068A3AB1652797` |
| Post-fix run 4 (owner-authorized, final) | `Found 6748 errors in 313 files (checked 979 source files)`; exit 1 | Compared with baseline: 0 new and 0 missing signatures. Stdout 1,982,258 bytes, SHA-256 `F53D63A027341D4ECAC1E7D441E7C47E97A0D23860719CB75D82B2F3872BF0B0`; stderr empty; exit-code file contains `1`. |

Run 4's safety scan found 37 scheme strings, all `https://mypy.readthedocs.io/`; it found no userinfo, password, token, or credential-assignment matches. The mypy process was complete, an exit receipt existed, and no project backend Python process remained before the output files were read.

The sole run-3 diagnostic was `src/sketch2life/infrastructure/persistence/parent_profile_repository.py:304: Name "body" already defined on line 293 [no-redef]`. The only follow-up edit renamed the local in the 409 `DELETE_PENDING` branch to `conflict_body`; run 4 confirms that signature is gone with no baseline signatures missing.

### Ruff

Ruff baseline run 1 reported 222 errors (82 `I001` and 140 other diagnostics). Post-implementation run 2 reported 226; four added findings were corrected. The owner-authorized Ruff post-fix run 3 exited 1 with `Found 222 errors.` Signature comparison against baseline found 0 new and 0 removed diagnostics. Stdout was 206,130 bytes, SHA-256 `ED36AA87765BCFFF6159E9D550C1B877D6E9A8FAECE6B354EDC638C540C92142`; stderr was empty; exit-code file contains `1`. Its safety scan found one HTTPS URL-like source string with a synthetic example hostname, and no userinfo, password, token, or credential-assignment matches; no URL was contacted. The owner did not authorize a further Ruff run after the final local variable rename.

### Validators and diff check

`validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check` each passed in the previous final source check set (`post-checks-r2-20261112`) before the final two-reference `body` to `conflict_body` rename. The earlier check set also passed. No additional validator or diff-check was run after that final source edit. The owner’s conditional authorization for one further run of each is unused until the final source and owner-requested records are in place. `validate_skeleton.py` was not run; no repository directory structure was added.

## Owner-run boundary and remaining work

The Gate P2 runner and launch instruction are present, and the separately reviewed Gate P2-only approval is recorded. Gate P2 remains NOT LAUNCHED until the owner runs the single command. Its expected single invocation adds one `parent.child_profiles` row, two `parent.profile_revisions` rows, and three `parent.command_receipts` rows, for six total rows; the data is retained and must not be cleaned up or produced by a retry. The accepted S1a-P Gate B post-inventory pin is `5A5DBC464ED1FD57C88860BD9E0313920B328A9EF39BB37EA4C91B631B8C1D98` (120 tables, 36 rows). The owner-reported absent BE1 role columns remain unchanged; no BE1 migration or seed is allowed here.

No database query or write, Alembic command, Gate P2 run, Docker, Modal, provider, network action, pytest run by Codex, stage, commit, or push was performed. No Alembic command, migration or DDL is included; the runner and test perform a read-only check of `public.alembic_version`. S1a-P2 is not accepted; S1b, S2, S3, and M3–M6 remain closed. Do not create the closure record until the owner explicitly writes `ACCEPTED`.

D-192 has been appended to `DECISIONS.md`, and its append-only pin-refresh addendum precedes the Gate P2 approval entry in the feature `TASK_APPROVAL.md`. The post-D-192 `DECISIONS.md` pin is 182704 bytes, SHA-256 `3F326E490BF6ECA10B516631F151368F8C5F59D43D24F16F3C66CFE0A3C30B59`. The Gate P2 approval-prefix value is recorded in the final approval entry and was computed from the scratch append sequence. The draft records mypy post-fix runs 3 and 4, Ruff post-fix run 3, and coordinator pytest run 3. Any final validator/diff-check runs, if separately authorized and completed, must also be recorded. No commit is requested or made by this report.
