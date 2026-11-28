import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter, useLocation } from "react-router-dom";
import { TeacherPortalApp } from "../App";
import { backendApi } from "../../../shared/api/backendApi";
import { teacherOccurrenceApi, type Occurrence } from "../../../shared/api/teacherOccurrenceApi";
import { authService } from "../../school-manager/be1/services/authService";
import { clearAiWorkflowSession } from "../services/aiWorkflowSession";
import { clearSvgDraftRequests } from "../services/svgDraftRequests";
import {
  beginAiTask,
  finishAiTask,
  getAiTaskAggregateStatus,
  getAiTaskMark,
  svgTaskStatusKey,
} from "../services/aiTaskStatus";

const portal = vi.hoisted(() => ({ logout: vi.fn() }));

vi.mock("../../../shared/auth/PortalSessionContext", () => ({
  usePortalSession: () => ({ currentRole: "TEACHER", isAuthenticated: true, toast: null, logout: portal.logout }),
}));
vi.mock("../pages/TeacherPresentationPage", () => ({ TeacherPresentationPage: () => <h1>Presentation route</h1> }));
vi.mock("../pages/TeacherSampleRunPage", () => ({ TeacherSampleRunPage: () => <h1>Sample video route</h1> }));
vi.mock("../pages/TeacherProjectionPage", () => ({ TeacherProjectionPage: () => <h1>Class projection route</h1> }));

const occurrence: Occurrence = {
  contract: "LessonOccurrenceV1",
  occurrence_id: "occ-1",
  class_id: "class-1",
  title: "Buổi dạy",
  scheduled_date: null,
  state: "APPROVED",
  revision: 1,
  responsible_teacher_ref: "teacher-1",
  lesson_version_ref: null,
  lesson_version_no: null,
  approved_plan: null,
  sample_video: { slot_state: "CLAIMED", claimed_at: null, run_ref: null },
  created_at: "2026-11-26T00:00:00Z",
};

function CurrentRoute() {
  const location = useLocation();
  return <output data-testid="current-route">{location.pathname}{location.search}</output>;
}

function renderTeacher(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <TeacherPortalApp />
      <CurrentRoute />
    </MemoryRouter>,
  );
}

function mockOccurrencePage() {
  vi.spyOn(backendApi, "assignments").mockResolvedValue({
    contract: "Be1AdultAssignmentsV1", subject: "teacher", organization_id: "org-test",
    assignments: [{ role: "teacher", class_id: "class-1", active: true }],
  } as never);
  vi.spyOn(backendApi, "classes").mockResolvedValue({
    items: [{ contract: "Be1ClassV1", class_id: "class-1", display_name: "Lớp Mầm" }],
  } as never);
  vi.spyOn(backendApi, "lessons").mockResolvedValue({ items: [] } as never);
  vi.spyOn(teacherOccurrenceApi, "list").mockResolvedValue({ items: [occurrence], next_cursor: null } as never);
  vi.spyOn(teacherOccurrenceApi, "get").mockResolvedValue({ data: occurrence, etag: '"1"', notModified: false } as never);
  vi.spyOn(teacherOccurrenceApi, "listDocuments").mockResolvedValue({ items: [], next_cursor: null } as never);
  vi.spyOn(teacherOccurrenceApi, "listPlans").mockResolvedValue({ items: [], next_cursor: null } as never);
}

function beforeUnloadEvent() {
  const event = new Event("beforeunload", { cancelable: true }) as BeforeUnloadEvent;
  Object.defineProperty(event, "returnValue", { configurable: true, writable: true, value: "unchanged" });
  return event;
}

beforeEach(() => {
  portal.logout.mockReset();
  portal.logout.mockImplementation(() => undefined);
  window.sketch2lifeConfig = { organizationId: "org-test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "unit-test-token") } as never;
  vi.spyOn(authService, "observe").mockImplementation((callback) => {
    callback({ uid: "teacher-test" } as never);
    return () => undefined;
  });
  mockOccurrencePage();
});

afterEach(() => {
  cleanup();
  clearAiWorkflowSession();
  clearSvgDraftRequests();
  vi.restoreAllMocks();
  vi.useRealTimers();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

describe("Teacher AI navigation continuity", () => {
  it.each([
    ["Chỉnh sửa và trình bày slide", "/teacher/t02-presentation?occurrence=occ-1", "Presentation route"],
    ["Video mẫu", "/teacher/t06-sample-story-run?occurrence=occ-1", "Sample video route"],
    ["Chiếu cho lớp", "/teacher/t07-video-presentation-confirmation?occurrence=occ-1", "Class projection route"],
  ])("keeps workflow state while following %s and returning", async (label, targetPath, targetHeading) => {
    renderTeacher("/teacher/t13-ai-lesson-workflow");
    const topic = await screen.findByLabelText(/Chủ đề/) as HTMLInputElement;
    fireEvent.change(topic, { target: { value: "Continuity draft" } });
    let runId = 0;
    act(() => { runId = beginAiTask("suggestion"); });
    expect(getAiTaskMark("suggestion")?.status).toBe("pending");

    fireEvent.click(screen.getByRole("link", { name: /Buổi dạy/ }));
    await waitFor(() => expect(screen.getByTestId("current-route").textContent).toBe("/teacher/t04-session-sketch-deck"));
    fireEvent.click(await screen.findByRole("link", { name: label }));
    await waitFor(() => expect(screen.getByTestId("current-route").textContent).toBe(targetPath));
    expect(screen.getByRole("heading", { name: targetHeading })).toBeTruthy();

    fireEvent.click(screen.getByRole("link", { name: /Gợi ý giáo án AI/ }));
    await waitFor(() => expect(screen.getByTestId("current-route").textContent).toBe("/teacher/t13-ai-lesson-workflow"));
    expect((screen.getByLabelText(/Chủ đề/) as HTMLInputElement).value).toBe("Continuity draft");
    expect(getAiTaskMark("suggestion")?.runId).toBe(runId);
    expect(getAiTaskMark("suggestion")?.status).toBe("pending");
  });

  it("registers one leave warning while any task is pending and removes it afterwards", async () => {
    const addListener = vi.spyOn(window, "addEventListener");
    const removeListener = vi.spyOn(window, "removeEventListener");
    renderTeacher("/teacher/t13-ai-lesson-workflow");
    expect(addListener.mock.calls.filter(([type]) => type === "beforeunload")).toHaveLength(0);

    let suggestionRun = 0;
    let svgRun = 0;
    const svgKey = svgTaskStatusKey("occ-1");
    act(() => {
      suggestionRun = beginAiTask("suggestion");
      svgRun = beginAiTask(svgKey);
    });
    await waitFor(() => expect(addListener.mock.calls.filter(([type]) => type === "beforeunload")).toHaveLength(1));
    const handler = addListener.mock.calls.find(([type]) => type === "beforeunload")?.[1];
    expect(typeof handler).toBe("function");

    const warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(true);
    expect(warning.returnValue).toBe("");

    act(() => { finishAiTask("suggestion", suggestionRun, "done"); });
    expect(removeListener.mock.calls.filter(([type]) => type === "beforeunload")).toHaveLength(0);
    const stillPendingWarning = beforeUnloadEvent();
    window.dispatchEvent(stillPendingWarning);
    expect(stillPendingWarning.defaultPrevented).toBe(true);

    act(() => { finishAiTask(svgKey, svgRun, "done"); });
    await waitFor(() => expect(removeListener.mock.calls.some(([type, listener]) => type === "beforeunload" && listener === handler)).toBe(true));
    const completedWarning = beforeUnloadEvent();
    window.dispatchEvent(completedWarning);
    expect(completedWarning.defaultPrevented).toBe(false);
    expect(getAiTaskAggregateStatus()).toBe("done");
  });

  it("clears pending task state before Teacher logout can trigger a warning", async () => {
    let statusAtLogout: ReturnType<typeof getAiTaskAggregateStatus> = "pending";
    let preventedAtLogout: boolean | undefined;
    portal.logout.mockImplementation(() => {
      statusAtLogout = getAiTaskAggregateStatus();
      const event = beforeUnloadEvent();
      window.dispatchEvent(event);
      preventedAtLogout = event.defaultPrevented;
    });
    renderTeacher("/teacher/t13-ai-lesson-workflow");
    act(() => {
      beginAiTask("suggestion");
      beginAiTask(svgTaskStatusKey("occ-1"));
    });
    await waitFor(() => expect(getAiTaskAggregateStatus()).toBe("pending"));

    fireEvent.click(screen.getByRole("button", { name: "Đăng xuất" }));

    expect(portal.logout).toHaveBeenCalledOnce();
    expect(statusAtLogout).toBeUndefined();
    expect(preventedAtLogout).toBe(false);
    expect(getAiTaskMark("suggestion")).toBeUndefined();
    expect(getAiTaskMark(svgTaskStatusKey("occ-1"))).toBeUndefined();
  });
});
