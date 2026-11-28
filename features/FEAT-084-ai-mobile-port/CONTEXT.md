# FEAT-084 — AI mobile port

## Goal

Bring the new Parent AI screens of CaoDat's branch `origin/codex/parent-modal-e2e-20261123` (commit `77635688`, `apps/ui-mobile`) onto the current mobile line without losing the goal v4 Phase A Android Parent wiring.

## Why

The source branch is built on an older mobile base. Its topic, drawing-subject and sketch-guide screens are wanted; its older wiring, video-candidate screen and activity calls are not. FEAT-083 ported the matching backend routes under Phase A, so the screens can now be wired to a real contract.

## Product authority

Only the FEAT-063 canonical working SRS named in `docs/context/SRS_AUTHORITY.md` at the base commit. SRS Rev70-Rev73 on the source branch is not adopted here.

## Boundaries

See `plan/PLAN.md`. No backend, no Modal, no SRS, no video candidate, no activity-selection change.

## Related

FEAT-081 (Parent mobile port), FEAT-083 (AI backend port), FEAT-066 (goal v4 Phase A wiring).

## Current run (2026-11-23)

- Preflight passed: the approved plan hash matches `approvals/TASK_APPROVAL.md`; approval records remain unchanged.
- Product behavior was checked against the FEAT-063 v2.7-draft SRS, especially FR-P-11, FR-P-12 and FR-AI-15.
- Request/response field mapping is checked against the AIPORT1 Pydantic contracts at commit `283158a8`.
- Current mobile base is `d8786b2b`; source UI is `77635688`.
- Baseline on the current base: 18 Vitest files / 228 tests pass; UI-copy validation passes; typecheck reports 111 existing errors, all under `packages/art-renderer` because `zod` is unavailable in the linked environment.
- `pnpm exec` attempted an automatic modules reconciliation and aborted before running; direct linked Vitest/TypeScript binaries were used, with no network install.
- Implementation and post-change verification are complete. The report in `evidence/notes/FINAL_REPORT_20261123.md` records the hand-merge inventory, test changes, validation results, non-runs and open follow-ups.
- Final checks: 20 Vitest files / 239 tests pass; UI-copy and repository/security/architecture/harness validators pass; typecheck remains at 111 baseline errors in `packages/art-renderer` and zero elsewhere; temporary dependency junctions were removed.
