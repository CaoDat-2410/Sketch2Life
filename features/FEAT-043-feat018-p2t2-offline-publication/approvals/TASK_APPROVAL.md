# Task approval

- Status: APPROVED
- Approver: Person 2 — owner of the task (AI Understanding lane), owner of FEAT-018 P2-T2.
- Approved scope: publish the FEAT-018 P2-T2 offline WIP checkpoint as the five PUB-P1 commits on
  `feature/feat018-p2t2-live-lightning`, with owner decisions A + B1 + C1 as quoted below.
- Plan revision: FEAT-043 `plan/PLAN.md` revision PUB-P1-EXEC-1, executing the local draft plan
  PUB-P1 (`features/FEAT-018-live-image-canvas-flow/plan/P2_T2_PUBLICATION_COMMIT_PLAN_DRAFT_20261011.md`,
  19659 bytes, SHA-256 `3e01af07d80b749334169999b2671f797b5a17f446b2fdf58535bd358b557dc0`) and its
  inventory (`features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_PUBLICATION_INVENTORY_20261011.json`,
  55247 bytes, SHA-256 `7dcec8354036f585a21c64551eba97701f8d849bda0f0d8cced60049e9b962de`).
  Both remain local and unpublished.
- Approved at: owner decision timestamp NOT SUPPLIED. Recorder timestamp (observed): 2026-10-11T05:39:42Z.
- Notes: recorded in this separate publication feature because the FEAT-018
  `approvals/TASK_APPROVAL.md` approval-write hold stays in force; this record neither releases
  that hold nor repins FEAT-018 history. Recorder: Claude Code session acting for Person 2.

## Approval 1 — publication preparation (2026-10-11)

Person 2 authorized, in chat: preparation, a separate publication worktree, recording the
publication approval in an appropriate owning feature (a separate feature if needed to avoid
the APP-write hold), offline verification, exact-scope staging, commit and normal push once the
mandatory gates are met. It was explicitly not acceptance of every content exclusion; missing
semantics acceptance was to be reported with a precise request. No live, D6, provider, SSH,
credential, force-push or dev-merge action is authorized.

## Approval 2 — owner decisions A + B1 + C1 (verbatim, 2026-10-11)

The owner's message is reproduced verbatim except that two local machine paths are replaced by
bracketed placeholders, because this record is public.

```text
Hoàn tất publication checkpoint WIP FEAT-018 P2-T2 theo 5 commit của PUB-P1 và push lên origin/feature/feat018-p2t2-live-lightning.

Tôi duyệt thực hiện A + B1 + C1 trong phạm vi dưới đây. Đây là approval mới cho publication; hãy ghi nhận trong FEAT-043. Không cần hỏi lại các quyết định đã chốt nếu candidate và bằng chứng vẫn khớp.

Nguồn:
- Repository: [local repository root]
- PUB-P1: features/FEAT-018-live-image-canvas-flow/plan/P2_T2_PUBLICATION_COMMIT_PLAN_DRAFT_20261011.md
- Inventory: features/FEAT-018-live-image-canvas-flow/evidence/notes/P2_T2_PUBLICATION_INVENTORY_20261011.json
- Review package, exclusions và summary nằm trong:
  [local session scratchpad]
- Baseline: 44af2e4f9a75064df327496f033c75f9fe0d0f5d.

Các quyết định đã duyệt:

A. Chấp nhận content-exclusion semantics cho đúng 5 publication trees:
- 231 file baseline trong SCANNER_EXCLUSIONS_T1_T4.tsv.
- T5 được thêm đúng 8 .gitkeep của template FEAT-043, mỗi file 0 byte; ghi rõ từng path.
- Scanner SHA-256:
  4c8733f65cf507c6c3276d03ad8bd530e982839d75605d72e292d4f1520cfb5c
- Exclusions TSV SHA-256:
  a40f8fed3f693462481d82ce69bccdc8814e5d28681ce6db38582fc4c2468c02
- Acceptance chỉ áp dụng cho checkpoint này. Không phải security PASS tổng quát, không đóng Security S3/C1–C7 hoặc live gates. Ghi rõ 5 binary baseline chưa được kiểm tra content.

B1. Giữ nguyên architecture finding baseline tại backend_ai_workflow.py:
- Chấp nhận ngoại lệ publication cho đúng finding không đổi đã xác định.
- Vẫn ghi architecture check là FAIL.
- Không đưa ARCHITECTURE_MINIMAL_FIX.patch vào đợt này; để FEAT-020 xử lý riêng.

C1. Publish nguyên bytes của 18 selected originals:
- Chấp nhận lint/type debt đã kiểm kê để lưu checkpoint WIP: whole-backend Ruff 550 findings (547 mới), mypy 115 errors (112 mới).
- Vẫn ghi các check này là FAIL; không đổi config, thêm ignores, format hoặc sửa source/test.
- Không khẳng định tất cả findings đều false positive. Chỉ ghi rà mẫu chưa thấy runtime defect trong các cụm đã kiểm tra.
- Historical acceptance vẫn có hiệu lực với historical bytes. Revision mới sau này phải có identity, review và acceptance riêng.
- 9 full-suite failures chỉ được ghi là baseline khi tên test và nguyên nhân khớp bằng chứng đã đối chiếu. Không miễn trừ lỗi mới dựa vào tổng count.

Thực hiện:

1. Đọc AGENTS.md và context/source register liên quan. Chuẩn bị FEAT-043 plan, acceptance criteria, approval và evidence trước publication. Approval trích đúng yêu cầu này; giữ nguyên FEAT-018 approval-file hold.

2. Giữ nguyên root checkout, 76 originals, acceptance pins lịch sử, 58 held files và BE2 worktree. Commit trên nhánh preparation riêng trong worktree publication.

3. Hoàn tất fresh review scanner source/test đúng identities hiện tại, lưu scope, kết luận và giới hạn vào FEAT-043. Không dùng các review M1 cũ làm current PASS. Giữ nguyên output mandatory_gate của scanner; ghi riêng owner semantics acceptance cùng actual-tree results.

4. Sửa public summary:
- {T4_RESULT} → 1692 passed / 5 skipped.
- Ghi đầy đủ full-suite T4: 3138 passed / 12 skipped / 9 failed, với baseline attribution.
- Chỉ ghi FEAT-043 acceptance đã được record sau khi thực sự ghi nhận.
- Phân biệt 8 R3 files với wrapper unchanged được acceptance riêng.
- Giữ Medium residual, POSIX UNVERIFIED và các live/security blockers.
- Không đưa machine paths hoặc held private content vào tài liệu public.

Tôi duyệt summary sau khi các sửa đổi trên hoàn tất và review không phát hiện vấn đề mới; khi đó được thêm vào evidence index.

5. Tạo đúng 5 commit theo PUB-P1:
- fix(security): guard repository text reads and declare exclusions
- feat(feat018): add offline binding and execution contracts
- feat(feat018): add preflight and runtime observations
- feat(feat018): add guarded SSH development attempt
- docs(feat018): publish offline checkpoint and remaining gates

Chuẩn bị FEAT-043 records ở khu vực preparation riêng; chỉ đưa bộ public vào candidate ở commit 5. Không để các file untracked này làm T1–T4 lệch khỏi exact intermediate trees.

6. Kiểm tra từng actual commit tree. Có thể tái sử dụng fresh T1–T4 evidence nếu tree/blob identities khớp hoàn toàn. Chạy repository security trước mỗi commit/push. T5 phải chạy lại harness, security, architecture, skeleton khi áp dụng, và diff checks sau khi thêm toàn bộ tài liệu. Chỉ giữ các ngoại lệ B1/C1 và baseline test failures đã duyệt; không mở rộng sang lỗi khác.

7. Kiểm tra remote tip trước publication. Nếu vẫn đúng baseline, push bình thường bằng refspec rõ ràng:
   HEAD:refs/heads/feature/feat018-p2t2-live-lightning
Không force-push, merge dev, thay branch ref của root checkout hoặc thực hiện live/provider actions.

Nếu originals, scanner identity, exclusions, remote tip lệch hoặc có blocker mới, dừng commit/push liên quan và báo nguyên nhân cụ thể. Ngoài các trường hợp đó, tiếp tục đến khi push hoàn tất.

Báo cáo cuối: 5 commit hashes, remote tip sau push, kiểm tra cuối và các FAIL/limitations được giữ lại. Xác nhận originals, historical pins, root checkout và BE2 worktree không đổi.
```

## Pre-execution identity check (recorder, 2026-10-11T05:38:43Z)

All 76 PUB-P1 originals matched the inventory (size, raw SHA-256, CRLF count, LF projection; 0
mismatches; 18 selected / 58 held). The scanner was 24792 bytes, SHA-256
`4c8733f65cf507c6c3276d03ad8bd530e982839d75605d72e292d4f1520cfb5c`. The exclusion TSV matched
`a40f8fed3f693462481d82ce69bccdc8814e5d28681ce6db38582fc4c2468c02`. All 8 template `.gitkeep`
files were 0 bytes. The remote tip of `feature/feat018-p2t2-live-lightning` equalled the baseline
`44af2e4f9a75064df327496f033c75f9fe0d0f5d`.

## Limits of this approval

- Decision A applies only to the five PUB-P1 commit trees. It is not a general repository-security
  PASS and closes neither Security S3, C1–C7, D6 nor any live gate. The five binary baseline
  files listed in the evidence were not content-checked by the scanner.
- B1 and C1 are publication exceptions for the exact findings measured. Architecture, Ruff and
  mypy remain recorded as FAIL. No other failure is exempted.
- Historical acceptances stay bound to their historical bytes. A later revision of any
  published file needs its own identity, review and acceptance.
