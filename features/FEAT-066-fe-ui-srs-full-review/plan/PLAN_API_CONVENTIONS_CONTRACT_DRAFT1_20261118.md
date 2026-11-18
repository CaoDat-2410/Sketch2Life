# FEAT-066 A-3 — API conventions contract (O-CONV) — Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT REVIEWED. Contract plan only. It authorizes no code, test, OpenAPI change or command. Every choice below is an **option for the owner**. A recommendation is given only where the SRS or the current source supports one.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Place in the roadmap:** Phase A item A-3 of the reconciliation addendum (`tmp/feat066-phase-a/roadmap-reconciliation/PHASE_A_ROADMAP_RECONCILIATION_20261118.md`). It covers the global items E and PX and the pagination, idempotency and revision columns of the A-1 register (`tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT1_20261118.md`). It also covers roadmap Draft 4 §8 O-CONV and O-2c and the "Conventions" row of its §9.
- **SRS basis:** the adopted working SRS (701,157 bytes, `B9B1F42D…`, D-209), unsigned. Clauses used:
  - §9.8 error contract (lines 847–875);
  - §21.1 shared HTTP rules (lines 1632–1641);
  - §21.4 idempotency and optimistic concurrency (lines 1695–1701);
  - §9.6 (exact paths and schemas are still to be finalized against OpenAPI).
- **Source basis:** BE worktree `.worktrees/manager-api`, HEAD `1c9148e8` = `origin/dev`. Static reading only. Six MGR-8 files are dirty and unverified; the P1 rerun is in progress.
- **Slice name:** the addendum called the conventions slice "B-1", but the Billing contract also numbers its slices B-1 to B-5. To avoid the clash, this plan calls it **CONV-1**.

## 1. Current state (evidence)

| Item | Observed in source or Phase A audits |
|---|---|
| Error bodies | Four shapes, none a complete §9.8 envelope (P2 global item D10):<ul><li>FastAPI `detail` on auth and Platform Admin (E-A);</li><li>`{code, message, request_id}` on BE1 (E-B);</li><li>a `detail: {code, message}` / `{code, message, request_id}` shape on Lesson Library (E-L);</li><li>a nested `detail` on Teacher AI (E-T).</li></ul>**The M2 Parent routes are the exception:** `ParentErrorResponse` (`contracts/schemas/parent_profiles.py:70`) has `code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds`, `field_errors` and two extras, `request_id` and `current_version` |
| Correlation header | `interfaces/http/app.py:329–344` reads `X-Request-ID` from the request and echoes it on the response; error handlers repeat it (`app.py:407`, `:465`). `routers/story_run_lite.py:319,335` uses `X-Correlation-ID` instead |
| Idempotency | The `Idempotency-Key` header is used by the M2 Parent routes (`routers/parent_profiles.py:51`) and by Lesson Library commands. It is missing on account create and update, class create, assignment, consent writes, lesson update and archive, upload abort, version create, membership delete and access-grant revoke (P2 D07; register rows A04, A05, A18, A19, A25, B01, B02, B07, B08) |
| Revision / precondition | The M2 Parent routes take `expected_revision` in the body. Lesson Library takes a strong `If-Match` / `ETag`. Assignment returns no revision; accounts return one but take no precondition (P2 D08) |
| Pagination | Lesson Library uses a cursor, default 50 (the unverified MGR-8 edit sets 25 for access grants and Parent groups). Accounts use offset, default 50. BE1 classes, profiles and consents are unpaginated. M2 Parent profiles use a cursor with `next_cursor` (P2 D09; P3 rows 2, 15, 16, 19) |
| Path prefix | Most routes use `/api/<namespace>/v1/...`. M2 Parent and StoryRun routes use `/v1/...` (P2 global item PX) |
| Validation errors | FastAPI's default is 422; the M2 Parent routes list 400 and 422. SRS §9.8 lists `INVALID_REQUEST` under 400 and reserves 422 for semantic codes (`SUBJECT_NOT_CONFIRMED`, `UPLOAD_INCOMPLETE`, …) |
| Out-of-scope access | BE1 returns 403 for a missing or wrong assignment. §9.8 requires 404 `RESOURCE_NOT_FOUND` with the same shape as a non-existent ID, and 403 `ACTION_NOT_ALLOWED` only when the resource is in the actor's scope |

## 2. Items, options and recommendations

### C-1 Error envelope (SRS §9.8)

| Option | Effect |
|---|---|
| **A — adopt the M2 Parent shape for every route (recommended)** | It is already a superset of §9.8. The extras stay: `request_id` (see C-2) and `current_version` (only with `STALE_REVISION`, which §21.4 asks to return "cùng version hiện tại"). The body is top-level, not nested in `detail`. The M2 Parent clients and the mobile parser keep working (P3: the mobile parser already reads top-level or `detail`) |
| B — strict §9.8 fields only | Drops `request_id` and `current_version`. This breaks the M2 Parent contract that the M2 closure accepted and the frozen client projection |

Rules for either option:
- `message` is a safe Vietnamese text.
- No stack trace, local path, provider detail or upload text.
- `field_errors` holds codes, not echoed input.

**Owner decision C-D1:** option A or B.

### C-2 Correlation ID

| Option | Effect |
|---|---|
| **A — one ID, `X-Request-ID` (recommended)** | Already the global middleware. `correlation_id` in the body equals the `X-Request-ID` response header. `request_id` stays as a deprecated alias with the same value for M2 compatibility. `story_run_lite`'s `X-Correlation-ID` is read as an alias and answered with `X-Request-ID` |
| B — rename to `X-Correlation-ID` | Matches the §9.8 field name. Changes every client that already reads `X-Request-ID` (the mobile `ParentApi` sends `X-Request-ID`, P3) |

**Owner decision C-D2.**

### C-3 Validation status

| Option | Effect |
|---|---|
| **A — 400 `INVALID_REQUEST` with `field_errors` for schema and validation failures; 422 only for the §9.8 semantic codes (recommended)** | Follows the §9.8 table literally. **Breaking** for callers and tests that expect FastAPI's 422 |
| B — keep 422 for validation | Smaller change. Deviates from §9.8 |

**Owner decision C-D3.** If A is chosen, the change happens in CONV-1 only, never route by route.

### C-4 404 versus 403 (SRS §9.8)

**Rule:** an ID that does not exist and a resource outside the actor's scope return the same 404 `RESOURCE_NOT_FOUND`. 403 `ACTION_NOT_ALLOWED` is returned only when the resource is in scope but the action is not allowed.

**Today:** BE1 returns 403 for out-of-scope organization access. Moving to the rule is a **behaviour change** for web callers and tests (the Billing contract keeps 403 until this decision).

**Owner decision C-D4:** change in CONV-1, or per capability slice.

### C-5 Idempotency key (SRS §21.1, §21.4)

**Fixed by the SRS:**
- A key is required on every state-changing command.
- The key is scoped by (principal, operation, target resource).
- The same key with the same payload returns the original result.
- The same key with a different payload returns 400 `INVALID_IDEMPOTENCY_KEY`.

**Proposed:**
- Header `Idempotency-Key`, the name already used.
- A missing key on a command returns 400 `INVALID_REQUEST` with a field error. This is an **interpretation**, and **breaking** for routes that take no key today: the account, class, assignment and lesson commands above.

| Sub-item | Options |
|---|---|
| Key format | **A — the format the M2 Parent routes already validate** (its exact rule is NOT VERIFIED here; read it in the CONV-1 package); B — UUID only |
| Retention | A — durable receipts, as the existing BE1 and Lesson Library receipt tables (no expiry); B — a fixed window (for example 24 hours) with a cleanup job. No SRS value: **owner choice** |
| Errors are stored? | **No (recommended)**, as in the Billing contract and the current receipts: only successful results are replayed |

**Owner decisions C-D5 (format), C-D6 (retention).**

### C-6 Revision / optimistic concurrency (SRS §21.4)

**SRS:** profile, lesson plan, story and script changes send an expected revision or hash. A stale request gets 409 `STALE_REVISION` with the current version and never overwrites the head. The SRS does not fix the transport (header or body).

| Option | Effect |
|---|---|
| **A — keep the transport per resource family, unify the outcome (recommended)** | Body `expected_revision` stays for M2 Parent resources; strong `If-Match`/`ETag` stays for Lesson Library. Every stale case returns 409 `STALE_REVISION` with `current_version` (or the current ETag) in the envelope. No client path changes |
| B — body `expected_revision` everywhere | Changes Lesson Library clients |
| C — `If-Match` everywhere | Changes the M2 Parent contract (frozen) |

**Which resources need a precondition beyond the SRS list** (assignment, account) stays with the capability slices: O-3d and O-ACCREV.

**Owner decision C-D7.**

### C-7 Pagination (SRS §21.1)

**SRS:** an opaque, stable cursor; default page size 25, maximum 100; an explicit, deterministic order; no client-supplied SQL field names.

**Proposed page shape:** `{items, next_cursor}` plus the correlation field. It is already used by M2 Parent profiles and Lesson Library. Query parameters are `cursor` and `limit`.

| Sub-item | Options |
|---|---|
| `limit` above 100 | **A — 400 `INVALID_REQUEST` with a field error (recommended: explicit, no silent change)**; B — clamp to 100 |
| Offset paging on accounts | Replaced by a cursor, **breaking** for the Platform Admin FE (`UsersPage` sends `limit` and `offset`). It changes in the Platform Admin slice, not in CONV-1 |
| Unpaginated BE1 lists | Get a cursor in their capability slices (C-M), using the CONV-1 helper |

**Owner decision C-D8** (limit above 100).

### C-8 Path prefix (SRS §21.1 "Base path có version, bắt đầu từ /v1"; §9.6 exact paths still to be finalized against OpenAPI)

| Option | Cost and effect |
|---|---|
| A — keep `/api/<namespace>/v1/...` and record a deviation | No code or client change. The SRS sentence is not met literally; the deviation needs an owner decision and, later, an SRS reconciliation note |
| B — public `/v1/...` through a gateway or proxy rewrite to the current routes | No router move. Needs a deployment component (none is verified today); local and Bruno use the internal paths |
| C — move every route to `/v1/<resource>` with compatibility aliases for a fixed window (§21.1 allows a compatibility period) | Largest change: every router, the OpenAPI catalog, all web callers and the Bruno collection |

**No recommendation.** The SRS states `/v1` but §9.6 leaves exact paths open, and the cost differs by an order of magnitude.

**Owner decision C-D9.** Whatever is chosen, the M2 Parent and StoryRun routes are already on `/v1` and stay there.

### C-9 Parent ordering (roadmap O-CONV second half; A-4 brief D-E)

**Question:** may the 8 M2-allowed Parent operations be wired (C-P) before CONV-1?

**Evidence for yes:**
- They already use the §9.8 superset (C-1 option A), `Idempotency-Key` and cursor pages.
- They are on `/v1`.

**Risk:** if C-1 B or C-2 B is chosen, the Parent parser changes again.

**Owner decision C-D10.**

## 3. CONV-1 slice shape

**Scope proposal (recommended: small global core plus shared helpers):**

| Part | Content | Files likely touched (to be fixed in its Task Approval) |
|---|---|---|
| Global core | One error envelope builder and the exception handlers (C-1, C-3, C-4 if chosen), correlation ID (C-2) | `interfaces/http/app.py`, a shared error module, `openapi_contract.py`, the catalog test, app-composition and error tests |
| Shared helpers | Idempotency-key parsing and validation (C-5), cursor page helper (C-7), stale-revision error helper (C-6) | new helper modules; no router adopts them in CONV-1 except as listed |
| Adoption | Each capability slice (C-A, C-M, C-T and the Parent Lesson Library slice) adopts the helpers for its own routes | per slice |

**Why not everything in one slice:**
- Every route change also changes FE callers and Bruno.
- One huge slice would block the one-at-a-time BE queue for long.
- It would mix behaviour changes (keys, 404, paging) that each need their own FE work.

**Gates:**
- CONV-1 starts only after the S-LL commit (G0), because both touch `openapi_contract.py` and the catalog test.
- It needs its own Task Approval: the MGR-7 approval excludes `app.py` envelope mapping.
- Then an independent review.

**FE effect:**
- **Web:** one error parser instead of four.
- **Mobile:** its parser already reads the M2 shape (P3); option A keeps it working.

## 4. Acceptance (for the later CONV-1 task)

- Every error path that the global handlers cover returns the chosen envelope, with the correlation header equal to the body field.
- Validation errors and the 404/403 rule behave as decided.
- The M2 Parent responses are unchanged in shape (option A), or changed exactly as decided.
- The helpers have unit tests; the OpenAPI catalog reflects the envelope.
- The FE and Bruno follow-ups are listed for each behaviour change.

## 5. Owner decisions (summary)

| ID | Question | Recommendation |
|---|---|---|
| C-D1 | Envelope: M2 Parent superset (A) or strict §9.8 (B) | A |
| C-D2 | Correlation header: `X-Request-ID` (A) or `X-Correlation-ID` (B) | A |
| C-D3 | Validation: 400 `INVALID_REQUEST` (A) or keep 422 (B) | A |
| C-D4 | 404/403 rule: in CONV-1 or per slice | none — timing only |
| C-D5 | Key format | A (existing M2 rule, to be read) |
| C-D6 | Key retention | none — owner choice |
| C-D7 | Revision transport: per family with one outcome (A), body (B), `If-Match` (C) | A |
| C-D8 | `limit` above 100: 400 (A) or clamp (B) | A |
| C-D9 | Prefix: deviation (A), gateway (B), move routes (C) | none |
| C-D10 | Parent C-P before CONV-1 | owner choice; evidence favours yes if C-D1 = A and C-D2 = A |

## 6. Not verified

- The exact `Idempotency-Key` validation rule of the M2 Parent routes.
- Lesson Library's current status code for an `If-Match` mismatch.
- Whether any deployment proxy exists.
- Every route's current 422 behaviour.
- The MGR-8 edits (P1 pending).

No test, runtime or OpenAPI generation was run for this draft.
