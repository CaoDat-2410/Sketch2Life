# V3 T-2a plan, Draft 1: generic upload sessions (DDL-F)

Status: SUPERSEDED IN PART BY THE EVIDENCE NOTE (`evidence/notes/V3_T_2A_EVIDENCE_20261119.md`): plan review R1 passed (READY WITH NOTES, 0 P1 / 3 P2 / 7 P3, DDL-F approvable as designed); the implementation was built at HEAD `9341f175` (T0.1-T0.5, T0.11 and T-2z present) and records its decisions as `T-2a-DEC-n`. Date 2026-11-19. Goal v3, task T-2a (WP-2, P-17, AUD-T#13). Facts below were verified read-only at HEAD `317b4da8`; read the corrections list before the body.

Corrections applied after plan review R1 and the coordinator rulings (these override the body):
- F-01 (asset key): a Parent asset has `asset_ref` = object key = `parent/{run_id}/{token}/original` (token = UUIDv5 of the session id, so a retry overwrites), version 1, `source_refs == [run_id]`, scope `PARENT_ACCOUNT` with the hash ref and a NULL organization. Chunk objects are `parent/{run_id}/upload/{session}/parts/{n}` (swept by the run-prefix sweep). The R3 and D10 text ("completed assets join the purge closure in T-2b") is stale: T-2a assets are already purge-closure seeds, covered by a PostgreSQL test.
- F-02 and Q4 (image types): `RUN_ARTWORK` accepts JPEG, PNG and WebP, at most 20 MiB (SRS l.983, l.1942); "(HEAD limit)" in D2 is wrong (the HEAD drawing route caps lower and is the old route).
- F-03 (complete failures): retryable (session stays OPEN, nothing written) versus terminal (FAILED committed before the error is raised) as written in the evidence note section 2.
- Q1: the lite demo and the generic routes are mutually exclusive; `include_upload_sessions` defaults to True; the CONV-1 family rule is a whole-segment check in `error_envelope.is_conv1_path(..., include_upload_sessions=...)`, off while the demo is on.
- Q2: `RUN_AUDIO` is declared but disabled (create answers 400 `INVALID_REQUEST`, field `purpose`); `AUDIO_TOO_LARGE` is omitted until T-2c (recorded deviation).
- Q3: `MALWARE_DETECTED` (422) is kept as a recorded technical decision; a scanner outage is 503 `PROVIDER_UNAVAILABLE` (retryable), an object-store fault is 503 `STORAGE_UNAVAILABLE`.
- Implementation review R1 (T2A-IR-02): the `asset_ref` a client receives is the opaque handle `upl_{upload_id}`; the physical key above stays in `core_upload_sessions.final_asset_ref` and `core_asset_metadata` (the purge keys on it), and `resolve_asset_key` maps a handle back server side.
- Section 6 allowlist deviations are listed in the evidence note section 4 (the three-place app.py family and catalog hooks, `test_story_demo_collision_guard.py`, `core_lifecycle_store.py` mechanics, the new `uploads` test package).

## 1. Re-verified HEAD facts

- **F1 Lesson routes.** `POST /api/lesson-library/v1/organizations/{org}/lessons/{lesson}/upload-sessions` and `GET`, `DELETE`, `PUT .../parts/{n}`, `POST .../complete` under `/api/lesson-library/v1/upload-sessions/{id}` (`routers/lesson_library.py:284-386`, `lesson_library/service.py:695-1160, 2057-2110`). Create has `file_name, media_type, byte_length<=25,000,000, sha256`: no purpose, no target. Parts use `X-Part-SHA256` + `Content-Range`; a bad part hash is 422 `INVALID_SOURCE_DOCUMENT`. Complete has a key but **no body** and creates the lesson source document.
- **F2 C4 behaviour.** Derived revision (`1+parts` OPEN, `2+parts` otherwise), `DELETE` with strong `If-Match` (202, idempotent), expiry on touch with parts purged, session row locked `FOR UPDATE` on part and complete, codes 409 `UPLOAD_PART_CONFLICT`/`UPLOAD_SESSION_STATE_CONFLICT`, 410 `UPLOAD_SESSION_EXPIRED`, 422 `UPLOAD_INCOMPLETE`.
- **F3 Tables** (`20261028_ll_0001`, `lesson_library/tables.py:58-110`). `core_upload_sessions`: `organization_id` **NOT NULL**, `owner_principal_ref`, `purpose` (CHECK already `PROFILE_IMAGE, RUN_ARTWORK, RUN_AUDIO, LESSON_SOURCE`), `target_ref`, `safe_file_name`, expected media/size (1..25,000,000)/sha256, chunk fixed 4194304, `expected_parts 1..7`, `state` (OPEN, COMPLETED, ABORTED, EXPIRED, FAILED), `expires_at`, `final_asset_ref`. `core_upload_parts`: PK `(session, part_number)`, `byte_size`, `sha256`, `storage_object_ref`. The lesson service filters `purpose = 'LESSON_SOURCE'`.
- **F4 A second stack owns the literal path.** StoryRun-lite (`storyrun_upload_sessions/parts`, renamed from `core_upload_*` by `20261103_story_upload_compat`) serves **`/v1/upload-sessions`** (`routers/story_run_lite.py:211-310`), mounted only when `STORYRUN_LITE_MAIN_DEMO_ENABLED=1`; the M2 Parent routes mount when it is `0` (`app.py:1058-1060`, `router_composition.py:60-77`).
- **F5 Parent side.** Drawing today is base64 in `POST /api/parent/v1/ai/drawing-understandings` (`parent_ai.py:255-300`). `ensure_accepting_artwork` allows only `INPUT_PROCESSING` (`parent_story_repository.py:674`); Parent scope ref is sha256 of canonical `{issuer, subject}` (`:2001`).
- **F6 Typed owner scope exists** on `core_asset_metadata` and `core_audit_entries` (FR-C-08, `OWNER_SCOPE_CHECK`, nullable `organization_id`). `be1_command_receipts` (`20261119_ar_0002`) has a nullable organization (generic module receipt); the lesson `command_receipts` needs one.
- **F7 FR-C-08** run delete closes only `storyrun_upload_sessions` (`core_lifecycle_store.py:431-470`).
- **F8 Alembic.** 14 heads; lesson_library head `20261119_ar_0002` (`-> ar_0001 -> ll_0001`). Pinned by `tests/unit/test_synthetic_eligibility.py:454-470` (33 revisions, heads 14/10) and `tests/integration/test_m2_s2_g1_parent_story_postgres.py:96` (version rows).
- **F9 Envelope.** `CONV1_PREFIXES` has no `/v1/...`; every new code needs a `MESSAGES` entry or `STATUS_MESSAGE_ONLY` (`tests/unit/test_http_error_envelope.py`).
- **F10 T-2z is not at HEAD.** Only `ClamAvScanner`, `DeterministicLessonDocumentParser` and the S3 adapter exist (wired `app.py:1054-1096`, `app.state.lesson_library_storage/lesson_document_scanner`). T-2a starts after T-2z delivers the local S3Mock target and the allowlist scanner (TD-29) on the same ports.

## 2. Decisions (SRS-cited)

- **D1 Path and mount (TD-01, C-D9; l.1654-1658).** Literal paths under `/v1/upload-sessions`, new router `routers/upload_sessions.py`, combined profile only. Because of F4 it mounts **only when the lite demo is off** (`include_upload_sessions=not story_demo_enabled`, the `include_parent_story_runs` pattern); they never share a process. `/v1/upload-sessions` joins `CONV1_PREFIXES` (R10); a test pins that demo-mode responses are unchanged.
- **D2 Purposes and targets (l.1654, 1664, 1653).** `purpose` in `RUN_ARTWORK | RUN_AUDIO | OCCURRENCE_DOCUMENT`, `target_ref` = run or occurrence id. Lesson sources stay on the lesson routes (P-17): generic create refuses `LESSON_SOURCE`/`PROFILE_IMAGE` (400 `INVALID_REQUEST`), and generic GET/PUT/complete/DELETE answer 404 for a lesson session.
  - `RUN_ARTWORK`: Parent; JPEG, PNG or WebP, at most 20 MiB (SRS l.983; corrected, see the list at the top); run owned by caller and `INPUT_PROCESSING`.
  - `OCCURRENCE_DOCUMENT`: assigned Teacher; PDF, DOCX, PPTX, at most 25,000,000 bytes (FR-T-06 l.545). Target is validated by a resolver port that **T-3a/T-3b register** (no occurrence table at HEAD); T-2a tests use a fake resolver, with none registered create answers 404.
  - `RUN_AUDIO`: 20 MB cap is FR-P-03, but the SRS lists **no audio types** and the 2-minute rule needs a decoder, so generic create answers 400 (`purpose`) until **T-2c** enables it (Q2; not a park of T-2a).
- **D3 Actor and scope (l.1637, C-D4, CV-5).** Actor from the verified token; body is `extra=forbid` (a role, owner or organization field is 400 `UNKNOWN_FIELD`). Parent: active `parent` identity, scope `PARENT_ACCOUNT` (F5 ref). Teacher: active, **current** assignment; organization from the resolved target. Wrong role for the purpose, inactive account, unknown or out-of-scope target, another actor's session: uniform **404 `RESOURCE_NOT_FOUND`**. Scope is re-resolved on every call (revoked assignment stops parts and complete; a purged run gives 409 `INVALID_STATE_TRANSITION`).
- **D4 Keys and receipts (C-D5, C-D6, l.1697).** `parse_idempotency_key(request)`: one header, 1-128 visible ASCII; missing is 400 `INVALID_REQUEST` (REQUIRED); same key with another payload 400 `INVALID_IDEMPOTENCY_KEY`. Create, complete, DELETE are keyed; receipts in `be1_command_receipts` (no new table, Parent callers need no organization); stored responses hold no storage reference.
- **D5 Parts.** Raw `application/octet-stream`, header `X-Part-SHA256` (same as lesson, one client), part 1..`expected_parts`, bounded stream (over 4 MiB is 413 with the purpose's too-large code). Offsets follow from part number and the fixed 4 MiB chunk. Same part and hash: 200 receipt, no storage write; other hash: 409 `UPLOAD_PART_CONFLICT`; body not matching header: 422 `UPLOAD_CHECKSUM_MISMATCH`. `FOR UPDATE` on the session plus the PK serialize concurrent retries.
- **D6 Complete (l.1657, l.504).** Body `{expected_size_bytes, expected_sha256}` must equal the create-time values (else 422 `UPLOAD_CHECKSUM_MISMATCH`); purpose and target cannot be sent. Order: parts present (422 `UPLOAD_INCOMPLETE`), part and aggregate size/hash recomputed from storage (422 `UPLOAD_CHECKSUM_MISMATCH`), declared type allowed (415), **signature vs declared type** (PNG/JPEG magic, `%PDF`, ZIP `PK` for DOCX/PPTX; 422 `UPLOAD_CONTENT_MISMATCH`), AV scan via `MalwareScanner` (infected 422 `MALWARE_DETECTED`, kept from the lesson and `parent_ai` flows, not in 9.8; scanner or storage down 503 `STORAGE_UNAVAILABLE`). Only then one PutObject of the final object, a `core_asset_metadata` row (owner scope per D3, `source_refs=[target_ref]`) and an audit row, and the session becomes `COMPLETED` with `final_asset_ref`. **An asset is usable exactly when that row exists and the session is COMPLETED**; a failed check leaves no asset row, sets `FAILED` with `error_code`, purges parts. Response **202** `UploadCompletionV1` (state, `asset_ref`, `asset_state`, scanner name/version) with `ETag`; same-key repeat returns the stored response. Validation is synchronous (bounded 25 MB); deep document parsing (encryption, pages, OCR) stays with T-3b, image dimensions and multi-child with T-2b.
- **D7 DELETE (l.1658).** Strong `If-Match` (derived revision), keyed, idempotent, 202; OPEN to ABORTED then parts purged after commit; COMPLETED/FAILED: 409 `UPLOAD_SESSION_STATE_CONFLICT`; EXPIRED 410; stale 409 `STALE_REVISION` with current ETag.
- **D8 Codes (9.8 l.862-873).** 400 `INVALID_REQUEST`/`INVALID_IDEMPOTENCY_KEY`; 404; 409 `UPLOAD_PART_CONFLICT`, `UPLOAD_SESSION_STATE_CONFLICT`, `STALE_REVISION`, `INVALID_STATE_TRANSITION`; 410 `UPLOAD_SESSION_EXPIRED`; 413 `MEDIA_TOO_LARGE` (image), `LESSON_FILE_TOO_LARGE` (document); 415 `UNSUPPORTED_MEDIA_TYPE` (image), `UNSUPPORTED_LESSON_TYPE` (document); 422 `UPLOAD_INCOMPLETE`, `UPLOAD_CHECKSUM_MISMATCH`, `UPLOAD_CONTENT_MISMATCH`; 503 `STORAGE_UNAVAILABLE`. Messages added to `error_envelope.MESSAGES`; `AUDIO_TOO_LARGE` comes with T-2c.
- **D9 No storage leak (l.1692).** Bodies carry only `upload_id, purpose, target_ref, state, part_size_bytes, expected_parts, accepted_parts[{part_no, byte_length, sha256}], byte_count, expires_at, revision` and, after complete, `asset_ref, asset_state`. No bucket, key, URL or credential in any body or header; a contract test scans responses and the OpenAPI schema.
- **D10 FR-C-08.** `SqlCoreRunUploadClose` also plans and closes OPEN generic sessions (`PARENT_ACCOUNT`, `target_ref=run`) to ABORTED with `error_code=RUN_DELETED` and purges parts. Completed-but-unattached assets (`source_refs=[run]`) are already purge-closure seeds (corrected, see the list at the top).

## 3. Routes

| Route | Actor | Success | Extra errors |
|---|---|---|---|
| `POST /v1/upload-sessions` (l.1654) | Parent or assigned Teacher; key | 201 session, `ETag`, chunk 4 MiB, TTL 24 h, replay = first response | 413/415 by purpose; 400 purpose not enabled |
| `GET /v1/upload-sessions/{upload_id}` (l.1655) | owner, same scope | 200 state, receipts, `byte_count`, expiry | 404, 410 |
| `PUT .../parts/{part_no}` (l.1656) | owner | 200 receipt and progress | 409 x2, 410, 413, 422, 503 |
| `POST .../complete` (l.1657) | owner; key; body | 202 `UploadCompletionV1` | 415, 422 x3, `MALWARE_DETECTED`, 410, 503 |
| `DELETE .../{upload_id}` (l.1658) | owner; key; `If-Match` | 202 state | 409 x2, 410 |

No attach route here; T-3b and T-2b consume `asset_ref` and re-verify the hash.

## 4. DDL-F (to be approved by name after plan review passes, OD-01)

One migration `20261119_uf_0001_upload_scope.py`: `revision "20261119_uf_0001"`, `down_revision "20261119_ar_0002"` (extends the lesson_library branch, no `branch_labels`, `depends_on None`; heads stay 14/10, graph 34 revisions). Alters only; no table created or dropped. Contents to approve:

1. `core_upload_sessions.organization_id`: drop NOT NULL.
2. Add `owner_scope_kind VARCHAR(32) NOT NULL DEFAULT 'ORGANIZATION'`, `owner_scope_ref VARCHAR(128) NULL`, and CHECK `ck_core_upload_owner_scope` with the FR-C-08 `OWNER_SCOPE_CHECK` text; existing lesson rows satisfy it.
3. Replace `ck_core_upload_purpose` with `purpose IN ('PROFILE_IMAGE','RUN_ARTWORK','RUN_AUDIO','LESSON_SOURCE','OCCURRENCE_DOCUMENT')`.
4. Add nullable `error_code VARCHAR(64)`, `scan_verdict VARCHAR(16)`, `scanner_name VARCHAR(64)`, `scanner_version VARCHAR(64)`, `validated_at timestamptz`.
5. Add indexes `ix_core_upload_scope_state (owner_scope_kind, owner_scope_ref, state, expires_at)` and `ix_core_upload_target_state (target_ref, state)`.
6. **Unchanged:** size, chunk, parts-count and state CHECKs, and all of `core_upload_parts` (per-part SHA-256 and PK already fit; the register's mention of parts needs no change, reviewer to confirm).

No backfill. **Downgrade** raises while any row has `owner_scope_kind <> 'ORGANIZATION'` or `purpose = 'OCCURRENCE_DOCUMENT'` (FR-C-08 style guard), else drops indexes, columns and the new CHECK, restores the old purpose CHECK and NOT NULL. Verified with `alembic upgrade heads` on a fresh database and an upgrade, downgrade, upgrade round trip. `UPLOAD_SESSIONS` in `lesson_library/tables.py` changes in the same commit.

## 5. Tests

- **Unit:** purpose limits, scope derivation, fingerprints, revision math, signature checks, code mapping, migration text and downgrade guard.
- **Contract:** five operations in `MOUNTED_OPERATIONS`, `SRS_V22_INCLUDED_OPERATIONS`, idempotency-mismatch keys (create, complete, DELETE), no storage words, mount exclusivity, demo responses unchanged.
- **PostgreSQL (fresh `frc08_v3_t2a_*` db):** resume after partial upload; concurrent same-part retry (one object, equal receipts) and different hash (one 409); cross-actor and cross-scope GET/PUT/complete/DELETE all 404; expired 410 on every route, parts purged; part after abort 409; wrong part hash, wrong complete size/hash, content mismatch, infected fixture, incomplete: 422; complete replay; Teacher assignment revoked mid-session 404; run in `DELETE_PENDING` blocks parts and DELETE_RUN aborts open sessions; lesson suites still pass; migration round trip and guard.
- **Update:** `test_synthetic_eligibility.py` (34 revisions), `test_m2_s2_g1_parent_story_postgres.py` (version rows), `test_openapi_contract_catalog.py`, `test_http_error_envelope.py`, `test_story_run_lite_main_composition.py`, `test_app_composition.py`. Base failures compared by id (83-id list); ruff and mypy on touched files; four validators and `git diff --check`. Test buckets contain `t2a`.

## 6. File allowlist

New: `alembic/versions/20261119_uf_0001_upload_scope.py`; `src/sketch2life/infrastructure/uploads/{__init__,service,purposes,resolvers}.py`; `application/ports/upload_sessions.py`; `contracts/schemas/upload_sessions.py`; `interfaces/http/routers/upload_sessions.py`; `tests/unit/test_upload_sessions_*.py`; `tests/contract/test_upload_sessions_routes.py`; `tests/integration/uploads/test_upload_sessions_postgres.py`; evidence note `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/V3_T_2A_EVIDENCE_20261119.md`.
Modified: `lesson_library/tables.py`, `router_composition.py`, `app.py` (mount flag only), `error_envelope.py`, `openapi_contract.py`, `openapi_srs_v22.py`, `persistence/core_lifecycle_store.py`, and the six tests above. The lesson service is not refactored; T-2z files are not touched; anything else is a recorded deviation.

## 7. FE impact, rollback, risks

- **FE (not in v3):** Android drawing/audio and Web Teacher occurrence documents move to this client (create, PUT parts with `X-Part-SHA256`, complete with size and hash, DELETE with `If-Match`); the Web library keeps lesson routes; new codes need localized strings.
- **Rollback:** revert the single commit; downgrade only when no generic or occurrence rows exist (the guard refuses otherwise); lesson routes and tables stay valid (additive columns with defaults).
- **Risks:** R1 path collision with the lite demo (exclusive mount, test); R2 `CONV1_PREFIXES` change could alter demo error bodies (regression test); R3 unattached completed assets after run delete (resolved: asset key under `parent/{run}/`, tested); R4 migration must also be tested on a database that went through `20261103_story_upload_compat`; R5 `MALWARE_DETECTED` not in 9.8; R6 head-count tests pin the graph; R7 allowlist scanner is clean only for fixture hashes.

## 8. Park conditions and open questions

- **BLOCKED_OPEN if:** DDL-F is not approved by name after review passes (OD-01); or T-2z has not delivered the adapters (TD-29).
- **Q1 (default chosen):** keep the lite demo and generic routes mutually exclusive (D1). If the owner wants both in one process, the lite stack must leave `/v1/upload-sessions`, a separate decision.
- **Q2 (for T-2c, no park):** which audio media types does FR-P-03 allow, and where is the 2-minute check made?
- **Q3:** keep `MALWARE_DETECTED` (422) for infected files, or map to `UPLOAD_CONTENT_MISMATCH`? Default keep.
- **Q4:** closed by SRS l.983: `RUN_ARTWORK` accepts JPEG, PNG and WebP (the HEAD drawing route is the old, narrower rule).
