import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { OverviewPage } from "../AdminDirectoryPages";

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "Content-Type": "application/json" },
});

const eventTime = (offsetMinutes: number) => new Date(Date.now() - offsetMinutes * 60_000).toISOString();

const schools = {
  total: 10,
  active: 6,
  paused: 2,
  disabled: 1,
  other: 1,
};

const operations = {
  database: { status: "healthy", response_ms: 11 },
  broker: { status: "healthy", response_ms: 4, queue_count: 2, transport_pending_count: 0, active_workers: 3 },
  queue: { queued_jobs: 4, running_jobs: 2, failed_jobs: 1, oldest_queued_at: null, last_dispatched_at: null, last_started_at: null, last_finished_at: null },
  jobs: [{ state: "running", count: 2 }],
  core_outbox: [],
  email: [{ state: "sent", count: 5 }, { state: "pending", count: 1 }],
  lifecycle: [],
};

const invoices = [
  { invoice_id: "inv-pending", owner_kind: "ORGANIZATION", units: 1, amount_vnd: 70_000, state: "PENDING", revision: 1, created_at: eventTime(1) },
  { invoice_id: "inv-failed", owner_kind: "ORGANIZATION", units: 1, amount_vnd: 50_000, state: "FAILED", revision: 1, created_at: eventTime(2) },
  { invoice_id: "inv-canceled", owner_kind: "ORGANIZATION", units: 1, amount_vnd: 25_000, state: "CANCELED", revision: 1, created_at: eventTime(3) },
  { invoice_id: "inv-paid", owner_kind: "ORGANIZATION", units: 1, amount_vnd: 150_000, state: "PAID", revision: 1, created_at: eventTime(4) },
];

const paymentEvents = [
  { event_id: "event-paid-latest", invoice_id: "invoice-1", amount_vnd: 60_000, outcome: "PAID", created_at: eventTime(1) },
  { event_id: "event-failed", invoice_id: "invoice-2", amount_vnd: 80_000, outcome: "FAILED", created_at: eventTime(2) },
  { event_id: "event-paid-earlier", invoice_id: "invoice-3", amount_vnd: 40_000, outcome: "PAID", created_at: eventTime(24 * 60) },
];

function fixtureFetch(options: { failEvents?: boolean; failOperations?: boolean; testSchool?: boolean } = {}) {
  return vi.fn(async (input: RequestInfo | URL) => {
    const href = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(href, "http://localhost");
    const path = url.pathname;
    if (path.endsWith("/organizations/summary")) return response(schools);
    if (path.endsWith("/organizations")) return response({ items: [{ organization_id: "school-1", display_name: options.testSchool ? "[TEST] Trường Hoa Mai" : "Trường Hoa Mai", state: "active", revision: 1 }], total: 10 });
    if (path.endsWith("/accounts")) {
      const role = url.searchParams.get("role");
      const totals: Record<string, number> = { parent: 3, teacher: 2, school_manager: 1, platform_admin: 1 };
      return response({ items: [], total: role ? totals[role] : 8, limit: 1, next_cursor: null });
    }
    if (path.endsWith("/lessons")) return response({ items: [], total: 5 });
    if (path.endsWith("/inbox")) return response({ items: [
      { item_id: "notice-1", kind: "ACCOUNT_CREATED", is_read: false, created_at: eventTime(20) },
      { item_id: "notice-2", kind: "ORGANIZATION_UPDATED", is_read: true, created_at: eventTime(40) },
      { item_id: "notice-3", kind: "LESSON_FEEDBACK_CREATED", is_read: false, created_at: eventTime(60) },
    ], total: 3, unread_count: 2 });
    if (path.endsWith("/operations")) return options.failOperations ? response({ code: "UNAVAILABLE" }, 503) : response(operations);
    if (path.endsWith("/billing/quota-invoices")) return response({ items: invoices, total: 101 });
    if (path.endsWith("/billing/quota-payment-events")) return options.failEvents ? response({ code: "UNAVAILABLE" }, 503) : response({ items: paymentEvents, total: 501 });
    if (path.endsWith("/settings")) return response({ environment: "test", real_payments_enabled: false, momo_sandbox_enabled: true, vnpay_sandbox_enabled: false, billing_sandbox_enabled: true, smtp_configured: false, preferences: { locale: "vi-VN", email_notifications: true, revision: 1 } });
    return response({ items: [], total: 0, unread_count: 0 });
  });
}

function mount() {
  return render(<MemoryRouter><OverviewPage /></MemoryRouter>);
}

beforeEach(() => {
  window.sketch2lifeAuth = { getIdToken: async () => "synthetic-dashboard-token" };
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  delete window.sketch2lifeAuth;
});

describe("Platform Admin overview dashboard", () => {
  it("shows overview totals and event labels, then navigates tabs with arrow keys", async () => {
    const fetch = fixtureFetch();
    vi.stubGlobal("fetch", fetch);
    mount();

    const metrics = screen.getByRole("region", { name: "Số liệu tổng quan" });
    const schoolCard = await within(metrics).findByRole("link", { name: /Trường học/ });
    expect(within(schoolCard).getByText("10")).toBeTruthy();
    expect(within(within(metrics).getByRole("link", { name: /Tài khoản/ })).getByText("8")).toBeTruthy();
    expect(within(within(metrics).getByRole("link", { name: /Học liệu chờ duyệt/ })).getByText("5")).toBeTruthy();
    expect(within(within(metrics).getByRole("link", { name: /Thông báo chưa đọc/ })).getByText("2")).toBeTruthy();
    expect(screen.getByRole("img", { name: /Trường đang hoạt động chiếm 60/ })).toBeTruthy();
    expect(await screen.findByText("Tạo tài khoản")).toBeTruthy();
    expect(screen.getByText("Cập nhật trường học")).toBeTruthy();
    expect(screen.getByText("Có phản hồi học liệu mới")).toBeTruthy();

    const overviewTab = screen.getByRole("tab", { name: "Tổng quan" });
    fireEvent.keyDown(overviewTab, { key: "ArrowRight" });
    const financeTab = screen.getByRole("tab", { name: "Tài chính" });
    await waitFor(() => expect(financeTab.getAttribute("aria-selected")).toBe("true"));
    fireEvent.click(screen.getByRole("tab", { name: "Vận hành" }));
    expect(await screen.findByRole("heading", { name: "Tình trạng vận hành" })).toBeTruthy();
    const databaseHealth = screen.getByRole("heading", { name: "Kho dữ liệu" }).closest("section")!;
    expect(within(databaseHealth).getByText("11 ms")).toBeTruthy();
    expect(within(databaseHealth).getByText("Đang hoạt động")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Tiến trình xử lý đang chạy" })).toBeTruthy();
    expect(screen.getByText("Số tiến trình đang phản hồi.")).toBeTruthy();
  });

  it("strips the test prefix when calculating school initials", async () => {
    vi.stubGlobal("fetch", fixtureFetch({ testSchool: true }));
    mount();

    const schoolName = await screen.findByText("[TEST] Trường Hoa Mai");
    expect(schoolName.parentElement?.querySelector("span")?.textContent).toBe("TH");
  });

  it("uses successful payment events and capped source notes on the finance tab", async () => {
    vi.stubGlobal("fetch", fixtureFetch());
    mount();

    fireEvent.click(screen.getByRole("tab", { name: "Tài chính" }));
    expect(await screen.findByText("Dữ liệu thử nghiệm")).toBeTruthy();
    expect(await screen.findByText("Đã thu")).toBeTruthy();
    expect(screen.getAllByText(/100\.000/).length).toBeGreaterThan(0);
    expect(screen.getByText(/70\.000/)).toBeTruthy();
    expect(screen.getByText(/75\.000/)).toBeTruthy();
    expect(screen.getByText(/chỉ tính trên 3 bản ghi gần nhất đã tải/)).toBeTruthy();
    expect(screen.getByText(/chỉ tính trên 4 bản ghi gần nhất đã tải/)).toBeTruthy();
    expect(screen.getByRole("img", { name: /Khoản thu thành công trong 7 ngày/ })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "12 tháng" }));
    expect(screen.getByRole("button", { name: "12 tháng" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByText("Xem bảng số liệu biểu đồ")).toBeTruthy();
  });

  it("keeps overview, finance, and operations available when other data sources fail", async () => {
    vi.stubGlobal("fetch", fixtureFetch({ failEvents: true, failOperations: true }));
    mount();

    expect(await screen.findByRole("heading", { name: "Trạng thái trường học" })).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: "Tài chính" }));
    expect(await screen.findByText("Dữ liệu thử nghiệm")).toBeTruthy();
    expect(screen.getAllByRole("alert").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("tab", { name: "Vận hành" }));
    expect(await screen.findAllByRole("alert")).toHaveLength(1);
    fireEvent.click(screen.getByRole("tab", { name: "Tổng quan" }));
    expect(await screen.findByText("Trường Hoa Mai")).toBeTruthy();
  });

  it("reloads all dashboard sources from the page refresh control", async () => {
    const fetch = fixtureFetch();
    vi.stubGlobal("fetch", fetch);
    mount();
    await screen.findByText("Trường Hoa Mai");
    const countsBefore = ["/organizations/summary", "/organizations?", "/operations", "/billing/quota-invoices", "/billing/quota-payment-events", "/settings"]
      .map((path) => fetch.mock.calls.filter(([input]) => String(input).includes(path)).length);

    fireEvent.click(screen.getByRole("button", { name: "Tải lại" }));
    await waitFor(() => {
      const countsAfter = ["/organizations/summary", "/organizations?", "/operations", "/billing/quota-invoices", "/billing/quota-payment-events", "/settings"]
        .map((path) => fetch.mock.calls.filter(([input]) => String(input).includes(path)).length);
      expect(countsAfter.every((count, index) => count > countsBefore[index])).toBe(true);
    });
  });
});
