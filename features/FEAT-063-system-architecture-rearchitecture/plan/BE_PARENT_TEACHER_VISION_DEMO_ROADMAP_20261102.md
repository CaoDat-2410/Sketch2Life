# Lộ trình BE Parent/Teacher và demo Vision

- Ngày lập: 2026-11-02; rà soát theo review độc lập vòng 1–3 ngày 2026-11-03, Asia/Ho_Chi_Minh.
- Trạng thái: **OWNER-ACCEPTED LÀM BASELINE LẬP KẾ HOẠCH**. Dùng SRS v2.3-draft hiện có làm baseline cho M2–M6 và giữ nguyên nội dung SRS. Đây không phải approval triển khai, không thay thế SRS hoặc plan task riêng từng mốc.
- Ưu tiên ban đầu là BE demo nhận ảnh synthetic và trả kết quả Vision qua API để người phụ trách UI ghép demo. Mốc 1 đã được review chấp nhận trong phạm vi synthetic local; không còn là việc đang chạy.
- Phạm vi SRS: Parent/Teacher mới dùng ảnh tranh giấy; tài liệu SRS v2.3 vẫn là draft. Demo là một lát cắt, không chứng minh toàn bộ luồng Parent/Teacher hoặc sẵn sàng cho dữ liệu trẻ thật.
- Mốc 2–6 đã được owner chấp nhận làm baseline lập kế hoạch theo SRS v2.3-draft; chưa có approval triển khai. Trước mỗi mốc cần plan, acceptance, nguồn dữ liệu/migration và approval riêng. M2 và M6 phải được chia subphase trong plan riêng trước khi launch goal.

## Sáu mốc BE

| Mốc | Kết quả cần hướng tới | B0–B13 đưa vào mốc | Tiêu chí hoàn thành ở mức kế hoạch |
|---|---|---|---|
| 1. Vision demo — **xong** | StoryRun-lite S1→S2: ảnh synthetic → API BE → admission → Vision loopback → API trả trạng thái/kết quả. | Không gắn task B0–B13. | Review vòng 3 ACCEPTED cho demo synthetic local. Đây không phải production approval hay bằng chứng gọi Modal sau review-fix. Xem `evidence/MILESTONE1_INDEPENDENT_REVIEW_ROUND3_20261103.md`. |
| 2. Nền Parent/Teacher | Danh tính, tenant/role, hồ sơ và consent; owner/scope, job, asset, revision, persistence và lifecycle nền. | B3 (manifest mới, owner/sign-off); B4b (consent chỉ sau OI-05..08; trước gate M2 từ chối `REAL`/`LEGACY_UNCLASSIFIED`); phần nền B6/B7/B10; B5 chỉ nếu còn requirement receipt legacy. | Trước migration M2: đối soát schema vật lý với Alembic trên DB task-owned và ghi disposition cho 58 hàng synthetic cũ trong `sketch2life`; không dọn DB dùng chung nếu chưa được duyệt. Ghi mypy baseline đã biết và không thêm lỗi trong scope. Trước dữ liệu thật: deny-by-default, revoke, restart/idempotency, lifecycle tối thiểu và schema owner. |
| 3. Đầu vào hoàn chỉnh | Parent input text/voice/image, transcript/Vision revisions và người lớn xác nhận/sửa chủ thể/context. | Phần input B9; Parent line-sketch B13 theo Q146 đã trả lời, nếu owner xếp lịch và các model/safety gates đạt. | API có revision/idempotency; từ chối sai scope/stale; xác nhận subject mismatch trước re-suggest. Trước M3: synthetic POC và owner chọn model/version cho ASR/VLM cùng license/cost/safety/retention/capacity gate. Line-sketch hoãn không chặn capture/Vision chính. |
| 4. Story/storyboard | Story có cấu trúc, revision, rewrite có giới hạn và adult approval. | Phần story/script/rewrite còn lại của B9. | Có acceptance cho revision/rewrite, idempotency và adult approval. Script-following theo lesson là tùy chọn, không thay tranh của trẻ. Trước M4: synthetic POC và owner chọn model/version cho Story LLM cùng license/cost/safety/retention/capacity gate. Điều kiện “không video trước script approval” được kiểm tại cổng vào/dispatch M5. |
| 5. Video | Tạo reference/scene, consistency, ghép, TTS/phụ đề, safety và playback riêng tư. | B11; Parent quota/usage admission + AI compute reservation từ B10/B12. | M5 phải có Billing `video_quota_grants` và append-only `video_quota_usage` cho Parent scope: tháng `Asia/Ho_Chi_Minh`, included trước rồi top-up FIFO, concurrency AT-06/AT-09, request/run cap BR-11. AI Policy quản lý compute reservation lease/release/reconcile, không giữ product quota. Cùng idempotency key; quota admission + reservation receipt + đúng một usage unit phải có trước accepted/dispatch theo BR-38. Từ chối thì không accepted/usage/job/dispatch. Có synthetic model/GPU/cost POC và test từng stage. |
| 6. Hoàn thiện sản phẩm | Teacher lesson/occurrence/sample, organization/roster, sharing/moderation, history/feedback, commerce/billing nâng cao, quan sát và tích hợp. | Phần còn lại B6/B7/B10; B12 vẫn chạy xuyên mốc 2–6; phần Teacher/org/roster/billing B13; B5 chỉ nếu owner xác nhận cần receipt legacy. | Mở rộng quota sang Teacher/school scope, quota summary và commerce: price/invoice/payment/top-up/subscription/capacity. Hoàn tất purge/retention đa miền, NFR và quyết định dữ liệu thật/production. Không để M6 là nơi đầu tiên có grant/usage admission hoặc compute gate. |

**Cách hiểu ID cũ:** B0a/B1/B2 là hồ sơ đối chiếu/quyết định đã có, không chạy lại như goal; B0b còn thiếu bằng chứng lịch sử nhưng không chặn. B4a thuộc eligibility canvas cũ; B8 là smoke route demo cũ. B9 tách input M3 và story/script M4; B10 có nền idempotency/job ở M2, Parent quota/usage/compute admission ở M5 và commerce/Teacher-scope ở M6; B11 ở M5; B12 là gate xuyên M2–M6; B13 có thể đưa Parent line-sketch vào M3 theo Q146 nếu owner xếp lịch và gates đạt, còn Teacher/org/roster/capacity ở M6. B5 không được tính lặp ở M2/M6: chỉ giữ M2 nếu receipt legacy còn yêu cầu; nếu không, owner ghi disposition. B6/B7 phải đối chiếu từng requirement Rev36 và re-plan. Backlog B0–B13 là hồ sơ lịch sử; roadmap này là mapping hiện hành cho sáu mốc. Plan B0–B13 hiện có mismatch provenance và không được dùng làm authority cho goal mới đến khi owner xác nhận lại đúng bytes hoặc duyệt addendum. Đây là phân bổ đề xuất, không phải approval triển khai.

## Trạng thái hiện tại và thứ tự tiếp theo

1. **Mốc 1: COMPLETE / ACCEPTED** cho synthetic local demo theo review độc lập vòng 3. Review dựa trên evidence đã lưu, không chạy lại test; Vision của review là loopback stub. Một Modal live smoke trước đó có evidence riêng, nhưng review Mốc 1 không xác nhận live sau review-fix hoặc production. UI do người phụ trách khác ghép.
2. **A1: COMPLETE; A2: ACCEPTED / COMPLETE** trong phạm vi plan/addendum A2, theo closeout local `features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md`. Bản closeout này và snapshot liên quan đang local-only, chưa có trên remote mà phiên cloud review quan sát; không dùng dòng trạng thái lịch sử dưới đây làm trạng thái mới nhất.
3. Chuỗi FEAT-064 A2→B1→B2 được ghi ở `features/FEAT-064-current-flow-modal-vision-dev/plan/FEAT064_A2_B1_B2_SEQUENTIAL_GOAL_20261103.md`, SHA-256 `D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A`. Tài liệu là kế hoạch/goal riêng và có thể tạm được owner ưu tiên trước M2–M6; trạng thái phase đang chạy phải lấy từ active implementation thread, không suy ra từ header hoặc closeout cũ. Chuỗi này không phải sáu mốc Parent/Teacher và không thay thế launch riêng cho từng phase.
4. **Mốc 2–6:** owner chấp nhận roadmap này làm baseline lập kế hoạch theo SRS v2.3-draft hiện có, giữ nguyên nội dung SRS; thứ tự Parent trước Teacher theo §8.1. Chưa có approval triển khai riêng cho bất kỳ mốc nào. Không suy diễn trạng thái triển khai từ hoạt động của chuỗi FEAT-064. M2/M6 cần plan chia subphase; trước M3/M4 cần synthetic model POC và quyết định owner về model/version cùng các gate liên quan. Lịch Parent line-sketch, optional lesson access và provenance B0 vẫn là gate; không tự suy đoán.

### Ràng buộc Mốc 1 và giới hạn còn lại

- Mốc 1 dùng binding riêng cho ảnh chụp; không giả provenance checkpoint canvas hoặc thay đổi hành vi canvas đã chấp nhận.
- Thứ tự worker/guard/transport/bridge/ledger và crash/restart được kiểm soát theo hợp đồng A1; sau SENT/UNKNOWN không tự gửi lại. M2 phải đánh giá lại nếu thêm worker/process hoặc durable AI Jobs.
- Admission, hash ảnh gốc/hash ảnh gửi VLM, artifact storage và scope truy cập của demo không được xem là thiết kế production; debt cần được đóng trong plan có liên quan trước dữ liệu thật.
- M1 chưa tích hợp `AiJobService`; đây là giới hạn demo cần map ở M2. Việc sửa subject phải tạo revision theo contract; không âm thầm thay kết quả đã được người lớn xem.
- Identity trong demo chỉ là synthetic/local. Identity/consent Parent thật và production API contract thuộc các mốc sau; UI không thuộc scope BE.
- `/health` chỉ chứng minh app Modal trả lời, không chứng minh model, token hoặc transport A1. Smoke FEAT-061 ngày 29/10 dùng luồng demo cũ; ghi chép ngày 01/11 không có log thô và không chứng minh A1 live.
- Mốc 1 chỉ là synthetic local demo. Không suy rộng thành danh tính Parent thật, dữ liệu trẻ thật, sản phẩm production hoặc xác nhận Modal live sau review-fix.

## Trạng thái lịch sử tại lần ghi 2026-11-02 — đã được cập nhật

Các dòng dưới đây ghi nhận trạng thái khi lập roadmap, không phải trạng thái hiện tại. A1 lúc đó được ghi COMPLETE; A2 lúc đó còn tạm dừng và chưa review. A2 sau đó được review độc lập ACCEPTED/COMPLETE theo closeout local ngày 2026-11-03, được dẫn ở phần trạng thái hiện tại. Closeout đó vẫn local-only nên phiên cloud chỉ đọc remote refs không thể quan sát nó.

Các ghi chú cũ về teardown, hàng synthetic còn lại, B1/B2 canvas và `origin/dev` là ảnh chụp tại thời điểm 2026-11-02; không dùng chúng để kết luận trạng thái hiện nay. Tên B1/B2 trong backlog canvas, Goal FEAT-064 A2→B1→B2 và sáu mốc Parent/Teacher là ba phạm vi lập kế hoạch riêng.

## Kiểm tra môi trường ban đầu

Quan sát ngày 2026-11-02: `backend/.venv` dùng Python 3.12.10; FastAPI TestClient thử app tối thiểu trả OpenAPI 200; Pillow xử lý PNG synthetic trong bộ nhớ; A1 transport/ledger import được. PostgreSQL 17/18 đang chạy và TCP loopback 5432 mở, nhưng chưa xác minh database/schema/cleanup. Docker client có nhưng engine không kết nối được. Modal CLI không có trên PATH hoặc trong `backend/.venv`; môi trường khác chưa kiểm. Một số dependency backend khai báo còn thiếu; cần đối chiếu phạm vi goal trước khi cài. Chưa test app Sketch2Life thật hay gọi Modal trong lượt kiểm này.

## Nguồn và cách cập nhật

- SRS v2.3-draft: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` §§5–8.1, 11, 13, 14.1, 19, 22, 29, 31; đặc biệt BR-38, BR-47–60, FR-PL-01–25, NFR-34–38, FR-P-11/FR-AI-15 và AT-18/19. Tài liệu chưa có sign-off.
- DTR v2.3-draft: `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` §§1, 5.6; working-copy CRLF SHA-256 `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22`; cùng nội dung chuẩn hóa LF cho SHA-256 `201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2`. Hash khác nhau do line ending; không có bằng chứng khác nội dung trong phép đối chiếu này.
- Phân bổ backlog: `plan/B0_B13_SIX_MILESTONE_REDISPOSITION_PLAN_20261102.md` và `evidence/B0_B13_SIX_MILESTONE_REDISPOSITION_REPORT_20261102.md`. Current plan bytes SHA-256 `773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A`, khác nội dung với hash `03AEA...B582` ghi trong report (không phải line-ending-only). Bytes lịch sử chưa tìm thấy; owner phải xác nhận lại plan hiện tại hoặc duyệt addendum trước khi plan này được dùng làm authority.
- Quyết định pilot: `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md`; sổ `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md`.
- Evidence smoke BE demo cũ: `features/FEAT-061-modal-qwen-vl-endpoint/evidence/BACKEND_DEMO_MODAL_SMOKE_20261029.md`; không phải bằng chứng cho flow mới hay A1 live.
- Cập nhật kế hoạch/trạng thái có dẫn nguồn sau từng quyết định hoặc review; không sửa hồ sơ approval lịch sử. Khi thông tin mới mâu thuẫn, ghi rõ thời điểm và nguồn mới thay vì âm thầm tuyên bố hoàn tất.

## Disposition B0–B13

Chi tiết trạng thái lịch sử từng ID vẫn ở `plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md`, phần “Disposition sau khi chuyển sang StoryRun-lite”. Bảng ở đầu roadmap là phân bổ đề xuất hiện tại. SRS vẫn là draft; việc đổi kế hoạch không xóa yêu cầu SRS hoặc tự cấp approval triển khai cho Mốc 2–6.

## Cổng traceability và acceptance cho Mốc 2–6

### Traceability SRS ở mức roadmap

| Mốc | Nhóm requirement được giao ở mức kế hoạch | Ghi chú / gate |
|---|---|---|
| 2 | FR-PL-01/02/07/08/25; BR-48/49/57/58; NFR-34/36/38; identity, role, tenant, profile grant/revoke, age provenance, owner/job/lifecycle nền. | Trước migration: đối soát physical schema/Alembic và disposition cho 58 hàng synthetic A2 còn trong shared `sketch2life`, trên DB task-owned hoặc theo quyết định riêng; không tự dọn DB dùng chung. Ghi mypy baseline exception và không thêm lỗi mới. Chốt data owner/schema convergence; quyền/revoke phủ API, asset, token/cache và job. |
| 3 | FR-PL-19; FR-P-11/FR-AI-15 và BR-46 cho Parent line-sketch theo Q146 đã trả lời, nếu owner xếp lịch; BR-54. | Subject correction thuộc input. Parent guide tùy chọn, chỉ topic/độ khó generic; trước M3 cần synthetic POC và owner chọn model/version cùng license/cost/safety/retention/capacity gates. Teacher Sketch Deck thuộc M6. |
| 4 | FR-PL-17 và phần story/script của BR-56; các yêu cầu Parent story/revision trong §§5–7/19/22. | Lesson script-following tùy chọn, cần lesson access gate nếu bật. Đường no-lesson là baseline ban đầu theo SRS; không thay ảnh của đúng trẻ. Synthetic fixture không chứng minh authorization. Trước M4 cần synthetic POC và owner chọn model/version cho Story LLM. |
| 5 | FR-PL-16/18; BR-11/38/55/56; video pipeline trong §§5–7/19/22; privacy/safety/observability NFR và §29. | M5 sở hữu Parent-scope Billing grants + usage ledger, quota admission và AI Policy compute reservation trước accepted request/dispatch. Included-current-month-first rồi top-up FIFO; tháng `Asia/Ho_Chi_Minh`; concurrency AT-06/09 và request/run cap BR-11. `video_quota_usage` ghi đúng một unit idempotent trước dispatch sau các receipt cần thiết; request bị từ chối không tạo usage/accepted job. M6 mở rộng commerce và Teacher/school quota. |
| 6 | FR-PL-03–06, 09–15, 20–24; BR-47–54, 58–60; NFR-34–38; Teacher lesson, occurrence/sample, sharing, moderation, history/feedback, billing/ops. | FR-PL-15 Teacher portion ở đây; NFR/BR là acceptance xuyên miền, không chỉ một dòng ở M6. |

Những ID ở bảng trên là mapping mức roadmap, không thay cho crosswalk requirement→API/table/owner/AT. Mỗi phase plan phải đưa ra crosswalk chi tiết, testable acceptance criteria và stop gate trước khi được owner phê duyệt. M4 chỉ hoàn tất script review/approval; quy tắc không tạo video trước approval được thực thi và nghiệm thu ở M5 entry/dispatch gate.

### Parent-first / Teacher-later — theo baseline SRS §8.1 đã được owner chấp nhận

SRS §8.1 sắp Parent vertical trước Teacher vertical; owner xác nhận dùng baseline SRS hiện có nên roadmap giữ đúng thứ tự đó. M2–M5 kiểm chứng Parent vertical end-to-end; M2 có thể xây shared identity/tenant/profile contracts nhưng không tuyên bố Teacher flow hoàn tất. M6 mở Teacher lesson/occurrence/sample flow trên các nền tảng đó. Mỗi mốc vẫn cần dependency, acceptance và approval triển khai riêng; muốn đổi thứ tự phải có quyết định/addendum riêng.

SRS cho phép Parent run không có lesson. Do đó M4/M5 ban đầu có thể nghiệm thu no-lesson path; script-following theo lesson ở M4 và activity list sau video ở M5 chỉ được bật khi quyền đọc hiện hành và dependency qua Lesson đã sẵn sàng. Nếu muốn đưa lesson access lên sớm, phase plan phải xin approval cho phần quyền tối thiểu (PUBLIC hoặc grant chia sẻ hợp lệ), revoke/unpublish check và cấm public fallback. Synthetic lesson fixture chỉ kiểm tra lineage/flow, không chứng minh quyền truy cập. D-114 vẫn yêu cầu ẩn activity list khi lesson bị revoke/unpublish mà không làm đổi video.

### Lifecycle và schema convergence

- M2 phải định nghĩa state/owner-lock/cancel/delete contract tối thiểu, gồm cạnh tranh, restart và quyền sở hữu job; ghi debt D-127: hủy sau PREPARATION_REVIEW chuyển `DELETE_PENDING`, nhả active owner nhưng giữ result/assets/receipts. M6 hoàn thiện purge/retention/audit cùng tác động qua asset, history và quota; không ghi “delete hoàn tất” chỉ dựa trên `DELETE_PENDING` hoặc owner lock release.
- Mỗi mốc tự xử lý cancel, kết quả đến muộn và purge hoặc ghi rõ debt cho artifact/job mà mốc đó tạo. Cancel trong khi video job chạy và chặn late result là trách nhiệm M5, không đợi M6.
- Theo BR-39, adult-wait bắt đầu khi không còn AI job và cần thao tác người lớn. Tại +144h tạo đúng một inbox reminder (push/email best-effort theo chính sách SRS); tại +168h `VIDEO_READY` → `COMPLETED`, các trạng thái adult-wait khác → `ABANDONED`, nhả owner lock và giữ nội dung tới khi bị xóa. Phase sở hữu state phải kiểm tra timer/dedupe/restart; hệ thống notification cross-cutting không làm lỗi gửi đổi trạng thái.
- StoryRun-lite Mốc 1 là schema demo riêng, không được xem là đã khớp DTR. Trước M2 migration, lập mapping giữa demo `storyrun_upload_sessions` và target `core.upload_sessions`, `story.runs.run_id` và target `story.runs.story_run_id`, cùng owner columns/asset references. A2 closeout còn ghi 58 synthetic rows trong shared `sketch2life`, physical schema chưa đối soát Alembic history và một mypy protocol baseline issue. Trước migration M2 phải có task-owned DB cô lập hoặc quyết định an toàn riêng, reconciliation physical/Alembic, disposition dữ liệu và baseline mypy; không tự xóa/reset shared DB. Phải có kế hoạch tương thích/di trú và giữ nguyên lịch sử; chưa sửa DTR tại roadmap này.

### Cổng xuyên mốc

B12 được áp dụng cho từng Mốc 2–6: privacy, authorization, safety, idempotency, stale/replay, observability, restart/recovery và failure mapping. Mỗi phase chỉ đóng khi có AC/AT gắn source IDs, evidence, kiểm thử phù hợp, giới hạn dữ liệu được ghi rõ và review độc lập ACCEPTED. Mốc sau cần launch/approval riêng; umbrella roadmap không phải blanket approval. M2/M6 plan phải chia subphase và scope kiểm chứng trước khi tạo goal triển khai.
