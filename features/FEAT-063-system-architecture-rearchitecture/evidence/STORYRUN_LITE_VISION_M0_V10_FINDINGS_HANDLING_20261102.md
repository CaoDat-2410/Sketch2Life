# M0 V10 — Handling các phát hiện C1–C8

Ngày: 2026-11-02. Trạng thái: **CHỈ LẬP KẾ HOẠCH / CHƯA OWNER DUYỆT / CHƯA REVIEW ĐỘC LẬP V10**. Không tạo goal, không triển khai, không migration, không commit/stage/push/merge, không gọi Modal/GPU/provider và không dùng database.

## Baseline và hash

| Tệp | Hash ghim/đối chiếu | Kết quả tự tính |
|---|---|---|
| Prompt owner `CODEX_PROMPT_M0_V10_HANDLE_FINDINGS_20261102.md` | `9DE0931A8C7AAD85C32788533FB50CC246E664840C5D16959C4362803FBC160B` | Khớp. |
| M0 V9 | Prompt ghim `F922C7AEBFBA5A6DACAC5315952C33B94A1B06097719C9B50A7485A83CA5979C` | File hiện tại `C2364A72D4C8E11EDFEE015C2E4F6C2B40F5813A1230EC4265EC363890FD6C9D`; **không khớp**. Hash F922 được tính trước khi tôi chuẩn hóa mixed line endings của V9 sang CRLF ở lượt trước; V10 dùng file hiện tại, không sửa V9. |
| M0 V8 | `75F7C0312E7683EA24BBC079BECF7FC7CF364F107B3AE89552F5546C5DE6A0D3` | Khớp. |
| Review V8 | `B88F014CBF34DBAE879DE63BA2E6D15254BB10F99BDBC8E799BFD4BC5AFF5A8E` | Khớp; NEEDS_REVISION, bốn P2. |
| Roadmap Parent/Teacher | Không có hash ghim trong prompt | `B88188B846C62FF086AB067DB7EC7F9678967847D43BED9598274387E2B93A07`. |
| SRS FEAT-063 v2.3 draft | Không có hash ghim trong prompt | `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC`. |
| DATA_TABLE_REGISTER | Không có hash ghim trong prompt | `0415BBF7FC2477021543C79E72F7011E11A3CE09DBCB92291C5F187907873B8F`. |
| Owner decisions G3/G4 V4 | `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6` | Khớp. |
| StoryRun-lite Decisions V2 draft | `06346124F6851DD401148CE25EC2541B29C2738E0D67A77FE3258666F81CB71B` | Khớp. |

Branch/HEAD đọc được: `feature/feat063-be-foundation` / `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`. Mã A1 được đọc qua `git --no-optional-locks show HEAD:<path>`; không dùng bản A2 đang sửa cục bộ làm bằng chứng.

## Kết quả kiểm C1–C8

| ID | Kết luận | Bằng chứng và xử lý trong V10 |
|---|---|---|
| C1 | **ĐÚNG** | V9 D1 (`plan/STORYRUN_LITE_VISION_M0_V9_DRAFT_20261102.md:33–34`) dừng tại PREPARATION_REVIEW và không có cancel/reanalyze; SRS §6.1.1 (`SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:339`) liệt kê PREPARATION_REVIEW là adult-wait, còn terminal/release được mô tả ở cùng dòng và FR-C-03 (`:436`). V9 D2 giữ một synthetic actor (`:34`), nên run đầu giữ active lock và chặn run tiếp. SRS UC-11 (`:1422–1432`) và route `POST /v1/story-runs/{id}/cancel` (`:1581`) đã có đường hủy; lỗi `ACTIVE_RUN_EXISTS` hướng người dùng tiếp tục/hủy (`:1630`). SRS `AWAITING_RECONCILIATION` là AiJob state (`:343`), không phải StoryRun state. V10 thêm Q2 cho cancel API, operator wrapper hoặc synthetic actors; không chọn thay owner. |
| C2 | **ĐÚNG MỘT PHẦN** | Hypothesis đúng ở cạnh tranh cùng tuple: `tables.py:145–156` unique `(job_id, attempt_id)`; `ledger.py:64–80` `claim()` dùng `ON CONFLICT DO NOTHING`; `invocation_guard.py:75–84` refusal sau claim conflict không gửi. Nhưng claim lock là transaction-scoped advisory lock theo organization (`ledger.py:66–71`), còn `mark_sent()` chỉ CAS từ `CLAIMED` (`ledger.py:82–101`) và không kiểm runtime lease/epoch. Claimant cũ đã CLAIMED vẫn có thể mark SENT sau khi mất process leadership; uniqueness và Story revision CAS không chứng minh zero-send ở ranh giới đó. V10 giữ Q3 mở, trình bày full fence / bỏ fence / fence tối thiểu; nghiêng về fence tối thiểu ở `mark_sent` + CAS. |
| C3 | **ĐÚNG MỘT PHẦN** | Finding rằng full upload-session/receipt/quarantine/purge/migration scope nặng cho demo là đúng: SRS route family có upload session (`SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1562–1566`), còn resumability/part và AV lifecycle nằm ở §24.2 (`:1842–1851`). DTR đã có `core.upload_sessions`/`core.upload_parts` (`DATA_TABLE_REGISTER.md:302–308`); V9 D14/D16/D18 thêm receipts, state race, quarantine/purge và migration owner scope (`V9:46,48,50`). `CoreAssetMetadataModel` đang có `organization_id NOT NULL`, `source_refs`, hash/media metadata (`backend/src/sketch2life/infrastructure/persistence/core_models.py:143–160`); DTR cũng yêu cầu mapping/backfill (`DATA_TABLE_REGISTER.md:251`). Tuy nhiên, nhận định multipart tự nó lệch SRS §21.3 chưa được chứng minh: §21.3 cho phép API upload local. Khác biệt rõ hơn là resumable session ở §24.2 và route `/assets` hiện được mô tả là attach asset ref (`SRS:1572`), nên đổi route đó thành nhận multipart sẽ đổi semantics/API contract. V10 đã sửa ma trận Q1 để nêu đúng các ranh giới này. Số row dữ liệu DB chưa kiểm tra. |
| C4 | **ĐÚNG** | V9 D4 (`V9:36`) đặt 256 MiB subprocess cap nhưng chỉ nói fail readiness nếu OS không enforce; không nêu Windows Job Object. SRS yêu cầu worker cô lập/giới hạn tài nguyên (`SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md:1847,1850–1851`). Static search trong backend không tìm thấy Job Object/`setrlimit` helper. Host của phiên là Windows; đây là risk suy ra từ môi trường, không phải runtime thử. V10 để owner chọn Job Object, bỏ memory cap kèm deviation rõ, hoặc container chỉ khi engine được xác minh. |
| C5 | **ĐÚNG MỘT PHẦN** | Yêu cầu scanner thật `CLEAN` trước model là thật: SRS `:1842,1844`; V9 D15 (`V9:47`). Repo có `ClamAvScanner` (`backend/src/sketch2life/infrastructure/documents/clamav_scanner.py:17–67`) và cấu hình app (`backend/src/sketch2life/interfaces/http/app.py:678–680`). Nhưng tình trạng ClamAV/cổng 3310 hiện tại không được kiểm trong lượt này; prompt nêu báo cáo port lỗi, trong khi báo cáo REV33 ngày 29/10 ghi ClamAV healthy (`evidence/REV33_NON_AI_API_TESTS_AND_LOCAL_MIGRATION_20261029.md:42`). Không thể suy ra trạng thái hiện tại từ hai ghi chép khác thời điểm. V10 đưa scanner thật so với exact synthetic fixture attestation riêng; attestation không được gọi là scanner verdict/CLEAN. |
| C6 | **ĐÚNG (phạm vi shared boundary là thật; seam còn mở)** | Guard hiện nhận `ObservationRequest` và gọi inner observe/finalize (`backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py:180–292`; `observe` tại `:204`); request bắt buộc `render` ở `application/ports/vision_analysis.py:168–181`. Bridge V2 cũng nhận request/render (`legacy_v2.py:124–165,233–274`). Evidence kind/domain validation nằm ở `domain/vision_analysis.py:76–84,689–729`, và OpenAPI literal/validator ở `backend/src/sketch2life/contracts/schemas/analysis_results.py`. Fencing thêm check vào `InvocationLedger.claim/mark_sent` (`ledger.py:64–101`) và Story result head CAS; transport/pilot policy có thể giữ nguyên. Regression cần trên `tests/unit/test_invocation_guard_transport_ga1.py`, `test_vision_analysis_legacy_bridge.py`, `test_vision_analysis_domain.py`, cộng test Story photo adapter: canvas default unchanged, hook trước finalize, evidence không gắn LIVE cho loopback, zero send khi fence từ chối, stale worker không cập nhật run head. V10 chỉ liệt kê seam; D3/Q3 vẫn cần owner chọn. |
| C7 | **ĐÚNG** | V9 hiện khoảng 60 KB và gồm Core/Story receipts, upload state machine, migration, photo bridge, worker fencing, OpenAPI/Bruno và readiness gates (`V9:1–233`). A1 ~4,5 giờ và A2 >một ngày chưa được accept là số liệu do owner cung cấp trong prompt, không phải benchmark độc lập. Scope và history cho thấy một goal gộp sẽ có nhiều cửa review-fix; V10 đề xuất hai goal tuần tự với hardening SRS tách riêng, effort chỉ là khoảng ước lượng. |
| C8 | **ĐÚNG về nội dung; không đồng nghĩa được review accept** | Đối chiếu file V9 hiện tại: (1) hai count views và `part_number` ở `V9:24,143,172`; (2) canonical `story.command_receipts` + decision `command_receipt_id` ở `V9:46,143`; (3) orphan PENDING→FINAL 409, giữ FINAL 202, version CAS ở `V9:50,62,79,143–148`; (4) full CONFIRM/PREPARATION_REVIEW/replay/stale revision/Bruno ở `V9:108,147`. Bốn P2 đã được viết vào draft. Hash V9 khác prompt pin như trên; chưa có kết luận independent review V9 được lưu/nhận trong lượt này, và V10 cũng chưa review. |

## Quyết định owner còn mở

- **Q1:** upload SRS đầy đủ / session tối giản giữ path+DTO / multipart một request. Quyết định đổi số route, Core receipt/DTR/migration và UI resume/poll.
- **Q2:** SRS cancel route / operator script chỉ gọi route đó / nhiều synthetic actor đã seed. Không được đánh dấu UNKNOWN là FAILED hoặc sửa DB trực tiếp.
- **Q3:** giữ full D17 / bỏ D17 và chấp nhận ranh giới yếu hơn / fence tối thiểu ở `mark_sent` và run-head CAS.
- **Q4:** Windows Job Object hay bỏ hard memory cap với deviation; scanner thật hay exact synthetic fixture attestation riêng.
- **Q5:** một goal gộp / hai goal tuần tự / ba mốc. V10 nghiêng hai goal tuần tự; chưa tạo goal.
- **Q6:** cập nhật D1–D18 phụ thuộc Q1–Q5, đặc biệt actor/run reset, D3/D5/D8 asset, D9/D11 UNKNOWN/AiJob, D10/D14 API+receipts, D12/D17 worker, D15/D16/D18 scanner/upload; V4 D9 tối đa hai run-first calls chỉ áp dụng StoryRun-lite sau khi owner xác nhận.

## Thay đổi trong V10 so với V9

1. Thêm bảng mức chứng cứ smoke V2 §1.1; phân biệt rõ smoke 01/11 tự thuật và `/health` riêng, không chứng minh A1 live.
2. Xác định PREPARATION_REVIEW giữ active lock; ánh xạ UNKNOWN thành AiJob state đúng SRS và trình bày các đường thoát owner chọn.
3. Thêm ma trận upload, Windows decode/scanner, D17 fence, các thay đổi shared A1 cụ thể, và milestone tuần tự với acceptance/ước lượng.
4. Ghi kết quả fact-check C1–C8 và hash mismatch V9 trong hồ sơ này; không sửa V1–V9/SRS/DTR.

## Chưa xác minh trong phạm vi này

- ClamAV/port 3310 đang sống hay không; không dò port/service.
- Dữ liệu thật trong PostgreSQL, trạng thái migration/heads, số hàng `core_asset_metadata`; không mở DB/A2 và không đọc `local_pg_*`.
- Việc decoder Job Object có hoạt động ở môi trường chạy mục tiêu; không chạy code.
- Modal live/cold-start/token/model readiness, chất lượng nhận diện và ảnh fixture thực tế.
- UI consumer có chấp nhận DTO mới; không có UI approval/implementation review.
- Ước lượng ngày công, sự kiện network/process crash và khả năng cleanup; không chạy test.
- V9 hash pin mismatch đã ghi; V9 independent review chưa có kết luận nhận được.

Trong lượt này được tạo chỉ M0 V10 draft và file handling này. Chưa có owner approval, chưa có independent review V10, chưa mở goal.
