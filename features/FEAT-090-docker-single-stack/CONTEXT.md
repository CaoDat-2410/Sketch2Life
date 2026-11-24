# FEAT-090 — Single local Docker stack

## Findings

- The Android emulator's shared `.env` target is `http://10.0.2.2:18001`.
- The healthy Compose project `fe085-parent-api` owns host port `18001` and has one API, PostgreSQL, Redis, MinIO, and ClamAV container.
- Four other Sketch2Life Compose projects were also running. Together they duplicated API, ClamAV, Firebase Auth emulator, PostgreSQL, Redis, and MinIO services.
- Each active ClamAV container used about 953–964 MiB. Three duplicate stacks account for most excess memory.
- The current runtime now has only the canonical five services running, using about 1.49 GiB reported container memory. The API remains healthy on port 18001.
- The Compose YAML already defines one instance per service by default. Duplicate instances came from launching separate Compose project names, so the durable fix is in the canonical start script: stop the known competing project names and start dependencies under one fixed project.

## Plan and approval

- Plan: `plan/PLAN_REV1_SINGLE_DOCKER_STACK.md`.
- Approval: `approvals/TASK_APPROVAL.md`.
- Evidence: `evidence/RUNTIME_BEFORE.md` and `evidence/RUNTIME_AFTER.md`.
