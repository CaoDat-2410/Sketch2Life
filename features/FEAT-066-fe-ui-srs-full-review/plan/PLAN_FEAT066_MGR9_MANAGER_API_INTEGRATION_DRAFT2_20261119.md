# FEAT-066 MGR-9 / C-W1 Web API Alignment Plan — Draft 2

**Status:** DRAFT / NOT APPROVED / NOT LAUNCHED
**Task mode:** Planning only. This plan authorizes no source, test, API, OpenAPI, UI-action, install or deployment change.
**Supersedes for planning:** `PLAN_FEAT066_MGR9_MANAGER_API_INTEGRATION_DRAFT1_20261118.md` (the owner's untracked Draft 1; it is read here, never edited).
**Observation time:** 2026-11-19 (night coordinator run; read-only git inspection, no fetch, no command beyond `git show`/`git log`/hashing).

## 1. What changed since Draft 1

| Draft 1 (2026-11-18) | Draft 2 (2026-11-19) |
|---|---|
| FE base `297a28b1`, 1 behind / 3 ahead of local `origin/dev` | FE base is web branch `codex/fe-ui-web-remediation` HEAD `c42d913a6b4f538b8711f3c0ad28f6643f253421` (pushed). It is **not** an ancestor of `origin/dev`; `origin/dev` is the BE truth source, the web branch is the FE truth source. |
| BE base `1c9148e8`; MGR-7 approved but no implementation | `origin/dev` = `ba295f1113129fa233ddc762ef29fadd92b996e8` (merge of PR #30). It contains MGR-7 commit `08439b22fc3c1f34786a3f45f34530075a3914e0` (ancestor check passed). MGR-8 is **VERIFIED** (see §2.3). |
| Authority = Rev60 SRS (553,948 B) | Authority = the D-209 working SRS, `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` (re-hashed tonight; matches D-209). Rev60 is no longer a requirement reference. |
| Question: is any API ready? | Answer: the 27 page-called routes are checked one by one against `origin/dev` source (§4). Result: 19 match, 8 carry a documented gap (G-1 to G-5); two findings (G-5, G-7) are FE-fixable now (§5). |

Clauses used (D-209 copy): §9.8 error envelope (line 847), §21.1 HTTP rules incl. cursor pagination default 25 / max 100, correlation ID, idempotency key per state-changing command (line 1632), §21.2 resource contract table (line 1643), §21.4 idempotency / optimistic concurrency (line 1695), §31.2–31.3 lesson reuse and tenant roles (lines 2553, 2569).

## 2. Source pins

### 2.1 Identities

| Item | Value |
|---|---|
| Web branch | `codex/fe-ui-web-remediation` = `c42d913a6b4f538b8711f3c0ad28f6643f253421` (commit time 2026-11-19 13:25 +07:00). Worktree `.worktrees/ui`; its `apps/` tree has no dirty path (the dirty files are FEAT-066 docs only, owner's work, untouched). |
| BE truth | `origin/dev` = `ba295f1113129fa233ddc762ef29fadd92b996e8` (local ref, no fetch run) |
| MGR-7 commit | `08439b22fc3c1f34786a3f45f34530075a3914e0` is an ancestor of `origin/dev` |
| SRS | D-209 copy, 701,157 B, `B9B1F42D…B675F5` |

### 2.2 Source files read (size / SHA-256, taken with `git show <ref>:<path>`)

| Ref | Path | Bytes | SHA-256 |
|---|---|---:|---|
| c42d913a | apps/web/src/shared/api/backendApi.tsx | 25,951 | 4047674F9434E489205995E0BDA44E2654482AA5DBCF953399B83120225C986F |
| c42d913a | apps/web/src/modules/school-manager/be1/services/managerBusinessService.ts | 2,409 | 2FDE883554E5A1D7E02B74ED80A7B1B1D145A92315A2EA391A2E7ADD22414B8D |
| c42d913a | apps/web/src/modules/school-manager/be1/pages/ParentGroupsPage.tsx | 9,473 | E31EF487E32BFFE9892158A20172D7F6331144233AB54207BAB1E0CEE7BDA67A |
| c42d913a | apps/web/src/modules/school-manager/pages/ManagerScreens.tsx | 16,775 | D7C71D0F634D6429B1BB021CE79A3060B107A3ADC96A2CC6580BF3011433A985 |
| c42d913a | apps/web/src/modules/teacher/pages/TeacherApiLessonPage.tsx | 21,795 | 403985B29DCB5A3CD5541320252E19EC95D2F5B8F692AA86CC4BC6BC1C72E954 |
| c42d913a | apps/web/src/modules/teacher/pages/TeacherApiImportPage.tsx | 23,428 | 3752F1DB2437B3A9B1EF3191B3371910824369338E9596FE5B9EEBCA96455DF4 |
| c42d913a | apps/web/src/modules/platform-admin/pages/UsersPage.tsx | 20,284 | 415E3C9736BCED41102A3E26EC209B384D6F65B3C0EFE733FAC15C88AE8908B6 |
| c42d913a | apps/web/src/modules/school-manager/be1/__tests__/managerBusinessService.test.ts | 2,226 | 639244AA3DCF76A0910930D8EB022E95CB5AB5C32B93E8A81CC00D07F911AEF1 |
| origin/dev | backend/src/sketch2life/interfaces/http/routers/lesson_library.py | 28,784 | 732DB7C469B9900C94A8B85E92A530934A346AA3BABE4D88C4CB61358DFC9400 |
| origin/dev | backend/src/sketch2life/interfaces/http/routers/be1_registry.py | 20,549 | B090F30C4F87FB53D8A85A83C53391AD77F086AF83F0A1E202EACB0F1C0375FE |
| origin/dev | backend/src/sketch2life/interfaces/http/routers/platform_admin_accounts.py | 17,541 | 1D43D61B68182E621E1409B7983D2C3D5651751ED0C6C67432BC871397E9945D |
| origin/dev | backend/src/sketch2life/infrastructure/lesson_library/service.py | 91,447 | F37DB928B3C7CA5115A537D9E82D740D4BF9B23F34C02A0CBEE3C30BB995255D |
| origin/dev | backend/src/sketch2life/interfaces/http/app.py | 74,569 | 1387A59354DCCED45A74872721E3BA9ECEDEDE8CC44DE43A1BF33CBEDDCCC439 |
| origin/dev | backend/src/sketch2life/interfaces/http/openapi_contract.py | 1,379,096 | 35801B20DC67630B9AAEEFDD46F82886CD91F34990BA2CCE6C2B3E67B6A989B7 |

### 2.3 MGR-8 evidence (in `origin/dev`)

`MGR_8_IMPLEMENTATION_VERIFICATION_20261118.md` (3,208 B, `BCDACA87…127CC7`) and `MGR_8_EVIDENCE_INDEPENDENT_REVIEW_20261118.md` (6,705 B, `8AE285D1…A06E7`; verdict PASS WITH NOTES, P1 0 / P2 0 / P3 4). Both MGR-7 integration tests passed in the owner run; the one failing test (PDF upload) failed on the absent local ClamAV service, not on MGR-7 behavior. This plan relies on the source read in §2.2, not on those notes alone.

## 3. What MGR-7 changed in the BE (verified from source)

1. `GET …/organizations/{org}/parent-groups` — `limit` default **25**, 1–100 (`lesson_library.py` line 529). Was 50.
2. `GET …/organizations/{org}/access-grants` — `limit` default **25**, 1–100 (line 442). Was 50.
3. Reuse of an `Idempotency-Key` with a different payload — HTTP **400** `INVALID_IDEMPOTENCY_KEY` (`service.py` line 506; body shape `{"detail":{"code","message"}}` through `_call`). Same key and same payload still replays the stored result.

MGR-7 did **not** change: `GET …/lessons` (default still 50), `/me/lessons`, `/me/lesson-invitations`, `/me/parent-group-invitations` (default 50), BE1 lists (no pagination), Platform Admin accounts (offset pagination, default 50), or the error envelope (Lesson Library, BE1 registry and Platform Admin routes still return FastAPI `{"detail":{"code","message"}}`; the §9.8 envelope handler in `app.py` is path-scoped to story-run and parent-profile routes). The §9.8 envelope for these roles is the CONV-1 work (`feature/feat066-conv1`, not yet in `dev`), handled by C-W2, not here.

## 4. The 27 page-called routes against `origin/dev`

Legend — **M** = FE request and BE contract match for what the page does today. **G-n** = gap, defined in §5. "BE default" is the list `limit` default on `origin/dev`.

| # | Route (method path template) | FE sends (c42d913a) | BE on `origin/dev` | Result |
|---:|---|---|---|---|
| 1 | GET /api/auth/v1/me | auth only | declared, returns role | M |
| 2 | GET /health | none | declared | M |
| 3 | GET /api/platform-admin/v1/accounts | `limit` (PAGE_SIZE), `offset`, filters | offset/limit/total, default 50, max 100 | **G-3** (offset, not cursor; §21.1) |
| 4 | POST /api/platform-admin/v1/accounts | JSON body, **no Idempotency-Key** | handler takes no key | **G-4** (§21.4) |
| 5 | PATCH /api/platform-admin/v1/accounts/{account_id} | JSON body, no key | no key | **G-4** |
| 6 | GET /api/be1/v1/organizations/{org}/me | auth | declared | M |
| 7 | GET /api/be1/v1/organizations/{org}/classes | no limit | no `limit`/`cursor`; returns all active classes | **G-2** |
| 8 | GET /api/be1/v1/organizations/{org} | auth | declared | M |
| 9 | GET …/classes/{class}/profiles | no limit | no pagination | **G-2** |
| 10 | GET …/classes/{class}/consents | no limit | no pagination | **G-2** |
| 11 | GET /api/lesson-library/v1/organizations/{org}/access-grants | no `limit`; follows `next_cursor` | default **25**, max 100, cursor | M (MGR-7) |
| 12 | GET …/lessons/{lesson_id} | auth | declared; `ETag` returned | M |
| 13 | POST …/access-grants/{id}/decision | `If-Match "rev"` + `Idempotency-Key`; key bound to a signature of grant, revision, version, decision, reason | both headers required; 428 without If-Match; 400 `INVALID_IDEMPOTENCY_KEY` on payload mismatch | M |
| 14 | GET …/parent-groups | `limit=50`, `cursor` | default 25, max 100 | M (explicit 50 is within max) |
| 15 | POST …/parent-groups | `Idempotency-Key`; key kept after an unknown-outcome failure | key required; 400 `INVALID_IDEMPOTENCY_KEY` on mismatch | **G-5** (key reuse across an edited name) |
| 16 | GET …/lessons | no `limit`; follows `next_cursor` | default **50**, max 100 | **G-1** (default 50 vs §21.1 25) |
| 17 | POST …/lessons | `Idempotency-Key` bound to a payload signature | key required | M |
| 18 | PATCH …/lessons/{id} | `If-Match`, no key | `If-Match` required, no key | M |
| 19 | DELETE …/lessons/{id} | `If-Match`, no key | `If-Match` required, no key | M |
| 20 | POST …/lessons/{id}/access-grants | `Idempotency-Key` bound to lesson and version | key required | M |
| 21 | POST …/lessons/{id}/upload-sessions | `Idempotency-Key` in the resume record | key required | M |
| 22 | GET /api/lesson-library/v1/upload-sessions/{id} | auth | declared | M |
| 23 | PUT …/upload-sessions/{id}/parts/{n} | `X-Part-SHA256`, `Content-Range`, octet-stream | both headers required, same shape | M |
| 24 | POST …/upload-sessions/{id}/complete | `Idempotency-Key` from the resume record | key required | M |
| 25 | DELETE …/upload-sessions/{id} | none | no key, no If-Match | M (SRS §21.2 table lists "expected state/version; idempotent" for abort; see G-6) |
| 26 | GET …/source-documents/{id} | auth | declared | M |
| 27 | GET …/source-documents/{id}/revisions/{rev} | auth | declared | M |

Totals: **19 rows match** (rows 1, 2, 6, 8, 11, 12, 13, 14, 17–27; row 25 matches with note G-6) and **8 rows carry a gap** (rows 3, 4, 5, 7, 9, 10, 15, 16). Draft 1 stated the 27 as inventory only; this replaces it with a verified per-row result.

Unchanged from Draft 1: Parent shared login gate `GET …/me/lessons` is not in the 27 (mobile, separate); the three Teacher AI calls are local/test-only and excluded.

## 5. Gaps and where each is fixed

| Gap | Finding | SRS clause | Fix is | Slice |
|---|---|---|---|---|
| **G-1** | `GET …/lessons` default 50; FE sends no `limit`. Also `/me/lessons`, `/me/lesson-invitations`, `/me/parent-group-invitations` default 50 (Parent mobile). | §21.1 default 25 / max 100 | BE (default 25) first; no FE change needed (FE follows `next_cursor`) | C-T BE slice (step 17); FE only re-verifies |
| **G-2** | Class list, profile list, consent list are unpaginated arrays. | §21.1 cursor pagination for list APIs | BE first (cursor + `next_cursor`), then FE "load more" | Needs its own BE contract; excluded from MGR-7; not M9-B. Proposed new item MGR-10 (see PD-3) |
| **G-3** | Platform Admin accounts list uses `limit`/`offset`/`total`. | §21.1 cursor | BE first, then FE (`UsersPage`) | C-A (step 18) |
| **G-4** | Platform Admin create/update accounts send and accept no `Idempotency-Key`. | §21.1, §21.4 | BE first (accept key, replay), then FE | C-A (step 18) |
| **G-5** | `ParentGroupsPage` keeps `retryKey` after an unknown-outcome failure. If the user edits the group name before retrying, the same key is sent with a different payload; since MGR-7 this returns 400 `INVALID_IDEMPOTENCY_KEY` with an English BE message shown to the user. Other write pages bind the key to a payload signature and are safe (ManagerScreens signature; TeacherApiLessonPage signature; TeacherApiImportPage resume record). | §21.1 ("keep the key when retrying the **same** command"), §21.4 | **FE only** | **C-W1 slice F1** |
| **G-6** | `DELETE …/upload-sessions/{id}` has no expected-state/version in BE or FE. | §21.2 row for DELETE upload-session (idempotent, expected state/version) | BE decision first (owner/BE); not C-W1 | Proposed note in C-T BE slice; no FE change planned |
| **G-7** | No FE mapping for `INVALID_IDEMPOTENCY_KEY`; the English BE message (`Idempotency-Key was already used for another request`) is shown as-is. | §9.8 message must be safe and localized (Vietnamese) | **FE only**, small, no new route | **C-W1 slice F2** |

## 6. C-W1 scope (what an approved FE task may change)

C-W1 is the **FE-only** part: two small slices, each bounded to the files named. No new API call; the 27-route inventory is unchanged.

### F1 — Bind the ParentGroups retry key to the payload (G-5)

- **Files:** `apps/web/src/modules/school-manager/be1/pages/ParentGroupsPage.tsx`; its test under `apps/web/src/modules/school-manager/be1/__tests__/`.
- **Change:** store the retry key together with the trimmed `display_name` it was minted for. Send the stored key only when the trimmed name equals the stored name; otherwise mint a fresh key. Keep the existing rule that a 4xx rejection clears the key.
- **Acceptance:** (a) same name after a network/5xx/408 failure sends the same key; (b) an edited name sends a new key; (c) success or 4xx clears the key; (d) no new route or header.

### F2 — Safe Vietnamese message for `INVALID_IDEMPOTENCY_KEY` (G-7)

- **Files:** `apps/web/src/shared/api/backendApi.tsx` (`errorFromResponse` message mapping only) and one test.
- **Change:** when `code === "INVALID_IDEMPOTENCY_KEY"` use a fixed Vietnamese message that tells the user the action must be retried as a new request (no server text is echoed). No change to retry logic or headers.
- **Acceptance:** the message is shown for HTTP 400 with that code; all other codes keep their current messages; `request_id` handling is unchanged.

### F3 — Regression checks (no code change)

Confirm by test that: `accessGrants` and `ParentGroups` consume default-25 pages through `next_cursor` (no assumption of 50 items per page); `lessons` consumers do not assume a page size; the three signature-bound pages still send a stable key on same-payload retry.

### Explicitly out of C-W1

- G-1, G-2, G-3, G-4, G-6: BE-first slices (C-T, C-A, MGR-10), then FE.
- C-W2 (CONV-1 envelope: `correlation_id`, `retryable`, field errors) after CONV-1 is in `dev`.
- **M9-A** class create (needs Billing capacity, MGR-2), **M9-B** Teacher assignment (MGR-3), **M9-C** exact-version review (MGR-6): remain **BLOCKED** exactly as in Draft 1 §5; their BE contracts do not exist in `origin/dev`.
- Parent invitation/membership, consent writes, moderation, Teacher AI calls: excluded as in Draft 1 §5.1.

## 7. Verification plan (for the later implementation task, not tonight)

Run only after the owner approves this plan and allows `pnpm install` in `.worktrees/ui`: typecheck, the web unit tests that cover F1/F2/F3, lint on the touched files, `git diff --check`, and the repository validators named in the harness. Report actual output. No browser runtime, database, Docker or network step is part of C-W1.

## 8. Proposed decisions (recommendations; the owner approves the batch)

| ID | Question | Recommendation | SRS basis |
|---|---|---|---|
| PD-1 | Approve C-W1 as F1 + F2 + F3 only (two FE files + tests, no new route)? | Yes | §21.1, §21.4, §9.8 |
| PD-2 | Lessons list default 50 → 25 (G-1): treat as a BE change in the C-T slice, not in C-W1? | Yes; one-line BE change plus a test, bundled with A16/A18/A19 | §21.1 |
| PD-3 | Class/profile/consent list pagination (G-2): open a separate BE item (MGR-10) after C-0, cursor + default 25? | Yes; do not stretch M9-B | §21.1 |
| PD-4 | Platform Admin accounts cursor pagination and idempotency keys (G-3/G-4): fold into C-A BE-first slice? | Yes | §21.1, §21.4 |
| PD-5 | Upload-session abort expected-state (G-6): leave as is for now and record as a note? | Yes; low risk, upload sessions are owner-scoped | §21.2 (DELETE upload-session row) |
| PD-6 | Keep M9-A/B/C BLOCKED until MGR-2/3/6 BE contracts exist? | Yes | §21.2 rows for class create and assignment; §31.2–31.3 |

## 9. Stop rules

Stop and re-plan if: `origin/dev` or the web branch moves and any pin in §2.2 changes; MGR-7 behavior in §3 is not what the source shows at implementation time; the SRS authority changes; or F1/F2 would need a new route, DTO, header or client-side authorization workaround.

## 10. Planning disposition

27 routes checked: 19 match, 8 rows carry a gap (G-1..G-5); 2 gaps (G-5, G-7) are fixable in FE now and make up C-W1; the others are BE-first. **MGR-9 Draft 2 plan only; not approved or launched.**
