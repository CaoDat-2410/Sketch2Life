import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

const { readMock } = vi.hoisted(() => ({ readMock: vi.fn() }));
vi.mock("../../services/adminService", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../services/adminService")>();
  return { ...actual, read: readMock };
});

import { QuotaPage } from "../AdminBillingPages";

const product = {
  product_id: "product-1",
  offer_id: "offer-1",
  version: 1,
  display_name: "Gói lớp học",
  offer_kind: "TOP_UP",
  cycle_months: null,
  owner_kind: "ORGANIZATION",
  units: 100,
  amount_vnd: 100000,
  active: true,
  revision: 1,
  updated_at: null,
};

beforeEach(() => {
  window.sketch2lifeAuth = { getIdToken: async () => "synthetic-billing-token" };
  readMock.mockReset().mockImplementation((path: string) => {
    if (path.includes("/events")) return Promise.resolve({ items: [], total: 0 });
    if (path.includes("/quota-products")) return Promise.resolve({ items: [product], total: 1 });
    if (path.includes("/billing/sandbox/quota")) return Promise.resolve({ available_units: 42, granted_units: 50, used_units: 8, grants: [] });
    if (path.includes("/billing/quota")) return Promise.resolve({ available_units: 42, granted_units: 50, used_units: 8, grants: [] });
    if (path.includes("/billing/quota-invoices")) return Promise.resolve({ items: [], total: 0 });
    if (path === "/settings") return Promise.resolve({ billing_sandbox_enabled: true, real_payments_enabled: false, momo_checkout_enabled: false, vnpay_checkout_enabled: false });
    if (path.includes("/organizations")) return Promise.resolve({ items: [{ organization_id: "org-1", display_name: "Trường Một", state: "active" }], total: 1, next_cursor: null });
    return Promise.resolve(null);
  });
});

afterEach(() => { cleanup(); delete window.sketch2lifeAuth; vi.unstubAllGlobals(); });

function mount() {
  return render(<MemoryRouter><QuotaPage /></MemoryRouter>);
}

async function openHistory() {
  fireEvent.click(await screen.findByRole("button", { name: "Lịch sử" }));
  return screen.findByRole("dialog", { name: "Lịch sử hạn mức" });
}

describe("quota product event drawer", () => {
  it("uses Vietnamese copy in the sandbox quota grant form", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ items: [], total: 0, limit: 25, next_cursor: null }), { status: 200, headers: { "Content-Type": "application/json" } })));
    const { container } = render(<MemoryRouter><QuotaPage initialScope={{ owner_kind: "ORGANIZATION", owner_ref: "org-1" }} /></MemoryRouter>);
    fireEvent.click(await screen.findByText("Công cụ hạn mức thử nghiệm"));
    expect(await screen.findByRole("heading", { name: "Cấp hạn mức tháng thử nghiệm" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cấp hạn mức thử nghiệm" })).toBeTruthy();
    expect(container.textContent).not.toMatch(/\btest\b|\boffer\b|\baudit\b/i);
  });

  it("labels every quota offer and owner kind in Vietnamese", async () => {
    readMock.mockImplementation((path: string) => {
      if (path.includes("/events")) return Promise.resolve({ items: [], total: 0 });
      if (path.includes("/quota-products")) return Promise.resolve({
        items: [product, {
          ...product,
          product_id: "product-2",
          display_name: "Gói phụ huynh",
          offer_kind: "MONTHLY",
          owner_kind: "PARENT_ACCOUNT",
        }],
        total: 2,
      });
      return Promise.resolve(null);
    });

    mount();

    for (const label of ["Mua thêm", "Gói tháng", "Trường học", "Phụ huynh"]) {
      expect(await screen.findByText(label)).toBeTruthy();
    }
    for (const rawValue of ["TOP_UP", "MONTHLY", "ORGANIZATION", "PARENT_ACCOUNT"]) {
      expect(screen.queryByText(rawValue)).toBeNull();
    }
  });

  it("shows a loading state, then the empty state", async () => {
    let resolveEvents!: (value: unknown) => void;
    readMock.mockImplementation((path: string) => {
      if (path.includes("/events")) return new Promise((resolve) => { resolveEvents = resolve; });
      if (path.includes("/quota-products")) return Promise.resolve({ items: [product], total: 1 });
      return Promise.resolve(null);
    });
    mount();
    const drawer = await openHistory();
    expect(within(drawer).getByRole("status").textContent).toContain("Đang tải lịch sử sự kiện");
    resolveEvents({ items: [], total: 0 });
    expect(await screen.findByText("Chưa có sự kiện nào cho gói này.")).toBeTruthy();
  });

  it("shows a recoverable error state", async () => {
    readMock.mockImplementation((path: string) => {
      if (path.includes("/events")) return Promise.reject(new Error("server details must stay hidden"));
      if (path.includes("/quota-products")) return Promise.resolve({ items: [product], total: 1 });
      return Promise.resolve(null);
    });
    mount();
    await openHistory();
    await waitFor(() => expect(screen.getAllByRole("alert").some((alert) => alert.textContent?.includes("Không tải được lịch sử sự kiện."))).toBe(true));
    expect(screen.getByRole("button", { name: "Thử lại" })).toBeTruthy();
    expect(screen.queryByText("server details must stay hidden")).toBeNull();
  });

  it("renders action and snapshot values as text, truncating long values", async () => {
    readMock.mockImplementation((path: string) => {
      if (path.includes("/events")) return Promise.resolve({
        total: 1,
        items: [{
          event_id: "event-1",
          product_id: product.product_id,
          offer_id: product.offer_id,
          actor_ref: "platform-admin-12345678901234567890",
          action: "PRICE_UPDATED",
          snapshot: { display_name: "<img src=x onerror=alert(1)>", note: "x".repeat(260) },
          created_at: "2026-11-25T00:00:00Z",
        }],
      });
      if (path.includes("/quota-products")) return Promise.resolve({ items: [product], total: 1 });
      return Promise.resolve(null);
    });
    const { container } = mount();
    const drawer = await openHistory();
    expect(await within(drawer).findByRole("columnheader", { name: "Mã gói" })).toBeTruthy();
    expect(within(drawer).queryByRole("columnheader", { name: "Mã offer" })).toBeNull();
    expect(await screen.findByText("PRICE_UPDATED")).toBeTruthy();
    fireEvent.click(screen.getByText("Chi tiết"));
    expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeTruthy();
    expect(container.querySelector("img, script, iframe")).toBeNull();
    const longValue = Array.from(container.querySelectorAll(".pa-event-snapshot dd"))
      .find((value) => value.textContent?.startsWith("xxx"))?.textContent ?? "";
    expect(longValue.length).toBeLessThanOrEqual(240);
  });
});
