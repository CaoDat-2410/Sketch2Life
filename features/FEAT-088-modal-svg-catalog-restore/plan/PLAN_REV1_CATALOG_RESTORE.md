# FEAT-088 Plan Rev1 — Restore Modal Openclipart catalog in the new workspace

**State:** Approval recorded from the owner's direct request on 2026-11-24 to recover the existing SVG catalog for the new Modal workspace and provide deployment commands for the three core AI apps.
**Product authority:** FEAT-063 v2.7-draft remains the current product SRS. This is an infrastructure/data restoration; no SRS requirements change.

## Goal

Make the full Openclipart source catalog available in the current Modal `dev` workspace, using the same immutable dataset revision already present in the old workspace. Preserve the old volume and keep the corpus out of Docker and the repository. Give the owner exact commands for deploying the three current core Modal apps.

## Verified source and target

- **Source profile/workspace:** `anhkhoa14155`, environment `dev`.
- **Source Volume:** `sketch2life-openclipart-catalog-dev`, Volume v2; Modal listed it as created by `siesta-6107`. The user supplied a dashboard image showing the volume with 102.7 GiB and 175,817 files.
- **Target profile/workspace:** `hieuptse184252`, environment `dev`.
- **Target state:** the same-named catalog Volume is absent. Existing model-weight and job-scratch Volumes are present.
- **Expected immutable dataset revision and prior import result:** `df38e5ef633be067d397df7da19a9f009e69b3bd`; 178,561 source rows; 178,134 unique CC0 rows; 1,923 guide-eligible SVGs; 110,284,614,262 stored bytes. These values are implementation evidence from the prior Modal import, not product requirements.

## Scope

1. Read the old Volume's active/manifest metadata using the old profile and confirm the immutable revision before creating anything in the target workspace.
2. Recreate the same dataset revision in the target workspace using the previously executed CPU-only Modal importer from branch `codex/feat063-parent-docker-modal-seed-20261111`. Pin the revision explicitly; do not resolve `main` again. The importer lazily creates a Volume v2 with the existing name in the target `dev` environment, streams the public source inside Modal, verifies shards/assets, builds the SQLite/FTS index, and marks the manifest `READY` only after validation.
3. Use CPU only for ingestion. Do not call Qwen, LTX, or any GPU/model inference. Do not modify or delete the old source Volume. Do not place dataset contents in Docker, Git, or persistent local storage.
4. Verify the target Volume's manifest, status, dataset revision, row counts, eligible count, and stored byte count against the old import evidence.
5. Provide commands for the three current app files: `drawing_vlm_app.py`, `language_audio_app.py`, and `video_app.py`, explicitly targeting profile `hieuptse184252` and environment `dev`. Do not deploy these apps in this task.
6. Inspect whether the current active branch's language/audio app mounts or consumes this catalog. Report the integration state accurately; do not claim the data is used if the current code does not reference the Volume.

## Out of scope

- No app deployment, health request, GPU warm-up, Qwen/LTX inference, video generation, Docker dataset transfer, account/profile changes, token/secret changes, volume deletion, source-volume mutation, SRS amendment, model migration, UI/backend changes, commit, or push.
- Do not silently substitute the historical Qwen3.5 language worker for the current Qwen3.8 worker.

## Acceptance criteria

- The target `hieuptse184252/dev` contains a Volume v2 named `sketch2life-openclipart-catalog-dev` with a `READY` manifest matching the old immutable dataset revision and import counts.
- The old `anhkhoa14155/dev` source Volume remains present and unchanged.
- Ingestion uses no GPU and leaves no corpus copy in Docker or tracked files.
- Final response gives the exact three deploy commands and states whether the current language/audio source mounts the catalog.
- Evidence records the actual import result and any difference from the source manifest. No claim of app deployment or AI output is made.

## Implementation sources

- Prior importer: `codex/feat063-parent-docker-modal-seed-20261111:deployment/modal/srs_v23/openclipart_catalog_app.py` and `openclipart_catalog.py`.
- Prior import result: `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-110_OPENCLIPART_MODAL_VOLUME_CATALOG_20261114/REPORT.md` on that historical branch.
- Current app entrypoints: `deployment/modal/srs_v23/drawing_vlm_app.py`, `language_audio_app.py`, and `video_app.py`.
- Current Modal CLI: `<LOCAL_ROOT>\.venv-modal\Scripts\modal.exe`.

## References

- [Modal Volumes](https://modal.com/docs/guide/volumes)
- [Modal CLI Volume commands](https://modal.com/docs/cli/latest/volume)
- [Modal deployment commands](https://modal.com/docs/cli/latest/deploy)
- [Openclipart dataset](https://huggingface.co/datasets/kawwaaa/openclipart)
