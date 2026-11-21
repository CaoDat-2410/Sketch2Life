import { BackendApiError, backendRequest } from "./backendApi";
import type { AccessGrant } from "./backendApi";

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

const visibleAscii = /^[\x21-\x7E]{1,128}$/;

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
