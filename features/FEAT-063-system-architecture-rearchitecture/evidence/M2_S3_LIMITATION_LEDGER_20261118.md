# FEAT-063 M2-S3 — limitation and inherited-condition ledger — 2026-11-18

- **Task:** M2-S3 under `plan/M2_S3_TASK_APPROVAL_DRAFT11_20261118.md` (SHA-256 `C45B9D89BAB0960780BAD45A1350280ED22D8CBDCD166F073F83868F732C9C6E`), approved under D-213 item 7; S3 base commit `7950d303239455ba492e33ffe3bae3828be9a469`. Written by the coordinating Claude session (Opus 5.5); not independently reviewed at the time of writing.
- **Rule:** built by reading each phase's closure and acceptance records. Every item has an owner or a phase ("conditions được gán owner/phase", baseline line 265). "Person 2" is the task owner of this lane (BE co-owned). An item marked "Person 2 to assign" has no decided owner or phase yet; that is itself recorded. S3 repairs, masks or broadens none of these.

## 1. Deferred or partial by decision

| # | Item | Status | Owner or phase |
|---|---|---|---|
| D1 | S1b (grant, revoke, consent, share) | DEFERRED in M2 (D-171 item 1; D-197) | M6 or a later phase |
| D2 | M2-AT-05, 06, 07 | NOT RUN / DEFERRED | with S1b (M6 or later) |
| D3 | NFR-36 | PARTIAL: child-media access deferred to M5, cross-organisation feedback to M6, Platform Admin child-media access deny by default (D-171 item 1). An M2 disposition, not completed SRS acceptance | M5, M6 |
| D4 | NFR-38 | PARTIAL: M2 claims age and language metadata only; AC-65 story to M4, video to M5 (D-171 item 1) | M4, M5 |
| D5 | M2-AT-09 | NOT RUN / DEFERRED (D-210 item 1); client integration with the three assistance operations blocked until the OpenAPI P3 gate is closed and a PostgreSQL gate for M2-AT-09 has passed (D-211 item 1) | a future gate G2; Person 2 |
| D6 | OpenAPI P3 gate for the two assistance POST operations | OPEN; S3 does not close it (D-210 item 2) | with D5 |
| D7 | Departure 1: "mọi M2-AT khác phải chạy và pass" relaxed (M2-AT-08 and the StoryRun part of 10 by gate G1 with deviations; 09 deferred; 01, 04A, 04B and the service and contract part of 10 at a narrowed scope) | stated departure; basis D-210 items 3 and 4 | Person 2 (accepted by the decisions named) |
| D8 | Departure 2: "đóng OpenAPI P3" not done | stated departure | with D6 |
| D9 | Departure 3: "OpenAPI parity được kiểm" checked in part only (nine target operations by reading; 134 catalogued by the mapper comparison; the rest NOT CHECKED) | stated departure (D-211 item 2) | Person 2 |
| D10 | Departure 4: the client-integration stop narrowed to the three assistance operations; the N-1 route test sentences ("trước D9 hoặc frontend/client integration", lines 317 and 396; "trước D9/client integration", lines 76, 264 and 407) departed from to the same extent; M2-S2 closed without the test the same sentences require "trước khi thoát S2" | stated departure (D-211 item 1; D-210 item 1) | Person 2 |
| D11 | Departure 5: baseline line 409 narrowed to a per-operation rule for the Parent target operations; at the freeze, client integration with the cancel operation is not allowed (absent from the projection) | stated departure (D-212 item 2) | Person 2; the cancel item with D18 |

## 2. Baseline items not covered

| # | Item | Status | Owner or phase |
|---|---|---|---|
| B1 | BR-58 | NOT COVERED in M2 (D-148 item 8); Parent-group and invitee audience belongs to M6 | M6 |
| B2 | FR-C-10 and BR-35 | The baseline says no profile deletion route in M2 (line 300); S1a-P2 added a Parent profile deletion request (`DELETE /v1/parent/profiles/{profile_id}`, 202 pending). Recorded as it is | Person 2; FR-C-08 and the lifecycle phase |
| B3 | Baseline line 300: no list route in M2 | S1a-P2 added `GET /v1/parent/profiles`. Recorded as it is | Person 2 |
| B4 | B1 stale-owner orphan gate (baseline lines 392 and 407: invalidation, reconciliation, read-exposure contract and regression before non-synthetic data or a provider) | NOT ESTABLISHED: no record read for S3 states it closed. D-171 item 10 decides that an orphan result is accepted only with a result ref and an authoritative receipt (a rule, not regression evidence); M2-AT-09 is deferred | before non-synthetic data or a provider (Person 2) |
| B5 | The three SRS section 21.2 foundation routes (`/v1/organizations/{org_id}/classes`, `/v1/classes/{class_id}/assignments`, `/v1/classes/{class_id}/profiles`) | ABSENT FROM RUNTIME; the BE1 compatibility operations carry the M2-AT-02, 04A, 04B evidence (D-211 item 4) | Person 2 to assign |
| B6 | Per-requirement cells NOT COVERED (acceptance-test ledger section 2): grant and share routes and tables (FR-PL-07, FR-PL-08, BR-48), age-band catalog route and owner (FR-PL-25, BR-57) | NOT COVERED | S1b with M6 (grants); Person 2 to assign (age-band catalog) |

### Baseline section 7 item 5 (D-213 item 5)

Item 5: "Target migration/schema inventory/data disposition/rollback limits được owner phê duyệt; DB/source/snapshot gate lệch thì dừng." Mapped by reading S2 Draft 18 (`5CA09CC6...`) and the gate G1 records:

| Part | Record of the owner's approval | Status | Owner or phase |
|---|---|---|---|
| Target migration | gate G1 Draft 2 section 4 pins the 13 heads, approved with the gate (approval entries of 2026-11-17 and 2026-11-18); D-211 item 3 accepts the migration of an empty PostgreSQL 17 database to them as establishing the Story-chain target on a new database | COVERED for a new database; for the task database `sketch2life_m2_s1a` NOT COVERED (K3 NOT VERIFIED) | Person 2 |
| Schema inventory | no owner-approved M2 target schema inventory found. Facts only: the S1a-P Gate B post-inventory (120 tables) was accepted for that run (D-188); gate G1 observed 123 tables after migration on its own database (an observation, not an approved inventory) | NOT COVERED | Person 2 to assign |
| Data disposition | no decision found for the synthetic rows in the task database `sketch2life_m2_s1a` (left by S1a-T, S1a-P Gate B and the failed Gate P2 attempt; the S1a-T acceptance says no phase may clean them up without a decision) or for the 58 synthetic rows of A2 (baseline section 5.2, kept by default) | NOT COVERED | Person 2 to assign |
| Rollback limits | S2 Draft 18 section 5 records source facts (`20261112_parent_story_context` upgrades only on an empty `story.runs`); the baseline section 5.3 records that `20261103_story_upload_compat` is not reversible; no downgrade was run; no owner approval of rollback limits found | NOT COVERED | Person 2 to assign |

The second sentence of item 5 ("Offline-check là historical fact-only; Alembic execution, live graph reconciliation và M2 mypy baseline chưa chạy nên không đóng gate"):

| Part | Status | Owner or phase |
|---|---|---|
| Alembic execution | run on an empty PostgreSQL 17 database to the 13 pinned heads by gate G1 (owner-run, 2026-11-18) | — (established for a new database only) |
| Live graph reconciliation | NOT RUN on the task database | Person 2 to assign |
| M2 Mypy baseline | no owner-approved M2 Mypy baseline; S2 closed on a comparison (19 added `arg-type` diagnostics waived, 336 existing) and earlier phases on baseline comparisons (exit 1 is NO PASS) | Person 2 to assign |

## 3. Gate G1

| # | Item | Owner or phase |
|---|---|---|
| G1 | Deviations DV-1 to DV-19 (G1 Draft 2 section 3.1; gate-run draft section 4), accepted with the result | Person 2 (accepted) |
| G2 | S2 Draft 18 row 13 not covered | Person 2 to assign |
| G3 | One run on one machine and one PostgreSQL minor version | Person 2 to assign |
| G4 | No operating-system egress block; containment by a Python-level socket guard and literal loopback addresses; trust authentication on the container's local socket | Person 2 to assign |
| G5 | The API ran as the role that owns the schema; privileges of a separate runtime role not shown | Person 2 to assign |
| G6 | Create with a lesson version not exercised | with the lesson pin (D-196 defers it) |
| G7 | No real-provider behaviour | M3 or later; `OWNER_MODAL_CALL_APPROVED=NO` |
| G8 | The first gate attempt, read literally under the approved rule, is a failed attempt; the result comes from an owner-approved second attempt (review finding K1) | Person 2 (accepted knowing it) |

## 4. Product defects found after the S2 closure

| # | Item | Owner or phase |
|---|---|---|
| P1 | Four PostgreSQL write defects in `parent_story_repository.py` (W1 to W4), repaired in `b430b67a` | Person 2 (repaired) |
| P2 | W3 (pending receipt used by story-revision reservation) not verified on PostgreSQL | Person 2 to assign |
| P3 | Other repositories not surveyed for the same two patterns (explicit `None` bound to a JSONB column; ORM add without flush before a Core insert under `autoflush=False`) | Person 2 to assign |
| P4 | M2-S2 was closed while these defects existed; no addendum to the S2 closure record has been decided | Person 2 (open question) |

## 5. What S2 was closed with

| # | Item | Owner or phase |
|---|---|---|
| S1 | 19 added Mypy `arg-type` diagnostics in `parent_ai.py` and `parent_story_runs.py`, waived as typing debt; 336 existing signatures | Person 2 (follow-up, not started) |
| S2 | 17 existing Ruff diagnostics on the six S2 source paths and one `I001` on `tests/contract/test_openapi_contract_catalog.py` | Person 2 (follow-up) |
| S3 | Only the nine-file pytest selection ran, not the full backend suite | Person 2 to assign |
| S4 | The production role adapter not exercised on PostgreSQL (D-190) | Person 2 to assign |
| S5 | The stale-version P3 on routes other than cancel | Person 2 (follow-up, outside D-207) |
| S6 | The FEAT-047 description overlay on `be1_artifacts.py` kept | Person 2 |
| S7 | The unexplained hang of 2026-11-14 | Person 2 to assign |
| S8 | The deviations S2 Draft 18 section 6 records against the SRS (image-first order, main-activity selection, context snapshot, lesson pin, purge and job cancellation, `/v1/jobs`), kept as DEVIATION and not conformance (D-203) | Person 2; later phases by separate scope decision |
| S9 | S2 open items: response fields of the cancel receipt not specified by D-204 or an existing contract stay OPEN (D-204); a safe current-run reference in the create conflict body OPEN (D-199); which request or dispatch follows context confirmation OPEN or NOT VERIFIED (S2 Draft 18 section 4, BQ-1 table; the S1a-P2 addendum section 5 records a run left in `INPUT_PROCESSING` after context confirmation); OQ-S2-4 and OQ-S2-5 deferred (D-196) | Person 2 |

## 6. Mapper task and closure verification

| # | Item | Owner or phase |
|---|---|---|
| M1 | Four commands needed a second run (failed first runs kept on record) | Person 2 (accepted) |
| M2 | The post export ran without the egress block (accepted deviation) | Person 2 (accepted) |
| M3 | Two test files changed after the export and comparison without re-runs | Person 2 (accepted) |
| M4 | The approval record changed between the exports (Amendment 1) | Person 2 (accepted) |
| M5 | Two pytest invocations where one was specified | Person 2 (accepted) |
| M6 | The request-identifier inventory OPEN beyond Amendment 1 | Person 2 to assign |
| M7 | The closure comparison ignores line numbers | Person 2 (accepted) |
| M8 | The closure driver's timeout path never exercised | Person 2 to assign |

## 7. S1a-P2 specifics

| # | Item | Owner or phase |
|---|---|---|
| Q1 | Real-PostgreSQL PATCH, deletion request and list NOT VERIFIED (closure record); the scratch-database addendum is supporting evidence only, not a closure | Person 2 (gap open) |
| Q2 | Validators and `git diff --check` not run after the rework | Person 2 to assign |
| Q3 | The production BE1 adapter not covered (D-190) | Person 2 to assign |
| Q4 | Gate P2 attempt 1 FAILED and consumed; P2-AT-03 NOT RUN; three synthetic rows left without cleanup | Person 2 |

## 8. S1a

| # | Item | Owner or phase |
|---|---|---|
| A1 | D-188 limitations: K3 unresolved; upstream age-band reference not satisfying NFR-38 and AC-65; strict Mypy exit 1 not PASS; temporary approval-parser pytest NOT VERIFIED; Gate A `PYTHONPATH`/`PYTHONHOME` inheritance risk accepted on the owner's report; `PROCESS_TREE_CHILD_ENUMERATION=NOT_VERIFIED` for Gates A and B; system-role negatives NOT RUN; external consumers of the Teacher-profile POST NOT VERIFIED, Bruno 013 and `validate_be_full_collection.py` documentation debt | Person 2 |
| A2 | K3 NOT VERIFIED (D-188, D-198) | Person 2 to assign |
| A3 | S1a-T debt under D-170 (including the items in `openapi_contract.py` and six Ruff `I001`; acceptance of the I001 diagnostics and of the coordinator-run offline pytest reruns left open by D-171 item 13 and the S1a-T acceptance entry); Ruff, the security validator and `git diff --check` not re-run on the final S1a-T PostgreSQL test file | Person 2 |
| A4 | Partial coverage of M2-AT-04A (capacity) and 04B (expected class revision) | Person 2 to assign |
| A5 | Synthetic rows left in the earlier task database `sketch2life_m2_s1a` | Person 2 (see data disposition, section 2) |

## 9. Story-chain target

Established for a new database by gate G1's migration of an empty PostgreSQL 17 database to the 13 pinned heads, which include `20261112_parent_story_context` (D-211 item 3). Nothing is concluded about the earlier task database. The term comes from D-196, D-198 and the S2 drafts (the explicit Alembic target on the Story chain), not from the S1a records. K3 stays NOT VERIFIED. Owner: Person 2.

## 10. Mounted operations with no current authority, and the cancel operation

| # | Item | Owner or phase |
|---|---|---|
| O1 | Eleven mounted operations without a current authority, listed as OPEN-OWNER (D-211 item 5): `POST /api/auth/v1/registrations`; `GET /api/auth/v1/me`; `GET` and `POST /api/platform-admin/v1/accounts`; `PATCH /api/platform-admin/v1/accounts/{account_id}`; `POST /api/parent/v1/ai/sketch-guides`; `POST /api/parent/v1/ai/drawing-understandings`; `POST /api/parent/v1/ai/story-runs/{run_id}/story-revisions`; `POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-plan-suggestions`; `POST /api/teacher/v1/organizations/{organization_id}/ai/sketch-decks`; `POST /api/teacher/v1/organizations/{organization_id}/ai/lesson-visuals` | Person 2 (classification follow-up) |
| O2 | `POST /v1/story-runs/{run_id}/cancel` uncatalogued (no description) and absent from the client-facing projection; client integration not allowed until closed | Person 2 |
| O3 | `GET /v1/story-runs/active/current` summary begins "[PROPOSAL]" although D-199 makes it an M2 target read | Person 2 |
| O4 | Error-envelope reading of the parity table: the added fields `request_id` and `current_version` are tabulated NOT STATED IN THE SRS | Person 2 (to confirm or overrule) |

## 11. Kept on the owner's machine, not in the repository

The mapper export folders under `backend/tmp/` (git-ignored); the gate containers and volumes `s2l-m2-s2-gate`, `s2l-m2-s2-gate-2`, `s2l-m2-s2-rehearsal-4`, `s2l-m2-s2-rehearsal-5`; the run outputs under the repository-root `tmp/m2-s2-pg-gate/runs/`; the gate secret directory; the gate driver. Nothing was removed. Owner: Person 2.

## 12. Open owner questions

| # | Question | Owner |
|---|---|---|
| Q-A | Deletion eligibility of FAILED and ABANDONED runs (FR-C-08; D-209 item 4) | Person 2; FR-C-08 gate |
| Q-B | The decision-number citation convention (identifiers D-135 to D-149 occur twice) | Person 2 |
| Q-C | The SRS pointer in other worktrees and the root checkout (D-209 item 6) | Person 2 |
| Q-D | Re-pinning of the roadmap addendum and other drafts required by D-209 item 5 | Person 2 |
| Q-E | What "D9" denotes: not known (D-213 item 6). Note from review R4: within the baseline, "D8→D9" is used for Draft 8 to Draft 9 (lines 40 and 491), a possible reading not adopted here | Person 2 |
| Q-F | Whether the S2 closure record needs an addendum (P4) | Person 2 |
| Q-G | Commit `7cc5cf74` and its push have no repository record of their own (the status and context entries of 2026-11-17 still say "uncommitted") | Person 2 |
| Q-H | Repository documents that contain local absolute paths: 40 tracked Markdown files at commit `7950d303` (22 of them in the FEAT-063 folder), counted with `git grep -l -E '(^|[^A-Za-z0-9])[A-Za-z]:[\\]' 7950d303 -- '*.md'` (backslash drive form only; the forward-slash form is not counted) | Person 2 |
| Q-I | Whether to record the closure of the S1a-P2 known gap on the strength of the scratch-database addendum (Q1) | Person 2 |
| Q-J | D-151 condition C1: the plan-text defect in foundation plan Draft 10 section 5.3 not corrected in any plan revision | Person 2 |

## 13. Records not independently reviewed (as the records read for S3 state)

- The S1a-T closure record (written by the coordinator; the R7 package and code were reviewed).
- Revision 3 of the S2 closure-verification draft and driver, the Mypy triage, and both evidence reports of 2026-11-17 (S2 closure entry).
- Gate G1 evidence report revision 2 (accepted without a further review; revision 1 was reviewed, R3).
- The S1a-P2 real-PostgreSQL addendum (supporting evidence; no review recorded).
- The S2 shared OpenAPI mapper implementation evidence report and its Amendments 2 and 3 (Amendment 1 was reviewed on an earlier revision, R18).
- The PostgreSQL write-defect fix evidence of 2026-11-18 (W1 to W4).
- The gate-run Task Approval Draft 1 of gate G1 (its basis, the pre-gate delta review R2, reviewed the test, launcher, driver and product fix).
- The four S3 output records, until the independent review of the S3 package.
