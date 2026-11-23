# FEAT-066 C-T — Teacher Lesson Library slice package (Draft 4, goal v2 C4)

- **Status:** DRAFT for independent review (round 2). Written by the goal v2 coordinator under the program approval
  (`plan/GOAL_V2_PHASE_BC_PROGRAM_20261119.md`, 13,611 B, SHA-256 `5DFC1EDE…4795F8`). No code before the review
  verdict is READY (WITH NOTES).
- **Date:** 2026-11-19. **Supersedes:** Draft 3 (`PLAN_CT_TEACHER_SLICE_PACKAGE_DRAFT3_20261119.md`, 13,148 B,
  `50ADEB84…`; review R1 NOT READY 0 P1 / 6 P2 / 10 P3, `tmp/phase-bc/reviews/C4_CT_DRAFT3_REVIEW_R1.md`) and Draft 2
  (`PLAN_CT_TEACHER_SLICE_PACKAGE_DRAFT2_20261118.md`, 19,629 B). Both stay as written. §8 maps each R1 finding to
  its fix.
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
   keyed routes. Each service method runs, in this order: (a) load the target row with `FOR UPDATE` (404 if absent);
   (b) `_replay` under that lock, with scope `"<METHOD> <route path with IDs>"` and a fingerprint of the body (if
   any) plus `if_match`; (c) the scope and ownership checks (author or manager; a non-owner gets 404); (d) the
   revision check; (e) the state checks; (f) the change, without its own commit; (g) `_idempotent` writes the
   receipt and commits once. Taking the lock before the replay makes a concurrent duplicate wait and then replay
   (R1-07). Checking ownership before the revision keeps another Teacher's PRIVATE lesson invisible: a non-author
   gets 404 with no `current_version` or `ETag`, never a 409 (R1-04; SRS §9.8 404 row). A retry with the same key and
   the old `If-Match` replays the stored response. School Manager calls of A19 and B08 need the key too. Exception
   to "no own commit": the expiry path (step 4) commits the `EXPIRED` state before raising 410, as today; storage
   purges (`_delete_upload_parts`) run after the commit (R1-12).
2. **Stale revision (C-D7).** `_require_revision` raises a `LessonLibraryError` subclass that carries the current
   revision; `_call` turns it into `raise_stale_revision(current_version=<n>, etag=str(<n>))`. This applies to every
   Lesson Library route that checks `If-Match` (also decision, membership revoke and moderation): one helper, one
   behaviour. Those three keep their own order; decision and moderation already check scope first, membership
   revoke checks ownership first.
3. **A24 complete → 202.** Status code only; body, failures and replay unchanged.
4. **A25 abort → 202 (CT-5, CT-14).** Session `revision` is derived, with no migration: with `n` the number of part
   rows, `1 + n` while the state is `OPEN`, and `2 + n` in every other state (`COMPLETED`, `ABORTED`, `EXPIRED`,
   `FAILED`; the table allows exactly these five). It is monotonic (part rows are never deleted, and
   `put_upload_part` now loads the session `FOR UPDATE`, so no part row lands after a terminal transition, R1-09).
   `UploadSessionV1` gains a required `revision` field; create (201) and GET return it, and also send it as the
   strong `ETag` header (the two routes gain a `Response` parameter). Abort requires the key and `If-Match`, checked
   in this order (R1-08): lock; replay; 404 if not the owner's; then
   - an `OPEN` session past `expires_at` is first marked `EXPIRED` (committed), so its revision moves on;
   - stale `If-Match` → 409 `STALE_REVISION` with the current `ETag`;
   - `OPEN` and current → `ABORTED`, parts purged after the commit, 202 with the session;
   - `ABORTED` and current → 202 with the session, no change (SRS 1658 "idempotent");
   - `COMPLETED` or `FAILED` and current → 409 `UPLOAD_SESSION_STATE_CONFLICT` (SRS 867, invalid transition);
   - `EXPIRED` and current → 410 `UPLOAD_SESSION_EXPIRED` (SRS 868). This is a design choice: SRS 1658 also allows
     reading "idempotent" as 202 for an already expired session; the goal uses the one code the SRS assigns to an
     expired session, and the web treats 410 on abort as "already gone" (§4).
   A stored create receipt from before this change has no `revision`; the service adds `revision: 1` after
   `_idempotent` returns (a new session has no parts). A replayed create may therefore carry an older revision than
   the live session; the web reads status before abort (§4).
4a. **Part upload and complete on a closed session (R1-03).** `_require_upload_open` answers by state, whether the
   state was persisted earlier or set by this request: `EXPIRED` (or `OPEN` past `expires_at`) → 410
   `UPLOAD_SESSION_EXPIRED`; `COMPLETED`, `ABORTED`, `FAILED` → 409 `UPLOAD_SESSION_STATE_CONFLICT`. The complete
   replay for a `COMPLETED` session with a source document stays as it is.
5. **Upload codes (CT-6).** 413 `REQUEST_TOO_LARGE` → `LESSON_FILE_TOO_LARGE` (create, complete and the Lesson
   Library middleware branch); 409 `PART_CONFLICT` → `UPLOAD_PART_CONFLICT`; 409 `UPLOAD_EXPIRED` → 410
   `UPLOAD_SESSION_EXPIRED`; 409 `UPLOAD_INCOMPLETE` → 422 `UPLOAD_INCOMPLETE`; an invalid upload-session transition
   (`_require_upload_open`, abort) → 409 `UPLOAD_SESSION_STATE_CONFLICT`. Each new code gets a Vietnamese message in
   `MESSAGES`; old names stay in `STATUS_MESSAGE_ONLY` while another module still uses them (`REQUEST_TOO_LARGE` is
   still used by `learning_content.py` and the non-Lesson-Library middleware branch; `PART_CONFLICT`,
   `UPLOAD_EXPIRED` and `UPLOAD_INCOMPLETE` by StoryRun Lite). The `LESSON_FILE_TOO_LARGE` message follows SRS 1725
   (supported types and the 25 MB limit; choose another file).
6. **OpenAPI.** Catalog entries of A24 and A25 move their success row to 202; the five keyed operations join
   `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` (11 → 16) and the test's expected set (and its `== 11` assertion); request-
   input text names the new headers in the catalog's form (`header \`Idempotency-Key\`: string`, `header
   \`If-Match\`: object`) so the parameter comparison holds; abort and complete gain 410 and 409 rows where the
   catalog lists errors; A25 joins nothing in the kept-422 set (it raises no 422).
7. **Tests (required edits, R1-01).**
   - `tests/contract/test_http_error_conventions.py::test_lesson_library_part_over_limit_is_413_envelope`: expected
     code `LESSON_FILE_TOO_LARGE`.
   - `tests/contract/test_openapi_contract_catalog.py`: constant size and set.
   - `tests/integration/lesson_library/test_lesson_library_api.py` existing tests: PATCH, DELETE, versions and grant
     revoke calls gain a key (lines about 504-528, 618-624, 754-756, 781-783, 826-828); complete on an incomplete
     session 409 → 422 `UPLOAD_INCOMPLETE` (about 568-573); complete 200 → 202 (about 596-597); abort gains key and
     `If-Match`, 200 → 202 (about 652-654).
   - New integration tests (fake scanner and parser where a complete is needed, so ClamAV is not required): missing
     key → 400; same key and old `If-Match` → replay; other payload → 400 `INVALID_IDEMPOTENCY_KEY`; stale → 409
     with `ETag` and `current_version`; non-author with a stale `If-Match` → 404 without `current_version` or
     `ETag`; complete → 202; every abort row of step 4 including `FAILED`; part PUT and complete on a session
     persisted as `EXPIRED` → 410; `UPLOAD_PART_CONFLICT`; create and GET return `revision` and `ETag`.
   - Unit: the derived revision function for all five states; the stale-revision mapping.
   - Database: a fresh database whose name contains `be1_acceptance` (the fixture refuses any other), on
     `127.0.0.1:55458` (R1-15).
8. **Bruno files** 072, 074, 076, 080 and 086: add the key header (and `If-Match` on 086) with the same placeholder
   style; 088 already has the key (status note only). Not run. `be-full/API_COVERAGE.csv` and
   `be-full/openapi.runtime.json` will show the old statuses and headers; they are an L5 follow-up, not edited here
   (R1-14).

**Allowlist (BE):** `routers/lesson_library.py`; `lesson_library/service.py`; `contracts/schemas/lesson_library.py`;
`middleware/bounded_image_upload.py` (Lesson Library branch only); `error_envelope.py` (message entries only);
`openapi_contract.py` (the four entries and the constant); `openapi_contract_amendments.py` (only if needed);
`tests/integration/lesson_library/test_lesson_library_api.py`; `tests/contract/test_openapi_contract_catalog.py`;
`tests/contract/test_http_error_conventions.py` (the 413 test); one new unit test file; the five Bruno files; this
package and the C4 evidence note. **No migration.**

**Not in C4 (recorded so CT-13 is not read as full coverage, R1-13):** the Parent-group membership revoke DELETE is a
state-changing command with `If-Match` only; its key belongs to MGR-4 / C-M2, not C4. It gets the stale-409 mapping
of step 2 only.

## 4. Web design (one commit on `codex/fe-ui-web-remediation`)

- `backendApi.tsx`: `updateLesson` and `archiveLesson` take an `idempotencyKey` (default `createRequestId()`) and send
  it with `If-Match`; `abortUploadSession(uploadSessionId, revision, idempotencyKey)` sends both headers; new typed
  `createLessonVersion(organizationId, lesson, sourceRevisionId, content, idempotencyKey)` (B07, no page control);
  `LessonUploadSession.revision`; `uploadLessonPart` typed as `UploadPartReceipt`. 202 is a 2xx and needs no change
  (checked in tests).
- **Key lifecycle (R1-05).** A key belongs to one exact command: its signature is (command, organization, target ID,
  the `If-Match` revision sent, payload). The existing `mutationKeys` signature map in `TeacherApiLessonPage.tsx`
  holds it. A retry of the same signature (network error, 5xx, timeout) reuses the key; a new revision (after a 409
  reload) or a changed payload is a new signature and so a new key; the entry is dropped after success.
- `TeacherApiLessonPage.tsx`: save (PATCH) and archive use that map; on 409 `STALE_REVISION` the page reloads the
  lesson and shows the stale message, so the next attempt carries the new revision and a new key.
- `TeacherApiImportPage.tsx` (R1-06): abort reads the session status (GET) first and sends its `revision` as
  `If-Match`, with a key stored in the resume record next to the revision it was made for (`abortKey`,
  `abortRevision`; a record without them, or with another revision, gets a new key). Abort right after a failed
  create uses the create response. Answers: 202 → clear the resume record; 409 `STALE_REVISION` → read status
  again and retry once with a new key; 410 or 409 `UPLOAD_SESSION_STATE_CONFLICT` → refresh the session state from
  status and clear the resume record (the session is already closed). The upload loop also keeps the latest
  `revision` it learns from status reads.
- Messages: the C2 code table gains `LESSON_FILE_TOO_LARGE`, `UPLOAD_PART_CONFLICT`, `UPLOAD_SESSION_EXPIRED`,
  `UPLOAD_INCOMPLETE` and `UPLOAD_SESSION_STATE_CONFLICT`, with the same wording as the BE `MESSAGES` entries (the
  C2 parser shows the server message for CONV-1 bodies; the table is the fallback), R1-16(a).
- Tests: key reuse on retry, new key after a stale reload, abort with status read, abort stale-retry, abort
  410/state-conflict cleanup.
- **Combined verification (R1-16(b)):** after C5 the web branch is merged again into
  `feature/feat066-be-integration` (continuation step), so both commits meet there before D2.
- Tests next to the changed modules; `npm run test`, lint (no new warnings against 28), build.
- **Parked:** the B07 page control (`BLOCKED_OPEN`, CT-15) and the B08 control (G-T1, Draft 2 CT-9).

## 5. Settled answers

Draft 2 CT-1 to CT-12 stay, except CT-11 and CT-12 (queue position and branch), which the program replaces: C4 runs
now on `feature/feat066-be-integration` and `codex/fe-ui-web-remediation`. New:

| ID | Point | Answer | SRS basis |
|---|---|---|---|
| CT-13 | Does `If-Match` alone satisfy §21.4 for lesson PATCH and DELETE? (C1-review open item) | **No.** A state-changing command needs an idempotency key per principal, operation and target (§21.4 first bullet, line 1697; §21.1 line 1636). `If-Match` is the separate expected-revision rule; for lessons its basis is decision C-D7 (§21.4 third bullet, line 1699, names profile, lesson plan, story and script). Both are required | lines 1697, 1636; C-D7 |
| CT-14 | Expected state of DELETE upload session (C1-review open item, line 1658) | Design reading: `If-Match` on the derived session revision is the "expected state/version"; abort is idempotent (replay; repeat on `ABORTED` → 202 unchanged); `COMPLETED` or `FAILED` → 409 `UPLOAD_SESSION_STATE_CONFLICT`; expired → 410 `UPLOAD_SESSION_EXPIRED` | line 1658; §9.8 lines 867–868 |
| CT-15 | B07 page control | `BLOCKED_OPEN`: the API needs a full `LessonContentInputV1`; the SRS does not say how extracted fields become that content or which review UI the Teacher uses, so the goal does not invent it. The typed client method ships | §21.2 line 1653 covers only the later extraction-job route |

## 6. Checks before the commits

BE: ruff and mypy on the touched files (0 new); `pytest tests/unit tests/contract` in a clean environment, failing
ids compared with `tmp/be-integration/fail_ids.txt` (0 new); the Lesson Library PostgreSQL test on a fresh database
whose name contains `be1_acceptance`, on `127.0.0.1:55458` (never `sketch2life_m2_s1a`, never 5432 or 5433); the four validators; `git diff --check`; the
security validator again before the commit. Web: fetch `origin/codex/fe-ui-web-remediation` first; tests, lint,
build. Implementation review (Sonnet 5.5 high) before each commit.

## 7. Breaking change window

Between the BE commit and the web merge, the current web client gets 400 on lesson save, archive and abort (no key).
Both commits stay local; the owner pushes them together.

## 8. Review R1 findings and their fixes

| Finding | Fix in Draft 4 |
|---|---|
| C4-R1-01 (P2) 413 contract test and known test edits | §3 step 7 lists them as required edits; allowlist names the 413 test |
| C4-R1-02 (P2) `FAILED` state | §3 step 4: `2 + n` in every non-`OPEN` state; abort of `FAILED` → 409 `UPLOAD_SESSION_STATE_CONFLICT`; unit test for five states |
| C4-R1-03 (P2) persisted `EXPIRED` → 410 | §3 step 4a; integration cases for part PUT and complete |
| C4-R1-04 (P2) revision leak to a non-author | §3 step 1: ownership before revision; 404 test without `current_version` and `ETag` |
| C4-R1-05 (P2) web key lifecycle | §4 key signature includes the revision; new key after a stale reload |
| C4-R1-06 (P2) web abort stale revision | §4: status read before abort; stale retry once; 410 / state-conflict cleanup |
| C4-R1-07 (P3) concurrent duplicate | §3 step 1: lock, then replay |
| C4-R1-08 (P3) abort precedence, 410 choice | §3 step 4 order; 410 recorded as a design choice |
| C4-R1-09 (P3) unlocked part insert | §3 step 4: `put_upload_part` loads `FOR UPDATE` |
| C4-R1-10 (P3) citation | CT-13 cites line 1636 and C-D7 |
| C4-R1-11 (P3) receipt `revision` and `Response` | §3 step 4 |
| C4-R1-12 (P3) expiry-path commit | §3 step 1 exception |
| C4-R1-13 (P3) membership revoke key | §3 "Not in C4" |
| C4-R1-14 (P3) Bruno 088, coverage files | §3 step 8 |
| C4-R1-15 (P3) database name | §3 step 7 and §6 |
| C4-R1-16 (P3) copy and merge path | §3 step 5 and §4 |
