# S1a-P2 Close-out Owner Checklist — 2026-11-13 (Draft)

**Current state:** Gate P2 attempt 1 `FAILED` / approval `CONSUMED`; no second M2 task-database attempt authorized. Three extra synthetic rows remain; do not clean them up. Run 4 is complete; acceptance awaits explicit owner `ACCEPTED`.

Do not use the Gate P2 launch steps in the historical checklist below. Run 4 used the same ten files: `1 failed, 125 passed in 75.59s`, only the unchanged baseline catalog test failed. Targeted mypy/Ruff on the two changed files exited 0 with 0 diagnostics. These run ceilings are consumed. Post-final-edit validators and `git diff --check` are NOT RUN.

The transaction-boundary cause is an INFERENCE from code because output was withheld. The fix and two regression tests do not verify real PostgreSQL. PATCH, DELETE, and list remain an open item for a scratch DB before merge to `dev`; the M2 task DB must not be used. Production BE1 role adapter is NOT COVERED under D-190. OWNER_MODAL_CALL_APPROVED=NO; S1b DEFERRED; S2, S3, M3-M6 closed.

Current pins: `backend/src/sketch2life/infrastructure/persistence/parent_profile_repository.py` 19813 B / `1AF38B44ACBB40C94BD0B77F54A1BF0B1C90AE5F8C9F9D9A95DA055B5F4D1742`; `backend/tests/unit/test_parent_profiles_service.py` 10243 B / `99A82152F2DA3D72BB085FB7A967EB3113FB98CF743637EC6FB0681DEF57989C`. Their R5 pins were `4D9C502FEA7E482607CF485CB11767C5280FFF3BA1F9E4055353978EB7424751` and `B9B3346B766E821B2712FFED1B7CA858AD5C29284D107B8175480DECDD44F218`; their pre-rework Gate P2 pins were `680FF349F7ED340EDE4C80AE085EFB0CC8DE788EA0620993115F617FA5488D63` and `49FB5493AFD8544A36617F09B701510D87978388698D5B2B164A072823CCCB7B`.

The closure-record draft proposes `ACCEPTED WITH KNOWN GAP` but is not installed. Do not create the canonical record until the owner explicitly says `ACCEPTED`.

---

> Historical checklist from the live predecessor follows unchanged for prior run provenance only. Its Gate P2 launch instructions are superseded; do not use them.

> Owner-authorized canonical checklist update: records coordinator pytest run 3 and is installed under the 2026-11-13 authorization.

# Owner Checklist — S1a-P2 Gate P2 and Closeout

**Current state: PYTEST RUN 3 COMPLETE; GATE P2 APPROVED (GATE P2 ONLY); NOT LAUNCHED; AWAITING OWNER-RUN.** This checklist is operational guidance, not an approval or launch authorization. `OWNER_MODAL_CALL_APPROVED=NO` remains in force.

## 1. Post-implementation offline pytest

Coordinator-run pytest run 3 is complete outside the Codex sandbox on the same ten approved files listed below. It collected 124 items and returned the official summary `1 failed, 123 passed in 11.84s`; the sole failure is the unchanged OpenAPI baseline test. The launcher did not provide an exit-code receipt. Run 3 stdout is `tmp/m2-s1a-p2-impl/coordinator_post_run3_20261112T222614/pytest.stdout.txt` (37,810 bytes, SHA-256 `FA76C7DD28D95C5A9E22A13D14E4F2FB5B79C5FD82424482E97EDEEAC90A5CAB`); companion `status.txt` is 266 bytes, SHA-256 `00B5B9F0085F09D94D5B66C34A62A96A1B3B5C84227A37846F04598A4B273C45`. Codex must not run pytest again. This does not authorize Gate P2 or any database action.

The ten files are:

1. `backend/tests/unit/test_parent_profiles.py`
2. `backend/tests/unit/test_parent_profiles_service.py`
3. `backend/tests/contract/test_parent_profiles_routes.py`
4. `backend/tests/contract/test_app_composition.py`
5. `backend/tests/contract/test_openapi_contract_catalog.py`
6. `backend/tests/unit/test_be1_fact_reader.py`
7. `backend/tests/contract/test_be1_fact_reader_contract.py`
8. `backend/tests/unit/test_synthetic_audience_limit.py`
9. `backend/tests/unit/test_parent_profiles_migration.py` (hash-only, read-only; the module states that it never executes DDL)
10. `backend/tests/unit/test_be1_parent_role_adapter.py`

Run 1 was the pre-edit nine-file baseline: `1 failed, 108 passed in 10.89s`, with the known OpenAPI catalog difference `142 == 131` for the 11 PR #22 operations that are not catalogued. Run 2 returned `2 failed, 122 passed in 28.69s`: that unchanged catalog failure plus a new error-envelope test failure. The latter was caused by the test overriding principal and service but not `get_parent_role_reader`; the allowlisted test now installs `_FakeRoleReader()`, consistent with the other tests in the same file. The owner widened the two-run ceiling to three for this one test-only correction. Run 3 returned `1 failed, 123 passed in 11.84s` (124 collected); only the unchanged OpenAPI catalog test failed, and `test_parent_unhandled_errors_keep_the_safe_error_envelope` passed. The captured `ERROR sketch2life.api ... parent_unhandled_exception` line is expected output from the passing test. The launcher supplied no exit-code receipt. Run 3 stdout is `tmp/m2-s1a-p2-impl/coordinator_post_run3_20261112T222614/pytest.stdout.txt` (37,810 bytes, SHA-256 `FA76C7DD28D95C5A9E22A13D14E4F2FB5B79C5FD82424482E97EDEEAC90A5CAB`); companion `status.txt` is 266 bytes, SHA-256 `00B5B9F0085F09D94D5B66C34A62A96A1B3B5C84227A37846F04598A4B273C45`. No further pytest run is authorized; do not edit the catalog test or add the 11 PR #22 operations.

## 2. Interpret the already completed type/lint checks

- Mypy post-fix run 4: exit 1 because the baseline has 6,748 diagnostics; diagnostic-signature comparison has 0 new and 0 missing. This is not a PASS.
- Ruff post-fix run 3: exit 1 with 222 diagnostics, equal to baseline; comparison has 0 new and 0 removed. No additional Ruff run is authorized after the final local rename.
- Earlier final-source validator/diff-check runs passed before that local rename. Do not describe them as checks of the final bytes. The conditional one-more-run authorization for `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check` has not been used; wait until the final source and owner-requested records are in place.

The complete run history, log paths, hashes, and safety-scan counts are recorded in `tmp/m2-s1a-p2-impl/COMMAND_LEDGER.md` and the implementation report. D-192 has been appended to `DECISIONS.md`; the append-only pin-refresh addendum and Gate P2 approval entry are recorded in the feature `TASK_APPROVAL.md`. The post-D-192 decision pin is 182704 bytes, SHA-256 `3F326E490BF6ECA10B516631F151368F8C5F59D43D24F16F3C66CFE0A3C30B59`. The Gate P2 entry carries the approval-prefix hash computed from the scratch append sequence. Any separately authorized final validator/diff-check runs must also be recorded before the single S1a-P2 commit.

## 3. Gate P2 remains a separate owner-run gate

Do not launch Gate P2 under the Draft 7 implementation approval alone. The separately reviewed Gate P2-only approval entry and current owner launch instruction are now in place. Gate P2 remains NOT LAUNCHED until the owner runs the single command.

With that separate approval and launch instruction in place, the owner should:

**Credential boundary (Owner decision, 2026-11-13, Option A):** The prohibition on a database URL or password applies to the parent PowerShell shell and its process environment, command text, shell history, logs, and files. After the hidden `getpass` prompt, the runner may construct the database URL in memory and pass it in the pytest child-process environment as `SKETCH2LIFE_DATABASE_URL` and `S1A_P_TEST_DATABASE_URL` for the duration of the run, matching the accepted S1a-P Gate B runner. Residual risk: another process running as the same account may read that child-process environment while pytest runs. The owner may rotate the database password after the run. The runner remains unchanged.

1. Before the owner run, confirm that the canonical launch-instruction path contains the final owner-authorized bytes and matches the length and SHA-256 pinned in the Gate P2 approval entry. Recompute its byte length and SHA-256 and the exact manifest table; confirm the approval entry pins those values. Recheck the accepted S1a-P Gate B post-inventory SHA-256 `5A5DBC464ED1FD57C88860BD9E0313920B328A9EF39BB37EA4C91B631B8C1D98` (120 tables, 36 rows). Stop on any pin, inventory, identity, revision, manifest, or environment mismatch.
2. Immediately before launch, ensure the parent PowerShell shell and its process environment have no variable whose name begins with `PYTHON`, `PYTEST`, `DATABASE`, `PG`, `POSTGRES`, `SQLALCHEMY`, or `ALEMBIC`. Do not read `.env`.
3. Run only the single command in `M2_S1A_P2_GATE_P2_LAUNCH_INSTRUCTION_20261112.md`, from the repository root, after its gates are approved. Enter the password only at the runner's hidden prompt. Gate P2 has no preview prompt.
4. Expect one `parent.child_profiles` row, two `parent.profile_revisions` rows, and three `parent.command_receipts` rows: six added rows total. Keep them; do not clean them up or retry the one-shot runner.
5. Return the exact `RUN_ID`, `LOG_DIR`, `POST_INVENTORY_SHA256`, process exit code, official pytest summary, and complete requested logs. Never send the password or a database URL.

Gate P2 uses an application-layer role stub and covers Parent-owned list, deletion-request, and receipt behavior only. It does not query the production BE1 role adapter or seed/change BE1 identity data. The owner-reported absence of `account_id`, `account_role`, and `role_revision` in `public.be1_adult_identities` remains unverified by Codex; production adapter behavior against PostgreSQL is NOT COVERED until a separate owner decision aligns that database state. No BE1 migration, cleanup, Docker, Modal, provider, or network action is authorized here. No Alembic command, migration or DDL is included; the runner and test perform a read-only check of `public.alembic_version`.

## 4. Acceptance and closeout boundary

The coordinator run-3 log is complete. After reviewing it and any separately approved Gate P2 evidence, the owner must state acceptance explicitly. Only after the owner writes `ACCEPTED` may the allowlisted S1a-P2 closure record be created. This checklist does not accept S1a-P2, authorize Gate P2, or open S1b, S2, S3, or M3–M6. No stage, commit, or push is requested by this checklist.
