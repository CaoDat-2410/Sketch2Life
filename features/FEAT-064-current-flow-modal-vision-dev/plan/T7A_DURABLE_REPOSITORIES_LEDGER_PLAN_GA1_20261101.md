# T7a — durable pilot repositories + invocation ledger (GOAL A1)

## Căn cứ và lớp

Owner V4D2/D7 và goal A1, task sau M1. M1 đã XONG-CHƯA REVIEW. Không đổi các plan/T0 đã ghim; mục này thay disposition BLOCKED cũ bằng phạm vi được owner duyệt.

| Lớp | Phạm vi/cổng |
|---|---|
| L1 | Tái dùng domain assistance/analysis/records; fixed-type codec roundtrip đơn vị, không sửa domain tại T7a. |
| L2 | Implements các port hiện có; không sửa service hoặc ports ai_jobs. |
| L3 | Schema nhánh riêng; upgrade/downgrade đúng nhánh trên PostgreSQL owner tạo; method durability/atomic/CAS/uniqueness thật. |
| L4 | Scoped SQL repositories, codec, ledger; unit trước/sau và PG. |
| L5 | Không route/composition mới. |
| L6 | DEFERRED-BY-OWNER. |
| L7 | Mốc CPU601pass4skip và PG BE1 giữ; ledger race/restart/rollback và method inventory. |

## Storage và các phương thức

- Schema pilot_vision, ít nhất9 bảng: request,receipt,event,notice,epoch,analysis_head,observation,provider_result,invocation. Tên vật lý chốt trong tables.py và migration, cùng metadata. Không evidence_kind CHECK liệt kê values để T6 thêm live_legacy_bridge không đổi migration.
- Hai repository bind organization_id, short transaction có org-scoped advisory transaction lock; không giữ transaction qua provider. Có CAS expectedversion và recordversion+1; analysis binding/observation hash immutable; unique active semantic identity(org,semantic) bằng partial index cho scheduling/scheduled. Epoch(request,analysis) commit cùng state/fence; OwnerFence BE1 thật thuộc A2, chưa giả đã có.
- Inventory36 members: Assistance18methods+transaction và Analysis16methods+transaction; T0csv13ATOMIC_DURABLE/12READ_ONLY/11FAIL_CLOSED. Assistance cache3methods(find_cache,put_cache,add_sketch_intent) và Analysis correction/receipt/invalidation/notice8methods phải raise failclosed. Mỗi selectedmethod có test bền/atomic hoặc scopedread; không trả fake/noop để lấp port.
- JSONB payload dùng codec có registry fixed-type của các domain dataclass/enums được import tĩnh, tuple/frozenset/datetime/mapping tagged; không pickle, không import loại dữ liệu từ tên trong JSON. Reject unknown tag/type và nonfiniteJSON.
- Provider result reference/rawcanonical/hash phải bền; test cleanup xóa exactorg/resultref theo FK dependency trước head hoặc cascade schema-owned. Chỉ service-path repository ghi; chưa có API/worker writer mở ngoài scope.
- Ledger ngay từ T7a đủ run_id UNIQUE, job_id/attempt_id UNIQUE pair, state CLAIMED/SENT/SUCCEEDED/FAILED/UNKNOWN, timestamps, result hash. Claim atomic không thể reset/reuse; crash CLAIMED/SENT không cho gửi lại. API giao tiếp T6 dùng primitives(run_id,job_id,attempt_id,organization_id), claim/mark_sent/complete/get. T6 mới dùng guard/transport; T7a không gọi network.

## Migration và metadata

- File `backend/alembic/versions/20261102_pilot_vision.py`, revision20261102_pv_0001; down_revision=None; branch_labels=(pilot_vision,); depends_on=(20261101_be1_age_0001,20261015_ai_0001).
- backend/alembic/env.py thêm đúng MỘT target_metadata.append cho pilot_vision; import metadata/schema và khai báo managedschema là boilerplate cần thiết, không sửa list metadata nền hoặc các registration cũ.
- Downgrade chỉ drop tables/schema nhánh mới do task tạo, explicitowner exception T12; không DROP/TRUNCATE bảng cũ, không hạnhánh BE1/AI cũ. Chỉ sau khi toàn bộ hàng nhánh mới của test đã dọn và nhánh không có dữliệu ngoài test. Sau roundtrip để DB ở head mới.
- Test cũ `ai_jobs/test_migrations.py:335–340` có fixture tạo/drop DB khác: NOT RUN theo ranhgiới1DB. Đọc so `_versions=={BE1_CHAIN[0],AI_HEAD}` bằng query trong DB đượcduyệt và ghi kếtquảthật riêng; không giảđã chạy nguyênfixture, không sửa testcũ.

## Allowlist chính xác

- New backend/src/sketch2life/infrastructure/vision_analysis/{tables.py,codec.py,repository.py,ledger.py}.
- New backend/src/sketch2life/infrastructure/assistance/sql_repository.py (và __init__.py nếu cần).
- New backend/alembic/versions/20261102_pilot_vision.py; backend/alembic/env.py theo scope trên.
- New backend/tests/unit/test_pilot_vision_persistence_ga1.py; backend/tests/integration/test_pilot_vision_persistence_ga1_postgres.py.
- Plan này; evidence/T7A_DURABLE_REPOSITORIES_LEDGER_REPORT_GA1_20261101.md; append approval/ledger; snapshot.

## Acceptance/test-first/rủi ro

- Viết tests trước, ghi đỏ thật. Codec roundtrip +unknown tags; all selectedmethods /11failclosed; rollback/restart; CAS stale; unique semantic concurrency; ledger unique run/pair; providerresult cleanup. PG tests dùng unique testorg/run/job/attempt, dọnđúnghàng test.
- Schemaofflinegraph, onlineup/down/up, counts/version rows trước/sau, DBretainedhead. Ruff/mypy chỉ lỗi mới/3validators/diffcheck; hồi quy baseline không tụt.
- Residual: DB-only ledger không chống host/DBrestore theo run-firstV4, witness deferred; no OwnerFence BE1 actual untilA2; statusread projection/teacher authorization not exposed untillatergoal. No livecall, token/.env, realchilddata, stage/commit/push.
