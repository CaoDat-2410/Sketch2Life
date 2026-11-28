import { afterEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import * as lessonApi from "../../../../shared/api/teacherLessonLibraryApi";
import { BackendApiError } from "../../../../shared/api/backendApi";
import { TeacherSketchDeckPanel } from "../TeacherSketchDeckPanel";
import { teacherOccurrenceApi, type CurrentSketchDeck, type PlanRevision, type SketchDeckRevision, type SketchDeckStep } from "../../../../shared/api/teacherOccurrenceApi";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

const plan: PlanRevision = {
  contract: "LessonPlanRevisionV1",
  occurrence_id: "occ-1",
  plan_revision_id: "plan-rev-2",
  revision_no: 2,
  state: "APPROVED",
  content_hash: "a".repeat(64),
  document_revision_ref: null,
  objectives: ["Observe a tree."],
  teacher_direction: "Guide the observation.",
  safety_notes: null,
  lesson_version_ref: null,
  lesson_version_no: null,
  activities: [{ plan_activity_id: "activity-1", order: 1, kind: "CUSTOM", lesson_activity_id: null, title: "Activity", description: null, snapshot_hash: null, checklist_required: false, checklist_version: null, confirmed: false }],
  created_at: "2026-11-26T00:00:00Z",
  approved_at: "2026-11-26T00:00:01Z",
  supersedes_revision_no: null,
};

function revision(state: SketchDeckRevision["state"] = "READY"): SketchDeckRevision {
  return {
    contract: "SketchDeckRevisionV1",
    sketch_deck_revision_id: "deck-rev-1",
    occurrence_id: "occ-1",
    plan_revision_id: plan.plan_revision_id,
    revision_no: 1,
    plan_content_hash: plan.content_hash,
    review_confirmed: true,
    topic: "A tree",
    drawing_steps: Array.from({ length: 4 }, (_, index) => ({ action: `Draw part ${index + 1}`, placement: `At part ${index + 1}` })),
    subject_knowledge: ["Trees have roots."],
    target_age_band: "age-36-71-months-v1",
    deck_schema_version: "sketch2life.teacher-sketch-deck.v1",
    state,
    content_hash: state === "READY" ? "b".repeat(64) : null,
    created_at: "2026-11-26T00:00:00Z",
    ready_at: state === "READY" ? "2026-11-26T00:00:01Z" : null,
    superseded_at: null,
  };
}

function step(index: number): SketchDeckStep {
  return {
    sketch_deck_step_id: `step-${index}`,
    plan_activity_id: "activity-1",
    instruction_group_key: "tree-guide",
    step_index: index,
    step_kind: "DRAW",
    subject_key: "tree",
    short_title: "Tree drawing steps",
    child_facing_prompt: `Draw part ${index}.`,
    teacher_explanation: `Teacher note ${index}.`,
    bounded_layout_hints: { region: `part-${index}` },
    line_sketch_asset_ref: null,
    line_sketch_asset_version: null,
    source_job_ref: null,
    state: "READY",
    created_at: "2026-11-26T00:00:00Z",
  };
}

function current(overrides: Partial<CurrentSketchDeck> = {}, state: SketchDeckRevision["state"] = "READY"): CurrentSketchDeck {
  return {
    contract: "SketchDeckCurrentV1",
    occurrence_id: "occ-1",
    current_revision: revision(state),
    steps: state === "READY" ? Array.from({ length: 4 }, (_, index) => step(index + 1)) : [],
    stale: false,
    presentable: state === "READY",
    ...overrides,
  };
}

function setup(deck: CurrentSketchDeck) {
  vi.spyOn(teacherOccurrenceApi, "getPlan").mockResolvedValue({ data: plan, etag: null, notModified: false });
  vi.spyOn(teacherOccurrenceApi, "getSketchDeck").mockResolvedValue(deck);
  return vi.spyOn(teacherOccurrenceApi, "createSketchDeck").mockResolvedValue(revision("GENERATING"));
}

async function fillAndSubmit(teacherAgeBandRef: string | null = "age-36-71-months-v1") {
  await screen.findByLabelText("Chủ đề");
  // Loading the plan resets the confirmations in an effect; let it run before filling the form.
  await act(async () => {});
  const ageBandField = screen.queryByRole("combobox", { name: /Nhóm tuổi mục tiêu/ });
  if (ageBandField && teacherAgeBandRef) {
    // The shared Select keeps a hidden native control; changing it is what picking an option does.
    const nativeSelect = ageBandField.parentElement?.querySelector("select.s2l-select-native");
    if (!nativeSelect) throw new Error("The age band uses the shared Select");
    fireEvent.change(nativeSelect, { target: { value: teacherAgeBandRef } });
  }
  fireEvent.change(screen.getByLabelText("Chủ đề"), { target: { value: "A tree" } });
  for (let index = 1; index <= 4; index += 1) {
    fireEvent.change(screen.getByLabelText(`Thao tác bước ${index}`), { target: { value: `Draw part ${index}` } });
    fireEvent.change(screen.getByLabelText(`Vị trí bước ${index}`), { target: { value: `At part ${index}` } });
  }
  fireEvent.change(screen.getByLabelText("Ghi chú 1"), { target: { value: "Trees have roots." } });
  const reviewCheckbox = screen.getByRole("checkbox") as HTMLInputElement;
  if (!reviewCheckbox.checked) fireEvent.click(reviewCheckbox);
  fireEvent.click(screen.getByRole("button", { name: "Tạo Sketch Deck" }));
}

const emptyDeck: CurrentSketchDeck = {
  contract: "SketchDeckCurrentV1", occurrence_id: "occ-1", current_revision: null, steps: [], stale: false, presentable: false,
};

describe("TeacherSketchDeckPanel", () => {
  it("shows a STALE banner and does not allow presentation", async () => {
    setup(current({ stale: true, presentable: false }));
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    expect(await screen.findByText("Sketch Deck đã cũ.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Mở trình chiếu" })).toBeNull();
  });

  it("does not present a READY deck unless the backend marks it presentable", async () => {
    setup(current({ presentable: false }));
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    expect(await screen.findByText(/Backend chưa đánh dấu bản này có thể trình bày/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Mở trình chiếu" })).toBeNull();
  });

  it("opens the existing presentation component for a READY deck on the approved plan", async () => {
    setup(current());
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    fireEvent.click(await screen.findByRole("button", { name: "Mở trình chiếu" }));
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect(screen.getByText("Draw part 1.")).toBeTruthy();
  });

  it("validates before sending and requires explicit Teacher review", async () => {
    const create = setup({
      contract: "SketchDeckCurrentV1", occurrence_id: "occ-1", current_revision: null, steps: [], stale: false, presentable: false,
    });
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await screen.findByLabelText("Chủ đề");
    fireEvent.change(screen.getByLabelText("Chủ đề"), { target: { value: "A tree" } });
    for (let index = 1; index <= 4; index += 1) {
      fireEvent.change(screen.getByLabelText(new RegExp(`Thao tác bước ${index}`)), { target: { value: `Draw part ${index}` } });
      fireEvent.change(screen.getByLabelText(new RegExp(`Vị trí bước ${index}`)), { target: { value: `At part ${index}` } });
    }
    fireEvent.change(screen.getByLabelText("Ghi chú 1"), { target: { value: "Trees have roots." } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo Sketch Deck" }));

    expect(await screen.findByText("Hãy xác nhận đã rà soát thông tin trước khi tạo Sketch Deck.")).toBeTruthy();
    expect(create).not.toHaveBeenCalled();
  });

  it("shows the required count message when the drawing rows are empty", async () => {
    const create = setup(emptyDeck);
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await screen.findByLabelText("Chủ đề");
    fireEvent.change(screen.getByLabelText("Chủ đề"), { target: { value: "A tree" } });
    fireEvent.change(screen.getByLabelText("Ghi chú 1"), { target: { value: "Trees have roots." } });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Tạo Sketch Deck" }));

    expect(screen.getByRole("alert").textContent).toContain("Cần 4–8 bước vẽ");
    expect(create).not.toHaveBeenCalled();
  });

  it("shows FAILED and offers full deck creation again", async () => {
    setup(current({}, "FAILED"));
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    expect(await screen.findByText(/Lần tạo Sketch Deck không thành công/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Tạo Sketch Deck" })).toBeTruthy();
  });

  it("shows the empty state and refresh action while generation is pending", async () => {
    const generating = current({}, "GENERATING");
    setup({ ...generating, current_revision: { ...generating.current_revision!, created_at: new Date().toISOString() } });
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    expect(await screen.findByText(/Deck đang được tạo/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Làm mới trạng thái" })).toBeTruthy();
  });

  it("offers creation when no current deck exists", async () => {
    setup(emptyDeck);
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    expect(await screen.findByText("Chưa có Sketch Deck cho buổi dạy này.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Tạo Sketch Deck" })).toBeTruthy();
  });

  it("requires the Teacher to choose an age band when the plan has no library source", async () => {
    const create = setup(emptyDeck);
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await fillAndSubmit(null);

    expect(await screen.findByText("Hãy chọn nhóm tuổi mục tiêu để xác nhận cho kế hoạch chưa gắn bài học trong thư viện.")).toBeTruthy();
    expect(create).not.toHaveBeenCalled();
  });

  it("keeps Teacher age-band confirmation optional when the plan has a library source", async () => {
    const sourcePlan: PlanRevision = {
      ...plan,
      lesson_version_ref: {
        lesson_id: "lesson-1",
        version_id: "version-1",
        content_sha256: "c".repeat(64),
      },
      lesson_version_no: 1,
    };
    vi.spyOn(teacherOccurrenceApi, "getPlan").mockResolvedValue({ data: sourcePlan, etag: null, notModified: false });
    vi.spyOn(teacherOccurrenceApi, "getSketchDeck").mockResolvedValue(emptyDeck);
    const create = vi.spyOn(teacherOccurrenceApi, "createSketchDeck").mockResolvedValue(revision("GENERATING"));
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    await fillAndSubmit(null);

    expect(create).toHaveBeenCalledTimes(1);
    expect(create.mock.calls[0]?.[1]).not.toHaveProperty("teacher_confirmed_age_band_ref");
  });

  it("locks creation during a fresh, non-stale generation and explains why", async () => {
    const generating = current({}, "GENERATING");
    setup({ ...generating, current_revision: { ...generating.current_revision!, created_at: new Date().toISOString() } });
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    expect(await screen.findByText(/nút tạo được khóa trong 15 phút/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Tạo Sketch Deck" }).hasAttribute("disabled")).toBe(true);
  });

  it("allows another generation after 15 minutes or when the current generation is stale", async () => {
    const oldGenerating = current({}, "GENERATING");
    setup({ ...oldGenerating, current_revision: { ...oldGenerating.current_revision!, created_at: new Date(Date.now() - 16 * 60_000).toISOString() } });
    const { unmount } = render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    expect(await screen.findByText(/đã kéo dài hơn 15 phút/)).toBeTruthy();
    expect(screen.getByRole("button", { name: "Tạo Sketch Deck" }).hasAttribute("disabled")).toBe(false);
    unmount();
    cleanup();

    const staleGenerating = current({ stale: true, presentable: false }, "GENERATING");
    setup(staleGenerating);
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await screen.findByText(/Deck đã cũ/);
    expect(screen.getByRole("button", { name: "Tạo Sketch Deck" }).hasAttribute("disabled")).toBe(false);
  });

  it("shows incomplete-plan guidance with technical details and does not reload", async () => {
    const getPlan = vi.spyOn(teacherOccurrenceApi, "getPlan").mockResolvedValue({ data: plan, etag: null, notModified: false });
    const getDeck = vi.spyOn(teacherOccurrenceApi, "getSketchDeck").mockResolvedValue(emptyDeck);
    const create = vi.spyOn(teacherOccurrenceApi, "createSketchDeck").mockRejectedValue(
      new BackendApiError("Backend message", "SKETCH_DECK_PLAN_INCOMPLETE", 409, "req-incomplete"),
    );
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await fillAndSubmit();

    expect(await screen.findByText(/Kế hoạch hiện tại chưa đủ điều kiện tạo Sketch Deck/)).toBeTruthy();
    fireEvent.click(screen.getByText("Thông tin kỹ thuật"));
    expect(screen.getByText("SKETCH_DECK_PLAN_INCOMPLETE")).toBeTruthy();
    expect(screen.getByText("req-incomplete")).toBeTruthy();
    expect(getPlan).toHaveBeenCalledTimes(1);
    expect(getDeck).toHaveBeenCalledTimes(1);
    expect(create).toHaveBeenCalledTimes(1);
    expect(screen.queryByText(/Kế hoạch hoặc nguồn đã thay đổi/)).toBeNull();
  });

  it("translates a server EMPTY step-count field error into the required message", async () => {
    const create = vi.spyOn(teacherOccurrenceApi, "createSketchDeck").mockRejectedValue(
      new BackendApiError("Yêu cầu không hợp lệ.", "INVALID_REQUEST", 400, "req-empty", [
        { field: "drawing_steps", code: "EMPTY" },
      ]),
    );
    vi.spyOn(teacherOccurrenceApi, "getPlan").mockResolvedValue({ data: plan, etag: null, notModified: false });
    vi.spyOn(teacherOccurrenceApi, "getSketchDeck").mockResolvedValue(emptyDeck);
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await fillAndSubmit();

    expect(await screen.findByText("Cần 4–8 bước vẽ.")).toBeTruthy();
    fireEvent.click(screen.getByText("Thông tin kỹ thuật"));
    expect(screen.queryByText("EMPTY")).toBeNull();
    expect(create).toHaveBeenCalledTimes(1);
  });

  it("reloads only for STALE_REVISION and leaves other 409 errors as normal errors", async () => {
    const getPlan = vi.spyOn(teacherOccurrenceApi, "getPlan").mockResolvedValue({ data: plan, etag: null, notModified: false });
    const getDeck = vi.spyOn(teacherOccurrenceApi, "getSketchDeck").mockResolvedValue(emptyDeck);
    const create = vi.spyOn(teacherOccurrenceApi, "createSketchDeck")
      .mockRejectedValueOnce(new BackendApiError("Plan revision moved", "STALE_REVISION", 409))
      .mockRejectedValueOnce(new BackendApiError("Another conflict", "INVALID_STATE_TRANSITION", 409));
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);

    await fillAndSubmit();
    expect(await screen.findByText(/Đã tải lại kế hoạch và Sketch Deck hiện tại/)).toBeTruthy();
    expect(getPlan).toHaveBeenCalledTimes(2);
    expect(getDeck).toHaveBeenCalledTimes(2);

    await fillAndSubmit();
    expect(await screen.findByText("Another conflict")).toBeTruthy();
    expect(getPlan).toHaveBeenCalledTimes(2);
    expect(getDeck).toHaveBeenCalledTimes(2);
    expect(create).toHaveBeenCalledTimes(2);
  });

  it("keeps the successful generation notice after reloading current state", async () => {
    vi.spyOn(teacherOccurrenceApi, "getPlan").mockResolvedValue({ data: plan, etag: null, notModified: false });
    vi.spyOn(teacherOccurrenceApi, "getSketchDeck")
      .mockResolvedValueOnce(emptyDeck)
      .mockResolvedValueOnce(current({}, "GENERATING"));
    const create = vi.spyOn(teacherOccurrenceApi, "createSketchDeck").mockResolvedValue(revision("GENERATING"));
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await fillAndSubmit();

    expect(await screen.findByText("Yêu cầu đang được xử lý. Làm mới trạng thái để kiểm tra.")).toBeTruthy();
    expect(create).toHaveBeenCalledTimes(1);
    expect(create).toHaveBeenCalledWith(
      "occ-1",
      expect.objectContaining({ teacher_confirmed_age_band_ref: "age-36-71-months-v1" }),
      expect.any(String),
    );
  });
});


it.each([0, 7])("blocks deck creation for %i approved activities", async (count) => {
  const create = setup(current({ current_revision: null, steps: [], presentable: false }));
  vi.mocked(teacherOccurrenceApi.getPlan).mockResolvedValue({ data: { ...plan, activities: Array.from({ length: count }, (_, index) => ({ ...plan.activities[0], order: index + 1 })) }, etag: null, notModified: false });
  render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
  const button = await screen.findByRole("button", { name: "Tạo Sketch Deck" }) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  const message = screen.getByText("Giáo án cần có từ 1 đến 6 hoạt động. Hãy thêm hoạt động rồi duyệt lại giáo án.");
  expect(button.getAttribute("aria-describedby")).toBe(message.id);
  fireEvent.submit(button.closest("form")!);
  expect(create).not.toHaveBeenCalled();
});


const pinnedPlan: PlanRevision = { ...plan, lesson_version_ref: { lesson_id: "lesson-1", version_id: "version-1", content_sha256: "c".repeat(64) } };
const lesson = {
  lesson_id: "lesson-1", version_id: "version-1", structured_content_hash: "c".repeat(64),
  content: { drawing_subject: "Tree", topic: "Nature", drawing_steps_text: "1. Head 2. Body 3. Leaves", subject_learning_notes: "Roots\nLeaves" },
} as lessonApi.LessonVersionDetail;

function setupPinned(deck = emptyDeck) {
  const create = setup(deck);
  vi.mocked(teacherOccurrenceApi.getPlan).mockResolvedValue({ data: pinnedPlan, etag: null, notModified: false });
  return create;
}

describe("pinned lesson prefill", () => {
  it("fills the pinned content, leaving placements and review empty", async () => {
    const create = setupPinned();
    const getLesson = vi.spyOn(lessonApi, "getLessonVersion").mockResolvedValue(lesson);
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    expect(await screen.findByText("Đã điền sẵn từ giáo án đã ghim. Hãy rà soát và bổ sung vị trí từng bước.")).toBeTruthy();
    expect(getLesson).toHaveBeenCalledWith(expect.any(String), "lesson-1", "version-1");
    expect((screen.getByLabelText("Chủ đề") as HTMLInputElement).value).toBe("Tree");
    expect((screen.getByLabelText("Thao tác bước 2") as HTMLTextAreaElement).value).toBe("Body");
    expect((screen.getByLabelText("Thao tác bước 4") as HTMLTextAreaElement).value).toBe("");
    expect((screen.getByLabelText("Vị trí bước 1") as HTMLTextAreaElement).value).toBe("");
    expect((screen.getByLabelText("Ghi chú 2") as HTMLTextAreaElement).value).toBe("Leaves");
    expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(false);
    expect(create).not.toHaveBeenCalled();
  });

  it("keeps all excess steps and notes in the eighth card", async () => {
    setupPinned();
    vi.spyOn(lessonApi, "getLessonVersion").mockResolvedValue({ ...lesson, content: { ...lesson.content, drawing_subject: "", drawing_steps_text: Array.from({ length: 10 }, (_, i) => `${i + 1}. Step ${i + 1}`).join("\n"), subject_learning_notes: Array.from({ length: 10 }, (_, i) => `Note ${i + 1}`).join("\n") } });
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await screen.findByText(/Đã điền sẵn từ giáo án/);
    expect((screen.getByLabelText("Chủ đề") as HTMLInputElement).value).toBe("Nature");
    expect((screen.getByLabelText("Thao tác bước 8") as HTMLTextAreaElement).value).toBe("Step 8\nStep 9\nStep 10");
    expect((screen.getByLabelText("Ghi chú 8") as HTMLTextAreaElement).value).toBe("Note 8\nNote 9\nNote 10");
  });

  it("does not overwrite edits made while the lesson loads or on refresh", async () => {
    setupPinned();
    let resolve!: (value: lessonApi.LessonVersionDetail) => void;
    vi.spyOn(lessonApi, "getLessonVersion").mockReturnValue(new Promise((done) => { resolve = done; }));
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    fireEvent.change(await screen.findByLabelText("Chủ đề"), { target: { value: "My topic" } });
    await act(async () => resolve(lesson));
    expect((screen.getByLabelText("Chủ đề") as HTMLInputElement).value).toBe("My topic");
    expect(screen.queryByText(/Đã điền sẵn từ giáo án/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Làm mới trạng thái" }));
    await screen.findByText("Chưa có Sketch Deck cho buổi dạy này.");
    expect((screen.getByLabelText("Chủ đề") as HTMLInputElement).value).toBe("My topic");
  });

  it("uses an existing deck without loading the lesson", async () => {
    setupPinned(current({ presentable: false }));
    const getLesson = vi.spyOn(lessonApi, "getLessonVersion");
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await screen.findByDisplayValue("A tree");
    expect(getLesson).not.toHaveBeenCalled();
    expect(screen.queryByText(/Đã điền sẵn từ giáo án/)).toBeNull();
  });

  it.each([403, 404, 0])("silently leaves the form empty when lesson loading fails (%i)", async (status) => {
    setupPinned();
    vi.spyOn(lessonApi, "getLessonVersion").mockRejectedValue(new BackendApiError("failed", "ERROR", status));
    render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    await screen.findByText("Chưa có Sketch Deck cho buổi dạy này.");
    await act(async () => {});
    expect((screen.getByLabelText("Chủ đề") as HTMLInputElement).value).toBe("");
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.queryByText(/Đã điền sẵn từ giáo án/)).toBeNull();
  });

  it("clears the previous session and ignores its pending lesson", async () => {
    setupPinned();
    let resolve!: (value: lessonApi.LessonVersionDetail) => void;
    vi.spyOn(lessonApi, "getLessonVersion").mockReturnValue(new Promise((done) => { resolve = done; }));
    const { rerender } = render(<TeacherSketchDeckPanel occurrenceId="occ-1" approvedRevisionNo={2} />);
    fireEvent.change(await screen.findByLabelText("Chủ đề"), { target: { value: "Previous session" } });
    vi.mocked(teacherOccurrenceApi.getPlan).mockResolvedValue({ data: { ...plan, occurrence_id: "occ-2" }, etag: null, notModified: false });
    rerender(<TeacherSketchDeckPanel occurrenceId="occ-2" approvedRevisionNo={2} />);
    await screen.findByText("Chưa có Sketch Deck cho buổi dạy này.");
    await act(async () => resolve(lesson));
    expect((screen.getByLabelText("Chủ đề") as HTMLInputElement).value).toBe("");
  });
});
