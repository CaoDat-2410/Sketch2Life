# FEAT-088 catalog restore progress

- Date: 2026-11-24 (Asia/Saigon)
- Source Modal profile/environment: `anhkhoa14155/dev`
- Target Modal profile/environment: `hieuptse184252/dev`
- Target Volume: `sketch2life-openclipart-catalog-dev` (v2)
- Pinned dataset revision: `df38e5ef633be067d397df7da19a9f009e69b3bd`
- Import app: `ap-mZjcpEhSqlOdAx33tbxUqE` (`sketch2life-openclipart-catalog-import-dev`)
- Execution: CPU-only, 4 CPU / 16 GiB; no GPU inference.

## Source manifest

- Shards: 18
- Source rows: 178,561
- Stored CC0 rows: 178,134
- Guide-eligible SVGs: 1,923
- Rejected rows: 176,638
- Compressed source shards: 22,340,611,707 bytes
- Extracted SVG assets: 87,741,484,027 bytes
- SQLite index: 202,518,528 bytes
- Total expected catalog: 110,284,614,262 bytes
- Source manifest status: `READY`

## Import checkpoint

At 2026-11-24 17:52 (Asia/Saigon), importer logs showed 17 of 18 shards committed and 170,000 source rows processed. After a preemption, shard 16 was successfully reprocessed and committed in 2,158 seconds. Shard 17 is now running; final validation remains pending. The new Volume had been created, but final readiness must not be inferred until `active.json` points to the pinned revision and the destination manifest reports `READY` with matching totals.

The previous shard checkpoints were:

| Shard | Cumulative rows | Cumulative CC0 rows | Cumulative eligible SVGs |
|---:|---:|---:|---:|
| 0 | 10,000 | 9,984 | 142 |
| 1 | 20,000 | 19,965 | 236 |
| 2 | 30,000 | 29,938 | 373 |
| 3 | 40,000 | 39,924 | 454 |
| 4 | 50,000 | 49,905 | 585 |
| 5 | 60,000 | 59,883 | 731 |
| 6 | 70,000 | 69,871 | 852 |
| 7 | 80,000 | 79,836 | 943 |
| 8 | 90,000 | 89,793 | 1,050 |
| 9 | 100,000 | 99,757 | 1,163 |
| 10 | 110,000 | 109,736 | 1,231 |
| 11 | 120,000 | 119,717 | 1,352 |
| 12 | 130,000 | 129,696 | 1,404 |
| 13 | 140,000 | 139,666 | 1,526 |
| 14 | 150,000 | 149,651 | 1,631 |
| 15 | 160,000 | 159,611 | 1,725 |
| 16 | 170,000 | 169,587 | 1,853 |
| 17 | 178,561 | 178,135 | 1,923 |

## Import interruption

At 2026-11-24 17:15:39, shard 16 indexing was interrupted with `KeyboardInterrupt`; importer cleanup then logged `sqlite3.OperationalError: database table is locked`. Modal logged a container preemption at 17:16:13 and automatically restarted the same function input at 17:16:17. The restarted task resolved the same pinned dataset revision and began shard 16 again; the 16 completed-shard checkpoints remain the resume boundary. No manual stop or second import was issued. The importer finalizer verified all expected shard files and hashes before setting `READY`; this run did not execute SQLite `PRAGMA integrity_check`.

The automatic restart completed shard 16 at 17:52:15 with cumulative `source_rows=170000`, `stored_cc0_rows=169587`, and `guide_eligible=1853`. The worker continued to shard 17. The interrupted attempt did not alter the 16 prior durable checkpoints.

No source Volume files were modified. No core AI apps were deployed. The current checked-out language/audio worker does not yet mount this catalog; see `CONTEXT.md` before treating the dataset as wired into Parent SVG guidance.

## Final target verification

- Target: Modal profile `hieuptse184252`, environment `dev`, Volume v2 `sketch2life-openclipart-catalog-dev`.
- Active revision: `df38e5ef633be067d397df7da19a9f009e69b3bd` (`kawwaaa/openclipart`).
- `active.json` manifest digest matches the downloaded target `catalog-manifest.json`: `30b4d154f55a6897a626e8f90bd5c4d5e518aef5500ca2f7209c425a9a55b1a1`.
- Manifest status: `READY`; completed shards: 18/18; source rows: 178,561; final indexed CC0 rows: 178,134; guide-eligible SVGs: 1,923; stored SVG bytes: 87,741,484,027; catalog database bytes: 202,518,528; total stored bytes: 110,284,614,262 (~102.7 GiB).
- The final indexed-row count matches the prior source manifest. The shard progress accumulator reported 178,135 CC0 rows, one above the final indexed `COUNT(*)` recorded by the importer finalizer. The accumulator is a per-record progress value while the final count is the indexed row count; the exact record behind the one-row difference was not identified. It did not cause a manifest/source mismatch. No additional inference or re-import was needed.
- Target `volume ls` shows `openclipart-catalog/active.json` and the pinned revision directory with `assets`, `catalog-manifest.json`, `catalog.sqlite3`, and `source_shards`. The importer verifies all expected shard files and hashes before setting `READY`.
- App `ap-mZjcpEhSqlOdAx33tbxUqE` stopped normally at `2026-11-24 18:08:47+07:00`; `modal app list` reports `stopped`, `tasks=0`. No GPU work was run.
- Evidence files `target-active-20261124.json` and `target-manifest-20261124.json` contain only catalog metadata, not the dataset corpus.
- The old source Volume was not modified. The current Qwen3.8 language/audio app still has no catalog Volume mount/reference, so this restoration does not yet activate catalog-backed SVG guide generation.
