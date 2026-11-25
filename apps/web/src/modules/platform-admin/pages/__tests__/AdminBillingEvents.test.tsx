import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  readMock.mockReset().mockImplementation((path: string) => {
    if (path.includes("/events")) return Promise.resolve({ items: [], total: 0 });
    if (path.includes("/quota-products")) return Promise.resolve({ items: [product], total: 1 });
    return Promise.resolve(null);
  });
});

afterEach(() => cleanup());

function mount() {
  return render(<MemoryRouter><QuotaPage /></MemoryRouter>);
}

async function openHistory() {
  fireEvent.click(await screen.findByRole("button", { name: "Lịch sử" }));
  return screen.findByRole("dialog", { name: "Lịch sử quota" });
}

describe("quota product event drawer", () => {
  it("shows a loading state, then the empty state", async () => {
    let resolveEvents!: (value: unknown) => void;
    readMock.mockImplementation((path: string) => {
      if (path.includes("/events")) return new Promise((resolve) => { resolveEvents = resolve; });
      if (path.includes("/quota-products")) return Promise.resolve({ items: [product], total: 1 });
      return Promise.resolve(null);
    });
    mount();
    await openHistory();
    expect(screen.getByRole("status").textContent).toContain("Đang tải lịch sử sự kiện");
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
    await openHistory();
    expect(await screen.findByText("PRICE_UPDATED")).toBeTruthy();
    fireEvent.click(screen.getByText("Chi tiết"));
    expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeTruthy();
    expect(container.querySelector("img, script, iframe")).toBeNull();
    const longValue = Array.from(container.querySelectorAll(".pa-event-snapshot dd"))
      .find((value) => value.textContent?.startsWith("xxx"))?.textContent ?? "";
    expect(longValue.length).toBeLessThanOrEqual(240);
  });
});
