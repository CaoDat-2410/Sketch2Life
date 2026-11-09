# M2 S0-owner-run Task Approval — Draft 2

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
- **Script input:** evidence/scripts/m2_s0_owner_run_readonly_20261107.py; không chỉnh sửa script trong lượt owner-run.
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
| Các bảng tạo nên con số 58 synthetic rows, ý nghĩa của con số, cách tránh cộng trùng thực thể | OWNER ĐIỀN |
| Bằng chứng synthetic-only cho từng bảng không có provenance đáng tin cậy | OWNER ĐIỀN |
| Lựa chọn Alembic K3: P1 static-AST / P2 owner-run CLI / K3 NOT RUN | OWNER CHỌN, để trống đến khi owner quyết |
| Nếu chọn P1: chấp thuận mở read-only allowlist từ 9 lên đúng 28 revision files bên dưới | OWNER CHỌN, để trống |
| Nếu chọn P2: chấp thuận phạm vi rộng hơn, process riêng, cấu hình hiệu lực và owner attestation cùng target | OWNER CHỌN, để trống |
| Nếu cần nonlocal host: lý do và chấp thuận cờ --allow-nonlocal-host | OWNER ĐIỀN; mặc định từ chối |
| Mypy command candidate, interpreter/version và timeout | OWNER CHỌN, để trống |
| Hash script sau independent review, ghi ngay trước approval thực thi | OWNER ĐIỀN SAU REVIEW |
| Chấp thuận script đọc .gitignore ngoài allowlist Draft 10 §8 | OWNER CHỌN, để trống |

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

### P2 — Owner-run Alembic CLI trong process riêng

Đây là phạm vi rộng hơn P1, không phải lối thoát hẹp. alembic heads nạp/thực thi các revision modules trong graph; alembic current thực thi backend/alembic/env.py, đọc cấu hình ứng dụng và import khoảng 20 module sketch2life.* ngoài allowlist Draft 10 §8. P2 cần chấp thuận riêng phạm vi rộng hơn trước khi dùng. Không chạy upgrade, downgrade, stamp, revision hoặc migration test.

Chạy heads và current trong PowerShell/process riêng sau khi owner cấp cấu hình kết nối chỉ trong process đó. Không dùng current --verbose. Source Alembic 1.19.1 đã đọc cho thấy successful nonverbose output chủ yếu là revision identifiers; không thể bảo đảm mọi stderr/exception path luôn sạch. Vì vậy, owner giữ toàn bộ stdout/stderr thô chỉ trong bộ nhớ, không Tee/transcript/redirect trực tiếp ra file và không hiển thị output thô. Chỉ ghi file nếu mọi dòng khớp chính xác revision identifier hoặc revision identifier cộng (head). Nếu exit code khác 0, output rỗng, có dòng lạ hoặc thiếu revision lines, chỉ ghi NOT RUN: OUTPUT_NOT_WHITELISTED_OR_INCOMPLETE; không lưu bất kỳ dòng thô nào. Lọc lỗi cũng là NOT RUN.

Command candidate, phải thay placeholder và pin số lần/timeout trong approval:

    & .\.venv\Scripts\python.exe -m alembic -c .\alembic.ini heads

    & .\.venv\Scripts\python.exe -m alembic -c .\alembic.ini current

Chạy từ backend; mỗi command có giới hạn lần và timeout riêng. Không dùng Tee-Object. Lưu filtered output và exit status tách biệt, không lưu host/port/user/URL hay đường dẫn tuyệt đối.

#### Cấp cấu hình P2 và kiểm soát target

P2 cần SKETCH2LIFE_DATABASE_URL trong process environment của shell riêng vì backend/alembic/env.py gọi get_core_database_settings().database_url. Không ghi URL vào command history, file, log, chat hoặc transcript; owner nhập qua prompt ẩn trong shell riêng và chỉ giữ trong process memory. Script inventory B chạy ở shell khác, không có biến môi trường nào chứa :// vì script cố ý chặn mọi biến giá trị như vậy.

settings.py khai báo file backend/.env và .env tương đối với current working directory; process environment ưu tiên hơn file. Owner phải xác nhận cấu hình hiệu lực trỏ đúng target được duyệt và không có file .env ngoài ý muốn làm lệch target. P2 dùng cùng target với K1 chỉ là CAM KẾT/ATTESTATION CỦA OWNER, không có kiểm tra tự động nối identity của Alembic với K1. K1 chỉ so current_database() với tên DB. Nếu owner không thể xác nhận cấu hình hiệu lực, không chạy P2.

### K3 NOT RUN

Chỉ lựa chọn này nằm trọn trong 9 revision modules của Draft 10 §8: script không đọc revision files ngoài allowlist và không chạy Alembic CLI. K3 vẫn NOT RUN; không suy diễn database head.

#### Cảnh báo phương pháp 9 so với 12

Theo source Alembic 1.19.1 đã đọc và metadata 28 revision files, đây là suy luận chưa chạy: normal alembic heads chỉ xét down_revision có thể trả 12 heads, thêm 20261101_be1_age_0001, 20261015_ai_0001 và 20261102_pv_0001; P1 kết hợp down_revision với depends_on nên có thể trả 9 effective heads. Hai số dùng phương pháp khác nhau, không tự chứng minh DB lệch. Đây không phải kết quả đã chạy Alembic và không chấp nhận K3.

## Tiền điều kiện và identity

Trong approval thực thi, owner đánh dấu từng điều kiện ĐÃ XONG hoặc CHƯA XONG. Bất kỳ điều kiện bắt buộc nào CHƯA XONG thì không chạy:

- [ ] OWNER XÁC NHẬN: dump/restore point ngoài repo; ghi tên file/hash dump và đã thử restore hay chưa.
- [ ] OWNER XÁC NHẬN: container, database và identity manifest khớp target đã duyệt.
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
- [ ] OWNER XÁC NHẬN: mypy command/version/cache/timeout đã duyệt hoặc mypy để NOT RUN.

K1 chỉ so tên current_database() với tên owner duyệt. Nó không xác minh Docker container, host/port/user, revision head, schema/table count hoặc tổng row count. Container khác có DB trùng tên vẫn có thể qua K1. Sau khi chạy, owner đối chiếu riêng manifest (database name, revision, schema count, table count, tổng row count) và tự xác minh container bằng phương thức riêng. Không gọi đây là full identity PASS chỉ vì tên database khớp.

## Command ceiling đề xuất — chưa được chạy

Các command chỉ có hiệu lực sau review độc lập, owner điền trường bắt buộc, chọn K3, pin hash script và ghi approval riêng. Owner phải điền số lần/timeout; không có mặc định. Lỗi, timeout hay output thiếu đều dừng.

### 1. Inventory script B

Python 3.12 trong backend virtual environment; mật khẩu hỏi ẩn. Placeholder chỉ được thay trong approval cuối:

    & .\backend\.venv\Scripts\python.exe .\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s0_owner_run_readonly_20261107.py --expect-db {OWNER_DB_NAME} --out-dir .claude\handoff\logs\{OWNER_RUN_ID} --alembic-method {OWNER_CHOICE_STATIC_AST_OWNER_CLI_OR_NOT_RUN}

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

Script ứng viên nằm tại evidence/scripts/m2_s0_owner_run_readonly_20261107.py. Đây là vị trí lâu dài cho script đã review; owner-run chỉ đọc/chạy, không sửa. Hash candidate sau review phải bằng bytes tại đúng path này và được owner ghi vào Task Approval thực thi. Bất kỳ byte nào thay đổi sau khi pin làm approval vô hiệu và cần review/approval lại.

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

> Draft 2 chưa được independent reviewer chấp nhận, chưa được owner duyệt và không cho phép kết nối DB hay chạy lệnh.

