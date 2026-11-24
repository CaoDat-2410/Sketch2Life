# Docker inventory after cleanup — 2026-11-24

Docker Desktop 29.6.2. Six stopped test containers and 24 old, unreferenced Sketch2Life images were removed. No running container was stopped. Containers were removed without `-v`; no volume-prune command ran.

| Resource | Before total | Before active | Before size | Before reclaimable | After total | After active | After size | After reclaimable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Images | 57 | 19 | 26.09 GB | 12.3 GB | 33 | 17 | 16.54 GB | 7.013 GB |
| Containers | 39 | 15 | 29.06 MB | 27.77 MB | 33 | 15 | 28.86 MB | 27.58 MB |
| Local volumes | 86 | 27 | 3.757 GB | 2.178 GB | 86 | 23 | 3.757 GB | 2.441 GB |
| Build cache | 462 records | 13 | 37.95 GB | 21.21 GB | 462 records | 13 | 37.95 GB | 29.26 GB |

The image storage metric decreased by 9.55 GB. The active-container count remains 15 and the volume count remains 86. Volume “active” count decreased from 27 to 23 because four removed containers had mounted volumes; those volumes were retained. Build-cache size did not change; its reclaimable estimate changed as Docker recalculated cache references.

The cleanup removed exactly these old stopped containers:

- `sketch2life-rev52-parent-api-pg-20261106`
- `sketch2life-storyrun-api-retest-20261105`
- `sketch2life-modal-api-host-20261103`
- `sketch2life-modal-db-host-20261103-postgres-1`
- `sketch2life-modal-db-20261103-postgres-1`
- `sketch2life-modal-api-20261103-api-1`

It removed the 24 image tags listed in `INVENTORY_BEFORE.md` after checking they were older than seven days and had no container references. No generic upstream or unrelated-project images were selected. A second eligibility scan found zero remaining old, unreferenced Sketch2Life images within the plan's naming and age criteria.

Intentionally retained: all volumes; all 15 running containers; recent stopped test stacks including `s2l-feat081-rev23`; exited helper containers belonging to Compose groups with running services; generic base images; unrelated-project resources; and all 37.95 GB of shared BuildKit cache.
