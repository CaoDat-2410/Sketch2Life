import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { backendApi } from "../../../../shared/api/backendApi";
import { PortalSessionProvider } from "../../../../shared/auth/PortalSessionContext";
import { TeacherApiImportPage } from "../TeacherApiImportPage";

vi.mock("../../components/LessonVersionsPanel", () => ({ LessonVersionsPanel: () => null }));

const lessonPage = {
  contract: "LessonPageV1",
  items: [{
    contract: "LessonSummaryV1",
    lesson_id: "lesson-1",
    title: "Giáo án hiện tại",
    topic: "Thực vật",
    current_version_no: 4,
    review_state: "APPROVED",
    visibility: "PRIVATE",
    activity_count: 1,
    updated_at: "2026-11-20T00:00:00Z",
  }],
  next_cursor: null,
};

const sourceDocument = {
  contract: "LessonSourceDocumentStatusV1",
  source_document_id: "source-1",
  state: "READY_FOR_REVIEW",
  safe_file_name: "lesson.docx",
  file_extension: "docx",
  page_or_slide_count: 2,
  warnings: [],
  parser_version: "parser-v1",
  asset_sha256: "hash",
  revision_id: "revision-1",
};

const documentRevision = {
  contract: "LessonDocumentRevisionPreviewV1",
  revision_id: "revision-1",
  extracted_fields: {
    title: "Giáo án trích xuất",
    topic: "Thế giới cây xanh",
    drawing_subject: "Cây non",
    drawing_steps_text: "Vẽ thân cây rồi thêm lá.",
    subject_learning_notes: "Cây cần nước và ánh sáng.",
    objectives: ["Nhận biết cây non"],
    script_direction: "Hỏi trẻ cây cần gì để lớn lên?",
  },
  warnings: [],
  page_coverage: [1, 2],
  review_state: "NEEDS_REVIEW",
  parser_version: "parser-v1",
};

const currentLesson = {
  contract: "LessonDetailV1",
  lesson_id: "lesson-1",
  organization_id: "org-test",
  owner_kind: "ORGANIZATION",
  created_by: "teacher-1",
  state: "ACTIVE",
  visibility: "PRIVATE",
  moderation_state: "VISIBLE",
  current_version: {
    contract: "LessonVersionV1",
    lesson_id: "lesson-1",
    version_id: "version-1",
    version_no: 4,
    review_state: "DRAFT",
    structured_content_hash: "hash",
    source_document_revision_id: null,
    authored_principal_ref: "teacher-1",
    created_at: "2026-11-20T00:00:00Z",
    content: {
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
      activities: [],
    },
  },
  revision: 4,
  created_at: "2026-11-20T00:00:00Z",
  updated_at: "2026-11-20T00:00:00Z",
};

function renderPage() {
  return render(<PortalSessionProvider><TeacherApiImportPage /></PortalSessionProvider>);
}

beforeEach(() => {
  window.sessionStorage.clear();
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-test" };
  window.sketch2lifeAuth = { signIn: vi.fn(async () => undefined), getIdToken: vi.fn(async () => "token-1") } as never;
  vi.spyOn(backendApi, "assignments").mockResolvedValue({
    contract: "Be1AdultAssignmentsV1",
    subject: "teacher-1",
    organization_id: "org-test",
    assignments: [{ role: "teacher", class_id: "class-1", active: true }],
  });
  vi.spyOn(backendApi, "lessons").mockResolvedValue(lessonPage as never);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
  window.sessionStorage.clear();
});

describe("Teacher import page", () => {
  it("shows only the maximum file size and selected file size", async () => {
    const { container } = renderPage();
    expect(screen.getByText("Tối đa 25 MB.")).toBeTruthy();
    const fileInput = container.querySelector("#teacher-source-file") as HTMLInputElement;
    const file = new File([new Uint8Array(2 * 1024 * 1024)], "lesson.pdf", { type: "application/pdf" });
    fireEvent.change(fileInput, { target: { files: [file] } });

    expect(screen.getByText("2.00 MB")).toBeTruthy();
    expect(screen.queryByText(/tính toàn vẹn/i)).toBeNull();
  });

  it("collapses the read-only extracted grid while the editable panel is visible", async () => {
    window.sessionStorage.setItem("s2l.teacher.upload-resume.v1", JSON.stringify({
      organizationId: "org-test",
      lessonId: "lesson-1",
      byteLength: 1,
      lastModified: 1,
      sha256: "hash",
      uploadSessionId: "upload-1",
      createKey: "create-key",
      completeKey: "complete-key",
    }));
    vi.spyOn(backendApi, "uploadSessionStatus").mockResolvedValue({
      contract: "UploadSessionV1",
      upload_session_id: "upload-1",
      state: "COMPLETED",
      part_size_bytes: 5_000_000,
      expected_parts: 1,
      accepted_part_numbers: [1],
      expires_at: "2026-11-27T00:00:00Z",
      revision: 2,
    });
    vi.spyOn(backendApi, "completeUpload").mockResolvedValue(sourceDocument as never);
    vi.spyOn(backendApi, "documentRevision").mockResolvedValue(documentRevision as never);
    vi.spyOn(backendApi, "teacherLesson").mockResolvedValue(currentLesson as never);
    renderPage();

    const editableTitle = await screen.findByDisplayValue("Giáo án trích xuất");
    expect((editableTitle as HTMLInputElement).disabled).toBe(false);
    const summary = screen.getByText("Bản trích xuất để rà soát").closest("summary");
    const disclosure = summary?.closest("details");
    expect(disclosure?.open).toBe(false);
    if (!summary) throw new Error("extracted fields disclosure summary not rendered");
    fireEvent.click(summary);
    expect(screen.getByText("Cây non")).toBeTruthy();
  });
});
