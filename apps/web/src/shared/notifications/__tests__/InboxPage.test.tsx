import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BackendApiError } from "../../api/backendApi";
import * as notificationsApi from "../../api/notificationsApi";
import type { NotificationItem, NotificationPage } from "../../api/notificationsApi";
import { InboxPage } from "../InboxPage";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function item(id: string, overrides: Partial<NotificationItem> = {}): NotificationItem {
  return {
    contract: "NotificationV1",
    inbox_item_id: id,
    notification_type: "UNKNOWN_TYPE",
    template_version: 1,
    safe_parameters: { raw_marker: "DO_NOT_RENDER_RAW" },
    created_at: "2026-11-20T10:00:00Z",
    read_at: null,
    expires_at: null,
    ...overrides,
  };
}

function page(items: NotificationItem[], overrides: Partial<NotificationPage> = {}): NotificationPage {
  return {
    contract: "NotificationPageV1",
    items,
    next_cursor: null,
    unread_count: items.filter((entry) => entry.read_at === null).length,
    ...overrides,
  };
}

describe("InboxPage", () => {
  it("shows an accessible loading status while the first page is pending", () => {
    vi.spyOn(notificationsApi, "listNotifications").mockImplementation(() => new Promise(() => undefined));

    render(<InboxPage />);

    expect(screen.getByRole("status").getAttribute("aria-busy")).toBe("true");
    expect(screen.getByText("Đang tải hộp thư…")).toBeTruthy();
  });

  it("states calmly when the inbox is empty", async () => {
    vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue(page([]));

    render(<InboxPage />);

    const emptyMessage = await screen.findByText("Hộp thư hiện đang trống.");
    expect(emptyMessage.tagName).toBe("P");
    expect(emptyMessage.className).toContain("s2l-empty-copy");
    expect(emptyMessage.closest("section")).toBeNull();
    expect(screen.queryByText("Chưa đọc: 0")).toBeNull();
  });

  it("shows a mapped error and retries a failed first-page request", async () => {
    const list = vi.spyOn(notificationsApi, "listNotifications")
      .mockRejectedValueOnce(new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0))
      .mockResolvedValueOnce(page([]));

    render(<InboxPage />);
    expect((await screen.findByRole("alert")).textContent).toContain("Không kết nối được dịch vụ.");
    fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));

    expect(await screen.findByText("Hộp thư hiện đang trống.")).toBeTruthy();
    expect(list).toHaveBeenCalledTimes(2);
  });

  it("renders unread and read items distinctly, marks one read, and never renders safe parameters", async () => {
    const unread = item("unread-1");
    const read = item("read-1", { read_at: "2026-11-20T11:00:00Z" });
    vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue(page([unread, read], { unread_count: 2 }));
    vi.spyOn(notificationsApi, "markNotificationRead").mockResolvedValue({ ...unread, read_at: "2026-11-20T12:00:00Z" });

    const { container } = render(<InboxPage />);
    const markOne = await screen.findByRole("button", { name: "Thông báo mới: đánh dấu đã đọc" });
    expect(screen.getAllByText("Chưa đọc").length).toBeGreaterThan(0);
    expect(container.querySelector('time[datetime="2026-11-20T11:00:00Z"]')).toBeTruthy();
    expect(container.textContent).not.toContain("DO_NOT_RENDER_RAW");
    expect(container.querySelector('[aria-label="Thông báo chưa đọc: 2"]')).toBeTruthy();

    fireEvent.click(markOne);

    expect(await screen.findByText("Đã đánh dấu thông báo là đã đọc.")).toBeTruthy();
    await waitFor(() => expect(container.querySelector('[aria-label="Thông báo chưa đọc: 1"]')).toBeTruthy());
    expect(screen.queryByRole("button", { name: "Thông báo mới: đánh dấu đã đọc" })).toBeNull();
  });

  it("marks all read and replaces the list with the fresh first page", async () => {
    const old = item("old-1", { created_at: "2026-11-19T10:00:00Z" });
    const fresh = item("fresh-1", { read_at: "2026-11-20T12:00:00Z", created_at: "2026-11-20T12:00:00Z" });
    const list = vi.spyOn(notificationsApi, "listNotifications")
      .mockResolvedValueOnce(page([old]))
      .mockResolvedValueOnce(page([fresh]));
    const markAll = vi.spyOn(notificationsApi, "markAllNotificationsRead").mockResolvedValue({ contract: "NotificationReadAllV1", marked_count: 1 });

    const { container } = render(<InboxPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Đánh dấu tất cả đã đọc" }));

    expect(await screen.findByText("Đã đánh dấu tất cả thông báo là đã đọc.")).toBeTruthy();
    expect(list).toHaveBeenCalledTimes(2);
    expect(markAll).toHaveBeenCalledOnce();
    expect(container.querySelector('time[datetime="2026-11-19T10:00:00Z"]')).toBeNull();
    expect(container.querySelector('time[datetime="2026-11-20T12:00:00Z"]')).toBeTruthy();
  });

  it("appends load-more results, drops duplicate ids, and stops on a repeated cursor", async () => {
    const first = item("item-1");
    const duplicate = item("item-1", { created_at: "2026-11-19T10:00:00Z" });
    const second = item("item-2", { created_at: "2026-11-18T10:00:00Z" });
    const list = vi.spyOn(notificationsApi, "listNotifications")
      .mockResolvedValueOnce(page([first], { next_cursor: "cursor-1" }))
      .mockResolvedValueOnce(page([duplicate, second], { next_cursor: "cursor-1" }));

    const { container } = render(<InboxPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Tải thêm" }));

    await waitFor(() => expect(screen.getAllByRole("heading", { name: "Thông báo mới", level: 3 })).toHaveLength(2));
    expect(list).toHaveBeenCalledTimes(2);
    expect(list.mock.calls[1][0]?.cursor).toBe("cursor-1");
    expect(screen.queryByRole("button", { name: "Tải thêm" })).toBeNull();
    expect(container.querySelectorAll('time[datetime="2026-11-19T10:00:00Z"]')).toHaveLength(0);
  });

  it("shows 99+ for the capped count and keeps it capped after marking one item", async () => {
    const unread = item("unread-1");
    vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue(page([unread], { unread_count: 100 }));
    vi.spyOn(notificationsApi, "markNotificationRead").mockResolvedValue({ ...unread, read_at: "2026-11-20T12:00:00Z" });

    const { container } = render(<InboxPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Thông báo mới: đánh dấu đã đọc" }));

    expect(await screen.findByText("Đã đánh dấu thông báo là đã đọc.")).toBeTruthy();
    expect(container.querySelector('[aria-label="Thông báo chưa đọc: 99+"]')).toBeTruthy();
  });

  it("uses the fixed 404 text without offering a retry action", async () => {
    vi.spyOn(notificationsApi, "listNotifications").mockRejectedValue(
      new BackendApiError("Không tìm thấy nội dung hoặc bạn không có quyền truy cập.", "RESOURCE_NOT_FOUND", 404),
    );

    render(<InboxPage />);

    expect((await screen.findByRole("alert")).textContent).toContain("Không tìm thấy nội dung hoặc bạn không có quyền truy cập.");
    expect(screen.queryByRole("button", { name: "Thử lại" })).toBeNull();
  });

  it("does not dispatch two mark-read commands from a double click", async () => {
    const unread = item("unread-1");
    vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue(page([unread]));
    let resolveRead!: (updated: NotificationItem) => void;
    const mark = vi.spyOn(notificationsApi, "markNotificationRead").mockImplementation(
      () => new Promise((resolve) => { resolveRead = resolve; }),
    );

    render(<InboxPage />);
    const button = await screen.findByRole("button", { name: "Thông báo mới: đánh dấu đã đọc" });
    fireEvent.click(button);
    fireEvent.click(button);

    expect(mark).toHaveBeenCalledOnce();
    await act(async () => resolveRead({ ...unread, read_at: "2026-11-20T12:00:00Z" }));
  });

  it("reuses the same idempotency key after a network failure retry", async () => {
    const unread = item("unread-1");
    vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue(page([unread]));
    const mark = vi.spyOn(notificationsApi, "markNotificationRead")
      .mockRejectedValueOnce(new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0))
      .mockResolvedValueOnce({ ...unread, read_at: "2026-11-20T12:00:00Z" });

    render(<InboxPage />);
    const button = await screen.findByRole("button", { name: "Thông báo mới: đánh dấu đã đọc" });
    fireEvent.click(button);
    await screen.findByText("Không kết nối được dịch vụ.");
    fireEvent.click(button);

    await screen.findByText("Đã đánh dấu thông báo là đã đọc.");
    expect(mark).toHaveBeenCalledTimes(2);
    expect(mark.mock.calls[0][1]).toBe(mark.mock.calls[1][1]);
  });

  it("ignores a first-page result that completes after unmount", async () => {
    let resolvePage!: (result: NotificationPage) => void;
    const list = vi.spyOn(notificationsApi, "listNotifications").mockImplementation(
      () => new Promise((resolve) => { resolvePage = resolve; }),
    );
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => undefined);
    const view = render(<InboxPage />);
    await waitFor(() => expect(list).toHaveBeenCalledOnce());
    view.unmount();

    await act(async () => resolvePage(page([item("late-item")])));

    expect(list).toHaveBeenCalledOnce();
    expect(consoleError).not.toHaveBeenCalled();
  });

  it("does not claim success when read-all succeeds but the refresh fails, and shows the items as read", async () => {
    vi.spyOn(notificationsApi, "listNotifications")
      .mockResolvedValueOnce(page([item("a-1")]))
      .mockRejectedValueOnce(new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0));
    vi.spyOn(notificationsApi, "markAllNotificationsRead").mockResolvedValue({ contract: "NotificationReadAllV1", marked_count: 1 });

    render(<InboxPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Đánh dấu tất cả đã đọc" }));

    expect(await screen.findByText("Đã gửi yêu cầu; hãy tải lại để xem trạng thái mới.")).toBeTruthy();
    expect(screen.queryByText("Đã đánh dấu tất cả thông báo là đã đọc.")).toBeNull();
    expect(screen.queryByRole("button", { name: /đánh dấu đã đọc/ })).toBeNull();
  });

  it("refreshes the list when marking an item answers 404", async () => {
    const stuck = item("gone-1");
    const list = vi.spyOn(notificationsApi, "listNotifications")
      .mockResolvedValueOnce(page([stuck]))
      .mockResolvedValueOnce(page([]));
    vi.spyOn(notificationsApi, "markNotificationRead").mockRejectedValue(new BackendApiError(notificationsApi.NOTIFICATION_NOT_FOUND_MESSAGE, "RESOURCE_NOT_FOUND", 404));

    render(<InboxPage />);
    fireEvent.click(await screen.findByRole("button", { name: "Thông báo mới: đánh dấu đã đọc" }));

    expect(await screen.findByText("Hộp thư hiện đang trống.")).toBeTruthy();
    expect(screen.getByText(notificationsApi.NOTIFICATION_NOT_FOUND_MESSAGE)).toBeTruthy();
    expect(list).toHaveBeenCalledTimes(2);
  });

  it("renders an invalid timestamp as a dash instead of crashing", async () => {
    vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue(page([item("bad-1", { created_at: "not-a-date" })]));

    render(<InboxPage />);

    expect(await screen.findByText("—")).toBeTruthy();
  });
});
