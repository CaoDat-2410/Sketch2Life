import type { StatusTone } from "../../../shared/ui";

export type TeacherStatusContext = "lesson" | "visibility" | "plan" | "grant" | "session" | "job" | "default";

export type TeacherStatusMeta = {
  label: string;
  tone: StatusTone;
};

const COMMON_STATUS: Record<string, TeacherStatusMeta> = {
  APPROVED: { label: "Đã duyệt", tone: "success" },
  DRAFT: { label: "Bản nháp", tone: "neutral" },
  PENDING_REVIEW: { label: "Chờ duyệt", tone: "warn" },
  CHANGES_REQUESTED: { label: "Cần chỉnh sửa", tone: "warn" },
  REJECTED: { label: "Bị từ chối", tone: "danger" },
  SUPERSEDED: { label: "Đã thay thế", tone: "neutral" },
  ARCHIVED: { label: "Đã lưu trữ", tone: "neutral" },
  PUBLIC: { label: "Công khai", tone: "info" },
  PRIVATE: { label: "Riêng tư", tone: "neutral" },
  ACTIVE: { label: "Đang hoạt động", tone: "success" },
  CONFIRMED: { label: "Đã xác nhận", tone: "success" },
  REVOKED: { label: "Đã thu hồi", tone: "neutral" },
  INVITED: { label: "Đang chờ phụ huynh", tone: "warn" },
  OPEN: { label: "Đang mở", tone: "info" },
  CLOSED: { label: "Đã đóng", tone: "neutral" },
  QUEUED: { label: "Đang chờ", tone: "warn" },
  RUNNING: { label: "Đang xử lý", tone: "info" },
  SUCCEEDED: { label: "Hoàn thành", tone: "success" },
  COMPLETED: { label: "Hoàn thành", tone: "success" },
  FAILED: { label: "Thất bại", tone: "danger" },
  CANCELLED: { label: "Đã hủy", tone: "neutral" },
  READY: { label: "Sẵn sàng", tone: "success" },
  PROCESSING: { label: "Đang xử lý", tone: "info" },
  PRESENTING: { label: "Đang chiếu", tone: "info" },
  ENDED: { label: "Đã kết thúc", tone: "neutral" },
  NEEDS_REVIEW: { label: "Cần rà soát", tone: "warn" },
  READY_FOR_REVIEW: { label: "Sẵn sàng rà soát", tone: "success" },
  PENDING: { label: "Chờ giáo viên duyệt", tone: "warn" },
  PENDING_EDUCATOR_REVIEW: { label: "Chờ giáo viên duyệt", tone: "warn" },
  PENDING_CURATOR_REVIEW: { label: "Chờ quản trị nội dung", tone: "warn" },
  STROKE_READY: { label: "Có thể tạo hướng dẫn", tone: "success" },
  REQUIRES_MANUAL_AUTHORING: { label: "Cần biên soạn thủ công", tone: "warn" },
  STATIC_ONLY: { label: "Chỉ có hình tĩnh", tone: "neutral" },
  ACCEPTED: { label: "Đã xác nhận", tone: "success" },
  EXPIRED: { label: "Đã hết hạn", tone: "neutral" },
  WITHDRAWN: { label: "Đã rút", tone: "neutral" },
};

const CONTEXT_OVERRIDES: Partial<Record<TeacherStatusContext, Record<string, TeacherStatusMeta>>> = {
  plan: {
    APPROVED: { label: "Đã xác nhận", tone: "success" },
    CONFIRMED: { label: "Đã xác nhận", tone: "success" },
  },
  grant: {
    ACTIVE: { label: "Đang chia sẻ", tone: "success" },
  },
  visibility: {
    SCHOOL: { label: "Trong trường", tone: "info" },
    SELECTED_AUDIENCE: { label: "Chia sẻ chọn lọc", tone: "info" },
  },
  session: {
    PLANNED: { label: "Đã lên lịch", tone: "neutral" },
    ACTIVE: { label: "Đang diễn ra", tone: "info" },
    COMPLETED: { label: "Đã hoàn thành", tone: "success" },
  },
  job: {
    PENDING_CONFIRMATION: { label: "Chờ xác nhận", tone: "warn" },
    CONFIRMED: { label: "Đã xác nhận", tone: "success" },
  },
};

/** Resolve a raw backend status/visibility code into a Vietnamese label and StatusBadge tone. */
export function teacherStatusMeta(
  value: string | null | undefined,
  context: TeacherStatusContext = "default",
): TeacherStatusMeta {
  const key = (value ?? "").trim().toUpperCase();
  if (!key) return { label: context === "visibility" ? "Chưa rõ" : "Chưa rõ trạng thái", tone: "neutral" };
  const override = CONTEXT_OVERRIDES[context]?.[key];
  if (override) return override;
  return COMMON_STATUS[key] ?? { label: context === "visibility" ? "Chưa rõ" : "Đang xử lý", tone: "neutral" };
}
