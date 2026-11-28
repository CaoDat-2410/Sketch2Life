import { createIdempotencyKey } from "../../../../shared/api/backendApi";
import { AdminBe1Error, adminBe1Request, adminOrganizationId } from "./be1Client";

export interface ManagerActiveStoryRunConflictV1 {
  contract: "ManagerActiveStoryRunConflictV1";
  run_id: string;
  run_state: string;
  revision: number;
}

export interface ManagerForceClosedStoryRunV1 {
  contract: "ManagerForceClosedStoryRunV1";
  run_id: string;
  run_state: "ABANDONED";
  revision: number;
}

export type StoryRunForceCloseErrorKind = "not-found" | "forbidden" | "stale" | "invalid" | "network" | "other";
export type StoryRunForceCloseErrorContext = "lookup" | "command";

export interface StoryRunForceCloseErrorMessage {
  kind: StoryRunForceCloseErrorKind;
  message: string;
  keepIdempotencyKey: boolean;
}

function organizationPath(): string {
  return `/organizations/${encodeURIComponent(adminOrganizationId())}`;
}

export const storyRunForceCloseService = {
  getActiveConflict: (teacherRef: string): Promise<ManagerActiveStoryRunConflictV1> => {
    return adminBe1Request<ManagerActiveStoryRunConflictV1>(
      `${organizationPath()}/teachers/${encodeURIComponent(teacherRef)}/active-story-run-conflict`,
      { headers: { "Cache-Control": "private, no-store" }, cache: "no-store" },
    );
  },

  forceClose: (
    runId: string,
    expectedRevision: number,
    reason: string,
    idempotencyKey: string = createIdempotencyKey(),
  ): Promise<ManagerForceClosedStoryRunV1> => {
    const trimmedReason = reason.trim();
    if (!Number.isInteger(expectedRevision) || expectedRevision < 1 || trimmedReason.length < 1 || trimmedReason.length > 500) {
      throw new AdminBe1Error("Invalid force-close request.", 400, "INVALID_REQUEST");
    }
    if (!/^[\x21-\x7E]{1,128}$/.test(idempotencyKey)) {
      throw new AdminBe1Error("Invalid idempotency key.", 400, "INVALID_REQUEST");
    }

    return adminBe1Request<ManagerForceClosedStoryRunV1>(
      `${organizationPath()}/story-runs/${encodeURIComponent(runId)}/force-close`,
      {
        method: "POST",
        headers: {
          "Cache-Control": "private, no-store",
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify({ expected_revision: expectedRevision, reason: trimmedReason }),
        cache: "no-store",
      },
    );
  },
};

/** Maps only known status and network failures; server text is never shown to managers. */
export function storyRunForceCloseErrorMessage(
  cause: unknown,
  context: StoryRunForceCloseErrorContext = "command",
): StoryRunForceCloseErrorMessage {
  if (cause instanceof AdminBe1Error) {
    if (cause.status === 404) {
      return {
        kind: "not-found",
        message: context === "lookup"
          ? "Giáo viên này không có lượt đang chạy."
          : "Lượt này không còn hoạt động. Đã tải lại trạng thái.",
        keepIdempotencyKey: false,
      };
    }
    if (cause.status === 403) {
      return { kind: "forbidden", message: "Bạn không có quyền thực hiện thao tác này.", keepIdempotencyKey: false };
    }
    if (cause.status === 409 && cause.code === "STALE_REVISION") {
      return {
        kind: "stale",
        message: "Lượt đã thay đổi. Hãy kiểm tra thông tin mới rồi xác nhận lại.",
        keepIdempotencyKey: false,
      };
    }
    if (cause.status === 400) {
      return {
        kind: "invalid",
        message: "Yêu cầu chưa hợp lệ. Hãy kiểm tra lý do từ 1 đến 500 ký tự.",
        keepIdempotencyKey: false,
      };
    }
    if (cause.status >= 400 && cause.status < 500) {
      return { kind: "other", message: "Không thể hoàn tất thao tác này.", keepIdempotencyKey: false };
    }
    return {
      kind: "network",
      message: "Chưa nhận được kết quả. Hãy thử lại cùng yêu cầu.",
      keepIdempotencyKey: true,
    };
  }

  return {
    kind: "network",
    message: "Chưa kết nối được. Hãy thử lại cùng yêu cầu.",
    keepIdempotencyKey: true,
  };
}
