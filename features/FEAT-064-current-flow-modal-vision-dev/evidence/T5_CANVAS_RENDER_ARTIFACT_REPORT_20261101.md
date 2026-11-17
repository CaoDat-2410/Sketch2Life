# T5 — canvas render, private artifact, and admission report

- **Status:** XONG-CHƯA REVIEW for operation-based PNG rendering, private artifact persistence, real FEAT-018 admission, receipt persistence, and the internal `CanvasRenderHandoffV1`.
- **G4 boundary:** mapping this operation-export handoff into the current BE2 source port remains **BLOCKED**. That port requires a real checkpoint binding, while T4 rejects checkpoint history and supplies accepted operations. No checkpoint identity was fabricated and no BE2 request or Vision claim was made.
- **Approved plan:** `plan/T5_CANVAS_RENDER_ARTIFACT_PLAN_20261101.md`.
- **Approved plan SHA-256:** `6BCC29D243B4D86624D34DA38640E67AA7A988E6ABE290B3C348BA8EF45DB46B`.
- **Upstream T4 plan SHA-256:** `B009F3F6D01DA5E39269E1D03085447042A64DE2F60804880764D0B7B94C41B0`.

## Implementation

- Added `CanvasExportV1` rendering in `infrastructure/canvas_render/renderer.py`: 1024×1024 RGB, white background, decimal `ROUND_HALF_UP` coordinate and width mapping, the existing five-color/three-width profile only, round caps/joins, preserved operation order, retained coincident two-point strokes, and a defensive no-op for a one-point draw. The upstream profile still rejects one-point operations. `CanvasOperationProfileV1` and Teacher checkpoints are unchanged and are not rendering inputs.
- Each operation must retain the server-bound `canvas_operation_profile_id`; the renderer verifies that exact id, removes only this metadata for the existing stroke validator, and leaves the original payload covered by T4's source digest.
- The derivation binding includes the T4 source reference/hash, export-spec version, renderer version, exact Pillow version, dimensions, RGB mode, background, media type, and raw PNG SHA-256.
- The O06 helper in `be1_artifacts.py` stores the PNG under an opaque local artifact ref, reads back and verifies the stored bytes, runs the actual FEAT-018/PyAV admission decoder over those bytes, and stores a canonical typed receipt only after `ADMITTED`. The render and receipt metadata are organization-scoped and retain the source chain. The handoff's receipt hash is the SHA-256 of the exact stored receipt bytes; the receipt separately carries a binding hash over its canonical fields.
- The helper is internal only. No public route, generic artifact upload/download behavior, OpenAPI surface, application/BE2 port, schema, migration, or provider was changed.
- On admission or metadata-commit failure, only artifact refs created by that invocation are deleted and the DB session is rolled back.

## Test-first history and verification

- The resumed initial render unit set had **6 failures** because the new renderer package had not yet been implemented. Final render/export unit set: **13 passed** (9 renderer and 4 T4 export cases).
- An expanded renderer unit test first had one test-authoring error (duplicate `pillow_version` keyword); it was corrected. No product defect was involved in that intermediate failure.
- First T5 PostgreSQL integration attempt: **2 failed** because valid T4 payloads include the server-bound profile id that the renderer initially rejected. The renderer now verifies and handles that binding. The next attempt had one test assertion mismatch about the image's `derived_from_ref`; the assertion was corrected to match the approved source-provenance chain. Final focused T5 cases: **3 passed** (successful handoff, metadata-commit cleanup, and non-admitted-image cleanup).
- Full isolated synthetic-pilot PostgreSQL module: **56 passed in 60.08s**. The fixture used synthetic identifiers and cleaned only its test-owned organization rows. No migration or Alembic command ran.
- CPU/offline regression set: **334 passed, 4 skipped in 30.32s**. The four skips remain the existing DB-environment-dependent cases. This is above the recorded T4 set of 298 passed, 4 skipped.
- Contract suite excluding `tests/contract/test_live_image_demo_api.py`: **1,381 passed in 72.01s**. `test_live_image_demo_api.py` was not run.
- Ruff check: **All checks passed** on the five T5 Python paths. Ruff format: **5 files already formatted**.
- Strict mypy on the new renderer: **Success: no issues found in 1 source file**, using a writable temporary cache. A first run using the default cache ended in a mypy internal error; the cached rerun exposed one `Literal` annotation issue, which was corrected before the successful run.
- Repository validators: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (6,019 publishable files scanned); `ARCHITECTURE_VALID`; `git diff --check` clean. New-file UTF-8/LF/no-BOM/trailing-whitespace scan is recorded in the group ledger after closeout.

## Not run / remaining gates

- BE2 production adapter/port consumption and Vision-claim digest: **BLOCKED for G4** pending a separately approved source contract and an approved allowlisted path.
- Full unit collection, `tests/contract/test_live_image_demo_api.py`, UI/Jest, visual AC20, Alembic/migrations, Modal/GPU/provider, live Vision claim, and real-child data: **NOT RUN**.
- Visual parity with a future Child UI remains unverified. No image was sent to an AI provider.
