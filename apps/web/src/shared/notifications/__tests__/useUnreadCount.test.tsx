import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import * as api from "../../api/notificationsApi";
import { notifyNotificationsRead, useUnreadCount } from "../useUnreadCount";

const page = (unread_count: number) => ({ contract: "NotificationPageV1" as const, items: [], next_cursor: null, unread_count });
afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe("useUnreadCount", () => {
  it("hides loading, zero, invalid and failed counts", async () => {
    const list = vi.spyOn(api, "listNotifications").mockResolvedValueOnce(page(0)).mockResolvedValueOnce(page(1.5)).mockRejectedValueOnce(new Error());
    const { result } = renderHook(() => useUnreadCount(true, "/"));
    expect(result.current).toBeNull();
    await waitFor(() => expect(list).toHaveBeenCalledTimes(1));
    await act(async () => { notifyNotificationsRead(); });
    expect(result.current).toBeNull();
    await act(async () => { notifyNotificationsRead(); });
    expect(result.current).toBeNull();
  });

  it("refreshes on route, visibility, focus and read events; ignores stale results and never polls", async () => {
    let resolveOld!: (value: ReturnType<typeof page>) => void;
    const list = vi.spyOn(api, "listNotifications").mockResolvedValueOnce(page(4))
      .mockImplementationOnce(() => new Promise((resolve) => { resolveOld = resolve; }))
      .mockResolvedValue(page(2));
    const interval = vi.spyOn(window, "setInterval");
    const { result, rerender, unmount } = renderHook(({ route }) => useUnreadCount(true, route), { initialProps: { route: "/one" } });
    await act(async () => {});
    expect(result.current).toBe(4);
    expect(list.mock.calls[0][0]).toMatchObject({ limit: 1 });
    act(() => { window.dispatchEvent(new Event("focus")); });
    expect(result.current).toBe(4);
    const oldSignal = list.mock.calls[1][0]?.signal;
    await act(async () => { notifyNotificationsRead(); });
    expect(oldSignal?.aborted).toBe(true);
    expect(result.current).toBe(2);
    await act(async () => { resolveOld(page(9)); });
    expect(result.current).toBe(2);
    rerender({ route: "/two" });
    expect(list).toHaveBeenCalledTimes(4);
    Object.defineProperty(document, "visibilityState", { configurable: true, value: "visible" });
    await act(async () => { document.dispatchEvent(new Event("visibilitychange")); });
    expect(list).toHaveBeenCalledTimes(5);
    expect(interval).not.toHaveBeenCalled();
    const lastSignal = list.mock.calls[4][0]?.signal;
    unmount();
    expect(lastSignal?.aborted).toBe(true);
  });
});
