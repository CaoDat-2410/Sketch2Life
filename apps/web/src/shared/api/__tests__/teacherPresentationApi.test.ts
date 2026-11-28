import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BackendApiError } from "../backendApi";
import { teacherPresentationApi } from "../teacherPresentationApi";

const hash = "a".repeat(64);
const revision = {
  contract: "LessonPresentationRevisionV1", revision_no: 1, base_revision_no: null, state: "DRAFT", aspect_ratio: "16:9",
  source_state: "CURRENT", stale_reasons: [], plan_revision_no: 2, plan_content_hash: hash, content_hash: hash,
  slides: [{ slide_id: "slide-1", position: 1, title: "Title", body_text: "Body", media: null, media_state: null }],
  created_at: "2026-11-25T00:00:00Z", readied_at: null,
};
const presentation = {
  contract: "LessonPresentationV1", presentation_id: "pres-1", occurrence_id: "occ-1", revision: 4,
  head_revision_no: 1, ready_revision_no: null, source_state: "CURRENT", stale_reasons: [], presentable: false, head: revision,
};

function response(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return { ok: status >= 200 && status < 300, status, headers: new Headers(headers), text: async () => JSON.stringify(body) } as Response;
}
function setup(replies: Response[]) {
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
function call(fetcher: ReturnType<typeof setup>, index = 0) {
  const [url, init] = fetcher.mock.calls[index] as unknown as [string, RequestInit];
  return { url: new URL(url), init, headers: new Headers(init.headers), body: init.body ? JSON.parse(String(init.body)) as unknown : undefined };
}

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") } as never;
});
afterEach(() => {
  vi.restoreAllMocks(); vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined; window.sketch2lifeConfig = undefined;
});

describe("Teacher presentation API", () => {
  it("sends a strong aggregate If-Match and an idempotency key for a revision", async () => {
    const fetcher = setup([response(201, presentation, { ETag: '"5"' })]);
    const input = { repin_to_current_plan: false, operations: [{ op: "UPDATE_SLIDE" as const, slide_id: "slide-1", title: "New" }] };
    await teacherPresentationApi.createRevision("occ 1", 4, input, "revision-key");
    expect(call(fetcher).url.pathname).toBe("/v1/lesson-occurrences/occ%201/presentation/revisions");
    expect(call(fetcher).headers.get("If-Match")).toBe('"4"');
    expect(call(fetcher).headers.get("Idempotency-Key")).toBe("revision-key");
    expect(call(fetcher).body).toEqual(input);
  });

  it("rejects malformed presentation responses at runtime", async () => {
    const fetcher = setup([response(200, { ...presentation, head: { ...revision, content_hash: "bad" } })]);
    await expect(teacherPresentationApi.get("occ-1")).rejects.toMatchObject<Partial<BackendApiError>>({ code: "INVALID_RESPONSE", status: 502 });
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it("accepts a video slide without alt_text and still requires it for a picture", async () => {
    const slide = revision.slides[0];
    const video = { kind: "VIDEO_EMBED", provider: "YOUTUBE", video_id: "abc", embed_url: "https://www.youtube-nocookie.com/embed/abc", placement: "FULL" };
    const withMedia = (media: unknown) => ({ ...presentation, head: { ...revision, slides: [{ ...slide, media, media_state: "CURRENT" }] } });
    setup([
      response(200, withMedia(video), { ETag: '"4"' }),
      response(200, withMedia({ kind: "SVG_CATALOG", catalog_entry_id: "entry", canonical_sha256: hash, placement: "FULL" }), { ETag: '"4"' }),
    ]);
    await expect(teacherPresentationApi.get("occ-1")).resolves.toBeTruthy();
    await expect(teacherPresentationApi.get("occ-1")).rejects.toMatchObject<Partial<BackendApiError>>({ code: "INVALID_RESPONSE" });
  });

  it("preserves Retry-After for an SVG cooldown", async () => {
    const fetcher = setup([response(429, { code: "RATE_LIMITED", message: "safe", retryable: true }, { "Retry-After": "3600" })]);
    await expect(teacherPresentationApi.createSvgDraft("occ-1", { plan_activity_id: "activity-1", subject_text: "cat" }, "svg-key"))
      .rejects.toMatchObject({ code: "RATE_LIMITED", status: 429, retryAfterSeconds: 3600 });
    expect(call(fetcher).headers.get("Idempotency-Key")).toBe("svg-key");
  });

  it("creates a PRESENTATION_IMAGE session, uploads parts, and completes it", async () => {
    const session = (state: string, assetRef: string | null = null) => ({
      contract: "GenericUploadSessionV1", upload_id: "upload-1", purpose: "PRESENTATION_IMAGE", target_ref: "occ-1", state,
      part_size_bytes: 4 * 1024 * 1024, expected_parts: 1, accepted_parts: [], byte_count: 0,
      expires_at: "2026-11-25T00:00:00Z", revision: 1, asset_ref: assetRef, asset_state: null, error_code: null,
    });
    const fetcher = setup([
      response(201, session("OPEN")), response(200, session("OPEN")), response(200, { part_no: 1, accepted: true }), response(200, session("COMPLETED", "upl_image")),
    ]);
    vi.stubGlobal("crypto", { subtle: { digest: vi.fn(async () => new Uint8Array(32).fill(1).buffer) }, randomUUID: vi.fn(() => "generated-key") });
    const file = new File(["x"], "slide.png", { type: "image/png" });
    Object.defineProperty(file, "arrayBuffer", { value: async () => new Uint8Array([120]).buffer });
    await expect(teacherPresentationApi.uploadImage(file, "occ-1", { create: "create-key", complete: "complete-key" })).resolves.toBe("upl_image");
    expect(call(fetcher).url.pathname).toBe("/v1/upload-sessions");
    expect(call(fetcher).body).toMatchObject({ purpose: "PRESENTATION_IMAGE", target_ref: "occ-1", media_type: "image/png" });
    expect(call(fetcher).body).not.toHaveProperty("file_name");
    expect(call(fetcher, 0).headers.get("Idempotency-Key")).toBe("create-key");
    expect(call(fetcher, 3).headers.get("Idempotency-Key")).toBe("complete-key");
  });

  it("fetches image bytes with the bearer token instead of using a bare image URL", async () => {
    const fetcher = vi.fn(async () => new Response(new Blob(["image"]), { status: 200, headers: { "Content-Type": "image/png" } }));
    vi.stubGlobal("fetch", fetcher);
    const blob = await teacherPresentationApi.image("occ-1", "upl_x");
    expect(blob.type).toBe("image/png");
    const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(new URL(url).pathname).toBe("/v1/lesson-occurrences/occ-1/presentation/images/upl_x");
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer token-1");
  });
});
