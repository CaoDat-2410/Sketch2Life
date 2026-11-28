import { afterEach, describe, expect, it, vi } from "vitest";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  NOTIFICATIONS_PAGE_LIMIT,
  NOTIFICATIONS_TIMEOUT_MS,
  NOTIFICATION_NOT_FOUND_MESSAGE,
} from "../notificationsApi";
import type { NotificationItem } from "../notificationsApi";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

function response(status: number, body?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "response-1" }),
    text: async () => body === undefined ? "" : JSON.stringify(body),
  } as Response;
}

function setup(replies: Response[]) {
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

function item(overrides: Partial<NotificationItem> = {}): NotificationItem {
  return {
    contract: "NotificationV1",
    inbox_item_id: "item-1",
    notification_type: "CLASS_ARCHIVED",
    template_version: 1,
    safe_parameters: { class_ref: "opaque-1" },
    created_at: "2026-11-20T10:00:00Z",
    read_at: null,
    expires_at: null,
    ...overrides,
  };
}

function call(fetcher: ReturnType<typeof setup>, index = 0) {
  const [url, init] = fetcher.mock.calls[index];
  return { url, init, headers: new Headers(init.headers), body: init.body };
}

describe("notifications API", () => {
  it("uses the default page limit and the maximum supported limit", async () => {
    const fetcher = setup([
      response(200, { contract: "NotificationPageV1", items: [], next_cursor: null, unread_count: 0 }),
      response(200, { contract: "NotificationPageV1", items: [], next_cursor: null, unread_count: 100 }),
      response(200, { contract: "NotificationPageV1", items: [], next_cursor: null, unread_count: 1 }),
    ]);

    await listNotifications();
    await listNotifications({ limit: 100 });
    await listNotifications({ limit: 1 });

    expect(NOTIFICATIONS_PAGE_LIMIT).toBe(25);
    expect(new URL(call(fetcher, 0).url).searchParams.get("limit")).toBe("25");
    expect(new URL(call(fetcher, 1).url).searchParams.get("limit")).toBe("100");
    expect(new URL(call(fetcher, 2).url).searchParams.get("limit")).toBe("1");
  });

  it("passes an opaque cursor unchanged and sends Accept and X-Request-ID", async () => {
    const fetcher = setup([response(200, { contract: "NotificationPageV1", items: [], next_cursor: null, unread_count: 0 })]);
    const cursor = "opaque /cursor?part=1&x=2";

    await listNotifications({ cursor });

    const request = call(fetcher);
    expect(new URL(request.url).searchParams.get("cursor")).toBe(cursor);
    expect(request.headers.get("Accept")).toBe("application/json");
    expect(request.headers.get("X-Request-ID")).toBeTruthy();
    expect(request.headers.get("Authorization")).toBe("Bearer token-1");
  });

  it("sends keyed POSTs without a body and percent-encodes the inbox item id", async () => {
    const fetcher = setup([
      response(200, item({ inbox_item_id: "item /1", read_at: "2026-11-20T11:00:00Z" })),
      response(200, { contract: "NotificationReadAllV1", marked_count: 3 }),
    ]);

    await markNotificationRead("item /1", "read-key-1");
    await markAllNotificationsRead("read-all-key-1");

    const one = call(fetcher, 0);
    expect(new URL(one.url).pathname).toBe("/v1/notifications/item%20%2F1/read");
    expect(one.init.method).toBe("POST");
    expect(one.headers.get("Idempotency-Key")).toBe("read-key-1");
    expect(one.body).toBeUndefined();
    const all = call(fetcher, 1);
    expect(new URL(all.url).pathname).toBe("/v1/notifications/read-all");
    expect(all.headers.get("Idempotency-Key")).toBe("read-all-key-1");
    expect(all.body).toBeUndefined();
  });

  it("rejects invalid visible-ASCII keys before sending a request", async () => {
    const fetcher = setup([]);

    await expect(markNotificationRead("item-1", "has space")).rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY" });
    await expect(markAllNotificationsRead("k".repeat(129))).rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY" });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("returns 401 without an auth bridge token and never calls fetch", async () => {
    const fetcher = setup([]);
    window.sketch2lifeAuth = undefined;

    await expect(listNotifications()).rejects.toMatchObject({ status: 401, code: "AUTHENTICATION_REQUIRED" });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("maps every 404 to the same fixed message", async () => {
    setup([
      response(404, { detail: { code: "RESOURCE_NOT_FOUND", message: "wrong role or item" } }),
      response(400, { code: "RESOURCE_NOT_FOUND", message: "wrong role or item" }),
    ]);

    await expect(listNotifications()).rejects.toMatchObject({ status: 404, message: NOTIFICATION_NOT_FOUND_MESSAGE });
    await expect(listNotifications()).rejects.toMatchObject({ status: 400, message: NOTIFICATION_NOT_FOUND_MESSAGE });
  });

  it("preserves INVALID_IDEMPOTENCY_KEY and rejects unexpected response contracts", async () => {
    setup([
      response(400, { code: "INVALID_IDEMPOTENCY_KEY", message: "invalid" }),
      response(200, { contract: "OtherPageV1", items: [], next_cursor: null, unread_count: 0 }),
    ]);

    await expect(markAllNotificationsRead("valid-key")).rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY" });
    await expect(listNotifications()).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });

  it("times out a hung request with a retryable REQUEST_TIMEOUT error", async () => {
    vi.useFakeTimers();
    try {
      window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
      vi.stubGlobal("fetch", vi.fn((_url: string, init: RequestInit) => new Promise((_resolve, reject) => {
        init.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
      })));

      const pending = markAllNotificationsRead("valid-key");
      const assertion = expect(pending).rejects.toMatchObject({ code: "REQUEST_TIMEOUT", status: 0 });
      await vi.advanceTimersByTimeAsync(NOTIFICATIONS_TIMEOUT_MS + 1);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });
});
