import { createIdempotencyKey } from "../../../../shared/api/backendApi";
import { AdminBe1Error, adminBe1Request, adminOrganizationId } from "./be1Client";

export interface TeacherInvitationResponse {
  account_ref: string;
  status: "PENDING_VERIFICATION";
}

export interface TeacherInvitationOutcomeMessage {
  message: string;
  keepIdempotencyKey: boolean;
}

const TEACHER_EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const IDEMPOTENCY_KEY_PATTERN = /^[\x21-\x7E]{1,128}$/;

export function isValidTeacherEmail(email: string): boolean {
  return email.length >= 3 && email.length <= 254 && TEACHER_EMAIL_PATTERN.test(email);
}

function organizationPath(): string {
  return `/organizations/${encodeURIComponent(adminOrganizationId())}`;
}

function validateIdempotencyKey(key: string): void {
  if (!IDEMPOTENCY_KEY_PATTERN.test(key)) {
    throw new AdminBe1Error("Invalid idempotency key.", 400, "INVALID_IDEMPOTENCY_KEY");
  }
}

export const teacherInvitationService = {
  invite(
    email: string,
    idempotencyKey: string = createIdempotencyKey(),
  ): Promise<TeacherInvitationResponse> {
    if (!isValidTeacherEmail(email)) {
      throw new AdminBe1Error("Invalid teacher invitation request.", 400, "INVALID_REQUEST");
    }
    validateIdempotencyKey(idempotencyKey);

    return adminBe1Request<TeacherInvitationResponse>(
      `${organizationPath()}/teacher-invitations`,
      {
        method: "POST",
        headers: {
          "Cache-Control": "private, no-store",
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({ email }),
        cache: "no-store",
      },
    );
  },

  resend(
    accountRef: string,
    idempotencyKey: string = createIdempotencyKey(),
  ): Promise<TeacherInvitationResponse> {
    if (accountRef.length < 1 || accountRef.length > 36) {
      throw new AdminBe1Error("Invalid teacher invitation reference.", 400, "INVALID_REQUEST");
    }
    validateIdempotencyKey(idempotencyKey);

    return adminBe1Request<TeacherInvitationResponse>(
      `${organizationPath()}/teacher-invitations/${encodeURIComponent(accountRef)}/resend`,
      {
        method: "POST",
        headers: {
          "Cache-Control": "private, no-store",
          "Idempotency-Key": idempotencyKey,
        },
        cache: "no-store",
      },
    );
  },
};

/** Maps API and network outcomes to safe manager copy without exposing server text. */
export function teacherInvitationOutcomeMessage(cause: unknown): TeacherInvitationOutcomeMessage {
  if (cause instanceof AdminBe1Error) {
    if (cause.status === 409 && cause.code === "ACCOUNT_SETUP_UNAVAILABLE") {
      return {
        message: "Không thể gửi lời mời đến email này.",
        keepIdempotencyKey: false,
      };
    }

    if (cause.status === 400 && cause.code === "INVALID_IDEMPOTENCY_KEY") {
      return {
        message: "Khóa yêu cầu đã được dùng cho thao tác khác. Hãy gửi lại để tạo khóa mới.",
        keepIdempotencyKey: false,
      };
    }

    if (cause.status === 400) {
      return {
        message: "Yêu cầu chưa hợp lệ. Hãy kiểm tra lại thông tin.",
        keepIdempotencyKey: false,
      };
    }

    if (cause.status === 404) {
      return {
        message: "Không thể thực hiện thao tác này với thông tin hiện tại.",
        keepIdempotencyKey: false,
      };
    }

    if (cause.status >= 500) {
      return {
        message: "Dịch vụ đang tạm gián đoạn. Hãy thử lại cùng thao tác.",
        keepIdempotencyKey: true,
      };
    }

    if (cause.status >= 400 && cause.status < 500) {
      return {
        message: "Không thể hoàn tất thao tác này.",
        keepIdempotencyKey: false,
      };
    }
  }

  return {
    message: "Chưa kết nối được. Hãy thử lại cùng thao tác.",
    keepIdempotencyKey: true,
  };
}
