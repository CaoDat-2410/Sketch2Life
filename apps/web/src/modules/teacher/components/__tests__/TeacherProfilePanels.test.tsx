import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BackendApiError } from "../../../../shared/api/backendApi";
import { teacherProfileApi } from "../../../../shared/api/teacherProfileApi";
import { OccurrenceApiError } from "../../../../shared/api/teacherHttp";
import { TeacherProfilePanels } from "../TeacherProfilePanels";

vi.mock("../../../../shared/api/teacherProfileApi", () => ({
  teacherProfileApi: {
    listProfileRevisions: vi.fn(),
    getProfileRevision: vi.fn(),
    editProfile: vi.fn(),
    getSupportNeeds: vi.fn(),
    putSupportNeeds: vi.fn(),
  },
}));

const api = vi.mocked(teacherProfileApi);
const revision = (
  revisionNo = 2,
  displayName = "Synthetic Sample",
  ageMonths = 60,
  interests = ["Building"],
) => ({
  contract: "Be1ProfileRevisionV1" as const,
  child_id: "child-1",
  profile_revision_id: `rev-${revisionNo}`,
  revision_no: revisionNo,
  display_name: displayName,
  age_months: ageMonths,
  age_band: { band_version: 1, band_code: "AGE_36_71" as const },
  structured_interests: interests,
  revision_hash: `hash-${revisionNo}`,
  created_at: "2026-11-24T09:00:00Z",
});
const revisionPage = (item = revision(), nextCursor: string | null = null) => ({
  contract: "Be1ProfileRevisionPageV1" as const,
  items: [item],
  next_cursor: nextCursor,
});
const supportValue = (revisionNo = 1, category: string | null = "fixture category", note: string | null = "fixture note") => ({
  contract: "Be1SupportNeedsV1" as const,
  child_id: "child-1",
  revision: revisionNo,
  category,
  note,
});
const editResult = { contract: "Be1ProfileEditResultV1" as const, child_id: "child-1", profile_revision_id: "rev-3", revision_no: 3, revision_hash: "hash-3" };
const supportWrite = { contract: "Be1SupportNeedsWriteV1" as const, child_id: "child-1", revision: 1 };

function renderPanels(onProfileSaved = vi.fn()) {
  return {
    onProfileSaved,
    ...render(<TeacherProfilePanels organizationId="org-1" classId="class-1" childId="child-1" canEdit onProfileSaved={onProfileSaved} />),
  };
}

beforeEach(() => {
  api.listProfileRevisions.mockReset();
  api.getProfileRevision.mockReset();
  api.editProfile.mockReset();
  api.getSupportNeeds.mockReset();
  api.putSupportNeeds.mockReset();
  api.listProfileRevisions.mockResolvedValue(revisionPage());
  api.getProfileRevision.mockResolvedValue(revision());
  api.editProfile.mockResolvedValue(editResult);
  api.getSupportNeeds.mockResolvedValue(supportValue());
  api.putSupportNeeds.mockResolvedValue(supportWrite);
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("Teacher profile revision panel", () => {
  it("loads history only after open, shows no author, and pages on demand", async () => {
    const newest = revision(2);
    api.listProfileRevisions
      .mockResolvedValueOnce({ ...revisionPage(newest), items: [{ ...newest, author: "Never rendered" } as never, revision(1, "Synthetic Earlier")], next_cursor: "opaque /+?=cursor" })
      .mockResolvedValueOnce(revisionPage(revision(3, "Synthetic New")));
    renderPanels();
    expect(api.listProfileRevisions).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Lịch sử hồ sơ" }));
    expect(await screen.findByText("Phiên bản 2")).toBeTruthy();
    const newestCard = document.querySelectorAll(".teacher-profile-revision")[0];
    expect(newestCard?.textContent).toContain("60 tháng · 36–71 tháng");
    expect(newestCard?.textContent).toContain("Sở thích: Building");
    expect(newestCard?.textContent).toContain("Thời điểm:");
    expect(Array.from(document.querySelectorAll(".teacher-profile-revision h4")).map((item) => item.textContent)).toEqual(["Phiên bản 2", "Phiên bản 1"]);
    expect(screen.queryByText("Never rendered")).toBeNull();
    expect(api.listProfileRevisions).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Tải thêm" }));
    expect(await screen.findByText("Phiên bản 3")).toBeTruthy();
    expect(api.listProfileRevisions).toHaveBeenNthCalledWith(2, "org-1", "class-1", "child-1", "opaque /+?=cursor");
  });

  it("sends only changed fields with the head revision and refreshes both views", async () => {
    const { onProfileSaved } = renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Lịch sử hồ sơ" }));
    await screen.findByText("Phiên bản 2");
    fireEvent.click(screen.getByRole("button", { name: "Sửa hồ sơ" }));
    fireEvent.change(screen.getByLabelText("Tuổi (tháng)"), { target: { value: "72" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    await waitFor(() => expect(api.editProfile).toHaveBeenCalledTimes(1));
    expect(api.editProfile).toHaveBeenCalledWith("org-1", "class-1", "child-1", { expected_revision: 2, age_months: 72 }, expect.stringMatching(/^[\x21-\x7E]{1,128}$/));
    expect(onProfileSaved).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(api.listProfileRevisions).toHaveBeenCalledTimes(2));
  });

  it("reuses a key for a retry and creates a new key after the form changes", async () => {
    api.editProfile
      .mockRejectedValueOnce(new BackendApiError("private server message", "PROVIDER_UNAVAILABLE", 503))
      .mockRejectedValueOnce(new BackendApiError("private server message", "PROVIDER_UNAVAILABLE", 503))
      .mockResolvedValueOnce(editResult);
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Lịch sử hồ sơ" }));
    await screen.findByText("Phiên bản 2");
    fireEvent.click(screen.getByRole("button", { name: "Sửa hồ sơ" }));
    fireEvent.change(screen.getByLabelText("Tuổi (tháng)"), { target: { value: "72" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    expect(await screen.findByText("Chưa thể hoàn tất thao tác lúc này. Hãy thử lại sau.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Thử lại cùng yêu cầu" }));
    await waitFor(() => expect(api.editProfile).toHaveBeenCalledTimes(2));
    const firstKey = api.editProfile.mock.calls[0][4];
    const retryKey = api.editProfile.mock.calls[1][4];
    expect(retryKey).toBe(firstKey);
    fireEvent.change(screen.getByLabelText("Tuổi (tháng)"), { target: { value: "84" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    await waitFor(() => expect(api.editProfile).toHaveBeenCalledTimes(3));
    expect(api.editProfile.mock.calls[2][4]).not.toBe(firstKey);
  });

  it("reloads the head after a stale edit and asks for review", async () => {
    api.listProfileRevisions
      .mockResolvedValueOnce(revisionPage(revision(2)))
      .mockResolvedValueOnce(revisionPage(revision(3, "Synthetic Updated", 72, ["Blocks"])));
    api.editProfile.mockRejectedValueOnce(new BackendApiError("private server message", "STALE_REVISION", 409));
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Lịch sử hồ sơ" }));
    await screen.findByText("Phiên bản 2");
    fireEvent.click(screen.getByRole("button", { name: "Sửa hồ sơ" }));
    fireEvent.change(screen.getByLabelText("Tuổi (tháng)"), { target: { value: "84" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    expect(await screen.findByText("Thông tin đã thay đổi. Đã tải bản mới nhất; hãy kiểm tra lại trước khi lưu.")).toBeTruthy();
    expect((screen.getByLabelText("Tên hiển thị") as HTMLInputElement).value).toBe("Synthetic Updated");
    expect(screen.queryByText("private server message")).toBeNull();
  });

  it("maps diagnosis field errors without echoing text", async () => {
    api.editProfile.mockRejectedValueOnce(new OccurrenceApiError(
      "private server message",
      "INVALID_REQUEST",
      400,
      "request-1",
      [{ field: "structured_interests.0", code: "DIAGNOSIS_LIKE" }],
    ));
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Lịch sử hồ sơ" }));
    await screen.findByText("Phiên bản 2");
    fireEvent.click(screen.getByRole("button", { name: "Sửa hồ sơ" }));
    fireEvent.change(screen.getByLabelText("Sở thích"), { target: { value: "fixture stem" } });
    fireEvent.click(screen.getByRole("button", { name: "Thêm sở thích" }));
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    expect(await screen.findByText("Sở thích không nên nêu chẩn đoán.")).toBeTruthy();
    expect(screen.queryByText("private server message")).toBeNull();
  });

  it.each([
    [404, "RESOURCE_NOT_FOUND", "Không tìm thấy nội dung hoặc bạn không có quyền truy cập. Hãy làm mới danh sách."],
    [409, "CONSENT_NOT_EFFECTIVE", "Hồ sơ hiện chưa khả dụng để chỉnh sửa."],
    [409, "INVALID_STATE_TRANSITION", "Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ."],
    [503, "PROVIDER_UNAVAILABLE", "Chưa thể hoàn tất thao tác lúc này. Hãy thử lại sau."],
  ])("uses safe profile copy for status %s", async (status, code, safeText) => {
    api.editProfile.mockRejectedValueOnce(new BackendApiError("private server message", code, status));
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Lịch sử hồ sơ" }));
    await screen.findByText("Phiên bản 2");
    fireEvent.click(screen.getByRole("button", { name: "Sửa hồ sơ" }));
    fireEvent.change(screen.getByLabelText("Tuổi (tháng)"), { target: { value: "72" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu thay đổi" }));
    expect(await screen.findByText(safeText)).toBeTruthy();
    expect(screen.queryByText("private server message")).toBeNull();
  });
});

describe("Teacher support-needs panel", () => {
  it.each([
    [404, "RESOURCE_NOT_FOUND"],
    [503, "SUPPORT_NEEDS_UNAVAILABLE"],
    [409, "CONSENT_NOT_EFFECTIVE"],
  ])("uses the same neutral unavailable copy for status %s", async (status, code) => {
    api.getSupportNeeds.mockRejectedValueOnce(new BackendApiError("private server message", code, status));
    renderPanels();
    expect(api.getSupportNeeds).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Mục này chưa khả dụng.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Thử lại" })).toBeTruthy();
    expect(screen.queryByText("private server message")).toBeNull();
  });

  it("writes both fields with expected_revision and does not fetch until open", async () => {
    api.getSupportNeeds
      .mockResolvedValueOnce(supportValue(0, null, null))
      .mockResolvedValueOnce(supportValue(1, "fixture category", "fixture note"));
    renderPanels();
    expect(api.getSupportNeeds).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Phiên bản 0")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sửa nhu cầu hỗ trợ" }));
    fireEvent.change(screen.getByLabelText("Danh mục"), { target: { value: "  fixture category  " } });
    fireEvent.change(screen.getByLabelText("Ghi chú"), { target: { value: "\nfixture note\t" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu nhu cầu hỗ trợ" }));
    await waitFor(() => expect(api.putSupportNeeds).toHaveBeenCalledTimes(1));
    expect(api.putSupportNeeds).toHaveBeenCalledWith(
      "org-1", "class-1", "child-1",
      { expected_revision: 0, category: "  fixture category  ", note: "\nfixture note\t" },
      expect.stringMatching(/^[\x21-\x7E]{1,128}$/),
    );
    expect(await screen.findByText("Đã lưu nhu cầu hỗ trợ.")).toBeTruthy();
  });

  it("reuses the same support-needs key after a 503 retry", async () => {
    api.getSupportNeeds.mockResolvedValueOnce(supportValue(0, null, null)).mockResolvedValueOnce(supportValue(1, "fixture category", null));
    api.putSupportNeeds
      .mockRejectedValueOnce(new BackendApiError("private server message", "SUPPORT_NEEDS_UNAVAILABLE", 503))
      .mockResolvedValueOnce(supportWrite);
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    await screen.findByText("Phiên bản 0");
    fireEvent.click(screen.getByRole("button", { name: "Sửa nhu cầu hỗ trợ" }));
    fireEvent.change(screen.getByLabelText("Danh mục"), { target: { value: "fixture category" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Mục này chưa khả dụng.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
    await waitFor(() => expect(api.putSupportNeeds).toHaveBeenCalledTimes(2));
    expect(api.putSupportNeeds.mock.calls[1][4]).toBe(api.putSupportNeeds.mock.calls[0][4]);
    expect(await screen.findByText("fixture category")).toBeTruthy();
  });

  it("clears displayed support values on close and never writes them to logs or storage", async () => {
    let resolveSecond!: (value: ReturnType<typeof supportValue>) => void;
    const secondRead = new Promise<ReturnType<typeof supportValue>>((resolve) => { resolveSecond = resolve; });
    api.getSupportNeeds.mockResolvedValueOnce(supportValue()).mockReturnValueOnce(secondRead);
    const log = vi.spyOn(console, "log").mockImplementation(() => undefined);
    const info = vi.spyOn(console, "info").mockImplementation(() => undefined);
    const debug = vi.spyOn(console, "debug").mockImplementation(() => undefined);
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);
    const error = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const trace = vi.spyOn(console, "trace").mockImplementation(() => undefined);
    const setItem = vi.spyOn(Storage.prototype, "setItem");
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    expect(await screen.findByText("fixture note")).toBeTruthy();
    expect(log).not.toHaveBeenCalled();
    expect(info).not.toHaveBeenCalled();
    expect(debug).not.toHaveBeenCalled();
    expect(warn).not.toHaveBeenCalled();
    expect(error).not.toHaveBeenCalled();
    expect(trace).not.toHaveBeenCalled();
    expect(setItem).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Đóng" }));
    expect(screen.queryByText("fixture note")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Đang tải mục này…")).toBeTruthy();
    expect(screen.queryByText("fixture note")).toBeNull();
    resolveSecond(supportValue(2, "new fixture category", "new fixture note"));
    expect(await screen.findByText("new fixture note")).toBeTruthy();
    expect(api.getSupportNeeds).toHaveBeenCalledTimes(2);
  });

  it("maps diagnosis field errors and rejects control characters without echoing values", async () => {
    api.putSupportNeeds.mockRejectedValueOnce(new OccurrenceApiError(
      "private server message",
      "INVALID_REQUEST",
      400,
      "request-2",
      [{ field: "category", code: "DIAGNOSIS_LIKE" }],
    ));
    api.getSupportNeeds.mockResolvedValue(supportValue(0, null, null));
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    await screen.findByText("Phiên bản 0");
    fireEvent.click(screen.getByRole("button", { name: "Sửa nhu cầu hỗ trợ" }));
    fireEvent.change(screen.getByLabelText("Danh mục"), { target: { value: "fixture category" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Thông tin hỗ trợ không nên nêu chẩn đoán.")).toBeTruthy();
    expect(screen.queryByText("private server message")).toBeNull();
    fireEvent.change(screen.getByLabelText("Ghi chú"), { target: { value: "bad\u0001input" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Ghi chú có ký tự không được hỗ trợ.")).toBeTruthy();
    expect(api.putSupportNeeds).toHaveBeenCalledTimes(1);
  });

  it("reloads the support revision after a stale write and requires another review", async () => {
    api.getSupportNeeds
      .mockResolvedValueOnce(supportValue(1, "old category", "old note"))
      .mockResolvedValueOnce(supportValue(2, "new category", "new note"));
    api.putSupportNeeds.mockRejectedValueOnce(new BackendApiError("private server message", "STALE_REVISION", 409));
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Phiên bản 1")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sửa nhu cầu hỗ trợ" }));
    fireEvent.change(screen.getByLabelText("Ghi chú"), { target: { value: "changed note" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Thông tin đã thay đổi. Đã tải bản mới nhất; hãy kiểm tra lại trước khi lưu.")).toBeTruthy();
    expect(screen.getByText("Phiên bản 2")).toBeTruthy();
    expect((screen.getByLabelText("Ghi chú") as HTMLTextAreaElement).value).toBe("new note");
    expect(screen.queryByText("private server message")).toBeNull();
  });

  it("maps a class-state refusal to the shared read-only copy", async () => {
    api.getSupportNeeds.mockResolvedValue(supportValue(0, null, null));
    api.putSupportNeeds.mockRejectedValueOnce(new BackendApiError("private server message", "INVALID_STATE_TRANSITION", 409));
    renderPanels();
    fireEvent.click(screen.getByRole("button", { name: "Nhu cầu hỗ trợ" }));
    await screen.findByText("Phiên bản 0");
    fireEvent.click(screen.getByRole("button", { name: "Sửa nhu cầu hỗ trợ" }));
    fireEvent.change(screen.getByLabelText("Danh mục"), { target: { value: "fixture category" } });
    fireEvent.click(screen.getByRole("button", { name: "Lưu nhu cầu hỗ trợ" }));
    expect(await screen.findByText("Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ.")).toBeTruthy();
    expect(screen.queryByText("private server message")).toBeNull();
  });
});
