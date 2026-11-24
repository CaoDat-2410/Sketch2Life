# FEAT-089 Plan Rev1 — Docker cleanup

**State:** Approved by the owner's direct request, “dọn bớt docker,” on 2026-11-24.
**Scope:** Remove stale, rebuildable Sketch2Life Docker test containers/images while preserving active services and all persistent data.

## Baseline

Docker Desktop 29.6.2 inventory before cleanup:

| Resource | Total | Active | Size | Reclaimable |
|---|---:|---:|---:|---:|
| Images | 57 | 19 | 26.09 GB | 12.3 GB |
| Containers | 39 | 15 | 29.06 MB | 27.77 MB |
| Local volumes | 86 | 27 | 3.757 GB | 2.178 GB |
| Build cache | 462 records | 13 | 37.95 GB | 21.21 GB |

## Approved cleanup

1. Remove exited Sketch2Life test containers older than seven days only after confirming they are not part of a Compose project with running services. Use `docker rm` without `-v`.
2. Remove only old Sketch2Life test images (`sketch2life-*`, `s2l-*`, `rev*`, `feat*`) older than seven days that have zero container references at execution time. Do not remove generic upstream images or images used by any container.
3. Preserve all running containers, recent stopped test containers, all Docker volumes (named and anonymous), Compose projects with running services, and all BuildKit cache because that cache is shared across projects.
4. Record before/after usage. Do not alter Compose files, app code, `.env`, Modal resources, or any database/object-store volume.

## Acceptance criteria

- No running service is stopped or removed.
- Only qualifying old, stopped Sketch2Life test containers and unreferenced images are removed.
- No Docker volume is removed; no persistent data is pruned.
- Final report lists exact cleanup scope and Docker usage before/after.

## Explicit exclusions

- No `docker system prune`, `docker volume prune`, `docker compose down`, or build-cache prune.
- Keep recent E2E stacks (including `fe085-parent-api`, `s2l-feat081-rev23`) and all containers belonging to partially running Compose projects.
- No commit or push.
