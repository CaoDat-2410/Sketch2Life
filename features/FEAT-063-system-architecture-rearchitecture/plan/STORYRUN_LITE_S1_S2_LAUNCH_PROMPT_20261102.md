# Prompt giao một goal S1 → S2

Bạn là phiên triển khai StoryRun-lite trong repo `D:\GitHub\Sketch2Life`. Hãy chạy **một goal tổng gồm S1 rồi S2 liên tục** theo file plan dưới đây, tự xử lý các lỗi trong phạm vi được giao và không yêu cầu tôi duyệt lại các quyết định đã ghi. Tôi cần BE demo để người khác ghép UI.

**Nguồn ghim — đọc nguyên file và tự tính hash trước khi làm:**

- `features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_S1_S2_MASTER_GOAL_20261102.md`
  SHA-256 `C5E8B15839FA3470596DAC4B964450BD56428D481EA1A78B8AEC70B2E6A02B42`.
- `features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_VISION_M0_V12_FINAL_DRAFT_20261102.md`
  SHA-256 `D0560C4B7821EA76A50780D00161DE1D1AC9917168B9C975547077C457FB448B`; §10 ghi phạm vi ảnh hiện hành.
- `features/FEAT-063-system-architecture-rearchitecture/plan/STORYRUN_LITE_GOAL_1_PLAN_20261102.md`
  SHA-256 `0447E054079CA2FF3595773DE4C7A3B77EE41FF28E23831A47103D93FC7B083A`.
- `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md`
  SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.

Hash lệch thì dừng phần phụ thuộc, báo giá trị đo được. Đọc AGENTS.md, harness, FEAT-063 context/decisions/source register/approval, SRS/DTR và báo cáo review V11 theo plan. Baseline `feature/feat063-be-foundation` / HEAD `a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58`; ghi index và hash các thay đổi local trước khi làm. Không ghi đè hoặc dọn các file A2; không dùng hay dọn database A2.

**Tôi duyệt phạm vi S1 + S2 trong plan goal tổng đã ghim**, bao gồm soạn OpenAPI/Bruno, source/test/migration, amendment DTR cần thiết, kiểm môi trường và test theo plan; bạn được tạo một plan triển khai bao phủ cả hai chặng, tự tính hash, và **append một approval record** ghi chính xác chỉ thị này, phạm vi, hash trước khi sửa source/migration theo AGENTS/harness. Được tự xác định danh sách file cụ thể trong phạm vi đó và tự sửa test/lint/validator do thay đổi của goal gây ra; không hỏi lại tôi cho từng file hoặc từng expectation liên quan. Không xóa/ghi đè file local có sẵn; dùng worktree sạch hoặc cơ chế cô lập phù hợp nếu cần. M0 V12 không được gọi là đã review ACCEPTED.

Chọn ảnh **synthetic khác nhau mỗi lần** từ JPEG/PNG/WebP; không ghim một ảnh duy nhất. Goal 1: OpenAPI/Bruno trước, upload/quarantine/scanner/admission/normalization, StoryRun, Vision giả, CONFIRM/cancel. Goal 2: photo bridge A1, guard/ledger/transport, loopback, regression canvas, Bruno flow tổng và readiness. Sau khi S1 đạt các điều kiện kỹ thuật cần thiết, **tự chuyển sang S2**, không mở thêm review M0 hoặc chờ tôi duyệt giữa chặng. Nếu scanner/PG/OS worker limit chưa sẵn, làm tiếp các phần độc lập; ghi NOT VERIFIED/BLOCKED đúng phần và hướng khắc phục. Không giả CLEAN, không tắt giới hạn an toàn để ép pass.

Tôi cho phép kiểm và chạy test cần thiết trên HTTP loopback và **database PostgreSQL disposable riêng** do phiên tạo/kiểm chứng quyền sở hữu cho goal này, chỉ với dữ liệu synthetic/test. Chỉ cleanup tài nguyên đã chứng minh thuộc goal; không DROP/TRUNCATE database người dùng, không đụng database A2. Dependency/service dùng môi trường isolated của repo nếu có thể; không cài/thay đổi cấu hình hệ thống toàn cục. Không ghi secret vào log/evidence.

Không gọi Modal/GPU/provider hoặc mạng ngoài để inference; không dùng dữ liệu trẻ thật; không làm UI, Teacher, voice, story/video, A2/B1/B2; không stage/commit/push/merge/deploy. Modal live sẽ có lệnh riêng sau readiness. Giữ checkpoint S1/S2 và evidence trong FEAT-063; khi hết ngữ cảnh hoặc bị chặn, ghi chính xác bước resume. Kết thúc báo file đã sửa, kết quả thật, rủi ro, tình trạng từng chặng và hướng dẫn dùng Bruno; chỉ nói `XONG-CHƯA REVIEW IMPLEMENTATION` nếu acceptance thật sự đạt.
