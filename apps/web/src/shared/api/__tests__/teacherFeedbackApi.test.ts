import { afterEach, describe, expect, it, vi } from "vitest";
import { teacherFeedbackApi } from "../teacherFeedbackApi";

afterEach(() => { vi.unstubAllGlobals(); window.sketch2lifeAuth = undefined; });

const summary = { thread_id: "thread-1", lesson_id: "lesson-1", version_id: "version-2", lesson_title: "Khoa học vui", version_no: 2, revision: 4, created_at: "2026-11-25T10:00:00Z" };
const thread = { thread_id: "thread-1", organization_id: "org-1", lesson_id: "lesson-1", version_id: "version-2", lesson_title: "Khoa học vui", version_no: 2, revision: 4, limit: 10, next_cursor: null, items: [{ message_id: "message-1", body: "Good lesson", from_you: false, author_role: "parent", author_display_name: "Phụ huynh An", created_at: "2026-11-25T10:00:00Z" }] };
function mock(body: unknown, status = 200) {
  window.sketch2lifeAuth = { getIdToken: async () => "token" };
  const fetcher = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

describe("Teacher feedback API", () => {
  it("loads organization threads with the page size and cursor", async () => {
    const body = { total: 1, limit: 12, next_cursor: null, items: [summary] };
    const fetcher = mock(body);
    await expect(teacherFeedbackApi.feedbackThreads("org one", 12, "next cursor")).resolves.toEqual(body);
    const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url.endsWith("/api/lesson-library/v1/organizations/org%20one/feedback?limit=12&cursor=next+cursor")).toBe(true);
    expect(init.method ?? "GET").toBe("GET");
    expect(init.body).toBeUndefined();
    expect(body.items[0]).toMatchObject({ lesson_title: "Khoa học vui", version_no: 2 });
  });

  it("loads a thread page using the encoded thread id", async () => {
    const body = { ...thread, thread_id: "thread/one" };
    const fetcher = mock(body);
    await expect(teacherFeedbackApi.feedbackThread("org-1", "thread/one", 10)).resolves.toEqual(body);
    const [url] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url.endsWith("/api/lesson-library/v1/organizations/org-1/feedback/thread%2Fone?limit=10")).toBe(true);
    expect(body.items[0]).toMatchObject({ author_role: "parent", author_display_name: "Phụ huynh An" });
  });

  it("replies with the quoted revision, key, and exact body", async () => {
    const result = { thread_id: "thread-1", revision: 5 };
    const fetcher = mock(result);
    await expect(teacherFeedbackApi.replyFeedback("org-1", "thread-1", "Thank you", 4, "reply-key")).resolves.toEqual(result);
    const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    const headers = new Headers(init.headers);
    expect(url.endsWith("/api/lesson-library/v1/organizations/org-1/feedback/thread-1/replies")).toBe(true);
    expect(init.method).toBe("POST");
    expect(headers.get("If-Match")).toBe('"4"');
    expect(headers.get("Idempotency-Key")).toBe("reply-key");
    expect(JSON.parse(String(init.body))).toEqual({ body: "Thank you" });
  });

  it("rejects invalid response shapes", async () => {
    const fetcher = mock({ total: 1, limit: 25, next_cursor: null, items: [{ ...summary, revision: "bad" }] });
    await expect(teacherFeedbackApi.feedbackThreads("org-1")).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
