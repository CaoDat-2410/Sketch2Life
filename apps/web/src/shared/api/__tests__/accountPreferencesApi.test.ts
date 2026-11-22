import { afterEach, describe, expect, it, vi } from "vitest";
import { backendMessage } from "../backendApi";
import { getPreferences, updatePreferences } from "../accountPreferencesApi";

const preferences = { locale: "vi-VN" as const, email_notifications: true, revision: 7 };

function response(body: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "preferences-response" }),
    text: async () => JSON.stringify(body),
  } as Response;
}

function setup(replies: Response[]) {
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "synthetic-token") };
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test" };
  const fetcher = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

describe("accountPreferencesApi", () => {
  it("gets preferences from the shared account endpoint without admin-only reads", async () => {
    const fetcher = setup([response(preferences)]);

    await expect(getPreferences()).resolves.toEqual(preferences);

    const [url, init] = fetcher.mock.calls[0];
    expect(new URL(String(url)).pathname).toBe("/api/platform-admin/v1/preferences");
    expect(init?.method ?? "GET").toBe("GET");
    expect(new Headers(init?.headers).get("Authorization")).toBe("Bearer synthetic-token");
    expect(new Headers(init?.headers).get("Accept")).toBe("application/json");
    expect(fetcher.mock.calls.map(([requestUrl]) => String(requestUrl))).not.toEqual(
      expect.arrayContaining([expect.stringMatching(/\/(session|settings)(\?|$)/)]),
    );
  });

  it("sends the locale, notification choice, revision and a fresh idempotency key on each update attempt", async () => {
    const fetcher = setup([
      response({ ...preferences, email_notifications: false, revision: 8 }),
      response({ ...preferences, email_notifications: false, revision: 8 }),
    ]);
    const input = { locale: "vi-VN" as const, email_notifications: false, expected_revision: 7 };

    await expect(updatePreferences(input)).resolves.toEqual({ ...preferences, email_notifications: false, revision: 8 });
    await updatePreferences(input);

    const first = fetcher.mock.calls[0];
    const second = fetcher.mock.calls[1];
    for (const [url, init] of [first, second]) {
      expect(new URL(String(url)).pathname).toBe("/api/platform-admin/v1/preferences");
      expect(init?.method).toBe("PUT");
      expect(new Headers(init?.headers).get("Content-Type")).toBe("application/json");
      expect(JSON.parse(String(init?.body))).toEqual(input);
      expect(new Headers(init?.headers).get("Idempotency-Key")).toBeTruthy();
    }
    expect(new Headers(first[1]?.headers).get("Idempotency-Key")).not.toBe(new Headers(second[1]?.headers).get("Idempotency-Key"));
    expect(fetcher.mock.calls.map(([requestUrl]) => String(requestUrl)).some((url) => /\/(session|settings)(\?|$)/.test(url))).toBe(false);
  });

  it("preserves conflict details for the shared Vietnamese message", async () => {
    const fetcher = setup([response({
      code: "RESOURCE_CONFLICT",
      message: "Revision changed.",
      correlation_id: "preferences-conflict",
      retryable: false,
    }, 409)]);

    let caught: unknown;
    try {
      await getPreferences();
    } catch (cause) {
      caught = cause;
    }

    expect(caught).toMatchObject({ code: "RESOURCE_CONFLICT", status: 409, requestId: "preferences-conflict" });
    expect(backendMessage(caught)).toContain("Dữ liệu đã thay đổi. Tải lại trước khi thao tác tiếp.");
    expect(fetcher).toHaveBeenCalledOnce();
  });
});
