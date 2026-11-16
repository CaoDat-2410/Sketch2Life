# B1 P2 — Independent review 2

**Ngày:** 2026-11-04  
**Phạm vi:** FEAT-064 B1 P2, mã nguồn và bằng chứng trong repository; runner PostgreSQL do owner thực thi.  
**Kết luận:** Bằng chứng PostgreSQL mới xác nhận 20/20 lượt chạy đều PASS, không có SKIP hoặc FAIL. Các ranh giới owner/artifact đã được owner chấp nhận và được công bố rõ. Không thấy blocker P1/P2 mới ngoài các giới hạn đã được owner chấp nhận. Có một hệ quả P3 cần ghi nhận: stale-owner rejection để lại một analysis row và provider invocation đã hoàn tất nhưng không được gắn với kết quả job được chấp nhận.

## Giới hạn thao tác và trạng thái repository

- Reviewer không kết nối PostgreSQL, không chạy test PostgreSQL, không đọc giá trị biến môi trường hoặc DB URL, không mở script cấu hình DB, không gọi mạng/provider, không chạy Alembic.
- Runner PostgreSQL trong bằng chứng mới là do owner chạy. Reviewer chỉ đọc và đối chiếu các log của lần chạy đó.
- Không sửa source, test, plan, approval, status, migration hoặc file tracked nào khác. Không stage hay commit. Báo cáo này là file repository duy nhất được tạo.
- Log chạy owner nằm trong thư mục ignored .claude/handoff/snapshots/GB1_P2_A5B_20261104T194708/.
- HEAD trong log và hiện tại là b6dbfa68e66718f3f40902c093e9ebd634b1ebb9; index rỗng. Log ghi 113 đường dẫn trạng thái trước và sau; hai danh sách giống hệt nhau. Điều này xác nhận runner không làm thay đổi worktree trong khoảng chạy, không khẳng định worktree vốn sạch.

## R1–R3 — Đối chiếu độc lập source, test và thay đổi

Đã đọc test/source trước khi dùng các báo cáo closure làm căn cứ. Bốn SHA-256 hiện tại khớp với các hash kết thúc Addendum 5:

| File | SHA-256 |
|---|---|
| backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py | 2D4A99E15C3650A3E30538B9557251872CAFEE338E3F82FF7917A55D8284F004 |
| backend/tests/unit/test_be1_pilot_artifact_fence.py | 3D3683640B3876E1431E02294561AF9C90C616FA0FC5C32711F1D6311B84FA1D |
| backend/tests/integration/test_be1_synthetic_pilot_postgres.py | 0620AFDEBDB83584C2AA97BE9BCD6E1437CD99B84C912E4EF216BA4B1885440D |
| backend/tests/unit/test_pilot_queue_composition_b1.py | 5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4 |

Đã đối chiếu manifest A4/A5, snapshot và từng hunk của pilot_composition.py. Hash bản cuối A4 trùng baseline A5; hash bản cuối A5 trùng source hiện tại. So sánh AST sau khi bỏ annotation/docstring cho thấy phần executable của function/class không đổi. Khác biệt AST nằm ở import: các kiểu được import để dùng trong annotation và ProviderContextMode được import trực tiếp từ domain thay vì application-port re-export. So sánh AST này không chứng minh side-effect của module import hoặc hành vi runtime của dependency.

PilotFakeArtifacts.hold_fences chỉ giữ lock trong lúc kiểm tra rồi nhả trước khi caller commit SQL. Docstring hiện nói rõ đây là point-in-time fence và không bảo vệ khoảng giữa kiểm tra với commit. Đây là giới hạn đã được owner chấp thuận; test hold-before-send xác nhận revoke trước lần gửi khiến worker không gọi provider.

Các test kiểm tra:

- Thành công: receipt authoritative đúng một bản; disposition accepted, reason rỗng; revision của receipt bằng revision job đã lưu; job SUCCEEDED, một result ref, invocation SUCCEEDED, một analysis và một provider call.
- Stale owner: test thay đổi owner fact thật, rồi đòi chính xác job còn RUNNING, disposition rỗng, không result ref/receipt, provider invocation đã SUCCEEDED, một analysis row và attempt outcome vẫn rỗng. Đây là assertion mạnh hơn việc chỉ đòi “không accepted”.
- Artifact fence: unit test dùng digest khác nhưng vẫn đúng định dạng SHA-256 hợp lệ; không chỉ thử chuỗi sai định dạng.
- Restart/re-delivery: sau khi invocation đã SENT, composition/worker/ledger/envelope mới không gửi provider lần hai. Test dùng cùng SQLAlchemy engine và tái tạo application objects trong cùng test process; nó không kill/relaunch test process hoặc tạo engine mới giữa hai composition.

## R4 — Runner và log mới

Đã kiểm tra runner owner dùng, sau đó kiểm tra độc lập toàn bộ thư mục log mới. Runner tạo process riêng cho từng pytest invocation, đợi mỗi process kết thúc, giữ test selector cố định, dùng --basetemp riêng và tắt pytest cache bằng -p no:cacheprovider.

Log chạy từ 2026-11-04 19:47:08 +07:00 đến 19:49:31 +07:00, ghi HEAD đúng, index có 0 staged paths và source hashes ở đầu/cuối trùng Addendum 5. Run plan có 13 lượt lặp trước lượt tổng hợp và 7 lượt final; tổng theo node:

| Test node | Số lượt | Kết quả đã đối chiếu |
|---|---:|---|
| test_b1_succeeded_is_durable_before_real_app_result_acceptance | 4 | 4 PASS |
| test_b1_unknown_after_sent_is_not_accepted_or_replayed | 2 | 2 PASS |
| test_b1_hold_before_send_creates_no_result_or_invocation | 2 | 2 PASS |
| test_b1_stale_owner_fence_rejects_result_after_provider_success | 4 | 4 PASS |
| test_b1_stale_artifact_fence_rejects_result_after_provider_success | 2 | 2 PASS |
| test_b1_concurrent_duplicate_delivery_uses_one_attempt_and_one_send | 2 | 2 PASS |
| test_b1_sent_invocation_survives_process_rebuild_without_second_provider_call | 4 | 4 PASS |

Không chỉ dựa vào summary.txt: đã kiểm tra đủ 20 file command, 20 stdout và 20 stderr. Từng command chứa đúng test node ghi trong tên log và các cờ pytest mong đợi. Mỗi stdout có đúng một test passed, không có skipped/failed/error; tất cả stderr rỗng. Bảng summary có 20 verdict PASS, 0 SKIP, 0 FAIL. Không tính SKIP là PASS.

run-context.txt chỉ ghi trạng thái hiện diện của cấu hình test database, không ghi giá trị; reviewer không truy xuất giá trị đó. Không có libpq routing variable nào được runner ghi nhận.

## R5 — Kiểm tra offline và static

Các lệnh được chạy theo phạm vi được yêu cầu; không chạy PostgreSQL từ phiên review:

- Unit: từ backend, .\.venv\Scripts\python.exe -m pytest -o addopts= -q --tb=short tests/unit/test_be1_pilot_artifact_fence.py tests/unit/test_pilot_queue_composition_b1.py — 29 passed.
- F1 contract: .\.venv\Scripts\python.exe -m pytest -o addopts= -q --tb=short tests/contract/test_app_composition.py::test_real_app_composes_pilot_only_for_valid_local_synthetic_gate — 1 passed.
- Offline regression runner: chạy từ các bản copy byte-identical trong thư mục log local để không ghi đè output/historical log trong source tree — 460 passed.
- Ruff check theo lệnh root được ghi trong A5, trên bốn file trong scope — All checks passed. Một lần gọi không chuẩn từ backend với cách chỉ định config khác tạo import-order diagnostics; không dùng kết quả đó thay cho lệnh root chuẩn đã pass.
- Ruff format check trên ba file composition/unit-test được phép format — 3 files already formatted. Khi thêm file PostgreSQL integration thứ tư, formatter báo file đó sẽ được format lại (exit 1). Không áp dụng formatting; đây là ghi nhận về style, không phải test/runtime failure.
- Mypy strict trên bốn file — 60 errors trong một file, toàn bộ ở tests/integration/test_be1_synthetic_pilot_postgres.py; 0 lỗi ở composition và hai unit-test file. Vì vậy strict mypy trên đủ bốn file không pass.
- python tools/validate_harness.py — HARNESS_VALID.
- python tools/validate_repository_security.py — REPOSITORY_SECURITY_VALID (6417 files).
- python tools/validate_architecture.py — ARCHITECTURE_VALID.
- git diff --check — exit 0, không có whitespace diagnostic; Git có in cảnh báo chuẩn hóa CRLF.

## R6 — Kiểm tra phạm vi và trạng thái bảo vệ

- Các file owner fence, assistance port và BE1 registry khớp baseline B1 đã lưu. application/services/vision_analysis.py khớp snapshot trước A5; app.py và be1_runtime.py khớp snapshot trước A4.
- AI Jobs service, SQL repository, ports, SQL table definitions, invocation ledger, worker, legacy provider, transport, analysis repository và BE1 models đều sạch so với blob ở HEAD.
- Không có dirty file trong backend/alembic hoặc backend/migrations.
- FEAT-064 STATUS.md và PILOT_GOAL_LEDGER khớp snapshot trước A5. Không có snapshot bytes trước A5 để xác minh độc lập TASK_APPROVAL.md; báo cáo Addendum 5 nói file đó không bị sửa, nhưng điều này ở đây là không xác định được bằng byte comparison độc lập.
- Security validator không phát hiện vi phạm theo rule hiện hành. Báo cáo này không chứa URL, credential, absolute machine path, model weight hay raw media.

## R7 — Hệ quả và giới hạn còn lại

1. **Stale-owner side effect mới, P3, synthetic/local scope.** Assertion và persisted-state helper cho thấy lần stale-owner bị từ chối vẫn đã ghi một analysis row và invocation SUCCEEDED; job vẫn RUNNING, không result ref và không authoritative receipt. VisionAnalysisService.record_observation commit analysis riêng qua SqlAnalysisRepository, trước transaction accept/reject kết quả job. Đây là durable orphan/unreferenced analysis state vượt quá mô tả đơn thuần “job còn RUNNING, không receipt” đã được owner chấp thuận. Trong test này payload và artifact đều synthetic/local, nên không phải blocker cho scope hiện tại. Trước khi dùng luồng với dữ liệu hoặc provider không synthetic, cần định nghĩa cleanup/invalidation/reconciliation và xác nhận reader không thể coi row này là kết quả accepted.
2. **Fake artifact không durable.** PilotFakeArtifacts giữ bytes trong RAM; quarantine chỉ ghi marker/tăng epoch, không xóa body. SQL có result reference bền vững nhưng backing fake artifact không tồn tại qua composition/process rebuild. Giới hạn này phù hợp với synthetic pilot, không chứng minh storage semantics cho production.
3. **Receipt và audit.** B1 success test xác nhận authoritative completion receipt và revision liên hệ với persisted job. Helper cũng quan sát audit outbox, nhưng B1 node không assertion cụ thể cho outbox/audit delivery. Các generic AI Jobs integration tests có kiểm tra durability/recovery audit, nhưng không nằm trong phạm vi lệnh được chạy trong review này. Không suy rộng kết quả receipt thành bằng chứng audit delivery.
4. **Reconciliation/timeout.** PilotVisionComposition.dispatch_one chỉ gọi dispatch outbox và queue. Reconciler chưa được nối vào live composition. Policy hiện đặt một attempt, timeout 180 giây; nếu sweeper áp dụng policy này cho attempt quá hạn, trạng thái có thể thành FAILED_EXHAUSTED. Đây là giới hạn vận hành đã công bố, không có bằng chứng runner mới rằng stale RUNNING tự được khôi phục.

## Trạng thái các findings trước đó

| Finding | Kết luận review 2 |
|---|---|
| FND01 — point-in-time owner/artifact fence | Giới hạn còn lại đã được owner chấp thuận và docstring công bố; test hold-before-send xác nhận hành vi trước provider send. |
| FND02 — stale RUNNING/no receipt và recovery | Giới hạn còn lại đã được owner chấp thuận; không có reconciler tự động trong composition. |
| FND03 — bằng chứng PostgreSQL cho SENT/restart | Log PostgreSQL mới xác nhận node pass 4/4. Đóng khoảng trống “chưa có fresh PG run”; giới hạn test dùng engine chung và không tạo OS process/engine restart giữa hai composition vẫn được nêu ở trên. |
| FND04 — receipt acceptance assertion | Được test kiểm tra đúng một receipt authoritative và revision khớp job đã lưu; fresh PostgreSQL node pass 4/4. |
| FND05 — stale-owner test assertion yếu | Đã siết: test yêu cầu các trạng thái cụ thể nêu trong R3, bao gồm RUNNING, null disposition, không result ref/receipt và invocation/analysis side effects. |
| FND06 — valid-format digest mismatch | Có unit case với SHA-256 hợp lệ nhưng khác; unit suite và stale-artifact PostgreSQL node pass. |
| FND07 — typing | Không ghi nhận lỗi ở ba file implementation/unit-test; strict check toàn bộ bốn file vẫn có 60 diagnostics trong integration test. Kết quả này được công bố, không gọi là mypy pass. |
| Review 2 mới — stale-owner analysis side effect | P3, giới hạn synthetic/local; cần xử lý hoặc ràng buộc rõ trước khi mở rộng luồng. |

**Disposition:** Bằng chứng mới xác nhận hành vi B1 P2 trong phạm vi local synthetic, với các quyết định giới hạn đã được owner ghi nhận. Ghi nhận P3 stale-owner analysis state; chưa có cơ sở để tuyên bố artifact persistence, cleanup/reconciliation, audit delivery hoặc true OS-process/engine restart đã được chứng minh.

## Phụ lục A — Phán quyết và phân loại bằng chứng

### Mốc trước khi nối phụ lục

- Branch: `feature/feat063-be-foundation`; HEAD: `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index: rỗng.
- `git status --porcelain=v1`: 114 mục (Git mặc định gộp thư mục untracked); đây là checkout có thay đổi sẵn, không phải worktree sạch.
- SHA-256 của report ngay trước khi append: `A4CCA5798FB5DC47C83290F98CE44FE5A1A5AFD0114B809670DFF3C40B2B2A56`, khớp hash ghim của prompt bổ sung.
- Phụ lục này không sửa lại nội dung R1–R7 hoặc bảng finding cũ. Quyết định owner (c)–(e) được xem là ranh giới đã chốt, không mở lại trong review này.

### Phán quyết

- **F1 — ACCEPTED.** Đường `create_app()` chuyển factory vào runtime; composition chỉ được bật qua gate local/test, PostgreSQL và cờ synthetic bật rõ ràng. Contract test đường app thật đạt 1 passed. Tham chiếu: report §R4; `backend/src/sketch2life/interfaces/http/app.py:731–733`, `backend/src/sketch2life/interfaces/http/be1_runtime.py:94–125`, `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py:628–633`; log `contract-f1.log`.
- **F2 — ACCEPTED.** Bằng chứng PostgreSQL mới là 20 lần gọi cho 7 test node đã định, tất cả PASS, 0 SKIP, 0 FAIL; các stdout/stderr và command khớp node. Các nhóm được chạy 4/2/2/4/2/2/4 lần theo thứ tự success, UNKNOWN, hold-before-send, stale-owner, stale-artifact, concurrent duplicate và rebuild/replay. Unit 29 passed, F1 contract 1 passed và offline regression 460 passed; không chạy lại các bộ này trong phụ lục. Không có P1/P2 còn mở ngoài ranh giới được owner chấp thuận. Tham chiếu: Addendum 5b plan và thư mục log owner `.claude/handoff/snapshots/GB1_P2_A5B_20261104T194708/`; test tại `backend/tests/integration/test_be1_synthetic_pilot_postgres.py:3270–3498,3570–3622`.
- **B1 tổng trong phạm vi review này — ACCEPTED_WITH_CONDITIONS.** F1 và F2 đạt, PostgreSQL evidence mới không có skip/fail, và finding còn lại là P3 ngoài gate P1/P2. Chấp nhận chỉ cho B1 local/test synthetic, default-off, với stub loopback. Đây không phải xác nhận production readiness hay phê duyệt một goal tiếp theo.

Điều kiện của verdict tổng:

1. Giữ nguyên ranh giới local/test synthetic và default-off của B1; không dùng kết quả này để bật dữ liệu không synthetic hoặc provider thật.
2. Trước khi mở rộng sang dữ liệu/provider không synthetic, implementer phải đề xuất cách cleanup/invalidation/reconciliation cho analysis orphan, bổ sung kiểm tra reader và regression; owner duyệt phạm vi đó trước khi triển khai.
3. B2 là goal riêng, review này không tự khởi chạy hay phê duyệt B2. P3 không cản một bước B2 chỉ dùng synthetic/local/default-off nếu bước đó không đọc, công bố hoặc xem các analysis orphan là kết quả được chấp nhận. Nếu B2 thêm projection/route đọc các row này hoặc mở rộng dữ liệu/provider, phải đáp ứng điều kiện 2 trước.

### Phân tích P3 — stale-owner side effect và quyết định (d)

Quyết định (d) chấp nhận cho pilot việc completion stale có thể để job ở `RUNNING`, chưa có receipt/result, không đổi AI Jobs runtime; generic recovery tồn tại nhưng chưa được nối vào dispatcher. Nó **không nói rõ và không bao trùm đầy đủ** side effect bổ sung là một analysis row bền vững cùng invocation `SUCCEEDED` đã được ghi trước khi AI Jobs từ chối completion. Vì vậy đây là phần mở rộng của giới hạn (d), được giữ thành P3 chứ không đổi âm thầm quyết định owner.

Test stale-owner hiện khóa đúng trạng thái: job `RUNNING`, không disposition/result ref/receipt, invocation `SUCCEEDED`, một analysis row, attempt outcome rỗng (`test_be1_synthetic_pilot_postgres.py:3570–3622`). Flow ghi analysis qua transaction của `SqlAnalysisRepository` trước khi kết quả job được accept/reject (`application/services/vision_analysis.py:552–583`; `infrastructure/vision_analysis/repository.py:200–230`); sau đó pilot provider trả claim dựa trên tính authoritative của observation (`pilot_composition.py:570–605`). Điều này đủ để xác nhận P3 là durable state không được tham chiếu bởi receipt/result của job, không đủ để khẳng định mọi consumer đều xử lý sai hoặc đúng.

P3 **không chặn B1 local synthetic/default-off hiện tại** theo quyết định owner. Trước dữ liệu không synthetic hoặc provider thật cần: (a) quy tắc invalidation/cleanup/reconciliation có owner và trạng thái cuối rõ; (b) regression cho orphan analysis và stale invocation; (c) rà toàn bộ route/projection/reader để chứng minh không consumer nào coi row không có authoritative job receipt là kết quả được chấp nhận. Tôi chỉ đối chiếu các hàm SQL `get_head`, `find_by_attempt`, `get_observation` trong `infrastructure/vision_analysis/repository.py:42–58,138–145`; **chưa kiểm tra đầy đủ mọi consumer/read surface**, nên hiện không kết luận rằng reader không thể phơi bày hoặc diễn giải row đó là accepted.

### FND-03 — mức chứng minh của restart/replay

Test dựng lại composition, worker, `InvocationLedger` và envelope sau mô phỏng crash; đồng thời gọi provider trực tiếp trên composition mới và yêu cầu stub vẫn chỉ có một lần gửi (`test_be1_synthetic_pilot_postgres.py:3388–3498`). Composition tạo một ledger object mới từ cùng SQLAlchemy engine (`pilot_composition.py:555–560,641–673`); ledger thực hiện claim/get bằng PostgreSQL (`infrastructure/vision_analysis/ledger.py:37–46,121–160`) và bảng có unique constraint theo `(job_id, attempt_id)` (`infrastructure/vision_analysis/tables.py:137–153`). Do đó test này **đủ đóng FND-03 cho B1 ở mức rebuild application objects và chứng minh durable PostgreSQL SENT chống gọi lại**. Một ledger RAM chỉ giữ state trong instance mới sẽ không có SENT/claim trước đó; lời gọi provider trực tiếp sau rebuild sẽ tạo thêm request và làm assertion `stub.calls == 1` thất bại. Kết luận này dựa trên cả đường test và implementation SQL; test không chứng minh một shared process-global RAM cache không tồn tại trong mọi thiết kế thay thế.

Giới hạn: test dùng cùng OS process và cùng SQLAlchemy engine/connection pool; nó không kill/relaunch tiến trình thật, dispose/tạo engine mới hay restart PostgreSQL. B1 không cần thêm cổng OS-process restart để chấp nhận guarantee object-rebuild đã duyệt. Nếu owner muốn tuyên bố guarantee cho process/engine restart thật, owner phải xác định đó là acceptance bắt buộc; khi được duyệt, implementer cần thêm test subprocess hoặc engine mới trước khi đưa ra tuyên bố đó.

### Bảng phân loại bằng chứng

Mỗi kết quả dưới đây nằm đúng một cột theo nguồn bằng chứng; log được đọc không đồng nghĩa với việc chạy lại test trong lượt append này.

| Kết quả | Tự xác minh (reviewer) | Owner-run (reviewer đọc log) | Implementer-reported (reviewer không tự kiểm) |
|---|---|---|---|
| Checkout trước append: branch, HEAD, index, 114 mục status | Branch/HEAD đúng; index rỗng; 114 mục theo `git status --porcelain=v1`. | — | — |
| Hash report trước append và 4 file source/test ghim | Report khớp `A4CCA579…B2B2A56`; bốn file source/test khớp hash cuối A5 đã ghim. | — | — |
| Đọc source/test và kết luận F1 | Đã đọc trực tiếp các đường composition, ledger, repository và test được dẫn ở trên. | — | — |
| PostgreSQL bảy node | — | 20 invocation PASS, 0 SKIP/FAIL; command/stdout/stderr và status trước/sau được đối chiếu trong `GB1_P2_A5B_20261104T194708`. Reviewer không kết nối DB. | — |
| Unit, F1 contract, offline regression | 29 passed, 1 passed, 460 passed theo log reviewer đã lưu; không rerun trong lượt append. | — | — |
| Ruff và strict mypy | Ruff check đạt; format: 3 file đã format, file PostgreSQL integration sẽ được formatter sửa; strict mypy có 60 lỗi chỉ trong file PostgreSQL integration và 0 lỗi ở composition/unit files. | — | — |
| Validators, diff-check, AST và R6 source scope | Harness/security/architecture và diff-check đạt trong log; AST xác nhận executable ngoài import không đổi; scope log cho thấy AI Jobs/schema/ledger/repository/worker và migration sạch so với HEAD, status/ledger khớp snapshot. | — | — |
| `TASK_APPROVAL.md` không đổi trong A5 | — | — | Addendum 5 ghi không sửa approval, nhưng không có bytes pre-A5 để so sánh độc lập: **NOT DETERMINED bằng byte comparison**. |

### Phạm vi kết luận

Reviewer không kết nối PostgreSQL, không chạy lại test trong lượt append, không đọc DB URL/credential, không chạy Alembic/Modal/provider và không thay source/test/approval/status. Bảng và phán quyết chỉ dùng source, log owner đã khử bí mật, và log reviewer đã lưu. SHA-256 mới của report sẽ được gửi ngoài file sau khi kiểm tra append.