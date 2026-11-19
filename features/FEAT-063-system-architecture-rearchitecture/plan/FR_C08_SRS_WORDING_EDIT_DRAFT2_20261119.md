# FR-C-08 SRS wording edit — proposed text, Draft 2

**Status: DRAFT / NOT APPROVED.** Round-2 candidate.
**Date:** 2026-11-19.
**Purpose:** the documentation-only SRS revision required by D-214 item 1 and scheduled by
D-216 item 6. The coordinator drafts the text and does **not** edit the canonical SRS.

**Change from Draft 1:** fixes the round-1 cold review
(`tmp/frc08-srs-edit/review-r1/FR_C08_SRS_WORDING_EDIT_COLD_REVIEW_R1_20261119.md`, NEEDS
REVISION, 0 P1 / 3 P2 / 5 P3). The new term "run đã kết thúc" is dropped; every site names the
three states (F1). §5 restates the after-approval steps against D-208 item 6 and D-216 item 6
(F2). The owner chose on 2026-11-19 to include the three retention sites (F3, R1-R3), the
two-class re-pin rule (§5 step 5) and O1 (now E13). F4-F8 are applied.

## 1. Pins

| Input | Pin |
|---|---|
| Canonical SRS (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`; UTF-8, 3,428 lines, mixed CRLF/LF endings |
| Decision written into the SRS | D-214 item 1 (user DELETE for COMPLETED, FAILED, ABANDONED; FAILED and ABANDONED never purged automatically); D-216 item 4 (two documented extension states) |
| Site list | D-216 item 6 (lines 270, 284, 500, 1465, 1470, 1622, 1674, 1707, 1798), plus R1-R3 and E13 by the owner's choice; lines 1037 and 1845 need no change |

## 2. Rules for applying the edit

1. Each edit changes only the quoted phrase, and only on the cited line; the phrase occurs
   exactly once on that line (checked for all fourteen). Never apply an edit as a file-wide
   replace (the phrase `xóa run đã hoàn tất` also occurs on other edited lines).
2. Line endings stay as they are (the ten cited lines end in CRLF).
3. The header and the "Kiểm soát tài liệu" table (lines 4-39) are not touched, so no line moves
   and every line citation in D-208 to D-217, the Contract and the DTR stays valid. The revision
   is recorded in `DECISIONS.md` and the re-pin records instead.
4. The state names are written in the SRS's own form (`COMPLETED`, `FAILED`, `ABANDONED`).

## 3. Edits

| # | Line | Current phrase (exact) | Replacement |
|---|---|---|---|
| E1 | 270 (BR-26) | `Khi người dùng xóa run đã hoàn tất hoặc hủy run chưa hoàn tất,` | `Khi người dùng xóa run ở COMPLETED, FAILED hoặc ABANDONED hoặc hủy run chưa hoàn tất,` |
| E2 | 270 (BR-26) | `chỉ giữ audit metadata tối thiểu.` | `chỉ giữ audit metadata tối thiểu. Run FAILED hoặc ABANDONED không bị purge tự động; nội dung được giữ đến khi người lớn có quyền yêu cầu xóa run hoặc xóa hồ sơ/tài khoản theo lifecycle.` |
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
| R3 | 2239 (R-19) | ``Run `COMPLETED`/`ABANDONED` và media`` | ``Run `COMPLETED`/`FAILED`/`ABANDONED` và media`` |
| E13 | 394 (StoryRun row, remarks cell) | `quyền cũ/token bị thu hồi, audit metadata được ghi.` | the same phrase followed by ` Ngoại lệ có ghi nhận: SCRIPT_GENERATING và SCRIPT_GENERATION_UNKNOWN là hai giá trị mở rộng ngoài danh mục trạng thái này; hai giá trị được giữ trong response và dữ liệu lưu, và được phép hủy theo UC-11.` |

Notes:
- E2 replaces Draft 1's "chỉ bị xóa khi … yêu cầu xóa", which could be read as "only through the
  delete route", while profile or account deletion (SRS lines 502, 1496) also purges runs (F4).
- E6 drops Draft 1's redundant clause; "run chưa trong quá trình xóa" already covers it, and the
  three states named first exclude `DELETE_PENDING` and `DELETED`.
- The cancel wording "hủy run chưa hoàn tất" stays unchanged; its set is defined at line 1518
  (F5, accepted as is).
- E13 changes the cancel-eligible set of the SRS from 13 to 15 values in effect; Contract §3.1
  (which says the two values must not become public states) must be updated in the same step
  (§5 step 3).

## 4. Checks done on this draft

- All fourteen current phrases (E1-E10, R1-R3, E13) occur exactly once on the cited line
  (Python, UTF-8, against the pinned bytes); the E13 anchor occurs once in the whole file.
- No tenth delete-eligibility site exists (round-1 review §3, whole-file search).

## 5. Steps after this draft

0. **Precondition (D-216 item 6):** the SRS is edited once, at the end, after the DTR, the Core
   port, and the next Contract and Allowlist revision are approved. The owner confirms that the
   SRS edit is the next step.
1. The owner approves the final text (E1-E10, R1-R3, E13).
2. An independent review (Sonnet 5.5 high) checks the exact before/after bytes.
3. The Contract is updated in the same step (§3.1 two extension states; §3.2 "the SRS currently
   states"), and reviewed (D-208 item 6: SRS wording **and corresponding contract**).
4. **Who edits:** the owner, or a separately started session on the owner's word; not the
   coordinating session (D-216 item 6). The edit is applied by byte position, keeping line
   endings.
5. **Re-pin, two classes (owner choice of 2026-11-19, to be recorded in the approving decision
   row, because D-216 item 6 says "re-pinned"):**
   - live authority pointers and active plans are re-pinned to the new SHA-256:
     `docs/context/PROJECT_CONTEXT.md`, `SOURCE_REGISTER.md`, `SRS_AUTHORITY.md`, FEAT-063 and
     FEAT-066 `CONTEXT.md`, `SOURCE_REGISTER.md`, `STATUS.md`, and the active FR-C-08 plan
     documents;
   - historical records pinned to `B9B1F42D…` (cold reviews, M2 approvals and evidence, FEAT-066
     audits) stay as written and are listed in the approving decision row as pinned to the
     earlier revision.
6. **Post-edit check:** the changed lines are exactly the approved set; the line count stays
   3,428; line endings are unchanged; the new size and SHA-256 equal values pre-computed from the
   approved text; the decision row records them.

## 6. Not verified

- Documents outside the repository that quote these SRS lines.
