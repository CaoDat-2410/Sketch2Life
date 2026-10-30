# B1 — Kế hoạch thực hiện bảng crosswalk API (DRAFT)

- Trạng thái: **DRAFT** — kế hoạch làm tài liệu, không phải approval triển khai. Không sửa `approvals/TASK_APPROVAL.md`. B1 là tài liệu thuần túy: không code, không migration, không chạy backend/DB/MinIO/Modal.
- Ngày: 2026-10-30. Nguồn mục tiêu: dòng B1 và B0a/B0b trong [backlog điều phối](BACKLOG_API_REV37_SRS23_MODAL_20261030.md).
- Người đọc: BA và nhóm BE, để phân loại API hiện có thành giữ / sửa / legacy / fixture / mới theo SRS 2.3 và biết dòng nào pilot FEAT-064 cần.
- Kết quả mong muốn: một bảng 135 dòng của catalog Rev37 cộng các dòng đích mới từ SRS, mỗi dòng có đủ cột trong §3, kèm tổng hợp và danh sách dòng cần owner quyết định. **Mọi disposition là đề xuất để owner duyệt, không phải quyết định.**

## 1. Đầu vào phải ghim (ghi hash vào đầu tài liệu kết quả)

| Đầu vào | Ghim |
|---|---|
| Catalog Rev37 | Dùng bản trong Git: commit `e9ba2ddde46c576aff5dbd919ba3ab285b464a87`, blob `56fee2a1f54317f6fc79a34698da9b887701e001` (LF), SHA-256 bytes LF `4090833B7EC03A6FEE81E0F8AE7FD57F9C2C1A8901D969D13F3C3F5CAAD29C54`. Bản chủ task giữ là CRLF, SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`, cùng nội dung. Không chép catalog vào repo; đọc bằng `git show <commit>:<path>` để không phụ thuộc đường dẫn local. |
| Snapshot B0a | `evidence/B0_openapi_combined_storage-off_20261030.json` (121 operation) và `…storage-on_20261030.json` (124 operation); hash trong `evidence/B0_OPENAPI_OFFLINE_SNAPSHOT_20261030.md`. |
| SRS | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (v2.3-draft): §9.6 nhóm route đích; §21.2 bảng method/path đích (37 dòng, một số dòng gộp nhiều method như `GET/PATCH`); §21.1–21.4 quy tắc chung; BR-08/09/15, FR-P-05 cho hoạt động của Parent. |
| Register | `artifacts/DATA_TABLE_REGISTER.md` (owner dữ liệu, dùng để điền cột owner). |
| S1 | `plan/REV36_S1_EXECUTION_SCOPE_DRAFT_20261029.md`: 29 operation candidate-fence (mục "Static operation inventory") và 8 operation đề xuất giữ (`join-status`, `data-requests` và 6 ghi registry). Đây là draft, không phải denylist đã duyệt. |
| Pilot | `../FEAT-064-current-flow-modal-vision-dev/plan/PLAN.md` §4–§5, §7 (vòng đời lobby → join → admit → start → turn → vẽ → export/request) và `plan/CONTRACT_OUTLINE_DRAFT.md` mục C (route gateway pilot, mới chỉ là outline). |
| Kết quả B0 | `evidence/B0_CLOSEOUT_20261030.md` (đã kiểm: 124 mounted khớp snapshot; 11 chưa mount). B0b còn mở. |

## 2. Nguyên tắc (áp dụng cho mọi dòng)

1. **Không ghi PASS.** Cột bằng chứng chỉ có các mức ở §4; không dòng nào được ghi là đã test pass.
2. **Không ghép theo tên.** Chỉ ghép một dòng hiện có với một đích SRS khi path **và** ngữ nghĩa trùng. Giống tên nhưng khác ngữ nghĩa thì giữ riêng và ghi `analogous-to #N`.
3. **Demo/fixture không tự thành đích SRS.** Dòng demo mặc định `LEGACY_HOLD`; dòng fixture/candidate mặc định `FIXTURE`.
4. **Không tự quyết mâu thuẫn Parent.** Mọi dòng liên quan chọn hoạt động của Parent hoặc StoryRun: `blocked_by = B2`, không chọn bên nào của SRS.
5. **Không nhân đôi pilot.** Endpoint mới của pilot (gateway request/status, projection) là `NEW_TARGET` với `target_source = FEAT064`, trỏ về task T-N của FEAT-064; không tạo task mới.
6. **Thiếu thông tin thì ghi `NEEDS_OWNER`, không đoán.** Mỗi dòng `NEEDS_OWNER` phải có câu hỏi cụ thể.

## 3. Cột của bảng

| Cột | Giá trị |
|---|---|
| `key` | `C###` cho dòng catalog (số `#` của catalog); `T###` cho dòng đích mới |
| `method`, `path` | Chuẩn hóa `{x:path}` thành `{x}` như OpenAPI. Dòng đích gộp (`GET/PATCH`) tách thành từng method |
| `group` | BE1 / Demo / Lesson Library / Storage example / Candidate-fixture (catalog) hoặc nhóm đích của SRS |
| `profile` | `classroom`, `demo`, `combined-only`, `combined+storage-flag`, `not-mounted`, hoặc `target` |
| `actor_auth` | Lấy từ cột "Authentication / handler" của catalog; dòng đích lấy cột Actor của SRS §21.2 |
| `owner_module` | Theo §9.7 của SRS (BE1, Lesson, Story, AI Jobs, Billing, Notifications, Core…) |
| `evidence_level` | `E0`–`E3` (§4) |
| `srs_ref` | Dòng SRS (UC/FR/BR/§21.2 row) hoặc `none` |
| `disposition` | `KEEP` / `MODIFY` / `LEGACY_HOLD` / `FIXTURE` / `NEW_TARGET` |
| `target_source` | Chỉ cho `NEW_TARGET`: `SRS21.2`, `SRS9.6`, `FEAT064`, `LESSON_REV31` |
| `relation` | `replaces #N`, `analogous-to #N`, `same-as #N` hoặc rỗng |
| `s1` | `S1_CANDIDATE_BLOCK`, `S1_PRESERVE_RECOMMENDED`, `S1_NOT_IN_INVENTORY` |
| `pilot` | `Y` / `N` / `MAYBE` + lý do ngắn (theo vòng đời PLAN.md §7 và T-N liên quan) |
| `blocked_by` | Danh sách từ: `none`, `B0b`, `B2`, `B3`, `B4a`, `B4b`, `B5`, `OD-n`, `T-N` |
| `rationale` | Một câu căn cứ + trích dẫn nguồn (đường dẫn:dòng) |
| `confidence` | `HIGH` / `MED` / `LOW`; `LOW` luôn kèm `NEEDS_OWNER` |
| `needs_owner` | Câu hỏi cụ thể hoặc rỗng |

## 4. Mức bằng chứng

| Mức | Nghĩa | Cách xác định |
|---|---|---|
| E0 | Chỉ có trong SRS/plan, không có route | dòng đích mới |
| E1 | Chỉ có nhãn catalog | dòng catalog chưa mount, hoặc không có trong snapshot |
| E2 | Có trong snapshot offline B0a | method/path có trong JSON storage-on |
| E3 | E2 và có file test tham chiếu path/operation (đọc tĩnh, **không chạy**) | tìm trong `backend/tests` theo path hoặc tên hàm; ghi tên file |

Không có E4. Nhãn PASS/BLOCKED của catalog được chép vào ghi chú như "nhãn catalog", không đổi thành mức bằng chứng.

## 5. Các bước thực hiện

| Bước | Việc | Đầu ra | Xong khi |
|---|---|---|---|
| S0 | Preflight: đọc `AGENTS.md`; `git status`/`git log -3`; ghi hash 8 file local đang giữ; xác nhận không file nào trong danh sách bảo toàn bị đổi | Ghi chú preflight trong tài liệu kết quả | Hash khớp bản ghi; nếu lệch, dừng và hỏi |
| S1 | Trích 135 dòng catalog từ blob Git vào bộ nhớ/tệp tạm ngoài repo; chuẩn hóa path | Bảng trung gian (không commit) | 135 dòng, số `#` 1–135 không trùng |
| S2 | Đối chiếu với snapshot storage-on và off: gán `profile` và `evidence_level` sơ bộ | Cột `profile`, E1/E2 | 124 mounted có E2; 11 chưa mount có E1; 3 dòng storage ghi `combined+storage-flag`; 121/124 giải thích đúng |
| S3 | Dựng tập đích mới: tách mỗi dòng SRS §21.2 theo method, thêm nhóm §9.6 chưa có trong §21.2 (ví dụ `/health/*`, `/metrics`, `/v1/me`) nếu có; bỏ dòng trùng với dòng hiện có đã ghép theo nguyên tắc 2 | Tập `T###` | Mỗi dòng có `srs_ref` chỉ vào đúng dòng SRS; dòng gộp được tách; số dòng tăng được ghi rõ |
| S4 | Gắn S1: khớp 29 candidate + 8 preserve của draft với dòng catalog bằng method + path (mở rộng tiền tố `B/O/S/G/M/C/L` theo định nghĩa trong draft) | Cột `s1` | Đúng 29 + 8 dòng khớp; còn lại `S1_NOT_IN_INVENTORY`; không dòng nào khớp mơ hồ |
| S5 | Quét tĩnh test (E3) | Cột `evidence_level`, ghi tên file test | Mỗi E3 có tên file; không chạy test |
| S6 | Gắn `pilot` theo PLAN.md §7: lobby, join, admit, start, grant turn, canvas operations, artifacts, đọc trạng thái; và các route gateway mới của contract outline mục C | Cột `pilot`, các dòng `T###` target_source=FEAT064 | Mỗi `Y/MAYBE` có lý do + T-N; các dòng pilot mới trỏ về FEAT-064, không tạo task mới |
| S7 | Đề xuất `disposition` + `rationale` + `confidence` + `blocked_by` theo mặc định ở §6 rồi xem xét từng nhóm | Cột còn lại | Không ô trống; mọi `LOW` có `needs_owner` |
| S8 | Viết kết quả: `evidence/B1_API_CROSSWALK_20261030.md` (giới hạn, phương pháp, tổng hợp, bảng đầy đủ, danh sách `NEEDS_OWNER`) và `evidence/B1_API_CROSSWALK_20261030.csv` (đủ cột, UTF-8) | 2 file mới | Đầu tài liệu có khối giới hạn (§7) |
| S9 | Tự kiểm (script ngoài repo hoặc kiểm tay có đếm): xem §8 | Bảng kết quả kiểm trong tài liệu | Mọi kiểm tra đạt hoặc ghi lệch có lý do |
| S10 | Chạy `validate_harness`, `validate_repository_security`, `validate_architecture`, `git diff --check`; báo cáo kết quả thật | Phần báo cáo cuối | Cả bốn exit 0, hoặc ghi rõ blocker; **không commit, không push** |

## 6. Mặc định đề xuất theo nhóm (điểm xuất phát, phải kiểm lại với nguồn)

| Nhóm catalog | Số dòng | Mặc định | Ghi chú cho người phân loại |
|---|---:|---|---|
| BE1 / classroom | 56 | `KEEP` health, registry (org, assignment, class, profile) và nhánh dữ liệu; `LEGACY_HOLD` cho 29 candidate S1; `MODIFY` cho consent | Consent là `blocked_by B4a/B4b`; `join-status`, `data-requests` theo S1 preserve |
| Demo / local flow | 35 | `LEGACY_HOLD` | Không ghép sang StoryRun theo tên; ghi `replaces`/`analogous-to` chỉ khi ngữ nghĩa trùng |
| Lesson Library | 30 | `KEEP` (hoặc `MODIFY` nếu lệch SRS §31/ADR-0022) | Rev31 đã duyệt; rà path so với SRS lesson route; Parent-group replay là `blocked_by B5` |
| Local storage example | 3 | `FIXTURE` | Chỉ khi `combined` + `env=local` + `storage_example_enabled=true` |
| Candidate / fixture | 11 | `FIXTURE` | Chưa mount; không coi là đích SRS |

Dòng đích mới: `NEW_TARGET`; `blocked_by B2` cho mọi dòng liên quan chọn hoạt động Parent/StoryRun; `blocked_by B3` cho dòng cần quyết định owner/migration.

## 7. Khối giới hạn bắt buộc ở đầu tài liệu kết quả

- Nguồn là snapshot offline B0a (profile `combined`), không phải lịch sử Rev37; B0b còn mở (thiếu `EV-063-30`).
- Không dòng nào đã được chạy hay "pass"; cột bằng chứng chỉ là mức E0–E3.
- Chưa có snapshot riêng cho profile `classroom` (profile của pilot); cột `profile` suy từ nhóm catalog, chưa xác minh bằng OpenAPI của `classroom`.
- SRS 2.3 và register là bản draft; mâu thuẫn hoạt động của Parent chưa được giải quyết (B2); disposition là đề xuất.
- Draft S1 chưa được duyệt; không cho phép chặn route nào.

## 8. Kiểm tra tự động / đếm bắt buộc (S9)

1. Có đúng 135 dòng `C###`; `#` 1–135, không trùng; số dòng `(method, path)` không trùng.
2. 124 dòng mounted đều có E2 hoặc E3; 11 dòng candidate đều E1; 3 dòng storage là `combined+storage-flag`.
3. Mọi giá trị cột enum thuộc đúng tập ở §3–§4; không ô trống; mọi `LOW` có `needs_owner`.
4. S1: đúng 29 `S1_CANDIDATE_BLOCK` và 8 `S1_PRESERVE_RECOMMENDED` trong 135 dòng; không dòng nào khác mang nhãn S1.
5. Mọi dòng `NEW_TARGET` có `target_source`, `srs_ref` (hoặc `FEAT064` + T-N) và không trùng một dòng `C###` có cùng method/path.
6. Mọi dòng liên quan hoạt động Parent/StoryRun có `blocked_by` chứa `B2`.
7. Không có đường dẫn tuyệt đối local, token, nội dung `.env` hay dữ liệu trẻ trong hai file kết quả.
8. Tổng hợp trong tài liệu (số theo disposition, nhóm, pilot) khớp với CSV.

## 9. Ranh giới

- Không sửa: `approvals/TASK_APPROVAL.md`, bất kỳ approval nào, code sản phẩm, `backend/`, `apps/`, plan/SRS/register, hai báo cáo B0 và backlog đã có, 8 file local đang được giữ.
- Chỉ thêm hai file kết quả mới (`.md`, `.csv`) và tùy chọn một ghi chú ngắn trong `evidence/notes/`.
- Không chạy backend, DB, MinIO, Modal, GPU, test; không dùng token hay dữ liệu trẻ thật.
- Không stage, commit, push, stash, reset. Việc đẩy lên GitHub sẽ làm một lượt sau khi chủ task duyệt B1.
- Không chọn phía của mâu thuẫn Parent; không tự gán owner cho một người cụ thể.

## 10. Quyết định đã giả định (chủ task có thể đổi)

| Giả định | Lý do |
|---|---|
| B1 là tài liệu thuần túy, không tạo mục approval riêng | Backlog xếp B1 là bảng điều phối; việc ghi approval do chủ task quyết định |
| Dẫn catalog bằng commit + hash, không copy vào repo | Tránh phân phối thêm bản file khi chủ task chưa quyết định |
| Dòng đích gộp (`GET/PATCH`) được tách theo method | Để so với OpenAPI và có thể đếm |
| Disposition là đề xuất | SRS và S1 đều draft |

## 11. Việc cần owner sau khi B1 xong

1. Duyệt các dòng `NEEDS_OWNER` và các dòng `confidence LOW`.
2. Quyết định có ghi approval cho B1 hay không.
3. Quyết định đưa catalog vào repo hay giữ cách dẫn bằng hash.
4. Quyết định thời điểm đẩy (gộp với B0 closeout và các thay đổi local khác).
