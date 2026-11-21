# School Manager web wiring plan (teacher assignment menu, in-school feedback)

Date: 2026-11-21. Status: plan written before implementation; executed on the owner's direct task (relayed by the coordinating session) in worktree branch `claude/manager-web-wiring-eae1cf`, cut from `codex/fe-ui-web-remediation` tip `bcfd53fc`. `TASK_APPROVAL.md` and `DECISIONS.md` are not changed by this task (same pattern as `PHASE_B_FE_WIRING_PLAN_20261121.md`).

Scope: `apps/web` module `school-manager` and the School Manager navigation in `shared/navigation/WebAppShell.tsx` only. Out of scope: Teacher and Platform Admin pages, backend, Android, capacity, video quota and billing (owned by the teammate).

SRS: FEAT-063 v2.7-draft copy at `.worktrees/v3/features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, SHA-256 prefix `443A3CA3` (the owner's canonical working copy for this program); `l.N` are its lines. Backend contract source (read only): `.worktrees/be-integration`, branch `feature/backend-srs-api-and-fe-integration`, `45e77aaf`.

| Menu | Backend (as built) | Change |
|---|---|---|
| Phân công giáo viên | `GET /api/be1/v1/organizations/{org}/teacher-candidates`; `POST /api/be1/v1/classes/{class_id}/assignments` with `If-Match` and `Idempotency-Key` (SRS l.1650); API test M-10..M-24 pass | Dedicated page `/school/teacher-assignments` reusing `TeacherAssignmentCard`; nav item becomes available. The card stays on the Roster & consent page. |
| Phản hồi trong trường | `GET /api/lesson-library/v1/organizations/{org}/feedback`, `GET .../feedback/{thread_id}`, `POST .../feedback/{thread_id}/replies` (`If-Match` thread revision, `Idempotency-Key`; body 1..2000) | List, thread view and reply on `/school/feedback` (SRS l.223, l.2574, l.2591, l.2630, FR-PL-22 l.2468, AC-58 l.2727). No create-thread, attachment or completion controls. |
| Hộp thư | Only `GET /api/platform-admin/v1/inbox` works for non-admin accounts; the SRS route is `GET /v1/notifications` (l.812, l.1681; goal v3 T-8a, Phase C, not on this branch) | No change. A Manager screen must not depend on a Platform Admin route. Wait for T-8a. |
| Nhóm giáo viên | none | Dropped by the owner's decision of 2026-11-21 (the SRS copy still mentions Teacher/Parent groups at l.223 and l.2574, so this is an owner decision, not an SRS removal; reconciliation stays open): remove the menu item, its `UNAVAILABLE` entry and its route. |
| Sức chứa, Hạn mức video, Thanh toán | not for Manager | Untouched. |

Verification: `npm run check` in `apps/web`, `validate_harness.py` (known FEAT-072 failure on this branch), `validate_repository_security.py`, `validate_architecture.py`, `git diff --check`, one Sonnet 5.5 (high) review, one local commit, no push.
