import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { aiWorkflowService } from "../aiWorkflowService";

const jsonResponse = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-test" };
  window.sketch2lifeAuth = {
    signIn: vi.fn(async () => undefined),
    getIdToken: vi.fn(async () => "unit-test-id-token"),
    signOut: vi.fn(async () => undefined),
  };
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete window.sketch2lifeConfig;
  delete window.sketch2lifeAuth;
});

const input = { topic: "Con vật" } as never;

describe("Teacher AI workflow errors", () => {
  it("turns a rate limit response into plain Vietnamese guidance", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({
      code: "RATE_LIMITED",
      message: "Modal Qwen error code RATE_LIMITED request_id hidden",
      correlation_id: "corr-5",
      retryable: true,
      retry_after_seconds: 30,
    }, 429)));

    await expect(aiWorkflowService.suggestLessonPlan(input)).rejects.toThrow(
      "Bạn đã gửi nhiều yêu cầu liên tiếp. Hãy thử lại sau ít phút.",
    );
  });

  it("turns a detail-wrapped permission response into plain guidance", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({
      detail: { code: "ACTION_NOT_ALLOWED", message: "Not allowed for this role" },
    }, 403)));

    await expect(aiWorkflowService.suggestLessonPlan(input)).rejects.toThrow(
      "Bạn chưa thể thực hiện thao tác này. Hãy liên hệ người quản lý.",
    );
  });

  // T0.9 (SRS l.864-865, l.1720-1721): the old 403 TEACHER_ORGANIZATION_ACCESS_REQUIRED is gone; a caller
  // outside scope gets the uniform 404, an in-organization non-Teacher role the safe 403.
  it.each([
    ["suggestLessonPlan", 404, "RESOURCE_NOT_FOUND", "Không tìm thấy tài nguyên được yêu cầu."],
  ] as const)("T0.9: %s projects %i %s without a policy detail", async (method, status, code, message) => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({ code, message, correlation_id: "corr-9", retryable: false }, status)));
    const error = await aiWorkflowService[method](input).then(() => { throw new Error("expected a rejection"); }, (cause: unknown) => cause as Error);
    expect(error.message).toBe(status === 404
      ? "Không tìm thấy thông tin cần dùng. Hãy tải lại trang."
      : "Bạn chưa thể thực hiện thao tác này. Hãy liên hệ người quản lý.");
    expect(error.message).not.toContain("TEACHER_ORGANIZATION_ACCESS_REQUIRED");
  });

});
