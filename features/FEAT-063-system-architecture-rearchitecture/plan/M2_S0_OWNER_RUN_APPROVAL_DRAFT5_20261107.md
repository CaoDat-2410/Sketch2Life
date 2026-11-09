# M2 S0-owner-run Task Approval — Draft 5

**Status: DRAFT — chưa phải approval, chưa được owner duyệt, chưa khởi chạy.** Bản này đề xuất một lượt đối soát owner-run chỉ đọc. Nó không tự mở pha S0-owner-run và không cho phép chạy lệnh cho tới khi owner hoàn tất lựa chọn, approval riêng và pin hash sau review độc lập.

## Owner decision record

Bản này là DRAFT tổng hợp hướng owner đã chốt và các đề xuất cần owner hoàn tất trước một Task Approval thực thi riêng. Các quyết định hướng không tự mở S0-owner-run, không cho chạy script và không thay thế các attestation còn thiếu.

## Plan và baseline

- **Plan:** plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md
- **Plan SHA-256:** 7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1
- **Baseline đề xuất:** branch feature/feat063-be-foundation; HEAD dd70685eae58aaaefea3e567f5c23d09345a8513; index rỗng. Approval thực thi phải pin lại; lệch thì dừng và xin xác nhận.
- **Owner directions:** D-144, D-148, D-150, D-151; D-150 chỉ đóng S0-doc; D-151 chỉ chấp nhận Draft 10 làm planning baseline. Không pha implementation nào được mở.
- **S0-doc evidence:** evidence/M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md, SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001.

## Owner-confirmed directions for Draft 5 (not execution approval)

| Chủ đề | Hướng đã ghi nhận |
|---|---|
| Database mục tiêu | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** dùng database BE tổng có tên `sketch2life` trong Docker, chỉ đọc cho S0-owner-run. Nguồn repo: D-144 §9.1, `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:274`. Tên container, port và identity hiện tại chưa được xác minh. |
| K3 | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** chọn P1 static-AST; chấp thuận mở rộng allowlist chỉ đọc từ 9 lên đúng 28 revision files trong manifest bên dưới. Đây là lựa chọn cho bản nháp, không phải quyền chạy. |
| Nonlocal host | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** không dùng host non-loopback và không dùng `--allow-nonlocal-host`. |
| Đọc `.gitignore` | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** cho phép đọc `.gitignore` để xác minh log local được ignore. Repo rule `.gitignore:99` là `tmp/`; kiểm tra Git chỉ đọc cũng match đường dẫn mypy cache mẫu. |
| User PostgreSQL | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** dùng user công khai `postgres`; owner xác nhận đây là superuser. Vì vậy điều kiện least-privilege **không đạt**; không mô tả đây là role tối thiểu. Script giữ transaction read-only, không phát lệnh ghi. Tạo role read-only riêng nằm ngoài phạm vi này. A2 chỉ ghi nhận lịch sử current user/database owner `postgres` tại thời điểm 2026-11-03 (`features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_MAIN_DB_TEARDOWN_FIX_20261103.md:23`); không xác minh role Docker hiện tại. |
| 58 hàng synthetic | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-06, D-144 §9.2):** giữ nguyên, không cleanup. Nguồn repo: `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:274`. |
| Database cho pha ghi về sau | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** S1a/S2 dùng database riêng trong cùng container, tạo từ schema-only copy của `sketch2life`, không sao chép data; chi tiết phải được ghi trong Task Approval S1a. Đây chỉ là hướng tương lai, không thuộc S0-owner-run. D-144 §9.1 cũng yêu cầu database riêng cho pha ghi; cách schema-only là chỉ thị owner hiện tại. |
| Script r4 và review | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** pin script r4 bằng SHA-256 `C28527CE531A4C1816B04BB4BA071B3F237CAD0AC7E95794A04CC86A2FABADB5`; tính lại ngay trước approval thực thi, lệch một byte thì approval cũ vô hiệu. Theo kết quả review do owner cung cấp, sau bốn vòng độc lập verdict cuối là ACCEPT_WITH_CONDITIONS, 0 P1, 0 P2, 6 P3. Chưa tìm thấy báo cáo review chi tiết trong thư mục evidence của repo; đây là provenance được owner báo lại, không phải kết quả review mới của Draft 5. |
| Mypy | **OWNER CHỌN:**  |
## Approved scope đề xuất — chưa có hiệu lực

Một lượt owner-run chỉ đọc lên database BE tổng có tên `sketch2life` để thu thập inventory metadata, row counts, grouped origin counts và các kiểm tra bên dưới. Tên database đã được owner chọn; container, port, identity manifest và chứng cứ chỉ chứa synthetic data vẫn phải được owner cung cấp trong approval thực thi. Không đọc giá trị hàng, không sửa schema/dữ liệu, không cleanup 58 hàng lịch sử, không chạy migration và không dùng database write-phase. S1a/S2 phải dùng database riêng trong cùng container theo hướng schema-only copy không kèm data; hướng đó chưa mở và phải ghi ở Task Approval S1a.

- **Existing files permitted to modify:** none.
- **Script input:** evidence/scripts/m2_s0_owner_run_readonly_20261107_r4.py; không chỉnh sửa script trong lượt owner-run.
- **Output files chỉ được tạo sau approval riêng:** `inventory.json` và `inventory.txt` trong run directory mới dưới `.claude/handoff/logs/`; mypy-*.txt chỉ nếu owner chọn/duyệt mypy. Vị trí cache mypy vẫn là `OWNER CHỌN` giữa hai đề xuất ở mục Mypy; Draft 4 trước đây yêu cầu ngoài repo, còn phương án `tmp/` nằm trong repo nhưng bị ignore. Approval này không tạo output Alembic vì không có phương án chạy Alembic CLI.
- Owner đã chấp thuận cho Draft 5 việc đọc `.gitignore` (chỉ đọc) ngoài allowlist Draft 10 §8 để xác minh log/cache local được ignore. Approval thực thi vẫn phải xác minh đường dẫn output/cache cụ thể bằng Git metadata; nếu không được ignore thì dừng, không tạo output tại đó.
- Script chỉ tạo output không ghi đè; nếu không thể tạo đủ hai artifact thì dừng an toàn, không giữ file dở dang.

## Các trường owner bắt buộc điền trước approval thực thi

Không ghi URL kết nối, mật khẩu hoặc token vào hồ sơ. Không để trống trường bắt buộc trong approval thực thi. Alembic CLI P2 không thuộc approval này.

| Trường cần hoàn tất | Giá trị/trạng thái |
|---|---|
| Database BE tổng | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** `sketch2life`, chỉ đọc trong S0-owner-run; D-144 §9.1, `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md:274`. |
| Tên Docker container/service và cách xác minh | **OWNER ĐIỀN:** tên chính xác và bằng chứng container đang chạy. Cách lấy: xem danh sách container Docker hiện tại. |
| Port host được map tới PostgreSQL | **OWNER ĐIỀN:** port hiện tại theo mapping Docker; không suy từ cấu hình cũ. A2 lịch sử từng cần port 5433 để tới `sketch2life` (`features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_MAIN_DB_TEARDOWN_FIX_20261103.md:23`); kiểm tra lại mapping hiện tại bằng danh sách port Docker. |
| Host/user thực tế và current identity | **OWNER ĐIỀN:** attestation identity từ shell riêng và output đã lọc; user được chọn là `postgres`, nhưng kết nối hiện tại chưa được xác minh. Không ghi URL/mật khẩu. |
| Privilege acknowledgement | **OWNER ĐIỀN:** trước khi chạy, attestation current identity phải xác nhận đúng user `postgres`; hồ sơ owner xác nhận user này là superuser nên least-privilege không đạt. Không tạo role khác; giữ toàn bộ checkbox chưa tick và không gọi quyền này là tối thiểu. |
| Baseline manifest trước inventory | **OWNER ĐIỀN:** database name, revision rows, số schema/bảng và tổng row count; không coi số A2 lịch sử là hiện tại. |
| Dump file ngoài repo và SHA-256 | **OWNER ĐIỀN:** tên file và hash; lấy hash SHA-256 sau khi tạo dump, không đưa dump vào repo. |
| Restore trial | **OWNER ĐIỀN:** đã thử/chưa thử, kết quả và người xác nhận. Chưa có bằng chứng repo cho restore trial hiện tại. |
| Người chạy và người bảo toàn/khôi phục DB | **OWNER ĐIỀN:** tên người chạy và tên người chịu trách nhiệm khôi phục. **ĐỀ XUẤT (Codex, chưa xác nhận):** Person 2 / task owner trực tiếp chạy vì FEAT-064 CONTEXT.md:58 ghi Person 2 là integration owner/operator; danh tính cụ thể vẫn do owner điền. |
| Số lần và timeout cho từng command | **ĐỀ XUẤT (Codex, chưa xác nhận):** script một lần/5400 giây; `mypy --version` một lần/60 giây; mypy baseline một lần/900 giây. Owner cần xác nhận lại trong approval thực thi. Tính toán ở mục Command ceiling đề xuất bên dưới. |
| K3 lựa chọn | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** P1 static-AST; K3 NOT RUN chỉ là phương án thay thế nếu owner đổi hướng trước approval thực thi. |
| Allowlist K3 | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** cho phép đúng 28 revision files ở manifest; đây là mở rộng read-only, không cho import revision hay application module. |
| P2 Alembic CLI | Không nằm trong approval này; phụ lục chỉ tham khảo và không cấp quyền thực thi. |
| Nonlocal host | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** từ chối; không bật `--allow-nonlocal-host`. |
| Script hash | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** r4 `C28527CE531A4C1816B04BB4BA071B3F237CAD0AC7E95794A04CC86A2FABADB5`; rehash trước approval thực thi. |
| Đọc `.gitignore` | **OWNER ĐÃ QUYẾT ĐỊNH (hội thoại 2026-11-07):** được phép đọc để xác minh ignore. `.gitignore:99` ghi `tmp/`; kiểm tra Git chỉ đọc khớp cache mẫu dưới `tmp/`. Không có log runtime nào được tạo trong lượt soạn Draft 5. |
| Mypy command/interpreter/version/cache | **OWNER CHỌN:**  |
| Synthetic-only proof cho các bảng thiếu `data_origin` | **OWNER ĐIỀN:** bằng chứng theo từng bảng. Danh sách bảng thiếu cột này hiện chưa thể biết nếu chưa có inventory; các A2 count-map chỉ có số đếm, không có provenance. Trong nguồn đã đọc chưa có bằng chứng synthetic-only theo từng bảng này; nếu owner không bổ sung được proof thì K5 = NOT RUN. |
| Synthetic-only proof cho 24 hàng baseline A2 | **OWNER ĐIỀN:** bằng chứng theo bảng cho toàn bộ 24 hàng. A2 report và count maps không chứng minh các hàng ban đầu là synthetic; hiện trạng là chưa có bằng chứng. Nếu không chứng minh được toàn bộ dữ liệu thuộc phạm vi synthetic-only thì K5 = NOT RUN; không chỉ xét phần tăng 58. |
| Tổng row count cho inventory | **OWNER ĐIỀN:** tổng hiện tại theo script, gồm mọi hàng hiện có, kể cả 24 hàng lịch sử ban đầu và mọi delta khác; không coi 82 hay 58 là số hiện tại. |

## A2 row-count evidence — historical only, not current DB state

A2 report ngày 2026-11-03 ghi 117 bảng, 24 hàng trước test và 82 sau teardown lỗi, tức delta +58 bảng-row; report nêu delta chi tiết nằm trong snapshot. Nguồn: `features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_MAIN_DB_TEARDOWN_FIX_20261103.md:27,33` (SHA-256 `3A8BDC49BEBB6FF768E1A441A551A275A115CE675E95FDF3D1550DBF8D469511`). Count maps có trong snapshot `.claude/handoff/snapshots/GA2_A2_FINAL_20261103T181341/`: `db_row_counts_all_schemas_before.json` (file SHA-256 `5DB346429F80328FA013409B6A1084568F6A5CB98D54C675BF176AFD33E6E293`, embedded counts SHA-256 `3b08a731709bf11b84414cfca57786a095ea187bc6520d7f079b7c9d441d83a9`) và `db_row_counts_after_first_failed_teardown.json` (file SHA-256 `6B444FAEC17C4285E1FB5AC1AA96F9124A3C079D1CD9E07DAA26D4BFDCAF6353`, embedded counts SHA-256 `b3da6df4225bf6b1e1b2534b67842987acabb7eb518bfcd91c87e7cc79107aa7`). So sánh hai snapshot JSON xác nhận 117 bảng trước/sau, 24 → 82 hàng và delta dưới đây. Đây là lịch sử, không xác minh database/container hiện tại; số hàng trong các bảng không phải số thực thể unique.

| Table | Delta lịch sử |
|---|---:|
| `ai_jobs.attempt` | +1 |
| `ai_jobs.command_receipt` | +1 |
| `ai_jobs.job` | +1 |
| `ai_jobs.outbox` | +2 |
| `ai_jobs.semantic_request` | +1 |
| `pilot_vision.epoch` | +1 |
| `pilot_vision.request` | +1 |
| `public.be1_adult_identities` | +1 |
| `public.be1_child_turns` | +1 |
| `public.be1_classrooms` | +1 |
| `public.be1_device_grants` | +1 |
| `public.be1_managed_profiles` | +1 |
| `public.be1_organization_assignments` | +1 |
| `public.be1_organizations` | +1 |
| `public.be1_session_groups` | +1 |
| `public.be1_session_learning_stage_events` | +2 |
| `public.be1_session_learning_stages` | +1 |
| `public.be1_session_memberships` | +1 |
| `public.be1_sessions` | +1 |
| `public.be1_synthetic_eligibility_proofs` | +1 |
| `public.core_aggregate_revisions` | +3 |
| `public.core_asset_metadata` | +2 |
| `public.core_audit_entries` | +16 |
| `public.core_canvas_operations` | +2 |
| `public.core_idempotency_receipts` | +2 |
| `public.core_outbox_events` | +11 |

Tổng delta bảng-row là 58 theo phép cộng trên. Đây là phần tăng được ghi nhận sau lượt test/teardown lỗi; không tự chứng minh riêng từng hàng synthetic, không chứng minh 24 hàng baseline là synthetic và không thay thế owner proof. Owner đã quyết định giữ nguyên 58 hàng lịch sử, không cleanup. K5 phải đếm toàn bộ tổng hiện tại và cần synthetic-only proof cho cả baseline 24 lẫn mọi bảng thiếu provenance; thiếu proof thì NOT RUN.

## Lựa chọn K3 trong approval này

Owner đã chọn P1 static-AST trong hội thoại 2026-11-07 và chấp thuận allowlist 28 revision files. K3 NOT RUN chỉ là phương án thay thế nếu owner đổi quyết định trước khi approval thực thi. Không có Alembic CLI trong approval này; nếu owner giữ P1, lựa chọn đó phải được ghi lại trong approval thực thi riêng.

### P1 — Static AST trên 28 revision files

Script đọc bytes và SHA-256 của đúng 28 file revision dưới đây, sau đó phân tích AST/literal metadata mà không import revision hoặc application modules. Script kiểm tra exact manifest, từng hash, revision identifiers, down_revision, depends_on, branch_labels, dependency closure và chu trình. Nếu manifest/hash/AST/graph không xác minh được, K3 = NOT RUN; không tự dò thêm file.

Draft 10 §8 liệt kê 9 revision modules. Theo quyết định owner đã chốt, P1 mở rộng allowlist chỉ đọc thêm 19 file, tổng đúng 28 file; không import revision hoặc application modules. Approval thực thi phải rehash đủ manifest trước khi chạy.

**K3 result mapping theo r4:** PASS chỉ khi danh sách revision trong `alembic_version`, sau khi sort, bằng chính xác tập source heads được static-AST tính từ cả `down_revision` và `depends_on`. Hash/manifest/AST/graph không xác minh được thì NOT RUN; tập khác thì FAIL; thiếu bảng `alembic_version` thì FAIL theo mã r4. Source graph đã pin suy ra 9 effective heads; con số 9 là suy luận từ mã static-AST, không phải kết quả runtime của Alembic CLI. P1 không chạy Alembic CLI.

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

### K3 NOT RUN

K3 NOT RUN chỉ dùng nếu owner đổi lựa chọn P1 trước approval thực thi. Khi đó script vẫn đọc `alembic_version` như inventory nhưng không so sánh DB revision rows với source và không suy diễn database head. Nếu bảng version không tồn tại, r4 ghi K3 = FAIL; nếu revision IDs không xác minh được, ghi NOT RUN. Script không chạy Alembic CLI. Nếu giữ lựa chọn hiện tại, P1 dùng đúng manifest 28 revision files phía trên; kết quả theo quy tắc K3 đã nêu ở mục P1.

## Draft 4 behavior updates for P3-1 through P3-4

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

K2 chạy trước K1. Khi K2 fail, K2 = FAIL; K1 và K3–K7 đang ở trạng thái mặc định chưa thử nên được ghi NOT RUN / STOPPED_AFTER_K2. Khi K1 mismatch sau khi K2 đã PASS, K1 = FAIL với detail DATABASE_NAME_MISMATCH; ACTUAL_NAME_WITHHELD; K2 giữ PASS vì đã thực sự chạy và đạt; K3–K7 đang chưa thử được ghi NOT RUN / STOPPED_AFTER_K1. Hàm đánh dấu chỉ đổi gate có status NOT RUN và detail NOT_ATTEMPTED; không ghi đè PASS, FAIL, COLLECTED hoặc NOT RUN đã có detail khác. Không ghi tên database thực tế đọc được vào detail hoặc field khác ngoài tên database kỳ vọng do owner nhập.

### Host option, Python và K5 timeout

argparse dùng `allow_abbrev=False`. Mặc định chỉ chấp nhận literal loopback IP hoặc tên localhost không phân biệt hoa/thường (không DNS resolve). r4 có cờ `--allow-nonlocal-host` kèm `--nonlocal-host-reason`, nhưng owner đã quyết định không dùng host nonlocal và không bật cờ đó; không dùng lý do để mở ngoại lệ. JSON/TXT vẫn ghi `nonlocal_host_flag_used: false`. Không thêm `inet_server_addr()`; địa chỉ container qua mapped port không phải bằng chứng loopback.

Python version guard phải chạy ngay sau import sys và trước import thư viện khác; Python khác 3.12 chỉ in STOPPED_SAFELY: PYTHON_312_REQUIRED, không traceback/đường dẫn. Script vẫn phải chạy bằng Python 3.12 của backend venv: cú pháp yêu cầu từ interpreter cũ có thể gây SyntaxError lúc compile trước khi guard chạy; guard không bắt được lỗi biên dịch.

Timeout cố định nội bộ đọc từ script: statement_timeout = 20000 ms, lock_timeout = 3000 ms, connect_timeout = 5 giây. COUNT(*) trên bảng lớn hoặc GROUP BY data_origin có thể gặp QueryCanceled (STATEMENT_TIMEOUT) hoặc LockNotAvailable (LOCK_TIMEOUT). Khi một trong hai lỗi xảy ra trong K5, đúng operation đó là NOT RUN với detail cố định TABLE_COUNT_STATEMENT_TIMEOUT, TABLE_COUNT_LOCK_TIMEOUT, ORIGIN_GROUP_STATEMENT_TIMEOUT hoặc ORIGIN_GROUP_LOCK_TIMEOUT; tên bảng chỉ ở trường riêng, không nằm trong detail. K6/K7 chưa thử được đánh dấu STOPPED_AFTER_K5; mọi kết quả đã có trước đó được giữ nguyên. K5 không bao giờ PASS; không suy ra bảng rỗng hoặc synthetic-only, không ghi count chưa thu được và không giả định tổng 58 là tổng DB. Khi nhóm origin có bucket khác SYNTHETIC_DEV, K5 = FAIL và K6/K7 chưa thử được đánh dấu STOPPED_AFTER_K5.

Ngoài K5, `LockNotAvailable` trên truy vấn cố định cho version table/catalog/CHECK đi theo `safe_exception_code`: `UNEXPECTED_SAFE_STOP`, exit 6. Trường hợp này không gọi `mark_gates_stopped_after`; các gate chưa tới giữ `NOT RUN / NOT_ATTEMPTED`, không đổi thành `STOPPED_AFTER_*`. K7 là mypy owner chạy ngoài script nhưng routine đánh dấu sau một stop script có thể gắn nhãn `STOPPED_AFTER_Kx`; nhãn này chỉ biểu thị thứ tự dừng, không có nghĩa mypy đã chạy.

Dừng sớm theo r4: Python-version guard trước khi tạo output directory trả exit 2 và không tạo report; thiếu psycopg (`PSYCOPG_V3_UNAVAILABLE`) hoặc mật khẩu rỗng/non-TTY (`EMPTY_PASSWORD_INPUT`) xảy ra sau khi chuẩn bị output, trả exit 5 và ghi cặp JSON/TXT; lỗi kết nối (`DATABASE_CONNECTION_FAILED`) trả exit 6 và ghi cặp JSON/TXT nếu output directory đã được tạo. Ba nhánh này không gọi `mark_gates_stopped_after`; nếu cặp report ghi được, K1–K7 đều `NOT RUN / NOT_ATTEMPTED`. Lỗi ghi report vẫn tuân theo mã thoát ưu tiên của r4.

## Tiền điều kiện và identity

Trong approval thực thi, owner đánh dấu từng điều kiện ĐÃ XONG hoặc CHƯA XONG. Bất kỳ điều kiện bắt buộc nào CHƯA XONG thì không chạy:

- [ ] OWNER XÁC NHẬN: dump/restore point ngoài repo; ghi tên file/hash dump và đã thử restore hay chưa.
- [ ] OWNER XÁC NHẬN: container, database và identity manifest khớp target đã duyệt.
- [ ] OWNER XÁC NHẬN: database chỉ dùng cho inventory read-only, không phải write-phase.
- [ ] OWNER XÁC NHẬN: current identity là user `postgres` theo lựa chọn owner; owner đã xác nhận user này là superuser, đây là ngoại lệ đã biết so với least-privilege. Không tạo role mới; script vẫn chỉ được chạy theo transaction READ ONLY.
- [ ] OWNER XÁC NHẬN: password chỉ nhập tại getpass ẩn; không command line, env, file, log hoặc chat.
- [ ] OWNER XÁC NHẬN: PGHOST, PGPORT, PGUSER trong shell riêng đúng target; không có biến password/service/file/options override.
- [ ] OWNER XÁC NHẬN: script chạy trong shell riêng không chứa biến môi trường nào có ://; chặn rộng là chủ ý và có thể từ chối vì biến không liên quan, khi đó phải dùng shell sạch.
- [ ] OWNER XÁC NHẬN: .claude/handoff/logs/ đang bị ignore; chấp thuận script đọc .gitignore ngoài allowlist Draft 10 §8.
- [ ] OWNER XÁC NHẬN: git status trên backend/alembic/versions sạch trước khi chạy.
- [ ] OWNER XÁC NHẬN: đã xác định các bảng tạo nên 58 synthetic rows và có bằng chứng cho bảng thiếu provenance.
- [ ] OWNER XÁC NHẬN: đã chọn P1 hoặc ghi K3 NOT RUN; không suy ra lựa chọn.
- [ ] OWNER XÁC NHẬN: dùng literal loopback; không bật `--allow-nonlocal-host` và không đổi connection để lách guard.
- [ ] OWNER XÁC NHẬN: mypy command/version/cache/timeout đã duyệt hoặc mypy để NOT RUN.

K1 chỉ so tên current_database() với tên owner duyệt. Nó không xác minh Docker container, host/port/user, revision head, schema/table count hoặc tổng row count. Container khác có DB trùng tên vẫn có thể qua K1. Sau khi chạy, owner đối chiếu riêng manifest (database name, revision, schema count, table count, tổng row count) và tự xác minh container bằng phương thức riêng. Không gọi đây là full identity PASS chỉ vì tên database khớp.

## Command ceiling đề xuất — chưa được chạy

Các con số dưới đây là đề xuất Codex, chưa được owner xác nhận làm trần thực thi. Chỉ có hiệu lực nếu được owner điền/xác nhận trong Task Approval riêng sau independent review, các attestation và hash gate. Script dự kiến một lần tối đa 5400 giây; `mypy --version` một lần/60 giây; mypy baseline một lần/900 giây. Không chạy lệnh Alembic CLI trong approval này. Thiếu xác nhận, lỗi, timeout hoặc output thiếu thì dừng.

**Cơ sở đề xuất timeout script:** r4 có timeout statement 20 giây, lock 3 giây và connect 5 giây. Dùng cận bảo thủ theo inventory lịch sử 117 bảng: tối đa 117 COUNT queries + tối đa 117 GROUP BY `data_origin` queries = 234 × 20 giây = 4680 giây; cộng 10 query cố định × 20 giây = 200 giây và connect 5 giây, tổng lý thuyết 4885 giây. Đề xuất 5400 giây để còn 515 giây dự phòng; 300 giây không đủ cho cận này. Số 117 là lịch sử A2, không phải hiện tại; owner phải điền inventory hiện tại và xác nhận timeout lại trong approval thực thi. Mỗi query vẫn có timeout nội bộ của r4.

### 1. Inventory script B

Python 3.12 trong backend virtual environment; mật khẩu hỏi ẩn. Đây là command candidate, chưa được phép chạy; placeholder duy nhất còn lại là ID thư mục run:

    & .\backend\.venv\Scripts\python.exe .\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s0_owner_run_readonly_20261107_r4.py --expect-db sketch2life --out-dir .claude\handoff\logs\{OWNER_RUN_ID} --alembic-method static-ast

Không thêm `--allow-nonlocal-host`. Output directory phải mới và đã xác minh ignore. Script chạy K2 trước K1: `SHOW transaction_read_only` phải trả `on` trước mọi query khác. K4/K6 chỉ COLLECTED, không PASS. K5 không bao giờ PASS; chỉ GROUP BY cột `data_origin`; bucket thành SYNTHETIC_DEV/REAL/LEGACY_UNCLASSIFIED/NULL/EMPTY/OTHER; bucket không synthetic gây FAIL/STOP, thiếu provenance/proof thì NOT RUN.

### 2. Mypy version và baseline (OWNER CHỌN — để trống)

**OWNER CHỌN:** command, interpreter/version, package scope, timeout và cache location chưa được owner duyệt; không có candidate command trong Draft 5. Nếu sau này owner chọn chạy mypy, thực hiện trong shell con để cô lập import path; nếu dùng cùng shell phải lưu/khôi phục `PYTHONPATH` và `MYPYPATH` trong `finally`. Crash/timeout/no verdict = NOT RUN, không PASS. D-144 §9.6 yêu cầu ghi command/version; M2 không thêm diagnostic so baseline.

Hai đề xuất về cache (không chọn thay owner):

- **ĐỀ XUẤT (Codex, chưa xác nhận), phương án A:** `tmp/m2-s0-owner-run/mypy-cache`. `.gitignore:99` ignore `tmp/`, và kiểm tra Git chỉ đọc khớp đường dẫn mẫu. Đánh đổi: cache nằm trong repository tree dù ignored, trái yêu cầu Draft 4 “cache ngoài repo”; harness mới của task yêu cầu scratch dưới `tmp/<task>/`.
- **ĐỀ XUẤT (Codex, chưa xác nhận), phương án B:** `$env:TEMP/s2l-mypy-s0-owner-run`, cache ngoài repo như Draft 4; môi trường Windows này có thể khiến owner phải dọn ổ C. Chưa chọn phương án nào.

## Diễn giải gates và giới hạn inventory

| Gate | Bằng chứng / ý nghĩa | Kết quả được phép ghi |
|---|---|---|
| K1 — Database name | So current_database() với tên owner duyệt; không kiểm container/full manifest. | Mismatch hoặc không đọc được: STOP. Match chỉ là name check. |
| K2 — Read-only | default_transaction_read_only=on và connection.read_only=True trước SQL đầu tiên; SHOW transaction_read_only là SQL đầu và phải trả on. | Không xác nhận on: STOP, không query tiếp. |
| K3 — Alembic | Owner đã chọn P1 static-AST; so danh sách DB revision rows đã sort với source heads tính từ `down_revision` và `depends_on`. 9 effective heads là suy luận từ graph tĩnh đã pin, không phải CLI output. | PASS khi bằng nhau; FAIL khi khác hoặc thiếu `alembic_version`; NOT RUN khi manifest/hash/AST/graph hoặc revision IDs không xác minh được. Không migrate/stamp/CLI. |
| K4 — Schema inventory | Thu schema, regular/partitioned tables, columns, types, nullability/defaults, constraints/indexes; chưa so source metadata. | Chỉ COLLECTED. information_schema.columns có thể ẩn cột nếu role thiếu quyền. Partition child có thể vừa được đếm riêng vừa nằm trong parent count, nên tổng row counts có thể chồng lấp. |
| K5 — Synthetic-only | COUNT(*) theo từng bảng; chỉ GROUP BY `data_origin` nếu có đúng cột; không chọn row values. `age_source` và cột tương tự không phải proof. | Không bao giờ PASS. Non-synthetic/NULL/EMPTY/OTHER: FAIL/STOP. Thiếu `data_origin` hoặc owner proof: NOT RUN. Owner phải xác định delta 58 rows và tránh cộng trùng; kiểm synthetic-only cho toàn bộ DB, gồm cả 24 hàng lịch sử baseline, không chỉ delta. |
| K6 — CHECK definitions | Thu định nghĩa CHECK để đối chiếu riêng. | Chỉ COLLECTED; không diễn giải đúng/sai, không PASS. |
| K7 — Mypy | Owner-run baseline, command/version/checkout/cache/timeout được ghi. | Verdict thật mới là baseline; crash/timeout/no verdict = NOT RUN. |

### Quyền của script inventory và ngoại lệ đã biết

Về mặt quyền tối thiểu, script B chỉ cần `CONNECT`, `USAGE` trên schema được kiểm kê và `SELECT` trên các relation mà nó đọc/đếm, kể cả `public.alembic_version`; không cần `INSERT`, `UPDATE`, `DELETE`, `CREATE` hay DDL. Đây là phân tích quyền cần thiết, không phải xác nhận quyền hiện tại. Owner đã chọn user `postgres` và xác nhận user đó là superuser; vì vậy least-privilege không đạt. Draft 5 ghi nhận đây là ngoại lệ đã biết, không tạo role mới và không gọi superuser là quyền tối thiểu. K2 read-only, query allowlist, target identity, backup/restore và synthetic-only gates vẫn bắt buộc; không dùng superuser để vượt bất kỳ stop gate nào.

information_schema.columns chỉ hiện cột mà role được phép nhìn thấy; inventory có thể thiếu cột. Với partitioned tables, table cha có thể đếm hàng thuộc các partition trong khi partition con cũng xuất hiện và được đếm riêng. Không cộng tổng row counts thành số thực thể unique.

## Hard stop và exclusions

- Thiếu owner field, dump hash/restore disposition, target/container identity, synthetic-only proof, timeout/ceiling, K3 choice, hash script đã review hoặc Task Approval: không chạy.
- K1/K2 không đạt; identity không khớp owner attestation; non-synthetic origin; revision/hash/manifest không xác minh; cần query ghi/migration/cleanup hoặc đọc row values: STOP. Không đổi shell/connection để lách. User `postgres` là ngoại lệ superuser đã được owner chọn và phải được khai báo; ngoại lệ này không cho phép ghi hoặc bỏ qua gate.
- Safety check không có verdict = NOT RUN; dừng đúng cổng.
- Không ghi row data, child data, URL kết nối, mật khẩu, token, host/port/user thật hoặc đường dẫn tuyệt đối vào output/chat/Git.
- Không cleanup 58 synthetic rows; không đổi schema, DB, migration, source, test, policy hoặc route.
- Không Modal/provider; OWNER_MODAL_CALL_APPROVED=NO.
- Không stage/commit/push/merge.

## Lưu trữ và pin

Script r4 nằm tại `evidence/scripts/m2_s0_owner_run_readonly_20261107_r4.py`. Đây là vị trí lâu dài cho script đã review; owner-run chỉ đọc/chạy, không sửa. SHA-256 đã được owner chọn là `C28527CE531A4C1816B04BB4BA071B3F237CAD0AC7E95794A04CC86A2FABADB5`; phải rehash đúng path trước approval thực thi và độc lập review. Bất kỳ byte nào đổi sau pin làm approval vô hiệu và cần review/approval lại.

Inventory và logs chỉ lưu trong run directory mới dưới `.claude/handoff/logs/`, sau khi owner xác minh directory mới được ignore. Mypy cache location là `OWNER CHỌN` giữa hai đề xuất ở mục Mypy; không mặc định chọn ngoài repo hay trong `tmp/`. Sau đó chỉ hash, exit status và verdict đã lọc mới được ghi hồ sơ. Không commit runtime artifacts.

## Nguồn, baseline và trạng thái

- Draft 10 §8 liệt kê 9 revision files; owner đã chọn P1 và chấp thuận mở rộng read-only allowlist lên đúng 28 file ở manifest trên; approval thực thi phải rehash đủ 28 file.
- Phân tích source Alembic 1.19.1 chỉ được giữ trong phụ lục P2 không có hiệu lực thực thi; không có lệnh Alembic CLI nào được chạy trong approval này.
- Không xác minh DB identity/data, restore, synthetic-only proof, baseline mypy hoặc migration state.
- S0-doc đã đóng ở phạm vi tài liệu theo D-150; S0-owner-run chưa mở. S1a, S1b, S2, S3 và M3–M6 vẫn đóng. Không implementation approval.

## Điều kiện hiệu lực

- **Exit criteria:** script và approval được independent review; owner điền target/container/identity, backup/restore, synthetic-only proof (bao gồm 24 hàng baseline A2 và mọi bảng thiếu provenance), command ceilings, mypy choice/command/version/cache, và xác nhận P1 hoặc đổi K3 sang NOT RUN; hash script được pin; mọi attestation có bằng chứng; safety check NOT RUN không được tính PASS.
- **Stop gate:** pin/manifest/identity/output/hash lệch, thiếu verdict, current identity khác user `postgres`, quyền read-only không hoạt động hoặc cần ghi DB thì dừng và báo, giữ nguyên DB; không thử phương án khác. User `postgres` là ngoại lệ superuser đã được owner chấp thuận, không được nhầm thành least-privilege.
- **Validity:** bản này chỉ là DRAFT, không cấp quyền chạy S0-owner-run. Approval thực thi là mục riêng append-only được owner duyệt sau independent review. Mỗi pha sau cần Task Approval riêng.
- **Approval basis:** yêu cầu owner soạn bản sửa, hội thoại 2026-11-07; Draft 10 SHA-256 ở trên.
- **OWNER_MODAL_CALL_APPROVED=NO.**

## Draft 4 change inventory — đối chiếu Draft 3 → Draft 4

| Nhóm | Thay đổi trong Draft 4 |
|---|---|
| Revision identity | Tạo approval Draft 4 và chuyển input/command/storage reference sang script r4; Draft 1–3 và r1–r3 giữ nguyên lịch sử. |
| P3-1 — gate state | Chỉ gắn `STOPPED_AFTER_<gate>` cho gate đang NOT RUN / NOT_ATTEMPTED; giữ mọi PASS, FAIL, COLLECTED và NOT RUN đã có detail. Approval nêu rõ K2 fail và K1 mismatch. |
| P3-2 — P2 scope | K3 chỉ còn P1 static-AST hoặc NOT RUN. Bỏ P2 owner fields, attestation và executable Alembic command; giữ phân tích P2 trong phụ lục không có hiệu lực thực thi, kèm điều kiện cho approval riêng sau này. |
| P3-3 — K5 timeout | Bắt cả `QueryCanceled` và `LockNotAvailable`, ghi detail timeout cố định theo operation, dừng K5 và đánh dấu K6/K7 chưa thử là STOPPED_AFTER_K5 mà không ghi đè kết quả đã có; bucket origin không synthetic cũng làm K5 FAIL và dừng các gate sau. |
| P3-4 — wording | Ghi localhost không phân biệt hoa/thường theo `casefold()` và ghi thời hạn là 20000 ms / 3000 ms. |

**Đính chính tính đầy đủ của bảng lịch sử D3→D4 (bổ sung, không sửa ngầm mục cũ):** bảng trên còn thiếu các thay đổi được thực hiện khi soạn Draft 4: bỏ `owner-cli` khỏi choices của script; viết lại đoạn K3 NOT RUN; sửa hàng K3 trong bảng gate; xóa ba bullet nguồn Draft 3 ở cuối bản cũ và bỏ cụm “và trước Alembic” khỏi mục mypy; đổi heading “Draft 3 behavior updates…” thành “Draft 4 behavior updates…”. Ghi chú này bổ sung lịch sử, không thay đổi nội dung Draft 4.

## Draft 5 change inventory — đối chiếu Draft 4 → Draft 5

| Nhóm | Thay đổi trong Draft 5 |
|---|---|
| Owner directions và trạng thái | Ghi rõ quyết định owner: target `sketch2life`; K3 P1 và allowlist 28 revision; không nonlocal; đọc `.gitignore`; user `postgres` là superuser/ngoại lệ least-privilege; giữ 58 rows; S1a/S2 schema-only DB riêng; script r4 cùng provenance review; mypy command chưa được chọn. Không mở pha nào. |
| K5/A2 history | Bổ sung hash report/count maps, số lịch sử 117 bảng, 24→82 hàng, delta +58 theo bảng; phân biệt số lịch sử với hiện tại và yêu cầu chứng minh synthetic-only cho baseline 24 cùng bảng thiếu provenance. |
| K3 P1 | Ghi lựa chọn đã chốt, quy tắc PASS/FAIL/NOT RUN của r4, cách tính từ `down_revision` + `depends_on`, và 9 effective heads là suy luận tĩnh chứ không phải CLI result. |
| Safety/error behavior | Giới hạn P3-3 timeout handling vào K5; bổ sung `LockNotAvailable` ngoài K5, ba nhánh dừng sớm, trạng thái gate và mã thoát đúng r4; cấm cờ nonlocal theo owner decision. |
| Owner fields và quyền | Giữ checkbox chưa tick; các trường cần owner điền được để trống; ghi rõ `postgres` superuser không phải least-privilege; chuyển quyền tối thiểu script B vào phần hiệu lực, không để trong P2 appendix. |
| Command ceilings và mypy | Đề xuất script 1/5400 giây theo cận 4885 giây; mypy version 1/60, baseline 1/900; để command/version/package/timeout/cache ở `OWNER CHỌN`; nêu hai vị trí cache chưa chọn và đánh đổi giữa `tmp/` ignored trong repo với `$env:TEMP` ngoài repo. |
| Storage, source và exit criteria | Xác nhận owner đã cho phép đọc `.gitignore`; giữ logs phải kiểm ignore; pin lại r4 trước execution; cập nhật exit criteria cho P1, backup/restore, synthetic proof và mypy. Draft 5 vẫn DRAFT, không cấp quyền chạy. |

## Phụ lục tham khảo — P2 (KHÔNG nằm trong approval này; chỉ tham khảo Alembic current, không thực thi)

### P2 — Owner-run Alembic CLI, chỉ tài liệu tham khảo

CẢNH BÁO: toàn bộ mục này KHÔNG nằm trong approval này; không thực thi và không cấp quyền. Chỉ giữ làm tài liệu tham khảo cho một approval P2 riêng trong tương lai. P2 cần runner riêng có hash, independent review và Task Approval riêng. Source Alembic 1.19.1 cho thấy heads nạp revision modules; current chạy backend/alembic/env.py, cấu hình ứng dụng, import metadata của nhiều module sketch2life.* ngoài allowlist Draft 10 §8, tạo SQLAlchemy engine và mở connection. Không chạy upgrade, downgrade, stamp, revision hoặc migration test.

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

Không có command block hay lệnh Alembic thực thi trong phụ lục tham khảo này. Các quy tắc capture và whitelist dưới đây chỉ mô tả điều kiện cần thiết để một approval P2 riêng có thể được review sau này.

Mỗi lệnh chỉ chạy số lần và timeout do owner điền riêng. Filtered output và exit status có thể lưu tách trong các file alembic-heads.filtered.txt / alembic-current.filtered.txt; raw stdout/stderr không được lưu. Không dùng current --verbose vì code verbose in URL đã che password nhưng vẫn lộ thông tin đích.

#### Cấp cấu hình, target và quyền tối thiểu cho Alembic current (tham khảo P2)

P2 current dùng SKETCH2LIFE_DATABASE_URL trong process environment vì backend/alembic/env.py gọi get_core_database_settings().database_url. Không ghi URL vào command history, file, log, chat hoặc transcript; owner nhập trong shell riêng và chỉ giữ trong process memory. settings.py cho phép đọc backend/.env hoặc .env theo current working directory; process environment ưu tiên hơn file. Một approval P2 riêng trong tương lai cần owner attestation rằng cấu hình hiệu lực của child process nhắm cùng database đã qua K1 và không có nguồn cấu hình làm lệch target. K1 chỉ kiểm current_database() của script B, không ràng buộc connection mà Alembic current tự mở.

Theo đọc backend/alembic/env.py: import settings và các module metadata, lấy cấu hình database, tạo engine NullPool, mở connection, configure Alembic context rồi gọi context.run_migrations(). command.current truyền callback chỉ đọc version state và dont_mutate=True; runtime/migration.py dùng cờ này để không tự tạo alembic_version khi DB chưa có version rows. Đây là source inference, chưa chạy. env.py không bật transaction/session read-only; do đó current chạy NGOÀI K2/read-only safeguard của script B, dù không gọi upgrade/downgrade và không chạy migration functions. Không chạy current nếu không có cấu hình đích được owner attestation và role read-only.

Alembic current trong một approval P2 tương lai cần `CONNECT`, `USAGE` trên schema của `alembic_version` và `SELECT` trên version table; đọc catalog theo quyền PostgreSQL tương ứng. `env.py` không bật transaction/session read-only, nên không dựa vào cơ chế K2 của script B. Cần role read-only được xác minh riêng; user `postgres` đã được owner xác nhận là superuser và không đáp ứng yêu cầu least-privilege của một approval P2. Không chạy P2 trong Draft 5.



#### Điều kiện bắt buộc cho mọi approval P2 riêng trong tương lai

- Pin runner riêng bằng SHA-256, review độc lập runner và nội dung, rồi ghi Task Approval riêng trước khi owner chạy.
- Capture stdout/stderr đồng thời bằng Process API; khi timeout phải kill process, xác nhận process và mọi child process đã thoát, rồi mới thu dọn. Không ghi raw output.
- Chuẩn hóa CRLF và CR về LF trước khi parse; whitelist toàn bộ dòng và chỉ lưu output đã lọc.
- Mô tả thuật toán chiếu `get_all_current` theo đúng source Alembic đã pin: bắt đầu từ các version rows, mở rộng qua ancestors và `depends_on`, sau đó lọc các branch heads theo implementation; không so trực tiếp stdout `current` với version rows thô. Nếu thuật toán không được tái lập chính xác thì K3 = NOT RUN.
- Chỉ `heads` và `current` mới có thể được xem xét; cấm upgrade, downgrade, stamp, revision và migration tests trừ khi có approval khác.

#### Cảnh báo phương pháp 9 so với 12

Theo source Alembic 1.19.1 đã đọc và metadata 28 revision files, đây là suy luận chưa chạy: normal alembic heads chỉ xét down_revision có thể trả 12 heads, thêm 20261101_be1_age_0001, 20261015_ai_0001 và 20261102_pv_0001; P1 kết hợp down_revision với depends_on nên có thể trả 9 effective heads. Hai số dùng phương pháp khác nhau, không tự chứng minh DB lệch. Đây không phải kết quả đã chạy Alembic và không chấp nhận K3.


> Draft 4 là bản DRAFT chờ independent review và quyết định owner; chưa được duyệt và không cho phép kết nối DB hay chạy lệnh.

