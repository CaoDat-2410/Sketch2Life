import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TeacherApiLessonPage } from "../TeacherApiLessonPage";
import { PortalSessionProvider } from "../../../../shared/auth/PortalSessionContext";
import { BackendApiError, backendApi, type TeacherLessonDetail } from "../../../../shared/api/backendApi";

const detailAt = (revision: number, title: string): TeacherLessonDetail => ({
  contract: "LessonDetailV1",
  lesson_id: "lesson-1",
  organization_id: "org-test",
  owner_kind: "ORGANIZATION",
  created_by: "teacher-1",
  state: "ACTIVE",
  visibility: "PRIVATE",
  moderation_state: "VISIBLE",
  current_version: {
    contract: "LessonVersionV1",
    lesson_id: "lesson-1",
    version_id: `version-${revision}`,
    version_no: revision,
    review_state: "DRAFT",
    structured_content_hash: `hash-${revision}`,
    source_document_revision_id: null,
    authored_principal_ref: "teacher-1",
    created_at: "2026-11-19T00:00:00Z",
    content: {
      locale: "vi-VN",
      title,
      topic: "Con vật",
      target_age_band_ref: "age-band-test",
      target_age_band_version: 1,
      objectives: ["Quan sát"],
      drawing_subject: "Con mèo",
      drawing_steps_text: "Vẽ đầu",
      subject_learning_notes: "Ghi chú",
      script_direction: null,
      script_following_allowed: false,
      activities: [{
        title: "Dạo vườn",
        objective: "Quan sát",
        materials_text: "",
        preparation_text: "",
        instructions_text: "Đi chậm",
        observation_notes: "",
        safety_notes: "",
        activity_kind: "outdoor",
      }],
    },
  },
  revision,
  created_at: "2026-11-19T00:00:00Z",
  updated_at: "2026-11-19T00:00:00Z",
} as unknown as TeacherLessonDetail);

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-test" };
  window.sketch2lifeAuth = {
    signIn: vi.fn(async () => undefined),
    getIdToken: vi.fn(async () => "unit-test-id-token"),
    signOut: vi.fn(async () => undefined),
  };
  vi.spyOn(backendApi, "assignments").mockResolvedValue({
    assignments: [{ role: "teacher", active: true }],
  } as unknown as Awaited<ReturnType<typeof backendApi.assignments>>);
  vi.spyOn(backendApi, "lessons").mockResolvedValue({
    contract: "LessonPageV1",
    items: [{ contract: "LessonSummaryV1", lesson_id: "lesson-1", title: "Bản cũ", topic: "Con vật", current_version_no: 2, review_state: "DRAFT", visibility: "PRIVATE", activity_count: 1, updated_at: "2026-11-19T00:00:00Z" }],
    next_cursor: null,
  } as unknown as Awaited<ReturnType<typeof backendApi.lessons>>);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  delete window.sketch2lifeConfig;
  delete window.sketch2lifeAuth;
});

describe("Teacher lesson stale save (FEAT-066 C4)", () => {
  it("keeps the form until the Teacher reloads, then saves with the new revision and a new key", async () => {
    const teacherLesson = vi.spyOn(backendApi, "teacherLesson")
      .mockResolvedValueOnce(detailAt(2, "Bản cũ"))
      .mockResolvedValueOnce(detailAt(3, "Bản của người khác"));
    const stale = new BackendApiError("Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", "STALE_REVISION", 409);
    const update = vi.spyOn(backendApi, "updateLesson")
      .mockRejectedValueOnce(stale)
      .mockResolvedValueOnce(detailAt(4, "Bản của người khác"));

    render(<MemoryRouter><PortalSessionProvider><TeacherApiLessonPage /></PortalSessionProvider></MemoryRouter>);

    fireEvent.click(await screen.findByRole("button", { name: /Bản cũ/ }));
    expect(await screen.findByText(/Revision 2/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Lưu cập nhật/ }));

    const reload = await screen.findByRole("button", { name: /Tải lại bản hiện tại/ });
    // The form text is not replaced automatically after the stale answer.
    expect(screen.getByDisplayValue("Bản cũ")).toBeTruthy();
    expect(teacherLesson).toHaveBeenCalledTimes(1);

    fireEvent.click(reload);
    expect(await screen.findByText(/Revision 3/)).toBeTruthy();
    expect(screen.getByDisplayValue("Bản của người khác")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Lưu cập nhật/ }));
    await waitFor(() => expect(update).toHaveBeenCalledTimes(2));
    const [first, second] = update.mock.calls;
    expect(first[1].revision).toBe(2);
    expect(second[1].revision).toBe(3);
    expect(second[3]).not.toBe(first[3]);
  });
});
