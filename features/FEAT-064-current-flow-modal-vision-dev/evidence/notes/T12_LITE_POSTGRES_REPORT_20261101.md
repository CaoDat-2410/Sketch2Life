# T12-lite PostgreSQL report — 2026-11-01

## Scope and safety boundary

- T12 execution specification: `.claude/handoff/CODEX_PROMPT_T12_POSTGRES_RUN_20261101.md`, SHA-256 `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C506365D`.
- The owner-created local connection source was read only into the test process environment. No connection string, password, `.env`, or token is recorded here.
- Safety conditions: (a) local ignored connection source present/readable — **yes**; (b) database name contains `be1_acceptance` — **yes**; (c) target and query overrides are loopback only — **yes**; (d) connection succeeds to PostgreSQL **17.11** — **yes**; (e) the database contains repository migration-owned schemas only — **yes**, 99 user tables across 10 repository schemas, with no unexpected schema/table detected.
- Tests used synthetic-prefixed identities and their fixtures. No table was dropped or truncated. Test-created rows were removed by fixture/manual cleanup. After the final synthetic-pilot rerun, counts across all 99 user tables had **no delta** from the per-run baseline; managed profiles and synthetic eligibility proofs remained at zero.
- No source implementation or Alembic migration was edited during T12. The only code-path change for the final rerun was import ordering and type annotations/import location in the allowlisted PostgreSQL test.

## Schema migration checks

- `alembic upgrade heads`: succeeded; no revisions were applied because all 10 version rows already matched the current heads.
- Authorized round trip: `downgrade be1_core@-1` downgraded `20261101_be1_age_0001` to `20261031_be1_se_0001`; `upgrade be1_core@head` restored `20261101_be1_age_0001`. Both commands succeeded.
- Pre-downgrade safety counts: `be1_managed_profiles=0`, `SYNTHETIC_DEV profiles=0`, `be1_synthetic_eligibility_proofs=0`. After upgrade, `age_revision` and `age_source` were present again, profiles/proofs remained zero, and all 10 Alembic version rows exactly matched the pre-round-trip set.

## PostgreSQL test outcomes

| Test module | Result | Finding / cleanup |
| --- | --- | --- |
| `tests/integration/test_be1_postgres_api.py` (excluding the global retention-worker case) | **1 passed, 2 failed, 1 deselected** | Route catalog assertion expected 50 and observed 51. `test_room_code_start_revocation_stage_and_early_outcome_are_durable` expected HTTP 200 but received HTTP 409 `CONSENT_NOT_EFFECTIVE`. No source or old test was changed. The 3 synthetic organizations, 4 synthetic adults, and one new rate-limit row from the failed run were removed; table counts returned to baseline. |
| `tests/integration/test_be1_age_provenance_postgres.py` | **1 passed** | Fixture cleanup restored table counts. |
| `tests/integration/lesson_library/test_lesson_library_api.py` | **5 passed, 1 failed** | `test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http` received HTTP 503 `DEPENDENCY_UNAVAILABLE`: local ClamAV at loopback port 3310 was unavailable. Fixture cleanup restored table counts; no scanner/package was installed. |
| `tests/integration/test_be1_synthetic_pilot_postgres.py` | **56 passed in 70.77s** on the final rerun after test typing/import fixes; the earlier run also exited **0** | Rerun compared row counts for all 99 user tables; no count changed, profiles/proofs remained zero. The test module blocks non-loopback sockets. |
| AI Jobs PostgreSQL migration tests that create/drop a separate database | **NOT RUN** | Outside the one-database approval boundary. No second database was touched. |

## Static checks

- Ruff check on the new T12 test: **passed** after correcting four import-order findings (three in the first pass and one in the second).
- Ruff format check: **passed**, file already formatted.
- Mypy strict on the new T12 test with a fresh temporary cache: **passed**, no issues in one source file. The initial default-cache invocation returned an internal mypy error; it was retried with a fresh cache. Three test-file diagnostics were corrected before the passing run.
- Final repository checks: `python tools/validate_harness.py` → `HARNESS_VALID`; `python tools/validate_repository_security.py` → `REPOSITORY_SECURITY_VALID` (6,032 publishable files); `python tools/validate_architecture.py` → `ARCHITECTURE_VALID`; `git diff --check` clean. The test/report/ledger byte scan found UTF-8, LF, no BOM, and no trailing whitespace.

## Conclusion and limits

- **B4a PostgreSQL acceptance: not fully achieved.** The synthetic pilot module passed all 56 cases, but the existing BE1 PostgreSQL module retains the 51-versus-50 route-count assertion and the consent guard returns 409 where one test expects 200. No product behavior was weakened or patched.
- **B5 PostgreSQL acceptance: not fully achieved.** Five Lesson Library tests passed, including `test_parent_group_accept_replays_legacy_receipt_without_repeating_effects`; the upload/review path failed because the local ClamAV dependency was unavailable.
- This is one isolated local PostgreSQL database run only. It does not establish provider/Modal behavior, UI/visual AC20, production readiness, or a complete end-to-end Child-to-Teacher AI flow. No Modal/GPU/provider call, external network request, or real-child data was used.
- No stage, commit, or push occurred.

## Đối chiếu hai lượt chạy

- Bản báo cáo đã commit ở HEAD được giữ nguyên từng byte tại [`T12_LITE_POSTGRES_REPORT_20261101_RUN1_AS_COMMITTED.md`](T12_LITE_POSTGRES_REPORT_20261101_RUN1_AS_COMMITTED.md), SHA-256 `98DE23DFEE611B491E90FFEA9DDAAB82962D4D0565253E9C6885CD1C80574D63`.
- Bản RUN1 nói fixture B5 replay không tự dọn hàng; sau đó người chạy đã xóa các hàng thuộc tổ chức synthetic bằng khóa/phạm vi cụ thể và xác nhận các bảng ứng dụng trống. Báo cáo hiện tại nói fixture của lượt chạy sau khôi phục số lượng hàng; source hiện tại có `finally` dọn các hàng theo tổ chức do fixture sở hữu. Hai bản ghi khác nhau về cơ chế/thời điểm dọn, nhưng đều nói các hàng đã được dọn trước khi kết thúc lượt tương ứng.
- Không có log hoặc bảng đếm trước/sau riêng cho B5 để xác định độc lập cơ chế dọn ở từng lượt. Kết luận: **MÂU THUẪN CHƯA PHÂN XỬ** về việc hàng B5 được fixture tự dọn hay phải dọn thủ công ở mỗi lượt; không suy ra còn hàng sót sau các lần chạy.
- Đề xuất một lượt kiểm riêng có approval: chạy duy nhất B5 trên ranh giới DB dùng một lần, ghi số hàng theo từng bảng trước/sau, ghi rõ fixture teardown và không thực hiện dọn thủ công trước khi chụp số sau.
