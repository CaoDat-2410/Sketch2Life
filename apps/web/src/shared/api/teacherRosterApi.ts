// Teacher BE1 roster client (goal v3 Phase B: T-7a roster reads, T-7c keyed profile create, T-7d
// enrollment move). The class is always a path segment; a command body never carries `class_id`.
// Every command sends one Idempotency-Key (1-128 visible ASCII) per user action and the strong
// `If-Match: "<class_revision>"` (SRS §21.4 l.1697-1699). Errors keep the server code, the safe
// Vietnamese message and, for 429, the wait from Retry-After (SRS §21.6 l.1735).
import { BackendApiError, apiBaseUrl, createIdempotencyKey } from "./backendApi";
import { CURSOR_PAGE_LIMIT, collectCursorPages, pageQuery, type CursorPage } from "./cursorPages";
import { parseApiError } from "./errorEnvelope";

export interface TeacherProfile { child_id: string; class_id: string; display_name: string; age_months: number }
export interface TeacherConsent { consent_id: string; child_id: string; purpose_ref: string; state: string; effective: boolean }
export interface CreatedProfile {
  contract: "Be1ManagedProfileV1"; child_id: string; class_id: string; enrollment_id: string;
  display_name: string; age_months: number; data_origin: string; class_revision: number;
}
export interface ProfileMove {
  contract: "Be1ProfileMoveV1"; child_id: string; from_class_id: string; to_class_id: string;
  enrollment_id: string; from_class_revision: number; to_class_revision: number;
}
export interface ProfileInput { display_name: string; age_months: number }

// Backend `CreateProfileRequest` (T-7c): every profile written today is synthetic.
export const SYNTHETIC_NAME_PREFIX = "Synthetic ";
export const PROFILE_NAME_MAX = 200;
export const PROFILE_AGE_MONTHS = { min: 36, max: 120 } as const;

export const NOT_FOUND_OR_NO_ACCESS = "Không tìm thấy nội dung hoặc bạn không có quyền truy cập. Hãy làm mới danh sách.";
export const STALE_RELOADED = "Đã tải lại dữ liệu mới nhất; hãy kiểm tra rồi xác nhận lại.";
export const CLASS_READ_ONLY = "Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ.";

const CODE_MESSAGES: Record<string, string> = {
  ACTION_NOT_ALLOWED: "Tài khoản không được phép thực hiện thao tác này.",
  INVALID_STATE_TRANSITION: `Lớp hoặc hồ sơ không còn ở trạng thái cho phép thao tác này. ${CLASS_READ_ONLY}`,
  SYNTHETIC_PROFILE_CREATION_UNAVAILABLE: "Môi trường này chưa cho phép tạo hồ sơ thử nghiệm (synthetic).",
};

const visibleAscii = /^[\x21-\x7E]{1,128}$/;

export class TeacherRosterApiError extends BackendApiError {
  readonly retryAfterSeconds?: number;
  constructor(message: string, code: string, status: number, requestId?: string, retryAfterSeconds?: number) {
    super(message, code, status, requestId);
    this.name = "BackendApiError";
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

function retryAfterFrom(header: string | null, bodySeconds: number | undefined): number | undefined {
  if (bodySeconds !== undefined) return Math.max(1, Math.ceil(bodySeconds));
  if (header && /^\d{1,6}$/.test(header.trim())) return Math.max(1, Number(header.trim()));
  return undefined;
}

/** Screen text for a failed roster call: one uniform text for any 404 (SRS l.865, l.1720). */
export function rosterMessage(status: number, code: string, serverMessage: string, retryAfterSeconds?: number): string {
  if (status === 404 || code === "RESOURCE_NOT_FOUND") return NOT_FOUND_OR_NO_ACCESS;
  if (code === "RATE_LIMITED" || status === 429) {
    return retryAfterSeconds
      ? `Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau ${retryAfterSeconds} giây.`
      : "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.";
  }
  if (status === 403) return CODE_MESSAGES.ACTION_NOT_ALLOWED;
  return CODE_MESSAGES[code] ?? serverMessage;
}

/** True when the outcome of a command is unknown (network, timeout, 5xx): retry with the same key. */
export function keepsCommandKey(cause: unknown): boolean {
  return cause instanceof BackendApiError && (cause.status === 0 || cause.status === 408 || cause.status >= 500);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  const requestId = headers.get("X-Request-ID") ?? createIdempotencyKey();
  headers.set("X-Request-ID", requestId);
  const token = await window.sketch2lifeAuth?.getIdToken().catch(() => null);
  if (!token) throw new TeacherRosterApiError("Phiên đăng nhập chưa sẵn sàng.", "AUTHENTICATION_REQUIRED", 401, requestId);
  headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl()}${path}`, { ...init, headers, signal: init.signal ?? AbortSignal.timeout(15_000) });
  } catch (cause) {
    if (cause instanceof Error && cause.name === "AbortError" && init.signal?.aborted) throw cause;
    throw new TeacherRosterApiError("Không kết nối được dịch vụ. Hãy thử lại cùng yêu cầu.", "NETWORK_ERROR", 0, requestId);
  }
  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try { body = JSON.parse(text) as unknown; }
    // A 2xx whose body cannot be read leaves the outcome unclear: report 502 so the action key is kept (F-01).
    catch { throw new TeacherRosterApiError("Dịch vụ trả về dữ liệu không hợp lệ. Hãy thử lại cùng yêu cầu.", "INVALID_RESPONSE", response.ok ? 502 : response.status, response.headers.get("X-Request-ID") ?? requestId); }
  }
  if (!response.ok) {
    const parsed = parseApiError(body, response.status, response.headers.get("X-Request-ID") ?? requestId);
    const retryAfter = response.status === 429 ? retryAfterFrom(response.headers.get("Retry-After"), parsed.retryAfterSeconds) : undefined;
    throw new TeacherRosterApiError(rosterMessage(response.status, parsed.code, parsed.message, retryAfter), parsed.code, response.status, parsed.requestId, retryAfter);
  }
  if (!body || typeof body !== "object") throw new TeacherRosterApiError("Dịch vụ trả về dữ liệu không hợp lệ. Hãy thử lại cùng yêu cầu.", "INVALID_RESPONSE", 502, requestId);
  return body as T;
}

function commandHeaders(key: string, revision: number): Record<string, string> {
  if (!visibleAscii.test(key)) throw new TeacherRosterApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
  if (!Number.isInteger(revision) || revision < 1) throw new TeacherRosterApiError("Chưa có phiên bản lớp hợp lệ; hãy tải lại.", "INVALID_REQUEST", 400);
  return { "Idempotency-Key": key, "If-Match": `"${revision}"` };
}

/** Client-side check of the backend profile rules before a create is sent; null when valid. */
export function profileInputProblem(input: ProfileInput): string | null {
  const name = input.display_name;
  if (!name.startsWith(SYNTHETIC_NAME_PREFIX) || name.trim().length <= SYNTHETIC_NAME_PREFIX.trim().length) {
    return `Tên hồ sơ thử nghiệm phải bắt đầu bằng “${SYNTHETIC_NAME_PREFIX}” và có thêm tên phía sau.`;
  }
  if (name.length > PROFILE_NAME_MAX) return `Tên hồ sơ tối đa ${PROFILE_NAME_MAX} ký tự.`;
  if (!Number.isInteger(input.age_months) || input.age_months < PROFILE_AGE_MONTHS.min || input.age_months > PROFILE_AGE_MONTHS.max) {
    return `Tuổi tính theo tháng phải từ ${PROFILE_AGE_MONTHS.min} đến ${PROFILE_AGE_MONTHS.max}.`;
  }
  return null;
}

const enc = encodeURIComponent;
const classPath = (organizationId: string, classId: string) =>
  `/api/be1/v1/organizations/${enc(organizationId)}/classes/${enc(classId)}`;

export const teacherRosterApi = {
  /** A09 for the class's own Teacher; a Manager-shaped count body is refused, never rendered. */
  profiles: async (organizationId: string, classId: string): Promise<TeacherProfile[]> => {
    const body = await request<{ contract?: string; items?: TeacherProfile[] }>(`${classPath(organizationId, classId)}/profiles`);
    if (body.contract !== "Be1ManagedProfileListV1" || !Array.isArray(body.items)) {
      throw new TeacherRosterApiError("Dịch vụ trả roster không đúng contract cho Teacher.", "INVALID_RESPONSE", 200);
    }
    return body.items;
  },
  /** A10, every page (T-7a cursor, newest first). */
  consents: async (organizationId: string, classId: string): Promise<TeacherConsent[]> => {
    const { items } = await collectCursorPages<TeacherConsent>((cursor) =>
      request<CursorPage<TeacherConsent>>(`${classPath(organizationId, classId)}/consents${pageQuery({ limit: CURSOR_PAGE_LIMIT, cursor })}`));
    return items;
  },
  /** T-7c: synthetic profile create; the class is the path and its revision the strong If-Match. */
  createProfile: async (organizationId: string, classId: string, classRevision: number, input: ProfileInput, key: string): Promise<CreatedProfile> => {
    const problem = profileInputProblem(input);
    if (problem) throw new TeacherRosterApiError(problem, "INVALID_REQUEST", 400);
    return request<CreatedProfile>(`${classPath(organizationId, classId)}/profiles`, {
      method: "POST",
      headers: commandHeaders(key, classRevision),
      body: JSON.stringify({ display_name: input.display_name, age_months: input.age_months }),
    });
  },
  /** T-7d: the source revision is the If-Match, the target revision travels in the body. */
  moveProfile: async (sourceClassId: string, sourceRevision: number, childId: string, target: { classId: string; revision: number }, key: string): Promise<ProfileMove> => {
    if (target.classId === sourceClassId) throw new TeacherRosterApiError("Hãy chọn một lớp khác để chuyển.", "INVALID_REQUEST", 400);
    return request<ProfileMove>(`/api/be1/v1/classes/${enc(sourceClassId)}/profiles/${enc(childId)}/move`, {
      method: "POST",
      headers: commandHeaders(key, sourceRevision),
      body: JSON.stringify({ target_class_id: target.classId, target_class_revision: target.revision }),
    });
  },
};
