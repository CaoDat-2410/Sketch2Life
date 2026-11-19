# C4 C-T — Teacher Lesson Library web slice, implementation evidence (goal v2)

- **Date:** 2026-11-19. **Task:** goal v2 row C4, web part. Accepted by the goal under program approval
  (`GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, SHA-256 `5DFC1EDE…4795F8`); owner final check pending. Nothing pushed.
- **Package:** `PLAN_CT_TEACHER_SLICE_PACKAGE_DRAFT4_20261119.md` on `feature/feat066-be-integration` (SHA-256
  `1A199C40…`), review R2 READY WITH NOTES. The BE half is the C4 commit on `feature/feat066-be-integration`.
- **Teammate branch:** `origin/codex/fe-ui-web-remediation` fetched before the work: `c42d913a`, no new commits.

## Decisions (SRS D-209 copy)

- Lesson save (PATCH), archive (DELETE), version create and upload abort send an `Idempotency-Key` with `If-Match`
  (SRS §21.4 line 1697, §21.1 line 1636; CT-13).
- One key per exact command: the signature holds command, organization, target, the `If-Match` revision and the
  payload; a retry reuses it, a new revision or payload gets a new key (§21.1 line 1636).
- Abort reads the session status first and sends its `revision` (SRS line 1658; CT-14); a stale answer reads the
  status again and retries once with a new key; 410 or 409 `UPLOAD_SESSION_STATE_CONFLICT` clears the saved session;
  a `COMPLETED` session is recovered, not cleared.
- After a 409 `STALE_REVISION` the form keeps the Teacher's text; the Teacher chooses "Tải lại bản hiện tại" to load
  the current version (no silent overwrite, §21.4 line 1699).
- Fallback messages for the five SRS §9.8 upload codes, same wording as the backend table.
- `BLOCKED_OPEN` CT-15: no page control for B07 (version from extraction); only the typed client method ships. The
  B08 grant-revoke control waits for G-T1.

## What changed

`shared/api/backendApi.tsx` (keys, abort revision, `createLessonVersion`, `UploadPartReceipt`, `LessonVersion`,
`LessonUploadSession.revision`); `shared/api/errorEnvelope.ts` (five codes);
`modules/teacher/services/commandKeys.ts` and `uploadAbort.ts` (new); `modules/teacher/pages/TeacherApiLessonPage.tsx`
and `TeacherApiImportPage.tsx`; tests `modules/teacher/services/__tests__/commandKeys.test.ts`,
`uploadAbort.test.ts`, `modules/teacher/pages/__tests__/TeacherApiLessonPage.stale.test.tsx`.

## Checks (`apps/web`)

- `npm run test`: 12 files / 55 tests pass (before C4: 9 files / 43).
- `npm run lint`: exit 0, 28 warnings (= baseline 28).
- `npm run build`: exit 0.
- Implementation review (Sonnet 5.5 high, subagent): R1 NOT ACCEPTABLE 0 / 1 P2 (stale recovery) / 6 P3; P2 and the
  COMPLETED-recovery P3 fixed; R2 ACCEPTABLE WITH NOTES 0 / 0 / 4 (`tmp/phase-bc/reviews/C4_IMPL_REVIEW_R2.md`).

## Notes

- The upload loop does not track the revision; abort always reads the status first (equivalent, accepted deviation
  from package §4).
- `LessonVersion` is a subset of `LessonVersionV1`; a later B07 control must refetch the lesson for the new revision.
