# FEAT-063 M2 — Bản nháp Task Approval: baseline trước S1a — Draft 2

**Trạng thái:** DRAFT / NOT APPROVED / NOT LAUNCHED
**Owner decision record:** ____________________
Đây chỉ là bản nháp. Nó không cấp quyền chạy lệnh và không mở pha nào.

## Thay đổi từ Baseline Draft 1 sang Draft 2

| Phần Draft 1 | Thay đổi ở Draft 2 | Cơ sở |
|---|---|---|
| §2 pins | Cập nhật DECISIONS pin có D-157, trỏ M2 sang Draft 11 và ghim S1a-T/P Draft 3 sau khi hoàn tất | D-156, D-157; checkout đọc tĩnh |
| §3.1–3.2 selection | Mở rộng từ module tổng hợp duy nhất thành 11 module offline-safe đã đọc tĩnh; graph-count test vẫn được chạy như baseline, không loại trước | D-156 R8; D-157 O7 |
| §3.2 exclusions | Phân biệt OpenAPI/catalog và app-composition tests chưa baselineable vì tạo app/settings với các module đủ điều kiện; mọi integration/destructive fixtures tiếp tục loại | Static import/call-path review |
| §4.1, §4.3 | Chỉ giữ wrapper mypy qua cmd.exe với direct redirection; ghim đúng pytest module selection | An toàn ghi nhận output, không chạy lệnh |
| §8–11 | Ghi rõ baseline là đề xuất, không mở S1a; baseline sau T phải tính lại trước P | D-156 R1/R8 |

## 1. Mục tiêu và phạm vi

Đề xuất một lượt owner-run chỉ đọc để ghi nhận baseline trước khi S1a-T viết code: strict mypy, Ruff, pytest offline với selection giới hạn, cùng ba repository validator và git diff --check. Không kết nối database, không đọc dữ liệu ứng dụng, không dùng mạng/provider, không chạy Alembic, không sửa mã. Kết quả là mốc so sánh, không phải verdict chấp nhận hay từ chối S1a.

## 2. Cơ sở và pin đầu vào

Owner/executor phải xác minh lại tất cả pin trước lần chạy được duyệt riêng. Sai pin, source/config/test liên quan đổi, hoặc index không rỗng thì dừng.

| Đầu vào | SHA-256 |
|---|---|
| Branch / HEAD | feature/feat063-be-foundation / dd70685eae58aaaefea3e567f5c23d09345a8513 |
| M2 plan Draft 11 | 6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68 |
| S1a-T Task Approval Draft 3 | 9EA2A89C8540931AF770ED27542F19CB3E613D58B7B87F7403FCD234C1ED2E1C |
| S1a-P Task Approval Draft 3 | 635689889C24C429B1440D62D8562D85ADC0477679BF1F364916576BB07C6BF5 |
| Historical S0-owner-run approval spec Draft 6 (capture-pattern reference) | 6B4978C9B941C371D1EFFA654308C43B605A9823B056F2F89B6808005B82D9DE |
| DECISIONS.md lúc soạn | DE0BBA068ECB7080DD1150EAF8C73CDA29790C4831C5EF8EBB660E357127E9F4 |
| TASK_APPROVAL.md lúc soạn | FEEE42E506F94352A8161EFE0B4B94870967072BEDF233285BFDF882352A3DF7 |
| backend/pyproject.toml | 2B8EF44141D0BC4702B73C414AE77325DA547F45B1EDBF37008114E9BCD46C1A |
| backend/tests/conftest.py | D4D18732D1C4F5518A1AAA36A9FACD98926F13BF8C10504FC0C866DABFC1A7E5 |
| pytest `backend/tests/unit/test_profile_age_invariant.py` | B166C424BC64F35CBB0F1454964F8459FA67B6D956C811C33A854E6B70E76BAB |
| pytest `backend/tests/contract/test_be1_synthetic_pilot.py` | 03CCBCE40EB3DA13FA15D3C128F22CF70B6AEE4968CF0B726A7ED8B136C74611 |
| pytest `backend/tests/unit/test_age_provenance_columns.py` | DE1B745B83AE490C4ACAD8F1D457B3CF1E16420B06F79B19DDFF3576BE778C97 |
| pytest `backend/tests/unit/test_synthetic_eligibility.py` | B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1 |
| pytest `backend/tests/unit/test_assistance_domain.py` | AFABE3545E47EAB5101551B1642855143D71E9FD910DA0BA8F213A9B78A89DC8 |
| pytest `backend/tests/unit/test_assistance_service.py` | A40BF516BD7232F7E641EF0168764F7B61ADE0E0A895C0A7B03A74B60ABFDAAC |
| pytest `backend/tests/unit/test_be1_fact_reader.py` | F234E7056F0FAFD0479519AB419271E3EE19552E1AF55A17E5A09CD387F5F815 |
| pytest `backend/tests/unit/test_vision_analysis_service.py` | D5B5A3F23A69B6CFD8079EBF57A6BDE85AC0CBB7699A586C03B14789FC8C8CDD |
| pytest `backend/tests/unit/test_vision_analysis_review_fixes.py` | CC3F777F2C7D48733B9C2444FC0DC3D496FC8D914A0DF4469DAE2EABB54EBD3D |
| pytest `backend/tests/unit/test_vision_context_domain.py` | 4A457F16A74C0CEEA9C2C53BB85174C7D2067C2113E80558E79266F234E43F96 |
| pytest `backend/tests/unit/test_vision_context_service.py` | E7E9BAAC7D54C42F45F7F56E9D8A99942290EEAB7F15620DE1B3911666D78348 |
| settings source | DB1A5FB6E4F7C800F00B4AD1F9386D20AEE7F41DBD35BA54C7F13426D7CDD387 |
| validate_harness.py | 0804EABBAECF471F191E259760E48AA0DC2D5A4D23DA5D38336D8EDE2F09D232 |
| validate_repository_security.py | EFD691DF935565D1FA148B5B4A765EF77C90D701D210FC5E869BFBD1548DD210 |
| validate_architecture.py | FA236C8D389B608251153D601FC370EFE3F3E2479446CA4A56A3D395F892E0B5 |

D-144 §9.6 để lại mypy baseline; D-155 Q10 yêu cầu baseline mypy owner-run, không database, trước code S1a; D-156 R8 yêu cầu offline pytest baseline trước code và tách lỗi có sẵn khỏi PASS/FAIL của S1a; D-157 O7 đổi shared age validator cho giá trị mới ở BE1. Đây là hướng đã ghi, không phải quyền chạy lệnh của bản nháp này.

## 3. An toàn và pytest selection

### 3.1. Rủi ro settings và phương pháp đọc tĩnh

Settings và CoreDatabaseSettings có thể nạp backend `.env` và root `.env` sau các biến môi trường tiến trình. Hai file `.env` được biết là hiện diện; nội dung không được đọc. Unset `SKETCH2LIFE_DATABASE_URL` một mình không chứng minh test offline-safe.

Trước khi soạn bản nháp, đã đọc tĩnh từng module trong danh sách §3.2 cùng `backend/tests/conftest.py`: root conftest chỉ có docstring, không có unit conftest; các module được chọn không khởi tạo `Settings`/`get_settings`, app, engine/session, socket, HTTP, subprocess, Alembic hay provider. Đây là đánh giá source-level, không phải runtime verdict. Nếu pin đổi hoặc một module bắt đầu khởi tạo cấu hình/app hay mở tài nguyên ngoài tiến trình, dừng và xin approval mới.

`tests/contract/test_app_composition.py` và `tests/contract/test_openapi_contract_catalog.py` **NOT BASELINEABLE** trong lượt này: chúng gọi composition/create_app và có đường nạp Settings/engine; không được đưa chúng vào baseline chỉ bằng cách override/mock. Chỉ có thể xem xét chạy chúng sau khi một safe-settings seam được đọc, ghim và duyệt riêng; nếu chưa chứng minh được thì ghi NOT RUN. Mọi PostgreSQL test, integration suite, destructive fixture và `test_migrations.py` đều bị loại.

### 3.2. Selection offline duy nhất được đề xuất

Một invocation pytest gồm đúng 11 module sau, từ cwd `backend`; không chạy cả thư mục unit/contract và không thêm node ngoài danh sách:

    tests/unit/test_profile_age_invariant.py
    tests/contract/test_be1_synthetic_pilot.py
    tests/unit/test_age_provenance_columns.py
    tests/unit/test_synthetic_eligibility.py
    tests/unit/test_assistance_domain.py
    tests/unit/test_assistance_service.py
    tests/unit/test_be1_fact_reader.py
    tests/unit/test_vision_analysis_service.py
    tests/unit/test_vision_analysis_review_fixes.py
    tests/unit/test_vision_context_domain.py
    tests/unit/test_vision_context_service.py

`test_synthetic_eligibility.py` chứa test graph-count có kỳ vọng 25 revisions và heads (11, 9). Báo cáo review trước nêu graph hiện tại có thể là 28 revisions, 12 raw heads/9 resolved; đây chưa được tái xác minh bằng lệnh graph và không phải verdict. Không bỏ test này khỏi baseline: ghi kết quả và node ID thật. Khi so sánh về sau, giữ cùng node set; nếu implementation approval sau này loại node khỏi tiêu chí S1a thì node đó vẫn là baseline data, không phải PASS.

Các module tuổi trong selection kiểm tra caller của shared `validate_age_months` sau D-157 O7. Fixture bands 36–155 riêng biệt không tự động đổi phạm vi O7; chỉ đổi test khi nó khẳng định quy tắc cho giá trị mới và đúng allowlist/approval. `tests/contract/test_learning_content_commands.py` có schema boundary độc lập 155; `tests/unit/test_t2c_digest_pin.py` pin policy reference. Chúng không tự động thuộc O7; cần call-path evidence và amendment riêng trước khi đưa vào.

Loại toàn bộ `tests/integration`, gồm `tests/integration/ai_jobs/conftest.py`, `tests/integration/ai_policy/conftest.py`, `tests/integration/learning_content/conftest.py`, `tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py`, `tests/integration/ai_jobs/test_migrations.py`, các PostgreSQL suites và BE1 PostgreSQL fixture. Những fixture này có thể tạo/drop database hoặc kết nối DB. Nếu phát hiện fixture/side effect mới trong 11 module trước launch, dừng; không thay selection để lách.

## 4. Candidate commands — chưa được phép chạy

Mỗi command tối đa một lần sau khi có Task Approval riêng đã được owner duyệt. Trước launch, chỉ tạo hai thư mục mới, chưa tồn tại và đã xác nhận bị ignore:

- Logs: .claude/handoff/logs/M2_BASELINE_RUN_20261107/
- Cache và pytest temporary files: tmp/M2_BASELINE_RUN_20261107/

Cả hai vắng mặt lúc soạn; .gitignore bỏ qua /.claude/ và tmp/. Kiểm tra lại trước launch. Nếu có sẵn hoặc không còn ignored, dừng; không xóa, dọn hay ghi đè. Không commit artifacts.

Với từng lệnh, capture stdout, stderr và exit code vào file riêng trong logs. Mypy phải dùng cmd.exe /d /c và direct redirection như pattern của S0-owner-run; không pipe, Tee-Object hay transcript. Launch record phải ghim capture wrapper, không in giá trị environment.

### 4.1. Mypy strict

Working directory `backend`; executable `backend/.venv/Scripts/mypy.exe`. Mỗi invocation chỉ chạy đúng một lần bằng wrapper direct-capture bên dưới.

Candidate PowerShell launch from backend, using cmd.exe direct stdout/stderr redirection:

    cmd.exe /d /c "set PYTHONPATH=src&& set MYPYPATH=src&& .\.venv\Scripts\mypy.exe --version 1>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy-version.stdout.txt 2>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy-version.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy-version.exit.txt', [string]$exitCode)

Một lần, trần 60 giây; lưu mypy-version.stdout.txt, mypy-version.stderr.txt, mypy-version.exit.txt.

Chạy đúng một lần bằng wrapper direct-capture dưới đây, từ cwd `backend`.

Candidate direct capture from backend, then record the returned exit code immediately:

    cmd.exe /d /c "set PYTHONPATH=src&& set MYPYPATH=src&& .\.venv\Scripts\mypy.exe --package sketch2life --config-file pyproject.toml --strict --no-incremental --cache-dir ..\tmp\M2_BASELINE_RUN_20261107\mypy-cache 1>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy.stdout.txt 2>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy.exit.txt', [string]$exitCode)

Một lần, trần 900 giây; lưu mypy.stdout.txt, mypy.stderr.txt, mypy.exit.txt. pyproject.toml đã đặt strict=true; --strict nêu rõ intent. Cache chỉ ở tmp được ignore; không dùng cache incremental cũ.

### 4.2. Ruff

Working directory backend; executable .\.venv\Scripts\ruff.exe. Một lần, trần 300 giây. Rule set đọc từ pyproject.toml là E,F,I,UP,B,SIM; paths tường minh src và tests.

    .\.venv\Scripts\ruff.exe check --select E,F,I,UP,B,SIM --cache-dir ..\tmp\M2_BASELINE_RUN_20261107\ruff-cache src tests

Lưu ruff.stdout.txt, ruff.stderr.txt, ruff.exit.txt. Không format, autofix hay đổi cấu hình.

### 4.3. Pytest offline

Working directory backend; executable .\.venv\Scripts\python.exe. Một lần, trần 1800 giây; chỉ chạy module §3.2; tắt cache provider và đặt basetemp dưới tmp ignored.

    .\.venv\Scripts\python.exe -m pytest tests\unit\test_profile_age_invariant.py tests\contract\test_be1_synthetic_pilot.py tests\unit\test_age_provenance_columns.py tests\unit\test_synthetic_eligibility.py tests\unit\test_assistance_domain.py tests\unit\test_assistance_service.py tests\unit\test_be1_fact_reader.py tests\unit\test_vision_analysis_service.py tests\unit\test_vision_analysis_review_fixes.py tests\unit\test_vision_context_domain.py tests\unit\test_vision_context_service.py -p no:cacheprovider --basetemp ..\tmp\M2_BASELINE_RUN_20261107\pytest -q

Lưu pytest.stdout.txt, pytest.stderr.txt, pytest.exit.txt. Ghi summary chính thức passed/failed/skipped/errors và failed/error node IDs; không ghi giá trị environment hay secret. Summary hoàn chỉnh dù có assertion failure vẫn là baseline có dữ liệu, không phải xanh. Collection/import error, internal error, timeout, interruption, summary thiếu hoặc safety verdict thiếu = NOT RUN/không verdict. SKIP và NOT RUN không phải PASS.

### 4.4. Bốn repository checks

Từ repository root, mỗi lệnh một lần, trần 300 giây. Interpreter ghim là backend\.venv\Scripts\python.exe.

    backend\.venv\Scripts\python.exe tools\validate_harness.py
    backend\.venv\Scripts\python.exe tools\validate_repository_security.py
    backend\.venv\Scripts\python.exe tools\validate_architecture.py
    git diff --check

Ba validator đã được đọc tĩnh: imports là standard library; security validator gọi local git ls-files. Không thấy truy cập DB/mạng trong các script này. Capture stdout/stderr/exit riêng thành validate-harness.*, validate-repository-security.*, validate-architecture.* và git-diff-check.*. Không cần validate_skeleton.py vì không đổi cấu trúc repo.

git diff --check bỏ qua file untracked; kết quả chỉ áp dụng tracked diff và không kiểm chứng bản nháp này hay logs.

## 5. Owner launch preconditions

Checkboxes để trống; chỉ owner điền trong launch record riêng.

- [ ] Branch, HEAD, index và mọi pin §2 được kiểm lại; index rỗng.
- [ ] Backend source, config, test và validator inputs không đổi so với pin.
- [ ] Hai output directories chưa tồn tại, bị ignore; không tái sử dụng cache hoặc basetemp.
- [ ] Không có pytest/mypy process khác.
- [ ] Shell không có SKETCH2LIFE_DATABASE_URL, PostgreSQL client variables hoặc giá trị dạng connection URI; xác minh kín, không in values.
- [ ] Pytest selection chỉ gồm đúng 11 module §3.2, không thêm test hay chạy rộng integration, contract hoặc unit directory.
- [ ] Do settings loader có fallback .env, xác nhận từ source đã ghim rằng module không khởi tạo Settings/gọi loader. Không đọc .env; nếu không thể xác minh, không chạy pytest.
- [ ] Không command/output nào in password, token, DB URL hoặc environment values.
- [ ] Owner chấp nhận test revision-count chỉ là nghi vấn tĩnh cho tới khi có output.
- [ ] Có operator được chỉ định để theo dõi từng ceiling.

Bất kỳ ô nào chưa xác minh đều chặn chạy. Không đổi shell, env, selection hay command để vượt stop gate.

## 6. Output và cách so baseline

Raw outputs chỉ lưu trong ignored local log folder. Hồ sơ về sau chỉ ghi command, executable/version, cwd, exit, hash log và summary đã lọc; không ghi credentials, DB URL, environment values hay absolute local paths. Không đưa logs vào Git.

So mypy sau này bằng tập diagnostic chuẩn hóa (repo-relative file, error code, message), không so tổng dòng. Diagnostic thiếu code ghi thành no-code riêng và phải review. So pytest bằng đúng cùng node set, summary counts và failed/error node IDs. Node bị loại ở pha sau là NOT RUN, không PASS; đổi selection cần approval riêng và không dùng để xóa baseline failure.

## 7. Diễn giải exit và stop gates

- Mypy exit 0: không diagnostic ở invocation đã ghim. Nonzero với diagnostic thường là baseline, không cho phép sửa code. Internal error, traceback, timeout, interruption hoặc output thiếu: không verdict.
- Ruff/validators: ghi output và exit thật; nonzero là vấn đề baseline, không sửa trong task này; result thiếu hoặc bị ngắt là NOT RUN.
- Pytest: run hoàn tất có summary là dữ liệu baseline kể cả có failures; giữ node IDs. Nghi vấn stale revision chưa được xác nhận tới khi quan sát.
- git diff --check exit 0 chỉ áp dụng tracked diff.
- Pin drift, prompt bất ngờ, dấu hiệu DB/mạng/provider access, secret/URL trong log, output ngoài hai ignored dirs, file ngoài dự kiến, thiếu exit record hoặc chạm ceiling: dừng ngay. Không retry, đổi shell/flags hay đổi selection.

Các ceiling đề xuất chưa có timing evidence cho đúng command set này, là ước lượng chờ owner chốt: mypy 900 giây; mypy --version 60; Ruff 300; pytest module giới hạn 1800; từng validator và git diff --check 300; chuẩn bị dirs 60. Owner theo dõi và ngắt khi chạm trần. Timeout/interruption = NOT RUN; retry cần approval riêng.

## 8. Quan hệ với S1a và các pha sau

Đây chỉ đề xuất đúng một baseline “trước” cho S1a-T tại các pin §2; bản nháp này không được dùng lần hai. Theo D-156 R1, sau S1a-T và trước S1a-P cần inventory cùng offline/mypy baseline mới với pin được tính lại và một approval/launch record riêng. Không dùng tài liệu này để chạy baseline sau T. Không thay Task Approval S1a-T/S1a-P và không cấp quyền cho bất kỳ pha nào.

## 9. Tiêu chí hoàn tất và ô owner

Chỉ lập baseline record khi từng command được duyệt có output và exit code thực, owner đã xem failures và output đã lọc. Lệnh không verdict vẫn là NOT RUN. Không gọi baseline là sạch nếu output không chứng minh.

- [ ] Duyệt hoặc sửa selection pytest tại §3.2.
- [ ] Xác nhận điều kiện an toàn về settings fallback tại §5.
- [ ] Xác nhận executable paths và direct-capture wrapper.
- [ ] Chốt ceilings tại §7.
- [ ] Ghi operator và duyệt hai output locations.
- [ ] Chốt cách preflight shell kín, không in environment values.
- [ ] Chốt launch record, log retention và nơi báo cáo.
- [ ] Owner decision record / approval basis: ____________________.

## 10. Hiệu lực và loại trừ

Nếu được duyệt sau này, đề xuất chỉ áp dụng đúng một lượt tại các pin nêu trên. Hết hiệu lực nếu pin, test selection, command, safety condition hay output path thay đổi; không tự thích nghi văn bản này.

Không mở S1a-T, S1a-P, S1b, S2, S3 hay M3–M6. Không cho phép implementation, sửa source/test, kết nối/ghi DB, migration, Docker, Modal, GPU, provider hay network. OWNER_MODAL_CALL_APPROVED=NO giữ nguyên.

## 11. Known conditions

- Báo cáo review trước mô tả strict mypy từng nonzero do protocol incompatibility. Lượt này không chạy hay xác minh lại; baseline phải ghi kết quả hiện tại.
- Candidate pytest selection gồm 11 module; `test_synthetic_eligibility.py` có test kỳ vọng 25 revision và (11, 9) heads. Mismatch với graph hiện tại là suy luận từ review trước, không phải kết quả của lượt này.
- Hai file .env tồn tại nhưng không đọc nội dung. Fallback settings là lý do chỉ đưa các module đã đọc tĩnh vào pytest candidate.
- Chưa chứng minh toàn bộ tests/unit hoặc tests/contract offline-safe; chúng không thuộc command candidate.
