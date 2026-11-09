# Sketch2Life — Giao diện Phụ huynh (Parent UI)

Thư mục độc lập chứa toàn bộ mã nguồn giao diện cho vai trò **parent-ui** trong dự án **Sketch2Life**.

## Danh sách màn hình
- P01 (`/p01-lesson-library`): Thư viện bài học & trạng thái UI05
- P02 (`/p02-lesson-detail`): Chi tiết bài học & các bước vẽ
- P03 (`/p03-drawing-line-guide`): Bé vẽ tranh kèm gợi ý nét vẽ tùy chọn
- P04 (`/p04-capture-subject-confirmation`): Chụp tranh & xác nhận chủ thể
- P05 (`/p05-context-idea-confirmation`): Xác nhận ngữ cảnh & ý tưởng của bé
- P06 (`/p06-story-review`): Rà soát kịch bản 5 phân cảnh (chỉ đọc) & gợi ý AI (tối đa 3 lần)
- P07 (`/p07-video-job-status`): Tiến trình tạo video theo 4 bước rời rạc
- P08 (`/p08-video-and-activities`): Xem video riêng tư (có phụ đề CC) & hoạt động ngoài trời
- P09 (`/p09-history-feedback`): Lịch sử học & phản hồi bài học (UI09)
- P10 (`/p10-child-profiles`): Quản lý hồ sơ bé (24–155 tháng tuổi)
- P11 (`/p11-authentication`): Đăng nhập / Tạo tài khoản / Quên mật khẩu
- P12 (`/p12-video-quota`): Lượt tạo video & mua thêm lượt (MoMo, VNPAY)

## Cài đặt & Chạy độc lập
```bash
npm install
npm run dev
```
- Ứng dụng chạy mặc định tại: `http://localhost:5171`

## Kiểm tra TypeScript & Build Production
```bash
npm run build
```
