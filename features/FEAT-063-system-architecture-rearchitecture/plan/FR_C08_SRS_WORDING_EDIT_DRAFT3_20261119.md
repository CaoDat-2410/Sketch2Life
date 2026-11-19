# FR-C-08 SRS wording edit — final text, Draft 3

**Status: FINAL TEXT FOR APPLICATION (program task B4).** Date: 2026-11-19.
**Review:** independent review round 1 (Sonnet 5.5, high effort, separate session) READY WITH
NOTES, 0 P1 / 0 P2 / 5 P3; it reproduced every value of §5. Its five P3 notes (F-1 to F-5) are
applied to the prose of this draft and of Contract Draft 12 without a further review; no edit
string of §3 changed after the review.
**Purpose:** the documentation-only SRS revision required by D-214 item 1 and scheduled by
D-216 item 6, in the exact bytes that are applied to the canonical SRS. Draft 2 is not edited.

**Change from Draft 2:** applies the six P3 notes of cold review round 2
(`tmp/frc08-srs-edit/review-r2/FR_C08_SRS_WORDING_EDIT_COLD_REVIEW_R2_20261119.md`, READY WITH
NOTES, 0 P1 / 0 P2 / 6 P3) only where the meaning stays inside D-214 item 1 and D-216 item 4.
Three replacement strings change (E1, E2, E13); R2 is kept. §4 gives the disposition of each
note. Every other edit is byte-identical to Draft 2.

## 1. Pins

| Input | Pin |
|---|---|
| Canonical SRS before the edit (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`; UTF-8; 3,427 LF-terminated lines (3,428 parts when split on LF, the last one empty); 3,362 CRLF and 65 bare LF endings |
| Draft 2 (owner-approved edit set) | `plan/FR_C08_SRS_WORDING_EDIT_DRAFT2_20261119.md`, 7,643 bytes, SHA-256 `7525479D5E49CA398E76F767D4D86B98597B306ED32F8C2C90686C9F64457F53` |
| Cold review round 2 of Draft 2 | local working note under `tmp/frc08-srs-edit/review-r2/`, 17,269 bytes, SHA-256 `CD7B4DACF227CB603D514389A561512879C6EA81245C4448E3DB82F51EA37DF7` |
| Decisions written into the SRS | D-214 item 1 (user DELETE for COMPLETED, FAILED and ABANDONED; FAILED and ABANDONED never purged automatically); D-216 item 4 (two documented extension states, kept in the response and stored values, cancel eligible) |
| Site list | D-216 item 6 (lines 270, 284, 500, 1465, 1470, 1622, 1674, 1707, 1798), plus R1-R3 and E13 by the owner's choice; lines 1037 and 1845 mention cancel only and need no change |

## 2. Rules for applying the edit

1. Each edit changes only the quoted phrase, and only on the cited line; the phrase occurs
   exactly once on that line. Never apply an edit as a file-wide replace: the phrase of E9
   (`xóa run đã hoàn tất`) also occurs on lines 270, 500 and 1465, which other edits change.
2. The fourteen edits touch thirteen lines (E1 and E2 are both on line 270 and do not overlap;
   they are applied right to left). All thirteen lines end in CRLF; endings stay as they are.
3. The header and the "Kiểm soát tài liệu" table (lines 1-39) are not touched, so no line moves
   and every SRS line citation in D-208 to D-218, the Contract, the DTR and the port design stays
   valid. The revision is recorded in `DECISIONS.md` and the re-pin records instead.
4. State names are written in the SRS's own form (`COMPLETED`, `FAILED`, `ABANDONED`).
5. Numbering: E1-E10 are the delete-eligibility sites, R1-R3 the retention sites, E13 the
   state-inventory note. E11 and E12 are not used; the numbers are kept from Draft 2 so the
   owner's approval and the reviews refer to the same labels.

## 3. Edits (exact strings)

| # | Line | Current phrase (exact) | Replacement (exact) |
|---|---|---|---|
| E1 | 270 (BR-26) | `Khi người dùng xóa run đã hoàn tất hoặc hủy run chưa hoàn tất,` | `Khi người dùng xóa run ở COMPLETED, FAILED hoặc ABANDONED, hoặc hủy run chưa hoàn tất,` |
| E2 | 270 (BR-26) | `chỉ giữ audit metadata tối thiểu.` | `chỉ giữ audit metadata tối thiểu. Run FAILED hoặc ABANDONED không bị purge tự động; nội dung được giữ đến khi người lớn có quyền yêu cầu xóa.` |
| E3 | 284 (BR-40) | `xóa run hoàn tất xóa linked media/content.` | `xóa run ở COMPLETED, FAILED hoặc ABANDONED xóa linked media/content.` |
| E4 | 500 (FR-C-08) | `hoặc xóa run đã hoàn tất qua lifecycle.` | `hoặc xóa run ở COMPLETED, FAILED hoặc ABANDONED qua lifecycle.` |
| E5 | 1465 (UC-07 heading) | `### UC-07 — Người lớn xóa run đã hoàn tất` | `### UC-07 — Người lớn xóa run ở COMPLETED, FAILED hoặc ABANDONED` |
| E6 | 1470 (UC-07 precondition) | `Run đã hoàn tất; caller có quyền; run chưa trong quá trình xóa` | `Run ở COMPLETED, FAILED hoặc ABANDONED; caller có quyền; run chưa trong quá trình xóa` |
| E7 | 1622 (permission matrix) | `Xóa nội dung run đã hoàn tất` | `Xóa nội dung run ở COMPLETED, FAILED hoặc ABANDONED` |
| E8 | 1674 (API table, DELETE) | `Chỉ run đã hoàn tất; lifecycle command idempotent` | `Chỉ run ở COMPLETED, FAILED hoặc ABANDONED; lifecycle command idempotent` |
| E9 | 1707 (Android Parent scope) | `xóa run đã hoàn tất` | `xóa run ở COMPLETED, FAILED hoặc ABANDONED` |
| E10 | 1798 (lifecycle rules) | `- Xóa run đã hoàn tất cũng tạo lifecycle request;` | `- Xóa run ở COMPLETED, FAILED hoặc ABANDONED cũng tạo lifecycle request;` |
| R1 | 656 (NFR-31) | `run hoàn tất/abandoned và media giữ đến khi người dùng chủ động xóa;` | `run COMPLETED/FAILED/ABANDONED và media giữ đến khi người dùng chủ động xóa;` |
| R2 | 1064 (retention table) | `video hoàn tất hoặc ABANDONED` | `video của run COMPLETED, FAILED hoặc ABANDONED` |
| R3 | 2239 (R-19) | `` Run `COMPLETED`/`ABANDONED` và media `` | `` Run `COMPLETED`/`FAILED`/`ABANDONED` và media `` |
| E13 | 394 (StoryRun row, remarks cell) | `quyền cũ/token bị thu hồi, audit metadata được ghi.` | `quyền cũ/token bị thu hồi, audit metadata được ghi. Ngoại lệ có ghi nhận: SCRIPT_GENERATING và SCRIPT_GENERATION_UNKNOWN là hai giá trị mở rộng ngoài danh mục trạng thái này; hai giá trị được giữ trong response và dữ liệu lưu, và run ở hai giá trị này được phép hủy theo UC-11.` |

Reading the table: each cell's string is the text between the backticks. In R3 the string is
delimited by double backticks plus one space on each side, and contains single backticks.
E13's replacement is the whole anchor, one space, then the new sentence; the anchor itself is
unchanged and occurs once in the whole file.

Notes kept from Draft 2:
- E6: naming the three states excludes `DELETE_PENDING` and `DELETED`; "run chưa trong quá
  trình xóa" stays.
- The cancel wording "hủy run chưa hoàn tất" stays unchanged; its set is defined at line 1518.
- E13 makes the SRS record the two values of D-216 item 4 as a noted exception to the 18-state
  inventory of line 394. It adds no public state rule, no mapping and no new cancel rule
  beyond line 1518's negative definition. Contract §3.1 and §5 are aligned in the same step.

## 4. Disposition of the round-2 notes

| Note | Disposition | Effect |
|---|---|---|
| N-1 (two adjacent "hoặc" in E1) | **APPLIED.** A comma before the second "hoặc" separates the delete set from the cancel clause. | E1 +23 bytes instead of +22; punctuation only |
| N-2 (E2 names profile/account deletion) | **APPLIED, minimal D-214 form.** The second sentence now ends "…đến khi người lớn có quyền yêu cầu xóa." This is exactly D-208 item 6 / D-214 item 1 ("until an authorized user requests deletion"). It names no trigger, so it neither writes the account-deletion purge that SRS line 502 leaves open nor excludes profile deletion (UC-09, line 1496), which is itself a deletion request. | E2 +141 bytes instead of +194 |
| N-3 (R2 attaches the qualifier to "video" only) | **NOT APPLIED; accepted as is.** The suggested span ("Run COMPLETED, FAILED hoặc ABANDONED và tranh/audio, …") would restrict the subject of the retention row to runs in three states, which is a scope change beyond D-214 item 1. R2 only adds FAILED to the qualifier that the row already had; the looseness is the same in kind as today's text. | none |
| N-4 (a) (Contract approved before step 0, updated in step 3) | **RESOLVED.** Contract Draft 11 is approved for implementation and stays unchanged. The alignment is a new revision, Contract Draft 12 (§6), limited to SRS references; it is reviewed with this draft in step 2. | §6 |
| N-4 (b) (post-edit check by whom) | **RESOLVED.** Step 2 is the independent review (Sonnet 5.5 at high effort, set explicitly, a separate session) of the pre-computed bytes in §5. Step 6 compares the applied file with those values; an equal SHA-256 proves the file is byte-identical to what the reviewer verified, so the review covers the applied result. | §7 |
| N-5 (bookkeeping) | **APPLIED.** Line count stated both ways (§1); thirteen lines, not ten (§2 rule 2); numbering explained (§2 rule 5); re-pin paths written in full, FEAT-066 "where it carries the pin" (§7 step 5). | text only |
| N-6 (literal E13 string, pre-computed values) | **APPLIED.** E13's replacement is given literally (§3); the result is pre-computed in §5. The optional polish is applied: "và run ở hai giá trị này được phép hủy theo UC-11" (the run, not the value, is cancelled). | E13 +278 bytes instead of +250 |

## 5. Pre-computed result

Computed in memory from the pinned bytes by applying §3 at byte positions on the cited lines
(Python, `-B -I`, files read as bytes, lines split on LF with CR kept):

| Edit | Line | On line | In file | Byte column | Delta | Line ends CRLF |
|---|---|---|---|---|---|---|
| E1 | 270 | 1 | 1 | 10 | +23 | yes |
| E2 | 270 | 1 | 1 | 287 | +141 | yes |
| E3 | 284 | 1 | 1 | 119 | +27 | yes |
| E4 | 500 | 1 | 1 | 63 | +22 | yes |
| E5 | 1465 | 1 | 1 | 0 | +22 | yes |
| E6 | 1470 | 1 | 1 | 33 | +22 | yes |
| E7 | 1622 | 1 | 1 | 2 | +22 | yes |
| E8 | 1674 | 1 | 1 | 95 | +22 | yes |
| E9 | 1707 | 1 | 4 | 445 | +22 | yes |
| E10 | 1798 | 1 | 1 | 0 | +22 | yes |
| R1 | 656 | 1 | 1 | 88 | +5 | yes |
| R2 | 1064 | 1 | 1 | 57 | +16 | yes |
| R3 | 2239 | 1 | 1 | 9 | +9 | yes |
| E13 | 394 | 1 | 1 | 2814 | +278 | yes |

Byte columns are 0-based offsets of the current phrase within the line's bytes (before any edit
on that line).

- Changed lines: exactly 13: 270, 284, 394, 500, 656, 1064, 1465, 1470, 1622, 1674, 1707, 1798,
  2239. Lines 1-39 and every other line are byte-identical.
- Line count unchanged: 3,427 LF-terminated lines (3,428 split parts).
- Endings unchanged: 3,362 CRLF, 65 bare LF, 0 bare CR.
- Decodes as UTF-8.
- Size: 701,157 → **701,810** bytes (+653, the sum of the deltas).
- SHA-256 after the edit: **`443A3CA37272D2FE96127564BAF400461F394E098724A6BD999D723A4E504021`**.

## 6. Contract change made in the same step (D-208 item 6)

The approved Contract Draft 11 does not contain the sentences that Draft 2 §5 step 3 named
("must not become public StoryRun states" and "the SRS currently states" were in Contract
Draft 8 and were replaced by Draft 9). After the SRS edit the following Draft 11 text is stale,
and Contract Draft 12 (`plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT12_20261119.md`)
changes only these places:

- §1: the SRS pin moves to the new size and SHA-256; the SRS-wording row names this draft as
  applied.
- §3.1 (cancel, the two extension states): the eligible-states row and the R5-F3 paragraph
  say the SRS now records the two values in the remarks of line 394, so they are no longer a
  deviation from the SRS text; D-216 item 4 stays their authority.
- §3.2 (delete): the eligible-states row cites the aligned SRS lines (270, 500, 1465, 1470,
  1674).
- §5: the rows "User DELETE allowed for FAILED and ABANDONED" and "Two extension run states"
  are marked closed by the SRS revision.
- §6: the SRS-wording bullet says the edit is applied.
- Header and §9: change note and lineage.

No route, state set, schema, error, path or acceptance condition changes. Draft 11 stays the
contract against which the accepted implementation (`ceb3ea27`) was approved and accepted.

## 7. Steps

0. **Precondition (D-216 item 6), status on 2026-11-19:** the DTR (Draft 6, D-218 A-1), the
   Core port design (Draft 6, D-218 A-1), the Contract (Draft 11) and the Allowlist (Draft 13,
   with amendment 1) are approved; the implementation is accepted (FEAT-063
   `approvals/TASK_APPROVAL.md`, FR-C-08 entries of 2026-11-19). The owner confirmed that the
   SRS edit is the next step. This is not the order of D-208 item 6 and D-216 item 6, which
   put the reviewed SRS edit before any implementation: the owner approved and accepted the
   implementation first, and the implementation approval lists the SRS edit as not authorized
   by it. The edit is therefore a follow-up recorded in `TASK_APPROVAL.md` (review F-4).
1. The owner approved the edit set E1-E10, R1-R3 and E13 of Draft 2, shown with its lines and
   replacement strings. Draft 3 changes only the E1, E2 and E13 strings, within D-214 item 1
   and D-216 item 4 (§4); the bytes applied are therefore not exactly the bytes the owner saw.
   The approving decision row names the three changes so that the owner can confirm or reverse
   them (review F-3).
2. An independent review on Sonnet 5.5 at high effort (set explicitly, separate session)
   checks §3, §5 and Contract Draft 12 against the pinned bytes.
3. The Contract alignment (§6) is made in the same step.
4. **Who edits:** a separately started session on the owner's word, not the coordinating
   session (D-216 item 6). The edit is applied by byte position, keeping line endings.
5. **Re-pin, two classes:**
   - live pointers and active plans move to the new SHA-256: `docs/context/PROJECT_CONTEXT.md`,
     `docs/context/SOURCE_REGISTER.md`, `docs/context/SRS_AUTHORITY.md`; FEAT-063 `CONTEXT.md`,
     `SOURCE_REGISTER.md` and `status/STATUS.md`; FEAT-066 `status/STATUS.md` (FEAT-066 has no
     `CONTEXT.md` or `SOURCE_REGISTER.md` that carries the pin). This draft and Contract Draft 12
     already carry the new SHA-256 (with the old one as the "before" pin) and need no change;
   - records pinned to `B9B1F42D…` (decisions, approvals, cold reviews, evidence, earlier and
     approved drafts) stay as written and are listed in the approving decision row.
6. **Post-edit check:** changed lines equal the §5 set; 3,427 lines; endings unchanged; size and
   SHA-256 equal §5; the decision row records them. The decision row is D-219, the next free ID
   in FEAT-063 `DECISIONS.md` (D-218 is the last in this branch and in the root checkout).

## 8. Not verified

- Documents outside the repository that quote these SRS lines, and the companion
  `DATA_TABLE_REGISTER.md`.
- Native-speaker review of the Vietnamese beyond the reviewers' own reading.
