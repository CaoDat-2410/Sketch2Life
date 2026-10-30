# Backlog đề xuất: API hiện tại, SRS 2.3 và Modal

**Trạng thái: DRAFT — phục vụ BA/nhóm BE phân rã và review; không phải approval thực thi.** Đây là backlog điều phối, không thay thế hay sửa plan FEAT-063 Rev36, FEAT-064 hoặc các approval tương ứng. Mỗi task cần scope, owner, plan/contract, review và approval theo harness trước khi triển khai; các task live/DB/provider còn cần phạm vi thao tác được chấp thuận riêng. Không tự gán người thực hiện. Các ID dưới đây chỉ là nhãn trong tài liệu này, không phải mã feature mới.

## Mục tiêu và nguồn

Đối chiếu API hiện có với luồng Parent/Teacher một trẻ của SRS 2.3; xác định việc nền tảng, API và kiểm thử cần làm. Kết quả hoàn thành là BA/BE có thể nhận diện phụ thuộc và tạo task có thể nghiệm thu, không phải tuyên bố hệ thống đã đạt SRS hoặc production.

| Nguồn | Phạm vi và giới hạn |
|---|---|
| `API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md` | Bản được cung cấp ngoài repo, SHA-256 `56FC8BEA01360E11F73E45B2D43AC1897540B30BC8AE524CDE1ECEFACFBB1B88`. Cần lấy bản lưu có provenance và hai file evidence được catalog dẫn trước khi pin snapshot/commit. |
| [SRS 2.3 draft](../artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md), [data table register](../artifacts/DATA_TABLE_REGISTER.md), [decisions](../DECISIONS.md) | SRS/register chưa ký. Chênh lệch trong SRS phải giải quyết bằng crosswalk và quyết định được ghi lại. |
| [Plan backend Rev36](PLAN_REV36_BACKEND_SRS23_ALIGNMENT_20261029.md) | `AWAITING_APPROVAL`; S1/S2/S3 chỉ là nền tảng và chưa cho phép triển khai StoryRun hoặc pipeline AI. |
| [FEAT-064 plan](../../FEAT-064-current-flow-modal-vision-dev/plan/PLAN.md) | Pilot flow lớp học cũ là đề xuất riêng, chưa được phê duyệt triển khai; phải quyết định có làm hay không và thứ tự so với flow mới. |
| [FEAT-061 smoke demo trước merge](../../FEAT-061-modal-qwen-vl-endpoint/evidence/BACKEND_DEMO_MODAL_SMOKE_20261029.md) | Một lượt synthetic BE demo → Qwen3-VL Modal thành công trước merge; không chứng minh BE sau merge hay chất lượng mô hình. |

Catalog báo 135 operation được kê khai, gồm 124 operation mount trong snapshot Compose local trên 111 path và 11 candidate/fixture chưa mount. Trong 124: 56 BE1/classroom (bao gồm root health), 35 demo, 30 Lesson Library, 3 storage example phụ thuộc cấu hình. Con số này không phải 124 operation đã pass hay 135 API target của SRS. Rev36 nói 121 operation vô điều kiện theo baseline trước; 3 storage local có điều kiện có thể giải thích chênh lệch nhưng cần đối chiếu commit, profile và flags trước khi kết luận.

Catalog ghi API upload ảnh #59 pass ở trường hợp ảnh quá lớn bị từ chối 413; #60 understanding và #62 tạo session chỉ được ghi đã mount, chưa live-probe riêng. Hai file OpenAPI JSON và `EV-063-30` được liên kết trong catalog chưa tìm thấy tại checkout khi review; không coi lời mô tả trong catalog là evidence đã xác minh độc lập.

## Backlog để phân công

Mức effort chỉ để lập kế hoạch tương đối: **S** = một review cycle nhỏ; **M** = một lát có nhiều kiểm thử; **L** = cần tách plan/task và có phụ thuộc liên nhóm. Các mức không phải cam kết thời gian. Tất cả task ban đầu là **đề xuất/chưa bắt đầu**.

| ID | Kết quả cần giao | Phụ thuộc | Có thể chuẩn bị song song | Nghiệm thu tối thiểu | Effort / rủi ro |
|---|---|---|---|---|---|
| B0 | Xác minh catalog Rev37, OpenAPI JSON, `EV-063-30` và baseline nhánh/profile. | Không | B1, B2, B3 (review) | Có commit, profile, flags và hash cho snapshot; phân biệt mounted, probe, pass/fail/skip; giải thích hoặc ghi chưa rõ 121/124; đối chiếu từng link, không giả định file mất vĩnh viễn. | S; snapshot có thể không cùng commit. |
| B1 | Lập bảng API **giữ / sửa / mới / tạm giữ legacy** theo SRS và Rev37. | Catalog, SRS; hoàn thiện sau B0 | B2, B3 | Mỗi dòng có method/path hoặc contract target, actor, owner boundary, trạng thái, chứng cứ và task phụ thuộc; không gán operation demo/fixture thành SRS target chỉ vì tên giống. | M; SRS đang draft. |
| B2 | Hòa giải thứ tự hoạt động Parent/Teacher trong SRS/register. | Quyết định chủ task, review BA | B0, B3 | Crosswalk các đoạn BR-08/15, UC-02, state, pipeline, API và `story.runs`; ghi quyết định chính xác về input/state và ảnh hưởng. Quyết định trước đây đặt Parent sau video, Teacher pin một hoạt động trước video; không tự xóa đoạn mâu thuẫn. | M; chặn contract StoryRun phụ thuộc. |
| B3 | Chốt phân công và baseline migration/schema cho Rev36 và khả năng FEAT-064. | Quyết định chọn/không chọn pilot, owner xác nhận | B0–B2 | Có named owners, người review/cosign, manifest file và migration, graph hiện hành, thứ tự và policy consent/data-origin; phối hợp P4 theo ADR-0015; không gán mặc định toàn bộ BE/E2E cho P4. | M; file và schema giao nhau. |
| B4 | Đề xuất sửa contract consent BE1 cho đường hợp lệ, trong scope riêng. | B3, plan + approval phù hợp | B5; thiết kế B6–B7 | Tái hiện có kiểm soát: DB CHECK chỉ cho `pending`/`revoked`, code yêu cầu `effective`; có phương án và regression cho legal consent và các trường hợp từ chối, không tạo consent giả hoặc tắt guard. PostgreSQL chỉ dùng DB tạm sau approval. | M; sai consent có thể mở dữ liệu không hợp lệ. |
| B5 | Bảo toàn tương thích idempotency receipt cũ của lời mời/accept Parent Group. | Plan + approval phù hợp; dữ liệu fixture cũ | B4; chuẩn bị B6 | Tái hiện receipt trước nâng cấp thiếu `revision`, retry cùng key có response hợp lệ mà không thực thi lại tác dụng; kiểm tra key xung đột và revision/provenance. Bằng chứng hiện tại là review source, chưa xác nhận lỗi với DB thực. | M; response cũ có thể gây 500. |
| B6 | Rev36 S1: chuẩn bị fence có kiểm soát cho legacy. | B0, B3, các quyết định S1 và approval pin đúng plan cùng disposition | B7 sau khi phân file | Mặc định giữ hành vi; kiểm từng operation được duyệt, đặc biệt finish/completion/revoke/leave/rotate và POST mang nghĩa đọc; preserve auth, privacy, rollback và đường demo standalone. Không coi local flag là cutover. | M; cắt sai route có thể chặn an toàn/lớp học. |
| B7 | Rev36 S2/S3: nền tảng Parent identity/profile và AI-job target, additive. | B3, OD tương ứng, plan + approval; cơ chế phối hợp B4/B6 | Sau phân ownership, có thể tách thiết kế S2/S3 | Scope và migration theo Rev36; account scope, profile immutable, data-origin/eligibility fail-closed; tám target kind theo hợp đồng, giữ job legacy và chống downgrade. Kiểm cách ly tenant, migration upgrade/downgrade và CI; DB tạm cần approval, thiếu thì nghiệm thu BLOCKED. | L; migration nhiều nhánh và tương thích dữ liệu cũ. |
| B8 | Smoke lại **demo Vision → Modal** trên BE sau merge. | Quyết định phạm vi test, approval/live-call gate phù hợp, fixture synthetic; không phụ thuộc B4–B7 nếu chỉ test demo | B0–B7 khi không sửa file/runtime chung | Ghi commit/profile; tạo session, upload ảnh giả lập hợp lệ, gọi understanding, kiểm HTTP **và** trạng thái nghiệp vụ, model/revision, thời gian, chi phí và dừng serve; không gửi audio. Không xóa/tái dùng reservation marker đã tiêu thụ; không lộ secret. | S–M; call có phí, cold start/timeout, profile khác. |
| B9 | Thiết kế/tách task StoryRun, media và các gate người lớn. | B1, B2, B7 và approval từng plan | Chuẩn bị contract sau B2 | Versioned API/state cho một trẻ; ảnh, audio ≤2 phút, Whisper, transcript revision và xác nhận, VLM review, context allowlist được người lớn duyệt, story/storyboard và script confirmation. Không giả định `/v1/sessions` là StoryRun. | L; auth, provenance và dữ liệu trẻ. |
| B10 | Thiết kế/tách task quota, budget, jobs và vòng đời. | B1, B7; phối hợp B9/B11 | Thiết kế song song B9 | Đặc tả admission idempotent, budget/quota trước dispatch, scope, timezone Asia/Ho_Chi_Minh, deadline 6h, 144h/168h, retry/regeneration, cancel/xóa và thông báo theo SRS; kiểm mất response/đối soát. | L; race và phí. |
| B11 | Thiết kế/POC pipeline video và quality/safety. | B9, B10 và approval plan/provider/chi phí | Nghiên cứu synthetic sau B1 | LTX-2.5 L40S, per-scene retry, consistency/technical checks, FFmpeg, TTS/subtitles, safety fail-closed, private playback; pin runtime/version, benchmark chất lượng/độ trễ/chi phí bằng synthetic. Không coi route video demo là LTX đã chạy. | L; GPU, chất lượng và safety chưa xác nhận. |
| B12 | Nghiệm thu liên kết contract và CI cho từng lát được duyệt. | Các task thực thi tương ứng | Chuẩn bị checklist với B0–B11 | Test auth, scope, trạng thái, schema, lỗi và idempotency; test mới thực sự được CI thu thập; ghi skip và lý do. DB/MinIO/provider chưa chạy phải ghi BLOCKED/NOT RUN, không suy từ CI xanh. Evidence thuộc đúng feature. | M–L; CI hiện chỉ chọn một số file. |
| B13 | Tách và lập kế hoạch phần SRS còn lại: tổ chức/roster/capacity, billing MoMo/VNPAY, lifecycle và hai luồng sketch. | B1, quyết định owner và kế hoạch riêng | Lập inventory cùng B9–B11 | Trace từng yêu cầu SRS tới task/owner đề xuất và dependency; ghi rõ phase phát hành, không tự bỏ yêu cầu khỏi SRS hoặc tuyên bố đã hoàn thành. | L; phạm vi và liên nhóm. |

## Thứ tự và cổng ra quyết định

1. B0–B3 tạo cơ sở phân chia: lấy evidence, crosswalk API, hòa giải SRS và chốt quyền sở hữu. B4/B5 có thể chuẩn bị độc lập; sửa code vẫn cần plan và approval riêng.
2. Sau quyết định và approval, làm S1/S2/S3 theo Rev36 và kiểm migration/CI. B8 là smoke demo độc lập, không thay thế FEAT-064 hay B9–B11.
3. B9–B11 là các plan sau: StoryRun và duyệt → admission/budget/quota → pipeline video/safety. Các bản thiết kế có thể phát triển song song khi chốt interfaces, còn code/migration dùng chung phải có một owner và thứ tự rõ ràng.
4. B12 kiểm tra từng lát, không chờ hết toàn bộ hệ thống. B13 bảo đảm các nhánh công việc còn lại có người nhận và không bị mất khỏi phạm vi SRS.

**Đường phụ thuộc chính:** B0/B1 + B2 + B3 → B7 → B9 → B10 → B11 → B12. B4 và B5 là lỗi cần phân loại/xử lý theo ảnh hưởng và scope; B8 chỉ xác minh kết nối demo, không mở khóa hoặc nghiệm thu chuỗi SRS. B6 là chuẩn bị legacy và không tự động là điều kiện của FEAT-064.

## Cần chủ task/BA/BE xác nhận

- Chọn có chạy FEAT-064 current-flow pilot hay đi trực tiếp theo nhánh SRS mới; điều phối file/schema khi hai hướng cùng tồn tại. Không coi smoke demo đã chứng minh Child UI → BE1 → BE2 → Modal → Teacher.
- Chốt các OD và disposition S1 trong Rev36, pin đúng hash plan và scope khi ghi approval; quyết định riêng quyền dùng DB tạm, Modal và giới hạn phí khi cần.
- Xác nhận nguồn `EV-063-30`, OpenAPI JSON, commit và profile của Rev37; bổ sung bản catalog/evidence có quyền chia sẻ nếu nhóm cần dẫn chứng. Không đưa dữ liệu nhạy cảm vào Git.
- B2 phải ghi quyết định và giải quyết các đoạn mâu thuẫn trước khi freeze API StoryRun. SRS 2.3 vẫn là draft.
- Qwen3-VL-8B/L40S từng smoke về kết nối nhưng SRS ghi chất lượng Qwen3-VL `NO_GO`; Qwen2.5-VL-7B/L4 là ứng viên chưa benchmark. Muốn chọn model phải có benchmark và quyết định riêng; không ngầm đổi provider production. Chính sách production hiện tại vẫn Runpod, còn Modal là đường dev thử nghiệm theo scope được duyệt.

## Ranh giới và evidence

Chỉ dùng dữ liệu giả lập cho demo/pilot. Không đưa token, nội dung `.env`, model weights hoặc dữ liệu trẻ thật vào repo/chat. Modal endpoint thử hiện chỉ phục vụ `/health` và `/v2/vision`; health không chứng minh model đã sẵn sàng, HTTP 200 không thay thế kiểm trạng thái nghiệp vụ. Timeout backend và Modal cần được ghi vào runbook khi test. Route `unauthenticated` ở lớp Modal không đồng nghĩa app đã bỏ kiểm tra Bearer.

Không có task nào trong backlog này tự cho phép thay đổi schema, sửa approval, chạy PostgreSQL/MinIO/Modal, dùng GPU, chuyển dữ liệu thật, deploy, thay provider production hay cutover. Evidence khi thực hiện phải được lưu trong feature tương ứng và phân biệt chính xác PASS/FAIL/BLOCKED/NOT RUN; không ghi pass cho việc chưa chạy.
