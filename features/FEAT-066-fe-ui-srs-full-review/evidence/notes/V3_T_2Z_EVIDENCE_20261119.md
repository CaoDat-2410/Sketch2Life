# V3 T-2z Local S3Mock storage and scanner / media-validator adapters (TD-29) - evidence note (2026-11-20)

Status: accepted by the goal under program approval after implementation review R1 (ACCEPTABLE WITH NOTES, 0 P1 / 0 P2 / 6 P3, all handled in section 7); owner final check pending. Plan: `plan/V3_T_2Z_PLAN_DRAFT1_20261119.md` (plan review R1: READY WITH NOTES, 0 P1 / 4 P2 / 8 P3, all applied below). Backend at `.worktrees/v3`, branch `feature/backend-srs-api-v3`, base HEAD `f7ab272c` (contains T0.1-T0.5 and T0.11). One local commit, not pushed. SRS lines are `l.N` of the canonical SRS (443A3CA3).

## 1. What changed

New (under `backend/`):
- `src/sketch2life/application/ports/upload_validation.py`: optional port `UploadMediaValidator.validate(file_obj, *, declared_media_type) -> MediaValidationResult(detected_media_type, validator_name, validator_version)`, `UploadMediaRejected(code)` with codes `UNSUPPORTED_MEDIA_TYPE` and `UPLOAD_CONTENT_MISMATCH` (SRS 9.8 l.870-871), and one pure signature table (`header_matches_media_type`, `is_known_media_type`): PNG, JPEG, WebP (RIFF/WEBP), PDF, WAV (RIFF/WAVE), DOCX and PPTX (ZIP local header). It reads at most 16 header bytes and decodes nothing.
- `src/sketch2life/infrastructure/documents/local_test_adapters.py`: `LocalTestAllowlistScanner(env, allowed_sha256)`, `LocalTestSignatureMediaValidator(env)`, `LocalAdapterRefused`, `load_allowlist_file`. Both classes refuse unless `env in {"local","test"}`.
- `src/sketch2life/infrastructure/documents/factory.py`: `build_document_scanner(settings)` and `build_upload_media_validator(settings)` (selection rule in T-2z-DEC-3).
- `tools/local_s3mock_target.py`: `check_s3mock_target`, `check_s3_credentials`, `ensure_task_bucket`.
- Tests: `tests/synthetic_upload_fixtures.py` (stdlib-only synthetic bytes), `tests/unit/test_local_test_scanner_adapters.py` (55), `tests/unit/test_local_s3mock_target_guard.py` (42), `tests/integration/test_t2z_s3mock_lineage_postgres.py` (6).

Edited: `application/ports/lesson_documents.py` (adds only the helper `scanner_identity_sha256(name, version)`; the `MalwareScanResult` dataclass is NOT changed), `infrastructure/config/settings.py` (`scanner_adapter: Literal["clamav","local_test_allowlist"] = "clamav"`, `local_scanner_allowlist_file: Path | None`; the refusal is the first check of `enforce_deployment_provider_policy`), `interfaces/http/app.py` (import swap, `application.state.upload_media_validator = None` next to the other defaults at the top so it exists in every profile, and the combined block calls the two builders instead of `ClamAvScanner(...)`), `tests/unit/test_settings_security.py` (+8), `tests/contract/test_app_composition.py` (+7). No route, migration, router, repository, contract catalog, `ensure_local_bucket.py`, StoryRun-lite, web or mobile file is touched. No dependency is added (boto3 and Pillow were already declared; fixtures are stdlib).

## 2. Decisions (drafts; the coordinator assigns D-066 numbers; TD-29 is D-066-99)

- T-2z-DEC-1 (storage): no new storage class. The existing `Boto3S3CompatibleObjectStorage` plus a target guard and a bucket helper serve S3Mock (FR-C-12 l.504: chunks by PutObject, no Multipart API).
- T-2z-DEC-2 (fail closed, SRS l.940, l.1934): CLEAN only for an explicit allowlist of synthetic fixture SHA-256 digests (64 lowercase hex, 1 to 256 entries). Any other digest raises `MalwareDetected("LOCAL_TEST_HASH_NOT_ALLOWLISTED")`; an unreadable or non-seekable stream raises `MalwareScannerUnavailable`. Nothing about content, hash or path is logged or put in an exception text. Scan seeks to 0 before hashing and to 0 afterwards (as `ClamAvScanner` does), also when the stream starts at a non-zero position (review P3-1). **For T-2a tests:** an unlisted fixture surfaces as the same `MalwareDetected` as an infected file, so the route answers 422 `MALWARE_DETECTED` (a stand-in code outside 9.8, T2A Q3); it is "unknown", not "infected", and a test must not read it as a virus verdict (P3-6).
- T-2z-DEC-3 (selection rule, review P2-1): the local scanner AND the local validator are built only when `scanner_adapter == "local_test_allowlist"` (one flag, one guard); otherwise `ClamAvScanner(host, port)` exactly as before and `None`. The allowlist file path alone never selects them. A missing or unusable allowlist file stops startup (`LocalAdapterRefused`). `app.state.upload_media_validator` is `None` in every profile unless the combined profile selects the local pair. Builders live in `factory.py` so `local_test_adapters.py` does not import ClamAV.
- T-2z-DEC-4 (production refusal, two layers): `Settings` raises (first policy check, so staging and production fail on this reason before the Firebase reason) when `scanner_adapter != "clamav"` and env is not local/test; `create_app` calls `get_settings()` first, so the process does not start. Both local constructors refuse any env outside `{"local","test"}` as the second layer.
- T-2z-DEC-5 (scanner identity, review P2-2): the scanner identity is `local-test-allowlist`, version `1+allowlist-<first 16 hex of sha256 of the sorted allowlist>` (28 characters; fits the lineage 128 and the T-2a upload table 64). `MalwareScanResult` gains NO `scanner_sha256` field. The Parent formula `sha256(name NUL version)` stays in the repository and is exposed as the helper `scanner_identity_sha256` for lineage tests. **Dual meaning stays open for T-2a (finding F-1):** `core_asset_lineage.scanner_sha256` holds the identity digest in the Parent writer (`attach_artwork`) and the digest of the scanned bytes in the StoryRun-lite writer. T-2z does not settle it; T-2a must pick one meaning before it writes a lineage row.
- T-2z-DEC-6 (validator and T-2a, review P2-4): the validator is an optional port. T-2a may consume `app.state.upload_media_validator`, or, when it is `None`, call the shared `header_matches_media_type` / `is_known_media_type` functions of the port module, so there is ONE signature table and no second copy of the check in T-2a's `complete` (T-2a D6 "signature vs declared type"). **Coordinator ruling (implementation review R1): T-2a consumes the `app.state.upload_media_validator` port**; the shared functions remain the single table behind it. Note for T-2a: DOCX and PPTX share one ZIP-header check in this double, so a T-2a test must not rely on DOCX versus PPTX discrimination. WebP is in the table because SRS l.983 allows JPEG/PNG/WebP (T-2a review F-02). The allowed types per purpose stay with T-2a/T-2c (audio types are not in the SRS; WAV is only a test-double entry).
- T-2z-DEC-7 (target guard, review P2-3, P3-3, P3-5): `check_s3mock_target` reuses `tools.run_be1_lifecycle_consumer.check_storage_target` (exact `FRC08_ALLOWED_ENDPOINT` and `FRC08_ALLOWED_BUCKET`, loopback) and adds: scheme `http`, explicit port, ports 5432/5433/9000 refused, bucket `^[a-z0-9][a-z0-9-]{2,62}$` containing `frc08` and the task tag. No new `S2L_LOCAL_S3_ALLOWED_PORT` variable (superseded by the exact-endpoint match). `check_s3_credentials` requires both keys and refuses any ambient `AWS_*` variable so boto3 never uses its default chain. `ensure_task_bucket` calls only `head_bucket` and, for 404/`NoSuchBucket`/`NotFound`, `create_bucket`; 403 or any other answer raises and creates nothing; `BucketAlreadyOwnedByYou`/`BucketAlreadyExists` after create are accepted; it never lists buckets (P3-4).

## 3. Tests and checks (real results)

Unit and contract (new): 55 + 42 scanner/validator/factory and guard tests, +8 settings, +7 composition (default keeps ClamAV and `None`, local pair composed, allowlist file alone keeps ClamAV, unusable allowlist stops startup, staging/production stop at `create_app`, classroom/demo profiles define `None`). All pass.

Full unit+contract run in a clean env (no DB, S3 or `AWS_*` variables, only `PYTHONPATH`), junit `tmp/phase-v3/t_2z/junit_uc.xml`: 8860 tests, 65 failed, 18 collection errors, 22 skipped. The 83 failing ids equal the 83-id base list exactly: **0 new, 0 fixed** (compared by `tmp/phase-v3/t_2z/compare_ids.py`). A first run was cut off at 99% by an interruption (no junit) and was repeated in full.

PostgreSQL + S3Mock, fresh database `frc08_v3_t2z_20261120113303b_be1_acceptance` (`alembic upgrade heads`, exit 0), endpoint `http://127.0.0.1:59458`, bucket `frc08-v3-t2z-s3mock`: `test_t2z_s3mock_lineage_postgres.py` 6 passed: put/get/`list_keys`/delete round trip and missing key `None` through the real adapter; bucket present after `ensure_task_bucket` (no create); a Parent run, scan of the allowlisted synthetic PNG, `attach_artwork` with the scan's name and version, and the `core_asset_lineage` row has `scanner_name == "local-test-allowlist"`, the scanner's version and `scanner_sha256 == scanner_identity_sha256(name, version)` (64 characters); it differs from a ClamAV-named row; an unlisted file raises `MalwareDetected` and adds no lineage row. The module skips with `NOT_RUN` when the variables are unset and fails with `REFUSED code=...` before any client or engine is built when a target is outside the allow-list (checked with a wrong bucket: `STORAGE_BUCKET_REFUSED`). The test has no teardown (see section 4); S3 keys and endpoint come from `T2Z_S3_*`, the database from `BE1_TEST_DATABASE_URL` checked with `check_database_url` (needs `FRC08_ALLOWED_DATABASE`/`FRC08_ALLOWED_PORT`, name containing `frc08_v3_t2z`).
Regression set for the default adapter, same database: `tests/integration/lesson_library` + `tests/contract/test_parent_ai_late_result_guards.py` 16 passed, 1 failed: `test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http` (503 `PROVIDER_UNAVAILABLE`, the known base failure: it needs a real ClamAV). Together with the 6 new tests: 22 passed, 1 failed. Not run: `test_frc08_lifecycle_postgres.py` (owner-run gate, variables unset) - **NOT RUN**.
No route-level proof with the local adapters (review P3-8): the first real consumer is T-2a. Composition tests prove only the wiring.

Static checks: ruff 0 findings on all touched and new files (HEAD baseline also 0). mypy on the six touched or new source files: 9 errors, all in `app.py` and identical to HEAD (9 before). New tools and test files: 0 (`--explicit-package-bases`); `test_settings_security.py` 8 errors before and after; `test_app_composition.py` 2 before and after (my appended tests add none). Validators from the worktree root (logs `tmp/phase-v3/t_2z/final_*.log`): `validate_harness.py` 0, `validate_repository_security.py` 0, `validate_architecture.py` 0, `git diff --check` 0; `validate_skeleton.py` not run (no structure change). All touched files LF, no NUL, no trailing whitespace.

## 4. Deviations and notes

- File allowlist: `infrastructure/documents/factory.py` added (review P2-1); no other file outside the plan. The plan body is a historical record; this note supersedes it where they differ (the plan header says so).
- Environment variables of the integration test differ from the plan text: it reuses `FRC08_ALLOWED_*` and `BE1_TEST_DATABASE_URL`, plus `T2Z_S3_ENDPOINT`, `T2Z_S3_BUCKET`, `T2Z_S3_ACCESS_KEY`, `T2Z_S3_SECRET_KEY` (test-only dummy values supplied at run time; none is committed).
- S3 deletes (coordinator ruling R1): the fixture teardown loop was removed; the keys stay under a unique per-run prefix. The only delete is the in-body `delete_object` call of the round-trip test, which is the behaviour under test. No bucket or database is ever deleted.
- The S3Mock bucket `frc08-v3-t2z-s3mock` was created by the test helper if absent (first run) and stays.

## 5. Databases and buckets created

- `frc08_v3_t2z_20261120012056_be1_acceptance` (first run, migrated to heads, never dropped).
- `frc08_v3_t2z_20261120113303b_be1_acceptance` (stage-1 final run, fresh, migrated to heads, never dropped).
- `frc08_v3_t2z_20261120114244c_be1_acceptance` (stage-2 re-run, fresh, migrated to heads, never dropped).
- Created by the implementation reviewer: `frc08_v3_t2zrev_20261120113555_be1_acceptance` and bucket `frc08-v3-t2z-rev-20261120`.
- S3Mock buckets `frc08-v3-t2z-s3mock` and `frc08-v3-t2z-stage2` (never deleted; test keys are left under unique prefixes except those the round-trip test deletes in its body).

## 6. Parked and open

- OP-1 (T-2a/T-2c): allowed media types per upload purpose and the audio list (FR-P-03).
- OP-2 / F-1 (open item for T-2a, explicit): the double meaning of `core_asset_lineage.scanner_sha256` (identity digest in the Parent writer, content digest in the StoryRun-lite writer); T-2a decides before it writes a lineage row. T-2z does not settle it.
- OP-3: the StoryRun-lite scanner port (`ImageSafetyScannerPort`) is not covered (demo runtime).
- OP-4: a real ClamAV run stays a later owner-gated check; no claim of a real AV scan is made. `local-test-allowlist` is not a malware scanner.
- Ruling applied: T-2a consumes the validator port (T-2z-DEC-6).

## 7. Implementation review R1 and how the P3 notes were handled

Report: `tmp/phase-v3/reviews/T_2Z_IMPL_REVIEW_R1.md` (Sonnet 5.5, high; read-only). The reviewer ran the integration module on `frc08_v3_t2zrev_20261120113555_be1_acceptance` with bucket `frc08-v3-t2z-rev-20261120` (both stay; nothing else was touched).
- P3-1 stale plan body: the plan file now carries a corrections list (no `scanner_sha256` field, `factory.py`, `FRC08_ALLOWED_*` variables, `parent_ai.py` l.267/273, HEAD pin) before the body, and the status line says it is superseded in part by this note.
- P3-2 evidence record: section 5 lists the reviewer's database and bucket; the stage-2 re-runs are in section 3a.
- P3-3 weak test names: renamed to `test_lineage_scanner_hash_depends_on_the_scanner_name_the_caller_passes` (repository-level, not a ClamAV verdict) and `test_scanner_level_unlisted_file_stops_before_attach_artwork_is_called` (scanner-level); each has a one-line docstring saying what it proves. Route-level proof belongs to T-2a.
- P3-4 DOCX/PPTX share a signature: recorded in T-2z-DEC-6 for T-2a.
- P3-5 unlisted hash reported as `MalwareDetected`: already in T-2z-DEC-2; T-2a test expectations must carry it (422 `MALWARE_DETECTED`, a stand-in outside 9.8).
- P3-6 open rulings: (a) answered, T-2a consumes the port; (b) F-1 stays an explicit open item for T-2a (OP-2); (c) `localhost` is accepted by the inherited loopback check but the exact-endpoint match makes it harmless.

## 3a. Stage-2 re-runs

(Numbers in section 3 are from stage 1; these are after the review changes.)
- Fresh database `frc08_v3_t2z_20261120114244c_be1_acceptance` (`alembic upgrade heads` exit 0), S3Mock bucket `frc08-v3-t2z-stage2`: `test_t2z_s3mock_lineage_postgres.py` 6 passed; with `tests/integration/lesson_library` and `test_parent_ai_late_result_guards.py` 22 passed, 1 failed (the known ClamAV PDF test).
- Full unit+contract clean run (no DB, S3 or `AWS_*` variables), junit `tmp/phase-v3/t_2z/junit_uc.xml`: 8860 tests, 65 failed, 18 collection errors, 22 skipped; failing ids 83 = the 83-id base list: **0 new, 0 fixed**.
- ruff on the touched test file: 0 findings; mypy (`--explicit-package-bases`): no issues. Validators run as separate commands after the last edit (logs `tmp/phase-v3/t_2z/s2_*.log`).
