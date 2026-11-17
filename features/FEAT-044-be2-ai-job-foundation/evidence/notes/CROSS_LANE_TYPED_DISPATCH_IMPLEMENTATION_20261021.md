# BE2-01 typed cross-lane dispatch — 2026-10-21

## Result

Implemented the approved BE2-01 typed worker route within the exact scope
addendum SHA256
`AD1BA2706655CD040ACBBBF508577F79A41F5D5B3EF57D1437DA4C7F7F185DBD` and
execution manifest in `approvals/PHASE_B_TASK_APPROVAL.md`.

`DispatchWorker` now routes the explicitly configured BE2-08 job type to its
registered `VideoWorker`, passing the original `WorkerDispatchEnvelope`
unchanged. The existing `sketch_assistance` provider path remains registered;
all other and malformed job types return a typed rejection before foundation
attempt start or provider invocation. The router does not define or persist a
new shared job-type value; composition supplies it. BE2-08 admission remains
responsible for authoritative persisted job/request/attempt checks.

The change does not implement CR08-01, a durable BE2-07 source fence, a
BE2-14 execution grant/reservation binding, or CR09-01 artifact reads. The
unit-level dispatch proof is not an X09-08 composition proof and does not
change BE2-01 card acceptance/status.

## Changed paths

- Modified `backend/src/sketch2life/infrastructure/ai_jobs/worker.py`.
- Added `backend/src/sketch2life/infrastructure/ai_jobs/typed_dispatch.py`.
- Added `backend/tests/unit/test_ai_job_video_dispatch.py`.

No Phase B source, schema, migration, or existing test file changed. No other
card-owned source/test was edited. The five approved scope addenda remain
byte-identical. X01 remains `PARTIAL`; X05d remains `BLOCKED`; X05c/CR09-02
remains open. No Modal, Lightning, provider, server, database, or runtime was
used.

## Offline validation

Environment: repository's existing `backend/.venv`, CPython 3.12.10; no
packages installed.

| Check | Result |
|---|---|
| New dispatch + BE2-01 B5 + BE2-08 worker focused batch | 79 passed, 0 failed, 0 errors, 0 skipped |
| Ruff on the three changed code/test files | PASS |
| mypy strict on the three changed code/test files | PASS |
| Harness, security, architecture, skeleton validators | PASS |
| `git diff --check` | PASS |

JUnit: `evidence/raw/cross-lane-typed-dispatch-20261021/junit.xml`.
Machine-readable source/test receipt:
`evidence/metrics/CROSS_LANE_TYPED_DISPATCH_20261021.json`.
Repository validators and `git diff --check` were run after the documentation
updates and are recorded in the final receipt; security scanned 4,567 publishable
files. No card is marked accepted or DONE.
