// Goal v3 Phase B (T-7a/T-7b): A07 paging and state filter, class suspend/archive with class revision.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminBe1Error } from "../services/be1Client";
import { ClassesPage } from "../pages/ClassesPage";
import { allowedClassCommands, classService, classStateOutcomeMessage, type Be1Class } from "../services/classService";

beforeEach(() => {
  vi.stubEnv("VITE_BE1_BASE_URL", "https://api.example.test");
  vi.stubEnv("VITE_BE1_ORGANIZATION_ID", "org-test");
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

async function stubFetch(replies: Array<{ status: number; body: unknown }>) {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    const reply = replies.shift()!;
    return new Response(JSON.stringify(reply.body), { status: reply.status, headers: { "Content-Type": "application/json" } });
  }));
  const { authService } = await import("../services/authService");
  vi.spyOn(authService, "getIdToken").mockResolvedValue("unit-test-id-token");
  return calls;
}

const klass = (id: string, state: Be1Class["state"], revision = 1): Be1Class => ({
  class_id: id, display_name: "Lớp " + id, state, class_revision: revision, assignment_revision: 1, has_active_teacher: true,
});

describe("classService A07 paging and state filter", () => {
  it("follows next_cursor to the end with the state filter and page limit", async () => {
    const calls = await stubFetch([
      { status: 200, body: { contract: "Be1ClassListV1", items: [klass("a", "active")], next_cursor: "cur/2" } },
      { status: 200, body: { contract: "Be1ClassListV1", items: [klass("b", "suspended")], next_cursor: null } },
    ]);
    const items = await classService.listClasses("all");
    expect(items.map((item) => item.class_id)).toEqual(["a", "b"]);
    expect(calls).toHaveLength(2);
    const first = new URL(calls[0].url);
    expect(first.pathname).toBe("/api/be1/v1/organizations/org-test/classes");
    expect(Object.fromEntries(first.searchParams)).toEqual({ state: "all", limit: "100" });
    expect(Object.fromEntries(new URL(calls[1].url).searchParams)).toEqual({ state: "all", limit: "100", cursor: "cur/2" });
  });

  it("stops when the server repeats a cursor", async () => {
    const calls = await stubFetch([
      { status: 200, body: { items: [klass("a", "active")], next_cursor: "same" } },
      { status: 200, body: { items: [klass("b", "active")], next_cursor: "same" } },
    ]);
    const items = await classService.listClasses("active");
    expect(items).toHaveLength(2);
    expect(calls).toHaveLength(2);
  });
});

describe("classService suspend/archive (T-7b)", () => {
  it("sends no body, the action key and the strong class-revision If-Match", async () => {
    const calls = await stubFetch([{ status: 200, body: { contract: "Be1ClassStateV1", class_id: "c/1", state: "suspended", class_revision: 5 } }]);
    const result = await classService.changeClassState("c/1", "suspend", 4, "key-1");
    expect(result).toEqual({ contract: "Be1ClassStateV1", class_id: "c/1", state: "suspended", class_revision: 5 });
    expect(calls[0].url).toBe("https://api.example.test/api/be1/v1/classes/c%2F1/suspend");
    expect(calls[0].init.method).toBe("POST");
    expect(calls[0].init.body).toBeUndefined();
    const headers = new Headers(calls[0].init.headers);
    expect(headers.get("If-Match")).toBe('"4"');
    expect(headers.get("Idempotency-Key")).toBe("key-1");
  });

  it("uses the archive path and keeps STALE_REVISION as a typed error", async () => {
    await stubFetch([{ status: 409, body: { code: "STALE_REVISION", message: "Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", correlation_id: "r-1", retryable: false, current_version: 6 } }]);
    const error = await classService.changeClassState("c-1", "archive", 4, "key-2").catch((cause: unknown) => cause);
    expect(error).toBeInstanceOf(AdminBe1Error);
    expect((error as AdminBe1Error).code).toBe("STALE_REVISION");
    expect((error as AdminBe1Error).status).toBe(409);
  });

  it("offers only the backend transitions; archived is terminal with no restore", () => {
    expect(allowedClassCommands("active")).toEqual(["suspend", "archive"]);
    expect(allowedClassCommands("suspended")).toEqual(["archive"]);
    expect(allowedClassCommands("archived")).toEqual([]);
  });

  it.each([
    [new AdminBe1Error("Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", 409, "STALE_REVISION"), /Thông tin đã thay đổi.*hãy kiểm tra rồi xác nhận lại/, true, false],
    [new AdminBe1Error("x", 409, "INVALID_STATE_TRANSITION"), /không còn ở trạng thái cho phép/, true, false],
    [new AdminBe1Error("x", 404, "RESOURCE_NOT_FOUND"), /Không tìm thấy lớp hoặc bạn không có quyền truy cập/, true, false],
    [new AdminBe1Error("x", 403, "ACTION_NOT_ALLOWED"), /không được phép thực hiện thao tác này/, false, false],
    [new AdminBe1Error("Khóa yêu cầu trùng với một yêu cầu có nội dung khác.", 400, "INVALID_IDEMPOTENCY_KEY"), /Khóa yêu cầu trùng/, false, false],
    [new AdminBe1Error("Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.", 429, "RATE_LIMITED"), /quá nhiều yêu cầu/, false, false],
    [new AdminBe1Error("Dịch vụ tạm thời chưa sẵn sàng.", 503, "PROVIDER_UNAVAILABLE"), /gửi lại cùng yêu cầu/, false, true],
    [new TypeError("Failed to fetch"), /gửi lại cùng yêu cầu/, false, true],
  ])("maps %s to the SRS recovery", (cause, text, reload, keepKey) => {
    const outcome = classStateOutcomeMessage(cause);
    expect(outcome.text).toMatch(text);
    expect(outcome.reload).toBe(reload);
    expect(outcome.keepKey).toBe(keepKey);
  });
});

describe("ClassesPage class lifecycle", () => {
  it("lists every state by default with Vietnamese labels and re-lists on a filter change", async () => {
    const list = vi.spyOn(classService, "listClasses").mockResolvedValue([klass("a", "active"), klass("s", "suspended"), klass("x", "archived")]);
    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    expect((await screen.findAllByText("Tạm ngưng")).length).toBeGreaterThan(0);
    expect(screen.getAllByText("Đã lưu trữ").length).toBeGreaterThan(0);
    expect(list).toHaveBeenCalledWith("all");
    fireEvent.change(screen.getByLabelText("Trạng thái lớp"), { target: { value: "suspended" } });
    await waitFor(() => expect(list).toHaveBeenLastCalledWith("suspended"));
  });

  it("suspends only after an explicit confirm and sends the class revision", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([klass("a", "active", 3)]);
    const change = vi.spyOn(classService, "changeClassState").mockResolvedValue({ contract: "Be1ClassStateV1", class_id: "a", state: "suspended", class_revision: 4 });
    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Tạm ngưng lớp" }));
    expect(change).not.toHaveBeenCalled();
    expect(screen.getByText(/Lớp tạm ngưng chỉ đọc, mọi dữ liệu vẫn được giữ./)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tạm ngưng" }));
    await waitFor(() => expect(change).toHaveBeenCalledTimes(1));
    expect(change.mock.calls[0].slice(0, 3)).toEqual(["a", "suspend", 3]);
    expect(change.mock.calls[0][3]).toBeTruthy();
    expect(await screen.findByText(/Đã tạm ngưng lớp/)).toBeTruthy();
  });

  it("offers only archive for a suspended class and nothing (no restore) for an archived class", async () => {
    vi.spyOn(classService, "listClasses").mockResolvedValue([klass("s", "suspended"), klass("x", "archived")]);
    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    expect(await screen.findByRole("button", { name: "Lưu trữ lớp" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Tạm ngưng lớp" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Lớp x/ }));
    expect(screen.queryByRole("button", { name: "Lưu trữ lớp" })).toBeNull();
    expect(screen.queryByRole("button", { name: /khôi phục|kích hoạt/i })).toBeNull();
    expect(screen.getByText(/không có thao tác khôi phục/)).toBeTruthy();
  });

  it("reuses the key only for an unclear failure and reloads after STALE_REVISION", async () => {
    const list = vi.spyOn(classService, "listClasses").mockResolvedValue([klass("a", "active", 3)]);
    const change = vi.spyOn(classService, "changeClassState")
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockRejectedValueOnce(new AdminBe1Error("Thông tin đã thay đổi. Vui lòng tải lại và thử lại.", 409, "STALE_REVISION"))
      .mockResolvedValueOnce({ contract: "Be1ClassStateV1", class_id: "a", state: "archived", class_revision: 4 });
    render(<MemoryRouter><ClassesPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Lưu trữ lớp" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận lưu trữ" }));
    expect((await screen.findByRole("alert")).textContent).toContain("gửi lại cùng yêu cầu");
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận lưu trữ" }));
    await waitFor(() => expect(change).toHaveBeenCalledTimes(2));
    expect(change.mock.calls[1][3]).toBe(change.mock.calls[0][3]);
    expect((await screen.findByRole("alert")).textContent).toContain("hãy kiểm tra rồi xác nhận lại");
    await waitFor(() => expect(list.mock.calls.length).toBeGreaterThanOrEqual(2));
    // The stale refusal closed the confirm step; the next press is a new command with a new key.
    fireEvent.click(await screen.findByRole("button", { name: "Lưu trữ lớp" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận lưu trữ" }));
    await waitFor(() => expect(change).toHaveBeenCalledTimes(3));
    expect(change.mock.calls[2][3]).not.toBe(change.mock.calls[0][3]);
  });
});
