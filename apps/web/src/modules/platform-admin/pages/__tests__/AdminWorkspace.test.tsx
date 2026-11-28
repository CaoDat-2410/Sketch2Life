import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import {
  A01ContentModerationPage,
  A02PlatformOperationsPage,
} from "../AdminScreens";
import { commandClient } from "../../services/adminService";
import { authService } from "../../../school-manager/be1/services/authService";

beforeEach(() => {
  window.sketch2lifeAuth = { getIdToken: async () => "synthetic-token" };
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  delete window.sketch2lifeAuth;
  window.sessionStorage.clear();
});
const response = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const operations = {
  database: { status: "healthy", response_ms: null },
  broker: { status: "healthy", response_ms: null, queue_count: 0, transport_pending_count: 0, active_workers: 0 },
  queue: { queued_jobs: 0, running_jobs: 0, failed_jobs: 0, oldest_queued_at: null, last_dispatched_at: null, last_started_at: null, last_finished_at: null },
  jobs: [],
  core_outbox: [],
  email: [],
  lifecycle: [],
};

describe("Admin workspace API integration", () => {
  it("shows real overview counts and notification state instead of unavailable panels", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.includes("/organizations/summary"))
          return response({ total: 3, active: 1, paused: 1, disabled: 1, other: 0 });
        if (url.includes("/organizations"))
          return response({ items: [], total: 3 });
        if (url.includes("/accounts")) return response({ items: [], total: 6 });
        if (url.includes("/operations")) return response(operations);
        if (url.includes("/inbox"))
          return response({ items: [], unread_count: 2 });
        return response({}, 404);
      }),
    );
    render(
      <MemoryRouter>
        <A02PlatformOperationsPage />
      </MemoryRouter>,
    );
    expect(await screen.findByText("3")).toBeTruthy();
    const accountCard = screen.getAllByRole("link").find((link) => link.getAttribute("href") === "/platform/accounts" && link.classList.contains("pa-dashboard-metric"));
    expect(accountCard && within(accountCard).getByText("6")).toBeTruthy();
    expect(
      screen.getByLabelText("Số thông báo chưa đọc").textContent === "2",
    ).toBeTruthy();
    expect(screen.queryByText("Chờ dịch vụ")).toBeNull();
  });

  it("keeps dashboard sections available when one data source fails", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url.includes("/organizations/summary")) return response({ total: 3, active: 1, paused: 1, disabled: 1, other: 0 });
      if (url.includes("/organizations")) return response({ items: [], total: 3 });
      if (url.includes("/accounts")) return response({ items: [], total: 6 });
      if (url.includes("/operations")) return response(operations);
      if (url.includes("/inbox")) return response({ code: "PROVIDER_UNAVAILABLE" }, 503);
      return response({}, 404);
    }));
    render(<MemoryRouter><A02PlatformOperationsPage /></MemoryRouter>);

    expect(await screen.findByText("6")).toBeTruthy();
    expect(screen.getByText("3")).toBeTruthy();
    expect(await screen.findByText("Không tải được dữ liệu")).toBeTruthy();
    expect(screen.getByText("Chưa có trường học")).toBeTruthy();
    expect(screen.getAllByRole("link").some((link) => link.getAttribute("href") === "/platform/accounts")).toBe(true);
  });

  it("keeps an authenticated permission denial visible and offers retry", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        response({ code: "FORBIDDEN", message: "Forbidden" }, 403),
      ),
    );
    render(
      <MemoryRouter initialEntries={["/?panel=orgs"]}>
        <A02PlatformOperationsPage />
      </MemoryRouter>,
    );
    expect((await screen.findByRole("alert")).textContent).toContain(
      "chưa có quyền",
    );
    expect(
      screen.getAllByRole("button", { name: "Tải lại" }).length,
    ).toBeGreaterThan(0);
    expect(screen.queryByText("Chưa có dữ liệu")).toBeNull();
  });

  it("shows directory rows and accurate record distribution without inventing a trend", async () => {
    vi.stubGlobal("fetch", vi.fn(async (url: string) => {
      if (url.includes("/organizations/summary")) return response({ total: 1, active: 1, paused: 0, disabled: 0, other: 0 });
      if (url.includes("/organizations")) return response({
        total: 1, items: [{ organization_id: "school-1", display_name: "Trường Mầm non Vườn Lá", state: "ACTIVE" }],
      });
      if (url.includes("/accounts")) return response({ items: [], total: 6 });
      if (url.includes("/operations")) return response({
        ...operations, email: [{ state: "sent", count: 12 }, { state: "pending", count: 4 }],
      });
      if (url.includes("/inbox")) return response({ items: [], unread_count: 0 });
      return response({}, 404);
    }));
    render(<MemoryRouter><A02PlatformOperationsPage /></MemoryRouter>);
    expect(await screen.findByText("Trường Mầm non Vườn Lá")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Mở Trường Mầm non Vườn Lá" }).getAttribute("href"))
      .toContain("search=" + encodeURIComponent("Trường Mầm non Vườn Lá"));
    fireEvent.click(screen.getByRole("tab", { name: "Vận hành" }));
    expect(screen.getByRole("img", { name: /Phân bố 16 bản ghi/ })).toBeTruthy();
    const legend = screen.getByRole("table", { name: "Số bản ghi theo nhóm" });
    const email = within(legend).getByRole("row", { name: /Thư điện tử/ });
    expect(within(email).getByText("16")).toBeTruthy();
    expect(within(email).getByText("100%")).toBeTruthy();
  });

  it("restores a school filter from its URL into both the API query and search field", async () => {
    const fetch = vi.fn(async (url: string) => response(url.includes("/organizations/summary")
      ? { total: 0, active: 0, paused: 0, disabled: 0, other: 0 }
      : { items: [], total: 0 }));
    vi.stubGlobal("fetch", fetch);
    render(<MemoryRouter initialEntries={["/?panel=orgs&search=" + encodeURIComponent("Trường Vườn Lá")]}>
      <A02PlatformOperationsPage />
    </MemoryRouter>);
    await waitFor(() => expect(fetch).toHaveBeenCalled());
    expect((screen.getByRole("searchbox", { name: "Tìm tên trường học, mã trường..." }) as HTMLInputElement).value).toBe("Trường Vườn Lá");
    const directoryCall = fetch.mock.calls.find(([url]) => String(url).includes("/organizations?"));
    expect(new URL(directoryCall?.[0] as unknown as string, "http://localhost").searchParams.get("search")).toBe("Trường Vườn Lá");
  });

  it("restores the open school form and reuses its idempotency key after remount", async () => {
    const user = { uid: "platform-admin-one" } as never;
    vi.spyOn(authService, "getCurrentUser").mockReturnValue(user);
    vi.spyOn(authService, "observe").mockImplementation((callback) => { callback(user); return () => undefined; });
    let createAttempts = 0;
    const keys: string[] = [];
    const fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const url = new URL(href, "http://localhost");
      if (url.pathname.endsWith("/organizations/summary")) return response({ total: 0, active: 0, paused: 0, disabled: 0, other: 0 });
      if (url.pathname.endsWith("/organizations") && init?.method === "POST") {
        createAttempts += 1;
        keys.push(new Headers(init.headers).get("Idempotency-Key") ?? "");
        if (createAttempts === 1) throw new Error("network response was lost");
        return response({ organization_id: "created-school" });
      }
      return response({ items: [], total: 0, next_cursor: null });
    });
    vi.stubGlobal("fetch", fetch);

    const firstView = render(<MemoryRouter initialEntries={["/?panel=orgs"]}><A02PlatformOperationsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Thêm trường học" }));
    fireEvent.change(screen.getByLabelText("Tên trường học"), { target: { value: "Trường Mầm non Hoa Mai" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo trường học" }));
    await waitFor(() => expect(createAttempts).toBe(1));
    firstView.unmount();

    render(<MemoryRouter initialEntries={["/?panel=orgs"]}><A02PlatformOperationsPage /></MemoryRouter>);
    expect((await screen.findByLabelText("Tên trường học") as HTMLInputElement).value).toBe("Trường Mầm non Hoa Mai");
    fireEvent.click(screen.getByRole("button", { name: "Tạo trường học" }));
    await waitFor(() => expect(createAttempts).toBe(2));
    expect(keys[1]).toBe(keys[0]);
    await waitFor(() => expect(screen.queryByRole("region", { name: "Thêm trường học" })).toBeNull());
    expect(Array.from({ length: window.sessionStorage.length }, (_, index) => window.sessionStorage.key(index) ?? "")
      .some((key) => key.startsWith("sketch2life:session-draft:v1:platform-admin%3Aorganization-create"))).toBe(false);
  });

  it("clears the saved school form when canceled", async () => {
    const user = { uid: "platform-admin-one" } as never;
    vi.spyOn(authService, "getCurrentUser").mockReturnValue(user);
    vi.spyOn(authService, "observe").mockImplementation((callback) => { callback(user); return () => undefined; });
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const href = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
      const url = new URL(href, "http://localhost");
      if (url.pathname.endsWith("/organizations/summary")) return response({ total: 0, active: 0, paused: 0, disabled: 0, other: 0 });
      return response({ items: [], total: 0, next_cursor: null });
    }));

    const view = render(<MemoryRouter initialEntries={["/?panel=orgs"]}><A02PlatformOperationsPage /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Thêm trường học" }));
    fireEvent.change(screen.getByLabelText("Tên trường học"), { target: { value: "Draft to cancel" } });
    expect(Array.from({ length: window.sessionStorage.length }, (_, index) => window.sessionStorage.key(index) ?? "")
      .some((key) => key.startsWith("sketch2life:session-draft:v1:platform-admin%3Aorganization-create"))).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Hủy" }));
    expect(screen.queryByRole("region", { name: "Thêm trường học" })).toBeNull();
    expect(Array.from({ length: window.sessionStorage.length }, (_, index) => window.sessionStorage.key(index) ?? "")
      .some((key) => key.startsWith("sketch2life:session-draft:v1:platform-admin%3Aorganization-create"))).toBe(false);
    view.unmount();
    render(<MemoryRouter initialEntries={["/?panel=orgs"]}><A02PlatformOperationsPage /></MemoryRouter>);
    expect(screen.queryByRole("region", { name: "Thêm trường học" })).toBeNull();
  });

  it("reloads an approved lesson and publishes its exact persisted review evidence", async () => {
    const lesson = {
      lesson_id: "lesson-1",
      revision: 7,
      version_id: "version-2",
      version_no: 2,
      content_hash: "a".repeat(64),
      review_state: "APPROVED",
      visibility: "PUBLIC",
      moderation_state: "VISIBLE",
      is_published_version: false,
      is_author: false,
      reviews: [
        { review_id: "review-persisted", decision: "APPROVE", reason: null },
      ],
      content: {
        locale: "vi-VN",
        title: "Bài học chiếc lá",
        topic: "Thiên nhiên",
        target_age_band_ref: "36-71",
        target_age_band_version: 1,
        objectives: ["Quan sát"],
        drawing_subject: "Chiếc lá",
        drawing_steps_text: "Vẽ chiếc lá",
        subject_learning_notes: "Quan sát hình lá",
        activities: [],
      },
    };
    const fetch = vi.fn(async (url: string, init?: RequestInit) => {
      if (init?.method === "POST")
        return response({ ...lesson, visibility: "PUBLIC", is_published_version: true });
      if (url.includes("/session"))
        return response({
          account_id: "reviewer",
          items: [
            {
              permission: "content_admin",
              effective: true,
              active: true,
              revision: 1,
            },
          ],
        });
      if (url.endsWith("/lessons/lesson-1")) return response(lesson);
      if (url.includes("/lessons?"))
        return response({ items: [lesson], total: 1 });
      return response({}, 404);
    });
    vi.stubGlobal("fetch", fetch);
    render(
      <MemoryRouter>
        <A01ContentModerationPage />
      </MemoryRouter>,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: /Bài học chiếc lá/ }),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Xuất bản" }));
    await waitFor(() =>
      expect(fetch.mock.calls.some(([, init]) => init?.method === "POST")).toBe(
        true,
      ),
    );
    const [, init] = fetch.mock.calls.find(
      ([, request]) => request?.method === "POST",
    )!;
    expect(JSON.parse(String(init?.body))).toMatchObject({
      review_id: "review-persisted",
      version_id: "version-2",
      content_hash: "a".repeat(64),
    });
    expect(new Headers(init?.headers).get("If-Match")).toBe('"7"');
  });

  it("reuses a command key after a lost network response", async () => {
    const fetch = vi
      .fn()
      .mockRejectedValueOnce(new Error("network lost"))
      .mockResolvedValueOnce(response({ organization_id: "created-once" }))
      .mockResolvedValueOnce(response({ organization_id: "created-again" }));
    vi.stubGlobal("fetch", fetch);
    const send = commandClient();
    await expect(
      send("/organizations", { display_name: "Test school" }),
    ).rejects.toThrow();
    await send("/organizations", { display_name: "Test school" });
    expect(fetch.mock.calls[0][1].headers.get("Idempotency-Key")).toBe(
      fetch.mock.calls[1][1].headers.get("Idempotency-Key"),
    );
    expect(fetch.mock.calls[0][1].headers.get("Authorization")).toBe(
      "Bearer synthetic-token",
    );
    await send("/organizations", { display_name: "Test school" });
    expect(fetch.mock.calls[2][1].headers.get("Idempotency-Key")).not.toBe(
      fetch.mock.calls[1][1].headers.get("Idempotency-Key"),
    );
  });

  it("filters email failures server-side and shows safe recovery guidance", async () => {
    const fetch = vi.fn(async (url: string) => {
      if (url.includes('/email-deliveries')) return response({ total: 1, items: [{ delivery_id: 'delivery-1', template: 'password_setup', state: 'failed', attempts: 1, failure_code: 'EMAIL_DELIVERY_UNAVAILABLE', created_at: '2026-11-20T07:00:00Z' }] });
      if (url.includes('/settings')) return response({ environment: 'local', real_payments_enabled: false, billing_sandbox_enabled: true, smtp_configured: true });
      return response({}, 404);
    });
    vi.stubGlobal('fetch', fetch);
    render(<MemoryRouter initialEntries={['/?panel=settings']}><A02PlatformOperationsPage /></MemoryRouter>);
    expect(await screen.findByRole('heading', { name: 'Email hệ thống' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Môi trường hiện tại' })).toBeTruthy();
    expect(screen.getByRole('heading', { name: 'Lịch sử gửi email' })).toBeTruthy();
    expect(screen.queryByText('Thông báo cá nhân')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Lưu tùy chọn' })).toBeNull();
    expect(fetch.mock.calls.some(([url]) => url.includes('/preferences'))).toBe(false);
    expect(await screen.findByText(/Không gửi được. Kiểm tra SMTP/)).toBeTruthy();
    fireEvent.click(screen.getByRole('combobox', { name: 'Trạng thái gửi email' }));
    fireEvent.click(screen.getByRole('option', { name: 'Thất bại' }));
    await waitFor(() => expect(fetch.mock.calls.some(([url]) => url.includes('state=failed') && !url.includes('offset='))).toBe(true));
  });

  it("only offers lifecycle states accepted by the Admin API", async () => {
    const fetch = vi.fn(async (url: string) => {
      if (url.includes("/lifecycle")) return response({ total: 0, items: [] });
      return response({}, 404);
    });
    vi.stubGlobal("fetch", fetch);
    render(<MemoryRouter initialEntries={["/?panel=lifecycle"]}><A02PlatformOperationsPage /></MemoryRouter>);
    const filter = await screen.findByRole("combobox", { name: "Trạng thái xử lý dữ liệu" });
    fireEvent.click(filter);
    const listbox = screen.getByRole("listbox", { name: "Trạng thái xử lý dữ liệu" });
    const labels = within(listbox).getAllByRole("option").map((option) => option.textContent);
    expect(labels).toEqual(["Tất cả trạng thái", "Đang chờ xử lý", "Đang xử lý", "Chờ xóa ở dịch vụ ngoài", "Hoàn tất", "Cần xử lý thủ công"]);
    fireEvent.click(within(listbox).getByRole("option", { name: "Cần xử lý thủ công" }));
    await waitFor(() => expect(fetch.mock.calls.some(([url]) => url.includes("/lifecycle?") && url.includes("state=exception"))).toBe(true));
  });

  it("shows live API health without treating an empty queue as a failure", async () => {
    const fetch = vi.fn(async (url: string) => {
      if (url === "/health") return response({ status: "ok", service: "sketch2life-api" });
      if (url.includes("/operations")) return response(operations);
      return response({}, 404);
    });
    vi.stubGlobal("fetch", fetch);
    render(<MemoryRouter initialEntries={["/?panel=queues"]}><A02PlatformOperationsPage /></MemoryRouter>);

    expect(await screen.findByText("Dịch vụ phản hồi bình thường")).toBeTruthy();
    expect(screen.getByText("Chưa có bản ghi công việc AI")).toBeTruthy();
    expect(screen.queryByText("Không thể xác nhận trạng thái dịch vụ.")).toBeNull();
  });
});
