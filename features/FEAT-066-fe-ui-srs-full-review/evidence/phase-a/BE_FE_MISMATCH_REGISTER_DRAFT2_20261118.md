# FEAT-066 A-1 — merged BE–FE mismatch register — Draft 2

- **Status:** PLANNING DOCUMENT / NOT APPROVED / NOT RE-REVIEWED. It authorizes nothing. No row is "ready" merely because it has a caller, a BE route, an OpenAPI entry or a Bruno request. Readiness needs the gates of roadmap Draft 4 §5.6 and §9.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Predecessor, unchanged:** Draft 1 (25,303 bytes, `3F89EB1DD1650132170D0BDE103CEFBB0E52C4702381EB86692F384FB7BD8842`).
- **Draft 1 review:** Sonnet 5.5 high, round 1, READY WITH NOTES (0 P1 / 5 P2 / 10 P3). The record is `tmp/feat066-phase-a/register/BE_FE_MISMATCH_REGISTER_DRAFT1_COLD_REVIEW_20261118.md` (6,262 bytes, `822DB4A04DD21DB0…`). §8 disposes of R1-01 to R1-14.
- **Paths:** every path in this document is relative to the repository root. The file sits in git-ignored `tmp/` and can move into `features/FEAT-066-fe-ui-srs-full-review/` on the owner's word.

## 0. Inputs (pinned; static audit evidence only)

| Input | Bytes | SHA-256 | Base it audited |
|---|---:|---|---|
| P2 web audit `tmp/feat066-phase-a/web-audit/WEB_API_SRS_AUDIT_DRAFT1_20261118.md` | 34,713 | `8C3E809DCE70EED1585EBFBDC22010D85A3847F343795A07AA235110D5A2081A` | BE `dev` `1c9148e8` plus six dirty MGR-8 files; web `297a28b1` |
| P3 Parent mobile audit `tmp/feat066-phase-a/mobile-audit/MOBILE_PARENT_API_AUDIT_DRAFT1_20261118.md` | 21,787 | `E5A4485CAF36A9C2A42EE7C67387EF7874937B214148D9F2203309EA5E35734D` | mobile working tree incl. staged edits (`73fe001e`); BE `dev` and M2 `833df677` |
| P4 Bruno inventory `tmp/feat066-phase-a/bruno-inventory/BRUNO_COVERAGE_INVENTORY_DRAFT1_20261118.md` | 48,221 | `50BACD27C9096C4266E1F2B70596F9CFD113C69EB541DC0CFB6A4EA180A8D419` | M2 freeze (151 operations) against the root working-tree collection (145 files) |
| Phase A addendum `tmp/feat066-phase-a/roadmap-reconciliation/PHASE_A_ROADMAP_RECONCILIATION_20261118.md` | 27,080 | `C6DB3CBF88EFA3698193D10A7FAD0FB713D683756341211B463F77DF9C0AD777` | — |
| Roadmap Draft 4 `.worktrees/manager-api/features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md` | 42,628 | `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6` | — |
| A-4 mobile brief `tmp/feat066-phase-a/mobile-brief/PARENT_MOBILE_RECONCILIATION_BRIEF_20261118.md` | 8,691 | `506B766030C66029829CE2CE7F97A47FE20B76F78A6653771DC83731643C8A6A` | — |
| Canonical SRS | 701,157 | `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` | v2.7-draft, unsigned |

**How the Bruno column was filled:** a read-only script matched every row by method and path template to the P4 matrix, after checking the P4 pin. For mobile rows that call a non-M2 path, it used the M2 counterpart named by P3. The script is `tmp/feat066-phase-a/register/map_p4.py`; it parsed all 151 rows. The review re-ran it and agreed.

**Carried correction (addendum C-03):** P2 cites the Rev52 audit pin with its last digit missing. The live pin is `8B1EB54A05A4B4A6FF502D45B278DBFE3B885EC278229A7ADEA98D3DA7ECA50A`.

**Not re-derived:** DTO, status and scope findings come from P2 and P3. **Every NOT VERIFIED mark of the audits is carried in the rows below (NV = NOT VERIFIED).**

## 1. Classes, global items and legends

| Code | Class | Meaning |
|---|---|---|
| **GAP** | SRS / BE gap | BE behaviour or capability differs from the adopted SRS; fix BE-side |
| **FE** | FE contract correction | The BE route matches its contract (or the frozen M2 contract); the FE caller is wrong or incomplete |
| **OD** | Owner decision | The SRS does not settle it, or a recorded owner boundary excludes it |
| **COND** | Conditional / demo route | Mounted only in local/test, synthetic or `modal_dev` profiles, or a demo surface |
| **CONN** | Already connected | A caller exists and no route-specific defect is recorded beyond the global items. **Not "ready".** |

**Global items** (not repeated per row; they go to the conventions slice CONV-1 after O-CONV; see `PLAN_API_CONVENTIONS_CONTRACT_DRAFT1_20261118.md`):
- **E (D10):** no full §9.8 envelope.
- **PX:** an `/api/<namespace>/v1` path versus the SRS `/v1` base.

**Exemptions:**
- A02 (`/health`) is exempt from both E and PX.
- Operations whose **frozen M2 path** is under `/v1/` are exempt from PX. That means the Parent profile and StoryRun operations, judged by their frozen path, not by the path a caller uses.
- The M2 Parent error schema is a §9.8 superset. Its extra fields `request_id` and `current_version` were read as not blocking, but **M2 ledger item O4 leaves them for Person 2 to confirm**, so the E exemption for those operations is provisional (R1-07).

**Classification rules (R1-02, R1-03):**
1. A row whose only defect is E is **CONN with the marker "E-only"**.
2. The primary class follows the audit's class for that row, unless this register reclassifies it. A reclassification is marked **"RC:"** with its reason. "Also" lists the other classes the audit named. Dependencies such as O-PROJ or O-ASSIST appear under "Blocked by", not as a class.
3. One operation can appear under two callers (A01 and M27; WP and M15). Their primaries differ **by caller**, because the callers' defects differ.

**Bruno legend (P4 terms):**
- **COVERED:** a matching request with an assertion or script. This is positive-only today and is not the full L5 case set.
- **PARTIAL:** a matching request **without** any assertion or script. It does not mean "partly covered".
- **MISSING:** no matching request.

The number after the status is the request file number. The class code in brackets is the M2 classification.

**Slice labels:**
- **CONV-1:** conventions; the addendum called it B-1, renamed to avoid a clash with the Billing slices.
- **SEED-1:** seed implementation.
- **FEBASE:** FE base reconciliation.
- **BRU-0:** Bruno baseline.
- **Billing B-1 to B-5:** the Billing contract slices.
- **G0:** S-LL verification.
- **C-A / C-M / C-T / C-P:** the Platform Admin, School Manager, Teacher and Parent slices.
- **W-CAP / W-ASSIGN / W-LESSON:** MGR-2 / MGR-3 / MGR-6.
- **EXCL:** excluded — MGR-4 by D-066-62; MGR-5 while its policy is OPEN.

**Owners (R1-09):** owners are set per slice, not per row, and follow the addendum.
- BE slices: Person 2 / CaoDat (BE co-owners).
- FE slices: Person 2.
- Billing payment parts: the payment teammate (PT).
- Mobile staged work: its author; see the A-4 brief D-B, author NOT VERIFIED.

## 2. Web register — 41 templates (P2) plus one Parent login probe

**Callers:** A01–A27 are page-called; AI1–AI3 are conditional page calls; B01–B09 and C01–C02 have no page caller.

| ID | Method + path (template) | Role | Primary | Also | Mismatch (from P2) | Bruno (P4) | Next slice | Blocked by |
|---|---|---|---|---|---|---|---|---|
| A01 | GET `/api/auth/v1/me` | shared | OD | — | FE reads `role`; scope comes separately (A06); route/scope contract open | PARTIAL 141 (OO) | CONV-1 | O-CONV |
| A02 | GET `/health` | Admin | CONN | — | DTO matches; exempt from E and PX | PARTIAL 090 (OS) | BRU-0 | — |
| A03 | GET `/api/platform-admin/v1/accounts` | Admin | GAP | — | offset paging, BE default 50; SRS cursor 25/100 | PARTIAL 142 (OO) | C-A | CONV-1 |
| A04 | POST `/api/platform-admin/v1/accounts` | Admin | GAP | — | no `Idempotency-Key` FE or BE | PARTIAL 143 (OO) | C-A | CONV-1 |
| A05 | PATCH `/api/platform-admin/v1/accounts/{account_id}` | Admin | GAP | OD | no key; revision returned, no If-Match (not an SRS mandate) | PARTIAL 144 (OO) | C-A | CONV-1, O-ACCREV |
| A06 | GET `/api/be1/v1/organizations/{organization_id}/me` | Manager, Teacher | OD | — | scope-snapshot shape; class-service type narrower; exact type equivalence NV | PARTIAL 021 (CB) | CONV-1 | O-CONV |
| A07 | GET `…/organizations/{organization_id}/classes` | Manager, Teacher | GAP | — | unpaginated; `ClassesPage` does not page | PARTIAL 006 (CB) | C-M | CONV-1 |
| A08 | GET `…/organizations/{organization_id}` | Manager | CONN | — | DTO matches | PARTIAL 003 (CB) | BRU-0 | — |
| A09 | GET `…/classes/{class_id}/profiles` | Manager, Teacher | OD | GAP | Manager reads names/age vs SRS §31.3 line 2586; unpaginated | PARTIAL 012 (CB) | C-M | O-PRIV, CONV-1 |
| A10 | GET `…/classes/{class_id}/consents` | Manager, Teacher | OD | FE, GAP | consent meaning (MGR-5); FE expects uppercase state, BE lowercase; unpaginated | PARTIAL 008 (CB) | C-M (FE map) | O-5, CONV-1 |
| A11 | GET `/api/lesson-library/v1/organizations/{organization_id}/access-grants` | Manager | CONN | — | cursor 25/100 only in dirty MGR-8 source (NV); response field alias comparison NV | PARTIAL 068 (OS) | — | **G0** |
| A12 | GET `…/lessons/{lesson_id}` (Lesson Library) | Manager, Teacher | OD | GAP | current head only; no exact-version read (G06); FE field-level type equivalence NV | PARTIAL 073 (OS) | W-LESSON | O-6a..c, G0 |
| A13 | POST `…/access-grants/{access_grant_id}/decision` | Manager | OD | FE | grant-version binding open; FE response untyped; 400 reuse only in dirty source (NV) | PARTIAL 069 (OS) | W-LESSON / M9-C | O-6a..c, G0 |
| A14 | GET `…/parent-groups` | Manager | CONN | — | 25/100 in dirty source (NV); FE asks 50 (within max) | PARTIAL 081 (OS) | — | **G0** |
| A15 | POST `…/parent-groups` | Manager | CONN | — | key sent; changed-payload 400 only in dirty source (NV) | PARTIAL 082 (OS) | — | **G0** |
| A16 | GET `…/lessons` (Lesson Library list) | Teacher | GAP | — | default 50; SRS 25; response alias comparison NV | PARTIAL 070 (OS) | C-T | G0, CONV-1 |
| A17 | POST `…/lessons` | Teacher | CONN | — | request contract matches; **response field-level mapping NV** | PARTIAL 071 (OS) | BRU-0 | — |
| A18 | PATCH `…/lessons/{lesson_id}` | Teacher | GAP | — | no `Idempotency-Key`; response mapping NV; immutable-version behaviour NV | PARTIAL 074 (OS) | C-T | G0, CONV-1 |
| A19 | DELETE `…/lessons/{lesson_id}` | Teacher | GAP | — | no key; FE response mapping NV; archive semantics NV | PARTIAL 072 (OS) | C-T | G0, CONV-1 |
| A20 | POST `…/lessons/{lesson_id}/access-grants` | Teacher | CONN | — | request fields match; **response field-level mapping NV** | PARTIAL 075 (OS) | BRU-0 | — |
| A21 | POST `…/lessons/{lesson_id}/upload-sessions` | Teacher | OD | — | path shape differs from the SRS target example; full response alias comparison NV | PARTIAL 079 (OS) | C-T | O-UPLOAD |
| A22 | GET `/api/lesson-library/v1/upload-sessions/{upload_session_id}` | Teacher | CONN | — | DTO field equality NV | PARTIAL 087 (OS) | BRU-0 | — |
| A23 | PUT `…/upload-sessions/{upload_session_id}/parts/{part_number}` | Teacher | FE | — | FE response untyped vs `UploadPartReceiptV1`; progress field NV | PARTIAL 089 (OS) | C-T (FE) | — |
| A24 | POST `…/upload-sessions/{upload_session_id}/complete` | Teacher | GAP | OD | 200 synchronous vs SRS 202 accepted (D11); exact field mapping NV | PARTIAL 088 (OS) | C-T | G0, CONV-1, O-UPLOAD |
| A25 | DELETE `…/upload-sessions/{upload_session_id}` | Teacher | GAP | — | 200 vs 202; no key; no expected state/version; response mapping NV | PARTIAL 086 (OS) | C-T | G0, CONV-1 |
| A26 | GET `…/source-documents/{source_document_id}` | Teacher | CONN | — | status DTO mapping NV | PARTIAL 077 (OS) | BRU-0 | — |
| A27 | GET `…/source-documents/{source_document_id}/revisions/{revision_id}` | Teacher | CONN | — | read OK; **FE alias comparison NV**; save-as-version capability absent (see B07) | PARTIAL 078 (OS) | BRU-0 | — |
| AI1 | POST `/api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions` | Teacher | COND | — | local/test + `modal_dev`; output schema NV | MISSING (OO) | refusal case only | — |
| AI2 | POST `…/ai/sketch-decks` | Teacher | COND | — | same; schema NV | MISSING (OO) | refusal case only | — |
| AI3 | POST `…/ai/lesson-visuals` | Teacher | COND | — | same; schema NV | MISSING (OO) | refusal case only | — |
| B01 | POST `…/organizations/{organization_id}/classes` | Manager | GAP | — | no Billing capacity admission, no key (G01, D02); FE create locked | PARTIAL 007 (CB) | W-CAP (Billing B-2) | Billing B-1, O-PAY |
| B02 | POST `/api/be1/v1/classes/{class_id}/assignments` | Manager | OD | GAP, FE | FE helper posts an org-level path; BE 201 without revision vs SRS 200 + revision; no key; no candidates (G02, D01) | **MISSING**; stale 004/005 use the drifted path | W-ASSIGN | O-3a..d |
| B03 | POST `…/classes/{class_id}/consents` | Manager, Teacher | OD | — | staff pending ≠ Parent consent; FE key ignored by BE | PARTIAL 009 (CB) | EXCL (MGR-5) | O-5, O-X |
| B04 | POST `…/consents/{consent_id}/revoke` | Manager, Teacher | OD | — | same; no key or revision | PARTIAL 010 (CB) | EXCL (MGR-5) | O-5, O-X |
| B05 | POST `…/parent-groups/{parent_group_id}/invitations` | Manager | OD | — | no Manager Parent discovery (G05) | PARTIAL 083 (OS) | EXCL (MGR-4) | D-066-62 reopen, O-X |
| B06 | DELETE `…/parent-groups/{parent_group_id}/members/{membership_id}` | Manager | OD | — | no key; no scoped membership read | PARTIAL 084 (OS) | EXCL (MGR-4) | D-066-62 reopen, O-X |
| B07 | POST `…/lessons/{lesson_id}/versions` | Teacher | GAP | — | no `Idempotency-Key`; no page caller | PARTIAL 080 (OS) | C-T | G0, CONV-1 |
| B08 | DELETE `…/lessons/{lesson_id}/access-grants/{access_grant_id}` | Manager, Teacher | GAP | — | no key; FE DTO absent | PARTIAL 076 (OS) | C-T | G0, CONV-1 |
| B09 | PATCH `/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` | Admin | OD | GAP | role check only, no Content Admin permission; no queue or exact-version read (G07, D06); page blocked | PARTIAL 085 (OS) | C-A | O-CONTENTADMIN |
| C01 | POST `…/classes/{class_id}/profiles` | Teacher | COND | GAP | synthetic local/test only; production route and expected class revision absent (G03) | PARTIAL 013 (CB) | C-T (G03) | CONV-1 |
| C02 | GET `…/sessions/{session_id}/pilot-profiles` | Teacher, Manager | COND | — | synthetic, lobby-only | PARTIAL 050 (PO + CB) | refusal case only | — |
| WP | GET `/api/lesson-library/v1/me/lessons` (login probe, outside the 41) | Parent gate on web | CONN | — | role gate only; same operation as M15 (primary differs by caller); response mapping and pagination NV | PARTIAL 063 (OS) | with M15 | — |

**Web primary counts (41 templates, probe excluded):** CONN 10 (A11, A14 and A15 pending G0), GAP 12, OD 13, FE 1, COND 5.

### 2.1 Web capability gaps (P2)

| ID | Capability | Class | Next slice | Blocked by |
|---|---|---|---|---|
| G01 | Capacity-safe class creation; effective-capacity projection | GAP | W-CAP (Billing B-2) | Billing B-1, O-PAY |
| G02 | Scoped Teacher-candidate discovery | GAP + OD | W-ASSIGN | O-3a, O-3b |
| G03 | Production Teacher profile create/enrollment | GAP | C-T | CONV-1 |
| G04 | Consent evidence/eligibility; school-managed workflow | OD | EXCL (MGR-5) | O-5 |
| G05 | Manager Parent discovery; membership read | OD | EXCL (MGR-4) | D-066-62 reopen |
| G06 | Exact LessonVersion read; grant-bound decision | GAP + OD | W-LESSON | O-6a..c, G0 |
| G07 | Moderation queue; Content Admin permission check | GAP + OD | C-A | O-CONTENTADMIN |
| G08 | Platform catalog authoring/publish; permission administration | GAP + OD | new ID (C-A) | O-CONTENTADMIN |
| G09 | Class archive/suspend/reassignment (UC-12) | GAP | new ID (C-M) | O-3c; Billing B-5 suspension |
| G10 | School quota summary (`GET /v1/video-quota`; same capability as MG09) | GAP | Billing B-3 | Billing contract (Draft 7) and B-1 |
| G11 | Subscription, invoice, payment attempt, reconciliation | excluded — payment | PT | O-PAY |
| G12 | School feedback read/reply (FR-PL-22) | GAP | MGR-10 (no owner) | owner assignment |
| G13 | Notification inbox/read state | GAP | MGR-10 (no owner) | owner assignment |
| G14 | Teacher occurrence, plan, sample/run, projection, lifecycle (FR-T-08–17) | GAP | new IDs (C-T) | CONV-1; planning |

## 3. Parent mobile register — 27 product and auth rows (P3)

**"Called path":**
- **exact:** the app calls the frozen path.
- **counterpart:** the app calls a non-M2 path that P3 maps to the M2 operation shown.
- **none:** no BE route on `dev` or M2.

**Counterpart rows come from the staged FEAT-081 Plan Revision 19 / Addendum 34 work.** That work was built against the legacy `/api/parent/v1/...` routes of the 45-commit-behind mobile branch (A-4 brief §2), not as random drift.

**Mobile FE rows carry the shared mobile gates:** O-MOB2, O-9 and FEBASE (mobile).

| ID | Mobile call (working tree) | Frozen operation / counterpart | Called path | M2 8 | Primary | Also | Mismatch (from P3) | Bruno (P4) | Next slice | Blocked by |
|---|---|---|---|---|---|---|---|---|---|---|
| M01 | GET `/api/parent/v1/consent-policy` | — (legacy route removed by M2) | none | no | OD | — | no route on `dev`/M2, no SRS path; status/response NV | — | — | O-PCONSENT |
| M02 | GET `/v1/parent/profiles` | same | exact | yes | FE | — | no cursor continuation | COVERED 137 (T) | C-P | O-MOB2, O-9, FEBASE |
| M03 | GET `/v1/parent/profiles/{profile_id}` | same | exact | yes | FE | — | FE expects `{profile}`; BE flat view or delete-pending view | COVERED 138 (T) | C-P | O-MOB2, O-9, FEBASE |
| M04 | POST `/api/parent/v1/child-profiles` | POST `/v1/parent/profiles` | counterpart | yes | FE | — | legacy path; extra consent fields; nested response; no `Idempotency-Key` | **MISSING** (T) | C-P | O-MOB2, O-9, FEBASE |
| M05 | PATCH `/api/parent/v1/child-profiles/{profile_id}` | PATCH `/v1/parent/profiles/{profile_id}` | counterpart | yes | FE | — | legacy path; response wrapper; no key | **MISSING** (T) | C-P | O-MOB2, O-9, FEBASE |
| M06 | POST `/api/parent/v1/child-profiles/{profile_id}/data-authorizations` | — (legacy, removed) | none | no | OD | — | no route; no key; DTO and status NV | — | — | O-PCONSENT |
| M07 | DELETE `…/child-profiles/{profile_id}/data-authorizations` | — (legacy, removed) | none | no | OD | — | no route; DTO and status NV | — | — | O-PCONSENT |
| M08 | DELETE `/api/parent/v1/child-profiles/{profile_id}` | DELETE `/v1/parent/profiles/{profile_id}` | counterpart | yes | FE | — | legacy path; 202 delete-pending receipt vs FE profile envelope; no key | **MISSING** (T) | C-P | O-MOB2, O-9, FEBASE |
| M09 | GET `/v1/story-runs/active/current` | same | exact | yes | FE | — | FE type omits `run_revision`; route summary still "[PROPOSAL]" — **OPEN (M2 ledger O3), not decided** | COVERED 139 (T + PR) | C-P | O-MOB2, O-9, FEBASE, O-0 |
| M10 | GET `/v1/story-runs/{run_id}` | same | exact | yes | FE | — | FE type omits `run_revision`; `{id}` vs `{run_id}` is spelling only | COVERED 140 (+126, 127) (T) | C-P | O-MOB2, O-9, FEBASE, O-0 |
| M11 | POST `/api/parent/v1/story-runs` | POST `/v1/story-runs` | counterpart | yes | FE | — | legacy path; extra body fields; no key; no `run_revision`; no active caller | PARTIAL 125 (T) | C-P | O-MOB2, O-9, FEBASE, O-0 |
| M12 | POST `/api/parent/v1/story-runs/{run_id}/subject-confirmations` | POST `/v1/story-runs/{run_id}/subject-confirmation` | counterpart | no | FE | — | legacy plural path; no key; outside the 8 | PARTIAL 130 (PR) | after O-PROJ | O-PROJ, O-MOB2, O-9, O-0 |
| M13 | POST `/api/parent/v1/story-runs/{run_id}/story-revision-confirmations` | POST `/v1/story-runs/{run_id}/script-confirmation` | counterpart | no | FE | — | legacy path; no key; outside the 8; no presentation caller | **MISSING** (PR) | after O-PROJ | O-PROJ, O-MOB2, O-9, O-0 |
| M14 | POST `/api/parent/v1/ai/story-runs/{run_id}/story-revisions` | same | exact | no (blocked) | OD | — | assistance blocked by M2; frozen response generic, so the **exact FE response DTO is NV**; the legacy caller omits the key | MISSING (OO) | refusal case only | O-ASSIST |
| M15 | GET `/api/lesson-library/v1/me/lessons` | same | exact | no | FE | — | no cursor continuation (asks 50); same operation as WP | PARTIAL 063 (OS) | Parent Lesson Library slice (**PROPOSED**) | O-PROJ, O-MOB2, O-9, FEBASE, CONV-1 |
| M16 | GET `…/me/lesson-invitations` | same | exact | no | FE | — | no continuation; item type subset | PARTIAL 060 (OS) | same (**PROPOSED**) | same |
| M17 | POST `…/me/lesson-invitations/{access_grant_id}/accept` | same | exact | no | CONN | E-only | key present; response typed unknown; runtime errors NV | PARTIAL 061 (OS) | CONV-1 (E) | O-CONV |
| M18 | POST `…/me/lesson-invitations/{access_grant_id}/decline` | same | exact | no | CONN | E-only | same | PARTIAL 062 (OS) | CONV-1 (E) | O-CONV |
| M19 | GET `…/me/parent-group-invitations` | same | exact | no | FE | — | no continuation; membership type omits fields | PARTIAL 066 (OS) | Parent Lesson Library slice (**PROPOSED**) | O-PROJ, O-MOB2, O-9, FEBASE, CONV-1 |
| M20 | POST `…/me/parent-group-invitations/{membership_id}/accept` | same | exact | no | CONN | E-only | key present; runtime errors NV | PARTIAL 067 (OS) | CONV-1 (E) | O-CONV |
| M21 | GET `…/me/lessons/{lesson_id}` | same | exact | no | FE | — | FE type omits required `locale` | PARTIAL 064 (OS) | Parent Lesson Library slice (**PROPOSED**) | O-PROJ, O-MOB2, O-9, FEBASE, CONV-1 |
| M22 | GET `…/me/lessons/{lesson_id}/download` | same | exact | no | CONN | E-only | `LessonExportV1` shape matches; **presentation caller NV** | PARTIAL 065 (OS) | CONV-1 (E) | O-CONV |
| M23 | POST `/api/parent/v1/ai/sketch-guides` | same | exact | no (blocked) | FE | — | FE `step_count:3`, BE 3–5, SRS FR-P-11 4–8; FE expects an image, SRS a validated SVG; **presentation caller NV** | MISSING (OO) | refusal case only | O-ASSIST |
| M24 | POST `/api/parent/v1/ai/drawing-understandings` | same | exact | no (blocked) | FE | — | legacy artwork-ingestion flow; base64 in JSON vs SRS upload-session rule; integration blocked by M2 | MISSING (OO) | refusal case only | O-ASSIST |
| M25 | POST `/api/parent/v1/ai/story-runs/{run_id}/activity-suggestions` | — | none | no | OD | — | no route; no SRS path. The 2026-11-11 Rev78 owner direction (catalog-first suggestions) is recorded in `docs/context/SOURCE_REGISTER.md`, not in the audits | — | — | O-ASSIST |
| M26 | POST `/api/auth/v1/registrations` | same | exact | no | GAP | — | sends no bearer, X-Request-ID or idempotency key; BE also returns `email_verified`; errors not §9.8 | **MISSING** (OO) | CONV-1 | O-CONV |
| M27 | GET `/api/auth/v1/me` | same (= A01) | exact | no | GAP | — | X-Request-ID absent; BE also returns `role_revision`; errors not §9.8. Same operation as A01, which is OD for the web caller (primary differs by caller) | PARTIAL 141 (OO) | CONV-1 | O-CONV |

**Mobile primary counts (27 rows):** FE 16, OD 5, GAP 2, CONN 4 (E-only: M17, M18, M20, M22), COND 0.
- **Called paths:** exact 17 (M02, M03, M09, M10, M14–M24, M26, M27); counterpart 6 (M04, M05, M08, M11, M12, M13); none 4 (M01, M06, M07, M25).
- **The 8 M2-allowed operations:** 4 are called exactly (M02, M03, M09, M10) and 4 only through the legacy counterpart paths (M04, M05, M08, M11). Bruno has a request for 5 of the 8: 4 COVERED (positive-only) and 1 PARTIAL. M04, M05 and M08 have none.

### 3.1 Parent capability gaps (P3: no mobile caller and no BE route)

| ID | SRS capability (stated route) | Class | Next slice | Blocked by |
|---|---|---|---|---|
| MG01 | Attach validated artwork — POST `/v1/story-runs/{id}/assets` | GAP | new Parent StoryRun slice | O-PROJ. The 6 `dev`-only `storyrun-lite` routes are a candidate base, not in the freeze |
| MG02 | Text/audio idea — POST `/v1/story-runs/{id}/idea` | GAP | same | planning |
| MG03 | Job polling — GET `/v1/jobs/{job_id}` | GAP | same | planning |
| MG04 | Video admission — POST `/v1/story-runs/{id}/video-generations` | GAP | Billing B-3 + StoryRun | Billing B-1 |
| MG05 | Mark video unsuitable | GAP | Parent StoryRun slice | planning |
| MG06 | Complete run | GAP | same | planning |
| MG07 | Delete completed run | GAP | same | planning |
| MG08 | Playback token | GAP | same | planning |
| MG09 | Parent quota summary — GET `/v1/video-quota` (same capability as G10) | GAP | Billing B-3 | Billing B-1 |
| MG10 | Notifications inbox | GAP | MGR-10 (no owner) | owner assignment |
| MG11 | Push endpoint register/revoke | GAP | MGR-10 (no owner) | owner assignment |
| MG12 | StoryRun history (no SRS method/path) | GAP + OD | — | SRS path open; do not invent |
| MG13 | Parent lesson delivery history and feedback (FR-PL-21/22; no SRS path) | GAP + OD | — | SRS path open |
| MG14 | Child-profile sharing/revoke (FR-PL-07; no SRS path) | GAP + OD | — | O-PCONSENT |
| MG15 | Quota purchase — POST `/v1/video-quota/purchases` | excluded — payment | PT | Q193, O-PAY |

**Demo and mock surfaces (P3; not registered as mismatches):**
- `src/demo/api.ts`: 23 declared paths; parity NV.
- `src/services/api.ts`: a dormant mock with 8 paths.
- Firebase provider calls.

## 4. Frozen operations outside both audits (P4 scope residue)

**"Touched"** means audited by P2 or P3, or mapped by P3 as a counterpart. The count is the de-duplicated union over the 151 frozen operations: A01 = M27 and WP = M15 are each counted once, and 6 of the operations are reached only through counterpart paths (R1-14).

On that definition the P2 and P3 rows touch **63** operations. The other **88** were not audited against an FE caller:

| M2 class | Count | What they are | Handling |
|---|---:|---|---|
| CB (BE1 compatibility) | 44 | classroom sessions, device grants, room code, canvas, checkpoints, groups, gallery, observations, data requests, portfolio, BE1 health | NOT AUDITED; no web or Parent mobile caller in P2/P3 → O-L3SCOPE |
| CD (demo-group compatibility) | 35 | `/v1/sessions…`, renderer, whiteboard, preview | NOT AUDITED. Some session paths appear among the 23 paths of mobile `src/demo/api.ts`, but the mapping is **NV** (renderer, whiteboard and preview are not among them) → O-L3SCOPE |
| LE (local example) | 3 | `/api/dev/v1/storage-examples…` | COND → O-L3SCOPE |
| PO + CB (pilot-only) | 4 | assistance requests: create, cancel, status, pending | COND; Bruno MISSING → O-L3SCOPE |
| T | 1 | POST `/v1/story-runs/{run_id}/cancel` | M2 target, not in the client projection (M2 ledger O2); the mobile adapter returns "unavailable"; Bruno PARTIAL 129 → O-PROJ |
| PR | 1 | POST `/v1/story-runs/{run_id}/context-confirmation` | no mobile caller; Bruno MISSING → O-PROJ |

**Bruno status of the 88:** 83 PARTIAL and 5 MISSING (the four PO + CB operations and context-confirmation).

**Context:** the M2 freeze (D-171 item 7) classes CB and CD as compatibility surfaces to be deprecated, while roadmap L3 says "audit every runtime operation". O-L3SCOPE settles which applies to the 86 CB, CD, LE and PO operations.

## 5. Next-slice queue derived from the register

| Slice | Rows | Gate before work | Count |
|---|---|---|---|
| G0 (S-LL) | A11, A14, A15 (confirm); A13 (400 code); prerequisite for every Lesson Library row | ENV-P1 (done), P1 run | 3 direct + 1 |
| CONV-1 | global E and PX on all rows. Primary or E work: A01, A06, M17, M18, M20, M22, M26, M27, i.e. **7 operations** (A01 = M27). Pagination rule for A03, A07, A09, A10, A16, M02, M15, M16, M19 | G0 commit (or the owner parks S-LL); O-CONV | 8 rows / 7 operations + 9 pagination rows |
| C-P Parent first slice | M02, M03, M04, M05, M08, M09, M10, M11, plus 3 Bruno requests for M04, M05, M08 | O-MOB2, O-9, FEBASE (mobile), O-0, C-D10 | 8 |
| Parent Lesson Library slice (**PROPOSED — not in Draft 4 or the addendum**) | M15, M16, M19, M21 | O-PROJ (these OS operations are outside the M2 projection), O-MOB2, O-9, FEBASE, CONV-1 | 4 |
| C-M / W-* | A07, A09, A10, A12, A13, B01, B02; G01, G02, G06, G09 | Draft 4 §5.2–5.4 | 7 rows + 4 gaps |
| C-T | A16, A18, A19, A21, A23, A24, A25, B07, B08, C01; G03, G14 | G0 (shared Lesson Library files), CONV-1 | 10 rows + 2 gaps |
| C-A | A03, A04, A05, B09; G07, G08 | CONV-1; O-CONTENTADMIN for B09/G07/G08 | 4 rows + 2 gaps |
| L2 (Billing) | B01 (with W-CAP); G10 = MG09; MG04 | Billing B-1, O-PAY | 1 row + 3 IDs / 2 capabilities |
| Excluded / refusal-only Bruno | B03–B06 (EXCL); AI1–AI3, C02, M14, M23, M24 (COND or blocked) | — | 11 |
| Owner decision only (no slice yet) | M01, M06, M07, M25; M12, M13 (O-PROJ) | the named decisions | 6 |
| BRU-0 Bruno baseline (connected; no route-specific defect recorded) | A02, A08, A17, A20, A22, A26, A27 | A-5, O-TOKEN, SEED-1 | 7 |

## 6. Decisions referenced (none is made here)

**From Draft 4:**
- O-0, O-CONV, O-SEQ, O-PAY;
- O-2a..c, O-3a..d, O-6a..c;
- O-5, O-X, O-9, O-BRU, O-SRS.

**From the addendum §9:**
- ENV-P1 (done);
- O-MOB2, O-PCONSENT, O-PRIV, O-ASSIST, O-CONTENTADMIN, O-ACCREV, O-UPLOAD, O-TOKEN.

**From A-3:** C-D1 to C-D10. **From A-4:** D-A to D-E.

**From M2 (open, owner Person 2):** ledger O2 (cancel), O3 (`[PROPOSAL]` summary), O4 (extra envelope fields).

**New in this register:**

| ID | Question | Rows |
|---|---|---|
| O-PROJ | Extend the M2 client projection beyond the 8 operations, and in which order:<ul><li>subject, script and context confirmation;</li><li>cancel (overlaps M2 ledger O2);</li><li>the Parent Lesson Library `/me` operations (OS class).</li></ul> | M12, M13, M15, M16, M19, M21; cancel; context-confirmation; MG01 |
| O-L3SCOPE | Are the **86** CB, CD, LE and PO + CB operations of §4 in the L3 audit and L4 wiring scope, and under which role or client? The freeze (D-171 item 7) marks CB and CD for deprecation. The remaining 2 of the 88 belong to O-PROJ | §4 |

## 7. Limits

- This register regroups pinned static audits. No source, test, Bruno or worktree file was read or changed for it, beyond the P4 matrix parse and the A-4 brief's read-only Git facts.
- No test, build, validator, runtime, database, Docker, network or Bruno run.
- DTO, status and scope claims carry the audits' NV marks. The MGR-8 effects remain NV until G0.
- Primary classes follow the audits. A coordinator reclassification would be marked "RC:"; Draft 2 has none left, because it restores the audit classes for M12, M13, M23 and M24.

## 8. Disposition of the Draft 1 review (not re-reviewed)

| ID | Disposition |
|---|---|
| R1-01 | NV marks restored: A11, A12, A16, A17, A18, A19, A20, A21, A24, A25, A26, A27, M14, M22, M23; plus the P3 NV cells of M01, M06, M07 |
| R1-02 | §1 rules: E-only rows are CONN with a marker (M17, M18, M20, M22); "GAP (E)" removed from A01, M15, M16, M19, M21; primaries may differ by caller (A01/M27, WP/M15), stated in the rows |
| R1-03 | M12, M13, M23 and M24 back to the audit class FE; O-PROJ and O-ASSIST moved to "Blocked by"; §7 wording fixed |
| R1-04 | The Parent Lesson Library slice is marked PROPOSED; gates O-PROJ, O-MOB2, O-9, FEBASE, CONV-1 added to it and to M15, M16, M19, M21 |
| R1-05 | M09: "OPEN (M2 ledger O3), not decided" |
| R1-06 | A02 exempt from PX; the M2 exemption applies by frozen path; O-9 and O-0 added to M12/M13 |
| R1-07 | §1 cites M2 ledger O4 for the provisional E exemption |
| R1-08 | §5 L2 "3 IDs / 2 capabilities"; CONV-1 "8 rows / 7 operations" |
| R1-09 | §1 Owners: slice-level, aligned with the addendum (Person 2 / CaoDat for BE); MWO removed |
| R1-10 | §1 Bruno legend; §0 pins the addendum, Draft 4 and the A-4 brief; the C-03 correction is carried |
| R1-11 | §4 CD mapping marked NV; O-L3SCOPE widened to 86 operations, with the other 2 under O-PROJ; D-171 item 7 and M2 ledger O2 cited |
| R1-12 | M25 cites the source register; §5 BRU-0 says "no route-specific defect recorded" |
| R1-13 | M26 and M27 header facts added |
| R1-14 | §4 defines "touched" |
| Also | Slice labels renamed to avoid the clash with Billing B-1 to B-5 (CONV-1, SEED-1, FEBASE, BRU-0); the counterpart rows linked to the A-4 brief finding |
