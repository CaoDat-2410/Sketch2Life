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
  it("reads the CONV-1 envelope: code and Vietnamese message are kept", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({
      code: "RATE_LIMITED",
      message: "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
      correlation_id: "corr-5",
      retryable: true,
      retry_after_seconds: 30,
    }, 429)));

    await expect(aiWorkflowService.suggestLessonPlan(input)).rejects.toThrow(
      "Yêu cầu AI thất bại (RATE_LIMITED). Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
    );
  });

  it("reads a detail-wrapped body and shows a Vietnamese message instead of the English one", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({
      detail: { code: "ACTION_NOT_ALLOWED", message: "Not allowed for this role" },
    }, 403)));

    await expect(aiWorkflowService.suggestLessonPlan(input)).rejects.toThrow(
      "Yêu cầu AI thất bại (ACTION_NOT_ALLOWED). Tài khoản không được phép thực hiện thao tác này.",
    );
  });
});
