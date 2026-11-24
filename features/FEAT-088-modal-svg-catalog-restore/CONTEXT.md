# FEAT-088 — Modal SVG catalog restore

## Goal

Restore the existing full Openclipart catalog into the current Modal workspace without copying the corpus into Docker or the repository.

## Current findings

- The source Volume is `sketch2life-openclipart-catalog-dev` v2 in profile `anhkhoa14155`, environment `dev`; it was created by `siesta-6107`.
- The current profile is `hieuptse184252`; its `dev` environment now contains the restored `sketch2life-openclipart-catalog-dev` Volume v2.
- The old import was pinned to dataset revision `df38e5ef633be067d397df7da19a9f009e69b3bd` and recorded 178,561 source rows, 178,134 unique CC0 rows, 1,923 guide-eligible SVGs, and 110,284,614,262 stored bytes.
- The active worktree's current `language_audio_app.py` does not reference or mount `sketch2life-openclipart-catalog-dev`. A successful volume restoration alone will not make the active branch's Parent SVG guide call consume the catalog. The historical branch that contains the importer and catalog worker uses Qwen3.5; it must not be substituted silently for the current Qwen3.8 worker.
- The core app entrypoints requested for deployment are drawing VLM, language/audio, and video. This task only prepares commands; it does not deploy them.
- Target verification on 2026-11-24: `active.json` points to the pinned revision and its manifest SHA-256 matches the downloaded target manifest. The manifest is `READY`, has 18/18 completed shards, 178,561 source rows, 178,134 indexed CC0 rows, 1,923 guide-eligible SVGs, and 110,284,614,262 stored bytes. The final manifest's indexed CC0 count matches the prior source manifest; one shard log's cumulative per-record counter reported 178,135, which is not the final distinct indexed-row count.
- The CPU importer app `ap-mZjcpEhSqlOdAx33tbxUqE` stopped normally at 18:08:47+07:00 with zero tasks. No persistent importer worker remains running.

## Constraints

- Use FEAT-063 v2.7-draft as current product authority; do not change the SRS.
- Keep the old source Volume intact. Create/restore only the same-named v2 Volume in the new `dev` environment.
- Use the pinned dataset revision and CPU importer; no GPU/model inference.
- Do not store the full corpus in Docker, the repository, or persistent local storage.
- Do not overwrite the active language/audio worker with a historical Qwen3.5 version.

## Plan and approval

- Plan: `plan/PLAN_REV1_CATALOG_RESTORE.md`.
- Approval: `approvals/TASK_APPROVAL.md`.
