# Sổ tiến độ — FEAT-064 pilot T2B đến T12

- Cập nhật: 2026-11-01
- Chế độ: TREO KHÔNG COMMIT
- Phạm vi lượt này: G2-G6, tiếp tục từ T4 đang dở; G0-G1 là lịch sử đã hoàn tất.
- Trạng thái nhóm: G2 XONG-CHƯA REVIEW; G3/G4 XONG-CHƯA REVIEW cho blocker disposition (implementation còn BLOCKED); G5 XONG-CHƯA REVIEW cho hợp đồng tài liệu; G6 T12 partial, chưa đạt full acceptance.
- Trạng thái review độc lập: chưa review; chỉ owner đặt REVIEWED.

## BÁO CÁO CUỐI — lượt G2-G6 (2026-11-01)

- **Trạng thái tổng: TẠM DỪNG; READY_FOR_T13: CHƯA.** G2 và G5 đã hoàn tất trong phạm vi được duyệt; G3/G4 đóng hồ sơ blocker nhưng các phần triển khai liên quan vẫn BLOCKED; T12 đã chạy partial trên PostgreSQL thật nhưng còn lỗi hồi quy và thiếu ClamAV. Không có Modal/GPU/provider/live claim.
- Nhánh `feature/feat063-be-foundation`; HEAD giữ nguyên `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`; không stage, commit, push, reset, checkout, clean, hay stash.

### Bảng task × lớp

Ký hiệu: `XCR` = XONG-CHƯA REVIEW; `B` = BLOCKED; `NR` = NOT RUN/NOT DONE; `—` = không thuộc task; `UI-D` = L6 DEFERRED-BY-OWNER.

| Task | Trạng thái | L1 contracts/domain | L2 application | L3 persistence | L4 adapter | L5 HTTP | L6 UI | L7 integration |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T3 canvas profile | XCR | XCR | — | không đổi | — | XCR | UI-D | XCR trên PG |
| T2 Child reconnect | XCR | XCR | — | không đổi | — | XCR | UI-D | XCR trên PG |
| T9 Teacher pilot-profile list (G1) | XCR | XCR | — | không đổi | — | XCR | UI-D | XCR trên PG |
| T4 authoritative source export | XCR | XCR | — | — | — | XCR | UI-D | XCR trên PG |
| T5 private render/admission | XCR | XCR | — | không đổi | XCR | XCR | UI-D | XCR trên PG; BE2 consumption B |
| T6 invocation guard | B | B | B | NR | B | NR | UI-D | NR |
| T7a durable assistance state | B | NR | B | B | NR | NR | UI-D | B |
| T7b OwnerFence/UoW | B | B | B | B | B | NR | UI-D | B |
| T7c ledger/witness | B | B | B | B | B | NR | UI-D | B |
| T2C BE1 facts adapter | B | hiện có chưa đủ scope | chưa đủ | NR | B | NR | UI-D | B |
| T8 guarded worker | B | B | B | B | B | NR | UI-D | B |
| T9 gateway/status remainder | B | B | B | B | B | B | UI-D | B |
| T10 Child handoff | XCR cho hợp đồng | bản nháp; source binding B | B | B | B | route NR | UI-D | B |
| T11 Teacher pending | XCR cho hợp đồng | route B | B | B | B | route NR | UI-D | B |
| T12 PostgreSQL partial acceptance | partial, XCR chưa review | regressions có lỗi | regressions có lỗi | migration round-trip XCR | BE1 pilot XCR; ClamAV dependency lỗi | HTTP tests có lỗi | UI-D | PG chạy partial, chưa đạt B4a/B5 |

### Test và kiểm chứng thực tế

- **G1 review-fixes history:** CPU/offline 294 passed/4 skipped; contract trừ `test_live_image_demo_api.py` 1,381 passed; full-unit snapshot 6,195 passed/9 failed/24 skipped/12 errors; isolated PostgreSQL synthetic-pilot 48 passed. 12 collection errors gắn với optional `imageio`/`imageio_ffmpeg`; không cài package.
- **G2:** CPU/offline 334 passed/4 skipped; contract 1,381 passed; T4/T5 unit set 13 passed; synthetic-pilot PG 56 passed ở G2. Lần G6 retest cuối cũng 56 passed/70.77s.
- **G3/G4:** implementation tests NOT RUN vì tasks BLOCKED trước code; không suy ra số đỏ.
- **G5:** UI/npm/visual AC20 NOT RUN theo owner; chỉ hoàn tất hợp đồng T10/T11.
- **G6/T12 R0:** CPU/offline 508 passed/4 skipped; database loopback PostgreSQL 17.11, tên chứa `be1_acceptance`; 99 bảng/10 schema repo; 10 Alembic version rows khớp các heads. R2 `alembic upgrade heads` thành công, không có revision mới cần áp.
- **T12 PostgreSQL:** `test_be1_postgres_api.py` (bỏ global retention worker) 1 passed/2 failed/1 deselected: catalog assertion mong 50 route nhưng nhận 51; `test_room_code_start_revocation_stage_and_early_outcome_are_durable` mong 200 nhưng guard trả 409 `CONSENT_NOT_EFFECTIVE`. Không sửa source/test cũ.
- `test_be1_age_provenance_postgres.py`: 1 passed. `lesson_library/test_lesson_library_api.py`: 5 passed/1 failed; `test_teacher_uploads_and_reviews_a_synthetic_pdf_through_http` nhận 503 `DEPENDENCY_UNAVAILABLE` vì ClamAV local ở loopback cổng 3310 không chạy. Ca `test_parent_group_accept_replays_legacy_receipt_without_repeating_effects` nằm trong 5 ca xanh.
- `test_be1_synthetic_pilot_postgres.py`: **56 passed/70.77s** ở lần chạy cuối. So sánh count trước/sau trên 99 bảng: không có delta; managed profiles=0, synthetic profiles=0, proofs=0.
- R4: downgrade `be1_core@-1` đã hạ `20261101_be1_age_0001` về `20261031_be1_se_0001`; upgrade `be1_core@head` khôi phục revision, `age_revision`/`age_source`, và toàn bộ 10 version rows trở lại đúng như trước. Preflight profile/proof bằng 0; không DROP/TRUNCATE.
- Kiểm cuối sau khi sửa test mới: Ruff check đạt; Ruff format báo 1 file already formatted; mypy strict 1 file, no issues; `validate_harness.py` HARNESS_VALID; `validate_repository_security.py` REPOSITORY_SECURITY_VALID (6,032 file); `validate_architecture.py` ARCHITECTURE_VALID; `git diff --check` sạch; byte scan test/report/ledger UTF-8, LF, không BOM/trailing whitespace.

### BLOCKED, NOT RUN và việc owner cần làm

- T6 cần owner chốt deadline tổng HTTP, completion margin/cold-start, phản hồi đến muộn và immutable invocation identity/guard handshake.
- T7a cần một schema/migration owner duy nhất, schema/parent/revision, durable subset và writer; T7b cần người đồng ký `OwnerFenceV1`, owner UoW/methods; T7c cần quyết định manifest/witness và semantics khi restore.
- T2C cần nguồn facts BE1 có scope organization/class/session/canvas/group/audience/purpose và snapshot nhất quán, cùng nguồn revision age/region policy. T8 phụ thuộc T6/T7/T2C và còn cổng digest contract BE2 cần approval riêng. T9 gateway/status cần route/DTO, authorization/error mapping và dependency trên được chốt.
- T12 chưa đạt full acceptance: xử lý sai khác route count; chủ sản phẩm/BE1 xác nhận đường consent mong muốn thay vì nới guard; chạy ClamAV local để kiểm lại upload/review B5; AI Jobs tests tạo database thứ hai NOT RUN vì nằm ngoài boundary một DB.
- UI AC20, npm/UI, Modal/GPU/provider/Vision claim, dữ liệu thật của trẻ, B4b/B6/B7 và live T13 đều NOT RUN/ngoài phạm vi. `test_live_image_demo_api.py` không chạy.
- **Việc owner cần làm trước commit:** rà toàn bộ diff/snapshot; yêu cầu review độc lập; quyết blocker T6/T7/T2C/T8/T9; xử lý các lỗi T12 trong task được duyệt riêng; sau này kiểm AC20 với UI thật. Không coi `PLAN_REVIEW_PASS`/validator xanh là approval production.
- File ngoài allowlist mới phát hiện: không có. Các thay đổi owner-protected/local đã thấy vẫn giữ nguyên, không stage; nguồn kết nối PostgreSQL local ignore không nằm trong snapshot/Git.
- Protected hashes cuối: SOURCE_REGISTER `0B43E4BA`; FEAT-063 CONTEXT `E7C8143A`; FEAT-063 STATUS `F1ADB793`; REMAINING_AI `8BBFD0ED`; REV36_DELTA `B61B0607`; VIDEO_FLOW `93374E96`; S1_DECISION_CARD `4D95D303`.
- Snapshots: G1R `.claude/handoff/snapshots/G1R_20261101T143559/`; G2 `.claude/handoff/snapshots/G2_20261101T154756/`; G3 `.claude/handoff/snapshots/G3_20261101T160006/`; G4 `.claude/handoff/snapshots/G4_20261101T161324/`; G5 `.claude/handoff/snapshots/G5_20261101T161840/`; G6 `.claude/handoff/snapshots/G6_20261101T164500/`.

## Cập nhật mới nhất — G1 review-fixes (R0–R6)

- Trạng thái: **XONG-CHƯA REVIEW**. Chỉ hoàn tất sửa F1–F4 và phần được phép của F5/F6; G2 trở đi chưa làm.
- HEAD giữ nguyên: `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`; plan G1 review-fixes SHA-256 `90424CEFDA794A38B21BA2818462BFEAE862C65526B37FC08B0F97997F313E95`.
- F1–F4: LÀM; catalog test, hostile payload, nullable reconnect `profile_version`, và fingerprint session cũ đã được sửa/kiểm. F5: LÀM; fixture giới hạn URL tới DB acceptance loopback, đồng thời ghi rõ socket patch không bảo vệ libpq/psycopg. F6: LÀM MỘT PHẦN; reconnect/Teacher regression đã chạy, nhưng positive legal-effective reconnect là NOT DONE vì DB hiện chỉ cho trạng thái consent `pending`/`revoked`.
- R0/R4 số mới: CPU/offline `294 passed, 4 skipped` (R0 lịch sử `267/4`); full contract trừ `test_live_image_demo_api.py`: `1,381 passed`; full unit: `6,195 passed, 9 failed, 24 skipped, 12 errors`; PostgreSQL synthetic-pilot: `48 passed` (R0 lịch sử `31 passed`). HEAD archive cùng bộ hiện hành: CPU/offline `227/4`, contract `1,378 passed, 1 failed`, unit `6,112 passed, 27 failed, 24 skipped, 12 errors`, PG module cũ hơn `4 passed`.
- Unit failures/errors được phân loại trong `evidence/G1_REVIEW_FIXES_REPORT_20261101.md`: 12 collection errors vì thiếu optional `imageio`/`imageio_ffmpeg`; 7 test failures cùng có ở HEAD; 2 failures mới do fixture scratch FEAT-018 read-only. Không sửa/xóa fixtures; scratch tạm mới chạy evaluation thành công. Không chạy migration, Modal/GPU/provider, UI hoặc `test_live_image_demo_api.py`.
- F4 prompt ghi sáu khóa fingerprint lịch sử; đọc source tại HEAD cho thấy công thức thật có năm khóa. Regression test pin năm khóa thực tế; đây là sai khác nguồn được ghi nhận, không thay đổi pinned plan.
- Câu hỏi owner: xử lý nét hai điểm trùng nhau; export 1024/render params thuộc profile v1 hay T4/T5; checkpoint dict tự do phải không được dùng làm nguồn T4. F6 legal-effective path cũng cần quyết định/schema được duyệt riêng.
- Báo cáo chi tiết: `evidence/G1_REVIEW_FIXES_REPORT_20261101.md`. Snapshot cuối lượt: `.claude/handoff/snapshots/G1R_20261101T143559/` (local, ignored; 14 file: 11 sửa, 3 mới). Snapshot `G1R_20261101T143252` được giữ nguyên như bản trung gian.
- Kiểm cuối: HARNESS_VALID; REPOSITORY_SECURITY_VALID (6,012 publishable files); ARCHITECTURE_VALID; `git diff --check` sạch. Ruff lint/format sạch; mypy có 0 lỗi mới so với HEAD.

## Baseline G0

- Nhánh: feature/feat063-be-foundation
- HEAD đầu G0: 1e93bc3f3ac645cf4baecbbc09c73afe48719c92
- origin/feature/feat063-be-foundation...HEAD: 0 1
- 9f337aff là tổ tiên của HEAD: có
- T2B rework migration được theo dõi trong HEAD: có
- Không có merge/rebase/cherry-pick đang diễn ra.
- git status --porcelain lúc bắt đầu:
  - M docs/context/SOURCE_REGISTER.md
  - M features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md
  - M features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md
- Ba thay đổi trên là baseline local của owner, không thuộc task này.

### Hash bảy file local được bảo vệ

| File | SHA-256 đầu |
|---|---|
| docs/context/SOURCE_REGISTER.md | 0B43E4BA |
| features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md | E7C8143A |
| features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md | F1ADB793 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/REMAINING_AI_MODEL_RECOMMENDATIONS_20261030.md | 8BBFD0ED |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/REV36_DELTA_REVIEW_AND_S1_PREPARATION_20261030.md | B61B0607 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/notes/VIDEO_FLOW_COMPARISON_20261030.md | 93374E96 |
| features/FEAT-063-system-architecture-rearchitecture/plan/S1_DECISION_CARD_20261030.md | 4D95D303 |

### G0 kiểm tra thực tế

- Baseline test, chạy từ backend với PYTHONPATH=src và basetemp ngoài repo; gồm 5 file CI và 2 file T1:
  - tests/contract/test_app_composition.py
  - tests/contract/test_session_http_api.py
  - tests/unit/test_classroom_stage_policy.py
  - tests/unit/test_session_lock_pool.py
  - tests/integration/test_be1_postgres_api.py
  - tests/unit/test_synthetic_eligibility.py
  - tests/contract/test_be1_synthetic_pilot.py
  - Kết quả: 227 passed, 4 skipped, 21.18s.
  - tests/contract/test_live_image_demo_api.py không chạy theo phạm vi baseline.
- Alembic heads: 10. 20261015_ai_0001 (ai_jobs); 20261017_lc_0001 (learning_content); 20261018_ap_0009 (ai_policy); 20261018_kv_0001 (knowledge_video); 20261018_vr_0001 (video_review); 20261019_ae_0001 (activity_execution); 20261019_pa_0001 (preset_automation); 20261019_vf_0001 (video_failure); 20261028_ll_0001 (lesson_library); 20261101_be1_age_0001 (be1_core).
- Python backend: Pillow 12.3.0; NumPy 2.5.2.
- apps/child-ui/node_modules: absent; apps/teacher-ui/node_modules: absent (bình thường, UI bị owner hoãn).
- PostgreSQL: đọc-only, host loopback và tên DB khớp be1_acceptance; server 17.11; 99 bảng người dùng trong 10 schema. Schema thực tế: activity_execution, ai_jobs, ai_policy, knowledge_video, learning_content, lesson, preset_automation, public, video_failure, video_review. So với khai báo CREATE SCHEMA/SCHEMA/CreateSchema trong backend/alembic/versions: không có schema lạ. Không chạy Alembic, không ghi DB.
- Kết quả PG chỉ xác nhận kết nối/nhận diện schema; chưa chạy migration hay test PG.

### Bảng nhóm G0-G7

| Nhóm | Phạm vi | Trạng thái |
|---|---|---|
| G0 | Baseline, môi trường, bảng đường dẫn, snapshot | XONG-CHƯA REVIEW |
| G1 | T3 server/profile; Child reconnect; Teacher pilot-profiles; hợp đồng UI | XONG-CHƯA REVIEW |
| G2 | T4 export; T5 render/artifact/admission | XONG-CHƯA REVIEW; BE2 port mapping BLOCKED in G4 |
| G3 | T6 guard; T7a/T7b/T7c persistence, fence, witness | XONG-CHƯA REVIEW as blocker closeout; all four BLOCKED before implementation |
| G4 | T2C adapters; T8 worker; phần gateway/status còn lại của T9 | CHƯA LÀM |
| G5 | T10/T11 hợp đồng UI, không code UI | DEFERRED-BY-OWNER |
| G6 | T12 CPU/PG integration/recovery tests | CHƯA LÀM |
| G7 | T13/B8/T14 tài liệu và handoff; không live call | CHƯA LÀM |

## Bảng đường dẫn theo task và cổng đã biết

Phạm vi mỗi task cần plan riêng, hash riêng và mục approval riêng. Danh sách dưới đây là hàng T0 manifest; B5.1 cho phép đường dẫn bổ sung chỉ trong các thư mục nêu rõ, từng file phải được kê và pin trong plan/approval. Không suy diễn allowlist ngoài các đường dẫn này.

| Task | Đường dẫn/hàng nguồn | Cổng hoặc phần đã biết |
|---|---|---|
| T1 | O02, O03, O07; các file T1 đã có trong HEAD | Có trong baseline; không sửa lại trong G0. |
| T2 | O02 be1_runtime.py; O03 be1_registry.py, be1_sessions.py; O08/O10 domain, ports và contracts đã nêu trong manifest | Reconnect dùng O02/O05 theo goal; BE1→BE2 adapters nếu cần thuộc infrastructure/assistance theo B5.1. |
| T3 | O01 contracts/schemas/be1_runtime.py; O03 registry/sessions; O05 be1_canvas.py; O17 apps/child-ui paths | L6 và mọi apps/child-ui code DEFERRED-BY-OWNER. DRAFT1 có core_foundation.py là đường dẫn có điều kiện; chỉ dùng nếu task plan pin và không cần mở rộng persistence. Cần kiểm tra khả năng lưu profile id trong accepted operation; nếu cần file persistence/migration ngoài allowlist, T3 phần đó BLOCKED. |
| T4 | O01 contracts/schemas/be1_runtime.py; O05 be1_canvas.py | Nếu export cần file mới ngoài đường dẫn T0/B5.1, task phải BLOCKED trước khi sửa. |
| T5 | O06 be1_artifacts.py; B5.1 backend/src/sketch2life/infrastructure/canvas_render/** | Pillow đã có; không tự cài thêm gói. |
| T6 | O08-O12, O14, O15 theo từng repo_path trong T0 manifest | Phụ thuộc hợp đồng/context; file mới cần plan/approval. |
| T7a | O07/O15 và O16 NEEDS_OWNER; B5.1 assistance/**, vision_analysis/**, backend/alembic/versions/*.py | Migration mới cần một parent, downgrade, backfill và PG; chỉ làm khi task plan pin đủ path. |
| T7b | O08/O15 và O16 NEEDS_OWNER; B5.1 assistance/**, vision_analysis/** | Phụ thuộc T7a và hợp đồng fence/UoW; file ngoài các thư mục này BLOCKED. |
| T7c | O16 NEEDS_OWNER; B5.1 assistance/**, vision_analysis/**, backend/alembic/versions/*.py | Run manifest/witness cần task plan ghi chính xác path và kiểm Windows/PG. |
| T8 | O08-O12, O14; B5.1 application/services/{assistance,vision_analysis}.py, infrastructure/routers theo quy tắc B5.1 | Phụ thuộc T2/T5/T6/T7a-c. Thay đổi ai_jobs ports/schemas/sql ngoài hướng thu hẹp thì BLOCKED. |
| T9 | O02/O10/O13; B5.1 application/services/** và routers/**; đăng ký chỉ qua điểm router hiện có | G1 chỉ làm route Teacher pilot-profiles; gateway/status đầy đủ còn ở G4. |
| T10 | O17 Child UI | DEFERRED-BY-OWNER; chỉ hợp đồng UI, không code/npm. |
| T11 | O18 Teacher UI | DEFERRED-BY-OWNER; chỉ hợp đồng UI, không code/npm. |
| T12 | Tests theo từng task + backend/tests/integration/** khi được pin; DB chỉ local loopback *be1_acceptance | Chưa chạy ở G0; cần các nhóm trước và approval scope. |
| T13 | Tài liệu/evidence בלבד | Live Modal/GPU/provider không nằm trong quyền; chỉ plan khi G7. |
| T14 | Tài liệu/evidence/status report | Sau T13 hoặc ghi rõ gate chưa chạy. |

## Task ledger và lớp

| Task/slice | Nhóm | Lớp | Trạng thái / ghi chú |
|---|---|---|---|
| T0 | G0 | L1-L7 inventory only | XONG-CHƯA REVIEW; baseline pins đã đọc. |
| T1 | prerequisite | L1/L3/L5 | Có trong HEAD và baseline xanh; không sửa trong lượt này; XONG-CHƯA REVIEW. |
| T3 server/profile | G1 | L1, L5; L6 deferred | XONG-CHƯA REVIEW; report evidence/T3_CANVAS_PROFILE_IMPLEMENTATION_REPORT_20261101.md; plan SHA-256 347CC6C7… |
| T2 Child reconnect slice | G1 | L1/L2 reused; L5 | XONG-CHƯA REVIEW; report evidence/T2_CHILD_CANVAS_RECONNECT_REPORT_20261101.md; plan SHA-256 4DFD74DD… |
| T9 Teacher pilot-profiles slice | G1 | L1, L5 | XONG-CHƯA REVIEW; report evidence/T9_TEACHER_PILOT_PROFILE_ROUTE_REPORT_20261101.md; revised plan SHA-256 D9BD291A… |
| T3 Child canvas UI | G1 | L6 | DEFERRED-BY-OWNER; sẽ ghi HỢP ĐỒNG CHO UI. |
| T4 authoritative export | G2 | L1/L5/L7 | XONG-CHƯA REVIEW; report `evidence/T4_AUTHORITATIVE_CANVAS_EXPORT_REPORT_20261101.md`; plan SHA-256 `B009F3F6…`. |
| T5 render/admission/internal handoff | G2 | L1/L4/L5/L7 | XONG-CHƯA REVIEW for private render + actual admission + internal handoff; BE2 port consumption BLOCKED in G4. |
| T6-T14 | G3-G7 | theo PLAN.md | CHƯA LÀM hoặc DEFERRED-BY-OWNER theo bảng nhóm; chưa thực hiện. |

## Kết quả G1

### T3 server/profile — cập nhật sau task

- Trạng thái: XONG-CHƯA REVIEW; L1 domain/schema và L5 session/append hoàn tất. L3 không đổi; L6 Child UI DEFERRED-BY-OWNER.
- Plan: plan/T3_BE1_CANVAS_PROFILE_IMPLEMENTATION_PLAN_20261101.md; SHA-256 347CC6C7D8B7DC0877E933A1AB13D68629F6BE849B7AAA3E07E3D1683ABE347A.
- Files: domain/core_foundation.py, contracts/schemas/be1_runtime.py, routers/be1_sessions.py, routers/be1_canvas.py, unit test test_canvas_operation_profile.py, shared PostgreSQL test.
- Tests: 39 profile unit tests passed; combined final CPU/offline set 267 passed, 4 skipped; final shared PostgreSQL module 31 passed. The original T3 red-phase count was not retained in the current ledger/output record.
- PostgreSQL result is from the shared G1 module; no migration was run.
- Evidence: evidence/T3_CANVAS_PROFILE_IMPLEMENTATION_REPORT_20261101.md.
- Ruff, mypy, validators, and snapshot are recorded in “G1 closeout” below.

### T2 Child reconnect — cập nhật sau task

- Trạng thái: XONG-CHƯA REVIEW; reused typed eligibility/status-read behavior and updated the L5 reconnect response/route. No L3 or migration change.
- Plan: plan/T2_CHILD_CANVAS_RECONNECT_IMPLEMENTATION_PLAN_20261101.md; SHA-256 4DFD74DD41B433ED85C9BA3C6FDA4946A4E1B8304E438A136FDD09A8D8657E6B.
- Files: interfaces/http/be1_runtime.py (documentation only), contracts/schemas/be1_runtime.py, routers/be1_canvas.py, contract test, shared PostgreSQL test.
- Test-first observations: one contract failure and three reconnect PostgreSQL failures before the route used the status-read path.
- Tests: combined final CPU/offline set 267 passed, 4 skipped; final shared PostgreSQL module 31 passed. An intermediate expired-proof test setup violated the existing proof interval CHECK; the fixture was corrected to preserve issued_at < expires_at while making the proof expired, and the focused case passed.
- Evidence: evidence/T2_CHILD_CANVAS_RECONNECT_REPORT_20261101.md.
- Ruff, mypy, validators, and snapshot are recorded in “G1 closeout” below.

### T9 Teacher session-scoped pilot profiles — cập nhật sau task

- Trạng thái: XONG-CHƯA REVIEW; L1 response schema and L5 route complete. No L3, migration, or composition wiring change.
- Plan: plan/T9_TEACHER_PILOT_PROFILE_ROUTE_IMPLEMENTATION_PLAN_20261101.md; revised SHA-256 D9BD291A35F7C97E07632C7953D2A58469A7D6FE9F52F77D7260B8117FD941BC.
- Approval: append-only T9 route-surface correction in approvals/TASK_APPROVAL.md pins the revised plan and permits only the exact new route in test_app_composition.py.
- Tests: red phase had one response-schema contract failure and the T9 PostgreSQL filter had 13 failures/1 pass; final combined CPU/offline set 267 passed, 4 skipped; final shared PostgreSQL module 31 passed.
- Evidence: evidence/T9_TEACHER_PILOT_PROFILE_ROUTE_REPORT_20261101.md.
- Ruff, mypy, validators, and snapshot are recorded in “G1 closeout” below.

### G1 closeout (số lịch sử trước review-fixes)

- Status: XONG-CHƯA REVIEW; independent review has not been performed. This closes G1 only; it does not mark G2-G7 complete.
- Completed scope: T3 server-side canvas profile; T2 Child reconnect/status read; T9 Teacher session-scoped pilot profile route. Child/Teacher UI, L6, visual AC20, and `tests/contract/test_live_image_demo_api.py` were not run.
- Final tests: combined CPU/offline suite 267 passed, 4 skipped; isolated PostgreSQL synthetic-pilot module 31 passed. The four offline skips are DB-environment-dependent checks as previously recorded. No Alembic/migration, Modal, GPU, or provider call ran.
- Ruff: lint passed for 10 Python files; format passed for 9. The existing formatter suggestion in `test_app_composition.py` was left untouched because it is outside the approved one-line route change.
- Mypy: strict L1 check passed on 3 files; the full scope has the same 5 router/Result.rowcount diagnostics as the HEAD-source comparison, with no new diagnostics.
- Final validators: `python tools/validate_harness.py` -> HARNESS_VALID; `python tools/validate_repository_security.py` -> REPOSITORY_SECURITY_VALID (6010 publishable files scanned); `python tools/validate_architecture.py` -> ARCHITECTURE_VALID; `git diff --check` -> clean.
- G1 snapshot: `.claude/handoff/snapshots/G1_20261101T115654/` (local, ignored; file list, SHA-256 manifest, copies, and tracked-file diff).
- Data boundary: synthetic fixtures only; PostgreSQL loopback. No real child data was used.
- Environment incident: an earlier PostgreSQL setup initialized `Settings` with default dotenv loading unintentionally. No environment values were copied into repository/evidence. Review that local command output; rotate credentials if any real credential appeared. The final fixture disables dotenv loading.
- Next: obtain independent G1 review and resolve required decisions/approvals before G2. Do not continue to G2 in this task.

### G1 review-fix closeout (R0–R6)

- F1–F5: LÀM. F6: LÀM MỘT PHẦN; positive reconnect với legal-effective consent là NOT DONE do constraint hiện hữu chỉ cho `pending` và `revoked`, không bypass schema/guard.
- Test-first: F1 catalog mismatch 1 đỏ; F2 hai ca unhashable gây exception; F3 một contract schema đỏ và ba reconnect PG failures đã ghi trong T2; F4 một fingerprint regression đỏ. Các regression được sửa đều xanh ở bộ focused hiện hành (132 passed). F5/F6 không có red count riêng được lưu trước khi implementation; kết quả hiện tại của module PG là 48 passed.
- R4 hiện tại: CPU/offline 294 passed/4 skipped; contract (trừ live-image) 1,381 passed; unit 6,195 passed/9 failed/24 skipped/12 errors; PG synthetic-pilot 48 passed. So sánh HEAD archive và nguyên nhân test suite đỏ nằm trong báo cáo G1 review-fixes.
- Ruff: lint `All checks passed!`; format `7 files already formatted`. Strict mypy so 6 source file với HEAD: 5 diagnostics hiện tại, 7 ở HEAD, 0 mới, 2 được giải quyết. OpenAPI generated source không đổi.
- Validators cuối: `python tools/validate_harness.py` → HARNESS_VALID; `python tools/validate_repository_security.py` → REPOSITORY_SECURITY_VALID (6,012 publishable files); `python tools/validate_architecture.py` → ARCHITECTURE_VALID; `git diff --check` sạch. Quét whitespace/CR/BOM và kiểm hash 7 file local hoàn tất.
- Giới hạn đã ghi: không chạy migration/Alembic, Modal/GPU/provider, UI, AC20, `test_live_image_demo_api.py`, hay G2+. Một lần setup PostgreSQL trước đó đã khởi tạo `Settings` với dotenv mặc định; không giá trị nào được sao chép vào file. Review-fixes dùng `_env_file=None`, URL DB không in.
- Snapshot R6 local/ignored: `.claude/handoff/snapshots/G1R_20261101T143559/`; chứa danh sách, SHA-256, bản sao và delta so với snapshot G1 trước đó. Bản trung gian `G1R_20261101T143252` được giữ nguyên. Không commit.

## Snapshot

- G0: .claude/handoff/snapshots/G0_20261101T111404/
- G1: .claude/handoff/snapshots/G1_20261101T115654/ (local, ignored)

## G2 — T4 authoritative canvas source export (2026-11-01)

- Status: **XONG-CHƯA REVIEW**. T4 and the approved T5 scope are closed. BE2 port compatibility remains BLOCKED for G4; this does not make T5’s private render/admission/internal handoff incomplete. G2 snapshot: `.claude/handoff/snapshots/G2_20261101T154756/`.
- Approved plan: `plan/T4_AUTHORITATIVE_CANVAS_EXPORT_PLAN_20261101.md`; SHA-256 `B009F3F6D01DA5E39269E1D03085447042A64DE2F60804880764D0B7B94C41B0`.
- Evidence: `evidence/T4_AUTHORITATIVE_CANVAS_EXPORT_REPORT_20261101.md`; SHA-256 `F1A0B836D3B159AB40059D4A5ADCD6A6DFDD3B37B5325B51700D6E75E4204401`.
- Implementation is limited to typed `CanvasSourceExportV1` and the internal BE1 builder. The builder reads session profile, aggregate revision, all operations for the canvas, and checkpoint existence in one SQL statement; rejects empty/incomplete/mixed-epoch/unprofiled/malformed/checkpoint history generically; and returns no partial source. No public route, artifact, renderer, admission, claim, schema, migration, UI, or provider change.
- Test-first history: **không còn số đỏ** đủ tin cậy sau khi lượt thực hiện bị ngắt; no initial red count is claimed.
- Actual checks: T4 unit 4 passed; T4-selected PostgreSQL 5 passed; full isolated PostgreSQL synthetic-pilot module 53 passed in 58.88s; CPU/offline set including T4 unit 298 passed / 4 skipped; contract suite excluding `test_live_image_demo_api.py` 1,381 passed; `test_feat018_p2_t5_evaluation.py` 25 passed. The two FEAT-018 evaluation regressions are green after the owner removed the prior scratch directory.
- Ruff check: all checks passed; Ruff format: 4 files already formatted. Strict mypy current and G1R shadow both have the same 3 pre-existing `be1_canvas.py` diagnostics; zero new T4 diagnostics. Repository validators: HARNESS_VALID, REPOSITORY_SECURITY_VALID (6,014 files scanned), ARCHITECTURE_VALID; `git diff --check` clean; T4 unit UTF-8/LF/no-BOM check clean.
- `test_live_image_demo_api.py`, full unit suite, migrations/Alembic, Modal/GPU/provider, UI, and live claim were not run. The existing 12 full-unit collection errors tied to missing `imageio`/`imageio_ffmpeg` remain an environment baseline; no packages were installed.
- Owner render decision is routed to T5: versioned 1024×1024 RGB white export; stroke width profile ratio × 1024 rounded using decimal `ROUND_HALF_UP` (13/23/36 px for current tokens); rounded caps; one-point input draws no dot; coincident two-point strokes remain accepted. `export_spec_version` and `renderer_version` must bind the rendered-image source hash. `CanvasOperationProfileV1` remains unchanged; checkpoints are not rendering input.
- Vision-claim digest handoff is deferred to G4 and requires its own approval. If G4 lacks an approved path, mark BLOCKED and ask the owner.
- Protected local hashes after T4 (prefixes): SOURCE_REGISTER `0B43E4BA`; FEAT-063 CONTEXT `E7C8143A`; FEAT-063 STATUS `F1ADB793`; REMAINING_AI `8BBFD0ED`; REV36_DELTA `B61B0607`; VIDEO_FLOW `93374E96`; S1_DECISION_CARD `4D95D303`.
- No stage, commit, or push occurred. T4's report and this ledger retain its standalone closeout; the approved T5 closeout follows below.

### T5 — canvas render, private artifact, and admission (2026-11-01)

- Status: **XONG-CHƯA REVIEW** for the approved T5 boundary: render validated T4 operations, persist an opaque PNG and receipt, run actual FEAT-018/PyAV admission over read-back artifact bytes, and return an internal `CanvasRenderHandoffV1` after metadata commit. The image and receipt remain private derived artifacts; no public route was added.
- Plan: `plan/T5_CANVAS_RENDER_ARTIFACT_PLAN_20261101.md`; SHA-256 `6BCC29D243B4D86624D34DA38640E67AA7A988E6ABE290B3C348BA8EF45DB46B`.
- Approval: appended T5 entry in `approvals/TASK_APPROVAL.md`; the pinned plan hash matches. No separate approval was added for a Vision-claim digest.
- Evidence: `evidence/T5_CANVAS_RENDER_ARTIFACT_REPORT_20261101.md`; SHA-256 `C0D324E80CA3E25CAE30EE5FFF0824547382B3E391E6063E118F6BB4B1A45B73`.
- Files touched by T5: `backend/src/sketch2life/infrastructure/canvas_render/__init__.py` (SHA prefix `C98F4E11`), `renderer.py` (`058CE472`), `backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py` (`E022249C`), `backend/tests/unit/test_canvas_source_render.py` (`C80503AC`), and shared `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` (`C159CB4D`). Plan, approval, report, and this ledger are also T5 paths.
- Test history: six initial renderer cases failed before the renderer package existed; final T4-export + renderer unit set was 13 passed. First PG attempt had two product failures because the renderer rejected T4's server-bound profile id; the renderer was fixed to verify that id and remove only the metadata before stroke validation. One following failure was a test expectation mismatch for image source provenance and was corrected. Final focused T5 cases: 3 passed; full synthetic-pilot PostgreSQL module: 56 passed in 60.24s.
- Final CPU/offline set: 334 passed, 4 skipped in 30.34s, above the recorded T4 set (298 passed, 4 skipped). Contract suite excluding `test_live_image_demo_api.py`: 1,381 passed in 72.01s.
- Ruff: check passed on five T5 Python paths; format check reported five files already formatted. Strict mypy on `canvas_render/renderer.py`: no issues in one source file using a writable temporary cache. The default cache first returned an internal error; a writable-cache run found one `Literal` diagnostic, corrected before the final clean run.
- Validators after implementation: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (6,019 publishable files); `ARCHITECTURE_VALID`; `git diff --check` clean. T4/T5 new-file byte scan: all eight new plan/report/unit/renderer files checked as UTF-8, LF, no BOM, and no trailing whitespace.
- Layer state: L1 contract values and receipt/hash binding, L4 rendering/storage/admission, L5 internal helper, and L7 PostgreSQL handoff are XONG-CHƯA REVIEW. L2 and L3 are NOT APPLICABLE (no application service or persistence schema/migration change). L6 is DEFERRED-BY-OWNER.
- G4 blocker: current BE2 `CheckpointBinding`/`RenderBinding`/`AdmissionReceipt` source types are checkpoint-specific. T4 export rejects checkpoint/restore history. No synthetic checkpoint was fabricated; no BE2 port or Vision claim was called. G4 needs a separately approved operation-export source contract/allowlisted path before mapping this handoff.
- Not run: migration/Alembic, full unit collection (known 12 collection errors from missing `imageio`/`imageio_ffmpeg` remain; no package installed), `test_live_image_demo_api.py`, UI/visual AC20, Modal/GPU/provider, real-child data, or Vision claim. No stage, commit, or push occurred.
- Protected owner hashes remain: SOURCE_REGISTER `0B43E4BA`; FEAT-063 CONTEXT `E7C8143A`; STATUS `F1ADB793`; REMAINING_AI `8BBFD0ED`; REV36_DELTA `B61B0607`; VIDEO_FLOW `93374E96`; S1_DECISION_CARD `4D95D303`.
- Snapshot: `.claude/handoff/snapshots/G2_20261101T154756/` contains the G2 file list, SHA-256 manifest, copies, and tracked-file delta from G1R.
- No stage, commit, or push occurred.

### T12 partial — G6 PostgreSQL acceptance (partial run complete; full acceptance not met)

- Task plan/spec: `.claude/handoff/CODEX_PROMPT_T12_POSTGRES_RUN_20261101.md`; SHA-256 `055F557F7228E6DA1F74B0D5E3B6497972F19B0A24ED9D20047B7357C506365D`. This local handoff procedure is the pinned execution specification; no separate plan file is in the T12 allowlist.
- R0 baseline: offline regression set **508 passed, 4 skipped in 23.96s** with database variables unset. An earlier invocation had one wrong test path, exited before collecting tests (`no tests ran`); it is not a test failure and is not counted.
- R0 local DB safety inspection (read-only): connection file existed; database name matched `be1_acceptance`; target resolved to loopback; connection succeeded to PostgreSQL **17.11**. The database had 99 user tables in 10 repository migration-owned schemas, 10 Alembic version rows matching all current heads, and the T1 `data_origin` column/check plus synthetic-proof table were present. No migration was applied at R0.
- Current row baseline is non-empty: 25 tables contain rows; organization and adult-identity counts are synthetic-prefixed, while managed profiles, synthetic proofs and child turns are empty. No row values or connection data were recorded.
- R1 append-only approvals were added to both FEAT-063 and FEAT-064, pinning the execution spec hash and the partial test/database boundary. Do not include PostgreSQL suites that create/drop a second database. No source or migration edits are authorized here.
- R0/R1 checks are recorded; database tests, migration downgrade, final validators, and G6 snapshot are still pending. No `.env` or token was read; no stage, commit or push occurred.
- R2: `alembic upgrade heads` ran against the pinned loopback DB with settings `_env_file=None`; it succeeded and emitted no revision application because all 10 heads were already current.
- R3 actual PostgreSQL outcomes: `test_be1_postgres_api.py` excluding the global retention-worker case = **1 passed, 2 failed, 1 deselected**. Failures: route catalog assertion expected 50 and got 51; room-code flow expected HTTP 200 but received `CONSENT_NOT_EFFECTIVE` (409). No source/test fix was made. Its 3 synthetic organizations, 4 synthetic adults, and the one new rate-limit row were removed by exact test ownership; table row counts returned to the per-run baseline.
- `test_be1_age_provenance_postgres.py` = **1 passed**; fixture cleanup restored all table counts.
- `lesson_library/test_lesson_library_api.py` = **5 passed, 1 failed**. The upload/review test received HTTP 503 `DEPENDENCY_UNAVAILABLE` because the local ClamAV scanner at loopback port 3310 was unavailable; the fixture cleanup restored all table counts. No scanner or package was installed.
- `test_be1_synthetic_pilot_postgres.py` = **56 passed in 62.30s**; fixture cleanup restored all table counts, and no new synthetic organization/adult rows remained.
- AI Jobs tests requiring a separate PostgreSQL database were NOT RUN because they create/drop a second `be2_b2_*` database, outside this one-database authorization. No other integration database was touched.
- R4 safety preflight after test cleanup: `be1_managed_profiles=0`, `SYNTHETIC_DEV profiles=0`, and `be1_synthetic_eligibility_proofs=0`; the approved database remained loopback-only. The authorized `be1_core@-1` downgrade removed `20261101_be1_age_0001`, then `be1_core@head` restored it. Both commands succeeded; `age_revision` and `age_source` returned, all 10 Alembic version rows matched the preflight set, and profiles/proofs remained at zero.
- Final synthetic-pilot rerun after test typing/import fixes: **56 passed in 70.77s**; all 99 user-table counts matched pre-run values; managed profiles/proofs remained zero.
- Ruff check and format passed; strict mypy on the new PostgreSQL test passed with no issues. Final validators: HARNESS_VALID; REPOSITORY_SECURITY_VALID (6,032 publishable files); ARCHITECTURE_VALID; `git diff --check` clean; UTF-8/LF/no-BOM/no-trailing-whitespace scan clean for the T12 test, report, and ledger.
- T12 report: `evidence/notes/T12_LITE_POSTGRES_REPORT_20261101.md`; SHA-256 `4A674FB55AE036FB5BE75CBC7B45E09B4A6F1DE4D733E60B5DC6260F13440BC3`. G6 snapshot: `.claude/handoff/snapshots/G6_20261101T164500/`.
- No `.env`/token was read; no stage, commit or push occurred.

### T6 — Invocation guard and observation provenance

- Status: **BLOCKED before implementation**. Plan `plan/T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_20261101.md`; SHA-256 `C2186576249BA008D30ADEE47DCD132F8C8FCD3588F5E7FC1F87EE61AC7E2A71`. Approval appended for blocker-only scope; no code/tests/DB operation.
- Layer matrix: L1-L2 BLOCKED; L3 NOT RUN; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 NOT RUN.
- Blocker: BLOCKED before implementation: T0 leaves total HTTP wall deadline, completion margin, late-response policy, and transport-bound invocation handshake unresolved.
- Owner questions: Owner: set total HTTP deadline/completion margin/cold-start policy; define late complete-response disposition; freeze immutable invocation identity and guard handshake at the transport boundary.

### T7a — Minimal durable assistance and analysis state

- Status: **BLOCKED before implementation**. Plan `plan/T7A_DURABLE_PILOT_STATE_PLAN_20261101.md`; SHA-256 `6BB50353C244759CB054FF044A9298BC8252B630DA09C2D2A53C93DBFF3B6E6C`. Approval appended for blocker-only scope; no code/tests/DB operation.
- Layer matrix: L1 NOT RUN; L2 BLOCKED; L3 BLOCKED; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Blocker: BLOCKED before implementation: O16 does not name the single schema/migration owner, selected schema/parent/revision, exact durable subset, or writer; T6 remains blocked where shared lifecycle requires its guard contract.
- Owner questions: Owner: identify single schema/migration owner, exact migration branch/parent/schema/revision, selected durable method subset, and O16 writer.

### T7b — OwnerFenceV1 and acceptance unit of work

- Status: **BLOCKED before implementation**. Plan `plan/T7B_OWNER_FENCE_UOW_PLAN_20261101.md`; SHA-256 `D08D62A346D3397A0D7F0ED2FB0012E4C234B9D27505833B9A9410E1B4A020F1`. Approval appended for blocker-only scope; no code/tests/DB operation.
- Layer matrix: L1-L2 BLOCKED; L3 BLOCKED by T7a; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Blocker: BLOCKED before implementation: T7a durable storage and a concrete cross-owner atomic transaction boundary are not established. Per owner instruction §E.3, missing co-signatures are not treated as the blocker and remain unsigned.
- Owner questions: Owner: identify the BE1-owned transaction hook/fence publication and exact approved UoW/fence methods; confirm concrete OwnerFenceV1 contract while retaining unsigned status.

### T7c — Run manifest, invocation ledger, and host witness

- Status: **BLOCKED before implementation**. Plan `plan/T7C_RUN_LEDGER_WITNESS_PLAN_20261101.md`; SHA-256 `C3806A9DE0DB1502E8D971DB76A7CED1D551F503619FD1546313B9CBEF0C50BE`. Approval appended for blocker-only scope; no code/tests/DB operation.
- Layer matrix: L1-L2 BLOCKED; L3 BLOCKED; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Blocker: BLOCKED before implementation: depends on T7a/T7b and T6; O16 paths/schema/writer remain unresolved and the selected host witness filesystem/durability boundary has not been verified.
- Owner questions: Owner: freeze manifest issuer and invocation IDs, O16 paths/schema/writer, witness directory/filesystem and accepted Windows durability primitive, and T12 throwaway fault-test identities.

## G3 closeout — 2026-11-01

- Group status: **XONG-CHƯA REVIEW** as a blocker closeout. T6, T7a, T7b and T7c are **BLOCKED before implementation**; no runtime code or tests were run for these blocked tasks. Their individual plans, SHA-256 hashes, append-only blocker-scope approvals, layer matrices and open owner questions are recorded immediately above in the task updates.
- T6 is blocked by the unresolved total HTTP deadline/completion margin, late-response disposition, and invocation identity at possible-send. T7a is blocked by unresolved O16 schema owner, exact durable method subset, migration/schema path/revision/parent and writer. T7b is blocked by missing T7a plus the BE1-owned atomic source/eligibility fence hook; the owner’s §E.3 signature waiver is honored and signatures remain unsigned. T7c is blocked by T6/T7a/T7b dependencies and unverified host witness filesystem/durability boundary.
- Tests: G3 task-level red/green **NOT RUN**, because implementation did not begin; no failure count is inferred. PostgreSQL, Alembic, witness/fault injection and provider calls **NOT RUN**.
- G2 snapshot recheck: `.claude/handoff/snapshots/G2_20261101T154756/` — 14/14 SHA-256 entries matched before starting G3.
- G3 blocker report: `evidence/G3_GUARD_PERSISTENCE_BLOCKERS_REPORT_20261101.md`.
- Next independent work: G4 T2C inventory and implementation may proceed without T6/T7. T8 and T9 remain dependent on the blocked T6/T7 path.- G3 validation: `validate_harness.py` = `HARNESS_VALID`; `validate_repository_security.py` = `REPOSITORY_SECURITY_VALID` (6,025 publishable files); `validate_architecture.py` = `ARCHITECTURE_VALID`; `git diff --check` clean; G3 new-file UTF-8/LF/no-BOM/trailing-whitespace scan clean.
- G3 snapshot: `.claude/handoff/snapshots/G3_20261101T160006/` (to be hash-verified after capture).

### T2C — BE1 canvas, roster and current-turn adapter (G4)

- Status: **BLOCKED before implementation**; blocker plan and task approval recorded, no adapter code or tests.
- Plan: `plan/T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_20261101.md`; SHA-256 `8E7EACF0C1E8C205A5FBB2FA49F60165A4271F55861A8F5475D5A1CA758064DF`.
- Files this task touched: the T2C plan, the append-only FEAT-064 approval, this ledger, and the combined G4 blocker report `evidence/G4_G4_BLOCKERS_REPORT_20261101.md`.
- Layer status: L1/L2 existing contracts reviewed but insufficiently scoped; L3 NOT DONE; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Tests/PG: NOT RUN; no test failure count exists because implementation did not start.
- Owner question: approve a session-scoped BE1 owner-facts request/source binding organization, class, session, canvas/group, audience, purpose reference, and one consistent snapshot, with exact paths/writer; also identify authoritative age-policy and region-policy revision sources.

### T8 — guarded worker (G4)

- Status: **BLOCKED before implementation**; blocker plan and task approval recorded; worker and transport were not changed.
- Plan: `plan/T8_GUARDED_WORKER_BLOCKER_PLAN_20261101.md`; SHA-256 `7F3781DDA34BB22C7DBF55939085A575544FCB3DACD9C6C980268CDFA26DCF0E`.
- Files this task touched: the T8 plan, the append-only FEAT-064 approval, this ledger, and the combined G4 blocker report.
- Layer status: L1/L2 BLOCKED; L3 BLOCKED; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Tests/PG: NOT RUN; no implementation test or failure count is claimed; no provider call.
- Owner questions: resolve the T6 invocation deadline/identity/late-response contract, T7a durable schema and methods, T7b atomic BE1 fence/UoW, and T2C scoped facts source before a new implementation approval.

### T9 — request gateway, cancel and Child-own-status remainder (G4)

- Status: **BLOCKED before implementation** for the G4 gateway/status remainder. The already completed G1 Teacher pilot-profile route remains XONG-CHƯA REVIEW and is not reopened by this entry.
- Plan: `plan/T9_GATEWAY_STATUS_BLOCKER_PLAN_20261101.md`; SHA-256 `50C39BA327F26103A822D8706E59046935FEE8EA0EB91D9A91806612A0998BBA`.
- Files this task touched: the T9 plan, the append-only FEAT-064 approval, this ledger, and the combined G4 blocker report.
- Layer status: L1/L2 BLOCKED for final lifecycle semantics; L3 BLOCKED by T7a; L4 BLOCKED by T2C/T8; L5 BLOCKED; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Tests/PG: NOT RUN; no production gateway/status route was added, so candidate-router tests would not establish acceptance.
- Owner questions: resolve T6/T7/T8 dependencies; freeze request/cancel/Child-own-status and Teacher-pending routes, DTOs, fields and authorization/error mapping; approve paths and task plans. O18 remains NEW/TBD.

## G4 closeout — 2026-11-01

- Group status: **XONG-CHƯA REVIEW as a blocker disposition**. T2C, T8, and the G4 request/status remainder of T9 are BLOCKED before implementation; the prior G1 Teacher pilot-profile route is unchanged.
- Report: `evidence/G4_G4_BLOCKERS_REPORT_20261101.md`; SHA-256 `8C432C2B372602CB31D02694263DD5C0C044D2C7B9D6ADA6F1E57E8BC44DDBDB`.
- Plans and approvals: T2C `8E7EACF0C1E8C205A5FBB2FA49F60165A4271F55861A8F5475D5A1CA758064DF`; T8 `7F3781DDA34BB22C7DBF55939085A575544FCB3DACD9C6C980268CDFA26DCF0E`; T9 remainder `50C39BA327F26103A822D8706E59046935FEE8EA0EB91D9A91806612A0998BBA`. Append-only blocker approvals pin each plan and bound writes to its plan/report/approval/ledger.
- Tests: T2C/T8/T9 implementation tests NOT RUN; no red count inferred. PostgreSQL/Alembic NOT RUN. Ruff/mypy NOT RUN because no Python implementation files changed. UI/visual AC20 DEFERRED-BY-OWNER/NOT RUN. No Modal/GPU/provider/network or real-child data.
- Checks actually run: `python tools/validate_harness.py` → HARNESS_VALID; `python tools/validate_repository_security.py` → REPOSITORY_SECURITY_VALID (6,029 publishable files); `python tools/validate_architecture.py` → ARCHITECTURE_VALID; `git diff --check` clean; 4 G4 plan/report files UTF-8/LF/no-BOM/no-trailing-whitespace.
- Protected owner hashes unchanged: SOURCE_REGISTER `0B43E4BA`; FEAT-063 CONTEXT `E7C8143A`; STATUS `F1ADB793`; REMAINING_AI `8BBFD0ED`; REV36_DELTA `B61B0607`; VIDEO_FLOW `93374E96`; S1_DECISION_CARD `4D95D303`.
- Snapshot: `.claude/handoff/snapshots/G4_20261101T161324/`.
- No stage, commit, or push occurred.

### T10 — Child UI handoff contract (G5)

- Status: **XONG-CHƯA REVIEW cho tài liệu hợp đồng UI**; UI DEFERRED-BY-OWNER; runtime submit/status integration BLOCKED by T9 and the T4/T5 source versus candidate checkpoint DTO mismatch.
- Plan: `plan/T10_CHILD_UI_HANDOFF_CONTRACT_PLAN_20261101.md`; SHA-256 `96AFC6FB2DF302CB1404FB92CDAEDA85CBEAA58D26FF305F4D61B13E5460B261`.
- Approval: append-only T10 documentation-only entry in `approvals/TASK_APPROVAL.md`; pins the plan and exact docs-only allowlist.
- Evidence: `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`; SHA-256 `840A96780CC9F3FCEF20BF5839ACFFDDA3F053CCD20C8A46E06F37B4E42D8970`.
- Layers: L1 candidate request DTO reviewed, final source-binding contract BLOCKED; L2/L3/L4 BLOCKED by T9/G3/T2C; L5 production route NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED. Candidate fixture route is documented as non-live only.
- Tests: UI/npm/visual AC20 NOT RUN; L5 production contract test NOT RUN because no mounted route/source-bound DTO exists. No red count inferred.
- Owner questions: freeze a command binding `CanvasRenderHandoffV1` without checkpoint fabrication; route/DTO for submit/cancel/Child-own-status; stable public errors for lost reply/UNKNOWN/denied poll; payload and preview fields.

### T11 — Teacher pending-analysis UI contract (G5)

- Status: **XONG-CHƯA REVIEW cho tài liệu hợp đồng UI**; UI DEFERRED-BY-OWNER; route/DTO integration BLOCKED while O18 remains NEW/TBD and T9/G3 dependencies remain blocked.
- Plan: `plan/T11_TEACHER_PENDING_UI_CONTRACT_PLAN_20261101.md`; SHA-256 `F4AF9EA99F73D866190180086B34938E8BC027F3B729B38013D0D6E9D54AFE70`.
- Approval: append-only T11 documentation-only entry in `approvals/TASK_APPROVAL.md`; pins the plan and exact docs-only allowlist.
- Evidence: `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`; shared G5 contract document, SHA-256 `840A96780CC9F3FCEF20BF5839ACFFDDA3F053CCD20C8A46E06F37B4E42D8970`.
- Layers: L1/L2/L5 BLOCKED for final route/projection; L3/L4 BLOCKED by G3/T2C/T8; L6 DEFERRED-BY-OWNER; L7 BLOCKED. No production Teacher pending route was added.
- Tests: UI/npm/visual AC20 NOT RUN; L5 route tests NOT RUN because O18 has no frozen route/DTO. No red count inferred.
- Owner questions: freeze O18 route, minimal safe DTO, pagination/error mapping, and whether Teacher pending read is allowed while paused or without an active turn.

## G5 closeout — 2026-11-01

- Group status: **XONG-CHƯA REVIEW for contract documentation only**. T10/T11 UI stays DEFERRED-BY-OWNER; production request/status and Teacher pending routes remain BLOCKED.
- Shared contract draft: `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`; SHA-256 `840A96780CC9F3FCEF20BF5839ACFFDDA3F053CCD20C8A46E06F37B4E42D8970`.
- Plans pinned by append-only approvals: T10 `96AFC6FB2DF302CB1404FB92CDAEDA85CBEAA58D26FF305F4D61B13E5460B261`; T11 `F4AF9EA99F73D866190180086B34938E8BC027F3B729B38013D0D6E9D54AFE70`.
- Tests: UI/npm/visual AC20 NOT RUN; production L5 route tests NOT RUN because route/DTO/source binding are not frozen or mounted. PostgreSQL/Alembic/provider NOT RUN. No red count inferred.
- Checks actually run: `validate_harness.py` → HARNESS_VALID; `validate_repository_security.py` → REPOSITORY_SECURITY_VALID (6,032 publishable files); `validate_architecture.py` → ARCHITECTURE_VALID; `git diff --check` clean; 3/3 G5 new files UTF-8/LF/no-BOM/no-trailing-whitespace.
- Snapshot: `.claude/handoff/snapshots/G5_20261101T161840/`.
- No stage, commit, or push occurred.

### G6 review fixes — lượt riêng TREO KHÔNG COMMIT

- Trạng thái: **F1 DONE; F2 BLOCKED; F3 ghi nhận MÂU THUẪN CHƯA PHÂN XỬ; F4 kiểm tra xong với ghi chú phiên bản.** Goal G2–G6 vẫn giữ trạng thái trước đó.
- Plan: `plan/G6_REVIEW_FIXES_PLAN_20261101.md`, SHA-256 `F17A53203EFCD901FDA058FFF329D8EEFFBA28A87117D9CCD2D19E26FA62416B`; báo cáo: `evidence/G6_REVIEW_FIXES_REPORT_20261101.md`.
- F1 sửa assertion path/operation 50/55 thành 51/56; lần chạy BE1 API cuối 3 passed, 1 failed (F2). F2 vẫn 409 vì `get_verified_device` trong `be1_runtime` chặn trước canvas; patch thứ ba vượt phạm vi được duyệt nên không áp dụng.
- F3 giữ bản T12 đã commit nguyên byte (SHA-256 `98DE23DFEE611B491E90FFEA9DDAAB82962D4D0565253E9C6885CD1C80574D63`); thiếu log/số hàng B5 riêng để phân xử khác biệt cách dọn.
- F4: Ruff 0.16.4 trong môi trường; pyproject cho `>=0.12,<1`, uv.lock là 0.17.2. Sửa import order ở một test được phép; hai file F4 được phép đều qua check/format. Full-set Ruff còn cảnh báo I001 ở BE1 API và format ở app-composition/BE1 API; không sửa ngoài phạm vi.
- Kiểm thử: contract 1381 passed (live-network test NOT RUN); unit 6204 passed / 13 failed / 24 skipped / 12 collection errors; PostgreSQL BE1 API 3 passed / 1 failed; synthetic pilot 56 passed. Chi tiết nguyên nhân và validator ở báo cáo.
- Validator: HARNESS_VALID; REPOSITORY_SECURITY_VALID (6035); ARCHITECTURE_VALID; `git diff --check` sạch. Không có Modal/GPU/provider/mạng ngoài hoặc dữ liệu trẻ thật.
- Snapshot: `.claude/handoff/snapshots/G6R_20261101T175708/`. Không stage, commit hoặc push.

### G6 F2-only — NOT RUN tại cổng thủ tục PostgreSQL

- R0 plan/approval đã hoàn tất; plan `G6_F2_PLAN_20261101.md` SHA-256 `BDE6D64168B6801E023AB305B3F787D46474152C49DB4779A37DE93BB2DF9AF8`, owner prompt SHA-256 `446AF8ADB92885282B7CAE26F8D2561A1E01911BD2E97B5995E21DD2F614271D`.
- F2 **NOT RUN**, không sửa test: prompt ghim T12 SHA `...365D`, file T12 hiện có SHA `...3657`; không đọc file kết nối hoặc chạy DB khi hash thủ tục lệch. Kết quả đỏ HTTP 409 ở báo cáo G6 trước đây là lịch sử, không phải chạy lại lượt này.
- BE1 PostgreSQL API/synthetic-pilot modules và test âm: NOT RUN. Ruff 0.16.4: file BE1 API còn I001 và format finding; giữ nguyên vì file không đổi trong F2. Các validator đạt; xem `evidence/G6_F2_REPORT_20261101.md`.
- Snapshot: `.claude/handoff/snapshots/G6F2_20261101T181528/`. Không stage, commit hoặc push; goal G2–G6 không đổi trạng thái.
### G6 F2-only — tiếp tục sau đính chính hash; BLOCKED ở assertion mới

- Owner đính chính hash T12 thật kết thúc `...3657`; mục đính chính đã append vào approval CẢ FEAT-063 và FEAT-064. Prompt F2 `446AF8AD...4271D` và plan `BDE6D641...DF9AF8` giữ nguyên hash.
- Đã chạy PostgreSQL thật trước/sau: trước 1 failed tại drawing HTTP 409; sau 1 failed tại dòng 652 `len(stored_attempts)==10`, thực tế 1. Kiểm tra âm pending consent 409 và request drawing sau đúng hai patch mới đạt HTTP 200/accepted trước khi gặp assertion mới. Không tuyên bố F2 xanh.
- Theo hard stop, dừng tại assertion mới, không sửa query/assertion hoặc thêm patch thứ tư. Hai module PG đầy đủ NOT RUN trong lượt tiếp tục. Sau mỗi lượt focused, 98 bảng giữ số hàng mốc từng bảng (561 hàng có trước); chỉ dọn dữ liệu do test lượt này tạo.
- Chỉ hàm test F2 đổi; F1/F3/F4 và mã sản phẩm giữ nguyên. Ruff 0.16.4 còn I001/format có trước; validator HARNESS_VALID, REPOSITORY_SECURITY_VALID (6037), ARCHITECTURE_VALID, diff check sạch.
- Chi tiết và lỗi nguyên văn: `evidence/G6_F2_REPORT_20261101.md`, mục tiếp tục ngày 2026-11-01 18:30. Snapshot `.claude/handoff/snapshots/G6F2_20261101T182616/`. Cần chỉ thị owner cho điểm lỗi tiếp theo; không stage/commit/push, goal G2–G6 không đổi.

### G6 F2 rate-limit assertion — hoàn tất test phía PostgreSQL

- Owner duyệt mở rộng; plan và approval chỉ append, plan SHA-256 mới `6BA7E86D199A7822E57641BAF52E1A255367AC6F840BFEC1EDB6DE505ED2E210`.
- Chẩn đoán tại điểm lỗi: 8 dòng, lengths [1,2,2,2,2,2,2,10], query không WHERE lấy length 1; đúng nguồn TestClient có một dòng length 10. Đã lọc source_hmac theo helper sản phẩm với đúng ASGI client tuple; GIỮ assertion ==10. Chỉ test F2 đổi; không sửa lỗi assertion bổ sung (0/2).
- Focused F2 1 passed; BE1 API đầy đủ 4 passed / 0 failed / 0 skipped; synthetic pilot 56 passed / 0 failed / 0 skipped. Sau mỗi lượt, 98 bảng ứng dụng giữ số hàng mốc từng bảng (561 hàng có trước).
- Inventory hiện tại: 99 bảng tổng = 98 ứng dụng + 1 alembic_version; G6 lịch sử không có raw inventory để đối chiếu danh tính từng bảng. Không có migration/xóa bảng trong lượt này.
- Ruff còn I001/format cũ; mypy so bản trước còn cùng 1 lỗi fixture dòng60, không lỗi mới. Các validator đạt, diff check sạch. Báo cáo chi tiết nối tại `evidence/G6_F2_REPORT_20261101.md`.
- Snapshot `.claude/handoff/snapshots/G6F2_20261101T183921/`. F2 hoàn tất test-only; goal G2–G6 không đổi. Không stage/commit/push, không sửa sản phẩm hoặc gọi Modal.

## GOAL A1 — bước 0 / baseline (2026-11-01)

- Owner đã duyệt đủ mục4 V4; V4 SHA `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`; goal SHA `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`. Phạm vi M1 → T7a → T6, không goal sau. OWNER_MODAL_CALL_APPROVED: NO.
- HEAD `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`, index rỗng, 7 prefix owner khớp. Baseline đầy đủ gồm git status + SHA256 từng file và bản sao bytes tại `.claude/handoff/snapshots/GA1_BASE/` (không dùng G6F2 sáu file làm mốc).
- Số file mốc: 57; SHA256 manifest `fbbdc06e0a78cc1ec47a28e2c6a17a69a1d4454c26895cd9903f00996caf392e`. Mọi thay đổi mới phải thuộc task và được ghi vào sổ.
- Đang đo test nền, F2 và Alembic heads thật; chưa coi kết quả lịch sử là kết quả goal này.

```text
 M backend/src/sketch2life/contracts/schemas/be1_runtime.py
 M backend/src/sketch2life/domain/core_foundation.py
 M backend/src/sketch2life/interfaces/http/be1_runtime.py
 M backend/src/sketch2life/interfaces/http/routers/be1_artifacts.py
 M backend/src/sketch2life/interfaces/http/routers/be1_canvas.py
 M backend/src/sketch2life/interfaces/http/routers/be1_registry.py
 M backend/src/sketch2life/interfaces/http/routers/be1_sessions.py
 M backend/tests/contract/test_app_composition.py
 M backend/tests/contract/test_be1_synthetic_pilot.py
 M backend/tests/contract/test_openapi_contract_catalog.py
 M backend/tests/integration/test_be1_postgres_api.py
 M backend/tests/integration/test_be1_synthetic_pilot_postgres.py
 M docs/context/SOURCE_REGISTER.md
 M features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md
 M features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md
 M features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md
 M features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md
 M features/FEAT-064-current-flow-modal-vision-dev/evidence/notes/T12_LITE_POSTGRES_REPORT_20261101.md
?? backend/src/sketch2life/infrastructure/canvas_render/
?? backend/tests/unit/test_canvas_operation_profile.py
?? backend/tests/unit/test_canvas_source_export.py
?? backend/tests/unit/test_canvas_source_render.py
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/G1_REVIEW_FIXES_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/G3_GUARD_PERSISTENCE_BLOCKERS_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/G4_G4_BLOCKERS_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/G6_F2_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/G6_REVIEW_FIXES_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/T2_CHILD_CANVAS_RECONNECT_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/T3_CANVAS_PROFILE_IMPLEMENTATION_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/T4_AUTHORITATIVE_CANVAS_EXPORT_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/T5_CANVAS_RENDER_ARTIFACT_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/T9_TEACHER_PILOT_PROFILE_ROUTE_REPORT_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/evidence/notes/T12_LITE_POSTGRES_REPORT_20261101_RUN1_AS_COMMITTED.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/G1_REVIEW_FIXES_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/G6_F2_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/G6_REVIEW_FIXES_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T10_CHILD_UI_HANDOFF_CONTRACT_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T11_TEACHER_PENDING_UI_CONTRACT_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T2_CHILD_CANVAS_RECONNECT_IMPLEMENTATION_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T3_BE1_CANVAS_PROFILE_IMPLEMENTATION_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T4_AUTHORITATIVE_CANVAS_EXPORT_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T5_CANVAS_RENDER_ARTIFACT_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T7A_DURABLE_PILOT_STATE_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T7B_OWNER_FENCE_UOW_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T7C_RUN_LEDGER_WITNESS_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T8_GUARDED_WORKER_BLOCKER_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T9_GATEWAY_STATUS_BLOCKER_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/plan/T9_TEACHER_PILOT_PROFILE_ROUTE_IMPLEMENTATION_PLAN_20261101.md
?? features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md
```

### M1 (A1) — ĐANG LÀM

- Plan `M1_CANVAS_CAPACITY_RENDER_PLAN_GA1_20261101.md`, SHA `D27E902D268200F954758F26D262DA6E1D3A3D1D3F470AF05A9442D4863B418F`, approval append đã ghim V4/goal/plan. Chạm L3/4/5/7; L1 profile nguyên hash; L2 không sửa; L6 DEFERRED. Mốc offline590pass4skip; Alembic10head.

### M1 (A1) — XONG-CHƯA REVIEW

- Plan SHA D27E902D268200F954758F26D262DA6E1D3A3D1D3F470AF05A9442D4863B418F; fixture addendum49E05F5BEF07A235489DA626D28F40F8F6FC6C2C3DC72B4B2F5A396B149C6723; evidence `evidence/M1_CANVAS_CAPACITY_RENDER_REPORT_GA1_20261101.md`, SHA `126522099f857374f3451fe52a5792481707ce99dfd931f70f2924d3d15a38a4`.
- L1 profile nguyênhash; L2khôngsửa; L3PG; L4unit20pass(test-first9fail1pass); L5PGcapacity4red→5green thêm deadline; L6DEFERRED; L7baseline590→601pass4skip, PGsynthetic56pass. Ruff7file sạch; mypy4lỗi cũ/no new; validators đạt.
- Deadline cooperative; commitlate503 có thể giữartifact/metadata đãcommit. Không sourcebypass. Snapshot `.claude/handoff/snapshots/GA1_M1_20261101T192254/`.
- File task: limits.py, renderer.py, be1_canvas.py, be1_artifacts.py; newtests canvas_render_limits_ga1/canvas_capacity_ga1_postgres; profileunitfake; plan/addendum/evidence và append approval/ledger.

### T7a (A1) — ĐANG LÀM

- Plan `T7A_DURABLE_REPOSITORIES_LEDGER_PLAN_GA1_20261101.md`, SHA `8A277676DC3DE4DDD19A7B69FFFC14ABF12EA729E9B87254980D71D422C201C7`; approval appended, scopeL1–4/7; L5notin task/L6deferred. M1complete snapshot GA1_M1_20261101T192254.

### A1 baseline bổ sung — F2 và migration assertion cũ

- F2/API PG thật4pass trướcM1 và4pass sauM1 (2.44s); DBsốhàng từngbảng giữmốc. Alembic script10head; DBversion10rows. Assertion cũ ai_jobs/test_migrations.py335–340 mong2versions, đọc thực tế10 nên equality=False. Nguyênpytest NOTRUN vìfixture tạo/dropDBkhácngoàiranhgiới1DB; không giảđã chạy test. Bằngchứngread-only `.claude/handoff/snapshots/GA1_BASE/old-migration-assertion-readonly.json`.

### T7a (A1) — XONG-CHƯA REVIEW; aggregate regression has one stale test

- Approved plan SHA `8A277676DC3DE4DDD19A7B69FFFC14ABF12EA729E9B87254980D71D422C201C7`; implementation/evidence `evidence/T7A_DURABLE_REPOSITORIES_LEDGER_REPORT_GA1_20261101.md`.
- New durable branch `20261102_pv_0001`: nine `pilot_vision` tables; scoped SQL Assistance/Analysis repositories, fixed-type codec, single-use invocation ledger, and metadata registration. 17 focused unit tests passed; five focused PostgreSQL tests passed. Ruff check/format passed; mypy passed on five source files.
- PostgreSQL roundtrip upgrade → `pilot_vision@base` downgrade → upgrade succeeded. It preserved the 561 preexisting application rows and restored the previous 10 Alembic version rows on downgrade; final state is the new pilot head with 9 version rows and 9 empty pilot tables. An initial reversed label `base@pilot_vision` was a no-op; detected before testing, then corrected and verified.
- Aggregate offline set: 606 passed, 1 failed, 4 skipped. Only failure: `tests/unit/test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation` expects 24 script revisions; the added branch makes the graph 25. That existing test is outside the T7a allowlist and remains unchanged; aggregate regression is therefore not green pending an approved test-scope update.
- Snapshot in progress: `.claude/handoff/snapshots/GA1_T7A_20261101T194545/`. No stage/commit/push, provider call, or real-child data.

### T7a (A1) — final verification and snapshot (2026-11-01 19:51 Asia/Saigon)

- Reran the aggregate offline set with both M1 `test_canvas_render_limits_ga1.py` and T7a `test_pilot_vision_persistence_ga1.py`: 617 passed, 1 failed, 4 skipped. The only failure is `tests/unit/test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation` at line 456: expected 24 revisions, actual graph 25 after adding `20261102_pilot_vision.py`. This test is outside the T7a allowlist; not changed. Aggregate regression remains NOT GREEN and should be handled under a separately approved test scope.
- Re-ran validators: `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (6,053 files scanned); `ARCHITECTURE_VALID`; `git diff --check` clean.
- T7a report updated with the final run count. Snapshot: `.claude/handoff/snapshots/GA1_T7A_20261101T195106/`. No stage/commit/push, provider call, Modal, or real-child data.

### GOAL A1 — Tạm dừng trước T6 (2026-11-01 19:52 Asia/Saigon)

- T6 chưa bắt đầu. Cổng regression của goal yêu cầu dừng khi test nền tụt mà không thể khôi phục trong phạm vi task: T7a thêm revision `20261102_pilot_vision.py`, làm assertion trong `tests/unit/test_synthetic_eligibility.py:456` đòi 24 thay vì graph thực 25. Test này không nằm trong allowlist T7a; không sửa.
- T7a focused unit/PG và migration roundtrip đã chạy theo báo cáo, nhưng aggregate offline regression chưa xanh. Cần owner quyết định có duyệt một sửa test-only đúng assertion revision-count, với plan/approval hẹp, hay giữ nguyên trạng thái dừng. T6 chưa được triển khai theo hard stop; không có Modal/provider/network call.
- Tạm dừng sau snapshot `.claude/handoff/snapshots/GA1_PAUSE_20261101T195200/`. Không stage/commit/push.

### GA1 revision-count test alignment — second hard-stop (2026-11-01 20:05 Asia/Saigon)

- Owner approved the narrow test-only scope; approval text SHA-256 `6718eb16faeeed242440d31868d20868130aa9d2f52f42ac322b894dd9aa84e7`; pinned plan SHA-256 `B86D35814B73D759049BC06C23D75C050CAA6398CA5252726C2979A8D4C0C158`.
- Changed only the revision-count assertion/comment in `backend/tests/unit/test_synthetic_eligibility.py` from 24 to 25.
- Focused test: **1 failed** at line 463. The first count assertion passes; actual head counts are `(11, 9)`, while the following assertion expects `(10, 10)`. The test also still expects `20261101_be1_age_0001` to be dependency-aware terminal.
- Cause is the T7a migration's independent root (`down_revision=None`) and its `depends_on` edges to the age and AI revisions. The pilot revision is the dependency-aware terminal head. No migration change is proposed.
- Per the approved plan's hard-stop, full offline aggregate was **NOT RUN** after this focused failure. The prior aggregate remains 617 passed / 1 failed / 4 skipped. T6 has not started.
- Any update to head counts, dependency-aware terminal identity, or its explanatory comment needs a separate exact-scope approval. Evidence: `evidence/GA1_REVISION_COUNT_TEST_ALIGNMENT_REPORT_20261101.md`. No PostgreSQL, Modal/provider/network, real-child data, or Git publication action.

### GOAL A1 — revision graph regression gate cleared (2026-11-01 20:17 Asia/Saigon)

- Owner approved the exact head-expectation follow-up; approval text SHA-256 `d53ba18a53938062d5293b2c34a71b1b1d10d4601b370a352b3e365894ab81ff`; plan `plan/GA1_REVISION_GRAPH_HEAD_ALIGNMENT_PLAN_20261101.md`, SHA-256 `272B7C06546BABB86AFB1DBDCB2CB6CC73B0872CFC3667D9F40A80E9F5D84DF6`.
- Updated only the approved assertions/comment in `backend/tests/unit/test_synthetic_eligibility.py`: total revisions 25; down_revision-only/dependency-aware heads `(11, 9)`; `20261102_pv_0001` is the dependency-aware terminal head.
- Verification: focused test 1 passed; established GA1 offline regression with M1/T7a unit add-ons 618 passed, 4 skipped, 0 failed in 8.60s; runner exit 0. The copied runner blocked external network, cleared DB/provider configuration, and kept pytest temp files outside the repository.
- Evidence: `evidence/GA1_REVISION_GRAPH_HEAD_ALIGNMENT_REPORT_20261101.md`; local snapshot `.claude/handoff/snapshots/GA1_HEADFIX_20261101T201542/`.
- The regression hard-stop is cleared. T6 remains NOT STARTED. Before any T6 source edit, create and pin a GA1-specific implementation plan and append its approval under V4 D3; the earlier G3 T6 approval remains blocker-disposition-only. No PG, Modal/provider/network, staging, commit, or push.

### T6 (A1) — XONG-CHƯA REVIEW (2026-11-01 20:53 Asia/Saigon)

- Approved plan `T6_INVOCATION_GUARD_IMPLEMENTATION_PLAN_GA1_20261101.md`, SHA-256 `E339DE53582C60DA2BAFF65236333ABEFEC0E087D6D42D0F1340F73C69B8668B`; authority V4/Goal A1 hashes match their pins. T6 implementation approval was already appended before source changes.
- Implemented L1 guard port/failure codes/live bridge provenance, L4 single-use ledger guard + one-request 160-second bounded HTTP transport + identity-checked bridge outcome + one-attempt policy; L7 adds 19 T6 test cases and evidence. L2/L3/L5 unchanged; L6 deferred. No service/worker/caller wiring.
- Test-first red was an expected collection import error for the not-yet-added `InvocationGuardState`. First broad run showed six offline fixture failures from over-broad typed-failure checks; validation was narrowed to guarded live transport. Final focus: 653 passed / 4 skipped. Cleared 618-test A1 baseline plus M1/T7a add-ons and 19 T6 cases: 637 passed / 4 skipped / 0 failed. No PostgreSQL/Alembic, Modal/GPU/provider, external network, or real-child data.
- Ruff check passed; Ruff format check: four new files already formatted; mypy: seven source files, no issues. `HARNESS_VALID`, `REPOSITORY_SECURITY_VALID` (6,062 scanned), `ARCHITECTURE_VALID`; `git diff --check` clean. Report: `evidence/T6_INVOCATION_GUARD_IMPLEMENTATION_REPORT_GA1_20261101.md`.
- Snapshot: `.claude/handoff/snapshots/GA1_T6_20261101T205305/`. No independent review is claimed. No stage/commit/push. `OWNER_MODAL_CALL_APPROVED: NO`.


### T6 final validator recount (2026-11-01 20:53 Asia/Saigon)

- The final validator run after the T6 report was added returned `REPOSITORY_SECURITY_VALID` with 6,063 publishable files scanned. The earlier T6 entry's 6,062 count was from the run before that new report existed. All three validators and `git diff --check` were rerun and passed.

### T6 independent review — NEEDS_REVISION (2026-11-01)

- Read-only review against V4 D3, Goal A1, the approved T6 plan, approval, implementation report, tests, and snapshot `GA1_T6_20261101T205305`. V4/A1 pins match; the twelve T6 snapshot files match current files; approval and ledger preserve the prior lines and append only.
- Findings: P1, decorator can pass success or downgrade `provider_invoked=True` while its guard is still NEW (`invocation_guard.py:208`); P2, race test starts the second worker after the first has sent and persisted SENT (`test_invocation_guard_transport_ga1.py:400`); P2, synchronous DNS lookup is outside the socket timeout and can exceed the total deadline (`transport.py:84`). Details and fix directions are in `evidence/T6_INDEPENDENT_REVIEW_REPORT_GA1_20261101.md`.
- The recorded 637 passed / 4 skipped, validators, and static checks were not rerun by the reviewer. No source or approval entry was changed; no PostgreSQL, Modal, provider, or external network call. T6 remains XONG-CHƯA REVIEW pending fixes and follow-up review; A2 must not start before review passes.

### T6 independent-review fixes — XONG-CHƯA REVIEW (2026-11-01 21:45 Asia/Saigon)

- Owner launch message approved the bounded review-fix plan `T6_REVIEW_FIXES_PLAN_GA1_20261101.md`, SHA-256 `30BB0D4778B3CFE81F9DB04E67DE1078483FE2A61E2A3BBC336E7AC0291D0160`; its approval was appended before source edits. V4/A1/frozen-T6 plan pins were rechecked and matched.
- Added same-object guard identity exposure and constructor/pre-call checks; guard NEW only passes typed local failures marked not invoked. Added deadline-bounded resolver injection, preserved HTTPS hostname/certificate validation, and synchronized independent claims at the claim boundary. Duplicate-after-SENT and crash/restart remain separate tests. No ledger/schema/migration edit.
- Focused T6: 28 passed / 0 failed. Copied GA1 offline runner, exact script SHA-256 `766225385A00C5E6537C000F5BA71E559E5BABCF58243E0DB199FE342D3C8E76`, with updated T6 module: 618 passed / 4 skipped / 0 failed. The previous T6 report recorded 637/4; the current same-byte runner output differs by 19 tests, with no failures. The run output does not identify the cause; no attribution is made.
- Ruff check passed on all four T6 implementation/test paths. Format check passed on the three files changed solely for this task; whole-file formatting of `legacy_v2.py` would alter unrelated pre-existing lines, so those lines were left untouched. Mypy passed on three T6 source files after using a temporary cache.
- Initial validators before adding this follow-up report/ledger returned `HARNESS_VALID`, `REPOSITORY_SECURITY_VALID` (6,065 files), `ARCHITECTURE_VALID`, and `git diff --check` exit 0. Final post-document recount is recorded in the review-fix report.
- Evidence: `evidence/T6_REVIEW_FIXES_REPORT_GA1_20261101.md`. New local snapshot: `.claude/handoff/snapshots/GA1_T6_REVIEWFIX_20261101T214519/`. No PostgreSQL/Alembic, Modal/GPU/provider, external network, stage, commit, or push. A1 remains XONG-CHƯA REVIEW; do not start A2 until independent review accepts these fixes.

### T6 review-fix independent review — NEEDS_REVISION (2026-11-01)

- Read-only follow-up against V4 D3, Goal A1, the approved implementation/review-fix plans, approval, source, tests, report, and snapshot `GA1_T6_REVIEWFIX_20261101T214519`. V4/A1/review-fix plan/report hashes match their recorded pins. The three prior findings appear fixed: guard identity is checked at construction and before invocation; unexpected NEW outcomes are rejected; the race test synchronizes inside the shared claim; DNS wait is bounded for the caller.
- P1 evidence blocker: copied runner defaults omit `tests/unit/test_invocation_guard_transport_ga1.py` and append tests only from command-line arguments. Saved aggregate log is 618 passed / 4 skipped, while focused T6 log is 28 passed. Thus the saved 618 aggregate does not evidence the claimed appended T6 module. Rerun the established offline suite with M1/T7a add-ons and T6 explicitly appended; preserve exact arguments/output and append corrected evidence plus a new snapshot. Expected count is 646 passed / 4 skipped if no failures; record actual.
- P2 implementation risk: `transport.py:242` starts one daemon resolver thread per lookup. A caller timeout cannot stop a stalled resolver, so repeated/concurrent timeouts can accumulate unbounded live threads. Resolve with an explicitly bounded resolver strategy and a deterministic repeated-stall test before wiring concurrent live calls. This expands the approved review-fix source scope; create a narrow plan and obtain owner approval before editing source.
- Reviewer did not run tests or validators and made no source/test/approval/plan/snapshot changes. No PostgreSQL/Alembic, Modal/GPU/provider, or external network was used. Keep GOAL A1 at `XONG-CHƯA REVIEW`; do not start A2. Full review: `evidence/T6_REVIEWFIX_INDEPENDENT_REVIEW_GA1_20261101.md`.

### T6 regression correction and bounded-resolver plan review — OWNER APPROVAL PENDING (2026-11-01)

- Independently checked the correction report and new copied runner snapshot `GA1_T6_REGRESSION_CORRECTION_20261101T222500`: runner hash matches; exact command includes the M1 canvas-render, T7a persistence, and T6 invocation-guard unit add-ons; saved output is 646 passed / 4 skipped, both runner and outer process exit 0. The earlier aggregate-evidence finding is cleared. Tests were not rerun by this reviewer.
- Reviewed draft plan `plan/T6_BOUNDED_DNS_RESOLVER_PLAN_GA1_20261101.md`, SHA-256 `2D1E5D4B46613FA7AEBCC8A96E6288F87423DF725174FF88DBAA46DA7A66B10F`. The proposed process-wide cap of two active resolver workers, no unbounded queue, retaining capacity while a resolver remains blocked, fail-closed saturation, and focused saturation/recovery tests are technically acceptable. Owner must explicitly confirm that cap 2 applies per Python process (so N BE processes allow up to 2N workers) before implementation.
- No approval entry for this plan hash was present. This review is not implementation approval. No code/test/plan/approval/snapshot was changed; no validators or tests were run. Keep T6 `XONG-CHƯA REVIEW`; do not start A2. Full plan review: `evidence/T6_BOUNDED_DNS_PLAN_REVIEW_GA1_20261101.md`.

### T6 review-fix regression correction and bounded DNS plan — A1 (2026-11-01)

- The independent review found that the prior saved aggregate output omitted the T6 module, despite the previous report wording. No prior report, approval, plan, or snapshot was edited. Correction report: `evidence/T6_REGRESSION_CORRECTION_REPORT_GA1_20261101.md`, SHA-256 `0E6870260AB74BB3C2CC64B0C81C3086DAEC6AD17E0399FB0F7B6BF74681D1DE`.
- A fresh snapshot runner copied byte-for-byte (SHA-256 `766225385A00C5E6537C000F5BA71E559E5BABCF58243E0DB199FE342D3C8E76`) ran with explicit M1, T7a, and T6 add-ons. Actual result: 646 passed / 4 skipped / 0 failed; runner and outer exit code 0. Exact command and output are saved in `.claude/handoff/snapshots/GA1_T6_REGRESSION_CORRECTION_20261101T222500/`.
- The P2 finding that timed-out DNS calls can leave unbounded DNS resolver daemon threads is not implemented. New draft plan `plan/T6_BOUNDED_DNS_RESOLVER_PLAN_GA1_20261101.md`, SHA-256 `2D1E5D4B46613FA7AEBCC8A96E6288F87423DF725174FF88DBAA46DA7A66B10F`, proposes a process-wide cap of two active resolver workers, fail-closed saturation, and deterministic multi-stall tests. This is a recommendation only; no approval has been appended and no source/test was changed for this finding.
- T6 remains `XONG-CHƯA REVIEW`; await owner approval of the plan and worker cap before resolver source/test work. No A2, PostgreSQL/Alembic, Modal/GPU/provider, or external network operation.
### T6 bounded DNS resolver follow-up — XONG-CHƯA REVIEW (2026-11-01 22:51:26 Asia/Saigon)

- Owner approved plan T6_BOUNDED_DNS_RESOLVER_PLAN_GA1_20261101.md, SHA-256 2D1E5D4B46613FA7AEBCC8A96E6288F87423DF725174FF88DBAA46DA7A66B10F, with a process-wide cap of at most two active resolver workers per Python process. Approval was appended before source changes.
- Updated only backend/src/sketch2life/infrastructure/vision_analysis/transport.py and backend/tests/unit/test_invocation_guard_transport_ga1.py: bounded shared resolver pool, no unbounded queue, deadline-bounded capacity/DNS waits, fail-closed saturation, deterministic stalled-resolver saturation and recovery coverage.
- Focused T6 module: 30 passed / 0 failed in 14.60s. Offline GA1 runner with explicit M1/T7a/T6 add-ons: 648 passed / 4 skipped / 0 failed in 22.42s; runner and outer exit 0. Runner SHA-256 766225385A00C5E6537C000F5BA71E559E5BABCF58243E0DB199FE342D3C8E76.
- Ruff check and format check passed; mypy reported no issues in transport.py. HARNESS_VALID; REPOSITORY_SECURITY_VALID (6,071 publishable files); ARCHITECTURE_VALID; git diff --check exit 0; report UTF-8/whitespace check clean.
- Report evidence/T6_BOUNDED_DNS_RESOLVER_REPORT_GA1_20261101.md, SHA-256 D6D5E1DDABF0ABFBF2A3035248097085EECF695BEF5BBB8F570199E2A14ECA91. Snapshot .claude/handoff/snapshots/GA1_T6_BOUNDED_RESOLVER_CLOSEOUT_20261101T224927/.
- No PostgreSQL/Alembic, Modal/GPU/provider, or external network was used. No stage, commit, push, or A2. A1 remains XONG-CHƯA REVIEW pending independent review.

### T6 final independent review — ACCEPTED; GOAL A1 still pending (2026-11-01)

- Approved bounded-resolver plan SHA-256 `2D1E5D4B46613FA7AEBCC8A96E6288F87423DF725174FF88DBAA46DA7A66B10F` and owner approval for a process-wide cap of two active resolver workers per Python process were verified. Review confirmed the pool has no unbounded submission queue, timed-out waiters do not release active resolver slots, saturation fails closed before `SENT`/HTTP bytes, and the test exercises concurrent saturation and recovery.
- Prior T6 findings on guard identity/NEW-state handling, claim-race timing, DNS deadline, and omitted aggregate test evidence are resolved. Snapshot `GA1_T6_BOUNDED_RESOLVER_CLOSEOUT_20261101T224927` contains 23 manifest entries; every copied file matches its hash, and 16 copied working-tree files match the current files. Saved report records 30 focused tests and 648 passed / 4 skipped for the offline aggregate with all three add-ons. Reviewer did not rerun tests or validators.
- No actionable T6 finding remains; T6 is independently accepted. This does not accept GOAL A1 as a whole: M1 and T7a remain `XONG-CHƯA REVIEW` in their ledger entries. Keep A1 pending and do not start A2 until those components are independently reviewed and the owner closes A1. Full review: `evidence/T6_FINAL_INDEPENDENT_REVIEW_GA1_20261101.md`.
- Branch/HEAD and empty index were verified. No source/test/approval/plan/snapshot changes, tests, validators, PostgreSQL/Alembic, Modal/GPU/provider, or external network operation were performed by the reviewer. No stage/commit/push.

### M1 and T7a final independent review — GOAL A1 NEEDS_REVISION (2026-11-01)

- Reviewed V4, Goal A1, approved M1/T7a plans, addendum, reports, source/tests, and implementation snapshots. V4 and Goal A1 pinned hashes match.
- **M1 ACCEPTED:** no actionable finding in scope. Export limits/order, pre-render capacity checks, renderer semaphore/deadline, admission/provenance, and failure cleanup match the approved contract. M1 snapshot has 12 entries; ten current files match, with only the append-only approval and ledger advanced afterward.
- **T7a NEEDS_REVISION — P2:** `backend/src/sketch2life/infrastructure/assistance/sql_repository.py:168-178`, `put_receipt()` checks the receipt key's organization but not `receipt.snapshot.facts.organization_id`. A receipt scoped to org A can therefore persist and return an org B request snapshot if the same assistance ID exists under both organizations. Require the snapshot organization to match the bound repository and add a regression test before re-review. No source/test fix was made.
- T7a snapshot has 74 entries; 72 current files match, with only append-only approval and ledger entries advanced. Implementation test/validator counts were read from reports and not rerun by this reviewer. T6 was previously independently accepted.
- A1 is **NEEDS_REVISION / not accepted** until the T7a finding is fixed and independently reviewed; do not start A2. Review evidence: `evidence/M1_T7A_FINAL_INDEPENDENT_REVIEW_GA1_20261101.md`, SHA-256 `69A4684FD512EA30923E53004AE17B5D3E1E25CBF17926B691658373813A14A3`.
- Review changed only this append-only ledger entry and the review report. Branch/HEAD remain `feature/feat063-be-foundation` / `1e93bc3f3ac645cf4baecbbc09c73afe48719c92`; index was empty. No tests, validators, PostgreSQL/Alembic, Modal/GPU/provider, external network, stage, commit, or push.

### T7a tenant-scope review fix — implementation verified; pending independent re-review (2026-11-01 23:36 Asia/Saigon)

- Resolved the reported P2 in `SqlAssistanceUnitOfWork.put_receipt()`: validate `receipt.snapshot.facts.organization_id` against the bound organization before any SQL. Added a unit regression with a repository-scoped receipt key, foreign-organization snapshot, and a storage mock that must remain untouched. No schema, migration, service, port, or route changed.
- Focused T7a persistence module: **18 passed**. Offline GA1 runner with the M1, T7a, and T6 add-ons: **649 passed, 4 skipped, 0 failed**; runner and outer exit were both 0. Ruff check/format, strict mypy on both changed Python files, and the three repository validators passed. The final `git diff --check` is recorded after this append-only update.
- Report: `evidence/T7A_TENANT_SCOPE_REVIEW_FIX_REPORT_GA1_20261101.md`, SHA-256 `5677467DC4D0B29DB4F4EE53D15D7995F70CDD20FEBF3E035D87C9D85FE0B9E2`. Runner/output and copied source records are in `.claude/handoff/snapshots/GA1_T7A_TENANT_SCOPE_FIX_20261101T233641/`.
- **GOAL A1 status: XONG-CHƯA REVIEW; not yet COMPLETE.** The previous independent reviewer must re-review the correction and accept T7a before the owner closes A1. Do not start A2 before that gate. No PostgreSQL/Alembic, Modal/GPU/provider, external network, stage, commit, or push was used in this correction.

### GOAL A1 independent-review dispatch — unresolved bridge outcome (2026-11-01 23:39 Asia/Saigon)

- Requested a separate read-only Codex review thread under stable request ID `a1-t7a-tenant-scope-review-20261101-2338`, as required for independent review. The thread bridge returned `outcome_unknown` / `InvalidMessage: did not receive a valid HTTP response`; `get_operation` remained unknown and thread listing also failed with the same transport error.
- No reviewer thread ID or disposition was obtained. Do not treat this as a review or mark GOAL A1 COMPLETE. Current status remains **XONG-CHƯA REVIEW** pending a confirmed independent review. Do not start A2.

### GOAL A1 final closeout — COMPLETE after independent T7a review (2026-11-01 23:52 Asia/Saigon)

- Owner supplied the independent Claude review of the T7a correction. Disposition: **ACCEPTED**; the organization-scope P2 is closed. Review record: `evidence/T7A_TENANT_SCOPE_INDEPENDENT_REVIEW_GA1_20261101.md`, SHA-256 `B8D8A72B143D3A3B9019B2486288DD1E0A3AC5270716720753155D840B57C66A`. The previous unresolved Codex-thread dispatch entry above is superseded by this confirmed reviewer result.
- M1 and T6 were previously independently accepted. The reported implementation evidence for the final T7a fix is focused 18 passed and offline GA1 649 passed / 4 skipped / 0 failed, with Ruff, mypy, three validators, and scoped diff-check passing. The independent reviewer did not rerun these checks.
- **GOAL A1 status: COMPLETE.** The implementation fix is being included in the existing unpushed A1 commit under the owner's prior instruction. No A2 work is included here.
- The existing A2 goal pins the old HEAD `1e93bc3f…`; the current post-A1 branch baseline is newer. A2 remains unopened until the owner chooses and approves the revised post-A1 HEAD pin and updated goal hash.
