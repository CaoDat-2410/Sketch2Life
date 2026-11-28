import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CapacityServiceError, capacityService, type Be1OrganizationCapacity, type CapacityResponse } from "../services/capacityService";
import { classService, type Be1Class } from "../services/classService";
import { managerBusinessService } from "../services/managerBusinessService";
import { CapacityPage } from "../pages/CapacityPage";

const organization = {
  contract: "Be1OrganizationV1" as const,
  organization_id: "org-qa",
  display_name: "Trường kiểm thử",
};

function capacity(overrides: Partial<Be1OrganizationCapacity> = {}): Be1OrganizationCapacity {
  return {
    contract: "Be1OrganizationCapacityV1",
    organization_id: "org-qa",
    subscription_id: "subscription-private",
    capacity: 20,
    active_class_count: 3,
    available_slots: 17,
    subscription_state: "ACTIVE",
    revision: 5,
    period_start: "2026-01-01T00:00:00Z",
    period_end: "2026-12-31T00:00:00Z",
    scheduled_change: null,
    ...overrides,
  };
}

function result(data: Be1OrganizationCapacity): CapacityResponse {
  return { data, etag: '"' + data.revision + '"', revision: data.revision };
}

function activeClasses(count = 3): Be1Class[] {
  return Array.from({ length: count }, (_, index) => ({
    class_id: "class-private-" + (index + 1),
    display_name: "Lớp " + (index + 1),
    state: "active" as const,
  }));
}

function renderPage() {
  return render(<MemoryRouter><CapacityPage /></MemoryRouter>);
}

async function beginDowngrade(classCount = 3) {
  vi.mocked(classService.listClasses).mockResolvedValue(activeClasses(classCount));
  fireEvent.click(await screen.findByRole("button", { name: "Lên lịch hạ sức chứa" }));
  return screen.findByRole("checkbox", { name: "Tạm ngưng lớp Lớp 1" });
}

beforeEach(() => {
  vi.spyOn(managerBusinessService, "organization").mockResolvedValue(organization);
  vi.spyOn(capacityService, "getCapacity").mockResolvedValue(result(capacity()));
  vi.spyOn(capacityService, "purchases").mockResolvedValue([]);
  vi.spyOn(capacityService, "configureCapacity").mockImplementation(async (_organizationId, revision, body) => {
    return result(capacity({ revision: revision + 1, scheduled_change: body.action === "downgrade"
      ? {
        addon_slots: body.addon_slots,
        capacity: 10 + body.addon_slots,
        effective_at: "2026-12-31T00:00:00Z",
        suspend_class_refs: body.suspend_class_refs,
      }
      : null }));
  });
  vi.spyOn(classService, "listClasses").mockResolvedValue(activeClasses());
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("CapacityPage", () => {
  it("shows the included capacity and a no-subscription empty state", async () => {
    vi.mocked(capacityService.getCapacity).mockResolvedValueOnce(result(capacity({
      subscription_id: null,
      capacity: 10,
      active_class_count: 2,
      available_slots: 8,
      subscription_state: "NONE",
      period_start: null,
      period_end: null,
    })));
    vi.mocked(capacityService.purchases).mockResolvedValue([{
      invoice_id: "admin-start-invoice", kind: "START", state: "PENDING", provider: "SANDBOX",
      units: 12, amount_vnd: 100000, activated: false,
      attempts: [{ state: "OPEN", checkout_url: "https://sandbox.example.test/pay", expires_at: "2099-01-01T00:00:00Z" }],
    }, {
      invoice_id: "admin-renew-invoice", kind: "RENEW", state: "PAID", provider: "SANDBOX",
      units: 12, amount_vnd: 100000, activated: true, attempts: [],
    }, {
      invoice_id: "admin-addon-invoice", kind: "ADDON", state: "PAID", provider: "SANDBOX",
      units: 12, amount_vnd: 100000, activated: true, attempts: [],
    }]);

    const { container } = renderPage();

    expect(await screen.findByText("Trường chưa có gói sức chứa. Sức chứa mặc định gồm 10 lớp.")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Sức chứa lớp" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Hóa đơn sức chứa" })).toBeTruthy();
    expect(screen.getByText(/Đăng ký gói/)).toBeTruthy();
    expect(screen.getByText(/Gia hạn gói/)).toBeTruthy();
    expect(container.textContent).toContain("· Mua thêm slot ·");
    expect(container.textContent).toContain("· Thử nghiệm (quản trị) ·");
    expect(container.textContent).toContain("· 12 slot bổ sung trong gói ·");
    expect(screen.queryByRole("link", { name: "Mở lại thanh toán" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Kiểm tra trạng thái" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Hủy đơn đã hết hạn" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Tắt gia hạn" })).toBeNull();
    expect(screen.getAllByText("Chưa có gói").length).toBeGreaterThan(0);
  });

  it("shows scheduled downgrade details and gives unknown subscription states a neutral label", async () => {
    vi.mocked(capacityService.getCapacity).mockResolvedValueOnce(result(capacity({
      subscription_state: "FUTURE_PRIVATE_STATE",
      scheduled_change: {
        addon_slots: 5,
        capacity: 15,
        effective_at: "2026-12-31T00:00:00Z",
        suspend_class_refs: ["class-private-1", "class-private-2"],
      },
    })));

    const { container } = renderPage();

    expect((await screen.findAllByText("Trạng thái chưa xác định")).length).toBeGreaterThan(0);
    expect(screen.getByText("Sức chứa mới").parentElement?.textContent).toContain("15 lớp");
    expect(screen.getByText("Lớp sẽ tạm ngưng").parentElement?.textContent).toContain("2 lớp");
    expect(screen.getByText("Thời điểm áp dụng").parentElement?.textContent).toContain(
      new Date("2026-12-31T00:00:00Z").toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }),
    );
    expect(container.textContent).not.toContain("FUTURE_PRIVATE_STATE");
    expect(container.textContent).not.toContain("class-private");
  });

  it("confirms renewal cancellation and reuses the same key on a retry", async () => {
    vi.mocked(capacityService.configureCapacity)
      .mockRejectedValueOnce(new TypeError("network unavailable"))
      .mockResolvedValueOnce(result(capacity({ revision: 6, subscription_state: "CANCEL_AT_PERIOD_END" })));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Tắt gia hạn" }));
    expect(capacityService.configureCapacity).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tắt gia hạn" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tắt gia hạn" }));

    await waitFor(() => expect(capacityService.configureCapacity).toHaveBeenCalledTimes(2));
    const first = vi.mocked(capacityService.configureCapacity).mock.calls[0];
    const second = vi.mocked(capacityService.configureCapacity).mock.calls[1];
    expect(first.slice(0, 3)).toEqual(["org-qa", 5, { action: "cancel_renewal" }]);
    expect(second[3]).toBe(first[3]);
    expect(await screen.findByRole("status")).toBeTruthy();
  });

  it("clears the downgrade key when a selected input changes", async () => {
    vi.mocked(capacityService.getCapacity).mockResolvedValueOnce(result(capacity({
      capacity: 12,
      active_class_count: 12,
      available_slots: 0,
    })));
    vi.mocked(classService.listClasses).mockResolvedValue(activeClasses(12));
    vi.mocked(capacityService.configureCapacity)
      .mockRejectedValueOnce(new TypeError("network unavailable"))
      .mockResolvedValueOnce(result(capacity({ capacity: 10, revision: 6 })));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Lên lịch hạ sức chứa" }));
    fireEvent.click(await screen.findByRole("checkbox", { name: "Tạm ngưng lớp Lớp 1" }));
    fireEvent.click(screen.getByRole("button", { name: "Xem lại thay đổi" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận hạ sức chứa" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    const firstKey = vi.mocked(capacityService.configureCapacity).mock.calls[0][3];

    fireEvent.click(screen.getByRole("button", { name: "Sửa lựa chọn" }));
    fireEvent.change(screen.getByLabelText("Số slot bổ sung sau khi hạ"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("checkbox", { name: "Tạm ngưng lớp Lớp 1" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Tạm ngưng lớp Lớp 2" }));
    fireEvent.click(screen.getByRole("button", { name: "Xem lại thay đổi" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận hạ sức chứa" }));

    await waitFor(() => expect(capacityService.configureCapacity).toHaveBeenCalledTimes(2));
    const calls = vi.mocked(capacityService.configureCapacity).mock.calls;
    expect(calls[0][2]).toEqual({ action: "downgrade", addon_slots: 1, suspend_class_refs: ["class-private-1"] });
    expect(calls[1][2]).toEqual({ action: "downgrade", addon_slots: 0, suspend_class_refs: ["class-private-1", "class-private-2"] });
    expect(calls[1][3]).not.toBe(firstKey);
  });

  it("reloads after a stale revision and uses the newly loaded revision", async () => {
    vi.mocked(capacityService.getCapacity)
      .mockResolvedValueOnce(result(capacity({ revision: 5 })))
      .mockResolvedValueOnce(result(capacity({ revision: 6 })));
    vi.mocked(capacityService.configureCapacity)
      .mockRejectedValueOnce(new CapacityServiceError("stale", 409, "STALE_REVISION", 6))
      .mockResolvedValueOnce(result(capacity({ revision: 7 })));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Tắt gia hạn" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tắt gia hạn" }));

    expect(await screen.findByText("Thông tin sức chứa đã thay đổi. Hãy xem lại trước khi xác nhận.")).toBeTruthy();
    expect(capacityService.getCapacity).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("button", { name: "Xác nhận tắt gia hạn" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Tắt gia hạn" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tắt gia hạn" }));
    await waitFor(() => expect(capacityService.configureCapacity).toHaveBeenCalledTimes(2));
    expect(vi.mocked(capacityService.configureCapacity).mock.calls[1][1]).toBe(6);
  });

  it.each([
    ["CLASS_SELECTION_REQUIRED", "Hãy chọn đủ số lớp cần tạm ngưng trước khi xác nhận."],
    ["INVALID_CAPACITY_DOWNGRADE", "Mức sức chứa hoặc danh sách lớp chưa hợp lệ. Hãy kiểm tra lại lựa chọn."],
  ])("shows a safe message for %s", async (code, message) => {
    vi.mocked(capacityService.getCapacity).mockResolvedValueOnce(result(capacity({
      capacity: 12,
      active_class_count: 12,
      available_slots: 0,
    })));
    vi.mocked(classService.listClasses).mockResolvedValue(activeClasses(12));
    vi.mocked(capacityService.configureCapacity).mockRejectedValueOnce(new CapacityServiceError("private backend body", 422, code));

    renderPage();
    await beginDowngrade(12);
    fireEvent.click(screen.getByRole("checkbox", { name: "Tạm ngưng lớp Lớp 1" }));
    fireEvent.click(screen.getByRole("button", { name: "Xem lại thay đổi" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận hạ sức chứa" }));

    expect(await screen.findByText(message)).toBeTruthy();
    expect(screen.queryByText("private backend body")).toBeNull();
    expect(screen.queryByText(code)).toBeNull();
  });
});


describe("Capacity purchases", () => {
  it("refreshes a changed quote and requires a new confirmation", async () => {
    const original = { price_id: "price", cycle_months: 1 as const, base_amount_vnd: 100000, slot_amount_vnd: 10000, quantity: 1, current_addon_slots: 10, resulting_capacity: 21, period_start: "2026-01-01", period_end: "2026-12-31", remaining_time_ratio: "0.5", amount_vnd: 5000, formula: "half-up", quoted_at: "2026-06-01", momo_checkout_enabled: true, vnpay_checkout_enabled: true, synthetic_sandbox_price: true as const };
    const quote = vi.spyOn(capacityService, "quote").mockResolvedValueOnce(original).mockResolvedValueOnce({ ...original, amount_vnd: 6000, quoted_at: "2026-06-02" });
    const checkout = vi.spyOn(capacityService, "checkout").mockRejectedValueOnce(new CapacityServiceError("changed", 409, "CAPACITY_QUOTE_CHANGED")).mockResolvedValueOnce({ state: "PENDING", checkout_url: null });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Xem báo giá" }));
    fireEvent.click(await screen.findByRole("button", { name: "Thanh toán" }));
    expect(await screen.findByText(/Tổng tạm tính: 6.000/)).toBeTruthy();
    expect(screen.getByText("Báo giá đã thay đổi. Hãy xem lại số tiền mới và bấm thanh toán để xác nhận lại.")).toBeTruthy();
    expect(quote).toHaveBeenCalledTimes(2);
    expect(checkout).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByRole("button", { name: "Thanh toán" }));
    await waitFor(() => expect(checkout).toHaveBeenCalledTimes(2));
    expect(checkout.mock.calls[0][3]).not.toBe(checkout.mock.calls[1][3]);
  });

  it("shows a synthetic quote and only enabled providers", async () => {
    vi.spyOn(capacityService, "quote").mockResolvedValue({ price_id: "price", cycle_months: 1,
      base_amount_vnd: 100000, slot_amount_vnd: 10000, quantity: 1, current_addon_slots: 10,
      resulting_capacity: 21, period_start: "2026-01-01", period_end: "2026-12-31",
      remaining_time_ratio: "0.5", amount_vnd: 5000, formula: "half-up", quoted_at: "2026-06-01",
      momo_checkout_enabled: false, vnpay_checkout_enabled: true, synthetic_sandbox_price: true });
    renderPage();
    expect(await screen.findByText("Giá thử nghiệm giả lập (sandbox), chưa phải giá thương mại chính thức.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Xem báo giá" }));
    expect(await screen.findByText(/Tổng tạm tính: 5.000/)).toBeTruthy();
    expect(screen.getByText("VNPay")).toBeTruthy();
    expect(screen.queryByText("MoMo")).toBeNull();
    expect(screen.getByText(/Ngày gia hạn không thay đổi/)).toBeTruthy();
    expect(screen.getByText(/Phí gói cơ bản cho 10 slot: 100.000/)).toBeTruthy();
    expect(screen.getByText("Chu kỳ gói: 1 tháng")).toBeTruthy();
    expect(screen.getByText("Sức chứa sau khi mua: 21 lớp")).toBeTruthy();
    expect(screen.getByText(/Tỷ lệ thời gian còn lại: 50/)).toBeTruthy();
    expect(screen.getByRole("group", { name: "Chọn cổng thanh toán" })).toBeTruthy();
    expect(screen.getByRole("radio", { name: "VNPay" }).getAttribute("name")).toBe("capacity-provider");
  });

  it("does not claim a paid purchase was activated when the server says otherwise", async () => {
    window.history.replaceState({}, "", "/school/capacity?invoice=inv");
    vi.mocked(capacityService.purchases).mockResolvedValue([{ invoice_id: "inv", kind: "ADDON", state: "PAID", provider: "MOMO", units: 1, amount_vnd: 5000, activated: false, attempts: [] }]);
    renderPage();
    expect((await screen.findAllByText(/Đã thanh toán, chờ xử lý thủ công/)).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Thanh toán đã xác nhận và slot đã được cộng/)).toBeNull();
    window.history.replaceState({}, "", "/");
  });

  it.each([
    ["PENDING", false, "Đang chờ thanh toán"],
    ["FAILED", false, "Thanh toán thất bại"],
    ["CANCELED", false, "Đã hủy"],
    ["PAID", false, "Đã thanh toán, chờ xử lý thủ công"],
    ["PAID", true, "Đã kích hoạt"],
  ])("shows the returned invoice state %s", async (state, activated, label) => {
    window.history.replaceState({}, "", "/?invoice=12345678-1234-1234-1234-123456789abc");
    vi.mocked(capacityService.purchases).mockResolvedValue([{ invoice_id: "12345678-1234-1234-1234-123456789abc", kind: "ADDON", state, provider: "MOMO", units: 1, amount_vnd: 5000, activated, created_at: "2026-01-01T00:00:00Z", attempts: [{ state: "UNKNOWN", checkout_url: null, expires_at: null }] }]);
    const { container } = renderPage();
    expect(await screen.findByText(`Trạng thái giao dịch: ${label}.`)).toBeTruthy();
    expect(container.textContent).toContain("Mã đơn: 12345678 · Mua thêm slot · MoMo");
    expect(container.textContent).toContain("Ngày tạo:");
    expect(container.textContent).toContain("Chờ xác minh");
    expect(container.textContent).not.toContain("12345678-1234-1234-1234-123456789abc");
    expect(container.textContent).not.toContain("UNKNOWN");
    window.history.replaceState({}, "", "/");
  });

  it.each([
    ["network", new TypeError("network"), true],
    ["server", new CapacityServiceError("server", 503, "ERROR"), true],
    ["client", new CapacityServiceError("client", 422, "ERROR"), false],
    ["finished", null, false],
    ["pending", null, true],
  ])("handles purchase retry keys after %s", async (kind, error, reused) => {
    vi.spyOn(capacityService, "quote").mockResolvedValue({ price_id: "price", cycle_months: 1, base_amount_vnd: 100000, slot_amount_vnd: 10000, quantity: 1, current_addon_slots: 10, resulting_capacity: 21, period_start: "2026-01-01", period_end: "2026-12-31", remaining_time_ratio: "0.5", amount_vnd: 5000, formula: "half-up", quoted_at: "2026-06-01", momo_checkout_enabled: true, vnpay_checkout_enabled: true, synthetic_sandbox_price: true });
    const checkout = vi.spyOn(capacityService, "checkout");
    if (error) checkout.mockRejectedValueOnce(error);
    else checkout.mockResolvedValueOnce({ state: kind === "pending" ? "PENDING" : "PAID", checkout_url: null });
    checkout.mockResolvedValue({ state: "PENDING", checkout_url: null });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Xem báo giá" }));
    fireEvent.click(await screen.findByRole("button", { name: "Thanh toán" }));
    await waitFor(() => expect(checkout).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByRole("button", { name: "Thanh toán" })).not.toHaveProperty("disabled", true));
    fireEvent.click(screen.getByRole("button", { name: "Thanh toán" }));
    await waitFor(() => expect(checkout).toHaveBeenCalledTimes(2));
    expect(checkout.mock.calls[0][3] === checkout.mock.calls[1][3]).toBe(reused);
  });
});
