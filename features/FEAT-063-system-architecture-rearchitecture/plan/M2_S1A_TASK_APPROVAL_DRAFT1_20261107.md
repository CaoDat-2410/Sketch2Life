# M2 S1a Task Approval — Draft 1

**Status: DRAFT — CHƯA ĐƯỢC OWNER DUYỆT, CHƯA LAUNCHED.** Đây là phiếu để owner và reviewer xem xét. Nội dung không phải approval, không mở S1a và không cấp quyền sửa code, ghi database, migration, test hay chạy lệnh.

**Owner decision record:** CHƯA CÓ. Các hướng owner nêu trong hội thoại ngày 2026-11-07 được đánh dấu riêng bên dưới; chúng chưa được ghi vào DECISIONS.md và cần owner xác nhận lại trong Task Approval cuối.

**Independent review:** CHƯA CÓ cho Draft 1.

## 1. Baseline, nguồn và provenance

### 1.1. Plan và checkout

| Mục | Giá trị | Ý nghĩa |
|---|---|---|
| Plan lập kế hoạch | features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md | SHA-256 7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1 |
| Owner decision về plan | D-151 | Draft 10 được nhận làm baseline lập kế hoạch; không mở pha và không phải Task Approval |
| Branch / HEAD lúc soạn | feature/feat063-be-foundation / dd70685eae58aaaefea3e567f5c23d09345a8513 | Baseline hiện tại; final Task Approval phải ghim lại và dừng nếu khác |
| Index lúc soạn | Rỗng | Không có staged path |
| DECISIONS.md | SHA-256 C2B57EE2E65BD8FB9CA8084B90B352A028B1B8E09707D0B1B162798243B85B1 | D-142…D-154 có mặt tại lúc soạn |
| approvals/TASK_APPROVAL.md | SHA-256 FEEE42E506F94352A8161EFE0B4B94870967072BEDF233285BFDF882352A3DF7 | Có S0-owner-run approval/closure; chưa có S1a approval |
| Evidence S0-doc | SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001 | S0-doc CLOSED trong phạm vi tài liệu theo D-150; không phải bằng chứng implementation |
| Evidence inventory S0-owner-run | .claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json; SHA-256 E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F | Owner-run, coordinator đọc artifact; không phải kết nối DB của phiên soạn Draft 1 |

### 1.2. Nguồn sản phẩm được ghim

- SRS điều khiển: SRS v2.3-draft, features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md, SHA-256 DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC.
- DTR điều khiển: features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md, SHA-256 3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22.
- SRS v2.7-draft chỉ dùng làm đối chiếu, chưa ký và chưa gộp vào be-foundation. Hai ref origin/docs/feat063-srs-v26-checklist-20261107 và origin/docs/feat063-diagram-readiness-20261107 trùng byte, SRS SHA-256 3869BA77EA0867FF7C7DAD491D9D0D6B90E332CA936B4236EE3AA7AEF4027696. Không thay pin v2.3.
- Các ref SRS trước đó chỉ để truy nguyên: v2.5 origin/docs/feat063-rev45-srs-code-alignment-20261106, SHA-256 SRS b513ad2f510a7cda6c54fb0b49523005a60a2f918b4ac705231006ec6be9da7e; v2.6 origin/docs/feat063-srs-conflict-remediation-20261106, SHA-256 SRS dd9382fe0eb8a32c4e0206f0e5107dab49cef063e2b73156d1efb51a08007f4f; nhánh v2.6 khác origin/docs/feat063-v25-report-remediation-20261106, SHA-256 SRS 56aca9fac892f189653d59120ac8afaeb1c7730addd60076bd7fc39436f931a7.
- DTR được ghim là v2.3; DTR tại nhánh v2.7 không thay nguồn chuẩn. DTR v2.7 thiếu core.upload_command_receipts và story.command_receipts so với bản đã có StoryRun-lite amendment; số logic/physical được báo là 92/140 so với 94/142. Đây là ghi chú so sánh, không phải thay đổi S1a.
- Hai nhánh v2.6 khác nhau về cách gọi role; nhánh v25-report-remediation giữ “Admin tổ chức”, không coi “organization admin” là alias của School Manager và chờ Q-13; nhánh này không phải tổ tiên của v2.7. Decision IDs D-135…D-138 giữa các nhánh có nghĩa khác nhau; SRS v2.7 dùng D-146 cho nội dung/quota, khác D-146 của be-foundation. Mọi trích dẫn quyết định trong hồ sơ M2 phải ghi kèm nhánh/tài liệu.
- Phần yêu cầu S1a cần dùng vẫn là năm route mẫu tại SRS v2.3 §21.2, đúng một Teacher active phụ trách lớp, tuổi 36–120 tháng, provenance/origin và BR-49/BR-58 theo phạm vi Draft 10. Không dùng v2.7 để thay đổi contract đã ghim.

### 1.3. Trạng thái S0 và DB được owner báo

- S0-doc đã đóng tại phạm vi đối chiếu tài liệu theo D-150. S0-owner-run đã đóng tại phạm vi đúng một lượt inventory chỉ đọc theo D-154. Hai trạng thái này không mở S1a.
- S0-owner-run quan sát DB sketch2life trên PostgreSQL 17.11 native localhost:5433: 117 bảng, 82 hàng tổng, 9 hàng public.alembic_version. Đây là dữ kiện owner-run được ghi trong inventory; không xác nhận mọi hàng ứng dụng là synthetic.
- K3 của S0-owner-run FAIL: inventory ghi revision 20261103_story_upload_compat; source có head 20261104_story_revisions; schema story trong inventory có năm bảng. K4 source comparison chưa chạy, K5 synthetic-only proof cho 15 hàng baseline chưa có và NOT RUN, K7 NOT RUN. Không suy diễn K3 thành migration đã chạy hay graph hiện hành đã được hòa giải.
- Owner báo DB riêng sketch2life_m2_s1a đã được tạo trên cùng PostgreSQL 17 native instance localhost:5433, user postgres, từ dump schema-only sketch2life-schema-only-20261107.dump, SHA-256 E02F2D6E43053FBBACC388002AC9A66FABC73A9AE51399704FB65179BD1BE2E8. Owner báo 117 bảng, 0 hàng và chưa chạy Alembic trên DB này. Phiên soạn Draft 1 không kết nối để xác minh các dữ kiện đó; dump không được đọc trực tiếp trong phiên này.
- D-154 ghi lúc đó DB schema-only chưa tạo; thông tin owner nêu ở trên là trạng thái sau thời điểm ghi D-154. Không coi đây là mâu thuẫn.

### 1.4. SRS v2.7 — ghi chú đối chiếu, không phải authority

- v2.7 làm rõ School Manager là tên thống nhất; “Admin nội dung” là permission của Platform Admin, không phải role/principal đăng nhập. Platform Admin xem media trẻ: deny mặc định. D-148 mục 1–2 không đổi; mã school_admin chỉ xuất phát từ D-148, không phải mã role do SRS tạo.
- v2.7 giữ các yêu cầu lõi S1a nêu trên, nhưng có khác biệt cần biết khi review: SRS dùng SYNTHETIC_TEST trong khi DB CHECK hiện dùng SYNTHETIC_DEV; DTR v2.7 bỏ hai receipt tables; SRS §11.2 và DTR v2.7 chốt Teacher dùng quota school, không có TEACHER_ACCOUNT. Các khác biệt quota/receipt không mở rộng S1a.
- SRS v2.7 §31.10 mục 14–17 có các quyết định role/persistence/resolver, plan supersession và audit còn mở. Những mục này không được tự quyết trong S1a. Các ghi chú về M3–M6 chỉ là tham khảo cho kế hoạch sau, không đổi mốc hay scope.

## 2. Pha và phạm vi đề nghị

**Pha:** M2 S1a — identity, tenant/role, profile, age provenance. Trạng thái hiện tại vẫn CLOSED / NOT LAUNCHED cho đến khi owner duyệt một Task Approval cuối đã review độc lập.

### 2.1. Route set

Theo SRS v2.3 §21.2 và Draft 10 §4.1, năm route pattern nền gồm sáu HTTP operations:

1. POST /v1/parent/profiles
2. GET /v1/parent/profiles/{profile_id}
3. PATCH /v1/parent/profiles/{profile_id}
4. POST /v1/organizations/{org_id}/classes
5. POST /v1/classes/{class_id}/assignments
6. POST /v1/classes/{class_id}/profiles

Assignment route chuẩn là POST /v1/classes/{class_id}/assignments theo hướng F-1 của owner và SRS §21.2. Source hiện có route assignment theo organization với class trong body; final approval phải chỉ rõ cách chuyển sang route chuẩn và disposition cho route cũ. Không thêm alias writable song song nếu chưa được owner duyệt riêng.

### 2.2. Hướng owner đã nêu, chưa ghi vào DECISIONS.md

Đây là hướng từ hội thoại ngày 2026-11-07, chưa phải approval thực thi. Owner cần xác nhận lại các mục F-1, F-2, F-4, F-6, F-7 và F-8 trong Task Approval cuối.

| Mục | Hướng được owner nêu | Giới hạn/chỗ cần chốt trước launch |
|---|---|---|
| F-1 | Route chuẩn assignment là POST /v1/classes/{class_id}/assignments theo SRS §21.2. | Cách xử lý route BE1 cũ; không tự thêm alias hoặc xóa route cũ. |
| F-2 | Bảo đảm chính xác một Teacher active phụ trách mỗi lớp; thêm ca Teacher thứ hai vào M2-AT-04A. | Chốt kết quả khi cố gán Teacher thứ hai: từ chối hay chuyển giao nguyên tử; không tự đặt response code/transition. |
| F-3 | Hướng role/tenant denial đã chốt tại D-148 mục 5. | Coordinator gán nhãn F-3 theo nội dung D-148; không coi nhãn là ID đã ghi trong D-148. |
| F-4 | school_admin bị từ chối tại route tạo profile Teacher. | Chốt error envelope/code hiện hành; không tạo mã mới nếu chưa được duyệt. |
| F-5 | Hướng age 36–120 tháng đã chốt tại D-148 mục 6–7. | Coordinator gán nhãn F-5 theo nội dung D-148; không coi nhãn là ID đã ghi trong D-148. |
| F-6 | S1a chỉ tạo profile synthetic; SYNTHETIC_DEV với consent_id và consent_purpose_ref NULL. REAL và LEGACY_UNCLASSIFIED bị từ chối. Route M2 kế thừa ràng buộc child_id bắt đầu synthetic-, display_name bắt đầu Synthetic , age_source là SYNTHETIC_FIXTURE từ create_synthetic_profile. Đường tạo profile REAL hiện có phải bị chặn trong M2. | Chốt cơ chế chặn REAL và phạm vi route bị chặn; không thay đổi hành vi BE1 rộng hơn nếu chưa được owner nêu rõ. |
| F-7 | Giữ giá trị vật lý SYNTHETIC_DEV dù SRS v2.3 gọi SYNTHETIC_TEST; ghi rõ ánh xạ, không migration enum. | Chốt biểu diễn API/contract và mapping giữa giá trị contract với giá trị lưu trữ. |
| Age | Dùng một hằng 36–120 ở application cho Parent; không dùng domain/child_age.py cho Parent profile. | Chốt age_source/provenance semantics của Parent; không thêm ngày sinh chính xác. |
| F-8 | Ba route Teacher/tổ chức dùng các bảng BE1 hiện có, không migration BE1. Ba operations Parent dùng Parent-owned parent.child_profiles và parent.profile_revisions; Parent là owner duy nhất, không gộp với be1.managed_profiles, không FK chéo owner. Alembic chỉ trên sketch2life_m2_s1a và chỉ thêm bảng parent.* mới; không đổi/xóa bảng hiện hữu và không đụng sketch2life. | Cần F-9 về Alembic bootstrap và xác nhận bảng vật lý sau K4; không migration trước quyết định. |
| F-9 | CHƯA QUYẾT. | Owner chọn cách xử lý Alembic target trước bất kỳ migration hoặc test PostgreSQL nào cần schema mới. Xem §5. |

### 2.3. Ngoài phạm vi

- S1b grant/share/consent, M2-AT-05/06/07 và OI-05..08: DEFERRED; không mở và không chạy.
- S2 job/asset/revision/StoryRun lifecycle, M2-AT-08/09, route /v1/story-runs, /cancel hoặc /api/be1: ngoài scope.
- S3, M3–M6, OpenAPI P3, provider, Modal, GPU, mạng ngoài, ClamAV, dữ liệu người dùng thật và production.
- Profile deletion, Parent/Teacher profile merge, cross-owner foreign key, schema convergence của các bảng BE1/Core/Story hiện có.
- Consent giả, REAL, LEGACY_UNCLASSIFIED hoặc bất kỳ dữ liệu thật nào.

## 3. Database policy, lệnh ứng viên và command ceilings

### 3.1. DB duy nhất được xem xét cho S1a

| Thuộc tính | Giá trị được owner báo | Điều kiện trước lệnh |
|---|---|---|
| Database task-owned | sketch2life_m2_s1a | Owner xác nhận lại tên và mục đích trước mỗi lần chạy |
| Instance | PostgreSQL native Windows, major 17 | Owner xác nhận đúng service/instance; phiên này chưa kết nối |
| Host/port | localhost:5433; dự kiến loopback 127.0.0.1 | Owner xác nhận listener loopback; non-loopback bị cấm |
| User | postgres | Owner xác nhận current_user và quyền; least-privilege chưa được chứng minh. Không tạo role trong scope này. |
| Nội dung | Owner báo 117 bảng, 0 hàng, schema-only copy | Chỉ là owner report; cần kiểm identity/schema trước khi dùng. Bất kỳ hàng không synthetic hoặc không rõ provenance nào thì dừng. |
| Alembic | Owner báo chưa chạy trên DB này | Revision table/graph phải được đọc xác nhận trước khi có migration. |

Không kết nối, đọc hoặc ghi vào sketch2life từ S1a. Không reset, drop, truncate, restore, clone lại, chạy cleanup rộng hoặc sửa DB bất kỳ. Tất cả persistence tests và migration tương lai chỉ được trỏ đúng sketch2life_m2_s1a. Nếu guard không chứng minh chính xác DB, user, loopback host/port và PostgreSQL major, dừng trước khi chạy lệnh.

Mật khẩu chỉ do owner nhập tại prompt cục bộ của công cụ; không dán vào chat, file, command history, log hay biến được ghi vào file. Không mở hoặc sửa .env. Các ví dụ bên dưới không chứa URL hoặc mật khẩu.

### 3.2. Lệnh chỉ đọc được đề xuất để owner xem xét

Các lệnh dưới đây là candidate cho Task Approval cuối, KHÔNG được phép chạy bởi Draft này. Final approval phải pin lại executable, working directory, exact env variable name, command, số lần và timeout. Không dùng command thay thế khi một command lỗi.

**A. Đọc Alembic heads từ source, không kết nối DB; tối đa 1 lần, timeout đề xuất 300 giây:**

    python -m alembic -c backend/alembic.ini heads --verbose

**B. Đọc current revision trên đúng DB target; chỉ sau owner approval riêng cho lệnh đọc và sau khi process-local SKETCH2LIFE_DATABASE_URL được owner đặt an toàn; tối đa 1 lần, timeout đề xuất 300 giây:**

    python -m alembic -c backend/alembic.ini current --verbose

URL chỉ được cung cấp trong process bởi owner, phải được guard xác nhận DB là sketch2life_m2_s1a; không lưu URL vào hồ sơ. Nếu không thể chứng minh target, dừng. Lệnh này đọc revision state; nó không thay thế inventory hoặc K4.

**C. Schema/empty-state inventory read-only bằng psql; mỗi lần trước và sau các thao tác được duyệt tối đa 1 lần, timeout đề xuất 300 giây. Đây là một session READ ONLY; psql hỏi mật khẩu bằng -W:**

    @'
    \set ON_ERROR_STOP on
    BEGIN TRANSACTION READ ONLY;
    SHOW transaction_read_only;
    SELECT current_database(), current_user, inet_server_addr()::text, inet_server_port(), current_setting('server_version');
    SELECT format('SELECT %L AS table_name, count(*)::bigint AS row_count FROM %I.%I;', table_schema || '.' || table_name, table_schema, table_name)
    FROM information_schema.tables
    WHERE table_type = 'BASE TABLE'
      AND table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name
    \gexec
    SELECT version_num FROM public.alembic_version ORDER BY version_num;
    ROLLBACK;
    '@ | psql -X -W -v ON_ERROR_STOP=1 -h localhost -p 5433 -U postgres -d sketch2life_m2_s1a -f -

Nếu public.alembic_version không tồn tại, query lỗi hoặc identity khác, giữ DB nguyên trạng và dừng. Không diễn giải lỗi psql thành kết quả inventory đạt.

### 3.3. Test command candidates và giới hạn đề xuất

Các path mới dưới đây chưa được xác minh tồn tại. Chúng không được tạo hoặc chạy bằng Draft này. Final approval phải pin hash của từng file sau khi có mặt.

| Nhóm | Command candidate | Số lần / timeout đề xuất | Trạng thái |
|---|---|---|---|
| Offline unit/contract và regressions | python -m pytest -q backend/tests/unit/test_profile_age_invariant.py backend/tests/unit/test_age_provenance_columns.py backend/tests/unit/test_child_learning_profile_contract.py backend/tests/contract/test_be1_synthetic_pilot.py backend/tests/unit/test_m2_parent_profile_service.py backend/tests/contract/test_m2_parent_teacher_routes.py | 1 lần, 600 giây | Chờ owner duyệt; path mới cuối chưa xác minh |
| PostgreSQL route/persistence | python -m pytest -q backend/tests/integration/test_m2_s1a_postgres.py | 1 lần, 1800 giây | F-9 phải được quyết; test fixture phải chứng minh chỉ kết nối sketch2life_m2_s1a |
| Alembic source graph | python -m alembic -c backend/alembic.ini heads --verbose | 1 lần, 300 giây | Read-only candidate |
| Alembic current target | python -m alembic -c backend/alembic.ini current --verbose | 1 lần, 300 giây | Chờ target guard và owner approval |
| Alembic ghi schema | CHƯA CÓ COMMAND | Không có số lần hay timeout được duyệt | F-9 OPEN; không chạy upgrade heads mặc định, stamp, upgrade, downgrade hoặc revision command |
| Mypy | NOT RUN trong S0-owner-run theo lựa chọn A của owner | Không có command, cache hoặc output trong approval này | D-144 §9.6 baseline còn nợ; cần scope/quyết định riêng |

Timeout là mức đề xuất, chưa phải quyết định owner. Một timeout, crash, setup error hoặc thiếu summary chính thức là STOP; không retry tự động. Owner giữ log đã khử bí mật và phân biệt PASS, FAIL, ERROR, SKIP, NOT RUN. SKIP/NOT RUN không tính PASS.

### 3.4. Ranh giới ghi DB

Khi và chỉ khi owner đã chọn F-9, review độc lập ACCEPTED và Task Approval cuối pin lệnh migration, phạm vi ghi tối đa được đề xuất là tạo mới các bảng Parent đã liệt kê; không ALTER/DROP/RENAME dữ liệu hoặc bảng BE1/Core/Story hiện có. Không có quyền sửa public.alembic_version ngoài thao tác migration đã được owner chọn cụ thể. Nếu công cụ Alembic cần một thao tác rộng hơn hoặc không thể chứng minh chỉ thêm parent.*, dừng và xin approval mới.

## 4. K4 — đối chiếu schema/source, bước đầu tiên

K4 là bước đọc source và artifact, không kết nối DB. K4 phải hoàn tất trước khi sửa code. Sử dụng inventory S0-owner-run đã ghim làm quan sát lịch sử của sketch2life; không gọi đó là inventory đã xác minh của DB schema-only target. Nếu cần xác nhận target hiện tại, chỉ dùng lệnh READ ONLY ở §3 sau approval riêng.

Đối chiếu theo path cụ thể:

- Inventory S0-owner-run và danh sách schema/bảng/constraint đã ghi.
- backend/src/sketch2life/infrastructure/persistence/be1_models.py và core_models.py.
- backend/alembic/env.py và migration modules đã ghim trong Draft 10 §1.3, gồm backend/alembic/versions/20261104_story_revisions.py.
- S0-owner-run K3 discrepancy: DB recorded 20261103_story_upload_compat, source head 20261104_story_revisions; inventory chỉ ghi năm bảng schema story.
- Các bảng BE1 hiện có và constraints tuổi/origin/consent cần cho S1a; Parent module chưa được Draft 10 xác nhận là đã có.

K4 evidence candidate mới: features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_K4_SCHEMA_SOURCE_RECONCILIATION_20261107.md — CHƯA XÁC MINH/CHƯA ĐƯỢC PHÉP TẠO. Final approval phải ghim path, hash/source inventory, format và allowlist.

Evidence phải phân biệt: (a) quan sát owner-run, (b) đọc trực tiếp source, (c) suy luận, (d) chưa xác minh. K4 không được tuyên bố Alembic graph hiện tại được đối soát nếu chưa đọc DB target bằng lệnh được duyệt. K4 mismatch về bảng, constraint, migration ancestry hoặc Parent metadata là hard stop; không tự sửa migration hay DB.

## 5. F-9 — lựa chọn Alembic còn mở, không có lệnh ghi được duyệt

S0-owner-run K3 FAIL; target schema-only do owner báo có 117 bảng và 0 hàng, chưa có Alembic run. Owner phải chọn cách bootstrap/versioning trước migration. Không có mặc định nào được chọn.

| Phương án cần đánh giá | Có thể làm gì | Rủi ro / bằng chứng cần có |
|---|---|---|
| A. Đối chiếu schema vật lý trước; sau đó stamp một tập revision baseline được xác định rõ và chạy migration Parent additive | Có thể đưa version table về trạng thái mà graph mong đợi mà không replay toàn bộ migrations | Stamp không chạy migration; có thể ghi nhận sai lịch sử nếu bảng/constraint không khớp revision. K3 mismatch hiện tại khiến rủi ro cao. Cần K4 complete, từng revision được đối chiếu với schema target, exact revisions và owner approval. |
| B. Chạy một migration path cụ thể sau khi xác lập baseline đã xác minh; tuyệt đối không dùng upgrade heads mặc định | Có thể thực thi phần thiếu nếu graph và vật lý tương thích | Alembic có nhiều head/dependency; target 117 bảng đã có nhưng version state chưa xác minh. Có thể tạo lỗi xung đột hoặc thay đổi ngoài Parent. Cần SQL offline/plan review, current/heads, chứng minh command chỉ tạo parent.* và owner pin exact target revision. |
| C. Dùng lineage/config/version table tách riêng cho Parent schema | Có thể cô lập trạng thái migration Parent khỏi graph legacy | Tạo hai nguồn sự thật, phức tạp vận hành, khó tích hợp metadata và deployment; cần kiến trúc/owner schema approval và test upgrade từ DB rỗng/schema-only. |

Owner có thể chọn phương án khác nhưng phải ghi rõ revision baseline, version table, dependency, expected DDL, rollback limits, command, pre/post inventory và cách khôi phục. Không dùng downgrade trên DB có dữ liệu. Không chạy migration khi K4 chưa xong hoặc khi phương án được chọn đụng bảng hiện hữu.

## 6. Allowlist dự kiến theo path

Đây là allowlist đề xuất cho owner/reviewer. Nó chưa có hiệu lực. Phiên triển khai chỉ được sửa đúng các path trong Task Approval cuối; không wildcard. Nếu cần path khác, dừng và xin mở scope.

### 6.1. Existing files — chỉ đọc

| Path | Lý do đọc | Quyền sửa trong đề xuất này |
|---|---|---|
| backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py | Identity verifier hiện có | Chỉ đọc |
| backend/src/sketch2life/domain/child_age.py | So sánh rule tuổi; Parent không dùng module này theo owner direction | Chỉ đọc |
| backend/src/sketch2life/contracts/schemas/child_learning_profile.py | Baseline contract liên quan tuổi | Chỉ đọc |
| backend/src/sketch2life/infrastructure/persistence/be1_models.py | BE1 tables, constraints, defaults và invariants hiện có | Chỉ đọc; không đổi schema BE1 |
| backend/src/sketch2life/infrastructure/persistence/core_models.py | Core metadata/ownership baseline | Chỉ đọc |
| backend/src/sketch2life/infrastructure/persistence/core_store.py | Tham chiếu synthetic guard create_synthetic_profile | Chỉ đọc |
| backend/src/sketch2life/interfaces/http/routers/be1_common.py | require_assignment và common denial helpers | Chỉ đọc trừ khi final allowlist xác nhận |
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py | Route class/assignment/profile hiện có | Chỉ đọc cho tới khi approval cuối cho phép sửa |
| backend/src/sketch2life/interfaces/http/routers/be1_records.py | Profile record routes hiện có | Chỉ đọc |
| backend/src/sketch2life/application/ports/identity.py | Principal và identity port | Chỉ đọc |
| backend/src/sketch2life/application/services/be1_runtime.py | BE1 application runtime | Chỉ đọc |
| backend/src/sketch2life/interfaces/http/be1_runtime.py | BE1 runtime/composition dependency | Chỉ đọc |
| backend/src/sketch2life/interfaces/http/app.py | Router mounting/composition | Chỉ đọc |
| backend/alembic/env.py | Alembic metadata/config baseline | Chỉ đọc |
| backend/alembic/versions/20261014_0002_be1_runtime.py | BE1 schema history | Chỉ đọc |
| backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py | Graph dependency context | Chỉ đọc |
| backend/alembic/versions/20261028_ll_0001_lesson_library.py | Graph/schema context | Chỉ đọc |
| backend/alembic/versions/20261031_be1_synthetic_eligibility.py | Synthetic eligibility schema | Chỉ đọc |
| backend/alembic/versions/20261101_be1_age_provenance.py | Age provenance history | Chỉ đọc |
| backend/alembic/versions/20261102_pilot_vision.py | Revision graph context | Chỉ đọc |
| backend/alembic/versions/20261102_story_run_lite.py | Revision graph context | Chỉ đọc |
| backend/alembic/versions/20261103_story_upload_compat.py | K3/schema discrepancy context | Chỉ đọc |
| backend/alembic/versions/20261104_story_revisions.py | Current source head and graph context | Chỉ đọc |
| backend/tests/unit/test_profile_age_invariant.py | Existing regression baseline | Chỉ đọc |
| backend/tests/unit/test_age_provenance_columns.py | Existing regression baseline | Chỉ đọc |
| backend/tests/unit/test_child_learning_profile_contract.py | Existing regression baseline | Chỉ đọc |
| backend/tests/contract/test_be1_synthetic_pilot.py | Existing regression baseline | Chỉ đọc |
| backend/tests/integration/test_be1_age_provenance_postgres.py | Existing PostgreSQL baseline; not assumed safe for this DB | Chỉ đọc |

### 6.2. Existing files — candidate cho phép sửa sau khi owner duyệt bản cuối

| Path | Lý do có thể cần sửa | Giới hạn |
|---|---|---|
| backend/src/sketch2life/application/ports/identity.py | Role/principal contract nếu route policy thực sự yêu cầu | Không đổi Firebase/auth protocol nếu không cần |
| backend/src/sketch2life/application/services/be1_runtime.py | Application policy/age validation | Không sửa age policy ngoài 36–120 |
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py | Canonical assignment path, class/profile authorization và synthetic-only guard | Không dùng route cũ làm alias mới; không cho REAL |
| backend/src/sketch2life/interfaces/http/routers/be1_records.py | Chỉ khi Parent/Teacher record behavior trong allowlist phụ thuộc trực tiếp | Mỗi thay đổi phải gắn M2-AT |
| backend/src/sketch2life/interfaces/http/routers/be1_common.py | Chỉ nếu cần làm đồng nhất denial mà không đổi ranh giới BE1 ngoài scope | Chốt exact denial contract trước |
| backend/src/sketch2life/interfaces/http/be1_runtime.py | Chỉ nếu cần inject Parent runtime/service | Không khởi tạo provider hay external client |
| backend/src/sketch2life/interfaces/http/app.py | Mount router Parent sau khi source wiring được xác nhận | Không đổi route khác hoặc profile mặc định |
| backend/alembic/env.py | Chỉ nếu F-9 được owner duyệt và Parent metadata cần được nạp | Không tự sửa graph; không đổi target DB logic |

Không có file model/migration BE1 nào trong candidate-edit list vì F-8 không cho migration/chỉnh bảng hiện hữu. Nếu chính sách đòi sửa schema BE1 hoặc constraint để đảm bảo invariant, dừng và xin Task Approval/scope mới.

### 6.3. New files — tên ứng viên chưa xác minh, chưa được phép tạo

| Path ứng viên | Mục đích | Trạng thái |
|---|---|---|
| backend/src/sketch2life/domain/parent_profile.py | Parent profile rules/value objects | Chưa xác minh |
| backend/src/sketch2life/application/ports/parent_profiles.py | Parent persistence/application port | Chưa xác minh |
| backend/src/sketch2life/application/services/parent_profiles.py | Parent profile use cases | Chưa xác minh |
| backend/src/sketch2life/contracts/schemas/parent_profiles.py | Request/response schemas | Chưa xác minh |
| backend/src/sketch2life/infrastructure/persistence/parent_models.py | Parent-owned tables metadata | Chưa xác minh |
| backend/src/sketch2life/infrastructure/persistence/parent_repository.py | Parent repository | Chưa xác minh |
| backend/src/sketch2life/interfaces/http/routers/parent_profiles.py | Parent profile routes | Chưa xác minh |
| backend/alembic/versions/20261107_m2_parent_profiles.py | Additive Parent migration; chỉ nếu F-9 cho phép | Chưa xác minh; không chạy |
| backend/tests/unit/test_m2_parent_profile_service.py | Parent service unit tests | Chưa xác minh |
| backend/tests/contract/test_m2_parent_teacher_routes.py | Contract/role/route tests | Chưa xác minh |
| backend/tests/integration/test_m2_s1a_postgres.py | Target-specific PostgreSQL acceptance | Chưa xác minh |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_K4_SCHEMA_SOURCE_RECONCILIATION_20261107.md | K4 read-only reconciliation evidence | Chưa xác minh |

Tên này chỉ là đề xuất cụ thể để review; final approval phải xác nhận path từng file, phân biệt file được tạo/sửa, hash của mọi file đã tồn tại và các dependency mới. Không tự đổi tên hay tạo file phụ.

### 6.4. Exclusions

Không sửa .env, secret, credentials, Docker/Compose, SRS, DTR, roadmap, B0 plan, Draft 1–10, DECISIONS.md, STATUS.md, CONTEXT.md, SOURCE_REGISTER.md, TASK_APPROVAL.md, ledger, FEAT-064, database sketch2life, các bảng BE1/Core/Story hiện có, các test fixture có thể tạo/xóa DB khác, child_age.py, StoryRun-lite, AI Jobs, migration legacy, OpenAPI assistance routes hoặc bất kỳ path nào không liệt kê ở §6.2–§6.3.

## 7. Hành vi route và invariant đề nghị

### 7.1. Identity, roles và tenant

- Identity đến từ principal đã xác minh; client không được tự chọn owner, organization hoặc quyền.
- school_admin chỉ được thao tác tổ chức/lớp/assignment trong scope hiện hành; role “Admin tổ chức”/“School Manager” và tên trong các mục SRS không hoàn toàn nhất quán. D-148 là nguồn cho code school_admin và scope.
- POST /v1/classes/{class_id}/assignments chỉ là operation Admin theo F-1; route Teacher profile chỉ cho Teacher được phân công.
- Platform Admin, Operator và Admin nội dung bị từ chối trên năm route nền theo M2-AT-01; Admin nội dung trong SRS v2.7 là permission, không phải role mới.
- Với không có assignment, class không tồn tại, class thuộc tenant khác và org_id không được phép, denial không được lộ existence/content. Organization của class phải được server suy ra từ class record; không nhận tenant authority từ header/claim do client gửi.
- Không có grant/share trong S1a; cross-role access ngoài owner scope bị deny.

### 7.2. Teacher và tổ chức

- Ba operation: tạo class; gán Teacher theo canonical route; tạo Teacher-managed profile/enrollment qua route Teacher.
- school_admin bị deny trên Teacher profile route (F-4).
- Invariant là chính xác một Teacher active phụ trách lớp (F-2). Schema hiện có unique assignment theo organization/subject/class/role, nhưng không ép một Teacher active duy nhất trên mỗi class. Cách đảm bảo đồng thời/race-safe và xử lý Teacher thứ hai cần owner chốt; không được giảm yêu cầu thành “không quá một” nếu direction là “chính xác một”.
- Không sửa schema BE1 trong S1a. Nếu không thể chứng minh invariant qua ứng dụng với schema hiện có thì dừng, không tuyên bố đạt.

### 7.3. Parent profile và tuổi

- Parent là owner duy nhất qua principal đã xác minh; Parent profile tách khỏi be1.managed_profiles. Không tạo FK chéo owner.
- POST tạo hồ sơ tổng hợp; GET chỉ trả profile của owner; PATCH ghi revision bất biến mới và cập nhật current revision theo contract được duyệt. Không có route xóa trong S1a.
- Logical tables theo DTR v2.3 là parent.child_profiles và parent.profile_revisions. Revision có unique (parent_profile_id, revision_no), tuổi 36–120 tháng, không lưu ngày sinh chính xác; age_band_ref/version còn cần nguồn/catalog có version và null không được tính là NFR-38/AC-65 đạt.
- S1a synthetic profile dùng data origin vật lý SYNTHETIC_DEV và consent refs NULL; contract mapping với tên SYNTHETIC_TEST trong SRS phải được ghi, không đổi enum DB trong S1a.
- REAL và LEGACY_UNCLASSIFIED bị từ chối. Cơ chế chặn route REAL hiện hữu phải được chốt trước khi thực thi. Không có đường tạo hồ sơ REAL nào được phép đi qua phạm vi S1a.
- Ràng buộc synthetic: child_id có prefix synthetic-, display_name có prefix Synthetic , age_source bằng SYNTHETIC_FIXTURE. Không gọi đây là consent thật hay synthetic-only proof cho DB sketch2life.

## 8. Acceptance matrix và test đề xuất

Chỉ các acceptance test được owner tick/chấp nhận trong Task Approval cuối mới thuộc exit gate S1a. Route/persistence tests phải dùng app composition, authentication, dependency wiring và PostgreSQL target thật; không monkeypatch _build_child_binding hoặc override dependency cần kiểm. Test không tự chạy Alembic hay tạo/xóa database.

| Test | Requirement / behavior | Tầng và test path đề xuất | DB cần? | Điều kiện |
|---|---|---|---|---|
| M2-AT-01 | Đúng/sai role và scope trên năm route; Admin nội dung, Platform Admin, Operator bị deny; không grant thì không có cross-role read; error không rò metadata | Unit/service + contract + backend/tests/integration/test_m2_s1a_postgres.py | Có cho route/persistence | Denial/error envelope phải ghim trong approval; route wiring thật |
| M2-AT-02 | Không assignment, class missing, cross-org/class mismatch và org_id không được phép có cùng denial/status/shape; server suy org từ DB record | Unit matrix + backend/tests/integration/test_m2_s1a_postgres.py | Có cho route | Không đọc lộ existence; test cả org id không tồn tại |
| M2-AT-03 | 35/36/120/121: 36 và 120 hợp lệ; giá trị mới 35/121 bị từ chối ở application; hàng cũ giữ nguyên; không dựa vào DB CHECK 36–155 | backend/tests/unit/test_m2_parent_profile_service.py, backend/tests/contract/test_m2_parent_teacher_routes.py, integration | Có cho persistence | Không dùng child_age.py; không đổi DB check BE1 |
| M2-AT-04A | Admin tạo class/assignment; Teacher bị deny trên Admin operation; capacity chỉ dùng mã nếu contract có; ca Teacher thứ hai chứng minh invariant chính xác một active | backend/tests/integration/test_m2_s1a_postgres.py | Có | Owner phải chọn reject hay transfer khi có Teacher active; concurrency/race-safe |
| M2-AT-04B | Assigned Teacher tạo profile/enrollment; unassigned/cross-tenant/Admin bị deny; response không lộ dữ liệu tenant khác | backend/tests/integration/test_m2_s1a_postgres.py | Có | Authentication và wiring thật |
| M2-AT-05/06/07 | Share, grant/revoke, consent và Admin permission policy | Không chạy trong S1a | Không | S1b DEFERRED; NOT RUN, không tính vào PASS |
| M2-AT-08/09 | StoryRun/AI Job lifecycle và assistance request/cancel | Không chạy trong S1a | Không | S2 chưa mở; route test ngoài năm route nền |
| M2-AT-10 | Locale vi-VN, age 36/120, revision serialize/persist/read; profile cũ 121–155 không đủ điều kiện tạo StoryRun | backend/tests/unit/test_m2_parent_profile_service.py, contract và integration | Có cho persistence | Theo D-151 C2, kiểm service/contract ở S1a; không gọi route /v1/story-runs hoặc route S2 |
| M2-AT-11 | Từ chối REAL/LEGACY_UNCLASSIFIED; cho phép đúng fixture synthetic với SYNTHETIC_DEV, NULL consent refs và synthetic markers | backend/tests/integration/test_m2_s1a_postgres.py | Có | Cơ chế block REAL và API↔DB origin mapping phải được owner chốt |

### 8.1. D-151 C1–C5 carry-forward

- C1: không dùng Alembic upgrade heads làm mặc định; Draft 10 §5.3 có lỗi biên tập/truncated text. F-9 và exact command phải được giải quyết trong Task Approval, không dùng lỗi đó để suy ra quyền migration.
- C2: M2-AT-10 tại service/contract/persistence; không gọi StoryRun route trong S1a.
- C3: placeholder POST /cancel là {id} theo SRS §21.2; ngoài S1a, giải quyết trong Task Approval S2.
- C4: S3 gate chỉ áp dụng acceptance được owner duyệt trong Task Approval S1a; không mặc định AT-11/AT-04A consent/cardinality hoặc AT khác đã duyệt.
- C5: chờ Task Approval S2 quyết liệu quy tắc năm route nền M2 có áp dụng route S2 hay không.

## 9. Exit criteria, stop gates và hiệu lực

S1a chỉ có thể đóng sau khi owner có Task Approval cuối, review độc lập ACCEPTED hoặc verdict mà owner chấp thuận, K4 complete, F-9 và các mục blocking ở §10 được quyết định, toàn bộ test được duyệt chạy thật và đạt, kết quả PostgreSQL được xác minh trên đúng target, evidence/status được lập và owner ra quyết định đóng. Test SKIPPED, NOT RUN, timeout, runner output thiếu summary hoặc owner report chưa được reviewer kiểm không tính là PASS.

Stop ngay nếu: branch/HEAD/pin lệch; target DB khác tên/instance/port/user/version; host không loopback; DB sketch2life bị chỉ định; target có row không synthetic/không rõ nguồn; K4 còn mismatch; Alembic graph/baseline chưa được owner quyết; lệnh có thể ALTER/DROP/RENAME bảng hiện có; cần sửa schema BE1; không thể ép đúng một Teacher active với schema hiện tại; denial lộ tenant existence; route contract chưa rõ; REAL path chưa bị chặn; test fixture tự migration/reset/drop DB; timeout/crash/setup error; credential xuất hiện trong log; hoặc cần file/path ngoài allowlist.

Không tự retry, chuyển instance/port, đổi env target, chạy command khác để lấy verdict, mở quyền rộng hơn, chạy test trên database sketch2life, tạo role mới, thêm route alias hoặc đổi yêu cầu để làm test xanh. Giữ DB sau timeout và xin quyết định owner.

**Hiệu lực:** Draft 1 không cấp quyền. Sau khi owner hoàn tất các ô, một bản Task Approval cuối phải được review độc lập, có hash/path allowlist chính xác, lệnh/ceiling/timeout đã chốt và owner approval rõ ràng. Mỗi phiên triển khai và review là hai phiên mới, độc lập; không dùng subagent làm reviewer. Không stage/commit/push nếu không có chỉ thị riêng.

**Không mở:** S1a hiện vẫn chưa mở; S1b, S2, S3, M3–M6 vẫn đóng; không có implementation approval; OWNER_MODAL_CALL_APPROVED=NO giữ nguyên.

## 10. Owner fields và quyết định còn mở

| Trường owner phải xác nhận/điền | Trạng thái hiện tại | Vì sao cần trước approval cuối |
|---|---|---|
| Chấp nhận chính thức F-1, F-2, F-4, F-6, F-7, F-8 | Hướng đã nêu trong hội thoại; chưa ghi hồ sơ | Chuyển hướng trao đổi thành acceptance cụ thể |
| F-2: xử lý gán Teacher thứ hai | Chưa quyết reject hay transfer; response chưa chốt | Cần xác định invariant và test deterministic |
| F-3/F-5 mapping | D-148 mục 5–7 đã quyết hướng; nhãn F do coordinator gán | Xác nhận cách dẫn chiếu không tạo mã quyết định mới |
| F-6: route/phạm vi chặn REAL | Hướng deny đã nêu; cơ chế và mức ảnh hưởng route cũ chưa quyết | Tránh vô hiệu hóa hành vi BE1 ngoài scope |
| F-7: SYNTHETIC_TEST ↔ SYNTHETIC_DEV | Giữ DB enum và ghi mapping; API representation chưa chốt | Cần contract nhất quán, không migration enum |
| Age provenance / age_source | Tuổi 36–120 chốt hướng; provenance semantics còn mở | M2 cần biết nguồn, authored_by, revision behavior |
| Error code/shape cho tenant denials | Cùng denial đã định hướng; exact code/HTTP contract chưa chốt | Không tạo response contract mới trong test |
| F-9 Alembic target bootstrap | OPEN | Chọn baseline/migration strategy; không command write trước đó |
| K4 evidence path/hash | Chưa tạo, path ứng viên ở §4 | Ghim artifact và allowlist trước launch |
| DB target attestation | Owner báo DB mới 117 bảng/0 hàng; chưa xác minh kết nối | Pin service, version, port, current_user, DB owner, schema/revision, row count |
| Data provenance và quyền | Schema-only dump hash có owner report; postgres privilege chưa xác minh tối thiểu | Xác nhận DB không chứa app rows và owner chấp nhận privilege |
| Restore/rollback | Restore trial của dump mới chưa được xác minh | Cần kế hoạch khôi phục target schema-only mà không đụng sketch2life |
| Exact executable/env guard | Chưa có test fixture/guard mới | Chứng minh test chỉ dùng sketch2life_m2_s1a, không dùng BE1_TEST_DATABASE_URL mặc định |
| Command/time ceilings | Các con số tại §3 là đề xuất | Owner phải xác nhận từng command, số lần và timeout |
| Mypy baseline | D-144 §9.6 còn outstanding; S0 owner chọn NOT RUN | Quyết định riêng có đưa vào S1a hay để phase khác; không có command trong draft này |
| D-151 C1–C4 | Carry-forward theo §8.1 | Chốt câu chữ/ranh giới khi final approval |
| D-151 C5 | Hoãn tới Task Approval S2 | Không quyết trong S1a |
| Exact file allowlist và hash | Candidate ở §6; path mới chưa xác minh | Final approval phải phân biệt read-only/edit/new và pin hash |
| Review và owner authorization | Chưa có | Draft này chỉ trở thành approval sau independent review và lệnh duyệt rõ ràng |

**Approval basis:** CHƯA ĐIỀN — owner quyết định khi xem xét bản cuối.
**Owner signature / date:** CHƯA ĐIỀN.
**Final approval hash:** CHƯA CÓ.
**OWNER_MODAL_CALL_APPROVED:** NO.
