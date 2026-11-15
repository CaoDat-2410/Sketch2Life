# Rev87.15 — Openclipart catalog on Modal Volume with source-bound Qwen strokes

**Date:** 2026-11-14<br>
**Status:** APPROVED by the owner's direct instruction to use a Modal Volume and not Docker for the SVG dataset.<br>
**Canonical SRS:** FEAT-063 v2.7-draft. §§1–31 remain unchanged; append environment-specific implementation evidence in §32 only.

## Goal

Make the Parent SVG guide cover many more topics by using the public Openclipart dataset as a searchable source corpus stored on Modal Volume v2. At runtime, retrieve a suitable source SVG and let Qwen3.5 plan its progressive stroke order from that illustration. Preserve the actual source geometry so the finished strokes form the same animal/object as the color reference.

## Approved scope

1. **Dataset and Modal storage**
   - Use `kawwaaa/openclipart`, whose dataset card reports 178,604 public-domain SVG records, English-heavy metadata, and about 22.3 GB of compressed source shards.
   - Add a CPU-only Modal ingestion app/function. It resolves the dataset's `main` ref once, records the immutable resolved commit, downloads the public JSONL-Zstandard shards directly inside Modal, and stores both the original compressed shards and extracted CC0 SVG assets, metadata index, license/provenance manifest, and shard checksums on a dedicated **Modal Volume v2** named `sketch2life-openclipart-catalog-dev` in environment `dev`.
   - Keep the dataset, derived catalog, index and import temporary files out of Docker images, Docker build context, the repository, and local machine storage. The importer may use its Modal container's ephemeral disk while processing; durable corpus artifacts go only to the Modal Volume.
   - Do not mix the catalog with the Qwen model Volume or request scratch Volume. Do not delete or overwrite existing Volumes. The first import is idempotent and refuses to replace a non-empty catalog with a different dataset revision.

2. **Catalog layout and safety**
   - Preserve source row identity and Openclipart page URL, title, description/tags, artist when present, CC0 declaration, dataset commit, source-shard name/hash, SVG content hash, and the exact stored SVG bytes.
   - Build a local text-search index on the Modal Volume. Keep every source record in the corpus; mark a record eligible for drawing-guide use only after bounded SVG parsing and safety/complexity checks.
   - Indexing does not make external SVG trusted. Reject or exclude scripts, event handlers, foreign objects, external URLs/references, raster embeds, unsupported elements/transforms, invalid viewBox, oversized files, or complexity outside a bounded guide profile. Never deliver raw external XML to mobile/web UI.
   - Access candidate source bytes through a safe, read-only catalog adapter. Keep any small curated Openclipart/OpenMoji/Arcadia source packs as fallbacks and preserve their existing provenance.

3. **Qwen source-derived guide**
   - Mount the catalog Volume read-only in the existing private language/audio Modal app; do not add data to its image or Docker image. Keep the guide workload disabled by default.
   - Search uses generic adult-selected topic and difficulty only. Since source metadata is mainly English, use the already loaded Qwen model to create bounded English search terms, then retrieve a small deterministic top-candidate set from the Volume index.
   - Send only the selected safe source illustration and bounded component/path identifiers to Qwen3.5. Qwen returns a versioned plan: 4–8 ordered stages, path/component identifiers, and short age-appropriate Vietnamese labels. Qwen must not invent or return replacement path geometry.
   - The backend/worker validates that every chosen identifier belongs to the selected pinned source and appears exactly once, that stage count and complexity satisfy current hard gates, and that output is safe. The deterministic SVG renderer reuses exact source geometry to create progressive line stages and pairs the original color source for the final reveal. Invalid or unsuitable sources fail closed and the optional guide remains skippable/nonblocking to required photo capture.
   - Response provenance identifies dataset, resolved dataset revision, source asset/page, CC0, and source hash. Draft remains private and requires adult review. No child image, child profile, voice/audio, account/Firebase identity, or child-specific context is sent to the topic-guide workload.

4. **Parent contract/UI**
   - Extend the existing versioned response only as needed to carry the safe original-color reference and dataset source provenance. Keep the progressive step renderer and show the matching color source at the last step, consistent with the existing local source-guide behavior.
   - No new user-visible feature is made required. Catalog miss, unsafe source, disabled workload, timeout or quality rejection does not block drawing/photo capture.

5. **Operations and cost**
   - Importing/downloading happens only when an operator explicitly runs the Modal ingestion command; starting Docker or the normal inference app does not download the dataset or issue AI inference.
   - Use CPU for corpus ingestion, a bounded ephemeral disk, shard-by-shard streaming, resumable checkpoints and an explicit final Volume commit. Inference uses the existing Qwen Modal GPU only after a user explicitly requests a guide.
   - Record actual Modal Volume name/version/environment, resolved dataset commit, source shard checksums, source row count, accepted/rejected eligibility counts, stored byte count, import duration, Modal compute/storage usage if available, and worker/UI attempt results. Do not claim upload/deployment without live Modal evidence.

## In-scope files

- `deployment/modal/srs_v23/openclipart_catalog_app.py` — new CPU-only Modal ingestion/index app and explicit local entrypoint.
- `deployment/modal/srs_v23/openclipart_catalog.py` — bounded dataset/catalog read, provenance, and safe SVG component extraction helpers shared with the worker.
- `deployment/modal/srs_v23/language_audio_app.py` — read-only catalog mount and source-bound progressive guide planning in the existing Qwen workload.
- `deployment/modal/srs_v23/workloads.json` and `deployment/modal/srs_v23/README.md` — disabled-by-default state, operator command, Volume name, import/recovery/health guidance.
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` and `backend/src/sketch2life/contracts/schemas/svg_engine.py` — source selection/provenance response integration, preserving the current private draft contract.
- `apps/ui-mobile/src/parent/domain/svgGuide.ts`, `apps/ui-mobile/src/parent/presentation/screens/SketchGuideScreen.tsx`, and `apps/ui-mobile/src/parent/presentation/components/ProgressiveSvgGuide.tsx` — consume matching safe color illustration and source credit if contract needs extension.
- FEAT-063 plan, approval, context, source register, decision, status, evidence and canonical SRS §32.30 / `docs/context/SRS_AUTHORITY.md` pointer only. Do not edit SRS §§1–31.

## Acceptance criteria

- [x] A dedicated Modal Volume v2 is the sole durable location for the full dataset and derived catalog; no dataset corpus/index is copied into Docker or tracked repository files.
- [x] The importer resolves and records one immutable HF dataset revision, streams and durably retains every original compressed source shard on the Modal Volume, resumes safely, verifies shard/asset hashes and refuses partial catalog activation.
- [x] The catalog records the full source row count and rejection count; only CC0 rows enter the usable catalog, and only safe/complexity-bounded rows become guide candidates.
- [ ] The worker mounts the catalog read-only and returns a source-bound Qwen plan whose identifiers are validated against the selected SVG; the renderer uses only those exact source paths for progressive stages.
- [ ] Parent receives the matching color illustration/source/license metadata on the last step, with no raw external SVG executed in the client.
- [ ] Guide remains optional; workload flag remains off unless explicitly enabled; any catalog/model/quality failure still permits required photo capture.
- [x] Evidence distinguishes source review, code checks, real Modal import, real Qwen inference, and Android/UI runtime. Missing Modal CLI/auth/credit or unavailable services are reported as not executed, not passed.

## Boundaries

- No Docker dataset upload, no local corpus download, no GPU request for import, no video, no child data, no seed/account/consent/database mutation, no secret/token changes, no production enablement/publication, no Volume deletion, no shared-service restart, no gate weakening, no commit/push/merge.
- Do not install or invoke unrelated models. No Modal inference is sent during startup or ingestion.
- Existing system/Modal model and scratch Volumes are preserved. The new catalog uses a separate v2 Volume to avoid interfering with them.

## Research and primary references

- Dataset card and documented schema/size: https://huggingface.co/datasets/kawwaaa/openclipart
- Openclipart license statement: https://openclipart.org/faq
- Modal large dataset ingestion guidance: https://modal.com/docs/guide/dataset-ingestion
- Modal Volume v2 guide: https://modal.com/docs/guide/volumes
- Modal Volume SDK reference: https://modal.com/docs/sdk/py/latest/Volume

## Known execution constraint at approval time

At approval time, no `modal` executable was found in the checked locations. This constraint was resolved when the owner switched Modal account access and the CLI became available; runtime authorization is recorded in `approvals/TASK_APPROVAL.md`.

## Runtime execution result — 2026-11-15

- Import: **PASS** — all 18 source shards were stored and hash-verified; Volume v2 returned `READY`. Final counts and byte sizes are in `evidence/EV-063-110_OPENCLIPART_MODAL_VOLUME_CATALOG_20261114/REPORT.md`.
- Deployment/health: **PASS** — language/audio app deployed; CPU `/health` confirmed pinned Qwen3.5-9B and catalog ready without allocating a GPU.
- Qwen worker: **FAIL** — one real synthetic `con mèo` inference reached model generation but strict output validation rejected path coverage with `SVG_CATALOG_STROKE_PLAN_PATH_COVERAGE_INVALID`. It was not a timeout; no retry was performed.
- Parent UI/API/Android and Teacher presentation: **NOT TESTED**. No child data or video was used. Workload remains disabled by default.
- Acceptance 4: failed. Acceptance 5–6: not established at runtime. Acceptance 7: evidence recorded. Target SRS §§1–31 remain unchanged; SRS §32.30 is as-built evidence only.
