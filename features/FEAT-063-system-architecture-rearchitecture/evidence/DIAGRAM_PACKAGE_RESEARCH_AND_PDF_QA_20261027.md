# EV-063-14 — Nghiên cứu bộ sơ đồ và QA PDF

**Ngày:** 2026-10-27  
**Trạng thái:** Hoàn tất tạo và kiểm tra artifact theo phạm vi tài liệu đã được chủ sở hữu cho phép. SRS và Data Table Register vẫn là bản nháp, chưa được phê duyệt nội dung.

## 1. Phạm vi và nguồn

Tạo đúng hai đầu ra tại thư mục người dùng chỉ định: một Draw.io nhiều trang có thể chỉnh sửa và một PDF tương ứng. Nội dung được dựng từ SRS v2.0-draft, DATA_TABLE_REGISTER v2.0-draft và các tài liệu tham khảo người dùng cung cấp: `Report3_Software Requirements Specification.docx`, `Report4_Software Design Document.docx`, `Report7_Final Project Report.docx`.

Các sơ đồ được chọn theo phần yêu cầu/luồng cần diễn đạt trong SRS và hướng dẫn chuẩn về yêu cầu, UML, C4 và Draw.io. Không thêm loại sơ đồ không làm rõ Sketch2Life.

## 2. Đầu ra

| Artifact | Đường dẫn | Kích thước | SHA-256 |
|---|---|---:|---|
| Draw.io gốc, chỉnh sửa được | `owner-selected local document directory\Sketch2Life_SRS_Architecture_Diagrams.drawio` | 623,437 bytes | `29e0f5237d66ba764e52e4151c75cb1e8dcc8aa198e0f0ccde1d4c2babfad9a5` |
| PDF | `owner-selected local document directory\Sketch2Life_SRS_Architecture_Diagrams.pdf` | 296,658 bytes | `b2d27dc18f6b29e1579eebd3227253626a23e5f46e85dbb096d0adc7ac670d98` |

## 3. Danh mục sơ đồ

Draw.io có 45 trang; PDF có 45 trang ngang, mỗi sơ đồ chiếm một trang PDF. Tất cả sơ đồ nằm trong cùng một file Draw.io.

| Trang | Nội dung |
|---|---|
| 00 | Trang chỉ mục, baseline dữ liệu và phạm vi đã chốt |
| 01–10 | Context; Use Case; Parent Screen Flow; Teacher Screen Flow; Conceptual Data Model; System Architecture; Package; Domain Class; Data Ownership; Cross-Schema Logical Relationship Map |
| 11–20 | Logical ERD theo 10 owner: Core, BE1, Parent, Learning Content, Lesson, Story, AI Jobs, AI Policy, Billing, Notifications |
| 21 | Danh mục 48 mapping legacy/read-only, không đưa vào ERD active |
| 22–25 | Activity: Teacher AI Sketch Deck; Parent Story Run; Teacher sample video; Story-to-Video pipeline |
| 26–34 | Sequence: Parent run; import lesson/Sketch; Teacher sample; quota admission saga; scene retry/stale result; payment callback; resumable upload; reassignment; deletion |
| 35–38 | State Machine: StoryRun; VideoGeneration; AI Job; LessonOccurrence + SketchDeck |
| 39–44 | Deployment; Data Flow/Trust Boundaries; Monitoring/Rate Limits/AI Cost; API/Error Contract; Migration/Cutover; Requirements Traceability/Sources |

## 4. Nội dung dữ liệu được thể hiện

- ERD logical có đúng 78 bảng active, xuất hiện đúng một lần trên các trang owner; card nêu PK/FK và cột tiêu biểu. Quan hệ cùng owner và cardinality được vẽ trong trang owner tương ứng.
- 48 mapping legacy/read-only được liệt kê riêng. Không biểu diễn chúng như bảng active.
- Cross-owner relationship map mô tả các hợp đồng tham chiếu có kiểu, owner và revision; không đề xuất FK hoặc SQL join xuyên schema.
- Story/Video Class Diagram và ERD thể hiện composite revision key để buộc GenerationScene thuộc cùng StoryRevision với VideoGeneration và StoryScene.
- Luồng thể hiện Parent và Teacher là hai scope riêng; mỗi StoryRun chỉ gắn đúng một hồ sơ trẻ; Teacher occurrence tạo một deck dùng chung, còn video mẫu là một trẻ + một activity.
- Pipeline video phản ánh VLM → story/storyboard 5–15 cảnh → người lớn xác nhận script → Character Bible/reference → LTX-2.5 image-to-video trên Modal L40S candidate → consistency → FFmpeg → Vietnamese TTS/subtitles → automated safety → private playback. Không có final video approval hoặc public gallery.
- Teacher AI Sketch có hướng dẫn vẽ dạng 3–5 bước line-sketch theo nhóm tuổi, gợi ý bố cục/đặt chủ thể (ví dụ chủ thể giữa, hoa bên phải), giải thích ngắn activity ngoài trời và điều khiển trình chiếu. Parent không có AI Sketch.

## 5. Kiểm tra artifact và hình ảnh

| Kiểm tra | Kết quả |
|---|---|
| Parse XML của Draw.io | Thành công; 45 diagram pages |
| Parse model theo `DATA_TABLE_REGISTER` | 78 active target tables; 48 legacy mappings; 10 owner groups |
| Đối chiếu ERD | 78/78 bảng active được hiển thị đúng một lần; 48/48 legacy có trong trang inventory riêng |
| Số trang PDF | 45; mỗi trang là một sơ đồ/diagram view |
| Màu trong style XML | Chỉ `#000000` và `#FFFFFF` (ngoài các fill/stroke trong suốt) |
| Render trang | 45/45 trang được render PNG từ Draw.io; lưu trong `drawio_package/rendered/` |
| Contact sheet | 3 ảnh tổng quan hiện hành: `contact-qa-1.png` đến `contact-qa-3.png` |
| Kiểm tra toàn trang | Đã xem cả ba contact sheet và các trang chi tiết của context, use case, screen flow, conceptual model, architecture, package/class, data ownership, các ERD chính, activity/pipeline, sequence, state, deployment, trust, monitoring, migration và traceability |

Không thấy sơ đồ bị cắt khỏi trang hoặc chữ trong node bị cắt. Một số sơ đồ quan hệ/sequence có nhiều đường nối; khổ ngang và mức zoom của PDF cần thiết để đọc nhãn nhỏ. Các đường nối không che nội dung node. Draw.io và PDF được dựng từ cùng một nguồn XML; trang PNG QA nằm tại `features/FEAT-063-system-architecture-rearchitecture/evidence/drawio_package/rendered/`.

## 6. Bản chất và giới hạn

- Đây là bộ sơ đồ thiết kế logical/draft, không phải DDL và không phải bằng chứng của database đang chạy. Số bảng được lấy từ khai báo repository và register; chưa introspect database live.
- Việc tạo PDF không phê duyệt SRS hoặc Data Table Register. Nội dung hai file nguồn vẫn ở trạng thái draft.
- Không sửa product code/schema/migration; không chạy product tests/builds; không gọi Modal, AI provider, payment provider hoặc môi trường production; không dùng dữ liệu trẻ thật.
- Model/GPU, chi phí, benchmark chất lượng, hosting production, vùng dữ liệu và tích hợp provider vẫn là các cổng kỹ thuật/vận hành được nêu trong SRS.

## 7. Nguồn hướng dẫn

Đã tra cứu ngày 2026-10-27. Các nguồn dưới đây giúp chọn loại view và cách xuất, không thay thế quyết định nghiệp vụ trong SRS:

- ISO/IEC/IEEE 29148:2018, Requirements engineering: <https://www.iso.org/standard/72089.html>
- OMG UML 2.5.1: <https://www.omg.org/spec/UML/>
- C4 diagrams: <https://c4model.com/diagrams>
- Draw.io multipage diagrams: <https://www.drawio.com/docs/manual/pages/>
- Draw.io PDF export, all pages: <https://www.drawio.com/docs/manual/export/export-to-pdf/>
