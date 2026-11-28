import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PortalSessionProvider } from "../../../../shared/auth/PortalSessionContext";
import { backendApi } from "../../../../shared/api/backendApi";
import type { PublicLessonHit, RemixLessonResult } from "../../../../shared/api/teacherLessonLibraryApi";
import { TeacherApiLessonPage } from "../TeacherApiLessonPage";

const library = vi.hoisted(() => ({ searchPublicLessons: vi.fn(), remixLesson: vi.fn(), listLessonVersions: vi.fn() }));
vi.mock("../../../../shared/api/teacherLessonLibraryApi", async () => ({
  ...(await vi.importActual("../../../../shared/api/teacherLessonLibraryApi")),
  searchPublicLessons: library.searchPublicLessons,
  remixLesson: library.remixLesson,
  listLessonVersions: library.listLessonVersions,
}));

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "test-token") };
  vi.spyOn(backendApi, "assignments").mockResolvedValue({ assignments: [{ role: "teacher", active: true }] } as never);
  vi.spyOn(backendApi, "lessons")
    .mockResolvedValueOnce({ contract: "LessonPageV1", items: [], next_cursor: null })
    .mockResolvedValue({ contract: "LessonPageV1", items: [], next_cursor: null } as never);
  library.searchPublicLessons.mockResolvedValue({ contract: "PublicLessonSearchPageV1", items: [], next_cursor: null });
  library.listLessonVersions.mockResolvedValue({ contract: "LessonVersionsPageV1", lesson_id: "private-copy", items: [], next_cursor: null });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.clearAllMocks();
  delete window.sketch2lifeConfig;
  delete window.sketch2lifeAuth;
  vi.unstubAllGlobals();
});

function publicHit(): PublicLessonHit {
  return {
    contract: "PublicLessonHitV1", lesson_id: "public-lesson", version_id: "public-v3", structured_content_hash: "a".repeat(64),
    title: "Public lesson", topic: "Động vật", target_age_band_ref: "age-1", target_age_band_version: 1,
    activity_count: 1, updated_at: "2026-11-20T00:00:00Z",
  };
}

function remixResult(): RemixLessonResult {
  return {
    contract: "RemixLessonResponseV1",
    lesson: {
      contract: "LessonDetailV1", lesson_id: "private-copy", organization_id: "org-test", owner_kind: "ORGANIZATION", created_by: "teacher-1",
      state: "ACTIVE", visibility: "PRIVATE", moderation_state: "VISIBLE",
      current_version: {
        contract: "LessonVersionV1", lesson_id: "private-copy", version_id: "copy-v1", version_no: 1, review_state: "DRAFT",
        structured_content_hash: "b".repeat(64), source_document_revision_id: null, authored_principal_ref: "teacher-1", created_at: "2026-11-20T00:00:00Z",
        content: {
          locale: "vi-VN", title: "Private copy", topic: "Động vật", target_age_band_ref: "age-1", target_age_band_version: 1,
          objectives: ["Quan sát"], drawing_subject: "Con mèo", drawing_steps_text: "Vẽ đầu", subject_learning_notes: "Ghi chú",
          script_direction: null, script_following_allowed: false,
          activities: [{ title: "Hoạt động mới", objective: "Quan sát", materials_text: "", preparation_text: "", instructions_text: "Đi chậm", observation_notes: "", safety_notes: "", activity_kind: "outdoor" }],
        },
      },
      revision: 1, created_at: "2026-11-20T00:00:00Z", updated_at: "2026-11-20T00:00:00Z",
    },
    source: { lesson_id: "public-lesson", version_id: "public-v3", content_sha256: "a".repeat(64) },
  };
}

describe("TeacherApiLessonPage lesson library wiring", () => {
  it("opens the remix result, shows its source, and refreshes the lesson list", async () => {
    vi.stubGlobal("crypto", { randomUUID: () => "page-remix-key" });
    library.searchPublicLessons.mockResolvedValue({ contract: "PublicLessonSearchPageV1", items: [publicHit()], next_cursor: null });
    const result = remixResult();
    library.remixLesson.mockResolvedValue(result);

    render(<MemoryRouter><PortalSessionProvider><TeacherApiLessonPage /></PortalSessionProvider></MemoryRouter>);
    fireEvent.change(await screen.findByLabelText("Từ khóa"), { target: { value: "Public" } });
    fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));
    fireEvent.click(await screen.findByRole("button", { name: "Sao chép thành bản của tôi" }));

    expect(await screen.findByDisplayValue("Private copy")).toBeTruthy();
    expect((await screen.findAllByText(/Tạo từ bài công khai “Public lesson”/)).length).toBeGreaterThan(0);
    await waitFor(() => expect(backendApi.lessons).toHaveBeenCalledTimes(2));
    const selected = screen.getByRole("button", { name: /Private copy/ });
    expect(selected.getAttribute("aria-pressed")).toBe("true");
    expect(library.remixLesson).toHaveBeenCalledWith("org-test", "public-lesson", { sourceVersionId: "public-v3", sourceContentSha256: "a".repeat(64) }, "page-remix-key");
  });
});
