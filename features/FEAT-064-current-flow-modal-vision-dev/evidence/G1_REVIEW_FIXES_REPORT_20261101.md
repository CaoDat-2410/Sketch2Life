# Báo cáo sửa review G1 — T2 / T3 / T9

- Trạng thái: **XONG-CHƯA REVIEW**; chỉ hoàn tất G1 review-fixes, không kết luận production-ready.
- Nhánh: `feature/feat063-be-foundation`.
- HEAD trong lượt: `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`.
- Plan được duyệt: `plan/G1_REVIEW_FIXES_PLAN_20261101.md`, SHA-256 `90424CEFDA794A38B21BA2818462BFEAE862C65526B37FC08B0F97997F313E95`.
- Chế độ: TREO KHÔNG COMMIT; không stage, commit, push, reset, checkout, clean hoặc stash.
- Dữ liệu: chỉ fixture synthetic. Không dùng dữ liệu thật của trẻ, Modal, GPU, provider ngoài hoặc migration.

## R0–R6

| Bước | Trạng thái | Kết quả |
|---|---|---|
| R0 — tiền kiểm và mốc | LÀM | Nhánh/HEAD và snapshot G1 được giữ; mốc hiện tại và bản HEAD archive được đo. Ba file owner-local sửa và bốn ghi chú local không bị chỉnh. |
| R1 — plan/approval | LÀM | Plan và approval append-only pin đúng SHA-256 nêu trên. |
| R2 — test trước, sửa F1–F4 | LÀM | Đã ghi các lỗi đỏ ban đầu và sửa regression trong allowlist; chi tiết bên dưới. |
| R3 — F5/F6 trong allowlist | LÀM MỘT PHẦN | Loopback guard và các kiểm tra reconnect/Teacher đã chạy. Positive reconnect bằng legal effective consent: NOT DONE do constraint hiện hữu chỉ cho `pending`/`revoked`. |
| R4 — kiểm sau sửa | LÀM | Bộ hẹp, full contract, full unit, PostgreSQL, Ruff, mypy và validators đã chạy; các giới hạn môi trường được ghi rõ, không che lỗi suite. |
| R5 — báo cáo/UI contract/sổ | LÀM | Báo cáo này, báo cáo T2/T3/T9 và ledger được cập nhật. |
| R6 — snapshot | LÀM | Snapshot cục bộ cuối lượt được tạo tại `.claude/handoff/snapshots/G1R_20261101T.../`; `files.txt`, `hashes.csv`, bản sao và `diff.patch` được lưu. |

## F1–F6

| Finding | Trạng thái | Đỏ → sau sửa / bằng chứng |
|---|---|---|
| F1 — OpenAPI catalog và route T9 | LÀM | Ban đầu catalog assertion đỏ vì runtime có 112 paths/125 operations còn catalog Rev37 vẫn là 111/124. Sau sửa, contract catalog xanh: tách đúng một `PILOT_ONLY_OPERATIONS`, giữ nguyên 111/124 cho phần catalog và kiểm route pilot riêng. Builder vẫn xử lý route ngoài catalog; không sửa `openapi_contract.py`. |
| F2 — payload stroke JSON độc hại | LÀM | Hai ca màu dạng list/dict trước đó làm kiểm tra membership ném `TypeError`; sau sửa, màu không phải chuỗi bị từ chối typed. Unit/contract hiện kiểm list, dict, null, bool, chuỗi lạ, số lớn, kích thước, điểm và tọa độ; HTTP trả 422 an toàn, không lưu operation. Bộ focused sau sửa: 132 passed. |
| F3 — Child reconnect thiếu `profile_version` | LÀM | Red ban đầu gồm một contract/schema failure và ba reconnect PostgreSQL failures được ghi trong test-first report T2. Schema/route nay trả version server cấp; session cũ trả null; active/paused không cần turn đang chạy; append dùng version trả về. Không trả toàn bộ cấu hình/palette. |
| F4 — fingerprint session cũ | LÀM | Một regression test đỏ trước sửa. `profile_version` chỉ vào fingerprint khi khác null; test tính digest độc lập. Đối chiếu HEAD cho thấy công thức lịch sử thực tế có **5 khóa JSON**, dù prompt ban đầu nói 6; test ghim đúng 5 khóa thực tế để bảo toàn digest, không sửa hành vi khác. |
| F5 — an toàn URL PostgreSQL | LÀM | Fixture kiểm tra tên DB `be1_acceptance`, host loopback (`localhost`, `127.0.0.1`, `::1`) và loại query override host không-loopback. PG module hiện: 48 passed. Chặn socket Python không bảo vệ kết nối libpq/psycopg; URL pre-check là hàng rào riêng. Không in URL. |
| F6 — hồi quy reconnect/Teacher | LÀM MỘT PHẦN | PG module hiện: 48 passed, gồm các denial, Teacher khác lớp/org, staging/pilot-off và đọc lại `canvas_operation_profile_id`. Positive legal-effective reconnect: **NOT DONE**; constraint DB hiện hữu chỉ cho `pending`/`revoked`, không thể tạo consent effective hợp lệ trong phạm vi này. Không bypass constraint hoặc migration. |

## Kết quả kiểm thử R0/R4 và đối chiếu HEAD

Các lệnh chạy từ `backend/` với `PYTHONPATH=src`; `basetemp` nằm ngoài repo. `test_live_image_demo_api.py` bị loại khỏi full contract suite theo phạm vi/offline guard và ghi **NOT RUN** riêng.

| Bộ kiểm | R0 trước review-fixes | Working tree R4 | HEAD archive đối chiếu |
|---|---:|---:|---:|
| Bộ CPU/offline R0 (5 file CI + synthetic eligibility + BE1 pilot + canvas profile) | 267 passed, 4 skipped | **294 passed, 4 skipped** | 227 passed, 4 skipped |
| `tests/contract` trừ `test_live_image_demo_api.py` | Chưa có mốc tổng | **1,381 passed** | 1,378 passed, 1 failed |
| `tests/unit` | Chưa có mốc tổng | **6,195 passed, 9 failed, 24 skipped, 12 errors** | 6,112 passed, 27 failed, 24 skipped, 12 errors |
| `test_be1_synthetic_pilot_postgres.py` | 31 passed (số lịch sử) | **48 passed** | 4 passed (module HEAD cũ hơn) |

Giải thích suite đỏ:

- Một contract HEAD archive fail trong `test_sketch_review_contracts.py::test_rv_c02_shared_pack_bytes_unchanged_from_baseline`: `git archive` không mang thư mục `.git`; test catalog OpenAPI ở HEAD thì xanh, còn working tree xanh sau F1.
- Full unit có 12 collection errors do optional `imageio`/`imageio_ffmpeg` không cài. Bảy lỗi test cùng hiện diện ở HEAD: knowledge-video source closure, Lightning whiteboard parser, persistent Qwen timeout, ba Pixi log-capture cases và whiteboard renderer thiếu dependency.
- Hai lỗi unit chỉ xuất hiện ở working tree là FEAT-018 P2-T5 evaluation: scratch cố định có fixture synthetic read-only nên probe ghi file nhận `PermissionError`. Không sửa/xóa fixture đó. Probe bằng scratch mới dưới thư mục pytest tạm chạy thành công (`SUCCEEDED`; 121 `SUCCEEDED`, 25 `NOT_EXECUTED`). Đây là chẩn đoán riêng, không đổi kết quả full suite.
- So với HEAD archive, full unit có 20 lỗi HEAD-only; không quy tất cả cho thiếu `.git`.
- So sánh số suite giữa HEAD archive và working tree phản ánh hai cây khác nhau, không phải khẳng định mọi lỗi archive đều do thay đổi G1.

## Ruff, mypy và OpenAPI

- Ruff lint trên 7 file Python thuộc review-fixes: `All checks passed!` với `--config backend/pyproject.toml`.
- Ruff format check: `7 files already formatted`.
- Strict mypy trên 6 file source hiện tại: 5 diagnostic; HEAD-source shadow: 7; `NEW_DIAGNOSTICS=0`, `RESOLVED_DIAGNOSTICS=2`.
- Generated `backend/src/sketch2life/interfaces/http/openapi_contract.py` không sửa; nguồn catalog Rev37 giữ nguyên. Contract catalog xác nhận 111 paths/124 operations trong catalog và đúng một route pilot-only ngoài catalog.

## Hợp đồng cho UI

Chi tiết request/response synthetic reconnect và Teacher `pilot-profiles`, mã HTTP, thứ tự 403 trước 409, lỗi append stroke, làm tròn tọa độ, palette, độ dày, giới hạn 2–512 điểm/32 KiB và các ghi chú client được ghi trong ba báo cáo T2/T3/T9. Tóm tắt:

- Reconnect trả `profile_version` dạng chuỗi cho session có profile và `null` cho session cũ; `turn_id` nullable, có thể null trong paused/không có turn. Không gửi lại request chỉ vì read bị từ chối.
- Client phải làm tròn tọa độ trước khi gửi; tối đa 6 chữ số thập phân. Ví dụ `0.30000000000000004` bị 422. Server không tự sửa payload.
- Append nhận 2–512 điểm, palette T0 năm màu, độ dày 5/9/14 và payload tối đa 32 KiB. Profile mismatch trả 409; profile invalid trả 422; nét bị từ chối không được lưu.
- T9 chỉ trả `child_id` và `display_name`; kiểm role/class assignment xảy ra trước các điều kiện route 409. `apps/child-ui/src/services/sessionClient.ts` vẫn khai `turn_id: string` và chưa gửi `profile_version`; UI không sửa trong G1.
- Không đưa dữ liệu thật vào ví dụ UI.

## Giới hạn và câu hỏi còn mở

- F6 positive legal-effective reconnect chưa chạy vì consent schema hiện tại không có trạng thái effective; cần giải quyết bằng task/schema được duyệt riêng, không nới guard ở G1.
- Hai điểm trùng nhau hiện vẫn được chấp nhận; spec chỉ cấm ít hơn hai điểm. Owner cần quyết định có giữ quy tắc này không.
- Kích thước export 1024 và tham số render chưa thuộc profile v1; owner cần quyết định thuộc T4/T5 hay profile version mới.
- Checkpoint snapshot hiện là dictionary tự do; T4 phải dựng export từ accepted operations, không tin snapshot.
- Hàng rào socket test patch `socket.socket.connect/connect_ex` không bao phủ libpq/psycopg. An toàn đích DB dựa thêm vào pre-check URL loopback và DB `be1_acceptance`.
- Trong một thao tác chuẩn bị PG trước đây, `Settings` từng khởi tạo với dotenv mặc định. Không có giá trị môi trường nào được ghi vào repo/báo cáo. Lần chạy review-fixes dùng `_env_file=None`; URL DB chỉ ở bộ nhớ và không in ra.
- Visual AC20, UI, `test_live_image_demo_api.py`, migration/Alembic, Modal/GPU/provider và G2+ **NOT RUN**.

## Validators và snapshot

- `python tools/validate_harness.py` → `HARNESS_VALID`.
- `python tools/validate_repository_security.py` → `REPOSITORY_SECURITY_VALID`; 6,012 publishable files scanned; không phát hiện đường dẫn tuyệt đối máy.
- `python tools/validate_architecture.py` → `ARCHITECTURE_VALID`.
- `git diff --check` → sạch.
- Ruff lint/format và mypy: kết quả ở mục trên. Whitespace/CR/BOM và hash được kiểm riêng trước snapshot.
- Snapshot R6 local/ignored: `.claude/handoff/snapshots/G1R_20261101T143559/`; có 14 file (11 thay đổi so với G1 trước, 3 file mới), không stage/commit. Snapshot `G1R_20261101T143252` được giữ nguyên nhưng là bản trung gian tạo trước khi hoàn thiện bảng hash này.

## Hash file trong snapshot R6

SHA-256 của mọi file được snapshot. Hai dấu `—` là file không thể tự ghi hash của chính nó; hash báo cáo được pin trong approval, hash approval nằm trong `hashes.csv` của snapshot.

| Trạng thái so với G1 trước | File | SHA-256 |
|---|---|---|
| M | `backend/src/sketch2life/domain/core_foundation.py` | `FFC7B8BBAA1AF2CB0D63479AAA598B74AFD1B4FB4DD58088A5706235A16C19B3` |
| M | `backend/src/sketch2life/contracts/schemas/be1_runtime.py` | `2484A952C7F96ECF46EAB3373DD34E1D206C79F69ABD3D9D9D0BF68C68D51978` |
| M | `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py` | `B679820CDDC8038793BA65B1393E0FAEA11ADD09F8D46999E1309FB465698F6C` |
| M | `backend/tests/unit/test_canvas_operation_profile.py` | `BCC8FABCEB5EA9A6775D33D3EE333092D0CEFF3D364B679BBE618390384E5983` |
| M | `backend/tests/contract/test_be1_synthetic_pilot.py` | `03CCBCE40EB3DA13FA15D3C128F22CF70B6AEE4968CF0B726A7ED8B136C74611` |
| A | `backend/tests/contract/test_openapi_contract_catalog.py` | `342D78CDE873B72A5CE9A30D999B633ABAD0EBF4331F193976233E2032812806` |
| M | `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | `46E06FD77C6214A7F0822EAEBB9AE54790D307BB26B536165742C5EB97C7B85C` |
| A | `plan/G1_REVIEW_FIXES_PLAN_20261101.md` | `90424CEFDA794A38B21BA2818462BFEAE862C65526B37FC08B0F97997F313E95` |
| A | `evidence/G1_REVIEW_FIXES_REPORT_20261101.md` | — (pinned by approval) |
| M | `evidence/T2_CHILD_CANVAS_RECONNECT_REPORT_20261101.md` | `C812A45AB622F4A6EDE9F95C4AC4E1D6265CDEF5036BF4E49E814F2862E8CDB1` |
| M | `evidence/T3_CANVAS_PROFILE_IMPLEMENTATION_REPORT_20261101.md` | `EFAC25C98AA50D6A3D6E98BFD3C47B64AEE534405D4A6813C2CF9892ACB47FE5` |
| M | `evidence/T9_TEACHER_PILOT_PROFILE_ROUTE_REPORT_20261101.md` | `4943EB093BC1B429243F7187EA53B7A4E2E34BFA1592F6DE2134534CB6151503` |
| M | `status/PILOT_GOAL_LEDGER_20261101.md` | `B14A6D17A64B181EFEC3DADD094B9E8C056DA4B0EA19E9B5B606BB51A17F78F3` |
| M | `approvals/TASK_APPROVAL.md` | — (pin nằm trong snapshot `hashes.csv`) |

