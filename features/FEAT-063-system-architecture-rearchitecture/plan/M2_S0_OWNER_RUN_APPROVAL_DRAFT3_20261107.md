# M2 S0-owner-run Task Approval — Draft 3

**Status: DRAFT — chưa phải approval, chưa được owner duyệt, chưa khởi chạy.** Bản này đề xuất một lượt đối soát owner-run chỉ đọc. Nó không tự mở pha S0-owner-run và không cho phép chạy lệnh cho tới khi owner hoàn tất lựa chọn, approval riêng và pin hash sau review độc lập.

## Owner decision record

**OWNER ĐIỀN:** chưa có quyết định thực thi trong bản nháp này.

## Plan và baseline

- **Plan:** plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md
- **Plan SHA-256:** 7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1
- **Baseline đề xuất:** branch feature/feat063-be-foundation; HEAD dd70685eae58aaaefea3e567f5c23d09345a8513; index rỗng. Approval thực thi phải pin lại; lệch thì dừng và xin xác nhận.
- **Owner directions:** D-144, D-148, D-150, D-151; D-150 chỉ đóng S0-doc; D-151 chỉ chấp nhận Draft 10 làm planning baseline. Không pha implementation nào được mở.
- **S0-doc evidence:** evidence/M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md, SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001.

## Approved scope đề xuất — chưa có hiệu lực

Một lượt owner-run chỉ đọc để thu thập inventory metadata, row counts, grouped origin counts và các kiểm tra dưới đây. Không đọc giá trị hàng, không sửa schema/dữ liệu, không cleanup 58 synthetic rows, không chạy migration và không dùng database write-phase. Database riêng cho S1a/S2 nằm ngoài phạm vi.

- **Existing files permitted to modify:** none.
- **Script input:** evidence/scripts/m2_s0_owner_run_readonly_20261107_r3.py; không chỉnh sửa script trong lượt owner-run.
- **Output files chỉ được tạo sau approval riêng:** inventory.json và inventory.txt trong thư mục run mới dưới .claude/handoff/logs/; mypy-*.txt và alembic-*.txt chỉ nếu owner chọn/duyệt đúng phương án; mypy cache chỉ ngoài repository.
- Việc đọc .gitignore để xác nhận log local được ignore nằm ngoài allowlist Draft 10 §8. Đây là mở rộng rủi ro thấp; owner phải chấp thuận rõ trong approval thực thi. Không chấp thuận thì không chạy script.
- Script chỉ tạo output không ghi đè; nếu không thể tạo đủ hai artifact thì dừng an toàn, không giữ file dở dang.

## Các trường owner bắt buộc điền trước approval thực thi

Không ghi URL kết nối, mật khẩu hoặc token vào hồ sơ. Không để trống trường bắt buộc trong approval thực thi.

| Trường | Giá trị do owner cung cấp |
|---|---|
| Tên database BE tổng | OWNER ĐIỀN |
| Tên Docker container/service BE tổng và cách owner tự xác minh container | OWNER ĐIỀN |
| Baseline manifest: database name, revision, schema count, table count, tổng row count | OWNER ĐIỀN |
| Host/port/user trong shell riêng của owner; không ghi password hoặc URL | OWNER ĐIỀN |
| Người trực tiếp chạy từng lệnh | OWNER ĐIỀN |
| Tên dump file ngoài repository và SHA-256 | OWNER ĐIỀN |
| Restore trial đã chạy chưa, kết quả và người xác nhận | OWNER ĐIỀN |
| Người chịu trách nhiệm bảo toàn DB và khôi phục nếu cần | OWNER ĐIỀN |
| Số lần tối đa và timeout riêng cho từng command ở §4 | OWNER ĐIỀN |
| Danh sách các bảng tạo nên con số 58 synthetic rows; ý nghĩa và cách tránh cộng trùng thực thể | OWNER ĐIỀN |
| Tổng row count đo được trong inventory, bao gồm các hàng ngoài 58 synthetic rows | OWNER ĐIỀN |
| Bằng chứng synthetic-only cho từng bảng không có provenance đáng tin cậy | OWNER ĐIỀN |
| Lựa chọn Alembic K3: P1 static-AST / P2 owner-run CLI / K3 NOT RUN | OWNER CHỌN, để trống đến khi owner quyết |
| Nếu chọn P1: chấp thuận mở read-only allowlist từ 9 lên đúng 28 revision files bên dưới | OWNER CHỌN, để trống |
| Nếu chọn P2: chấp thuận phạm vi rộng hơn, process riêng, cấu hình hiệu lực và owner attestation cùng target | OWNER CHỌN, để trống |
| Nếu cần nonlocal host: lý do và chấp thuận cờ --allow-nonlocal-host | OWNER ĐIỀN; mặc định từ chối |
| Mypy command candidate, interpreter/version và timeout | OWNER CHỌN, để trống |
| Hash script sau independent review, ghi ngay trước approval thực thi | OWNER ĐIỀN SAU REVIEW |
| Chấp thuận script đọc .gitignore ngoài allowlist Draft 10 §8 | OWNER CHỌN, để trống |

Ghi chú lịch sử, không phải bằng chứng hiện tại: hồ sơ A2/FEAT-064 từng báo 24 hàng trước lỗi teardown PostgreSQL và 82 hàng sau lỗi (+58). Owner phải xác nhận lại, không dùng số cũ làm baseline.

## Ba lựa chọn Alembic K3 — không có lựa chọn mặc định

Không lựa chọn nào được đánh dấu sẵn. Chỉ phương án được ghi rõ trong approval riêng mới được thực hiện.

### P1 — Static AST trên 28 revision files

Script đọc bytes và SHA-256 của đúng 28 file revision dưới đây, sau đó phân tích AST/literal metadata mà không import revision hoặc application modules. Script kiểm tra exact manifest, từng hash, revision identifiers, down_revision, depends_on, branch_labels, dependency closure và chu trình. Nếu manifest/hash/AST/graph không xác minh được, K3 = NOT RUN; không tự dò thêm file.

Draft 10 §8 liệt kê 9 revision modules. P1 cần thêm 19 file chỉ đọc để xem toàn graph; chỉ dùng P1 nếu owner chấp thuận rõ allowlist đúng 28 file và approval thực thi ghim đủ manifest/hash.

| Revision file | SHA-256 |
|---|---|
| backend/alembic/versions/20261014_0001_core_persistence.py | 55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C |
| backend/alembic/versions/20261014_0002_be1_runtime.py | 08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520 |
| backend/alembic/versions/20261014_0003_canvas_payload.py | 194A831C661CA84C796557CCCF762715F6C0CC0E747521D588D1F30E1A5BB9E5 |
| backend/alembic/versions/20261014_0004_be1_constraint_names.py | AB15DFCE0738D994B14B337A03B34F7365BBBC67AFFE3BB01F24901F87BAFFFD |
| backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py | D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714 |
| backend/alembic/versions/20261017_ap_0001_policy_lifecycle.py | 81F84E9B3C4C7929018EB0A82ABED1DC2581811BB178EC6097E3134BBD8D765A |
| backend/alembic/versions/20261017_ap_0002_effective_scope.py | 35DBAA33A4F41EC69A01E03D688AF9B9238145EE0006D54CA67C115D0987CDE7 |
| backend/alembic/versions/20261017_ap_0003_resource_ledger.py | FEE3A90E27691B90B1D45E6DE7D14C3DB77311EBE86414051B55C75D02AB1924 |
| backend/alembic/versions/20261017_ap_0004_copy_inventory.py | 3EC8747A198941C9C4B36C4FDD0E08986355F0B2334589951EEA99BBF20AC2E7 |
| backend/alembic/versions/20261017_ap_0005_copy_evidence.py | 9E364BF938C2D6B6714FDE8C2A2527AAB84D3DD378C1AE16C0578FD86B9B8C12 |
| backend/alembic/versions/20261017_lc_0001_content_publication.py | DA2B372442A7CF234B8C1FC0FC7472B5A068FE8F832B6465C1BC1E4D2FE2F498 |
| backend/alembic/versions/20261018_ap_0006_copy_operations.py | B266744B3792E0E68347FA674B374A54D14CC33E4776106ADE91E2E407C447F7 |
| backend/alembic/versions/20261018_ap_0007_copy_delivery.py | 3BF400A165F5D681017FFE1AADEEAEB724BFFF5992289FB21331F5247C479E52 |
| backend/alembic/versions/20261018_ap_0008_delivery_authority.py | 9D8171F8B00C603FD350E32B6D6412B049A504F47B4D4F92355D654C86B71E05 |
| backend/alembic/versions/20261018_ap_0009_copy_resolution.py | 465A3421BC54895D2969AE95B1E3A9425689D1ED38B1CD6BCD8FE29D9B961A44 |
| backend/alembic/versions/20261018_kv_0001_knowledge_video.py | E7EFE124ECBFC5D1E280529DBA3B05EB2B00DCE04C24BF9EAC11BCE516B15D87 |
| backend/alembic/versions/20261018_vr_0001_video_review.py | 3E489443949C0934B414E4A69C6BD01B09782F4653042803C79291D66B415FC7 |
| backend/alembic/versions/20261019_ae_0001_activity_execution.py | 56993DC8CE1507D471ED3E3052F99A3A05B9D26C64E979822198946CD9EF9C30 |
| backend/alembic/versions/20261019_pa_0001_preset_automation.py | D2A8B958D6BD9411D040E3358F5568E2C728C1095D5395D55532916ACC5182E8 |
| backend/alembic/versions/20261019_vf_0001_video_failure.py | 0520CB0EB850D1BB4A267571F30937677908E505B77E221D1F0C90EE806FD178 |
| backend/alembic/versions/20261024_0005_classroom_srs_contracts.py | E533FC15447222C334A82CD162DC01FEB7B94221B402552D774CBD11E7D7289C |
| backend/alembic/versions/20261028_ll_0001_lesson_library.py | 733836723A95834C721E6CD0CA3527D73EA6EFE089B2F109A956EA484DFE1D83 |
| backend/alembic/versions/20261031_be1_synthetic_eligibility.py | 421F695FE49193C4A2EDCAC66B4461D8AFCB47B825813918E0083B21BC1483FC |
| backend/alembic/versions/20261101_be1_age_provenance.py | 2A634DC4DDF00326AFEF4079F7795A185D458DE2DB65BA6FD3C40291BBA5614E |
| backend/alembic/versions/20261102_pilot_vision.py | 6335AD224708AEC8251447A296458854B663FC7DD763EFB184E4AFF156E86BD9 |
| backend/alembic/versions/20261102_story_run_lite.py | D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143 |
| backend/alembic/versions/20261103_story_upload_compat.py | F16346F5D0D320B22AF0767F387FE066ED3683D57DDD380804424B5A837CA166 |
| backend/alembic/versions/20261104_story_revisions.py | 3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8 |

### P2 — Owner-run Alembic CLI trong process riêng (scope mở rộng; không mặc định)

P2 cần owner chọn và chấp thuận riêng trong approval thực thi; đây không phải lối thoát hẹp cho P1. Source Alembic 1.19.1 cho thấy heads nạp revision modules; current chạy backend/alembic/env.py, cấu hình ứng dụng, import metadata của nhiều module sketch2life.* ngoài allowlist Draft 10 §8, tạo SQLAlchemy engine và mở connection. Không chạy upgrade, downgrade, stamp, revision hoặc migration test.

#### Ngữ pháp output đã suy từ source (chưa chạy CLI)

Nguồn đã đọc: alembic/script/base.py:273-275, 356-378, 903-956; alembic/command.py:632-656, 688-727; alembic/script/revision.py:201-260, 314-356, 666-677, 848-867, 1520-1528, 1640-1695; alembic/runtime/migration.py:205-215, 601-604; backend/alembic.ini:26-39; 28 revision files trong manifest §P1. Đây là suy luận từ mã Alembic 1.19.1 và bytes revision đã pin; chưa có lệnh heads/current nào được chạy trong lượt soạn này.

Revision ID chỉ được lấy trong tập 28 ID sau:

~~~text
20261014_0001, 20261014_0002, 20261014_0003, 20261014_0004,
20261015_ai_0001,
20261017_ap_0001, 20261017_ap_0002, 20261017_ap_0003,
20261017_ap_0004, 20261017_ap_0005, 20261017_lc_0001,
20261018_ap_0006, 20261018_ap_0007, 20261018_ap_0008,
20261018_ap_0009, 20261018_kv_0001, 20261018_vr_0001,
20261019_ae_0001, 20261019_pa_0001, 20261019_vf_0001,
20261024_0005, 20261028_ll_0001, 20261031_be1_se_0001,
20261101_be1_age_0001, 20261102_pv_0001,
20261102_story_run_lite, 20261103_story_upload_compat,
20261104_story_revisions
~~~

Branch label chỉ được lấy trong tập: activity_execution, ai_jobs, ai_policy, be1_core, knowledge_video, learning_content, lesson_library, pilot_vision, preset_automation, story_run_lite, video_failure, video_review. Nhãn ở head có thể được kế thừa từ revision gốc theo revision.py:_add_branches; không được nhận nhãn ngoài tập này.

Ngữ pháp nonverbose được phép:

~~~text
HEADS_LINE :=
  REVISION_ID " (" BRANCH_LABEL ")" " (" ("head" | "effective head") ")"

CURRENT_LINE :=
  REVISION_ID
  [ " (" ("head" | "effective head") ")" ]
  [ " (branchpoint)" ]
  [ " (mergepoint)" ]
~~~

Với heads, command.py gọi cmd_format(verbose=False, include_branches=True, tree_indicators=False): nhãn nhánh và đúng một marker head/effective head có thể xuất hiện; branchpoint, mergepoint, current không được xuất hiện. Tập dòng phải khớp chính xác 12 dòng dự kiến sau (so sánh như tập, không phụ thuộc thứ tự):

~~~text
20261015_ai_0001 (ai_jobs) (effective head)
20261017_lc_0001 (learning_content) (head)
20261018_ap_0009 (ai_policy) (head)
20261018_kv_0001 (knowledge_video) (head)
20261018_vr_0001 (video_review) (head)
20261019_ae_0001 (activity_execution) (head)
20261019_pa_0001 (preset_automation) (head)
20261019_vf_0001 (video_failure) (head)
20261028_ll_0001 (lesson_library) (head)
20261101_be1_age_0001 (be1_core) (effective head)
20261102_pv_0001 (pilot_vision) (effective head)
20261104_story_revisions (story_run_lite) (head)
~~~

Với current, command.py gọi cmd_format(verbose=False), không yêu cầu branch labels; base.py bật tree indicators nên branchpoint/mergepoint có thể là hậu tố. Marker current chỉ được in nếu _db_current_indicator được đặt. Trong code path current của phiên bản đã pin, command.current không đặt marker này; nếu quan sát được (current), coi là dòng lạ và NOT RUN cho tới khi source được kiểm lại và re-pin. Dòng stdout phải parse thành revision IDs thuộc tập 28 ở trên, không trùng; không có dòng rỗng xen giữa hay nội dung phụ. Output current không được so trực tiếp như danh sách thô với hàng alembic_version: get_all_current mở rộng version rows qua ancestors/dependencies rồi lọc branch heads. Chỉ đối chiếu nếu có thể tái tạo chính xác tập dòng từ các version rows trong inventory theo đúng thuật toán nguồn nêu trên; nếu không, K3 = NOT RUN.

Heads mặc định trả 12 versioned heads; ba dòng đánh dấu effective head là revision chỉ được giữ làm head do phụ thuộc. Chín dòng đánh dấu head tương ứng chín effective source heads mà P1 tính từ down_revision + depends_on. K3 P2 chỉ được PASS nếu: (a) heads khớp đủ 12 dòng chính xác; (b) current khớp đầy đủ phép chiếu get_all_current của raw database_alembic_versions; và (c) raw database_alembic_versions khớp đúng chín ID có marker head, không gồm ba effective head. Output hợp lệ nhưng trạng thái DB khác chín effective heads thì K3 = FAIL; không parse được, thiếu/thừa dòng, không xác định được current projection, hoặc thiếu version rows thì K3 = NOT RUN.

Alembic.ini dùng formatter %(levelname)-5.5s [%(name)s] %(message)s và console StreamHandler tới stderr. Trong current, hai dòng INFO được source migration.py tạo ra và có thể bỏ qua khi khớp nguyên văn, đúng thứ tự:

~~~text
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
~~~

stderr của heads phải rỗng. stderr của current chỉ được rỗng hoặc đúng hai dòng INFO trên. Mọi dòng stderr khác, kể cả warning/traceback/native-command error, làm command đó NOT RUN. Không ghi, không hiển thị và không đưa stderr thô vào báo cáo. Các dòng INFO được phép chỉ giữ trong memory rồi bỏ, không lưu ra file.

#### Cách capture bắt buộc trên PowerShell 5.1

Mỗi command chạy trong System.Diagnostics.Process với UseShellExecute=false và RedirectStandardOutput/RedirectStandardError=true; mở ReadToEndAsync cho cả hai stream đồng thời, rồi WaitForExit theo timeout riêng đã duyệt để tránh pipe deadlock. Không dùng native redirection 2>&1, Tee-Object, transcript, redirect ra file hoặc pipeline PowerShell cho stderr: PowerShell 5.1 có thể chuyển native stderr thành ErrorRecord/NativeCommandError, làm biến dạng output và exit handling. Không in raw stdout/stderr. Chỉ sau khi exit code = 0 và toàn bộ output vượt whitelist mới ghi revision lines đã lọc cùng exit status; stdout rỗng, stderr lạ, output rỗng, revision ID ngoài tập, dòng trùng hoặc thiếu head/current revision theo phép đối chiếu ⇒ NOT RUN, không lưu raw.

Command candidate, chạy từ backend trong process riêng, không thêm --verbose:

~~~powershell
& .\.venv\Scripts\python.exe -m alembic -c .\alembic.ini heads
& .\.venv\Scripts\python.exe -m alembic -c .\alembic.ini current
~~~

Mỗi lệnh chỉ chạy số lần và timeout do owner điền riêng. Filtered output và exit status có thể lưu tách trong các file alembic-heads.filtered.txt / alembic-current.filtered.txt; raw stdout/stderr không được lưu. Không dùng current --verbose vì code verbose in URL đã che password nhưng vẫn lộ thông tin đích.

#### Cấp cấu hình, target và quyền tối thiểu P2

P2 current dùng SKETCH2LIFE_DATABASE_URL trong process environment vì backend/alembic/env.py gọi get_core_database_settings().database_url. Không ghi URL vào command history, file, log, chat hoặc transcript; owner nhập trong shell riêng và chỉ giữ trong process memory. settings.py cho phép đọc backend/.env hoặc .env theo current working directory; process environment ưu tiên hơn file. Checkbox attestation P2 ở §Tiền điều kiện là bắt buộc riêng: owner phải xác nhận cấu hình hiệu lực của child process nhắm cùng database đã qua K1 và không có .env/environment source lệch target. K1 chỉ kiểm current_database() của script B, không ràng buộc connection mà Alembic current tự mở.

Theo đọc backend/alembic/env.py: import settings và các module metadata, lấy cấu hình database, tạo engine NullPool, mở connection, configure Alembic context rồi gọi context.run_migrations(). command.current truyền callback chỉ đọc version state và dont_mutate=True; runtime/migration.py dùng cờ này để không tự tạo alembic_version khi DB chưa có version rows. Đây là source inference, chưa chạy. env.py không bật transaction/session read-only; do đó current chạy NGOÀI K2/read-only safeguard của script B, dù không gọi upgrade/downgrade và không chạy migration functions. Không chạy current nếu không có cấu hình đích được owner attestation và role read-only.

Quyền tối thiểu đề xuất: script B cần CONNECT, USAGE trên schema được kiểm kê và SELECT trên các bảng mà nó đếm/đọc, gồm public.alembic_version; không cần INSERT/UPDATE/DELETE/CREATE/DDL. Alembic current cần CONNECT, USAGE trên schema của alembic_version và SELECT trên version table; hệ thống catalog cần đọc theo mặc định PostgreSQL. Owner phải xác nhận quyền thực tế, ưu tiên role chỉ đọc; không dùng quyền ghi để vượt lỗi. Nếu không xác minh được quyền tối thiểu thì K3 P2 NOT RUN.

### K3 NOT RUN

Chỉ lựa chọn này nằm trọn trong 9 revision modules của Draft 10 §8: script không đọc revision files ngoài allowlist và không chạy Alembic CLI. K3 vẫn NOT RUN; không suy diễn database head.

#### Cảnh báo phương pháp 9 so với 12

Theo source Alembic 1.19.1 đã đọc và metadata 28 revision files, đây là suy luận chưa chạy: normal alembic heads chỉ xét down_revision có thể trả 12 heads, thêm 20261101_be1_age_0001, 20261015_ai_0001 và 20261102_pv_0001; P1 kết hợp down_revision với depends_on nên có thể trả 9 effective heads. Hai số dùng phương pháp khác nhau, không tự chứng minh DB lệch. Đây không phải kết quả đã chạy Alembic và không chấp nhận K3.

## Draft 3 behavior updates for N-2 through N-7

### Mã thoát và trạng thái gate

| Mã thoát | Ý nghĩa |
|---:|---|
| 0 | Cặp report được ghi; không có nghĩa K5 PASS hay approval/acceptance. |
| 2 | Python version guard hoặc controlled stop trước khi tạo output directory. |
| 3 | K2_READ_ONLY_GATE_FAILED. |
| 4 | K1_IDENTITY_GATE_NOT_CONFIRMED; detail cố định, không ghi tên database thực tế. |
| 5 | Safe stop sau khi output directory đã được tạo, gồm K5 timeout/gate. |
| 6 | Unexpected safe exception đã được chuẩn hóa. |
| 7 | Rollback không được xác nhận khi chưa có exit code ưu tiên cao hơn. |
| 8 | Connection close không được xác nhận khi chưa có exit code ưu tiên cao hơn. |
| 9 | Không ghi được cặp report JSON/TXT khi chưa có exit code ưu tiên cao hơn. |
| 130 | Interrupted. |

K2/K1 set mã riêng 3/4 và handler SafeStop chỉ gán mã tổng quát khi chưa có mã, nên không ghi đè 3/4 thành 5. Nếu rollback/close hoặc ghi report lỗi sau một gate cụ thể, mã gate 3/4 được giữ làm nguyên nhân chính; code 7/8/9 chỉ dùng khi chưa có mã cụ thể trước đó.

K2 chạy trước K1. Nếu K2 fail: K2 = FAIL; K1 và K3–K7 = NOT RUN, detail STOPPED_AFTER_K2. Nếu K1 mismatch sau khi K2 đã PASS: K1 = FAIL với detail cố định DATABASE_NAME_MISMATCH; ACTUAL_NAME_WITHHELD; K2 vẫn PASS vì đã thực sự chạy và đạt trước đó; K3–K7 = NOT RUN, detail STOPPED_AFTER_K1. Không ghi tên database thực tế đọc được vào detail hoặc field khác ngoài tên database kỳ vọng do owner nhập.

### Host option, Python và K5 timeout

argparse dùng allow_abbrev=False. Mặc định chỉ chấp nhận literal loopback IP hoặc tên localhost viết chính xác (không DNS resolve); cờ --allow-nonlocal-host cần --nonlocal-host-reason riêng. JSON và TXT luôn có nonlocal_host_flag_used: true/false; nếu cờ bật, có thêm lý do owner cung cấp đã chuẩn hóa, scrub target values/path/IP/domain/URL và cắt tối đa 160 ký tự. Lý do không chứa URL. Không thêm inet_server_addr(); địa chỉ container qua mapped port không phải bằng chứng loopback.

Python version guard phải chạy ngay sau import sys và trước import thư viện khác; Python khác 3.12 chỉ in STOPPED_SAFELY: PYTHON_312_REQUIRED, không traceback/đường dẫn. Script vẫn phải chạy bằng Python 3.12 của backend venv: cú pháp yêu cầu từ interpreter cũ có thể gây SyntaxError lúc compile trước khi guard chạy; guard không bắt được lỗi biên dịch.

Timeout cố định nội bộ đọc từ script: statement_timeout = 20.000 ms, lock_timeout = 3.000 ms, connect_timeout = 5 giây. COUNT(*) trên bảng lớn hoặc GROUP BY data_origin có thể phát sinh QueryCanceled/QUERY_TIMEOUT. Khi xảy ra, K5 và đúng bảng/operation đó là NOT RUN, detail QUERY_TIMEOUT; không suy ra bảng rỗng hoặc synthetic-only và không ghi count chưa thu được. K5 không bao giờ PASS; detail cuối không giả định tổng 58 là tổng DB.

## Tiền điều kiện và identity

Trong approval thực thi, owner đánh dấu từng điều kiện ĐÃ XONG hoặc CHƯA XONG. Bất kỳ điều kiện bắt buộc nào CHƯA XONG thì không chạy:

- [ ] OWNER XÁC NHẬN: dump/restore point ngoài repo; ghi tên file/hash dump và đã thử restore hay chưa.
- [ ] OWNER XÁC NHẬN: container, database và identity manifest khớp target đã duyệt.
- [ ] OWNER XÁC NHẬN RIÊNG CHO P2: cấu hình hiệu lực của alembic current mà process kế thừa là cùng target đã qua K1; owner đã kiểm tra .env và process environment, không có nguồn cấu hình nào làm lệch target giữa K1 và P2.
- [ ] OWNER XÁC NHẬN: database chỉ dùng cho inventory read-only, không phải write-phase.
- [ ] OWNER XÁC NHẬN: role có quyền tối thiểu cần thiết.
- [ ] OWNER XÁC NHẬN: password chỉ nhập tại getpass ẩn; không command line, env, file, log hoặc chat.
- [ ] OWNER XÁC NHẬN: PGHOST, PGPORT, PGUSER trong shell riêng đúng target; không có biến password/service/file/options override.
- [ ] OWNER XÁC NHẬN: script chạy trong shell riêng không chứa biến môi trường nào có ://; chặn rộng là chủ ý và có thể từ chối vì biến không liên quan, khi đó phải dùng shell sạch.
- [ ] OWNER XÁC NHẬN: .claude/handoff/logs/ đang bị ignore; chấp thuận script đọc .gitignore ngoài allowlist Draft 10 §8.
- [ ] OWNER XÁC NHẬN: git status trên backend/alembic/versions sạch trước khi chạy.
- [ ] OWNER XÁC NHẬN: đã xác định các bảng tạo nên 58 synthetic rows và có bằng chứng cho bảng thiếu provenance.
- [ ] OWNER XÁC NHẬN: đã chọn K3 hoặc ghi K3 NOT RUN; không suy ra lựa chọn.
- [ ] OWNER XÁC NHẬN nếu dùng nonlocal host: chỉ bật --allow-nonlocal-host khi lý do ghi trong approval; mặc định script từ chối host không loopback.
- [ ] OWNER XÁC NHẬN nếu bật --allow-nonlocal-host: đã cung cấp --nonlocal-host-reason ngắn, không chứa URL hay thông tin target.
- [ ] OWNER XÁC NHẬN: mypy command/version/cache/timeout đã duyệt hoặc mypy để NOT RUN.

K1 chỉ so tên current_database() với tên owner duyệt. Nó không xác minh Docker container, host/port/user, revision head, schema/table count hoặc tổng row count. Container khác có DB trùng tên vẫn có thể qua K1. Sau khi chạy, owner đối chiếu riêng manifest (database name, revision, schema count, table count, tổng row count) và tự xác minh container bằng phương thức riêng. Không gọi đây là full identity PASS chỉ vì tên database khớp.

## Command ceiling đề xuất — chưa được chạy

Các command chỉ có hiệu lực sau review độc lập, owner điền trường bắt buộc, chọn K3, pin hash script và ghi approval riêng. Owner phải điền số lần/timeout; không có mặc định. Lỗi, timeout hay output thiếu đều dừng.

### 1. Inventory script B

Python 3.12 trong backend virtual environment; mật khẩu hỏi ẩn. Placeholder chỉ được thay trong approval cuối:

    & .\backend\.venv\Scripts\python.exe .\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s0_owner_run_readonly_20261107_r3.py --expect-db {OWNER_DB_NAME} --out-dir .claude\handoff\logs\{OWNER_RUN_ID} --alembic-method {OWNER_CHOICE_STATIC_AST_OWNER_CLI_OR_NOT_RUN}

Chỉ thêm --allow-nonlocal-host khi owner đã ghi lý do và được chấp thuận riêng. Output directory phải mới. Script chạy K2 trước K1: SHOW transaction_read_only phải trả on trước mọi query khác. K4/K6 chỉ COLLECTED, không PASS. K5 không bao giờ PASS; chỉ GROUP BY cột data_origin; bucket thành SYNTHETIC_DEV/REAL/LEGACY_UNCLASSIFIED/NULL/EMPTY/OTHER; bucket không synthetic gây FAIL/STOP, thiếu provenance/proof thì NOT RUN.

### 2. Mypy version và baseline (candidate, không phải command chuẩn repo)

Chưa xác định command mypy chuẩn trong hồ sơ đã đọc. Owner phải xác nhận interpreter, version, package scope, timeout. Cache ngoài repo. Chạy trong shell con để cô lập import path. Nếu chạy cùng shell, lưu rồi phục hồi PYTHONPATH/MYPYPATH trong finally ngay sau mypy và trước Alembic.

    & .\.venv\Scripts\python.exe -m mypy --version

    & .\.venv\Scripts\python.exe -m mypy --package sketch2life --config-file .\pyproject.toml --no-incremental --cache-dir "$env:TEMP\s2l-mypy-s0-owner-run"

Mypy crash/timeout/no verdict = NOT RUN, không PASS. D-144 §9.6 yêu cầu ghi command/version; M2 không thêm diagnostic so baseline.

## Diễn giải gates và giới hạn inventory

| Gate | Bằng chứng / ý nghĩa | Kết quả được phép ghi |
|---|---|---|
| K1 — Database name | So current_database() với tên owner duyệt; không kiểm container/full manifest. | Mismatch hoặc không đọc được: STOP. Match chỉ là name check. |
| K2 — Read-only | default_transaction_read_only=on và connection.read_only=True trước SQL đầu tiên; SHOW transaction_read_only là SQL đầu và phải trả on. | Không xác nhận on: STOP, không query tiếp. |
| K3 — Alembic | So DB revision rows với P1 static-AST hoặc filtered P2 output; K3 NOT RUN là lựa chọn hợp lệ. | Không migrate/stamp. Manifest/hash/graph/output sai hoặc thiếu: NOT RUN. |
| K4 — Schema inventory | Thu schema, regular/partitioned tables, columns, types, nullability/defaults, constraints/indexes; chưa so source metadata. | Chỉ COLLECTED. information_schema.columns có thể ẩn cột nếu role thiếu quyền. Partition child có thể vừa được đếm riêng vừa nằm trong parent count, nên tổng row counts có thể chồng lấp. |
| K5 — Synthetic-only | COUNT(*) theo table; chỉ GROUP BY data_origin nếu có đúng cột; không chọn row values. age_source và cột tương tự không phải proof. | Không bao giờ PASS. Non-synthetic/NULL/EMPTY/OTHER: FAIL/STOP. Thiếu data_origin hoặc owner proof: NOT RUN. Owner xác định bảng tạo nên 58 rows và tránh cộng trùng thực thể. |
| K6 — CHECK definitions | Thu định nghĩa CHECK để đối chiếu riêng. | Chỉ COLLECTED; không diễn giải đúng/sai, không PASS. |
| K7 — Mypy | Owner-run baseline, command/version/checkout/cache/timeout được ghi. | Verdict thật mới là baseline; crash/timeout/no verdict = NOT RUN. |

information_schema.columns chỉ hiện cột mà role được phép nhìn thấy; inventory có thể thiếu cột. Với partitioned tables, table cha có thể đếm hàng thuộc các partition trong khi partition con cũng xuất hiện và được đếm riêng. Không cộng tổng row counts thành số thực thể unique.

## Hard stop và exclusions

- Thiếu owner field, dump hash/restore disposition, target/container identity, synthetic-only proof, timeout/ceiling, K3 choice, hash script đã review hoặc Task Approval: không chạy.
- K1/K2 không đạt; non-synthetic origin; revision/hash/manifest không xác minh; quyền quá rộng; yêu cầu write/migration/cleanup hoặc đọc row values: STOP. Không đổi shell/connection để lách.
- Safety check không có verdict = NOT RUN; dừng đúng cổng.
- Không ghi row data, child data, URL kết nối, mật khẩu, token, host/port/user thật hoặc đường dẫn tuyệt đối vào output/chat/Git.
- Không cleanup 58 synthetic rows; không đổi schema, DB, migration, source, test, policy hoặc route.
- Không Modal/provider; OWNER_MODAL_CALL_APPROVED=NO.
- Không stage/commit/push/merge.

## Lưu trữ và pin

Script ứng viên nằm tại evidence/scripts/m2_s0_owner_run_readonly_20261107_r3.py. Đây là vị trí lâu dài cho script đã review; owner-run chỉ đọc/chạy, không sửa. Hash candidate sau review để trống trong bản nháp; owner ghi hash bytes ở đúng path này vào Task Approval thực thi sau independent review. Bất kỳ byte nào thay đổi sau khi pin làm approval vô hiệu và cần review/approval lại.

Inventory và logs chỉ lưu trong run directory mới dưới .claude/handoff/logs/; mypy cache chỉ ngoài repository. Sau đó chỉ hash, exit status và verdict đã lọc mới được ghi hồ sơ. Không commit runtime artifacts.

## Nguồn, baseline và trạng thái

- Draft 10 §8 liệt kê 9 revision files; P1 đề xuất 28 file ở manifest trên và cần owner duyệt mở rộng.
- backend/alembic.ini để URL tĩnh trống; backend/alembic/env.py dùng cấu hình ứng dụng.
- settings.py chọn file backend/.env và .env theo current working directory; process environment ưu tiên hơn file.
- Source Alembic 1.19.1 và revision metadata đã được đọc; nhận định 9/12 heads là suy luận, chưa chạy CLI.
- Không xác minh DB identity/data, restore, synthetic-only proof, baseline mypy hoặc migration state.
- S0-doc đã đóng ở phạm vi tài liệu theo D-150; S0-owner-run chưa mở. S1a, S1b, S2, S3 và M3–M6 vẫn đóng. Không implementation approval.

## Điều kiện hiệu lực

- **Exit criteria:** script và approval được independent review; owner điền target/restore/synthetic proof/command ceilings/K3/mypy và chọn; hash script được pin; các attestation có bằng chứng; safety check NOT RUN không được tính PASS.
- **Stop gate:** pin/manifest/identity/output/permission/hash lệch, thiếu verdict hoặc cần ghi DB thì dừng và báo, giữ nguyên DB; không thử phương án khác.
- **Validity:** bản này chỉ là DRAFT, không cấp quyền chạy S0-owner-run. Approval thực thi là mục riêng append-only được owner duyệt sau independent review. Mỗi pha sau cần Task Approval riêng.
- **Approval basis:** yêu cầu owner soạn bản sửa, hội thoại 2026-11-07; Draft 10 SHA-256 ở trên.
- **OWNER_MODAL_CALL_APPROVED=NO.**

> Draft 3 chưa được independent reviewer chấp nhận, chưa được owner duyệt và không cho phép kết nối DB hay chạy lệnh.

