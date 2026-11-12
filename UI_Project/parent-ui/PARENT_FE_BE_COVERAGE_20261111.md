# Đối chiếu Parent UI với FE và BE trên Sketch2Life

Rà soát ngày 2026-11-11. Tài liệu này cập nhật phạm vi FE + BE theo yêu cầu mới; `PARENT_FLOW_AUDIT.md` là kết quả của lượt rà soát BE trước đó.

## Nguồn và mức tin cậy

| Nguồn | Commit đã đọc | Vai trò |
|---|---|---|
| `main` | `1c2c6d35` (24-08) | Cũ; không dùng để kết luận flow hiện hành. |
| `dev` | `1431ef81` (06-11) | Baseline tích hợp được xuất bản, còn thiếu nhiều Parent target routes. |
| `docs/feat063-diagram-readiness-20261107` | `d77ad86c` (09-11) | SRS v2.7-draft Rev60, working baseline chưa sign-off. |
| `feature/feat063-be-foundation` | `4b7f07cc` (09-11) | BE Teacher/StoryRun-lite foundation, chưa merge vào `dev`. |
| `codex/feat063-parent-teacher-modal-ui` | `800c8e9f` (10-11) | Parent Android React Native, Firebase auth, Parent AI pilot và BE lesson/auth routers. |
| `codex/fe-ui-web-remediation` / `feature/fe-ui-full-remediation` | `c4dd9aa3` (10-11) | FE web Parent/Teacher/Admin prototype, Parent lesson invitation và nhiều màn tham khảo. |
| `FE/UI-Parent`, `FE_UI_Project` | `b29a9f54` (01-11), `c384dcc6` (09-11) | Nhánh FE cũ hoặc vai trò khác; đối chiếu touchpoint, không coi là contract đã merge. |

Đã kiểm tra remote refs của repository và đọc source theo commit. Một nhánh mới hơn không tự động trở thành chức năng production hoặc API đã merge vào `dev`. Trạng thái runtime chỉ ghi là đã kiểm chứng khi evidence của nhánh có kết quả tương ứng.

## Những phần Parent có căn cứ và trạng thái trong UI này

| Chức năng Parent | Căn cứ FE/BE/SRS | Bản xem trước ở `parent-ui` | Tích hợp thực |
|---|---|---|---|
| Đăng ký/đăng nhập, quên và đổi mật khẩu | Rev63 auth; Parent Android `ParentAuthScreen`; Firebase recovery/change | Có màn đăng ký, đăng nhập, khôi phục và đổi mật khẩu; đăng ký/đổi mật khẩu kiểm tra 6–128 ký tự | Chưa nối Firebase ở workspace này. Nhánh 10-11 đã có auth pilot; email verification còn mở. |
| Hồ sơ trẻ, chọn đúng một trẻ, xem/sửa thông tin | FR-P-01/02; screen map P01/P02; FE web Parent profile | Có danh sách, chi tiết, thêm/sửa, ảnh, tuổi, biệt danh, nhu cầu hỗ trợ; thêm sở thích, quan sát, thành tích và trải nghiệm ngoài app; xóa dữ liệu mẫu có xác nhận | Dữ liệu phiên trình duyệt; API profile target, revision bất biến và trạng thái purge chưa được xác nhận end-to-end. |
| Dùng tuổi làm ngữ cảnh AI | SRS tối thiểu hóa dữ liệu | Mặc định tắt, ba mẹ xác nhận trong từng run; chi tiết hồ sơ giải thích quyền riêng tư | Chưa truyền API; không có quyền đồng ý rộng cho ảnh/biệt danh/nhu cầu hỗ trợ. |
| Lời mời nhóm phụ huynh | `lesson_library.py`: GET danh sách, POST accept | Màn lời mời nhóm, trạng thái chờ/đã tham gia; không có nút từ chối vì BE không có route đó | Dữ liệu mẫu; không tự chia sẻ hồ sơ trẻ. |
| Lời mời giáo án | `lesson_library.py`: GET, POST accept/decline | Nhận/từ chối; giáo án lời mời chỉ hiện trong thư viện và picker sau khi nhận | Dữ liệu mẫu; cần nối auth + API và trạng thái loading/empty/error. |
| Thư viện, chi tiết, tải nội dung giáo án | `lesson_library.py`: list/detail/download | Có thư viện, chi tiết, TXT xuất từ fixture; lịch sử giáo án và feedback | Chưa nối BE; không tải video hoặc nội dung trẻ. |
| Chọn lesson version hoặc không preset | FR-P-01..11, Rev60 | Có picker trước khi tạo; không chọn activity trước video; lesson activities mở ở trang riêng sau VIDEO_READY | Fixture; exact version/hash pin cần BE xác nhận. |
| Tranh, chữ/voice, transcript, chủ thể VLM | Rev60; Parent Android pilot và Parent AI routes | Có capture/upload, ghi âm, sửa transcript, xác nhận/sửa chủ thể | Parent AI pilot mới PARTIAL; drawing-understanding 504 trong evidence 10-11. |
| Ngữ cảnh, script/storyboard, 3 lần viết lại | Rev60 | Có các cổng xác nhận và giới hạn trong UI | Chưa nối pipeline durable hoặc script hash thật. |
| Job, safety, video, 2 lần tạo lại, hoàn tất/hủy | Rev60 | Có các màn và giới hạn mô phỏng; chỉ hiện activity của lesson sau trạng thái ready | Chưa có E2E video được chứng minh; art/video trong UI là minh họa. |
| Xem riêng tư và phụ đề | NFR-20; FE web Parent có captions | Có nút CC bật/tắt và khung 16:9 toàn màn hình trên bản minh họa; không có tải/xuất video | Chưa có playback token hoặc caption track thật. |
| Đánh giá sau video | FE web P08c session feedback | Sau VIDEO_READY hoặc từ lịch sử, có 1–5 sao, nhãn nhanh, ghi chú và bỏ qua; lưu trong phiên xem trước, tách khỏi feedback giáo án | FE web chỉ cập nhật React mock state; chưa tìm được API session feedback trong BE/SRS Rev60. |
| Chia sẻ hồ sơ với giáo viên, thu hồi; giáo án được giao, phản hồi | SRS Parent/Teacher touchpoints; FE web Parent | Có UI chọn giáo viên mẫu theo ID, lịch sử giao bài và feedback gắn với giáo án; không ghép theo tên nhập tự do | Chưa nối danh bạ định danh/permission thật; field allowlist, consent scope và expiry vẫn cần owner chốt. Không cấp quyền thật. |
| Quota/gói sử dụng, notification | SRS admission/quota; FE web | Có màn giải thích và thông báo mẫu; không bịa số lượt/giá mua | Cần API/owner policy. |

## Những điều FE/BE mới chưa chứng minh

- Nhánh Parent Android ngày 10-11 đã chạy được signup/role resolution và optional sketch guide qua UI. Evidence `EV-063-74` ghi **PARTIAL**: drawing-understanding trả HTTP 504 do JSON bị cắt; story bị chặn, không gọi video. Bản nâng output cap từ 256 lên 512 chưa được xác nhận lại qua Parent UI.
- Parent Android pilot hiện chỉ có luồng guide/drawing/subject/story ngắn; hồ sơ trẻ, version pin, transcript, context, durable job, safety, video, lesson activity, quota và feedback chưa được chứng minh trong app native đó. Web Parent branch là prototype tham khảo và có một số tương tác mock.
- Rev63 xác nhận backend đăng ký Parent và `/me`, còn bước email verification/invitation delivery của UC-13 chưa hoàn tất. `dev` vẫn ở SHA 06-11; không được coi mã 10-11 là đã tích hợp vào `dev`.
- Lesson Library có route Parent list/invite/detail/download, nhưng workspace UI này không có Firebase session, API client hay BE chạy cùng. Toàn bộ màn mới ở đây dùng fixture và trạng thái trong bộ nhớ.
- Activity khi run không dùng preset, hồ sơ share field allowlist/expiry, lifecycle archive/delete của trẻ, quota/giá, lịch sử giáo án và trạng thái phát video là các policy/gate chưa chốt. UI không tự đặt chính sách thay owner.

## Kết quả kiểm tra bản xem trước

- TypeScript `tsc --noEmit`: đạt.
- `npm run build`: đạt.
- Đã mở bản chạy ở `http://127.0.0.1:4175/`, kiểm tra trực tiếp: lời mời giáo án accept làm giáo án xuất hiện trong thư viện; nhóm từ pending sang accepted; mở chi tiết trẻ; form đổi mật khẩu báo lỗi khi trống; nút CC hiển thị trên màn chuyện; form mời giáo viên chọn từ danh sách mẫu thay vì nhập tên tự do.
- Lượt tiếp 12-11: chạy xuyên luồng qua màn hoạt động và feedback, kiểm chứng lưu sao/nhãn/ghi chú trong lịch sử; hủy run không tạo story hoàn tất; truy cập hoạt động của story cũ không đóng active run khác. `tsc --noEmit` và `npm run build` đạt. Xem bảng chi tiết ở `PARENT_COVERAGE_RECHECK_20261111.md`.
- Ảnh kiểm tra: `parent-lesson-invitation-preview.png`, `parent-sharing-preview.png`.
- Đây là kiểm tra UI chạy trong trình duyệt ở kích thước điện thoại. Chưa phải nghiệm thu Android native, API, database, Firebase, Modal hoặc E2E Parent video.

## Tài liệu gốc

- SRS Rev60: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` tại `d77ad86c`.
- Auth Rev63, evidence Rev64: `features/FEAT-063-system-architecture-rearchitecture/artifacts/AUTH_ROLE_API_CONTRACT_REV63_20261110.md` và `evidence/EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110.md` tại `800c8e9f`.
- Native Parent: `apps/mobile/src/features/auth/ParentAuthScreen.tsx`, `apps/mobile/src/features/parent/ParentWorkflowScreen.tsx` tại `800c8e9f`.
- BE Parent lesson: `backend/src/sketch2life/interfaces/http/routers/lesson_library.py` tại `800c8e9f`.
- FE web Parent: `apps/parent-ui/src/pages/ParentScreens.tsx`, `apps/parent-ui/src/context/ParentContext.tsx` tại `c4dd9aa3`.
