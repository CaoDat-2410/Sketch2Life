import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { BackendApiError } from "../../../../shared/api/backendApi";
import { teacherOccurrenceApi, type Occurrence, type PlanRevision } from "../../../../shared/api/teacherOccurrenceApi";
import { teacherSvgCatalogApi } from "../../../../shared/api/teacherSvgCatalogApi";
import { teacherPresentationApi, type LessonPresentation, type PresentationMedia, type PresentationRevision } from "../../../../shared/api/teacherPresentationApi";
import { TeacherSlidesPage } from "../TeacherSlidesPage";
import { clearSvgDraftRequests } from "../../services/svgDraftRequests";
import { getAiTaskMark, svgTaskStatusKey } from "../../services/aiTaskStatus";

const hash = "a".repeat(64);
const occurrence: Occurrence = { contract: "LessonOccurrenceV1", occurrence_id: "occ-1", class_id: "class-1", title: "Buổi vẽ", scheduled_date: null, state: "APPROVED", revision: 1, responsible_teacher_ref: "teacher-1", lesson_version_ref: null, lesson_version_no: null, approved_plan: { revision_no: 2, plan_hash: hash, approved_at: "2026-11-25T00:00:00Z" }, sample_video: { slot_state: "AVAILABLE", claimed_at: null, run_ref: null }, created_at: "2026-11-25T00:00:00Z" };
const plan: PlanRevision = { contract: "LessonPlanRevisionV1", occurrence_id: "occ-1", plan_revision_id: "plan-rev-2", revision_no: 2, state: "APPROVED", content_hash: hash, document_revision_ref: null, objectives: [], teacher_direction: "", safety_notes: null, lesson_version_ref: null, lesson_version_no: null, activities: [{ plan_activity_id: "activity-1", order: 1, kind: "CUSTOM", lesson_activity_id: null, title: "Con mèo", description: null, snapshot_hash: null, checklist_required: false, checklist_version: null, confirmed: true }], created_at: "2026-11-25T00:00:00Z", approved_at: "2026-11-25T00:00:00Z", supersedes_revision_no: null };
const presentation: LessonPresentation = { contract: "LessonPresentationV1", presentation_id: "pres-1", occurrence_id: "occ-1", revision: 2, head_revision_no: 1, ready_revision_no: null, source_state: "CURRENT", stale_reasons: [], presentable: false, head: { contract: "LessonPresentationRevisionV1", revision_no: 1, base_revision_no: null, state: "DRAFT", aspect_ratio: "16:9", source_state: "CURRENT", stale_reasons: [], plan_revision_no: 2, plan_content_hash: hash, content_hash: hash, slides: [{ slide_id: "slide-1", position: 1, title: "Con mèo", body_text: "Cùng quan sát", media: null, media_state: null }], created_at: "2026-11-25T00:00:00Z", readied_at: null } };
const presentationWithMedia = (media: PresentationMedia): LessonPresentation => ({
  ...presentation,
  head: {
    ...presentation.head,
    slides: presentation.head.slides.map((slide) => ({ ...slide, media, media_state: "CURRENT" as const })),
  },
});
const savedImage: PresentationMedia = { kind: "IMAGE", asset_ref: "asset-saved", alt_text: "Ảnh mèo", media_type: "image/png", width: 640, height: 480, placement: "RIGHT" };
const savedCatalogMedia: PresentationMedia = { kind: "SVG_CATALOG", catalog_entry_id: "catalog-1", alt_text: "Minh họa", canonical_sha256: hash, placement: "RIGHT" };
const presentationWithSlides = (slides: PresentationRevision["slides"]): LessonPresentation => ({
  ...presentation,
  head: { ...presentation.head, slides },
});
const currentPresentationWithMedia = presentationWithMedia(savedCatalogMedia);
const stalePresentation: LessonPresentation = {
  ...currentPresentationWithMedia,
  source_state: "STALE",
  stale_reasons: ["PLAN_REVISION_CHANGED"],
  head: { ...currentPresentationWithMedia.head, source_state: "STALE", stale_reasons: ["PLAN_REVISION_CHANGED"] },
};

function beforeUnloadEvent() {
  const event = new Event("beforeunload", { cancelable: true }) as BeforeUnloadEvent;
  Object.defineProperty(event, "returnValue", { configurable: true, writable: true, value: "unchanged" });
  return event;
}

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-1" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token") } as never;
  vi.spyOn(teacherOccurrenceApi, "get").mockResolvedValue({ data: occurrence, etag: '"1"', notModified: false });
  vi.spyOn(teacherOccurrenceApi, "getPlan").mockResolvedValue({ data: plan, etag: '"2"', notModified: false });
  vi.spyOn(teacherPresentationApi, "get").mockRejectedValue(new BackendApiError("not found", "RESOURCE_NOT_FOUND", 404));
  vi.spyOn(teacherSvgCatalogApi, "getAsset").mockRejectedValue(new BackendApiError("not found", "SVG_CATALOG_ITEM_NOT_FOUND", 404));
  vi.spyOn(teacherPresentationApi, "create").mockResolvedValue(presentation);
  vi.spyOn(teacherPresentationApi, "createSvgDraft").mockResolvedValue({
    contract: "PresentationSvgDraftV1", svg_draft_id: "draft-1", state: "PENDING_REVIEW", revision: 1,
    document: { schema_version: "SvgDocumentV1", view_box: "0 0 1 1", paths: [] }, preview_svg: "<svg/>", canonical_sha256: hash,
    generator: { name: "test", version: "1" }, license_id: "CC0-1.0", created_at: "2026-11-25T00:00:00Z", decided_at: null,
  });
});
afterEach(() => { cleanup(); clearSvgDraftRequests(); vi.restoreAllMocks(); vi.useRealTimers(); window.sketch2lifeAuth = undefined; window.sketch2lifeConfig = undefined; });

describe("Teacher slides page", () => {
  const mediaCard = () => screen.getByRole("region", { name: "Đính kèm hình ảnh minh họa" });

  it("warns before unload only while slide edits differ from the saved draft", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    vi.spyOn(teacherPresentationApi, "createRevision").mockResolvedValueOnce(presentationWithSlides([
      { ...presentation.head.slides[0], title: "Tiêu đề đã lưu" },
    ]));
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });

    const title = screen.getByLabelText("Tiêu đề");
    let warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(false);

    fireEvent.change(title, { target: { value: "Bản nháp chưa lưu" } });
    warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(true);

    fireEvent.change(title, { target: { value: "Con mèo" } });
    warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(false);

    fireEvent.change(title, { target: { value: "Tiêu đề đã lưu" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Lưu bản nháp mới" })[0]);
    expect(await screen.findByText("Đã tạo bản nháp mới.")).toBeTruthy();

    warning = beforeUnloadEvent();
    window.dispatchEvent(warning);
    expect(warning.defaultPrevented).toBe(false);
  });

  it("shows a shared empty state linking to Buổi dạy when no session is selected", () => {
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation"]}><TeacherSlidesPage /></MemoryRouter>);

    expect(screen.getByRole("heading", { name: "Chưa chọn buổi dạy" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Chọn buổi dạy" }).getAttribute("href")).toBe("/teacher/t04-session-sketch-deck");
  });

  it("shows one version without repeating readiness or an absent date", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    expect(await screen.findByText("Phiên bản 2")).toBeTruthy();
    expect(screen.queryByText("Chưa đánh dấu sẵn sàng")).toBeNull();
    expect(screen.getByText("Chưa sẵn sàng")).toBeTruthy();
    expect(screen.queryByText("Chưa đặt ngày")).toBeNull();
    expect(screen.queryByText(/Bản nháp 1|Kế hoạch phiên bản 2/)).toBeNull();
  });

  it("keeps the scheduled date beside the version when available", async () => {
    vi.mocked(teacherOccurrenceApi.get).mockResolvedValueOnce({ data: { ...occurrence, scheduled_date: "2026-11-26" }, etag: '"1"', notModified: false });
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    expect(await screen.findByText("Phiên bản 2 · 26/11/2026")).toBeTruthy();
  });

  it("shows the operation chip from 40 changes", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    expect(screen.queryByText(/\d+ \/ 50 thao tác/)).toBeNull();

    for (let index = 0; index < 40; index += 1) {
      fireEvent.click(screen.getByRole("button", { name: "Thêm slide" }));
    }

    expect(screen.getByText("40 / 50 thao tác")).toBeTruthy();
  });

  async function stageUploadedImage() {
    vi.spyOn(teacherPresentationApi, "uploadImage").mockResolvedValue("asset-new");
    fireEvent.change(screen.getByLabelText("Ảnh JPEG, PNG hoặc WebP"), {
      target: { files: [new File(["image"], "cat.png", { type: "image/png" })] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Tải ảnh lên" }));
    await screen.findByText("Ảnh đã tải lên, sẵn sàng để đính kèm.");
    fireEvent.change(screen.getByLabelText("Mô tả hình ảnh"), { target: { value: "Mèo mới" } });
    fireEvent.click(within(mediaCard()).getByRole("button", { name: "Đính kèm vào bản nháp" }));
  }

  it.each([
    ["without a query", "https://www.youtube-nocookie.com/embed/video-1", "https://www.youtube-nocookie.com/embed/video-1?rel=0"],
    ["with an existing query", "https://www.youtube-nocookie.com/embed/video-1?autoplay=1&start=12", "https://www.youtube-nocookie.com/embed/video-1?autoplay=1&start=12&rel=0"],
  ] as const)("adds rel=0 to a YouTube preview URL %s", async (_case, embedUrl, expectedSrc) => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithMedia({ kind: "VIDEO_EMBED", provider: "YOUTUBE", video_id: "video-1", embed_url: embedUrl, placement: "FULL" }));
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    expect((await screen.findByTitle("Video nhúng")).getAttribute("src")).toBe(expectedSrc);
  });

  it("keeps the Vimeo preview URL unchanged", async () => {
    const embedUrl = "https://player.vimeo.com/video/12345?autoplay=1&muted=1";
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithMedia({ kind: "VIDEO_EMBED", provider: "VIMEO", video_id: "12345", embed_url: embedUrl, placement: "FULL" }));
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    expect((await screen.findByTitle("Video nhúng")).getAttribute("src")).toBe(embedUrl);
  });

  it("presents the selected ready revision without mounting duplicate media or making another revision request", async () => {
    const readySlides: PresentationRevision["slides"] = [
      {
        ...presentation.head.slides[0],
        title: "Nội dung đã duyệt",
        body_text: "Xem video cùng nhau.",
        media: { kind: "VIDEO_EMBED", provider: "YOUTUBE", video_id: "video-1", embed_url: "https://www.youtube-nocookie.com/embed/video-1", placement: "FULL" },
      },
      { ...presentation.head.slides[0], slide_id: "slide-2", position: 2, title: "Slide kế tiếp", body_text: "Nội dung kế tiếp", media: null, media_state: null },
    ];
    const readyRevision: PresentationRevision = { ...presentation.head, revision_no: 1, state: "READY", slides: readySlides };
    const current: LessonPresentation = {
      ...presentation,
      revision: 3,
      head_revision_no: 2,
      ready_revision_no: 1,
      head: { ...presentation.head, revision_no: 2 },
    };
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(current);
    const getRevision = vi.spyOn(teacherPresentationApi, "getRevision").mockResolvedValue(readyRevision);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    expect(await screen.findByText("Nội dung đã duyệt")).toBeTruthy();
    const getCount = vi.mocked(teacherPresentationApi.get).mock.calls.length;
    const revisionCount = getRevision.mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "Trình chiếu" }));

    expect(await screen.findByRole("dialog", { name: "Trình chiếu · Bản sẵn sàng" })).toBeTruthy();
    expect(screen.getAllByTitle("Video nhúng")).toHaveLength(1);
    expect(screen.getByTitle("Video nhúng").getAttribute("src")).toBe("https://www.youtube-nocookie.com/embed/video-1?rel=0");
    fireEvent.keyDown(document, { key: "ArrowRight" });
    expect(await screen.findByText("Nội dung kế tiếp")).toBeTruthy();
    expect(vi.mocked(teacherPresentationApi.get).mock.calls).toHaveLength(getCount);
    expect(getRevision).toHaveBeenCalledTimes(revisionCount);
  });

  it("sends the original YouTube URL when saving video media to a draft", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    const createRevision = vi.spyOn(teacherPresentationApi, "createRevision").mockResolvedValue(presentation);
    const originalUrl = "https://www.youtube.com/watch?v=video-1&list=playlist-2";
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });

    fireEvent.change(screen.getByLabelText("Loại nội dung"), { target: { value: "VIDEO_EMBED" } });
    fireEvent.change(screen.getByLabelText("Liên kết YouTube hoặc Vimeo"), { target: { value: originalUrl } });
    fireEvent.click(screen.getByRole("button", { name: "Đính kèm vào bản nháp" }));
    fireEvent.click(within(mediaCard()).getByRole("button", { name: "Lưu bản nháp mới" }));

    await screen.findByText("Đã tạo bản nháp mới.");
    expect(createRevision).toHaveBeenCalledWith("occ-1", 2, {
      repin_to_current_plan: false,
      operations: [{ op: "SET_MEDIA", slide_id: "slide-1", placement: "FULL", media: { kind: "VIDEO_EMBED", url: originalUrl } }],
    }, expect.any(String));
  });

  it("disables remove and reposition with no saved or staged media and keeps the card save button disabled", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });

    const card = mediaCard();
    expect(screen.getAllByRole("button", { name: "Lưu bản nháp mới" })).toHaveLength(2);
    expect((within(card).getByRole("button", { name: "Gỡ hình ảnh" }) as HTMLButtonElement).disabled).toBe(true);
    expect((within(card).getByRole("button", { name: "Cập nhật vị trí hiện tại" }) as HTMLButtonElement).disabled).toBe(true);
    expect((within(card).getByRole("button", { name: "Lưu bản nháp mới" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("stages saved-media removal, explains it beside the actions, and saves CLEAR_MEDIA", async () => {
    const imageSlides: PresentationRevision["slides"] = [
      presentation.head.slides[0],
      { ...presentation.head.slides[0], slide_id: "slide-2", position: 2, title: "Con chó", media: savedImage, media_state: "CURRENT" },
    ];
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithSlides(imageSlides));
    const createRevision = vi.spyOn(teacherPresentationApi, "createRevision").mockResolvedValue(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });

    const card = mediaCard();
    fireEvent.change(within(card).getByLabelText("Slide"), { target: { value: "slide-2" } });
    const remove = within(card).getByRole("button", { name: "Gỡ hình ảnh" }) as HTMLButtonElement;
    fireEvent.click(remove);
    expect(await within(card).findByText("Chưa lưu: đã đánh dấu gỡ hình ảnh.")).toBeTruthy();
    expect(remove.disabled).toBe(true);
    fireEvent.click(within(card).getByRole("button", { name: "Lưu bản nháp mới" }));

    await screen.findByText("Đã tạo bản nháp mới.");
    expect(createRevision).toHaveBeenCalledWith("occ-1", 2, {
      repin_to_current_plan: false,
      operations: [{ op: "CLEAR_MEDIA", slide_id: "slide-2" }],
    }, expect.any(String));
  });

  it("drops a staged-only image without creating a CLEAR_MEDIA operation", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    const createRevision = vi.spyOn(teacherPresentationApi, "createRevision").mockResolvedValue(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    await stageUploadedImage();

    const card = mediaCard();
    expect(await within(card).findByText("Chưa lưu: hình ảnh mới.")).toBeTruthy();
    expect((within(card).getByRole("button", { name: "Gỡ hình ảnh" }) as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(within(card).getByRole("button", { name: "Gỡ hình ảnh" }));

    expect(within(card).queryByText("Chưa lưu: hình ảnh mới.")).toBeNull();
    expect(screen.queryByText("0 / 50 thao tác")).toBeNull();
    expect(createRevision).not.toHaveBeenCalled();
  });

  it("follows the selected slide placement without replacing the Teacher's choice on that slide", async () => {
    const slides: PresentationRevision["slides"] = [
      presentation.head.slides[0],
      { ...presentation.head.slides[0], slide_id: "slide-2", position: 2, title: "Con chó", media: savedCatalogMedia, media_state: "CURRENT" },
    ];
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithSlides(slides));
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });

    const card = mediaCard();
    const slideSelect = within(card).getByLabelText("Slide") as HTMLSelectElement;
    const placementSelect = within(card).getByLabelText("Vị trí") as HTMLSelectElement;
    const reposition = within(card).getByRole("button", { name: "Cập nhật vị trí hiện tại" }) as HTMLButtonElement;
    expect(placementSelect.value).toBe("FULL");
    fireEvent.change(slideSelect, { target: { value: "slide-2" } });
    expect(placementSelect.value).toBe("RIGHT");
    expect(reposition.disabled).toBe(true);
    fireEvent.change(placementSelect, { target: { value: "LEFT" } });
    expect(reposition.disabled).toBe(false);
    fireEvent.change(within(card).getByLabelText("Loại nội dung"), { target: { value: "VIDEO_EMBED" } });
    expect(placementSelect.value).toBe("LEFT");

    fireEvent.change(slideSelect, { target: { value: "slide-1" } });
    expect(placementSelect.value).toBe("FULL");
    fireEvent.change(slideSelect, { target: { value: "slide-2" } });
    expect(placementSelect.value).toBe("RIGHT");
  });

  it("refreshes the placement select from saved media after reload", async () => {
    const updated = presentationWithMedia({ ...savedCatalogMedia, placement: "LEFT" });
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithMedia(savedCatalogMedia)).mockResolvedValueOnce(updated);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });

    const placementSelect = screen.getByLabelText("Vị trí") as HTMLSelectElement;
    expect(placementSelect.value).toBe("RIGHT");
    fireEvent.change(placementSelect, { target: { value: "FULL" } });
    fireEvent.click(screen.getByRole("button", { name: "Tải lại" }));
    await waitFor(() => expect((screen.getByLabelText("Vị trí") as HTMLSelectElement).value).toBe("LEFT"));
  });

  it("repositions a staged image without replacing it and refreshes placement after save", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    const saved = presentationWithMedia({ kind: "IMAGE", asset_ref: "asset-new", alt_text: "Mèo mới", media_type: "image/png", width: 640, height: 480, placement: "RIGHT" });
    const createRevision = vi.spyOn(teacherPresentationApi, "createRevision").mockResolvedValue({
      ...saved,
      revision: 3,
      head_revision_no: 2,
      head: { ...saved.head, revision_no: 2 },
    });
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    await stageUploadedImage();

    const card = mediaCard();
    const placementSelect = within(card).getByLabelText("Vị trí") as HTMLSelectElement;
    fireEvent.change(placementSelect, { target: { value: "RIGHT" } });
    const reposition = within(card).getByRole("button", { name: "Cập nhật vị trí hiện tại" }) as HTMLButtonElement;
    expect(reposition.disabled).toBe(false);
    fireEvent.click(reposition);
    expect(await within(card).findByText("Chưa lưu: hình ảnh mới, vị trí bên phải.")).toBeTruthy();
    fireEvent.change(placementSelect, { target: { value: "LEFT" } });
    expect(placementSelect.value).toBe("LEFT");
    fireEvent.click(within(card).getByRole("button", { name: "Lưu bản nháp mới" }));

    await screen.findByText("Đã tạo bản nháp mới.");
    await waitFor(() => expect(placementSelect.value).toBe("RIGHT"));
    expect(createRevision).toHaveBeenCalledWith("occ-1", 2, {
      repin_to_current_plan: false,
      operations: [{ op: "SET_MEDIA", slide_id: "slide-1", placement: "RIGHT", media: { kind: "IMAGE", asset_ref: "asset-new", alt_text: "Mèo mới" } }],
    }, expect.any(String));
  });

  it("uses the same save rules in the card and explains stale-source repinning beside staged media", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(stalePresentation);
    const createRevision = vi.spyOn(teacherPresentationApi, "createRevision").mockResolvedValue(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    await stageUploadedImage();

    const card = mediaCard();
    const cardSave = within(card).getByRole("button", { name: "Lưu bản nháp mới" }) as HTMLButtonElement;
    const existingSave = screen.getAllByRole("button", { name: "Lưu bản nháp mới" })[0] as HTMLButtonElement;
    expect(await within(card).findByText(/Ghim phiên bản kế hoạch hiện tại/)).toBeTruthy();
    expect(cardSave.disabled).toBe(true);
    expect(existingSave.disabled).toBe(true);

    fireEvent.click(screen.getByRole("checkbox", { name: "Ghim phiên bản kế hoạch hiện tại khi tạo bản nháp mới" }));
    expect(cardSave.disabled).toBe(false);
    expect(existingSave.disabled).toBe(false);
    fireEvent.click(cardSave);
    await screen.findByText("Đã tạo bản nháp mới.");
    expect(createRevision).toHaveBeenCalledWith("occ-1", 2, {
      repin_to_current_plan: true,
      operations: [{ op: "SET_MEDIA", slide_id: "slide-1", placement: "RIGHT", media: { kind: "IMAGE", asset_ref: "asset-new", alt_text: "Mèo mới" } }],
    }, expect.any(String));
  });

  it("mentions the retained ready version only when the response includes one", async () => {
    const current: LessonPresentation = {
      ...presentation,
      revision: 3,
      head_revision_no: 2,
      ready_revision_no: 1,
      head: { ...presentation.head, revision_no: 2 },
    };
    const readyRevision: PresentationRevision = { ...presentation.head, revision_no: 1, state: "READY" };
    const next: LessonPresentation = {
      ...current,
      revision: 4,
      head_revision_no: 3,
      head: { ...current.head, revision_no: 3, slides: [{ ...current.head.slides[0], title: "Nội dung mới" }] },
    };
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(current);
    const getRevision = vi.spyOn(teacherPresentationApi, "getRevision").mockResolvedValue(readyRevision);
    const createRevision = vi.spyOn(teacherPresentationApi, "createRevision").mockResolvedValue(next);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    fireEvent.change(screen.getByLabelText("Tiêu đề"), { target: { value: "Đã sửa nội dung" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Lưu bản nháp mới" })[0]);

    expect(await screen.findByText("Đã tạo bản nháp mới. Bản đã sẵn sàng trước đó vẫn được giữ nguyên.")).toBeTruthy();
    expect(createRevision).toHaveBeenCalledWith("occ-1", 3, expect.anything(), expect.any(String));
    expect(getRevision).toHaveBeenCalledWith("occ-1", 1);
  });

  it("disables both save buttons and explains the 50-operation limit beside staged media", async () => {
    const slides: PresentationRevision["slides"] = Array.from({ length: 50 }, (_, index) => ({
      ...presentation.head.slides[0],
      slide_id: `slide-${index + 1}`,
      position: index + 1,
      title: `Slide ${index + 1}`,
    }));
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithSlides(slides));
    const createRevision = vi.spyOn(teacherPresentationApi, "createRevision").mockResolvedValue(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });

    act(() => {
      for (let index = 0; index < slides.length; index += 1) {
        fireEvent.change(screen.getAllByLabelText("Tiêu đề")[index], { target: { value: `Updated ${index + 1}` } });
      }
    });
    await stageUploadedImage();

    const card = mediaCard();
    expect(screen.getByText("51 / 50 thao tác")).toBeTruthy();
    expect(await within(card).findByText(/Đã vượt giới hạn 50 thay đổi/)).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Lưu bản nháp mới" }).every((button) => (button as HTMLButtonElement).disabled)).toBe(true);
    fireEvent.click(within(card).getByRole("button", { name: "Lưu bản nháp mới" }));
    expect(createRevision).not.toHaveBeenCalled();
  }, 15_000);

  it("uses the occurrence from the teacher entry point and creates only after a click", async () => {
    const create = vi.mocked(teacherPresentationApi.create);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    expect(await screen.findByRole("button", { name: "Tạo slide trống" })).toBeTruthy();
    expect(create).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Tạo slide trống" }));
    expect(await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" })).toBeTruthy();
    expect(create).toHaveBeenCalledWith("occ-1", "BLANK", expect.any(String));
    expect(teacherPresentationApi.createSvgDraft).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Trình chiếu" }));
    expect(await screen.findByRole("dialog", { name: "Trình chiếu · Bản nháp" })).toBeTruthy();
  });

  it("requests an SVG draft only on the Teacher's explicit click", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    expect(await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" })).toBeTruthy();
    expect(teacherPresentationApi.createSvgDraft).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Hoạt động trong kế hoạch"), { target: { value: "activity-1" } });
    const subjectInput = screen.getByLabelText("Chủ thể") as HTMLInputElement;
    expect(subjectInput.placeholder).toBe("Ví dụ: con mèo");
    expect(screen.queryByText("Ví dụ: con mèo")).toBeNull();
    fireEvent.change(subjectInput, { target: { value: "con mèo" } });
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" }));
    expect(await screen.findByRole("heading", { name: "Bản nháp cần bạn quyết định" })).toBeTruthy();
    expect(teacherPresentationApi.createSvgDraft).toHaveBeenCalledWith("occ-1", { plan_activity_id: "activity-1", subject_text: "con mèo" }, expect.any(String));
  });

  it("lists approved SVG catalog entries and hides pending entries", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValue(presentation);
    vi.spyOn(teacherSvgCatalogApi, "listAssets").mockResolvedValue({ items: [
      { catalog_entry_id: "svg-approved", title_vi: "SVG đã duyệt", alt_text_vi: "Minh họa", review_state: "APPROVED" },
      { catalog_entry_id: "svg-pending", title_vi: "SVG đang chờ", alt_text_vi: "Minh họa", review_state: "PENDING_EDUCATOR_REVIEW" },
    ] } as never);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    fireEvent.change(screen.getByLabelText("Loại nội dung"), { target: { value: "SVG_CATALOG" } });

    expect(await screen.findByRole("option", { name: "SVG đã duyệt" })).toBeTruthy();
    expect(screen.queryByRole("option", { name: "SVG đang chờ" })).toBeNull();
  });

  it("renders an approved catalog document as an encoded SVG image in the slide preview", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithMedia(savedCatalogMedia));
    const listAssets = vi.spyOn(teacherSvgCatalogApi, "listAssets").mockResolvedValue({ items: [{
      catalog_entry_id: "catalog-1",
      title_vi: "Mèo trong danh mục",
      alt_text_vi: "Minh họa",
      review_state: "APPROVED",
      document: {
        schema_version: "SvgDocumentV1",
        view_box: "0 0 24 24",
        paths: [{ path_id: "p1", d: "M1 2 L3 4", fill: "#fff", stroke: "#123", stroke_width: 1 }],
      },
    }] } as never);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    const preview = screen.getByRole("region", { name: "Xem trước slide" });
    const image = await within(preview).findByRole("img", { name: "Minh họa" });
    const source = image.getAttribute("src") ?? "";
    expect(source).toMatch(/^data:image\/svg\+xml;charset=utf-8,/);
    expect(decodeURIComponent(source.slice(source.indexOf(",") + 1))).toContain('<path d="M1 2 L3 4" fill="#fff" stroke="#123" stroke-width="1" />');
    expect(preview.querySelector(".tp-slide-preview-canvas svg")).toBeNull();
    expect(listAssets).toHaveBeenCalledWith("org-1", { limit: 100 });
  });

  it("loads the SVG by id when a slide entry is outside the loaded catalog list", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithMedia(savedCatalogMedia));
    vi.spyOn(teacherSvgCatalogApi, "listAssets").mockResolvedValue({ items: [] });
    const getAsset = vi.mocked(teacherSvgCatalogApi.getAsset).mockResolvedValueOnce({
      catalog_entry_id: "catalog-1",
      title_vi: "Mèo ngoài trang đầu",
      alt_text_vi: "Minh họa",
      document: {
        schema_version: "SvgDocumentV1",
        view_box: "0 0 24 24",
        paths: [{ path_id: "p1", d: "M1 2 L3 4", fill: "#fff", stroke: "#123", stroke_width: 1 }],
      },
    } as never);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    const preview = screen.getByRole("region", { name: "Xem trước slide" });
    expect(await within(preview).findByRole("img", { name: "Minh họa" })).toBeTruthy();
    expect(getAsset).toHaveBeenCalledWith("org-1", "catalog-1");
  });

  it("keeps the SVG alt text visible while its catalog source is loading and after failure", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithMedia(savedCatalogMedia));
    let finishLoad: ((result: { items: unknown[] }) => void) | undefined;
    vi.spyOn(teacherSvgCatalogApi, "listAssets").mockImplementation(() => new Promise((resolve) => {
      finishLoad = (result) => resolve(result as never);
    }) as never);
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    const preview = screen.getByRole("region", { name: "Xem trước slide" });
    expect(await within(preview).findByText("Minh họa · Đang tải hình minh họa SVG…")).toBeTruthy();
    await act(async () => { finishLoad?.({ items: [] }); });
    expect(await within(preview).findByText("Minh họa · Chưa tìm thấy bản vẽ trong danh mục.")).toBeTruthy();
  });

  it("shows the SVG alt text and a short note when the catalog read fails", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithMedia(savedCatalogMedia));
    vi.spyOn(teacherSvgCatalogApi, "listAssets").mockRejectedValueOnce(new Error("offline"));
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    const failedPreview = screen.getByRole("region", { name: "Xem trước slide" });
    expect(await within(failedPreview).findByText("Minh họa · Chưa thể tải hình minh họa SVG.")).toBeTruthy();
  });

  it("shows a Vietnamese message when saving a presentation with a pending catalog SVG", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentationWithMedia(savedCatalogMedia));
    vi.spyOn(teacherPresentationApi, "createRevision").mockRejectedValueOnce(
      new BackendApiError("not approved", "SVG_CATALOG_NOT_APPROVED", 409),
    );
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);

    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    fireEvent.change(screen.getByLabelText("Tiêu đề"), { target: { value: "Tiêu đề đã sửa" } });
    fireEvent.click(screen.getAllByRole("button", { name: "Lưu bản nháp mới" })[0]);
    expect(await screen.findByText("SVG trong danh mục chưa được duyệt để lưu hoặc trình chiếu.")).toBeTruthy();
  });

  it("explains why the SVG dropdown is empty", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValue(presentation);
    vi.spyOn(teacherSvgCatalogApi, "listAssets").mockResolvedValue({ items: [] });
    render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    fireEvent.change(screen.getByLabelText("Loại nội dung"), { target: { value: "SVG_CATALOG" } });

    expect(await screen.findByText("Chỉ SVG đã được duyệt xuất hiện ở đây. Nhờ giáo viên khác duyệt trong Danh mục SVG.")).toBeTruthy();
  });

  const open = () => render(<MemoryRouter initialEntries={["/teacher/t02-presentation?occurrence=occ-1"]}><TeacherSlidesPage /></MemoryRouter>);
  async function ask() {
    await screen.findByRole("heading", { name: "Chỉnh sửa bản nháp" });
    fireEvent.change(screen.getByLabelText("Hoạt động trong kế hoạch"), { target: { value: "activity-1" } });
    fireEvent.change(screen.getByLabelText("Chủ thể"), { target: { value: "con mèo" } });
  }

  it("sets and clears the SVG mark after the draft is shown on the slides page", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValueOnce(presentation);
    let finish: (() => void) | undefined;
    vi.mocked(teacherPresentationApi.createSvgDraft).mockImplementation(() => new Promise((resolve) => {
      finish = () => resolve({
        contract: "PresentationSvgDraftV1", svg_draft_id: "draft-1", state: "PENDING_REVIEW", revision: 1,
        document: { schema_version: "SvgDocumentV1", view_box: "0 0 1 1", paths: [] }, preview_svg: "<svg/>", canonical_sha256: hash,
        generator: { name: "test", version: "1" }, license_id: "CC0-1.0", created_at: "2026-11-25T00:00:00Z", decided_at: null,
      });
    }));
    open();
    await ask();
    vi.useFakeTimers();
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" }));
    const svgKey = svgTaskStatusKey("occ-1");
    expect(getAiTaskMark(svgKey)?.status).toBe("pending");

    await act(async () => {
      finish?.();
      await Promise.resolve();
    });
    expect(screen.getByRole("heading", { name: "Bản nháp cần bạn quyết định" })).toBeTruthy();
    expect(getAiTaskMark(svgKey)?.status).toBe("done");
    await act(async () => { vi.advanceTimersByTime(3_999); });
    expect(getAiTaskMark(svgKey)?.status).toBe("done");
    await act(async () => { vi.advanceTimersByTime(1); });
    expect(getAiTaskMark(svgKey)).toBeUndefined();
  });

  it("keeps a slow SVG request across screens, shows it is working and never sends a second call", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValue(presentation);
    const reply = await vi.mocked(teacherPresentationApi.createSvgDraft).getMockImplementation()!("occ-1", {} as never);
    vi.mocked(teacherPresentationApi.createSvgDraft).mockClear();
    let finish: () => void = () => undefined;
    vi.mocked(teacherPresentationApi.createSvgDraft).mockImplementation(() => new Promise((resolve) => { finish = () => resolve(reply); }));
    const first = open();
    await ask();
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" }));
    expect(screen.getByRole("status").textContent).toContain("Đang tạo bản SVG");
    first.unmount();

    open();
    await ask();
    const button = screen.getByRole("button", { name: "Đang tạo bản SVG…" }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    fireEvent.click(button);
    expect(teacherPresentationApi.createSvgDraft).toHaveBeenCalledTimes(1);
    await act(async () => { finish(); });
    expect(await screen.findByRole("heading", { name: "Bản nháp cần bạn quyết định" })).toBeTruthy();
  });

  it("keeps the button after a server failure and retries with the same key", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValue(presentation);
    const send = vi.mocked(teacherPresentationApi.createSvgDraft);
    send.mockRejectedValue(new BackendApiError("x", "PROVIDER_UNAVAILABLE", 503));
    open();
    await ask();
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" }));
    expect((await screen.findByText("Tạo SVG hiện chưa khả dụng."))).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" }));
    await screen.findByText("Tạo SVG hiện chưa khả dụng.");
    expect(send).toHaveBeenCalledTimes(2);
    expect(send.mock.calls[1][2]).toBe(send.mock.calls[0][2]);
  });

  it("does not show an old error after the page is remounted", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValue(presentation);
    const send = vi.mocked(teacherPresentationApi.createSvgDraft);
    send.mockRejectedValue(new BackendApiError("x", "PROVIDER_UNAVAILABLE", 503));
    const first = open();
    await ask();
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" }));
    expect(await screen.findByText("Tạo SVG hiện chưa khả dụng.")).toBeTruthy();
    first.unmount();

    open();
    await ask();
    expect(screen.queryByText("Tạo SVG hiện chưa khả dụng.")).toBeNull();
    expect(send).toHaveBeenCalledTimes(1);
  });

  it("keeps the original 429 cooldown end across a remount", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValue(presentation);
    const clock = vi.spyOn(Date, "now");
    const start = 1_000_000;
    clock.mockReturnValue(start);
    const rateLimit = Object.assign(new BackendApiError("x", "RATE_LIMITED", 429), { retryAfterSeconds: 120 });
    const send = vi.mocked(teacherPresentationApi.createSvgDraft);
    send.mockRejectedValue(rateLimit);
    const first = open();
    await ask();
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" }));
    expect(await screen.findByText("Đã đạt giới hạn tạo SVG. Hãy thử lại sau thời gian chờ.")).toBeTruthy();
    first.unmount();

    clock.mockReturnValue(start + 30_000);
    const second = open();
    await ask();
    expect(screen.getByRole("button", { name: "Thử lại sau 90 giây" })).toBeTruthy();
    expect(screen.queryByText("Đã đạt giới hạn tạo SVG. Hãy thử lại sau thời gian chờ.")).toBeNull();
    second.unmount();

    clock.mockReturnValue(start + 120_000);
    open();
    await ask();
    expect(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" })).toBeTruthy();
    expect(screen.queryByText("Đã đạt giới hạn tạo SVG. Hãy thử lại sau thời gian chờ.")).toBeNull();
    expect(send).toHaveBeenCalledTimes(1);
  });

  it("waits out the server after a long lost connection instead of calling again", async () => {
    vi.mocked(teacherPresentationApi.get).mockResolvedValue(presentation);
    let fail: () => void = () => undefined;
    vi.mocked(teacherPresentationApi.createSvgDraft).mockImplementation(() => new Promise((_, reject) => { fail = () => reject(new BackendApiError("x", "NETWORK_ERROR", 0)); }));
    const first = open();
    await ask();
    const clock = vi.spyOn(Date, "now");
    const start = 1_000_000;
    clock.mockReturnValue(start);
    fireEvent.click(screen.getByRole("button", { name: "Yêu cầu tạo bản SVG" }));
    clock.mockReturnValue(start + 120_000);
    await act(async () => { fail(); });
    expect(await screen.findByText(/Hệ thống có thể vẫn đang tạo/)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Đang chờ kết quả…" }) as HTMLButtonElement).disabled).toBe(true);
    expect(teacherPresentationApi.createSvgDraft).toHaveBeenCalledTimes(1);
    first.unmount();

    open();
    await ask();
    expect(await screen.findByText(/Hệ thống có thể vẫn đang tạo/)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Đang chờ kết quả…" }) as HTMLButtonElement).disabled).toBe(true);
    expect(teacherPresentationApi.createSvgDraft).toHaveBeenCalledTimes(1);
  });
});
