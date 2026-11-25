import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import {
  BackendApiError,
  backendApi,
  type LessonContent,
  type LessonDocumentRevisionPreview,
  type LessonSourceDocumentStatus,
  type LessonVersion,
  type TeacherLessonDetail,
} from "../../../../shared/api/backendApi";
import { ImportToVersionPanel } from "../ImportToVersionPanel";

const activity = {
  title: "Quan sát lá",
  objective: "Nhận biết gân lá",
  materials_text: "Lá cây",
  preparation_text: "Rửa sạch lá",
  instructions_text: "Quan sát hình dáng và màu sắc.",
  observation_notes: "Khuyến khích trẻ mô tả.",
  safety_notes: "Không đưa lá vào miệng.",
  activity_kind: "indoor" as const,
};

const currentContent: LessonContent = {
  locale: "vi-VN",
  title: "Giáo án hiện tại",
  topic: "Thực vật",
  target_age_band_ref: "age-4-6",
  target_age_band_version: 2,
  objectives: ["Quan sát cây"],
  drawing_subject: "Chiếc lá",
  drawing_steps_text: "Vẽ cuống lá.",
  subject_learning_notes: "Lá giúp cây hấp thụ ánh sáng.",
  script_direction: "Dùng câu hỏi gợi mở.",
  script_following_allowed: true,
  activities: [activity],
};

const detail = (revision = 4, versionId = "version-1", content = currentContent): TeacherLessonDetail => ({
  contract: "LessonDetailV1",
  lesson_id: "lesson-1",
  organization_id: "org-1",
  owner_kind: "ORGANIZATION",
  created_by: "teacher-1",
  state: "ACTIVE",
  visibility: "PRIVATE",
  moderation_state: "VISIBLE",
  current_version: {
    contract: "LessonVersionV1",
    lesson_id: "lesson-1",
    version_id: versionId,
    version_no: revision,
    review_state: "DRAFT",
    structured_content_hash: "hash",
    source_document_revision_id: null,
    authored_principal_ref: "teacher-1",
    created_at: "2026-11-20T00:00:00Z",
    content,
  },
  revision,
  created_at: "2026-11-20T00:00:00Z",
  updated_at: "2026-11-20T00:00:00Z",
});

const sourceDocument: LessonSourceDocumentStatus = {
  contract: "LessonSourceDocumentStatusV1",
  source_document_id: "source-1",
  state: "READY_FOR_REVIEW",
  safe_file_name: "lesson.docx",
  file_extension: "docx",
  page_or_slide_count: 2,
  warnings: [],
  parser_version: "parser-v1",
  asset_sha256: "hash",
  revision_id: "document-revision-1",
};

const documentRevision: LessonDocumentRevisionPreview = {
  contract: "LessonDocumentRevisionPreviewV1",
  revision_id: "document-revision-1",
  extracted_fields: {
    title: "Giáo án trích xuất",
    topic: "Thế giới cây xanh",
    drawing_subject: "Cây non",
    drawing_steps_text: "Vẽ thân cây rồi thêm lá.",
    subject_learning_notes: "Cây cần nước và ánh sáng.",
    objectives: ["Nhận biết cây non", "Quan sát chiếc lá"],
    script_direction: "Hỏi trẻ cây cần gì để lớn lên?",
  },
  warnings: [],
  page_coverage: [1, 2],
  review_state: "NEEDS_REVIEW",
  parser_version: "parser-v1",
};

const createdVersion: LessonVersion = {
  contract: "LessonVersionV1",
  lesson_id: "lesson-1",
  version_id: "version-2",
  version_no: 5,
  review_state: "DRAFT",
  structured_content_hash: "hash",
  source_document_revision_id: "document-revision-1",
  authored_principal_ref: "teacher-1",
  created_at: "2026-11-25T00:00:00Z",
  content: currentContent,
};

function renderPanel(overrides: {
  source?: LessonSourceDocumentStatus;
  revision?: LessonDocumentRevisionPreview;
  onRevisionConfirmed?: () => void;
  onVersionCreated?: () => void;
} = {}) {
  return render(<ImportToVersionPanel
    organizationId="org-1"
    lessonId="lesson-1"
    sourceDocument={overrides.source ?? sourceDocument}
    revision={overrides.revision ?? documentRevision}
    onRevisionConfirmed={overrides.onRevisionConfirmed}
    onVersionCreated={overrides.onVersionCreated}
  />);
}

beforeEach(() => {
  vi.spyOn(backendApi, "teacherLesson").mockResolvedValue(detail());
  vi.spyOn(backendApi, "createLessonVersion").mockResolvedValue(createdVersion);
  vi.spyOn(backendApi, "requestPublicReview").mockResolvedValue({} as never);
  vi.stubGlobal("crypto", { randomUUID: vi.fn(() => `key-${Math.random()}`) });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("ImportToVersionPanel", () => {
  it("prefills extracted fields and retains age, activities, and locale", async () => {
    renderPanel();

    expect(await screen.findByDisplayValue("Giáo án trích xuất")).toBeTruthy();
    expect(screen.getByDisplayValue("Thế giới cây xanh")).toBeTruthy();
    expect((screen.getByLabelText("Mục tiêu 1") as HTMLTextAreaElement).value).toBe("Nhận biết cây non");
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạo phiên bản" }));

    await waitFor(() => expect(backendApi.createLessonVersion).toHaveBeenCalledTimes(1));
    const sentContent = vi.mocked(backendApi.createLessonVersion).mock.calls[0][3];
    expect(sentContent).toMatchObject({
      locale: "vi-VN",
      title: "Giáo án trích xuất",
      topic: "Thế giới cây xanh",
      target_age_band_ref: "age-4-6",
      target_age_band_version: 2,
      activities: [activity],
      script_following_allowed: true,
    });
  });

  it.each([
    ["not ready", { ...sourceDocument, state: "FAILED" } as LessonSourceDocumentStatus, documentRevision],
    ["already confirmed", sourceDocument, { ...documentRevision, review_state: "CONFIRMED" } as LessonDocumentRevisionPreview],
  ])("keeps promotion disabled when the source is %s", async (_label, source, revision) => {
    renderPanel({ source, revision });
    expect(screen.getByText("Chưa sẵn sàng")).toBeTruthy();
    expect(backendApi.teacherLesson).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: "Xác nhận tạo phiên bản" })).toBeNull();
  });

  it("reloads a stale lesson, keeps the edited draft, and asks for confirmation again", async () => {
    const freshActivity = { ...activity, title: "Vẽ bông hoa mới" };
    const freshContent: LessonContent = {
      ...currentContent,
      locale: "vi-VN",
      title: "Server title",
      topic: "Server topic",
      target_age_band_ref: "age-6-8",
      target_age_band_version: 3,
      script_following_allowed: false,
      activities: [freshActivity],
    };
    vi.mocked(backendApi.teacherLesson)
      .mockResolvedValueOnce(detail())
      .mockResolvedValueOnce(detail(5, "version-5", freshContent));
    vi.mocked(backendApi.createLessonVersion)
      .mockRejectedValueOnce(new BackendApiError("stale", "STALE_REVISION", 409))
      .mockResolvedValueOnce(createdVersion);
    let keyNumber = 0;
    vi.stubGlobal("crypto", { randomUUID: vi.fn(() => `stale-key-${++keyNumber}`) });
    renderPanel();

    fireEvent.change(await screen.findByLabelText("Tên giáo án"), { target: { value: "Bản giáo án đã sửa" } });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạo phiên bản" }));

    expect(await screen.findByText("Giáo án đã thay đổi. Bản chỉnh sửa của bạn vẫn được giữ; hãy rà soát và xác nhận lại.")).toBeTruthy();
    expect(screen.getByDisplayValue("Bản giáo án đã sửa")).toBeTruthy();
    expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(false);
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạo phiên bản" }));

    await waitFor(() => expect(backendApi.createLessonVersion).toHaveBeenCalledTimes(2));
    expect(vi.mocked(backendApi.createLessonVersion).mock.calls[0][1].revision).toBe(4);
    expect(vi.mocked(backendApi.createLessonVersion).mock.calls[1][1].revision).toBe(5);
    expect(vi.mocked(backendApi.createLessonVersion).mock.calls[0][4]).not.toBe(vi.mocked(backendApi.createLessonVersion).mock.calls[1][4]);
    expect(vi.mocked(backendApi.createLessonVersion).mock.calls[1][3]).toMatchObject({
      title: "Bản giáo án đã sửa",
      topic: "Thế giới cây xanh",
      locale: "vi-VN",
      target_age_band_ref: "age-6-8",
      target_age_band_version: 3,
      activities: [freshActivity],
      script_following_allowed: false,
    });
  });

  it("reuses an idempotency key for the same retry and creates a new key after an edit", async () => {
    let keyNumber = 0;
    vi.stubGlobal("crypto", { randomUUID: vi.fn(() => `retry-key-${++keyNumber}`) });
    vi.mocked(backendApi.createLessonVersion)
      .mockRejectedValueOnce(new BackendApiError("unavailable", "PROVIDER_UNAVAILABLE", 503))
      .mockRejectedValueOnce(new BackendApiError("unavailable", "PROVIDER_UNAVAILABLE", 503))
      .mockResolvedValueOnce(createdVersion);
    renderPanel();

    await screen.findByDisplayValue("Giáo án trích xuất");
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạo phiên bản" }));
    await screen.findByText("Dịch vụ tạm thời chưa sẵn sàng. Vui lòng thử lại sau.");
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạo phiên bản" }));
    await waitFor(() => expect(backendApi.createLessonVersion).toHaveBeenCalledTimes(2));
    const firstKey = vi.mocked(backendApi.createLessonVersion).mock.calls[0][4];
    const retryKey = vi.mocked(backendApi.createLessonVersion).mock.calls[1][4];
    expect(retryKey).toBe(firstKey);

    fireEvent.change(screen.getByLabelText("Tên giáo án"), { target: { value: "Giáo án mới" } });
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạo phiên bản" }));
    await waitFor(() => expect(backendApi.createLessonVersion).toHaveBeenCalledTimes(3));
    expect(vi.mocked(backendApi.createLessonVersion).mock.calls[2][4]).not.toBe(firstKey);
  });

  it("maps a 422 field error to the matching form field", async () => {
    vi.mocked(backendApi.createLessonVersion).mockRejectedValueOnce(
      new BackendApiError("invalid", "INVALID_REQUEST", 422, undefined, [{ field: "content.title", code: "STRING_TOO_LONG" }]),
    );
    renderPanel();
    await screen.findByDisplayValue("Giáo án trích xuất");
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạo phiên bản" }));

    expect(await screen.findByText("Kiểm tra nội dung và giới hạn của trường này.")).toBeTruthy();
    expect(screen.getByText("Một số mục cần được chỉnh sửa trước khi tạo phiên bản.")).toBeTruthy();
  });

  it("shows the created draft and signals revision and list refresh", async () => {
    const onRevisionConfirmed = vi.fn();
    const onVersionCreated = vi.fn();
    vi.mocked(backendApi.teacherLesson)
      .mockResolvedValueOnce(detail())
      .mockResolvedValueOnce(detail(5, "version-2"));
    renderPanel({ onRevisionConfirmed, onVersionCreated });
    await screen.findByDisplayValue("Giáo án trích xuất");
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạo phiên bản" }));

    expect(await screen.findByText("Đã tạo bản 5 · Bản nháp")).toBeTruthy();
    expect(onRevisionConfirmed).toHaveBeenCalledOnce();
    expect(onVersionCreated).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "Gửi duyệt công khai" }));
    await screen.findByText("Đã gửi yêu cầu duyệt công khai");
    expect(backendApi.teacherLesson).toHaveBeenCalledTimes(2);
    expect(backendApi.requestPublicReview).toHaveBeenCalledWith("org-1", expect.objectContaining({ current_version: expect.objectContaining({ version_id: "version-2" }) }), expect.any(String));
  });
});
