import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, configure, fireEvent, render as testRender, screen, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { TeacherOccurrencePage } from "../TeacherOccurrencePage";
import { BackendApiError, backendApi } from "../../../../shared/api/backendApi";
import { teacherWorkspaceApi, type TeacherActivity } from "../../../../shared/api/teacherWorkspaceApi";
import { NOT_FOUND_OR_NO_ACCESS, OccurrenceApiError, teacherOccurrenceApi, type JobStatus, type Occurrence, type PlanRevision, type SourceDocument } from "../../../../shared/api/teacherOccurrenceApi";
import { authService } from "../../../school-manager/be1/services/authService";
import type { User } from "firebase/auth";

// The page now renders Router Links; keep the original assertions under a real router context.
function render(ui: ReactNode) {
  return testRender(<MemoryRouter>{ui}</MemoryRouter>);
}

// The full suite runs many jsdom files in parallel: the default 1000 ms findBy/waitFor window is too short for the
// upload and polling flows below, so every async query in this file waits up to 8 s (it returns as soon as the UI is ready).
configure({ asyncUtilTimeout: 8000 });
// The per-test limit (5 s default) must be longer than the async-query window above, or a loaded run fails on the test timeout first.
vi.setConfig({ testTimeout: 30000 });

const HASH = "a".repeat(64);
const PINNED_LESSON = { lesson_id: "lesson-1", version_id: "version-2", content_sha256: "b".repeat(64) };
const occurrenceOf = (id: string, title: string, extra: Partial<Occurrence> = {}): Occurrence => ({
  contract: "LessonOccurrenceV1", occurrence_id: id, class_id: "class-1", title, scheduled_date: "2026-11-25", state: "DRAFT", revision: 1,
  responsible_teacher_ref: "teacher-1", lesson_version_ref: null, lesson_version_no: null, approved_plan: null,
  sample_video: { slot_state: "AVAILABLE", claimed_at: null, run_ref: null }, created_at: "2026-11-20T00:00:00Z", ...extra,
});
const activityOf = (id: string, order: number, title: string, lesson_id = "lesson-1", version_id = "version-2"): TeacherActivity => ({
  lesson_id, version_id, version_no: 2, content_sha256: PINNED_LESSON.content_sha256, lesson_title: "Con mèo", lesson_topic: null,
  lesson_activity_id: id, activity_order: order, title, objective: null, activity_kind: "indoor", materials_text: null,
  preparation_text: null, instructions_text: null, observation_notes: null, safety_notes: null,
});
const documentOf = (id = "doc-1", head = 1): SourceDocument => ({
  contract: "LessonSourceDocumentV1", source_document_id: id, occurrence_id: "occ-1", file_name: "giao-an.pdf", file_extension: ".pdf",
  page_or_slide_count: 3, document_state: "EXTRACTED", head_revision_no: head, job_ref: "job-1", warnings: [], page_coverage: [1, 2, 3], uploaded_at: "2026-11-20T00:00:00Z",
});
const planOf = (revision: number, state: PlanRevision["state"] = "DRAFT", hash = HASH): PlanRevision => ({
  contract: "LessonPlanRevisionV1", occurrence_id: "occ-1", plan_revision_id: `plan-rev-${revision}`, revision_no: revision, state, content_hash: hash, document_revision_ref: null,
  objectives: ["Quan sát"], teacher_direction: "Dẫn dắt trẻ", safety_notes: null, lesson_version_ref: null, lesson_version_no: null,
  activities: [], created_at: "2026-11-20T00:00:00Z", approved_at: null, supersedes_revision_no: null,
});
const planSummary = (plan: PlanRevision) => ({ revision_no: plan.revision_no, state: plan.state, content_hash: plan.content_hash, activity_count: plan.activities.length, created_at: plan.created_at, approved_at: plan.approved_at });
const jobOf = (state: JobStatus["state"]): JobStatus => ({
  job_id: "job-1", target_kind: "LESSON_SOURCE_DOCUMENT", target_ref: "doc-1", job_revision: 1, attempt_number: 1, target_revision: 1, input_hash: HASH, state,
  result_disposition: "accepted", correlation_id: "corr", created_at: "2026-11-20T00:00:00Z", updated_at: "2026-11-20T00:00:00Z", started_at: null,
  completed_at: "2026-11-20T00:00:01Z", progress: { kind: "unknown", value: null, stage_label: null }, failure: null, result_refs: [], poll_after_ms: null,
});
const revisionOf = (no: number, text: string) => ({
  contract: "LessonDocumentRevisionV2" as const, source_document_id: "doc-1", revision_no: no, origin: "EXTRACTION" as const, review_state: "NEEDS_REVIEW" as const,
  base_revision_no: null, extracted_text: text, text_hash: HASH, text_length: text.length, parser: null, warnings: [], page_coverage: [1], created_at: "2026-11-20T00:00:00Z",
});

function mockBackend(options: { occurrences?: Occurrence[]; plans?: PlanRevision[]; documents?: SourceDocument[] } = {}) {
  const occurrences = options.occurrences ?? [occurrenceOf("occ-1", "Buổi vẽ con mèo")];
  const documents = options.documents ?? [];
  const plans = options.plans ?? [];
  vi.spyOn(backendApi, "assignments").mockResolvedValue({ contract: "Be1AdultAssignmentsV1", subject: "s", organization_id: "org-test", assignments: [{ role: "teacher", class_id: "class-1", active: true }] } as never);
  vi.spyOn(backendApi, "classes").mockResolvedValue({ items: [{ contract: "Be1ClassV1", class_id: "class-1", display_name: "Lớp Mầm" }] } as never);
  vi.spyOn(backendApi, "lessons").mockResolvedValue({ items: [
    { contract: "LessonSummaryV1", lesson_id: "lesson-1", title: "Con mèo", topic: "Vẽ", current_version_no: 2, review_state: "APPROVED", visibility: "PRIVATE", activity_count: 1, updated_at: "" },
    { contract: "LessonSummaryV1", lesson_id: "lesson-2", title: "Bản nháp", topic: "Vẽ", current_version_no: 1, review_state: "DRAFT", visibility: "PRIVATE", activity_count: 1, updated_at: "" },
  ] } as never);
  vi.spyOn(backendApi, "teacherLesson").mockResolvedValue({ lesson_id: "lesson-1", current_version: { version_id: "version-2", review_state: "APPROVED", structured_content_hash: "b".repeat(64), content: { title: "Con mèo" } } } as never);
  vi.spyOn(teacherWorkspaceApi, "activities").mockResolvedValue({ contract: "TeacherActivityPageV1", items: [], next_cursor: null });
  const list = vi.spyOn(teacherOccurrenceApi, "list").mockResolvedValue({ contract: "LessonOccurrencePageV1", items: occurrences, next_cursor: null });
  vi.spyOn(teacherOccurrenceApi, "get").mockImplementation(async (id) => ({ data: occurrences.find((item) => item.occurrence_id === id) ?? occurrences[0], etag: '"1"', notModified: false }));
  vi.spyOn(teacherOccurrenceApi, "listDocuments").mockResolvedValue({ contract: "LessonSourceDocumentPageV1", items: documents, next_cursor: null });
  const listPlans = vi.spyOn(teacherOccurrenceApi, "listPlans").mockResolvedValue({ contract: "LessonPlanRevisionPageV1", items: plans.map(planSummary), next_cursor: null });
  vi.spyOn(teacherOccurrenceApi, "getPlan").mockImplementation(async (_id, revision) => ({ data: plans.find((plan) => plan.revision_no === revision) ?? plans[0], etag: `"${revision}"`, notModified: false }));
  vi.spyOn(teacherOccurrenceApi, "getDocument").mockImplementation(async (_o, id) => ({ data: documents.find((item) => item.source_document_id === id) ?? documents[0], etag: '"d"', notModified: false }));
  vi.spyOn(teacherOccurrenceApi, "listDocumentRevisions").mockResolvedValue({ contract: "LessonDocumentRevisionPageV1", items: [{ revision_no: 1, origin: "EXTRACTION", review_state: "NEEDS_REVIEW", text_hash: HASH, text_length: 8, created_at: "" }], next_cursor: null });
  vi.spyOn(teacherOccurrenceApi, "getDocumentRevision").mockImplementation(async (_o, _d, no) => ({ data: revisionOf(no, "Văn bản gốc"), etag: `"r${no}"`, notModified: false }));
  return { list, listPlans };
}

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-test" };
  window.sketch2lifeAuth = { signIn: vi.fn(async () => undefined), getIdToken: vi.fn(async () => "unit-test-id-token") } as never;
  vi.spyOn(authService, "observe").mockImplementation((callback) => {
    callback({ uid: "teacher-test" } as User);
    return () => undefined;
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

/**
 * Wait until the first occurrence is open and its form reset has run. The page clears the file, plan and text fields in
 * the same effect that requests the plans, so a heading alone is not enough: on a slow runner the reset can still follow
 * and drop what the test has already entered.
 */
async function opened() {
  await screen.findByRole("heading", { name: "Buổi vẽ con mèo" });
  await waitFor(() => expect(teacherOccurrenceApi.listPlans).toHaveBeenCalled());
}

describe("TeacherOccurrencePage: list and create", () => {
  it("lists the occurrences of the assigned class and opens the first one", async () => {
    const { list } = mockBackend({ occurrences: [occurrenceOf("occ-1", "Buổi vẽ con mèo"), occurrenceOf("occ-2", "Buổi tô màu")] });
    render(<TeacherOccurrencePage />);
    expect(await screen.findByRole("heading", { name: "Buổi vẽ con mèo" })).toBeTruthy();
    expect(screen.getByText(/Buổi tô màu/)).toBeTruthy();
    expect(list).toHaveBeenCalledWith("class-1", { cursor: undefined });
    fireEvent.click(screen.getByRole("combobox", { name: /Ghim giáo án đã duyệt/ }));
    expect(screen.getByRole("option", { name: "Con mèo" })).toBeTruthy();
    expect(screen.queryByRole("option", { name: "Bản nháp" })).toBeNull();
  });

  it("keeps occurrences and the selected occurrence when re-selecting the already selected class (F-006)", async () => {
    const { list } = mockBackend({ occurrences: [occurrenceOf("occ-1", "Buổi vẽ con mèo"), occurrenceOf("occ-2", "Buổi tô màu")] });
    render(<TeacherOccurrencePage />);
    await opened();
    expect(screen.getByText(/Buổi tô màu/)).toBeTruthy();
    expect(list).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("combobox", { name: /Lớp được phân công/ }));
    fireEvent.click(screen.getByRole("option", { name: "Lớp Mầm" }));

    expect(screen.getByRole("heading", { name: "Buổi vẽ con mèo" })).toBeTruthy();
    expect(screen.getByText(/Buổi tô màu/)).toBeTruthy();
    expect(screen.queryByText("Chưa có buổi dạy trong lớp này.")).toBeNull();
    expect(list).toHaveBeenCalledTimes(1);
  });

  it("shows concise form guidance and keeps creation disabled until a title is entered", async () => {
    mockBackend();
    render(<TeacherOccurrencePage />);
    await opened();

    const title = screen.getByLabelText("Tên buổi dạy") as HTMLInputElement;
    const createButton = screen.getByRole("button", { name: "Tạo buổi dạy" }) as HTMLButtonElement;
    expect(title.placeholder).toBe("Ví dụ: Buổi vẽ lá cây");
    expect(screen.getByText("Tên ngắn giúp dễ nhận biết buổi học.")).toBeTruthy();
    expect(screen.getAllByText("(không bắt buộc)").length).toBeGreaterThan(0);
    expect(createButton.disabled).toBe(true);

    fireEvent.change(title, { target: { value: "Buổi mới" } });
    expect(createButton.disabled).toBe(false);
  });

  it("creates an occurrence with the optional date, the exact lesson pin and one key; a retry after a network failure reuses the key", async () => {
    mockBackend();
    const create = vi.spyOn(teacherOccurrenceApi, "create")
      .mockRejectedValueOnce(new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0))
      .mockResolvedValueOnce(occurrenceOf("occ-9", "Buổi mới", { scheduled_date: "2026-12-01" }));
    render(<TeacherOccurrencePage />);
    await opened();
    fireEvent.change(screen.getByLabelText("Tên buổi dạy"), { target: { value: "Buổi mới" } });
    fireEvent.change(screen.getByLabelText("Ngày dự kiến"), { target: { value: "2026-12-01" } });
    fireEvent.click(screen.getByRole("combobox", { name: /Ghim giáo án đã duyệt/ }));
    fireEvent.click(screen.getByRole("option", { name: "Con mèo" }));
    fireEvent.click(screen.getByRole("button", { name: "Tạo buổi dạy" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Không kết nối được dịch vụ.");
    fireEvent.click(screen.getByRole("button", { name: "Tạo buổi dạy" }));
    expect(await screen.findByRole("heading", { name: "Buổi mới" })).toBeTruthy();
    expect(create).toHaveBeenCalledTimes(2);
    const [firstInput, firstKey] = create.mock.calls[0];
    const [secondInput, secondKey] = create.mock.calls[1];
    expect(firstKey).toBeTruthy();
    expect(secondKey).toBe(firstKey);
    expect(secondInput).toEqual(firstInput);
    expect(firstInput).toEqual({ class_id: "class-1", title: "Buổi mới", scheduled_date: "2026-12-01", lesson_version_ref: { lesson_id: "lesson-1", version_id: "version-2", content_sha256: "b".repeat(64) } });
  });

  it("creates an occurrence without date or pin as null fields", async () => {
    mockBackend();
    const create = vi.spyOn(teacherOccurrenceApi, "create").mockResolvedValue(occurrenceOf("occ-9", "Chỉ tên"));
    render(<TeacherOccurrencePage />);
    await opened();
    fireEvent.change(screen.getByLabelText("Tên buổi dạy"), { target: { value: "Chỉ tên" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo buổi dạy" }));
    await waitFor(() => expect(create).toHaveBeenCalled());
    expect(create.mock.calls[0][0]).toEqual({ class_id: "class-1", title: "Chỉ tên", scheduled_date: null, lesson_version_ref: null });
  });

  it("loads the next page of occurrences with the cursor", async () => {
    const { list } = mockBackend();
    list.mockResolvedValueOnce({ contract: "LessonOccurrencePageV1", items: [occurrenceOf("occ-1", "Buổi một")], next_cursor: "cursor-2" })
      .mockResolvedValueOnce({ contract: "LessonOccurrencePageV1", items: [occurrenceOf("occ-2", "Buổi hai")], next_cursor: null });
    render(<TeacherOccurrencePage />);
    fireEvent.click(await screen.findByRole("button", { name: "Tải thêm buổi dạy" }));
    expect(await screen.findByText("Buổi hai")).toBeTruthy();
    expect(list).toHaveBeenLastCalledWith("class-1", { cursor: "cursor-2" });
    expect(screen.queryByRole("button", { name: "Tải thêm buổi dạy" })).toBeNull();
  });
});

describe("TeacherOccurrencePage: 404 versus 403", () => {
  it("shows the not-found-or-no-access copy for a wrong-scope 404", async () => {
    mockBackend();
    vi.spyOn(teacherOccurrenceApi, "list").mockRejectedValue(new BackendApiError(NOT_FOUND_OR_NO_ACCESS, "RESOURCE_NOT_FOUND", 404, "req-1"));
    render(<TeacherOccurrencePage />);
    expect((await screen.findByRole("alert")).textContent).toContain(NOT_FOUND_OR_NO_ACCESS);
  });

  it("shows occurrence-list diagnostics for a 404 and clears that banner after a successful refresh", async () => {
    const { list } = mockBackend();
    list.mockRejectedValueOnce(new BackendApiError(NOT_FOUND_OR_NO_ACCESS, "RESOURCE_NOT_FOUND", 404, "req-list"));
    render(<TeacherOccurrencePage />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain(NOT_FOUND_OR_NO_ACCESS);
    expect(alert.textContent).toContain("Tải danh sách buổi dạy");
    fireEvent.click(screen.getByText("Thông tin kỹ thuật"));
    expect(alert.textContent).toContain("/v1/lesson-occurrences?limit=25&class_id=class-1");
    expect(alert.textContent).toContain("404");
    expect(alert.textContent).toContain("RESOURCE_NOT_FOUND");
    expect(alert.textContent).toContain("req-list");

    fireEvent.click(screen.getByRole("button", { name: "Làm mới" }));
    await waitFor(() => expect(list).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });

  it("names the document step when a document request returns a 404", async () => {
    mockBackend();
    vi.spyOn(teacherOccurrenceApi, "listDocuments")
      .mockRejectedValueOnce(new BackendApiError(NOT_FOUND_OR_NO_ACCESS, "RESOURCE_NOT_FOUND", 404, "req-doc"));
    render(<TeacherOccurrencePage />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Tải tài liệu");
    fireEvent.click(screen.getByText("Thông tin kỹ thuật"));
    expect(alert.textContent).toContain("/v1/lesson-occurrences/occ-1/documents?limit=25");
    expect(alert.textContent).toContain("req-doc");
  });

  it("shows a distinct permission message for a 403", async () => {
    mockBackend();
    vi.spyOn(teacherOccurrenceApi, "list").mockRejectedValue(new BackendApiError("Tài khoản không được phép thực hiện thao tác này.", "ACTION_NOT_ALLOWED", 403, "req-2"));
    render(<TeacherOccurrencePage />);
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("Tài khoản không được phép thực hiện thao tác này.");
    expect(alert.textContent).not.toContain("không tìm thấy");
  });
});

describe("TeacherOccurrencePage: attach document", () => {
  const pdf = () => new File([new Uint8Array([1, 2, 3])], "giao-an.pdf", { type: "application/pdf", lastModified: 1 });

  it("uploads, attaches under one key set, polls the job and shows the extracted document", async () => {
    const documents: SourceDocument[] = [];
    mockBackend({ documents });
    vi.spyOn(teacherOccurrenceApi, "listDocuments").mockImplementation(async () => ({ contract: "LessonSourceDocumentPageV1", items: [...documents], next_cursor: null }));
    const upload = vi.spyOn(teacherOccurrenceApi, "uploadOccurrenceFile").mockResolvedValue("upl_abc");
    const attach = vi.spyOn(teacherOccurrenceApi, "attachDocument").mockImplementation(async () => {
      documents.push(documentOf());
      return { contract: "LessonSourceDocumentAcceptedV1", source_document_id: "doc-1", document_revision_no: 1, job: { job_id: "job-1", target_kind: "LESSON_SOURCE_DOCUMENT", state: "succeeded" } };
    });
    const getJob = vi.spyOn(teacherOccurrenceApi, "getJob").mockResolvedValue({ data: jobOf("succeeded"), etag: '"1"', notModified: false });
    render(<TeacherOccurrencePage />);
    await opened();
    fireEvent.change(screen.getByLabelText(/Tải PDF, DOCX hoặc PPTX/), { target: { files: [pdf()] } });
    fireEvent.click(screen.getByRole("button", { name: /Tải và đính kèm/ }));
    expect(await screen.findByText("Tài liệu đã được trích xuất.")).toBeTruthy();
    expect(upload.mock.calls[0][1]).toBe("occ-1");
    expect(upload.mock.calls[0][2]?.keys?.create).toBeTruthy();
    expect(upload.mock.calls[0][2]?.keys?.create).not.toBe(upload.mock.calls[0][2]?.keys?.complete);
    expect(attach).toHaveBeenCalledWith("occ-1", "upl_abc", expect.any(String));
    expect(getJob).toHaveBeenCalledWith("job-1", undefined, expect.any(AbortSignal));
    expect(await screen.findAllByText(/giao-an\.pdf/)).not.toHaveLength(0);
    expect(await screen.findByDisplayValue("Văn bản gốc")).toBeTruthy();
    expect(screen.getByText(/Xử lý tài liệu: Đã hoàn tất/)).toBeTruthy();
  });

  it("retries the attach with the same key and does not upload the file again", async () => {
    mockBackend();
    const upload = vi.spyOn(teacherOccurrenceApi, "uploadOccurrenceFile").mockResolvedValue("upl_abc");
    const attach = vi.spyOn(teacherOccurrenceApi, "attachDocument")
      .mockRejectedValueOnce(new BackendApiError("Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.", "PROVIDER_UNAVAILABLE", 503))
      .mockResolvedValueOnce({ contract: "LessonSourceDocumentAcceptedV1", source_document_id: "doc-1", document_revision_no: 1, job: { job_id: "job-1", target_kind: "LESSON_SOURCE_DOCUMENT", state: "succeeded" } });
    vi.spyOn(teacherOccurrenceApi, "getJob").mockResolvedValue({ data: jobOf("succeeded"), etag: '"1"', notModified: false });
    render(<TeacherOccurrencePage />);
    await opened();
    fireEvent.change(screen.getByLabelText(/Tải PDF, DOCX hoặc PPTX/), { target: { files: [pdf()] } });
    fireEvent.click(screen.getByRole("button", { name: /Tải và đính kèm/ }));
    expect((await screen.findByRole("alert")).textContent).toContain("Dịch vụ tạm thời chưa sẵn sàng");
    fireEvent.click(screen.getByRole("button", { name: /Tải và đính kèm/ }));
    await waitFor(() => expect(attach).toHaveBeenCalledTimes(2));
    expect(attach.mock.calls[1][2]).toBe(attach.mock.calls[0][2]);
    expect(upload).toHaveBeenCalledTimes(1);
  });

  it("aborts an interrupted upload session through the keyed abort", async () => {
    mockBackend();
    vi.spyOn(teacherOccurrenceApi, "uploadOccurrenceFile").mockImplementation(async (_file, _id, options) => {
      options?.onSession?.({ upload_id: "upl-9" } as never);
      throw new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0);
    });
    const abort = vi.spyOn(teacherOccurrenceApi, "abortOpenUpload").mockResolvedValue({ state: "ABORTED" } as never);
    render(<TeacherOccurrencePage />);
    await opened();
    fireEvent.change(screen.getByLabelText(/Tải PDF, DOCX hoặc PPTX/), { target: { files: [pdf()] } });
    fireEvent.click(screen.getByRole("button", { name: /Tải và đính kèm/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Hủy phiên tải lên" }));
    await waitFor(() => expect(abort).toHaveBeenCalledWith("upl-9", expect.any(String)));
    expect(await screen.findByText("Đã hủy phiên tải lên.")).toBeTruthy();
  });

  it("stops polling the job when the screen unmounts", async () => {
    mockBackend();
    vi.spyOn(teacherOccurrenceApi, "uploadOccurrenceFile").mockResolvedValue("upl_abc");
    vi.spyOn(teacherOccurrenceApi, "attachDocument").mockResolvedValue({ contract: "LessonSourceDocumentAcceptedV1", source_document_id: "doc-1", document_revision_no: 1, job: { job_id: "job-1", target_kind: "LESSON_SOURCE_DOCUMENT", state: "succeeded" } });
    const getJob = vi.spyOn(teacherOccurrenceApi, "getJob").mockResolvedValue({ data: { ...jobOf("running"), completed_at: null }, etag: '"1"', notModified: false });
    const view = render(<TeacherOccurrencePage />);
    await opened();
    fireEvent.change(screen.getByLabelText(/Tải PDF, DOCX hoặc PPTX/), { target: { files: [pdf()] } });
    fireEvent.click(screen.getByRole("button", { name: /Tải và đính kèm/ }));
    await waitFor(() => expect(getJob).toHaveBeenCalled());
    const signal = getJob.mock.calls[0][2] as AbortSignal;
    expect(signal.aborted).toBe(false);
    view.unmount();
    expect(signal.aborted).toBe(true);
  });
});

/**
 * Render and wait until the opened occurrence has finished its form reset. The page clears the plan form in the same
 * effect that requests the plans, so typing is safe only after that request was made; a form that is merely visible
 * can still be cleared on a slow runner.
 */
async function openPlanForm(listPlans: ReturnType<typeof mockBackend>["listPlans"]) {
  render(<TeacherOccurrencePage />);
  await waitFor(() => expect(listPlans).toHaveBeenCalled());
  return screen.findByLabelText(/Mục tiêu học tập/);
}

describe("TeacherOccurrencePage: plan form limits and field errors", () => {
  it("blocks more than 12 objectives, over-long objectives and shows why, without sending", async () => {
    const { listPlans } = mockBackend();
    const create = vi.spyOn(teacherOccurrenceApi, "createPlan");
    const objectives = await openPlanForm(listPlans);
    fireEvent.change(screen.getByLabelText(/Hướng dẫn cho giáo viên/), { target: { value: "Dẫn dắt" } });
    fireEvent.change(objectives, { target: { value: Array.from({ length: 13 }, (_, index) => `Mục ${index + 1}`).join("\n") } });
    expect(screen.getByText(/Tối đa 12 mục tiêu \(đang có 13\)/)).toBeTruthy();
    const save = screen.getByRole("button", { name: "Lưu bản kế hoạch" }) as HTMLButtonElement;
    expect(save.disabled).toBe(true);
    fireEvent.change(objectives, { target: { value: "x".repeat(1001) } });
    expect(screen.getByText(/Mỗi mục tiêu tối đa 1000 ký tự/)).toBeTruthy();
    expect(save.disabled).toBe(true);
    fireEvent.change(objectives, { target: { value: "x".repeat(1000) } });
    expect(save.disabled).toBe(false);
    expect((screen.getByLabelText(/Hướng dẫn cho giáo viên/) as HTMLTextAreaElement).maxLength).toBe(2000);
    expect((screen.getByLabelText(/Ghi chú an toàn/) as HTMLTextAreaElement).maxLength).toBe(2000);
    expect(create).not.toHaveBeenCalled();
  });

  it("renders the field errors of a 400 as safe Vietnamese lines", async () => {
    const { listPlans } = mockBackend();
    vi.spyOn(teacherOccurrenceApi, "createPlan").mockRejectedValue(new OccurrenceApiError("Yêu cầu không hợp lệ.", "INVALID_REQUEST", 400, "req-7", [
      { field: "objectives[1]", code: "INVALID_FORMAT" }, { field: "activities[0].kind", code: "NOT_SUPPORTED" },
    ]));
    fireEvent.change(await openPlanForm(listPlans), { target: { value: "A\nB" } });
    fireEvent.change(screen.getByLabelText(/Hướng dẫn cho giáo viên/), { target: { value: "Dẫn dắt" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu bản kế hoạch" }));
    expect(await screen.findByText("Mục tiêu học tập (dòng 2): không hợp lệ.")).toBeTruthy();
    expect(screen.getByText("Hoạt động: chưa được hỗ trợ.")).toBeTruthy();
    expect(screen.getByText("Yêu cầu không hợp lệ.")).toBeTruthy();
  });
});

describe("TeacherOccurrencePage: upload abort", () => {
  const pdf = () => new File([new Uint8Array([1, 2, 3])], "giao-an.pdf", { type: "application/pdf", lastModified: 1 });
  async function failedUpload() {
    mockBackend();
    const upload = vi.spyOn(teacherOccurrenceApi, "uploadOccurrenceFile").mockImplementation(async (_file, _id, options) => {
      options?.onSession?.({ upload_id: "upl-9" } as never);
      throw new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0);
    });
    render(<TeacherOccurrencePage />);
    await opened();
    // A later load step can re-initialise the form on a slow runner: repeat the input until the upload really starts.
    await waitFor(() => {
      fireEvent.change(screen.getByLabelText(/Tải PDF, DOCX hoặc PPTX/), { target: { files: [pdf()] } });
      fireEvent.click(screen.getByRole("button", { name: /Tải và đính kèm/ }));
      expect(upload).toHaveBeenCalled();
    });
    return screen.findByRole("button", { name: "Hủy phiên tải lên" });
  }

  it("keeps the session and the abort key after a stale answer, then clears on success", async () => {
    const button = await failedUpload();
    const abort = vi.spyOn(teacherOccurrenceApi, "abortOpenUpload")
      .mockRejectedValueOnce(new BackendApiError("Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", "STALE_REVISION", 409, "req-8"))
      .mockResolvedValueOnce({ state: "ABORTED" } as never);
    fireEvent.click(button);
    expect((await screen.findByRole("alert")).textContent).toContain("Thông tin đã thay đổi");
    fireEvent.click(await screen.findByRole("button", { name: "Hủy phiên tải lên" }));
    expect(await screen.findByText("Đã hủy phiên tải lên.")).toBeTruthy();
    expect(abort).toHaveBeenCalledTimes(2);
    expect(abort.mock.calls[1]).toEqual(["upl-9", abort.mock.calls[0][1]]);
    expect(screen.queryByRole("button", { name: "Hủy phiên tải lên" })).toBeNull();
  });

  it("ends the session on a final refusal such as an expired session", async () => {
    const button = await failedUpload();
    vi.spyOn(teacherOccurrenceApi, "abortOpenUpload").mockRejectedValue(new BackendApiError("Tài nguyên không còn khả dụng.", "UPLOAD_SESSION_EXPIRED", 410, "req-9"));
    fireEvent.click(button);
    expect((await screen.findByRole("alert")).textContent).toContain("không còn khả dụng");
    await waitFor(() => expect(screen.queryByRole("button", { name: "Hủy phiên tải lên" })).toBeNull());
  });
});

describe("TeacherOccurrencePage: switching context", () => {
  it("drops the plan form and the document ref of the previous occurrence", async () => {
    const { listPlans } = mockBackend({ occurrences: [occurrenceOf("occ-1", "Buổi A"), occurrenceOf("occ-2", "Buổi B")], documents: [documentOf("doc-1", 1)] });
    fireEvent.change(await openPlanForm(listPlans), { target: { value: "Mục tiêu của A" } });
    fireEvent.change(screen.getByLabelText(/Hướng dẫn cho giáo viên/), { target: { value: "Hướng dẫn A" } });
    await screen.findByDisplayValue("Văn bản gốc");
    fireEvent.click(screen.getByRole("button", { name: /Buổi B/ }));
    await screen.findByRole("heading", { name: "Buổi B" });
    await waitFor(() => expect((screen.getByLabelText(/Mục tiêu học tập/) as HTMLTextAreaElement).value).toBe(""));
    expect((screen.getByLabelText(/Hướng dẫn cho giáo viên/) as HTMLTextAreaElement).value).toBe("");
  });

  it("ignores an occurrence page that arrives after the Teacher switched class", async () => {
    mockBackend();
    vi.spyOn(backendApi, "assignments").mockResolvedValue({ contract: "Be1AdultAssignmentsV1", subject: "s", organization_id: "org-test", assignments: [{ role: "teacher", class_id: "class-1", active: true }, { role: "teacher", class_id: "class-2", active: true }] } as never);
    vi.spyOn(backendApi, "classes").mockResolvedValue({ items: [{ contract: "Be1ClassV1", class_id: "class-1", display_name: "Lớp Mầm" }, { contract: "Be1ClassV1", class_id: "class-2", display_name: "Lớp Chồi" }] } as never);
    let releaseFirst: (page: Awaited<ReturnType<typeof teacherOccurrenceApi.list>>) => void = () => undefined;
    const list = vi.spyOn(teacherOccurrenceApi, "list").mockImplementation((classId) => classId === "class-1"
      ? new Promise((resolve) => { releaseFirst = resolve; })
      : Promise.resolve({ contract: "LessonOccurrencePageV1", items: [occurrenceOf("occ-b", "Buổi lớp Chồi", { class_id: "class-2" })], next_cursor: null }));
    render(<TeacherOccurrencePage />);
    await waitFor(() => expect(list).toHaveBeenCalledWith("class-1", expect.anything()));
    fireEvent.click(screen.getByRole("combobox", { name: "Lớp được phân công" }));
    fireEvent.click(await screen.findByRole("option", { name: "Lớp Chồi" }));
    expect(await screen.findByRole("heading", { name: "Buổi lớp Chồi" })).toBeTruthy();
    releaseFirst({ contract: "LessonOccurrencePageV1", items: [occurrenceOf("occ-a", "Buổi lớp Mầm")], next_cursor: "stale-cursor" });
    await new Promise((resolve) => setTimeout(resolve, 20));
    expect(screen.queryByText("Buổi lớp Mầm")).toBeNull();
    expect(screen.queryByRole("button", { name: "Tải thêm buổi dạy" })).toBeNull();
  });

  it("clears the old class and does not request it after the signed-in account changes", async () => {
    let activeUid = "teacher-a";
    let authListener: ((user: User | null) => void) | undefined;
    vi.spyOn(authService, "observe").mockImplementation((callback) => {
      authListener = callback;
      callback({ uid: activeUid } as User);
      return () => undefined;
    });
    mockBackend();
    vi.mocked(backendApi.assignments).mockImplementation(async () => ({
      contract: "Be1AdultAssignmentsV1",
      subject: activeUid,
      organization_id: "org-test",
      assignments: [{ role: "teacher", class_id: activeUid === "teacher-a" ? "class-1" : "class-2", active: true }],
    } as never));
    vi.mocked(backendApi.classes).mockImplementation(async () => ({
      items: [{
        contract: "Be1ClassV1",
        class_id: activeUid === "teacher-a" ? "class-1" : "class-2",
        display_name: activeUid === "teacher-a" ? "Lớp Mầm" : "Lớp Lá",
      }],
    } as never));
    const list = vi.mocked(teacherOccurrenceApi.list).mockImplementation(async (classId) => ({
      contract: "LessonOccurrencePageV1",
      items: [occurrenceOf(`occ-${classId}`, `Buổi ${classId}`, { class_id: classId })],
      next_cursor: null,
    }));

    render(<TeacherOccurrencePage />);
    await screen.findByRole("heading", { name: "Buổi class-1" });
    const callCountBeforeSwitch = list.mock.calls.length;
    activeUid = "teacher-b";
    act(() => authListener?.({ uid: activeUid } as User));

    await screen.findByRole("heading", { name: "Buổi class-2" });
    const callsAfterSwitch = list.mock.calls.slice(callCountBeforeSwitch).map(([classId]) => classId);
    expect(callsAfterSwitch).toEqual(["class-2"]);
    expect(screen.getByRole("combobox", { name: "Lớp được phân công" }).textContent).toContain("Lớp Lá");
    expect(screen.queryByRole("heading", { name: "Buổi class-1" })).toBeNull();
  });
});

describe("TeacherOccurrencePage: document revisions", () => {
  it("saves an edit as a new revision from the current head with one key", async () => {
    mockBackend({ documents: [documentOf("doc-1", 1)] });
    const edit = vi.spyOn(teacherOccurrenceApi, "editDocumentRevision").mockResolvedValue({ ...revisionOf(2, "Đã sửa"), origin: "TEACHER_EDIT" });
    render(<TeacherOccurrencePage />);
    const text = await screen.findByDisplayValue("Văn bản gốc");
    fireEvent.change(text, { target: { value: "Đã sửa" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thành bản mới" }));
    await waitFor(() => expect(edit).toHaveBeenCalledWith("occ-1", "doc-1", "Đã sửa", 1, expect.any(String)));
    expect(await screen.findByText("Đã lưu bản văn bản 2.")).toBeTruthy();
  });

  it("reloads the head after a stale revision and does not hide the safe message", async () => {
    mockBackend({ documents: [documentOf("doc-1", 1)] });
    vi.spyOn(teacherOccurrenceApi, "editDocumentRevision").mockRejectedValue(new BackendApiError("Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", "STALE_REVISION", 409, "req-3"));
    const listDocuments = vi.mocked(teacherOccurrenceApi.listDocuments);
    render(<TeacherOccurrencePage />);
    fireEvent.change(await screen.findByDisplayValue("Văn bản gốc"), { target: { value: "Sửa muộn" } });
    const before = listDocuments.mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "Lưu thành bản mới" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Thông tin đã thay đổi");
    await waitFor(() => expect(listDocuments.mock.calls.length).toBeGreaterThan(before));
    expect(await screen.findByText(/Đã tải lại bản mới nhất/)).toBeTruthy();
  });
});

describe("TeacherOccurrencePage: pinned plan activities", () => {
  it("sends every activity from the pinned version in the first plan", async () => {
    const { listPlans } = mockBackend({ occurrences: [occurrenceOf("occ-1", "Buổi vẽ", { lesson_version_ref: PINNED_LESSON })] });
    vi.mocked(teacherWorkspaceApi.activities).mockResolvedValue({
      contract: "TeacherActivityPageV1",
      items: [activityOf("activity-1", 1, "Hoạt động A"), activityOf("activity-2", 2, "Hoạt động B")],
      next_cursor: null,
    });
    const create = vi.spyOn(teacherOccurrenceApi, "createPlan").mockResolvedValue(planOf(1));
    const objectives = await openPlanForm(listPlans);
    const first = await screen.findByRole("checkbox", { name: /Hoạt động A/ }) as HTMLInputElement;
    const second = screen.getByRole("checkbox", { name: /Hoạt động B/ }) as HTMLInputElement;
    await waitFor(() => expect(first.checked && second.checked).toBe(true));

    fireEvent.change(objectives, { target: { value: "Quan sát" } });
    fireEvent.change(screen.getByLabelText(/Hướng dẫn cho giáo viên/), { target: { value: "Dẫn dắt" } });
    const save = screen.getByRole("button", { name: "Lưu bản kế hoạch" }) as HTMLButtonElement;
    fireEvent.click(save);
    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(save.disabled).toBe(false));
    expect(create.mock.calls[0][1].activities).toEqual([
      { kind: "LESSON", lesson_activity_id: "activity-1" },
      { kind: "LESSON", lesson_activity_id: "activity-2" },
    ]);
    expect(first.checked && second.checked).toBe(true);

    fireEvent.click(save);
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][1].activities).toEqual(create.mock.calls[0][1].activities);
  });

  it("does not send a pinned activity the Teacher unticks", async () => {
    const { listPlans } = mockBackend({ occurrences: [occurrenceOf("occ-1", "Buổi vẽ", { lesson_version_ref: PINNED_LESSON })] });
    vi.mocked(teacherWorkspaceApi.activities).mockResolvedValue({
      contract: "TeacherActivityPageV1",
      items: [activityOf("activity-1", 1, "Hoạt động A"), activityOf("activity-2", 2, "Hoạt động B")],
      next_cursor: null,
    });
    const create = vi.spyOn(teacherOccurrenceApi, "createPlan").mockResolvedValue(planOf(1));
    const objectives = await openPlanForm(listPlans);
    const first = await screen.findByRole("checkbox", { name: /Hoạt động A/ }) as HTMLInputElement;
    const second = screen.getByRole("checkbox", { name: /Hoạt động B/ }) as HTMLInputElement;
    await waitFor(() => expect(first.checked && second.checked).toBe(true));
    fireEvent.click(second);

    fireEvent.change(objectives, { target: { value: "Quan sát" } });
    fireEvent.change(screen.getByLabelText(/Hướng dẫn cho giáo viên/), { target: { value: "Dẫn dắt" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu bản kế hoạch" }));
    await waitFor(() => expect(create).toHaveBeenCalled());
    expect(create.mock.calls[0][1].activities).toEqual([{ kind: "LESSON", lesson_activity_id: "activity-1" }]);
    expect(first.checked).toBe(true);
    expect(second.checked).toBe(false);
  });

  it("keeps a deliberately empty selection empty after save and on the next save", async () => {
    const { listPlans } = mockBackend({ occurrences: [occurrenceOf("occ-1", "Buổi vẽ", { lesson_version_ref: PINNED_LESSON })] });
    vi.mocked(teacherWorkspaceApi.activities).mockResolvedValue({
      contract: "TeacherActivityPageV1",
      items: [activityOf("activity-1", 1, "Hoạt động A"), activityOf("activity-2", 2, "Hoạt động B")],
      next_cursor: null,
    });
    const create = vi.spyOn(teacherOccurrenceApi, "createPlan").mockResolvedValue(planOf(1));
    const objectives = await openPlanForm(listPlans);
    const first = await screen.findByRole("checkbox", { name: /Hoạt động A/ }) as HTMLInputElement;
    const second = screen.getByRole("checkbox", { name: /Hoạt động B/ }) as HTMLInputElement;
    await waitFor(() => expect(first.checked && second.checked).toBe(true));
    fireEvent.click(first);
    fireEvent.click(second);

    fireEvent.change(objectives, { target: { value: "Quan sát" } });
    fireEvent.change(screen.getByLabelText(/Hướng dẫn cho giáo viên/), { target: { value: "Dẫn dắt" } });
    const save = screen.getByRole("button", { name: "Lưu bản kế hoạch" }) as HTMLButtonElement;
    fireEvent.click(save);
    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(save.disabled).toBe(false));
    expect(create.mock.calls[0][1].activities).toEqual([]);
    expect(first.checked || second.checked).toBe(false);

    fireEvent.click(save);
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][1].activities).toEqual([]);
  });

  it("resets selection when switching to another occurrence", async () => {
    const { listPlans } = mockBackend({ occurrences: [
      occurrenceOf("occ-1", "Buổi vẽ", { lesson_version_ref: PINNED_LESSON }),
      occurrenceOf("occ-2", "Buổi vẽ lần hai", { lesson_version_ref: PINNED_LESSON }),
    ] });
    vi.mocked(teacherWorkspaceApi.activities).mockResolvedValue({
      contract: "TeacherActivityPageV1",
      items: [activityOf("activity-1", 1, "Hoạt động A"), activityOf("activity-2", 2, "Hoạt động B")],
      next_cursor: null,
    });
    await openPlanForm(listPlans);
    const second = await screen.findByRole("checkbox", { name: /Hoạt động B/ }) as HTMLInputElement;
    await waitFor(() => expect(second.checked).toBe(true));
    fireEvent.click(second);
    expect(second.checked).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: /Buổi vẽ lần hai/ }));
    const resetSecond = await screen.findByRole("checkbox", { name: /Hoạt động B/ }) as HTMLInputElement;
    await waitFor(() => expect(resetSecond.checked).toBe(true));
  });

  it("still saves the current selection when pinned activities fail to load", async () => {
    const { listPlans } = mockBackend({ occurrences: [occurrenceOf("occ-1", "Buổi vẽ", { lesson_version_ref: PINNED_LESSON })] });
    vi.mocked(teacherWorkspaceApi.activities).mockRejectedValueOnce(new Error("offline"));
    const create = vi.spyOn(teacherOccurrenceApi, "createPlan").mockResolvedValue(planOf(1));
    const objectives = await openPlanForm(listPlans);
    expect(await screen.findByText("Không thể tải hoạt động từ giáo án đã ghim. Có thể lưu kế hoạch với lựa chọn hiện tại.")).toBeTruthy();
    fireEvent.change(objectives, { target: { value: "Quan sát" } });
    fireEvent.change(screen.getByLabelText(/Hướng dẫn cho giáo viên/), { target: { value: "Dẫn dắt" } });
    const save = screen.getByRole("button", { name: "Lưu bản kế hoạch" }) as HTMLButtonElement;
    expect(save.disabled).toBe(false);
    fireEvent.click(save);
    await waitFor(() => expect(create).toHaveBeenCalled());
    expect(create.mock.calls[0][1].activities).toEqual([]);
  });
});

describe("TeacherOccurrencePage: plan revisions", () => {
  it("creates a plan revision from the selected one, keeping its lesson activities, against the current head", async () => {
    const head = { ...planOf(2), activities: [
      { order: 1, kind: "LESSON" as const, lesson_activity_id: "act-1", title: "Dạo vườn", description: null, snapshot_hash: HASH, checklist_required: false, checklist_version: null, confirmed: true },
      { order: 2, kind: "LESSON" as const, lesson_activity_id: "retired-act", title: "Hoạt động cũ", description: null, snapshot_hash: HASH, checklist_required: false, checklist_version: null, confirmed: true },
    ] };
    mockBackend({
      occurrences: [occurrenceOf("occ-1", "Buổi vẽ con mèo", { lesson_version_ref: PINNED_LESSON })],
      plans: [head, planOf(1)],
    });
    vi.mocked(teacherWorkspaceApi.activities).mockResolvedValue({
      contract: "TeacherActivityPageV1", items: [activityOf("act-1", 1, "Dạo vườn"), activityOf("act-2", 2, "Hoạt động mới")], next_cursor: null,
    });
    const create = vi.spyOn(teacherOccurrenceApi, "createPlan").mockResolvedValue(planOf(3));
    render(<TeacherOccurrencePage />);
    fireEvent.click(await screen.findByRole("button", { name: /Phiên bản 2 · Bản nháp/ }));
    fireEvent.click(await screen.findByRole("button", { name: "Tạo bản mới từ bản này" }));
    const copiedActivity = await screen.findByRole("checkbox", { name: /Dạo vườn/ }) as HTMLInputElement;
    const newActivity = screen.getByRole("checkbox", { name: /Hoạt động mới/ }) as HTMLInputElement;
    expect(copiedActivity.checked).toBe(true);
    expect(newActivity.checked).toBe(false);
    expect(screen.getByText(/Giữ nguyên 1 hoạt động không có trong danh sách hiện tại từ bản kế hoạch trước/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText(/Hướng dẫn cho giáo viên/), { target: { value: "Dẫn dắt mới" } });
    const save = screen.getByRole("button", { name: "Lưu bản kế hoạch" }) as HTMLButtonElement;
    fireEvent.click(save);
    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(save.disabled).toBe(false));
    expect(create).toHaveBeenCalledWith("occ-1", {
      expected_head_revision_no: 2, document_revision_ref: null, objectives: ["Quan sát"], teacher_direction: "Dẫn dắt mới", safety_notes: null,
      activities: [{ kind: "LESSON", lesson_activity_id: "act-1" }, { kind: "LESSON", lesson_activity_id: "retired-act" }],
    }, expect.any(String));
    expect(copiedActivity.checked).toBe(true);
    expect(newActivity.checked).toBe(false);

    fireEvent.click(save);
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
    expect(create.mock.calls[1][1].activities).toEqual([
      { kind: "LESSON", lesson_activity_id: "act-1" },
      { kind: "LESSON", lesson_activity_id: "retired-act" },
    ]);
  });

  it("views a revision and confirms only the latest draft with its content hash", async () => {
    const confirm = vi.spyOn(teacherOccurrenceApi, "confirmPlan");
    mockBackend({ plans: [planOf(2, "DRAFT", "c".repeat(64)), planOf(1, "SUPERSEDED", "d".repeat(64))] });
    confirm.mockResolvedValue({ ...planOf(2, "APPROVED", "c".repeat(64)), approved_at: "2026-11-20T01:00:00Z" });
    render(<TeacherOccurrencePage />);
    fireEvent.click(await screen.findByRole("button", { name: /Phiên bản 1 · Đã thay thế/ }));
    expect((await screen.findByRole("button", { name: "Xác nhận bản nháp mới nhất" }) as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: /Phiên bản 2 · Bản nháp/ }));
    await waitFor(() => expect((screen.getByRole("button", { name: "Xác nhận bản nháp mới nhất" }) as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận bản nháp mới nhất" }));
    await waitFor(() => expect(confirm).toHaveBeenCalledWith("occ-1", 2, "c".repeat(64), expect.any(String)));
    expect(await screen.findByText("Đã xác nhận bản kế hoạch.")).toBeTruthy();
  });

  it("handles a stale plan revision: shows the safe message, reloads the plans and selects the new head", async () => {
    const stale = planOf(1, "DRAFT", "e".repeat(64));
    const { listPlans } = mockBackend({ plans: [stale] });
    vi.spyOn(teacherOccurrenceApi, "confirmPlan").mockRejectedValue(new BackendApiError("Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", "STALE_REVISION", 409, "req-4"));
    render(<TeacherOccurrencePage />);
    fireEvent.click(await screen.findByRole("button", { name: /Phiên bản 1 · Bản nháp/ }));
    await waitFor(() => expect((screen.getByRole("button", { name: "Xác nhận bản nháp mới nhất" }) as HTMLButtonElement).disabled).toBe(false));
    const newHead = planOf(2, "DRAFT", "f".repeat(64));
    listPlans.mockResolvedValue({ contract: "LessonPlanRevisionPageV1", items: [planSummary(newHead), planSummary(stale)], next_cursor: null });
    vi.mocked(teacherOccurrenceApi.getPlan).mockImplementation(async (_id, revision) => ({ data: revision === 2 ? newHead : stale, etag: `"${revision}"`, notModified: false }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận bản nháp mới nhất" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Thông tin đã thay đổi");
    expect(await screen.findByRole("heading", { name: "Phiên bản 2 · Bản nháp" })).toBeTruthy();
    expect(screen.getByText(/Đã tải lại bản mới nhất/)).toBeTruthy();
  });

  it("does not invent a safety checklist: confirm is blocked while a checklist is required but not configured", async () => {
    const custom = { ...planOf(1), activities: [{ order: 1, kind: "CUSTOM" as const, lesson_activity_id: null, title: "Tự thêm", description: "x", snapshot_hash: null, checklist_required: true, checklist_version: null, confirmed: false }] };
    mockBackend({ plans: [custom] });
    const confirm = vi.spyOn(teacherOccurrenceApi, "confirmPlan");
    render(<TeacherOccurrencePage />);
    fireEvent.click(await screen.findByRole("button", { name: /Phiên bản 1 · Bản nháp/ }));
    expect(await screen.findByText(/danh mục kiểm tra an toàn nhưng danh mục chưa được cấu hình/)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Xác nhận bản nháp mới nhất" }) as HTMLButtonElement).disabled).toBe(true);
    expect(confirm).not.toHaveBeenCalled();
    expect(screen.queryByText("CUSTOM")).toBeNull();
  });
});
