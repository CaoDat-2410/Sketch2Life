# Local Docker runtime before single-stack cleanup — 2026-11-24

Android emulator endpoint from the shared project `.env`: `http://10.0.2.2:18001`.

Canonical stack `fe085-parent-api` (keep):

| Container | RAM |
|---|---:|
| `fe085-parent-api-20261123` (API) | 224.5 MiB |
| `fe085-parent-api-postgres-1` | 37.42 MiB |
| `fe085-parent-api-redis-1` | 9.27 MiB |
| `fe085-parent-api-minio-1` | 289.9 MiB |
| `fe085-parent-api-clamav-1` | 952.9 MiB |

Competing running containers to stop:

| Container | RAM | Role |
|---|---:|---|
| `rev87-parent-authfix-20261113-api-1` | 196.3 MiB | Duplicate API, port 58000 |
| `rev79-parent-local-20261112-firebase-auth-1` | 210.8 MiB | Old local Firebase Auth emulator |
| `rev79-parent-local-20261112-clamav-1` | 953.9 MiB | Duplicate ClamAV |
| `s2l-parent-e2e-20261111-api-1` | 184.9 MiB | Duplicate API, port 18000 |
| `s2l-parent-e2e-20261111-postgres-1` | 42.05 MiB | Duplicate PostgreSQL |
| `s2l-parent-e2e-20261111-redis-1` | 11.3 MiB | Duplicate Redis |
| `s2l-parent-e2e-20261111-clamav-1` | 959.8 MiB | Duplicate ClamAV |
| `s2l-parent-e2e-20261111-minio-1` | 81.24 MiB | Duplicate MinIO |
| `sketch2life-api-1` | 155.2 MiB | Duplicate API, port 8000 |
| `sketch2life-clamav-1` | 964.1 MiB | Duplicate ClamAV |

Initial inventory: 15 running containers across five Sketch2Life stacks. Docker's system memory report showed 31.29 GiB total host memory. Per-container usage above totals approximately 5.27 GiB; Docker Desktop's 9 GiB figure can include VM/engine overhead not attributed by `docker stats` to these containers.

The four competing projects have no configured endpoint in the active mobile `.env`; the current emulator points only to port 18001.
