# FR-C-08 - SRS-based analysis of the remaining blockers (2026-11-19)

Record only. This note decides nothing for the owner and approves nothing. It is a new file; no existing record was edited. It was written by the coordinating Claude session (Sonnet 5.5) after the owner asked for the open items to be settled from the SRS. Each item below is classed as SETTLED BY SRS, SETTLED WITH INFERENCE (the SRS fixes the direction, the coordinator fills a gap) or OWNER-ONLY (the SRS is silent, marks it open, or conflicts with accepted M2 behaviour). Nothing here is a decision row until the owner records it.

Sources read:

- Canonical SRS: 701,157 B, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`. The copy in the owner's Downloads folder is byte-identical.
- Companion register `artifacts/DATA_TABLE_REGISTER.md` (Rev57, v2.7-draft, named by the SRS header as the accompanying document). It is unsigned and older than the SRS date; D-209 does not name it. It is used here only as supporting evidence, and any item that rests on it alone is marked.
- Current backend source at the root HEAD `08439b22`.

## 1. Parent scope on the lifecycle receipt and the cancellation notice - SETTLED BY SRS (direction), OWNER-ONLY (migration)

- SRS line 1048 (section 11.2): "Không biểu diễn Parent bằng organization giả." SRS line 771 defines `OwnerScopeRefV1` with `PARENT_ACCOUNT`.
- Register line 73: every cross-role row that holds user-owned data must carry typed `owner_scope_kind` and `owner_scope_ref`; legacy organization columns stay "cho đến khi có migration tương thích được phê duyệt riêng". Register line 213: `ai_jobs.cancellation_notice` gets "owner scope và story_run_ref để hủy cho Parent/Teacher". Register line 247 lists the current `be1_data_lifecycle_requests` columns (`organization_id`, `state`, `unresolved_items`, `result_ref`, ...).
- Disposition: the delta that D-214 items 3 and 8 call for is now concrete. Add typed owner scope (`owner_scope_kind` / `owner_scope_ref`) to `be1_data_lifecycle_requests` and `ai_jobs.cancellation_notice`, and `story_run_ref` to the notice. Do not create an organization for a Parent.
- Inference: because a Parent row must not carry an organization, `organization_id` has to be allowed to stay empty for Parent rows (today it is non-nullable in both tables). The SRS does not say this in one sentence.
- Still OWNER-ONLY: register line 204 says exact SQL types and migration steps need the owner's separate approval. No schema work starts before that.

## 2. Durable receipt owner and workflow records - SETTLED BY SRS

- SRS lines 1475, 1523 and 2339 name `be1.data_lifecycle_requests` as the lifecycle record for run cancel and delete; register line 104 says BE1 coordinates "lifecycle hồ sơ/run và receipt xóa". SRS lines 1951-1952: lifecycle deletion works "theo batch idempotent. Lỗi giữ deletion-pending để retry; chưa đánh dấu hoàn tất đến khi đối soát đủ object."
- Disposition: BE1 owns the receipt in `be1_data_lifecycle_requests`. The existing columns `state`, `unresolved_items` and `result_ref` are the durable workflow (accepted, pending, retries, reconciliation, completion). No new table and no new public StoryRun state are needed. What remains for the technical DTR is the value vocabulary of those three columns; this narrows D-214 item 8.

## 3. Core reference closure - SETTLED BY SRS (rule), design work remains

- SRS line 1052: derived artifacts keep their own asset identity and source lineage. Line 1054: if another valid object still references an asset, delete it "chỉ ... khi không còn reference được lưu hợp lệ theo owner lifecycle". Line 1952: "Chia sẻ asset giữa run không phải tính năng V1." Register line 547: deleting a run must not silently delete the Lesson source document that an occurrence shares.
- Disposition: Core exposes one reference-closure check over `core.asset_metadata` and lineage; the run lifecycle deletes run-owned assets and keeps any asset with another valid reference. Because sharing between runs is not a V1 feature, the V1 check is a verification, not a general reference-counting service.
- Still open: no Core port exists today (`CoreAssetMetadataPort` has only save and get). Defining that port is a short design task with its own review.

## 4. Public run-state set in responses - SETTLED BY SRS

- SRS line 394 lists 18 StoryRun states; line 895 requires explicit enums for state. Line 1673 returns "202 trạng thái DELETE_PENDING" for cancel.
- Disposition: the public response state set is the 18 SRS states. `ABANDONED` and `DELETED` are added to the response literal in the Parent story-run schema.

## 5. The two source-only states - OWNER-ONLY

- `SCRIPT_GENERATING` and `SCRIPT_GENERATION_UNKNOWN` are not in the SRS. In source they are real stored values (database check constraint, `parent_story_repository.py` lines 1056 and 1213: the second marks an unknown generation outcome that is kept instead of failing the run).
- Coordinator reading, not an SRS statement: `SCRIPT_GENERATING` corresponds to `STORY_GENERATING`; `SCRIPT_GENERATION_UNKNOWN` is a not-yet-reconciled generation. Both are unfinished, so both should be cancellable under the 13-state rule.
- Why owner-only: changing or hiding them contradicts M2 behaviour the owner already accepted, and stored rows already carry them. The choice is between keeping them as documented extensions of the SRS or mapping them to SRS states at the response edge. The SRS does not decide this.

## 6. Lifecycle projection on the existing GET - SETTLED BY SRS (direction), details open

- SRS lines 805 and 1811: one aggregated `GET /v1/story-runs/{id}`; no extra endpoints; no internal object keys (line 2145 for errors). SRS line 1736: the client polls lifecycle status while the run is `DELETE_PENDING`. SRS line 1520 and 1951: `DELETED` is written only after the lifecycle completes and object references are reconciled.
- Disposition: the existing GET shows `DELETE_PENDING` until the lifecycle request is complete, then `DELETED`; no percentage and no content. The exact extra fields are a small technical design decision and must exclude media, prompts and storage keys.
- Related fact: the current GET lacks the SRS StoryRunDetailV1 timeline; the M2 owner disposition at `approvals/TASK_APPROVAL.md` line 3250 records this as OPEN-OWNER and non-blocking.

## 7. Audit - SETTLED BY SRS (fields), OWNER-ONLY (reader and retention)

- SRS line 1056: audit keeps "actor/action/loại resource/thời gian/kết quả và deletion receipt; không giữ media, transcript, prompt hoặc chi tiết profile." Register line 198 says `core_audit_entries` is metadata-only.
- Disposition: audit rows written by the lifecycle carry exactly those fields. Whether `core_audit_entries` is the physical target is likely but is not stated for this use.
- Not decidable from the SRS: SRS line 2758 and open item O-17 (line 2996) leave the 180 versus 365-day map, the audit-reader authorization and the physical mapping open.

## 8. SRS wording alignment for D-214 item 1 - proposed text, OWNER-ONLY to apply

The text below makes the SRS say what D-214 item 1 decided. It changes the canonical SRS bytes, so every pin to the SRS must be redone afterwards; do it once, together with any other SRS edit.

| SRS line | Current text (part) | Proposed text (part) |
|---|---|---|
| 270 (BR-26) | "Khi người dùng xóa run đã hoàn tất hoặc hủy run chưa hoàn tất" | "Khi người dùng xóa run đã kết thúc (COMPLETED, FAILED hoặc ABANDONED) hoặc hủy run chưa kết thúc" |
| 284 (BR-40) | "xóa run hoàn tất xóa linked media/content" | "xóa run COMPLETED, FAILED hoặc ABANDONED xóa linked media/content" |
| 500 (FR-C-08) | "xóa run đã hoàn tất qua lifecycle" | "xóa run COMPLETED, FAILED hoặc ABANDONED qua lifecycle" |
| 1470 (UC-07) | "Run đã hoàn tất; caller có quyền; run chưa trong quá trình xóa" | "Run ở COMPLETED, FAILED hoặc ABANDONED; caller có quyền; run chưa trong quá trình xóa" |
| 1674 (section 21.2) | "Chỉ run đã hoàn tất; lifecycle command idempotent" | "Chỉ run ở COMPLETED, FAILED hoặc ABANDONED; lifecycle command idempotent" |
| 1798 | "Xóa run đã hoàn tất cũng tạo lifecycle request" | "Xóa run COMPLETED, FAILED hoặc ABANDONED cũng tạo lifecycle request" |

Support for the change inside the SRS: lines 656, 1064, 1350 and 1372 already keep ABANDONED content "đến khi người dùng xóa", and line 383 names FAILED and ABANDONED together.

## 9. Teacher scope - SETTLED BY SRS (phasing)

- SRS lines 667 and 668 place Parent playback/delete in phase P1 and the Teacher slice in P2; lines 2339 and 2341 ask for a lifecycle "as shared Parent/Teacher slice". D-214 item 4 (Parent first, shared design, Teacher adapter deferred) is consistent with both. No change.

## 10. Items the SRS cannot settle (owner only)

1. Named accountable owners for the six modules and where the assignment is recorded (D-208 item 4, D-214 item 12).
2. Confirmation of CONV-1 and the exact FR-C-08 base commit (D-214 item 10). The local branch `feature/feat066-conv1` is now at `03342207`, a docs-only commit above `2dddc607`.
3. Approval of the schema and migration steps (register line 204).
4. The 180/365-day audit map and audit-reader authorization (SRS line 2758).
5. Disposition of the two source-only run states (section 5).
6. Whether to apply the SRS wording change in section 8 and when.

## 11. What this changes in the plan

- The "DTR/schema" blocker shrinks from a design of new receipt structures to: owner-scope columns on two existing tables, nullability of `organization_id` for Parent rows, `story_run_ref` on the notice, and a value vocabulary for `state` / `unresolved_items` / `result_ref`. It still needs the owner's migration approval.
- The "Core contract" blocker shrinks to one reference-closure port, with V1 verification semantics.
- The "response schema" blocker is settled except for the two source-only states.
- Remaining before an implementation approval request: items 1, 2, 3 and 5 of section 10, the SRS edit, the five P3 notes carried from review round 5, and the independent review of the resulting allowlist (the five-round cap is spent; the owner would have to extend it).
