import { Presentation } from "lucide-react";
import { FeatureAvailability, PageHeading } from "../../../shared/FeatureAvailability";

export function TeacherPresentationPage() {
  return (
    <div className="s2l-page">
      <PageHeading
        eyebrow="Teacher · Học liệu"
        title="Trình bày giáo án"
        description="Xem trước và sắp xếp nội dung trình bày cho buổi dạy."
        action={<span className="s2l-status-tag"><Presentation size={14} aria-hidden="true" />Đang chờ API</span>}
      />
      <FeatureAvailability
        title="Chưa thể chỉnh sửa bản trình bày"
        summary="Teacher cần soạn nội dung và thứ tự slide trước khi dùng trong occurrence. API hiện có hỗ trợ đọc và chỉnh sửa lesson content, nhưng chưa có contract slide và media để lưu bản trình bày."
        requirement="SRS §31.17 yêu cầu chỉnh sửa chữ slide, thêm/xóa/sắp xếp slide, tải ảnh, đặt ảnh hoặc SVG đã kiểm định, preview và reorder media. Published version phải bất biến; mọi chỉnh sửa tạo draft mới."
        dependencies={[
          "API slide/media draft có version precondition và lịch sử revision.",
          "Upload media có provenance, trạng thái kiểm duyệt và liên kết đến lesson revision.",
          "Catalog SVG được cấp phép và bộ dựng vector xác định; không nhận SVG/HTML/JS tự do.",
          "Nếu bật AI vector draft, chỉ nhận structured draft và phải qua Teacher review.",
        ]}
        permissionNote="Không tạo slide hoặc ảnh minh họa giả để làm như đã lưu. Không thay published revision."
        backTo="/teacher/t02-lesson-authoring"
        backLabel="Mở giáo án"
      />
    </div>
  );
}
