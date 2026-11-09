# FEAT-063 M2 — Baseline trước S1a-T — Đặc tả approval cuối cho owner review

**Status: SPEC — NOT APPROVED, NOT LAUNCHED.** Bản này chưa cho phép chạy và không phải kết quả baseline.

**Owner/operator:** owner tự chạy sau approval riêng. Owner direction B9 trong D-158 giữ Baseline Draft 2: offline pytest 11 module, strict mypy, Ruff, ba validator và git diff --check; dùng cmd.exe /d /c với stdout/stderr/exit tách riêng. Operator là owner.

**Phạm vi:** một lượt baseline offline trước code S1a-T. Không kết nối PostgreSQL, không đọc dữ liệu ứng dụng, không dùng Alembic CLI, không migrate DB, không HTTP/network/provider/Modal/Docker, không sửa source/test. Đây là dữ liệu baseline, không phải verdict chấp nhận/từ chối S1a-T.

## 1. Nguồn và trạng thái

- D-144 §9.6, D-155 Q10: owner-run mypy baseline trước code, không DB. D-156 R8: offline pytest baseline trước code; lỗi có sẵn phải ghi riêng, không tính thành PASS/FAIL của S1a-T.
- D-158 B9: giữ Baseline Draft 2; thu hẹp tuyên bố an toàn thành không external HTTP, không network, không Alembic CLI và không connected-database migration. Ghi rõ test_age_provenance_columns.py dùng MigrationContext/Operations ở chế độ offline SQL.
- Source-only assessment: 11 modules và backend/tests/conftest.py không gọi production `get_settings()` hoặc `create_app()`, và không mở kết nối DB, socket, external HTTP, subprocess, Alembic CLI hay provider. `test_vision_analysis_review_fixes.py` dùng một fixture FastAPI app và Starlette TestClient in-process; đây không phải external HTTP. `test_synthetic_eligibility.py` kiểm class field metadata và mock `get_settings`, không gọi settings loader thật. `test_age_provenance_columns.py` dùng MigrationContext/Operations để render SQL offline; không kết nối DB và không gọi Alembic CLI. Đây là kết luận đọc mã, không phải runtime verdict. Không đọc `.env` và không in biến môi trường.
- Baseline Draft 2 gốc: SHA-256 BD5B06C8B750AD49E5DA728D0B9A29F5202F21E384BF3D204784634DF3DDC591. S1a-T Draft 4: 0EF6E6D43F2ABF1A5DDA1A67FAC33200F7D700F4CD068FF6F3DE37E3298FFCFC. Draft 11: 6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68.
- Branch/HEAD baseline: feature/feat063-be-foundation / dd70685eae58aaaefea3e567f5c23d09345a8513. DECISIONS.md gồm D-158, SHA-256 tại lúc soạn 830672AFF1533CF2D42AEF48818967F4B2DBB110132F5B0709D66BD924FA3425.
- TASK_APPROVAL.md pre-G6 provenance hash là FEEE42E506F94352A8161EFE0B4B94870967072BEDF233285BFDF882352A3DF7; sau G6 hash sẽ đổi. Owner xác minh mục baseline riêng có Status APPROVED / NOT LAUNCHED; không dùng hash lịch sử này làm hash hiện hành.

## 2. Ghim đầu vào một lượt

Owner rehash các mục trước launch; pin/branch/HEAD/index/source/test/config/validator drift thì dừng.

| Đầu vào | SHA-256 |
|---|---|
| backend/pyproject.toml | 2B8EF44141D0BC4702B73C414AE77325DA547F45B1EDBF37008114E9BCD46C1A |
| backend/tests/conftest.py | D4D18732D1C4F5518A1AAA36A9FACD98926F13BF8C10504FC0C866DABFC1A7E5 |
| backend/src/sketch2life/infrastructure/config/settings.py | DB1A5FB6E4F7C800F00B4AD1F9386D20AEE7F41DBD35BA54C7F13426D7CDD387 |
| tests/unit/test_profile_age_invariant.py | B166C424BC64F35CBB0F1454964F8459FA67B6D956C811C33A854E6B70E76BAB |
| tests/contract/test_be1_synthetic_pilot.py | 03CCBCE40EB3DA13FA15D3C128F22CF70B6AEE4968CF0B726A7ED8B136C74611 |
| tests/unit/test_age_provenance_columns.py | DE1B745B83AE490C4ACAD8F1D457B3CF1E16420B06F79B19DDFF3576BE778C97 |
| tests/unit/test_synthetic_eligibility.py | B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1 |
| tests/unit/test_assistance_domain.py | AFABE3545E47EAB5101551B1642855143D71E9FD910DA0BA8F213A9B78A89DC8 |
| tests/unit/test_assistance_service.py | A40BF516BD7232F7E641EF0168764F7B61ADE0E0A895C0A7B03A74B60ABFDAAC |
| tests/unit/test_be1_fact_reader.py | F234E7056F0FAFD0479519AB419271E3EE19552E1AF55A17E5A09CD387F5F815 |
| tests/unit/test_vision_analysis_service.py | D5B5A3F23A69B6CFD8079EBF57A6BDE85AC0CBB7699A586C03B14789FC8C8CDD |
| tests/unit/test_vision_analysis_review_fixes.py | CC3F777F2C7D48733B9C2444FC0DC3D496FC8D914A0DF4469DAE2EABB54EBD3D |
| tests/unit/test_vision_context_domain.py | 4A457F16A74C0CEEA9C2C53BB85174C7D2067C2113E80558E79266F234E43F96 |
| tests/unit/test_vision_context_service.py | E7E9BAAC7D54C42F45F7F56E9D8A99942290EEAB7F15620DE1B3911666D78348 |
| tools/validate_harness.py | 0804EABBAECF471F191E259760E48AA0DC2D5A4D23DA5D38336D8EDE2F09D232 |
| tools/validate_repository_security.py | EFD691DF935565D1FA148B5B4A765EF77C90D701D210FC5E869BFBD1548DD210 |
| tools/validate_architecture.py | FA236C8D389B608251153D601FC370EFE3F3E2479446CA4A56A3D395F892E0B5 |

## 3. Safety boundary và đúng 11 pytest modules

Source-only assessment: 11 modules dưới đây cùng backend/tests/conftest.py không gọi production `get_settings()` hoặc `create_app()`, và không mở kết nối DB, socket, external HTTP, subprocess, Alembic CLI hay provider. `test_vision_analysis_review_fixes.py` dùng một fixture FastAPI app và Starlette TestClient in-process; đây không phải external HTTP. `test_synthetic_eligibility.py` kiểm class field metadata và mock `get_settings`, không gọi settings loader thật. `test_age_provenance_columns.py` dùng MigrationContext/Operations để render SQL offline; không kết nối DB và không gọi Alembic CLI. Đây là kết luận đọc mã, không phải runtime verdict. Không đọc `.env` và không in biến môi trường.

Pytest duy nhất, cwd backend, một invocation; không chạy nguyên thư mục unit/contract/integration:

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

Giữ graph-count node trong test_synthetic_eligibility.py: nó ghim 25 revisions và heads (11, 9); review trước chỉ nêu nghi vấn graph hiện tại có thể là 28/12 raw/9 resolved, chưa xác minh bằng graph command. Nếu node fail, ghi node ID và summary làm baseline data, không tính là S1a-T PASS/FAIL. Exclude toàn bộ tests/integration, các fixture ai_jobs/ai_policy/learning_content/be2_cross_lane, ai_jobs/test_migrations.py, mọi PostgreSQL suite và BE1 PostgreSQL fixture. test_app_composition.py và test_openapi_contract_catalog.py NOT BASELINEABLE và bị loại khỏi baseline; kết quả hậu code là after-only theo seam A.

## 4. Command ceiling candidates được giữ theo Draft 2

Không chạy nếu chưa có approval entry riêng G6 ở trạng thái APPROVED / NOT LAUNCHED. Mỗi command đúng một lần, không retry hoặc đổi shell/flags/selection. Dùng cmd.exe /d /c, stdout/stderr direct redirection vào file riêng và ghi exit ngay sau lệnh. Không pipe/Tee-Object/transcript.

Chỉ tạo nếu chưa tồn tại và đã xác nhận bị ignore:

    .claude/handoff/logs/M2_BASELINE_RUN_20261107/
    tmp/M2_BASELINE_RUN_20261107/

Nếu đã tồn tại hoặc không ignored, dừng; không xóa/dọn/dùng lại. pytest basetemp và caches ở tmp. Logs giữ local, không commit.

Mọi log path dưới đây tương đối với cwd đã nêu.

| Lệnh | cwd / executable | Trần |
|---|---|---:|
| mypy --version | backend / .venv/Scripts/mypy.exe | 60 giây |
| mypy --package sketch2life --config-file pyproject.toml --strict --no-incremental --cache-dir ../tmp/M2_BASELINE_RUN_20261107/mypy-cache | backend / .venv/Scripts/mypy.exe; PYTHONPATH=src; MYPYPATH=src | 900 giây |
| ruff check --select E,F,I,UP,B,SIM --cache-dir ../tmp/M2_BASELINE_RUN_20261107/ruff-cache src tests | backend / .venv/Scripts/ruff.exe | 300 giây |
| pytest [đúng 11 node ở §3] -p no:cacheprovider --basetemp ../tmp/M2_BASELINE_RUN_20261107/pytest -q | backend / .venv/Scripts/python.exe | 1800 giây |
| validate_harness.py; validate_repository_security.py; validate_architecture.py | repo root / backend/.venv/Scripts/python.exe | 300 giây mỗi lệnh |
| git diff --check | repo root / git | 300 giây |

Với từng invocation, lưu stdout, stderr, exit riêng trong .claude/handoff/logs/M2_BASELINE_RUN_20261107/. mypy/test/ruff caches chỉ ở tmp. Không ghi giá trị environment, database URI hay secret.

### Các lệnh đúng để owner dùng

Tại backend, mypy version:

    cmd.exe /d /c "set PYTHONPATH=src&&set MYPYPATH=src&& .\.venv\Scripts\mypy.exe --version 1>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy-version.stdout.txt 2>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy-version.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy-version.exit.txt', [string]$exitCode)

Tại backend, strict mypy:

    cmd.exe /d /c "set PYTHONPATH=src&&set MYPYPATH=src&& .\.venv\Scripts\mypy.exe --package sketch2life --config-file pyproject.toml --strict --no-incremental --cache-dir ..\tmp\M2_BASELINE_RUN_20261107\mypy-cache 1>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy.stdout.txt 2>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\mypy.exit.txt', [string]$exitCode)

Tại backend, Ruff:

    cmd.exe /d /c ".\.venv\Scripts\ruff.exe check --select E,F,I,UP,B,SIM --cache-dir ..\tmp\M2_BASELINE_RUN_20261107\ruff-cache src tests 1>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\ruff.stdout.txt 2>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\ruff.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\ruff.exit.txt', [string]$exitCode)

Tại backend, pytest (chỉ đúng selection §3):

    cmd.exe /d /c ".\.venv\Scripts\python.exe -m pytest tests\unit\test_profile_age_invariant.py tests\contract\test_be1_synthetic_pilot.py tests\unit\test_age_provenance_columns.py tests\unit\test_synthetic_eligibility.py tests\unit\test_assistance_domain.py tests\unit\test_assistance_service.py tests\unit\test_be1_fact_reader.py tests\unit\test_vision_analysis_service.py tests\unit\test_vision_analysis_review_fixes.py tests\unit\test_vision_context_domain.py tests\unit\test_vision_context_service.py -p no:cacheprovider --basetemp ..\tmp\M2_BASELINE_RUN_20261107\pytest -q 1>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\pytest.stdout.txt 2>..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\pytest.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('..\.claude\handoff\logs\M2_BASELINE_RUN_20261107\pytest.exit.txt', [string]$exitCode)

Từ repo root, chạy riêng từng command và ghi exit ngay:

    cmd.exe /d /c "backend\.venv\Scripts\python.exe tools\validate_harness.py 1>.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-harness.stdout.txt 2>.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-harness.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-harness.exit.txt', [string]$exitCode)

    cmd.exe /d /c "backend\.venv\Scripts\python.exe tools\validate_repository_security.py 1>.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-repository-security.stdout.txt 2>.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-repository-security.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-repository-security.exit.txt', [string]$exitCode)

    cmd.exe /d /c "backend\.venv\Scripts\python.exe tools\validate_architecture.py 1>.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-architecture.stdout.txt 2>.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-architecture.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('.claude\handoff\logs\M2_BASELINE_RUN_20261107\validate-architecture.exit.txt', [string]$exitCode)

    cmd.exe /d /c "git diff --check 1>.claude\handoff\logs\M2_BASELINE_RUN_20261107\git-diff-check.stdout.txt 2>.claude\handoff\logs\M2_BASELINE_RUN_20261107\git-diff-check.stderr.txt"
    $exitCode = $LASTEXITCODE
    [IO.File]::WriteAllText('.claude\handoff\logs\M2_BASELINE_RUN_20261107\git-diff-check.exit.txt', [string]$exitCode)

## 5. Stop gates, output và owner fields

Dừng nếu pin/index/HEAD lệch; source thay đổi; module gọi production Settings/app/engine theo cách có thể kết nối DB, mở socket hoặc gọi external HTTP/provider; DB/client env hoặc network có nguy cơ; output ngoài hai ignored directories; command vượt trần; secret lộ; exit/summary/safety verdict thiếu. Không retry, đổi shell hoặc thay selection.

Pytest phải có summary chính thức hoàn chỉnh (passed/failed/skipped/errors và node IDs lỗi). Assertion fail với summary là baseline data; collection/import error, internal error, timeout, interruption hoặc thiếu summary là NOT RUN/không verdict. SKIP/NOT RUN không là PASS. Mypy so về sau bằng diagnostic chuẩn hóa (repo-relative file, code, message); pytest so cùng node set và failed/error node IDs.

**Owner fields — để trống:** launch confirmation, kiểm tra môi trường kín, xác nhận output directories mới/ignored, thời điểm, kết quả từng lệnh, owner review/acceptance và baseline closure. Không tick checkbox.

Một lượt này không phải baseline sau T. Theo D-156 R1, inventory/offline/mypy baseline giữa T và P cần pin và approval riêng. Không mở S1a-T, S1a-P, S1b, S2, S3 hoặc M3–M6; không cho phép DB, migration, Docker, Modal, GPU, provider hay network. OWNER_MODAL_CALL_APPROVED=NO.

**Approval basis/signature/date:** CHƯA ĐIỀN.
