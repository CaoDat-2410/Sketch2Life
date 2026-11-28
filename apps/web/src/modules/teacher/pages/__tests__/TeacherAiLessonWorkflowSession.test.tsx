import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { TeacherAiLessonWorkflowPage } from "../TeacherAiLessonWorkflowPage";
import { aiWorkflowService } from "../../services/aiWorkflowService";
import { clearAiWorkflowSession } from "../../services/aiWorkflowSession";
import { getAiTaskMark } from "../../services/aiTaskStatus";
import { authService } from "../../../school-manager/be1/services/authService";

const account = vi.hoisted(() => ({ change: (_uid: string | null) => undefined as void }));

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-1" };
  vi.spyOn(authService, "getCurrentUser").mockReturnValue({ uid: "teacher-1" } as never);
  vi.spyOn(authService, "observe").mockImplementation((callback) => {
    account.change = (uid) => callback(uid ? ({ uid } as never) : null);
    account.change("teacher-1");
    return () => undefined;
  });
});
afterEach(() => {
  cleanup();
  clearAiWorkflowSession();
  vi.restoreAllMocks();
  vi.useRealTimers();
  window.sketch2lifeConfig = undefined;
});

const reply = {
  request_id: "req-1",
  suggestion: {
    drawing_steps_text: "Vẽ đầu\nVẽ tai\nVẽ đuôi",
    subject_learning_notes: "Mèo có bốn chân",
    activities: [{ title: "Quan sát mèo", objective: "Gọi tên bộ phận", materials_text: "", preparation_text: "", instructions_text: "Cùng quan sát", safety_notes: "Cẩn thận" }],
  },
} as never;

function startRequest() {
  let finish: () => void = () => undefined;
  const spy = vi.spyOn(aiWorkflowService, "suggestLessonPlan").mockImplementation(() => new Promise((resolve) => { finish = () => resolve(reply); }));
  const view = render(<TeacherAiLessonWorkflowPage />);
  fireEvent.change(screen.getByLabelText(/Chủ đề/), { target: { value: "Con mèo" } });
  fireEvent.change(screen.getByLabelText(/Chủ thể trẻ sẽ vẽ/), { target: { value: "con mèo" } });
  fireEvent.change(screen.getByLabelText(/Tuổi mục tiêu/), { target: { value: "48" } });
  fireEvent.change(screen.getByLabelText(/Mục tiêu quan sát/), { target: { value: "Quan sát" } });
  fireEvent.click(screen.getByRole("button", { name: "Gợi ý giáo án bằng AI" }));
  return { view, spy, finish: () => act(async () => { finish(); }) };
}

describe("Teacher AI workflow across screens", () => {
  it("sets and clears the lesson-plan mark after the visible page has shown the result", async () => {
    const visibility = Object.getOwnPropertyDescriptor(document, "visibilityState");
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });
    vi.useFakeTimers();
    try {
      const { finish } = startRequest();
      expect(getAiTaskMark("suggestion")?.status).toBe("pending");

      await finish();
      expect(getAiTaskMark("suggestion")?.status).toBe("done");

      await act(async () => { vi.advanceTimersByTime(3_999); });
      expect(getAiTaskMark("suggestion")?.status).toBe("done");
      await act(async () => { vi.advanceTimersByTime(1); });
      expect(getAiTaskMark("suggestion")).toBeUndefined();
    } finally {
      vi.useRealTimers();
      if (visibility) Object.defineProperty(document, "visibilityState", visibility);
      else Reflect.deleteProperty(document, "visibilityState");
    }
  });

  it("keeps the form, the running request and its result while the Teacher is on another screen", async () => {
    const { view, spy, finish } = startRequest();
    view.unmount();

    const back = render(<TeacherAiLessonWorkflowPage />);
    expect((screen.getByLabelText(/Chủ đề/) as HTMLInputElement).value).toBe("Con mèo");
    expect((screen.getByRole("button", { name: /Đang tạo bản nháp/ }) as HTMLButtonElement).disabled).toBe(true);
    back.unmount();

    await finish();
    render(<TeacherAiLessonWorkflowPage />);
    expect((screen.getByLabelText("Bước vẽ 1") as HTMLTextAreaElement).value).toBe("Vẽ đầu");
    expect(screen.getAllByLabelText(/^Bước vẽ/)).toHaveLength(3);
    expect(screen.getAllByLabelText(/^Vị trí bước/)).toHaveLength(3);
    expect(spy).toHaveBeenCalledTimes(1);
    expect(window.localStorage.length).toBe(0);
    const key = window.sessionStorage.key(0);
    expect(key).toContain("teacher-1:org-1");
    const stored = JSON.parse(window.sessionStorage.getItem(key!) ?? "{}") as Record<string, unknown>;
    expect(stored.busy).toBe("");
    expect(stored.suggestion).toBeTruthy();
    expect(stored.deck).toBeUndefined();
  });

  it("clears everything on sign-out and ignores a result that arrives afterwards", async () => {
    const { finish } = startRequest();
    act(() => account.change(null));
    expect((screen.getByLabelText(/Chủ đề/) as HTMLInputElement).value).toBe("");
    expect(window.sessionStorage.length).toBe(0);
    await finish();
    expect(screen.queryByLabelText("Bước vẽ 1")).toBeNull();
    expect(screen.getByRole("button", { name: "Gợi ý giáo án bằng AI" })).toBeTruthy();
  });
});
