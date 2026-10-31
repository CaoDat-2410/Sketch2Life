# T5 — canvas render, private artifact, and admission plan

- **Status:** prepared for bounded G2 execution; task approval is appended separately.
- **Feature:** FEAT-064 current-flow Modal Vision development pilot.
- **Owner instruction:** `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6, 2026-11-01; detailed contract in `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §§B4-B5, D-G2, E.
- **Upstream:** T4 `CanvasSourceExportV1`; T4 plan SHA-256 `B009F3F6D01DA5E39269E1D03085447042A64DE2F60804880764D0B7B94C41B0`.
- **Owner render decision:** a separate `CanvasExportV1` image-export spec; 1024×1024 RGB on `#FFFFFF`; stroke width is the profile ratio times 1024, rounded to nearest integer with decimal `ROUND_HALF_UP` (5/9/14 map to 13/23/36 pixels); round caps; one-point defensive drawing emits no dot; two coincident points remain accepted; no change to `CanvasOperationProfileV1`; render only the ordered accepted operation list, never a Teacher checkpoint snapshot; bind export spec and renderer versions into the render-source binding hash.

## 1. Goal and boundaries

Render an immutable T4 operation export on CPU, write its PNG to the existing opaque local artifact store, run the real FEAT-018 image admission decoder over the exact stored bytes, persist a typed admission/derivation receipt as a second private artifact, and return a typed internal `CanvasRenderHandoffV1` to a trusted server-side caller. The operation export remains the only drawing source. There is no public upload/download grant for these derived artifacts and no client-supplied image or checkpoint JSON is accepted.

The existing BE2 source domain currently binds `RenderBinding` and `AdmissionReceipt` to a `CheckpointBinding`; T4 deliberately rejects checkpoint/restore history and its accepted source is an operation export, not a checkpoint. T5 must not fabricate a checkpoint identity to satisfy that older shape. Therefore T5 produces a versioned internal handoff object for the G4 adapter; mapping it into the existing BE2 port is **BLOCKED for T5** pending the separately approved G4 contract decision. No provider, BE2 request, or Vision claim is made here.

## 2. Layer matrix and order

| Layer | T5 work | Gate |
|---|---|---|
| L1 contracts/domain | Immutable render derivation, admission receipt, and handoff values under the new renderer package. | Unit tests prove strict version/hash/scope binding and deterministic parameters. |
| L2 application | No change. | NOT APPLICABLE; do not add an application port/service in this task. |
| L3 persistence/migration | Reuse `CoreAssetMetadataModel`; persist image and receipt metadata with the existing `LocalArtifactStore`. | Isolated PostgreSQL test proves scoped metadata and cleanup on DB failure; no schema change or Alembic. |
| L4 infrastructure | New Pillow renderer under `infrastructure/canvas_render/**`; consume T4 export operations in revision order; write PNG and typed receipts. | CPU unit tests and actual FEAT-018 admission decode; no network. |
| L5 interface | Add only an internal helper in existing O06 `be1_artifacts.py` to store a derived private artifact and receipt. Do not add a route or alter generic upload/download behavior or OpenAPI. | Integration test invokes the helper under the existing synthetic pilot fixture. |
| L6 UI | DEFERRED-BY-OWNER. | Record the UI contract below; no UI code or visual claim. |
| L7 integration | T4 export → render → private storage → real image admission → internal typed handoff, with exact source/render/admission hashes. | Disposable loopback `*_be1_acceptance` PostgreSQL test and current CPU/offline regression set. |

## 3. Exact allowlist

- New `backend/src/sketch2life/infrastructure/canvas_render/__init__.py`.
- New `backend/src/sketch2life/infrastructure/canvas_render/renderer.py`.
- `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` (internal derived-artifact helper only; existing HTTP handlers unchanged).
- New `backend/tests/unit/test_canvas_source_render.py`.
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` (T5 synthetic integration cases).
- This plan; append-only `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md`; `features/FEAT-064-current-flow-modal-vision-dev/evidence/T5_CANVAS_RENDER_ARTIFACT_REPORT_20261101.md`; and the T5 entry in `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md`.

No other path is authorized by this T5 plan. New code is confined to B5.1's `infrastructure/canvas_render/**`; O06's existing `be1_artifacts.py` is the only interface path. Test paths are explicitly enumerated here.

## 4. Render and receipt contract

`CanvasExportV1` is independent of `CanvasOperationProfileV1`. It fixes:

- width and height 1024; RGB; background `#FFFFFF`; media type `image/png`;
- normalized coordinates map by `ROUND_HALF_UP(x × 1023)` and `ROUND_HALF_UP(y × 1023)` to pixel centers, preserving endpoints within the image;
- the five existing profile colors and only profile width tokens; pixel width is `ROUND_HALF_UP(Decimal(str(profile_ratio)) × 1024)`;
- Pillow line rendering uses round caps and round joins; it preserves operation order and every accepted point, including two coincident points; a defensive one-point low-level draw is a no-op. The upstream profile still rejects one-point operations;
- no checkpoint snapshot, background asset, gallery image, suggestion overlay, model output, or unaccepted history enters rendering.

`CanvasRenderDerivationV1` binds the T4 source ref/hash, `export_spec_version`, `renderer_version`, exact Pillow version, dimensions, mode, background, media type, and raw PNG SHA-256 into a canonical `render_source_binding_sha256`. Raw PNG SHA-256 and T4 source SHA-256 remain separate facts. `CanvasImageAdmissionReceiptV1` additionally binds the exact opaque image artifact ref/hash, the derivation receipt hash, FEAT-018 policy identifier `feat018-image-admission-v1`, actual `ADMITTED` outcome, and decoder metadata. Receipt bytes are canonical UTF-8 JSON, stored privately, and have their own content hash. The internal handoff contains both opaque refs and all three distinct hashes; it never claims that admission is a Vision result or consent decision.

Rendering revalidates the export profile and each operation payload using the existing server profile validator. It refuses unsupported profiles, empty/unordered source operations, invalid payload, invalid source hashes, or unsupported color/width rather than skipping or repairing an operation.

## 5. Artifact and admission behavior

1. Render only a validated `CanvasSourceExportV1` using Pillow already declared in `backend/pyproject.toml`; record the runtime Pillow version. No package installation or lockfile edit.
2. Store PNG bytes under an opaque `LocalArtifactStore` reference. Do not return bytes or create a download route.
3. Run `Feat018ImageAdmission` with `AvImageDecoder` over a bounded temporary copy of the exact PNG bytes, passing the stored opaque ref as its artifact reference. Always remove the temporary file. A missing optional decoder or any non-ADMITTED result fails closed and removes the just-written image; it is not translated into a PASS.
4. Create and store the typed receipt only after admission is actually `ADMITTED`. In the same DB unit, persist `CoreAssetMetadataModel` rows for the image and receipt, scoped to the organization/session/source; retain the T4 source ref in provenance and set the receipt's `derived_from_ref` to the image ref. Do not add child data beyond synthetic fixture identifiers.
5. If receipt storage or DB persistence fails, delete only artifact refs created by this invocation and roll back the current transaction. Do not delete unrelated rows/files.
6. Return `CanvasRenderHandoffV1` only after metadata commit. It is a trusted internal value for G4; no BE2 port call occurs in T5 because the current port requires a true checkpoint binding.

## 6. Tests and acceptance

Tests are written before implementation and use synthetic source exports only. All network sockets are blocked except loopback; every Settings construction uses `_env_file=None`.

| Layer | Required cases |
|---|---|
| L1 unit | 1024×1024 RGB/white PNG; exact 13/23/36 width mapping; finite normalized endpoints; palette and operation order; round endpoints; coincident two-point stroke retained/rendered; one-point low-level no-op; deterministic bytes/hashes; source/spec/renderer/Pillow changes alter binding hash; malformed payload, wrong profile, extra/non-profile width/color, empty source, and digest mismatch reject. |
| L4 admission | Actual PNG is decoded by PyAV admission; dimensions/pixel mode and exact raw PNG hash match. Corrupt/oversized/unsupported image and missing decoder never produce an admission receipt. |
| L3/L5/L7 PostgreSQL integration | Existing synthetic pilot fixture exports via T4 then calls the internal T5 helper; image and receipt refs resolve only in the organization/session metadata; receipt binds T4 source and stored PNG; non-admission and injected persistence failure yield no handoff and clean only this invocation's files/rows. Existing generic upload/download behavior is unchanged. |
| Regression | Recorded G1R CPU/offline and selected contract/PG baseline; T4 unit and current synthetic PostgreSQL module. Report literal results, including pre-existing collection errors. |

Run Ruff with `--config backend/pyproject.toml`; strict mypy on touched/new L1/L4 code and report only new diagnostics against the recorded G1R baseline; run `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check`; scan new files for UTF-8/LF/no-BOM/trailing whitespace. Do not run `test_live_image_demo_api.py`, UI tests, migrations, Modal/GPU/provider/network, or real-child data.

T5 is **XONG-CHƯA REVIEW** only for rendered image + private artifacts + real admission + the internal handoff. BE2 port compatibility remains **BLOCKED** as stated in §1 and must not be silently counted complete. G2 closeout must show this split explicitly.

## 7. UI contract (UI implementation deferred)

The future Child client sends no image or checkpoint snapshot. It asks the server for an export of its current own-group canvas using the authenticated device grant; the server derives organization/session/group/canvas/profile/epoch/current revision and rejects stale or unsupported source. The server returns only opaque render/source/admission references and versioned hashes, not candidate labels or provider output. The future UI previews the exact server PNG, preserves its request/source ref across lost replies, and never retries automatically. The route/HTTP DTO is intentionally not added in T5 because the BE2 source contract is not yet compatible; a public route is a separate G4/T9 contract decision. This is a contract note, not an implemented API.

## 8. Risks and exclusions

- Pillow determinism is pinned by recording its exact version and renderer version; visual parity with the mobile canvas remains unverified because UI is deferred.
- Local artifact files and PostgreSQL metadata are not one atomic storage transaction. On metadata failure T5 compensates by deleting only newly created refs; crash-between-write/DB reconciliation belongs to T12 and must fail closed.
- Current BE2 `CheckpointBinding`/`RenderBinding`/`AdmissionReceipt` cannot truthfully represent an accepted-operation source export without a checkpoint. G4 must propose an explicit versioned source contract and approval before any adapter consumes this handoff.
- No new DB schema or migration, public route, app composition/OpenAPI/catalog change, generic upload/download relaxation, consent change, vision claim, worker, provider, Modal/GPU, UI, staging, commit, or push.
