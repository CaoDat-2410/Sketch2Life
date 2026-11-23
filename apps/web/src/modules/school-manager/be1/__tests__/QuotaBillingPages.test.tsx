import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AdminBe1Error, adminBe1Request } from "../services/be1Client";
import { managerBusinessService } from "../services/managerBusinessService";
import { SchoolBillingPage } from "../pages/QuotaBillingPages";

vi.mock("../services/be1Client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../services/be1Client")>();
  return { ...actual, adminBe1Request: vi.fn() };
});

const organization = {
  contract: "Be1OrganizationV1" as const,
  organization_id: "org-qa",
  display_name: "Trường kiểm thử",
};

function pendingInvoice(overrides: Record<string, unknown> = {}) {
  return {
    invoice_id: "invoice-pending-1",
    units: 100,
    amount_vnd: 100000,
    state: "PENDING",
    provider: "MOMO",
    payment_mode: "MANUAL",
    created_at: null,
    attempts: [{ provider: "MOMO", state: "UNKNOWN", checkout_url: null, expires_at: null }],
    ...overrides,
  };
}

function mockInitialLoad(request: ReturnType<typeof vi.mocked<typeof adminBe1Request>>, invoices: unknown[]) {
  request
    .mockResolvedValueOnce({ owner_kind: "ORGANIZATION", available_units: 8, granted_units: 10, used_units: 2, grants: [], allocation: { allocated_unused_units: 0, available_school_units: 8, teachers: [] } } as never)
    .mockResolvedValueOnce({ items: [{ product_id: "product-1", offer_id: "offer-1", version: 1, display_name: "Gói mua thêm", offer_kind: "TOP_UP", cycle_months: null, units: 100, amount_vnd: 100000, active: true }] } as never)
    .mockResolvedValueOnce({ items: invoices, total: invoices.length } as never)
    .mockResolvedValueOnce({ items: [], total: 0 } as never)
    .mockResolvedValueOnce({ items: [] } as never)
    .mockResolvedValueOnce({ real_payments_enabled: true, momo_checkout_enabled: true, vnpay_checkout_enabled: false, momo_sandbox_enabled: true, vnpay_sandbox_enabled: true, monthly_auto_renew_enabled: false } as never);
}

function mockOrganization() {
  vi.spyOn(managerBusinessService, "organization").mockResolvedValue(organization);
}

afterEach(() => {
  cleanup();
  window.history.replaceState({}, "", "/");
  window.sessionStorage.clear();
  vi.restoreAllMocks();
});

describe("School billing payment lifecycle", () => {
  it("keeps an unresolved invoice open, explains that closing checkout does not cancel it, and blocks a duplicate purchase", async () => {
    mockOrganization();
    const request = vi.mocked(adminBe1Request);
    mockInitialLoad(request, [pendingInvoice()]);

    render(<MemoryRouter><SchoolBillingPage /></MemoryRouter>);

    expect(await screen.findByText("Chờ cổng xác nhận", { selector: "small" })).toBeTruthy();
    expect((await screen.findByRole("alert")).textContent).toContain("Đóng trang thanh toán không hủy hóa đơn");
    expect(screen.getByRole("button", { name: "Thanh toán MoMo" })).toHaveProperty("disabled", true);
    expect(screen.getByRole("button", { name: "Kiểm tra với cổng" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: /Mở lại thanh toán/ })).toBeNull();
  });

  it("offers the original checkout link again while it is still valid", async () => {
    mockOrganization();
    const request = vi.mocked(adminBe1Request);
    mockInitialLoad(request, [pendingInvoice({ attempts: [{ provider: "MOMO", state: "OPEN", checkout_url: "https://test-payment.momo.vn/checkout/one", expires_at: new Date(Date.now() + 5 * 60_000).toISOString() }] })]);

    render(<MemoryRouter><SchoolBillingPage /></MemoryRouter>);

    const resume = await screen.findByRole("link", { name: /Mở lại thanh toán/ });
    expect(resume.getAttribute("href")).toBe("https://test-payment.momo.vn/checkout/one");
    expect(resume.getAttribute("target")).toBe("_blank");
    expect(screen.getByRole("button", { name: "Thanh toán MoMo" })).toHaveProperty("disabled", true);
  });

  it("reconciles the invoice with the provider and tells the manager when a fresh order is safe", async () => {
    mockOrganization();
    const request = vi.mocked(adminBe1Request);
    mockInitialLoad(request, [pendingInvoice({ attempts: [{ provider: "MOMO", state: "OPEN", checkout_url: null, expires_at: new Date(Date.now() - 1000).toISOString() }] })]);
    request.mockResolvedValueOnce({ invoice_id: "invoice-pending-1", state: "FAILED", reconciled: true } as never);
    mockInitialLoad(request, [pendingInvoice({ state: "FAILED" })]);

    render(<MemoryRouter><SchoolBillingPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Kiểm tra trạng thái" }));

    expect(await screen.findByText("Cổng xác nhận giao dịch đã hết hạn hoặc thất bại. Bạn có thể tạo đơn thanh toán mới.")).toBeTruthy();
    await waitFor(() => expect(request).toHaveBeenCalledWith(
      "/organizations/org-qa/video-quota/invoices/invoice-pending-1/reconcile",
      { method: "POST" },
    ));
    expect(screen.getByRole("button", { name: "Thanh toán MoMo" })).toHaveProperty("disabled", false);
  });

  it("keeps an expired invoice unverified and explains a failed VNPay signature check without implying failure", async () => {
    mockOrganization();
    const request = vi.mocked(adminBe1Request);
    mockInitialLoad(request, [pendingInvoice({ provider: "VNPAY", attempts: [{ provider: "VNPAY", state: "OPEN", checkout_url: "https://sandbox.vnpayment.vn/expired", expires_at: new Date(Date.now() - 1000).toISOString() }] })]);
    request.mockRejectedValueOnce(new AdminBe1Error("Request failed", 502, "VNPAY_QUERY_RESPONSE_SIGNATURE_INVALID"));

    render(<MemoryRouter><SchoolBillingPage /></MemoryRouter>);

    expect(await screen.findByText("Chờ xác minh")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toContain("Đừng thanh toán lại");
    const reconcile = await screen.findByRole("button", { name: "Kiểm tra trạng thái" });
    fireEvent.click(reconcile);

    expect(await screen.findByText(/VNPay chưa trả phản hồi đối soát có chữ ký hợp lệ/)).toBeTruthy();
    expect(await screen.findByText(/Hóa đơn chưa chuyển trạng thái và quota chưa thay đổi/)).toBeTruthy();
    await waitFor(() => expect(reconcile).toHaveProperty("disabled", true));
    expect(screen.getByRole("button", { name: "Thanh toán MoMo" })).toHaveProperty("disabled", true);
  });

  it("lets the manager cancel an expired VNPay invoice and choose another provider", async () => {
    mockOrganization();
    const request = vi.mocked(adminBe1Request);
    mockInitialLoad(request, [pendingInvoice({
      provider: "VNPAY",
      attempts: [{ provider: "VNPAY", state: "OPEN", checkout_url: "https://sandbox.vnpayment.vn/expired", expires_at: new Date(Date.now() - 1000).toISOString() }],
    })]);
    request.mockResolvedValueOnce({ invoice_id: "invoice-pending-1", state: "CANCELED", canceled: true, reconciled: true } as never);
    mockInitialLoad(request, [pendingInvoice({
      provider: "VNPAY",
      state: "CANCELED",
      attempts: [{ provider: "VNPAY", state: "CANCELED", checkout_url: null, expires_at: new Date(Date.now() - 1000).toISOString() }],
    })]);

    render(<MemoryRouter><SchoolBillingPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Hủy đơn đã hết hạn" }));

    expect(await screen.findByText("Đã hủy hóa đơn hết hạn. Bạn có thể chọn lại VNPay hoặc MoMo để tạo đơn mới.")).toBeTruthy();
    await waitFor(() => expect(request).toHaveBeenCalledWith(
      "/organizations/org-qa/video-quota/invoices/invoice-pending-1/cancel",
      { method: "POST" },
    ));
    expect(screen.getByRole("button", { name: "Thanh toán MoMo" })).toHaveProperty("disabled", false);
  });

  it("checks the returned invoice until a verified success appears after payment", async () => {
    mockOrganization();
    const request = vi.mocked(adminBe1Request);
    window.history.replaceState({}, "", "/school/billing?invoice=invoice-pending-1");
    mockInitialLoad(request, [pendingInvoice()]);
    request.mockResolvedValueOnce({ items: [pendingInvoice({ state: "PAID", attempts: [{ provider: "MOMO", state: "PAID", checkout_url: null, expires_at: null }] })], total: 1 } as never);

    render(<MemoryRouter><SchoolBillingPage /></MemoryRouter>);

    expect(await screen.findByText("Thanh toán đã được xác nhận; quota đã được cộng vào số dư trường.")).toBeTruthy();
    await waitFor(() => expect(window.location.search).toBe("") );
    expect(request).toHaveBeenCalledWith("/organizations/org-qa/video-quota/invoices?limit=50");
  });
});
