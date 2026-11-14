import React, { useEffect, useRef, useState } from 'react';
import type { Role } from './webWorkspace';
import './rev7Mockup.css';

type Field = { id: string; label: string; kind?: 'text' | 'textarea' | 'select' | 'file' | 'checkbox' | 'date'; options?: string[]; hint?: string; required?: boolean; requiredWhen?: { field: string; value: string | boolean }; placeholder?: string };
type Step = { title: string; eyebrow: string; summary: string; fields?: Field[]; note?: string };
type Flow = { title: string; description: string; steps: Step[]; boundary: string };
type Operation = { title: string; description: string; items: { title: string; detail: string; state: string }[]; boundary: string };

const flowSpecs: Record<string, Flow> = {
  import: { title: 'Nhập và rà soát giáo án', description: 'Giữ file gốc, duyệt bản trích xuất trước khi đưa vào buổi dạy.', boundary: 'Parser, OCR và revision bất biến cần Lesson API.', steps: [
    { eyebrow: '01 · TÀI LIỆU', title: 'Chọn file giáo án', summary: 'PDF, PPTX hoặc DOCX · tối đa 25 MB và 100 trang/slide.', fields: [{ id: 'lessonFile', label: 'File giáo án', kind: 'file', required: true, hint: 'File đặt mật khẩu và trang scan không có OCR sẽ bị từ chối.' }] },
    { eyebrow: '02 · TRÍCH XUẤT', title: 'Kiểm tra nội dung', summary: 'Đối chiếu từng trường với file gốc; chỉnh sửa trong preview vẫn chỉ là fixture.', fields: [{ id: 'topic', label: 'Chủ đề', required: true, placeholder: 'Ví dụ: Quan sát thiên nhiên' }, { id: 'ageGroup', label: 'Nhóm tuổi', kind: 'select', options: ['3–4 tuổi', '4–5 tuổi', '5–6 tuổi'], required: true }, { id: 'objectives', label: 'Mục tiêu học tập', kind: 'textarea', required: true }, { id: 'drawingSteps', label: 'Các bước vẽ', kind: 'textarea', required: true }, { id: 'activities', label: 'Hoạt động', kind: 'textarea', required: true }, { id: 'materials', label: 'Vật liệu', kind: 'textarea', required: true }, { id: 'safety', label: 'Lưu ý an toàn', kind: 'textarea', required: true }], note: 'Bản xem trước không đọc file đã chọn. Trường được chèn là dữ liệu mẫu có thể sửa.' },
    { eyebrow: '03 · XÁC NHẬN', title: 'Duyệt bản trích xuất', summary: 'Chỉ bản đã được Giáo viên xác nhận mới dùng để lập plan.', fields: [{ id: 'confirmText', label: 'Tôi đã đối chiếu với tài liệu gốc', kind: 'checkbox', required: true }] },
  ] },
  occurrences: { title: 'Chuẩn bị buổi dạy', description: 'Một occurrence ghim đúng phiên bản giáo án, plan và danh sách hoạt động.', boundary: 'Phê duyệt thật cần revision/hash, quyền lớp và Lesson API.', steps: [
    { eyebrow: '01 · BỐI CẢNH', title: 'Chọn lớp và giáo án', summary: 'Chọn lớp mình đang phụ trách; giữ đúng version, không dùng “mới nhất” ngầm định.', fields: [{ id: 'class', label: 'Lớp được phân công', kind: 'select', options: ['Lớp Lá 1'], required: true }, { id: 'lesson', label: 'Giáo án và phiên bản', kind: 'select', options: ['Khám phá khu vườn · v1.4', 'Bầu trời kỳ diệu · v2.0'], required: true }, { id: 'date', label: 'Ngày dự kiến', kind: 'date', required: true }] },
    { eyebrow: '02 · PLAN', title: 'Mục tiêu và hướng kể', summary: 'Nội dung ngắn, rõ để dùng trong buổi học và video mẫu.', fields: [{ id: 'objective', label: 'Mục tiêu buổi dạy', kind: 'textarea', required: true, placeholder: 'Ví dụ: Quan sát màu sắc và hình dạng trong vườn' }, { id: 'direction', label: 'Hướng kể chuyện', kind: 'textarea', placeholder: 'Hướng kể phù hợp hoạt động đã duyệt' }] },
    { eyebrow: '03 · HOẠT ĐỘNG', title: 'Danh sách hoạt động', summary: 'Một occurrence có thể có nhiều hoạt động; video mẫu chỉ ghim một hoạt động.', fields: [{ id: 'activities', label: 'Hoạt động dự kiến', kind: 'textarea', required: true, placeholder: 'Mỗi dòng là một hoạt động' }, { id: 'safety', label: 'Tôi đã rà soát vật liệu, môi trường và an toàn hoạt động', kind: 'checkbox', required: true }] },
    { eyebrow: '04 · DUYỆT', title: 'Xem lại plan', summary: 'Sau khi duyệt, thay đổi plan sẽ khiến Sketch Deck cũ thành STALE.', fields: [{ id: 'approve', label: 'Xác nhận plan và phiên bản giáo án đã chọn', kind: 'checkbox', required: true }] },
  ] },
  children: { title: 'Hồ sơ trẻ trong lớp', description: 'Tạo hồ sơ có cấu trúc, giữ đúng một enrollment đang hoạt động.', boundary: 'Tạo, chuyển lớp và xóa hồ sơ thật cần quyền roster cùng API.', steps: [
    { eyebrow: '01 · HỒ SƠ', title: 'Thông tin tối thiểu', summary: 'Tên hiển thị có thể trùng; hệ thống dùng ID nội bộ để phân biệt.', fields: [{ id: 'childName', label: 'Tên hiển thị của trẻ', required: true }, { id: 'age', label: 'Nhóm tuổi', kind: 'select', options: ['3–4 tuổi', '4–5 tuổi', '5–6 tuổi'], required: true }, { id: 'class', label: 'Lớp hiện tại', kind: 'select', options: ['Lớp Lá 1'], required: true }] },
    { eyebrow: '02 · NGỮ CẢNH', title: 'Quan sát và sở thích', summary: 'Chỉ đưa thông tin tối thiểu đã được người lớn xác nhận vào run.', fields: [{ id: 'interests', label: 'Sở thích hoặc quan sát', kind: 'textarea', placeholder: 'Không nhập chẩn đoán vào bản xem trước' }, { id: 'confirmScope', label: 'Tôi đã kiểm tra phạm vi lớp và quyền xử lý hồ sơ', kind: 'checkbox', required: true }] },
  ] },
  sample: { title: 'Tạo video mẫu cho buổi dạy', description: 'Một trẻ đủ điều kiện do hệ thống chọn, một hoạt động đã duyệt, một video mẫu phát được.', boundary: 'Chọn trẻ ngẫu nhiên, consent, quota admission, AI và playback phải do backend xác nhận.', steps: [
    { eyebrow: '01 · ĐỐI TƯỢNG', title: 'Xác nhận trẻ được chọn', summary: 'Hệ thống chọn ngẫu nhiên từ roster đủ điều kiện. Giáo viên không tự chọn trẻ tùy ý.', fields: [{ id: 'occurrence', label: 'Buổi dạy', kind: 'select', options: ['Khám phá khu vườn · Lớp Lá 1'], required: true }] },
    { eyebrow: '02 · HOẠT ĐỘNG & TRANH', title: 'Ghim hoạt động, thêm tranh', summary: 'Chọn đúng một hoạt động đã duyệt; chụp bằng camera hoặc tải ảnh từ điện thoại.', fields: [{ id: 'activity', label: 'Hoạt động trong plan', kind: 'select', options: ['Quan sát khu vườn', 'Vẽ bông hoa yêu thích'], required: true }, { id: 'drawing', label: 'Ảnh tranh của một trẻ', kind: 'file', required: true }] },
    { eyebrow: '03 · ĐẦU VÀO', title: 'Rà soát ý tưởng', summary: 'Sửa transcript, xác nhận chủ thể VLM và context tối thiểu trước khi tạo story.', fields: [{ id: 'transcript', label: 'Ý tưởng hoặc transcript đã sửa', kind: 'textarea', required: true }, { id: 'subject', label: 'Chủ thể tranh đã xác nhận', required: true }, { id: 'context', label: 'Tôi chỉ dùng context tối thiểu cần thiết', kind: 'checkbox', required: true }] },
    { eyebrow: '04 · KỊCH BẢN', title: 'Xác nhận script', summary: 'Có thể yêu cầu tối đa ba lần viết lại. Không sửa tay từng scene trong V1.', fields: [{ id: 'script', label: 'Kịch bản/storyboard cần xem lại', kind: 'textarea', required: true }, { id: 'scriptConfirm', label: 'Xác nhận revision cuối trước khi tạo video', kind: 'checkbox', required: true }] },
    { eyebrow: '05 · TẠO VIDEO', title: 'Theo dõi trạng thái', summary: 'Admission, AI job và chờ người lớn là ba trạng thái khác nhau; không hiển thị phần trăm đoán.', note: 'Chưa có job thật. Khi nối API, màn này hiện stage, lỗi an toàn và hành động khôi phục.' },
    { eyebrow: '06 · KẾT QUẢ', title: 'Xem và hoàn tất', summary: 'VIDEO_READY phát riêng trong run. Giáo viên có thể hoàn tất, tạo lại theo giới hạn hoặc chiếu sau xác nhận.', note: 'Playback cần token ngắn hạn. Không có tải xuống hoặc thư viện công khai.' },
  ] },
  presentation: { title: 'Chiếu video trong lớp', description: 'Chỉ Giáo viên đang phụ trách mới xác nhận chiếu theo occurrence.', boundary: 'Xác nhận thật cần authorization và audit từ server.', steps: [
    { eyebrow: '01 · KIỂM TRA', title: 'Đúng buổi, đúng video', summary: 'Video phải đạt kiểm tra an toàn và đang ở VIDEO_READY.', fields: [{ id: 'occurrence', label: 'Buổi dạy', kind: 'select', options: ['Khám phá khu vườn · Lớp Lá 1'], required: true }, { id: 'presentationConfirm', label: 'Tôi đang phụ trách lớp và đã kiểm tra nội dung trước khi chiếu', kind: 'checkbox', required: true }] },
    { eyebrow: '02 · TRÌNH CHIẾU', title: 'Bề mặt trình chiếu', summary: 'Video mở trong cùng occurrence, không tạo bản sao công khai.', note: 'Bản xem trước chưa có video riêng tư hoặc playback token.' },
  ] },
  'run-control': { title: 'Hoàn tất hoặc hủy run', description: 'Kết thúc đúng run mẫu đang thuộc lớp và occurrence của bạn.', boundary: 'Lệnh thật cần run revision, quyền Teacher hiện hành, idempotency key và lifecycle server.', steps: [
    { eyebrow: '01 · RUN HIỆN HÀNH', title: 'Kiểm tra run', summary: 'Trạng thái video và quyền sở hữu phải được tải mới từ server.', fields: [{ id: 'run', label: 'Run đang phụ trách', kind: 'select', options: ['Run minh họa · Khám phá khu vườn'], required: true }] },
    { eyebrow: '02 · QUYẾT ĐỊNH', title: 'Chọn cách kết thúc', summary: 'Hoàn tất giữ video hợp lệ; hủy run chưa hoàn tất sẽ nhả khóa và đi vào lifecycle xóa.', fields: [{ id: 'runAction', label: 'Hành động', kind: 'select', options: ['Hoàn tất run', 'Hủy run chưa hoàn tất'], required: true }, { id: 'runReason', label: 'Ghi chú cho lịch sử', kind: 'textarea', required: true, placeholder: 'Ghi ngắn gọn lý do và bối cảnh' }, { id: 'runConfirm', label: 'Tôi đã kiểm tra đúng run và hiểu quota đã dùng không được hoàn', kind: 'checkbox', required: true }] },
  ] },
  'teacher-scope': { title: 'Tổ chức và lớp phụ trách', description: 'Chỉ mở những lớp có assignment còn hiệu lực của Giáo viên.', boundary: 'Danh sách tổ chức, lớp và quyền đọc phải do BE1 trả theo principal; preview không cấp quyền.', steps: [
    { eyebrow: '01 · TỔ CHỨC', title: 'Chọn trường', summary: 'Mỗi buổi dạy thuộc đúng một organization.', fields: [{ id: 'organization', label: 'Tổ chức được gán', kind: 'select', options: ['Trường Mầm non Ánh Nắng · minh họa'], required: true }] },
    { eyebrow: '02 · LỚP HỌC', title: 'Vào lớp phụ trách', summary: 'Khi assignment đổi, quyền xem run và media phải được kiểm tra lại.', fields: [{ id: 'class', label: 'Lớp được phân công', kind: 'select', options: ['Lớp Lá 1 · minh họa'], required: true }] },
  ] },
  assignment: { title: 'Phân công giáo viên', description: 'Mỗi lớp có đúng một Giáo viên phụ trách hiện tại.', boundary: 'Assignment thật cần kiểm tra quyền, version và lock từ BE1.', steps: [
    { eyebrow: '01 · LỚP HỌC', title: 'Chọn lớp', summary: 'Chỉ lớp thuộc tổ chức hiện tại mới được phân công.', fields: [{ id: 'class', label: 'Lớp học', kind: 'select', options: ['Lớp Mầm 1 · chưa có GV', 'Lớp Lá 1 · cô Mai'], required: true }] },
    { eyebrow: '02 · GIÁO VIÊN', title: 'Chọn người phụ trách', summary: 'Giáo viên phải đã được tổ chức provision và còn hiệu lực.', fields: [{ id: 'teacher', label: 'Giáo viên', kind: 'select', options: ['Cô Nguyễn Mai', 'Cô Trần Lan', 'Cô Phạm Hà'], required: true }, { id: 'assignmentConfirm', label: 'Tôi đã kiểm tra xung đột run trước khi chuyển phân công', kind: 'checkbox', required: true }] },
  ] },
  roster: { title: 'Quản lý roster', description: 'Enrollment của trẻ thuộc tổ chức, tối đa một lớp đang hoạt động.', boundary: 'Chuyển lớp thật phải đóng enrollment cũ và lưu lịch sử bằng BE1.', steps: [
    { eyebrow: '01 · DANH SÁCH', title: 'Chọn lớp và hồ sơ', summary: 'Quản lý trường thấy thông tin roster, không xem tranh hoặc video của trẻ.', fields: [{ id: 'class', label: 'Lớp', kind: 'select', options: ['Lớp Lá 1', 'Lớp Chồi 2', 'Lớp Mầm 1'], required: true }, { id: 'child', label: 'Hồ sơ trong roster', kind: 'select', options: ['Hồ sơ #01', 'Hồ sơ #02'], required: true }] },
    { eyebrow: '02 · CHUYỂN LỚP', title: 'Enrollment mới', summary: 'Giữ lịch sử enrollment cũ; không sao chép hồ sơ sang tài khoản Parent.', fields: [{ id: 'targetClass', label: 'Lớp đích', kind: 'select', options: ['Lớp Chồi 2', 'Lớp Mầm 1'], required: true }, { id: 'transferConfirm', label: 'Tôi đã kiểm tra lớp đích và capacity', kind: 'checkbox', required: true }] },
  ] },
  groups: { title: 'Nhóm gia đình và lời mời', description: 'Quản lý thành viên theo lớp và theo dõi trạng thái lời mời phụ huynh.', boundary: 'Membership, lời mời và quyền đọc giáo án cần Lesson Library API; lời mời chờ chấp nhận chưa cấp quyền.', steps: [
    { eyebrow: '01 · NHÓM', title: 'Chọn lớp và nhóm', summary: 'Chỉ thao tác trong tổ chức hiện tại. Thành viên được xác minh qua tài khoản phụ huynh.', fields: [{ id: 'groupClass', label: 'Lớp', kind: 'select', options: ['Lớp Lá 1', 'Lớp Chồi 2', 'Lớp Mầm 1'], required: true }, { id: 'groupAction', label: 'Việc cần làm', kind: 'select', options: ['Xem thành viên', 'Mời phụ huynh', 'Rà soát lời mời đang chờ', 'Thu hồi lời mời'], required: true }] },
    { eyebrow: '02 · THÀNH VIÊN', title: 'Nhập tài khoản phụ huynh', summary: 'Mời bằng tài khoản đã xác minh; không tạo quyền cho email chưa khớp danh tính.', fields: [{ id: 'parentAccount', label: 'Email tài khoản phụ huynh', requiredWhen: { field: 'groupAction', value: 'Mời phụ huynh' }, placeholder: 'phuhuynh@example.com' }, { id: 'groupNote', label: 'Ghi chú nội bộ (không bắt buộc)', kind: 'textarea', placeholder: 'Ghi chú cho người quản lý trong trường' }] },
    { eyebrow: '03 · XÁC NHẬN', title: 'Rà soát thay đổi', summary: 'Lời mời chỉ có hiệu lực khi phụ huynh chấp nhận. Thu hồi không xóa lịch sử membership.', fields: [{ id: 'groupConfirm', label: 'Tôi đã kiểm tra đúng lớp, tài khoản và trạng thái lời mời', kind: 'checkbox', required: true }], note: 'Bản xem trước không gửi lời mời hoặc thay đổi membership thật.' },
  ] },
  review: { title: 'Duyệt giáo án công khai', description: 'Quyết định dựa trên quyền trường, version và trạng thái hiện tại.', boundary: 'Quyết định thật cần API với revision và audit; không suy ra quyền từ giao diện.', steps: [
    { eyebrow: '01 · PHIÊN BẢN', title: 'Chọn yêu cầu', summary: 'Xem bản đang chờ và nội dung được phép hiển thị.', fields: [{ id: 'lesson', label: 'Giáo án', kind: 'select', options: ['Hành trình của hạt mầm · v1.0', 'Những đám mây kể chuyện · v1.2'], required: true }] },
    { eyebrow: '02 · QUYẾT ĐỊNH', title: 'Duyệt hoặc yêu cầu bổ sung', summary: 'Lý do được lưu cùng quyết định và phiên bản.', fields: [{ id: 'decision', label: 'Quyết định', kind: 'select', options: ['Duyệt', 'Yêu cầu bổ sung'], required: true }, { id: 'reason', label: 'Ghi chú quyết định', kind: 'textarea', required: true }, { id: 'reviewConfirm', label: 'Tôi đã kiểm tra đúng phiên bản', kind: 'checkbox', required: true }] },
  ] },
  transfers: { title: 'Đổi giáo viên phụ trách', description: 'Chuyển quyền theo lớp; run đang hoạt động có thể chặn chuyển.', boundary: 'Emergency force-close là command riêng, cần reason và audit. Giao diện không tự đóng run.', steps: [
    { eyebrow: '01 · CHUYỂN GIAO', title: 'Chọn lớp và người nhận', summary: 'Trong lúc transfer pending, lớp chỉ đọc và không ai xem nội dung run.', fields: [{ id: 'class', label: 'Lớp', kind: 'select', options: ['Lớp Lá 1', 'Lớp Chồi 2'], required: true }, { id: 'replacement', label: 'Giáo viên mới', kind: 'select', options: ['Cô Trần Lan', 'Cô Phạm Hà'], required: true }] },
  ] },
  capacity: { title: 'Sức chứa lớp học', description: 'Gói cơ bản có 10 slot; lớp mới chỉ tạo khi còn capacity hiệu lực.', boundary: 'Capacity, giá và lớp tạm ngưng cần Billing + BE1 xác nhận trong transaction.', steps: [
    { eyebrow: '01 · HIỆN TRẠNG', title: 'Xem sức chứa', summary: 'Bản xem trước: 4 lớp / 10 slot cơ bản, số thật phải lấy từ Billing.', fields: [{ id: 'capacityAction', label: 'Việc cần làm', kind: 'select', options: ['Tạo lớp trong slot còn lại', 'Mua thêm slot', 'Hạ capacity'], required: true }] },
    { eyebrow: '02 · ĐIỀU CHỈNH', title: 'Chọn lớp và kỳ hiệu lực', summary: 'Hạ capacity cần chọn lớp tạm ngưng; dữ liệu vẫn được giữ và chỉ đọc.', fields: [{ id: 'class', label: 'Lớp liên quan', kind: 'select', options: ['Lớp Lá 1', 'Lớp Chồi 2', 'Lớp Mầm 1'], required: true }, { id: 'confirmCapacity', label: 'Tôi đã xem trạng thái lớp và kỳ hiệu lực', kind: 'checkbox', required: true }] },
  ] },
  'class-lifecycle': { title: 'Vòng đời lớp học', description: 'Tạo, tạm ngưng và lưu trữ lớp trong phạm vi tổ chức.', boundary: 'Tạo lớp phải kiểm tra capacity; suspend/archive cần BE1, policy run đang mở và audit.', steps: [
    { eyebrow: '01 · LỚP HỌC', title: 'Chọn lớp', summary: 'Xem trạng thái lớp và số enrollment trước khi thay đổi.', fields: [{ id: 'class', label: 'Lớp thuộc tổ chức', kind: 'select', options: ['Lớp Lá 1 · đang hoạt động', 'Lớp Mầm 1 · chưa phân công'], required: true }] },
    { eyebrow: '02 · TRẠNG THÁI', title: 'Chọn thay đổi', summary: 'Tạm ngưng giữ dữ liệu và chuyển về chỉ đọc. Lưu trữ cần kiểm tra buổi dạy/run đang mở.', fields: [{ id: 'classAction', label: 'Hành động', kind: 'select', options: ['Tạm ngưng lớp', 'Lưu trữ lớp', 'Kích hoạt lại lớp'], required: true }, { id: 'classReason', label: 'Lý do', kind: 'textarea', required: true }, { id: 'classConfirm', label: 'Tôi đã kiểm tra enrollment, phân công và run đang hoạt động', kind: 'checkbox', required: true }] },
  ] },
  billing: { title: 'Gói và thanh toán', description: 'Theo dõi kỳ, hóa đơn, gia hạn và trạng thái thanh toán của tổ chức.', boundary: 'Không khởi tạo thanh toán từ bản xem trước; MoMo/VNPAY và callback cần backend xác minh.', steps: [
    { eyebrow: '01 · GÓI HIỆN TẠI', title: 'Kỳ dịch vụ', summary: 'Gói cơ bản 10 slot, chu kỳ tháng/năm; giá thật chờ cấu hình thương mại.', fields: [{ id: 'cycle', label: 'Chu kỳ dự kiến', kind: 'select', options: ['Theo tháng', 'Theo năm'], required: true }] },
    { eyebrow: '02 · GIA HẠN', title: 'Tùy chọn kỳ tiếp theo', summary: 'Tắt tự gia hạn vẫn giữ quyền đến hết kỳ đã thanh toán.', fields: [{ id: 'renew', label: 'Tự gia hạn ở kỳ tiếp theo', kind: 'checkbox' }, { id: 'method', label: 'Phương thức khi API sẵn sàng', kind: 'select', options: ['MoMo', 'VNPAY'], required: true }] },
    { eyebrow: '03 · HÓA ĐƠN', title: 'Xem trạng thái thanh toán', summary: 'Browser redirect không phải chứng từ thanh toán. Chỉ callback được xác minh mới cập nhật entitlement.', note: 'Bản xem trước không hiển thị hóa đơn hoặc giá chưa được phê duyệt.' },
  ] },
  moderation: { title: 'Kiểm duyệt nội dung', description: 'Rà soát nội dung công khai theo permission Content Admin.', boundary: 'Không có quyền xem media trẻ. Quyết định thật cần revision, lý do và audit.', steps: [
    { eyebrow: '01 · HÀNG CHỜ', title: 'Chọn nội dung', summary: 'Chỉ tài nguyên công khai trong phạm vi duyệt.', fields: [{ id: 'content', label: 'Nội dung chờ duyệt', kind: 'select', options: ['Dạo bước tìm màu sắc · hoạt động', 'Khu vườn nhỏ của bé · giáo án'], required: true }] },
    { eyebrow: '02 · QUYẾT ĐỊNH', title: 'Ghi nhận quyết định', summary: 'Nội dung bị ẩn không tự xóa version gốc.', fields: [{ id: 'decision', label: 'Trạng thái', kind: 'select', options: ['Cho hiển thị', 'Ẩn và yêu cầu sửa'], required: true }, { id: 'reason', label: 'Lý do', kind: 'textarea', required: true }, { id: 'confirmModeration', label: 'Tôi đã đối chiếu đúng revision', kind: 'checkbox', required: true }] },
  ] },
  catalog: { title: 'Danh mục hoạt động', description: 'Soạn nháp, rà soát và phát hành version đã duyệt.', boundary: 'Version đã phát hành bất biến; sửa đổi tạo version mới và cần review.', steps: [
    { eyebrow: '01 · BẢN NHÁP', title: 'Nội dung hoạt động', summary: 'Hoạt động phù hợp trẻ mầm non, ngắn và dễ chuẩn bị.', fields: [{ id: 'title', label: 'Tên hoạt động', required: true }, { id: 'kind', label: 'Loại hoạt động', kind: 'select', options: ['Ngoài trời', 'Trong nhà', 'Kết hợp'], required: true }, { id: 'instructions', label: 'Cách thực hiện', kind: 'textarea', required: true }] },
    { eyebrow: '02 · AN TOÀN', title: 'Rà soát vật liệu', summary: 'Ghi rõ vật liệu, chuẩn bị và lưu ý an toàn trước khi phát hành.', fields: [{ id: 'materials', label: 'Vật liệu và chuẩn bị', kind: 'textarea', required: true }, { id: 'safety', label: 'Lưu ý an toàn', kind: 'textarea', required: true }, { id: 'reviewed', label: 'Tôi đã kiểm tra nội dung và version', kind: 'checkbox', required: true }] },
    { eyebrow: '03 · PHÁT HÀNH', title: 'Version được xuất bản', summary: 'Chỉ version đã duyệt mới hiển thị như nội dung dùng được.', note: 'Bản xem trước không xuất bản lên catalog thật.' },
  ] },
  sharing: { title: 'Chia sẻ giáo án', description: 'Chọn đúng phiên bản và người nhận trước khi gửi lời mời.', boundary: 'Lời mời, quyền đọc và thu hồi cần Lesson Library API; người nhận chưa chấp nhận thì chưa có quyền.', steps: [
    { eyebrow: '01 · PHIÊN BẢN', title: 'Chọn giáo án', summary: 'Lời mời gắn với một phiên bản cụ thể, không tự trỏ sang bản mới nhất.', fields: [{ id: 'lesson', label: 'Giáo án và phiên bản', kind: 'select', options: ['Khám phá khu vườn · v1.4', 'Bầu trời kỳ diệu · v2.0'], required: true }, { id: 'shareScope', label: 'Đối tượng nhận', kind: 'select', options: ['Một tài khoản phụ huynh', 'Nhóm gia đình đã xác minh'], required: true }] },
    { eyebrow: '02 · NGƯỜI NHẬN', title: 'Nhập người nhận', summary: 'Dùng email hoặc nhóm đã được xác minh trong tổ chức.', fields: [{ id: 'recipient', label: 'Email tài khoản hoặc tên nhóm', required: true, placeholder: 'Nhập email hoặc chọn nhóm đã xác minh' }, { id: 'shareReason', label: 'Lời nhắn (không bắt buộc)', kind: 'textarea', placeholder: 'Ghi một lời nhắn ngắn cho gia đình' }] },
    { eyebrow: '03 · XÁC NHẬN', title: 'Rà soát lời mời', summary: 'Sau khi gửi, theo dõi trạng thái chờ chấp nhận; có thể thu hồi khi API hỗ trợ.', fields: [{ id: 'shareConfirm', label: 'Tôi đã kiểm tra đúng phiên bản, người nhận và quyền chia sẻ', kind: 'checkbox', required: true }], note: 'Hoàn tất trong preview chỉ mô phỏng trạng thái lời mời; chưa gửi email hoặc cấp quyền thật.' },
  ] },
  accounts: { title: 'Tài khoản nền tảng', description: 'Tra cứu tài khoản, rà soát vai trò và chuẩn bị thay đổi quyền có kiểm soát.', boundary: 'Danh sách và cập nhật tài khoản cần Platform Admin API, permission hợp lệ và audit; preview không thay đổi quyền thật.', steps: [
    { eyebrow: '01 · TRA CỨU', title: 'Tìm tài khoản', summary: 'Không tự tạo tài khoản hoặc cấp role từ màn đăng ký công khai.', fields: [{ id: 'account', label: 'Email hoặc mã tài khoản', required: true, placeholder: 'ten@tochuc.vn' }, { id: 'accountRole', label: 'Vai trò hiện tại (nếu đã biết)', kind: 'select', options: ['Phụ huynh', 'Giáo viên', 'Quản lý trường', 'Quản trị nền tảng'] }] },
    { eyebrow: '02 · ĐỀ XUẤT', title: 'Chọn thay đổi cần rà soát', summary: 'Chỉ đề xuất quyền phù hợp với hồ sơ và tổ chức đã xác minh.', fields: [{ id: 'accountAction', label: 'Thao tác', kind: 'select', options: ['Tạm khóa tài khoản', 'Mở lại tài khoản', 'Rà soát thay đổi vai trò'], required: true }, { id: 'requestedRole', label: 'Vai trò đề xuất', kind: 'select', options: ['Phụ huynh', 'Giáo viên', 'Quản lý trường', 'Quản trị nền tảng'], requiredWhen: { field: 'accountAction', value: 'Rà soát thay đổi vai trò' } }, { id: 'accountReason', label: 'Lý do và phạm vi', kind: 'textarea', required: true, placeholder: 'Ghi rõ căn cứ và tổ chức liên quan' }, { id: 'accountConfirm', label: 'Tôi đã kiểm tra danh tính và quyền vận hành', kind: 'checkbox', required: true }] },
  ] },
};

const operationSpecs: Record<string, Operation> = {
  history: { title: 'Lịch sử buổi dạy', description: 'Theo dõi occurrence và run mẫu theo lớp đang phụ trách.', boundary: 'Trạng thái thật và quyền đọc media cần Story/Lesson API.', items: [{ title: 'Khám phá khu vườn', detail: 'Lớp Lá 1 · occurrence minh họa', state: 'Đang chuẩn bị' }, { title: 'Bầu trời kỳ diệu', detail: 'Lớp Lá 1 · occurrence minh họa', state: 'Đã hoàn tất' }] },
  quota: { title: 'Lượt tạo video của trường', description: 'Giáo viên chỉ xem quota organization; Quản lý trường xem entitlement và kỳ.', boundary: 'Số còn lại, usage và grant phải lấy từ Billing. Quyền mua thêm quota đang OPEN.', items: [{ title: 'Lượt trong kỳ', detail: 'Số liệu chờ Billing API', state: 'Chưa kết nối' }, { title: 'Yêu cầu đã nhận', detail: 'Mỗi request accepted dùng một lượt, kể cả lỗi', state: 'Quy tắc hệ thống' }, { title: 'Video đã lưu', detail: 'Hết quota vẫn xem được nội dung cũ', state: 'Quyền truy cập' }] },
  inbox: { title: 'Hộp thư thông báo', description: 'Thông báo trong app là nguồn chuẩn; push/email chỉ hỗ trợ.', boundary: 'Inbox thật cần Notifications API, quyền tài khoản và trạng thái đã đọc.', items: [{ title: 'Chưa có thông báo thật', detail: 'Nhắc run và job sẽ xuất hiện tại đây khi API sẵn sàng.', state: 'Trống' }] },
  notifications: { title: 'Thông báo tổ chức', description: 'Nhắc gia hạn trước 7 ngày và 1 ngày, cập nhật thanh toán.', boundary: 'Ngày hạn và trạng thái chỉ lấy từ Billing/Notifications.', items: [{ title: 'Gia hạn và thanh toán', detail: 'Chưa có thông báo từ API', state: 'Trống' }, { title: 'Phân công và lớp', detail: 'Sự kiện thuộc organization của bạn', state: 'Theo quyền' }] },
  jobs: { title: 'Tác vụ AI', description: 'Theo dõi queue, stage và lỗi bằng metadata đã lọc.', boundary: 'Không mở prompt, ảnh, transcript hay video trẻ từ trang vận hành.', items: [{ title: 'Queue hiện tại', detail: 'Chờ AI Jobs API', state: 'Chưa kết nối' }, { title: 'Lỗi có thể thử lại', detail: 'Chỉ safe error code và correlation ID', state: 'Chưa kết nối' }] },
  health: { title: 'Sức khỏe nền tảng', description: 'Readiness, queue và backlog lifecycle bằng metadata đã lọc.', boundary: 'Chỉ metadata đã redact; số liệu live cần probe và quyền operator.', items: [{ title: 'API readiness', detail: 'Chờ health probe', state: 'Chưa kết nối' }, { title: 'Queue AI', detail: 'Chờ queue metrics', state: 'Chưa kết nối' }, { title: 'Lifecycle backlog', detail: 'Chỉ hiển thị số lượng và nhóm tuổi dữ liệu; không mở ID trẻ hoặc media.', state: 'Chờ API · metadata-only' }] },
  'billing-ops': { title: 'Đối soát thanh toán', description: 'Theo dõi invoice, callback và entitlement đã xác minh.', boundary: 'Không đánh dấu thanh toán thành công theo browser redirect.', items: [{ title: 'Invoice cần đối soát', detail: 'Chờ Billing API', state: 'Chưa kết nối' }, { title: 'Callback provider', detail: 'Đối chiếu idempotency và chữ ký', state: 'Chưa kết nối' }] },
  audit: { title: 'Nhật ký vận hành', description: 'Truy vết quyết định theo actor, thời điểm và revision.', boundary: 'Log phải lọc token, thông tin trẻ và media.', items: [{ title: 'Quyết định duyệt nội dung', detail: 'Chờ Audit API', state: 'Chưa kết nối' }, { title: 'Thay đổi tổ chức', detail: 'Chờ Audit API', state: 'Chưa kết nối' }] },
  accounts: { title: 'Tài khoản nền tảng', description: 'Tra cứu tài khoản và trạng thái cấp quyền.', boundary: 'Role và permission chỉ được quản lý qua API có kiểm tra quyền; đăng ký web không tự cấp vai trò.', items: [{ title: 'Tài khoản đang hoạt động', detail: 'Chờ API account list có phân quyền', state: 'Chưa kết nối' }, { title: 'Yêu cầu cấp quyền', detail: 'Chờ contract mời, duyệt và thu hồi', state: 'Chưa kết nối' }] },
};

function FieldControl({ field, value, onChange }: { field: Field; value: string | boolean; onChange: (value: string | boolean) => void }) {
  const required = field.required ?? false;
  if (field.kind === 'checkbox') return <label className="flow-check"><input type="checkbox" checked={Boolean(value)} required={required} onChange={(event) => onChange(event.target.checked)}/><span>{field.label}</span></label>;
  return <label className="flow-field"><span>{field.label}{required && <b aria-hidden="true"> *</b>}</span>{field.kind === 'textarea' ? <textarea value={String(value ?? '')} required={required} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)} rows={4}/> : field.kind === 'select' ? <select value={String(value ?? '')} required={required} onChange={(event) => onChange(event.target.value)}><option value="">Chọn một mục</option>{field.options?.map((option) => <option key={option}>{option}</option>)}</select> : field.kind === 'file' ? <input type="file" accept={field.id === 'lessonFile' ? '.pdf,.pptx,.docx' : 'image/*'} required={required && !value} onChange={(event) => { const file = event.target.files?.[0]; if (file && field.id === 'lessonFile' && file.size > 25 * 1024 * 1024) { event.target.value = ''; event.target.setCustomValidity('Giáo án tối đa 25 MB.'); event.target.reportValidity(); onChange(''); return; } event.target.setCustomValidity(''); onChange(file?.name ?? ''); }}/>: <input type={field.kind === 'date' ? 'date' : 'text'} value={String(value ?? '')} required={required} placeholder={field.placeholder} onChange={(event) => onChange(event.target.value)}/ >}{field.hint && <small>{field.hint}</small>}</label>;
}

function VideoSurface({ presentation }: { presentation: boolean }) {
  return <div className="flow-video"><div className="flow-video-canvas" role="img" aria-label="Khung trình phát video chưa có dữ liệu"><div className="flow-video-paper"><i/><i/><i/></div><span className="flow-video-play" aria-hidden="true">▶</span><small>VIDEO MẪU · CHƯA CÓ API</small></div><div className="flow-video-footer"><span><strong>{presentation ? 'Bề mặt chiếu cho lớp' : 'Video chỉ phát trong buổi dạy'}</strong><small>Chờ playback token ngắn hạn và kiểm tra an toàn từ server.</small></span><button type="button" disabled aria-label="Phát video chưa khả dụng">Phát video</button></div></div>;
}

function JobStages() {
  return <div className="flow-job-stages" aria-label="Các trạng thái tạo video"><div><b>01</b><span><strong>Kiểm tra lượt tạo</strong><small>Quota và compute cùng được chấp nhận</small></span></div><div><b>02</b><span><strong>Tạo cảnh và lời kể</strong><small>Hiển thị stage thật từ AI Jobs API</small></span></div><div><b>03</b><span><strong>Kiểm tra an toàn</strong><small>Chặn video chưa đạt trước playback</small></span></div><div><b>04</b><span><strong>Video sẵn sàng</strong><small>Giáo viên xem riêng trước khi chiếu</small></span></div></div>;
}

function BillingInvoicePanel() {
  return <section className="flow-invoice-panel" aria-labelledby="invoice-panel-title"><div className="flow-invoice-title"><strong id="invoice-panel-title">Chi tiết hóa đơn</strong><span>Chờ Billing API</span></div><p>Hóa đơn, số tiền và hạn thanh toán sẽ chỉ hiện sau khi backend xác minh dữ liệu.</p><dl><div><dt>Mã hóa đơn</dt><dd>—</dd></div><div><dt>Kỳ dịch vụ</dt><dd>—</dd></div><div><dt>Ngày phát hành</dt><dd>—</dd></div><div><dt>Hạn thanh toán</dt><dd>—</dd></div><div><dt>Tổng tiền</dt><dd>—</dd></div><div><dt>Trạng thái</dt><dd>Chưa có dữ liệu</dd></div></dl><div className="flow-invoice-actions"><button type="button" disabled>Tải hóa đơn</button><button type="button" disabled>Thanh toán</button></div></section>;
}

type RecoveryKind = 'loading' | 'denied' | 'stale' | 'retryable' | 'blocked' | 'reconcile' | 'deleting' | 'empty';
type RecoveryCase = { code: string; title: string; next: string; kind?: RecoveryKind };

function recoveryCasesFor(title: string): RecoveryCase[] {
  const cases: RecoveryCase[] = [
    { code: 'LOADING', title: 'Đang tải dữ liệu', next: 'Giữ nguyên bố cục và thao tác đang nhập; không tạo nút giả hoặc nhảy layout.', kind: 'loading' },
    { code: 'AUTH_REQUIRED / TOKEN_EXPIRED', title: 'Phiên đăng nhập cần xác thực lại', next: 'Giữ bản nháp, xác thực lại rồi tải lại quyền trước khi tiếp tục.', kind: 'denied' },
    { code: 'FORBIDDEN / ROLE_MISMATCH', title: 'Không đủ quyền hoặc sai vai trò', next: 'Không mở dữ liệu; quay về cổng phù hợp hoặc liên hệ người quản trị tổ chức.', kind: 'denied' },
    { code: 'RESOURCE_NOT_FOUND', title: 'Không tìm thấy hoặc không còn quyền truy cập', next: 'Làm mới danh sách trong phạm vi được cấp; không thử lại cùng mã tài nguyên.', kind: 'denied' },
    { code: 'STALE_REVISION', title: 'Dữ liệu đã có phiên bản mới', next: 'Giữ bản nháp, tải revision hiện hành, so sánh thay đổi và yêu cầu người lớn rà soát lại.', kind: 'stale' },
    { code: 'RETRYABLE_FAILURE', title: 'Lỗi tạm thời · có thể thử lại', next: 'Chỉ thử lại khi server trả retryable=true; giữ nguyên dữ liệu nhập và chống gửi trùng.', kind: 'retryable' },
    { code: 'NON_RETRYABLE_FAILURE', title: 'Lỗi không thể tự thử lại', next: 'Giữ dữ liệu, không hiện nút thử lại; chuyển tới hỗ trợ hoặc người có quyền xử lý.', kind: 'blocked' },
    { code: 'RATE_LIMITED', title: 'Thao tác đang bị giới hạn tốc độ', next: 'Chờ thời điểm server cho phép rồi chủ động thử lại một lần.', kind: 'retryable' },
    { code: 'NETWORK_UNKNOWN', title: 'Chưa rõ lệnh đã được nhận hay chưa', next: 'Giữ nội dung và kiểm tra trạng thái cùng mã yêu cầu trước khi gửi lại.', kind: 'reconcile' },
    { code: 'AWAITING_RECONCILIATION', title: 'Đang đối soát trạng thái', next: 'Giữ cùng request/idempotency key; không gửi lệnh mới khi kết quả chưa rõ.', kind: 'reconcile' },
    { code: 'DELETE_PENDING', title: 'Yêu cầu xóa đang chờ', next: 'Khóa dữ liệu liên quan đến run mới; chỉ kết thúc khi lifecycle server xác nhận.', kind: 'deleting' },
    { code: 'EMPTY_RESULTS', title: 'Chưa có dữ liệu trong danh sách', next: 'Giữ bộ lọc và hướng dẫn bước tiếp theo; không hiển thị số liệu hoặc bản ghi giả.', kind: 'empty' },
  ];
  if (/video|run|kịch bản|story|quota|lượt tạo/i.test(title)) cases.push(
    { code: 'ACTIVE_RUN_EXISTS', title: 'Đã có run đang hoạt động', next: 'Mở run hiện tại hoặc hủy theo lifecycle hợp lệ; không tạo run thứ hai.' },
    { code: 'TRANSCRIPT_NOT_CONFIRMED / SUBJECT_NOT_CONFIRMED / PROFILE_CONTEXT_NOT_CONFIRMED', title: 'Còn bước duyệt của người lớn', next: 'Quay lại đúng màn transcript, chủ thể hoặc context và xác nhận revision hiện tại.' },
    { code: 'STORY_REWRITE_LIMIT_REACHED', title: 'Đã hết lượt yêu cầu viết lại', next: 'Giữ kịch bản hiện tại để người lớn xác nhận hoặc dừng run.' },
    { code: 'VIDEO_QUOTA_EXCEEDED / AI_COST_LIMIT_REACHED', title: 'Chưa thể nhận yêu cầu tạo', next: 'Không gửi lặp; chỉ tiếp tục sau khi entitlement và trạng thái admission được xác minh.' },
    { code: 'PROVIDER_UNAVAILABLE / SAFETY_REJECTED', title: 'Dịch vụ tạm ngừng hoặc nội dung chưa đạt kiểm tra', next: 'Giữ nội dung an toàn, không mở player; chỉ thử lại nếu trạng thái server cho phép.' },
    { code: 'AWAITING_RECONCILIATION', title: 'Đang đối soát trạng thái tạo', next: 'Theo dõi cùng job/idempotency key; không tạo request khác khi kết quả chưa rõ.' },
    { code: 'DELETE_PENDING', title: 'Đang chờ xóa dữ liệu', next: 'Giữ thao tác liên quan ở trạng thái khóa và kiểm tra lifecycle đến khi server xác nhận.' },
  );
  if (/nhập|tài liệu|giáo án/i.test(title)) cases.push(
    { code: 'FILE_REJECTED / PARSE_FAILED', title: 'Tệp không đọc được', next: 'Giữ bản gốc, nêu định dạng/lý do cụ thể và cho chọn tệp khác hoặc sửa nội dung thủ công.' },
    { code: 'UNSUPPORTED_LESSON_TYPE / LESSON_FILE_TOO_LARGE', title: 'Tệp vượt loại hoặc giới hạn được hỗ trợ', next: 'Giữ nội dung đã nhập và thay bằng PDF, PPTX hoặc DOCX hợp lệ theo giới hạn server.' },
  );
  if (/mời|chia sẻ|nhóm/i.test(title)) cases.push(
    { code: 'INVITATION_EXPIRED / ALREADY_ACCEPTED', title: 'Lời mời đã hết hạn hoặc được chấp nhận', next: 'Làm mới trạng thái trước khi gửi lại; không cấp quyền từ trạng thái chờ.' },
  );
  if (/thanh toán|hóa đơn|capacity|sức chứa|lớp/i.test(title)) cases.push(
    { code: 'PAYMENT_PENDING / CALLBACK_UNVERIFIED', title: 'Thanh toán chưa được xác minh', next: 'Giữ entitlement hiện tại; chỉ dùng trạng thái callback đã được backend đối soát.' },
    { code: 'CLASS_CAPACITY_REACHED / SUBSCRIPTION_RESTRICTED', title: 'Lớp hoặc gói đang bị giới hạn', next: 'Giữ dữ liệu hiện có và hướng đến thao tác Billing được cấp quyền; không tự đổi entitlement.' },
  );
  if (/duyệt|catalog|nội dung|phát hành/i.test(title)) cases.push(
    { code: 'REVIEW_REJECTED / PUBLISH_NOT_ALLOWED', title: 'Nội dung cần sửa hoặc chưa đủ quyền phát hành', next: 'Giữ nguyên version đã phát hành, tạo revision mới và ghi lý do review.' },
  );
  if (/feedback|phản hồi|hỗ trợ/i.test(title)) cases.push(
    { code: 'FEEDBACK_SUBMIT_FAILED', title: 'Phản hồi chưa gửi được', next: 'Giữ bản nháp, kiểm tra phạm vi organization và thử lại khi service xác nhận trạng thái.' },
  );
  return cases;
}

type SampleChoice = 'not-checked' | 'ready' | 'confirmed' | 'declined' | 'none-eligible';

function TeacherSampleSelection({choice, onChange}: {choice: SampleChoice; onChange: (value: SampleChoice) => void}) {
  return <section className="sample-selection-card" aria-labelledby="sample-selection-heading">
    <div className="sample-selection-heading"><span className="flow-eyebrow">KẾT QUẢ HỆ THỐNG · MINH HỌA</span><h3 id="sample-selection-heading">Chọn một trẻ đủ điều kiện</h3><p>Teacher không tự chọn trẻ. Kết quả thật cần API kiểm tra roster và consent.</p></div>
    {choice === 'not-checked' ? <div className="sample-selection-empty"><span aria-hidden="true">◎</span><strong>Chưa có kết quả kiểm tra</strong><small>Không tạo run trước khi có kết quả và xác nhận của giáo viên.</small></div> : null}
    {choice === 'ready' || choice === 'confirmed' ? <article className={`sample-selection-result${choice === 'confirmed' ? ' is-confirmed' : ''}`} role="status"><span className="sample-selection-avatar" aria-hidden="true">A</span><div><strong>Trẻ minh họa · nhóm 4–5 tuổi</strong><small>Đủ điều kiện · consent hợp lệ trong fixture</small></div><span className="preview-state preview-state--ready">{choice === 'confirmed' ? 'ĐÃ XÁC NHẬN · PREVIEW' : 'CHỜ GIÁO VIÊN'}</span></article> : null}
    {choice === 'none-eligible' ? <div className="flow-recovery-detail flow-recovery-detail--warning" role="status"><span>NO_ELIGIBLE_CHILD · PREVIEW</span><strong>Chưa có trẻ phù hợp</strong><p>Không tạo run. Cách chọn lại hoặc thay đổi eligibility đang OPEN; preview không tự chọn trẻ khác.</p></div> : null}
    {choice === 'declined' ? <div className="flow-recovery-detail flow-recovery-detail--warning" role="status"><span>SELECTION_DECLINED · PREVIEW</span><strong>Luồng đã dừng</strong><p>Không tạo run hay chuyển tranh. Quy tắc chọn lại đang OPEN; chỉ tiếp tục khi API trả kết quả hợp lệ mới.</p></div> : null}
    <div className="sample-selection-actions">
      <button type="button" className="flow-secondary" onClick={() => onChange('ready')}>Xem eligibility fixture</button>
      <button type="button" className="flow-secondary" onClick={() => onChange('none-eligible')}>Xem nhánh không có trẻ · fixture</button>
      {choice === 'ready' ? <><button type="button" className="flow-primary" onClick={() => onChange('confirmed')}>Xác nhận trẻ này · preview</button><button type="button" className="flow-danger" onClick={() => onChange('declined')}>Từ chối và dừng</button></> : null}
      {choice !== 'ready' && choice !== 'confirmed' && choice !== 'not-checked' ? <button type="button" className="flow-secondary" onClick={() => onChange('not-checked')}>Quay lại trạng thái chờ</button> : null}
    </div>
    <small className="sample-selection-boundary">Dữ liệu hoàn toàn minh họa; không chứa danh tính trẻ và không gọi eligibility/consent API.</small>
  </section>;
}

const teacherSessionActivities = [
  { id: 'observe', title: 'Quan sát một bông hoa', prompt: 'Con nhìn thấy những màu sắc và hình dạng nào?', materials: 'Một bông hoa hoặc cây nhỏ' },
  { id: 'draw', title: 'Vẽ khu vườn nhỏ', prompt: 'Mời bé vẽ nơi chú bướm muốn ghé thăm.', materials: 'Giấy và bút màu' },
  { id: 'colors', title: 'Tìm màu trong vườn', prompt: 'Cùng bé tìm ba màu con thấy quanh mình.', materials: 'Không cần vật liệu' },
] as const;

const teacherSketchSlides = [
  { title: 'Bắt đầu bằng hình lớn', note: 'Phác một hình tròn hoặc bầu dục cho bông hoa.' },
  { title: 'Thêm cánh và thân', note: 'Mời bé chọn số cánh và nét thân theo ý mình.' },
  { title: 'Thêm màu con thích', note: 'Bé tự chọn màu và kể điều bé quan sát được.' },
] as const;

function TeacherSessionWorkspace() {
  const [className, setClassName] = useState('Lớp Lá 1');
  const [lessonId, setLessonId] = useState('garden');
  const [activityId, setActivityId] = useState<(typeof teacherSessionActivities)[number]['id']>('observe');
  const [sessionStage, setSessionStage] = useState<'setup' | 'slides' | 'interaction' | 'sample' | 'ended'>('setup');
  const [deckEnabled, setDeckEnabled] = useState(false);
  const [slideIndex, setSlideIndex] = useState(0);
  const [notice, setNotice] = useState('');
  const started = sessionStage !== 'setup';
  const ended = sessionStage === 'ended';
  const activity = teacherSessionActivities.find((item) => item.id === activityId) ?? teacherSessionActivities[0];
  const lessonTitle = lessonId === 'garden' ? 'Khám phá khu vườn · v1.4' : 'Bầu trời kỳ diệu · v2.0';
  const slide = teacherSketchSlides[slideIndex];
  const startPreviewSession = () => {
    setSessionStage(deckEnabled ? 'slides' : 'interaction');
    setSlideIndex(0);
    setNotice('Phiên này chỉ chạy trong trình duyệt; backend chưa nhận lệnh.');
  };

  return <div className="flow-page teacher-session-page">
    <header className="flow-heading"><span>BUỔI DẠY · BẢN XEM TRƯỚC</span><h1>{ended ? 'Buổi dạy đã kết thúc' : started ? 'Không gian buổi dạy' : 'Chuẩn bị cùng lớp'}</h1><p>{started && !ended ? 'Lần lượt trình chiếu hướng dẫn, tương tác với hoạt động rồi mới mở luồng video mẫu riêng.' : 'Chọn lớp, phiên bản giáo án và hoạt động trước khi bắt đầu.'}</p></header>
    <div className="feedback-preview-note" role="note"><strong>Chưa kết nối occurrence / run API</strong><span>Lớp, plan và trạng thái bên dưới là fixture trong trình duyệt; chưa mở phiên dạy thật hoặc gửi dữ liệu trẻ.</span></div>
    <div className="teacher-session-layout">
      <section className="teacher-session-setup" aria-label="Cấu hình buổi dạy">
        <div className="teacher-session-panel-heading"><span className="flow-eyebrow">THÔNG TIN BUỔI DẠY</span><b>PREVIEW</b></div>
        <label className="teacher-session-field">1 · Lớp được phân công<select value={className} disabled={started && !ended} onChange={(event) => setClassName(event.target.value)}><option>Lớp Lá 1</option><option>Lớp Chồi 2</option></select></label>
        <label className="teacher-session-field">2 · Giáo án và phiên bản<select value={lessonId} disabled={started && !ended} onChange={(event) => setLessonId(event.target.value)}><option value="garden">Khám phá khu vườn · v1.4</option><option value="sky">Bầu trời kỳ diệu · v2.0</option></select></label>
        <div className="teacher-session-field"><span>3 · Chọn hoạt động đã ghim</span><div className="teacher-session-activity-list">{teacherSessionActivities.map((item) => <button type="button" key={item.id} disabled={started && !ended} className={activityId === item.id ? 'is-selected' : ''} onClick={() => setActivityId(item.id)} aria-pressed={activityId === item.id}><span><strong>{item.title}</strong><small>{item.materials}</small></span><i>{activityId === item.id ? '✓' : ''}</i></button>)}</div></div>
        <label className="teacher-session-deck-choice"><input type="checkbox" checked={deckEnabled} disabled={started && !ended} onChange={(event) => { setDeckEnabled(event.target.checked); setSlideIndex(0); }}/><span><strong>Hiện slide / Sketch (tùy chọn)</strong><small>Bắt đầu với 3 bước minh họa tĩnh; có thể bỏ qua.</small></span></label>
        <a className="teacher-session-plan-link" href="#occurrences">Xem plan và chuẩn bị occurrence <span aria-hidden="true">→</span></a>
        {!started ? <button type="button" className="flow-primary teacher-session-start" onClick={startPreviewSession}>Bắt đầu buổi học · preview <span aria-hidden="true">→</span></button> : null}
        {ended ? <button type="button" className="flow-secondary teacher-session-start" onClick={() => { setSessionStage('setup'); setNotice(''); }}>Chuẩn bị buổi khác</button> : null}
      </section>

      <section className="teacher-session-stage" aria-label="Nội dung buổi dạy">
        <div className="teacher-session-sequence" aria-label="Tiến trình buổi dạy"><span className={['slides', 'interaction', 'sample', 'ended'].includes(sessionStage) ? 'is-done' : 'is-current'}>01 · Show Slide / Sketch</span><i aria-hidden="true">→</i><span className={['interaction', 'sample', 'ended'].includes(sessionStage) ? sessionStage === 'interaction' ? 'is-current' : 'is-done' : ''}>02 · Hoạt động</span><i aria-hidden="true">→</i><span className={['sample', 'ended'].includes(sessionStage) ? sessionStage === 'sample' ? 'is-current' : 'is-done' : ''}>03 · Video mẫu riêng</span></div>
        {!started ? <div className="teacher-session-empty"><span>01</span><strong>Sẵn sàng trình bày hoạt động</strong><p>Chọn lớp → giáo án → hoạt động, rồi bắt đầu buổi học.</p><div className="teacher-session-activity-preview"><b>{activity.title}</b><span>{activity.prompt}</span></div></div> : ended ? <div className="teacher-session-ended" role="status"><strong>Buổi học mẫu đã kết thúc.</strong><p>Không có session, học sinh, ảnh hoặc kết quả nào được lưu lên máy chủ.</p><span>{activity.title}</span></div> : sessionStage === 'slides' ? <section className="teacher-session-deck" aria-label="Trình chiếu slide và Sketch"><div className="teacher-session-deck-stage"><span>SHOW SLIDE · SKETCH · MINH HỌA TĨNH · {slideIndex + 1}/3</span><div className={`teacher-session-sketch teacher-session-sketch--${slideIndex + 1}`} aria-hidden="true"><i/><b/><em/></div><strong>{slide.title}</strong><small>{slide.note}</small></div><div className="teacher-session-deck-controls"><button type="button" disabled={slideIndex === 0} onClick={() => setSlideIndex((index) => Math.max(0, index - 1))}>← Slide trước</button><span>Slide {slideIndex + 1} / 3</span><button type="button" onClick={() => { if (slideIndex < teacherSketchSlides.length - 1) setSlideIndex((index) => index + 1); else setSessionStage('interaction'); }}>{slideIndex < teacherSketchSlides.length - 1 ? 'Slide tiếp →' : 'Hoàn tất · sang hoạt động'}</button><button type="button" className="teacher-session-skip" onClick={() => { setSessionStage('interaction'); setNotice('Đã bỏ qua slide / Sketch; hoạt động tiếp tục trong preview.'); }}>Bỏ qua slide</button></div></section> : sessionStage === 'interaction' ? <>
          <article className="teacher-session-activity-card"><span>BƯỚC 02 · HOẠT ĐỘNG TƯƠNG TÁC</span><strong>{activity.title}</strong><p>{activity.prompt}</p><small>Chuẩn bị: {activity.materials}</small></article>
          <section className="teacher-session-interaction" aria-label="Hoạt động tương tác"><div><strong>Cùng bé trao đổi</strong><p>Mời bé trả lời câu hỏi hoặc thực hiện hoạt động đã chọn.</p></div><button type="button" onClick={() => setSessionStage('sample')}>Hoàn tất hoạt động</button></section>
        </> : <aside className="teacher-session-sample-gate"><div><span className="preview-state">BƯỚC 03 · LUỒNG RIÊNG · PREVIEW</span><strong>Video mẫu không thuộc buổi học cả lớp</strong><p>Luồng riêng phải kiểm tra eligibility và consent trước khi chọn trẻ, rồi mới cho phép chụp tranh. Không dùng hoặc gắn media của lớp.</p></div><a className="flow-primary" href="#sample">Tiếp tục đến bước chụp tranh mẫu <span aria-hidden="true">→</span></a><button type="button" className="flow-secondary" onClick={() => setSessionStage('interaction')}>Quay lại hoạt động</button></aside>}
        {started && !ended && <div className="teacher-session-actions"><button type="button" className="flow-primary" onClick={() => { setSessionStage('ended'); setNotice('Buổi học kết thúc trong phiên xem trước; không gửi lệnh đến server.'); }}>Kết thúc buổi học · preview</button></div>}
        {notice && <p className="teacher-session-notice" role="status">{notice}</p>}
        <p className="teacher-session-boundary">Tranh và media của trẻ không được dùng từ màn này. Luồng mẫu riêng phải có eligibility, consent và xác nhận hợp lệ từ API trước bước chụp; hiện chỉ là fixture.</p>
      </section>
    </div>
    <FlowRecoveryDisclosure title="Buổi dạy của giáo viên" boundary="Mở occurrence, ghim revision, roster, consent, run và playback cần API authenticated cùng quyền lớp hiện hành."/>
  </div>;
}

function ManagerTransferWorkbench() {
  const [className, setClassName] = useState('Lớp Lá 1');
  const [replacement, setReplacement] = useState('Cô Trần Lan');
  const [scenario, setScenario] = useState<'no-conflict' | 'active-run' | 'compensation-pending'>('active-run');
  const [reason, setReason] = useState('');
  const [forceConfirmed, setForceConfirmed] = useState(false);
  const [status, setStatus] = useState<'idle' | 'transfer-preview' | 'abandoned-preview' | 'reconciled-preview'>('idle');
  const [notice, setNotice] = useState('');
  const forceClose = (): void => {
    if (!reason.trim() || !forceConfirmed || scenario !== 'active-run') return;
    setStatus('abandoned-preview');
    setNotice('Run mẫu đã chuyển sang ABANDONED trong preview; media và quota vẫn được giữ, chưa có command thật.');
    setForceConfirmed(false);
  };
  const reconcile = (): void => {
    setStatus('reconciled-preview');
    setNotice('Trạng thái đã được đánh dấu nhất quán trong fixture; không chạy compensation hoặc cấp quyền thật.');
  };
  const retryTransfer = (): void => {
    if (scenario === 'active-run' && status !== 'abandoned-preview') return;
    if (scenario === 'compensation-pending' && status !== 'reconciled-preview') return;
    setStatus('transfer-preview');
    setNotice('Đã mô phỏng transfer-pending → receipt → finalize; lớp và quyền thật chưa thay đổi.');
  };
  return <div className="flow-page"><header className="flow-heading"><span>ĐIỀU HÀNH NHÀ TRƯỜNG · BẢN XEM TRƯỚC</span><h1>Đổi giáo viên phụ trách</h1><p>Kiểm tra xung đột trước khi chuyển lớp; mọi command trong trang này chỉ là fixture.</p></header>
    <div className="feedback-preview-note" role="note"><strong>Chưa kết nối transfer API</strong><span>Quyền force-close, assignment version và audit phải do server xác nhận. Không hiển thị nội dung run.</span></div>
    <section className="transfer-workbench"><div className="transfer-form-grid"><label>Lớp<select value={className} onChange={(event) => { setClassName(event.target.value); setStatus('idle'); setNotice(''); setReason(''); setForceConfirmed(false); }}><option>Lớp Lá 1</option><option>Lớp Chồi 2</option></select></label><label>Giáo viên nhận bàn giao<select value={replacement} onChange={(event) => { setReplacement(event.target.value); setStatus('idle'); setNotice(''); setReason(''); setForceConfirmed(false); }}><option>Cô Trần Lan</option><option>Cô Phạm Hà</option></select></label><label className="transfer-scenario-field">Tình huống minh họa<select value={scenario} onChange={(event) => { setScenario(event.target.value as typeof scenario); setStatus('idle'); setNotice(''); setReason(''); setForceConfirmed(false); }}><option value="no-conflict">Không có run đang hoạt động</option><option value="active-run">Có run đang hoạt động · xung đột</option><option value="compensation-pending">Saga đang chờ đối soát</option></select></label></div>
      <div className="transfer-lifecycle" aria-label="Các trạng thái chuyển giao"><span className={status === 'transfer-preview' ? 'is-current' : ''}>Transfer pending · lớp chỉ đọc</span><i aria-hidden="true">→</i><span className={status === 'transfer-preview' ? 'is-current' : ''}>Story receipt</span><i aria-hidden="true">→</i><span className={status === 'transfer-preview' ? 'is-current' : ''}>Finalize assignment</span></div>
      {scenario === 'no-conflict' && status === 'idle' ? <div className="flow-recovery-detail" role="status"><span>PREFLIGHT · PREVIEW</span><strong>Không có xung đột run</strong><p>Luồng thật vẫn phải tải lại quyền, assignment version và nhận receipt từ Story trước khi mở quyền cho giáo viên mới.</p><button className="flow-primary" type="button" onClick={retryTransfer}>Xem kết quả chuyển giao · preview</button></div> : null}
      {scenario === 'active-run' && status !== 'abandoned-preview' && status !== 'transfer-preview' ? <section className="transfer-conflict-card"><span className="preview-state preview-state--paused">ACTIVE_RUN_CONFLICT · PREVIEW</span><h2>Run đang mở khóa lượt chuyển</h2><p>Chuyển thường chưa thể tiếp tục. Chỉ School Manager có permission phù hợp mới được xem xét force-close riêng.</p><label>Lý do khẩn cấp · bắt buộc<textarea rows={3} maxLength={400} value={reason} onChange={(event) => { setReason(event.target.value); setForceConfirmed(false); }} placeholder="Ghi căn cứ cần đóng run; không nhập nội dung của trẻ"/></label><label className="flow-check"><input type="checkbox" checked={forceConfirmed} onChange={(event) => setForceConfirmed(event.target.checked)}/><span>Tôi xác nhận force-close riêng: run thành ABANDONED; không xóa media và không hoàn quota.</span></label><button className="flow-danger" type="button" disabled={!reason.trim() || !forceConfirmed} onClick={forceClose}>Rà soát force-close · preview</button><small>Lệnh thật cần reason, permission và audit metadata từ server; preview không gửi lệnh.</small></section> : null}
      {status === 'abandoned-preview' ? <div className="flow-recovery-detail" role="status"><span>ABANDONED · PREVIEW</span><strong>Run mẫu đã được force-close minh họa</strong><p>Media không bị xóa, quota đã nhận vẫn giữ nguyên và School Manager không được xem nội dung. Có thể xem trước bước retry transfer.</p><button className="flow-primary" type="button" onClick={retryTransfer}>Thử chuyển lại · preview</button></div> : null}
      {scenario === 'compensation-pending' && status !== 'transfer-preview' ? <div className="flow-recovery-detail flow-recovery-detail--warning" role="status"><span>TRANSFER_PENDING · READ ONLY</span><strong>Chưa rõ kết quả bù</strong><p>Không cấp nội dung cho giáo viên cũ hoặc mới. Giữ lớp chỉ đọc và reconcile cùng request trước khi thử lại.</p><button className="flow-secondary" type="button" onClick={reconcile}>Xem kết quả đối soát · preview</button>{status === 'reconciled-preview' ? <button className="flow-primary" type="button" onClick={retryTransfer}>Thử chuyển lại · preview</button> : null}</div> : null}
      {status === 'transfer-preview' ? <div className="flow-recovery-detail" role="status"><span>TRANSFER FINALIZED · PREVIEW</span><strong>{className} → {replacement}</strong><p>Đây là trạng thái minh họa sau receipt; assignment thật không thay đổi. Creator provenance được giữ riêng.</p></div> : null}
      {notice ? <p className="groups-notice" role="status">{notice}</p> : null}
    </section><FlowRecoveryDisclosure title="Đổi giáo viên phụ trách" boundary="Force-close là command riêng có reason/audit; transfer bình thường không tự đóng run. Permission resolver và API vẫn chưa kết nối."/>
  </div>;
}

function FlowRecoveryDisclosure({ title, boundary }: { title: string; boundary: string }) {
  const cases = recoveryCasesFor(title);
  const [selectedCode, setSelectedCode] = useState(cases[0]?.code ?? '');
  const [previewAction, setPreviewAction] = useState('');
  const selected = cases.find((item) => item.code === selectedCode);
  const kind = selected?.kind ?? 'blocked';
  const safeAction = kind === 'retryable' ? 'Mô phỏng thao tác thử lại' : kind === 'stale' ? 'Giữ bản nháp và xem phiên bản mới' : kind === 'reconcile' ? 'Kiểm tra trạng thái minh họa' : kind === 'deleting' ? 'Theo dõi tiến độ xóa minh họa' : '';
  return <details className="flow-recovery"><summary>Trạng thái và cách khôi phục</summary><p className="flow-recovery-intro">Chọn tình huống để xem đúng cách giao diện phản hồi. Mọi trạng thái bên dưới là preview, không gọi API.</p><label className="flow-state-select">Tình huống<select value={selectedCode} onChange={(event) => { setSelectedCode(event.target.value); setPreviewAction(''); }} aria-label={`Tình huống trạng thái cho ${title}`}>{cases.map((item) => <option key={item.code} value={item.code}>{item.title}</option>)}</select></label>{selected && <article className={`flow-state-preview flow-state-preview--${kind}`} role="status" aria-live="polite"><span className="flow-state-code">{selected.code} · PREVIEW</span><strong>{selected.title}</strong>{kind === 'loading' ? <div className="flow-state-skeleton" aria-hidden="true"><i/><i/><i/></div> : null}<p>{selected.next}</p>{kind === 'stale' ? <div className="flow-state-comparison"><span>Bản đang sửa <b>được giữ</b></span><span>Phiên bản máy chủ <b>cần tải lại</b></span></div> : null}{kind === 'deleting' ? <div className="flow-state-progress"><span><i/></span><small>Chờ xác nhận lifecycle · không có tiến độ phần trăm giả</small></div> : null}{safeAction ? <button type="button" className="flow-secondary" onClick={() => setPreviewAction('Preview không gửi lệnh; cần kết quả và retryability từ backend trước khi tiếp tục.')}>{safeAction}</button> : null}{previewAction ? <small className="flow-state-action-note">{previewAction}</small> : null}</article>}<p className="flow-boundary-copy">{boundary}</p></details>;
}

function WizardPage({ spec }: { spec: Flow }) {
  const [index, setIndex] = useState(0);
  const [maxIndex, setMaxIndex] = useState(0);
  const [values, setValues] = useState<Record<string, string | boolean>>({});
  const [completed, setCompleted] = useState(false);
  const [slide, setSlide] = useState(0);
  const [message, setMessage] = useState('');
  const [sampleChoice, setSampleChoice] = useState<SampleChoice>('not-checked');
  const [completionNote, setCompletionNote] = useState('');
  const step = spec.steps[index];
  const isDeck = spec.title === 'Bộ hướng dẫn nét vẽ';
  const isSample = spec.title === 'Tạo video mẫu cho buổi dạy';
  const isPresentation = spec.title === 'Chiếu video trong lớp';
  const isImport = spec.title === 'Nhập và rà soát giáo án';
  return <div className="flow-page"><header className="flow-heading"><span>LUỒNG THEO VAI TRÒ · BẢN XEM TRƯỚC</span><h1>{spec.title}</h1><p>{spec.description}</p></header><div className="flow-layout"><aside className="flow-rail" aria-label="Các bước"><strong>TIẾN TRÌNH</strong>{spec.steps.map((item, position) => <button key={item.title} type="button" disabled={position > maxIndex} className={position === index ? 'active' : ''} onClick={() => { setIndex(position); setCompleted(false); setMessage(''); }} aria-current={position === index ? 'step' : undefined}><span>{String(position + 1).padStart(2,'0')}</span>{item.title}</button>)}<div className="flow-boundary"><b>Ranh giới tích hợp</b><p>{spec.boundary}</p></div></aside><section className="flow-card"><span className="flow-eyebrow">{step.eyebrow}</span><h2>{step.title}</h2><p className="flow-summary">{step.summary}</p>{completed ? <div className="flow-complete" role="status"><strong>{completionNote ? 'Đã bỏ qua hướng dẫn' : 'Đã đi hết luồng xem trước'}</strong><p>{completionNote || 'Thông tin chưa được gửi hoặc lưu trên backend. Các bước và kiểm tra quyền sẽ được nối theo contract tương ứng.'}</p><button type="button" onClick={() => { setIndex(0); setMaxIndex(0); setCompleted(false); setValues({}); setSampleChoice('not-checked'); setCompletionNote(''); }}>Xem lại từ đầu</button></div> : <form onSubmit={(event) => { event.preventDefault(); if (isSample && index === 0 && sampleChoice !== 'confirmed') return; if (isDeck && index === 0 && values.enable !== true) { setCompletionNote('Occurrence tiếp tục mà không có Sketch Deck, job AI hoặc asset. Đây chỉ là trạng thái preview.'); setCompleted(true); return; } if (index < spec.steps.length - 1) { setIndex(index + 1); setMaxIndex((current) => Math.max(current, index + 1)); setMessage(''); } else setCompleted(true); }}><div className="flow-fields">{isImport && index === 1 ? <section className="flow-extraction-preview" aria-label="Bản trích xuất minh họa"><span className="flow-eyebrow">BƯỚC TRÍCH XUẤT · MẪU</span><strong>Tệp: {String(values.lessonFile || "Chưa chọn")}</strong><p>Parser chưa kết nối. Nội dung dưới đây không được đọc từ tệp bạn chọn.</p><div className="flow-extraction-lines"><span>Chủ đề: quan sát khu vườn</span><span>Nhóm tuổi: 4–5 tuổi</span><span>Mục tiêu: nhận biết hình dạng và màu sắc</span><span>Các bước vẽ: phác hình lớn, thêm chi tiết, tô màu</span><span>Hoạt động: quan sát lá cùng người lớn</span><span>Vật liệu: giấy, bút màu, lá rụng</span><span>An toàn: không cho vật liệu vào miệng</span></div><button type="button" className="flow-secondary" disabled={!values.lessonFile} onClick={() => { setValues((current) => ({...current, topic: "Quan sát khu vườn", ageGroup: "4–5 tuổi", objectives: "Nhận biết hình dạng và màu sắc trong tự nhiên.", drawingSteps: "1. Phác hình lớn. 2. Thêm chi tiết. 3. Tô màu theo ý thích.", activities: "Quan sát lá cùng người lớn và kể điều con tò mò.", materials: "Giấy, bút màu, một vài chiếc lá rụng.", safety: "Không cho lá hoặc vật liệu nhỏ vào miệng."})); setMessage("Đã nạp các trường mẫu để cô rà soát và chỉnh sửa; không đọc tệp hoặc gọi parser."); }}>Nạp dữ liệu trích xuất mẫu</button></section> : null}{step.fields?.map((field) => <FieldControl key={field.id} field={field.requiredWhen ? {...field, required: values[field.requiredWhen.field] === field.requiredWhen.value} : field} value={values[field.id] ?? (field.kind === 'checkbox' ? false : '')} onChange={(value) => { setValues((current) => ({ ...current, [field.id]: value })); setMessage(''); }}/>)}</div>{isSample && index === 0 ? <TeacherSampleSelection choice={sampleChoice} onChange={setSampleChoice}/> : null}{isDeck && index > 0 && <div className="flow-deck"><div className="flow-deck-stage"><span>HƯỚNG DẪN NÉT VẼ</span><strong>{['Quan sát hình dạng', 'Phác nét chính', 'Thêm chi tiết'][slide]}</strong><div className="flow-deck-shape"/><small>Minh họa bố cục 16:9 · không phải AI output</small></div><div className="flow-deck-controls"><button type="button" disabled={slide === 0} onClick={() => setSlide((current) => Math.max(0,current - 1))}>← Trước</button><span>Bước {slide + 1}/3</span><button type="button" disabled={slide === 2} onClick={() => setSlide((current) => Math.min(2,current + 1))}>Tiếp →</button><button type="button" onClick={() => setMessage('Tạo lại một sketch cần AI job và revision mới; bản xem trước không gửi yêu cầu.')}>Tạo lại bước này</button></div></div>}{isSample && index === 4 && <JobStages/>}{((isSample && index === 5) || (isPresentation && index === 1)) && <VideoSurface presentation={isPresentation}/>}{step.note && <p className="flow-note">{step.note}</p>}{spec.title === 'Gói và thanh toán' && index === 2 && <BillingInvoicePanel/>}{message && <p className="flow-note" role="status">{message}</p>}<div className="flow-actions">{index > 0 && <button type="button" className="flow-secondary" onClick={() => setIndex(index - 1)}>Quay lại</button>}<button type="submit" disabled={isSample && index === 0 && sampleChoice !== 'confirmed'} className="flow-primary">{isDeck && index === 0 && values.enable !== true ? 'Bỏ qua · không tạo deck' : index === spec.steps.length - 1 ? 'Hoàn tất xem trước' : 'Tiếp tục'} <span aria-hidden="true">→</span></button></div></form>}</section></div><FlowRecoveryDisclosure title={spec.title} boundary={spec.boundary}/></div>;
}

function FlowDetailDialog({ spec, item, close }: { spec: Operation; item: Operation['items'][number]; close: () => void }) {
  const ref = useRef<HTMLElement>(null);
  const closeRef = useRef(close);
  closeRef.current = close;
  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    ref.current?.querySelector<HTMLButtonElement>('.flow-modal-close')?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.preventDefault(); closeRef.current(); }
      if (event.key !== 'Tab') return;
      const buttons = Array.from(ref.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? []);
      if (buttons.length < 2) return;
      if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault(); buttons[buttons.length - 1].focus(); }
      else if (!event.shiftKey && document.activeElement === buttons[buttons.length - 1]) { event.preventDefault(); buttons[0].focus(); }
    };
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('keydown', onKey); previous?.focus(); };
  }, []);
  return <div className="flow-modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) close(); }}><section ref={ref} className="flow-modal" role="dialog" aria-modal="true" aria-labelledby="flow-modal-title"><button className="flow-modal-close" onClick={close} aria-label="Đóng chi tiết">×</button><span className="flow-eyebrow">{item.state}</span><h2 id="flow-modal-title">{item.title}</h2><p>{item.detail}</p><p className="flow-note">{spec.boundary}</p><button className="flow-primary" onClick={close}>Đã hiểu</button></section></div>;
}

function OperationsPage({ spec }: { spec: Operation }) {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<number | null>(null);
  const items = spec.items.filter((item) => `${item.title} ${item.detail} ${item.state}`.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')));
  const operatorPage = ['Tác vụ AI', 'Sức khỏe nền tảng', 'Đối soát thanh toán', 'Nhật ký vận hành'].includes(spec.title);
  return <div className="flow-page"><header className="flow-heading"><span>KHÔNG GIAN VẬN HÀNH · BẢN XEM TRƯỚC</span><h1>{spec.title}</h1><p>{spec.description}</p></header>{operatorPage && <div className="feedback-preview-note" role="note"><strong>Bề mặt dành cho quyền vận hành kỹ thuật</strong><span>System Operator và Platform Admin là hai phạm vi cần permission contract xác nhận. Preview không cấp quyền; dữ liệu thật chỉ hiển thị theo quyền server.</span></div>}<section className="flow-operation"><div className="flow-operation-head"><strong>{spec.title === 'Sức khỏe nền tảng' ? 'METADATA ĐÃ LỌC' : 'DANH SÁCH'}</strong><label>Tìm trong trang<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm theo tên hoặc trạng thái"/></label></div><div className="flow-operation-grid">{items.map((item) => <button type="button" key={item.title} onClick={() => setSelected(spec.items.indexOf(item))}><span>{item.state}</span><strong>{item.title}</strong><small>{item.detail}</small><b aria-hidden="true">→</b></button>)}{items.length === 0 && <p>Không có kết quả phù hợp.</p>}</div><div className="flow-boundary"><b>Ranh giới tích hợp</b><p>{spec.boundary}</p></div></section><FlowRecoveryDisclosure title={spec.title} boundary={spec.boundary}/>{selected !== null && <FlowDetailDialog spec={spec} item={spec.items[selected]} close={() => setSelected(null)}/>}</div>;
}

type FeedbackEntry = { id: string; subject: string; author: string; date: string; message: string; reply?: string };
function FeedbackInboxPage({ role }: { role: Role }) {
  const entries: FeedbackEntry[] = role === 'teacher' ? [
    { id: 'family-1', subject: 'Khám phá khu vườn · v1.4', author: 'Gia đình Bé An', date: '3 ngày trước', message: 'Bé kể lại câu chuyện ở nhà và muốn quan sát thêm các loại lá trong sân trường.' },
    { id: 'family-2', subject: 'Bầu trời kỳ diệu · v2.0', author: 'Gia đình Bé Minh', date: 'Tuần trước', message: 'Cảm ơn cô đã gắn hoạt động vẽ mây với buổi học hôm nay.', reply: 'Cảm ơn gia đình. Tuần tới lớp sẽ tiếp tục quan sát các hình dạng đám mây.' },
  ] : role === 'manager' ? [
    { id: 'teacher-1', subject: 'Khám phá khu vườn · v1.4', author: 'Cô Mai · Lớp Lá 1', date: 'Hôm nay', message: 'Xin bổ sung mục tiêu quan sát màu sắc và vật liệu cần chuẩn bị trước khi duyệt.' },
    { id: 'teacher-2', subject: 'Bầu trời kỳ diệu · v2.0', author: 'Cô Lan · Lớp Chồi 2', date: 'Hôm qua', message: 'Bản sửa đã được cập nhật theo góp ý của nhà trường.', reply: 'Đã nhận bản sửa. Mình sẽ xem lại revision mới trong hàng chờ duyệt.' },
  ] : [
    { id: 'support-1', subject: 'Yêu cầu hỗ trợ · Trường Ánh Nắng', author: 'Quản lý trường', date: 'Hôm nay', message: 'Không mở được màn hình đối soát hóa đơn. Nhờ kiểm tra trạng thái dịch vụ.', reply: 'Đã tiếp nhận. Nhóm vận hành sẽ kiểm tra mã yêu cầu khi Support API được kết nối.' },
    { id: 'support-2', subject: 'Báo cáo nội dung · danh mục hoạt động', author: 'Người dùng đã xác minh', date: 'Hôm qua', message: 'Đề nghị rà soát lại hướng dẫn vật liệu trong một hoạt động đã phát hành.' },
  ];
  const [selectedId, setSelectedId] = useState(entries[0].id);
  const [filter, setFilter] = useState<'all' | 'open' | 'replied'>('all');
  const [search, setSearch] = useState('');
  const [draft, setDraft] = useState('');
  const [replies, setReplies] = useState<Record<string, string>>(() => Object.fromEntries(entries.filter((entry) => entry.reply).map((entry) => [entry.id, entry.reply!] as const)));
  const [notice, setNotice] = useState('');
  const active = entries.find((entry) => entry.id === selectedId) ?? entries[0];
  const filtered = entries.filter((entry) => {
    const replied = Boolean(replies[entry.id]);
    return (filter === 'all' || (filter === 'replied' ? replied : !replied)) && `${entry.subject} ${entry.author} ${entry.message}`.toLocaleLowerCase('vi').includes(search.toLocaleLowerCase('vi'));
  });
  const title = role === 'teacher' ? 'Phản hồi từ gia đình' : role === 'manager' ? 'Phản hồi giáo án' : 'Hỗ trợ & phản hồi';
  const description = role === 'teacher' ? 'Đọc góp ý gắn với đúng giáo án và trả lời trong cùng mạch trao đổi.' : role === 'manager' ? 'Theo dõi góp ý theo phiên bản, trao đổi với giáo viên và giữ lịch sử quyết định.' : 'Rà soát yêu cầu vận hành trong phạm vi tổ chức, không mở dữ liệu trẻ hoặc media.';
  const responseLabel = role === 'teacher' ? 'Trả lời gia đình' : role === 'manager' ? 'Phản hồi giáo viên' : 'Ghi nhận trả lời hỗ trợ';
  return <div className="flow-page"><header className="flow-heading"><span>{role === 'teacher' ? 'KẾT NỐI GIA ĐÌNH' : role === 'manager' ? 'CHẤT LƯỢNG GIÁO ÁN' : 'HỖ TRỢ VẬN HÀNH'} · BẢN XEM TRƯỚC</span><h1>{title}</h1><p>{description}</p></header><div className="feedback-preview-note" role="note"><strong>Chưa kết nối Feedback API</strong><span>Danh sách bên dưới là nội dung minh họa. Câu trả lời chỉ lưu trong phiên xem trước.</span></div><section className="feedback-layout"><div className="feedback-list-panel"><div className="feedback-tools"><label className="feedback-search">Tìm phản hồi<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tên giáo án hoặc người gửi"/></label><div className="feedback-filters" role="group" aria-label="Lọc phản hồi"><button type="button" className={filter === 'all' ? 'is-active' : ''} onClick={() => setFilter('all')}>Tất cả</button><button type="button" className={filter === 'open' ? 'is-active' : ''} onClick={() => setFilter('open')}>Chưa trả lời</button><button type="button" className={filter === 'replied' ? 'is-active' : ''} onClick={() => setFilter('replied')}>Đã trả lời</button></div></div><div className="feedback-entry-list">{filtered.map((entry) => <button type="button" key={entry.id} className={`feedback-entry ${active.id === entry.id ? 'is-selected' : ''}`} onClick={() => { setSelectedId(entry.id); setDraft(replies[entry.id] ?? ''); setNotice(''); }} aria-pressed={active.id === entry.id}><span className="feedback-entry-top"><strong>{entry.author}</strong><small>{entry.date}</small></span><b>{entry.subject}</b><span>{entry.message}</span><i>{replies[entry.id] ? 'Đã trả lời' : 'Chưa trả lời'}</i></button>)}{filtered.length === 0 && <div className="feedback-empty"><strong>Không có phản hồi phù hợp</strong><span>Thử đổi trạng thái hoặc xóa từ khóa.</span><button type="button" onClick={() => { setSearch(''); setFilter('all'); }}>Xóa bộ lọc</button></div>}</div><small className="feedback-count">{filtered.length} / {entries.length} phản hồi minh họa</small></div><article className="feedback-detail-panel"><span className="flow-eyebrow">{active.author} · {active.date}</span><h2>{active.subject}</h2><p className="feedback-message">{active.message}</p>{replies[active.id] ? <div className="feedback-sent"><strong>Phản hồi đã gửi trong phiên này</strong><p>{replies[active.id]}</p><button type="button" onClick={() => { setDraft(replies[active.id]); setNotice(''); }}>Chỉnh sửa bản nháp</button></div> : null}<label className="feedback-reply-field" htmlFor="feedback-reply">{responseLabel}<textarea id="feedback-reply" value={draft} maxLength={500} onChange={(event) => { setDraft(event.target.value); setNotice(''); }} placeholder="Viết ngắn gọn, rõ ràng và tôn trọng…" rows={5}/></label><div className="feedback-reply-foot"><small>{draft.length}/500 ký tự</small><button type="button" disabled={!draft.trim()} onClick={() => { const reply = draft.trim(); setReplies((current) => ({ ...current, [active.id]: reply })); setDraft(reply); setNotice('Đã lưu phản hồi trong phiên xem trước; chưa gửi đến người nhận.'); }}>{replies[active.id] ? 'Cập nhật bản nháp' : 'Lưu phản hồi nháp'}</button></div>{notice && <p className="feedback-notice" role="status">{notice}</p>}<p className="feedback-boundary">Quyền gửi, thông báo cho người nhận và lịch sử phản hồi cần được xác nhận từ API trước khi dùng thật.</p></article></section></div>;
}

type SchoolGroup = { id: string; name: string; className: string; members: number };
type GroupInvite = { id: string; groupId: string; email: string; status: 'Đang chờ' | 'Đã chấp nhận' | 'Đã thu hồi'; date: string };
const previewGroups: SchoolGroup[] = [{ id: 'la1', name: 'Gia đình Lớp Lá 1', className: 'Lớp Lá 1', members: 18 }, { id: 'choi2', name: 'Gia đình Lớp Chồi 2', className: 'Lớp Chồi 2', members: 16 }, { id: 'mam1', name: 'Gia đình Lớp Mầm 1', className: 'Lớp Mầm 1', members: 14 }];
const previewMembers: Record<string, { id: string; label: string; email: string; status: string }[]> = { la1: [{ id: 'p1', label: 'Phụ huynh #01', email: 'an***@example.com', status: 'Đang tham gia' }, { id: 'p2', label: 'Phụ huynh #02', email: 'min***@example.com', status: 'Đang tham gia' }], choi2: [{ id: 'p3', label: 'Phụ huynh #03', email: 'ha***@example.com', status: 'Đang tham gia' }], mam1: [{ id: 'p4', label: 'Phụ huynh #04', email: 'lin***@example.com', status: 'Đang tham gia' }] };

type TeacherProvisionStatus = 'Đang chờ' | 'Đã xác minh' | 'Hết hạn';
type TeacherProvisionPreview = { id: string; name: string; email: string; status: TeacherProvisionStatus; assignedClass: string; date: string };
const initialTeacherProvisionPreview: TeacherProvisionPreview[] = [
  { id: 'mai', name: 'Cô Nguyễn Mai', email: 'mai.nguyen@example.test', status: 'Đã xác minh', assignedClass: 'Lớp Lá 1', date: 'Tài khoản fixture' },
  { id: 'lan', name: 'Cô Trần Lan', email: 'tran.lan@example.test', status: 'Đã xác minh', assignedClass: 'Lớp Chồi 2', date: 'Tài khoản fixture' },
  { id: 'ha', name: 'Cô Phạm Hà', email: 'pham.ha@example.test', status: 'Đã xác minh', assignedClass: 'Lớp Lá 2', date: 'Tài khoản fixture' },
];

function ManagerTeacherProvisioning() {
  const [teachers, setTeachers] = useState<TeacherProvisionPreview[]>(initialTeacherProvisionPreview);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<'Tất cả' | TeacherProvisionStatus>('Tất cả');
  const [selectedId, setSelectedId] = useState('mai');
  const [classDraft, setClassDraft] = useState('');
  const [notice, setNotice] = useState('');
  const selected = teachers.find((teacher) => teacher.id === selectedId) ?? teachers[0];
  const visible = teachers.filter((teacher) =>
    (filter === 'Tất cả' || teacher.status === filter)
      && `${teacher.name} ${teacher.email} ${teacher.assignedClass}`.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')),
  );
  const selectTeacher = (teacher: TeacherProvisionPreview) => { setSelectedId(teacher.id); setClassDraft(teacher.assignedClass); setNotice(''); };
  const submitInvite = (event: React.FormEvent) => {
    event.preventDefault();
    const normalized = email.trim().toLocaleLowerCase('vi');
    const duplicate = teachers.find((teacher) => teacher.email.toLocaleLowerCase('vi') === normalized);
    if (duplicate && duplicate.status !== 'Hết hạn') {
      setNotice(duplicate.status === 'Đã xác minh' ? 'Email này đã có tài khoản xác minh trong fixture.' : 'Email này đã có lời mời đang chờ.');
      return;
    }
    const invite: TeacherProvisionPreview = { id: `teacher-invite-${Date.now()}`, name: name.trim(), email: normalized, status: 'Đang chờ', assignedClass: '', date: 'Vừa tạo · preview' };
    setTeachers((current) => [invite, ...current]);
    setSelectedId(invite.id);
    setClassDraft('');
    setName('');
    setEmail('');
    setFilter('Tất cả');
    setNotice('Đã tạo lời mời minh họa. Không gửi email hoặc tạo tài khoản thật.');
  };
  const updateStatus = (id: string, status: TeacherProvisionStatus, date: string) => {
    setTeachers((current) => current.map((teacher) => teacher.id === id ? { ...teacher, status, date, assignedClass: status === 'Đã xác minh' ? teacher.assignedClass : '' } : teacher));
    setNotice(status === 'Đã xác minh' ? 'Đã mô phỏng xác minh danh tính; chưa kích hoạt tài khoản thật.' : status === 'Hết hạn' ? 'Đã mô phỏng lời mời hết hạn; chưa có email hoặc token thật.' : 'Đã tạo lại lời mời trong preview; chưa gửi email.');
  };
  const saveAssignment = () => {
    if (selected.status !== 'Đã xác minh' || !classDraft) return;
    setTeachers((current) => current.map((teacher) => teacher.id === selected.id ? { ...teacher, assignedClass: classDraft } : teacher));
    setNotice(`Đã lưu phân công minh họa cho ${selected.name}; backend chưa nhận thay đổi.`);
  };
  return <div className="flow-page"><header className="flow-heading"><h1>Giáo viên & lời mời</h1><p>Mời giáo viên, theo dõi xác minh rồi mới mở thao tác phân công.</p></header>
    <div className="feedback-preview-note" role="note"><strong>Chưa kết nối Identity / Teacher API</strong><span>Trạng thái, lời mời và phân công chỉ nằm trong phiên xem trước. Không gửi email hoặc tạo tài khoản thật.</span></div>
    <section className="manager-teacher-console">
      <form className="manager-teacher-invite" onSubmit={submitInvite}>
        <h2>Tạo lời mời giáo viên</h2><p>Người nhận cần xác minh tài khoản trước khi có thể được phân công lớp.</p>
        <label>Họ tên<input required maxLength={100} autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Ví dụ: Cô Nguyễn An"/></label>
        <label>Email công việc<input required type="email" maxLength={254} autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="giaovien@truong.edu.vn"/></label>
        <button type="submit" className="flow-primary" disabled={!name.trim() || !email.trim()}>Tạo lời mời preview <span aria-hidden="true">→</span></button>
        <small>Quyền tổ chức chỉ được gán sau xác minh từ hệ thống danh tính.</small>
      </form>
      <section className="manager-teacher-directory">
        <div className="catalog-list-head"><h2>Giáo viên</h2><span>{teachers.length} mục</span></div>
        <label className="feedback-search">Tìm tên hoặc email<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm giáo viên…"/></label>
        <div className="feedback-filters" role="group" aria-label="Lọc lời mời giáo viên">
          {(['Tất cả', 'Đang chờ', 'Đã xác minh', 'Hết hạn'] as const).map((status) => <button type="button" key={status} className={filter === status ? 'is-active' : ''} onClick={() => setFilter(status)}>{status}</button>)}
        </div>
        <div className="manager-teacher-list">{visible.map((teacher) => <article key={teacher.id} className={`manager-teacher-row ${selected.id === teacher.id ? 'is-selected' : ''}`}>
          <button type="button" className="manager-teacher-select" onClick={() => selectTeacher(teacher)} aria-pressed={selected.id === teacher.id}>
            <span className="groups-member-avatar" aria-hidden="true">{teacher.name.slice(-1)}</span><span><strong>{teacher.name}</strong><small>{teacher.email} · {teacher.date}</small></span><i className={`preview-state preview-state--${teacher.status === 'Đã xác minh' ? 'active' : teacher.status === 'Hết hạn' ? 'archived' : 'paused'}`}>{teacher.status}{initialTeacherProvisionPreview.some((item) => item.id === teacher.id) ? ' · fixture' : ''}</i>
          </button>
          {teacher.status === 'Đang chờ' ? <div className="manager-teacher-actions"><button type="button" className="flow-secondary" onClick={() => updateStatus(teacher.id, 'Đã xác minh', 'Xác minh mô phỏng')}>Xác minh · preview</button><button type="button" className="manager-teacher-text-action" onClick={() => updateStatus(teacher.id, 'Hết hạn', 'Hết hạn · preview')}>Đánh dấu hết hạn</button></div> : teacher.status === 'Hết hạn' ? <div className="manager-teacher-actions"><button type="button" className="flow-secondary" onClick={() => updateStatus(teacher.id, 'Đang chờ', 'Gửi lại · preview')}>Tạo lại lời mời</button></div> : null}
        </article>)}{visible.length === 0 && <div className="feedback-empty"><strong>Không tìm thấy giáo viên</strong><span>Thử trạng thái hoặc từ khóa khác.</span><button type="button" onClick={() => { setQuery(''); setFilter('Tất cả'); }}>Xóa bộ lọc</button></div>}</div>
        {selected.status === 'Đã xác minh' ? <section className="manager-teacher-assignment"><div><h3>{selected.name}</h3><p>{selected.assignedClass ? `Hiện tại: ${selected.assignedClass}` : 'Chưa có lớp được phân công.'}</p></div><label>Lớp<select value={classDraft} onChange={(event) => setClassDraft(event.target.value)}><option value="">Chọn lớp</option><option>Lớp Lá 1</option><option>Lớp Chồi 2</option><option>Lớp Mầm 1</option><option>Lớp Lá 2</option></select></label><button type="button" className="flow-primary" disabled={!classDraft || classDraft === selected.assignedClass} onClick={saveAssignment}>Lưu phân công preview</button></section> : <p className="manager-teacher-gate"><strong>Phân công đang khóa</strong><span>Chỉ mở sau khi giáo viên được xác minh.</span></p>}
        {notice && <p className="groups-notice" role="status">{notice}</p>}
      </section>
    </section>
    <FlowRecoveryDisclosure title="Mời và provision giáo viên" boundary="Xác minh, cấp quyền tổ chức, gửi email và phân công thật cần Identity/Teacher API, quyền phù hợp và audit server-side."/>
  </div>;
}

function ParentGroupsConsole() {
  const [groupId, setGroupId] = useState('la1');
  const [tab, setTab] = useState<'members' | 'invites'>('members');
  const [showInvite, setShowInvite] = useState(false);
  const [email, setEmail] = useState('');
  const [notice, setNotice] = useState('');
  const [invites, setInvites] = useState<GroupInvite[]>([{ id: 'gi1', groupId: 'la1', email: 'minh***@example.com', status: 'Đang chờ', date: 'Hôm nay' }, { id: 'gi2', groupId: 'choi2', email: 'hoa***@example.com', status: 'Đã chấp nhận', date: 'Hôm qua' }]);
  const group = previewGroups.find((item) => item.id === groupId) ?? previewGroups[0];
  const groupInvites = invites.filter((item) => item.groupId === groupId);
  return <div className="flow-page"><header className="flow-heading"><span>NHÀ TRƯỜNG · BẢN XEM TRƯỚC</span><h1>Nhóm gia đình & lời mời</h1><p>Quản lý thành viên theo lớp, theo dõi lời mời và thu hồi khi cần.</p></header><div className="feedback-preview-note" role="note"><strong>Chưa kết nối Group API</strong><span>Danh sách minh họa; lời mời và membership chưa ghi lên backend.</span></div><div className="groups-console"><aside className="groups-chooser"><div className="groups-chooser-title"><strong>Các lớp</strong><small>{previewGroups.length} nhóm</small></div>{previewGroups.map((item) => <button key={item.id} type="button" className={groupId === item.id ? 'is-selected' : ''} onClick={() => { setGroupId(item.id); setNotice(''); }}><span className="groups-class-icon">{item.className.slice(0,1)}</span><span><strong>{item.className}</strong><small>{item.members} phụ huynh</small></span><b aria-hidden="true">›</b></button>)}</aside><section className="groups-detail"><header className="groups-detail-head"><div><span className="flow-eyebrow">{group.name}</span><h2>{group.className}</h2><p>{group.members} thành viên đang được cấp quyền theo lớp</p></div><button type="button" className="flow-primary" onClick={() => { setTab('invites'); setShowInvite((value) => !value); setNotice(''); }}>{showInvite ? 'Đóng biểu mẫu' : '+ Mời phụ huynh'}</button></header>{showInvite && <form className="groups-invite-form" onSubmit={(event) => { event.preventDefault(); const normalized = email.trim().toLocaleLowerCase('vi'); if (invites.some((item) => item.groupId === groupId && item.email.toLocaleLowerCase('vi') === normalized && item.status === 'Đang chờ')) { setNotice('Tài khoản này đã có lời mời đang chờ.'); return; } setInvites((current) => [{ id: `gi-${Date.now()}`, groupId, email: normalized, status: 'Đang chờ', date: 'Vừa tạo · preview' }, ...current]); setEmail(''); setNotice('Đã thêm lời mời minh họa; chưa gửi email hoặc cấp quyền.'); }}><label>Email tài khoản phụ huynh<input type="email" required maxLength={254} autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="phuhuynh@example.com"/></label><p>Chỉ tài khoản đã xác minh mới có thể tham gia; quyền bắt đầu sau khi lời mời được chấp nhận.</p><button type="submit" className="flow-primary" disabled={!email.trim()}>Tạo lời mời preview</button></form>}{notice && <p className="groups-notice" role="status">{notice}</p>}<div className="groups-tabs" role="tablist" aria-label="Thành viên và lời mời"><button type="button" role="tab" aria-selected={tab === 'members'} className={tab === 'members' ? 'is-active' : ''} onClick={() => { setTab('members'); setShowInvite(false); }}>Thành viên <span>{group.members}</span></button><button type="button" role="tab" aria-selected={tab === 'invites'} className={tab === 'invites' ? 'is-active' : ''} onClick={() => setTab('invites')}>Lời mời <span>{groupInvites.length}</span></button></div>{tab === 'members' ? <div className="groups-record-list">{(previewMembers[groupId] ?? []).map((member) => <div className="groups-record" key={member.id}><span className="groups-member-avatar">{member.label.slice(-2)}</span><span><strong>{member.label}</strong><small>{member.email}</small></span><i>{member.status}</i></div>)}</div> : <div className="groups-record-list">{groupInvites.map((invite) => <div className="groups-record" key={invite.id}><span className="groups-member-avatar">@</span><span><strong>{invite.email}</strong><small>{invite.date}</small></span><i className={invite.status === 'Đã thu hồi' ? 'is-revoked' : invite.status === 'Đã chấp nhận' ? 'is-accepted' : ''}>{invite.status}</i>{invite.status === 'Đang chờ' && <button type="button" className="groups-revoke" onClick={() => { setInvites((current) => current.map((item) => item.id === invite.id ? { ...item, status: 'Đã thu hồi' } : item)); setNotice('Đã thu hồi lời mời trong phiên preview.'); }}>Thu hồi</button>}</div>)}{groupInvites.length === 0 && <div className="feedback-empty"><strong>Chưa có lời mời</strong><span>Tạo lời mời cho tài khoản phụ huynh đã xác minh.</span></div>}</div>}<p className="groups-scope-note">Quản lý trường chỉ xem thông tin membership; không mở tranh, câu chuyện hoặc video của trẻ.</p></section></div></div>;
}

type LessonGrant = { id: string; lesson: string; recipient: string; status: 'Đang chờ' | 'Đã chấp nhận' | 'Đã thu hồi'; date: string };
function TeacherSharingConsole() {
  const [grants, setGrants] = useState<LessonGrant[]>([{ id: 'g1', lesson: 'Khám phá khu vườn · v1.4', recipient: 'Gia đình Lớp Lá 1', status: 'Đã chấp nhận', date: 'Hôm qua' }, { id: 'g2', lesson: 'Bầu trời kỳ diệu · v2.0', recipient: 'minh***@example.com', status: 'Đang chờ', date: 'Hôm nay' }]);
  const [lesson, setLesson] = useState('');
  const [recipientType, setRecipientType] = useState('Một phụ huynh');
  const [recipient, setRecipient] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [notice, setNotice] = useState('');
  const [filter, setFilter] = useState('Tất cả');
  const visible = grants.filter((grant) => filter === 'Tất cả' || grant.status === filter);
  return <div className="flow-page"><header className="flow-heading"><span>BÀI GIẢNG TRÊN LỚP · BẢN XEM TRƯỚC</span><h1>Chia sẻ giáo án</h1><p>Chọn đúng revision, người nhận và theo dõi quyền truy cập từ một nơi.</p></header><div className="feedback-preview-note" role="note"><strong>Chưa kết nối Lesson Grant API</strong><span>Preview không gửi email, cấp quyền đọc hoặc xác nhận lời mời thật.</span></div><section className="share-console"><form className="share-create-panel" onSubmit={(event) => { event.preventDefault(); if (!confirmed) return; const grant: LessonGrant = { id: `grant-${Date.now()}`, lesson, recipient: recipient.trim(), status: 'Đang chờ', date: 'Vừa tạo · preview' }; setGrants((current) => [grant, ...current]); setLesson(''); setRecipient(''); setConfirmed(false); setNotice('Đã tạo lời mời minh họa; quyền chỉ có hiệu lực sau khi phụ huynh chấp nhận.'); }}><span className="flow-eyebrow">LỜI MỜI MỚI</span><h2>Chọn phiên bản cần chia sẻ</h2><label>Giáo án và revision<select value={lesson} required onChange={(event) => setLesson(event.target.value)}><option value="">Chọn giáo án</option><option>Khám phá khu vườn · v1.4</option><option>Bầu trời kỳ diệu · v2.0</option></select></label><label>Loại người nhận<select value={recipientType} onChange={(event) => setRecipientType(event.target.value)}><option>Một phụ huynh</option><option>Nhóm gia đình</option></select></label><label>{recipientType === 'Nhóm gia đình' ? 'Tên nhóm đã xác minh' : 'Email phụ huynh'}<input required type={recipientType === 'Nhóm gia đình' ? 'text' : 'email'} maxLength={254} value={recipient} onChange={(event) => setRecipient(event.target.value)} placeholder={recipientType === 'Nhóm gia đình' ? 'Gia đình Lớp Lá 1' : 'phuhuynh@example.com'}/></label><label className="share-confirm"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)}/><span>Tôi đã kiểm tra đúng revision và người nhận.</span></label><button type="submit" className="flow-primary" disabled={!confirmed}>Tạo lời mời preview</button>{notice && <p role="status" className="groups-notice">{notice}</p>}<p className="groups-scope-note">Lời mời chờ chấp nhận chưa cấp quyền. Chính sách thời hạn đang chờ owner quyết định.</p></form><section className="share-grants-panel"><div className="share-grants-title"><div><span className="flow-eyebrow">QUYỀN ĐANG THEO DÕI</span><h2>Lời mời & chia sẻ</h2></div><label>Lọc<select value={filter} onChange={(event) => setFilter(event.target.value)}><option>Tất cả</option><option>Đang chờ</option><option>Đã chấp nhận</option><option>Đã thu hồi</option></select></label></div><div className="groups-record-list">{visible.map((grant) => <div className="groups-record share-grant-row" key={grant.id}><span className="groups-member-avatar">{grant.recipient.slice(0,1).toLocaleUpperCase('vi')}</span><span><strong>{grant.recipient}</strong><small>{grant.lesson} · {grant.date}</small></span><i className={grant.status === 'Đã thu hồi' ? 'is-revoked' : grant.status === 'Đã chấp nhận' ? 'is-accepted' : ''}>{grant.status}</i>{grant.status !== 'Đã thu hồi' && <button type="button" className="groups-revoke" onClick={() => setGrants((current) => current.map((item) => item.id === grant.id ? { ...item, status: 'Đã thu hồi' } : item))}>Thu hồi</button>}</div>)}{visible.length === 0 && <div className="feedback-empty"><strong>Không có lời mời ở trạng thái này</strong><span>Thử bộ lọc khác.</span></div>}</div></section></section></div>;
}

type PreviewAccount = { id: string; name: string; email: string; role: string; organization: string; status: 'Đang hoạt động' | 'Tạm khóa' };
type AccountProposal = { id: string; accountId: string; kind: 'Đổi vai trò' | 'Thay đổi trạng thái'; current: string; requested: string; reason: string; status: 'Chờ duyệt · preview' | 'Đã duyệt · preview' | 'Từ chối · preview' };
function AccountsConsole() {
  const accounts: PreviewAccount[] = [
    { id: 'a1', name: 'Nguyễn Mai', email: 'mai***@example.com', role: 'Giáo viên', organization: 'Trường Ánh Nắng', status: 'Đang hoạt động' },
    { id: 'a2', name: 'Trần Minh', email: 'minh***@example.com', role: 'Quản lý trường', organization: 'Trường Ánh Nắng', status: 'Đang hoạt động' },
    { id: 'a3', name: 'Lê An', email: 'an***@example.com', role: 'Phụ huynh', organization: 'Trường Lá Xanh', status: 'Tạm khóa' },
  ];
  const [selectedId, setSelectedId] = useState('a1');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('Tất cả');
  const [requestKind, setRequestKind] = useState<'role' | 'status' | ''>('');
  const [requestedRole, setRequestedRole] = useState('');
  const [reason, setReason] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [proposals, setProposals] = useState<AccountProposal[]>([]);
  const [notice, setNotice] = useState('');
  const selected = accounts.find((item) => item.id === selectedId) ?? accounts[0];
  const filtered = accounts.filter((item) => (filter === 'Tất cả' || item.status === filter) && `${item.name} ${item.email} ${item.role} ${item.organization}`.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')));
  const selectedProposals = proposals.filter((proposal) => proposal.accountId === selected.id);
  const resetDraft = () => { setRequestKind(''); setRequestedRole(''); setReason(''); setConfirmed(false); };
  const createProposal = (event: React.FormEvent) => {
    event.preventDefault();
    if (!requestKind || !reason.trim() || !confirmed) return;
    const kind = requestKind === 'role' ? 'Đổi vai trò' : 'Thay đổi trạng thái';
    const requested = requestKind === 'role' ? requestedRole : selected.status === 'Đang hoạt động' ? 'Tạm khóa' : 'Đang hoạt động';
    if (!requested || (requestKind === 'role' && requested === selected.role)) return;
    setProposals((current) => [{ id: `proposal-${Date.now()}`, accountId: selected.id, kind, current: requestKind === 'role' ? selected.role : selected.status, requested, reason: reason.trim(), status: 'Chờ duyệt · preview' }, ...current]);
    setNotice('Đã tạo đề xuất xem trước. Vai trò và trạng thái thật của tài khoản không thay đổi.');
    resetDraft();
  };
  const reviewProposal = (proposalId: string, status: 'Đã duyệt · preview' | 'Từ chối · preview') => {
    setProposals((current) => current.map((proposal) => proposal.id === proposalId ? { ...proposal, status } : proposal));
    setNotice(`Đã ghi nhận “${status}” cho đề xuất trong preview; không áp dụng thay đổi tài khoản.`);
  };
  return <div className="flow-page"><header className="flow-heading"><span>VẬN HÀNH NỀN TẢNG · BẢN XEM TRƯỚC</span><h1>Tài khoản & vai trò</h1><p>Tra cứu theo tổ chức; lập và rà soát đề xuất quyền có lý do.</p></header><div className="feedback-preview-note" role="note"><strong>Chưa kết nối Platform Account API</strong><span>Tài khoản là dữ liệu minh họa. Đề xuất và quyết định chỉ tồn tại trong phiên preview; không cấp quyền hay khóa tài khoản thật.</span></div><section className="accounts-console"><div className="accounts-list-panel"><label className="feedback-search">Tìm tài khoản<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tên, email hoặc tổ chức"/></label><div className="feedback-filters" role="group" aria-label="Lọc trạng thái tài khoản"><button type="button" className={filter === 'Tất cả' ? 'is-active' : ''} onClick={() => setFilter('Tất cả')}>Tất cả</button><button type="button" className={filter === 'Đang hoạt động' ? 'is-active' : ''} onClick={() => setFilter('Đang hoạt động')}>Đang hoạt động</button><button type="button" className={filter === 'Tạm khóa' ? 'is-active' : ''} onClick={() => setFilter('Tạm khóa')}>Tạm khóa</button></div><div className="accounts-list">{filtered.map((account) => <button type="button" key={account.id} className={selected.id === account.id ? 'is-selected' : ''} onClick={() => { setSelectedId(account.id); resetDraft(); setNotice(''); }}><span aria-hidden="true">{account.name.slice(0,1)}</span><span><strong>{account.name}</strong><small>{account.email}</small></span><i>{account.role}</i></button>)}{filtered.length === 0 && <div className="feedback-empty"><strong>Không tìm thấy tài khoản</strong><span>Đổi bộ lọc hoặc từ khóa.</span></div>}</div><small className="preview-count">{filtered.length} tài khoản · fixture đã ẩn bớt email</small></div><article className="account-detail-panel"><span className="flow-eyebrow">CHI TIẾT TÀI KHOẢN · FIXTURE</span><h2>{selected.name}</h2><p>{selected.email}</p><dl><div><dt>Vai trò hiện tại</dt><dd>{selected.role}</dd></div><div><dt>Tổ chức</dt><dd>{selected.organization}</dd></div><div><dt>Trạng thái hiện tại</dt><dd>{selected.status}</dd></div></dl><div className="account-proposal-actions"><button type="button" className={requestKind === 'role' ? 'is-active' : ''} onClick={() => { setRequestKind('role'); setRequestedRole(''); setReason(''); setConfirmed(false); }}>Đề xuất đổi vai trò</button><button type="button" className={requestKind === 'status' ? 'is-active' : ''} onClick={() => { setRequestKind('status'); setRequestedRole(''); setReason(''); setConfirmed(false); }}>Đề xuất đổi trạng thái</button></div>{requestKind && <form className="account-proposal-form" onSubmit={createProposal}><strong>{requestKind === 'role' ? 'Đề xuất vai trò mới' : 'Đề xuất trạng thái mới'}</strong>{requestKind === 'role' ? <label>Vai trò đề xuất<select required value={requestedRole} onChange={(event) => setRequestedRole(event.target.value)}><option value="">Chọn vai trò</option><option>Phụ huynh</option><option>Giáo viên</option><option>Quản lý trường</option><option>Quản trị nền tảng</option></select></label> : <p className="account-status-proposal">{selected.status} <span aria-hidden="true">→</span> {selected.status === 'Đang hoạt động' ? 'Tạm khóa' : 'Đang hoạt động'}</p>}<label>Lý do và phạm vi<textarea required maxLength={400} value={reason} onChange={(event) => setReason(event.target.value)} rows={3} placeholder="Nêu căn cứ, tổ chức và quyền cần thay đổi"/></label><label className="flow-check"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)}/><span>Đã kiểm tra đúng tài khoản, tổ chức và phạm vi quyền.</span></label><div className="manager-action-buttons"><button type="button" className="flow-secondary" onClick={resetDraft}>Hủy</button><button type="submit" className="flow-primary" disabled={!reason.trim() || !confirmed || (requestKind === 'role' && (!requestedRole || requestedRole === selected.role))}>Tạo đề xuất preview</button></div></form>}{selectedProposals.length > 0 && <section className="account-proposals"><div className="catalog-list-head"><div><span className="flow-eyebrow">LỊCH SỬ ĐỀ XUẤT</span><h3>Rà soát quyền</h3></div><span>{selectedProposals.length}</span></div>{selectedProposals.map((proposal) => <article key={proposal.id} className="account-proposal-record"><div><strong>{proposal.kind}: {proposal.current} → {proposal.requested}</strong><span className="catalog-status catalog-status--review">{proposal.status}</span></div><p>{proposal.reason}</p>{proposal.status === 'Chờ duyệt · preview' && <div className="manager-action-buttons"><button type="button" className="flow-secondary" onClick={() => reviewProposal(proposal.id, 'Từ chối · preview')}>Từ chối preview</button><button type="button" className="flow-primary" onClick={() => reviewProposal(proposal.id, 'Đã duyệt · preview')}>Duyệt đề xuất preview</button></div>}</article>)}</section>}{notice && <p className="groups-notice" role="status">{notice}</p>}<p className="groups-scope-note">Duyệt preview không đổi vai trò hoặc trạng thái tài khoản. Khi tích hợp cần kiểm tra quyền, organization scope, revision và audit từ server.</p></article></section><FlowRecoveryDisclosure title="Tài khoản và vai trò" boundary="Không áp dụng quyền trong preview; thay đổi thật cần API Platform Admin, xác thực scope, quyết định phê duyệt và audit server-side."/></div>;
}
type PreviewClass = { id: string; name: string; teacher: string; state: 'Đang hoạt động' | 'Tạm ngưng' | 'Lưu trữ'; note: string };
function ManagerClassConsole({ mode }: { mode: 'lifecycle' | 'capacity' }) {
  const [classes, setClasses] = useState<PreviewClass[]>([
    { id: 'class-a', name: 'Lớp Lá 1', teacher: 'Cô Mai', state: 'Đang hoạt động', note: 'Dữ liệu lớp minh họa' },
    { id: 'class-b', name: 'Lớp Chồi 2', teacher: 'Cô Lan', state: 'Đang hoạt động', note: 'Dữ liệu lớp minh họa' },
    { id: 'class-c', name: 'Lớp Mầm 1', teacher: 'Chưa phân công', state: 'Tạm ngưng', note: 'Dữ liệu lớp minh họa' },
  ]);
  const [selectedId, setSelectedId] = useState('class-a');
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('Tất cả');
  const [requestedAction, setRequestedAction] = useState<'Tạm ngưng' | 'Lưu trữ' | 'Kích hoạt lại' | ''>('');
  const [reason, setReason] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [notice, setNotice] = useState('');
  const [capacityRequest, setCapacityRequest] = useState<{ direction: 'increase' | 'decrease'; classNames: string[] } | null>(null);
  const [capacityDirection, setCapacityDirection] = useState<'increase' | 'decrease' | ''>('');
  const [capacityClassIds, setCapacityClassIds] = useState<string[]>([]);
  const [capacityConfirmed, setCapacityConfirmed] = useState(false);
  const selected = classes.find((item) => item.id === selectedId) ?? classes[0];
  const visible = classes.filter((item) => (filter === 'Tất cả' || item.state === filter) && `${item.name} ${item.teacher} ${item.state}`.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi')));
  const isCapacity = mode === 'capacity';
  const resetProposal = () => { setRequestedAction(''); setReason(''); setConfirmed(false); };
  const submitCapacityReview = (event: React.FormEvent) => {
    event.preventDefault();
    if (!capacityDirection || !capacityConfirmed || (capacityDirection === 'decrease' && capacityClassIds.length === 0)) return;
    const classNames = classes.filter((item) => capacityClassIds.includes(item.id)).map((item) => item.name);
    setCapacityRequest({ direction: capacityDirection, classNames });
    setNotice('Đã tạo trạng thái yêu cầu minh họa; Billing chưa nhận request và capacity chưa thay đổi.');
  };
  const confirmAction = (event: React.FormEvent) => {
    event.preventDefault();
    if (!selected || !requestedAction || !reason.trim() || !confirmed) return;
    const nextState = requestedAction === 'Kích hoạt lại' ? 'Đang hoạt động' : requestedAction;
    setClasses((current) => current.map((item) => item.id === selected.id ? {...item, state: nextState, note: 'Thay đổi trong phiên preview'} : item));
    setNotice(`${selected.name}: ${requestedAction.toLocaleLowerCase('vi')} trong phiên xem trước; backend chưa nhận thay đổi.`);
    resetProposal();
  };
  return <div className="flow-page"><header className="flow-heading"><span>NHÀ TRƯỜNG · BẢN XEM TRƯỚC</span><h1>{isCapacity ? 'Sức chứa & điều kiện tạo lớp' : 'Vòng đời lớp học'}</h1><p>{isCapacity ? 'Xem trạng thái capacity, kỳ dịch vụ và lớp cần rà soát trước khi gửi yêu cầu.' : 'Rà soát lớp, phân công và trạng thái trước khi đề xuất thay đổi.'}</p></header><div className="feedback-preview-note" role="note"><strong>{isCapacity ? 'Chưa kết nối Billing / capacity API' : 'Lớp và phân công là dữ liệu minh họa'}</strong><span>{isCapacity ? 'Không hiển thị số slot, giá hoặc entitlement chưa được xác nhận.' : 'Tạm ngưng/lưu trữ trong màn này chỉ đổi trạng thái trong phiên preview.'}</span></div>{isCapacity && <section className="capacity-summary" aria-label="Tóm tắt sức chứa"><article><span>Capacity hiện tại</span><strong>Chờ API</strong><small>Chưa có số liệu xác thực</small></article><article><span>Kỳ dịch vụ</span><strong>Chưa tải</strong><small>Không đoán gói hoặc ngày hết hạn</small></article><article><span>Yêu cầu điều chỉnh</span><strong>{capacityRequest ? 'Chờ Billing · preview' : 'Chưa tạo'}</strong><small>Không gửi giao dịch thanh toán</small></article></section>}<section className="manager-class-console"><div className="manager-class-list"><div className="manager-class-tools"><label>Tìm lớp<input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tên lớp hoặc giáo viên"/></label><label>Trạng thái<select value={filter} onChange={(event) => setFilter(event.target.value)}><option>Tất cả</option><option>Đang hoạt động</option><option>Tạm ngưng</option><option>Lưu trữ</option></select></label></div><div className="manager-class-rows">{visible.map((item) => <button key={item.id} type="button" className={selected.id === item.id ? 'is-selected' : ''} onClick={() => { setSelectedId(item.id); resetProposal(); setNotice(''); }}><span className="manager-class-mark">{item.name.slice(0,1)}</span><span><strong>{item.name}</strong><small>{item.teacher} · {item.note}</small></span><i className={`preview-state preview-state--${item.state === 'Đang hoạt động' ? 'active' : item.state === 'Tạm ngưng' ? 'paused' : 'archived'}`}>{item.state}</i></button>)}{visible.length === 0 && <div className="feedback-empty"><strong>Không có lớp phù hợp</strong><span>Thử bộ lọc hoặc từ khóa khác.</span></div>}</div><small className="preview-count">{visible.length} lớp minh họa · không đồng bộ BE</small></div><article className="manager-class-detail"><span className="flow-eyebrow">CHI TIẾT LỚP · PREVIEW</span><h2>{selected.name}</h2><p>Giáo viên phụ trách: {selected.teacher}</p><p className="groups-scope-note">Lịch sử lớp và roster thật cần API; màn quản lý không mở nội dung tranh hoặc video của trẻ.</p>{isCapacity ? <section className="capacity-request-card"><strong>Rà soát thay đổi sức chứa</strong><p>Số slot, giá và quyền mua sẽ do Billing API trả về; preview không tự tính hoặc gửi thanh toán.</p><form className="capacity-review-form" onSubmit={submitCapacityReview}><fieldset><legend>Phương án cần kiểm tra</legend><label className="flow-check"><input type="radio" name="capacityDirection" checked={capacityDirection === 'increase'} onChange={() => { setCapacityDirection('increase'); setCapacityClassIds([]); setCapacityRequest(null); setCapacityConfirmed(false); }}/><span>Tăng sức chứa · chờ Billing xác định điều kiện</span></label><label className="flow-check"><input type="radio" name="capacityDirection" checked={capacityDirection === 'decrease'} onChange={() => { setCapacityDirection('decrease'); setCapacityRequest(null); setCapacityConfirmed(false); }}/><span>Giảm sức chứa · cần chọn lớp dự kiến tạm ngưng</span></label></fieldset>{capacityDirection === 'decrease' && <div className="capacity-class-selection"><strong>Lớp dự kiến tạm ngưng</strong><p>Chọn lớp trong fixture để xem trước. Server phải xác nhận lại lớp và thời điểm hiệu lực trước khi thay đổi thật.</p>{classes.filter((item) => item.state === 'Đang hoạt động').map((item) => <label className="flow-check" key={item.id}><input type="checkbox" checked={capacityClassIds.includes(item.id)} onChange={(event) => setCapacityClassIds((current) => event.target.checked ? [...current, item.id] : current.filter((id) => id !== item.id))}/><span>{item.name} · {item.teacher}</span></label>)}</div>}<label className="flow-check"><input type="checkbox" checked={capacityConfirmed} onChange={(event) => setCapacityConfirmed(event.target.checked)}/><span>Đã kiểm tra tổ chức, kỳ dịch vụ và ảnh hưởng lớp; yêu cầu vẫn cần Billing xác minh.</span></label><button type="submit" className="flow-primary" disabled={!capacityDirection || !capacityConfirmed || (capacityDirection === 'decrease' && capacityClassIds.length === 0)}>Tạo đề xuất capacity preview</button></form>{capacityRequest && <div className="capacity-request-result" role="status"><strong>Trạng thái: chờ Billing · preview</strong><span>Phương án: {capacityRequest.direction === 'increase' ? 'Tăng sức chứa' : 'Giảm sức chứa'}</span>{capacityRequest.classNames.length > 0 && <span>Lớp dự kiến tạm ngưng: {capacityRequest.classNames.join(', ')}</span>}<small>Không có request, payment hoặc thay đổi capacity thật được gửi.</small></div>}</section> : <><div className="manager-class-actions"><button type="button" disabled={selected.state === 'Tạm ngưng' || selected.state === 'Lưu trữ'} onClick={() => setRequestedAction('Tạm ngưng')}>Tạm ngưng</button><button type="button" disabled={selected.state !== 'Đang hoạt động'} onClick={() => setRequestedAction('Lưu trữ')}>Lưu trữ</button><button type="button" disabled={selected.state !== 'Tạm ngưng'} onClick={() => setRequestedAction('Kích hoạt lại')}>Kích hoạt lại</button></div>{requestedAction && <form className="manager-action-review" onSubmit={confirmAction}><strong>Rà soát trước khi {requestedAction.toLocaleLowerCase('vi')}</strong><label>Lý do<textarea required maxLength={400} value={reason} onChange={(event) => setReason(event.target.value)} rows={3} placeholder="Ghi căn cứ và tình trạng lớp"/></label><label className="flow-check"><input type="checkbox" checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)}/><span>Đã kiểm tra lớp, enrollment, phân công và run đang hoạt động.</span></label><div className="manager-action-buttons"><button type="button" className="flow-secondary" onClick={resetProposal}>Hủy đề xuất</button><button type="submit" className="flow-primary" disabled={!reason.trim() || !confirmed}>Xác nhận trong preview</button></div></form>}</>}{notice && <p className="groups-notice" role="status">{notice}</p>}<p className="preview-boundary-note">Thay đổi chỉ nằm trong phiên xem trước; chưa ghi vào tổ chức.</p></article></section><FlowRecoveryDisclosure title={isCapacity ? 'Sức chứa lớp' : 'Vòng đời lớp'} boundary="Tạo lớp, hạ capacity và lưu trữ thật phải dùng quyền, revision, transaction và audit do backend xác nhận."/></div>;
}

type CatalogStatus = 'Nháp' | 'Chờ rà soát' | 'Đã duyệt' | 'Đã phát hành' | 'Yêu cầu chỉnh sửa';
type CatalogPreviewItem = { id: string; title: string; kind: string; version: string; status: CatalogStatus; instructions: string; materials: string; safety: string; reviewReason?: string; retireAt?: string; retireReason?: string };
function CatalogWorkbench() {
  const [items, setItems] = useState<CatalogPreviewItem[]>([
    { id: 'activity-1', title: 'Dạo bước tìm màu sắc', kind: 'Ngoài trời', version: 'v1', status: 'Đã phát hành', instructions: 'Quan sát các sắc độ trong sân trường và gọi tên điều con nhìn thấy.', materials: 'Thẻ màu giấy', safety: 'Đi cùng người lớn, tránh khu vực xe di chuyển.' },
    { id: 'activity-2', title: 'Khu vườn nhỏ của bé', kind: 'Ngoài trời', version: 'v2', status: 'Chờ rà soát', instructions: 'Quan sát lá, hình dạng và gân lá; kể lại điều con tò mò.', materials: 'Kính lúp nhựa', safety: 'Không bứt cây hoặc đưa vật liệu lên miệng.' },
    { id: 'activity-3', title: 'Âm thanh quanh em', kind: 'Trong nhà', version: 'v1', status: 'Nháp', instructions: 'Lắng nghe âm thanh nhẹ trong phòng và mô tả bằng từ của con.', materials: 'Không cần', safety: 'Giữ âm lượng vừa phải.' },
  ]);
  const [selectedId, setSelectedId] = useState('activity-1');
  const [filter, setFilter] = useState('Tất cả');
  const [search, setSearch] = useState('');
  const [draftTitle, setDraftTitle] = useState('');
  const [draftKind, setDraftKind] = useState('Ngoài trời');
  const [draftInstructions, setDraftInstructions] = useState('');
  const [draftMaterials, setDraftMaterials] = useState('');
  const [draftSafety, setDraftSafety] = useState('');
  const [reviewReason, setReviewReason] = useState('');
  const [decision, setDecision] = useState<'Đã duyệt' | 'Yêu cầu chỉnh sửa' | ''>('');
  const [publishConfirmed, setPublishConfirmed] = useState(false);
  const [retireAt, setRetireAt] = useState('');
  const [retireReason, setRetireReason] = useState('');
  const [retireConfirmed, setRetireConfirmed] = useState(false);
  const [notice, setNotice] = useState('');
  const retireMinDate = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  const selected = items.find((item) => item.id === selectedId) ?? items[0];
  const visible = items.filter((item) => (filter === 'Tất cả' || item.status === filter) && `${item.title} ${item.kind} ${item.version}`.toLocaleLowerCase('vi').includes(search.toLocaleLowerCase('vi')));
  const addDraft = (event: React.FormEvent) => {
    event.preventDefault();
    const item: CatalogPreviewItem = { id: `activity-${Date.now()}`, title: draftTitle.trim(), kind: draftKind, version: 'v1', status: 'Nháp', instructions: draftInstructions.trim(), materials: draftMaterials.trim(), safety: draftSafety.trim() };
    setItems((current) => [item, ...current]);
    setSelectedId(item.id);
    setDraftTitle(''); setDraftInstructions(''); setDraftMaterials(''); setDraftSafety('');
    setNotice('Đã tạo bản nháp minh họa trong phiên preview; chưa lưu lên catalog.');
  };
  const createRevision = () => {
    const number = Number(selected.version.replace(/\D/g, '')) || 1;
    const revision: CatalogPreviewItem = {...selected, id: `activity-${Date.now()}`, version: `v${number + 1}`, status: 'Nháp', reviewReason: undefined, retireAt: undefined, retireReason: undefined};
    setItems((current) => [revision, ...current]); setSelectedId(revision.id); setNotice('Đã tạo revision mới trong preview; bản đã phát hành vẫn nguyên trạng.'); setReviewReason(''); setDecision(''); setPublishConfirmed(false);
  };
  const submitForReview = () => { setItems((current) => current.map((item) => item.id === selected.id ? {...item, status: 'Chờ rà soát', reviewReason: undefined} : item)); setNotice('Đã chuyển trạng thái sang chờ rà soát trong preview; không gửi yêu cầu tới backend.'); };
  const recordReview = (event: React.FormEvent) => { event.preventDefault(); if (!decision || !reviewReason.trim()) return; setItems((current) => current.map((item) => item.id === selected.id ? {...item, status: decision, reviewReason: reviewReason.trim()} : item)); setNotice(`Đã ghi “${decision}” trong phiên preview; chưa phát hành nội dung.`); setDecision(''); setReviewReason(''); };
  const publishPreview = () => { if (!publishConfirmed || selected.status !== 'Đã duyệt') return; setItems((current) => current.map((item) => item.id === selected.id ? {...item, status: 'Đã phát hành'} : item)); setNotice('Đã đổi trạng thái phát hành trong preview; catalog thật không thay đổi.'); setPublishConfirmed(false); };
  const retirePreview = (event: React.FormEvent) => { event.preventDefault(); if (!retireAt || !retireReason.trim() || !retireConfirmed || selected.status !== 'Đã phát hành') return; setItems((current) => current.map((item) => item.id === selected.id ? {...item, retireAt, retireReason: retireReason.trim()} : item)); setNotice(`Đã lên lịch ngừng version ${selected.version} từ ${retireAt} trong preview. Snapshot run đã tạo được giữ nguyên.`); setRetireConfirmed(false); };
  return <div className="flow-page"><header className="flow-heading"><span>NỘI DUNG NỀN TẢNG · BẢN XEM TRƯỚC</span><h1>Danh mục hoạt động</h1><p>Soạn nháp, tạo revision và xem các cổng rà soát trước khi phát hành.</p></header><div className="feedback-preview-note" role="note"><strong>Chưa kết nối Activity Catalog API</strong><span>Các trạng thái bên dưới dùng dữ liệu mẫu; không có nội dung nào được phát hành thật.</span></div><div className="catalog-workbench"><section className="catalog-create-panel"><span className="flow-eyebrow">BẢN NHÁP MỚI</span><h2>Soạn hoạt động</h2><form onSubmit={addDraft}><label>Tên hoạt động<input required maxLength={100} value={draftTitle} onChange={(event) => setDraftTitle(event.target.value)} placeholder="Ví dụ: Săn hình trong khu vườn"/></label><label>Loại hoạt động<select value={draftKind} onChange={(event) => setDraftKind(event.target.value)}><option>Ngoài trời</option><option>Trong nhà</option><option>Kết hợp</option></select></label><label>Cách thực hiện<textarea required maxLength={1000} rows={3} value={draftInstructions} onChange={(event) => setDraftInstructions(event.target.value)} placeholder="Mô tả các bước ngắn, dễ làm"/></label><label>Vật liệu<textarea required maxLength={500} rows={2} value={draftMaterials} onChange={(event) => setDraftMaterials(event.target.value)} placeholder="Liệt kê vật liệu cần chuẩn bị"/></label><label>An toàn<textarea required maxLength={500} rows={2} value={draftSafety} onChange={(event) => setDraftSafety(event.target.value)} placeholder="Nêu rủi ro và cách phòng tránh"/></label><button type="submit" className="flow-primary" disabled={!draftTitle.trim() || !draftInstructions.trim() || !draftMaterials.trim() || !draftSafety.trim()}>Tạo bản nháp preview</button></form><p className="preview-boundary-note">Không đặt nhóm tuổi/giáo án mặc định khi chính sách chưa được chốt.</p></section><section className="catalog-list-panel"><div className="catalog-list-head"><div><span className="flow-eyebrow">VERSION & TRẠNG THÁI</span><h2>Nội dung hoạt động</h2></div><label>Tìm kiếm<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Tên hoặc version"/></label></div><div className="feedback-filters" role="group" aria-label="Lọc trạng thái hoạt động"><button type="button" className={filter === 'Tất cả' ? 'is-active' : ''} onClick={() => setFilter('Tất cả')}>Tất cả</button>{(['Nháp', 'Chờ rà soát', 'Đã duyệt', 'Đã phát hành', 'Yêu cầu chỉnh sửa'] as CatalogStatus[]).map((value) => <button type="button" key={value} className={filter === value ? 'is-active' : ''} onClick={() => setFilter(value)}>{value}</button>)}</div><div className="catalog-records">{visible.map((item) => <button type="button" key={item.id} className={selected.id === item.id ? 'is-selected' : ''} onClick={() => { setSelectedId(item.id); setNotice(''); setDecision(''); setReviewReason(''); setPublishConfirmed(false); setRetireAt(item.retireAt ?? String()); setRetireReason(item.retireReason ?? String()); setRetireConfirmed(false); }}><span className="catalog-record-icon" aria-hidden="true">{item.kind === 'Ngoài trời' ? '↗' : '◌'}</span><span><strong>{item.title}</strong><small>{item.kind} · {item.version}</small></span><i className={`catalog-status catalog-status--${item.status === 'Đã phát hành' ? 'published' : item.status === 'Nháp' ? 'draft' : item.status === 'Chờ rà soát' ? 'review' : 'other'}`}>{item.status}</i></button>)}{visible.length === 0 && <div className="feedback-empty"><strong>Không có hoạt động phù hợp</strong><span>Đổi bộ lọc hoặc tạo bản nháp mới.</span></div>}</div><small className="preview-count">{visible.length} mục · dữ liệu minh họa</small></section><article className="catalog-detail-panel"><span className="flow-eyebrow">CHI TIẾT VERSION · PREVIEW</span><h2>{selected.title}</h2><p>{selected.kind} · {selected.version}</p><div className="catalog-detail-fields"><div><strong>Cách thực hiện</strong><p>{selected.instructions}</p></div><div><strong>Vật liệu</strong><p>{selected.materials}</p></div><div><strong>An toàn</strong><p>{selected.safety}</p></div></div>{selected.reviewReason && <div className="flow-note"><strong>Lý do review:</strong> {selected.reviewReason}</div>}<div className="catalog-actions">{selected.status === 'Nháp' || selected.status === 'Yêu cầu chỉnh sửa' ? <><button type="button" className="flow-secondary" onClick={createRevision}>Tạo revision mới</button><button type="button" className="flow-primary" onClick={submitForReview}>Gửi rà soát preview</button></> : null}{selected.status === 'Đã phát hành' ? <button type="button" className="flow-primary" onClick={createRevision}>Tạo revision mới · giữ bản đã phát hành</button> : null}{selected.status === 'Chờ rà soát' && <form className="catalog-review-form" onSubmit={recordReview}><label>Kết quả rà soát<select required value={decision} onChange={(event) => setDecision(event.target.value as typeof decision)}><option value="">Chọn kết quả</option><option value="Đã duyệt">Đạt review</option><option value="Yêu cầu chỉnh sửa">Yêu cầu chỉnh sửa</option></select></label><label>Lý do<textarea required maxLength={400} rows={2} value={reviewReason} onChange={(event) => setReviewReason(event.target.value)} placeholder="Ghi lý do gắn với version này"/></label><button className="flow-primary" type="submit" disabled={!decision || !reviewReason.trim()}>Ghi review preview</button></form>}{selected.status === 'Đã duyệt' && <div className="catalog-publish-review"><label className="flow-check"><input type="checkbox" checked={publishConfirmed} onChange={(event) => setPublishConfirmed(event.target.checked)}/><span>Đã kiểm tra đúng version và trạng thái review.</span></label><button type="button" className="flow-primary" disabled={!publishConfirmed} onClick={publishPreview}>Phát hành preview</button><small>Quyền phát hành thật phải được xác nhận từ backend.</small></div>}{selected.status === 'Đã phát hành' ? (selected.retireAt ? <div className="catalog-retire-scheduled" role="status"><span className="preview-state preview-state--paused">ĐÃ LÊN LỊCH NGỪNG · PREVIEW</span><strong>Hiệu lực dự kiến: {selected.retireAt}</strong><p>{selected.retireReason}</p><small>Run đã tạo vẫn giữ snapshot/version đã ghim; lịch ngừng chưa được gửi lên server.</small></div> : <form className="catalog-retire-form" onSubmit={retirePreview}><span className="flow-eyebrow">RETIRE · RÀ SOÁT RIÊNG</span><h3>Ngừng phát hành version này</h3><p>Nội dung mới sẽ không được đề xuất sau thời điểm hiệu lực; run đã tạo vẫn giữ snapshot đã ghim.</p><label>Thời điểm hiệu lực<input type="date" min={retireMinDate} required value={retireAt} onChange={(event) => setRetireAt(event.target.value)}/></label><label>Lý do ngừng<textarea required maxLength={400} rows={2} value={retireReason} onChange={(event) => setRetireReason(event.target.value)} placeholder="Ghi lý do để lưu cùng lịch sử preview"/></label><label className="flow-check"><input type="checkbox" checked={retireConfirmed} onChange={(event) => setRetireConfirmed(event.target.checked)}/><span>Đã chọn đúng version và hiểu snapshot của run hiện hữu không đổi.</span></label><button type="submit" className="flow-danger" disabled={!retireAt || !retireReason.trim() || !retireConfirmed}>Xem lại lịch ngừng · preview</button><small>Không ghi catalog thật; quyền Content Admin và audit cần được xác nhận từ backend.</small></form>) : null}</div>{notice && <p className="groups-notice" role="status">{notice}</p>}<p className="preview-boundary-note">Version đã phát hành được giữ nguyên; chỉnh sửa bắt đầu bằng revision mới.</p></article></div><FlowRecoveryDisclosure title="Danh mục hoạt động và phát hành" boundary="Quyền publish, moderation và version được xác nhận từ backend; trạng thái preview không thay thế approval thật."/></div>;
}

type ModerationPreviewItem = { id: string; title: string; kind: string; organization: string; version: string; status: 'Chờ rà soát' | 'Đang hiển thị' | 'Đã ẩn' | 'Yêu cầu chỉnh sửa · preview'; summary: string };
function ModerationWorkbench() {
  const [items, setItems] = useState<ModerationPreviewItem[]>([
    { id: 'mod-1', title: 'Khu vườn nhỏ của bé', kind: 'Giáo án công khai', organization: 'Trường Ánh Nắng', version: 'v1.2', status: 'Đang hiển thị', summary: 'Chủ đề quan sát thiên nhiên, có mục tiêu và hoạt động.' },
    { id: 'mod-2', title: 'Dạo bước tìm màu sắc', kind: 'Hoạt động', organization: 'Catalog nền tảng', version: 'v2', status: 'Chờ rà soát', summary: 'Hoạt động nhận biết màu, cần kiểm tra lưu ý an toàn.' },
    { id: 'mod-3', title: 'Âm thanh quanh em', kind: 'Hoạt động', organization: 'Catalog nền tảng', version: 'v1', status: 'Đã ẩn', summary: 'Hoạt động lắng nghe âm thanh nhẹ; nội dung đang được xem lại trước khi mở lại.' },
  ]);
  const [selectedId, setSelectedId] = useState('mod-1');
  const [filter, setFilter] = useState('Tất cả');
  const [reason, setReason] = useState('');
  const [decision, setDecision] = useState<'Đã duyệt · preview' | 'Yêu cầu chỉnh sửa · preview' | ''>('');
  const [notice, setNotice] = useState('');
  const selected = items.find((item) => item.id === selectedId) ?? items[0];
  const filteredItems = items.filter((item) => filter === 'Tất cả' || item.status.startsWith(filter));
  const recordDecision = (event: React.FormEvent) => { event.preventDefault(); if (!decision || !reason.trim()) return; const status = decision === 'Đã duyệt · preview' ? 'Đang hiển thị' : 'Yêu cầu chỉnh sửa · preview'; setItems((current) => current.map((item) => item.id === selected.id ? {...item, status} : item)); setNotice(`Đã ghi nhận ${decision} trong preview; chưa publish hoặc thay đổi quyền truy cập.`); setDecision(''); setReason(''); };
  const setVisibility = (status: 'Đang hiển thị' | 'Đã ẩn') => { setItems((current) => current.map((item) => item.id === selected.id ? {...item, status} : item)); setNotice(`${status === 'Đã ẩn' ? 'Đã ẩn' : 'Đã mở lại'} nội dung trong phiên preview; chưa thay đổi catalog thật.`); };
  const statusClass = selected.status === 'Đang hiển thị' ? 'catalog-status--published' : selected.status === 'Chờ rà soát' ? 'catalog-status--review' : selected.status === 'Đã ẩn' ? 'catalog-status--other' : 'catalog-status--draft';
  return <div className="flow-page"><header className="flow-heading"><span>QUẢN TRỊ NỘI DUNG · BẢN XEM TRƯỚC</span><h1>Kiểm duyệt thư viện bài học</h1><p>Tra cứu version và chỉ hiển thị hành động phù hợp với trạng thái hiện tại.</p></header><div className="feedback-preview-note" role="note"><strong>Chưa kết nối Moderation API</strong><span>Hàng chờ là dữ liệu mẫu; mọi quyết định và trạng thái chỉ thay đổi trong phiên preview.</span></div><section className="moderation-workbench"><div className="moderation-list-panel"><div className="feedback-filters" role="group" aria-label="Lọc nội dung kiểm duyệt">{['Tất cả', 'Chờ rà soát', 'Đang hiển thị', 'Đã ẩn', 'Yêu cầu chỉnh sửa'].map((value) => <button type="button" key={value} className={filter === value ? 'is-active' : ''} onClick={() => setFilter(value)}>{value}</button>)}</div><div className="catalog-records">{filteredItems.map((item) => <button type="button" key={item.id} className={selected.id === item.id ? 'is-selected' : ''} onClick={() => { setSelectedId(item.id); setDecision(''); setReason(''); setNotice(''); }}><span className="catalog-record-icon" aria-hidden="true">{item.status === 'Đã ẩn' ? '○' : item.status === 'Chờ rà soát' ? '↗' : '✓'}</span><span><strong>{item.title}</strong><small>{item.kind} · {item.version}</small></span><i className={`catalog-status ${item.status === 'Đang hiển thị' ? 'catalog-status--published' : item.status === 'Chờ rà soát' ? 'catalog-status--review' : item.status === 'Đã ẩn' ? 'catalog-status--other' : 'catalog-status--draft'}`}>{item.status}</i></button>)}{filteredItems.length === 0 && <div className="feedback-empty"><strong>Không có nội dung ở trạng thái này</strong><span>Thử bộ lọc khác.</span></div>}</div></div><article className="moderation-detail-panel"><span className="flow-eyebrow">{selected.kind} · {selected.version}</span><h2>{selected.title}</h2><p>{selected.organization}</p><div className="moderation-effective-status"><span>Trạng thái hiệu lực</span><i className={`catalog-status ${statusClass}`}>{selected.status}</i></div><div className="moderation-safe-summary"><strong>Tóm tắt được phép xem</strong><p>{selected.summary}</p><small>Không hiển thị file gốc, tranh, video, transcript hoặc profile của trẻ.</small></div><div className="moderation-checklist"><span>✓ Revision đang chọn: {selected.version}</span><span>✓ Scope nội dung được rà soát theo fixture</span><span>○ Quyết định và audit server: chưa kết nối</span></div>{selected.status === 'Chờ rà soát' ? <form className="catalog-review-form" onSubmit={recordDecision}><label>Kết quả<select required value={decision} onChange={(event) => setDecision(event.target.value as typeof decision)}><option value="">Chọn quyết định</option><option value="Đã duyệt · preview">Đạt rà soát · hiển thị trong preview</option><option value="Yêu cầu chỉnh sửa · preview">Yêu cầu chỉnh sửa · preview</option></select></label><label>Lý do<textarea required maxLength={400} rows={3} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Ghi căn cứ gắn với version được chọn"/></label><button type="submit" className="flow-primary" disabled={!decision || !reason.trim()}>Ghi quyết định preview</button></form> : selected.status === 'Đang hiển thị' ? <div className="moderation-status-action"><p>Nội dung đang hiển thị. Có thể ẩn nội dung này nếu cần rà soát thêm.</p><button type="button" className="flow-danger" onClick={() => setVisibility('Đã ẩn')}>Ẩn nội dung · preview</button></div> : selected.status === 'Đã ẩn' ? <div className="moderation-status-action"><p>Nội dung đang ẩn, chưa được đề xuất cho gia đình.</p><button type="button" className="flow-primary" onClick={() => setVisibility('Đang hiển thị')}>Mở lại nội dung · preview</button></div> : <p className="preview-boundary-note">Nội dung đang chờ phiên bản sửa; không có hành động mở lại ở trạng thái này.</p>}{notice && <p className="groups-notice" role="status">{notice}</p>}</article></section><FlowRecoveryDisclosure title="Kiểm duyệt thư viện bài học" boundary="Hành động ẩn/mở lại thật phải dùng quyền Platform Admin, trạng thái mới nhất, expected revision và audit server-side."/></div>;
}

function ManagerBillingConsole() {
  const [scenario, setScenario] = useState<'active' | 'pending' | 'unverified' | 'failed-grace' | 'grace-ended' | 'recovered'>('active');
  const [autoRenew, setAutoRenew] = useState(true);
  const [renewalNotice, setRenewalNotice] = useState('');
  const [changeType, setChangeType] = useState<'increase' | 'decrease'>('increase');
  const [effectiveAt, setEffectiveAt] = useState('');
  const [selectedClasses, setSelectedClasses] = useState<string[]>([]);
  const [capacityConfirmed, setCapacityConfirmed] = useState(false);
  const [capacityNotice, setCapacityNotice] = useState('');
  const [planAction, setPlanAction] = useState<'renew' | 'upgrade'>('renew');
  const [planEffectiveAt, setPlanEffectiveAt] = useState('');
  const [planConfirmed, setPlanConfirmed] = useState(false);
  const [planNotice, setPlanNotice] = useState('');
  const today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  const stateCopy: Record<typeof scenario, {label: string; body: string; tone: string}> = {
    active: {label: 'Đang hoạt động · minh họa', body: 'Kỳ dịch vụ, capacity và quota thật chỉ hiện sau khi Billing API xác nhận.', tone: 'ready'},
    pending: {label: 'Thanh toán đang chờ · minh họa', body: 'Giữ nguyên entitlement hiện tại. Không bắt đầu lần thanh toán mới khi kết quả cũ chưa rõ.', tone: 'paused'},
    unverified: {label: 'Callback chưa xác minh · minh họa', body: 'Không tin kết quả quay về từ trình duyệt; chỉ callback đã xác minh mới đổi trạng thái.', tone: 'paused'},
    'failed-grace': {label: 'Thanh toán lỗi · trong grace · minh họa', body: 'Kỳ hiện tại chờ khôi phục. Billing API phải trả thời gian grace và quyền hiện hành.', tone: 'paused'},
    'grace-ended': {label: 'Grace đã kết thúc · minh họa', body: 'Chặn tạo lớp/run mới; vẫn cho xem lớp, roster, lịch sử và quản lý thanh toán.', tone: 'blocked'},
    recovered: {label: 'Đã khôi phục · minh họa', body: 'Chỉ chuyển active sau khi Billing xác minh thanh toán; đây chưa phải kết quả thật.', tone: 'ready'},
  };
  const submitCapacity = (event: React.FormEvent): void => {
    event.preventDefault();
    if (!effectiveAt || !capacityConfirmed || (changeType === 'decrease' && selectedClasses.length === 0)) return;
    const direction = changeType === 'increase' ? 'Tăng capacity' : 'Hạ capacity';
    setCapacityNotice(`${direction} đã vào trạng thái chờ Billing · preview, hiệu lực dự kiến ${effectiveAt}${selectedClasses.length ? ` · lớp: ${selectedClasses.join(', ')}` : ''}. Không có yêu cầu thật được gửi.`);
  };
  const changeAutoRenew = (enabled: boolean): void => {
    setAutoRenew(enabled);
    setRenewalNotice(enabled
      ? 'Đã bật tự gia hạn trong preview; không có thay đổi Billing thật.'
      : 'Đã tắt tự gia hạn trong preview. Quyền giữ đến hết kỳ đã trả; không tự tính hoàn tiền prorate.');
  };
  const submitPlanRequest = (event: React.FormEvent): void => {
    event.preventDefault();
    if (!planEffectiveAt || !planConfirmed) return;
    const actionLabel = planAction === 'renew' ? 'Gia hạn kỳ hiện tại' : 'Đề xuất nâng gói';
    setScenario('pending');
    setPlanNotice(`${actionLabel} · preview đang chờ Billing. Chưa chọn package/price version và chưa mở thanh toán.`);
    setPlanConfirmed(false);
  };
  return <div className="flow-page"><header className="flow-heading"><span>ĐIỀU HÀNH NHÀ TRƯỜNG · BẢN XEM TRƯỚC</span><h1>Gói dịch vụ & hóa đơn</h1><p>Rà soát kỳ dịch vụ, thanh toán và capacity. Không hiển thị giá hoặc entitlement giả.</p></header>
    <div className="feedback-preview-note" role="note"><strong>Chưa kết nối Billing API</strong><span>Tất cả thao tác dưới đây là fixture; không mở cổng thanh toán, đổi gói hay ghi entitlement.</span></div>
    <section className="billing-lifecycle-workbench">
      <article className="billing-current-card"><div className="billing-current-heading"><div><span className="flow-eyebrow">TRẠNG THÁI GÓI</span><h2>{stateCopy[scenario].label}</h2></div><span className={`preview-state preview-state--${stateCopy[scenario].tone}`}>PREVIEW</span></div><p>{stateCopy[scenario].body}</p><dl><div><dt>Kỳ hiệu lực</dt><dd>Chờ Billing API</dd></div><div><dt>Tự gia hạn</dt><dd>{autoRenew ? 'Bật · preview' : 'Tắt · preview'}</dd></div><div><dt>Capacity & quota</dt><dd>Chưa có dữ liệu xác thực</dd></div></dl><label className="billing-scenario-select">Xem trạng thái thanh toán<select value={scenario} onChange={(event) => { setScenario(event.target.value as typeof scenario); setPlanConfirmed(false); setCapacityConfirmed(false); }}><option value="active">Đang hoạt động</option><option value="pending">Thanh toán đang chờ</option><option value="unverified">Callback chưa xác minh</option><option value="failed-grace">Thanh toán lỗi · trong grace</option><option value="grace-ended">Grace đã kết thúc</option><option value="recovered">Đã khôi phục sau đối soát</option></select></label></article>
      <article className="billing-invoices"><div className="catalog-list-head"><div><span className="flow-eyebrow">HÓA ĐƠN</span><h2>Lịch sử thanh toán</h2></div><span className="preview-state preview-state--paused">Chờ Billing API</span></div><div className="billing-empty"><span aria-hidden="true">—</span><strong>Chưa có hóa đơn để hiển thị</strong><p>Hóa đơn, số tiền và hạn thanh toán chỉ hiện sau khi backend xác minh.</p></div><button type="button" className="flow-secondary" onClick={() => { setScenario('pending'); setRenewalNotice('Mở hành trình thanh toán preview; không chuyển trang hoặc gửi giao dịch.'); }}>Xem hành trình thanh toán · preview</button></article>
    </section>
    <section className="billing-action-grid">
      <article className="billing-action-card"><span className="flow-eyebrow">GIA HẠN</span><h2>Quản lý tự gia hạn</h2><p>Tắt gia hạn vẫn giữ quyền đến hết kỳ đã trả; V1 không tự tính hoàn tiền prorate.</p><div className="billing-renewal-toggle"><span>Tự gia hạn</span><button type="button" aria-pressed={autoRenew} className={autoRenew ? 'is-on' : ''} onClick={() => changeAutoRenew(!autoRenew)}>{autoRenew ? 'Đang bật' : 'Đang tắt'} · preview</button></div>{renewalNotice ? <p className="billing-inline-status" role="status">{renewalNotice}</p> : null}</article>
      <article className="billing-action-card"><span className="flow-eyebrow">GÓI DỊCH VỤ</span><h2>Gia hạn hoặc nâng gói</h2><p>Chọn loại yêu cầu và ngày hiệu lực. Package, price version và quyền thanh toán phải được Billing xác nhận.</p><form className="billing-plan-form" onSubmit={submitPlanRequest}><label>Yêu cầu<select value={planAction} onChange={(event) => { setPlanAction(event.target.value as typeof planAction); setPlanNotice(''); setPlanConfirmed(false); }}><option value="renew">Gia hạn kỳ hiện tại</option><option value="upgrade">Đề xuất nâng gói</option></select></label><label>Ngày hiệu lực dự kiến<input type="date" min={today} value={planEffectiveAt} onChange={(event) => { setPlanEffectiveAt(event.target.value); setPlanConfirmed(false); }}/></label><label className="flow-check"><input type="checkbox" checked={planConfirmed} onChange={(event) => setPlanConfirmed(event.target.checked)}/><span>Đã xem trạng thái hiện tại; yêu cầu vẫn cần Billing xác minh.</span></label><button type="submit" className="flow-primary" disabled={!planEffectiveAt || !planConfirmed}>Gửi đề xuất · preview</button></form>{planNotice ? <p className="billing-inline-status" role="status">{planNotice}</p> : null}</article>
      <article className="billing-action-card"><span className="flow-eyebrow">ĐỔI CAPACITY</span><h2>Rà soát thay đổi sức chứa</h2><p>Giá và số slot mới do Billing trả về. Khi hạ capacity, chọn lớp và thời điểm hiệu lực.</p><form className="billing-capacity-form" onSubmit={submitCapacity}><label>Thay đổi<select value={changeType} onChange={(event) => { setChangeType(event.target.value as typeof changeType); setCapacityNotice(''); setCapacityConfirmed(false); }}><option value="increase">Tăng capacity</option><option value="decrease">Hạ capacity</option></select></label>{changeType === 'decrease' ? <fieldset className="billing-class-selection"><legend>Lớp dự kiến tạm ngưng · bắt buộc</legend>{['Lớp Lá 1', 'Lớp Chồi 2', 'Lớp Mầm 1'].map((name) => <label key={name}><input type="checkbox" checked={selectedClasses.includes(name)} onChange={(event) => { setSelectedClasses((current) => event.target.checked ? [...current, name] : current.filter((item) => item !== name)); setCapacityConfirmed(false); }}/><span>{name}</span></label>)}</fieldset> : null}<label>Thời điểm hiệu lực<input type="date" min={today} value={effectiveAt} onChange={(event) => { setEffectiveAt(event.target.value); setCapacityConfirmed(false); }}/></label><label className="flow-check"><input type="checkbox" checked={capacityConfirmed} onChange={(event) => setCapacityConfirmed(event.target.checked)}/><span>Đã xem ảnh hưởng lớp và ngày hiệu lực dự kiến.</span></label><button type="submit" className="flow-primary" disabled={!effectiveAt || !capacityConfirmed || (changeType === 'decrease' && selectedClasses.length === 0)}>Xem lại đề xuất · preview</button></form>{capacityNotice ? <p className="billing-inline-status" role="status">{capacityNotice}</p> : null}</article>
    </section>
    <FlowRecoveryDisclosure title="Gói và thanh toán" boundary="Payment callback, renewal event, entitlement và capacity chỉ có hiệu lực sau khi Billing xác minh. Mua thêm quota vẫn OPEN theo Q193."/>
  </div>;
}

const deckSpec: Flow = { title: 'Bộ hướng dẫn nét vẽ', description: 'Tùy chọn bật trong session; deck dùng plan đã duyệt và bao quát các hoạt động.', boundary: 'Deck cũ STALE khi plan đổi. Tạo lại từng bước tạo revision mới; không tiêu quota video.', steps: [
  { eyebrow: '01 · TÙY CHỌN', title: 'Bật hướng dẫn', summary: 'Nếu không bật, occurrence tiếp tục không có deck hoặc AI job.', fields: [{ id: 'enable', label: 'Bật AI line-sketch cho buổi dạy này', kind: 'checkbox' }, { id: 'age', label: 'Nhóm tuổi mục tiêu', kind: 'select', options: ['3–4 tuổi', '4–5 tuổi', '5–6 tuổi'], requiredWhen: { field: 'enable', value: true } }] },
  { eyebrow: '02 · TRÌNH CHIẾU', title: 'Xem từng nét', summary: 'Bề mặt 16:9 nền trắng; chọn activity/chủ thể, Back/Next hoặc bỏ qua.', fields: [{ id: 'activity', label: 'Hoạt động', kind: 'select', options: ['Quan sát khu vườn', 'Vẽ bông hoa yêu thích'], required: true }] },
] };

type ManagerReviewItem = { id: string; title: string; version: string; owner: string; submitted: string; requestedVisibility: string; status: 'Chờ rà soát' | 'Đã duyệt · preview' | 'Yêu cầu chỉnh sửa · preview'; objective: string; activities: string[]; materials: string; safety: string; history: string[] };
const managerReviewGates = [
  'Đúng giáo án và phiên bản được gửi',
  'Mục tiêu phù hợp nhóm tuổi',
  'Hoạt động và vật liệu có thể thực hiện',
  'Lưu ý an toàn và phạm vi hiển thị đã rõ',
];

function ManagerPublicationReview() {
  const [items, setItems] = useState<ManagerReviewItem[]>([
    { id: 'lesson-seed', title: 'Hành trình của hạt mầm', version: 'v1.0', owner: 'Cô Mai · Lớp Lá 1', submitted: 'Hôm nay, 09:15', requestedVisibility: 'Công khai trong thư viện', status: 'Chờ rà soát', objective: 'Quan sát hạt nảy mầm và kể lại các thay đổi bằng lời của trẻ.', activities: ['Ươm một hạt mầm', 'Vẽ cây theo trí tưởng tượng'], materials: 'Hạt đậu, cốc giấy, bông ẩm, giấy và bút màu.', safety: 'Người lớn chuẩn bị hạt; không cho hạt hoặc bông vào miệng.', history: ['v1.0 · gửi duyệt · hôm nay'] },
    { id: 'lesson-cloud', title: 'Những đám mây kể chuyện', version: 'v1.2', owner: 'Cô Lan · Lớp Chồi 2', submitted: 'Hôm qua, 14:30', requestedVisibility: 'Công khai trong thư viện', status: 'Chờ rà soát', objective: 'Quan sát hình dạng đám mây và diễn đạt điều trẻ tưởng tượng.', activities: ['Tìm hình trong mây', 'Vẽ bầu trời hôm nay'], materials: 'Giấy, bút màu; quan sát từ khu vực có mái che.', safety: 'Không nhìn thẳng mặt trời; luôn có người lớn giám sát.', history: ['v1.1 · yêu cầu bổ sung · 10/11', 'v1.2 · gửi duyệt · hôm qua'] },
  ]);
  const [selectedId, setSelectedId] = useState('lesson-seed');
  const [tab, setTab] = useState<'content' | 'versions'>('content');
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [reason, setReason] = useState('');
  const [notice, setNotice] = useState('');
  const selected = items.find((item) => item.id === selectedId) ?? items[0];
  const readyToApprove = managerReviewGates.every((gate) => checked[gate]);
  const approve = () => {
    if (!readyToApprove || selected.status !== 'Chờ rà soát') return;
    setItems((current) => current.map((item) => item.id === selected.id ? { ...item, status: 'Đã duyệt · preview', history: [...item.history, `${item.version} · duyệt trong preview`] } : item));
    setNotice(`Đã ghi trạng thái duyệt minh họa cho ${selected.version}; không công khai giáo án thật.`);
  };
  const requestChanges = (event: React.FormEvent) => {
    event.preventDefault();
    if (!reason.trim() || selected.status !== 'Chờ rà soát') return;
    setItems((current) => current.map((item) => item.id === selected.id ? { ...item, status: 'Yêu cầu chỉnh sửa · preview', history: [...item.history, `${item.version} · yêu cầu bổ sung trong preview`] } : item));
    setNotice(`Đã ghi yêu cầu chỉnh sửa minh họa: ${reason.trim()}`);
    setReason('');
  };
  return <div className="flow-page manager-publication-page">
    <header className="flow-heading"><span>NHÀ TRƯỜNG · BẢN XEM TRƯỚC</span><h1>Duyệt giáo án công khai</h1><p>Rà soát đúng nội dung và version trước khi quyết định trong quy trình của trường.</p></header>
    <div className="feedback-preview-note" role="note"><strong>Quyết định chỉ nằm trong fixture</strong><span>Không có quyền công khai nào được cấp trên hệ thống; mỗi quyết định tương lai cần đúng version và được ghi audit.</span></div>
    <section className="manager-publication-workbench">
      <aside className="manager-publication-queue"><div className="catalog-list-head"><div><span className="flow-eyebrow">HÀNG CHỜ</span><h2>Yêu cầu đang chờ</h2></div><span>{items.filter((item) => item.status === 'Chờ rà soát').length}</span></div>{items.map((item) => <button type="button" key={item.id} className={selected.id === item.id ? 'is-selected' : ''} onClick={() => { setSelectedId(item.id); setTab('content'); setChecked({}); setNotice(''); setReason(''); }}><span className="catalog-record-icon">{item.status === 'Chờ rà soát' ? '↗' : '✓'}</span><span><strong>{item.title}</strong><small>{item.version} · {item.owner}</small></span><i className={`preview-state ${item.status === 'Chờ rà soát' ? 'preview-state--paused' : 'preview-state--active'}`}>{item.status}</i></button>)}</aside>
      <article className="manager-publication-detail"><div className="manager-publication-title"><div><span className="flow-eyebrow">VERSION ĐƯỢC GỬI · {selected.version}</span><h2>{selected.title}</h2><p>{selected.owner} · {selected.submitted}</p></div><span className="manager-requested-visibility"><small>Yêu cầu hiển thị</small><strong>{selected.requestedVisibility}</strong></span></div>
        <div className="manager-publication-tabs" role="tablist" aria-label="Nội dung và phiên bản"><button type="button" role="tab" aria-selected={tab === 'content'} className={tab === 'content' ? 'is-active' : ''} onClick={() => setTab('content')}>Nội dung</button><button type="button" role="tab" aria-selected={tab === 'versions'} className={tab === 'versions' ? 'is-active' : ''} onClick={() => setTab('versions')}>Lịch sử phiên bản</button></div>
        {tab === 'content' ? <div className="manager-review-content"><section><span>Mục tiêu</span><p>{selected.objective}</p></section><section><span>Hoạt động</span><ol>{selected.activities.map((activity) => <li key={activity}>{activity}</li>)}</ol></section><section><span>Vật liệu</span><p>{selected.materials}</p></section><section><span>Lưu ý an toàn</span><p>{selected.safety}</p></section></div> : <div className="manager-version-history">{selected.history.map((record) => <p key={record}><i/>{record}</p>)}</div>}
        {selected.status === 'Chờ rà soát' ? <>
          <section className="manager-review-checklist"><div><span className="flow-eyebrow">CỔNG KIỂM TRA</span><strong>Hoàn tất cả bốn mục để bật duyệt</strong></div>{managerReviewGates.map((gate) => <label key={gate}><input type="checkbox" checked={Boolean(checked[gate])} onChange={(event) => setChecked((current) => ({ ...current, [gate]: event.target.checked }))}/><span>{gate}</span></label>)}</section>
          <div className="manager-publication-actions"><button type="button" className="flow-primary" disabled={!readyToApprove} onClick={approve}>Duyệt version này · preview</button><span>{readyToApprove ? 'Đã đủ bốn cổng rà soát.' : 'Nút duyệt mở sau khi đủ bốn xác nhận.'}</span></div>
          <form className="manager-change-request" onSubmit={requestChanges}><label>Yêu cầu chỉnh sửa<textarea value={reason} onChange={(event) => setReason(event.target.value)} required maxLength={400} rows={3} placeholder="Nêu nội dung cần bổ sung và lý do để Giáo viên sửa đúng phiên bản"/></label><button type="submit" className="flow-secondary" disabled={!reason.trim()}>Gửi yêu cầu chỉnh sửa · preview</button></form>
        </> : <div className="flow-note" role="status">Trạng thái hiện tại: {selected.status}. Chọn một yêu cầu khác để tiếp tục rà soát.</div>}
        {notice && <p className="groups-notice" role="status">{notice}</p>}
      </article>
    </section>
  </div>;
}

export function RoleFlowPage({ role, page }: { role: Role; page: string }) {
  if (page === 'session' && role === 'teacher') return <TeacherSessionWorkspace key={`${role}-${page}`}/>;
  if (page === 'review' && role === 'manager') return <ManagerPublicationReview key={`${role}-${page}`}/>;
  if (page === 'sample' && role === 'teacher') return <WizardPage key={`${role}-${page}`} spec={flowSpecs.sample}/>;
  if (page === 'transfers' && role === 'manager') return <ManagerTransferWorkbench key={`${role}-${page}`}/>;
  if (page === 'deck' && role === 'teacher') return <WizardPage key={`${role}-${page}`} spec={deckSpec}/>;
  if (page === 'feedback') return <FeedbackInboxPage key={`${role}-${page}`} role={role}/>;
  if (page === 'teachers' && role === 'manager') return <ManagerTeacherProvisioning key={`${role}-${page}`}/>;
  if (page === 'groups' && role === 'manager') return <ParentGroupsConsole key={`${role}-${page}`}/>;
  if (page === 'sharing' && role === 'teacher') return <TeacherSharingConsole key={`${role}-${page}`}/>;
  if (page === 'accounts' && role === 'admin') return <AccountsConsole key={`${role}-${page}`}/>;
  if (page === 'catalog' && role === 'admin') return <CatalogWorkbench key={`${role}-${page}`}/>;
  if (page === 'moderation' && role === 'admin') return <ModerationWorkbench key={`${role}-${page}`}/>;
  if (page === 'class-lifecycle' && role === 'manager') return <ManagerClassConsole key={`${role}-${page}`} mode="lifecycle"/>;
  if (page === 'capacity' && role === 'manager') return <ManagerClassConsole key={`${role}-${page}`} mode="capacity"/>;
  if (page === 'billing' && role === 'manager') return <ManagerBillingConsole key={`${role}-${page}`}/>;
  const allowed: Record<Role, string[]> = {
    teacher: ['teacher-scope','import','occurrences','session','children','sample','presentation','run-control','history','quota','inbox','sharing'],
    manager: ['assignment','roster','groups','teachers','review','transfers','capacity','class-lifecycle','billing','quota','notifications'],
    admin: ['moderation','catalog','accounts','jobs','health','billing-ops','audit','notifications'],
  };
  if (!allowed[role].includes(page)) return null;
  const flow = flowSpecs[page];
  const operation = operationSpecs[page];
  return flow ? <WizardPage key={`${role}-${page}`} spec={flow}/> : operation ? <OperationsPage key={`${role}-${page}`} spec={operation}/> : null;
}

export function hasRoleFlow(role: Role, page: string): boolean {
  return page === 'feedback' || (role === 'teacher' && page === 'deck') || ({ teacher: ['teacher-scope','import','occurrences','session','children','sample','presentation','run-control','history','quota','inbox','sharing'], manager: ['assignment','roster','groups','teachers','review','transfers','capacity','class-lifecycle','billing','quota','notifications'], admin: ['moderation','catalog','accounts','jobs','health','billing-ops','audit','notifications'] } as Record<Role,string[]>)[role].includes(page);
}

