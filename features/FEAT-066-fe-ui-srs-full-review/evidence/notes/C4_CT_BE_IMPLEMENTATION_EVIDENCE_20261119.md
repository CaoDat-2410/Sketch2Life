# C4 C-T — Teacher Lesson Library BE slice, implementation evidence (goal v2)

- **Date:** 2026-11-19. **Task:** goal v2 row C4, the rest after A16 (`4318b190`): A18, A19, B07, B08, A24, A25 and the
  upload codes. Accepted by the goal under program approval (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`,
  13,611 B, SHA-256 `5DFC1EDE…4795F8`); owner final check pending. Nothing pushed.
- **Package:** `plan/PLAN_CT_TEACHER_SLICE_PACKAGE_DRAFT4_20261119.md` (20,112 B, SHA-256 `1A199C40…`). Reviews
  (Sonnet 5.5, effort high, fresh non-forked subagent, because starting a session was refused on this automated
  turn): Draft 3 R1 NOT READY 0 P1 / 6 P2 / 10 P3; Draft 4 R2 READY WITH NOTES 0 / 0 / 4. Reports:
  `tmp/phase-bc/reviews/C4_CT_DRAFT3_REVIEW_R1.md`, `C4_CT_DRAFT4_REVIEW_R2.md`.

## Decisions taken by the goal (SRS D-209 copy, 701,157 B)

| ID | Decision | SRS clause |
|---|---|---|
| CT-13 | `If-Match` alone does not satisfy §21.4: lesson PATCH and DELETE, version create, grant revoke and upload abort require an `Idempotency-Key` as well as `If-Match` | §21.4 line 1697; §21.1 line 1636; decision C-D7 for the lesson precondition |
| CT-14 | DELETE upload session: `If-Match` on the derived session revision is the expected state/version; idempotent (replay; repeat on `ABORTED` → 202); `COMPLETED`/`FAILED` → 409 `UPLOAD_SESSION_STATE_CONFLICT`; expired → 410 `UPLOAD_SESSION_EXPIRED` | line 1658; §9.8 lines 867–868 |
| CT-5 | Session revision derived without a migration: `1 + parts` while `OPEN`, `2 + parts` otherwise; body field `revision` and strong `ETag` on create and GET | line 1658; C-D7 |
| CT-3 | Complete and abort answer 202 (status only) | lines 1657–1658 |
| CT-6 | Upload codes: `LESSON_FILE_TOO_LARGE`, `UPLOAD_PART_CONFLICT`, 410 `UPLOAD_SESSION_EXPIRED`, 422 `UPLOAD_INCOMPLETE`, 409 `UPLOAD_SESSION_STATE_CONFLICT` | §9.8 lines 867–871; line 1725 |
| C-D7 | Every Lesson Library stale 409 carries `current_version` and the strong `ETag` | §21.4 line 1699; C-D7 |
| CT-15 | B07 page control `BLOCKED_OPEN` (no SRS rule maps extracted fields to `LessonContentInputV1`) | line 1653 covers only the later extraction-job route |

## What changed (BE)

- `routers/lesson_library.py`: key header on A18, A19, B07, B08, A25 (`IdempotencyKeyHeader` alias); A25 takes
  `If-Match`; complete and abort return 202; create and GET upload session set the `ETag`; `_call` maps the stale
  error to `raise_stale_revision(current_version, etag)`.
- `lesson_library/service.py`: lock → replay → ownership → revision → state → change → one commit, for the five
  commands; `LessonLibraryStaleRevision`; `upload_session_revision()`; `_expire_if_due()` with an `OPEN` guard
  (R2-02); `_upload_status()`; `put_upload_part` locks the session (R1-09); `_require_upload_open` answers by state
  (R1-03); upload codes.
- `schemas/lesson_library.py`: `UploadSessionV1.revision`. `error_envelope.py`: five messages (Vietnamese);
  `UPLOAD_INCOMPLETE` moved from `STATUS_MESSAGE_ONLY` to `MESSAGES`. Middleware: Lesson Library 413 code
  `LESSON_FILE_TOO_LARGE`.
- `openapi_contract.py`: four request-input texts, abort and complete success rows 202, five keys in
  `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` (11 → 16). Tests: catalog set and size, the 413 contract test, existing
  integration tests updated, three new integration tests, new unit test file. Bruno 072, 074, 076, 080, 086 headers.

## Checks

- `pytest tests/unit tests/contract` in a clean environment (no database variables), twice: 8,557 tests; 83 failing or
  erroring ids, identical to `tmp/be-integration/fail_ids.txt` (0 new).
- Fresh database `frc08_be1_acceptance_c4_20261119165649` on `127.0.0.1:55458` (`alembic upgrade heads` exit 0):
  `tests/integration/lesson_library` 12 pass, 1 fail — `test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http`
  (503, needs ClamAV; known failure at the base). The C4 complete test uses a synthetic scanner and parser.
- Ruff on the touched files: 59 findings against 64 at the base (0 new). Mypy (`--follow-imports=silent`) on the five
  touched source files: 102 errors against 103 at the base (0 new).
- Focused contract and unit files (catalog, error conventions, envelope, C4 revisions): pass.
- Implementation review R1 (Sonnet 5.5 high, subagent): NOT ACCEPTABLE 0 P1 / 1 P2 (web stale recovery) / 6 P3;
  the P2 and P3-02, -03, -04 (part), -05 were fixed; see `tmp/phase-bc/reviews/C4_IMPL_REVIEW_R1.md`.
- Implementation review R2 (same reviewer): ACCEPTABLE WITH NOTES 0 P1 / 0 P2 / 4 P3
  (`tmp/phase-bc/reviews/C4_IMPL_REVIEW_R2.md`).

## Findings and limits recorded (not fixed here)

- **Missing key on older keyed routes reports `INVALID_FORMAT`, not `REQUIRED`.** On this FastAPI version an
  `Annotated[str, Header(...)] = ...` parameter gets `Ellipsis` as its default, so a missing header fails as
  `string_type` and `field_errors_from_validation` answers `Idempotency-Key`/`INVALID_FORMAT`. The C4 routes (A18, A19,
  B07, B08, A25) and create upload session now declare the key without a default and answer `REQUIRED`; the other
  keyed Lesson Library routes (A24 complete, decision, moderation, grant create, group and invitation commands) keep
  the old declaration. Follow-up for C-T5/CONV-1.
- The PDF upload test needs ClamAV and `pypdf`, neither available here; the new C4 test uses a synthetic scanner and
  parser to reach the complete path.
- `be-full/API_COVERAGE.csv` and `be-full/openapi.runtime.json` still show the old statuses and headers (L5 follow-up).
- Parent-group membership revoke stays unkeyed (MGR-4 / C-M2), with the new stale mapping only.
- Reload on a stale save is manual on the web (R2-01): the form keeps the Teacher's text.
- The row lock in `put_upload_part` is held across the storage write (R2-04); acceptable for one uploader.
