# FR-C-08 SRS wording edit — proposed text, Draft 1

**Status: DRAFT / NOT REVIEWED / NOT APPROVED.**
**Date:** 2026-11-19.
**Purpose:** the documentation-only SRS revision that D-214 item 1 requires and D-216 item 6
schedules for the end of FR-C-08 planning. The coordinator drafts the text; it does **not**
edit the canonical SRS. The owner approves the final text, an independent review checks it, and
only then is the canonical file changed and every document that pins it re-pinned (D-208 item 6,
D-216 item 6).

## 1. Pins

| Input | Pin |
|---|---|
| Canonical SRS (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Decision being written into the SRS | D-214 item 1: user-triggered DELETE is allowed for `COMPLETED`, `FAILED` and `ABANDONED`; `FAILED` and `ABANDONED` are never purged automatically |
| Site list | D-216 item 6: lines 270, 284, 500, 1465, 1470, 1622, 1674, 1707, 1798 (lines 1037 and 1845 mention cancel only and need no change) |

## 2. Wording rule

The SRS text is Vietnamese, so the replacement text is Vietnamese. One term is used at every
site: **"run đã kết thúc"**, defined once at BR-26 as a run in `COMPLETED`, `FAILED` or
`ABANDONED`. It replaces "run đã hoàn tất" / "run hoàn tất" only where deletion eligibility is
meant. "Hủy run chưa hoàn tất" (cancel) is left unchanged: its set is defined negatively at
line 1518 and already excludes the three states.

Each edit changes only the quoted phrase; the rest of each line stays byte-identical.

## 3. Edits

| # | Line | Current text (exact phrase) | Proposed text |
|---|---|---|---|
| E1 | 270 (BR-26) | `Khi người dùng xóa run đã hoàn tất hoặc hủy run chưa hoàn tất,` | `Khi người dùng xóa run đã kết thúc (COMPLETED, FAILED hoặc ABANDONED) hoặc hủy run chưa hoàn tất,` and, after the sentence that ends `chỉ giữ audit metadata tối thiểu.`, insert ` Run FAILED hoặc ABANDONED không bị purge tự động; nội dung chỉ bị xóa khi người lớn có quyền yêu cầu xóa.` |
| E2 | 284 (BR-40) | `xóa run hoàn tất xóa linked media/content.` | `xóa run đã kết thúc (COMPLETED, FAILED hoặc ABANDONED) xóa linked media/content.` |
| E3 | 500 (FR-C-08) | `hoặc xóa run đã hoàn tất qua lifecycle.` | `hoặc xóa run đã kết thúc (COMPLETED, FAILED hoặc ABANDONED) qua lifecycle.` |
| E4 | 1465 (UC-07 heading) | `### UC-07 — Người lớn xóa run đã hoàn tất` | `### UC-07 — Người lớn xóa run đã kết thúc` |
| E5 | 1470 (UC-07 precondition) | `Run đã hoàn tất; caller có quyền; run chưa trong quá trình xóa` | `Run ở COMPLETED, FAILED hoặc ABANDONED; caller có quyền; run chưa trong quá trình xóa (không ở DELETE_PENDING hoặc DELETED)` |
| E6 | 1622 (permission matrix) | `Xóa nội dung run đã hoàn tất` | `Xóa nội dung run đã kết thúc` |
| E7 | 1674 (API table, DELETE) | `Chỉ run đã hoàn tất; lifecycle command idempotent` | `Chỉ run ở COMPLETED, FAILED hoặc ABANDONED; lifecycle command idempotent` |
| E8 | 1707 (Android Parent scope) | `xóa run đã hoàn tất` | `xóa run đã kết thúc` |
| E9 | 1798 (lifecycle rules) | `- Xóa run đã hoàn tất cũng tạo lifecycle request;` | `- Xóa run đã kết thúc (COMPLETED, FAILED hoặc ABANDONED) cũng tạo lifecycle request;` |

E5 adds "không ở DELETE_PENDING hoặc DELETED" to make "run chưa trong quá trình xóa" exact, in
the same terms as line 1518. It adds no new rule (Contract Draft 8 §3.2: those two states accept
no new delete or cancel command).

## 4. Optional edit for the owner to choose

| # | Line | Proposal | Reason |
|---|---|---|---|
| O1 | 394 (StoryRun state row, remarks cell) | Append: ` Hai giá trị mở rộng SCRIPT_GENERATING và SCRIPT_GENERATION_UNKNOWN được giữ trong response và dữ liệu lưu theo contract M2 đã freeze, là độ lệch có ghi nhận so với danh mục 18 trạng thái (D-216); cả hai được phép hủy.` | D-216 item 4 records keeping the two source-only values as an explicit deviation from line 394. Writing it in the SRS keeps the SRS and the response contract consistent; leaving it out keeps the deviation only in `DECISIONS.md`. |

**Recommendation:** include O1. Without it, the SRS still says the public set is exactly 18
values while the approved response has 20.

## 5. What this edit does not change

- The cancel rules (lines 1037, 1515-1523, 1673, 1797, 1845): unchanged.
- Teacher wording at UC-07 and line 1674 (Teacher remains a P2 slice; D-214 item 4 records the
  scope limit, not an SRS change).
- Any other requirement, state, route or table.

## 6. Steps after approval

1. Owner approves the final text (E1-E9, and O1 if chosen).
2. Independent review (Sonnet 5.5 high) of the exact before/after bytes.
3. The canonical file is edited once; new size and SHA-256 recorded in a decision row.
4. Every document that pins the old SHA-256 (`B9B1F42D…`) is re-pinned or marked as pinned to
   the earlier revision.

## 7. Not verified

- Whether other documents outside FEAT-063 quote these SRS lines verbatim.
- The line numbers after the edit (E1 adds a sentence inside an existing line, so no line moves).
