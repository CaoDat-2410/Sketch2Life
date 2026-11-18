# FEAT-066 Manager API Gap Closure — Draft 2 (dependency-driven roadmap)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Planning only. This draft authorizes no code edit, test, check, runtime, database, branch operation, approval or decision record. Draft 1 (`plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT1_20261117.md`, 38,054 bytes, SHA-256 `1015A3EE651C8B37F04FD2176FC1A8A7BF4F28A90BD46A27E1616FECA36A80CC`) is preserved unchanged and remains the historical record of MGR-0 to MGR-10 as first numbered.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5), from the owner's replan handoff `tmp/CLAUDE_FEAT066_MANAGER_ROADMAP_REPLAN_HANDOFF_20261118.md` (repository-root scratch, git-ignored). **Owner:** Person 2.
- **What changed from Draft 1:** the linear MGR-0 to MGR-10 list is replaced by workstreams with separate states, a dependency graph, a critical path and parallel lanes; the narrow MGR-7/MGR-8 Lesson Library slice is separated from the MGR-2/3/6 contract workstreams; the MGR-8 environment gate is first; shared-file overlap is measured, not assumed; MGR-4, MGR-5 and MGR-10 are kept out of the first wave with explicit reopen conditions; the SRS basis follows the owner's selection below.

## 0. SRS basis for this draft (owner selection, 2026-11-18)

- The owner selected, in the coordinating session and with D-209 quoted, the adopted copy as the basis of this draft: `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` (self-described v2.7-draft, Rev57 base with Rev58 to Rev69 updates; header date 2026-11-13). FEAT-063 decision D-209 (owner words: "SRS lấy theo bản này nha ko lấy tham chiếu theo các bản cũ nữa") makes this copy the single working SRS for every lane.
- **Branch fact:** D-209 and the adopted bytes are on `origin/feature/feat063-m2-parent-teacher-foundation` (`833df67789b9594ed41f83d672962ad99f1d2abd`), not on `origin/dev`. This BE worktree (based on `origin/dev`) still has `docs/context/SRS_AUTHORITY.md` 4,054 bytes / `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F` pointing to Rev60, and the in-repository SRS file is Rev60, 553,948 bytes / `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`. This draft does not edit either; the pointer on `dev` changes when the M2 BE branch reaches `dev` (gate O-0 below).
- **Header discrepancy:** the copy's header names Rev69 while its revision-history table ends at Rev68. Kept OPEN / NOT VERIFIED.
- **Consequence for the MGR plans:** MGR-2, MGR-3, MGR-5 and MGR-6 cite Rev60 line numbers. Each already carries a "Rev69 owner-input crosswalk" addendum comparing these same bytes (`B9B1F42D...`) and records that the copy adds no Billing API, candidate contract or exact-version contract. Before any of them is approved for implementation, its Rev60 line citations must be re-mapped to the adopted copy (part of each slice's approval package, not a new review cycle).
- **Relevant clauses located in the adopted copy:** FR-T-02 line 541; FR-T-03 line 542; UC-06 line 1453; UC-12 line 1525; UC-13 line 1537; §9.6 line 788; §9.7 line 820; §9.8 lines 847–875; §21.1 lines 1632–1641 (pagination 1640); §21.2 lines 1643–1685 (class create 1649, assignments 1650, class profiles 1651); §21.4 lines 1695–1701; §23 lines 1855–1900 (23.1 at 1857, 23.3 at 1877, 23.4 at 1892); §31.2 line 2553; §31.3 line 2569; §31.10 line 2738; FR-PL-05 line 2646; FR-PL-23 line 2664; BR-51 line 2676; BR-58 line 2683; Q168 line 2924; Q193 line 2949.

## 1. Live identity at this observation

| Item | Observed (2026-11-18) |
|---|---|
| BE worktree | `.worktrees/manager-api`, branch `feature/feat066-manager-api-contracts`, HEAD `1c9148e88600a101887e477541c4c4893ba1c7df` = `origin/dev`; 0 staged; 10 tracked modified, 34 untracked — all pre-existing, preserved |
| FE worktree | `.worktrees/ui`, branch `codex/fe-ui-web-remediation`, HEAD `297a28b1f406ab80e25d6e0aa5577e4b6f505ee2`; 1 behind / 3 ahead of `origin/dev`; 0 staged; 2 tracked modified, 4 untracked — preserved |
| M2 BE branch | `origin/feature/feat063-m2-parent-teacher-foundation` at `833df677`; merge-base with `origin/dev` is `c87d8008`; 2 commits not on `dev` (M2-S2, M2-S3), 31 `dev` commits not on it |
| Git note | one `git fetch -q origin` was run during this observation (remote-tracking refs only; `origin/dev` unchanged at `1c9148e8`). No other Git operation. |

Input pins (all re-hashed for this draft):

| Input | Bytes | SHA-256 | Review on record |
|---|---:|---|---|
| MGR-2 plan | 28,624 | `3F5AEA621BA5B9C182FC547FABD2C501140001755C29FD4826B583A6EB360FB7` | R6 `5B1E0E31...`, PASS WITH NOTES (P3 chronology) |
| MGR-3 plan | 34,432 | `80762D84A5C21BF2182D2214835B4F29CFA47CF31D292344FC987FB636F78F7B` | R4 `D92B0DD6...`, ACCEPT WITH NOTES (P3 locator, R3 labeling) |
| MGR-4 plan | 30,075 | `7248971517E56B06AC2F0532BE7B012FEFCD096280418BA710264E8F8514FFFF` | R2 report `149A998A...`, ACCEPT WITH NOTES |
| MGR-5 plan | 10,846 | `0174E6714379322E8904BEBD3BD0F18524105A871C20A1AF34EBF034FE3D5FBE` | R1 report `9B26DB14...`, ACCEPT WITH NOTES (with a P2 wording note: the write gate is a policy gate, not verified backend enforcement); owner brief `E3EB6481...` OPEN |
| MGR-6 plan | 24,165 | `BEB43ECBBF9E05A9949B1BC5407C3736886AA8BD83D52611A22BA037621721BC` | R6 `3E7BF9A4...`, ACCEPT, no findings |
| MGR-7 package | 34,177 | `37B412F3E10403238FDC9B940C437941293AD91F78EFDB76E61F5DE4C97E3FC3` | R2 `68947A73...`, ACCEPT; feature-local Task Approval "FEAT-066 MGR-7 — bounded BE contract-conformance implementation" (APPROVED_FOR_IMPLEMENTATION, six files) |
| MGR-1 owner disposition | 4,016 | `B32D4CBC47811960A5DE2B2F1A3CAA9C84B64F8F9DC7F79CD0CD68F92F37883A` | D-066-62 (working tree only, absent at pinned HEAD) |
| MGR-9 plan (FE worktree) | 43,006 | `1547F32C67CA4228DAB37DAD6BD77BDFEB3BB2040E9F17FE631B460565E2CEA3` | R2 `C235A560...`, ACCEPT |
| FE Rev52 audit (FE worktree) | 63,453 | `8B1EB54A05A4B4A6FF502D45B278DBFE3B885EC278229A7ADEA98D3DA7ECA50A` | — |

MGR-8 edit state: the six MGR-7 files are modified relative to HEAD (`git diff --stat`: 6 files, 207 insertions, 10 deletions). Their per-file pins are recorded in Draft 1's checkpoint of 11:37 and are to be re-hashed at the start of the MGR-8 execution task.

## 2. Historical IDs and current scopes

| ID | Draft 1 meaning | Current scope (this draft) |
|---|---|---|
| MGR-0 | Route inventory | **Done** (source/evidence level; no runtime claim). Its 17-route matrix and FE Rev52 audit feed every lane. |
| MGR-1 | Owner policy dispositions | **Done**: D-066-62 (discovery/invitation off; no staff consent on Parent's behalf; same-organization verified Teacher). D-066-63 sets the MGR-2 direction. Both are in the working tree only; they reach Git with the next FEAT-066 commit. |
| MGR-2 | Class capacity contract | **W-CAP**: Billing-owned class-capacity contract; still a contract-design workstream |
| MGR-3 | Teacher candidate/assignment | **W-ASSIGN**: candidate read and first assignment; UC-12 reassignment/offboarding proposed as separate |
| MGR-4 | Parent groups, invitation, membership | **W-GROUP**: excluded/deferred (D-066-62) |
| MGR-5 | Consent policy | **W-CONSENT**: excluded/deferred; policy OPEN |
| MGR-6 | Exact LessonVersion review | **W-LESSON**: exact-version read and decision binding for School Manager review |
| MGR-7 | Draft 1: one broad approval package for MGR-1–6. **Live:** a narrow six-file Lesson Library conformance approval | **S-LL**: list defaults 25 (max 100) for Parent Groups and access grants; HTTP 400 `INVALID_IDEMPOTENCY_KEY` for same-key/different-payload Lesson Library reuse; OpenAPI catalog and tests. It closes **none** of MGR-2/3/4/5/6. |
| MGR-8 | Draft 1: implement all approved BE slices | **S-LL verification**: run the two authorized pytest commands on the existing S-LL edits, record evidence. Later BE slices get their own implementation IDs (section 5), not "MGR-8". |
| MGR-9 | FE integration | **W-FE**: FE slices M9-A (class create), M9-B (assignment), M9-C (exact-version review), each gated on its BE slice |
| MGR-10 | Quota, billing, feedback, inbox | **Later feature group** outside this roadmap's first wave |

## 3. States used in this draft

Each workstream moves through separate states; one never implies the next:

`PLAN` (draft exists) → `PLAN-REVIEWED` (cold review ACCEPT/PASS, plan quality only) → `OWNER-DISPOSED` (owner answers the contract questions) → `APPROVED` (Task Approval with exact allowlist and command ceiling) → `EDITED` (source changed within the allowlist) → `VERIFIED` (authorized commands ran and passed, evidence written) → `EVIDENCE-REVIEWED` → `FE-INTEGRATED` (separate FE approval and evidence).

## 4. Status matrix

| Workstream | State now | Blocking item | FE capability kept disabled |
|---|---|---|---|
| S-LL (MGR-7/8) | APPROVED + EDITED; **verification AUTHORIZED / BLOCKED ON ENVIRONMENT / NOT RUN** | a pre-existing disposable PostgreSQL database selected through `BE1_TEST_DATABASE_URL` | none newly enabled; the two list pages already consume cursors |
| W-CAP (MGR-2) | PLAN-REVIEWED | owner disposition on Billing protocol and outcomes (O-2a..O-2d) | class creation (M9-A) |
| W-ASSIGN (MGR-3) | PLAN-REVIEWED | owner disposition (O-3a..O-3d) | Teacher assignment and candidate list (M9-B) |
| W-LESSON (MGR-6) | PLAN-REVIEWED | owner disposition (O-6a..O-6c); S-LL verified and committed first (shared files) | exact-version review (M9-C); existing ID-only guard stays as is |
| W-GROUP (MGR-4) | PLAN-REVIEWED; **EXCLUDED** (D-066-62) | reopen conditions, section 7 | invitation, member removal |
| W-CONSENT (MGR-5) | PLAN-REVIEWED; **EXCLUDED / policy OPEN** | owner policy O-5 | consent record/revoke |
| W-FE (MGR-9) | PLAN-REVIEWED | BE slices verified; FE base reconciliation method (O-9) | all three slices |
| MGR-10 | not planned here | separate decisions (Q193 OPEN) | quota, billing, feedback, inbox |

**Ready-for-new-FE-integration count: 0.**

## 5. Dependencies, shared files and lanes

### 5.1 Shared-file overlap (measured from the plans' candidate allowlists)

| File | S-LL (MGR-7/8) | W-CAP | W-ASSIGN | W-LESSON |
|---|---|---|---|---|
| `interfaces/http/openapi_contract.py` | edited | candidate | candidate | candidate |
| `tests/contract/test_openapi_contract_catalog.py` | edited | candidate | (catalog tests) | — |
| `interfaces/http/openapi_srs_v22.py` | — | candidate | candidate | candidate if projection in scope |
| `interfaces/http/routers/lesson_library.py` | edited | — | — | candidate |
| `infrastructure/lesson_library/service.py` | edited | — | — | candidate |
| `tests/integration/lesson_library/test_lesson_library_api.py` | edited | — | — | candidate |
| `interfaces/http/routers/be1_registry.py` | — | candidate | candidate | — |
| `contracts/schemas/be1_runtime.py` | — | candidate | candidate | — |
| `infrastructure/persistence/be1_models.py` (+ migration if approved) | — | candidate | candidate | — |
| `interfaces/http/app.py`, `router_composition.py` | — | candidate | — | — |
| Billing port/adapter | — | **unknown — not found in source** | — | — |

Conclusions: (1) every BE slice touches the shared OpenAPI catalog, so BE **implementation** slices run one at a time, each starting from the previous slice's verified commit; (2) W-LESSON shares three Lesson Library files with S-LL and cannot be edited before S-LL is verified and committed; (3) W-CAP and W-ASSIGN share BE1 router, schema and model files; (4) contract design, owner dispositions and approval packages for W-CAP, W-ASSIGN and W-LESSON have no file conflict and can run in parallel now.

**Cross-lane integration risk:** the M2 BE branch (`833df677`) changes `app.py` (+235/−109 lines from `c87d8008`) and `tests/contract/test_openapi_contract_catalog.py` (+63), and `dev` has changed `app.py` since. S-LL also edits `test_openapi_contract_catalog.py`. Whichever of the M2 branch and the S-LL commit reaches `dev` second will need a reconciliation of that test file (and `app.py` for M2). The order is owner decision O-0.

### 5.2 Dependency graph

```text
O-0 (M2 branch vs S-LL order on dev) ─────────────────────────────┐
                                                                   v
ENV-DB ──> S-LL verify ──> S-LL evidence review ──> S-LL commit ──> [dev base for BE slices]
                                                                   │
O-2a..d ──> W-CAP approval pkg ──> APPROVED ──> EDIT ──> VERIFY ──>│──> M9-A
O-3a..d ──> W-ASSIGN approval pkg ──> APPROVED ──> EDIT ──> VERIFY ─│──> M9-B
O-6a..c ──> W-LESSON approval pkg ──> APPROVED ──> EDIT* ──> VERIFY ┘──> M9-C
                                   (*only after S-LL commit; one BE slice at a time on the shared OpenAPI files)
O-9 (FE base reconciliation method) ──> FE base reconciled ──> refreshed audit/pins ──> FE Task Approval per slice ──> M9-x
W-GROUP, W-CONSENT: excluded until section 7 conditions; MGR-10: separate feature group
```

### 5.3 Critical path

ENV-DB → S-LL verification → evidence review → owner commit instruction for S-LL → (O-0 decided) → first BE slice approved → edit → verify → evidence → FE base reconciled (O-9) → FE Task Approval for that slice → FE integration and evidence. The first BE slice to follow S-LL is chosen by owner gate O-SEQ (recommendation: W-LESSON, because its owner questions are the narrowest and do not depend on an absent Billing service; W-CAP needs a Billing contract that does not exist in source).

### 5.4 Parallel lanes now (no file overlap, planning only)

| Lane | Can proceed while ENV-DB is blocked | Output |
|---|---|---|
| L1 | W-CAP owner questions O-2a..O-2d; Billing owner named | MGR-2 disposition record |
| L2 | W-ASSIGN owner questions O-3a..O-3d; identity source named | MGR-3 disposition record |
| L3 | W-LESSON owner questions O-6a..O-6c | MGR-6 disposition record |
| L4 | O-0 and O-9 branch decisions | recorded methods, no branch operation yet |
| L5 | Re-map Rev60 citations of the chosen next slice to the adopted SRS | part of that slice's approval package |

No lane edits source, runs tests or writes decision/approval records without its own owner instruction.

## 6. Workstream cards

### 6.1 S-LL — MGR-7 approval, MGR-8 verification (first operational gate)

- **Scope (approved):** exactly the six files of the MGR-7 Task Approval; behavior as listed in section 2. No route, DTO, schema, migration, `app.py` error mapping or FE file.
- **Verification authorization (as reported by the owner in the replan handoff; not found in any repository record at this observation):** two commands from `.worktrees/manager-api/backend`:
  1. `python -m pytest tests/contract/test_openapi_contract_catalog.py tests/unit/test_lesson_library_receipt_compatibility.py`
  2. `python -m pytest tests/integration/lesson_library/test_lesson_library_api.py`
  Conditional on an already-provisioned local disposable PostgreSQL database selected through `BE1_TEST_DATABASE_URL`, whose name contains `be1_acceptance`, with the Lesson Library migration applied. Authorized writes: `evidence/notes/MGR_8_IMPLEMENTATION_VERIFICATION_20261118.md`, feature `CONTEXT.md`, feature `status/STATUS.md`, and only the scoped verification-limit note in the feature-local approval.
- **State:** AUTHORIZED / BLOCKED ON ENVIRONMENT / NOT RUN — the latest owner-run attempt found `BE1_TEST_DATABASE_URL` absent, so neither command ran. No duplicate authorization is needed.
- **Execution rules for the later task:** re-hash the six files first; run only the two commands, once each; never print the database URL or credentials; do not provision or start a database or service; record exact commands, outputs, exit codes and final pins; record the authorization itself in the scoped approval note, since no repository record of it exists yet.
- **Acceptance:** both commands exit 0; the catalog test confirms the list defaults and the 400 code; same-key/same-payload replay unchanged; no file outside the six changed.
- **After verification:** independent review of the evidence (Sonnet 5.5 high), then one commit of the S-LL work on the owner's instruction. Push and the PR/merge into `dev` are separate owner instructions and depend on O-0.
- **What it does not do:** it enables no new FE action and closes no MGR-2/3/4/5/6 gap.

### 6.2 W-CAP — class capacity (MGR-2)

- **SRS-resolved:** School Manager creates classes within capacity; 10 included slots plus purchased slots (FR-T-03, line 542); transactional capacity check, 201 or `CLASS_CAPACITY_REACHED` (§21.2 line 1649; 409 in §9.8); Billing owns capacity (§9.7, §23.1); GRACE allows creation, RESTRICTED blocks it (§23.3); suspension at effective time (§23.4); idempotency semantics and 400 `INVALID_IDEMPOTENCY_KEY` (§21.4, §9.8); uniform 404 for out-of-scope (§9.8).
- **Technical gaps:** no Billing capacity port, adapter or service exists in source; versioned concurrency-safe admission protocol (receipt/reservation, expiry, recovery); public outcome for Billing unavailable or stale (fail closed is decided, the code is not); idempotency header name, key format, retention; error envelope (current BE1 error lacks `correlation_id`/`retryable`); `/v1` versus `/api/be1/v1` mapping; current 403 behavior versus target 404.
- **Owner decisions:** O-2a to O-2d (section 8).
- **Review notes kept open:** R6 P3 chronology note — nonblocking.
- **Likely files:** BE1 router/schema/models, composition, OpenAPI files, new capacity tests; Billing paths unknown.
- **Approval/evidence gate:** a Billing contract exists and is reviewed; W-CAP approval package with exact allowlist (including Billing paths), command ceiling and isolated concurrency test environment; owner Task Approval.
- **FE kept disabled:** class creation; client-side capacity checks forbidden.

### 6.3 W-ASSIGN — Teacher candidate and first assignment (MGR-3)

- **SRS-resolved:** exactly one active responsible Teacher per class; 200 with assignment revision (§21.2 line 1650); idempotency and stale semantics (§21.4); error envelope and 404/403 (§9.8); pagination (§21.1); same-organization verified Teacher eligibility (D-066-62).
- **Technical gaps:** no candidate-read route, fields or source of verified same-organization Teachers (Teacher accounts can exist without an organization assignment); current route returns 201 without revision, accepts no idempotency key, trusts the body `subject`; no persistence guarantee of one active Teacher across all writers; FE helper path and body mismatch the BE route.
- **Owner decisions:** O-3a to O-3d.
- **Review notes kept open:** R4 P3 locator (MGR-1 attachment path unavailable) and R3 labeling — nonblocking.
- **Likely files:** `be1_registry.py`, `be1_runtime.py` schemas, `be1_models.py` (+ migration only if approved), OpenAPI files, tests; possibly `platform_admin_accounts.py`.
- **Gate:** owner disposition; approval package; Task Approval; isolated PostgreSQL concurrency test environment.
- **FE kept disabled:** assignment and free-typed identity.

### 6.4 W-LESSON — exact immutable LessonVersion review (MGR-6)

- **SRS-resolved:** Teacher-authored lesson becomes PUBLIC only after School Manager approval (FR-PL-05 line 2646, BR-51 line 2676, Q168 line 2924); published versions are immutable and pinned refs are not retargeted (§31.2); pagination, idempotency, error envelope as above.
- **Technical gaps:** no exact-version read; grant/hash binding option A (hash snapshot on grant) versus B (resolve through an immutable version row); outcome for a pending grant whose version is superseded; decision precondition shape; Lesson Library error envelope fields; concurrency.
- **Owner decisions:** O-6a to O-6c.
- **Review notes:** none open (R6 ACCEPT).
- **Likely files:** `lesson_library.py` router, schemas, service, `tables.py` only if approved, OpenAPI files, `test_lesson_library_api.py` — **three shared with S-LL**.
- **Sequencing:** edit only after the S-LL commit exists; start from that commit.
- **Gate:** owner disposition; approval package; Task Approval.
- **FE kept disabled:** the new exact-version review slice; Platform Admin moderation stays a separate, unplanned flow.

## 7. Excluded and later work

| Workstream | Status | Exact conditions to reopen |
|---|---|---|
| W-GROUP (MGR-4) | Excluded by D-066-62. Group list/create stay as they are | A new owner decision that enables Manager-to-Parent discovery/invitation, plus an approved tenant-scoped contract: verified Parent reference, minimum visible fields, authority, acceptance, expiry, revoke, audit, membership read with revision, idempotent revoke. |
| W-CONSENT (MGR-5) | Excluded; policy OPEN. Parent remains the consent actor; staff `pending` is not Parent consent | An owner decision that a distinct school-managed consent workflow exists, with actor, legal basis, evidence, effective state, revoke and read visibility defined; a read-only visibility change needs its own decision on fields and pagination. |
| MGR-10 | Later separate feature group | Separate decisions for quota purchase/allocation (Q193 OPEN), billing/invoice/payment/reconciliation, feedback, inbox/notifications. |

**Server-side note (from the MGR-5 R1 P2 wording):** the consent record/revoke and Parent-group invitation/member-removal routes are mounted in BE today. "Unavailable" in this roadmap is a policy and FE gate, not verified backend enforcement. Whether to disable them server-side is owner decision O-X.

## 8. Owner decisions

| ID | Question | Recommended option (where the SRS or source supports one) | Consequence | Next artifact |
|---|---|---|---|---|
| O-0 | In which order do the M2 BE branch (`833df677`, carrying D-209 and the adopted SRS) and the S-LL commit reach `dev`? | M2 branch first, then S-LL rebased on it: `dev` then carries the adopted SRS pointer and the M2 catalog changes before S-LL edits the same test file | The second one reconciles `test_openapi_contract_catalog.py` (and M2 `app.py` against `dev`) | Owner instruction for the M2 → `dev` PR; S-LL execution task notes the base |
| O-SEQ | Which BE slice follows S-LL? | W-LESSON (narrowest owner questions; no absent service) | W-CAP and W-ASSIGN wait for the shared OpenAPI files | Approval package for the chosen slice |
| O-2a | Who owns the Billing capacity contract, and does a Billing service exist to build it on? | No recommendation: source has no Billing capacity component | Without an owner, W-CAP cannot be approved | Billing contract draft |
| O-2b | Public outcome when Billing is unavailable, stale or indeterminate (fail closed is decided) | No recommendation: the SRS does not define it | Fixes the FE error state for M9-A | MGR-2 disposition |
| O-2c | Idempotency header name, key format and retention for class create | Follow the SRS semantics; the name and retention are open | Shared by W-ASSIGN; deciding once avoids two conventions | Cross-slice API convention note |
| O-2d | Is the current 403 on out-of-scope class create replaced by the SRS 404? | SRS §9.8 (uniform 404 for out-of-scope) | Changes BE1 behavior and tests | Part of W-CAP package |
| O-3a | Source of verified same-organization Teachers for the candidate list | No recommendation: no source exists | Without it, W-ASSIGN cannot be built | Identity/BE1 owner note |
| O-3b | Candidate fields and privacy (which person-identifying fields may be shown) | Minimum fields; no provider IDs or e-mail without approval | Defines the candidate DTO | MGR-3 disposition |
| O-3c | Is UC-12 reassignment/offboarding a separate task? | Yes, separate (the plan's proposal) | W-ASSIGN covers first assignment only | MGR-3 disposition |
| O-3d | Revision type and stale precondition for assignment | SRS requires 200 + assignment revision; the token format is open | Defines If-Match use in M9-B | MGR-3 disposition |
| O-6a | Binding option A (hash snapshot on grant) or B (immutable version row) | No recommendation; A needs a schema change, B needs proven immutability | Determines whether a migration is in scope | MGR-6 disposition |
| O-6b | Outcome for a pending grant whose version is superseded | No recommendation: the SRS does not define it | Fixes M9-C UI states | MGR-6 disposition |
| O-6c | Decision precondition: expected version/hash in the request or a server review receipt | No recommendation | Defines the decision DTO | MGR-6 disposition |
| O-5 | Does a distinct school-managed consent workflow exist? | Keep excluded (Parent is the consent actor) unless a legal basis is defined | Keeps consent writes off | MGR-5 brief answer |
| O-X | Disable the mounted consent-write and invitation/member-removal routes server-side, or leave them mounted and FE-gated? | No recommendation (a BE change outside every current allowlist) | Server enforcement versus UI-only gating | Separate small approval if chosen |
| O-9 | Method to reconcile the FE branch (1 behind / 3 ahead of `dev`) before any FE slice | No recommendation; must preserve the 6 dirty FE paths | Gates all M9 slices | FE reconciliation instruction |
| O-SRS | Record the D-209 SRS choice in FEAT-066 decisions and update `SRS_AUTHORITY.md` on `dev` | Comes with O-0 if the M2 branch is merged to `dev` | Removes the Rev60/adopted split for every later FEAT-066 plan | Decision row or merge |

**Environment, not a decision:** ENV-DB — a disposable local PostgreSQL database as described in 6.1, available in the shell that runs the S-LL commands. **Nonblocking notes kept open:** MGR-2 R6 P3; MGR-3 R4 P3 and R3 labeling; the SRS header Rev69/Rev68 discrepancy. No new review cycles are planned for these.

## 9. Per-slice acceptance checks (later tasks)

| Slice | Must hold before VERIFIED | Must hold before FE-INTEGRATED |
|---|---|---|
| S-LL | two authorized commands exit 0; six-file scope unchanged; evidence written and reviewed | no FE change needed unless the evidence shows a DTO change (then MGR-9 re-plan) |
| W-CAP | create admits only on a verified Billing decision; two concurrent creates never exceed capacity; 201 / 409 `CLASS_CAPACITY_REACHED` / GRACE / RESTRICTED / unavailable outcomes as approved; idempotent replay; 404/403 as approved | M9-A: idempotency key sent; full/unavailable/unauthorized/empty states shown; no client capacity logic |
| W-ASSIGN | only verified same-organization Teachers listed; command-time revalidation; one active Teacher under concurrency; 200 + revision; replay; stale conflict | M9-B: exact path/DTO; no free-typed identity; stale/conflict not shown as success |
| W-LESSON | exact version/hash read; decision bound to it; superseded outcome as approved; no current-head fallback; replay; race outcome | M9-C: controls enabled only on exact version/hash match |

Each BE slice: its own Task Approval with exact allowlist and command ceiling, one commit on the owner's instruction, independent evidence review (Sonnet 5.5 high). Each FE slice: refreshed audit pins against the reconciled base, its own FE allowlist and Task Approval, separately approved FE checks, evidence and review before the UI control is enabled.

## 10. Exclusions and limits of this draft

- No BE or FE source, test, OpenAPI, schema, migration, SRS, `SRS_AUTHORITY.md`, decision, Task Approval, CONTEXT or STATUS change. No test, build, typecheck, lint, validator, diff-check, OpenAPI generation, runtime, database, Docker, install, network/provider, Modal or emulator command.
- No stage, commit, push, merge, rebase, cherry-pick, reset, restore, clean, stash or file copy. All pre-existing dirty paths in both worktrees are preserved.
- A plan review ACCEPT is not an approval. Nothing here launches S-LL verification, W-CAP, W-ASSIGN, W-LESSON or W-FE.

## 11. Next action for the owner

1. **ENV-DB:** make the disposable `be1_acceptance` PostgreSQL database available through `BE1_TEST_DATABASE_URL` in the shell that runs the S-LL commands, then launch the already-authorized S-LL verification (section 6.1). No new authorization is needed.
2. **While that is blocked:** answer O-0 and O-SEQ, then the questions of the chosen next slice (O-6a..c recommended first); name the Billing owner (O-2a) and the identity source owner (O-3a) so lanes L1 and L2 can move.
3. Decide O-9 before any FE work, and O-X if server-side enforcement of the excluded routes is wanted.
