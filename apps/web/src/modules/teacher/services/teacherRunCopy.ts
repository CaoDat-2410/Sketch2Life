import { BackendApiError } from "../../../shared/api/backendApi";
import { NOT_FOUND_OR_NO_ACCESS } from "../../../shared/api/teacherHttp";
export const copy = { title:"Video mẫu", back:"Buổi dạy", missing:"Hãy chọn một buổi dạy để tiếp tục.", draw:"Chọn bé cho video mẫu", offer:"Hệ thống đã chọn ngẫu nhiên một bé đủ điều kiện. Bạn xem và xác nhận trước khi tạo video.", confirm:"Xác nhận bé này", reselect:"Chọn lại", empty:"Hiện chưa có lựa chọn hợp lệ cho video mẫu.", stopped:"Buổi dạy này không còn lượt chọn bé nào.", expired:"Lựa chọn đã hết hạn. Hãy chọn lại.", stale:"Bé được đề xuất không còn phù hợp. Bạn có thể chọn lại một lần.", active:"Bạn đang có một lượt video mẫu chưa hoàn tất.", other:"Lượt này thuộc một buổi dạy khác.", openOther:"Mở buổi dạy của lượt này", noPlan:"Giáo án của buổi học chưa được duyệt. Vui lòng duyệt giáo án rồi thử lại.", used:"Buổi học này đã có video mẫu.", unavailable:"Bước này chưa thực hiện được ở trạng thái hiện tại. Lớp ở chế độ chỉ xem cũng không cho thao tác.", activityGap:"Chưa thể bắt đầu lượt video mẫu vì kế hoạch chưa cho biết hoạt động được chọn.", activity:"Chọn hoạt động", create:"Bắt đầu lượt video mẫu", refresh:"Làm mới", cancel:"Hủy lượt", cancelConfirm:"Lượt này sẽ bị xóa và bạn có thể bắt đầu lại", delete:"Xóa lượt kể chuyện", deleteConfirm:"Xóa lượt kể chuyện này và toàn bộ nội dung của lượt? Thao tác này không thể hoàn tác.", deletePending:"Yêu cầu xóa đã được nhận. Nội dung sẽ được dọn trong nền.", deleted:"Lượt kể chuyện đã được xóa.", deleteConflict:"Lượt này chưa ở trạng thái xóa được hoặc lớp đang chỉ đọc.", quotaLoading:"Đang tải số dư lượt tạo video…", quotaUnavailable:"Chưa tải được số dư lượt tạo video.", quotaServiceUnavailable:"Dịch vụ quota tạm thời chưa sẵn sàng.", quotaBalance:(units:number)=>`Số dư lượt tạo video: ${units}`, noQuota:"Chưa được cấp lượt tạo video", until:"Còn hiệu lực đến", loading:"Đang tải", generic:"Không thể thực hiện lúc này. Vui lòng thử lại.", dependencyUnavailable:"Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.", consumed:"Lựa chọn này đã được dùng cho một lượt.", openRun:"Mở lượt video mẫu", videoSummary:"Video", firstStory:"Bước viết kịch bản đầu tiên chưa sẵn sàng. Lượt này đã lưu và bạn có thể quay lại sau.", generatingStory:"Đang tạo kịch bản đầu tiên. Lượt này sẽ tự chuyển sang bước xác nhận khi hoàn tất.", waitingStory:"Các bước bạn xác nhận đã hoàn tất. Lượt này đang chờ hệ thống kiểm tra điều kiện viết kịch bản." } as const;
export const stateLabels: Record<string,string> = { DRAFT:"Bản nháp", INPUT_PROCESSING:"Đang chuẩn bị tác phẩm và ý tưởng", INPUT_REVIEW:"Cần rà soát ý tưởng và thông tin", SUBJECT_REVIEW:"Cần xác nhận chủ thể bức tranh", PREPARATION_REVIEW:"Sẵn sàng viết kịch bản", STORY_GENERATING:"Đang viết kịch bản", SCRIPT_GENERATING:"Đang viết kịch bản", SCRIPT_GENERATION_UNKNOWN:"Đang kiểm tra kết quả viết kịch bản", SCRIPT_REVIEW:"Cần xác nhận kịch bản", VIDEO_ADMISSION_PENDING:"Đang gửi yêu cầu tạo video", VIDEO_QUEUED:"Video đang chờ xử lý", VIDEO_GENERATING:"Đang tạo video", VIDEO_SAFETY_VALIDATING:"Đang kiểm tra an toàn video", VIDEO_READY:"Video đã sẵn sàng", SAFETY_BLOCKED:"Video chưa đạt kiểm tra an toàn", COMPLETED:"Đã hoàn tất", FAILED:"Không hoàn tất được", ABANDONED:"Đã đóng", DELETE_PENDING:"Đang xóa lượt này", DELETED:"Đã xóa" };
export const ageLabel = (months: number) => `${months} tháng tuổi`;
export const stateLabel = (state: string) => stateLabels[state] ?? "Đang cập nhật";
export function errorCopy(error: unknown): string {
 if (!(error instanceof BackendApiError)) return copy.generic;
 if (error.status === 404) return NOT_FOUND_OR_NO_ACCESS;
 if (error.status === 401) return "Phiên đăng nhập chưa sẵn sàng.";
 if (error.status === 429) { const seconds = "retryAfterSeconds" in error && typeof error.retryAfterSeconds === "number" ? error.retryAfterSeconds : null; return seconds === null ? "Bạn thao tác quá nhanh. Vui lòng thử lại sau." : `Bạn thao tác quá nhanh. Vui lòng thử lại sau ${seconds} giây.`; }
 if (["PARENT_STORE_UNAVAILABLE", "PARENT_STORY_RUN_STORE_UNAVAILABLE", "DEPENDENCY_UNAVAILABLE"].includes(error.code)) return copy.dependencyUnavailable;
 if (error.status === 503 || error.status >= 500) return copy.dependencyUnavailable;
 if (error.code === "NETWORK_ERROR") return "Không kết nối được dịch vụ. Vui lòng thử lại.";
 const messages: Record<string,string> = { ACTION_NOT_ALLOWED:"Bạn không phải giáo viên phụ trách nên chưa thực hiện được thao tác này.", TEACHER_ACTIVE_RUN_CONFLICT:"Giáo viên này đang có một lượt kể chuyện đang hoạt động.", ACTIVE_RUN_EXISTS:copy.active, SAMPLE_VIDEO_ALREADY_EXISTS:copy.used, LESSON_PLAN_NOT_APPROVED:copy.noPlan, INVALID_STATE_TRANSITION:"Lượt kể chuyện chưa ở trạng thái có thể xác nhận lại.", STALE_REVISION:"Thông tin lượt kể chuyện đã thay đổi. Hãy làm mới trước khi tiếp tục.", INVALID_REQUEST:"Yêu cầu không hợp lệ. Vui lòng kiểm tra lại.", INVALID_IDEMPOTENCY_KEY:"Yêu cầu bị trùng với một yêu cầu khác. Hãy tải lại rồi thử lại.", MULTI_CHILD_NOT_SUPPORTED:"Mỗi lượt kể chuyện chỉ dành cho một trẻ.", TRANSCRIPT_NOT_CONFIRMED:"Vui lòng xác nhận nội dung bản ghi âm trước.", SUBJECT_NOT_CONFIRMED:"Vui lòng xác nhận chủ thể của bức tranh trước.", PROFILE_CONTEXT_NOT_CONFIRMED:"Vui lòng xác nhận thông tin lượt kể chuyện.", STORY_REWRITE_LIMIT_REACHED:"Đã hết số lần viết lại câu chuyện.", VIDEO_QUOTA_EXCEEDED:"Đã hết lượt tạo video của kỳ này.", VIDEO_REGENERATION_LIMIT_REACHED:"Đã hết số lần tạo video của lượt này. Hãy hủy lượt để bắt đầu lượt mới.", VIDEO_TECHNICAL_FAILURE:"Video chưa thể tạo từ kế hoạch hiện tại. Hãy hủy lượt này rồi tạo lượt mới.", SUBSCRIPTION_RESTRICTED:"Gói dịch vụ hiện tại chưa cho phép tạo video.", AUDIO_TOO_LARGE:"Bản ghi âm vượt quá 2 phút hoặc 20 MB. Vui lòng ghi âm ngắn hơn.", IMAGE_DIMENSIONS_EXCEEDED:"Ảnh quá lớn để xử lý. Vui lòng chọn ảnh nhỏ hơn.", MEDIA_TOO_LARGE:"Tệp quá lớn. Vui lòng chọn tệp nhỏ hơn.", UNSUPPORTED_MEDIA_TYPE:"Định dạng nội dung không được hỗ trợ.", UPLOAD_INCOMPLETE:"Tệp tải lên chưa hoàn tất. Vui lòng thử lại.", UPLOAD_CHECKSUM_MISMATCH:"Dữ liệu tải lên không khớp mã kiểm tra. Hãy thử tải lại.", UPLOAD_CONTENT_MISMATCH:"Nội dung tệp không khớp định dạng đã chọn. Hãy chọn tệp khác.", INVALID_TOKEN:"Mã xem video không hợp lệ.", TOKEN_EXPIRED:"Mã xem video đã hết hạn. Đang xin mã mới.", RANGE_NOT_SATISFIABLE:"Phạm vi video được yêu cầu không hợp lệ." };
 const quotaMessages: Record<string,string> = {
  QUOTA_ALLOCATION_NOT_FOUND: "Nhà trường chưa phân bổ lượt tạo video cho tài khoản giáo viên này.",
  TEACHER_QUOTA_INSUFFICIENT: "Giáo viên đã dùng hết số lượt video được phân bổ.",
  SCHOOL_QUOTA_INSUFFICIENT: "Nhà trường đã hết lượt tạo video trong kỳ này.",
 };
 return quotaMessages[error.code] ?? messages[error.code] ?? copy.generic;
}

export function deleteErrorCopy(error: unknown): string {
 if (error instanceof BackendApiError && error.status === 409) return copy.deleteConflict;
 return errorCopy(error);
}

// Input labels are web-owned wording for owner review (FR-T-11, SRS l.551).
export const inputCopy = { drawing:"Ảnh bức tranh", upload:"Tải ảnh", stop:"Dừng tải lên", idea:"Ý tưởng", audio:"Tệp ghi âm", submitIdea:"Gửi ý tưởng", transcript:"Nội dung ghi âm", correction:"Chỉnh nội dung ghi âm", saveCorrection:"Lưu chỉnh sửa", confirmTranscript:"Xác nhận nội dung ghi âm", pending:"Đang chuẩn bị nội dung ghi âm.", refresh:"Làm mới", context:"Thông tin buổi học", age:"Tuổi", objectives:"Mục tiêu", direction:"Hướng dẫn", activity:"Hoạt động", confirmContext:"Xác nhận thông tin", subject:"Chủ thể bức tranh", features:"Đặc điểm nhìn thấy", others:"Vật khác đưa vào truyện", confirmSubject:"Xác nhận chủ thể", invalidIdea:"Hãy nhập từ 1 đến 500 ký tự hoặc chọn tệp ghi âm.", invalidCorrection:"Hãy nhập từ 1 đến 500 ký tự.", invalidSubject:"Hãy nhập chủ thể từ 1 đến 160 ký tự.", retry:"Thử lại" } as const;

// Web wording for the story and video flow; owner review required.
export const storyVideoCopy = {
  rewrite: "Viết lại", hint: "Gợi ý viết lại", invalidHint: "Gợi ý phải có tối đa 400 ký tự trên một dòng.", confirm: "Xác nhận kịch bản", confirmAgain: "Xác nhận lại kịch bản", planFence: "Kế hoạch đã thay đổi. Hãy hủy lượt này trước, rồi tạo lượt mới theo kế hoạch đã duyệt.",
  generate: "Tạo video", reason: "Lý do", unsuitable: "Không phù hợp", complete: "Hoàn tất", watch: "Xem thử",
  remaining: (n: number) => `còn ${n} lần tạo lại`, pending: "Đang gửi yêu cầu",
  blocked: "Video chưa đạt kiểm tra an toàn nên chưa thể dùng. Bạn có thể quay lại bước kịch bản.",
  playbackError: "Không xem được video lúc này. Hãy thử lại.",
  completeRule: "Bạn có thể xác nhận video cho lớp trước hoặc sau khi hoàn tất lượt này.", failedNewRun: "Video chưa thể tạo do kế hoạch đã thay đổi. Hãy tạo lượt mới.",
  failureMessage: (code: string | null | undefined) => {
    switch (code) {
      case "VIDEO_DEADLINE_EXCEEDED": return "Lượt tạo video đã hết thời gian chờ. Hãy tạo lượt video mẫu mới để thử lại.";
      case "PROVIDER_UNAVAILABLE": return "Dịch vụ tạo video tạm thời chưa sẵn sàng. Hãy chờ một lúc rồi tạo lượt video mẫu mới.";
      case "VIDEO_TECHNICAL_FAILURE": return "Video chưa thể tạo do kế hoạch đã thay đổi. Hãy tạo lượt mới.";
      default: return null;
    }
  },
  reasons: { QUALITY_LOW: "Chất lượng chưa tốt", NOT_MATCHING_STORY: "Chưa đúng với câu chuyện", CONTENT_CONCERN: "Có nội dung đáng lo ngại", OTHER: "Lý do khác" },
} as const;

// SRS l.555 and l.2697 describe the behavior; wording requires owner review.
export const projectionCopy = { title: "Chiếu cho lớp", confirm: "Xác nhận video hiện tại", confirmationRequired: "Hãy xác nhận lại video phiên bản hiện tại trước khi phát cho lớp.", confirmedCurrent: "Đã xác nhận video hiện tại lúc", acknowledgement: "Tôi xác nhận chiếu video này cho cả lớp", play: "Phát cho lớp", planNote: "Video được tạo từ bản kế hoạch cũ hơn bản đã duyệt hiện tại.", deadEnd: "Mẫu này đã được xác nhận trước khi hoàn tất lượt và không thể khôi phục cho lớp.", waiting: "Video đang chờ xử lý hoặc đang được tạo. Hãy làm mới trạng thái để kiểm tra.", refresh: "Làm mới trạng thái", refreshing: "Đang làm mới trạng thái…", unavailable: "Video chưa sẵn sàng để chiếu cho lớp.", playbackError: "Không xem được video lúc này. Hãy thử lại." } as const;
export function projectionError(error: unknown): string {
  if (error instanceof BackendApiError && error.status === 401 && error.code !== "AUTHENTICATION_REQUIRED") return projectionCopy.playbackError;
  if (error instanceof BackendApiError && error.status === 416) return "Phạm vi video được yêu cầu không hợp lệ.";
  if (error instanceof BackendApiError && error.status === 403) return "Bạn không phải giáo viên phụ trách nên chưa thực hiện được thao tác này.";
  return errorCopy(error);
}
