# FEAT-090 status

**State:** Complete; duplicate stacks stopped and canonical startup script made idempotent.
**Plan:** `plan/PLAN_REV1_SINGLE_DOCKER_STACK.md`.
**Approval:** `approvals/TASK_APPROVAL.md`.

| Milestone | Status | Result |
|---|---|---|
| M0 Inventory/canonical selection | Complete | `.env` and active Compose mapping identify `fe085-parent-api` on port 18001. |
| M1 Stop duplicates | Complete | Stopped ten competing containers across four old Compose projects; all container objects and volumes remain. |
| M2 Startup script | Complete | Script stops any competing Compose project rooted inside CAPSTONE, leaves unrelated projects alone, then runs Compose `up -d --build api` without `--no-deps` under the fixed project. |
| M3 Runtime verification | Complete | Five canonical services remain running; API health is `healthy`; 15 → 5 running containers; `docker stats` aggregate fell from about 5.15 GiB to 1.49 GiB. Compose config and PowerShell syntax both validate. |

See `evidence/RUNTIME_AFTER.md` for exact services and memory measurements.
