import { BackendApiError, apiBaseUrl, createIdempotencyKey } from "./backendApi";
import { parseApiError } from "./errorEnvelope";

export interface FieldIssue { field: string; code: string }
/** A backend error that keeps the safe `field_errors` of a 400 (field path and code only, never a raw body). */
export class OccurrenceApiError extends BackendApiError {
  readonly fieldErrors: FieldIssue[];
  readonly retryable?: boolean;
  readonly retryAfterSeconds?: number;
  readonly currentVersion?: number;
  constructor(message: string, code: string, status: number, requestId: string | undefined, fieldErrors: FieldIssue[], retryable?: boolean, retryAfterSeconds?: number, currentVersion?: number) {
    super(message, code, status, requestId);
    this.name = "BackendApiError";
    this.fieldErrors = fieldErrors;
    this.retryable = retryable;
    this.retryAfterSeconds = retryAfterSeconds;
    this.currentVersion = currentVersion;
  }
}
export const SAFE_FIELD = /^[A-Za-z0-9_.[\]-]{1,80}$/;
export const SAFE_CODE = /^[A-Z][A-Z0-9_]{0,63}$/;
export const safeFieldErrors = (items: FieldIssue[]) => items.filter((item) => SAFE_FIELD.test(item.field) && SAFE_CODE.test(item.code)).slice(0, 20);

export interface ConditionalResult<T> { data: T | null; etag: string | null; notModified: boolean }
export const visibleAscii = /^[\x21-\x7E]{1,128}$/;

// Vietnamese copy for codes the shared table does not cover. Everything else uses the shared envelope message.
const CODE_MESSAGES: Record<string, string> = {
  SUPPORT_NEEDS_UNAVAILABLE: "Mục này chưa khả dụng.",
  TEACHER_ASSIGNMENT_REQUIRED: "Bạn cần được phân công vào lớp trước khi tạo buổi dạy.",
  INDEPENDENT_REVIEW_REQUIRED: "Người tạo nội dung không thể tự duyệt. Hãy nhờ một giáo viên khác.",
  SVG_GUIDE_SOURCE_MISMATCH: "Guide cần gắn với đúng phiên bản và mã nguồn của SVG.",
  SVG_SOURCE_INVALID: "SVG không hợp lệ hoặc chứa nội dung không được chấp nhận. Hãy kiểm tra lại tệp.",
  SVG_PROVENANCE_URL_INVALID: "Liên kết nguồn và giấy phép phải là URL HTTPS hợp lệ.",
  SVG_CATALOG_ITEM_NOT_FOUND: "Không tìm thấy nội dung hoặc bạn không có quyền truy cập. Hãy làm mới danh sách.",
  OCR_NOT_SUPPORTED: "Tài liệu đã tải lên chưa được hỗ trợ trích xuất.",
  ENCRYPTED_DOCUMENT_UNSUPPORTED: "Tài liệu được bảo vệ và không thể trích xuất.",
  UPLOAD_CHECKSUM_MISMATCH: "Dữ liệu tải lên không khớp mã kiểm tra. Hãy thử tải lại.",
  UPLOAD_CONTENT_MISMATCH: "Nội dung tệp không khớp định dạng đã chọn. Hãy chọn tệp khác.",
  MALWARE_DETECTED: "Tệp không được chấp nhận. Hãy chọn tệp khác.",
  STORAGE_UNAVAILABLE: "Dịch vụ lưu trữ tạm thời chưa sẵn sàng. Hãy thử lại sau.",
};
export const NOT_FOUND_OR_NO_ACCESS = "Không tìm thấy nội dung hoặc bạn không có quyền truy cập. Hãy làm mới danh sách.";

export function messageFor(status: number, code: string, parsedMessage: string): string {
  // A wrong-scope 404 and a missing id look the same on purpose (SRS 9.8): never reveal which one it was.
  if (status === 404 || code === "RESOURCE_NOT_FOUND") return NOT_FOUND_OR_NO_ACCESS;
  return CODE_MESSAGES[code] ?? parsedMessage;
}

export async function request<T>(path: string, init: RequestInit = {}, conditional = false): Promise<ConditionalResult<T>> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  const requestId = headers.get("X-Request-ID") ?? createIdempotencyKey();
  headers.set("X-Request-ID", requestId);
  const token = await window.sketch2lifeAuth?.getIdToken().catch(() => null);
  if (!token) throw new BackendApiError("Phiên đăng nhập chưa sẵn sàng.", "AUTHENTICATION_REQUIRED", 401, requestId);
  headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof Blob) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  let response: Response;
  try { response = await fetch(`${apiBaseUrl()}${path}`, { ...init, headers }); }
  catch (cause) {
    if (cause instanceof Error && cause.name === "AbortError") throw cause;
    throw new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0, requestId);
  }
  const etag = response.headers.get("ETag");
  if (conditional && response.status === 304) return { data: null, etag, notModified: true };
  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try { body = JSON.parse(text) as unknown; }
    catch { throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", response.status, response.headers.get("X-Request-ID") ?? requestId); }
  }
  if (!response.ok) {
    const parsed = parseApiError(body, response.status, response.headers.get("X-Request-ID") ?? requestId);
    throw new OccurrenceApiError(messageFor(response.status, parsed.code, parsed.message), parsed.code, response.status, parsed.requestId, safeFieldErrors(parsed.fieldErrors), parsed.retryable, parsed.retryAfterSeconds, parsed.currentVersion);
  }
  return { data: body as T, etag, notModified: false };
}

export const data = <T>(result: ConditionalResult<T>): T => result.data as T;
export const enc = encodeURIComponent;
export const ifNoneMatch = (etag?: string): HeadersInit => (etag ? { "If-None-Match": etag } : {});
export function keyed(key: string, extra: HeadersInit = {}): Record<string, string> {
  if (!visibleAscii.test(key)) throw new BackendApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
  return { ...Object.fromEntries(new Headers(extra)), "Idempotency-Key": key };
}

/** A keyed write: the key is validated inside the promise, so a bad key rejects instead of throwing synchronously. */
export async function write<T>(path: string, method: "POST" | "DELETE", key: string, body?: unknown, extra: HeadersInit = {}): Promise<T> {
  const result = await request<T>(path, { method, headers: keyed(key, extra), body: body === undefined ? undefined : JSON.stringify(body) });
  return data(result);
}


export async function authorizedHeaders(): Promise<Headers> {
  const token = await window.sketch2lifeAuth?.getIdToken().catch(() => null);
  if (!token) throw new BackendApiError("Phiên đăng nhập chưa sẵn sàng.", "AUTHENTICATION_REQUIRED", 401);
  return new Headers({ Authorization: `Bearer ${token}` });
}
