import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TeacherActivitiesPage } from "../TeacherActivitiesPage";
import { TeacherHistoryPage } from "../TeacherHistoryPage";
import { TeacherProfilePage } from "../TeacherProfilePage";
import { teacherWorkspaceApi } from "../../../../shared/api/teacherWorkspaceApi";

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-1" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token") } as never;
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); window.sketch2lifeAuth = undefined; window.sketch2lifeConfig = undefined; });

describe("Teacher workspace pages", () => {
  it("shows only current approved activities from the organization API", async () => {
    vi.spyOn(teacherWorkspaceApi, "activities").mockResolvedValue({ contract: "TeacherActivityPageV1", next_cursor: null, items: [{
      lesson_id: "lesson-1", version_id: "version-1", version_no: 2, content_sha256: "a".repeat(64), lesson_title: "Màu sắc", lesson_topic: "Nghệ thuật", lesson_activity_id: "activity-1", activity_order: 1,
      title: "Vẽ cùng nhau", objective: "Quan sát", activity_kind: "indoor", materials_text: "Giấy", preparation_text: null, instructions_text: "Vẽ", observation_notes: null, safety_notes: null,
    }] });
    render(<TeacherActivitiesPage />);
    expect(await screen.findByRole("heading", { name: /Vẽ cùng nhau/ })).toBeTruthy();
    expect(screen.getByText("Hoạt động trong các giáo án đã duyệt.")).toBeTruthy();
    expect(screen.getByText("Trong lớp")).toBeTruthy();
    expect(screen.queryByText("Trong nhà")).toBeNull();
    expect(screen.getByText("Vẽ")).toBeTruthy();
  });

  it("filters history and links an occurrence to its presentation", async () => {
    vi.spyOn(teacherWorkspaceApi, "history").mockResolvedValue({ contract: "LessonOccurrencePageV1", next_cursor: null, items: [{
      contract: "LessonOccurrenceV1", occurrence_id: "occ-1", class_id: "class-1", title: "Buổi vẽ", scheduled_date: "2026-11-25", state: "SAMPLE_AVAILABLE", revision: 2,
      responsible_teacher_ref: "teacher-1", lesson_version_ref: null, lesson_version_no: null, approved_plan: null,
      sample_video: { slot_state: "AVAILABLE", claimed_at: null, run_ref: null }, created_at: "2026-11-25T00:00:00Z",
    }] });
    render(<MemoryRouter><TeacherHistoryPage /></MemoryRouter>);
    expect(await screen.findByText("Buổi vẽ")).toBeTruthy();
    expect(screen.getByText("Lên lớp")).toBeTruthy();
    const filter = screen.getByLabelText("Trạng thái");
    expect(filter.closest(".s2l-data-card")).toBeNull();
    expect(screen.getByRole("option", { name: "Rà soát tài liệu" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Rà soát kế hoạch" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Có thể tạo video mẫu" })).toBeTruthy();
    expect(screen.getByText("Buổi vẽ").closest("li")?.querySelector(".s2l-status-badge")?.textContent).toContain("Có thể tạo video mẫu");
    const presentationLink = screen.getByRole("link", { name: "Mở trình bày" });
    expect(presentationLink.className).toContain("s2l-card-link");
    expect(presentationLink.className).not.toContain("s2l-button");
    expect(presentationLink.style.minHeight).toBe("44px");
    expect(presentationLink.getAttribute("href")).toBe("/teacher/t02-presentation?occurrence=occ-1");
    expect(screen.getByRole("button", { name: "Tải lại" }).className).not.toContain("is-primary");
  });

  it("shows the read-only identity profile without edit controls", async () => {
    vi.spyOn(teacherWorkspaceApi, "profile").mockResolvedValue({ contract: "TeacherProfileV1", account_ref: "account-1", display_name: "Cô An", email: "an@example.test" });
    render(<TeacherProfilePage />);
    expect(await screen.findByText("Cô An")).toBeTruthy();
    expect(screen.getByText("an@example.test")).toBeTruthy();
    expect(screen.getByText("Thông tin tài khoản của bạn.")).toBeTruthy();
    expect(document.body.textContent?.match(/Giáo viên/g)).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /Sửa|Chỉnh sửa/ })).toBeNull();
  });
});
