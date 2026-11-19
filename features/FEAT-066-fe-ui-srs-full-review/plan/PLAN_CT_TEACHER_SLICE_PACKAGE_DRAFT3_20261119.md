# FEAT-066 C-T — Teacher Lesson Library slice package (Draft 3, goal v2 C4)

- **Status:** DRAFT for independent review. Written by the goal v2 coordinator under the program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, 13,611 B, SHA-256 `5DFC1EDE…4795F8`). No code before the review
  verdict is READY (WITH NOTES).
- **Date:** 2026-11-19. **Supersedes:** Draft 2 (`PLAN_CT_TEACHER_SLICE_PACKAGE_DRAFT2_20261118.md`, 19,629 B,
  unreviewed by the goal). Draft 2 stays as written.
- **Why a new draft:** Draft 2 was written against BE `2dddc607` and web `297a28b1`, as its own branch after Billing
  B-1. The program (row C4) runs it now on the integration branch; A16 is already built (`4318b190`); and two items
  that the C1 review left open belong here (§5, CT-13 and CT-14).

## 1. Scope

| Row | Endpoint (`/api/lesson-library/v1`) | Today (this base) | Target |
|---|---|---|---|
| A18 | PATCH `/organizations/{organization_id}/lessons/{lesson_id}` | `If-Match` only; Teacher author | `If-Match` **and** `Idempotency-Key` |
| A19 | DELETE `/organizations/{organization_id}/lessons/{lesson_id}` (archive; Teacher author or School Manager) | `If-Match` only | `If-Match` and key |
| B07 | POST `/organizations/{organization_id}/lessons/{lesson_id}/versions` | `If-Match` only; no web caller | `If-Match` and key; typed web client method |
| B08 | DELETE `/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}` (Teacher granter or School Manager) | `If-Match` only; no web caller | `If-Match` and key (BE only) |
| A24 | POST `/upload-sessions/{upload_session_id}/complete` | 200; keyed | 202; body unchanged |
| A25 | DELETE `/upload-sessions/{upload_session_id}` | 200; no key; no precondition | 202; key; `If-Match` on the session revision |
| Upload codes | create, part, complete, abort, Lesson Library 413 middleware branch | `REQUEST_TOO_LARGE`, `PART_CONFLICT`, 409 `UPLOAD_EXPIRED`, 409 `UPLOAD_INCOMPLETE`, 409 `INVALID_TRANSITION` | SRS §9.8 names (CT-6) |
| Stale 409 | every Lesson Library `If-Match` route | 409 `STALE_REVISION` without the current version | 409 `STALE_REVISION` with `current_version` and the current strong `ETag` (C-D7) |

Not in scope: A16 (done, `4318b190`); A21 path (C-D9 interim mapping, record only); C01/G03, G14, G-T1, C-T5 (as in
Draft 2 §4, unchanged); the School Manager web screens; Bruno runs (B2 deferred: request files are edited, not run).

## 2. Source facts (checked on BE `63363081`, web `7e416725`)

1. Router `interfaces/http/routers/lesson_library.py`: keyed routes declare
   `Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=128)] = ...`; a missing key is a
   validation error that the CONV-1 handler answers as 400 `INVALID_REQUEST` with field error
   `Idempotency-Key`/`REQUIRED`. `_strong_revision()` gives 400 for a missing or malformed `If-Match`.
2. Service `infrastructure/lesson_library/service.py`: `_replay` (same key and fingerprint → stored response; other
   fingerprint → 400 `INVALID_IDEMPOTENCY_KEY`) and `_idempotent` (execute, write the receipt, commit once) exist;
   `decide_access_grant` and `moderate_lesson` already run replay → revision check → execute → receipt.
   `update_lesson`, `archive_lesson`, `create_lesson_version`, `revoke_access_grant` and `abort_upload_session`
   commit inside the method and take no key.
3. `_require_revision` raises `LessonLibraryError(409, "STALE_REVISION")`; the router `_call` drops everything but
   code and message. `api_conventions.raise_stale_revision()` exists; the CONV-1 handler keeps `current_version`
   (int) for `STALE_REVISION` and passes exception headers through.
4. Upload sessions have no stored revision (`tables.py`); `_delete_upload_parts` deletes storage objects only, the
   `upload_parts` rows stay. `UploadSessionV1` has no `revision` field.
5. `complete_upload` is synchronous: success is the terminal source-document status (`READY_FOR_REVIEW`).
6. `error_envelope.py`: codes in `MESSAGES` get their own message; `STATUS_MESSAGE_ONLY` lists kept codes; a coverage
   test fails on a code literal in neither set. `PART_CONFLICT`, `UPLOAD_EXPIRED`, `UPLOAD_INCOMPLETE` and
   `REQUEST_TOO_LARGE` are in `STATUS_MESSAGE_ONLY`.
7. OpenAPI: `openapi_contract.MOUNTED_OPERATIONS` overrides the runtime responses; `IDEMPOTENCY_MISMATCH_OPERATION_KEYS`
   has 11 entries and its test (`tests/contract/test_openapi_contract_catalog.py`) pins the size and the set;
   `openapi_contract_amendments.LESSON_LIBRARY_KEPT_422_OPERATIONS` lists part upload and complete.
8. Middleware `interfaces/http/middleware/bounded_image_upload.py` answers the Lesson Library 413 with
   `REQUEST_TOO_LARGE` ("until the C-T slice").
9. Web `shared/api/backendApi.tsx`: `updateLesson` and `archiveLesson` send only `If-Match`; `abortUploadSession`
   sends nothing; `completeUpload` is keyed; there is no `createLessonVersion` or `revokeAccessGrant` method.
   `TeacherApiImportPage.tsx` keeps `createKey` and `completeKey` in its resume record and calls abort in two places.
   The import page tells the Teacher that no version is created from the extraction yet (line 416).
10. Bruno request files 072, 074, 076, 080, 086 and 088 exist (tracked) for these routes.

## 3. BE design (one commit on `feature/feat066-be-integration`)

1. **Keys (CT-2, CT-13).** A18, A19, B07, B08 and A25 declare the required `Idempotency-Key` header like the other
   keyed routes. Each service method runs: (a) `_replay` with scope `"<METHOD> <route path with IDs>"` and a
   fingerprint of the body (if any) plus `if_match`; (b) load with `FOR UPDATE` and the revision check; (c) the
   change, without its own commit; (d) `_idempotent` writes the receipt and commits once. A retry with the same key
   and the old `If-Match` replays the stored response instead of failing with 409. School Manager calls of A19 and
   B08 need the key too (same routes).
2. **Stale revision (C-D7).** `_require_revision` raises a `LessonLibraryError` subclass that carries the current
   revision; `_call` turns it into `raise_stale_revision(current_version=<n>, etag=str(<n>))`. This applies to every
   Lesson Library route that checks `If-Match` (also decision, membership revoke and moderation): one helper, one
   behaviour.
3. **A24 complete → 202.** Status code only; body, failures and replay unchanged.
4. **A25 abort → 202 (CT-5, CT-14).** Session `revision` is derived, with no migration: `1 + number of accepted
   part rows` while `OPEN`, that value `+ 1` once `COMPLETED`, `ABORTED` or `EXPIRED`. It is monotonic (part rows
   are never deleted). `UploadSessionV1` gains a required `revision` field; create (201) and GET return it, and also
   send it as the strong `ETag` header. Abort requires the key and `If-Match`:
   - same key and fingerprint → the stored 202 response;
   - stale `If-Match` → 409 `STALE_REVISION` with the current `ETag`;
   - `OPEN` and current → `ABORTED`, parts purged, 202 with the session;
   - already `ABORTED` and current → 202 with the session, no change (SRS 1658 "idempotent");
   - `COMPLETED` → 409 `UPLOAD_SESSION_STATE_CONFLICT`;
   - `EXPIRED`, or `OPEN` past `expires_at` → 410 `UPLOAD_SESSION_EXPIRED` (the session is marked `EXPIRED`).
   A stored create receipt from before this change has no `revision`; its replay adds `revision: 1` (a new session
   has no parts).
5. **Upload codes (CT-6).** 413 `REQUEST_TOO_LARGE` → `LESSON_FILE_TOO_LARGE` (create, complete and the Lesson
   Library middleware branch); 409 `PART_CONFLICT` → `UPLOAD_PART_CONFLICT`; 409 `UPLOAD_EXPIRED` → 410
   `UPLOAD_SESSION_EXPIRED`; 409 `UPLOAD_INCOMPLETE` → 422 `UPLOAD_INCOMPLETE`; an invalid upload-session transition
   (`_require_upload_open`, abort) → 409 `UPLOAD_SESSION_STATE_CONFLICT`. Each new code gets a Vietnamese message in
   `MESSAGES`; old names stay in `STATUS_MESSAGE_ONLY` only while another module still uses them.
6. **OpenAPI.** Catalog entries of A24 and A25 move their success row to 202; the five keyed operations join
   `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` (11 → 16) and the test's expected set; request-input text names the new
   headers; the new 410 and 409 rows on abort; A25 joins nothing in the kept-422 set (it raises no 422).
7. **Tests.** Unit: the derived revision function; the stale-revision mapping (current version and `ETag`).
   Contract: catalog constant and set; error-message coverage stays green. PostgreSQL integration
   (`tests/integration/lesson_library/test_lesson_library_api.py`, fresh database on the `frc08` container): missing
   key → 400; same key and old `If-Match` → replay; other payload → 400 `INVALID_IDEMPOTENCY_KEY`; stale → 409 with
   `ETag` and `current_version`; complete → 202; abort cases of step 4; the upload codes; existing tests updated for
   the new headers and codes.
8. **Bruno files** 072, 074, 076, 080, 086 and 088: add the key header (and `If-Match` on 086) with the same
   placeholder style; not run.

**Allowlist (BE):** `routers/lesson_library.py`; `lesson_library/service.py`; `contracts/schemas/lesson_library.py`;
`middleware/bounded_image_upload.py` (Lesson Library branch only); `error_envelope.py` (message entries only);
`openapi_contract.py` (the four entries and the constant); `openapi_contract_amendments.py` (only if needed);
`tests/integration/lesson_library/test_lesson_library_api.py`; `tests/contract/test_openapi_contract_catalog.py`;
`tests/contract/test_http_error_conventions.py` (only if a catalog assertion moves); one new unit test file; the six
Bruno files; this package, its review reports' pointers and the C4 evidence note. **No migration.**

## 4. Web design (one commit on `codex/fe-ui-web-remediation`)

- `backendApi.tsx`: `updateLesson` and `archiveLesson` take an `idempotencyKey` (default `createRequestId()`) and send
  it with `If-Match`; `abortUploadSession(uploadSessionId, revision, idempotencyKey)` sends both headers; new typed
  `createLessonVersion(organizationId, lesson, sourceRevisionId, content, idempotencyKey)` (B07, no page control);
  `LessonUploadSession.revision`; `uploadLessonPart` typed as `UploadPartReceipt`. 202 is a 2xx and needs no change
  (checked in tests).
- `TeacherApiLessonPage.tsx`: one key per logical save or archive command, kept for a retry of the same command and
  replaced after success or after the Teacher changes the content.
- `TeacherApiImportPage.tsx`: the resume record gains `abortKey` (old records without it are read with a new key);
  abort sends the session's current `revision` (from the latest status read or the create response).
- Messages: the C2 code table gains `LESSON_FILE_TOO_LARGE`, `UPLOAD_PART_CONFLICT`, `UPLOAD_SESSION_EXPIRED`,
  `UPLOAD_INCOMPLETE` and `UPLOAD_SESSION_STATE_CONFLICT` (Vietnamese), used only when the server message is not
  trusted.
- Tests next to the changed modules; `npm run test`, lint (no new warnings against 28), build.
- **Parked:** the B07 page control (`BLOCKED_OPEN`, CT-15) and the B08 control (G-T1, Draft 2 CT-9).

## 5. Settled answers

Draft 2 CT-1 to CT-12 stay, except CT-11 and CT-12 (queue position and branch), which the program replaces: C4 runs
now on `feature/feat066-be-integration` and `codex/fe-ui-web-remediation`. New:

| ID | Point | Answer | SRS basis |
|---|---|---|---|
| CT-13 | Does `If-Match` alone satisfy §21.4 for lesson PATCH and DELETE? (C1-review open item) | **No.** A state-changing command needs an idempotency key per principal, operation and target, and `If-Match` is the separate expected-revision rule; both are required | §21.4 first and third bullets (lines 1697, 1699); §21.1 line 1639 |
| CT-14 | Expected state of DELETE upload session (C1-review open item, line 1658) | `If-Match` on the derived session revision is the "expected state/version"; abort is idempotent (replay; repeat on `ABORTED` → 202 unchanged); `COMPLETED` → 409 `UPLOAD_SESSION_STATE_CONFLICT`; expired → 410 `UPLOAD_SESSION_EXPIRED` | line 1658; §9.8 lines 867–868 |
| CT-15 | B07 page control | `BLOCKED_OPEN`: the API needs a full `LessonContentInputV1`; the SRS does not say how extracted fields become that content or which review UI the Teacher uses, so the goal does not invent it. The typed client method ships | §21.2 line 1653 covers only the later extraction-job route |

## 6. Checks before the commits

BE: ruff and mypy on the touched files (0 new); `pytest tests/unit tests/contract` in a clean environment, failing
ids compared with `tmp/be-integration/fail_ids.txt` (0 new); the Lesson Library PostgreSQL test on a fresh database
on `127.0.0.1:55458` (never `sketch2life_m2_s1a`, never 5432 or 5433); the four validators; `git diff --check`; the
security validator again before the commit. Web: fetch `origin/codex/fe-ui-web-remediation` first; tests, lint,
build. Implementation review (Sonnet 5.5 high) before each commit.

## 7. Breaking change window

Between the BE commit and the web merge, the current web client gets 400 on lesson save, archive and abort (no key).
Both commits stay local; the owner pushes them together.
