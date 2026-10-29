# EV-063-11 — Q137–Q144 AI Sketch và pipeline video

## Phạm vi

Rà soát tài liệu theo câu trả lời Q137–Q144 và yêu cầu dùng pipeline video Sketch2Life do chủ sở hữu cung cấp. Công việc được giới hạn ở tài liệu FEAT-063 theo approval cho Plan revision 17; không sửa source code, schema/migration hoặc dữ liệu.

## Các điểm đã đối chiếu

- AI Sketch chỉ thuộc luồng Teacher. Parent không có gợi ý vẽ và không chọn trước chủ thể; sau khi chụp, VLM đề xuất chủ thể để người lớn xác nhận hoặc sửa.
- Một Teacher Sketch Deck dùng chung cho occurrence, được tạo từ plan đã duyệt và bao quát mọi activity. Deck hiển thị trên nền trắng 16:9, có 3–5 bước line-sketch tăng dần, gợi ý bố cục và giải thích ngắn. Teacher có thể Back/Next, chọn activity/chủ thể, skip hoặc tạo lại một sketch. Trẻ vẽ trên giấy; không có canvas cộng tác, freehand, chỉnh layout tùy ý hoặc PPTX.
- Deck không gắn hồ sơ, ảnh hay dữ liệu cá nhân của trẻ; Sketch có rate/compute cap riêng và không tiêu thụ video quota.
- Story/video chạy là một trẻ và một tranh mỗi run. Chuỗi được ghi trong SRS: VLM hiểu tranh → LLM tạo story có cấu trúc → storyboard 5–15 scene → người lớn xem/viết lại/xác nhận script → tạo Character Bible/scene reference → LTX-2.5 image-to-video theo scene trên Modal L40S → kiểm tra consistency → FFmpeg ghép scene → TTS giọng người lớn tiếng Việt/phụ đề đồng bộ, không nhạc → safety tự động → playback riêng.
- Mỗi scene có một lượt đầu và tối đa hai retry kỹ thuật tự động. Mỗi run có một request video đầu và tối đa hai lần tạo lại; mỗi request được nhận tính quota theo quy tắc đã chốt. Người lớn chỉ duyệt script/storyboard; video đạt kiểm tra kỹ thuật và safety được phát ngay. Nếu không phù hợp, bản cũ bị ẩn khi request thay thế được nhận, run quay lại bước duyệt script. Không có duyệt video cuối, gallery công khai hoặc download/export.
- Mô hình dữ liệu dùng 2 entity Lesson (`sketch_deck_revisions`, `sketch_deck_steps`). Character Bible không tạo bảng riêng: visual anchors có version nằm trong `story.understanding_revisions`, scene tham chiếu neo qua `story.story_scenes`, còn ảnh dẫn xuất và provenance nằm trong Core Asset/lineage.
- AI Job có target discriminator: job story/video gắn một StoryRun và đúng một child subject; job Sketch gắn Lesson Sketch Deck và không có child/profile subject. Hai loại job có aggregate, trạng thái, completion và quota/compute treatment riêng.
- Số bảng cuối được đối chiếu: 51 bảng giữ/tái cấu trúc + 44 bảng mới = 95 active; thêm 35 bảng legacy chỉ đọc = 130 vật lý dự kiến. Q135 là tổng trung gian 42/93/128 trước khi hai entity Sketch được thêm theo Q138–Q139.

## Kiểm tra tĩnh

- Đọc lại các mục quy trình, pipeline, yêu cầu, acceptance criteria, use case, state/AI job, trace matrix, data-table register, feature decisions/context/status và ADR-0021.
- Đối chiếu tham chiếu Q137–Q144, BR-42–BR-45, FR-T-18–FR-T-20, FR-AI-13/14, NFR-33, AC-33–AC-37, AT-14–AT-17 và hai bảng Sketch mới.
- Đếm ID requirement và định nghĩa entity bằng kiểm tra văn bản: 45 BR, 80 FR, 33 NFR, 37 AC, 17 AT; 44 bảng đích mới trong register; tổng đích 51 + 44 = 95 active và 95 + 35 = 130 vật lý dự kiến. Bảng pipeline trong SRS có 14 chặng.
- Xác minh bằng rà soát văn bản rằng không có yêu cầu tạo PDF hoặc diagram trong bước này; các bản Mermaid cũ trong thư mục evidence vẫn là bản nháp lịch sử chưa được duyệt.
- Approval hash của Plan revision 17 giữ nguyên: `F152E458D599317A4D26F915A5561EFA4ACFCBDD55239B12DFD5DE3D753F3D6F`.

Không chạy product tests/builds, database inspection, migration, provider, Modal, payment, benchmark hoặc kiểm thử dữ liệu thật. Các xác nhận về model, runtime, chất lượng, độ trễ, chi phí và storage adapter vẫn là POC/gate kỹ thuật, không được coi là đã triển khai.

## Trạng thái

SRS và Data Table Register vẫn là bản nháp để chủ sở hữu rà soát. Chỉ sau khi chủ sở hữu duyệt rõ cả hai Markdown baseline mới tiếp tục tạo Mermaid conceptual/logical và PDF theo yêu cầu.
