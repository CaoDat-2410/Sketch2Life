import { afterEach, describe, expect, it, vi } from "vitest";
import { BackendApiError } from "../backendApi";
import { getLessonVersion, listLessonVersions, remixLesson, searchPublicLessons } from "../teacherLessonLibraryApi";

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
    headers: new Headers({ ETag: '"1"', "X-Request-ID": "response-1" }),
    text: async () => body === undefined ? "" : JSON.stringify(body),
  } as Response;
}

function setup(replies: Response[]) {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

function request(fetcher: ReturnType<typeof setup>, index = 0) {
  const [url, init] = fetcher.mock.calls[index];
  return { url: new URL(url), init, headers: new Headers(init.headers) };
}

describe("teacher lesson library API", () => {
  it("lists versions with an opaque cursor, no-store headers, and encoded path ids", async () => {
    const fetcher = setup([response(200, { contract: "LessonVersionsPageV1", lesson_id: "lesson /1", items: [], next_cursor: null })]);
    const signal = new AbortController().signal;

    await listLessonVersions("org /1", "lesson /1", { cursor: "opaque /? page", signal });

    const sent = request(fetcher);
    expect(sent.url.pathname).toBe("/api/lesson-library/v1/organizations/org%20%2F1/lessons/lesson%20%2F1/versions");
    expect(sent.url.searchParams.get("limit")).toBe("25");
    expect(sent.url.searchParams.get("cursor")).toBe("opaque /? page");
    expect(sent.headers.get("Cache-Control")).toBe("private, no-store");
    expect(sent.init.signal).toBe(signal);
    expect(sent.headers.get("Authorization")).toBe("Bearer token-1");
  });

  it("reads one exact version without treating its ETag as a precondition", async () => {
    const fetcher = setup([response(200, { contract: "LessonVersionV1", lesson_id: "lesson-1", version_id: "version-1", version_no: 1, review_state: "DRAFT", structured_content_hash: "a".repeat(64), source_document_revision_id: null, authored_principal_ref: "teacher-1", created_at: "2026-11-20T00:00:00Z", content: { locale: "vi-VN", title: "Bài", topic: "Vẽ", target_age_band_ref: "age-1", target_age_band_version: 1, objectives: [], drawing_subject: "", drawing_steps_text: "", subject_learning_notes: "", script_direction: null, script_following_allowed: false, activities: [] } })]);

    await getLessonVersion("org-1", "lesson-1", "version/1");

    const sent = request(fetcher);
    expect(sent.url.pathname).toBe("/api/lesson-library/v1/organizations/org-1/lessons/lesson-1/versions/version%2F1");
    expect(sent.headers.get("Cache-Control")).toBe("private, no-store");
    expect(sent.headers.get("If-None-Match")).toBeNull();
    expect(sent.init.method).toBeUndefined();
  });

  it("searches with trimmed filters, a paired age band, and page limit", async () => {
    const fetcher = setup([response(200, { contract: "PublicLessonSearchPageV1", items: [], next_cursor: null })]);

    await searchPublicLessons("org-1", { q: "  Mèo  ", topic: "  Động vật ", targetAgeBandRef: "age-band:4", targetAgeBandVersion: 2, limit: 50 });

    const sent = request(fetcher);
    expect(sent.url.pathname).toBe("/api/lesson-library/v1/organizations/org-1/public-lessons");
    expect(Object.fromEntries(sent.url.searchParams)).toEqual({ q: "Mèo", topic: "Động vật", target_age_band_ref: "age-band:4", target_age_band_version: "2", limit: "50" });
    expect(sent.headers.get("Cache-Control")).toBe("private, no-store");
  });

  it("omits empty text filters and rejects invalid filter pairs, controls, and page bounds", async () => {
    const fetcher = setup([response(200, { contract: "PublicLessonSearchPageV1", items: [], next_cursor: null })]);

    await searchPublicLessons("org-1", { q: "   ", topic: "  " });
    expect(request(fetcher).url.searchParams.has("q")).toBe(false);
    expect(request(fetcher).url.searchParams.has("topic")).toBe(false);
    await expect(searchPublicLessons("org-1", { targetAgeBandRef: "age-1" })).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    await expect(searchPublicLessons("org-1", { q: "one\ntwo" })).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    await expect(searchPublicLessons("org-1", { limit: 101 })).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("remixes with the source ids, exact content hash, one idempotency key, and no If-Match", async () => {
    const fetcher = setup([response(201, { contract: "RemixLessonResponseV1", lesson: { lesson_id: "new-lesson" }, source: { lesson_id: "public-lesson", version_id: "v-2", content_sha256: "b".repeat(64) } })]);

    await remixLesson("org-1", "public-lesson", { sourceVersionId: "v-2", sourceContentSha256: "b".repeat(64) }, "remix-key-1");

    const sent = request(fetcher);
    expect(sent.url.pathname).toBe("/api/lesson-library/v1/organizations/org-1/lessons/public-lesson/remixes");
    expect(sent.init.method).toBe("POST");
    expect(sent.headers.get("Idempotency-Key")).toBe("remix-key-1");
    expect(sent.headers.get("If-Match")).toBeNull();
    expect(JSON.parse(String(sent.init.body))).toEqual({ source_version_id: "v-2", source_content_sha256: "b".repeat(64) });
  });

  it("maps unknown-resource and stale-source errors to safe copy and keeps current version", async () => {
    const fetcher = setup([
      response(404, { code: "RESOURCE_NOT_FOUND", message: "internal source detail", correlation_id: "c-1", retryable: false }),
      response(409, { code: "STALE_REVISION", message: "internal conflict", correlation_id: "c-2", retryable: false, current_version: 7 }),
      response(409, { code: "STALE_SOURCE_VERSION", message: "internal version detail", correlation_id: "c-3", retryable: false }),
    ]);

    await expect(getLessonVersion("org-1", "lesson-1", "missing"))
      .rejects.toMatchObject({ status: 404, message: "Không tìm thấy nội dung hoặc bạn không có quyền truy cập." });
    await expect(getLessonVersion("org-1", "lesson-1", "old"))
      .rejects.toMatchObject({ status: 409, code: "STALE_REVISION", currentVersion: 7, message: "Phiên bản đã thay đổi. Hãy tải lại nội dung rồi thử lại." });
    await expect(remixLesson("org-1", "lesson-1", { sourceVersionId: "v-1", sourceContentSha256: "c".repeat(64) }, "key-1"))
      .rejects.toMatchObject({ status: 409, code: "STALE_SOURCE_VERSION", message: "Bản công khai đã thay đổi. Hãy làm mới tìm kiếm rồi thử lại." });
    expect(fetcher).toHaveBeenCalledTimes(3);
  });

  it("rejects malformed remix keys and hashes before the request", async () => {
    const fetcher = setup([]);

    await expect(remixLesson("org-1", "lesson-1", { sourceVersionId: "v-1", sourceContentSha256: "bad" }, "bad key"))
      .rejects.toBeInstanceOf(BackendApiError);
    expect(fetcher).not.toHaveBeenCalled();
  });
});
