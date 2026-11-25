import { afterEach, describe, expect, it, vi } from "vitest";
import { backendApi, type LessonContent, type TeacherLessonDetail } from "../backendApi";

afterEach(() => {
  vi.unstubAllGlobals();
  window.sketch2lifeConfig = undefined;
  window.sketch2lifeAuth = undefined;
});

const content: LessonContent = {
  locale: "vi-VN",
  title: "Giáo án mới",
  topic: "Thực vật",
  target_age_band_ref: "age-4-6",
  target_age_band_version: 2,
  objectives: ["Nhận biết cây"],
  drawing_subject: "Cây non",
  drawing_steps_text: "Vẽ thân cây.",
  subject_learning_notes: "Cây cần nước.",
  script_direction: null,
  script_following_allowed: false,
  activities: [{
    title: "Quan sát cây",
    objective: "Nhận biết thân cây",
    materials_text: "",
    preparation_text: "",
    instructions_text: "Quan sát thân cây.",
    observation_notes: "",
    safety_notes: "",
    activity_kind: "indoor",
  }],
};

const lesson = {
  lesson_id: "lesson /1",
  revision: 8,
} as TeacherLessonDetail;

function response(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ ETag: '"9"', "X-Request-ID": "request-1" }),
    text: async () => JSON.stringify(body),
  } as Response;
}

describe("createLessonVersion API contract", () => {
  it("sends the strong revision, idempotency key, and version request body", async () => {
    window.sketch2lifeConfig = { apiBaseUrl: "https://api.test" };
    window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
    const fetcher = vi.fn(async () => response(201, { contract: "LessonVersionV1", version_id: "version-9", version_no: 9, review_state: "DRAFT" }));
    vi.stubGlobal("fetch", fetcher);

    await backendApi.createLessonVersion("org-1", lesson, "document-revision-1", content, "create-key-1");

    const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    const headers = new Headers(init.headers);
    expect(new URL(url).pathname).toBe("/api/lesson-library/v1/organizations/org-1/lessons/lesson%20%2F1/versions");
    expect(init.method).toBe("POST");
    expect(headers.get("If-Match")).toBe('"8"');
    expect(headers.get("Idempotency-Key")).toBe("create-key-1");
    expect(JSON.parse(String(init.body))).toEqual({
      contract: "CreateLessonVersionRequestV1",
      source_document_revision_id: "document-revision-1",
      content,
    });
  });

  it("retains safe field paths from a validation response for form mapping", async () => {
    window.sketch2lifeConfig = { apiBaseUrl: "https://api.test" };
    window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
    vi.stubGlobal("fetch", vi.fn(async () => response(422, {
      code: "INVALID_REQUEST",
      message: "Thông tin chưa hợp lệ.",
      correlation_id: "request-2",
      field_errors: [{ field: "content.title", code: "STRING_TOO_LONG" }, { field: "secret body", code: "DROP" }],
    })));

    await expect(backendApi.createLessonVersion("org-1", lesson, "revision-1", content, "create-key-2"))
      .rejects.toMatchObject({ status: 422, fieldErrors: [{ field: "content.title", code: "STRING_TOO_LONG" }] });
  });
});
