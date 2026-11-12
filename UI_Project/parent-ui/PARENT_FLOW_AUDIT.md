# Parent Android mainflow và rà soát các nhánh BE

Ngày rà soát: 2026-11-11.

## Phạm vi và cách đọc nguồn

- Theo yêu cầu của chủ dự án, lần rà soát này không dùng nhánh FE làm căn cứ. Mình chỉ đối chiếu tài liệu nghiệp vụ/BE, lịch sử nhánh BE, source BE và prototype Parent trong workspace để kiểm tra thứ tự luồng.
- Đã đọc các remote ref read-only tại thư mục tmp/Sketch2Life-be-dev-2026-11-07; không checkout hoặc sửa source của repository Sketch2Life.
- Đây là kiểm tra tĩnh branch, tài liệu và route composition. Không chạy API, database, provider, test hay build nên không xem đây là nghiệm thu runtime.

## Nguồn yêu cầu và trạng thái nhánh

| Nguồn | Mốc đã đọc | Ý nghĩa |
|---|---|---|
| main | 1c2c6d35, 2026-08-24 | Cũ hơn nhiều so với các cập nhật FEAT-063 tháng 11; không dùng làm workflow hiện hành. |
| dev | 1431ef81, 2026-11-06 | Nhánh code tích hợp đã xuất bản gần nhất trong các ref đã đọc. |
| docs/feat063-diagram-readiness-20261107 | d77ad86c, 2026-11-09 | Đặt SRS FEAT-063 v2.7-draft Rev60 làm canonical working baseline. Đây là bản nháp chưa sign-off và nhánh chỉ cập nhật tài liệu. |
| feature/feat063-be-foundation và feature/feat063-m2-parent-teacher-foundation | Cùng SHA 4b7f07cc, 2026-11-09 | Nhánh BE mới nhất trong phạm vi. Có dev làm tổ tiên và có các thay đổi BE chưa có trong dev; tài liệu/SRS của nhánh chỉ tới Rev57, chưa chứa tip Rev60. |
| BE2 card family | feature/be2-01-ai-job-foundation, be2-02-vision-correction, be2-03-assistance-orchestration, be2-04-sketch-generation, be2-05-sketch-review, be2-06-child-response, be2-07-knowledge-script, be2-08-14 và feature/be2-01-07 (2026-10-16..20) | Các nhánh card/lát xử lý BE2 cũ; đọc trạng thái tổng hợp ở nhánh integration bên dưới, không ghép riêng lẻ thành Parent API hiện hành. |
| feature/be2-backend-ai-integration | aa41ed6f, 2026-10-22 | Nhánh tích hợp BE2 cũ hơn, thuộc lineage của feature BE mới hơn. Status của FEAT-044/057 còn ghi BE2-01 IN_PROGRESS, X01 PARTIAL, X09-08 NOT_IMPLEMENTED và các gate chưa đóng. |
| Các nhánh BE/Modal khác | codex/be1-real-backend (15-10), codex/feat063-modal-backend-completion-20261103 (04-11), feature/feat061-modal-qwen-vl-endpoint và feature/modal-vision-dev (29-10), feature/feat063-modal-ai-reliability-20261106 (06-11) | Đây là các mốc backend/pilot/provider riêng; không thay thế contract và Parent mainflow trong SRS Rev60. |

SRS v2.7-draft Rev60 là nguồn yêu cầu làm việc mới nhất đã tìm thấy, không phải bằng chứng rằng backend đã implement hoặc SRS đã được ký. Nhánh BE foundation chưa được merge vào dev; do đó không được mô tả các API trên nhánh này như API đã có trong baseline dev.

## Parent target mainflow theo SRS v2.7-draft

UC-02, FR-P-01..11, §21.2, §21.5 và §31 quy định các cổng chính như sau:

1. Parent chọn đúng một hồ sơ trẻ. Có thể pin một phiên bản Lesson cụ thể hoặc tạo run không dùng preset.
2. Chụp/chọn đúng một tranh; nhập chữ, ghi âm hoặc dùng cả hai; tải asset qua upload session có resume và kiểm tra hash/media.
3. Nếu có audio, backend chạy ASR; người lớn sửa/xác nhận transcript trước khi đi tiếp.
4. VLM đề xuất chủ thể; người lớn xác nhận hoặc sửa, thao tác sửa tạo revision phân tích mới.
5. Người lớn duyệt context snapshot tối thiểu và optional lesson/story direction. Không gửi tên, ảnh hồ sơ, giọng nói hoặc thông tin nhạy cảm ngoài context đã được cho phép; không chọn activity trước video.
6. AI tạo story/storyboard có revision. Parent có thể gửi tối đa ba yêu cầu viết lại; không sửa scene trực tiếp.
7. Parent xác nhận đúng revision/hash cuối của script/storyboard trước video.
8. Video đi qua admission bất đồng bộ, gồm resource/budget và quota receipts. Chỉ dispatch khi admission được chấp nhận; job và stage được đọc từ backend.
9. Video chỉ phát sau kiểm tra kỹ thuật và safety. Khi ở VIDEO_READY, backend cấp playback token ngắn hạn; Parent không cần duyệt video cuối.
10. Nếu đánh dấu video không phù hợp, quay lại duyệt script trong giới hạn tối đa hai lần tạo lại. Video hiện tại chỉ bị ẩn khi request thay thế được chấp nhận.
11. Chỉ sau khi video playable mới hiển thị activities từ lesson version đã pin. Nếu không dùng preset, §31.10 còn hai lựa chọn OPEN-OWNER: không query catalog, hoặc query catalog sau video với permission/version/empty/revoke semantics đã chốt. UI không nên tự chọn một policy.
12. Parent hoàn tất hoặc hủy run. Reminder và idle closeout lần lượt là 144 giờ và 168 giờ adult-wait theo SRS; system/job wait không được tính như adult wait.

Điểm sửa quan trọng so với bản audit cũ: Rev60 đã hòa giải chỗ UC-02 mâu thuẫn activity. Parent không chọn activity trước video; hành vi catalog khi không có lesson vẫn là quyết định mở, không còn là mâu thuẫn nội bộ phải đảo luồng.

## Bằng chứng BE và khoảng trống so với target

### Nhánh dev

SRS §32.6 và §32.7 mô tả source composition ở mức source-only: main FastAPI app mount health/BE1, một số demo/session/story-video và Lesson Library. routers/ai_jobs.py cùng domain/application/infrastructure có trong source nhưng không được mount bởi main router_composition.py. Presence của module không đồng nghĩa Parent API chạy được.

### Nhánh feature/feat063-be-foundation

- Branch diff với dev chủ yếu là Teacher/organization M2 foundation, guarded pilot assistance, story-run demo, hợp đồng OpenAPI và test/source support. S1a-T được phê duyệt/đóng phạm vi riêng cho Teacher; tài liệu approval nói rõ S1a-P và S2 là phase riêng, chưa mở.
- Hồ sơ D-171 liệt kê S1a-P routes POST /v1/parent/profiles và GET/PATCH /v1/parent/profiles/{profile_id} như contract/phương hướng có điều kiện; không xem đó là code đã implement. S2 cũng cần approval riêng.
- Main router composition vẫn không mount durable AI Jobs router.
- story_run_lite có các thao tác create/read run, attach asset, subject confirmation, generate/read/confirm story revision, cancel và upload-session. Main app chỉ mount route này khi bật demo flag, trên combined local/test; source gắn nhãn unauthenticated loopback-only synthetic demo. Nó không chứng minh Parent identity, Firebase auth, tenant/owner boundary hay production runtime.
- Demo dispatch dùng FastAPI BackgroundTasks; không tương đương target durable AI Jobs/outbox/admission/reconciliation.
- Chưa thấy trong route này chuỗi target hoàn chỉnh gồm idea/ASR review, context confirmation, script-hash confirmation, video admission/generation, unsuitable/regenerate, completion, delete completed run, playback token, quota và notification. Một số domain/service/schema có thể tồn tại ở chỗ khác, nhưng không có bằng chứng route mounted end-to-end trong main app.

### Các nhánh BE2 và Modal

- FEAT-044/057 cũ lưu trạng thái BE2-01 còn IN_PROGRESS, X01 PARTIAL và X09-08 NOT_IMPLEMENTED; một số contract/source-fence, persisted job/run pinning và owner approvals còn mở. Status này không đủ cơ sở để khẳng định pipeline Parent đã tích hợp hoàn chỉnh.
- Các nhánh Modal ghi nhận development/pilot workloads và retest riêng. SRS Rev57 source snapshot nói worker profile là dev-only/disabled; source/module hoặc kết quả thử nghiệm non-video không chứng minh luồng Parent API/video end-to-end.
- Những mốc cũ vẫn hữu ích để tra lịch sử kỹ thuật, nhưng không được ghép rời rạc thành một API production duy nhất.

## Đối chiếu với prototype Parent

Prototype hiện thể hiện đúng thứ tự cốt lõi: chọn một trẻ/lesson tùy chọn → tranh → chữ/voice → xác nhận transcript → xác nhận chủ thể → duyệt context → duyệt script/storyboard → video async → hoạt động lesson sau khi video sẵn sàng → hoàn tất hoặc tạo lại. Không có bước chọn activity trước video. Các giới hạn viết lại/tạo lại và thời điểm ẩn video cũ cũng được mô phỏng theo flow.

Đây là kết luận về trật tự UX trong prototype web. Các trạng thái backend, auth, upload, job, safety, playback, quota, persistence, recovery và native Android permissions vẫn chưa được tích hợp/kiểm chứng. Prototype không thể chứng minh API hiện tại đã đáp ứng flow.

## Kết luận cho thiết kế tiếp theo

- Có thể dùng UC-02 Rev60 làm thứ tự màn hình mục tiêu cho Parent Android.
- Chưa thể nói BE hiện đã đủ API để ghép toàn bộ Parent flow. Nhánh dev chưa có target Parent API đầy đủ; nhánh feature BE mới có Teacher slice và StoryRun-lite demo có giới hạn; Parent profile và S2 cần phase/approval/code riêng.
- Thiết kế API-facing UI theo contract §21.2 và trạng thái §22–23. Các endpoint đã có thật, màn nào đang dùng fixture, lỗi nào backend trả và job nào durable cần được đánh dấu rõ trong quá trình ghép.
- Với no-preset activity, chỉ thể hiện điểm sau-video theo cấu trúc linh hoạt; không chốt picker/query/empty-state policy cho đến khi owner quyết định.
- Kết luận này thay thế các nhận định dựa trên SRS v2.5 trong bản audit trước.

