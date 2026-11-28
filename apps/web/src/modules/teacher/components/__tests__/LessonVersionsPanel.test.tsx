import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";

const api = vi.hoisted(() => ({ listLessonVersions: vi.fn(), getLessonVersion: vi.fn() }));
vi.mock("../../../../shared/api/teacherLessonLibraryApi", async () => ({
  ...(await vi.importActual("../../../../shared/api/teacherLessonLibraryApi")),
  listLessonVersions: api.listLessonVersions,
  getLessonVersion: api.getLessonVersion,
}));

import { LessonVersionsPanel } from "../LessonVersionsPanel";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const summary = (versionNo: number) => ({
  contract: "LessonVersionV1",
  version_id: `version-${versionNo}`,
  version_no: versionNo,
  review_state: "DRAFT" as const,
  structured_content_hash: "a".repeat(64),
  source_document_revision_id: null,
  authored_principal_ref: "teacher-1",
  created_at: `2026-11-${20 - versionNo}T00:00:00Z`,
});

describe("LessonVersionsPanel", () => {
  it("shows newest versions first, opens the exact version read-only, and loads more", async () => {
    api.listLessonVersions
      .mockResolvedValueOnce({ contract: "LessonVersionsPageV1", lesson_id: "lesson-1", items: [summary(3), summary(2)], next_cursor: "opaque-next" })
      .mockResolvedValueOnce({ contract: "LessonVersionsPageV1", lesson_id: "lesson-1", items: [summary(1)], next_cursor: null });
    api.getLessonVersion.mockResolvedValue({
      ...summary(2),
      lesson_id: "lesson-1",
      content: {
        locale: "vi-VN", title: "Bài bản hai", topic: "Động vật", target_age_band_ref: "age-72-107-months-v1", target_age_band_version: 1,
        objectives: ["Quan sát"], drawing_subject: "Con mèo", drawing_steps_text: "Vẽ đầu", subject_learning_notes: "Ghi chú",
        script_direction: null, script_following_allowed: false,
        activities: [{ title: "Đi dạo", objective: "Quan sát", materials_text: "Bút", preparation_text: "Chuẩn bị", instructions_text: "Đi chậm", observation_notes: "Quan sát", safety_notes: "Đi cùng cô", activity_kind: "outdoor" }],
      },
    });

    render(<LessonVersionsPanel organizationId="org-1" lessonId="lesson-1" />);
    const first = await screen.findByRole("button", { name: /Phiên bản 3/ });
    const second = screen.getByRole("button", { name: /Phiên bản 2/ });
    expect(first.textContent).toContain("Phiên bản 3 · ");
    expect(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();

    fireEvent.click(second);
    expect(await screen.findByRole("article", { name: "Nội dung phiên bản 2" })).toBeTruthy();
    expect(screen.getByText("Bài bản hai")).toBeTruthy();
    expect(screen.getByText("Nhóm tuổi:").parentElement?.textContent).toBe("Nhóm tuổi: 72–107 tháng");
    expect(screen.getByText(/Đi dạo/)).toBeTruthy();
    expect(api.getLessonVersion).toHaveBeenCalledWith("org-1", "lesson-1", "version-2", expect.any(AbortSignal));

    fireEvent.click(screen.getByRole("button", { name: "Tải thêm phiên bản" }));
    expect(await screen.findByRole("button", { name: /Phiên bản 1/ })).toBeTruthy();
    expect(api.listLessonVersions).toHaveBeenLastCalledWith("org-1", "lesson-1", { cursor: "opaque-next", signal: expect.any(AbortSignal) });
  });

  it("reloads the version list after a promotion refresh signal", async () => {
    api.listLessonVersions.mockResolvedValue({ contract: "LessonVersionsPageV1", lesson_id: "lesson-1", items: [], next_cursor: null });
    const view = render(<LessonVersionsPanel organizationId="org-1" lessonId="lesson-1" refreshToken={0} />);
    await waitFor(() => expect(api.listLessonVersions).toHaveBeenCalledTimes(1));

    view.rerender(<LessonVersionsPanel organizationId="org-1" lessonId="lesson-1" refreshToken={1} />);
    await waitFor(() => expect(api.listLessonVersions).toHaveBeenCalledTimes(2));
  });
});
