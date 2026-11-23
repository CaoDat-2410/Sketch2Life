# V3 T-2z plan, Draft 1: local S3Mock storage and scanner / media-validator adapters (TD-29)

Date 2026-11-19. Goal v3a, before T-2a. Branch `feature/backend-srs-api-v3`, plan facts verified at HEAD 317b4da8 (the implementation was built on `f7ab272c`, which adds T0.1-T0.5 and T0.11; line numbers in section 1 are of the older tree). Status: SUPERSEDED IN PART BY THE EVIDENCE NOTE - read the list of corrections below before the body. Plan review R1 READY WITH NOTES (0 P1 / 4 P2 / 8 P3), all notes applied in the implementation; implemented and committed with the evidence note. Where this plan body differs from the code (no `MalwareScanResult.scanner_sha256`; builders in `infrastructure/documents/factory.py`; guard reuses the `FRC08_ALLOWED_*` variables; shared signature table in the port module), `evidence/notes/V3_T_2Z_EVIDENCE_20261119.md` supersedes it.
Source: BE API plan Draft 5 §2.2 T-2z, TD-29 (§5B), WP-2; the T0.8 pack's draft D-066-99 (TD-29); SEED Draft 11 §7 O-SEED-STORAGE and O-SEED-SCAN and rules 9 and 10.
SRS: FR-C-12 l.504, l.1657 (asset usable only after hash, media validation and AV scan), l.940 and l.1934 (a scanner must return `CLEAN` first; timeout, error or unknown fails closed; scan never writes file content to a log). The SRS names neither S3Mock nor an allowlist scanner; both are test-double choices (D-066-99 flag).

Corrections applied after plan review R1 and implementation review R1 (these override the body):
- No `MalwareScanResult.scanner_sha256` field is added (sections 2(b), 3 and the integration assertion): `MalwareScanResult` is unchanged; only the helper `scanner_identity_sha256(name, version)` is added, and the integration test asserts `row.scanner_sha256 == scanner_identity_sha256(name, version)`. Finding F-1 (dual meaning of the column) stays open for T-2a.
- `build_document_scanner` and `build_upload_media_validator` live in the new file `infrastructure/documents/factory.py` (add it to the section 4 allowlist); one flag, `scanner_adapter == "local_test_allowlist"`, selects both local adapters, otherwise ClamAV and `None`. `app.state.upload_media_validator` is `None` in every other profile.
- The target guard reuses `FRC08_ALLOWED_ENDPOINT` and `FRC08_ALLOWED_BUCKET` (no `S2L_LOCAL_S3_ALLOWED_PORT`); the integration test variables are `BE1_TEST_DATABASE_URL`, `T2Z_S3_*` and `FRC08_ALLOWED_*`. The Parent route reads the scanner at `parent_ai.py` l.267 and calls `scan` at l.273 (not l.285).
- Coordinator ruling (implementation review R1): T-2a consumes the `upload_media_validator` port. The test teardown deletion loop was removed; the only S3 delete is the in-body one under test.

## 1. Facts at HEAD

- **S3 adapter exists.** `infrastructure/storage/s3_compatible.py` has `Boto3S3CompatibleObjectStorage` (path-style addressing and s3v4 when an endpoint is set; put, get, delete, `list_keys`). Settings already carry `s3_endpoint`, `s3_region`, `s3_bucket`, `s3_access_key`, `s3_secret_key` (`SKETCH2LIFE_*`). `interfaces/http/app.py` l.1085-1094 builds `application.state.lesson_library_storage` from them in the combined profile. The FR-C-08 owner-run test already drives it against S3Mock. So (a) needs configuration and a target guard, not a new storage class. Imports verified in `backend/.venv`: boto3 1.43.80, botocore 1.43.80, Pillow 12.3.0. No dependency is added. Read-only check: 127.0.0.1:59458 accepted a TCP connection (no S3 call made).
- `infrastructure/storage/ensure_local_bucket.py` accepts only `http://minio:9000` and is left alone.
- **Scanner port** `application/ports/lesson_documents.py`: `MalwareScanner.scan(file_obj) -> MalwareScanResult(scanner_name, scanner_version, verdict)`; failure is `MalwareDetected` or `MalwareScannerUnavailable`. Only `ClamAvScanner` (`infrastructure/documents/clamav_scanner.py`) implements it. The result has **no `scanner_sha256`**.
- **One scanner object serves three callers:** `app.state.lesson_document_scanner` is used by the Lesson Library (`infrastructure/lesson_library/service.py`), the Parent drawing route (`routers/parent_ai.py` l.285) and, later, T-2a and T-3b. Swapping that object is the single wiring point (`app.py` l.1095).
- **Lineage.** `core_asset_lineage` needs `scanner_name` (64), `scanner_version` (128) and `scanner_sha256` (exactly 64). `parent_story_repository.attach_artwork` (l.816) stores `scanner_sha256 = sha256(name + NUL + version)`. **Finding F-1:** StoryRun-lite (`story_run_lite/repository.py` l.1135-1137) writes `scanner_name="ClamAV"` and `scanner_sha256` = digest of the scanned bytes, a different meaning in the same column. T-2a must settle one meaning; T-2z follows the Parent repository formula (the M2 Parent path) and does not touch either repository.
- **No upload media validator port exists** for upload finalize (`MediaValidator` in `ports/knowledge_video_media.py` is for video decode; `file_inspector.py` returns quality signals). The Parent route sniffs PNG and JPEG magic inline.
- Test helpers: lesson-library tests inject an in-memory storage and a real `ClamAvScanner`; `tools/run_be1_lifecycle_consumer.py::check_storage_target` is the existing loopback-plus-allow-list pattern (bucket must contain `frc08`).

## 2. Design

### (a) S3Mock target, configuration only
Env for a local run (names only; the coordinator supplies values, no credentials in Git): `SKETCH2LIFE_ENV=test` or `local`, `SKETCH2LIFE_S3_ENDPOINT` (the loopback S3Mock URL), `SKETCH2LIFE_S3_BUCKET` (task-tagged), `SKETCH2LIFE_S3_REGION`, and the two existing S3 key variables with dummy values (S3Mock does not verify them; boto3 needs some).

New `backend/tools/local_s3mock_target.py` (pure functions, no network at import):
- `check_s3mock_target(endpoint, bucket, *, task_tag, environ)` raises `TargetRefused`-style errors unless: scheme `http`, no path, query or credentials; host is loopback (127.0.0.1, ::1, localhost); explicit port equal to env `S2L_LOCAL_S3_ALLOWED_PORT` (no default, so nothing runs unconfigured) and not 5432, 5433 or 9000; bucket matches `^[a-z0-9][a-z0-9-]{2,62}$` and contains both `frc08` and the task tag (`t2z`, later `t3b`, `seed`).
- `ensure_task_bucket(client, bucket)`: `head_bucket` on the named bucket only, `create_bucket` on 404. It never lists buckets, so no other bucket is touched.
Tests delete only keys they created and never delete the bucket.

### (b) Local scanner and media validator
New `backend/src/sketch2life/infrastructure/documents/local_test_adapters.py`:
- `LocalTestAllowlistScanner(env, allowed_sha256)` implements `MalwareScanner`. It streams the file in 64 KiB chunks into SHA-256 and restores the stream position (as ClamAV does). Hash in the allowlist: `MalwareScanResult(scanner_name="local-test-allowlist", scanner_version="1+allowlist-<first 16 hex of the sha256 of the sorted allowlist>", verdict="CLEAN", scanner_sha256=<identity digest>)`. Any other hash: `MalwareDetected("LOCAL_TEST_HASH_NOT_ALLOWLISTED")` (fail closed, l.940; the 422 `MALWARE_DETECTED` is a conservative stand-in, noted in the evidence). Unreadable or non-seekable stream: `MalwareScannerUnavailable`. It logs nothing about content.
- `LocalTestSignatureMediaValidator(env)` implements new port `UploadMediaValidator` (below). It reads at most 16 header bytes, checks the declared type against its signature (PNG, JPEG, PDF, RIFF/WAVE, ZIP for DOCX and PPTX) and decodes nothing. Unknown declared type: `UploadMediaRejected("UNSUPPORTED_MEDIA_TYPE")`; mismatch: `UploadMediaRejected("UPLOAD_CONTENT_MISMATCH")`. T-2a owns which types each purpose allows (OD-open, see §6). It returns validator name `local-test-signature` and a version.
- Both constructors raise `LocalAdapterRefused` unless `env in {"local", "test"}`.
- `build_document_scanner(settings) -> MalwareScanner` and `build_upload_media_validator(settings) -> UploadMediaValidator | None`: default is `ClamAvScanner(host, port)` exactly as today (no behaviour change) and `None`.
- Allowlist source: an explicit set (tests) or `local_scanner_allowlist_file`, a JSON object `{"sha256": [...]}` (at most 256 entries, each 64 lowercase hex). An empty or malformed allowlist refuses construction. No allowlist file is committed; the seed (S7, S8) owns its fixture hashes.

Port changes: `application/ports/lesson_documents.py` gains optional `MalwareScanResult.scanner_sha256: str | None = None` (ClamAV and all existing constructors unaffected) and `scanner_identity_sha256(name, version)` (the Parent formula). New `application/ports/upload_validation.py` holds `UploadMediaValidator`, `MediaValidationResult(detected_media_type, validator_name, validator_version)` and `UploadMediaRejected(code)`.

### (c) Wiring and startup guard
Settings (`infrastructure/config/settings.py`): `scanner_adapter: Literal["clamav", "local_test_allowlist"] = "clamav"` and `local_scanner_allowlist_file: Path | None = None`. `enforce_deployment_provider_policy` raises first when `scanner_adapter != "clamav"` and `env` is not `local` or `test`, so staging and production fail at `get_settings()`, which `create_app` calls: the process does not start. The constructor check is the second layer. `app.py` l.1095 becomes `build_document_scanner(storage_example_settings)`; new `application.state.upload_media_validator` is set from `build_upload_media_validator(...)` (default `None`). No route is added or changed, so the contract catalog is untouched.

### Decisions (drafts; the coordinator assigns D-066 numbers; TD-29 is D-066-99)
T2Z-a no new storage class, guard plus bucket helper only. T2Z-b unknown hash fails closed. T2Z-c the lineage scanner identity is `local-test-allowlist`, distinct from `clamav-clamd-instream`. T2Z-d refusal outside local and test at settings and constructor. T2Z-e `scanner_sha256` follows the Parent formula; F-1 goes to T-2a.

## 3. Tests (no real file is scanned)

Fixtures: `backend/tests/synthetic_upload_fixtures.py` builds tiny deterministic synthetic bytes in memory (stdlib only: PNG via zlib, a minimal PDF, a tiny WAV) and their SHA-256.
Unit (`tests/unit/test_local_test_scanner_adapters.py`): allowlisted hash is CLEAN with name, version and identity digest as above, and the digest has length 64; unlisted hash raises `MalwareDetected`; stream position restored; large stream chunked; empty or malformed allowlist refused; env `staging`, `production` and `""` refused for both classes; name at most 64 and version at most 128 characters; validator accepts matching and rejects mismatched or unknown types; no content or path in exception text.
Unit (`tests/unit/test_local_s3mock_target_guard.py`): refuses non-loopback host, https, a path, credentials in the URL, wrong or missing allowed port, ports 5432, 5433 and 9000, a bucket without `frc08` or the tag, an invalid bucket name; accepts the good target; `ensure_task_bucket` with a fake client calls only `head_bucket` and `create_bucket` (never `list_buckets`).
Unit (`tests/unit/test_settings_security.py`, extended): `Settings(env="staging", ...)` and a production setting with the local adapter raise `ValidationError`; local and test accept; default stays `clamav`.
Contract (`tests/contract/test_app_composition.py`, extended): with env test and the local adapter, `app.state.lesson_document_scanner` is the local scanner and `upload_media_validator` is set; the default keeps `ClamAvScanner` and `None`.
Integration, gated on env (NOT_RUN when unset), `tests/integration/test_t2z_s3mock_lineage_postgres.py`: on S3Mock with the task bucket, put, get, `list_keys` and delete of synthetic keys through the real adapter, and get of a missing key returns `None`; on a fresh PostgreSQL database, create a Parent run (pattern of `test_frc08_lifecycle_postgres._create`), scan an allowlisted fixture, call `attach_artwork` with the scan's name and version, and assert the `core_asset_lineage` row has `scanner_name == "local-test-allowlist"`, the expected version, and `scanner_sha256 == result.scanner_sha256`, and that it differs from a ClamAV-named row.
Then the standard run: unit and contract against the 83-id base (only new failures block), ruff and mypy on touched files (baseline counts first), the validators, `git diff --check`.

## 4. File allowlist

New: `backend/src/sketch2life/application/ports/upload_validation.py`; `backend/src/sketch2life/infrastructure/documents/local_test_adapters.py`; `backend/tools/local_s3mock_target.py`; `backend/tests/synthetic_upload_fixtures.py`; `backend/tests/unit/test_local_test_scanner_adapters.py`; `backend/tests/unit/test_local_s3mock_target_guard.py`; `backend/tests/integration/test_t2z_s3mock_lineage_postgres.py`; evidence note `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/V3_T_2Z_EVIDENCE_20261119.md`.
Edited: `application/ports/lesson_documents.py`; `infrastructure/config/settings.py`; `interfaces/http/app.py` (one import and one call site, a hot file, kept minimal); `tests/unit/test_settings_security.py`; `tests/contract/test_app_composition.py`.
Not touched: any repository, migration, router, the contract catalog, `ensure_local_bucket.py`, StoryRun-lite, web, mobile, DECISIONS or approval files.

## 5. Rollback

One local commit; revert it. The default adapter is `clamav`, so reverting changes no running behaviour. No DDL. The S3Mock bucket stays (never deleted); its keys are test-owned.

## 6. Open points and blockers

No blocker. S3Mock answers on the expected port; the coordinator supplies the endpoint, allowed port, task bucket name and dummy S3 key values through the environment at run time.
- OP-1: allowed media types per upload purpose, and the audio formats (FR-P-03), are not in this task. The validator uses a small signature table; T-2a sets the matrix and may extend it.
- OP-2: F-1, the double meaning of `scanner_sha256`; T-2a decides.
- OP-3: the StoryRun-lite scanner port (`ImageSafetyScannerPort`) is not covered; it is a demo runtime and not on the v3a path.
- OP-4: a real ClamAV run stays a later owner-gated check; no claim of a real AV scan is made.
