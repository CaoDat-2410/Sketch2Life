# FEAT-066 C-T — Teacher per-role slice package (Draft 1)

- **Status:** DRAFT / NOT REVIEWED / NOT APPROVED / NOT LAUNCHED. This package plans Phase C work for the Teacher web role only. It authorizes no code, migration, test, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **What C-T is:** roadmap Draft 4 §4 row C ("per-role slices") for the Teacher, and register Draft 4 §5 row "C-T": rows A16, A18, A19, A21, A23, A24, A25, B07, B08, C01 and gaps G03, G14. The Teacher rows shared with the School Manager (A07, A09, A10) are already in C-M1 (D-066-75); this package does not repeat them.
- **Owner delegation:** on 2026-11-18 the owner asked that package questions be settled from the SRS rather than asked one by one. §6 lists the settled answers with their basis; the owner can override any of them when approving the package.
- **NEW in this package:** the sub-slice names C-T1 to C-T4, the settled answers CT-1 to CT-9, and every behaviour marked NEW below.

## 1. Authority and inputs

| Input | Location | Bytes | SHA-256 (prefix) |
|---|---|---:|---|
| Working SRS (D-209, D-066-64) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | 701,157 | `B9B1F42D…` |
| Mismatch register Draft 4 | `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT4_20261118.md` (git-ignored) | 41,798 | `0F3F35FD…` |
| Roadmap Draft 4 | `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md` | 42,628 | `63710A9F…` |
| CONV-1 package Draft 5 (D-066-71) | `plan/PLAN_CONV1_BE_IMPLEMENTATION_APPROVAL_PACKAGE_DRAFT5_20261118.md` | 47,483 | `3FCF4741…` |
| C-M package Draft 4 (D-066-75) | `plan/PLAN_CM_SCHOOL_MANAGER_SLICE_PACKAGE_DRAFT4_20261118.md` | 28,716 | `401E8935…` |
| Decisions (conv1 worktree, uncommitted appends D-066-72 to D-066-75) | `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md` | 65,589 | `5FB8EBA7…` |

Decisions used: D-066-62, D-066-68 (conventions: C-D4 404/403, C-D5 `Idempotency-Key`, C-D7 revision per family with strong `If-Match`/`ETag` for Lesson Library, C-D8 paging, C-D9 interim paths), D-066-69 (profile visibility), D-066-71 (CONV-1 built), D-066-73 and D-066-75 (queue).

**BE source base:** commit `2dddc607` (CONV-1, local-only branch `feature/feat066-conv1`), which contains S-LL (MGR-7, MGR-8; G0 closed at `08439b22`). **FE source base:** `.worktrees/ui`, branch `codex/fe-ui-web-remediation` at `297a28b1`.

**SRS clauses used:**

| Line | Content |
|---|---|
| 798 | `/v1/lessons` and `/v1/lesson-occurrences`: import, extraction status, edit revisions, occurrence plan and approval |
| 1640 | Cursor paging, default 25, maximum 100, explicit deterministic order |
| 1651 | `POST /v1/classes/{class_id}/profiles`: assigned Teacher; structured fields and expected class revision; one active enrollment; 201 profile/enrollment ref |
| 1654–1658 | Upload sessions: create (purpose, media type, expected size/hash, scoped target, idempotency key); read; part PUT (≤ 4 MiB, SHA-256, same part/hash idempotent); **complete → 202** complete/validation state; **DELETE → 202** abort/purge, "Expected state/version; idempotent" |
| 1697–1699 | §21.4: every state-changing command carries an idempotency key; profile, lesson plan, story and script changes carry an expected revision; stale → `STALE_REVISION` |
| 2449–2452, 2644–2647 | FR-PL-03 to FR-PL-06: reusable lesson items and immutable versions pinned per use; visibility; School Manager approval for PUBLIC; grants with state and revoke |

## 2. What is already true (2026-11-18)

| Fact | Effect on C-T |
|---|---|
| G0 closed (`08439b22`) | The Lesson Library rows are no longer blocked by G0 |
| CONV-1 built (`2dddc607`, local only) | §9.8 envelope on `/api/lesson-library/v1`; missing `If-Match` → 400 `INVALID_REQUEST` (CV-4); `limit_query()` available; uniform 404 and in-scope 403 in the shared guards |
| MGR-7 built | Lesson Library same-key / different-payload → 400 `INVALID_IDEMPOTENCY_KEY`; Parent Groups and access-grants lists default 25 |
| C-M2 (W-LESSON) approved as a sub-slice (D-066-75) | It edits the same Lesson Library files (`lesson_library.py`, service, schemas); C-T1 and C-M2 must run one after the other (§5) |
| Synthetic-only rule | Teacher profile creation (C01) is mounted only when `env` is `local` or `test` **and** `synthetic_pilot_enabled`; it creates `SYNTHETIC_DEV` profiles |
| Consent source for real data is open (SRS OI-05; FEAT-081 open item; MGR-5 excluded) | A production Teacher profile route (G03) cannot be specified yet |

## 3. Row map (BE `2dddc607`, web `297a28b1`)

| Row | Endpoint / capability | Today | Target | Sub-slice |
|---|---|---|---|---|
| A16 | GET `/api/lesson-library/v1/organizations/{organization_id}/lessons` | `limit` default 50, max 100 | default 25 (C-D8, SRS 1640) | C-T1 |
| A18 | PATCH `…/lessons/{lesson_id}` | `If-Match` (optional header, now 400 when missing), no `Idempotency-Key` | `Idempotency-Key` required (§21.4); `If-Match` kept (C-D7) | C-T1 |
| A19 | DELETE `…/lessons/{lesson_id}` (archive) | `If-Match`, no key | `Idempotency-Key` required | C-T1 |
| B07 | POST `…/lessons/{lesson_id}/versions` | no key; no page caller | `Idempotency-Key` required; FE caller added (save as version) | C-T1 |
| B08 | DELETE `…/lessons/{lesson_id}/access-grants/{access_grant_id}` | no key; FE DTO absent | `Idempotency-Key` required; FE type and caller | C-T1 |
| A24 | POST `/api/lesson-library/v1/upload-sessions/{upload_session_id}/complete` | 200, synchronous | **202** with the complete/validation state (SRS 1657) | C-T1 |
| A25 | DELETE `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | 200; no key; no expected state | **202** (SRS 1658); `Idempotency-Key`; expected state through `If-Match` on the session `ETag` (C-D7) | C-T1 |
| A23 | PUT `…/upload-sessions/{upload_session_id}/parts/{part_number}` | BE matches; FE response untyped | FE types `UploadPartReceiptV1` | C-T1 (FE only) |
| A21 | POST `…/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` | path differs from the SRS example `POST /v1/upload-sessions` (scoped target in the body) | keep the current path as the C-D9 interim mapping (CT-4) | — (record only) |
| C01 | POST `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | synthetic only (local/test + flag); no expected class revision | stays synthetic in C-T (CT-6) | — |
| G03 | Production Teacher profile creation and enrollment | absent | deferred until the consent source is decided (CT-6) | C-T3 (deferred) |
| G14 | Teacher occurrence, plan, sample/run, projection, lifecycle (FR-T-08 to FR-T-17) | absent on the web | planned separately (CT-7) | C-T4 (planning) |

**Web callers** (`apps/web/src`): `shared/api/backendApi.tsx` (all Lesson Library methods), used by `modules/teacher/pages/TeacherApiLessonPage.tsx`, `TeacherApiImportPage.tsx` and `TeacherWorkbenchPage.tsx`. The helper already sends `Idempotency-Key` on create, upload-session create and complete, and `If-Match` on PATCH and DELETE.

## 4. Sub-slices

### C-T1 — Lesson Library conventions for the Teacher (A16, A18, A19, A23, A24, A25, B07, B08)

**BE part (one Task Approval, one commit):**
1. A16: `list_lessons` default 25 through `limit_query()` (max 100; above 100 → 400). Order stays as today and is stated in the evidence (SRS 1640).
2. A18, A19, B07, B08: `Idempotency-Key` required (C-D5: one value, 1–128 visible ASCII), using the existing Lesson Library receipt mechanism of MGR-7 (same key and payload → replay; different payload → 400 `INVALID_IDEMPOTENCY_KEY`). A missing key → 400 `INVALID_REQUEST` with field error `Idempotency-Key` / `REQUIRED` (CONV-1 rule). **Breaking change** for callers that send no key.
3. A24: `complete` returns **202** with the existing status body (the validation state); a replay returns the same 202.
4. A25: abort returns **202**; requires `Idempotency-Key` and `If-Match` with the session's strong `ETag` (NEW on upload sessions); a stale `If-Match` → 409 `STALE_REVISION` with the current `ETag` (C-D7). `GET` and `complete` responses carry the session `ETag`.
5. A18 immutable-version behaviour (register NV): the C-T1 BE task first confirms from source and a test whether a lesson PATCH creates a new immutable version or edits the head (FR-PL-03, §31.2). If it edits the head, the finding stops the task for an owner scope amendment; C-T1 does not redesign versioning (that is C-M2's version model).
6. OpenAPI: status codes, the required headers and examples, through `openapi_contract.py` and its amendments module.

**Proposed allowlist (exact paths fixed in the C-T1 Task Approval):** `interfaces/http/routers/lesson_library.py`; `infrastructure/lesson_library/service.py` (only for the upload-session `ETag` and abort precondition); `contracts/schemas/lesson_library.py`; `interfaces/http/openapi_contract.py` and `openapi_contract_amendments.py`; `tests/integration/lesson_library/test_lesson_library_api.py`; `tests/contract/test_openapi_contract_catalog.py`; Lesson Library unit tests; Bruno requests 070, 072, 074, 076, 080, 086, 088 and 089 (L5 per-slice update); the C-T1 evidence note. No migration unless the session `ETag` needs a stored revision; if it does, the task stops for a scope amendment.

**Checks:** contract catalog; unit tests; the Lesson Library PostgreSQL integration test on a disposable database whose name contains `be1_acceptance` (never `sketch2life_m2_s1a`, never ports 5432 or 5433), **run by the owner**; repository validators.

**FE part (one Task Approval, after the BE part is verified and the web branch is reconciled, O-9):**
- `shared/api/backendApi.tsx`: send `Idempotency-Key` on PATCH and DELETE lesson, version create and grant revoke (the same key for a retry of the same command); send `If-Match` and a key on upload abort; accept 202 on complete and abort; type `UploadPartReceiptV1`, the version response and the grant-revoke response; page with `next_cursor` where a screen needs more than 25 lessons.
- `TeacherApiLessonPage.tsx`: "save as version" (B07) and "revoke grant" (B08) controls, enabled only after the BE part is verified.
- `TeacherApiImportPage.tsx`: complete and abort read the 202 state; the upload screen shows the validation state instead of assuming success.
- Tests next to each changed module.

**BE-before-FE window:** local development only. Between the commits, lesson PATCH and DELETE from the current web helper fail with 400 (missing key), and the lesson list shows 25 items.

**Acceptance:** every C-T1 command refuses a missing key with 400 and replays the same key; A24 and A25 answer 202; a stale abort answers 409 `STALE_REVISION`; the list defaults to 25; the FE sends the headers and handles 202.

### C-T2 — Upload path mapping (A21): record only

No code. The current path `POST /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/upload-sessions` is kept as the C-D9 interim mapping of SRS 1654 (`POST /v1/upload-sessions` with a scoped target). The SRS reconciliation note that C-D9 requires lists it.

### C-T3 — Production Teacher profile creation (G03): deferred

C01 stays the synthetic local/test route. A production route (SRS 1651: structured fields, expected class revision, one active enrollment) needs the consent source for real child data, which is open (OI-05; MGR-5 excluded; FEAT-081 open item). C-T3 is planned when that decision exists.

### C-T4 — Teacher occurrence, plan, sample/run and lifecycle (G14): planning only

FR-T-08 to FR-T-17 are a large capability (lesson occurrences, plan approval, sample and run, projection, Teacher reassignment through UC-12). They have no web caller or BE route on this base. C-T4 is a separate planning package, written after C-T1, and coordinated with C-M5 (UC-12).

## 5. Order and queue

- **BE queue:** FR-C-08 → SEED-1 → PAY-0a → PAY-0b → PAY-0c → C-M1 BE → Billing B-1 → **C-T1 BE** (CT-8). C-M2 also edits the Lesson Library files; whichever of C-T1 and C-M2 runs second starts from the commit of the first.
- **FE:** C-T1 FE after C-T1 BE is verified and the web branch is reconciled (O-9). One FE slice at a time in the web app: C-M1 FE, then C-T1 FE.
- **Branch:** C-T1 BE on a new local-only branch `feature/feat066-ct1`, cut from the BE queue tip when its slot opens, never pushed; pins refreshed then (as CONV-1, SEED-1 and C-M1).
- Bruno requests are updated in L5 after the slice is verified.

## 6. Settled answers (per the SRS or the recommendation; owner delegation of 2026-11-18)

| ID | Point | Settled answer | Basis |
|---|---|---|---|
| CT-1 | Lesson list default page size | 25, max 100 | SRS 1640; C-D8 |
| CT-2 | `Idempotency-Key` on lesson PATCH and DELETE, version create and grant revoke | Required | SRS §21.4 line 1697; C-D5 |
| CT-3 | Upload complete and abort status | 202, as the SRS states | SRS 1657, 1658 |
| CT-4 | Upload-session create path (A21) | Keep the current path as the interim mapping | C-D9 keeps `/api/<namespace>/v1` paths; only a reconciliation note is required |
| CT-5 | Upload abort precondition | `If-Match` with the session's strong `ETag`; stale → 409 `STALE_REVISION` | SRS 1658 "Expected state/version"; C-D7 (strong `If-Match`/`ETag` for Lesson Library; never 412) |
| CT-6 | Production Teacher profile creation (C01, G03) | Deferred; C01 stays synthetic | SRS OI-05 and the excluded MGR-5 leave the consent source for real child data open; no production profile without it |
| CT-7 | Teacher occurrence and run capability (G14) | Separate planning package C-T4 after C-T1 | No route or caller exists; FR-T-08 to FR-T-17 are a capability of their own |
| CT-8 | Queue position of C-T1 BE | After Billing B-1 | Keeps the queue already set by D-066-73 and D-066-75; the owner can move it earlier |
| CT-9 | Branch policy for C-T1 BE | New local-only branch `feature/feat066-ct1`, never pushed, pins refreshed when the slot opens | Same policy as CONV-1 (D-066-71 CV-B), SEED-1 (D-066-72) and C-M1 (D-066-75 CM-9) |

## 7. Not verified

- Whether a lesson PATCH creates an immutable version (register NV; C-T1 BE step 5 checks it first).
- Exact response field mapping of the Lesson Library DTOs against the FE types (register NV marks).
- Bruno request content beyond file presence.
- No test, build or command was run for this draft beyond read-only searches.

## 8. Limits

C-T does not change the Teacher rows already in C-M1 (A07, A09, A10), Lesson Library approval (C-M2), Parent-group invitations (MGR-4), consent (MGR-5), Teacher AI calls (AI1 to AI3, conditional), Billing, or payment.
