# T4 — authoritative canvas source export report

- **Status:** XONG-CHƯA REVIEW.
- **Approved plan:** `plan/T4_AUTHORITATIVE_CANVAS_EXPORT_PLAN_20261101.md`.
- **Approved plan SHA-256:** `B009F3F6D01DA5E39269E1D03085447042A64DE2F60804880764D0B7B94C41B0`.
- **Scope:** internal typed export from accepted BE1 operations. No public route, renderer, private artifact, admission receipt, claim, migration, or provider call was added.

## Implementation

- `CanvasSourceExportV1` and its operation/manifest entries reject extra fields, non-lowercase SHA-256, payload-digest mismatch, incomplete revision sequences, duplicate operation identifiers, epoch mismatch, manifest mismatch, and inconsistent document/source bindings.
- `build_canvas_source_export` reads the aggregate revision, server session profile, operation rows, and checkpoint-existence fact with one SQL statement. It rejects missing/empty history, gaps or extra revisions, wrong organization/session/canvas/epoch, an unprofiled or changed profile, invalid stored stroke payloads, and any checkpoint/restore history with the same generic `409 CANVAS_SOURCE_UNAVAILABLE` and no partial export.
- Every stored operation must carry the server-attached `canvas-operation-profile-v1` identifier. The server removes that identifier only for profile-payload validation; the accepted stored payload remains intact in the export and its digest.
- The source digest binds organization, session, canvas, profile ID/version, epoch, revision, canonical operation document, and complete operation-manifest digest. It does not claim to be a rendered-image digest.

## Test-first and verification

- The initial red count from the interrupted T4 session is **không còn số đỏ** đủ tin cậy để tổng hợp; no initial count is claimed.
- T4 unit tests: **4 passed**.
- T4 PostgreSQL cases: **5 passed**; the full isolated synthetic-pilot PostgreSQL module, including prior G1 cases, finished **53 passed in 58.88s**.
- Recorded CPU/offline regression set plus T4 unit tests: **298 passed, 4 skipped**.
- Contract suite excluding `tests/contract/test_live_image_demo_api.py`: **1,381 passed**.
- Owner-requested `tests/unit/test_feat018_p2_t5_evaluation.py`: **25 passed** after the owner removed the old scratch directory.
- Ruff check: **All checks passed** on the four T4 Python files. Ruff format check: **4 files already formatted**.
- Strict mypy on the two source files reports three existing `be1_canvas.py` diagnostics. The G1R snapshot shadow run reports the same three diagnostics and no schema-file diagnostics: **0 new T4 diagnostics**. Mypy 1.20.2 initially could not open its default cache database; rerunning with a writable temporary cache completed the baseline comparison.
- `validate_harness.py`: `HARNESS_VALID`.
- `validate_repository_security.py`: `REPOSITORY_SECURITY_VALID` (`6014` publishable files scanned; no absolute machine paths).
- `validate_architecture.py`: `ARCHITECTURE_VALID`.
- `git diff --check`: clean. The new T4 unit test separately passed UTF-8/LF/no-BOM checks.
- `tests/contract/test_live_image_demo_api.py`: **NOT RUN**. No migration/Alembic, Modal/GPU/provider, UI, or real-child data was used.

## Owner decisions routed to T5 and G4

- T4 intentionally exports operation history only. T5 must pin a separate versioned image-export contract (for example, `CanvasExportV1`): 1024×1024 RGB, white `#FFFFFF` background, stroke pixel width `profile_width_ratio × 1024` rounded to the nearest integer using decimal `ROUND_HALF_UP` (13/23/36 px for the current 5/9/14 width tokens), rounded stroke caps, no dot for a one-point stroke, and acceptance of two coincident points. The image source hash must bind `export_spec_version` and `renderer_version`; this does not change `CanvasOperationProfileV1`.
- Rendering must use the exported accepted-operation list, never a Teacher-provided checkpoint snapshot. The existing profile requires at least two points; the no-dot one-point rule remains a defensive renderer rule and does not make a one-point operation acceptable to BE1.
- Passing this digest through a Vision claim is deferred to G4 and requires its own task approval. If the G4 allowlist has no path for the claim, that work must be marked BLOCKED with an owner question.

## Source hashes

| File | SHA-256 |
|---|---|
| `backend/src/sketch2life/contracts/schemas/be1_runtime.py` | `59A2CA1A356916816A788C77E4B03D4FA1A716ECF5CC245B515A39E146B14F11` |
| `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` | `62333F14C046F90AA9B37634064EFAA6EF9A462A18A76E1ED672DCCFF81BBE0B` |
| `backend/tests/unit/test_canvas_source_export.py` | `045228A939F13287298EFD8A51E96AAF399A50AB601D80E219BD013254784F82` |
| `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | `9D01C0F8F2564CB9DCA0B3F3D861050EBEAC44F648E3B4163B93BE712849833A` |

Independent review remains required. This report does not claim provider quality, production readiness, or live completion.
