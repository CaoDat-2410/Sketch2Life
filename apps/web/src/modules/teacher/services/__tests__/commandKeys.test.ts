import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { backendApi, type LessonContent, type TeacherLessonDetail } from "../../../../shared/api/backendApi";
import { fallbackMessage } from "../../../../shared/api/errorEnvelope";
import { commandSignature, keyForCommand } from "../commandKeys";

const lesson = (revision: number) => ({
  contract: "LessonDetailV1",
  lesson_id: "lesson-1",
  revision,
}) as unknown as TeacherLessonDetail;

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

describe("command keys", () => {
  it("reuses a key for the same command and revision, not for a new revision or payload", () => {
    const store = new Map<string, string>();
    const first = keyForCommand(store, commandSignature("update-lesson", "org", "lesson-1", 2, { title: "A" }));
    const retry = keyForCommand(store, commandSignature("update-lesson", "org", "lesson-1", 2, { title: "A" }));
    const reloaded = keyForCommand(store, commandSignature("update-lesson", "org", "lesson-1", 3, { title: "A" }));
    const edited = keyForCommand(store, commandSignature("update-lesson", "org", "lesson-1", 2, { title: "B" }));
    expect(retry).toBe(first);
    expect(reloaded).not.toBe(first);
    expect(edited).not.toBe(first);
  });
});

describe("Lesson Library command headers (FEAT-066 C4)", () => {
  it("sends If-Match and Idempotency-Key on save, archive and version create", async () => {
    const seen: Headers[] = [];
    vi.stubGlobal("fetch", vi.fn(async (_url: string, init: RequestInit) => {
      seen.push(new Headers(init.headers));
      return new Response(JSON.stringify({}), { status: 200, headers: { "Content-Type": "application/json" } });
    }));
    const content = {} as LessonContent;
    await backendApi.updateLesson("org-test", lesson(2), content, "key-save");
    await backendApi.archiveLesson("org-test", lesson(3), "key-archive");
    await backendApi.createLessonVersion("org-test", lesson(4), "rev-1", content, "key-version");
    expect(seen.map((headers) => [headers.get("If-Match"), headers.get("Idempotency-Key")])).toEqual([
      ['"2"', "key-save"],
      ['"3"', "key-archive"],
      ['"4"', "key-version"],
    ]);
  });

  it("accepts 202 from complete as success", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(
      JSON.stringify({ contract: "LessonSourceDocumentStatusV1", source_document_id: "s-1", state: "READY_FOR_REVIEW" }),
      { status: 202, headers: { "Content-Type": "application/json" } },
    )));
    const status = await backendApi.completeUpload("upload-1", "key-complete");
    expect(status.state).toBe("READY_FOR_REVIEW");
  });

  it("has a Vietnamese fallback for each new upload code", () => {
    for (const code of ["LESSON_FILE_TOO_LARGE", "UPLOAD_PART_CONFLICT", "UPLOAD_SESSION_STATE_CONFLICT", "UPLOAD_SESSION_EXPIRED", "UPLOAD_INCOMPLETE"]) {
      expect(fallbackMessage(code, 409)).not.toBe(fallbackMessage("UNKNOWN_CODE", 409));
    }
  });
});
