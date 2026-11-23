// Reads an API error body into one shape (SRS 9.8). Two body shapes exist while the backend moves:
// the CONV-1 envelope (top-level code, message, correlation_id, retryable, field_errors) and the
// older FastAPI body {"detail": {"code", "message"}} whose message may be English. The server
// message is shown only for the CONV-1 envelope, where it is Vietnamese by contract; every other
// body gets a Vietnamese message chosen by code, then by HTTP status.

export interface FieldError {
  field: string;
  code: string;
}

export interface ParsedApiError {
  code: string;
  message: string;
  requestId?: string;
  retryable: boolean;
  retryAfterSeconds?: number;
  fieldErrors: FieldError[];
  conv1: boolean;
}

const CODE_PATTERN = /^[A-Z][A-Z0-9_]{0,63}$/;
const RETRYABLE_STATUSES = [429, 502, 503, 504];
const MAX_SERVER_MESSAGE_LENGTH = 500;

const CODE_MESSAGES: Record<string, string> = {
  AUTH_REQUIRED: "Vui lòng đăng nhập để tiếp tục.",
  INVALID_TOKEN: "Phiên đăng nhập không hợp lệ. Vui lòng đăng nhập lại.",
  TOKEN_EXPIRED: "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
  ACTION_NOT_ALLOWED: "Tài khoản không được phép thực hiện thao tác này.",
  RESOURCE_NOT_FOUND: "Không tìm thấy tài nguyên được yêu cầu.",
  INVALID_STATE_TRANSITION: "Tài nguyên chưa ở trạng thái phù hợp cho thao tác này.",
  INVALID_REQUEST: "Yêu cầu không hợp lệ.",
  INVALID_IDEMPOTENCY_KEY: "Khóa yêu cầu trùng với một yêu cầu có nội dung khác.",
  STALE_REVISION: "Thông tin đã thay đổi. Vui lòng tải lại và thử lại.",
  PROVIDER_UNAVAILABLE: "Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.",
  RATE_LIMITED: "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
  MEDIA_TOO_LARGE: "Dữ liệu gửi lên vượt quá giới hạn cho phép.",
  UNSUPPORTED_MEDIA_TYPE: "Định dạng nội dung không được hỗ trợ.",
  // FEAT-066 C4: SRS 9.8 upload codes, same wording as the backend message table.
  LESSON_FILE_TOO_LARGE: "Tệp giáo án vượt quá 25 MB. Chỉ nhận PDF, DOCX hoặc PPTX; hãy chọn tệp khác.",
  UPLOAD_PART_CONFLICT: "Phần tệp này đã được gửi với nội dung khác.",
  UPLOAD_SESSION_STATE_CONFLICT: "Phiên tải lên không còn ở trạng thái cho phép thao tác này.",
  UPLOAD_SESSION_EXPIRED: "Phiên tải lên đã hết hạn. Vui lòng tải tệp lại từ đầu.",
  UPLOAD_INCOMPLETE: "Tệp chưa được tải lên đủ các phần.",
};

const STATUS_MESSAGES: Record<number, string> = {
  400: CODE_MESSAGES.INVALID_REQUEST,
  401: "Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.",
  403: "Tài khoản chưa được cấp quyền cho dữ liệu này.",
  404: CODE_MESSAGES.RESOURCE_NOT_FOUND,
  409: "Yêu cầu xung đột với trạng thái hiện tại.",
  410: "Tài nguyên không còn khả dụng.",
  413: CODE_MESSAGES.MEDIA_TOO_LARGE,
  415: CODE_MESSAGES.UNSUPPORTED_MEDIA_TYPE,
  422: "Yêu cầu chưa đáp ứng điều kiện nghiệp vụ.",
  429: CODE_MESSAGES.RATE_LIMITED,
  502: "Không thể hoàn tất yêu cầu lúc này.",
  503: CODE_MESSAGES.PROVIDER_UNAVAILABLE,
  504: CODE_MESSAGES.PROVIDER_UNAVAILABLE,
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

export function fallbackMessage(code: string, status: number): string {
  return (
    CODE_MESSAGES[code] ??
    STATUS_MESSAGES[status] ??
    (status >= 500 ? "Máy chủ chưa thể hoàn tất yêu cầu." : "Không thể hoàn tất yêu cầu.")
  );
}

function fieldErrorsOf(value: unknown): FieldError[] {
  if (!Array.isArray(value)) return [];
  const kept: FieldError[] = [];
  for (const item of value) {
    const record = asRecord(item);
    if (record && typeof record.field === "string" && typeof record.code === "string") {
      kept.push({ field: record.field, code: record.code });
    }
  }
  return kept;
}

export function parseApiError(
  body: unknown,
  status: number,
  headerRequestId: string | null = null,
): ParsedApiError {
  const record = asRecord(body) ?? {};
  const conv1 =
    typeof record.code === "string" &&
    typeof record.message === "string" &&
    record.message.trim().length > 0 &&
    record.message.length <= MAX_SERVER_MESSAGE_LENGTH &&
    typeof record.correlation_id === "string";
  const source = conv1 ? record : asRecord(record.detail) ?? record;
  const code =
    typeof source.code === "string" && CODE_PATTERN.test(source.code) ? source.code : `HTTP_${status}`;
  const requestId =
    typeof source.request_id === "string"
      ? source.request_id
      : typeof source.correlation_id === "string"
        ? source.correlation_id
        : headerRequestId ?? undefined;
  const retryAfter = source.retry_after_seconds;
  return {
    code,
    message: conv1 ? (record.message as string) : fallbackMessage(code, status),
    requestId,
    retryable: conv1 ? record.retryable === true : RETRYABLE_STATUSES.includes(status),
    retryAfterSeconds: typeof retryAfter === "number" && Number.isFinite(retryAfter) && retryAfter >= 0 ? retryAfter : undefined,
    fieldErrors: fieldErrorsOf(source.field_errors),
    conv1,
  };
}
