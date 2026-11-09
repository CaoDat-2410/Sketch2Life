# Sketch2Life — Giao diện Giáo viên (Teacher UI)

Thư mục độc lập chứa toàn bộ mã nguồn giao diện cho vai trò **teacher-ui** trong dự án **Sketch2Life**.

## Danh sách màn hình
- T01 (`/t01-lesson-workspace`): Tổng quan giáo án, Phản hồi phụ huynh (UI09) & Cài đặt
- T02 (`/t02-lesson-authoring`): Soạn giáo án có cấu trúc 4 bước
- T03 (`/t03-document-import-review`): Nhập tài liệu & rà soát trích xuất 2 cột (UI06)
- T04 (`/t04-session-sketch-deck`): Chuẩn bị buổi học & bộ gợi ý nét vẽ 16:9
- T05 (`/t05-classes-and-children`): Danh sách lớp học & 2 bảng quyền chia sẻ tách biệt (UI08)
- T06 (`/t06-sample-story-run`): Chạy thử kịch bản video mẫu cho 1 học sinh đại diện
- T07 (`/t07-video-presentation-confirmation`): Xem trước video mẫu & xác nhận trình chiếu tại lớp

## Cài đặt & Chạy độc lập
```bash
npm install
npm run dev
```
- Ứng dụng chạy mặc định tại: `http://localhost:5172`

## Kiểm tra TypeScript & Build Production
```bash
npm run build
```
