# Docker inventory before cleanup — 2026-11-24

Docker Desktop 29.6.2.

| Resource | Total | Active | Size | Reclaimable |
|---|---:|---:|---:|---:|
| Images | 57 | 19 | 26.09 GB | 12.3 GB |
| Containers | 39 | 15 | 29.06 MB | 27.77 MB |
| Local volumes | 86 | 27 | 3.757 GB | 2.178 GB |
| Build cache | 462 records | 13 | 37.95 GB | 21.21 GB |

Active Compose groups include `fe085-parent-api`, `rev79-parent-local-20261112`, `rev87-parent-authfix-20261113`, `s2l-parent-e2e-20261111`, and `sketch2life`. These are protected. `s2l-feat081-rev23` is fully stopped but only 42 hours old, so it is also protected by the seven-day rule.

Persistent volume names include PostgreSQL, MinIO, Firebase Auth emulator, Redis, and ClamAV data. No volume cleanup is authorized by this plan.

## Qualified targets

After checking status, age, Compose project state, volume mounts, and image references, these six stopped containers were eligible (all are from fully stopped, old test runs):

- `sketch2life-rev52-parent-api-pg-20261106`
- `sketch2life-storyrun-api-retest-20261105`
- `sketch2life-modal-api-host-20261103`
- `sketch2life-modal-db-host-20261103-postgres-1`
- `sketch2life-modal-db-20261103-postgres-1`
- `sketch2life-modal-api-20261103-api-1`

`docker rm` will be used without `-v`; the attached anonymous and named volumes are to remain. Containers in `fe085-parent-api`, `rev79-parent-local-20261112`, `rev87-parent-authfix-20261113`, `s2l-parent-e2e-20261111`, and `sketch2life` are not candidates because those Compose groups still have running services. `s2l-feat081-rev23` is recent and remains.

The following 24 old, unreferenced app/test image tags qualified at inspection time. Final removal will recheck image references immediately before deletion:

| Image |
|---|
| `rev87-parent-authfix-api:latest` |
| `sketch2life-rev87-11d-api-check:local` |
| `sketch2life-rev87-11b-api-check:local` |
| `rev87-10-parent-api:latest` |
| `rev79-parent-local-20261112-api:latest` |
| `rev84-svg-test-migrate:latest` |
| `rev84-svg-test-seed-teacher-demo:latest` |
| `rev84-svg-test-api:latest` |
| `rev84-svg-test-seed-parent-demo:latest` |
| `rev84-svg-test-minio-init:latest` |
| `rev79-parent-local-20261112-seed-teacher-demo:latest` |
| `rev79-parent-local-20261112-migrate:latest` |
| `sketch2life-seed-parent-demo:latest` |
| `sketch2life-firebase-auth:latest` |
| `rev84-svg-test-firebase-auth:latest` |
| `rev84-svg-test-minio:latest` |
| `s2l-parent-rev73-api:latest` |
| `s2l-parent-rev73-minio-init:latest` |
| `feat063-parent-rev71-minio-init:latest` |
| `feat063-parent-rev71-api:latest` |
| `sketch2life-e2e-20261110-api:latest` |
| `sketch2life-e2e-20261110-minio-init:latest` |
| `sketch2life-modal-backend-test:latest` |
| `sketch2life-modal-api-20261103-api:latest` (eligible after removing its two stopped containers) |

No generic upstream image, unrelated-project image, Docker volume, or shared BuildKit cache is a candidate.
