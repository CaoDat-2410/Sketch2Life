# FEAT-090 Plan Rev1 — Single local Docker stack

**State:** Approved by the owner's direct request on 2026-11-24 to stop unneeded running containers and make the local Docker setup run one copy of each system service.

## Goal and canonical stack

Use the healthy `fe085-parent-api` Compose project as the only active local Sketch2Life stack. The shared project `.env` points the Android emulator to `http://10.0.2.2:18001`, and this stack maps the API to host port `18001`.

It contains one each of the required local services: API, PostgreSQL, Redis, MinIO, and ClamAV. Compose already creates one container per service by default; the excess RAM comes from several old Compose projects being started side by side, including duplicate APIs and three ClamAV instances.

## Approved scope

1. Stop, without deleting, the ten running containers in the duplicate `rev87-parent-authfix-20261113`, `rev79-parent-local-20261112`, `s2l-parent-e2e-20261111`, and `sketch2life` stacks.
2. Keep all five running containers in `fe085-parent-api`.
3. Update the FEAT-085 local start script to stop any other Compose project whose working directory is within the CAPSTONE root before startup, and remove `--no-deps` so Compose ensures the canonical API's dependencies are started once when needed. Projects outside CAPSTONE are untouched.
4. Preserve every container object, volume, image, and project definition. Do not run `down`, `rm`, `prune`, or change credentials.

## Acceptance criteria

- Exactly five local Sketch2Life service containers are running in the canonical project: one API, PostgreSQL, Redis, MinIO, and ClamAV.
- API container health remains `healthy`; no competing API/ClamAV/infra containers remain running.
- All Docker volumes and existing stopped containers remain intact.
- The startup script is repeatable and starts dependencies in the same fixed Compose project rather than creating a new project per run.
- Evidence records per-container RAM before/after and the exact containers stopped.

## Exclusions

- Do not stop the unrelated `gara-project-showcase` project or any non-Sketch2Life resource.
- Do not change model/Modal services, `.env`, database contents, storage, or app code.
- No commit or push.
