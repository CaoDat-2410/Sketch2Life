# Sketch2Life product

<!-- impeccable:product-schema 1 -->

## Platform
web

## Users
Phụ huynh dùng giao diện điện thoại để tạo và xem câu chuyện từ tranh của bé. Giáo viên dùng cổng web để quản lý lớp, giáo án và buổi học. Quản lý trường và quản trị nền tảng dùng cổng web để vận hành, duyệt và quản trị dữ liệu trong phạm vi vai trò.

## Product Purpose
Sketch2Life kết nối tranh vẽ, giáo án và hoạt động học với câu chuyện và video hỗ trợ bởi AI. Mỗi vai trò cần thấy đúng tác vụ và dữ liệu quan trọng của mình.

## Operating Context
Biên bản `Bien_Ban_Review_UI_UX_Du_An.docx` (tài liệu review UI/UX của nhóm) là nguồn yêu cầu UX được người dùng ưu tiên. Parent là giao diện mobile hướng tới Android; Teacher, Manager và Admin là cổng web. SRS trong workspace bổ sung bối cảnh chức năng.

## Capabilities and Constraints
- Giữ nguyên mainflow, workflow, route, thao tác, phân quyền và chức năng hiện có trong lần làm lại giao diện.
- Parent: bước tùy chọn, nhập chữ cùng ghi âm, video, hoạt động ngoài trời, lịch sử, hồ sơ trẻ và cài đặt.
- Teacher: danh sách lớp và chi tiết lớp, CRUD giáo án, tạo hoặc tải tài liệu bằng modal, quyền chia sẻ, AI và trình chiếu.
- Manager/Admin: giữ các tác vụ CRUD, duyệt và vận hành theo vai trò; người dùng đã yêu cầu thay đổi diện mạo cho cả bốn role.
- API backend được tham khảo để hiểu khả năng hiện có; yêu cầu UX trong biên bản dẫn dắt thiết kế.

## Brand Commitments
Giữ tên Sketch2Life. Người dùng yêu cầu làm mới logo và thay toàn bộ diện mạo cũ bằng hệ giao diện sạch, gọn, chuyên nghiệp, ít chữ nhưng không bỏ nội dung quan trọng.

## Evidence on Hand
Mã nguồn của bốn ứng dụng trong workspace, biên bản review của leader, SRS và ảnh chụp giao diện cũ do người dùng cung cấp.

## Product Principles
- Tác vụ chính luôn dễ thấy và dễ thao tác.
- Chi tiết xuất hiện khi người dùng mở mục tương ứng.
- Trạng thái, quyền và cảnh báo quan trọng vẫn hiển thị rõ.
- Thông tin của trẻ được hiển thị theo phạm vi vai trò.
