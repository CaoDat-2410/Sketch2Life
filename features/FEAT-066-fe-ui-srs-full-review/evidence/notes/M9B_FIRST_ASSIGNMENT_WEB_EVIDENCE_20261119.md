# C6 part M9-B — first Teacher assignment, web evidence (goal v2)

- **Date:** 2026-11-19. **Task:** the owner's added scope "C6 part M9-B", web part, under the goal v2 program
  approval (SHA-256 `5DFC1EDE…4795F8`). Accepted by the goal; owner final check pending. Nothing pushed.
- **Plan:** `PLAN_M9B_FIRST_TEACHER_ASSIGNMENT_DRAFT3_20261119.md` on `feature/feat066-be-integration` (R3 READY WITH
  NOTES). BE half: commit `6f10ec24`.
- **Teammate branch:** fetched before the commit; `origin/codex/fe-ui-web-remediation` still `c42d913a`.

## Decisions (SRS)

- The School Manager chooses a Teacher from the server's candidate list (display name only; O-3b) for a class
  without an active Teacher; nothing is preselected because the assignment cannot be changed here (UC-12 out of
  scope). The command sends `If-Match` with the class `assignment_revision` and an `Idempotency-Key` per
  (class, candidate, revision), reused for a retry (SRS §21.2 line 1650, §21.4 lines 1697, 1699).
- 409 → classes reload with "Lớp đã thay đổi hoặc đã có Teacher; đã tải lại."; 404 (uniform shape) → neutral message
  and reload; 403 → no-permission message. Empty list: "Chưa có Teacher nào của tổ chức đủ điều kiện."
- A class without `assignment_revision` (older server) cannot be assigned; no `If-Match` is built.

## What changed

`modules/school-manager/be1/services/classService.ts` (types, `listTeacherCandidates`, `assignTeacher`,
`assignmentOutcomeMessage`); new `pages/TeacherAssignmentCard.tsx`; `pages/RosterConsentPage.tsx` (card replaces
the "Chờ API" placeholder; remounted per class so messages reset); `pages/SchoolOverviewPage.tsx` (copy);
`shared/api/backendApi.tsx` (unused `createAssignment` helper to a removed path deleted); new
`be1/__tests__/teacherAssignment.test.tsx`.

## Checks (`apps/web`)

- `npm run test`: 14 files / 65 tests pass. `npm run lint`: exit 0, 28 warnings (= baseline). `npm run build`: exit 0.
- Implementation review (Sonnet 5.5 high, subagent, BE and web): ACCEPTABLE WITH NOTES 0 / 0 / 6; the web notes
  (no preselection, per-class reset, candidate reload button) were applied.

## Limits

Two Teachers with the same display name cannot be told apart (no email allowed). The 409 text is shared by
`CLASS_TEACHER_EXISTS`, `STALE_REVISION` and `RESOURCE_CONFLICT`.
