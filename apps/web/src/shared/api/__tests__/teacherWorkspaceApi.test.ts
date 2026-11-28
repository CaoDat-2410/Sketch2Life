import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { teacherWorkspaceApi } from "../teacherWorkspaceApi";

function response(body: unknown): Response {
  return { ok: true, status: 200, headers: new Headers(), text: async () => JSON.stringify(body) } as Response;
}
function setup(replies: Response[]) {
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
function args(fetcher: ReturnType<typeof setup>, index = 0) {
  const [url, init] = fetcher.mock.calls[index] as unknown as [string, RequestInit];
  return { url: new URL(url), init };
}

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") } as never;
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); window.sketch2lifeAuth = undefined; window.sketch2lifeConfig = undefined; });

describe("Teacher workspace routes", () => {
  it("reads paginated organization activities with the requested cursor", async () => {
    const activity = { lesson_id: "lesson-1", version_id: "v1", version_no: 2, content_sha256: "a".repeat(64), lesson_title: "Lesson", lesson_topic: null, lesson_activity_id: "activity-1", activity_order: 1, title: "Draw", objective: null, activity_kind: "indoor", materials_text: null, preparation_text: null, instructions_text: "Draw together", observation_notes: null, safety_notes: null };
    const fetcher = setup([response({ contract: "TeacherActivityPageV1", items: [activity], next_cursor: "next" })]);
    expect(await teacherWorkspaceApi.activities("org/1", { limit: 10, cursor: "opaque" })).toMatchObject({ items: [activity], next_cursor: "next" });
    expect(args(fetcher).url.pathname).toBe("/api/lesson-library/v1/organizations/org%2F1/activities");
    expect(args(fetcher).url.searchParams.get("cursor")).toBe("opaque");
  });

  it("reads history with a state filter and rejects malformed response rows", async () => {
    const fetcher = setup([response({ contract: "LessonOccurrencePageV1", items: [], next_cursor: null })]);
    await teacherWorkspaceApi.history("org", { state: "APPROVED", limit: 7 });
    expect(args(fetcher).url.pathname).toBe("/api/teacher/v1/organizations/org/history");
    expect(args(fetcher).url.searchParams.get("state")).toBe("APPROVED");
    const invalid = setup([response({ contract: "LessonOccurrencePageV1", items: [{ occurrence_id: "unvalidated" }], next_cursor: null })]);
    await expect(teacherWorkspaceApi.history("org")).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
    expect(invalid).toHaveBeenCalledTimes(1);
  });

  it("reads only a validated teacher profile", async () => {
    setup([response({ contract: "TeacherProfileV1", account_ref: "acct-1", display_name: "Teacher", email: null })]);
    await expect(teacherWorkspaceApi.profile()).resolves.toMatchObject({ display_name: "Teacher", email: null });
    setup([response({ contract: "TeacherProfileV1", display_name: "Teacher", email: "x" })]);
    await expect(teacherWorkspaceApi.profile()).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });

  it("reads portfolio pages without accepting malformed content", async () => {
    const row = { observation_id: "obs-1", session_id: "session-1", kind: "observation", content: { note: "Observed" }, created_at: "2026-11-25T00:00:00Z" };
    const fetcher = setup([response({ contract: "Be1PortfolioPageV1", child_id: "child-1", items: [row], next_cursor: null })]);
    await expect(teacherWorkspaceApi.portfolio("org", "class", "child-1")).resolves.toMatchObject({ items: [row] });
    expect(args(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org/classes/class/profiles/child-1/portfolio");
    setup([response({ contract: "Be1PortfolioPageV1", child_id: "child-1", items: [{ ...row, content: null }], next_cursor: null })]);
    await expect(teacherWorkspaceApi.portfolio("org", "class", "child-1")).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });
});
