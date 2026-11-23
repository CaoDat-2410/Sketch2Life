# FR-C-08 wave 1 - independent cold review, round 4 (2026-11-19)

Record only. This note decides nothing for the owner and approves nothing. It is a new file; no existing record was edited. Below the coordinator addendum, the reviewer's report is reproduced as written (local path mentions reworded or shortened to repository-relative paths).

## 0. Coordinator addendum

- Started by the coordinating Claude session with the model set explicitly to Sonnet 5.5 and the effort parameter set explicitly to "high" in the start call. As in rounds 1 to 3, the reviewer cannot confirm from inside its session that "high" was applied, and the coordinator cannot verify it. This caveat must not be dropped when this note is cited.
- Reviewed pins: Contract Draft 7 (13,622 B, C43A761D649A4D520823972512C54A02A003715EC2A98291A30A2FF76F347BAD), Allowlist Draft 9 (20,981 B, EE19446E0B562479ACB5B67E75B2F91FB05280DA1EAFFE901F325ADD00826DC7), Owner Questions Rev4 (21,828 B, AD45CA0BDAF4902FC93011F4593BA10F19D3CA890BD26C567A1FE6EF7C47C90F), Lost Drafts Note Rev4 (5,546 B, 8F11D7C466CCDB67041943ACB549238DD835066848BAB850D401FB24A36A5D52), the local pin audit register (42,457 B, EB72E7AFCBE69D1B88ABCD8A0B2D2F29FF12CDDC2B3AE23B795FFE37D6DDFC4D), DECISIONS.md with D-214 (240,776 B, 6E30C69B5E43C2124B9083B6904FEEAE80D7BCEE0917C635F381BA518D32C723) and the canonical SRS (701,157 B, B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5).
- Result: READY WITH NOTES, P1 = 0, P2 = 0, P3 = 8. P1 + P2 by round: 5, 1, 0, 0. No P1 or P2 finding in rounds 3 and 4. Repeating classes are P3 only (citation precision, dangling pointers); a new P3 class appears: facts or blockers dropped by the rewrite (R4-F1, R4-F2, R4-F7).
- The reviewer confirmed that the D-214 row is an append-only last row and that all twelve dispositions are carried into the documents without re-decision; R4-F2 and R4-F6 note two gaps in that carry-over.

---

Read-only review. Nothing in the repository was edited, created, staged or committed. The only file written is this report; scratch scripts (hyg.py, quotes.py, pins.py) are under tmp/frc08-wave1-r4review/. No test, validator, database, Docker, network or provider command was run. No network git command was used. The gate-secrets folder and .worktrees were not opened (CONV-1 content was read only through `git show 2dddc607:<path>` and `git diff --name-only 08439b22 2dddc607`).

## 1. Header

- Round 4 of at most 5. Date 2026-11-19.
- Reviewer: subagent, model Sonnet 5.5 (`claude-sonnet-5-5`, as reported by my environment). Effort: the caller asked for the high setting. Caveat, same as earlier rounds: I cannot see an effort label inside my session, so I cannot confirm that "high" was applied.
- Method: all 31 verbatim SRS blockquotes in Owner Questions Rev4 compared by script (UTF-8, exact string equality) against the SRS line they cite; every SRS line number cited in the four documents resolved against the SRS; all 54 path/bytes/SHA-256 pins in Allowlist Draft 9 recomputed with `git show 2dddc607:<path>` (and compared with HEAD); 9 N paths checked absent at base, HEAD and the working tree; the 5 CONV-1 overlaps recomputed from `git diff --name-only 08439b22 2dddc607` (36 paths; 17 added, 19 modified); all 98 predecessor rows and 54 base-pin rows of PIN_AUDIT_R5 recomputed; hygiene by Python byte checks; every source line range read at the commit the documents name; D-214 compared to the documents item by item.

Pins verified before review (bytes and SHA-256 all match the brief):

| File | Bytes | SHA-256 (first 8) |
|---|---:|---|
| plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT7_20261118.md | 13,622 | C43A761D |
| plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT9_20261118.md | 20,981 | EE19446E |
| plan/FR_C08_OWNER_QUESTIONS_REV4_20261118.md | 21,828 | AD45CA0B |
| plan/FR_C08_LOST_DRAFTS_NOTE_REV4_20261118.md | 5,546 | 8F11D7C4 |
| tmp/frc08-wave1/PIN_AUDIT_R5.md | 42,457 | EB72E7AF |
| DECISIONS.md (working tree, D-214) | 240,776 | 6E30C69B |
| evidence/FR_C08_WAVE1_COLD_REVIEW_R3_20261118.md | 25,001 | 2EC0176A |
| artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md | 701,157 | B9B1F42D |
| .claude/handoff/CODEX_FRC08_WAVE1_R5_PROMPT_20261118.md | 11,311 | A0BC09ED (matches the audit) |

HEAD is 08439b22fc3c1f34786a3f45f34530075a3914e0. `git diff --numstat HEAD -- DECISIONS.md` gives 1 insertion, 0 deletions (D-214 is the last table row, append-only). `git diff --cached` is empty. The local branch feature/feat066-conv1 resolves to 2dddc6076c793b44cbcd5c0fa3e02a4ccc9902df with the single parent 08439b22.

## 2. Verdict: READY WITH NOTES - P1 = 0, P2 = 0, P3 = 8

P1 + P2 went 5 (round 1), 1 (round 2), 0 (round 3), 0 (round 4): the count did not rise, so the stop rule does not trigger on count.

What is sound: all 54 Allowlist pins recompute exactly at 2dddc607; all 31 SRS quotations are exact (the only difference is the SRS file's CRLF line ending, which is not part of a quotation); the section sign is restored everywhere; no odd backtick counts; five CONV-1 overlaps are listed correctly; all 12 D-214 dispositions are carried into Owner Questions Rev4 without re-decision, Q-OWNERS stays open; no Teacher path, migration, schema, new route, DTR file or Core reference-closure path is in the allowlist as editable; nothing claims approval, launch or closure; no command ceiling is approved.

Findings that repeat from earlier rounds (P3 only): citation or line-range precision (R2-F8, R3-F2 class; now R4-F3); dangling or stale pointer (R1-F6, R3-F10 class; now R4-F4). One new class appears and is the most useful to fix: facts or blockers silently dropped by the rewrite (R4-F1, R4-F2, R4-F7), the same kind of rewrite regression as R3-F1.

## 3. R3-F1 to R3-F10 disposition (judged independently)

| ID | Status | Evidence |
|---|---|---|
| R3-F1 section sign backtick | FIXED | Owner Questions Rev4 line 102 equals SRS line 1164 exactly and ends "§9.5–§9.7; §22.4; NFR-05/10 \|" (script; all 31 blockquotes EQUAL after ignoring the SRS CRLF). Section signs are real U+00A7: Contract 3, Allowlist 1, Rev4 4, Lost Note 4. Zero lines with an odd backtick count in the four documents and the register. |
| R3-F2 source ranges | PARTIAL | Correct at base: `be1_models.py:555-578` (class 555, last field 578), `be1_registry.py:107-125` (decorator 107, return dict ends 126; function 108-126, so 125 stops one short of the closing brace, acceptable), `be1_models.py:63-90`. But `be1_common.py:83-156` (Contract row "Teacher assignment source", Lost Note history row): at base `def require_assignment` starts at line 88 and ends at 156 (line 83 is a blank line and 84-85 is `_out_of_scope`; 83 is the HEAD start line). The sentence "At base 2dd, lines 83-138 alone do not include the end of the helper" is cryptic and uses an abbreviation. See R4-F3. |
| R3-F3 Draft 6/7/8 history | FIXED | Allowlist 31, Lost Note 38 and audit "Reconciliation notes" say Draft 6 listed four paths as E, Draft 7 moved them to H, Draft 8 kept them H and added four H references. Confirmed: Allowlist Draft 6 lines 30, 37-39 are in its section 2 "E"; Draft 7 lines 123-134 list them as H. |
| R3-F4 table split / unclosed backtick | FIXED | No blank line between table rows in any of the four documents (scripted); no odd backtick lines. Residual nit: Contract line 59 (paragraph) is directly followed by the table header on line 60 with no blank line (R4-F8). |
| R3-F5 five overlaps | FIXED | Allowlist 23-29 lists app.py and test_openapi_contract_catalog.py (E), openapi_contract_amendments.py, be1_common.py, be1_registry.py (H). My intersection of the 54 pinned paths with the 36 CONV-1 paths is exactly these five. Pin rows for these five differ between HEAD and base (as expected) and the pins are the base blobs. |
| R3-F6 process wording / CONV-1 record | FIXED | The "stale unreviewed-draft label" clause is gone. Allowlist line 17 states D-066-71, the approval entry and the implementation evidence are recorded at 2dddc607. I confirmed: `git show 2dddc607:features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md` has D-066-71 (heading line 434), TASK_APPROVAL.md has "FEAT-066 CONV-1 - API conventions core (BE)" (line 393), evidence note CONV_1_IMPLEMENTATION_EVIDENCE exists; root DECISIONS.md has 0 hits for D-066-71. Re-pin after the base is named: line 13. |
| R3-F7 400 provenance | FIXED | Contract row "Idempotency behavior": SRS 21.4 requires the code (SRS line 1697 gives code only, no status); D-200 (DECISIONS.md line 527) selects HTTP 400; source raises `ParentStoryRunError(400, "INVALID_IDEMPOTENCY_KEY")` at `parent_story_repository.py:369` (range 360-374 encloses it). |
| R3-F8 demo cancel route | FIXED | Contract row "Separate demo cancel" and Allowlist H row 112 (story_run_lite.py, pin recomputes) classify it as H / separate demo profile. Source: `@router.post("/story-runs/{run_ref}/cancel")` at `story_run_lite.py:193`; mounted at `app.py:1059-1060` only when the demo flag is on (base). Range 193-205 truncates the handler (it ends at 208), trivial (R4-F8). |
| R3-F9 audit completeness | FIXED | PIN_AUDIT_R5 has the two formerly missing paths (openapi_contract.py 1,379,096 B; M2_S2_IMPLEMENTATION_REPORT_20261114.md 25,879 B) among 54 base-pin rows (E 22, D 6, H 26; E = 20 source + 2 tests), 9 absent N paths, 5 overlaps. I recomputed 98 of 98 predecessor rows (97 unchanged + DECISIONS.md expected D-214 change) and 54 of 54 base-pin rows: zero mismatch. Counts equal the Allowlist (54 = 58 table pins - 7 migrations - 1 response schema + 1 demo router + 3 formerly inline tests). |
| R3-F10 audit caveat in Lost Note | FIXED | Lost Note section 4 says the register is local, git-ignored, not a durable repository record; Contract line 103 repeats it. The Allowlist points to PIN_AUDIT_R5.md at line 15 ("separately pinned in PIN_AUDIT_R5.md") and line 143 without the local/git-ignored caveat; the D-214 bytes are also given durably in Contract line 13 and Lost Note line 20, so nothing depends on it (R4-F8). |

## 4. D-214 fidelity (12 dispositions)

The D-214 row itself: append-only (1 insertion, 0 deletions); SRS line numbers it cites resolve correctly (270, 394, 667-668, 1469, 1470, 1473, 1475, 1518, 1523, 1674, 1676, 1797, 2144, 2146, 2339, 2341, 2758, 2996; 1496 is the UC-09 main flow naming the lifecycle request); TASK_APPROVAL 3243-3247 is the M2-S3 ACCEPTED / M2 CLOSED entry; STATUS.md line 876 is the "M2-S3 ACCEPTED; M2 CLOSED" entry (line 873 is the stale "NOT closed" text); reviewed-document pins and review-note pins in the D-214 row equal the files; "DECISIONS.md before append 233,645 B / 7EA82DB5..." equals the base blob.

| # | Item | Owner Questions Rev4 | Contract Draft 7 | Allowlist Draft 9 | Verdict |
|---|---|---|---|---|---|
| 1 | Q-A: option B, DELETE for COMPLETED/FAILED/ABANDONED; no auto purge; separate SRS wording revision | Faithful (lines 25-28) | Faithful (3.2, blocker 1) | Line 139 gate | OK |
| 2 | Q-STATES: option A, 13 states, compatibility map for the two source-only values, response-schema decision | Faithful (lines 41-44) | Faithful (3.1; 13 states listed and recounted equal SRS 394 minus 1518) | Line 138 open item; response schema path excluded | OK (note: "map or removal" comes from Rev3 option A text, D-214 text says "compatibility map" only) |
| 3 | Q-PARENT: option B, DTR/schema delta, never fabricate organization_id | Faithful | Faithful (3.4); source fact DataLifecycleRequestModel organization_id non-null confirmed at base 555-578 | Line 135 exclusion; DTR not in any table | OK |
| 4 | Q-TEACHER: option C, Parent-only first scope, shared design, adapter deferred, scope limit | Faithful (lines 85-88) | Faithful (section 2, 3.5) | No Teacher route/resolver/path; lesson_library/service.py moved E to H; line 137 | OK |
| 5 | Q-READ: option A, extend existing GET only, no second route, DELETED never from access denial | Faithful (lines 107-110) | Faithful (3.3, blocker 5) | No route; schema excluded | OK. The existing GET exists in source (`parent_story_runs.py:232-250`, ParentStoryRunEnvelopeV1) but Contract Draft 7 does not record that source fact (minor, within R4-F1) |
| 6 | Q-FENCE: option A, shared version/fence, provider cancel best-effort and not purge proof | Faithful; "not purge proof" is in Contract only | Faithful (3.5) | Worker/playback rows guarded | OK |
| 7 | Q-PURGE: option A; Core contracts missing = blocker; keep shared asset | Faithful | Faithful (3.5, blocker 4) | Line 136 blocker; no Core path invented (core_foundation.py, core_store.py, core_models.py are H read-only) | OK |
| 8 | Q-WORKFLOW: option B narrowed to DTR delta over SRS line 1523 tables | Faithful | Faithful (3.4) | Line 135 | OK |
| 9 | Q-AUDIT: option A; 180/365 map stays OPEN-TECHNICAL | Faithful | Faithful (3.5, blocker 3) | Line 135 | OK |
| 10 | Q-BASE: option B; tip of local never-pushed feature/feat066-conv1, 2dddc607 or later, parent 08439b22, after owner confirms CONV-1; shared paths re-pinned; exact commit named later; five overlaps | Mostly faithful; omits "never-pushed" and "after the owner confirms CONV-1" in the disposition line and says "later owner-confirmed commit" (D-214 says "or later") (R4-F6) | Provisional base, blocker 6 | Lines 13, 17, 23-29: faithful; says D-214 requires owner confirmation; says "provisional" | OK with R4-F6 |
| 11 | Q-M2-GATE: option A; M2 closure at TASK_APPROVAL 3243-3247 and STATUS 876 satisfies D-208 item 8; nothing transfers | Carried without the two citations (lines 202-205) | Not carried at all (no mention of M2 closure or non-transfer) | Section 9 "No M2 command ceiling transfers"; H rows | PARTIAL: R4-F2 |
| 12 | Q-OWNERS: option A selected, names and record location missing, launch blocked | OPEN (line 222) | Blocker 7 | Line 139 | OK |

No re-decision, no contradiction of D-214 found. D-214 item 13 (the "not yet fixed" status of the round-3 notes) is correctly not copied as a current claim.

## 5. New findings

### R4-F1 (P3) Contract Draft 7 silently drops Draft 6 source facts that still apply at the new base

- Where: Contract Draft 7 section 4 (lines 59-73) versus Draft 6 section 4 (lines 48-62) and section 5 (lines 64-75).
- Evidence (all verified at 2dddc607):
  - (a) Draft 6 said the existing AI Jobs cancellation notice is organization-scoped. Draft 7 row "AI Jobs cancellation" omits it. `application/ports/ai_jobs.py:249-257` defines `CancellationNotice` with a non-optional `organization_id`; the SRS line 1523 table list the Parent-only DTR delta must start from includes `ai_jobs.cancellation_notice`. A Parent has no organization, so this is a second place (besides `DataLifecycleRequestModel`) where Parent scope cannot be represented.
  - (b) Draft 6 flagged that the route's 1-256 Idempotency-Key limit differs from the convention (1-128 visible ASCII) and needed a separate resolution. At the chosen base this is sharper: the CONV-1 file `interfaces/http/api_conventions.py:67` enforces `1 <= len(value) <= 128`, while `routers/parent_story_runs.py` still declares `max_length=256` on 5 routes. Draft 7 row "Parent cancel operation" states 1-256 without the mismatch; blocker 8 only says "exact error and idempotency transport" in general terms.
  - (c) Draft 6 row "Cancel persistence" (what the M2 cancel repository does: replay, fingerprint check, revision check, DELETE_PENDING, lock release, receipt; "does not prove an integrated lifecycle request, notice, or purge receipt") is gone; so is the Draft 6 transport-convention list (body error fields, uniform 404, 409 STALE_REVISION with current version, body `expected_revision`).
  - (d) The existence of the owner-scoped GET (`parent_story_runs.py:232-250`) that D-214 item 5 extends is not stated as a source fact.
- Why it matters: the brief said "Keep every verified source fact; drop or mark superseded anything D-214 resolves". D-214 resolves none of (a)-(d). The facts are partly covered by blockers 3 and 8, so this does not block use; it is P3.
- Minimal fix: restore rows for (a), (b), (c) and (d) in section 4, and cite the base lines above.

### R4-F2 (P3) D-214 item 11 (M2 closure gate) is not carried into Contract Draft 7; Rev4 and the Lost Note omit its citations

- Where: Contract Draft 7 (no mention of M2 closure or non-transfer); Owner Questions Rev4 Q-M2-GATE (lines 202-205); Lost Note Rev4 section 3.
- Evidence: D-214 item 11 cites approvals/TASK_APPROVAL.md lines 3243-3247 and status/STATUS.md line 876 (I confirmed both). None of the four documents cites those lines (Allowlist row 91 only says "Contains M2 closure"). `grep` of Contract Draft 7 for "closure", "3243", "876", "transfer" finds only Core reference-closure text. Draft 6 section 2 and Lost Note Rev3 section 4 carried these citations and the "line 873 is a stale snapshot" warning.
- Why it matters: the brief asks that each of the 12 dispositions be carried; this one is carried in two of three documents and without its evidence pointers.
- Minimal fix: add one Contract sentence (D-214 item 11; M2 approvals, allowlists and command ceilings do not transfer; cite the two line ranges) and cite the lines in Q-M2-GATE.

### R4-F3 (P3) be1_common.py range is a HEAD/base hybrid; the explanatory sentence is cryptic (R3-F2 residual)

- Where: Contract section 4 row "Teacher assignment source"; Lost Note history row R3-F2; audit reconciliation note.
- Evidence: at 2dddc607 `def require_assignment` is at line 88 and the function ends at line 156 (`return tuple(row for row in rows if row.assignment_id in allowed_ids)`). The cited start 83 is the HEAD line; 83-87 at base is a blank line and `_out_of_scope`. The text "At base 2dd, lines 83-138 alone do not include the end of the helper" uses an unexplained abbreviation and compares against a range the document does not otherwise cite.
- Why it matters: the brief asked for each range to be re-checked at the base; the result is a range that encloses the helper but is not the helper. Same class as R2-F8 and R3-F2.
- Minimal fix: cite `be1_common.py:88-156` and drop the 83-138 sentence.

### R4-F4 (P3) Allowlist line 143 says two FEAT-066 pins "remain" but Draft 9 contains none

- Where: Allowlist Draft 9 section 8 (line 143).
- Evidence: "The two FEAT-066 inline pins remain separate coordination references, not allowlist paths." Draft 8 line 11 carried the two root-checkout FEAT-066 pins (DECISIONS.md 51,184 B C9375780..., TASK_APPROVAL.md 41,171 B E202446E...). A search of Draft 9 for "FEAT-066", "C9375780" and "E202446E" finds only this sentence. Those two files are in the 36-path CONV-1 change set, so the root pins no longer describe the base.
- Why it matters: a dangling reference (R1-F6 and R3-F10 class); a reader cannot find the pins the sentence says remain.
- Minimal fix: say "Draft 8's two root-checkout FEAT-066 pins are not carried because both files are changed by CONV-1".

### R4-F5 (P3) CONV-1 files that exist only at the base are not classified

- Where: Allowlist sections 2 to 6.
- Evidence: `git diff --name-status 08439b22 2dddc607` adds `interfaces/http/api_conventions.py` and `interfaces/http/error_envelope.py` (and modifies `middleware/bounded_image_upload.py`, `openapi_contract_amendments.py`). They exist at base and not at HEAD. The E row for `app.py` ("Apply approved error/correlation behavior only") and Contract blocker 8 (error and idempotency transport) depend on the first two, yet neither is an H reference or mentioned as out of scope. The overlap table correctly lists only paths that are in this allowlist.
- Why it matters: the brief asked that paths that exist at one commit and not the other be handled. All 54 pinned paths exist at both commits, and no N path is present at either, so nothing is wrong today; the dependency is just not recorded.
- Minimal fix: add the two files as H references (with base pins) or state that they are intentionally outside the allowlist.

### R4-F6 (P3) Owner Questions Rev4 overstates two things

- Where: Rev4 line 4 and Q-BASE (line 188).
- Evidence: line 4 says the authority is the D-209 SRS "as amended by the D-214 planning dispositions where consistent with that SRS". D-214 does not amend the SRS; it directs a separate documentation-only SRS revision (D-214 item 1; Rev4 line 226 says the SRS remains unsigned). Q-BASE disposition says "Use the tip of local feature/feat066-conv1 at 2dddc607 or a later owner-confirmed commit"; D-214 item 10 says "the local, never-pushed branch ... (commit 2dddc607 or later, parent 08439b22), after the owner confirms CONV-1". "Never-pushed" and "after the owner confirms CONV-1" are not in the disposition line, and "owner-confirmed" for a later commit is not in D-214 (the exact commit is "named when the base is fixed").
- Why it matters: the brief says Q-BASE wording must match D-214 item 10.
- Minimal fix: replace "as amended by" with "read together with"; copy the item 10 wording into the Q-BASE disposition.

### R4-F7 (P3) Lost Note Rev4 pared the lineage record

- Where: Lost Note Rev4 sections 1 and 5 versus Rev3 sections 1, 3, 4 and its revision-history table.
- Evidence: Rev4 line 10 refers to "the surviving historical pin-gate review" and no longer names evidence/FR_C08_DRAFT3_DRAFT5_COLD_REVIEW_20261116.md (it exists and its "Invalid/mismatching pins" register is at its line 36), so the statement cannot be traced. The Rev3 surviving-predecessor table (Spec Draft 4 and Plan Draft 4 read the D-208 eligibility; Contract Draft 2 and Allowlist Draft 4) and the R2-F1..R2-F9 history rows are gone; the brief said to add the new revision-history row to Rev3 and keep lineage statements correct, not replace the table.
- Why it matters: lineage statements that remain are correct, but the record no longer shows why Spec Draft 4 is historical or what Rev3 changed.
- Minimal fix: name the pin-gate review file, restore the predecessor table and the earlier history rows, then append the new rows.

### R4-F8 (P3) Small formatting and wording nits

- Contract line 59 (paragraph) runs directly into the table header on line 60 with no blank line; some renderers will not treat line 60 as a table.
- Allowlist line 31: "This draft retains that history accurately." is self-referential process wording; delete it.
- Contract and Allowlist cite `story_run_lite.py:193-205`; the handler spans 193-208.
- Allowlist lines 15 and 143 name PIN_AUDIT_R5.md without saying it is local and git-ignored (the Contract and Lost Note do).

## 6. Claims verified clean

- Pins: 54 of 54 Allowlist path pins recompute at 2dddc607 (E 22, D 6, H 26); every hex token is 64 characters; the only 40-character tokens are the two commit IDs, both valid; 8-character abbreviations resolve to the same commits. E/D/H classes match PIN_AUDIT_R5. Every CONV-1-changed overlap is flagged and its pin is the base blob. Provisional-pin wording is present (Allowlist 13, 35, 153; Contract 13, blocker 6).
- N paths: 9 of 9 absent at 2dddc607, HEAD and the working tree. Migrations (7 in Draft 8), the response-schema path and the three formerly inline tests are accounted for; no migration, schema, route, DTR or Core reference-closure path appears in any table.
- Quotations: 31 SRS blockquote blocks in Rev4 are exact (cited lines 270, 383, 394, 667, 668, 771, 780, 805, 1164, 1469, 1470, 1473, 1475, 1518, 1523, 1674, 1676, 1797, 1811, 2144, 2146, 2339, 2341, 2758, 2996). Cited line numbers in the Contract resolve (394, 667-668, 780, 805, 1164, 1470, 1518, 1523, 1674, 1697, 1811). D-200 (DECISIONS.md line 527), D-212/D-213 (539-540), D-208 items, TASK_APPROVAL 3243-3247 and STATUS 876 agree with what the documents say.
- Source facts at 2dddc607: Parent cancel route `parent_story_runs.py:253-294`, 202, header 1-256, `purge_state="PENDING"` literal at 276-283; composition `router_composition.py:60-76` and `app.py:1057-1064`; accepted state set `parent_story_repository.py:385-394` (7 literals; 5 inside the 13, 2 source-only; 8 SRS-eligible rejected); response literal `contracts/schemas/parent_story_runs.py:110-117` omits ABANDONED and DELETED; `DataLifecycleRequestModel.organization_id` non-nullable (555-578); assignment model has no version column (63-90); `CoreAssetMetadataPort` save/get only (181-186); `apply_cancellation_notice` at `services/ai_jobs.py:545-583`; demo cancel route in `story_run_lite.py:193`.
- State counts: SRS line 394 has 18 states; excluding the five of line 1518 leaves 13 and the 13 listed in Contract 3.1 are exactly those, in SRS order.
- Hygiene (Python byte checks, four documents and the register): UTF-8, no BOM, no CR, no tab, no dollar sign, no trailing whitespace, single final newline, no local absolute path, no Vietnamese outside blockquotes, no process labels (R-numbers) outside file names and the Lost Note revision-history table. Non-ASCII outside quotes is only em dash, en dash and the section sign.
- Overclaiming: Contract and Allowlist carry DRAFT / NOT APPROVED / NOT LAUNCHED; no document claims approval, launch, closure or proof; none says CONV-1 is absent or unapproved (the Allowlist and Lost Note state the CONV-1 records exist on 2dddc607, which I confirmed); no command ceiling is approved; the audit register is described as local and git-ignored in the Contract and Lost Note.
- Allowlist history sentence about Draft 8 to Draft 9 (58 + 3 inline pins to 54) is arithmetically correct and matches a set comparison of the two files.
- Existing records unchanged: all 98 predecessor register rows (including Rev3, Draft 6, Draft 8, round-2 and round-3 reviews, SRS) recompute as stated; `git diff --cached` is empty; the only modified tracked file is DECISIONS.md.

## 7. Not verified, and why

- Runtime, database, migration, generated OpenAPI, object-store and provider behavior: out of scope; the documents label them NOT VERIFIED.
- Content of CONV-1 at 2dddc607 beyond the changed-path list, the five overlap files' pins and the few lines read (`be1_common.py`, `api_conventions.py:59-68`, the CONV-1 decision/approval/evidence existence). I did not review whether CONV-1 changes cancel error bodies.
- Whether 2dddc607 is the right base, whether CONV-1 is confirmed, and the owner's queue: owner matters.
- Whether the E candidates (for example story_video.py, a /v1/sessions router) are the right files for a Parent-only slice: carried over from earlier rounds and not re-litigated.
- `git diff --check`: not run on the new untracked files; equivalent byte checks were done in Python.
- The effort level actually applied to this review (section 1).
