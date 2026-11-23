# FR-C-08 wave 1 - independent cold review, round 2 (2026-11-18)

Record only. This note decides nothing for the owner and approves nothing. It is a new file; no existing record was edited. Below the coordinator addendum, the reviewer's report is reproduced as written (only a local path mention was reworded).

## 0. Coordinator addendum

- Started by the coordinating Claude session with the model set explicitly to Sonnet 5.5 and the effort parameter set explicitly to "high" in the start call. The reviewer reports the same caveat as round 1: the effort value visible inside its session was the number 10, so it cannot confirm "high" from inside. The coordinator cannot verify the applied effort. This caveat must not be dropped when this note is cited.
- Verified context given to the reviewer (read-only, `git show 2dddc607:<path>`): CONV-1 exists only on the local, never-pushed branch `feature/feat066-conv1` (worktree `.worktrees/conv1`, commit `2dddc607`, parent `08439b22`, which is the root HEAD). That branch carries D-066-71, the CONV-1 Task Approval entry and the implementation evidence. The root checkout lacks them by design. Q-BASE stays an owner decision.
- Reviewed pins: the four round-3 documents listed in the report below, the pin audit register, the R1 review (9,387 B, AB45B6EA4781C14837A841E0C3B6AF948651D1398E510EE2F06FD7E16C442839) and the canonical SRS (701,157 B, B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5).
- Result: READY WITH NOTES, P1 = 0, P2 = 1, P3 = 8. P1 + P2 fell from 5 (round 1) to 1. Two round-1 findings are only partly fixed (R1-F13, R1-F16); no finding class repeated otherwise.

---

Read-only review. Nothing in the repository was edited, created, staged or committed except this report file. No test, validator, DB, Docker or network command was run. The gate-secrets folder was not read.

## 1. Header

- Round 2 of at most 5. Date 2026-11-18.
- Reviewer: subagent, model Sonnet 5.5 (`claude-sonnet-5-5`). Effort: the caller asked for "high". Caveat, same as round 1: the reasoning-effort value visible inside my session is the number 10, not the label "high", so I cannot confirm from inside that "high" was applied.
- Method: every SRS line number and every verbatim Vietnamese quote in the four documents was compared by script (UTF-8, exact string equality) against the canonical SRS. All 57 unique path/bytes/SHA-256 pins in Allowlist Draft 7 were recomputed. All 98 rows of PIN_AUDIT_R3.md were recomputed. Hygiene was checked with Python byte checks.

Pins verified before review (all match, bytes and SHA-256):

| File | Bytes | SHA-256 match |
|---|---:|---|
| FR_C08_LOST_DRAFTS_NOTE_REV2_20261118.md | 5,450 | yes (EFE648F2...) |
| FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT5_20261118.md | 16,210 | yes (C7985B5C...) |
| FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT7_20261118.md | 22,916 | yes (36048CFA...) |
| FR_C08_OWNER_QUESTIONS_REV2_20261118.md | 20,107 | yes (8AD5E982...) |
| tmp/frc08-wave1/PIN_AUDIT_R3.md | 21,614 | yes (6EA3E5C0...) |
| R1 review FR_C08_WAVE1_COLD_REVIEW_R1_20261118.md | 9,387 | yes (AB45B6EA...) |
| Canonical SRS | 701,157 | yes (B9B1F42D...) |

## 2. Verdict: READY WITH NOTES - P1 = 0, P2 = 1, P3 = 8

P1 plus P2 fell from 5 (round 1) to 1, so the stop rule does not trigger on count. The one P2 (R2-F1, Teacher-assignment source claim) is a wrong source claim that feeds Q-TEACHER. Correct it before Q-TEACHER goes to the owner. It does not block the other eleven questions.

No document asserts an approval, launch, closure or implementation state that the records do not show. No owner decision is pre-made. Hygiene is clean: all four documents and the audit have no BOM, no CR, no trailing whitespace, no dollar sign, no absolute path, no tab, and end with a newline. Vietnamese appears only inside verbatim quotes.

## 3. R1 finding disposition (judged independently, not from Codex's table)

| ID | My status | One-line evidence |
|---|---|---|
| R1-F1 | FIXED (residual P3: R2-F3, R2-F4) | "unreviewed draft" label gone (Allowlist line 5 says do not repeat it). CONV-1 approval, launch and file set are stated NOT VERIFIED for the root checkout, with no claim that CONV-1 is absent or unapproved (Allowlist 5, 11; Q-BASE 125). Per VERIFIED_CONTEXT, `feature/feat066-conv1` commit 2dddc607 carries D-066-71 and the approval, so "not found at root" is true and the documents do not overclaim. The overlap table (Allowlist 13-18) exists. Real intersection with conv1_changed_files.txt is `app.py` and `test_openapi_contract_catalog.py`; the stop rules (Allowlist 24, 164) and "re-pin at chosen base" handle it adequately. |
| R1-F2 | FIXED | Allowlist 134 pins `domain/ai_jobs/model.py` as 17,113 B / `512B604636C1A22E231AC3276D3E537AE0DEAE4D9BB6652CCB064FAB7314DB99`. That is 64 characters and recomputes correctly. No malformed hex token of length 62-65 exists in any of the four documents (61 hex tokens, all 64 characters; this matches the audit's count). |
| R1-F3 | FIXED (minor residual P3: R2-F6) | Q-A (OQ 5-29) now quotes D-208 item 6 verbatim (matches `DECISIONS.md`), BR-39 (283), 383, FR-C-08 (500), NFR-31 (656), 1064, 1350, 1372, UC-07 1470, section 21.2 1674. All quotes match exactly except line 283, which drops only the trailing table pipe. The recommendation states the trade-off (ABANDONED content would have no user route if COMPLETED-only). |
| R1-F4 | FIXED | Contract 53 and 69 now attribute the changed-payload rule to SRS 1697 (section 21.4, heading at 1695) and to the observed source (`parent_story_repository.py:369`), and state D-066-68 C-D5/C-D6 do not contain it. Matches D-066-68 text (C-D5: 1-128 ASCII, missing key 400 INVALID_REQUEST; C-D6: durable receipts). |
| R1-F5 | FIXED | Q-STATES added (OQ 31-41) and Contract 3.1 and the section 6 blocker list. Counts re-derived from source and SRS: 7 accepted literals (`parent_story_repository.py:385-394`), 5 in the 13 SRS-eligible states, 8 SRS-eligible rejected with 409 `INVALID_STATE_TRANSITION`, 2 source-only (`SCRIPT_GENERATING`, `SCRIPT_GENERATION_UNKNOWN`; zero occurrences in the SRS). Response literal (`contracts/schemas/parent_story_runs.py:113-116`) omits ABANDONED and DELETED. SRS line 394 has 18 states, 13 after excluding the five. All correct. |
| R1-F6 | FIXED | The pin register is described as local, git-ignored and not durable (Contract 108, Allowlist 121). Counts corrected to 88 present rows plus 4 outputs = 92 (I parsed PIN_AUDIT.md: 88 + 4). FEAT-066 files described as tracked and clean (`git ls-files` and `git status` agree). The 98 rows of PIN_AUDIT_R3 all recompute. |
| R1-F7 | FIXED | TASK_APPROVAL 3243-3247 (heading plus S3 acceptance and M2 closure items), STATUS 876 (closure heading), STATUS 873 ("M2 is NOT closed", stale) are all cited and correct. |
| R1-F8 | FIXED | Contract 12 and 32 and OQ 7 say D-209 item 4 names UC-07 and section 21.2, not FR-C-08. Matches D-209 item 4. |
| R1-F9 | FIXED | Contract 12, 36, 76 and OQ 77 say D-208 directions carry only where consistent with D-209 and Q-READ and Q-PARENT stay open. |
| R1-F10 | FIXED | Q-READ quotes 780, 805, 1164, 1811 (all exact) and TASK_APPROVAL 3250 (matches). |
| R1-F11 | FIXED | Q-BASE now cites governance records; Q-OWNERS cites D-208 item 4 (exact quote) and says it is not an SRS quote. |
| R1-F12 | FIXED | The four guard-only rows moved to H (Allowlist 6.1, lines 127-134). The missing Core reference-closure and Teacher-authorization paths are declared as blockers (Allowlist 136). `be1_parent_role_adapter.py` is described accurately (it only reads a Parent role). But see R2-F1 for the Teacher claim. |
| R1-F13 | PARTIAL | "OPEN under D-209 Q-A" and "R2 planning preflight" are gone. Internal process labels remain (R2-F5). |
| R1-F14 | FIXED | 0 lines with trailing whitespace in all four documents and the audit. |
| R1-F15 | FIXED | Rollback claim attributed to the owner's report and flagged as not independently evidenced (Lost Note 8). Branch `feature/feat063-m2-s2` = `bc124187d3b700de62d7f932e3cd10490b82d80c` (matches `git rev-parse`). Spec Draft 4 and Lifecycle Plan Draft 4 dispositioned as historical (Lost Note 24-25). D-208 item 8 gate left to Q-M2-GATE. The historical 2026-11-16 review characterization (pin-gate stop, content not reviewed) matches that file. The missing Draft 3 and Draft 5 are not in the `bc124187` tree. |
| R1-F16 | PARTIAL | A Teacher-authorization row exists (Contract 57), but its factual content is overstated (R2-F1). |

## 4. New findings

### R2-F1 (P2) Teacher "no current-assignment resolver" claim is wrong as stated

- Where: Contract line 57; Q-TEACHER (OQ 57: "no current Teacher-assignment resolver for this flow"); Allowlist line 136 and the H list (section 6, 6.1).
- Evidence: `backend/src/sketch2life/interfaces/http/routers/be1_common.py:83` defines `require_assignment(db, principal, organization_id, roles=, class_id=)`. It reads `OrganizationAssignmentModel` rows with `active` true for the subject, filters by `account_role`, and checks role and class. `be1_registry.py:61` wraps it as `_require_m2_assignment`, and `be1_registry.py:108` serves current assignments. `OrganizationAssignmentModel` (`be1_models.py:63-90`) has an `active` flag, a role and a `class_id`, and no version column. So a current-assignment check exists in the HTTP layer; what is missing is a versioned, Story-lifecycle-usable resolver. Neither `be1_common.py` nor `be1_registry.py` appears in the allowlist as E or H. CONV-1 changes both (conv1_changed_files.txt).
- Why it matters: the owner chooses between Q-TEACHER options A (use an existing resolver), B (define a versioned contract) and C (Parent only) on the premise that nothing exists. The documents' own `be1_parent_role_adapter.py` guidance (read-only reference) is accurate, but the sweeping claim is not.
- Minimal fix: reword to "no versioned current-assignment resolver usable by the Story lifecycle was found; an unversioned active-assignment check exists in `be1_common.require_assignment` (`be1_models.OrganizationAssignmentModel`, no version field)". Add `be1_common.py` and `be1_registry.py` as H rows (CONV-1 also edits them).

### R2-F2 (P3) UC-11 summary mixes lines outside 1517-1523 and adds a non-SRS sentence

- Where: Contract line 26.
- Evidence: "UC-11 at lines 1517-1523 requires ... Worker checks must fence costly dispatch and result acceptance; late output must be stale, non-playable, and purged." The worker-check wording is at SRS line 1797, not in UC-11 (1517-1523; line 1521 covers late results only). "No provider interruption result is purge proof" is an inference; the SRS says the lock is not held waiting for provider interrupt (1521).
- Fix: cite 1797 for the worker-check sentence and mark the purge-proof sentence as the coordinator's reading.

### R2-F3 (P3) CONV-1 wording discounts a claim that is true on a local branch

- Where: Lost Note line 36 ("The R1 finding and R3 task prompt contain claims that are not substantiated by the current root records; preserve the discrepancy"), Allowlist line 11 ("This contradicts the R1 finding/R3 prompt's later status assertions"); Q-BASE option B ("first provide and verify the missing CONV-1 approval ... records").
- Evidence: per VERIFIED_CONTEXT, `feature/feat066-conv1` (2dddc607, parent 08439b22) holds D-066-71, the CONV-1 approval and the evidence; `git worktree list` shows `.worktrees/conv1`. R1's own text said the local branch exists. The documents never name the branch.
- Why it matters: the documents correctly avoid labelling CONV-1, but "not substantiated" and "contradicts" read as if R1 was wrong, and Q-BASE B frames the records as "missing" when one read-only `git worktree list` finds the branch. This steers the owner's Q-BASE answer.
- Fix: neutral wording, e.g. "not present in the root checkout; R1 reports a local branch feature/feat066-conv1 that this document set did not inspect". Optionally list that branch in Q-BASE as a candidate for option C.

### R2-F4 (P3) Overlap table attributes a claim to R1 that R1 did not make, and over-lists a test

- Where: Allowlist lines 15-17.
- Evidence: line 16 says `test_app_composition.py` is a "potential composition-test overlap reported during review". The R1 report names only `app.py` and "routers"; it names no test file. `test_app_composition.py` is not among the 36 CONV-1 paths, while `test_openapi_contract_catalog.py` is. The `app.py` and `test_openapi_contract_catalog.py` rows are real overlaps.
- Fix: drop the attribution, or say "candidate overlap; to be checked against the CONV-1 file list at the chosen base". Also note that the `app.py` E purpose ("Apply approved error/correlation behavior only") may be fully covered by CONV-1's error-envelope work (CONV-1 changes `error_envelope.py`, `api_conventions.py`, `app.py`), so the row may be redundant after CONV-1.

### R2-F5 (P3) Internal process labels remain in repository documents

- Where: Allowlist 11 ("R1 finding/R3 prompt"), 90 ("This R2 task does not edit them"), 121 ("R3 recomputes", "R1-F2 applies"), 123; Lost Note 36 ("R3 task prompt"), 26, 38 ("R3 pin audit"); Contract 108.
- Why: the reader of the repository record does not have the R2 or R3 prompts. Same class as R1-F13.
- Fix: use dates or document names ("the 2026-11-18 pin audit") and drop the prompt references.

### R2-F6 (P3) Q-A omits two SRS rows that use the same "xóa run đã hoàn tất" wording

- Where: Owner Questions Q-A (lines 13-23).
- Evidence: SRS line 270 (BR-26: "Khi người dùng xóa run đã hoàn tất hoặc hủy run chưa hoàn tất ...") and line 284 (BR-40: "xóa run hoàn tất xóa linked media/content") both use the completed-run wording, and FR-C-11 (503) repeats "giữ nội dung đến khi người dùng xóa".
- Why it matters: a neutral Q-A should show the rows that support the narrow reading as well as the rows that support the wider reading. Today it lists the keep-until-deleted rows (wider) and 1470, 1674 (narrow), but not BR-26 or BR-40.
- Fix: add lines 270 and 284 (and optionally 503). Also state plainly that no SRS sentence says explicitly whether FAILED or ABANDONED may be deleted by the user.

### R2-F7 (P3) Existing response and governance facts that bear on Q-READ and route planning are missing

- Where: Contract section 4 table; Q-READ.
- Evidence: (a) the current cancel response already carries a fixed `purge_state="PENDING"` (`routers/parent_story_runs.py` build_response, about line 280), which bears on "purge-progress reporting" and on "do not invent progress"; the documents do not mention it. (b) D-212 item 2 (client-facing block) says `POST /v1/story-runs/{run_id}/cancel` is absent from the client-facing projection and is not integrated until its OpenAPI parity item closes, and D-213 item 3 records the `{run_id}` versus `{id}` difference as OPEN; Allowlist 68 mentions only "OpenAPI P3". (c) Q-READ option B, "use existing detail as-is", cannot represent `DELETED`, because the response literal omits it (the Contract notes the omission but Q-READ does not link it).
- Fix: add one source-fact row each for (a) and (b), and one sentence in Q-READ B pointing to Q-STATES.

### R2-F8 (P3) Citation gaps

- The "18-state inventory" and the 13-state count are not cited to SRS line 394 (Contract 28, OQ 33-35). Add the line number.
- Contract line 55 cites `be1_models.py:555-579`; the class starts at 553.
- Route additions would also touch OpenAPI source modules. `openapi_contract.py` is H (Allowlist 119), but `openapi_contract_amendments.py` (changed by CONV-1) and `openapi_srs_v22.py` are not classified at all. State that route or OpenAPI work needs a separate allowlist revision.

### R2-F9 (P3) Supporting audit carries stale classes

- Where: tmp/frc08-wave1/PIN_AUDIT_R3.md lines 74, 81-83.
- Evidence: the four paths are labelled "E source" there but are H in Allowlist 6.1. The audit is a non-deliverable, local file, but it is cited as the verification record.
- Fix: relabel to "H source (reclassified)" or add a note.

## 5. Claims verified clean

- All pins in the section 1 table match; all 57 unique path/bytes/SHA-256 pins in Allowlist Draft 7 match source on disk (including the 22 E rows, 5 doc rows, 3 test rows, 4 H rows of 6.1, 7 migrations, and the frozen references).
- All 98 rows of PIN_AUDIT_R3.md recompute with no mismatch. The counts in the audit (88 predecessor rows, 87 present, 98 total, 61 hex tokens of 64 characters, 9 absent N paths) are correct. The 88 + 4 = 92 correction to the predecessor audit is correct.
- The 9 N paths are all absent. FEAT-066 DECISIONS.md (51,184 B) and TASK_APPROVAL.md (41,171 B) pins match, are tracked and are clean; D-066-68 ends at line 405 with the "still needs its own Task Approval" sentence; the MGR-7 entry is at lines 366-374; there is no CONV-1 mention in the root TASK_APPROVAL.md.
- The 20 verbatim SRS quotations in the owner questions (lines 283, 383, 500, 656, 1064, 1350, 1372, 1470, 1674, 1518, 771, 780, 805, 1164, 1811, 1797, 1473, 1520, 2758, 1469) match the SRS text exactly (283 minus the trailing pipe). Line numbers in all four documents resolve to the cited content (including 1469-1475, 1517-1523, 1697, 1811).
- D-208 items 4, 6 and 8, the D-209 item 4 text, and the TASK_APPROVAL 3250 quote match their sources. M2 closure records at TASK_APPROVAL 3243-3247 and STATUS 876 (with 873 stale) are correct.
- Source claims: route at `parent_story_runs.py:253-294` (202, header 1-256); composition at `router_composition.py:61,75-76` and `app.py:1124-1127`; `cancel_run` at 328-438 with the receipt mismatch at 369; response literal; `DataLifecycleRequestModel.organization_id` (be1_models); `CoreAssetMetadataPort` exposes metadata save/get only (`core_foundation.py:181-186`); `CancellationNotice` has `organization_id` and no Parent handler wires to `apply_cancellation_notice` (grep finds no other call site).
- Twelve owner questions present (Q-A, Q-STATES, Q-PARENT, Q-TEACHER, Q-READ, Q-FENCE, Q-PURGE, Q-WORKFLOW, Q-AUDIT, Q-BASE, Q-M2-GATE, Q-OWNERS). Each has a question, 3 real options and a hedged recommendation; none is pre-decided. "No answers are recorded" is stated. Q-BASE, Q-M2-GATE and Q-OWNERS are governance questions and say they are not SRS quotes.
- No document claims approval, launch, closure or implementation; the Contract and Allowlist are labelled DRAFT / NOT APPROVED / NOT LAUNCHED. M2 closure is described as "with recorded debt and deviations", without transferring approval.

## 6. Not verified, and why

- Runtime, database, migration, generated OpenAPI and object-store behaviour: out of scope (no such commands allowed), and the documents themselves mark them NOT VERIFIED.
- The content of CONV-1 at 2dddc607: I took VERIFIED_CONTEXT and the file list as given; I did not diff that commit against the allowlist E rows beyond path intersection. I did not check whether CONV-1 changes the idempotency header range or the cancel error envelope.
- The owner's rollback report (Lost Note 8): not in the repository, so the claim stays unverified, as the note itself says.
- `git diff --check`: not run (not permitted). Equivalent byte checks (no trailing whitespace, no CR) were done in Python.
- The effort level actually applied to this review (see section 1).
