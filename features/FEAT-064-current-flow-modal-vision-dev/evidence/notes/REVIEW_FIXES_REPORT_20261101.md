# Báo cáo sửa phát hiện review độc lập (T2 / T2B / B5), 2026-11-01

Phạm vi: chỉ thị owner trong `CODEX_PROMPT_REVIEW_FIXES_20261101.md` (mục B), được ghi ở mục "Review fixes — T2/T2B/B5" trong `approvals/TASK_APPROVAL.md`. Baseline: commit `f1f977478bd8d015fa83ec148c35d00f3576348a`. Lượt này KHÔNG dùng PostgreSQL, không mạng, không push.

## 1. Bảng phát hiện

| Mã | Nội dung | Trạng thái | Cách làm |
| --- | --- | --- | --- |
| M1 | Test bất biến tuổi hồ sơ quá lỏng | LÀM | `test_profile_age_invariant.py` viết lại: detector AST/nguồn `find_age_write_paths` bắt các mẫu (a) constructor `ManagedProfileModel(age_months=...)` kể cả qua module hoặc bí danh import, (b) `ManagedProfileModel(**kwargs)`, (c) gán/`+=`/gán có chú thích/gán tuple tới `x.age_months`, (d) `.values(age_months=...)`, `.values({"age_months": ...})`, `update(ManagedProfileModel)`, `query(Model).update(...)`, (e) `setattr(obj, "age_months", ...)`, (f) chuỗi SQL thô có `UPDATE`/`INSERT` cùng `age_months` hoặc `be1_managed_profiles` (bỏ qua docstring), (g) `Model.__table__.update()/insert()`, qua biến trung gian, hoặc `metadata.tables["be1_managed_profiles"]`; thêm bulk helper. Danh sách cho phép liệt kê đích danh `(file, hàm, loại)`: `be1_registry.py::create_profile` và `core_store.py::create_synthetic_profile`, cùng loại `constructor`. `check_against_allowlist` thất bại với thông điệp nêu rõ đường ghi mới và nhắc `ALLOWED_CREATION_PATHS`; cũng thất bại khi đường cho phép biến mất hoặc có thêm loại ghi khác. Mỗi mẫu có test meta bằng đoạn mã giả; có thêm test âm (đọc, select, dict phản hồi, bảng khác, SQL SELECT, docstring) để detector không báo giả. Không sửa mã sản phẩm. |
| M2 | Test guard trạng thái T2 chỉ chạy với `eligibility_ready` bị monkeypatch | LÀM | `test_synthetic_status_guard.py` thêm lớp `_FilteringDb` áp dụng mệnh đề WHERE, ORDER BY và LIMIT của đúng các câu SELECT mà guard và `eligibility_ready` thật phát ra (toán tử không hỗ trợ thì lỗi lớn tiếng). Các ca chạy với `eligibility_ready`, `load_profile_origin`, `load_synthetic_proof` thật, không monkeypatch: proof hết hạn, bị thu hồi, không gắn session, sai session, sai run, chưa tới hạn, schema lạ, sai child/purpose/org, không có proof, pilot tắt, môi trường production, thiếu settings, hồ sơ REAL chỉ có proof; `admitted_child_id=None` (403 `DEVICE_SCOPE_INACTIVE`); alias path `org_id`/`organization_id` (lạ thì 403, đúng thì qua); session `finished`/`lobby`/`configured` (403); grant bị thu hồi (401 qua bộ lọc); nhánh legal vẫn chạy (effective qua, revoked/khác purpose thì 409). Mỗi ca khẳng định mã lỗi và audit `denied_consent_pending`. |
| L1 | `MemberFact` đường legal chặt hơn | GHI NHẬN, giữ nguyên | Quyết định owner. |
| L4 | Giới hạn audience synthetic lệch giữa các cổng | LÀM (một phần thuộc allowlist) | Thêm hằng `SYNTHETIC_AUDIENCE_SIZE = 1` ở `domain/eligibility.py`; `domain/assistance.py::audience_refusal` dùng hằng này và từ chối (`CONSENT_REQUIRED`) mọi audience có thành viên synthetic mà số thành viên khác hằng (trước đó assistance cho phép 2 thành viên synthetic, mỗi người đúng scope, và cho phép trộn synthetic với legal). Cổng vision (`application/services/vision_analysis.py`) và reader (`be1_fact_reader.py`) NẰM NGOÀI allowlist nên giữ kiểm tra một-thành-viên riêng của chúng, KHÔNG đổi sang hằng chung; thay vào đó `test_synthetic_audience_limit.py` khẳng định ba cổng đồng thuận (1 thành viên: cho phép ở cả ba; 2 thành viên synthetic: từ chối ở cả ba, assistance và vision `CONSENT_REQUIRED`, reader `AUDIENCE_UNSUPPORTED`; trộn synthetic và legal: từ chối theo cả hai thứ tự; legal đa thành viên không đổi). Một test ép hằng bằng 2 để chứng minh assistance đọc đúng hằng chung. `test_be2_synthetic_basis.py` không cần đổi vì không có ca nào kỳ vọng nhiều thành viên synthetic được phép. |
| L5 | Cột `needs_owner` của C022-C024 còn chữ "xác nhận B4a/B4b" (giả định: L5 là mục F5.1 của file chỉ thị) | LÀM | Ba ô của CSV và sáu vị trí tương ứng trong MD (bảng tóm tắt và bảng chi tiết, cùng câu mô tả) đổi "xác nhận B4a/B4b lifecycle và schema owner" thành "chốt lifecycle B4b và schema owner". Không cột/dòng nào khác đổi; vẫn 192 dòng dữ liệu (193 kể cả tiêu đề), kết thúc dòng LF như bản gốc. Dòng có `blocked_by` chứa `B5`: chỉ `C099` (`B5`), KHÔNG đổi. |
| F4a | Reader: proof `session_id=None` | LÀM | `ELIGIBILITY_DENIED`, không có member/context/revision. |
| F4b | Reader: nguồn ném exception | LÀM | Bốn loại lỗi cho `SOURCE_UNAVAILABLE`, không rò chuỗi lỗi (kiểm cả `repr` kết quả); `KeyboardInterrupt` không bị nuốt. |
| F4c | Reader: `evaluated_at` naive | LÀM | Từ chối `ELIGIBILITY_DENIED` (không giả định UTC); thêm proof `issued_at`/`expires_at` naive cũng từ chối. |
| F4d | Digest `context_revision` đổi theo `revocation_revision` / `evidence_id` | LÀM, có giới hạn | `evidence_id`, tuổi, group: digest đổi, qua reader. Digest ổn định khi dữ kiện giống hệt hoặc chỉ `evaluated_at` đổi. `revocation_revision` KHÔNG quan sát được qua một lần đọc được phép (reader chỉ cho phép proof chưa thu hồi và revision 0, proof thu hồi bị từ chối trước khi tạo digest), nên test kiểm trực tiếp `_context_payload` + hàm digest: revision 0, 1, 2 cho ba digest khác nhau. |
| F4e | Vision service, synthetic ở TYPED_CONTEXT | LÀM | `test_vision_service_typed_context_synthetic.py`: service trả `REFUSED` / `CONTEXT_PORT_DISAGREEMENT`, `provider_invoked=False`, 0 lời gọi provider (đếm bằng fake), kho lưu trữ rỗng, lặp lại 3 lần vẫn vậy; image-only vẫn nhận cùng cơ sở synthetic (1 lời gọi, không typed context); synthetic tự khai cờ legal bị cổng domain từ chối trước (`CONSENT_REQUIRED`). |
| L6 | Audit mỗi lần từ chối ở guard trạng thái | GHI NHẬN, làm sau | Không sửa theo quyết định owner. |
| L7 | `revision_source="recorded"` chưa được phát ra | GHI NHẬN, làm sau | Không sửa theo quyết định owner. |
| B5 blocker | Blocker B5 trong B1 | KHÔNG ĐỔI | B5 mới có test offline; replay PostgreSQL chưa kết luận. |

## 2. Phủ test: offline và PostgreSQL

- Phủ offline ở lượt này: toàn bộ logic guard và quyết định typed trên các dòng dữ liệu đã lọc (proof/hồ sơ/consent/session/grant/membership), mã lỗi và audit; ba cổng audience; reader; service vision.
- Chỉ PostgreSQL mới phủ (KHÔNG chạy ở lượt này): hành vi dialect SQL thật của các câu truy vấn guard, round-trip `timestamptz` của proof, chỉ mục và thứ tự trên dữ liệu thật, ràng buộc CHECK/FK. Fake `_FilteringDb` chỉ mô phỏng WHERE/ORDER BY/LIMIT; nếu SQL thật khác hành vi đó thì chỉ PG thấy.

## 3. Số test

Mốc trước khi sửa (cùng lệnh, từ `backend/`, `-o addopts=''`, không `BE1_TEST_DATABASE_URL`): 5 file CI = 26 passed, 4 skipped; nhóm T1/T2/T2B/BE2 (6 file nêu trong R0) = 274 passed.

| File | Trước | Sau |
| --- | --- | --- |
| `test_profile_age_invariant.py` | 1 | 33 |
| `test_synthetic_status_guard.py` | 12 | 41 |
| `test_be1_fact_reader.py` | 29 | 43 |
| `test_synthetic_audience_limit.py` (mới) | 0 | 9 |
| `test_vision_service_typed_context_synthetic.py` (mới) | 0 | 6 |
| `test_be2_synthetic_basis.py` | 31 | 31 (không đổi) |

Sau khi sửa: 5 file CI vẫn 26 passed, 4 skipped; nhóm mở rộng (8 file) 364 passed. Tăng 90 test, không test nào hiện có bị đổi hay bỏ.

Đỏ trước, xanh sau (kiểm đột biến cục bộ, đã hoàn tác bằng cách khôi phục file):
- Bỏ kiểm `admitted_child_id is None` trong guard và bỏ nhánh proof không gắn session trong `be1_common`: 2 test mới của M2 đỏ (`unbound_session`, `rejects_a_grant_without_an_admitted_child`).
- Vô hiệu kiểm một-thành-viên trong `audience_refusal` (mô phỏng hành vi cũ): 3 test của L4 đỏ (hai synthetic, trộn, hằng chung).
- Bỏ kiểm `proof_fact.session_id != request.session_id` và làm `evidence_id` không vào digest trong reader: 2 test F4 đỏ.
- Các test F4 và vision ở trên không phát hiện lỗi thật trong `be1_fact_reader.py` / `context_revision.py`; file đó không bị sửa.
- Các test meta của M1 và test vision-service là test chống hồi quy cho hành vi đã đúng: xanh ngay lần đầu.

Rộng hơn: `tests/unit` và `tests/contract` còn 53 test đỏ và 25 lỗi gom test ở các file không liên quan (live image demo bị chặn mạng ngoài trong test offline, whiteboard/story video thiếu `tools` trên đường dẫn khi chạy từ `backend/`, vision v3 benchmark, v.v.); không file nào đụng assistance, eligibility, BE1 hay synthetic. Không so với HEAD vì không liên quan thay đổi này.

## 4. Kiểm tra tĩnh và validator

- `ruff check --config backend/pyproject.toml` trên mọi file sửa/tạo: sạch, ngoại trừ một lỗi I001 (thứ tự import) có sẵn ở `test_synthetic_status_guard.py` tại HEAD (số lượng không đổi). `ruff format --check` cho 3 file test mới/viết lại: sạch.
- `mypy --strict`: 0 lỗi MỚI. Còn đúng 7 lỗi có sẵn ở `test_be1_fact_reader.py` (một thiếu chú thích kiểu và `replace(**dict[str, object])`), giống hệt kết quả ở HEAD.
- `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, `git diff --check`: đều đạt (chạy từ gốc worktree).

## 5. File đã đổi

Sửa: `domain/assistance.py`, `domain/eligibility.py`, `test_profile_age_invariant.py`, `test_synthetic_status_guard.py`, `test_be1_fact_reader.py`, B1 CSV, B1 MD, FEAT-064 `approvals/TASK_APPROVAL.md` (chỉ thêm dòng). Tạo: `test_synthetic_audience_limit.py`, `test_vision_service_typed_context_synthetic.py`, báo cáo này. Toàn bộ LF, UTF-8, không BOM. SHA-256 (sau khi sửa, trừ báo cáo này): xem bảng dưới.

| File | SHA-256 |
| --- | --- |
| `backend/src/sketch2life/domain/assistance.py` | `1AF5211FB97C2E2175A673EC9E6A79D531187D2026DF8A53395CFD346F0A8488` |
| `backend/src/sketch2life/domain/eligibility.py` | `7BAB7BDDF15305E146EE0618341520EB71F17AF2FF35FC6D14A7025BC3F63520` |
| `backend/tests/unit/test_profile_age_invariant.py` | `072B69085B5BE0695FBF47938D50E42F2F210DA8D184D2E80493442AE9845F72` |
| `backend/tests/unit/test_synthetic_status_guard.py` | `405C7E7792CA2953709C60CA89D230CC33BEBA7BD23EA13477CB5E0A29F24D7F` |
| `backend/tests/unit/test_be1_fact_reader.py` | `3095A06BE51BDB9BCF57A6AFE2A803D838D0EE344B513BED95E4070B69ADFC70` |
| `backend/tests/unit/test_synthetic_audience_limit.py` | `F28846DBCB778D4F1C6C2A9256FFD77BFAE56DDECA0588F513FAF5AB073ADE3B` |
| `backend/tests/unit/test_vision_service_typed_context_synthetic.py` | `D38D63C2301A150A74179D6CF06313E8ADDB41C9ED5D9531BE190260C2D1FAE4` |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.csv` | `BA017D25C047A3B65EECF6408342D322FA54953E5C78E54100EC8A2BACE4E2FB` (trước: `7EDB7A63…`) |
| `features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.md` | `E657774B1483B68A35EE8A2CF617113221F0AC43B15447E9A43335D130C17DB8` (trước: `93727FAC…`) |
| `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md` | `10A1F69AF671234855818AD2286CF55285C8AC0ACAEB9F6C533F56370592B71C` |

## 6. Không làm, giới hạn

- Không PostgreSQL, không push, không sửa L6/L7, không đổi blocker B5, không sửa router/runtime/migration, `be1_fact_reader.py`, `context_revision.py`, hay cổng vision.
- L4 chưa dùng hằng chung cho cổng vision và reader vì hai file đó ngoài allowlist; đồng thuận được giữ bằng test, nên đổi giới hạn trong tương lai cần sửa cả ba chỗ (test sẽ đỏ nếu lệch).
- `_FilteringDb` là mô phỏng SQL; không thay thế replay PostgreSQL.
