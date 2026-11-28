import { afterEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { teacherWorkspaceApi, type TeacherActivity } from "../../../../shared/api/teacherWorkspaceApi";
import { PlanActivityPicker, type PlanLessonActivity } from "../PlanActivityPicker";

const pin = { lesson_id: "lesson-1", version_id: "version-2" };
const activity = (lessonId: string, versionId: string, id: string, order: number, title: string): TeacherActivity => ({
  lesson_id: lessonId,
  version_id: versionId,
  version_no: 2,
  content_sha256: "a".repeat(64),
  lesson_title: "Giáo án",
  lesson_topic: null,
  lesson_activity_id: id,
  activity_order: order,
  title,
  objective: null,
  activity_kind: "indoor",
  materials_text: null,
  preparation_text: null,
  instructions_text: null,
  observation_notes: null,
  safety_notes: null,
});

function Harness({
  lessonVersionRef = pin,
  initialSelection = [],
  copiedFromPlan = false,
}: {
  lessonVersionRef?: typeof pin | null;
  initialSelection?: PlanLessonActivity[];
  copiedFromPlan?: boolean;
}) {
  const [selection, setSelection] = useState(initialSelection);
  return <>
    <PlanActivityPicker
      organizationId="org-1"
      lessonVersionRef={lessonVersionRef}
      selection={selection}
      onSelectionChange={setSelection}
      copiedFromPlan={copiedFromPlan}
    />
    <output aria-label="selected activities">{selection.map((item) => item.lesson_activity_id).join(",")}</output>
  </>;
}

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("PlanActivityPicker", () => {
  it("loads every page, offers only the pinned lesson version, orders activities, and selects them by default", async () => {
    const list = vi.spyOn(teacherWorkspaceApi, "activities")
      .mockResolvedValueOnce({
        contract: "TeacherActivityPageV1",
        items: [activity("lesson-1", "version-2", "activity-2", 2, "Hai"), activity("lesson-other", "version-2", "other-lesson", 1, "Giáo án khác")],
        next_cursor: "next-page",
      })
      .mockResolvedValueOnce({
        contract: "TeacherActivityPageV1",
        items: [activity("lesson-1", "version-2", "activity-1", 1, "Một"), activity("lesson-1", "version-old", "other-version", 3, "Phiên bản cũ")],
        next_cursor: null,
      });

    render(<Harness />);
    await screen.findByRole("checkbox", { name: /Một/ });
    await waitFor(() => expect((screen.getAllByRole("checkbox") as HTMLInputElement[]).every((checkbox) => checkbox.checked)).toBe(true));

    const checkboxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(checkboxes.map((checkbox) => checkbox.parentElement?.textContent)).toEqual(["1. Một", "2. Hai"]);
    expect(checkboxes.every((checkbox) => checkbox.parentElement?.classList.contains("cozy-form-checkbox-card"))).toBe(true);
    expect(checkboxes.every((checkbox) => checkbox.parentElement?.classList.contains("teacher-plan-activity-checkbox"))).toBe(true);
    expect(checkboxes.every((checkbox) => checkbox.checked)).toBe(true);
    expect(screen.getByLabelText("selected activities").textContent).toBe("activity-1,activity-2");
    expect(list).toHaveBeenNthCalledWith(1, "org-1", { limit: 100 });
    expect(list).toHaveBeenNthCalledWith(2, "org-1", { limit: 100, cursor: "next-page" });
  });

  it("keeps copied selections, including an activity missing from the current list", async () => {
    vi.spyOn(teacherWorkspaceApi, "activities").mockResolvedValue({
      contract: "TeacherActivityPageV1",
      items: [activity("lesson-1", "version-2", "activity-1", 1, "Một"), activity("lesson-1", "version-2", "activity-2", 2, "Hai")],
      next_cursor: null,
    });
    render(<Harness
      initialSelection={[
        { kind: "LESSON", lesson_activity_id: "activity-1" },
        { kind: "LESSON", lesson_activity_id: "retired-activity" },
      ]}
      copiedFromPlan
    />);

    await screen.findByRole("checkbox", { name: /Một/ });
    expect((screen.getByRole("checkbox", { name: /Một/ }) as HTMLInputElement).checked).toBe(true);
    expect((screen.getByRole("checkbox", { name: /Hai/ }) as HTMLInputElement).checked).toBe(false);
    expect(screen.getByLabelText("selected activities").textContent).toBe("activity-1,retired-activity");
    expect(screen.getByText(/Giữ nguyên 1 hoạt động không có trong danh sách hiện tại từ bản kế hoạch trước/)).toBeTruthy();
  });

  it("offers a retry after a load error", async () => {
    vi.spyOn(teacherWorkspaceApi, "activities")
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValueOnce({ contract: "TeacherActivityPageV1", items: [activity("lesson-1", "version-2", "activity-1", 1, "Một")], next_cursor: null });
    render(<Harness />);

    expect(await screen.findByRole("alert")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Thử tải lại hoạt động" }));
    expect(await screen.findByRole("checkbox", { name: /Một/ })).toBeTruthy();
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });

  it("renders nothing when no lesson version is pinned", () => {
    const list = vi.spyOn(teacherWorkspaceApi, "activities");
    render(<Harness lessonVersionRef={null} />);
    expect(screen.queryByRole("group", { name: "Hoạt động từ giáo án đã ghim" })).toBeNull();
    expect(list).not.toHaveBeenCalled();
  });
});
