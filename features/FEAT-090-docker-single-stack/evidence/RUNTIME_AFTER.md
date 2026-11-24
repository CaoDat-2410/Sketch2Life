# Local Docker runtime after single-stack cleanup — 2026-11-24

Only `fe085-parent-api` remains running for Sketch2Life. It maps the current Android API target `127.0.0.1:18001` to API port 8000.

| Running container | Service | RAM after |
|---|---|---:|
| `fe085-parent-api-20261123` | API | 227.7 MiB |
| `fe085-parent-api-postgres-1` | PostgreSQL | 40.18 MiB |
| `fe085-parent-api-redis-1` | Redis | 11.08 MiB |
| `fe085-parent-api-minio-1` | MinIO | 291.9 MiB |
| `fe085-parent-api-clamav-1` | ClamAV | 955 MiB |
| **Total** | **5 containers** | **1,525.86 MiB (~1.49 GiB)** |

The following duplicate services were stopped: `rev87-parent-authfix-20261113-api-1`; `rev79-parent-local-20261112-firebase-auth-1` and `rev79-parent-local-20261112-clamav-1`; all five `s2l-parent-e2e-20261111` containers (API, PostgreSQL, Redis, ClamAV, MinIO); and `sketch2life-api-1` plus `sketch2life-clamav-1`.

## Verification

- Running container count: 15 before → 5 after.
- Five canonical project containers: running.
- API Docker health: `healthy`.
- Host endpoint `http://127.0.0.1:18001/health`: HTTP success; body status `ok`.
- Docker volumes: 86 before and after; no volume was pruned or deleted.
- All stopped container objects remain available for intentional restart.
- Canonical Compose config validates with the shared project `.env` and FEAT-085 override.
- `start_fe085_parent_api.ps1` parses successfully. Its command now brings up the API and Compose dependencies under the fixed `fe085-parent-api` project. It first stops any competing Compose containers whose working directory is inside CAPSTONE; it does not remove their containers or volumes and leaves unrelated projects alone.
- Container RAM from `docker stats`: about 5.15 GiB before → 1.49 GiB after, saving about 3.66 GiB at the time of measurement. Docker Desktop's VM/engine usage can include memory not attributed to container stats.
- No test suite, image prune, volume prune, BuildKit prune, Compose `down`, app deployment, commit, or push was run.

## Next startup command

Use this from PowerShell to start the local backend stack again. It reuses the same Compose project, brings up its dependencies, and stops other Compose stacks rooted under CAPSTONE while preserving their data:

```powershell
& '<LOCAL_ROOT>\.codex-worktrees\fe\features\FEAT-085-parent-e2e-runtime-repair\evidence\runtime\start_fe085_parent_api.ps1' -ModalProfile 'hieuptse184252'
```
