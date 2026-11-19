# FEAT-066 A-1 — merged BE–FE mismatch register — Draft 1

- **Status:** PLANNING DOCUMENT / NOT REVIEWED / NOT APPROVED. It authorizes nothing. A row that has a caller, a BE route, an OpenAPI entry or a Bruno request is **not** ready on that basis; readiness needs the gates of roadmap Draft 4 §5.6 and §9.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5), on the owner's instruction "Làm A-1". **Owner:** Person 2.
- **Parent plan:** Phase A reconciliation addendum (`tmp/feat066-phase-a/roadmap-reconciliation/PHASE_A_ROADMAP_RECONCILIATION_20261118.md`), item A-1. Kept in `tmp/` (git-ignored) for the same reason as the addendum.

## 0. Inputs (pinned; static audit evidence only)

| Input | Bytes | SHA-256 | Base it audited |
|---|---:|---|---|
| P2 web audit | 34,713 | `8C3E809DCE70EED1585EBFBDC22010D85A3847F343795A07AA235110D5A2081A` | BE `dev` `1c9148e8` plus six dirty MGR-8 files; web `297a28b1` |
| P3 Parent mobile audit | 21,787 | `E5A4485CAF36A9C2A42EE7C67387EF7874937B214148D9F2203309EA5E35734D` | mobile working tree incl. staged edits (`73fe001e`); BE `dev` and M2 `833df677` |
| P4 Bruno inventory | 48,221 | `50BACD27C9096C4266E1F2B70596F9CFD113C69EB541DC0CFB6A4EA180A8D419` | M2 freeze (151 operations) against the root working-tree collection (145 files) |
| Canonical SRS | 701,157 | `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` | v2.7-draft, unsigned |

**How the Bruno column was filled:** a read-only script matched every P2 and P3 row by method and path template to the P4 matrix, after checking the P4 pin. For mobile rows that call a non-M2 path, it used the M2 counterpart named by P3. The script is `tmp/feat066-phase-a/register/map_p4.py`. All 151 P4 rows parsed. Every P2 template, and every P3 row that has a frozen operation, matched one.

**Not re-derived:** DTO, status and scope findings come from P2 and P3. This register regroups them; it does not re-read source code. Cells marked NOT VERIFIED in the audits stay NOT VERIFIED.

## 1. Classes and global items

| Code | Class | Meaning |
|---|---|---|
| **GAP** | Genuine SRS / BE gap | The BE behaviour or capability differs from the adopted SRS; the fix is BE-side |
| **FE** | FE contract correction | The BE route matches its contract (or the frozen M2 contract); the FE caller is wrong or incomplete |
| **OD** | Owner decision | The SRS does not settle it, or a recorded owner boundary excludes it; nothing is fixed until decided |
| **COND** | Conditional / demo route | Mounted only in local/test, synthetic or `modal_dev` profiles, or a demo surface; not product-ready |
| **CONN** | Already connected | A caller exists and no route-specific defect was recorded beyond the global items; **still not "ready"** |

Each row has one **primary** class (the one to resolve first) and may list others. The classes overlap, so counts are per inventory and per primary class only.

**Global items, not repeated per row:**
- **E (D10):** no route outside the M2 Parent schemas returns the full §9.8 envelope (`code`, `message`, `correlation_id`, `retryable`, optional `retry_after_seconds`, `field_errors`).
- **PX:** paths under `/api/<namespace>/v1` versus the SRS `/v1` base (§21.1).

Both belong to the conventions slice B-1, after O-CONV. **Every row carries them** except A02 (public health) for E, and the `/v1/...` M2 Parent rows for both.

**Owners:** every slice is Person 2's unless marked: **PT** = payment teammate; **MWO** = owner of the staged mobile work (NOT VERIFIED who).

**Slice labels** (from the addendum §4):
- **B-1:** conventions.
- **C-A / C-M / C-T / C-P:** Platform Admin, School Manager, Teacher and Parent slices.
- **W-CAP / W-ASSIGN / W-LESSON:** MGR-2 / MGR-3 / MGR-6.
- **G0:** S-LL verification.
- **EXCL:** excluded by D-066-62 (MGR-4) or policy OPEN (MGR-5).

## 2. Web register — 41 templates (P2) plus one Parent login probe

Connected: A01–A27 are page-called; AI1–AI3 are conditional page calls; B01–B09 and C01–C02 have no page caller.

| ID | Method + path (template) | Role | Primary | Also | Mismatch (from P2) | Bruno (P4) | Next slice | Blocked by |
|---|---|---|---|---|---|---|---|---|
| A01 | GET `/api/auth/v1/me` | shared | OD | GAP (E) | FE reads `role`; scope comes separately (A06); route/scope contract open | PARTIAL 141 (OO) | B-1 | O-CONV |
| A02 | GET `/health` | Admin | CONN | — | DTO matches | PARTIAL 090 (OS) | B-5 assertions | — |
| A03 | GET `/api/platform-admin/v1/accounts` | Admin | GAP | — | offset paging, BE default 50; SRS cursor 25/100 | PARTIAL 142 (OO) | C-A | B-1 |
| A04 | POST `/api/platform-admin/v1/accounts` | Admin | GAP | — | no `Idempotency-Key` FE or BE | PARTIAL 143 (OO) | C-A | B-1 |
| A05 | PATCH `/api/platform-admin/v1/accounts/{account_id}` | Admin | GAP | OD | no key; revision returned but no If-Match (not an SRS mandate) | PARTIAL 144 (OO) | C-A | B-1, O-ACCREV |
| A06 | GET `/api/be1/v1/organizations/{organization_id}/me` | Manager, Teacher | OD | — | scope-snapshot shape; class-service type narrower (NOT VERIFIED) | PARTIAL 021 (CB) | B-1 | O-CONV |
| A07 | GET `…/organizations/{organization_id}/classes` | Manager, Teacher | GAP | — | unpaginated; `ClassesPage` does not page | PARTIAL 006 (CB) | C-M | B-1 |
| A08 | GET `…/organizations/{organization_id}` | Manager | CONN | — | DTO matches | PARTIAL 003 (CB) | B-5 | — |
| A09 | GET `…/classes/{class_id}/profiles` | Manager, Teacher | OD | GAP | Manager reads names/age vs SRS §31.3 line 2586; unpaginated | PARTIAL 012 (CB) | C-M | O-PRIV, B-1 |
| A10 | GET `…/classes/{class_id}/consents` | Manager, Teacher | OD | FE, GAP | consent meaning (MGR-5); FE expects uppercase state, BE lowercase; unpaginated | PARTIAL 008 (CB) | C-M (FE map) | O-5, B-1 |
| A11 | GET `/api/lesson-library/v1/organizations/{organization_id}/access-grants` | Manager | CONN | — | cursor 25/100 only in dirty MGR-8 source | PARTIAL 068 (OS) | — | **G0** |
| A12 | GET `…/lessons/{lesson_id}` (Lesson Library) | Manager, Teacher | OD | GAP | current head only; no exact-version read (G06) | PARTIAL 073 (OS) | W-LESSON | O-6a..c, G0 |
| A13 | POST `…/access-grants/{access_grant_id}/decision` | Manager | OD | FE | grant-version binding open; FE response untyped; 400 reuse only in dirty source | PARTIAL 069 (OS) | W-LESSON / M9-C | O-6a..c, G0 |
| A14 | GET `…/parent-groups` | Manager | CONN | — | 25/100 in dirty source; FE asks 50 (within max) | PARTIAL 081 (OS) | — | **G0** |
| A15 | POST `…/parent-groups` | Manager | CONN | — | key sent; changed-payload 400 only in dirty source | PARTIAL 082 (OS) | — | **G0** |
| A16 | GET `…/lessons` (Lesson Library list) | Teacher | GAP | — | default 50; SRS 25 | PARTIAL 070 (OS) | C-T | G0, B-1 |
| A17 | POST `…/lessons` | Teacher | CONN | — | request contract matches | PARTIAL 071 (OS) | B-5 | — |
| A18 | PATCH `…/lessons/{lesson_id}` | Teacher | GAP | — | no `Idempotency-Key`; immutable-version behaviour NOT VERIFIED | PARTIAL 074 (OS) | C-T | G0, B-1 |
| A19 | DELETE `…/lessons/{lesson_id}` | Teacher | GAP | — | no key; archive semantics NOT VERIFIED | PARTIAL 072 (OS) | C-T | G0, B-1 |
| A20 | POST `…/lessons/{lesson_id}/access-grants` | Teacher | CONN | — | request fields match | PARTIAL 075 (OS) | B-5 | — |
| A21 | POST `…/lessons/{lesson_id}/upload-sessions` | Teacher | OD | — | path shape differs from the SRS target example | PARTIAL 079 (OS) | C-T | O-UPLOAD |
| A22 | GET `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | Teacher | CONN | — | DTO equality NOT VERIFIED | PARTIAL 087 (OS) | B-5 | — |
| A23 | PUT `…/upload-sessions/{upload_session_id}/parts/{part_number}` | Teacher | FE | — | FE response untyped vs `UploadPartReceiptV1`; progress field NOT VERIFIED | PARTIAL 089 (OS) | C-T (FE) | — |
| A24 | POST `…/upload-sessions/{upload_session_id}/complete` | Teacher | GAP | OD | 200 synchronous vs SRS 202 accepted (D11) | PARTIAL 088 (OS) | C-T | G0, B-1, O-UPLOAD |
| A25 | DELETE `…/upload-sessions/{upload_session_id}` | Teacher | GAP | — | 200 vs 202; no key; no expected state/version | PARTIAL 086 (OS) | C-T | G0, B-1 |
| A26 | GET `…/source-documents/{source_document_id}` | Teacher | CONN | — | DTO NOT VERIFIED | PARTIAL 077 (OS) | B-5 | — |
| A27 | GET `…/source-documents/{source_document_id}/revisions/{revision_id}` | Teacher | CONN | — | read OK; save-as-version capability absent (see B07) | PARTIAL 078 (OS) | B-5 | — |
| AI1 | POST `/api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions` | Teacher | COND | — | local/test + `modal_dev`; output schema NOT VERIFIED | MISSING (OO) | refusal case only | — |
| AI2 | POST `…/ai/sketch-decks` | Teacher | COND | — | same | MISSING (OO) | refusal case only | — |
| AI3 | POST `…/ai/lesson-visuals` | Teacher | COND | — | same | MISSING (OO) | refusal case only | — |
| B01 | POST `…/organizations/{organization_id}/classes` | Manager | GAP | — | no Billing capacity admission, no key (G01, D02); FE create locked | PARTIAL 007 (CB) | W-CAP (L2) | Billing B-1/B-2, O-PAY |
| B02 | POST `/api/be1/v1/classes/{class_id}/assignments` | Manager | OD | GAP, FE | FE helper posts org-level path; BE 201 without revision vs SRS 200 + revision; no key; no candidates (G02, D01) | **MISSING**; stale 004/005 use the drifted path | W-ASSIGN | O-3a..d |
| B03 | POST `…/classes/{class_id}/consents` | Manager, Teacher | OD | — | staff pending ≠ Parent consent; FE key ignored by BE | PARTIAL 009 (CB) | EXCL (MGR-5) | O-5, O-X |
| B04 | POST `…/consents/{consent_id}/revoke` | Manager, Teacher | OD | — | same; no key or revision | PARTIAL 010 (CB) | EXCL (MGR-5) | O-5, O-X |
| B05 | POST `…/parent-groups/{parent_group_id}/invitations` | Manager | OD | — | no Manager Parent discovery (G05) | PARTIAL 083 (OS) | EXCL (MGR-4) | D-066-62 reopen, O-X |
| B06 | DELETE `…/parent-groups/{parent_group_id}/members/{membership_id}` | Manager | OD | — | no key; no scoped membership read | PARTIAL 084 (OS) | EXCL (MGR-4) | D-066-62 reopen, O-X |
| B07 | POST `…/lessons/{lesson_id}/versions` | Teacher | GAP | — | no `Idempotency-Key`; no page caller | PARTIAL 080 (OS) | C-T | G0, B-1 |
| B08 | DELETE `…/lessons/{lesson_id}/access-grants/{access_grant_id}` | Manager, Teacher | GAP | — | no key; FE DTO absent | PARTIAL 076 (OS) | C-T | G0, B-1 |
| B09 | PATCH `/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` | Admin | OD | GAP | role check only, no Content Admin permission; no queue or exact-version read (G07, D06); page blocked | PARTIAL 085 (OS) | C-A | O-CONTENTADMIN |
| C01 | POST `…/classes/{class_id}/profiles` | Teacher | COND | GAP | synthetic local/test only; production route and expected class revision absent (G03) | PARTIAL 013 (CB) | C-T (G03) | B-1 |
| C02 | GET `…/sessions/{session_id}/pilot-profiles` | Teacher, Manager | COND | — | synthetic, lobby-only | PARTIAL 050 (PO + CB) | refusal case only | — |
| WP | GET `/api/lesson-library/v1/me/lessons` (login probe, outside the 41) | Parent gate on web | CONN | — | role gate only; same operation as M15 | PARTIAL 063 (OS) | with M15 | — |

**Web primary-class counts (41 templates; the probe excluded):** CONN 10 (three pending G0), GAP 12, OD 13, FE 1, COND 5.

### 2.1 Web capability gaps (P2, no route or incomplete route)

| ID | Capability | Class | Next slice | Blocked by |
|---|---|---|---|---|
| G01 | Capacity-safe class creation, effective-capacity projection | GAP | W-CAP (L2) | Billing contract READY, O-PAY |
| G02 | Scoped Teacher-candidate discovery | GAP + OD | W-ASSIGN | O-3a, O-3b |
| G03 | Production Teacher profile create/enrollment | GAP | C-T | B-1 |
| G04 | Consent evidence/eligibility; school-managed workflow | OD | EXCL (MGR-5) | O-5 |
| G05 | Manager Parent discovery, membership read | OD | EXCL (MGR-4) | D-066-62 reopen |
| G06 | Exact LessonVersion read; grant-bound decision | GAP + OD | W-LESSON | O-6a..c, G0 |
| G07 | Moderation queue; Content Admin permission check | GAP + OD | C-A | O-CONTENTADMIN |
| G08 | Platform catalog authoring/publish; permission administration | GAP + OD | new ID (C-A) | O-CONTENTADMIN |
| G09 | Class archive/suspend/reassignment (UC-12) | GAP | new ID (C-M) | O-3c; W-CAP suspension design |
| G10 | School quota summary (`GET /v1/video-quota`) | GAP | L2 | Billing contract READY |
| G11 | Subscription, invoice, payment attempt, reconciliation | excluded — payment | PT | O-PAY |
| G12 | School feedback read/reply (FR-PL-22) | GAP | MGR-10 (no owner) | owner assignment |
| G13 | Notification inbox/read state | GAP | MGR-10 (no owner) | owner assignment |
| G14 | Teacher occurrence, plan, sample/run, projection, lifecycle (FR-T-08–17) | GAP | new IDs (C-T) | B-1; planning |

## 3. Parent mobile register — 27 product and auth rows (P3)

"Called path": **exact** = the mobile app calls the frozen path; **counterpart** = it calls a non-M2 path that P3 maps to the M2 operation shown; **none** = no BE route in `dev` or M2. M2 8 = whether the operation is one of the 8 allowed for client integration.

| ID | Mobile call (working tree) | Frozen operation / counterpart | Called path | M2 8 | Primary | Also | Mismatch (from P3) | Bruno (P4) | Next slice | Blocked by |
|---|---|---|---|---|---|---|---|---|---|---|
| M01 | GET `/api/parent/v1/consent-policy` | — | none | no | OD | — | no route, no SRS path | — | — | O-PCONSENT |
| M02 | GET `/v1/parent/profiles` | same | exact | yes | FE | — | no cursor continuation | COVERED 137 (T) | C-P | O-MOB2, O-9 |
| M03 | GET `/v1/parent/profiles/{profile_id}` | same | exact | yes | FE | — | FE expects `{profile}` envelope; BE flat view or delete-pending view | COVERED 138 (T) | C-P | O-MOB2, O-9 |
| M04 | POST `/api/parent/v1/child-profiles` | POST `/v1/parent/profiles` | counterpart | yes | FE | — | staged path drift; extra consent fields; nested response; no `Idempotency-Key` | **MISSING** (T) | C-P | O-MOB2, O-9 |
| M05 | PATCH `/api/parent/v1/child-profiles/{profile_id}` | PATCH `/v1/parent/profiles/{profile_id}` | counterpart | yes | FE | — | path drift; response wrapper; no key | **MISSING** (T) | C-P | O-MOB2, O-9 |
| M06 | POST `/api/parent/v1/child-profiles/{profile_id}/data-authorizations` | — | none | no | OD | — | no route; no key | — | — | O-PCONSENT |
| M07 | DELETE `…/child-profiles/{profile_id}/data-authorizations` | — | none | no | OD | — | no route | — | — | O-PCONSENT |
| M08 | DELETE `/api/parent/v1/child-profiles/{profile_id}` | DELETE `/v1/parent/profiles/{profile_id}` | counterpart | yes | FE | — | path drift; 202 delete-pending receipt vs FE profile envelope; no key | **MISSING** (T) | C-P | O-MOB2, O-9 |
| M09 | GET `/v1/story-runs/active/current` | same | exact | yes | FE | — | FE type omits `run_revision`; summary still "[PROPOSAL]" (owner: does not block) | COVERED 139 (T + PR) | C-P | O-MOB2, O-9, O-0 |
| M10 | GET `/v1/story-runs/{run_id}` | same | exact | yes | FE | — | FE type omits `run_revision`; `{id}` vs `{run_id}` is spelling only | COVERED 140 (+126, 127) (T) | C-P | O-MOB2, O-9, O-0 |
| M11 | POST `/api/parent/v1/story-runs` | POST `/v1/story-runs` | counterpart | yes | FE | — | path drift; extra body fields; no key; no `run_revision`; no active caller | PARTIAL 125 (T) | C-P | O-MOB2, O-9, O-0 |
| M12 | POST `/api/parent/v1/story-runs/{run_id}/subject-confirmations` | POST `/v1/story-runs/{run_id}/subject-confirmation` | counterpart | no | FE | OD | path drift (plural); no key; outside the 8 | PARTIAL 130 (PR) | after O-PROJ | O-PROJ, O-MOB2 |
| M13 | POST `/api/parent/v1/story-runs/{run_id}/story-revision-confirmations` | POST `/v1/story-runs/{run_id}/script-confirmation` | counterpart | no | FE | OD | path drift; no key; outside the 8; no presentation caller | **MISSING** (PR) | after O-PROJ | O-PROJ, O-MOB2 |
| M14 | POST `/api/parent/v1/ai/story-runs/{run_id}/story-revisions` | same | exact | no (blocked) | OD | — | assistance blocked by M2; response generic | MISSING (OO) | refusal case only | O-ASSIST |
| M15 | GET `/api/lesson-library/v1/me/lessons` | same | exact | no | FE | GAP (E) | no cursor continuation (asks 50) | PARTIAL 063 (OS) | Parent Lesson Library slice | B-1 |
| M16 | GET `…/me/lesson-invitations` | same | exact | no | FE | GAP (E) | no continuation; item type subset | PARTIAL 060 (OS) | Parent Lesson Library slice | B-1 |
| M17 | POST `…/me/lesson-invitations/{access_grant_id}/accept` | same | exact | no | GAP | — | errors `detail:{code,message}`, not §9.8; key present | PARTIAL 061 (OS) | B-1 | O-CONV |
| M18 | POST `…/me/lesson-invitations/{access_grant_id}/decline` | same | exact | no | GAP | — | same | PARTIAL 062 (OS) | B-1 | O-CONV |
| M19 | GET `…/me/parent-group-invitations` | same | exact | no | FE | GAP (E) | no continuation; membership type omits fields | PARTIAL 066 (OS) | Parent Lesson Library slice | B-1 |
| M20 | POST `…/me/parent-group-invitations/{membership_id}/accept` | same | exact | no | GAP | — | errors not §9.8 | PARTIAL 067 (OS) | B-1 | O-CONV |
| M21 | GET `…/me/lessons/{lesson_id}` | same | exact | no | FE | GAP (E) | FE type omits required `locale` | PARTIAL 064 (OS) | Parent Lesson Library slice | B-1 |
| M22 | GET `…/me/lessons/{lesson_id}/download` | same | exact | no | GAP | — | shape matches; errors not §9.8 | PARTIAL 065 (OS) | B-1 | O-CONV |
| M23 | POST `/api/parent/v1/ai/sketch-guides` | same | exact | no (blocked) | OD | FE | FE `step_count:3`, BE 3–5, SRS FR-P-11 4–8; FE expects image, SRS validated SVG | MISSING (OO) | refusal case only | O-ASSIST |
| M24 | POST `/api/parent/v1/ai/drawing-understandings` | same | exact | no (blocked) | COND | OD | legacy base64-in-JSON flow vs SRS upload-session rule | MISSING (OO) | refusal case only | O-ASSIST |
| M25 | POST `/api/parent/v1/ai/story-runs/{run_id}/activity-suggestions` | — | none | no | OD | — | no route; no SRS path; Rev78 owner direction (catalog-first) in the source register | — | — | O-ASSIST |
| M26 | POST `/api/auth/v1/registrations` | same | exact | no | GAP | — | errors not §9.8; no `X-Request-ID` | **MISSING** (OO) | B-1 | O-CONV |
| M27 | GET `/api/auth/v1/me` | same (= A01) | exact | no | GAP | OD | errors not §9.8; scope contract shared with A01 | PARTIAL 141 (OO) | B-1 | O-CONV |

**Mobile primary-class counts (27 rows):** FE 14, OD 6, GAP 6, COND 1, CONN 0.
- **Calls a live frozen route on its exact path:** 17 rows — M02, M03, M09, M10, M14–M24, M26, M27.
- **Counterpart only:** 6 rows — M04, M05, M08, M11, M12, M13. All six are path drifts from the staged edits; see the addendum C-06.
- **No route:** 4 rows — M01, M06, M07, M25.

**The 8 M2-allowed operations:**
- 4 are called on their exact path: M02, M03, M09, M10.
- 4 are reached only through drifted paths: M04, M05, M08, M11.
- Bruno has a request for 5 of the 8 (4 COVERED positive-only, 1 PARTIAL) and none for 3 (M04, M05, M08).

### 3.1 Parent capability gaps (P3: no mobile caller and no BE route)

| ID | SRS capability (stated route) | Class | Next slice | Blocked by |
|---|---|---|---|---|
| MG01 | Attach validated artwork — POST `/v1/story-runs/{id}/assets` | GAP | new Parent StoryRun slice | O-PROJ; the 6 `dev`-only `storyrun-lite` routes are a candidate base, not in the freeze (C-08) |
| MG02 | Text/audio idea — POST `/v1/story-runs/{id}/idea` | GAP | same | planning |
| MG03 | Job polling — GET `/v1/jobs/{job_id}` | GAP | same | planning |
| MG04 | Video admission — POST `/v1/story-runs/{id}/video-generations` | GAP | L2 video quota + StoryRun | Billing contract READY |
| MG05 | Mark video unsuitable | GAP | Parent StoryRun slice | planning |
| MG06 | Complete run | GAP | same | planning |
| MG07 | Delete completed run | GAP | same | planning |
| MG08 | Playback token | GAP | same | planning |
| MG09 | Parent quota summary — GET `/v1/video-quota` | GAP | L2 (same as G10) | Billing contract READY |
| MG10 | Notifications inbox | GAP | MGR-10 (no owner) | owner assignment |
| MG11 | Push endpoint register/revoke | GAP | MGR-10 (no owner) | owner assignment |
| MG12 | StoryRun history (no SRS method/path) | GAP + OD | — | SRS path open; do not invent |
| MG13 | Parent lesson delivery history and feedback (FR-PL-21/22; no SRS path) | GAP + OD | — | SRS path open |
| MG14 | Child-profile sharing/revoke (FR-PL-07; no SRS path) | GAP + OD | — | O-PCONSENT |
| MG15 | Quota purchase — POST `/v1/video-quota/purchases` | excluded — payment | PT | Q193, O-PAY |

**Demo and mock surfaces (P3; not registered as mismatches):**
- `src/demo/api.ts`: 23 declared `/v1/sessions…` and related paths, the CD-class demo-group operations.
- `src/services/api.ts`: a dormant mock with 8 paths; `USE_MOCK_API` is true and there are no call sites.
- Firebase provider calls.

The owner should decide whether to keep these surfaces in the product build. That is not a BE contract item.

## 4. Frozen operations not covered by either audit (P4 scope residue)

The P2 and P3 rows touch **63** of the **151** frozen operations. They are counted once each: A01 and M27 are the same operation, and so are WP and M15. The other **88** were not audited against an FE caller by Phase A:

| M2 class | Count | What they are | Handling |
|---|---:|---|---|
| CB (BE1 compatibility) | 44 | classroom sessions, device grants, room code, canvas, checkpoints, groups, gallery, observations, data requests, portfolio, BE1 health | **NOT AUDITED.** No web or Parent mobile caller in P2/P3. Their client (classroom or child-device surface) is outside the four-role audits. Needs O-L3SCOPE |
| CD (demo-group compatibility) | 35 | `/v1/sessions…`, renderer, whiteboard, preview | demo surface (mobile `src/demo/api.ts`); COND |
| LE (local example) | 3 | `/api/dev/v1/storage-examples…` | COND |
| PO + CB (pilot-only) | 4 | assistance requests, create/cancel/status/pending | COND; Bruno MISSING; blocked like the Parent assistance operations |
| T | 1 | POST `/v1/story-runs/{run_id}/cancel` | M2 target, not in the client projection; mobile adapter returns "unavailable"; Bruno PARTIAL 129 | O-PROJ |
| PR | 1 | POST `/v1/story-runs/{run_id}/context-confirmation` | no mobile caller; Bruno MISSING | O-PROJ |

**Bruno status of the 88:** 83 PARTIAL, 5 MISSING (the four PO + CB operations and context-confirmation).

**Not in the freeze (P4):**
- The 6 `dev`-only `storyrun-lite` upload and asset requests.
- The Firebase helper.
- The 2 stale assignment requests.

## 5. Next-slice queue derived from the register

| Slice | Rows | Gate before work | Count of rows (primary or also) |
|---|---|---|---|
| G0 (S-LL) | A11, A14, A15 (confirm); A13 (400 code); prerequisite for every Lesson Library row | ENV-P1 | 3 direct + 1 |
| B-1 conventions | global E and PX on all rows; A01, A06, M17, M18, M20, M22, M26, M27; pagination rule for A03, A07, A09, A10, A16, M02, M15, M16, M19 | G0 commit (or owner parks S-LL); O-CONV | 8 primary + 9 pagination |
| C-P Parent first slice | M02, M03, M04, M05, M08, M09, M10, M11 (+ 3 Bruno requests for M04, M05, M08) | O-MOB2, O-9, O-0, O-CONV ordering | 8 |
| Parent Lesson Library slice | M15, M16, M19, M21 | B-1 | 4 |
| C-M / W-* | A07, A09, A10, A12, A13, B01, B02; G01, G02, G06, G09 | per Draft 4 §5.2–5.4 | 7 rows + 4 gaps |
| C-T | A16, A18, A19, A21, A23, A24, A25, B07, B08, C01; G03, G14 | G0 (shared Lesson Library files), B-1 | 10 rows + 2 gaps |
| C-A | A03, A04, A05, B09; G07, G08 | B-1; O-CONTENTADMIN for B09/G07/G08 | 4 rows + 2 gaps |
| L2 | B01 (with W-CAP), G10, MG04, MG09 | Billing contract READY, O-PAY | 1 row + 3 gaps |
| Excluded / refusal-only Bruno | B03–B06 (EXCL); AI1–AI3, C02, M14, M23, M24 (COND/blocked) | — | 11 |
| Owner decision only (no slice yet) | M01, M06, M07, M25; M12, M13 (O-PROJ) | the named decisions | 6 |
| B-5 Bruno baseline (connected, no route defect) | A02, A08, A17, A20, A22, A26, A27 | A-5, O-TOKEN, seed | 7 |

## 6. Decisions referenced (no decision is made here)

- **From Draft 4, still open:** O-0, O-CONV, O-SEQ, O-PAY, O-2a..c, O-3a..d, O-6a..c, O-5, O-X, O-9, O-BRU, O-SRS.
- **From the addendum §9:** ENV-P1, O-MOB2, O-PCONSENT, O-PRIV, O-ASSIST, O-CONTENTADMIN, O-ACCREV, O-UPLOAD, O-TOKEN.
- **New in this register:**

| ID | Question | Rows |
|---|---|---|
| O-PROJ | Extend the M2 client projection beyond the 8 operations — subject, script and context confirmation, and cancel — and in which order | M12, M13; cancel; context-confirmation; MG01 |
| O-L3SCOPE | Are the 44 CB classroom/device operations (and their client) in the L3 audit and L4 wiring scope, and under which role? | §4 |

## 7. Limits

- Regrouping of pinned static audits. No source, test, Bruno or worktree file was read or changed for this register beyond the P4 matrix parse.
- No test, build, validator, runtime, database, Docker, network or Bruno run.
- DTO, status and scope claims carry the audits' own NOT VERIFIED marks. The MGR-8 effects remain NOT VERIFIED until G0.
- Primary-class assignment is the coordinator's judgment of what must be resolved first. The "Also" column keeps the other classes the audits named.
