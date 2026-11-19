import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/authService", () => ({
  authService: { getIdToken: vi.fn(async () => "unit-test-id-token") },
}));

import { AdminBe1Error, adminApiRequest, adminBe1Request } from "../services/be1Client";

const jsonResponse = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

beforeEach(() => {
  vi.stubEnv("VITE_BE1_BASE_URL", "https://api.example.test");
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const callers = [
  ["adminApiRequest", () => adminApiRequest("/lesson-library/v1/x")],
  ["adminBe1Request", () => adminBe1Request("/x")],
] as const;

describe.each(callers)("%s error handling", (_name, call) => {
  it("reads the CONV-1 envelope: Vietnamese message, code and correlation id", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({
      code: "STALE_REVISION",
      message: "Thông tin đã thay đổi. Vui lòng tải lại và thử lại.",
      correlation_id: "corr-9",
      retryable: false,
      request_id: "corr-9",
    }, 409)));

    const error = await call().catch((cause: unknown) => cause);

    expect(error).toBeInstanceOf(AdminBe1Error);
    expect(error).toMatchObject({
      status: 409,
      code: "STALE_REVISION",
      message: "Thông tin đã thay đổi. Vui lòng tải lại và thử lại.",
      requestId: "corr-9",
      retryable: false,
    });
  });

  it("maps a detail-wrapped English body to a Vietnamese message without losing the code", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse({
      detail: { code: "INVALID_IDEMPOTENCY_KEY", message: "Idempotency-Key was already used for another request" },
    }, 400)));

    const error = await call().catch((cause: unknown) => cause);

    expect(error).toMatchObject({
      status: 400,
      code: "INVALID_IDEMPOTENCY_KEY",
      message: "Khóa yêu cầu trùng với một yêu cầu có nội dung khác.",
    });
  });

  it("does not show a generic English failure text for an empty error body", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response("", { status: 503 })));

    const error = (await call().catch((cause: unknown) => cause)) as AdminBe1Error;

    expect(error.message).toBe("Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.");
    expect(error.code).toBe("HTTP_503");
    expect(error.retryable).toBe(true);
  });
});
