# FEAT-066 C-T — Teacher per-role slice package (Draft 2)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package plans Phase C work for the Teacher web role only. It authorizes no code, migration, test, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 1 (14,777 B, `2E994E20…`). Its round-1 review was NOT READY with 0 P1, 6 P2 and 6 P3 (`evidence/notes/CT_COLD_REVIEW_DRAFT1_20261118.md`). §9 maps each finding to its fix.
- **What C-T is:** roadmap Draft 4 §4 row C for the Teacher, and register Draft 4 §5 row "C-T": rows A16, A18, A19, A21, A23, A24, A25, B07, B08, C01 and gaps G03, G14. The Teacher rows shared with the School Manager (A07, A09, A10) are in C-M1 (D-066-75). It also takes the items CONV-1 deferred to C-T (CONV-1 Draft 5 deferred-items table and item 2b).
- **Owner delegation:** on 2026-11-18 the owner asked that package questions be settled from the SRS rather than asked one by one. §6 lists the settled answers with their basis; the owner can override any of them when approving the package.
- **NEW in this package:** the sub-slice names C-T1 to C-T5; the settled answers CT-1 to CT-12; the upload-session `revision` field and its `ETag`; the required `Idempotency-Key` on A18, A19, B07, B08 and abort; the 202 status on complete and abort; the stale-409 `ETag` and `current_version` on the C-T1 routes; the upload error codes of §4; the FE "create version" and the deferred grant-revoke control; gap G-T1.

## 1. Authority and inputs

| Input | Location | Bytes | SHA-256 (prefix) |
|---|---|---:|---|
| Working SRS (D-209, D-066-64) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D…` |
| Mismatch register Draft 4 | `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md` (git-ignored) | 41,798 | `0F3F35FD…` |
| Roadmap Draft 4 | `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md` | 42,628 | `63710A9F…` |
| CONV-1 package Draft 5 (D-066-71) | `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT5_20261118.md` | 47,483 | `3FCF4741…` |
| C-M package Draft 4 (D-066-75) | `plan/PLAN_CM_SCHOOL_MANAGER_SLICE_PACKAGE_DRAFT4_20261118.md` | 28,716 | `401E8935…` |
| Decisions (conv1 worktree, uncommitted appends D-066-72 to D-066-76) | `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md` | 68,171 | `E615C3BF…` |

Decisions used: D-066-62; D-066-68 (C-D4 404/403, C-D5 `Idempotency-Key`, C-D7 strong `If-Match`/`ETag` for Lesson Library and stale → 409 `STALE_REVISION` with the current version or `ETag`, C-D8 paging, C-D9 interim paths); D-066-69; D-066-71 (CONV-1 built, with its deferrals); D-066-73, D-066-75 and D-066-76 (queue).

**BE source base:** commit `2dddc607` (CONV-1, local-only branch `feature/feat066-conv1`), which contains S-LL (MGR-7, MGR-8; G0 closed at `08439b22`). **FE source base:** `.worktrees/ui`, branch `codex/fe-ui-web-remediation` at `297a28b1`. Source facts below were checked by the round-1 review.

**SRS clauses used:** 798 (`/v1/lessons` family); 867–871 (§9.8 codes: 409 `UPLOAD_PART_CONFLICT` and `UPLOAD_SESSION_STATE_CONFLICT`, 410 `UPLOAD_SESSION_EXPIRED`, 413 `LESSON_FILE_TOO_LARGE`, 422 `UPLOAD_INCOMPLETE`); 1217 (OI-05); 1640 (paging); 1651 (Teacher profile create); 1653 (lesson documents → 202 extraction job); 1654–1658 (upload sessions; complete and abort → 202; abort "Expected state/version; idempotent"); 1697–1699 (§21.4); 1725 (`LESSON_FILE_TOO_LARGE` UX); FR-PL-03 to FR-PL-06 (2449–2452, 2644–2647).

## 2. What is already true (2026-11-18)

| Fact | Effect on C-T |
|---|---|
| G0 closed; CONV-1 built (local) | §9.8 envelope on `/api/lesson-library/v1`; missing `If-Match` → 400; `limit_query()` and `raise_stale_revision()` exist |
| MGR-7 built | Lesson Library receipts: same key and payload → replay; different payload → 400 `INVALID_IDEMPOTENCY_KEY`; the mechanism (`_idempotent`, `_replay`) lives in `infrastructure/lesson_library/service.py` |
| **Lesson PATCH already creates an immutable version** (`service.py` 209–244: `_insert_version` with the next `version_no`, then `current_version_id` repointed) | Settles the register NV for A18 (FR-PL-03, §31.2) |
| Upload complete is synchronous (`service.py` 760–955: assemble, scan, parse, store); success is terminal `READY_FOR_REVIEW`; failures are 4xx or 5xx | The 202 of SRS 1657 is a status change only here (CT-3) |
| Upload sessions have **no stored revision** (`tables.py` 58–83); the router accepts an `ETag` of `"<positive int>"` only (`lesson_library.py` line 54) | C-T1 derives a revision without a migration (CT-5) |
| A19 and B08 use the `_staff` guard (School Manager and Teacher); no School Manager web caller | The new key requirement applies to both roles (CT-2) |
| No Teacher route lists a lesson's access grants (`list_access_grants` is School-Manager-only) | A grant-revoke control cannot find grant IDs; recorded as gap G-T1 (CT-9) |
| Teacher profile create (C01) is always mounted; it returns 409 `SYNTHETIC_PROFILE_CREATION_UNAVAILABLE` unless `env` is `local` or `test` and `synthetic_pilot_enabled` is set (`be1_registry.py` 399–421) | A production route needs the consent source (OI-05), which is open |
| The FE already pages lessons with `cursor` (`TeacherApiLessonPage.tsx` 125, `TeacherApiImportPage.tsx` 145) | No FE paging work for A16 |

## 3. Row map (BE `2dddc607`, web `297a28b1`)

| Row | Endpoint | Today | Target | Sub-slice |
|---|---|---|---|---|
| A16 | GET `/api/lesson-library/v1/organizations/{organization_id}/lessons` | default 50, max 100; order `updated_at` desc, `lesson_id` desc | default 25 (CT-1) | C-T1 |
| A18 | PATCH `…/lessons/{lesson_id}` | `If-Match`, no key; creates a new version | key required; stale 409 with `ETag` | C-T1 |
| A19 | DELETE `…/lessons/{lesson_id}` (archive; `_staff`) | `If-Match`, no key | key required; stale 409 with `ETag` | C-T1 |
| B07 | POST `…/lessons/{lesson_id}/versions` | no key; needs a `READY_FOR_REVIEW` source revision; no FE caller | key required; FE control on the import page | C-T1 |
| B08 | DELETE `…/lessons/{lesson_id}/access-grants/{access_grant_id}` (`_staff`) | no key; no FE type | key required (BE); FE control deferred (G-T1) | C-T1 (BE) |
| A24 | POST `/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete` | 200; keyed | 202, body unchanged (CT-3) | C-T1 |
| A25 | DELETE `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | 200; no key; no precondition | 202; key; `If-Match` on the derived session revision (CT-5) | C-T1 |
| A23 | PUT `…/upload-sessions/{upload_session_id}/parts/{part_number}` | BE matches the SRS; FE response untyped | FE types `UploadPartReceiptV1` | C-T1 (FE) |
| Upload codes | complete, part, abort, the 413 middleware branch | `REQUEST_TOO_LARGE`, `PART_CONFLICT`, `UPLOAD_EXPIRED` 409, `UPLOAD_INCOMPLETE` 409, `INVALID_TRANSITION` 409 | SRS 867–871 codes (CT-6) | C-T1 |
| A21 | POST `…/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` | path differs from SRS 1654 | keep as the C-D9 interim mapping (CT-4) | C-T2 (record only) |
| C01 / G03 | Teacher profile create | synthetic only | deferred (CT-7) | C-T3 |
| G14 | Teacher occurrence, plan, sample/run, lifecycle (FR-T-08 to FR-T-17), plus the SRS 1653 extraction-job endpoint | absent | separate planning (CT-8) | C-T4 |
| G-T1 (NEW) | Teacher read of the access grants of an own lesson | absent | planned with C-T4 or C-M2 (CT-9) | — |
| Remainder | Lesson Library and Teacher AI domain 422 codes, Teacher AI request-ID logging and OpenAPI errors, `assistance_requests.py` envelope, ClamAV (CONV-1 deferrals) | unchanged | C-T5 (CT-10) | C-T5 |

**Web callers:** `shared/api/backendApi.tsx` (all Lesson Library methods), used by `modules/teacher/pages/TeacherApiLessonPage.tsx`, `TeacherApiImportPage.tsx` and `TeacherWorkbenchPage.tsx`. `apps/ui-mobile` calls only `/me` routes and is not affected.

## 4. Sub-slices

### C-T1 — Lesson Library conventions and upload codes for the Teacher

**BE part (one Task Approval, one commit):**

1. **A16:** `list_lessons` uses `limit_query()` (default 25, max 100; above 100 → 400); the existing order stays.
2. **Keys on A18, A19, B07, B08 and abort:** each service method (`update_lesson`, `archive_lesson`, `create_lesson_version`, `revoke_access_grant`, and the upload abort) takes the `Idempotency-Key` (C-D5) and follows the `decide_access_grant` pattern (`service.py` 1180–1240), in this order: (a) replay check — same key and fingerprint → the stored original response; same key, other fingerprint → 400 `INVALID_IDEMPOTENCY_KEY`; (b) revision check; (c) execute; (d) write the receipt and commit once. The fingerprint covers the target IDs, the `If-Match` value and the request body. A retry with the same key and an old `If-Match` therefore replays instead of failing with 409. A missing key → 400 `INVALID_REQUEST` with field error `Idempotency-Key` / `REQUIRED` (CONV-1 rule). The requirement applies to School Manager calls of A19 and B08 too (`_staff`). **Breaking change** for callers that send no key.
3. **Stale revisions (C-D7, the Lesson Library item CONV-1 deferred):** on A18, A19, B07, B08 and abort, a stale `If-Match` gives 409 `STALE_REVISION` through `raise_stale_revision()`, with the current strong `ETag` header and `current_version` in the envelope. The School-Manager-only decision route stays with C-M2.
4. **A24 complete → 202:** status code only. The body stays the source-document status (terminal `READY_FOR_REVIEW` on success); failures stay 4xx or 5xx; there is no polling and no non-terminal state. A replay returns the same 202. The SRS 1653 extraction job is not in C-T1 (C-T4).
5. **A25 abort → 202, keyed and preconditioned (CT-5):** the session `revision` is **derived, with no migration**: `1 + accepted part count` while the session is `OPEN`; that value `+ 1` once it is `COMPLETED`, `ABORTED` or `EXPIRED`. It is monotonic and changes whenever the parts or the state change. `UploadSessionV1` gains a `revision` field (**NEW**), and create (201) and GET return it as the strong `ETag` header too. Abort requires `If-Match` with that value and a key; a stale value → 409 `STALE_REVISION` with the current `ETag`; abort of a session that is no longer `OPEN` → 409 `UPLOAD_SESSION_STATE_CONFLICT`.
6. **Upload and file codes (CT-6, CONV-1 item 2b):** the lesson-upload 413 code `REQUEST_TOO_LARGE` → `LESSON_FILE_TOO_LARGE` (route and the Lesson Library branch of `bounded_image_upload.py`); `PART_CONFLICT` → 409 `UPLOAD_PART_CONFLICT`; `UPLOAD_EXPIRED` 409 → 410 `UPLOAD_SESSION_EXPIRED`; `UPLOAD_INCOMPLETE` 409 → 422 `UPLOAD_INCOMPLETE`; an invalid upload-session lifecycle transition → 409 `UPLOAD_SESSION_STATE_CONFLICT`. Each new code gets a safe Vietnamese message in the CONV-1 message set.
7. **OpenAPI:** status codes, required headers, the `revision` field, the new codes and examples, through `openapi_contract.py` and its amendments module; the `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` constant (about `openapi_contract.py` line 11230) grows by the five keyed operations.

**Proposed allowlist (exact paths fixed in the C-T1 Task Approval):** `interfaces/http/routers/lesson_library.py`; `infrastructure/lesson_library/service.py` (the five methods above, the upload-session revision and the upload codes); `contracts/schemas/lesson_library.py`; `interfaces/http/bounded_image_upload.py` (the Lesson Library 413 code only); `interfaces/http/error_envelope.py` (message entries only); `interfaces/http/openapi_contract.py` and `openapi_contract_amendments.py`; `tests/integration/lesson_library/test_lesson_library_api.py`; `tests/contract/test_openapi_contract_catalog.py` (the constant's size and set, lines about 42 and 498–501); `tests/contract/test_http_error_conventions.py` (kept green; edited only if a catalog assertion moves); Lesson Library unit tests; Bruno requests 070, 072, 074, 076, 080, 086, 087, 088 and 089 (L5 per-slice update); the C-T1 evidence note. **No migration.**

**Checks:** contract catalog; unit tests (derived revision, fingerprint, ordering); the Lesson Library PostgreSQL integration test on a disposable database whose name contains `be1_acceptance` (never `sketch2life_m2_s1a`, never ports 5432 or 5433), **run by the owner**; repository validators.

**FE part (one Task Approval, after the BE part is verified and the web branch is reconciled, O-9; after C-M1 FE):**
- `shared/api/backendApi.tsx`: send `Idempotency-Key` on lesson PATCH and DELETE, version create and upload abort (the same key for a retry of the same command); send `If-Match` on abort from `UploadSessionV1.revision`; accept 202 on complete and abort; type `UploadSessionV1.revision`, `UploadPartReceiptV1` and the version response; map the new upload codes.
- `TeacherApiImportPage.tsx`: persist the abort key in the upload resume record next to `createKey` and `completeKey`; a **"create version"** control (B07) after the extraction preview, where it now shows "Chưa tạo phiên bản giáo án từ bản trích xuất", enabled only for a `READY_FOR_REVIEW` source revision.
- `TeacherApiLessonPage.tsx`: no new control; the grant-revoke control waits for G-T1.
- Tests next to each changed module.

**BE-before-FE window:** local development only. Between the commits, lesson PATCH and DELETE and upload abort from the current web helper fail with 400 (missing key), and lists show 25 items.

**Acceptance:** each keyed command refuses a missing key, replays the same key (also with an old `If-Match`), and answers stale 409 with the current `ETag` and `current_version`; complete and abort answer 202; abort works only on an `OPEN` session at the current revision; the upload codes match SRS 867–871; the list defaults to 25; the FE sends the headers, stores the abort key and handles 202.

### C-T2 — Upload path mapping (A21): record only

The current path is kept as the C-D9 interim mapping of SRS 1654 and is listed in the SRS reconciliation note that C-D9 requires.

### C-T3 — Production Teacher profile creation (G03): deferred

C01 stays the synthetic route. SRS 1651 (structured fields, expected class revision, one active enrollment) is planned once the consent source for real child data (OI-05) is decided.

### C-T4 — Teacher occurrence, plan, sample/run and lifecycle (G14): planning only

FR-T-08 to FR-T-17 and the SRS 1653 extraction-job endpoint (`POST /v1/lesson-occurrences/{id}/documents` → 202 extraction job and source ref) are a separate planning package after C-T1, coordinated with C-M5 (UC-12). G-T1 is planned with it or with C-M2, whichever comes first.

### C-T5 — Lesson Library and Teacher AI error remainder: planning only

The CONV-1 deferrals not taken by C-T1: the Lesson Library and Teacher AI domain 422 codes, Teacher AI request-ID logging and OpenAPI errors, the `assistance_requests.py` envelope, and ClamAV behaviour. Planned after C-T1; it touches the conditional Teacher AI routes.

## 5. Order and queue

- **BE queue (D-066-73, D-066-75, D-066-76):** FR-C-08 → SEED-1 → PAY-0a → PAY-0b → PAY-0c → C-M1 BE → Billing B-1 → **C-T1 BE**. The periodic runner slice (PD-9a) and Billing B-2 to B-5 are ordered by the owner; C-T1 BE keeps its place after B-1 unless the owner moves it. C-M2 edits the same Lesson Library files; whichever of C-T1 and C-M2 runs second starts from the commit of the first.
- **FE:** C-T1 FE after C-T1 BE is verified, the web branch is reconciled (O-9) and C-M1 FE is done.
- **Branch:** C-T1 BE on a new local-only branch `feature/feat066-ct1`, cut from the BE queue tip when its slot opens, never pushed; pins refreshed then.
- Bruno requests are updated in L5 after the slice is verified.

## 6. Settled answers (per the SRS or the recommendation; owner delegation of 2026-11-18)

| ID | Point | Settled answer | Basis |
|---|---|---|---|
| CT-1 | Lesson list default | 25, max 100 | SRS 1640; C-D8 |
| CT-2 | Keys on A18, A19, B07, B08 and abort, for every caller role | Required; replay before the revision check | SRS 1697; C-D5; the MGR-7 `decide_access_grant` pattern |
| CT-3 | Complete and abort status | 202, status only; body and failures unchanged | SRS 1657, 1658; complete is synchronous today |
| CT-4 | Upload-session create path | Keep as the C-D9 interim mapping | C-D9 |
| CT-5 | Upload-session revision | Derived (`1 + accepted parts`, `+ 1` when terminal), exposed as body `revision` and strong `ETag`; no migration | SRS 1658 "Expected state/version"; C-D7; no revision column exists |
| CT-6 | Upload and file codes | SRS §9.8 names: `LESSON_FILE_TOO_LARGE`, `UPLOAD_PART_CONFLICT`, 410 `UPLOAD_SESSION_EXPIRED`, 422 `UPLOAD_INCOMPLETE`, `UPLOAD_SESSION_STATE_CONFLICT` | SRS 867–871, 1725; CONV-1 item 2b assigns them to C-T |
| CT-7 | Production Teacher profile creation | Deferred | OI-05 open; synthetic-only today |
| CT-8 | G14 and the extraction-job endpoint | C-T4 planning | No route or caller on this base |
| CT-9 | Grant-revoke FE control | Deferred until a Teacher grant read exists (G-T1, NEW gap); the BE key change still ships | A Teacher cannot list grant IDs today |
| CT-10 | Other CONV-1 deferrals for C-T | C-T5 planning | CONV-1 deferred-items table |
| CT-11 | Queue position of C-T1 BE | After Billing B-1 | D-066-73, D-066-75, D-066-76; the owner can move it |
| CT-12 | Branch policy | New local-only branch `feature/feat066-ct1`, never pushed, pins refreshed when the slot opens | Same policy as CONV-1, SEED-1 and C-M1 |

## 7. Not verified

- Exact DTO field mapping between the Lesson Library schemas and the FE types (register NV marks).
- Whether other Rev37 catalog constants beyond `IDEMPOTENCY_MISMATCH_OPERATION_KEYS` change.
- Whether ClamAV is the only scanner path (C-T5).
- No test, build or command was run for this draft beyond read-only searches.

## 8. Limits

C-T does not change A07, A09, A10 (C-M1), Lesson Library approval (C-M2), Parent-group invitations (MGR-4), consent (MGR-5), Teacher AI calls (conditional; C-T5 for their errors), Billing or payment.

## 9. Round-1 findings and their fixes

| Finding | Fixed in |
|---|---|
| CT-R1-01 (P2) | §2 and §4 step 5: derived revision, no migration; what it covers |
| CT-R1-02 (P2) | §4 step 5: `UploadSessionV1.revision` and `ETag` on create and GET (not complete); FE stores the abort key |
| CT-R1-03 (P2) | §4 step 2 and allowlist: the five service methods; replay, revision check, execute; fingerprint contents |
| CT-R1-04 (P2) | §4 step 3: stale 409 with `ETag` and `current_version` on all C-T1 routes; decision route left to C-M2 |
| CT-R1-05 (P2) | §4 step 6 takes the upload and file codes; C-T5 takes the rest of the CONV-1 deferrals (CT-10) |
| CT-R1-06 (P2) | §4 step 4 and CT-3: status-only change; SRS 1653 extraction job assigned to C-T4 |
| CT-R1-07 (P2) | B07 control moved to the import page; B08 FE control deferred with gap G-T1 (CT-9) |
| CT-R1-08 | §2: PATCH creates an immutable version, from source |
| CT-R1-09 | §2: C01 always mounted, request-time 409 gate |
| CT-R1-10 | §1 cites D-066-76; §5 and CT-11 position |
| CT-R1-11 | Allowlist: Bruno 087, the catalog constant and its test, `test_http_error_conventions.py` |
| CT-R1-12 | §2 notes FE paging already exists; header lists the NEW items |
| CT-R1-13 | §2 and step 2: the key requirement also applies to School Manager calls of A19 and B08 |
