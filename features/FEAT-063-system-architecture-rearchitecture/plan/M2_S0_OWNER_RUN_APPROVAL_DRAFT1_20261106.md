# M2 S0-owner-run Task Approval — Draft 1

**Status: DRAFT — chưa phải approval, chưa được owner duyệt, chưa khởi chạy.**  
Tài liệu này chỉ đề xuất một lượt owner-run chỉ đọc. Nó không sửa hoặc tạo approval có hiệu lực, không mở pha S0-owner-run, và không thay thế quyết định riêng của owner.

## 1. Mục tiêu và phạm vi đề xuất

Đề xuất đối soát **chỉ đọc** database BE tổng đang chạy trong Docker, theo hướng D-144 §9.1. Mục tiêu:

1. Thu thập inventory schema vật lý để coordinator đối chiếu với source sau đó; không sửa schema.
2. Đọc các revision đang có trong alembic_version, đối chiếu với head source theo một phương án Alembic do owner chọn.
3. Thu thập số đếm hàng và các giá trị provenance ở những bảng có cột data_origin, để đánh giá bằng chứng synthetic-only. Đây không tự chứng minh bảng không có provenance.
4. Chạy và ghi baseline mypy chỉ đọc theo D-144 §9.6; chưa có lệnh mypy chuẩn được xác định trong hồ sơ đã đọc, nên command candidate ở §4 phải được owner xác nhận trước khi dùng.

Không chạy migration, không ghi DB, không cleanup 58 hàng synthetic (D-144 §9.2), không thay đổi schema convergence (D-144 §9.5), và không dùng DB write-phase. Các database riêng cho S1a/S2 nằm ngoài phạm vi.

## 2. Trường owner phải điền hoặc chọn trước approval

Không để trống bất kỳ trường bắt buộc nào trong approval cuối. Không ghi credential hoặc connection URL vào hồ sơ.

| Trường | Giá trị owner cần cung cấp |
|---|---|
| Tên database đích chỉ đọc | **OWNER ĐIỀN:** |
| Tên Docker container/service xác nhận là BE tổng | **OWNER ĐIỀN:** |
| Identity/manifest baseline: tên DB, Alembic head hiện có, schema và số bảng, tổng số hàng theo inventory đã duyệt | **OWNER ĐIỀN:** |
| Host/port/user trong shell riêng của owner (không ghi password hoặc URL) | **OWNER ĐIỀN:** |
| Người trực tiếp chạy từng lệnh | **OWNER ĐIỀN:** |
| Dump/restore đã chuẩn bị; chỉ ghi tên file nằm ngoài repo, không ghi đường dẫn tuyệt đối hay dữ liệu dump | **OWNER ĐIỀN:** |
| Người chịu trách nhiệm kiểm tra restore và bảo toàn database | **OWNER ĐIỀN:** |
| Command ceiling: số lần tối đa và timeout của từng command tại §4 | **OWNER ĐIỀN:** |
| Phạm vi bảng owner xác nhận có 58 hàng synthetic theo D-144 §9.2, và ý nghĩa của con số 58 | **OWNER ĐIỀN:** |
| Bằng chứng owner về synthetic-only cho từng bảng không có cột provenance đủ tin cậy | **OWNER ĐIỀN:** |
| Phương án Alembic: P1 static AST / P2 owner-run CLI | **OWNER CHỌN:** |
| Nếu chọn P1: có cho phép đọc tĩnh toàn bộ 28 file revision hiện có không? | **OWNER CHỌN:** |
| Nếu chọn P2: xác nhận rõ alembic current sẽ kết nối qua cấu hình ứng dụng và cùng target đã qua K1 | **OWNER CHỌN:** |
| Mypy command candidate và timeout có được owner duyệt không? | **OWNER CHỌN:** |
| Hash script sau independent review, trước approval thực thi | **CHƯA TÍNH / OWNER GHI SAU REVIEW:** |

**Câu hỏi phạm vi cần giải quyết:** Draft 10 §8 liệt kê 9 revision modules (cộng env.py) trong allowlist S0-owner-run. P1 cần đọc tĩnh đủ 28 file revision trong backend/alembic/versions để tính heads của toàn graph; chỉ đọc 9 file không thể chứng minh đầy đủ source heads. Vì vậy, P1 chỉ được dùng nếu owner chấp thuận rõ việc mở rộng read-only source allowlist thành 28 file và approval thực thi liệt kê đúng toàn bộ manifest. Nếu không chấp thuận, chọn P2 hoặc để K3 là NOT RUN. Bản nháp này không tự mở rộng approval.

Manifest P1 đang được script ghim, cần owner/reviewer xem trước khi chọn:

- 20261014_0001_core_persistence.py
- 20261014_0002_be1_runtime.py
- 20261014_0003_canvas_payload.py
- 20261014_0004_be1_constraint_names.py
- 20261015_ai_0001_ai_jobs_schema.py
- 20261017_ap_0001_policy_lifecycle.py
- 20261017_ap_0002_effective_scope.py
- 20261017_ap_0003_resource_ledger.py
- 20261017_ap_0004_copy_inventory.py
- 20261017_ap_0005_copy_evidence.py
- 20261017_lc_0001_content_publication.py
- 20261018_ap_0006_copy_operations.py
- 20261018_ap_0007_copy_delivery.py
- 20261018_ap_0008_delivery_authority.py
- 20261018_ap_0009_copy_resolution.py
- 20261018_kv_0001_knowledge_video.py
- 20261018_vr_0001_video_review.py
- 20261019_ae_0001_activity_execution.py
- 20261019_pa_0001_preset_automation.py
- 20261019_vf_0001_video_failure.py
- 20261024_0005_classroom_srs_contracts.py
- 20261028_ll_0001_lesson_library.py
- 20261031_be1_synthetic_eligibility.py
- 20261101_be1_age_provenance.py
- 20261102_pilot_vision.py
- 20261102_story_run_lite.py
- 20261103_story_upload_compat.py
- 20261104_story_revisions.py

## 3. Tiền điều kiện do owner xác nhận

Mỗi dòng phải được owner đánh dấu **ĐÃ XONG** hoặc **CHƯA XONG** trong approval thực thi. Bất kỳ mục nào chưa xong thì không chạy lệnh:

- [ ] **OWNER XÁC NHẬN:** đã tạo dump/restore point bên ngoài repo và biết cách khôi phục.
- [ ] **OWNER XÁC NHẬN:** container, database và identity/manifest trùng target đã được duyệt.
- [ ] **OWNER XÁC NHẬN:** database này chỉ được dùng cho lượt inventory read-only; không phải database write-phase.
- [ ] **OWNER XÁC NHẬN:** user/role dùng cho kết nối chỉ có quyền cần thiết để đọc inventory; không dùng quyền ghi của ứng dụng nếu có lựa chọn an toàn hơn.
- [ ] **OWNER XÁC NHẬN:** mật khẩu sẽ được gõ riêng tại prompt ẩn của script; không truyền qua command line, environment, file, log hay chat.
- [ ] **OWNER XÁC NHẬN:** biến môi trường PGHOST, PGPORT và PGUSER trong đúng PowerShell session trỏ tới target; không có URL hoặc biến mật khẩu.
- [ ] **OWNER XÁC NHẬN:** .claude/handoff/logs/ đang bị ignore theo .gitignore; output sẽ không được commit.
- [ ] **OWNER XÁC NHẬN:** đã chốt phạm vi 58 hàng synthetic và có bằng chứng ngoài script cho các bảng không có origin field.
- [ ] **OWNER XÁC NHẬN:** đã chọn P1/P2 và giải quyết xung đột allowlist 9 so với 28 revision nếu chọn P1.
- [ ] **OWNER XÁC NHẬN:** đã chọn, kiểm tra và duyệt command mypy/version cùng timeout.

## 4. Command ceiling — đề xuất, chưa được phép chạy

Các lệnh dưới đây chỉ trở thành command ceiling sau khi owner điền database/timeout, chọn Alembic path, duyệt script hash sau review, và ghi approval riêng cho S0-owner-run. Không thay shell, không chạy lại khi lỗi, không tách/diễn đạt lệnh để vượt gate. Dấu ngoặc nhọn là placeholder phải được owner thay bằng giá trị đã duyệt; không phải giá trị kết nối.

### Lệnh 1 — inventory script B

Tối đa **OWNER ĐIỀN** lần, timeout **OWNER ĐIỀN**. Chạy từ repository root bằng Python 3.12 trong backend venv. Mật khẩu được hỏi ẩn qua getpass; host/port/user chỉ lấy từ PGHOST/PGPORT/PGUSER do owner đặt trong shell:

    & .\backend\.venv\Scripts\python.exe .\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s0_owner_run_readonly_20261106.py --expect-db {OWNER_DB_NAME} --out-dir .claude\handoff\logs\{OWNER_RUN_ID} --alembic-method {OWNER_CHOICE_STATIC_AST_OR_OWNER_CLI}

--out-dir phải là thư mục con mới dưới .claude/handoff/logs/; script từ chối overwrite. Output chỉ có metadata, row counts và grouped origin counts, không có row values.

### Lệnh 2 — mypy version

Tối đa **OWNER ĐIỀN** lần, timeout **OWNER ĐIỀN**. Candidate command, chạy trong backend sau khi thư mục run log đã được tạo; owner phải xác nhận interpreter:

    & .\.venv\Scripts\python.exe -m mypy --version 2>&1 | Tee-Object -FilePath ..\.claude\handoff\logs\{OWNER_RUN_ID}\mypy-version.txt

### Lệnh 3 — mypy baseline (candidate, chưa xác nhận là lệnh chuẩn repo)

Không tìm thấy một command mypy chuẩn được ghi rõ trong các file cấu hình/hồ sơ đã đọc. Candidate dưới đây lấy package/config từ backend/pyproject.toml, ghim import path vào checkout hiện tại và đặt cache qua $env:TEMP ngoài repo. Trước khi duyệt, owner phải xác nhận TEMP nằm ngoài repository và chọn timeout. Tối đa **OWNER ĐIỀN** lần, timeout **OWNER ĐIỀN**:

    $src=(Resolve-Path .\src).Path; $env:PYTHONPATH=$src; $env:MYPYPATH=$src; & .\.venv\Scripts\python.exe -m mypy --package sketch2life --config-file .\pyproject.toml --no-incremental --cache-dir "$env:TEMP\s2l-mypy-s0-owner-run" 2>&1 | Tee-Object -FilePath ..\.claude\handoff\logs\{OWNER_RUN_ID}\mypy-baseline.txt

Toàn bộ stdout/stderr phải được lưu vào log đã ignore, không lưu cache vào repository. Tool crash, timeout, hoặc không có verdict = **NOT RUN**, không phải PASS. test_be1_postgres_api.py đang **NO VERDICT**; command baseline này không được dùng để tuyên bố file test đó đã sạch.

### Phương án Alembic owner chọn

- **P1 — đề xuất mặc định, cần duyệt phạm vi 28 file:** script chỉ SELECT alembic_version, đọc AST của đúng manifest 28 revision files đã ghim trong mã, không import revision/application modules và không gọi Alembic CLI. K3 so sánh tập revision DB với heads source đã tính. File set khác manifest, AST không phải literal, revision trùng/thiếu, dependency thiếu hoặc graph lỗi thì K3 = NOT RUN và dừng phân tích K3; không tự dò thêm file.
- **P2 — owner-run CLI:** script vẫn đọc alembic_version, nhưng K3 trong báo cáo script = NOT RUN chờ đối chiếu. Sau khi K1 của script PASS, owner có thể chạy đúng hai lệnh dưới đây nếu đã duyệt, mỗi lệnh tối đa **OWNER ĐIỀN** lần và timeout **OWNER ĐIỀN**:

      & .\.venv\Scripts\python.exe -m alembic -c .\alembic.ini heads 2>&1 | Tee-Object -FilePath ..\.claude\handoff\logs\{OWNER_RUN_ID}\alembic-heads.txt

      & .\.venv\Scripts\python.exe -m alembic -c .\alembic.ini current --verbose 2>&1 | Tee-Object -FilePath ..\.claude\handoff\logs\{OWNER_RUN_ID}\alembic-current.txt

  heads đọc graph Alembic. current thực thi backend/alembic/env.py và kết nối database qua cấu hình ứng dụng; chỉ chạy nếu owner xác nhận chắc chắn cùng target đã qua K1, cấu hình an toàn và không có migration command. Không dùng upgrade, downgrade, stamp hay revision.

## 5. Tiêu chí kiểm tra và cách diễn giải

Mỗi kết quả chỉ mô tả bằng chứng thực tế; không tự coi kiểm tra đạt là approval hoặc phase closure.

| Gate | Bằng chứng cần thu | PASS / FAIL / NOT RUN và hành động |
|---|---|---|
| K1 — Identity | current_database() phải bằng chính xác tên owner đã duyệt. | Sai hoặc không đọc được: dừng ngay; không chạy query tiếp theo và không kết luận về DB đó. |
| K2 — Read-only | SHOW transaction_read_only phải trả on trước mọi query khác. | Không phải on: dừng ngay; không chạy K1 hoặc kiểm tra khác trên connection đó. |
| K3 — Alembic | Tập alembic_version so với source heads theo P1 hoặc output owner-run theo P2. | Ghi lệch đúng như thấy; không sửa/stamp/migrate. Path chưa được chọn, mismatch hoặc graph không thể tính = NOT RUN/FAIL theo điều kiện script. |
| K4 — Schema inventory | Schemas, regular/partitioned tables, columns, types, nullable/default, constraints, indexes. | PASS chỉ có nghĩa inventory được thu thập thành công. Source comparison là lượt tài liệu chỉ đọc riêng sau khi owner cung cấp output; discrepancy được ghi, không migrate (D-144 §9.5). |
| K5 — Synthetic-only | COUNT(*) cho mỗi user table; chỉ GROUP BY data_origin khi có đúng cột đó; không đọc giá trị hàng. | Giá trị NULL/rỗng hoặc ngoài allowlist SYNTHETIC_DEV = FAIL/STOP. Bảng không có cột provenance được ghi “không chứng minh được bằng script”; không có owner proof thì NOT RUN cho bảng và K5 tổng thể không PASS. Owner phải xác nhận bảng nào tạo nên con số 58; không cộng hàng qua bảng nếu quan hệ làm trùng thực thể. |
| K6 — CHECK/age definitions | In định nghĩa CHECK từ catalog, gồm các constraint liên quan tuổi. | PASS chỉ có nghĩa định nghĩa đã được liệt kê; không diễn giải tính đúng/sai hay sửa schema. Dùng làm bằng chứng cho việc đối chiếu F-6/age rule ở bước tài liệu riêng. |
| K7 — Mypy baseline | Output nguyên văn đã lưu, interpreter/mypy version, command, timeout và checkout. | Có verdict thật thì ghi baseline. Crash/timeout/no verdict = NOT RUN. M2 không được thêm diagnostic so với baseline theo D-144 §9.6. |

**Giới hạn provenance:** script chỉ xem metadata tên cột và số lượng theo data_origin; không đọc dữ liệu profile/child, không xác nhận nguồn gốc bằng nội dung. age_source hoặc tên cột tương tự không được mặc định coi là bằng chứng synthetic-only. Owner proof cho các bảng thiếu provenance phải nêu rõ bảng, cách xác minh và người chịu trách nhiệm.

## 6. Hard stop và điều cấm

- Thiếu trường owner, dump/restore, identity/manifest, bằng chứng synthetic-only, command ceiling, lựa chọn P1/P2, hash script đã review hoặc Task Approval riêng: **không chạy**.
- K1/K2 không đạt, provenance có giá trị khác SYNTHETIC_DEV/NULL/rỗng, source manifest không khớp, cần quyền ghi, cần migration hoặc cần sửa dữ liệu: dừng. Không thử command thay thế, không đổi shell/connection để lách gate.
- Safety check không có verdict = **NOT RUN**; dừng đúng cổng.
- Không đưa row data, child data, connection URL, password, token, host/port/user thật hoặc đường dẫn tuyệt đối vào chat/log/báo cáo/Git.
- Không cleanup 58 synthetic rows, không thay đổi DB, migration, source, test, policy hoặc route.
- Không stage/commit/push/merge. OWNER_MODAL_CALL_APPROVED=NO giữ nguyên.

## 7. Output và lưu trữ

- Script B đề xuất tạo đúng hai artifact mới (JSON và text) trong thư mục owner chọn dưới .claude/handoff/logs/; file hiện có thì từ chối ghi đè. Root .gitignore có quy tắc /.claude/; owner phải xác nhận ignore vẫn áp dụng trước lệnh.
- Report chứa script SHA-256, expected DB name, PostgreSQL server version, thời điểm UTC và trạng thái K1–K6. Không chứa endpoint, host, port, user, URL, password hay đường dẫn cục bộ.
- Chỉ hash output và kết quả gates được đưa vào hồ sơ sau đó; output không commit. Owner gửi tên file và hash cho coordinator; coordinator chỉ đọc output rồi làm K4 source comparison trong phạm vi được duyệt.
- Script B chưa có approval thực thi. SHA-256 để trống đến khi một reviewer độc lập xem script; sau đó owner phải ghi hash thực tế vào Task Approval. Bất kỳ byte thay đổi nào sau khi ghim đều vô hiệu hóa approval và yêu cầu review/approval lại.

## 8. Nguồn, baseline và giới hạn

- Checkout baseline đề xuất: branch feature/feat063-be-foundation, HEAD dd70685eae58aaaefea3e567f5c23d09345a8513, index rỗng. Approval thực thi phải pin lại branch/HEAD; lệch thì dừng và xin xác nhận lại.
- Kế hoạch nền: Draft 10 SHA-256 7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1.
- Owner directions: D-144, D-148, D-150, D-151 trong DECISIONS.md; S0-doc evidence SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001.
- backend/pyproject.toml khai báo Python 3.12-compatible, psycopg[binary] 3.x, Alembic/SQLAlchemy và mypy strict cho package sketch2life. Script dùng psycopg v3 từ backend venv; không thêm dependency.
- backend/alembic.ini để URL ứng dụng trống trong config tĩnh. backend/alembic/env.py lấy kết nối từ cấu hình ứng dụng và alembic current kết nối DB; do đó P2 có tác động vận hành khác P1.
- Đã đọc quy tắc .gitignore: /.claude/ loại trừ thư mục log local. Owner phải xác minh lại trong đúng checkout trước khi chạy.
- Inventory metadata và source comparison chưa chạy; dữ liệu DB, 58-row scope, identity, restore, container, mypy baseline và Alembic status chưa xác minh trong tài liệu này.
- D-150 đóng S0-doc ở phạm vi tài liệu only. D-151 chấp nhận Draft 10 làm planning baseline only; không phase implementation nào được mở. D-151 C1–C5, gồm câu bị cắt ở Draft 10 §5.3, vẫn là điều kiện/hạng mục carry-forward; không sửa hoặc quyết định chúng ở đây.

## 9. Quan hệ với các owner directions

| Owner direction | Cách bản nháp này phản ánh |
|---|---|
| D-144 §9.1 — BE tổng Docker DB chỉ đọc cho S0-owner-run; DB riêng cho write phases | §1, §2, §3 và §6 giới hạn đúng database read-only; S1a/S2 databases không nằm trong scope. |
| D-144 §9.2 — giữ nguyên 58 synthetic rows | §1, §2, §3, §5 và §6 yêu cầu scope owner xác nhận, không cleanup. |
| D-144 §9.5 — schema convergence chưa migrate, giữ history | §1, §5 và §6 chỉ inventory/ghi discrepancy, không migration. |
| D-144 §9.6 — mypy baseline chỉ đọc, owner-run | §2, §4 Lệnh 2–3, §5 K7 và §6. |

## 10. Câu hỏi mở cho owner

1. Tên database BE tổng, container/service và identity/manifest nào sẽ được dùng?
2. Ai chạy script và mypy? Ai chịu trách nhiệm dump/restore? Dump đã được kiểm tra restore chưa?
3. Host/port/user nào sẽ được đặt trong shell owner? Không gửi password/URL vào hồ sơ hoặc chat.
4. Con số 58 chỉ định những bảng nào và được hiểu là row count theo bảng hay tập thực thể nào?
5. Bảng nào không có cột data_origin; owner cung cấp bằng chứng synthetic-only gì cho từng bảng?
6. Chọn P1 static AST hay P2 owner-run Alembic CLI? Nếu P1, có phê duyệt rõ việc đọc tĩnh đủ 28 revision files, rộng hơn 9 revision modules được liệt kê trong Draft 10 §8 không?
7. Nếu P2, owner xác nhận alembic current --verbose sẽ dùng đúng DB đã qua K1 và cấu hình không thể trỏ sang database khác như thế nào?
8. Mypy candidate command, checkout/import path, cache ngoài repo, số lần chạy và timeout có được duyệt không?
9. Ai độc lập review script B, và ai ghi hash script cùng approval cuối?

**Điểm dừng:** tài liệu này và script B đều là bản nháp. Chúng chưa được review độc lập, chưa có hash được ghim vào approval, chưa được owner duyệt và không cho phép chạy S0-owner-run. S0-owner-run vẫn DRAFT; S1a, S1b, S2, S3, M3–M6 vẫn đóng. Không implementation approval; OWNER_MODAL_CALL_APPROVED=NO.
