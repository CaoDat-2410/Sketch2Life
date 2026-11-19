import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BackendApiError, backendApi, backendMessage } from "../backendApi";

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

describe("backendRequest error handling", () => {
  it("keeps the CONV-1 message and uses the correlation id as the request id", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({
      code: "ACTION_NOT_ALLOWED",
      message: "Tài khoản không được phép thực hiện thao tác này.",
      correlation_id: "corr-3",
      retryable: false,
      request_id: "corr-3",
    }, 403)));

    const error = await backendApi.accessGrants("org-test").catch((cause: unknown) => cause);

    expect(error).toBeInstanceOf(BackendApiError);
    expect(error).toMatchObject({ status: 403, code: "ACTION_NOT_ALLOWED", requestId: "corr-3" });
    expect(backendMessage(error)).toContain("Mã yêu cầu: corr-3");
  });

  it("replaces an English detail message with a Vietnamese one", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({
      detail: { code: "INVALID_IDEMPOTENCY_KEY", message: "Idempotency-Key was already used for another request" },
    }, 400)));

    const error = (await backendApi.accessGrants("org-test").catch((cause: unknown) => cause)) as BackendApiError;

    expect(error.code).toBe("INVALID_IDEMPOTENCY_KEY");
    expect(error.message).toBe("Khóa yêu cầu trùng với một yêu cầu có nội dung khác.");
  });
});
