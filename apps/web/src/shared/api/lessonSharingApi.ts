import { BackendApiError, apiBaseUrl, backendRequest, createIdempotencyKey } from "./backendApi";
import type { AccessGrant } from "./backendApi";
import { parseApiError } from "./errorEnvelope";

export type PrivateShareAudience = "ORGANIZATION" | "PRINCIPAL" | "PARENT_GROUP";
export type PrivateShareCapability = "VIEW" | "DOWNLOAD" | "REUSE";

export interface PrivateShareInput {
  /** Path context; omitted from the request body. */
  lessonId: string;
  versionId: string;
  audienceKind: PrivateShareAudience;
  audienceRef: string;
  capability: PrivateShareCapability;
  expiresAt: string | null;
}

export const PRIVATE_SHARE_NOT_FOUND_MESSAGE = "Không tìm thấy giáo án hoặc bạn không có quyền chia sẻ giáo án này.";
export const PRIVATE_SHARE_GROUP_STATE_MESSAGE = "Nhóm phụ huynh hiện không thể nhận lượt chia sẻ này.";
export const PRIVATE_SHARE_VALIDATION_MESSAGE = "Yêu cầu chia sẻ chưa đáp ứng điều kiện.";
export const PRIVATE_SHARE_REVOKE_REQUEST_MESSAGE = "Không thể thu hồi lượt chia sẻ này. Hãy kiểm tra lại và thử lại.";
export const PRIVATE_SHARE_REVOKE_STALE_MESSAGE = "Lượt chia sẻ đã thay đổi. Hãy xác nhận thu hồi lại với phiên bản mới.";
export const PRIVATE_SHARE_REVOKE_ERROR_MESSAGE = "Chưa thể thu hồi lượt chia sẻ lúc này. Vui lòng thử lại.";

const visibleAscii = /^[\x21-\x7E]{1,128}$/;

export class StaleAccessGrantRevisionError extends BackendApiError {
  readonly currentVersion?: number;

  constructor(requestId?: string, currentVersion?: number) {
    super(PRIVATE_SHARE_REVOKE_STALE_MESSAGE, "STALE_REVISION", 409, requestId);
    this.currentVersion = currentVersion;
  }
}

export async function createPrivateShare(
  organizationId: string,
  input: PrivateShareInput,
  idempotencyKey: string,
): Promise<AccessGrant> {
  if (!visibleAscii.test(idempotencyKey)) {
    throw new BackendApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
  }
  if (!(input.audienceKind === "ORGANIZATION" || input.audienceKind === "PRINCIPAL" || input.audienceKind === "PARENT_GROUP")) {
    throw new BackendApiError("Đối tượng chia sẻ riêng tư không hợp lệ.", "INVALID_REQUEST", 400);
  }
  if (!input.audienceRef) {
    throw new BackendApiError("Đối tượng nhận chia sẻ không hợp lệ.", "INVALID_REQUEST", 400);
  }

  try {
    return await backendRequest<AccessGrant>(
      `/api/lesson-library/v1/organizations/${encodeURIComponent(organizationId)}/lessons/${encodeURIComponent(input.lessonId)}/access-grants`,
      {
        method: "POST",
        headers: { "Idempotency-Key": idempotencyKey },
        body: JSON.stringify({
          contract: "CreateLessonAccessGrantRequestV1",
          version_id: input.versionId,
          audience_kind: input.audienceKind,
          audience_ref: input.audienceRef,
          capability: input.capability,
          expires_at: input.expiresAt,
        }),
      },
    );
  } catch (cause) {
    if (!(cause instanceof BackendApiError)) throw cause;
    if (cause.status === 404 || cause.code === "RESOURCE_NOT_FOUND") {
      throw new BackendApiError(PRIVATE_SHARE_NOT_FOUND_MESSAGE, cause.code, cause.status, cause.requestId);
    }
    if (cause.status === 409 && input.audienceKind === "PARENT_GROUP" && (cause.code === "INVALID_TRANSITION" || cause.code === "INVALID_STATE_TRANSITION")) {
      throw new BackendApiError(PRIVATE_SHARE_GROUP_STATE_MESSAGE, cause.code, cause.status, cause.requestId);
    }
    if (cause.status === 422) {
      throw new BackendApiError(PRIVATE_SHARE_VALIDATION_MESSAGE, cause.code, cause.status, cause.requestId);
    }
    throw cause;
  }
}

export async function revokeAccessGrant(
  organizationId: string,
  lessonId: string,
  grantId: string,
  revision: number,
  idempotencyKey: string,
): Promise<AccessGrant> {
  if (!Number.isInteger(revision) || revision < 1) {
    throw new BackendApiError(PRIVATE_SHARE_REVOKE_REQUEST_MESSAGE, "INVALID_IF_MATCH", 400);
  }
  if (!visibleAscii.test(idempotencyKey)) {
    throw new BackendApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
  }

  const token = await window.sketch2lifeAuth?.getIdToken().catch(() => null);
  if (!token) {
    throw new BackendApiError("Chưa có phiên đăng nhập để tiếp tục.", "AUTHENTICATION_REQUIRED", 401);
  }

  const requestId = createIdempotencyKey();
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/lesson-library/v1/organizations/${encodeURIComponent(organizationId)}/lessons/${encodeURIComponent(lessonId)}/access-grants/${encodeURIComponent(grantId)}`,
      {
        method: "DELETE",
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${token}`,
          "If-Match": `"${revision}"`,
          "Idempotency-Key": idempotencyKey,
          "X-Request-ID": requestId,
        },
        signal: controller.signal,
      },
    );
    const text = await response.text();
    let body: unknown = null;
    if (text) {
      try {
        body = JSON.parse(text) as unknown;
      } catch {
        throw new BackendApiError("Máy chủ trả về dữ liệu không đúng định dạng.", "INVALID_RESPONSE", response.status, response.headers.get("X-Request-ID") ?? requestId);
      }
    }
    if (response.ok) return body as AccessGrant;

    const parsed = parseApiError(body, response.status, response.headers.get("X-Request-ID"));
    if (response.status === 404 || parsed.code === "RESOURCE_NOT_FOUND") {
      throw new BackendApiError(PRIVATE_SHARE_NOT_FOUND_MESSAGE, parsed.code, response.status, parsed.requestId);
    }
    if (response.status === 400) {
      throw new BackendApiError(PRIVATE_SHARE_REVOKE_REQUEST_MESSAGE, parsed.code, response.status, parsed.requestId, parsed.fieldErrors);
    }
    if (response.status === 409 && parsed.code === "STALE_REVISION") {
      throw new StaleAccessGrantRevisionError(parsed.requestId, parsed.currentVersion);
    }
    throw new BackendApiError(PRIVATE_SHARE_REVOKE_ERROR_MESSAGE, parsed.code, response.status, parsed.requestId, parsed.fieldErrors);
  } catch (cause) {
    if (cause instanceof BackendApiError) throw cause;
    if (cause instanceof Error && cause.name === "AbortError") {
      throw new BackendApiError("Yêu cầu quá thời gian chờ. Hãy thử lại.", "REQUEST_TIMEOUT", 408, requestId);
    }
    throw new BackendApiError(PRIVATE_SHARE_REVOKE_ERROR_MESSAGE, "NETWORK_ERROR", 0, requestId);
  } finally {
    window.clearTimeout(timeout);
  }
}
