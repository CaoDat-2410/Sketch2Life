# Rà soát lại toàn bộ Parent UI — 2026-11-11; kiểm chứng tiếp 2026-11-12

## Phạm vi và thứ tự nguồn

Đã đối chiếu prototype `D:/Capstone Project/parent-ui` với FE web Parent tại commit `c4dd9aa3`, Parent Android pilot và BE lesson/auth tại `800c8e9f`, nhánh tích hợp `dev` tại `1431ef81`, SRS FEAT-063 v2.7-draft Rev60 tại `d77ad86c` và Screen Navigation Map Rev57. Các màn P01–P14 dưới đây là tên màn của **FE web mẫu**; chúng không phải ID P-01–P-12 của navigation map.

**Lưu ý phiên bản:** file `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS_V2.2_PRESERVED_20261028.md` trong workspace đã cũ. Bản đó yêu cầu Parent chọn hoạt động trước video. Rev60 tại `d77ad86c` nói rõ Parent **không chọn hoạt động trước video** (BR-15, FR-P-05, UC-02); chỉ xem hoạt động của lesson version đã pin sau VIDEO_READY. Với run không preset, query catalog hay không vẫn `OPEN-OWNER` §31.10(13). Không dùng file v2.2 để đảo mainflow.

## Đối chiếu từng màn FE mẫu

| Màn FE mẫu | Prototype hiện tại | Thiếu hoặc chưa chứng minh |
|---|---|---|
| P01 Trang chủ / thư viện giáo án | Có home, thư viện, lời mời giáo án/nhóm; lesson picker tùy chọn | Dữ liệu fixture; chưa có Firebase principal, list/detail theo server, pagination/loading/denied. |
| P02 Chi tiết giáo án | Có chi tiết, vật liệu/cách làm/ghi chú, tải TXT fixture | Chưa dùng exact published version/hash và quyền download từ BE; xuất TXT chỉ là bản minh họa. |
| P03 Gợi ý nét vẽ | Có màn riêng, bỏ qua được, không dùng dữ liệu trẻ | Kết quả hiện là **chữ mẫu**, chưa phải line art 3–5 bước đã qua schema/safety/AV, provenance/expiry; chưa có các trạng thái limit/timeout/retry. |
| P04 Tranh và chủ thể | Có camera/gallery UI, sửa chủ thể, revision label | Chưa upload-resume/hash/AV; VLM và revision server chưa nối; ảnh mẫu không chứng minh AI thật. |
| P05 Ý tưởng và audio | Có chữ, ghi âm/tệp ≤20 MB, transcript sửa/xác nhận | Whisper/ASR chưa nối; transcript ban đầu là UI mẫu; độ dài tệp nhập và upload-resume chưa xác nhận trên Android. |
| P06 Kịch bản | Có xem, tối đa 3 yêu cầu viết lại, 5 scene minh họa, cổng duyệt | Không có story/storyboard revision/hash thực; gợi ý viết lại chỉ cập nhật trạng thái mẫu, không phải AI output mới. |
| P07 Job video | Có màn chờ và quay về home | Chưa có video admission, queue/stage từ API, lỗi/retry/denied/reconcile, 6 giờ deadline và 144/168 giờ adult-wait. |
| P08 Video | Có ảnh minh họa 16:9, CC toggle, khung toàn màn hình, tạo lại tối đa 2 | **Chưa phát video thật**, chưa có phụ đề/âm thanh thật, token ngắn hạn và safety gate server. Không thể coi hình minh họa là VIDEO_READY thật. |
| P08b Hoạt động sau video | Có trang riêng với vật liệu, cách làm, lưu ý và chế độ chữ lớn; chỉ hiện nếu đã pin lesson | Exact version/hash và quyền catalog cần API. Với no-preset, chính sách truy vấn catalog vẫn mở; prototype không tự thêm hoạt động. |
| P08c Cảm nhận phiên | Đã thêm 1–5 sao, nhãn nhanh, ghi chú, lưu/bỏ qua; hiển thị lại ở lịch sử | Chỉ lưu trong React memory; **không tìm thấy API session feedback** trong SRS/BE. Khác `FR-PL-22` là feedback giáo án. |
| P09 Lịch sử | Có danh sách, lọc tất cả/chờ/đã hoàn tất, chi tiết và xóa mẫu | Chưa có phân loại CLOSED/ABANDONED/FAILED, phân trang, lịch sử server, retention và purge progress. |
| P10 Hồ sơ trẻ | Có danh sách/chi tiết/thêm/sửa/xóa mẫu; sở thích/quan sát/thành tích/trải nghiệm ngoài app; chọn context từng run | Chưa có revision bất biến, nguồn/provenance cho thông tin nhập, archive/restore mẫu như FE web, delete lifecycle server và trạng thái purge. |
| P11 Đăng nhập | Có form login và signup với kiểm tra nhập liệu/animation | Chưa xác thực Firebase, role từ BE, session/refresh và email verification. |
| P12 Lượt video | Có màn quota không bịa số dư/giá | Chưa có balance/admission/receipts, top-up policy và thanh toán; quyền mua/gói vẫn owner-open. |
| P13 Cài đặt | Có thông báo mẫu, quyền riêng tư, đổi mật khẩu form, bật/tắt thông báo phiên xem trước | Chưa có sửa tên/email tài khoản, phụ đề mặc định, auto landscape, dark mode theo FE mẫu; không có API settings hay push endpoint thật. Đây là tiện ích FE mẫu, không được coi là contract BE. |
| P14 Khôi phục mật khẩu | Có màn và form | Chưa gửi link Firebase/Email; email verification/retry/expired-link chưa có. |

## Mainflow SRS Rev60 và tình trạng thực tế

| Cổng yêu cầu | Trạng thái UX | Điều kiện trước khi ghép BE |
|---|---|---|
| Một trẻ thuộc Parent, một active run | Có chọn trẻ và chặn mở run thứ hai trong memory | Ownership/unique lock do server kiểm tra; restore sau restart. |
| Optional lesson version | Có picker; không bắt chọn activity trước video | Pin `LessonVersionRef` exact version/hash, quyền đọc, revoked/stale. |
| Camera/gallery, chữ/audio, ASR | Có thao tác mẫu và sửa transcript | Upload session resume/hash/AV, ASR result/revision, Android permission và background recovery. |
| VLM chủ thể, context tối thiểu | Có sửa và xác nhận; đổi trẻ xóa lựa chọn context cũ | VLM revision từ server; snapshot/hash/consent version và denied/stale handling. |
| Story 5–15 scene, tối đa 3 rewrite | Có 5 cảnh minh họa và giới hạn UI | AI revision thật, stale rejection, current script hash. |
| Video admission → queue → safety → ready | Có animation chờ và video minh họa | Durable jobs/outbox, quota reservation, safety result, playable URL/token, lỗi có đường hồi phục. |
| Sau VIDEO_READY: activity lesson, complete/regen | Có trang activity riêng, feedback tùy chọn, complete và tạo lại 2 lần | Recheck exact lesson version, server transition, timing ẩn video cũ, 144/168h và quota. |
| Cancel/delete | Đã sửa cancel để bỏ story đang tạo khỏi lịch sử mẫu; xóa có xác nhận | Server revoke quyền/token, nhả active lock ngay, purge progress. |

## Thiếu sót cần ưu tiên

1. **P0 — Không thể nghiệm thu Android/API:** workspace này là Vite/React prototype, không phải `apps/mobile` React Native. Chưa có Firebase, profile/run APIs hoàn chỉnh, upload-resume, AI pipeline/video, safety/playback token và dữ liệu lưu qua restart. Evidence Parent Android ngày 10-11 chỉ `PARTIAL`: drawing-understanding 504, story/video chưa qua E2E.
2. **P0 — Trạng thái server và hồi phục:** nhiều màn chưa biểu diễn đủ loading, empty, denied, stale/conflict, retry và tiến trình purge theo Navigation Map; xử lý lỗi hiện mới là kiểm tra form hoặc toast mẫu. Phải dùng mã lỗi/contract được BE chốt, không tự đặt quyền và trạng thái.
3. **P1 — Hồ sơ và riêng tư:** thiếu immutable revision/provenance, age legacy 121–155 theo quyết định owner, lịch sử trải nghiệm tách biệt, thu hồi quyền server và xóa theo lifecycle. UI mới có opt-in từng run và xóa fixture.
4. **P1 — Guide, media và video:** guide chưa có line art đã kiểm định; phụ đề/toàn màn hình chỉ là giao diện minh họa. Cần kiểm tra Android thật, giảm chuyển động và thiết bị nhỏ khi chuyển sang native.
5. **P1 — Quyết định sản phẩm còn mở:** no-preset activity catalog; Parent top-up/giá; profile sharing field allowlist/expiry; lịch sử/retention. UI không được tự suy diễn các policy này.
6. **P2 — Tiện ích FE mẫu:** archive/restore hồ sơ, account edit, dark mode, phụ đề mặc định, auto landscape chưa có trong prototype. Chúng không làm lệch Rev60 mainflow nhưng nên chốt cùng Product trước khi xây bản native.
7. **P2 — Session feedback:** FE web chỉ lưu mock state, chưa có BE contract. Màn mới cho Parent trải nghiệm và tránh bỏ sót UX, nhưng cần owner quyết định lưu đâu, retention, quyền xem và có dùng analytics hay không.

## Kiểm chứng đã thực hiện

- Đã chạy trình duyệt ở khung điện thoại: chọn trẻ/lesson → ảnh mẫu → ý tưởng → xác nhận chủ thể/context → script → video ready → hoạt động → feedback 5 sao/tags/note → lịch sử/chi tiết; giá trị đã hiện lại trong phiên.
- Đã kiểm tra `documentWidth` không vượt viewport trên màn chi tiết câu chuyện và không có console error ở lượt kiểm tra này.
- Đã sửa hai lỗi nhánh: đổi trẻ xóa opt-in context của trẻ trước; hoạt động của story cũ không hoàn tất nhầm active run khác. Đánh giá story đã hoàn tất dùng nhãn “Lưu đánh giá”/“Bỏ qua”, tránh ngụ ý hoàn tất active run khác.
- Đã sửa hủy run mẫu để không biến thành “đã hoàn tất”.
- Ngày 12-11 đã chạy lại TypeScript `tsc --noEmit` và `npm run build`: đều đạt. Trong browser, từ bước Chủ thể đi thẳng sang Ngữ cảnh (không có activity picker); hủy run ở bước Ngữ cảnh giữ lịch sử ở 2 story mẫu; mở activity của story cũ khi có active run khác không hiện nút Hoàn tất. Màn feedback vẫn mở được từ story đã hoàn tất.
- Ảnh giao diện: `parent-session-feedback-preview.png` và `parent-feedback-detail-preview.png`. Đây chỉ là browser preview; chưa nghiệm thu native/API/database.
- Ngày 12-11 đã thử kiểm tra remote GitHub để phát hiện cập nhật qua đêm; web trả cache miss/robots và `git ls-remote` lỗi mạng trong môi trường hiện tại. Các SHA trong báo cáo vẫn là những mốc đã đọc ngày 11-11; **chưa xác nhận nhánh có commit mới ngày 12-11 hay không**.

## Nguồn

- SRS Rev60: `d77ad86c:features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (BR-15, FR-P-01..11, UC-02, §31.10).
- Screen map Rev57: cùng nhánh docs, `features/FEAT-063-system-architecture-rearchitecture/artifacts/SCREEN_NAVIGATION_MAP_DRAFT_REV57_20261109.md`.
- FE web Parent: `c4dd9aa3:apps/parent-ui/src/pages/ParentScreens.tsx`, `apps/parent-ui/src/context/ParentContext.tsx`.
- Parent Android pilot và BE lesson: `800c8e9f:apps/mobile/src/features/parent/ParentWorkflowScreen.tsx`, `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`, `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-74_PARENT_TEACHER_MODAL_E2E_20261110.md`.

Không có kết luận “đầy đủ 100%”: mainflow prototype đã có đường đi và feedback, nhưng các P0/P1 trên vẫn là công việc thật trước khi ghép toàn bộ BE.
