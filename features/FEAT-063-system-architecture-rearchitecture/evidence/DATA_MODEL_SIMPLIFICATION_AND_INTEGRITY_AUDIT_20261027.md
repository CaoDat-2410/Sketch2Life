# EV-063-13 — Rà soát tinh gọn và tính toàn vẹn mô hình dữ liệu

**Ngày:** 2026-10-27 (Asia/Saigon)  
**Phạm vi:** tài liệu SRS, Data Table Register, proposed ADR-0021 và danh mục bảng khai báo trong repository.  
**Trạng thái:** đánh giá kiến trúc tĩnh; chủ sở hữu chưa duyệt nội dung SRS/register phiên bản này.

## 1. Kết quả kiểm kê

- Đối chiếu đủ 86 ánh xạ bảng production được khai báo trong repository; 5 fixture chỉ dành cho kiểm thử không được tính.
- 38 bảng nguồn được giữ/tái cấu trúc và 48 bảng nguồn được xếp legacy/read-only. Trong 48 bảng legacy có 35 bảng cộng tác/canvas/video/activity/preset cũ và 13 bảng AI Policy chưa cần ghi trong luồng synthetic V1.
- Từ điển thiết kế có 40 bảng mới. Kiểm tra tĩnh cho thấy cả 40 tên bảng trong từ điển đều có đúng một mục trong quan hệ §6.1.
- Phép tính baseline: 38 + 40 = 78 bảng active; 78 + 48 = 126 bảng vật lý dự kiến nếu mọi ánh xạ khai báo tồn tại trong database.
- Đây là số lượng từ source declarations; không phải kiểm kê database đang chạy.

## 2. Tinh gọn bảng

### Đã loại khỏi target ERD

Không tạo bốn bảng helper/snapshot vì mỗi dữ kiện đã có owner chuẩn:

1. `ai_jobs.job_subject_refs`: hồ sơ duy nhất được resolve từ target `STORY_RUN`.
2. `ai_jobs.job_result_assets`: Story/Lesson aggregate sở hữu output asset refs; completion receipt chỉ ghi nhận disposition/hash cần cho idempotency.
3. `story.profile_context_snapshots`.
4. `story.profile_context_snapshot_items`: context tối thiểu đã được người lớn duyệt được ghim có schema/hash/giới hạn trong immutable `story.run_inputs`.

### Chuyển thành legacy/read-only

Đưa 12 `ai_policy.copy_*` provider-copy registry và `ai_policy.resource_receipt` ra khỏi active-write target. Không drop hoặc sao chép dữ liệu/ID cũ. Synthetic V1 ghi opaque scratch/attempt ref, manifest hash và cleanup state/receipt trong `ai_jobs.attempt`/`ai_jobs.job_events`; provenance asset thuộc Core. `ai_policy.resource_event` giữ idempotency key, fingerprint, operation và bounded result snapshot cho lệnh resource mới. Lệnh, bảng/ledger cũ được giữ chỉ đọc.

Giới hạn: nếu một resource command trong implementation có thể tạo nhiều event có cùng idempotency key, unique constraint phải thêm event kind hoặc việc gộp receipt phải dừng cho đến khi mapping được chứng minh. Bản tài liệu ghi rõ nhánh này; không giả định migration đã an toàn.

Không gộp các bảng có vòng đời/quyền sở hữu thật sự độc lập chỉ để giảm số lượng. Parent và Teacher profile vẫn tách scope; revision/event/attempt/usage/upload lifecycle vẫn có owner riêng. Việc gộp bảng không được làm yếu authorization hoặc khiến dữ liệu chỉ liên kết bằng JSON không kiểm chứng.

## 3. Quan hệ và tính toàn vẹn

- Mỗi bảng mới có owner và quan hệ nội bộ hoặc typed, versioned cross-owner reference; không thêm bảng reference registry chung.
- Quan hệ cùng owner dùng FK/unique/check khi có thể biểu diễn.
- Story scene được khóa cùng revision: `video_generations` có khóa duy nhất `(video_generation_id, story_revision_id)`; `story_scenes` có `(story_revision_id, scene_id)`; `video_generation_scenes` dùng hai composite FK tương ứng. Bản sao `story_revision_id` trên generation-scene là khóa integrity bất biến, không phải nguồn trạng thái độc lập.
- Mỗi generation-scene lưu `source_job_ref` có kiểu. AI Job target `VIDEO_GENERATION_SCENE` trỏ ngược tới đúng generation-scene; Story owner kiểm tra cả hai chiều qua contract. `ai_jobs.attempt` là retry ledger duy nhất; Story scene không lưu retry counter thứ hai.
- Story command kiểm tra aggregate revision, input/story/video pointers và hash trước khi ghi; cập nhật pointer cùng projection state trong một transaction. `video_generations.state` là trạng thái canonical của generation; `story.runs.state` là projection cùng transaction.
- AI Job có đúng một target discriminator/ref/revision: `STORY_RUN`, `VIDEO_GENERATION`, `VIDEO_GENERATION_SCENE`, `LESSON_SOURCE_DOCUMENT` hoặc `LESSON_SKETCH_DECK_REVISION`.
- Một API StoryRun detail được tổng hợp qua owner ports để tránh frontend gọi hàng loạt endpoint. Không tạo read-model table và không join trực tiếp schema riêng của module.

## 4. Đường truy vết Story Run

Với `story_run_id`, application layer có thể tổng hợp theo graph sau mà không tạo bảng nối dư thừa:

```text
StoryRun
  ├── profile + pinned profile revision
  ├── run input + artwork/audio/transcript/understanding refs
  ├── current story revision → scenes
  ├── review decision(s)
  └── video generation(s) → generation scenes → AI job/attempts
                                  ├── clip asset refs
                                  └── final video/audio/subtitle asset refs
Billing quota usage ← accepted video request
Core Asset → hash/type/state/lineage and private bytes
```

Cross-owner references are resolved through explicit ports with resource kind, opaque ID, contract version and pinned revision/hash. Response/API composition reauthorizes each referenced resource; unknown or out-of-scope IDs do not expose foreign-resource existence.

## 5. Đối soát tài liệu

SRS, Data Table Register, proposed ADR-0021, feature plan, context, decisions and status were aligned to 78 active / 48 legacy / 126 projected physical. The prior 91/35 baseline is retained only as superseded history in decision/evidence records. Acceptance criteria and the target list include all five AI Job target kinds. The register relationship list and the new-table dictionary were compared by exact table name; both contain the same 40 entries.

## 6. Giới hạn xác minh

Đã chạy các phép đếm/tìm kiếm tĩnh trên Markdown và danh sách khai báo hiện có. Không kết nối database, không đọc schema đang chạy, không thay code/DDL/migration, không chạy test/build, không gọi Modal/provider/payment, không dùng dữ liệu trẻ thật và không tạo diagram/PDF. Trước khi triển khai cần inventory database thật, kiểm tra license/retention, đối soát bản ghi, kế hoạch migration có rollback, và phê duyệt riêng.

## 7. Kết luận để chủ sở hữu xem xét

Mô hình đề xuất giảm active tables từ 91 xuống 78 mà vẫn bảo toàn 126 mapping vật lý dự kiến; 13 bảng AI Policy được giữ làm legacy thay vì bị xóa. Quan hệ Story–AI Jobs–Core/Billing/Lesson được mô tả với ràng buộc revision và target rõ ràng. Đây là baseline kiến trúc đề xuất để chủ sở hữu rà lại trong hai Markdown; chưa phải phê duyệt nội dung hay lệnh triển khai.
