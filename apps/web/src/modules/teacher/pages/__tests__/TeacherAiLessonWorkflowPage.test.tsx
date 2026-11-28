import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { TeacherAiLessonWorkflowPage } from "../TeacherAiLessonWorkflowPage";
import { aiWorkflowService } from "../../services/aiWorkflowService";
import { clearAiWorkflowSession } from "../../services/aiWorkflowSession";
import { getAiTaskAggregateStatus, getAiTaskMark } from "../../services/aiTaskStatus";
import { authService } from "../../../school-manager/be1/services/authService";
import { backendApi } from "../../../../shared/api/backendApi";

const workflowStorageKey = "sketch2life:teacher-ai-workflow:v1:teacher-1:org-1";

beforeEach(() => {
  sessionStorage.clear();
  window.sketch2lifeConfig = { organizationId: "org-1" };
  vi.spyOn(authService, "getCurrentUser").mockReturnValue({ uid: "teacher-1" } as never);
  vi.spyOn(authService, "observe").mockImplementation((callback) => {
    callback({ uid: "teacher-1" } as never);
    return () => undefined;
  });
});

afterEach(() => {
  cleanup();
  clearAiWorkflowSession();
  vi.restoreAllMocks();
  window.sketch2lifeConfig = undefined;
});

function suggestionReply(drawing_steps_text: string, subject_learning_notes = "Mèo có bốn chân") {
  return {
    request_id: "req-1",
    suggestion: {
      title: "Giáo án về mèo",
      script_direction: "Mời trẻ kể điều đã quan sát.",
      drawing_steps_text,
      subject_learning_notes,
      activities: [{
        title: "Quan sát mèo",
        objective: "Gọi tên bộ phận",
        materials_text: "Giấy và bút chì",
        preparation_text: "Chuẩn bị tranh con mèo.",
        instructions_text: "Cùng quan sát",
        observation_notes: "Ghi nhận từ ngữ trẻ sử dụng.",
        safety_notes: "Không chạm vào mèo lạ",
        activity_kind: "indoor",
      }],
    },
  } as never;
}

function renderPage() {
  return render(<MemoryRouter><TeacherAiLessonWorkflowPage /></MemoryRouter>);
}

async function suggestSteps(drawing_steps_text: string, subject_learning_notes?: string) {
  vi.spyOn(aiWorkflowService, "suggestLessonPlan").mockResolvedValue(suggestionReply(drawing_steps_text, subject_learning_notes));
  renderPage();
  fireEvent.change(screen.getByLabelText(/Chủ đề/), { target: { value: "Con mèo" } });
  fireEvent.change(screen.getByLabelText(/Chủ thể trẻ sẽ vẽ/), { target: { value: "con mèo" } });
  fireEvent.change(screen.getByLabelText(/Tuổi mục tiêu/), { target: { value: "48" } });
  fireEvent.change(screen.getByLabelText(/Mục tiêu quan sát/), { target: { value: "Quan sát" } });
  fireEvent.click(screen.getByRole("button", { name: "Gợi ý giáo án bằng AI" }));
  await screen.findByLabelText("Vị trí bước 1");
  await waitFor(() => expect((screen.getByRole("button", { name: "Gợi ý giáo án bằng AI" }) as HTMLButtonElement).disabled).toBe(false));
}

function mockLessonSave() {
  return vi.spyOn(backendApi, "createLesson").mockResolvedValue({ lesson_id: "lesson-1" } as never);
}

describe("TeacherAiLessonWorkflowPage draft review and save", () => {
  it("normalizes generated knowledge list markers without dropping notes", async () => {
    await suggestSteps(
      "Vẽ đầu\nVẽ tai\nVẽ thân",
      "1. Trẻ nhận biết con mèo 3.5 tuổi. 2. Trẻ gọi tên các bộ phận.\n3. Trẻ quan sát cách mèo di chuyển.\n• Trẻ nêu cách mèo di chuyển.",
    );

    expect((screen.getByLabelText("Ghi chú kiến thức") as HTMLTextAreaElement).value).toBe(
      "Trẻ nhận biết con mèo 3.5 tuổi.\nTrẻ gọi tên các bộ phận.\nTrẻ quan sát cách mèo di chuyển.\nTrẻ nêu cách mèo di chuyển.",
    );
  });

  it("keeps objective text raw while typing and splits it only for the AI suggestion request", async () => {
    const suggestSpy = vi.spyOn(aiWorkflowService, "suggestLessonPlan").mockResolvedValue(
      suggestionReply("Vẽ đầu\nVẽ tai\nVẽ thân"),
    );
    renderPage();
    fireEvent.change(screen.getByLabelText(/Chủ đề/), { target: { value: "Con mèo" } });
    fireEvent.change(screen.getByLabelText(/Chủ thể trẻ sẽ vẽ/), { target: { value: "con mèo" } });
    fireEvent.change(screen.getByLabelText(/Tuổi mục tiêu/), { target: { value: "48" } });
    const objectives = screen.getByLabelText(/Mục tiêu quan sát/) as HTMLTextAreaElement;
    const rawObjectives = "Nhận biết hình dáng  \n\nGọi tên bộ phận\n";
    fireEvent.change(objectives, { target: { value: rawObjectives } });
    expect(objectives.value).toBe(rawObjectives);
    fireEvent.click(screen.getByRole("button", { name: "Gợi ý giáo án bằng AI" }));
    await screen.findByLabelText("Vị trí bước 1");

    expect(suggestSpy.mock.calls[0][0].objectives).toEqual(["Nhận biết hình dáng", "Gọi tên bộ phận"]);
  });

  it("saves every lesson field with schema limits and keeps the reviewed draft", async () => {
    const allNotes = Array.from({ length: 9 }, (_, index) => "Ghi chú " + (index + 1)).join("\n");
    const saveSpy = mockLessonSave();
    await suggestSteps("Vẽ đầu\nVẽ thân\nVẽ chân", allNotes);

    const title = screen.getByLabelText("Tên giáo án") as HTMLInputElement;
    fireEvent.change(title, { target: { value: "Giáo án quan sát mèo" } });
    fireEvent.change(screen.getByLabelText(/Mục tiêu quan sát/), { target: { value: "x".repeat(250) } });
    fireEvent.change(screen.getByLabelText("Bước vẽ 1"), { target: { value: "a".repeat(241) } });
    fireEvent.change(screen.getByLabelText("Vị trí bước 1"), { target: { value: "p".repeat(241) } });
    fireEvent.change(screen.getByLabelText("Vật liệu hoạt động 1"), { target: { value: "Giấy màu và bút chì" } });
    fireEvent.change(screen.getByLabelText("Chuẩn bị hoạt động 1"), { target: { value: "Cắt sẵn giấy màu." } });
    fireEvent.change(screen.getByLabelText("Cách thực hiện hoạt động 1"), { target: { value: "Mời trẻ quan sát tranh rồi mô tả." } });
    fireEvent.change(screen.getByLabelText("Ghi chú quan sát hoạt động 1"), { target: { value: "Ghi nhận vốn từ của trẻ." } });
    fireEvent.change(screen.getByLabelText("Lưu ý an toàn hoạt động 1"), { target: { value: "Không chạm vào mèo lạ." } });
    fireEvent.change(screen.getByLabelText("Định hướng kịch bản"), { target: { value: "Mời trẻ chia sẻ điều đã thấy." } });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Lưu thành giáo án" }));

    expect(saveSpy).toHaveBeenCalledTimes(1);
    const [organizationId, content, idempotencyKey] = saveSpy.mock.calls[0];
    expect(organizationId).toBe("org-1");
    expect(idempotencyKey).toEqual(expect.any(String));
    expect(content).toEqual({
      locale: "vi-VN",
      title: "Giáo án quan sát mèo",
      topic: "Con mèo",
      target_age_band_ref: "age-36-71-months-v1",
      target_age_band_version: 1,
      objectives: ["x".repeat(250)],
      drawing_subject: "con mèo",
      drawing_steps_text: [
        "Bước 1: " + "a".repeat(241) + " — vị trí: " + "p".repeat(241),
        "Bước 2: Vẽ thân — vị trí: trên trang vẽ",
        "Bước 3: Vẽ chân — vị trí: trên trang vẽ",
      ].join("\n"),
      subject_learning_notes: allNotes,
      script_direction: "Mời trẻ chia sẻ điều đã thấy.",
      script_following_allowed: false,
      activities: [{
        title: "Quan sát mèo",
        objective: "Gọi tên bộ phận",
        materials_text: "Giấy màu và bút chì",
        preparation_text: "Cắt sẵn giấy màu.",
        instructions_text: "Mời trẻ quan sát tranh rồi mô tả.",
        observation_notes: "Ghi nhận vốn từ của trẻ.",
        safety_notes: "Không chạm vào mèo lạ.",
        activity_kind: "indoor",
      }],
    });

    expect(await screen.findByRole("heading", { name: "Đã lưu thành giáo án" })).toBeTruthy();
    expect(screen.getByText("Giáo án quan sát mèo")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Mở thư viện giáo án" }).getAttribute("href")).toBe("/teacher/t02-lesson-authoring");
    expect(screen.getByRole("link", { name: "Mở trang buổi dạy" }).getAttribute("href")).toBe("/teacher/t04-session-sketch-deck");
    expect(screen.getByText(/chưa thể ghim vào buổi dạy/)).toBeTruthy();
    expect(screen.getByText(/Rà soát và duyệt kế hoạch/)).toBeTruthy();
    expect((screen.getByLabelText("Bước vẽ 1") as HTMLTextAreaElement).value).toBe("a".repeat(241));
    expect((screen.getByLabelText("Ghi chú kiến thức") as HTMLTextAreaElement).value.split("\n")).toHaveLength(9);
    expect(screen.queryByRole("button", { name: "Tạo Sketch Deck" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Mở trình chiếu" })).toBeNull();
    const stored = JSON.parse(sessionStorage.getItem(workflowStorageKey) ?? "{}") as Record<string, unknown>;
    expect(stored.savedLesson).toMatchObject({ title: "Giáo án quan sát mèo" });
    expect(stored.suggestion).toBeTruthy();
  });

  it("requires review confirmation and rejects serialized drawing steps beyond lesson schema limits", async () => {
    const saveSpy = mockLessonSave();
    await suggestSteps("Vẽ đầu\nVẽ thân\nVẽ chân");
    const initialSaveButton = screen.getByRole("button", { name: "Lưu thành giáo án" }) as HTMLButtonElement;
    expect(initialSaveButton.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Bước vẽ 1"), { target: { value: "x".repeat(3000) } });
    fireEvent.change(screen.getByLabelText("Vị trí bước 1"), { target: { value: "x".repeat(1200) } });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Lưu thành giáo án" }));

    expect((await screen.findByRole("alert")).textContent).toContain("Các bước vẽ tối đa 4.000 ký tự");
    expect(saveSpy).not.toHaveBeenCalled();
  });

  it("uses one in-flight request and reuses its idempotency key after an uncertain failure", async () => {
    let failFirst: ((cause: Error) => void) | undefined;
    const saveSpy = vi.spyOn(backendApi, "createLesson")
      .mockImplementationOnce(() => new Promise((_resolve, reject) => { failFirst = reject; }))
      .mockResolvedValueOnce({ lesson_id: "lesson-1" } as never);
    await suggestSteps("Vẽ đầu\nVẽ thân\nVẽ chân");
    fireEvent.click(screen.getByRole("checkbox"));
    const saveButton = screen.getByRole("button", { name: "Lưu thành giáo án" });

    fireEvent.click(saveButton);
    fireEvent.click(saveButton);
    expect(saveSpy).toHaveBeenCalledTimes(1);
    const firstKey = saveSpy.mock.calls[0][2];
    await vi.waitFor(() => expect(screen.getByRole("button", { name: "Đang lưu giáo án…" })).toBeTruthy());
    failFirst?.(new Error("Network issue"));
    await screen.findByRole("alert");
    await screen.findByRole("button", { name: "Lưu thành giáo án" });

    fireEvent.click(screen.getByRole("button", { name: "Lưu thành giáo án" }));
    await screen.findByRole("heading", { name: "Đã lưu thành giáo án" });

    expect(saveSpy).toHaveBeenCalledTimes(2);
    expect(saveSpy.mock.calls[1][2]).toBe(firstKey);
  });

  it("restores the draft only for the same account and organization", () => {
    const storedDraft = {
      topic: "Chủ đề đã lưu",
      ageMonths: "48",
      drawingSubject: "con mèo",
      objectivesText: "Quan sát đặc điểm",
      activityCount: "1",
      activityKind: "outdoor",
      suggestion: { drawing_steps_text: "steps", subject_learning_notes: "notes", activities: [] },
      lessonTitle: "Tên đã sửa",
      actions: ["Bước đã sửa"],
      placements: ["Trên trang vẽ"],
      knowledgeText: "Ghi chú đã sửa",
      activities: [{ activity_ref: "activity-1", title: "Hoạt động đã sửa", goal: "Mục tiêu", materials: "Vật liệu", preparation: "Chuẩn bị", instructions: "Cách làm", observation_notes: "Quan sát", safety_notes: "Lưu ý", activity_kind: "outdoor" }],
      reviewConfirmed: true,
      busy: "",
    };
    sessionStorage.setItem(workflowStorageKey, JSON.stringify(storedDraft));
    sessionStorage.setItem("sketch2life:teacher-ai-workflow:v1:teacher-2:org-2", JSON.stringify({ topic: "Dữ liệu tài khoản khác" }));
    window.sketch2lifeConfig = { organizationId: "org-2" };
    const view = renderPage();
    expect((screen.getByLabelText(/Chủ đề/) as HTMLInputElement).value).toBe("");

    window.sketch2lifeConfig = { organizationId: "org-1" };
    view.rerender(<MemoryRouter><TeacherAiLessonWorkflowPage /></MemoryRouter>);
    expect((screen.getByLabelText(/Chủ đề/) as HTMLInputElement).value).toBe("Chủ đề đã lưu");
    expect((screen.getByLabelText("Tên giáo án") as HTMLInputElement).value).toBe("Tên đã sửa");
    expect((screen.getByLabelText("Bước vẽ 1") as HTMLTextAreaElement).value).toBe("Bước đã sửa");
    expect((screen.getByLabelText("Ghi chú kiến thức") as HTMLTextAreaElement).value).toBe("Ghi chú đã sửa");
  });

  it("recovers an old page-local deck task without showing or waiting for a deck", () => {
    sessionStorage.setItem(workflowStorageKey, JSON.stringify({
      topic: "Chủ đề đang soạn",
      busy: "deck",
      deck: { schema_version: "legacy-deck", slides: [] },
    }));
    renderPage();

    expect((screen.getByRole("button", { name: "Gợi ý giáo án bằng AI" }) as HTMLButtonElement).disabled).toBe(false);
    expect(screen.queryByRole("button", { name: "Tạo Sketch Deck" })).toBeNull();
    expect(screen.getByRole("status").textContent).toContain("buổi dạy");
    expect(getAiTaskAggregateStatus()).toBeUndefined();
    expect(getAiTaskMark("suggestion")).toBeUndefined();
  });

  it("shows Vietnamese page copy and does not expose request details", async () => {
    await suggestSteps("Vẽ đầu\nVẽ thân\nVẽ chân");

    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Gợi ý giáo án AI");
    expect(screen.getByText("Nhập chủ đề, rà soát bản nháp rồi lưu thành giáo án trong thư viện.")).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/Qwen|Backend|Modal|Mã yêu cầu|req-1|schema|contract|token|organization_id/i);
    expect(getAiTaskMark("suggestion")?.status).toBe("done");
  });
});
