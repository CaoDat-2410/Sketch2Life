# EV-015-01 — Rà soát branch và mức sẵn sàng tích hợp

- Thời điểm: 2026-09-05, Asia/Saigon.
- Reviewer: Codex, theo yêu cầu trực tiếp của chủ dự án.
- Trạng thái review: DONE. Triển khai integration: NOT_STARTED / NOT_APPROVED.
- Nguồn: branch đã fetch, source/plan/approval/evidence tại commit dưới đây; ADR-0006; docs/architecture/CONTRACTS_AND_INTEGRATION.md; docs/context/SOURCE_REGISTER.md. Không đọc lại handbook gốc hoặc dùng nội dung ngoài repo để thay đổi quyết định.
- Phạm vi: review, test sẵn có và tài liệu; không sửa code, không merge/commit/push, không gọi GPU/provider, không đổi kiến trúc đã duyệt.

## 1. Inventory và quan hệ branch

Danh sách SHA đầy đủ và thời gian commit: ../raw/BRANCHES.txt.

| Thành viên/nhánh | Commit | Kết luận |
|---|---|---|
| main / origin/main | 1c2c6d3 | Foundation; chưa chứa kết quả 4 workstream |
| P1 local plan/person-1-montessori-sprint-1 | 2d61528 | Đã nằm trong nhánh offline-console |
| P1 plan/person-1-montessori-golden-hardening (local + origin) | f70f3c9 | Đã nằm trong offline-console |
| P1 plan/person-1-montessori-offline-console (local + origin) | b3f397c | Chọn làm đầu vào review P1 |
| P2 origin/plan/person-2-multimodal-input-validation | 6861b17 | Đã nằm trong Qwen branch |
| P2 origin/plan/person-2-asr-research | 6a3890c | Đã nằm trong Qwen branch |
| P2 origin/plan/person-2-qwen3-vl-structured-understanding | f3014e5 | Chọn làm đầu vào review P2 |
| P2 local fix/person-2-t1-hardening-t2-t3 | 1419f75 | Nhánh khác biệt; git cherry báo commit chưa có patch tương đương trên Qwen branch. Không bỏ hoặc merge mù |
| P3 origin/plan/person-3-art-animation-poc | 68aceeb | Chọn làm đầu vào review P3 |
| P4 origin/plan/person-4-learning-explanation-poc | f0dd622 | Chọn làm đầu vào review P4 |

Đã dùng git merge-base --is-ancestor để xác nhận các quan hệ trên. git cherry chỉ xác nhận patch khác biệt, không chứng minh mọi hành vi hardening đều thiếu ở nhánh remote. Cần đối chiếu các yêu cầu PCM/PNG/bounded reads/provenance với implementation remote trước khi giữ/cherry-pick bất kỳ phần nào của 1419f75, tránh tạo hai bộ adapter/contract song song.

Đã dùng git merge-tree --write-tree --name-only trên 6 cặp tip chính; thao tác tạo cây thử trong object database, không cập nhật branch/index/working tree. P1/P2 conflict tại docs/context/SOURCE_REGISTER.md; 5 cặp còn lại exit 0. Log: ../raw/MERGE_PREFLIGHT.txt. Đây là preflight từng cặp, chưa chứng minh một lần ghép đủ 4 nhánh sẽ sạch hoặc tương thích ngữ nghĩa. Khi giải conflict phải giữ source entries và ranh giới thẩm quyền của cả hai nhánh, không chọn toàn bộ ours/theirs.

## 2. Kết quả thực chứng

Môi trường: Windows, Python 3.12.14 / pytest 8.4.2 / Pydantic 2.13.4 từ backend/.venv; Node 24.18.1; pnpm 11.19.0. Mỗi workstream chạy trong detached worktree dưới tmp/. Những kết quả P1/P2 tái sử dụng từ review cùng ngày ở đúng SHA không đổi sau fetch; không chạy lại để tạo số đo dư thừa.

| Phần | Kết quả | Giới hạn |
|---|---|---|
| P1 b3f397c | 3 validator PASS: domain 100 activities/20 objectives/24 cases; Golden 20 activities/74 cases; console 74/74 parity và 4 scenarios | Offline, EXPLICIT_ACTIVITY_ONLY; production_eligible=false |
| P2 f3014e5 | 475 passed, 5 skipped; Ruff và repository security PASS | Fake/offline tests; skip có lý do attempt-zero row, không phải GPU success |
| P3 68aceeb | Typecheck PASS; 6/6 Vitest PASS; Vite demo build PASS | Chưa playback browser trực quan hoặc đo Android WebView/FPS/memory trong review này |
| P4 f0dd622 | 39 passed, 1 failed, 1 skipped; 4 demo exit 0 với CACHE_HIT/GENERATED/FALLBACK/BLOCK; repository security PASS | Fail so sánh đường dẫn POSIX trên Windows; skip FFmpeg/ffprobe chưa có; demos dùng mock |

P1/P2 evidence: features/FEAT-003-multimodal-understanding/evidence/notes/P2_P1_REVIEW_20260905.md và raw/P2_TEST_20260905_RUN2.txt. Lần test P2 đầu gặp quyền TEMP Windows, lần dùng basetemp mới trong workspace pass không sửa code.

P3 commands tại root worktree: pnpm install --frozen-lockfile --ignore-scripts --filter @sketch2life/art-renderer; pnpm --filter @sketch2life/art-renderer typecheck; test; build:demo. Lần install --offline ban đầu thiếu vite trong cache; đã tải dependency đúng lockfile để hoàn tất. Logs: ../raw/P3_DEPENDENCIES.txt, P3_TYPECHECK.txt, P3_TEST.txt, P3_BUILD.txt. Lockfile không đổi; build tạm đã xóa sau kiểm tra.

P4 command tại root worktree với PYTHONPATH=features/FEAT-005-backend-experience/src: python -m pytest features/FEAT-005-backend-experience/tests -ra -q -p no:cacheprovider --basetemp=<fresh workspace tmp>. Log ../raw/P4_TEST.txt. Failed: test_wan_generator.py::WanGeneratorTest::test_build_command_uses_official_ti2v_flags; expected /opt/Wan2.2/generate.py nhưng Path trên Windows tạo backslash. Đây là vấn đề portability của test/config được quan sát, chưa chứng minh Wan inference bị hỏng. Skipped: test_frame_sampler_integration.py thiếu ffmpeg và ffprobe.

P4 demos: python features/FEAT-005-backend-experience/scripts/run_demo.py --case cache-hit|cache-miss|fallback|block (4 lần riêng); log ../raw/P4_DEMOS.txt. GENERATED với provider=mock không chứng minh có video thật hoặc model validation thật. Các log mock có nhãn validator=qwen3-vl vẫn chỉ là policy dùng MockQwen3VLValidator.

## 3. Các khoảng trống cần xử lý

### G1 — Contract giữa P1 và P4 chưa khớp (blocking cho kết nối trực tiếp)

P1 data/activity-catalog/mvp/learning-objectives.v1.json dùng ví dụ OBJ_MOVEMENT_COORDINATION, version số 1. P4 LearningObjective trong src/learning_video/schemas.py chỉ nhận objective_id theo regex chữ thường và version dạng v1. Đây còn là khác biệt ý nghĩa: objective fixture butterfly_proboscis của P4 chưa có mapping chứng minh tương ứng catalog P1. Không tự lowercase ID để coi là đã nối.

Cần một reference canonical có ID/version và mapping được review; activity_ref cũng phải được khóa cùng objective_ref. PipelineResult P4 chưa mang activity/session/version envelope. Không đổi PROVISIONAL_OWNER_REVIEWED của P1 thành REVIEWED/production-eligible chỉ vì P4 có asset schema mang nhãn REVIEWED.

### G2 — P2 chưa xuất meaning thống nhất cho downstream

Có ASR V1, vision V1/V2 và adapter/benchmark nghiên cứu; chưa thấy runtime fusion RawUnderstandingResult hoặc T5 pipeline hoàn chỉnh. Gate A confirmation/canonical meaning chưa triển khai. Observation label/entity không phải activity/readiness và không cung cấp mask/crop để renderer dùng trực tiếp. P2 B3 mapping diagnostics là mapping model output vào vision schema, không phải mapping vào Montessori.

Context P2 báo B2 Lightning từng trả VISION_SCHEMA_INVALID/OUTPUT_MAPPING_FAILED; chưa xác minh lại GPU ở review này. Source có B3 diagnostics nhưng context/decisions vẫn ghi B3-B5 chưa thực thi. Cần đồng bộ execution evidence trước tuyên bố real-model readiness.

### G3 — P3 còn thiếu compiler và bridge runtime tích hợp

ArtAnimationPlan có planId/planVersion, objects, asset URI/provenance và Motion DSL. P2 vision observations chưa tạo được ArtObject asset refs hoặc Motion plan. Cần experience compiler và adapter artifact reference -> asset có quyền truy cập. Slice đầu dùng WHOLE_DRAWING + DRAW_REVEAL để không phụ thuộc segmentation chưa có.

Renderer phát PLAYBACK_STARTED/COMPLETED/FAILED/FALLBACK_APPLIED nhưng mobile messages.ts hiện chỉ có RENDERER_READY/RENDERER_ERROR. Cùng protocol string 1 không có nghĩa hai bên đã đồng bộ. Cần bridge command/event schema chung, session/plan/instance correlation và quy tắc xử lý completion cũ/trùng. sourceSha256 hiện optional và loader chuyển metadata; cần test xác minh bytes/hash và preservation riêng, không chỉ kiểm tra field được truyền tiếp.

### G4 — P4 có đường demo nhưng chưa đủ failure/identity contract cho runtime

Static review pipeline.py: gọi generator.generate, sampler.sample và validator.validate trực tiếp, không bắt WanGenerationError/timeout để chuyển sang typed fallback. Wan adapter có thể raise WanGenerationError. Fallback hiện chủ yếu xử lý kết quả validation; chưa đủ cơ sở nói provider crash/timeout luôn fallback.

Pipeline cũng chưa kiểm tra objective được truyền vào có cùng ID/version với brief/generated artifact; result có thể mang outer objective khác nested artifact khi caller truyền lệch. Đây là nhận xét source, chưa viết hoặc chạy test mới để tái hiện. Cần test mismatch trước tích hợp.

Wan artifact_id/output filename hiện dựa trên objective ID/version, chưa phân biệt nhiều job/cấu hình cùng objective; cần immutable artifact/job identity để không ghi đè kết quả đồng thời. P4 content validator là protocol + mock và policy mapping; chưa thấy concrete real Qwen VisualContentModel trong nhánh. Dùng cùng tên Qwen với P2 không tạo ra adapter tương thích: P2 hiểu tranh, P4 kiểm tra frames theo objective.

### G5 — Chưa có application điều phối chung

Thiếu session/job state machine, Gate A/B commands, compiler/composer, authorization/artifact access, persistence/queue adapters, Android flow, Activity Bridge và feedback runtime. Cần application layer gọi các port; không nối trực tiếp UI -> model hoặc P1 -> database của P4. Media BLOCK không được tự hiểu thành xóa hoạt động đã duyệt; policy quyết định safe fallback hoặc pause/request review và luôn bảo toàn handoff hợp lệ.

### G6 — Hồ sơ harness cần đồng bộ trước implementation

P4 TASK_APPROVAL ghi APPROVED revision 2, nhưng CONTEXT/PLAN vẫn AWAITING_APPROVAL và Implementation status NOT_STARTED. Evidence index còn danh sách planned, chưa có run report trong branch. Cần owner cập nhật trạng thái, acceptance và evidence đúng việc thực tế đã làm; reviewer này không tự phê duyệt lại hoặc sửa lịch sử nhánh P4.

P3 có validation note nhưng evidence index tổng quát, chưa có browser/device measurements. Baseline main vẫn mô tả foundation; không dùng status main để suy ra các branch chưa có code. Các phát hiện của review được ghi ở FEAT-015, không ghi đè status của workstream.

## 4. Kết luận readiness

Có đủ 4 đầu vào workstream để bắt đầu review/freeze contract và lên kế hoạch một vertical slice dùng fixture. Chưa đủ điều kiện tuyên bố luồng sản phẩm end-to-end chạy được. Ưu tiên contract/identity, fusion/Gates và failure semantics trước infrastructure hoặc model tối ưu. Kế hoạch nối và test nằm trong plan/INTEGRATION_PROPOSAL.md và plan/TEST_STRATEGY.md; đều PROPOSED, chưa có approval triển khai.

## Final documentation verification

- python tools/validate_harness.py --feature features/FEAT-015-integration-readiness-review: HARNESS_VALID.
- python tools/validate_repository_security.py: REPOSITORY_SECURITY_VALID, 460 publishable files scanned.
- git diff --check: no whitespace errors (only Git CRLF/LF normalization notices).
- P3/P4 detached worktrees: git status --short empty after removing only the generated P3 demo build.
- Initial harness invocation omitted the features/ prefix and was rejected; corrected command above passed. Initial security check rejected the absolute workspace prefix in Vitest output; a sanitized derivative is now retained, with original preserved in ignored local tmp as documented in the evidence index.
- Existing FEAT-003 changes are retained from the previous user-requested review. This task adds FEAT-015 documentation and a dated project-context snapshot only.
