import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { A02PlatformOperationsPage } from "../AdminScreens";

const school = { organization_id: "org-smoke-01", display_name: "Trường Mầm non Hoa Nắng", state: "active", revision: 2 };
const account = { account_id: "admin-smoke-01", display_name: "Quản trị viên thử nghiệm", email: "admin@example.test", role: "platform_admin", state: "active", revision: 1 };
const activity = {
  title: "Khu vườn nhỏ",
  objective: "Quan sát màu sắc của lá.",
  instructions_text: "Cùng trẻ quan sát một chiếc lá.",
  materials_text: "Giấy và bút màu",
  preparation_text: "Chuẩn bị giấy và bút màu.",
  observation_notes: "Khuyến khích trẻ quan sát.",
  safety_notes: "Rửa tay sau hoạt động.",
  activity_kind: "outdoor",
};
const catalogRecord = {
  record_id: "catalog-smoke-01", revision: 2, version: 1, content_hash: "catalog-hash",
  state: "PENDING_REVIEW", is_author: false,
  content: { activity, age_band: "36-71", age_band_version: 1, provenance: "HUMAN_AUTHORED" },
  reviews: [],
};

const response = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "Content-Type": "application/json" },
});

function fixtureFetch() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const href = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    const url = new URL(href, "http://localhost");
    const path = url.pathname;
    const method = init?.method ?? "GET";
    if (path.endsWith("/accounts") && method === "GET") return response({ items: [account], total: 1, limit: 25, next_cursor: null });
    if (path.endsWith("/session")) return response({ account_id: "another-admin", items: [{ permission: "content_admin", effective: true, active: true, revision: 1 }] });
    if (path.endsWith("/permissions")) return response({ items: [{ permission: "content_admin", effective: true, active: true, revision: 1 }] });
    if (path.endsWith("/inbox") && method === "GET") return response({ items: [{ item_id: "inbox-smoke-01", kind: "LESSON_FEEDBACK_CREATED", is_read: false, created_at: "2026-11-20T07:00:00Z" }], total: 1, unread_count: 1, next_cursor: null });
    if (path.endsWith("/audit/retention/preview")) return response({ retention_days: 365, policy_revision: 2, cutoff: "2025-11-20T07:00:00Z", candidate_count: 2, batch_count: 2, batch_limit: 100, oldest_candidate_at: "2025-01-01T00:00:00Z" });
    if (path.endsWith("/audit/retention")) return response({ retention_days: 365, revision: 2, total_entries: 10, eligible_count: 2, oldest_entry_at: "2025-01-01T00:00:00Z", newest_entry_at: "2026-11-20T07:00:00Z", last_purged_at: null, last_purged_count: 0 });
    if (path.endsWith("/audit")) return response({ items: [{ audit_id: "audit-smoke-01", action: "REVIEW", resource_type: "lesson", resource_id: "lesson-smoke", actor_ref: "admin-smoke", organization_id: "platform", created_at: "2026-11-20T07:00:00Z", decision: "allow" }], total: 1, next_cursor: null });
    if (path.endsWith("/organizations") && method === "GET") return response({ items: [school], total: 1, limit: 25, next_cursor: null });
    if (path.endsWith("/feedback/thread-smoke-01")) return response({ thread_id: "thread-smoke-01", revision: 1, lesson_id: "lesson-smoke-01", next_cursor: null, items: [{ message_id: "message-smoke-01", body: "Nội dung trao đổi mẫu.", from_you: false, created_at: "2026-11-20T07:00:00Z" }] });
    if (path.endsWith("/feedback")) return response({ items: [{ thread_id: "thread-smoke-01", lesson_id: "lesson-smoke-01", revision: 1, created_at: "2026-11-20T07:00:00Z" }], total: 1, next_cursor: null });
    if (path.endsWith("/catalog") && method === "GET") return response({ items: [catalogRecord], total: 1, next_cursor: null });
    if (path.includes("/catalog/")) return response(catalogRecord);
    if (path.endsWith("/settings")) return response({ environment: "Preview", real_payments_enabled: false, billing_sandbox_enabled: true, smtp_configured: true, preferences: { locale: "vi-VN", email_notifications: true, revision: 1 } });
    if (path.endsWith("/billing/sandbox/invoices")) return response({ items: [{ invoice_id: "invoice-smoke-01", owner_kind: "ORGANIZATION", owner_ref: school.organization_id, offer_id: "offer-smoke-01", units: 100, amount_vnd: 50000, state: "PAID", revision: 1 }], total: 1, next_cursor: null });
    if (path.endsWith("/billing/sandbox/offers")) return response({ items: [{ offer_id: "offer-smoke-01", owner_kind: "ORGANIZATION", units: 100, amount_vnd: 50000 }], total: 1, next_cursor: null });
    if (path.endsWith("/billing/quota")) return response({ available_units: 42, granted_units: 50, used_units: 8, owner_kind: "ORGANIZATION", owner_ref: school.organization_id, grants: [{ grant_id: "grant-smoke-01", kind: "included", units: 50, used: 8, available: 42, expires_at: null }] });
    if (path.endsWith("/billing/sandbox/subscriptions")) return response({ items: [{ subscription_id: "sub-smoke-01", organization_ref: school.organization_id, capacity: 10, addon_slots: 2, revision: 1, state: "active", period_end: "2026-12-20T00:00:00Z", scheduled_addon_slots: null, suspended_class_refs: [] }], total: 1, next_cursor: null });
    if (path.endsWith("/billing/sandbox/capacity-prices")) return response({ items: [{ price_id: "price-smoke-01", cycle_months: 1, base_amount_vnd: 200000, slot_amount_vnd: 20000 }], total: 1, next_cursor: null });
    if (path.endsWith("/capacity-classes")) return response({ items: [], total: 0, next_cursor: null });
    return response({ items: [], total: 0, unread_count: 0, next_cursor: null });
  });
}

function mount(panel: string, query = "") {
  return render(<MemoryRouter initialEntries={[`/?panel=${panel}${query}`]}><A02PlatformOperationsPage /></MemoryRouter>);
}

beforeEach(() => {
  window.sketch2lifeAuth = { getIdToken: async () => "synthetic-smoke-token" };
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  delete window.sketch2lifeAuth;
});

describe("Platform Admin page data and interactions", () => {
  it("previews the audit retention batch from the audit screen", async () => {
    const fetch = fixtureFetch();
    vi.stubGlobal("fetch", fetch);
    mount("audit");
    fireEvent.click(await screen.findByText(/Chính sách lưu nhật ký/));
    fireEvent.click(await screen.findByRole("button", { name: "Xem trước bản ghi đến hạn" }));
    expect(await screen.findByText("2 bản ghi đã quá hạn")).toBeTruthy();
    await waitFor(() => expect(fetch.mock.calls.some(([input]) => String(input).includes("/audit/retention/preview"))).toBe(true));
  });

  it("selects an administrator and loads the permission state", async () => {
    vi.stubGlobal("fetch", fixtureFetch());
    mount("permissions");
    fireEvent.click(await screen.findByRole("combobox", { name: "Quản trị viên" }));
    fireEvent.click(screen.getByRole("option", { name: "Quản trị viên thử nghiệm" }));
    expect(await screen.findByText(/Quyền duyệt nội dung:/)).toBeTruthy();
    expect(screen.getByLabelText("Lý do thay đổi")).toBeTruthy();
  });

  it("marks a loaded inbox item as read", async () => {
    const fetch = fixtureFetch();
    vi.stubGlobal("fetch", fetch);
    mount("inbox");
    fireEvent.click(await screen.findByRole("button", { name: "Đánh dấu đã đọc" }));
    await waitFor(() => expect(fetch.mock.calls.some(([input, init]) => String(input).includes("/inbox/inbox-smoke-01/read") && init?.method === "POST")).toBe(true));
  });

  it("opens a feedback thread and shows its message", async () => {
    vi.stubGlobal("fetch", fixtureFetch());
    mount("feedback", "&org=org-smoke-01");
    fireEvent.click(await screen.findByRole("button", { name: /Phản hồi thread/ }));
    expect(await screen.findByText("Nội dung trao đổi mẫu.")).toBeTruthy();
    expect(screen.getByLabelText("Phản hồi của bạn")).toBeTruthy();
  });

  it("opens an activity record from the catalog list", async () => {
    vi.stubGlobal("fetch", fixtureFetch());
    mount("catalog");
    fireEvent.click(await screen.findByRole("button", { name: /Khu vườn nhỏ/ }));
    expect(await screen.findByText("Khuyến khích trẻ quan sát.")).toBeTruthy();
    expect(screen.getByText("Cách thực hiện")).toBeTruthy();
  });

  it("opens the test invoice form from billing", async () => {
    vi.stubGlobal("fetch", fixtureFetch());
    mount("billing");
    fireEvent.click(await screen.findByRole("button", { name: /Tạo hóa đơn test/ }));
    expect(await screen.findByRole("heading", { name: "Tạo hóa đơn thử nghiệm" })).toBeTruthy();
    expect(screen.getByLabelText("Phạm vi")).toBeTruthy();
  });

  it("loads quota after selecting a school", async () => {
    vi.stubGlobal("fetch", fixtureFetch());
    mount("quota");
    fireEvent.click(await screen.findByRole("combobox", { name: "Trường học" }));
    fireEvent.click(screen.getByRole("option", { name: school.display_name }));
    expect(await screen.findByText("Còn khả dụng")).toBeTruthy();
    expect(screen.getByText("Còn khả dụng").closest("div")?.textContent).toContain("42");
  });

  it("opens the capacity price form while showing the active subscription", async () => {
    vi.stubGlobal("fetch", fixtureFetch());
    mount("capacity");
    expect((await screen.findAllByText(school.display_name)).length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /Tạo bảng giá test/ }));
    expect(await screen.findByRole("heading", { name: "Bảng giá mới" })).toBeTruthy();
  });
});
