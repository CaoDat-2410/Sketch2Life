import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { act, cleanup, configure, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { authService } from "../services/authService";
import { AdminBe1Error } from "../services/be1Client";
import { classService, type Be1TeacherCandidate } from "../services/classService";
import {
  storyRunForceCloseService,
  type ManagerActiveStoryRunConflictV1,
} from "../services/storyRunForceCloseService";
import { StoryRunForceClosePanel } from "../pages/StoryRunForceClosePanel";

configure({ asyncUtilTimeout: 8000 });

const teacher: Be1TeacherCandidate = { candidate_ref: "teacher-account-1", display_name: "Cô Lan" };
const conflict: ManagerActiveStoryRunConflictV1 = {
  contract: "ManagerActiveStoryRunConflictV1",
  run_id: "12345678-aaaa-bbbb-cccc-12345678def0",
  run_state: "RUNNING",
  revision: 7,
};

function beginServiceSpies() {
  const getConflict = vi.spyOn(storyRunForceCloseService, "getActiveConflict").mockResolvedValue(conflict);
  const forceClose = vi.spyOn(storyRunForceCloseService, "forceClose").mockResolvedValue({
    contract: "ManagerForceClosedStoryRunV1",
    run_id: conflict.run_id,
    run_state: "ABANDONED",
    revision: 8,
  });
  return { getConflict, forceClose };
}

async function chooseTeacherAndCheck() {
  await selectTeacher();
  fireEvent.click(screen.getByRole("button", { name: "Kiểm tra lượt đang chạy" }));
  await screen.findByText("Đã tìm thấy lượt đang chạy.");
}

async function selectTeacher() {
  fireEvent.click(await screen.findByRole("combobox", { name: "Giáo viên của tổ chức" }));
  fireEvent.click(await screen.findByRole("option", { name: "Cô Lan" }));
}

async function confirmPanel() {
  fireEvent.change(screen.getByRole("textbox", { name: "Lý do đóng khẩn cấp" }), {
    target: { value: "  Teacher bị chặn phân công lại.  " },
  });
  fireEvent.click(screen.getByRole("button", { name: "Xem lại yêu cầu" }));
  expect(screen.getByText("Bạn có chắc muốn đóng khẩn cấp lượt này? Thao tác không hoàn tác được.")).toBeTruthy();
}

beforeEach(() => {
  vi.stubEnv("VITE_BE1_BASE_URL", "https://be1.example.test/");
  vi.stubEnv("VITE_BE1_ORGANIZATION_ID", "org-qa");
  vi.spyOn(authService, "getIdToken").mockResolvedValue("test-token");
  vi.spyOn(classService, "listTeacherCandidates").mockResolvedValue({
    contract: "Be1TeacherCandidatePageV1",
    items: [teacher],
    next_cursor: null,
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("StoryRunForceClosePanel", () => {
  it("loads Teacher candidates when the panel mounts", async () => {
    const list = vi.mocked(classService.listTeacherCandidates);
    render(<StoryRunForceClosePanel />);

    await waitFor(() => expect(list).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole("combobox", { name: "Giáo viên của tổ chức" }));
    expect(await screen.findByRole("option", { name: "Cô Lan" })).toBeTruthy();
  });

  it("distinguishes duplicate Teacher labels without showing candidate references", async () => {
    vi.mocked(classService.listTeacherCandidates).mockResolvedValue({
      contract: "Be1TeacherCandidatePageV1",
      items: [
        { candidate_ref: "private-ref-a", display_name: null, email_masked: "s***@school.test" },
        { candidate_ref: "private-ref-b", display_name: null, email_masked: "s***@school.test" },
        { candidate_ref: "private-ref-c", display_name: null },
        { candidate_ref: "private-ref-d", display_name: null },
      ],
      next_cursor: null,
    });
    render(<StoryRunForceClosePanel />);

    fireEvent.click(await screen.findByRole("combobox", { name: "Giáo viên của tổ chức" }));

    expect(await screen.findByRole("option", { name: "s***@school.test (1)" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "s***@school.test (2)" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Giáo viên chưa có tên hiển thị (1)" })).toBeTruthy();
    expect(screen.getByRole("option", { name: "Giáo viên chưa có tên hiển thị (2)" })).toBeTruthy();
    expect(screen.queryByText(/private-ref/)).toBeNull();
  });

  it("checks a Teacher, confirms the exact command, and sends its idempotency header", async () => {
    const calls: Array<{ url: string; init: RequestInit }> = [];
    vi.stubGlobal("fetch", vi.fn(async (url: string | URL | Request, init: RequestInit = {}) => {
      calls.push({ url: String(url), init });
      const body = String(url).includes("active-story-run-conflict")
        ? conflict
        : { contract: "ManagerForceClosedStoryRunV1", run_id: conflict.run_id, run_state: "ABANDONED", revision: 8 };
      return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
    }));

    render(<StoryRunForceClosePanel />);
    await chooseTeacherAndCheck();
    expect(screen.getByText("12345678…def0")).toBeTruthy();
    expect(screen.getByText("Đang chạy")).toBeTruthy();
    expect(screen.getByText("7")).toBeTruthy();
    expect(screen.queryByText(conflict.run_id)).toBeNull();

    await confirmPanel();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" }));
    expect(await screen.findByText("Đã đóng lượt (ABANDONED)")).toBeTruthy();

    const post = calls.find((call) => call.init.method === "POST");
    expect(post?.url).toBe("https://be1.example.test/api/be1/v1/organizations/org-qa/story-runs/12345678-aaaa-bbbb-cccc-12345678def0/force-close");
    expect(JSON.parse(String(post?.init.body))).toEqual({
      expected_revision: 7,
      reason: "Teacher bị chặn phân công lại.",
    });
    const headers = new Headers(post?.init.headers);
    expect(headers.get("Idempotency-Key")).toMatch(/^[\x21-\x7E]{1,128}$/);
    expect(headers.get("Cache-Control")).toBe("private, no-store");
    expect(post?.init.cache).toBe("no-store");
    expect(screen.queryByRole("textbox", { name: "Lý do đóng khẩn cấp" })).toBeNull();
  });

  it("shows the calm no-active-run result for a uniform 404", async () => {
    vi.spyOn(storyRunForceCloseService, "getActiveConflict").mockRejectedValue(new AdminBe1Error("private server detail", 404, "RESOURCE_NOT_FOUND"));
    render(<StoryRunForceClosePanel />);

    await selectTeacher();
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra lượt đang chạy" }));

    expect(await screen.findByText("Giáo viên này không có lượt đang chạy.")).toBeTruthy();
    expect(screen.queryByText("private server detail")).toBeNull();
  });

  it("loads Teacher candidates by cursor", async () => {
    const list = vi.mocked(classService.listTeacherCandidates);
    list.mockReset()
      .mockResolvedValueOnce({ contract: "Be1TeacherCandidatePageV1", items: [teacher], next_cursor: "cursor-next" })
      .mockResolvedValueOnce({
        contract: "Be1TeacherCandidatePageV1",
        items: [{ candidate_ref: "teacher-account-2", display_name: "Thầy Minh" }],
        next_cursor: null,
      });
    render(<StoryRunForceClosePanel />);

    await selectTeacher();
    fireEvent.click(await screen.findByRole("button", { name: "Tải thêm Giáo viên" }));

    fireEvent.click(screen.getByRole("combobox", { name: "Giáo viên của tổ chức" }));
    expect(await screen.findByRole("option", { name: "Thầy Minh" })).toBeTruthy();
    expect(list).toHaveBeenNthCalledWith(2, "cursor-next");
  });

  it("uses a ref lock to send once on a rapid double click", async () => {
    const { forceClose } = beginServiceSpies();
    let resolveClose!: (value: Awaited<ReturnType<typeof storyRunForceCloseService.forceClose>>) => void;
    forceClose.mockReturnValue(new Promise((resolve) => { resolveClose = resolve; }));
    render(<StoryRunForceClosePanel />);
    await chooseTeacherAndCheck();
    await confirmPanel();

    const confirm = screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" });
    act(() => {
      fireEvent.click(confirm);
      fireEvent.click(confirm);
    });
    expect(forceClose).toHaveBeenCalledTimes(1);
    resolveClose({ contract: "ManagerForceClosedStoryRunV1", run_id: conflict.run_id, run_state: "ABANDONED", revision: 8 });
    expect(await screen.findByText("Đã đóng lượt (ABANDONED)")).toBeTruthy();
  });

  it("reloads after STALE_REVISION and asks for confirmation without retrying", async () => {
    const { getConflict, forceClose } = beginServiceSpies();
    getConflict.mockResolvedValueOnce(conflict).mockResolvedValueOnce({ ...conflict, revision: 8 });
    forceClose.mockRejectedValueOnce(new AdminBe1Error("raw stale response", 409, "STALE_REVISION"));
    render(<StoryRunForceClosePanel />);
    await chooseTeacherAndCheck();
    await confirmPanel();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" }));

    expect(await screen.findByText("Lượt đã thay đổi. Kiểm tra thông tin mới rồi xác nhận lại.")).toBeTruthy();
    expect(getConflict).toHaveBeenCalledTimes(2);
    expect(forceClose).toHaveBeenCalledTimes(1);
    expect(screen.getByText("8")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Xác nhận đóng khẩn cấp" })).toBeNull();
    expect(screen.queryByText("raw stale response")).toBeNull();
  });

  it("shows a no-permission message for 403", async () => {
    const { forceClose } = beginServiceSpies();
    forceClose.mockRejectedValueOnce(new AdminBe1Error("raw permission detail", 403, "ACTION_NOT_ALLOWED"));
    render(<StoryRunForceClosePanel />);
    await chooseTeacherAndCheck();
    await confirmPanel();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" }));

    expect(await screen.findByText("Bạn không có quyền thực hiện thao tác này.")).toBeTruthy();
    expect(screen.queryByText("raw permission detail")).toBeNull();
  });

  it("reloads after 404 and says the run is gone", async () => {
    const { getConflict, forceClose } = beginServiceSpies();
    getConflict.mockResolvedValueOnce(conflict).mockRejectedValueOnce(new AdminBe1Error("raw not found detail", 404, "RESOURCE_NOT_FOUND"));
    forceClose.mockRejectedValueOnce(new AdminBe1Error("raw not found detail", 404, "RESOURCE_NOT_FOUND"));
    render(<StoryRunForceClosePanel />);
    await chooseTeacherAndCheck();
    await confirmPanel();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" }));

    expect(await screen.findByText("Lượt này không còn tồn tại hoặc đã kết thúc.")).toBeTruthy();
    expect(getConflict).toHaveBeenCalledTimes(2);
    expect(screen.queryByText("raw not found detail")).toBeNull();
  });

  it("maps 400 without echoing server text and assigns a new key after the rejection", async () => {
    const { forceClose } = beginServiceSpies();
    forceClose
      .mockRejectedValueOnce(new AdminBe1Error("server supplied text", 400, "INVALID_REQUEST"))
      .mockResolvedValueOnce({ contract: "ManagerForceClosedStoryRunV1", run_id: conflict.run_id, run_state: "ABANDONED", revision: 8 });
    render(<StoryRunForceClosePanel />);
    await chooseTeacherAndCheck();
    await confirmPanel();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" }));

    expect(await screen.findByText("Yêu cầu chưa hợp lệ. Hãy kiểm tra lý do từ 1 đến 500 ký tự.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" }));
    await waitFor(() => expect(forceClose).toHaveBeenCalledTimes(2));
    expect(forceClose.mock.calls[1][3]).not.toBe(forceClose.mock.calls[0][3]);
    expect(screen.queryByText("server supplied text")).toBeNull();
  });

  it("reuses the same key after a network failure and never echoes its message", async () => {
    const { forceClose } = beginServiceSpies();
    forceClose
      .mockRejectedValueOnce(new TypeError("raw network diagnostic"))
      .mockResolvedValueOnce({ contract: "ManagerForceClosedStoryRunV1", run_id: conflict.run_id, run_state: "ABANDONED", revision: 8 });
    render(<StoryRunForceClosePanel />);
    await chooseTeacherAndCheck();
    await confirmPanel();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" }));

    expect(await screen.findByText("Chưa kết nối được. Hãy thử lại cùng yêu cầu.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận đóng khẩn cấp" }));
    await waitFor(() => expect(forceClose).toHaveBeenCalledTimes(2));
    expect(forceClose.mock.calls[1][3]).toBe(forceClose.mock.calls[0][3]);
    expect(screen.queryByText("raw network diagnostic")).toBeNull();
  });

  it("never renders child data and only shows a shortened run id", async () => {
    const privateConflict = { ...conflict, child_name: "Bé Mật Danh", story_title: "Câu chuyện bí mật" } as ManagerActiveStoryRunConflictV1;
    vi.spyOn(storyRunForceCloseService, "getActiveConflict").mockResolvedValue(privateConflict);
    render(<StoryRunForceClosePanel />);
    await chooseTeacherAndCheck();

    expect(screen.getByText("12345678…def0")).toBeTruthy();
    expect(screen.queryByText(conflict.run_id)).toBeNull();
    expect(screen.queryByText("Bé Mật Danh")).toBeNull();
    expect(screen.queryByText("Câu chuyện bí mật")).toBeNull();
  });
});
