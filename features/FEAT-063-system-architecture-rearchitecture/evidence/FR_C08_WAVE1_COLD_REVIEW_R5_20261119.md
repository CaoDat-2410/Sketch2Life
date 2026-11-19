# FR-C-08 wave 1 - independent cold review, round 5 of 5 (2026-11-19)

Record only. This note decides nothing for the owner and approves nothing. It is a new file; no existing record was edited. Below the coordinator addendum, the reviewer's report is reproduced as written (local path mentions reworded or shortened to repository-relative paths).

## 0. Coordinator addendum

- Started by the coordinating Claude session with the model set explicitly to Sonnet 5.5 and the effort parameter set explicitly to "high" in the start call. As in rounds 1 to 4, the reviewer cannot confirm from inside its session that "high" was applied, and the coordinator cannot verify it. This caveat must not be dropped when this note is cited.
- The documents under review were written by a separate author session (Sonnet 5.5, medium effort) that executed the saved R6 prompt in place of Codex; neither the coordinator nor the reviewer wrote them. Reviewed pins: Contract Draft 8 (18,143 B, 4ED48421C5F2F1A7491365AAF8672AF38F838B7AA50BA504CDEEE68D1E834ECA), Allowlist Draft 10 (23,348 B, F493F833BE4A0C8EAB02D1F9602958CCA25D058B437D82698FB9136208992847), Owner Questions Rev5 (22,128 B, EA7915648EF3805950F4401AF74E52F0C8B8C06794A1AF8A7695CAF07D2527CF), Lost Drafts Note Rev5 (10,330 B, E6A1E47F3EEF35E18FC9B672BBB4A6DE348D466F2F3D4688ADED04C8C8A40621), the local pin audit register (44,087 B, E970C90294DD087AE3F25BB71B404E851D1C8BA8F9C383A0ED5E716524643461), DECISIONS.md with D-214 (240,776 B, 6E30C69B5E43C2124B9083B6904FEEAE80D7BCEE0917C635F381BA518D32C723) and the canonical SRS (701,157 B, B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5).
- Result: READY WITH NOTES, P1 = 0, P2 = 0, P3 = 5. P1 + P2 by round: 5, 1, 0, 0, 0. All eight round-4 notes are FIXED. Round 5 is the last review round allowed by the owner's limit of five.
- Stop rule: the P1 + P2 count did not rise, but the reviewer reports that finding classes (dropped facts, citation precision, overstated wording) repeat at P3 level only. Per the coordinator's instruction, the owner decides how to proceed; nothing further is run automatically.
- Reviewer observation O-1 (section 8 of the report): the local branch feature/feat066-conv1 has advanced past 2dddc607 with a docs-only commit that changes no backend path and none of the 57 pinned paths. The pins and the overlaps stand. The exact base commit still has to be named by the owner.

---

Read-only review. Nothing in the repository was edited, created, staged or committed. The only repository-level output is this report. Scratch scripts (hyg.py, quotes.py, srsq.py, pins.py) and read-only `git show` copies of source files are under tmp/frc08-wave1-r5review/. No test, validator, database, Docker, network, provider or Modal command was run. No network git command was used. The gate-secrets folder and .worktrees were not opened (CONV-1 content was read only through `git show 2dddc607:<path>`, `git diff --name-only/--name-status`, `git log` and `git rev-parse`).

## 1. Header

- Round 5 of at most 5 (the last allowed). Date 2026-11-19.
- Reviewer: subagent, model Sonnet 5.5 (`claude-sonnet-5-5`, as my environment reports it). Effort: the caller asked for high. Caveat, same as rounds 1 to 4: I cannot see an effort label inside my session and cannot confirm that "high" was applied.
- Method: all 31 verbatim SRS blockquotes in Owner Questions Rev5 compared by script (UTF-8, exact string equality, SRS CRLF stripped) to the SRS line each cites; all 57 Allowlist path pins recomputed with `git show 2dddc607:<path>`; 9 N paths checked at base, HEAD and the working tree; the 8 CONV-1 overlaps recomputed from `git diff --name-only 08439b22 2dddc607` (36 paths); all 109 required-input and predecessor rows of PIN_AUDIT_R6 recomputed against the working tree and its 57 base-pin rows compared with the Allowlist table; every source line range read at `2dddc607`; hygiene by Python byte checks on the four documents and the register; line-by-line diff of Contract Draft 8 vs Draft 7, Allowlist Draft 10 vs Draft 9, Owner Questions Rev5 vs Rev4, Lost Note Rev5 vs Rev4 and Rev3, and a read of Contract Draft 6.

Pins verified before review (bytes and SHA-256 all match the brief):

| File | Bytes | SHA-256 (first 8) |
|---|---:|---|
| plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT8_20261119.md | 18,143 | 4ED48421 |
| plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT10_20261119.md | 23,348 | F493F833 |
| plan/FR_C08_OWNER_QUESTIONS_REV5_20261119.md | 22,128 | EA791564 |
| plan/FR_C08_LOST_DRAFTS_NOTE_REV5_20261119.md | 10,330 | E6A1E47F |
| tmp/frc08-wave1/PIN_AUDIT_R6.md (local register) | 44,087 | E970C902 |
| evidence/FR_C08_WAVE1_COLD_REVIEW_R4_20261119.md | 26,574 | 44C68655 |
| DECISIONS.md (working tree, D-214) | 240,776 | 6E30C69B |
| .claude/handoff/CODEX_FRC08_WAVE1_R6_PROMPT_20261119.md | 9,093 | F3D5D552 |
| .claude/handoff/FRC08_WAVE1_CARRY_FORWARD_20261119.md | 3,703 | DDEA51B2 |

Other facts: HEAD is 08439b22fc3c1f34786a3f45f34530075a3914e0; `git diff --numstat HEAD -- DECISIONS.md` gives 1 insertion and 0 deletions (D-214 is the last table row, append-only); `git diff --cached` is empty; the only modified tracked file is DECISIONS.md. Commit 2dddc6076c793b44cbcd5c0fa3e02a4ccc9902df has the single parent 08439b22. One drift versus the brief is reported in section 8 (observation O-1): the local branch tip is no longer 2dddc607.

## 2. Verdict: READY WITH NOTES - P1 = 0, P2 = 0, P3 = 5

Stop-rule answers:

- (a) Did P1 + P2 rise above 0? No. P1 + P2 by round: 5, 1, 0, 0, 0.
- (b) Does any finding class repeat from round 4? Yes, at P3 level only, and the author should be told plainly:
  - Dropped or incomplete facts (R4-F1, R4-F2, R4-F7; also the R3-F1 rewrite regression; rounds 3, 4, 5): R5-F2 is a Draft 6 fact that was dropped at Draft 7 and is still absent in Draft 8. It is NOT a regression introduced by the latest rewrite: the Draft 8 vs Draft 7 diff shows no unjustified removal (section 5). All four restored R4-F1 facts, the D-214 item 11 carry, the Lost Note lineage and every R4 note are present.
  - Citation / pointer precision (R2-F8, R3-F2, R4-F3, R4-F8; rounds 2, 3, 4, 5): R5-F1 (the FEAT-066 D-066-68 location misstated, plus an omitted body field).
  - Overstated wording (R4-F6; rounds 4, 5): R5-F3 and R5-F4 (D-214 wording widened slightly).
  - Dangling pointer (R1-F6, R3-F10, R4-F4): no instance found in round 5.
  If the coordinator applies the rule literally ("a finding class repeats"), the stop rule triggers on classes, not on count. All five findings are P3, none blocks use, and none changes a pin, a classification or a disposition. That call belongs to the coordinator and the owner.

What is sound: all 31 SRS quotations are exact; all 57 Allowlist pins (bytes and SHA-256, 64-hex) recompute at 2dddc607; 22 E, 6 D, 29 H counted equal stated; 8 overlaps counted equal stated (2 E, 6 H); 9 N paths absent at base, HEAD and working tree; no Teacher path, migration, schema, new route, DTR file or Core reference-closure path is editable in the allowlist; no approval, launch or command ceiling is claimed; hygiene is clean; the register agrees with the Allowlist row for row.

## 3. R4-F1 to R4-F8 disposition (judged independently)

| ID | Status | Evidence |
|---|---|---|
| R4-F1 (a) CancellationNotice.organization_id | FIXED | Contract row "Cancellation notice scope" (line 76) cites `application/ports/ai_jobs.py:249-257`. At 2dddc607 lines 248-257 are the `CancellationNotice` dataclass and line 253 is `organization_id: str` (no default, not optional). Carried into section 3.4 (line 45), blocker 3 (line 96) and Allowlist section 7 (line 141). SRS 1523 lists `ai_jobs.cancellation_notice` (verified). |
| R4-F1 (b) Idempotency-Key 256 vs 128 | FIXED | Contract line 74: five routes at `parent_story_runs.py` lines 136, 269, 306, 331, 362; I counted five `max_length=256` declarations at exactly those lines (create, cancel, context-confirmation, subject-confirmation, script-confirmation; route paths confirmed at lines 126-130, 253-254, 297-298, 322-323, 353-354). `api_conventions.py:59-69` is `parse_idempotency_key`; line 67 is `if not 1 <= len(value) <= 128 or any(ord(char) < 33 or ord(char) > 126 ...)`; `_invalid` returns HTTP 400 `INVALID_REQUEST`. Blocker 8 names the mismatch. Allowlist H row (line 116) repeats it. |
| R4-F1 (c) Cancel persistence + transport list | FIXED, with one new inaccuracy (R5-F1) | Row (line 68), range `parent_story_repository.py:328-438, especially 360-383`: receipt scope/fingerprint check 361-369 (400 `INVALID_IDEMPOTENCY_KEY` at 369), replay 370-378, revision check 380-384 (409 `STALE_REVISION`, `current_version`), seven-state set 385-394, `DELETE_PENDING` and `active_owner_parent_account_id=None` 405-407, revision/version increments 397-398, receipt store 415-427, commit 428. All elements named; "does not prove an integrated lifecycle request, notice, or purge receipt" present. Section 4.1 restores body error fields, uniform 404, 409 `STALE_REVISION` with current version, body `expected_revision`, and the 1-128 key rule, each checked against D-066-68 C-D1..C-D7 and `api_conventions.py:72-80`, `error_envelope.py:213-234`. Residual: the introductory sentence misplaces D-066-68 and drops `request_id` (R5-F1). |
| R4-F1 (d) existing owner-scoped GET | FIXED | Row "Parent owner-scoped read" (line 67): `GET /v1/story-runs/{run_id}`, `response_model=ParentStoryRunEnvelopeV1`, `_require_parent`, `service.get_run`; lines 232-250 verified (decorator 232, return 250). Linked from section 3.3 (line 39). Related dropped fact: R5-F2. |
| R4-F2 D-214 item 11 | FIXED | Contract section 1 paragraph 4 (line 15) carries item 11 and cites `approvals/TASK_APPROVAL.md` lines 3243-3247 and `status/STATUS.md` line 876. I read: TASK_APPROVAL 3243 is the heading "M2-S3 ACCEPTED and M2 CLOSED by the owner WITH RECORDED DEBT AND DEVIATIONS", 3244-3247 the owner decisions; STATUS 876 is "2026-11-18 - M2-S3 ACCEPTED; M2 CLOSED ..." and 873 is "M2 is NOT closed" (stale snapshot) - both at base 2dddc607 and in the working tree (TASK_APPROVAL blob sha equal, c718f2d9). Same citations in Rev5 Q-M2-GATE (line 202) and Lost Note section 4 (line 36); Allowlist section 5 H row (line 94) also cites 3243-3247 and section 9 says no M2 command ceiling transfers. |
| R4-F3 be1_common.py range | FIXED | Contract line 77 cites `be1_common.py:88-156`; at base `def require_assignment(` is line 88 and the last line of the function is 156 (`return tuple(row for row in rows if row.assignment_id in allowed_ids)`). The "83-138" sentence and "2dd" are gone (grep: no `2dd\b`, no `83-1`). `be1_registry.py:107-125` (decorator 107, return dict ends 126; accepted in round 4) and `be1_models.py:63-90`, `:555-578` re-verified. |
| R4-F4 FEAT-066 pin sentence | FIXED | Allowlist section 8 (line 153): "Draft 8 also carried two root-checkout FEAT-066 pins ... not carried here, because CONV-1 changes both files". Both files (FEAT-066 DECISIONS.md, TASK_APPROVAL.md) are `M` in `git diff --name-status 08439b22 2dddc607`. The "remain" sentence is gone. |
| R4-F5 classification of three CONV-1 paths | FIXED | api_conventions.py (6,387 B) and error_envelope.py (12,231 B) are `A` in the CONV-1 diff and absent at HEAD; bounded_image_upload.py (8,146 B) is `M` and present at HEAD. All three are classified H in Allowlist section 5 (lines 116-118) and listed in the overlap table (lines 30-32); their base pins recompute. Counts are consistent everywhere I looked: 57 = 22 E + 6 D + 29 H (Allowlist line 151, Lost Note R4-F5 row, register), 8 overlaps (2 E + 6 H). The descriptions are accurate: `bounded_image_upload.py` imports `build_error_body` from `error_envelope` at base. |
| R4-F6 Owner Questions overstatement; Q-BASE vs item 10 | FIXED | Rev5 line 4: "read together with D-214. D-214 amends nothing in the SRS; its item 1 directs a separate documentation-only SRS revision." Q-BASE disposition (line 188) is word-for-word D-214 item 10 minus the overlap list and the last sentence (the branch-not-root statement is kept in the Effect line). "never-pushed", "2dddc607 or later", "parent 08439b22", "after the owner confirms CONV-1", "exact commit is named when the base is fixed" are all present; "owner-confirmed" is gone. |
| R4-F7 Lost Note lineage | FIXED | Section 1 (line 10) names `evidence/FR_C08_DRAFT3_DRAFT5_COLD_REVIEW_20261116.md`; the file exists (5,487 B); its pin table header is at its line 36 and the 63-hex digest at its line 21; verdict `CHANGES REQUIRED` at its line 4. Section 3 restores the three-row predecessor table (Spec Draft 4, Plan Draft 4, Contract Draft 2 + Allowlist Draft 4; all four files exist in plan/). The nine R2 rows are byte-identical to Lost Note Rev3 (script), the ten R3 rows are kept, and eight R4 rows are appended: 27 history rows in total. |
| R4-F8 nits | FIXED | (i) blank line before the Contract table header (lines 61-63) - scripted check finds no table header without a preceding blank line in any document and no blank line inside a table; (ii) "This draft retains that history accurately." is gone (Allowlist line 34); (iii) `story_run_lite.py:193-208` (decorator 193, `)` closing the handler 208) in Contract line 70; (iv) PIN_AUDIT_R6.md is called local, git-ignored and not a durable repository record at Allowlist lines 15 and 151, Contract line 119 and Lost Note line 40. |

## 4. D-214 fidelity (12 dispositions)

D-214 row: append-only (1 insertion, 0 deletions), last row of the table; the "DECISIONS.md before append 233,645 B / 7EA82DB5..." value equals the blob at 2dddc607 and at HEAD.

| # | Item | Owner Questions Rev5 | Contract Draft 8 | Allowlist Draft 10 | Verdict |
|---|---|---|---|---|---|
| 1 | Q-A option B; DELETE for COMPLETED/FAILED/ABANDONED; no auto purge; separate SRS wording revision (UC-07 1470, 21.2 1674, BR-26 270) | lines 25-28 faithful | 3.2, blocker 1 | section 7 last bullet | OK |
| 2 | Q-STATES option A; 13 states; compatibility map; response-schema decision | lines 41-44 | 3.1, blocker 2; 13 states recounted equal SRS 394 minus 1518 | sections 7 | OK, wording drift noted as R5-F3 ("map or removal") |
| 3 | Q-PARENT option B; DTR/schema delta; never fabricate organization_id | faithful | 3.4; both org-scoped sources named | section 7; no DTR path | OK |
| 4 | Q-TEACHER option C; Parent-only first scope; shared design; adapter deferred | faithful | section 2, 3.5 | sections 1, 7; Teacher paths H only | OK |
| 5 | Q-READ option A; extend existing GET only; no second route; DELETED never from access denial | faithful | 3.3, blocker 5; existing GET now a source fact | no route | OK (R5-F2 on the related dropped fact) |
| 6 | Q-FENCE option A; shared version/fence; provider cancel best-effort, not purge proof | faithful | 3.5 | worker/playback E rows guarded | OK |
| 7 | Q-PURGE option A; Core contracts missing = blocker; keep shared asset | faithful | 3.5, blocker 4 | section 7; core_* H read-only | OK |
| 8 | Q-WORKFLOW option B narrowed to DTR delta over SRS 1523 | faithful | 3.4 | section 7 | OK |
| 9 | Q-AUDIT option A; 180/365 map OPEN-TECHNICAL | faithful | 3.5, blocker 3 | section 7 | OK |
| 10 | Q-BASE option B (item 10 wording) | now verbatim (R4-F6 fixed) | provisional base, blocker 6 | section 1 lines 13, 17; overlaps | OK |
| 11 | Q-M2-GATE option A; closure at 3243-3247 / 876; nothing transfers | cites both ranges | section 1 paragraph 4 (R4-F2 fixed) | section 9 | OK |
| 12 | Q-OWNERS option A selected; names and record location missing; launch blocked | OPEN (line 222) | blocker 7 | section 7 last bullet | OK, still open |

No re-decision and no contradiction of D-214 found. D-214 items 13 and 14 are not copied as current claims; the status labels stay DRAFT / NOT APPROVED / NOT LAUNCHED.

## 5. Removed-content table (regression check)

Contract Draft 8 vs Draft 7 (nine lines removed; every other line identical):

| Removed from Draft 7 | Judgement |
|---|---|
| Title "Draft 7", date 2026-11-18 | Legitimate (successor). |
| "twelve questions in Owner Questions Revision 4" | Legitimate (now Revision 5; wording issue noted in R5-F4). |
| Section 3.3 paragraph 1 and 3.4 paragraph 1 | Legitimate: replaced by the same text plus the existing-GET sentence and the second org-scoped source. |
| Row "Parent cancel operation" | Legitimate: replaced by the same row with "a body expected_revision". |
| Row "Separate demo cancel" (193-205) | Legitimate: range corrected to 193-208. |
| Row "Teacher assignment source" (83-156, "At base 2dd, 83-138 ...") | Legitimate (R4-F3). |
| Blocker 3 and blocker 8 | Legitimate: extended, not narrowed. |
| Lineage paragraph (Draft 7, Rev4, Draft 9, PIN_AUDIT_R5) | Legitimate (successor pointers). |

Nothing silently dropped from Draft 7. Draft 6 facts still absent from Draft 8, judged against the Draft 6 text: (i) the M2 owner disposition at `approvals/TASK_APPROVAL.md` line 3250 that the existing GET lacks the StoryRunDetailV1 timeline (R5-F2, dropped at Draft 7); (ii) Draft 6 bullet "request_id may alias correlation_id" and "semantic domain outcomes use their separately approved mappings" (folded into R5-F1); (iii) the SRS line 500 / UC-07 1469-1475 paraphrases and the NFR-31 retention sentence (covered in substance by blocker 9 and sections 3.2, 3.5; legitimate); (iv) the Draft 6 Core Asset row's mention of object_storage.py and core_store.py (both are H or E rows in the Allowlist; legitimate).

Allowlist Draft 10 vs Draft 9 (changed lines only): title/date; PIN_AUDIT_R5 to R6 plus the local/git-ignored caveat (legitimate); overlap count sentence and three table rows (R4-F5); history sentence "This draft retains that history accurately." removed (R4-F8) and the Draft 10 additions appended; TASK_APPROVAL H row now cites 3243-3247; three H rows added; section 7 DTR bullet widened with the org-scoped AI Jobs cancellation notice; section 8 rewritten (the "two FEAT-066 inline pins remain" sentence removed on purpose, R4-F4); acceptance paragraph points to Contract Draft 8. No row, count or exclusion was removed. 54 Draft 9 rows are all still present with identical bytes/digests (register comparison).

Owner Questions Rev5 vs Rev4: exactly three hunks (authority line, Q-BASE disposition/effect, Q-M2-GATE disposition). No question, quotation or open point removed.

Lost Note Rev5 vs Rev4: section 1 rewritten to name the pin-gate review (adds, restores); section 3 predecessor table added; R3-F2 row now states 88-156 and drops the sentence "The shorter 83-138 range is not the complete helper at this base" (legitimate under R4-F3, but note it rewrites what Rev4 recorded as the R3-F2 fix; the R4-F3 row discloses it); eight R4 rows and the R2 rows added. Compared with Rev3: Rev3 section 2 (open D-208/D-209 eligibility and D-208 item 8 questions) is legitimately superseded by D-214 items 1 and 11; Rev3 section 4 (root-checkout CONV-1 observations, M2-S2 branch bc124187 provenance, owner queue CONV-1, FR-C-08, SEED-1) was already dropped in Rev4 and R4 accepted it; D-214 item 10 settles the base question. I treat that as legitimate and not re-flag it.

Earlier-round fixes re-checked, no regression: section sign U+00A7 present (Contract 4, Allowlist 1, Rev5 4, Lost Note 9 occurrences, no mojibake); zero lines with an odd backtick count in the four documents and the register; no process labels outside the Lost Note revision-history table (the only "R2/R3/R4" hits are in table lines 46-72) and file names; local/git-ignored register caveat present; no table split by a blank line; no Teacher path, migration, schema, new route, DTR or Core reference-closure path editable.

## 6. New findings

### R5-F1 (P3) Contract section 4.1 misplaces D-066-68 and omits a body field it records

- Where: Contract Draft 8 line 84 (section 4.1) and bullet 1 (line 86).
- Evidence: line 84 says "D-066-68 in the FEAT-066 decision record on the local branch (not in the root checkout) fixes these conventions". `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md` has `## D-066-68 - API conventions for the conventions slice CONV-1 (2026-11-18)` at line 382 in the root working tree, in `git show HEAD:` and in `git show 2dddc607:` (identical position). What exists only on the local branch is D-066-71 and the CONV-1 approval entry and evidence (Allowlist line 17, Lost Note line 34 say so correctly). Bullet 1 lists the six top-level fields and says "current_version accompanies STALE_REVISION only", but D-066-68 C-D1 allows two extras (`current_version` and `request_id` equal to `correlation_id`) and `error_envelope.py:230` builds `"request_id": request_id`; Draft 6 recorded "request_id may alias correlation_id".
- Why it matters: a reader following the pointer "(not in the root checkout)" will look on the wrong branch, and the list reads as the complete body when the source carries a seventh field. Same pointer-precision class as R2-F8, R3-F2, R4-F3.
- Minimal fix: say "D-066-68 (present in the root checkout and at the provisional base; D-066-71 and the CONV-1 approval and evidence are only on the local branch)" and add "`request_id`, equal to `correlation_id`" to the bullet.

### R5-F2 (P3) The existing GET's missing StoryRunDetailV1 timeline (M2 owner disposition) is still not recorded

- Where: Contract Draft 8 section 3.3 and row "Parent owner-scoped read" (lines 39, 67).
- Evidence: Contract Draft 6 section 3.3 recorded "The M2 owner disposition at approvals/TASK_APPROVAL.md:3250 records the missing StoryRunDetailV1 timeline as OPEN-OWNER and non-blocking for the bounded M2 client integration decision." At that line the entry reads, for `GET /v1/story-runs/{run_id}`, that the response-content difference (no StoryRunDetailV1 timeline) is recorded OPEN-OWNER and does not block client integration. It was dropped in Draft 7 and is not restored in Draft 8; the R4-F1 list (a to d) did not mention it, so it was not requested. Draft 8 says only that the GET "carries no lifecycle projection".
- Why it matters: D-214 item 5 extends exactly this GET; the SRS contract it must preserve (lines 780, 805, 1164, 1811) is an aggregated StoryRunDetailV1, and the M2 closure already records that the existing response lacks the SRS timeline. This is a source/governance fact relevant to the "compatible response schema remain open" point. Class: dropped fact (rounds 3, 4, 5), but inherited from Draft 7, not a Draft 8 regression.
- Minimal fix: add one sentence to the row or section 3.3: the existing GET also lacks the SRS StoryRunDetailV1 timeline; M2 recorded that as OPEN-OWNER and non-blocking (approvals/TASK_APPROVAL.md line 3250); it does not establish lifecycle evidence.

### R5-F3 (P3) "Map or removal" widens D-214 item 2

- Where: Contract Draft 8 line 29 ("require an explicit compatibility map or removal"); Owner Questions Rev5 line 41 ("explicitly map or remove").
- Evidence: D-214 item 2: "after an explicit compatibility map for the two source-only values SCRIPT_GENERATING and SCRIPT_GENERATION_UNKNOWN that adds no public state". D-214 does not select removal; the "or remove" text comes from the Rev3 option text. Round 4 flagged this in its table but did not raise it as a finding.
- Why it matters: Q-STATES is an owner-decided disposition; adding an option the owner did not select is a fidelity drift (class: overstated wording, R4-F6).
- Minimal fix: write "an explicit compatibility map ... that adds no public state" and, if removal stays relevant, mark it as a later design option, not the disposition.

### R5-F4 (P3) "D-214 records ... the twelve questions in Owner Questions Revision 5"

- Where: Contract Draft 8 line 11.
- Evidence: D-214 states the reviewed documents are Owner Questions Rev3, Contract Draft 6, Allowlist Draft 8 and items 5 and 8 contrast with "the baseline recommendation in Owner Questions Rev3". D-214 predates Rev5 (and Rev4). Rev5 reproduces the twelve dispositions; it is not the document D-214 answered. The wording was inherited from Draft 7 (Revision 4) and passed rounds 4 unflagged.
- Why it matters: minor provenance overstatement in a lineage sentence.
- Minimal fix: "D-214 records owner planning dispositions for twelve questions first asked in Owner Questions Revision 3; Owner Questions Revision 5 restates them."

### R5-F5 (P3, nits)

- Allowlist line 21: "it now lists eight paths" is temporal/process wording ("now") in a record; drop "now".
- Allowlist line 118 (`bounded_image_upload.py` row): "Outside FR-C-08 scope" next to an H classification and line 34's statement that the app.py E row "depends on" the three files. The upload middleware does not obviously support the app.py error/correlation row; say either "frozen reference for the 413 envelope" or "listed only because CONV-1 modifies it".
- Lost Note R3-F2 row (line 56) now reports 88-156 as the R3-F2 disposition, while Rev4 recorded 83-156 for that finding; the R4-F3 row (line 67) discloses the change, so the history is traceable, but the R3-F2 row reads as if 88-156 was the round-3 fix.
- Contract line 119 / Allowlist line 151: the register name (`PIN_AUDIT_R6.md`) is the only place the label "R6" appears; it is a file name and allowed.

## 7. Claims verified clean

- Pins: 57 of 57 Allowlist path pins recompute at 2dddc607 (bytes and SHA-256); every hex token is 64 characters (58 in the Allowlist = 57 rows + the SRS pin; 2 in the Contract; 1 in the Lost Note; none in Rev5); the 8-character abbreviations 2dddc607 and 08439b22 and the two 40-character commit IDs all resolve to the right commits. E 22 (20 source + 2 tests), D 6, H 29 equal the counts stated in the Allowlist (line 151), Lost Note, register. The register's 57 base-pin rows equal the Allowlist rows (path, bytes, digest, class); its 109 required-input and predecessor rows recompute at the working tree with zero mismatch.
- CONV-1 overlaps: the 36 changed paths intersected with the 57 pinned paths give exactly the 8 in Allowlist lines 25-32 (app.py, test_openapi_contract_catalog.py as E; openapi_contract_amendments.py, be1_common.py, be1_registry.py, api_conventions.py, error_envelope.py, bounded_image_upload.py as H). No D path overlaps. D-214 item 10's own five-path overlap list is a subset.
- N paths: 9 of 9 absent at 2dddc607, HEAD and the working tree. No migration, schema, route, DTR or Core reference-closure path appears in any table; the Teacher-related rows (lesson_library/service.py, be1_parent_role_adapter.py, the Spec Draft 4) are H.
- Quotations: all 31 blockquotes in Rev5 (SRS lines 270, 383, 394, 667, 668, 771, 780, 805, 1164, 1469, 1470, 1473, 1475, 1518, 1523, 1674, 1676, 1797, 1811, 2144, 2146, 2339, 2341, 2758, 2996; some repeated) equal the SRS line exactly (script; only the SRS CRLF differs). Line 1164 still ends "§9.5-§9.7; §22.4; NFR-05/10 \|". SRS lines cited in the Contract (394, 667-668, 780, 805, 1164, 1470, 1518, 1523, 1674, 1697, 1811) resolve; line 1697 is the idempotency sentence in section 21.4 (heading at 1695), 1674 lies in section 21.2 (heading 1643). The 13 listed states equal SRS 394 minus the five of 1518, in SRS order.
- Governance quotes: D-200 (DECISIONS line 527) selects HTTP 400 for the changed-payload case and says the SRS gives no status; D-212/D-213 at lines 539-540; TASK_APPROVAL 3243-3247 and STATUS 876/873 as above; D-066-71 at line 434 and the CONV-1 approval at line 393 of the FEAT-066 records on 2dddc607 (0 hits for D-066-71 in the root copy).
- Source facts at 2dddc607: cancel route `parent_story_runs.py:253-294` (202, header, `purge_state="PENDING"` at 276-283); `router_composition.py:60-76`; `app.py:1057-1064` and `1057-1060`; accepted state set `parent_story_repository.py:385-394` (7 literals; 5 in the 13, 2 source-only; 8 rejected); response literal `parent_story_runs.py (schemas):110-117` omits ABANDONED and DELETED; `DataLifecycleRequestModel.organization_id` non-nullable (`be1_models.py:568`, class 555-578); `be1_models.py:63-90` has no version column; `core_foundation.py:181-186` (`CoreAssetMetadataPort`: save/get only); `ai_jobs.py` service `545-583`; `story_run_lite.py:193-208`.
- Hygiene (Python byte checks on all five files): UTF-8, no BOM, no CR, no tab, no trailing whitespace, no dollar sign, single final newline, no local absolute path, no Vietnamese outside blockquotes, non-ASCII limited to U+00A7, en/em dash and, in the SRS quotation, an arrow; no unbalanced backticks; no blank line inside a table; table header always preceded by a blank line; no process labels as prose.
- Overclaiming: all documents say DRAFT / NOT APPROVED / NOT LAUNCHED; no document claims approval, launch, closure, proof or a command ceiling; the register is described as local and git-ignored; nothing says CONV-1 is absent.
- Existing records unchanged: every predecessor row of the register recomputes; `git diff --cached` is empty; the only modified tracked file is DECISIONS.md (D-214, expected).

## 8. Not verified, and why

- Observation O-1 (not a finding against the documents): `feature/feat066-conv1` now resolves to 03342207 (commit of 2026-11-19 00:27 +0700, "docs(FEAT-066): Phase B/C packages, reviews and decisions D-066-72 to D-066-77"), whose parent is 2dddc607. It changes 34 paths, all under `features/FEAT-066-fe-ui-srs-full-review/`; no backend path and none of the 57 pinned paths changed, so the pins and the 8 overlaps stand. The documents say "local branch ... at commit 2dddc607" and "provisional"; D-214 item 10 says "2dddc607 or later" and names the exact commit later, so this is consistent, but the brief's preflight ("tip is 2dddc607") is no longer literally true. The coordinator should know before any later "tip of the branch" statement is relied on, and the exact base commit still has to be named.
- Runtime, database, migration, generated OpenAPI, object-store and provider behavior: out of scope; the documents label them NOT VERIFIED.
- Content of CONV-1 beyond the changed-path list, the pinned base blobs and the lines read (`api_conventions.py`, `error_envelope.py`, `bounded_image_upload.py` diff, the CONV-1 decision/approval/evidence existence). I did not review whether CONV-1 changes Parent cancel error bodies.
- Whether 2dddc607 (or 03342207) is the right base, whether CONV-1 is confirmed, the owner queue, and whether the E candidates are the right files for a Parent-only slice: owner matters, not re-litigated.
- `git diff --check` on the new untracked files: not run; equivalent byte checks were done in Python.
- The effort level actually applied to this review (section 1).
