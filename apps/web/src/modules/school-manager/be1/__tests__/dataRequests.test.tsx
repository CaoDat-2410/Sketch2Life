import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminBe1Error } from "../services/be1Client";
import { managerBusinessService, type Be1DataRequest, type Be1DataRequestCreated } from "../services/managerBusinessService";
import { DataRequestsPage } from "../pages/DataRequestsPage";

afterEach(() => {
  cleanup();
  try { window.sessionStorage.clear(); } catch { /* Some test cases make session storage unavailable. */ }
  vi.restoreAllMocks();
});

const createdRequest = (requestId: string): Be1DataRequestCreated => ({
  contract: "Be1DataRequestV1",
  request_id: requestId,
  state: "requested",
  completion_claimed: false,
});

const request = (overrides: Partial<Be1DataRequest> = {}): Be1DataRequest => ({
  contract: "Be1DataRequestV1",
  request_id: "request-1",
  request_type: "export",
  target_ref: "class-1",
  state: "requested",
  unresolved_items: 0,
  completion_claimed: false,
  ...overrides,
});

describe("Manager organization data requests", () => {
  it.each([
    { type: "export" as const, requestId: "export-request-1" },
    { type: "delete" as const, requestId: "delete-request-1" },
  ])("creates a $type request with the typed target and confirms deletion first", async ({ type, requestId }) => {
    const create = vi.spyOn(managerBusinessService, "createDataRequest").mockResolvedValue(createdRequest(requestId));
    render(<MemoryRouter><DataRequestsPage /></MemoryRouter>);

    fireEvent.change(screen.getByLabelText("Tham chiếu đích"), { target: { value: "target-1" } });
    if (type === "delete") {
      fireEvent.click(screen.getByLabelText("Xóa dữ liệu"));
      fireEvent.click(screen.getByRole("button", { name: "Gửi yêu cầu" }));
      expect(screen.getByRole("alertdialog").textContent).toContain("không thể khôi phục");
      expect(create).not.toHaveBeenCalled();
      fireEvent.click(screen.getByRole("button", { name: "Gửi yêu cầu xóa" }));
    } else {
      fireEvent.click(screen.getByRole("button", { name: "Gửi yêu cầu" }));
    }

    await waitFor(() => expect(create).toHaveBeenCalledWith(type, "target-1"));
    expect(await screen.findByText("Đã ghi nhận yêu cầu.")).toBeTruthy();
    expect(await screen.findByText("Đã ghi nhận")).toBeTruthy();
    expect(screen.getAllByText(requestId).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /tải xuống/i })).toBeNull();
    expect(screen.queryByText(/Đã hoàn tất/)).toBeNull();
  });

  it("locks rapid double submit because the endpoint has no idempotency key", async () => {
    let finishCreate!: (value: Be1DataRequestCreated) => void;
    const pending = new Promise<Be1DataRequestCreated>((resolve) => { finishCreate = resolve; });
    const create = vi.spyOn(managerBusinessService, "createDataRequest").mockReturnValue(pending);
    render(<MemoryRouter><DataRequestsPage /></MemoryRouter>);

    fireEvent.change(screen.getByLabelText("Tham chiếu đích"), { target: { value: "child-ref" } });
    const submit = screen.getByRole("button", { name: "Gửi yêu cầu" });
    fireEvent.click(submit);
    fireEvent.click(submit);
    expect(create).toHaveBeenCalledTimes(1);
    expect((submit as HTMLButtonElement).disabled).toBe(true);

    finishCreate(createdRequest("request-once"));
    expect(await screen.findByText("Đã ghi nhận yêu cầu.")).toBeTruthy();
  });

  it.each([
    ["requested", "Đã ghi nhận", false],
    ["running", "Đang xử lý", false],
    ["awaiting_external_purge", "Đang chờ xóa dữ liệu bên ngoài", false],
    ["completed", "Chờ xác nhận hoàn tất", false],
    ["exception", "Cần xử lý", false],
  ] as const)("shows the safe Vietnamese label for %s without claiming completion", async (state, label, completionClaimed) => {
    const lookup = vi.spyOn(managerBusinessService, "getDataRequest").mockResolvedValue(request({ request_id: "lookup-1", state, completion_claimed: completionClaimed }));
    render(<MemoryRouter><DataRequestsPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText("Mã yêu cầu"), { target: { value: "lookup-1" } });
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra trạng thái" }));

    expect(await screen.findByText(label)).toBeTruthy();
    expect(await screen.findByText("BE1 chưa xác nhận yêu cầu hoàn tất.")).toBeTruthy();
    expect(screen.queryByText(/Đã hoàn tất/)).toBeNull();
    expect(screen.queryByRole("button", { name: /tải xuống/i })).toBeNull();
    expect(lookup).toHaveBeenCalledWith("lookup-1");
  });

  it("claims completion only when the backend completion flag is true", async () => {
    vi.spyOn(managerBusinessService, "getDataRequest").mockResolvedValue(request({
      request_id: "lookup-done", state: "completed", completion_claimed: true,
    }));
    render(<MemoryRouter><DataRequestsPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText("Mã yêu cầu"), { target: { value: "lookup-done" } });
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra trạng thái" }));

    expect(await screen.findByText("Đã hoàn tất")).toBeTruthy();
    expect(await screen.findByText("BE1 xác nhận yêu cầu đã hoàn tất.")).toBeTruthy();
  });

  it("shows a uniform 404 lookup state without raw response text", async () => {
    vi.spyOn(managerBusinessService, "getDataRequest").mockRejectedValue(new AdminBe1Error("secret body", 404, "DATA_REQUEST_NOT_FOUND"));
    render(<MemoryRouter><DataRequestsPage /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText("Mã yêu cầu"), { target: { value: "missing-id" } });
    fireEvent.click(screen.getByRole("button", { name: "Kiểm tra trạng thái" }));

    expect(await screen.findByText("Không tìm thấy yêu cầu hoặc bạn không có quyền truy cập.")).toBeTruthy();
    expect(document.body.textContent).not.toContain("secret body");
    expect(document.body.textContent).not.toContain("DATA_REQUEST_NOT_FOUND");
  });

  it("tolerates sessionStorage read and write failures", async () => {
    vi.spyOn(window.sessionStorage, "getItem").mockImplementation(() => { throw new Error("storage blocked"); });
    vi.spyOn(window.sessionStorage, "setItem").mockImplementation(() => { throw new Error("storage blocked"); });
    vi.spyOn(managerBusinessService, "createDataRequest").mockResolvedValue(createdRequest("request-memory-only"));
    render(<MemoryRouter><DataRequestsPage /></MemoryRouter>);

    expect(await screen.findByText("Chưa có mã yêu cầu nào trong phiên này.")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Tham chiếu đích"), { target: { value: "org-1" } });
    fireEvent.click(screen.getByRole("button", { name: "Gửi yêu cầu" }));

    expect(await screen.findByText("Đã ghi nhận yêu cầu.")).toBeTruthy();
    expect(screen.getAllByText("request-memory-only").length).toBeGreaterThan(0);
  });
});
