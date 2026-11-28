import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { OccurrenceApiError } from "../../../../shared/api/teacherHttp";
import type { PublicLessonHit, RemixLessonResult } from "../../../../shared/api/teacherLessonLibraryApi";

const api = vi.hoisted(() => ({ searchPublicLessons: vi.fn(), remixLesson: vi.fn() }));
vi.mock("../../../../shared/api/teacherLessonLibraryApi", async () => ({
  ...(await vi.importActual("../../../../shared/api/teacherLessonLibraryApi")),
  searchPublicLessons: api.searchPublicLessons,
  remixLesson: api.remixLesson,
}));

import { PublicLessonSearchPanel } from "../PublicLessonSearchPanel";

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

function hit(versionId: string, title = "Vẽ con mèo", ageBandRef = "age-band-4"): PublicLessonHit {
  return {
    contract: "PublicLessonHitV1", lesson_id: "public-lesson", version_id: versionId,
    structured_content_hash: versionId === "version-1" ? "a".repeat(64) : "b".repeat(64),
    title, topic: "Động vật", target_age_band_ref: ageBandRef, target_age_band_version: 1,
    activity_count: 2, updated_at: "2026-11-20T00:00:00Z",
  };
}

describe("PublicLessonSearchPanel", () => {
  it("keeps the filters on each page and resets paging when an input changes", async () => {
    api.searchPublicLessons
      .mockResolvedValueOnce({ contract: "PublicLessonSearchPageV1", items: [hit("version-1", "Kết quả đầu")], next_cursor: "next-cursor" })
      .mockResolvedValueOnce({ contract: "PublicLessonSearchPageV1", items: [hit("version-2", "Kết quả sau")], next_cursor: null })
      .mockResolvedValueOnce({ contract: "PublicLessonSearchPageV1", items: [hit("version-1", "Kết quả mới")], next_cursor: null });
    const { container } = render(<PublicLessonSearchPanel organizationId="org-1" onRemixed={vi.fn()} />);
    expect(container.querySelector("section.tw-card")).toBeNull();
    expect(screen.queryByText("Khám phá bài học đã công khai")).toBeNull();
    expect(screen.getByRole("button", { name: "Tìm kiếm" }).className).toContain("bg-transparent");
    expect(screen.getByRole("combobox", { name: /Nhóm tuổi/ }).textContent).toContain("Tất cả");

    fireEvent.change(screen.getByLabelText("Từ khóa"), { target: { value: "Mèo" } });
    fireEvent.change(screen.getByLabelText("Chủ đề"), { target: { value: "Động vật" } });
    fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));
    expect(await screen.findByText("Kết quả đầu")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Tải thêm kết quả" }));
    expect(await screen.findByText("Kết quả sau")).toBeTruthy();
    expect(api.searchPublicLessons).toHaveBeenNthCalledWith(1, "org-1", { q: "Mèo", topic: "Động vật", targetAgeBandRef: undefined, targetAgeBandVersion: undefined });
    expect(api.searchPublicLessons).toHaveBeenNthCalledWith(2, "org-1", { q: "Mèo", topic: "Động vật", targetAgeBandRef: undefined, targetAgeBandVersion: undefined, cursor: "next-cursor" });

    fireEvent.change(screen.getByLabelText("Chủ đề"), { target: { value: "Cây" } });
    expect(screen.queryByText("Kết quả sau")).toBeNull();
    expect(screen.queryByRole("button", { name: "Tải thêm kết quả" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));
    expect(await screen.findByText("Kết quả mới")).toBeTruthy();
    expect(api.searchPublicLessons).toHaveBeenNthCalledWith(3, "org-1", { q: "Mèo", topic: "Cây", targetAgeBandRef: undefined, targetAgeBandVersion: undefined });
  });

  it("sends a selected age band and shows labels instead of raw result refs", async () => {
    const legacyRef = "age-band-legacy-unknown";
    api.searchPublicLessons.mockResolvedValue({
      contract: "PublicLessonSearchPageV1",
      items: [
        hit("version-1", "Kết quả có nhóm tuổi", "age-36-71-months-v1"),
        hit("version-2", "Kết quả nhóm tuổi cũ", legacyRef),
      ],
      next_cursor: null,
    });
    render(<PublicLessonSearchPanel organizationId="org-1" onRemixed={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Từ khóa"), { target: { value: "Mèo" } });
    const ageBand = screen.getByRole("combobox", { name: /Nhóm tuổi/ });
    fireEvent.click(ageBand);
    fireEvent.click(await screen.findByRole("option", { name: "72–107 tháng" }));
    fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));

    expect(await screen.findByText("Kết quả có nhóm tuổi")).toBeTruthy();
    expect(api.searchPublicLessons).toHaveBeenCalledWith("org-1", {
      q: "Mèo",
      topic: undefined,
      targetAgeBandRef: "age-72-107-months-v1",
      targetAgeBandVersion: 1,
    });
    expect(screen.getByText(/Nhóm tuổi: 36–71 tháng/)).toBeTruthy();
    expect(screen.getByText(/Nhóm tuổi: Nhóm tuổi khác/)).toBeTruthy();
    expect(screen.queryByText(legacyRef)).toBeNull();
  });

  it("reuses an idempotency key after a retryable failure", async () => {
    let keyIndex = 0;
    vi.stubGlobal("crypto", { randomUUID: () => `remix-key-${++keyIndex}` });
    api.searchPublicLessons.mockResolvedValue({ contract: "PublicLessonSearchPageV1", items: [hit("version-1")], next_cursor: null });
    const result = { source: { lesson_id: "public-lesson", version_id: "version-1", content_sha256: "a".repeat(64) }, lesson: { lesson_id: "private-copy" } } as RemixLessonResult;
    api.remixLesson.mockRejectedValueOnce(new OccurrenceApiError("Dịch vụ tạm thời chưa sẵn sàng.", "PROVIDER_UNAVAILABLE", 503, undefined, [], true)).mockResolvedValueOnce(result);
    const onRemixed = vi.fn();
    render(<PublicLessonSearchPanel organizationId="org-1" onRemixed={onRemixed} />);

    fireEvent.change(screen.getByLabelText("Từ khóa"), { target: { value: "Mèo" } });
    fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));
    fireEvent.click(await screen.findByRole("button", { name: "Sao chép thành bản của tôi" }));
    fireEvent.click(await screen.findByRole("button", { name: "Thử lại cùng yêu cầu" }));

    await waitFor(() => expect(api.remixLesson).toHaveBeenCalledTimes(2));
    expect(api.remixLesson.mock.calls[0][3]).toBe("remix-key-1");
    expect(api.remixLesson.mock.calls[1][3]).toBe("remix-key-1");
    expect(onRemixed).toHaveBeenCalledWith(result, hit("version-1"));
    expect(await screen.findByText(/Tạo từ bài công khai/)).toBeTruthy();
  });

  it("refreshes after STALE_SOURCE_VERSION and mints a new key for the updated hit", async () => {
    let keyIndex = 0;
    vi.stubGlobal("crypto", { randomUUID: () => `remix-key-${++keyIndex}` });
    api.searchPublicLessons
      .mockResolvedValueOnce({ contract: "PublicLessonSearchPageV1", items: [hit("version-1")], next_cursor: null })
      .mockResolvedValueOnce({ contract: "PublicLessonSearchPageV1", items: [hit("version-2")], next_cursor: null });
    api.remixLesson
      .mockRejectedValueOnce(new OccurrenceApiError("Bản công khai đã thay đổi.", "STALE_SOURCE_VERSION", 409, undefined, [], false))
      .mockResolvedValueOnce({ source: { lesson_id: "public-lesson", version_id: "version-2", content_sha256: "b".repeat(64) }, lesson: { lesson_id: "private-copy" } });
    render(<PublicLessonSearchPanel organizationId="org-1" onRemixed={vi.fn()} />);

    fireEvent.change(screen.getByLabelText("Từ khóa"), { target: { value: "Mèo" } });
    fireEvent.click(screen.getByRole("button", { name: "Tìm kiếm" }));
    fireEvent.click(await screen.findByRole("button", { name: "Sao chép thành bản của tôi" }));
    expect(await screen.findByText("Kết quả đã được làm mới. Hãy chọn bản mới để sao chép lại.")).toBeTruthy();
    await waitFor(() => expect(api.searchPublicLessons).toHaveBeenCalledTimes(2));
    fireEvent.click(screen.getByRole("button", { name: "Sao chép thành bản của tôi" }));

    await waitFor(() => expect(api.remixLesson).toHaveBeenCalledTimes(2));
    expect(api.remixLesson.mock.calls[0][1]).toBe("public-lesson");
    expect(api.remixLesson.mock.calls[0][2]).toEqual({ sourceVersionId: "version-1", sourceContentSha256: "a".repeat(64) });
    expect(api.remixLesson.mock.calls[0][3]).toBe("remix-key-1");
    expect(api.remixLesson.mock.calls[1][2]).toEqual({ sourceVersionId: "version-2", sourceContentSha256: "b".repeat(64) });
    expect(api.remixLesson.mock.calls[1][3]).toBe("remix-key-2");
  });
});
