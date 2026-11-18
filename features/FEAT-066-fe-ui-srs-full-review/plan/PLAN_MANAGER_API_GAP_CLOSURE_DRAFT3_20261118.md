# FEAT-066 API Alignment Roadmap — Draft 3 (owner workstreams, four roles)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Planning only. It authorizes no code edit, test, check, runtime, database, branch operation, approval or decision record.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Predecessors, unchanged:** Draft 1 (38,054 bytes, SHA-256 `1015A3EE651C8B37F04FD2176FC1A8A7BF4F28A90BD46A27E1616FECA36A80CC`); Draft 2 (28,657 bytes, SHA-256 `01EAF97E077A19A31199F00E1828D9D98CD364442A6F32D69182D1D79F61B07D`) and its cold review (Sonnet 5.5 high: NOT READY, 0 P1 / 5 P2 / 9 P3; `evidence/notes/MGR_ROADMAP_DRAFT2_COLD_REVIEW_20261118.md`, 6,414 bytes, SHA-256 `0A0A3DC189517DE562D05B3CDDE95F1ECDE05989315A5427F5A4008308BBADC6`). Section 11 disposes of every finding. Draft 3 is not reviewed; whether it gets a review is the owner's choice (the replan handoff allowed one round, used by Draft 2).
- **Why Draft 3:** the owner stated the scope of the owner's own work after Draft 2: (1) seed data; (2) quota — school class capacity and video quota; (3) fix the mismatches between BE and FE after auditing every API against the SRS; (4) wire the APIs into the FE for all four roles; (5) finally, Bruno tests for everything. **Payment belongs to another teammate and is not planned here** (only its interface is listed as a dependency). Draft 3 allocates that work into lanes with an order and work-in-progress limits, and keeps every gate of Draft 2.

## 0. SRS basis

- Basis, selected by the owner on 2026-11-18 with D-209 quoted: the adopted working SRS, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` (header: v2.7-draft, Rev57 base with Rev58 to Rev69 updates; the revision table ends at Rev68 — kept OPEN / NOT VERIFIED). FEAT-063 D-209 (owner words: "SRS lấy theo bản này nha ko lấy tham chiếu theo các bản cũ nữa") makes it the single working SRS for every lane. It is byte-identical to the SRS on `origin/feature/feat063-m2-parent-teacher-foundation`.
- **Records this selection supersedes once recorded (gate O-SRS):** D-066-63 ("The repository SRS authority remains the in-repository Rev60 pointer", and its scoping of the adopted copy to MGR-2 planning); the SRS bullet of `evidence/notes/MGR_1_OWNER_DISPOSITION_20261117.md`; the authority statements in the MGR-2 plan (line 11) and the MGR-3 plan (line 8) that keep the copy out of authority. Until O-SRS is recorded in FEAT-066, those texts stand as written and this draft notes the conflict instead of editing them.
- **On `dev`:** `docs/context/SRS_AUTHORITY.md` (4,054 bytes, `032223ED...`) and the in-repository SRS (Rev60, 553,948 bytes, `70DA43A3...`) are unchanged; they change when the M2 BE branch reaches `dev` or by a separate pointer update.
- **Plan citations:** only MGR-2 (line 125), MGR-3 (line 149) and MGR-6 (line 110) carry a "Rev69 owner-input crosswalk" addendum comparing these bytes; MGR-4 and MGR-5 cite Rev60 with no comparison. All five cite Rev60 line numbers, which must be re-mapped to the adopted copy in each slice's approval package. Known mapping: the §21.2 class-create row is Rev60 line 1622 and adopted line 1649. §23.3 and the §9.8 tables are identical in both (checked by review R1 of Draft 2); other differences were not fully diffed.

Adopted-copy clauses used below: FR-T-02 line 541 and FR-T-03 line 542; UC-06 line 1453, UC-12 line 1525, UC-13 line 1537; §9.6 line 788; §9.7 line 820; §9.8 lines 847–875; §21.1 lines 1632–1641; §21.2 lines 1643–1685 (class create 1649, assignments 1650, class profiles 1651, video quota read 1678); §21.4 lines 1695–1701; §23 lines 1855–1911 (23.1 at 1857, 23.2 at 1863, 23.3 at 1877, 23.4 at 1892, 23.5 at 1901); §31.2 line 2553; §31.3 line 2569; §31.10 line 2738; FR-PL-05 line 2646; FR-PL-23 line 2664; BR-51 line 2676; BR-58 line 2683; Q168 line 2924; Q193 line 2949.

## 1. Live identity (2026-11-18)

| Item | Observed |
|---|---|
| BE worktree | `.worktrees/manager-api`, `feature/feat066-manager-api-contracts`, HEAD `1c9148e88600a101887e477541c4c4893ba1c7df` = `origin/dev`; 0 staged; 10 tracked modified; untracked 34 before this planning work, plus Draft 2, its review record and this draft — all preserved |
| FE web worktree | `.worktrees/ui`, `codex/fe-ui-web-remediation`, HEAD `297a28b1f406ab80e25d6e0aa5577e4b6f505ee2`; 1 behind / 3 ahead of `origin/dev`; 0 staged; 2 modified, 4 untracked |
| FE mobile worktree (Parent) | `.worktrees/mobile`, `feature/fe-mobile-remediation`, HEAD `73fe001e3677ed30d8cdb33cefc1f66eb82d4966`; 45 behind / 10 ahead of `origin/dev`; 22 dirty paths — not inspected further |
| M2 BE branch | `origin/feature/feat063-m2-parent-teacher-foundation` at `833df677`; merge-base with `dev` `c87d8008`; 2 commits not on `dev` (M2-S2, M2-S3), 31 `dev` commits not on it; it changes `app.py` by 130 insertions / 105 deletions and `tests/contract/test_openapi_contract_catalog.py` by 59 / 4 since the merge-base |
| Root checkout | the main repository checkout, on the M2 BE branch at `833df677`, with the owner's uncommitted FEAT-081 Bruno changes (14 modified, 32 untracked) |

| Record (BE worktree) | Bytes | SHA-256 |
|---|---:|---|
| `approvals/TASK_APPROVAL.md` | 37,893 | `70919E3C65DFB3586A24BD261F0D8B9CAA19D4D0BE393934B031F2F8A7308E5B` |
| `DECISIONS.md` (D-066-62, D-066-63 uncommitted) | 38,951 | `A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C` |
| `CONTEXT.md` | 56,197 | `1A835DA5F8A33AFE0F6D3B50F3FA329EA511D468163DF6592BA7C20E95EBD2C4` |
| `status/STATUS.md` | 49,883 | `38FC4391BBC0E3B25EA1EA71747F4D071C004F0B4393005F384AEC506EE8D52F` |
| MGR-2 / 3 / 4 / 5 / 6 / 7 plans | as Draft 2 §1 | unchanged (re-verified by review R1) |

MGR-8 edited files (equal to the pins recorded in Draft 1): `routers/lesson_library.py` 28,784 `732DB7C4...`; `infrastructure/lesson_library/service.py` 91,447 `F37DB928...`; `openapi_contract.py` 1,379,096 `35801B20...`; `tests/integration/lesson_library/test_lesson_library_api.py` 48,196 `BD0FEE18...`; `tests/unit/test_lesson_library_receipt_compatibility.py` 8,798 `B2DAFF30...`; `tests/contract/test_openapi_contract_catalog.py` 21,114 `7D242528...`.

**Boundary deviation (disclosed):** while preparing Draft 2 the coordinating session ran one `git fetch -q origin`, which the replan handoff forbade ("Do not fetch"; no network commands). It updated remote-tracking refs only; `origin/dev` stayed at `1c9148e8`. No other network or Git operation was run for Drafts 2 and 3.

## 2. The owner's five workstreams and what is excluded

| Lane | Owner's words | Scope in this roadmap | Not in scope |
|---|---|---|---|
| **L1 Seed data** | "seed data" | Reproducible synthetic data for every role flow and every later test: organizations, School Manager, Teachers (assigned and unassigned), classes at and below capacity, Parent accounts and profiles, Parent groups, lessons and versions, access grants, StoryRuns in each state, subscription states (ACTIVE, GRACE, RESTRICTED) and video-quota grants once those exist | real-child data; credentials or tokens in Git; production data |
| **L2 Quota** | "quota" — class capacity and video quota | Class capacity and admission (MGR-2: FR-T-03, §21.2 line 1649, §23.1, §23.3, §23.4); video quota (§23.5: grants, append-only usage, admission saga, balance, `409 VIDEO_QUOTA_EXCEEDED`, `GET /v1/video-quota` line 1678) | **payment**: quote/invoice/checkout, MoMo/VNPAY callbacks, slot purchase and top-up purchase (§23.2, §23.5 last bullet), refunds — another teammate |
| **L3 API audit and BE–FE alignment** | "rà lại toàn bộ api theo SRS", "sửa lệch giữa BE và FE" | Audit every runtime operation against the SRS; build one BE–FE mismatch register for all four roles; fix the mismatches BE-side or FE-side, slice by slice | payment endpoints (listed, owned elsewhere) |
| **L4 FE integration, four roles** | "ghép api vào FE ở cả 4 role" | Parent (mobile app `apps/ui-mobile`), Teacher, School Manager and Platform Admin (web app `apps/web`) | enabling any action whose BE contract is not verified |
| **L5 Bruno tests** | "viết test ở bruno đồ lun" | Extend the existing collection `features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/` (145 request files at this observation; 136-operation coverage snapshot) to every integrated operation, with assertions and negative cases, run against a disposable environment with L1 seed data | secrets in `environments/*.bru` (placeholders only) |

## 3. Facts the lanes start from

- **Web audit (FE Rev52, 63,453 bytes, `8B1EB54A...`):** 41 statically composed BE templates in the web scope; 27 page-called; 3 conditional Teacher AI calls; 9 mounted with no page caller; 2 conditional uncalled; **0 ready for new integration**. Its mismatch register D01–D12 already lists the cross-cutting gaps: idempotency missing on many commands (D07), inconsistent revision preconditions (D08), pagination not aligned to the SRS default 25 / max 100 and offset paging on accounts (D09), error envelope not the SRS envelope (`{code,message,request_id}` or FastAPI `detail`, no `correlation_id`/`retryable`) (D10), plus per-capability gaps (D01–D06, D11, D12).
- **Parent (mobile):** no API audit of the mobile app exists in the inputs read. The M2 contract freeze (on the M2 BE branch) lists 9 Parent target operations; by the M2 closure, client integration is allowed for 8 of them on the compared dimensions and not for `POST /v1/story-runs/{run_id}/cancel` (absent from the client projection); the three assistance operations stay blocked.
- **Billing and quota:** no Billing code, table or migration exists in `backend/src` or `backend/alembic` at this observation (search for `video_quota`, `capacity_period`, `organization_subscriptions`, `billing.` found none). Both quota parts start at contract design.
- **Seed:** existing bootstrap code — `backend/src/sketch2life/infrastructure/persistence/be1_bootstrap.py` (with `backend/tests/unit/test_be1_bootstrap.py`) and `infrastructure/identity/bootstrap_platform_admin.py`; M2 gates seeded by SQL inside tests. No general seed script exists.
- **Bruno:** the root checkout holds the owner's uncommitted FEAT-081 Bruno edits to this collection; L5 must start from them, not overwrite them.
- **Shared files:** every BE slice touches `interfaces/http/openapi_contract.py`; S-LL, W-CAP and the M2 branch also touch `tests/contract/test_openapi_contract_catalog.py`. BE implementation slices therefore run **one at a time**, each from the previous verified commit.

## 4. Allocation: phases, order and limits

**Work-in-progress limits:** one BE implementation slice at a time (shared OpenAPI files); at most one FE slice per app (web, mobile) at a time, and only on a verified BE slice; seed, audit and contract design have no file conflict with BE slices and run alongside.

| Phase | L1 Seed | L2 Quota | L3 Audit / alignment | L4 FE integration | L5 Bruno |
|---|---|---|---|---|---|
| **A — now** | Seed scope and data model per role (design only) | Capacity and video-quota contract questions; agree the Billing interface boundary with the payment teammate | Full API audit against the SRS: every runtime operation × four roles; extend Rev52 to the mobile Parent app; one mismatch register | none (blocked) | Inventory the collection against the operation list; plan environments with placeholders |
| **B — foundations** | Implement the seed as a synthetic, idempotent script for a disposable database | Billing contract drafts reviewed | **Cross-cutting conventions slice** (decided once, applied once): error envelope §9.8, idempotency key name/format/retention, revision/If-Match token, cursor pagination 25/100, path prefix `/api/...` versus `/v1` | FE base reconciliation for web and mobile (O-9) | Baseline requests for the already page-called routes, run on seed data |
| **C — per-role slices** | Extend seed per slice | Implement capacity admission and video-quota read/admission once the Billing boundary exists | Per-slice fixes (Manager: W-LESSON, W-ASSIGN, W-CAP; Teacher; Admin; Parent) | Wire each verified slice; Parent first (8 M2-allowed operations), then School Manager, Teacher, Platform Admin | Add requests and assertions for each slice as it is verified |
| **D — completion** | Seed covers every flow | Quota UI read states in FE | Close remaining register items or record them OPEN | Remaining slices | Full collection run on a clean seeded environment; regression record |

Phase A can start immediately and in parallel. S-LL (section 5.1) runs as soon as ENV-DB exists, independent of the phases.

## 5. Gated items carried from Draft 2 (with review fixes)

### 5.1 S-LL — MGR-7 approval, MGR-8 verification (first operational gate)

- **Scope (approved, feature-local Task Approval):** exactly six files; Parent Groups and access-grants list defaults 25 (max 100); HTTP 400 `INVALID_IDEMPOTENCY_KEY` for same-key/different-payload Lesson Library reuse; catalog and tests. Closes none of MGR-2/3/4/5/6.
- **Verification authorization:** reported by the owner in the replan handoff as "exactly two pytest commands from the BE `backend` directory: contract + unit tests, then the Lesson Library integration test", conditional on an already-provisioned disposable PostgreSQL database selected through `BE1_TEST_DATABASE_URL` (name containing `be1_acceptance`, Lesson Library migration applied); authorized writes: `evidence/notes/MGR_8_IMPLEMENTATION_VERIFICATION_20261118.md`, feature `CONTEXT.md`, feature `status/STATUS.md`, and only the scoped verification-limit note in the feature-local approval. **No repository record of this authorization exists** (confirmed by review R1). The command strings below are **Draft 1's proposal**, to be confirmed against the owner's authorization text before running:
  1. `python -m pytest tests/contract/test_openapi_contract_catalog.py tests/unit/test_lesson_library_receipt_compatibility.py`
  2. `python -m pytest tests/integration/lesson_library/test_lesson_library_api.py`
- **State:** AUTHORIZED / BLOCKED ON ENVIRONMENT / NOT RUN (latest attempt: `BE1_TEST_DATABASE_URL` absent). No duplicate authorization is needed.
- **Rules for the execution task:** re-hash the six files; run each command once; never print the URL or credentials; provision or start nothing; record commands, outputs, exit codes and pins; record the authorization in the scoped approval note.
- **Acceptance:** both commands exit 0; the catalog test confirms the defaults and the 400 code; same-key/same-payload replay unchanged; **no source or test file outside the six** changed (the four documentation writes are separate and authorized).
- **After:** independent evidence review (Sonnet 5.5 high); one commit on the owner's instruction; push and PR into `dev` per O-0.

### 5.2 W-CAP — class capacity (MGR-2; lane L2)

- **SRS-specified:** School Manager creates classes within capacity (FR-T-02, UC-06); 10 base slots plus paid add-ons (FR-T-03, §23.1); transactional check, 201 or `CLASS_CAPACITY_REACHED` (§21.2 line 1649; 409 per §9.8); GRACE allows creation, RESTRICTED blocks it (§23.3); suspension projection at the effective time (§23.4); idempotency semantics (§21.4).
- **Decided by the owner (not SRS):** D-066-63 — Billing owns capacity; BE1 needs a versioned, concurrency-safe admission; fail closed when capacity cannot be verified; the SRS §9.8 404/403 distinction applies (only the reconciliation of current BE1 behavior is left).
- **Gaps:** no Billing component exists; admission protocol (receipt/reservation, expiry, recovery); public outcome for unavailable/stale; idempotency header details; error envelope; path prefix.
- **Payment dependency:** paid add-on slots exist only after a verified payment event (§23.2) — owned by the payment teammate; W-CAP consumes "effective capacity" through the agreed Billing interface (O-PAY).
- **Files:** BE1 router `be1_registry.py`, `be1_common.py`, schema `be1_runtime.py`, models `be1_models.py`, `routers/be1_runtime.py`, `router_composition.py`, `app.py`, OpenAPI files, `test_app_composition.py`, `test_be1_synthetic_pilot_postgres.py`, new capacity tests; Billing paths unknown.
- **FE kept disabled:** class creation (M9-A). Review note kept: MGR-2 R6 P3 chronology.

### 5.3 W-ASSIGN — Teacher candidate and first assignment (MGR-3; lane L3)

- **SRS-specified:** exactly one active responsible Teacher per class and 200 with assignment revision (§21.2 line 1650); generic idempotency (§21.4); error envelope and 404/403 (§9.8); pagination (§21.1). Reassignment and offboarding are UC-12; provisioning is UC-13.
- **Decided by the owner (not SRS):** D-066-62 — only a verified Teacher of the same organization is eligible; BE1 is authoritative; revalidate at command time.
- **Gaps:** no candidate route, fields or source of same-organization Teachers; current route returns 201 without revision, takes no idempotency key, trusts the body `subject`; the stale/precondition protocol for assignments is not defined by the SRS (§21.4 names profile, lesson-plan, story and script revisions only); one-active-Teacher guarantee across all writers; FE helper path/body mismatch (D01).
- **Files:** `be1_registry.py`, `be1_runtime.py` schema, `be1_models.py` (+ migration only if approved), OpenAPI files, tests; possibly `platform_admin_accounts.py`.
- **FE kept disabled:** assignment (M9-B). Review notes kept: MGR-3 R4 P3 locator, R3 labeling.

### 5.4 W-LESSON — exact immutable LessonVersion review (MGR-6; lane L3)

- **SRS-specified:** Teacher-authored lessons become PUBLIC only after School Manager approval (FR-PL-05, BR-51, Q168); immutable versions, pinned refs not retargeted (§31.2).
- **Gaps:** exact-version read; binding option A (hash snapshot on grant) or B (immutable version row); superseded pending-grant outcome; decision precondition; Lesson Library error envelope; concurrency.
- **Files:** `routers/lesson_library.py`, `contracts/schemas/lesson_library.py`, `infrastructure/lesson_library/service.py`, `tables.py` (only if approved), OpenAPI files, `test_lesson_library_api.py` — three shared with S-LL, so edits start only from the S-LL commit.
- **FE kept disabled:** the exact-version review slice (M9-C); Platform Admin moderation is a separate unplanned flow (D06).

### 5.5 Excluded: W-GROUP (MGR-4) and W-CONSENT (MGR-5)

| Workstream | Status | Reopen conditions |
|---|---|---|
| W-GROUP | Excluded by D-066-62; group list/create unchanged | A new owner decision enabling Manager-to-Parent discovery/invitation (FR-PL-23, BR-58 make membership revocable but do not define Manager discovery), plus an approved tenant-scoped contract (verified Parent reference, minimum fields, authority, acceptance, expiry, revoke, audit, membership read with revision, idempotent revoke) |
| W-CONSENT | Excluded; policy OPEN; Parent is the consent actor; staff `pending` is not Parent consent | An owner decision that a distinct school-managed consent workflow exists (actor, legal basis, evidence, effective state, revoke, read visibility). Review R1 of MGR-5 left two P2 items: the write gate is a policy gate, not verified backend enforcement; and consent-list pagination against §21.1 (still open in the plan). The same report's MGR-6 part is historical (superseded pin) |

The consent record/revoke and Parent-group invitation/member-removal routes are mounted in BE with no Manager FE write caller; "unavailable" here is a policy and FE gate, not server enforcement (decision O-X).

### 5.6 FE integration path (all roles)

For each FE slice, in this order and never in parallel with another slice of the same app: (1) the BE slice is verified, committed and pinned; (2) the app's branch is reconciled to that base by an owner-approved method — no merge, rebase, cherry-pick or file copy without that instruction, and all dirty paths preserved; (3) the audit and source pins are refreshed against the reconciled base; (4) a separate FE allowlist and Task Approval; (5) one API slice is integrated; (6) only separately approved FE checks run; (7) evidence and an independent review come before the UI control is enabled. Unavailable actions stay disabled throughout.

Carried, no owner yet: the already page-called `GET /api/be1/v1/organizations/{organization_id}/classes` has no cursor and `ClassesPage` does not paginate (MGR-9 plan §4.1) — an L3 register item.

## 6. Lane cards

### L1 Seed data

- **Goal:** one reproducible, idempotent, synthetic seed for a disposable local database that every lane uses (FE demos, Bruno runs, gate tests).
- **Content:** per role — Platform Admin; organization with School Manager; Teachers assigned and unassigned; classes up to capacity; Parent accounts and Parent profiles (36–120 months, `SYNTHETIC_DEV`); Parent groups; lessons with several versions and grants (pending, approved, superseded); StoryRuns in representative states; later, subscription states and quota grants/usage when L2 defines them.
- **Rules:** synthetic only (no real-child data); no password, token or Firebase credential in Git — identities seeded by reference, authentication via the existing local verifier or the owner's local setup; a marker on every seeded row; runs only against a disposable database whose name is checked (for example `be1_acceptance` or a `seed` marker); never against the task database `sketch2life_m2_s1a` or shared databases.
- **Gate:** seed design reviewed; a Task Approval with exact files (a seed script and its tests; `be1_bootstrap.py` only if extended) and a command ceiling; owner-run against the disposable database.
- **Acceptance:** two consecutive runs produce the same row set; every role can sign in locally and see its data; L5 runs against it.

### L2 Quota

- **Class capacity:** W-CAP above.
- **Video quota (§23.5):** Parent quota per Parent account; Teacher video counts against the organization's school quota (no Teacher pool); Billing owns `billing.video_quota_grants` and append-only `billing.video_quota_usage`; admission through a versioned Billing port inside the Story saga (`ADMISSION_PENDING` → `ACCEPTED`/`ADMISSION_REJECTED`), no cross-module transaction; one unit per accepted full-video request, never refunded after commit; `409 VIDEO_QUOTA_EXCEEDED`; balance computed only in Billing; read `GET /v1/video-quota` (§21.2 line 1678) with scope derived from the verified actor.
- **Open:** included monthly amount (fixed after a synthetic cost/latency benchmark); purchase/allocation authority and top-up (Q193, §31.10 (2), (6)) — top-up purchase is payment work; the video-generation flow that consumes admission is not built yet.
- **Gate:** the Billing interface agreed with the payment teammate (O-PAY); contract plan and review; Task Approval; isolated concurrency/idempotency tests.
- **FE:** read-only quota summary per role once `GET /v1/video-quota` is verified; purchase actions belong to the payment work.

### L3 API audit and BE–FE alignment

- **Audit:** every runtime operation (the M2 freeze lists 151 on the M2 branch; `dev` must be re-counted on its own base) × the four roles: route, DTO, auth/scope, status, error envelope, idempotency, revision, pagination, prefix — compared with the SRS and with each FE caller (web from Rev52; mobile Parent new).
- **Register:** one table, each item classified "fix in BE", "fix in FE", "needs owner decision" or "excluded" (payment, MGR-4/5).
- **Order of fixes:** the cross-cutting conventions slice first (D07–D10), because every later slice depends on one envelope, one idempotency convention, one revision token and one pagination rule; then per-capability slices one at a time.
- **Gate:** each fix slice gets its own Task Approval and verification; audit output is a document, reviewed once.

### L4 FE integration, four roles

| Role | App | First slice | Later slices |
|---|---|---|---|
| Parent | mobile (`apps/ui-mobile`, mobile worktree 45 behind / 10 ahead of `dev`) | the 8 M2-allowed Parent operations (profiles create/read/update/list/deletion request; StoryRun create, active/current, read) | cancel (after it is in the projection); video quota read |
| School Manager | web | existing 27-route baseline reconciled to the conventions slice | W-LESSON, W-ASSIGN, W-CAP slices; quota read |
| Teacher | web | baseline reconciled; Teacher AI calls stay conditional | lesson authoring and class-profile items from the register |
| Platform Admin | web | account management (offset paging and missing idempotency per D07/D09) | moderation only after its own contract (D06) |

### L5 Bruno tests

- Start from the existing collection including the owner's uncommitted FEAT-081 edits in the root checkout.
- One folder per role and slice; each request has status, envelope and key-field assertions; negative cases for out-of-scope 404, same-key replay, same-key/different-payload 400, stale revision 409, pagination bounds.
- Environments contain placeholders only; real tokens come from the local shell or the owner's machine, never Git.
- Runs only against a disposable seeded environment; a collection run record per phase (D: the full run).
- **Gate:** the Bruno CLI or runner and the environment boundary are approved per run, like any test command.

## 7. Dependency graph and critical path

```text
ENV-DB ──> S-LL verify ──> evidence review ──> S-LL commit ──┐
O-0 (order of M2 branch and S-LL into dev) ───────────────────┤
                                                              v
L3 audit ──> conventions slice (D07–D10) ──> per-capability BE slices (one at a time) ──> FE slice per role (one per app) ──> Bruno per slice
L1 seed design ──> seed implementation ───────────────────────────────────────────────┘ (feeds FE checks and Bruno)
L2 Billing boundary (O-PAY) ──> capacity / video-quota contracts ──> BE slices (in the one-at-a-time queue)
O-9 FE base reconciliation (web, mobile) ──> any FE slice
```

Critical path: ENV-DB → S-LL → O-0 → L3 audit → conventions slice → first per-capability slice → FE slice → Bruno. Seed and quota contract design run beside it and must be ready before the first FE slice and before W-CAP respectively.

## 8. Owner decisions

| ID | Question | Recommendation (only where SRS or source supports one) | Consequence | Next artifact |
|---|---|---|---|---|
| O-0 | Order in which the M2 BE branch (`833df677`) and the S-LL commit reach `dev` | No recommendation: depends on merge logistics. Their hunks in `test_openapi_contract_catalog.py` are adjacent and may conflict | The second to land reconciles that test file (and `app.py` for the M2 branch) | Owner instruction for each PR |
| O-SEQ | First per-capability BE slice after the conventions slice | Not W-CAP first: source has no Billing component, so W-CAP cannot be built yet | Order of W-LESSON and W-ASSIGN | Approval package |
| O-CONV | Adopt the cross-cutting conventions slice (§9.8 envelope, idempotency key, revision token, cursor 25/100, prefix) as the first L3 fix | SRS §9.8, §21.1 and §21.4 specify the semantics; header name, token format and prefix mapping are open | Every later slice and FE parser uses one convention | Conventions contract plan |
| O-PAY | Interface boundary with the payment teammate: who owns the Billing module, the capacity read/admission port, the video-quota admission port | No recommendation: ownership is a team decision | L2 can start implementation only after this | Interface note agreed by both owners |
| O-SEED | Seed scope and the disposable-database rule (name check, marker) | Synthetic only (SRS synthetic-only demo rule §24.1; M2 practice) | Seed usable by all lanes and Bruno | Seed design |
| O-2a | Billing contract owner and whether a Billing service will exist | No recommendation | W-CAP blocked until answered | Billing contract draft |
| O-2b | Public outcome when Billing is unavailable/stale (fail closed decided by D-066-63) | No recommendation | M9-A error states | MGR-2 disposition |
| O-2c | Idempotency header name, key format, retention | Covered by O-CONV | — | conventions plan |
| O-3a | Source of verified same-organization Teachers | No recommendation | W-ASSIGN blocked until answered | identity note |
| O-3b | Candidate fields and privacy | Minimum fields; no provider IDs or e-mail without approval | candidate DTO | MGR-3 disposition |
| O-3c | UC-12 reassignment/offboarding separate | Yes, separate (the plan's proposal) | W-ASSIGN = first assignment | MGR-3 disposition |
| O-3d | Assignment revision token and stale precondition | SRS requires 200 + revision; token open (O-CONV) | M9-B If-Match | MGR-3 disposition |
| O-6a | Binding option A or B | No recommendation | migration in or out of scope | MGR-6 disposition |
| O-6b | Superseded pending-grant outcome | No recommendation | M9-C states | MGR-6 disposition |
| O-6c | Decision precondition shape | No recommendation | decision DTO | MGR-6 disposition |
| O-5 | Distinct school-managed consent workflow? | Keep excluded unless a legal basis is defined | consent writes stay off | MGR-5 answer |
| O-X | Disable the mounted consent-write and invitation/member-removal routes server-side? | No recommendation | server enforcement versus FE-only gate | small approval if chosen |
| O-9 | Reconciliation method for the web branch (1/3) and the mobile branch (45/10) | No recommendation; dirty paths must be preserved | gates all FE slices | reconciliation instruction |
| O-MOB | Run the L3 audit on the mobile Parent app in the mobile worktree | Yes: no Parent API audit exists | Parent slice can be planned exactly | audit document |
| O-BRU | Bruno runner and environment boundary for L5 | No recommendation | how Bruno runs are approved | Bruno run plan |
| O-SRS | Record the D-209 SRS selection in FEAT-066 (superseding the texts in §0) and update `SRS_AUTHORITY.md` on `dev` | Follows D-209 | one SRS for every FEAT-066 plan | decision row or merge |

**Environment, not a decision:** ENV-DB (section 5.1). **Nonblocking notes kept open:** MGR-2 R6 P3; MGR-3 R4 P3 and R3 labeling; the SRS header discrepancy.

## 9. Per-slice acceptance checks

| Slice | Before VERIFIED | Before FE-INTEGRATED |
|---|---|---|
| S-LL | as 5.1 | none unless a DTO changed |
| Conventions | every touched route returns the §9.8 envelope; idempotency and revision behave as decided; list defaults/max as decided | FE parsers read one envelope; no client-invented retry semantics |
| W-CAP | verified Billing admission; concurrency never exceeds capacity; 201 / 409 / GRACE / RESTRICTED / unavailable as approved; replay | M9-A: key sent; all states shown; no client capacity logic |
| W-ASSIGN | same-organization candidates only; command-time revalidation; one active Teacher under concurrency; 200 + revision; replay; stale conflict | M9-B: exact path/DTO; no free-typed identity |
| W-LESSON | exact version/hash read; decision bound to it; superseded outcome; no current-head fallback; replay | M9-C: controls only on exact match |
| Video quota | append-only usage; one unit per accepted request; 409 on exhaustion; balance only in Billing | read-only summary per role |
| Seed | idempotent; marker on every row; disposable database only | every role sees its data |
| Bruno (per slice) | requests and assertions pass on the seeded environment, positive and negative | — |

Each BE slice: own Task Approval, exact allowlist, command ceiling, one commit on the owner's instruction, independent evidence review (Sonnet 5.5 high). Each FE slice: as 5.6.

## 10. Exclusions and limits of this draft

- No BE/FE source, test, OpenAPI, schema, migration, SRS, `SRS_AUTHORITY.md`, decision, Task Approval, CONTEXT, STATUS or Bruno file change; no test, build, typecheck, lint, validator, diff-check, OpenAPI generation, runtime, database, Docker, install, network/provider, Modal or emulator command for this draft. Payment work is not planned.
- No stage, commit, push, merge, rebase, cherry-pick, reset, restore, clean, stash or file copy. Dirty paths in every worktree and in the root checkout are preserved. The one fetch of Draft 2 is disclosed in section 1.
- A plan review ACCEPT is not an approval.

## 11. Disposition of the Draft 2 review findings

| ID | Disposition |
|---|---|
| F-01 | §0: addenda named for MGR-2/3/6 only; MGR-4/5 cite Rev60 without comparison |
| F-02 | §0: superseded texts listed; O-SRS records them |
| F-03 | §1 and §10: stated as a boundary deviation |
| F-04 | §5.1: command strings marked as Draft 1's proposal |
| F-05 | §8: O-0 has no recommendation and says "may conflict"; O-SEQ keeps only the evidence-based reason |
| F-06 | §1: corrected numbers |
| F-07 | §5.5: both MGR-5 P2 items; the MGR-6 part historical |
| F-08 | §5.2 to §5.4: complete candidate file lists; the overlap conclusion is stated in §3 |
| F-09 | §1: record pins and the six MGR-8 file pins |
| F-10 | §5.2, §5.3: SRS-specified and owner-decided separated; O-2d removed as decided by D-066-63 |
| F-11 | §5.6: FE path card with one slice at a time and the branch rule; class-list pagination gap carried |
| F-12 | §5.1: "no source or test file outside the six" |
| F-13 | §0: each listed clause is used in a card or lane; Rev60-to-adopted mapping note |
| F-14 | §2 of Draft 2 replaced: D-066-62/63 are "not yet committed" (§1 table) |

## 12. Next action for the owner

1. **ENV-DB, then S-LL verification** (already authorized; confirm the two command strings against your authorization text).
2. **Start Phase A in parallel:** L3 full API audit (web plus mobile Parent, O-MOB); L1 seed design (O-SEED); L2 Billing boundary with the payment teammate (O-PAY) and the quota questions; L5 Bruno inventory.
3. Decide O-0, O-CONV and O-9 before Phase B; then O-SEQ and the questions of the chosen first slice.
