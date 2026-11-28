// Teacher BE1 roster client (goal v4 Phase B T-7e paging and goal v3 T-7a reads, T-7c keyed profile
// create, T-7d enrollment move). Commands use the path and headers defined by each route contract.
// Profile create/move send Idempotency-Key and If-Match; consent record/revoke do not use If-Match.
// Errors retain the server code, safe Vietnamese message and, for 429, Retry-After (SRS §21.6 l.1735).
import { BackendApiError, apiBaseUrl, createIdempotencyKey } from "./backendApi";
import { CURSOR_PAGE_LIMIT, collectCursorPages, pageQuery, type CursorPage } from "./cursorPages";
import { parseApiError } from "./errorEnvelope";

export interface TeacherProfile { child_id: string; class_id: string; display_name: string; age_months: number }
export interface TeacherProfileList { items: TeacherProfile[]; activeProfileCount: number }
export interface TeacherConsent { consent_id: string; child_id: string; purpose_ref: string; state: string; effective: boolean }
export interface TeacherConsentRecord extends TeacherConsent { contract: "Be1ConsentV1" }
export interface TeacherConsentRevocation { consent_id?: string; state: "revoked" }
export interface TeacherConsentInput { childId: string; purposeRef: string; evidenceRef?: string }
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
  SYNTHETIC_PROFILE_CREATION_UNAVAILABLE: "Môi trường này chưa cho phép tạo hồ sơ thử nghiệm.",
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

/** A later roster page failed after one or more safe rows were already loaded. */
export class TeacherRosterPageError extends TeacherRosterApiError {
  readonly partial: TeacherProfileList;
  readonly cause: unknown;

  constructor(cause: unknown, partial: TeacherProfileList) {
    const source = cause instanceof TeacherRosterApiError
      ? cause
      : new TeacherRosterApiError("Không thể tải đầy đủ danh sách hồ sơ. Hãy thử tải lại.", "ROSTER_PAGE_FAILED", 0);
    super(source.message, source.code, source.status, source.requestId, source.retryAfterSeconds);
    this.name = "TeacherRosterPageError";
    this.partial = partial;
    this.cause = cause;
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
    return `Tên phải bắt đầu bằng “${SYNTHETIC_NAME_PREFIX}” rồi có tên hiển thị phía sau.`;
  }
  if (name.length > PROFILE_NAME_MAX) return `Tên hồ sơ tối đa ${PROFILE_NAME_MAX} ký tự.`;
  if (!Number.isInteger(input.age_months) || input.age_months < PROFILE_AGE_MONTHS.min || input.age_months > PROFILE_AGE_MONTHS.max) {
    return `Tuổi tính theo tháng phải từ ${PROFILE_AGE_MONTHS.min} đến ${PROFILE_AGE_MONTHS.max}.`;
  }
  return null;
}

function consentInputProblem(input: TeacherConsentInput): string | null {
  if (!input.childId.trim() || input.childId.length > 128) return "Mã trẻ phải có từ 1 đến 128 ký tự.";
  if (!input.purposeRef.trim() || input.purposeRef.length > 128) return "Mục đích consent phải có từ 1 đến 128 ký tự.";
  if (input.evidenceRef !== undefined && input.evidenceRef.length > 512) return "Tham chiếu bằng chứng tối đa 512 ký tự.";
  return null;
}

const enc = encodeURIComponent;
const classPath = (organizationId: string, classId: string) =>
  `/api/be1/v1/organizations/${enc(organizationId)}/classes/${enc(classId)}`;

function consentFailure(cause: unknown): TeacherRosterApiError {
  if (!(cause instanceof TeacherRosterApiError)) {
    return new TeacherRosterApiError("Không thể cập nhật consent. Vui lòng thử lại.", "REQUEST_FAILED", 0);
  }

  let message = "Không thể cập nhật consent. Vui lòng thử lại.";
  if (cause.status === 404) message = NOT_FOUND_OR_NO_ACCESS;
  else if (cause.status === 403) message = CODE_MESSAGES.ACTION_NOT_ALLOWED;
  else if (cause.status === 409 && cause.code === "INVALID_STATE_TRANSITION") message = CLASS_READ_ONLY;
  else if (cause.status === 422 && cause.code === "CLASS_SCOPE_MISMATCH") message = "Lớp trong yêu cầu không khớp với lớp đã chọn.";
  else if (cause.status === 400 || cause.status === 422) message = "Thông tin consent không hợp lệ. Vui lòng kiểm tra lại.";
  else if (cause.status === 429) {
    message = cause.retryAfterSeconds
      ? "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau " + cause.retryAfterSeconds + " giây."
      : "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.";
  } else if (cause.status === 401) message = "Phiên đăng nhập chưa sẵn sàng.";
  else if (cause.status === 0) message = "Không kết nối được dịch vụ. Hãy thử lại.";
  else if (cause.status >= 500) message = "Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.";

  return new TeacherRosterApiError(message, cause.code, cause.status, cause.requestId, cause.retryAfterSeconds);
}

async function consentRequest<T>(path: string, init: RequestInit): Promise<T> {
  try {
    return await request<T>(path, init);
  } catch (cause) {
    throw consentFailure(cause);
  }
}

function isConsentRecord(value: unknown): value is Pick<TeacherConsentRecord, "consent_id" | "state"> {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return typeof record.consent_id === "string" && typeof record.state === "string";
}

function consentResponseError(): TeacherRosterApiError {
  return new TeacherRosterApiError("Dịch vụ trả về trạng thái consent không hợp lệ. Hãy tải lại danh sách.", "INVALID_RESPONSE", 502);
}

function isConsentRevocation(value: unknown, consentId: string): value is TeacherConsentRevocation {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return record.state === "revoked" && (record.consent_id === undefined || record.consent_id === consentId);
}

export const teacherRosterApi = {
  /** T-7e: every filtered Teacher roster page; Manager-shaped responses are refused. */
  profiles: async (organizationId: string, classId: string): Promise<TeacherProfileList> => {
    type ProfilePage = CursorPage<TeacherProfile> & {
      contract?: string;
      active_profile_count?: number;
    };
    const path = `${classPath(organizationId, classId)}/profiles`;
    const pages = await collectCursorPages<TeacherProfile, ProfilePage>(async (cursor) => {
      const body = await request<ProfilePage>(`${path}${pageQuery({ limit: CURSOR_PAGE_LIMIT, cursor })}`);
      if (
        body.contract !== "Be1ManagedProfileListV1"
        || !Array.isArray(body.items)
        || (body.next_cursor !== null && typeof body.next_cursor !== "string")
        || !Number.isInteger(body.active_profile_count)
        || (body.active_profile_count ?? -1) < 0
      ) {
        throw new TeacherRosterApiError("Dịch vụ trả danh sách không đúng định dạng cho Giáo viên.", "INVALID_RESPONSE", 200);
      }
      return body;
    }, undefined, { retainLoadedOnError: true });

    const seen = new Set<string>();
    const items = pages.items.filter((profile) => {
      if (seen.has(profile.child_id)) return false;
      seen.add(profile.child_id);
      return true;
    });
    const result = { items, activeProfileCount: pages.first.active_profile_count! };
    if (pages.failure) throw new TeacherRosterPageError(pages.failure.cause, result);
    return result;
  },
  /** A10, every page (T-7a cursor, newest first). */
  consents: async (organizationId: string, classId: string): Promise<TeacherConsent[]> => {
    const { items } = await collectCursorPages<TeacherConsent>((cursor) =>
      request<CursorPage<TeacherConsent>>(`${classPath(organizationId, classId)}/consents${pageQuery({ limit: CURSOR_PAGE_LIMIT, cursor })}`));
    return items;
  },
  recordConsent: async (organizationId: string, classId: string, input: TeacherConsentInput, key?: string): Promise<Pick<TeacherConsentRecord, "consent_id" | "state">> => {
    const problem = consentInputProblem(input);
    if (problem) throw new TeacherRosterApiError(problem, "INVALID_REQUEST", 400);
    if (key !== undefined && !visibleAscii.test(key)) {
      throw new TeacherRosterApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
    }
    const headers = key === undefined ? undefined : { "Idempotency-Key": key };
    const consent = await consentRequest<unknown>(classPath(organizationId, classId) + "/consents", {
      method: "POST",
      headers,
      body: JSON.stringify({
        class_id: classId,
        child_id: input.childId,
        purpose_ref: input.purposeRef,
        ...(input.evidenceRef === undefined ? {} : { evidence_ref: input.evidenceRef }),
      }),
    });
    if (!isConsentRecord(consent)) {
      throw consentResponseError();
    }
    return { consent_id: consent.consent_id, state: consent.state };
  },
  revokeConsent: async (organizationId: string, classId: string, consentId: string): Promise<TeacherConsentRevocation> => {
    if (!consentId.trim() || consentId.length > 128) {
      throw new TeacherRosterApiError("Không thể xác định consent cần thu hồi.", "INVALID_REQUEST", 400);
    }
    const consent = await consentRequest<TeacherConsentRevocation>(
      classPath(organizationId, classId) + "/consents/" + enc(consentId) + "/revoke",
      { method: "POST" },
    );
    if (!isConsentRevocation(consent, consentId)) throw consentResponseError();
    return consent;
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
