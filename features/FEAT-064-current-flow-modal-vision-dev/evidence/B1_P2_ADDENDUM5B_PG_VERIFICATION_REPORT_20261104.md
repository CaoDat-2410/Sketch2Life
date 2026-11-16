# B1 P2 Addendum 5b — xác minh PostgreSQL từ log owner

**Trạng thái: `BLOCKED`**  
**Nguồn kết quả:** owner chạy runner cục bộ; phiên này chỉ đọc log, không tự chạy test PostgreSQL và không kết nối DB.

## Checkout, log và hash

- Branch hiện tại: `feature/feat063-be-foundation`; HEAD: `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index: 0 staged path.
- Owner log snapshot: `.claude/handoff/snapshots/GB1_P2_A5B_20261104T180758/`.
- Snapshot phân tích: `.claude/handoff/snapshots/GB1_P2_A5B_ANALYSIS_20261104T180555/`.
- Addendum 5 report ghim: `BB5EDC9DFD9D8C052DC636C2437B0A9F0BB65922BF76F5887E5456063723CA2A`; Addendum 5 plan: `F52C1B733900CEDF8391C2DD2A619560EB8B630CE06BCF0426626004AD94A3AC`; owner-run summary manifest: `D2D63B42B85037A50D89C063942438729DA4493A0F4D0A867C9323485D319E2D`.
- Plan Addendum 5b: `plan/B1_P2_ADDENDUM5B_PG_OWNER_RUN_PLAN_20261104.md`, SHA-256 `1AC527AF516B8CA13E759ED801336BABEBD32C5DBFA6296A13BB02C30685A157`.
- Bốn file ghim hiện khớp: `pilot_composition.py` `2D4A99E15C3650A3E30538B9557251872CAFEE338E3F82FF7917A55D8284F004`; `test_be1_pilot_artifact_fence.py` `3D3683640B3876E1431E02294561AF9C90C616FA0FC5C32711F1D6311B84FA1D`; `test_be1_synthetic_pilot_postgres.py` `0620AFDEBDB83584C2AA97BE9BCD6E1437CD99B84C912E4EF216BA4B1885440D`; `test_pilot_queue_composition_b1.py` `5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4`.
- Run context ghi đúng HEAD và `staged_paths=0`; branch không được ghi trong run-context. Summary ghi hash cuối khớp hash đầu; log không chứa các giá trị digest cụ thể. Runner script được phép đọc có đủ 4 hash ghim và dùng `Get-FileHash`. Checkout hiện tại có branch/HEAD đúng và 4 hash hiện tại khớp bảng.
- Danh sách trạng thái của owner trước/sau đều giống nhau, 110 mục. Runner summary báo 20/20 FAIL, 0 PASS, 0 SKIP.

## Kết quả 7 node

Log root tương đối: `.claude/handoff/snapshots/GB1_P2_A5B_20261104T180758/logs/`. ID trong bảng là tiền tố file log; mỗi ID có `.command.txt`, `.stdout.txt`, `.stderr.txt` tương ứng.

| Node | Các lượt | Kết quả stdout từng lượt | Stdout log (command/stderr cùng basename) |
| --- | --- | --- | --- |
| `test_b1_succeeded_is_durable_before_real_app_result_acceptance` | 3 repeats; 1 final | Mỗi lần: `ERROR` ở setup; 0 passed / 0 failed / 0 skipped; 1 setup error; exit 1. | `logs/01-test_b1_succeeded_is_durable_before_real_app_res-r1.stdout.txt`; `logs/02-test_b1_succeeded_is_durable_before_real_app_res-r2.stdout.txt`; `logs/03-test_b1_succeeded_is_durable_before_real_app_res-r3.stdout.txt`; `logs/14-test_b1_succeeded_is_durable_before_real_app_res-final.stdout.txt` |
| `test_b1_unknown_after_sent_is_not_accepted_or_replayed` | 1 repeats; 1 final | Mỗi lần: `ERROR` ở setup; 0 passed / 0 failed / 0 skipped; 1 setup error; exit 1. | `logs/04-test_b1_unknown_after_sent_is_not_accepted_or_re-r1.stdout.txt`; `logs/15-test_b1_unknown_after_sent_is_not_accepted_or_re-final.stdout.txt` |
| `test_b1_hold_before_send_creates_no_result_or_invocation` | 1 repeats; 1 final | Mỗi lần: `ERROR` ở setup; 0 passed / 0 failed / 0 skipped; 1 setup error; exit 1. | `logs/05-test_b1_hold_before_send_creates_no_result_or_in-r1.stdout.txt`; `logs/16-test_b1_hold_before_send_creates_no_result_or_in-final.stdout.txt` |
| `test_b1_stale_owner_fence_rejects_result_after_provider_success` | 3 repeats; 1 final | Mỗi lần: `ERROR` ở setup; 0 passed / 0 failed / 0 skipped; 1 setup error; exit 1. | `logs/06-test_b1_stale_owner_fence_rejects_result_after_p-r1.stdout.txt`; `logs/07-test_b1_stale_owner_fence_rejects_result_after_p-r2.stdout.txt`; `logs/08-test_b1_stale_owner_fence_rejects_result_after_p-r3.stdout.txt`; `logs/17-test_b1_stale_owner_fence_rejects_result_after_p-final.stdout.txt` |
| `test_b1_stale_artifact_fence_rejects_result_after_provider_success` | 1 repeats; 1 final | Mỗi lần: `ERROR` ở setup; 0 passed / 0 failed / 0 skipped; 1 setup error; exit 1. | `logs/09-test_b1_stale_artifact_fence_rejects_result_afte-r1.stdout.txt`; `logs/18-test_b1_stale_artifact_fence_rejects_result_afte-final.stdout.txt` |
| `test_b1_concurrent_duplicate_delivery_uses_one_attempt_and_one_send` | 1 repeats; 1 final | Mỗi lần: `ERROR` ở setup; 0 passed / 0 failed / 0 skipped; 1 setup error; exit 1. | `logs/10-test_b1_concurrent_duplicate_delivery_uses_one_a-r1.stdout.txt`; `logs/19-test_b1_concurrent_duplicate_delivery_uses_one_a-final.stdout.txt` |
| `test_b1_sent_invocation_survives_process_rebuild_without_second_provider_call` | 3 repeats; 1 final | Mỗi lần: `ERROR` ở setup; 0 passed / 0 failed / 0 skipped; 1 setup error; exit 1. | `logs/11-test_b1_sent_invocation_survives_process_rebuild-r1.stdout.txt`; `logs/12-test_b1_sent_invocation_survives_process_rebuild-r2.stdout.txt`; `logs/13-test_b1_sent_invocation_survives_process_rebuild-r3.stdout.txt`; `logs/20-test_b1_sent_invocation_survives_process_rebuild-final.stdout.txt` |

Đối chiếu từng stdout: cả 20 lần báo `ERROR at setup`, với `PermissionError [WinError 5]`; không có test body hoặc assertion nào chạy. Mỗi stdout còn có cảnh báo pytest không ghi được cache. Trong test source, `pilot_harness` yêu cầu fixture `tmp_path` (dòng 372), nên lỗi tạo temp path xảy ra trước khi thân fixture kiểm tra URL DB. Không có bằng chứng từ các lần này về acceptance hoặc kết quả PostgreSQL.

Các command đều có đúng đối số `-m pytest -o addopts= -q --tb=short tests/integration/test_be1_synthetic_pilot_postgres.py::<node>` và ghi `cwd: backend`; runner dùng interpreter venv bằng đường dẫn tuyệt đối. Nội dung đường dẫn không được sao chép vào báo cáo.

### Bảo vệ log

Quét 64 file text trong owner snapshot: 0 credential-bearing URL, 0 DB URL scheme, 0 password/secret assignment; có 20 HTTP(S) URL occurrence trong output pytest và 100 absolute-local-path occurrence. Nội dung URL/path không được chép vào báo cáo hoặc snapshot phân tích. Các log gốc chỉ được tham chiếu theo đường dẫn tương đối.

## Phân loại và trạng thái findings

Lỗi `WinError 5` ở bước fixture setup là lỗi quyền filesystem của môi trường runner, không phải assertion sai theo hành vi được duyệt. Phân loại **B — ngoài phạm vi sửa assertion**. Theo fail-stop, không sửa test/source và không chạy tiếp.

- **FND-03: MỞ** — crash/replay sau SENT chưa được kiểm chứng bằng PostgreSQL.
- **FND-04: MỞ** — receipt `accepted` bền và revision chưa được kiểm chứng bằng PostgreSQL.
- **FND-05: MỞ** — trạng thái stale-owner chính xác chưa được kiểm chứng bằng PostgreSQL.

## Kiểm tra tiếp theo

- PostgreSQL: owner chạy 20 invocation nhưng cả 20 lỗi ở setup; các test không đạt và không bị skip.
- Offline regression: `NOT RUN` vì điều kiện “cả 7 node đạt” không thỏa.
- Unit, Ruff, strict mypy, ba validator và `git diff --check`: `NOT RUN` trong lượt phân tích này do fail-stop ở PostgreSQL. Kết quả trong Addendum 5 trước đó chỉ là dữ liệu lịch sử, không được tính là kiểm tra hiện tại.
- Codex không kết nối DB, không đọc URL/mật khẩu, không sửa source, approval hoặc status; không chạy Modal/provider/GPU/mạng ngoài; không stage/commit/push/merge.
- Raw owner logs có các path/URL occurrence nêu trên; không chỉnh hoặc sao chép chúng. Cần owner sửa quyền ghi temp/cache của runner rồi gửi snapshot log mới. Review độc lập vẫn bắt buộc; không kết luận B1/F2 accepted.

## Snapshot và checksums

- Addendum 5b plan SHA-256: `1AC527AF516B8CA13E759ED801336BABEBD32C5DBFA6296A13BB02C30685A157`.
- Analysis snapshot manifest SHA-256: `D0F7D76FF3964F18D8AB06CB74F659543A4C0DCF639EFE3AB5E1759A537673B9`.
- SHA-256 của report này được ghi ở `report.sha256` trong analysis snapshot để tránh tự tham chiếu.
- Analysis JSON và SHA-256 list của log gốc trong snapshot là bản tóm tắt/hash; không chứa log raw.
