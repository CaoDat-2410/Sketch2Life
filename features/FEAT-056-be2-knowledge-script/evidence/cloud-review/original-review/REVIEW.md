# BE2-07 — Claude independent offline review (2026-10-20)

Phạm vi: implementation BE2-07 (FEAT-056), evidence cuối và các tracked diff. Read-only: không sửa source/test/plan/status/metrics, không stage/commit.
Worktree `.worktrees/be2-07-knowledge-script`, branch `feature/be2-07-knowledge-script`, HEAD `23acf9e83e181305edfeb345be9a8e7eb9dbef88`, index rỗng (xác nhận trước và sau khi chạy).

## 1. Findings

Không có P0/P1. Có 3 P2 và 6 P3. Hành vi ở P2-2, P3-2, P3-3, P3-4, P3-5 đã tái hiện bằng probe in-memory; P2-1 tái hiện trên bản sao; P2-3 và P3-1 là test gap có mutant sống sót (code hiện tại cư xử đúng).

### P2-1 — Unit test đóng băng SHA256 của 572 file backend dùng chung (đã tái hiện trên bản sao)
- File: `backend/tests/unit/test_knowledge_bundle_chain.py:230-258` (vòng so hash ở 234-237); node `test_572_original_backend_files_and_required_batch_profile_are_preserved` (map X02).
- Trigger: bất kỳ thay đổi hợp lệ nào về byte ở một trong 572 file (application/domain/infrastructure/contracts/interfaces, `main.py`, `conftest.py`...) sau khi 07 vào nhánh chung, ví dụ BE2-05/06 review-fix hoặc BE2-08..14 chỉnh file dùng chung. Test cũng đòi `required_07` đúng 6 file, nên thêm một file test 07 cũng làm nó đỏ.
- Expected: invariant "không sửa source 01–06" thuộc evidence runner (đã có `source-before/after.json`), không phải test sản phẩm vĩnh viễn.
- Actual: sao chép các file cần thiết sang `probes/frozen_copy`; test pass khi nguyên vẹn, thêm một dòng comment vào `domain/assistance.py` (chỉ trên bản sao) thì test FAIL (`probes/frozen_copy_probe.out`).
- Tác động: full unit suite đỏ ngay khi 07 được gộp vào nhánh có sửa file dùng chung; buộc sửa test 07 hoặc chấp nhận suite đỏ.
- Đề xuất: giữ kiểm tra này trong runner/finalizer (evidence); hoặc chỉ chạy khi có cờ evidence; bỏ phụ thuộc vào metrics của FEAT-055 và vào số file test 07.

### P2-2 — Heuristic "imagined → fact" bị vượt bằng khác biệt dấu câu/khoảng trắng/ký tự định dạng (đã tái hiện)
- File: `backend/src/sketch2life/domain/knowledge_bundle.py:225-226, 415-422`; lặp lại ở `contracts/schemas/knowledge_bundles.py:314-321` (record validator). Node liên quan: `test_unknown_duplicate_refs_and_literal_imagined_fact_laundering`, `test_record_full_basis_literal_and_hidden_imagined_metadata_rejected`, `test_child_imagined_removed_keeps_provenance_and_cannot_become_fact` (map N02/P08).
- Trigger (`probes/probe_a.out`, P5): child basis có imagined `"Mèo có cánh."` (chính fixture của harness). Teacher edit một claim teacher_attested có text `"Mèo có cánh"` (bỏ dấu chấm), `"Mèo  có cánh."` (hai khoảng trắng), `"Mèo có c​ánh."` (zero-width) hoặc `"Ｍèo có cánh."` (full-width). Cả bốn: edit 200, bundle v2 `generation_ready`, imagined text đi vào `script_text` như fact.
- Expected (plan §4.3, N02): leakage literal sau NFC/casefold bị chặn.
- Actual: chỉ chặn khi literal imagined là substring nguyên văn kể cả dấu câu và khoảng trắng; mọi test đều dùng literal có đủ dấu câu. Chiều ngược (claim là tiền tố/chuỗi con của imagined dài hơn) cũng không được kiểm.
- Tác động: kiểm soát duy nhất ngăn imagined thành fact bị vượt bởi biến thể rất nhỏ; handoff/map nói "NFC/casefold literal" nhưng không nói ranh giới dấu câu/whitespace nên dễ đọc là mạnh hơn thực tế. Teacher chịu trách nhiệm (OD03) và plan loại trừ paraphrase; mức P2 vì các biến thể trên không phải paraphrase.
- Đề xuất: chuẩn hóa so khớp (NFKC, casefold, bỏ dấu câu và ký tự format, gộp whitespace; kiểm cả hai chiều chứa nhau) và thêm regression cho bốn biến thể; hoặc ghi giới hạn này đúng nguyên văn vào handoff/map N02.

### P2-3 — Không có assertion nào cho hash pin sai ở `resolve_exact` (mutant sống sót)
- File: `backend/src/sketch2life/application/services/knowledge_bundle.py:569-570`. Test: chuỗi `EXACT_BUNDLE_MISMATCH` không xuất hiện trong `backend/tests`; N13/C05/R09 chỉ kiểm tamper storage và `BUNDLE_SUPERSEDED`.
- Trigger: `resolve_exact(principal, bundle_id, 1, "0"*64)` trên version hiện hành. Code thật trả `(ready=False, EXACT_BUNDLE_MISMATCH)` (`probes/probe_b.out`), nhưng mutant M07 (xóa dòng so hash) vẫn pass cả 190 test 07 (`probes/mutants.out`).
- Tác động: "exact id/revision/hash" là hợp đồng trung tâm của resolver mà consumer08 dùng; guard hash của pin không được chứng minh bằng test.
- Đề xuất: test hash sai (và sai bundle_id/version) qua handler thật.

### P3-1 — Thêm các mutant sống sót khác (assertion yếu)
- M01 xóa `AUDIENCE_CHANGED` (`service:261`): audience đổi member nhưng không đổi revision; code thật deny (`probe_b`) nhưng không có test. M04 xóa `SOURCE_RECORD_CHANGED` (`service:270`): metadata nguồn đổi, ref không đổi. M09/M10 xóa kiểm `expected_context_revision`/`expected_audience_revision` của body edit (`service:411-418`): chỉ create có test stale expected. M06 xóa kiểm nội dung receipt (`service:283`).
- Đề xuất: mỗi mutant một test ngắn qua handler.

### P3-2 — Edit theo claims đòi gửi lại toàn bộ danh sách và gán lại attestation cho người sửa (đã tái hiện)
- File: `service:419-437` (`attributed_claim` cho từng item), `domain:315-329`. Test chỉ phủ edit sections: `test_old_teacher_attestation_survives_other_teacher_section_edit`.
- Trigger (`probe_a`, P6): A attest claim ở v2; B gửi lại đúng claim đó (cùng text/reason) → tạo v3 (không phải NO_CONTENT_CHANGE) và `attested_by` đổi từ teacher-a sang teacher-b. Muốn thêm một claim, B buộc phải gửi lại các claim attested của A và nhận trách nhiệm chúng.
- Tác động: provenance của claim không đổi bị ghi cho người khác ở version hiện hành (lịch sử v2 vẫn giữ A). Map P04 chỉ chứng minh trường hợp sections. Cần quyết định có chủ ý và test, hoặc cho DTO sửa theo claim_id.

### P3-3 — Read/resolve bị chặn bởi `mutation_allowed` (`MUTATION_PAUSED`)
- File: `service:226` (trong `_context`, dùng bởi `_current` ở 251-270 cho cả resolve); các test ở `races.py:416, 457-535` khẳng định hành vi này.
- `probe_a` P1: session mutation paused → `read()`/`resolve_exact()` trả `(False, MUTATION_PAUSED)`. Plan §4.4 liệt kê resolve recheck basis/source/policy/audience/purpose; N10 gọi nó là "mutation-only pause". Đây là fail-closed plan chưa nêu cho đường đọc; cần xác nhận chủ ý (hoặc tách guard đọc khỏi guard ghi) và ghi vào handoff.

### P3-4 — Bundle có nguồn bị recall không sửa được bằng edit (câu hỏi chưa xác minh với plan)
- `service:410` chạy `_current(old)` trước mọi edit. `probe_a` P3: sau khi nguồn của v1 bị recall, edit chuyển claim sang nguồn reviewed khác bị `SOURCE_RECALLED` (409); chỉ còn cách tạo bundle mới. Plan §4.4 nói edit "không đổi basis/audience pin; tạo bundle mới nếu cần" nhưng không nói rõ trường hợp recall; handoff không nêu.

### P3-5 — `needs_content_action` không có `action_code`
- `service:481`, `572-575`; `contracts/schemas/knowledge_bundles.py` không ràng buộc readiness↔action_code. `probe_a` P4: bundle có claim nhưng edit chỉ còn story section → record `needs_content_action` với `action_code=None`; resolve báo `NO_ELIGIBLE_SOURCE` dù claim còn nguồn. Thông tin hành động sai/thiếu.

### P3-6 — Hygiene tài liệu và evidence
- `PROJECT_CONTEXT.md`, `SOURCE_REGISTER.md`, `BE2_EXECUTION_TRACKER.md` bị chèn mục mới phía trên tiêu đề H1 (HEAD luôn có H1 ở dòng 1); nhiều câu dùng "FEAT056", "planrev1", "Task06PR15" không có gạch nối/dấu cách nên tìm `FEAT-056` không thấy.
- `git diff --check` (evidence `diff-check`) không quét file untracked. Quét thủ công 56 file untracked: `evidence/notes/PART6_ADAPTERS.md` và `PART8_EXAMPLES.md` mỗi file có 1 dòng CRLF; `approvals/TASK_APPROVAL.md` kết thúc bằng dòng trống thừa. `git diff --check` sẽ báo khi stage.

## 2. Kiểm tra đã chạy và kết quả

Mọi lệnh chạy 2026-10-20 04:50–05:03Z, CWD là worktree, `PYTHONPATH`/`MYPYPATH` = `backend/src` của chính worktree (xác nhận trong `c0_imports.log`: module 07 resolve vào worktree). Output nằm trong `features/FEAT-056-be2-knowledge-script/evidence/local/claude-review-20261020T044951Z/` (ignored). Runner: `run_checks.sh`.

Chạy mới (Claude):

| Check | Kết quả |
|---|---|
| Sáu module 07, `-c backend/pyproject.toml`, basetemp riêng | exit 0; 190 passed, 0 skip (`c1_07.xml` sha256 `9ab986da2ad9ada984bd446e6f4809074b85af6e4d6a7951b5f477975019ce79`) |
| Batch 50 baseline + 6 module 07 theo `selected-files.json`, basetemp riêng | exit 0; 1,515 cases: 1,512 passed, 3 skipped (cùng 3 skip Pillow), 0 fail/error (`c2_batch.xml` sha256 `6a93e5f6be1849075f3bd5de86c5d53c0a08f6d07ff00a740be0601de68a9555`) |
| Ruff (11 file source/test 07) từ `backend/` | exit 0 |
| mypy `--strict` source 07 (10 file), cache mới | exit 0 |
| validate_harness, validate_architecture, validate_skeleton | exit 0 |
| validate_repository_security (chạy riêng) | exit 0 |
| `git diff --check` | exit 0 (không gồm file untracked) |
| Probe in-memory `probe_a.py`, `probe_b.py`, `probe_consumer.py` | kết quả ở mục 1 |
| 20 mutant trên bản sao | 14 killed; 6 sống sót (M01, M04, M06, M07, M09, M10) |
| Bản sao đóng băng 572 file | fail sau khi sửa một file của bản sao |

Kiểm lại receipt cũ (không chạy lại lệnh gốc):
- `source-before.json` = `source-after.json` = `7d204d1feddcd21082f422c6eab5188f9dafe461b035ca31484495f36afe0cf9`; 595 file trong manifest, từng file khớp SHA256/bytes trên đĩa trước và sau khi tôi chạy (`verify_snapshot.log`, `verify_snapshot_after.log`: không missing/mismatch; ngoài manifest chỉ có `__pycache__` bị ignore). Không có `SOURCE_SNAPSHOT_MISMATCH`.
- Hash khớp kỳ vọng: `PLAN_REV1_APPROVED.md` `6de3ed6d…ab36`; `junit.xml` `77b48bfd…9701`; `ACCEPTANCE_MAP_BE207_20261020.json` `98d9d9a5…1466`; `BE207_FINAL_OFFLINE_CHECKS_20261020.json` `c4382d69…bb3a`; `selected-files.json` `daaba054…e430` (đúng 50 baseline + 6 file 07, khớp `OFFLINE_BATCH_PROFILE.json`, 1 loại trừ Pillow).
- JUnit lưu: 1,515 cases, 1,512 pass, 0 fail/error, 3 skip; id và trạng thái từng case trùng JUnit tôi vừa chạy.
- Acceptance map: 42 id khớp bảng plan §9; 279 tham chiếu node, mỗi node có trong JUnit và pass, hàm test tồn tại trong file, `evidence_refs` tồn tại; 0 partial/not_run. Map chỉ là chỉ mục; chất lượng assertion được đánh giá ở mục 1.
- Conformance consumer08: tải `domain/knowledge_video/model.py` tại commit pinned `2d5d9256` vào thư mục review, dựng `VideoPin` thật từ `candidate_video_pin_material`; `VideoPin.digest()` = `candidate_video_pin_digest()` (`probes/probe_consumer.out`). Chứng minh khớp shape/thuật toán với bản pinned; không chứng minh actual08 đã adopt hay giữ lease/fence.

NOT_RUN / giới hạn:
- 3 skip live-app (Pillow) và module `test_lightning_vision_v2_server.py` (import Pillow): NOT_RUN, không đổi thành PASS.
- `external-invariants.json` (356 main, 1,243 shared, 6,112 A17) chỉ có số đếm và một hash tổng, không có baseline để kiểm lại: không kiểm lại.
- Không HTTP/DB/provider/Lightning; wire-parser duplicate-key ngoài `json.loads` của service và hành vi đa tiến trình không kiểm được trong fixture đơn tiến trình.
- Không thêm test vào repo; mọi probe chỉ trong memory hoặc trên bản sao dưới thư mục review.

## 3. Nhận định

**CHANGES_REQUIRED** (sửa nhỏ, không đổi kiến trúc). Lõi implementation (trusted basis, claim-source exact, immutable hash, receipt/replay, coordinator, rollback, consumer fixture) chạy đúng và các test quan trọng đi qua handler thật; tôi không tìm thấy lỗi P0/P1. Cần xử lý trước khi owner nghiệm thu: P2-1 (test phụ thuộc snapshot đóng băng), P2-2 (heuristic imagined/fact yếu hơn mô tả), P2-3 (thiếu assertion hash pin). P3 cần quyết định hoặc ghi vào handoff. Handoff hiện ghi "không còn P1/P2/P3 đã biết"; điều đó không còn đúng sau review này.

Đây là nhận định của reviewer; owner component acceptance và runtime adoption vẫn riêng. Component vẫn NOT_ACCEPTED, card IN_PROGRESS / NOT_DONE.
