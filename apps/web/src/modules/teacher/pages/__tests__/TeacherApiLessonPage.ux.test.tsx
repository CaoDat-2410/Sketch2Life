import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { PortalSessionProvider } from "../../../../shared/auth/PortalSessionContext";
import { BackendApiError, backendApi, type AccessGrant, type TeacherLessonDetail } from "../../../../shared/api/backendApi";
import type { PublicLessonHit } from "../../../../shared/api/teacherLessonLibraryApi";
import { TeacherApiLessonPage } from "../TeacherApiLessonPage";

const mocks = vi.hoisted(() => ({
  searchPublicLessons: vi.fn(),
  remixLesson: vi.fn(),
  listLessonVersions: vi.fn(),
  getLessonVersion: vi.fn(),
  createPrivateShare: vi.fn(),
  revokeAccessGrant: vi.fn(),
}));

vi.mock("../../../../shared/api/teacherLessonLibraryApi", async () => ({
  ...(await vi.importActual("../../../../shared/api/teacherLessonLibraryApi")),
  searchPublicLessons: mocks.searchPublicLessons,
  remixLesson: mocks.remixLesson,
  listLessonVersions: mocks.listLessonVersions,
  getLessonVersion: mocks.getLessonVersion,
}));

vi.mock("../../../../shared/api/lessonSharingApi", async () => ({
  ...(await vi.importActual("../../../../shared/api/lessonSharingApi")),
  createPrivateShare: mocks.createPrivateShare,
  revokeAccessGrant: mocks.revokeAccessGrant,
}));

function makeDetail(lessonId: string, title: string, overrides?: {
  revision?: number;
  materials_text?: string;
  preparation_text?: string;
  observation_notes?: string;
  target_age_band_ref?: string;
  target_age_band_version?: number;
}): TeacherLessonDetail {
  const revision = overrides?.revision ?? 1;
  return {
    contract: "LessonDetailV1",
    lesson_id: lessonId,
    organization_id: "org-test",
    owner_kind: "ORGANIZATION",
    created_by: "teacher-1",
    state: "ACTIVE",
    visibility: "PRIVATE",
    moderation_state: "VISIBLE",
    current_version: {
      contract: "LessonVersionV1",
      lesson_id: lessonId,
      version_id: `${lessonId}-v${revision}`,
      version_no: revision,
      review_state: "DRAFT",
      structured_content_hash: "a".repeat(64),
      source_document_revision_id: null,
      authored_principal_ref: "teacher-1",
      created_at: "2026-11-20T00:00:00Z",
      content: {
        locale: "vi-VN",
        title,
        topic: "Thiên nhiên",
        target_age_band_ref: overrides?.target_age_band_ref ?? "age-36-71-months-v1",
        target_age_band_version: overrides?.target_age_band_version ?? 1,
        objectives: ["Quan sát màu sắc"],
        drawing_subject: "Cây xanh",
        drawing_steps_text: "Vẽ thân cây rồi vẽ tán lá",
        subject_learning_notes: "Giải thích về lá xanh",
        script_direction: null,
        script_following_allowed: false,
        activities: [{
          title: "Quan sát sân trường",
          objective: "Nhận biết cây xanh",
          materials_text: overrides?.materials_text ?? "",
          preparation_text: overrides?.preparation_text ?? "",
          instructions_text: "Đi quanh sân trường",
          observation_notes: overrides?.observation_notes ?? "",
          safety_notes: "Giữ khoảng cách an toàn",
          activity_kind: "outdoor",
        }],
      },
    },
    revision,
    created_at: "2026-11-20T00:00:00Z",
    updated_at: "2026-11-20T00:00:00Z",
  } as unknown as TeacherLessonDetail;
}

function makeGrant(lessonId: string): AccessGrant {
  return {
    contract: "LessonAccessGrantV1",
    access_grant_id: "grant-1",
    lesson_id: lessonId,
    version_id: `${lessonId}-v1`,
    audience_kind: "ORGANIZATION",
    audience_ref: "org-test",
    capability: "VIEW",
    state: "ACTIVE",
    granted_by: "teacher-1",
    approved_by: null,
    approved_at: null,
    expires_at: null,
    revoked_at: null,
    revision: 1,
  };
}

function makePublicHit(): PublicLessonHit {
  return {
    contract: "PublicLessonHitV1",
    lesson_id: "public-1",
    version_id: "public-v1",
    structured_content_hash: "c".repeat(64),
    title: "Bài mẫu công khai",
    topic: "Động vật",
    target_age_band_ref: "age-72-107-months-v1",
    target_age_band_version: 1,
    activity_count: 1,
    updated_at: "2026-11-20T00:00:00Z",
  };
}

function beforeUnloadEvent() {
  const event = new Event("beforeunload", { cancelable: true }) as BeforeUnloadEvent;
  Object.defineProperty(event, "returnValue", { configurable: true, writable: true, value: "unchanged" });
  return event;
}

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "test-token") } as never;
  vi.spyOn(backendApi, "assignments").mockResolvedValue({
    assignments: [{ role: "teacher", active: true }],
  } as never);
  vi.spyOn(backendApi, "lessons").mockResolvedValue({
    contract: "LessonPageV1",
    items: [
      {
        contract: "LessonSummaryV1",
        lesson_id: "lesson-1",
        title: "Giáo án một",
        topic: "Thiên nhiên",
        current_version_no: 1,
        review_state: "DRAFT",
        visibility: "PRIVATE",
        activity_count: 1,
        updated_at: "2026-11-20T00:00:00Z",
      },
      {
        contract: "LessonSummaryV1",
        lesson_id: "lesson-2",
        title: "Giáo án hai",
        topic: "Động vật",
        current_version_no: 1,
        review_state: "DRAFT",
        visibility: "PRIVATE",
        activity_count: 1,
        updated_at: "2026-11-20T00:00:00Z",
      },
    ],
    next_cursor: null,
  } as never);
  mocks.listLessonVersions.mockResolvedValue({
    contract: "LessonVersionsPageV1",
    lesson_id: "lesson-1",
    items: [{
      contract: "LessonVersionV1",
      version_id: "lesson-1-v1",
      version_no: 1,
      review_state: "DRAFT",
      structured_content_hash: "a".repeat(64),
      source_document_revision_id: null,
      authored_principal_ref: "teacher-1",
      created_at: "2026-11-20T00:00:00Z",
    }],
    next_cursor: null,
  });
  mocks.searchPublicLessons.mockResolvedValue({
    contract: "PublicLessonSearchPageV1",
    items: [makePublicHit()],
    next_cursor: null,
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.clearAllMocks();
  delete window.sketch2lifeConfig;
  delete window.sketch2lifeAuth;
});

describe("TeacherApiLessonPage UX restructure", () => {
  it("warns before unload only while lesson content has unsaved changes", async () => {
    vi.spyOn(backendApi, "teacherLesson").mockResolvedValueOnce(makeDetail("lesson-1", "Giáo án một"));
    const updateLesson = vi.spyOn(backendApi, "updateLesson").mockResolvedValueOnce(
      makeDetail("lesson-1", "Giáo án đã lưu", { revision: 2 }),
    );
    const { container } = render(
      <MemoryRouter>
        <PortalSessionProvider>
          <TeacherApiLessonPage />
        </PortalSessionProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: /Giáo án mới/ }));
    const lessonForm = container.querySelector("form.teacher-lesson-form") as HTMLFormElement;
    const titleInput = within(lessonForm).getByLabelText(/Tiêu đề/);

    let warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(false);

    fireEvent.change(titleInput, { target: { value: "Bản nháp mới" } });
    warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(true);

    fireEvent.change(titleInput, { target: { value: "" } });
    warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: /Giáo án một/ }));
    expect(await screen.findByDisplayValue("Giáo án một")).toBeTruthy();

    fireEvent.change(titleInput, { target: { value: "Bản nháp" } });
    warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(true);

    fireEvent.change(titleInput, { target: { value: "Giáo án một" } });
    warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(false);

    fireEvent.change(titleInput, { target: { value: "Giáo án đã lưu" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu cập nhật" }));
    await waitFor(() => expect(updateLesson).toHaveBeenCalledOnce());
    await waitFor(() => expect((titleInput as HTMLInputElement).value).toBe("Giáo án đã lưu"));

    warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(false);
  });

  it("shows no tabs on a new lesson, mounts all three tabs for a selected lesson, preserves form/share/in-flight state across tab switches, and returns to Nội dung on lesson change", async () => {
    vi.spyOn(backendApi, "teacherLesson")
      .mockResolvedValueOnce(makeDetail("lesson-1", "Giáo án một"))
      .mockResolvedValueOnce(makeDetail("lesson-2", "Giáo án hai"));

    let resolveShare!: (grant: AccessGrant) => void;
    const sharePromise = new Promise<AccessGrant>((resolve) => {
      resolveShare = resolve;
    });
    mocks.createPrivateShare.mockReturnValueOnce(sharePromise);

    const { container } = render(
      <MemoryRouter>
        <PortalSessionProvider>
          <TeacherApiLessonPage />
        </PortalSessionProvider>
      </MemoryRouter>,
    );

    // No tabs in new unsaved lesson flow
    await screen.findByRole("button", { name: /Giáo án một/ });
    expect(screen.queryByRole("tablist")).toBeNull();

    // Select first lesson -> tabs appear with Nội dung active
    fireEvent.click(screen.getByRole("button", { name: /Giáo án một/ }));
    expect(await screen.findByDisplayValue("Giáo án một")).toBeTruthy();

    const tablist = screen.getByRole("tablist");
    const contentTab = within(tablist).getByRole("tab", { name: "Nội dung" });
    const shareTab = within(tablist).getByRole("tab", { name: "Chia sẻ" });
    const versionsTab = within(tablist).getByRole("tab", { name: "Phiên bản" });
    expect(contentTab.getAttribute("aria-selected")).toBe("true");
    expect(shareTab.getAttribute("aria-selected")).toBe("false");
    expect(versionsTab.getAttribute("aria-selected")).toBe("false");

    // Edit form value on Nội dung
    const titleInput = screen.getByLabelText(/Tiêu đề/) as HTMLInputElement;
    fireEvent.change(titleInput, { target: { value: "Giáo án một đã chỉnh" } });

    // Sticky save bar is inside visible Nội dung panel
    const saveButton = screen.getByRole("button", { name: "Lưu cập nhật" });
    expect(saveButton.closest("[role='tabpanel']")?.hasAttribute("hidden")).toBe(false);

    // Switch to Chia sẻ -> Nội dung panel and save bar are hidden, start in-flight share request
    fireEvent.click(shareTab);
    expect(shareTab.getAttribute("aria-selected")).toBe("true");
    expect(saveButton.closest("[role='tabpanel']")?.hasAttribute("hidden")).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Tạo chia sẻ" }));

    // Switch to Phiên bản while share request is still in flight
    fireEvent.click(versionsTab);
    expect(versionsTab.getAttribute("aria-selected")).toBe("true");
    const versionsPanel = screen.getByRole("tabpanel", { name: "Phiên bản" });
    expect(await within(versionsPanel).findByRole("button", { name: /Phiên bản 1/ })).toBeTruthy();
    expect(mocks.listLessonVersions).toHaveBeenCalledTimes(1);

    // Resolve the in-flight share request while on Phiên bản
    resolveShare(makeGrant("lesson-1"));

    // Switch back to Chia sẻ -> session share list survived and stayed mounted
    fireEvent.click(shareTab);
    expect(await screen.findByText("Chia sẻ trong phiên này")).toBeTruthy();
    expect(screen.getByText("Đang chia sẻ")).toBeTruthy();

    // Switch back to Nội dung -> edited title survived
    fireEvent.click(contentTab);
    expect((screen.getByLabelText(/Tiêu đề/) as HTMLInputElement).value).toBe("Giáo án một đã chỉnh");

    // Switch back to Phiên bản -> already loaded versions did not re-fetch
    fireEvent.click(versionsTab);
    expect(within(versionsPanel).getByRole("button", { name: /Phiên bản 1/ })).toBeTruthy();
    expect(mocks.listLessonVersions).toHaveBeenCalledTimes(1);

    // Selecting another lesson returns to Nội dung
    fireEvent.click(screen.getByRole("button", { name: /Giáo án hai/ }));
    expect(await screen.findByDisplayValue("Giáo án hai")).toBeTruthy();
    expect(screen.getByRole("tab", { name: "Nội dung" }).getAttribute("aria-selected")).toBe("true");

    // Switching to Phiên bản then clicking "Giáo án mới" returns to Nội dung and removes tabs
    fireEvent.click(screen.getByRole("tab", { name: "Phiên bản" }));
    expect(screen.getByRole("tab", { name: "Phiên bản" }).getAttribute("aria-selected")).toBe("true");
    fireEvent.click(screen.getByRole("button", { name: /Giáo án mới/ }));
    expect(screen.queryByRole("tablist")).toBeNull();
    expect(container.querySelector(".teacher-lesson-layout")).toBeTruthy();
  });

  it("keeps save errors and stale revision notices visible in whichever tab the user is on", async () => {
    vi.spyOn(backendApi, "teacherLesson").mockResolvedValueOnce(makeDetail("lesson-1", "Giáo án một", { revision: 2 }));
    vi.spyOn(backendApi, "updateLesson").mockRejectedValueOnce(
      new BackendApiError("Phiên bản đã thay đổi.", "STALE_REVISION", 409),
    );

    render(
      <MemoryRouter>
        <PortalSessionProvider>
          <TeacherApiLessonPage />
        </PortalSessionProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: /Giáo án một/ }));
    expect(await screen.findByDisplayValue("Giáo án một")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Lưu cập nhật" }));

    expect(await screen.findByText("Không thể lưu hoặc tải phiên bản")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Tải lại bản hiện tại/ })).toBeTruthy();

    fireEvent.click(screen.getByRole("tab", { name: "Chia sẻ" }));
    expect(screen.getByText("Không thể lưu hoặc tải phiên bản")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Tải lại bản hiện tại/ })).toBeTruthy();

    fireEvent.click(screen.getByRole("tab", { name: "Phiên bản" }));
    expect(screen.getByText("Không thể lưu hoặc tải phiên bản")).toBeTruthy();
    expect(screen.getByRole("button", { name: /Tải lại bản hiện tại/ })).toBeTruthy();
  });

  it("shows search disclosure only in Giáo án mới flow outside the form and preserves results across open/close", async () => {
    vi.spyOn(backendApi, "teacherLesson").mockResolvedValueOnce(makeDetail("lesson-1", "Giáo án một"));

    const { container } = render(
      <MemoryRouter>
        <PortalSessionProvider>
          <TeacherApiLessonPage />
        </PortalSessionProvider>
      </MemoryRouter>,
    );

    const summary = await screen.findByText("Sao chép từ bài học công khai");
    const details = summary.closest("details") as HTMLDetailsElement;
    expect(details).toBeTruthy();
    expect(details.open).toBe(false);
    expect(screen.getByRole("button", { name: "Nhập tài liệu" }).className).toContain("is-ghost");
    expect(screen.getByRole("button", { name: "Giáo án mới" }).className).toContain("is-ghost");
    expect(screen.getByRole("heading", { name: "Giáo án của tôi" })).toBeTruthy();
    expect(within(container.querySelector("form.teacher-lesson-form") as HTMLFormElement).getByRole("combobox", { name: /Nhóm tuổi/ })).toBeTruthy();
    // Outside the main lesson <form> element
    const lessonForm = container.querySelector("form.teacher-lesson-form");
    expect(lessonForm?.contains(details)).toBe(false);

    // Open disclosure, search, close and reopen -> results and query survive
    fireEvent.click(summary);
    expect(details.open).toBe(true);
    const keywordInput = screen.getByLabelText("Từ khóa") as HTMLInputElement;
    fireEvent.change(keywordInput, { target: { value: "Mèo" } });
    fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));
    expect(await screen.findByText("Bài mẫu công khai")).toBeTruthy();

    fireEvent.click(summary);
    expect(details.open).toBe(false);
    fireEvent.click(summary);
    expect(details.open).toBe(true);
    expect((screen.getByLabelText("Từ khóa") as HTMLInputElement).value).toBe("Mèo");
    expect(screen.getByText("Bài mẫu công khai")).toBeTruthy();

    // Selecting a lesson hides the public search disclosure
    fireEvent.click(screen.getByRole("button", { name: /Giáo án một/ }));
    expect(await screen.findByDisplayValue("Giáo án một")).toBeTruthy();
    expect(screen.queryByText("Sao chép từ bài học công khai")).toBeNull();
    expect(screen.queryByText("Tìm bài học để sao chép")).toBeNull();

    // Returning to Giáo án mới shows the collapsed disclosure again
    fireEvent.click(screen.getByRole("button", { name: /Giáo án mới/ }));
    const reopenedSummary = screen.getByText("Sao chép từ bài học công khai");
    expect((reopenedSummary.closest("details") as HTMLDetailsElement).open).toBe(false);
  });

  it("refreshes the version list after a successful lesson save", async () => {
    const versionSummary = (versionNo: number) => ({
      contract: "LessonVersionV1",
      version_id: `lesson-1-v${versionNo}`,
      version_no: versionNo,
      review_state: "DRAFT",
      structured_content_hash: "a".repeat(64),
      source_document_revision_id: null,
      authored_principal_ref: "teacher-1",
      created_at: `2026-11-${20 - versionNo}T00:00:00Z`,
    });
    mocks.listLessonVersions
      .mockResolvedValueOnce({ contract: "LessonVersionsPageV1", lesson_id: "lesson-1", items: [versionSummary(1)], next_cursor: null })
      .mockResolvedValueOnce({ contract: "LessonVersionsPageV1", lesson_id: "lesson-1", items: [versionSummary(2), versionSummary(1)], next_cursor: null });
    vi.spyOn(backendApi, "teacherLesson").mockResolvedValueOnce(makeDetail("lesson-1", "Giáo án một"));
    const updateLesson = vi.spyOn(backendApi, "updateLesson").mockResolvedValueOnce(
      makeDetail("lesson-1", "Giáo án đã cập nhật", { revision: 2 }),
    );

    render(
      <MemoryRouter>
        <PortalSessionProvider>
          <TeacherApiLessonPage />
        </PortalSessionProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByRole("button", { name: /Giáo án một/ }));
    expect(await screen.findByDisplayValue("Giáo án một")).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: "Phiên bản" }));
    const versionsPanel = screen.getByRole("tabpanel", { name: "Phiên bản" });
    expect(await within(versionsPanel).findByRole("button", { name: /Phiên bản 1/ })).toBeTruthy();
    await waitFor(() => expect(mocks.listLessonVersions).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole("tab", { name: "Nội dung" }));
    fireEvent.change(screen.getByLabelText(/Tiêu đề/), { target: { value: "Giáo án đã cập nhật" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu cập nhật" }));

    await waitFor(() => expect(updateLesson).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(mocks.listLessonVersions).toHaveBeenCalledTimes(2));
    fireEvent.click(screen.getByRole("tab", { name: "Phiên bản" }));
    expect(await within(versionsPanel).findByRole("button", { name: /Phiên bản 2/ })).toBeTruthy();
  });

  it("submits create and update through the sticky save bar and opens activity details only when populated", async () => {
    const createdDetail = makeDetail("lesson-created", "Giáo án vừa tạo", { materials_text: "Giấy màu" });
    const createLesson = vi.spyOn(backendApi, "createLesson").mockResolvedValueOnce(createdDetail);
    const teacherLesson = vi.spyOn(backendApi, "teacherLesson").mockResolvedValueOnce(createdDetail);
    const updateLesson = vi.spyOn(backendApi, "updateLesson").mockResolvedValueOnce(
      makeDetail("lesson-created", "Giáo án vừa cập nhật", { revision: 2, materials_text: "Giấy màu" }),
    );

    const { container } = render(
      <MemoryRouter>
        <PortalSessionProvider>
          <TeacherApiLessonPage />
        </PortalSessionProvider>
      </MemoryRouter>,
    );

    // New lesson activity starts with "Thêm chi tiết" closed and "An toàn" visible
    await screen.findByRole("button", { name: /Giáo án một/ });
    const initialDetails = container.querySelector("details.teacher-activity-details") as HTMLDetailsElement;
    expect(initialDetails.open).toBe(false);
    expect(screen.getByLabelText(/An toàn/)).toBeTruthy();

    // Fill required fields and submit via sticky save bar ("Tạo giáo án")
    const lessonForm = container.querySelector("form.teacher-lesson-form") as HTMLFormElement;
    expect(lessonForm).toBeTruthy();
    const formQueries = within(lessonForm);
    fireEvent.change(formQueries.getByLabelText(/Tiêu đề/), { target: { value: "Giáo án vừa tạo" } });
    fireEvent.change(formQueries.getByLabelText(/Chủ đề/), { target: { value: "Thiên nhiên" } });
    const ageBand = formQueries.getByRole("combobox", { name: /Nhóm tuổi/ });
    expect(ageBand.textContent).toContain("Chọn nhóm tuổi");
    expect(ageBand.getAttribute("aria-required")).toBe("true");
    fireEvent.click(ageBand);
    fireEvent.click(await screen.findByRole("option", { name: "36–71 tháng" }));
    fireEvent.change(formQueries.getByLabelText(/Đối tượng cần vẽ/), { target: { value: "Cây xanh" } });
    fireEvent.change(formQueries.getByLabelText(/Mục tiêu học tập/), { target: { value: "Quan sát" } });
    fireEvent.change(formQueries.getByLabelText(/Các bước hướng dẫn vẽ/), { target: { value: "Vẽ thân cây" } });
    fireEvent.change(formQueries.getByLabelText(/Ghi chú kiến thức/), { target: { value: "Lá xanh" } });
    fireEvent.change(formQueries.getByLabelText(/Tên hoạt động/), { target: { value: "Vẽ ngoài trời" } });
    fireEvent.change(formQueries.getByLabelText(/^Mục tiêu$/), { target: { value: "Quan sát cây" } });
    fireEvent.change(formQueries.getByLabelText(/Hướng dẫn/), { target: { value: "Cầm bút vẽ" } });

    const stickyBar = container.querySelector(".teacher-lesson-sticky-bar");
    expect(stickyBar).toBeTruthy();
    fireEvent.click(within(stickyBar as HTMLElement).getByRole("button", { name: "Tạo giáo án" }));

    await waitFor(() => expect(createLesson).toHaveBeenCalledTimes(1));
    expect(createLesson).toHaveBeenCalledWith(
      "org-test",
      expect.objectContaining({ title: "Giáo án vừa tạo", topic: "Thiên nhiên", target_age_band_ref: "age-36-71-months-v1", target_age_band_version: 1 }),
      expect.any(String),
    );

    // Loaded created lesson has materials_text -> "Thêm chi tiết" is open automatically
    await waitFor(() => expect(teacherLesson).toHaveBeenCalledWith("org-test", "lesson-created"));
    expect(await within(stickyBar as HTMLElement).findByRole("button", { name: "Lưu cập nhật" })).toBeTruthy();
    const populatedDetails = container.querySelector("details.teacher-activity-details") as HTMLDetailsElement;
    expect(populatedDetails.open).toBe(true);

    // Edit title and submit update via sticky save bar
    fireEvent.change(formQueries.getByLabelText(/Tiêu đề/), { target: { value: "Giáo án vừa cập nhật" } });
    fireEvent.click(within(stickyBar as HTMLElement).getByRole("button", { name: "Lưu cập nhật" }));

    await waitFor(() => expect(updateLesson).toHaveBeenCalledTimes(1));
    expect(updateLesson).toHaveBeenCalledWith(
      "org-test",
      expect.objectContaining({ lesson_id: "lesson-created", revision: 1 }),
      expect.objectContaining({ title: "Giáo án vừa cập nhật" }),
      expect.any(String),
    );
  });

  it("keeps a stored unsupported age band until the Teacher selects a supported band", async () => {
    const legacyDetail = makeDetail("lesson-1", "Giáo án một", {
      target_age_band_ref: "age-36-71-months-v1",
      target_age_band_version: 2,
    });
    vi.spyOn(backendApi, "teacherLesson").mockResolvedValueOnce(legacyDetail);
    const updateLesson = vi.spyOn(backendApi, "updateLesson").mockResolvedValueOnce(
      makeDetail("lesson-1", "Giáo án một", { revision: 2, target_age_band_ref: "age-108-120-months-v1" }),
    );

    const { container } = render(
      <MemoryRouter>
        <PortalSessionProvider>
          <TeacherApiLessonPage />
        </PortalSessionProvider>
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByRole("button", { name: /Giáo án một/ }));

    const form = container.querySelector("form.teacher-lesson-form") as HTMLFormElement;
    const ageBand = within(form).getByRole("combobox", { name: /Nhóm tuổi/ });
    expect(ageBand.textContent).toContain("Chọn nhóm tuổi");
    expect(await screen.findByText("Nhóm tuổi cũ không còn được dùng, hãy chọn lại.")).toBeTruthy();
    expect(ageBand.getAttribute("aria-describedby")).toBe("lesson-age-band-hint");

    fireEvent.submit(form);
    expect(await screen.findByText("Hãy chọn nhóm tuổi.")).toBeTruthy();
    expect(updateLesson).not.toHaveBeenCalled();

    fireEvent.click(ageBand);
    fireEvent.click(await screen.findByRole("option", { name: "108–120 tháng" }));
    fireEvent.submit(form);

    await waitFor(() => expect(updateLesson).toHaveBeenCalledTimes(1));
    expect(updateLesson).toHaveBeenCalledWith(
      "org-test",
      legacyDetail,
      expect.objectContaining({ target_age_band_ref: "age-108-120-months-v1", target_age_band_version: 1 }),
      expect.any(String),
    );
  });
});
