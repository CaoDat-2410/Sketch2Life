# Feature context

- Status: APPROVED (publication in progress)
- Owner: Person 2 — owner of the task (AI Understanding lane), FEAT-018 P2-T2.
- Goal: publish the FEAT-018 P2-T2 offline WIP checkpoint as five reviewed commits on
  `feature/feat018-p2t2-live-lightning`.
- Scope: the 18 selected PUB-P1 originals, a derived public summary, one FEAT-018
  evidence-index entry and these publication records. See `plan/PLAN.md`.
- Non-goals: live/Studio/SSH/provider work, D6 rebind, FEAT-018 approval history, scanner or
  lint/type configuration, FEAT-020 architecture fix, dev merge.
- Dependencies: FEAT-018 (owning task; its `approvals/TASK_APPROVAL.md` is under an owner
  approval-write hold, so the publication authority is recorded here); FEAT-020 owns the
  pre-existing `backend_ai_workflow.py` architecture finding.
- Risks: see `plan/PLAN.md`.

## Context snapshot

FEAT-018 P2-T2 offline work accumulated locally after baseline `44af2e4`. The local draft plan
PUB-P1 (2026-10-11) classified 76 changed/untracked files: 18 publication candidates, 58 held.
Fresh verification on exact intermediate trees, a fresh scanner review and an owner review
package preceded the owner's decisions A + B1 + C1 (see `approvals/TASK_APPROVAL.md`).

Status after this feature: offline code and records are published as WIP. D1/D11 stay
unresolved, D6 is not finally resolved, Stage 4 is NOT READY, live entry is NOT_AUTHORIZED and
repository security stays PENDING beyond this checkpoint's scoped acceptance. Security S3 and
C1–C7 remain open. POSIX behaviour remains UNVERIFIED.
