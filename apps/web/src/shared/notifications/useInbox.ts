import { useCallback, useEffect, useRef, useState } from "react";
import { BackendApiError, createIdempotencyKey } from "../api/backendApi";
import {
  NOTIFICATION_NOT_FOUND_MESSAGE,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type NotificationItem,
} from "../api/notificationsApi";

export type InboxStatus = "loading" | "ready" | "error";

export interface InboxState {
  status: InboxStatus;
  items: NotificationItem[];
  unreadCount: number;
  nextCursor: string | null;
  loadingMore: boolean;
  busy: boolean;
  errorMessage: string | null;
  errorStatus: number | null;
  message: string | null;
  messageIsError: boolean;
  retryable: boolean;
  loadMore: () => Promise<void>;
  reload: () => Promise<void>;
  markRead: (inboxItemId: string) => Promise<void>;
  markAllRead: () => Promise<void>;
}

const operationFailedMessage = "Không thể hoàn tất yêu cầu.";
const markReadSuccessMessage = "Đã đánh dấu thông báo là đã đọc.";
const markAllSuccessMessage = "Đã đánh dấu tất cả thông báo là đã đọc.";
const markAllUnconfirmedMessage = "Đã gửi yêu cầu; hãy tải lại để xem trạng thái mới.";

function errorMessage(cause: unknown): string {
  return cause instanceof Error && cause.message ? cause.message : operationFailedMessage;
}

function errorStatus(cause: unknown): number | null {
  return cause instanceof BackendApiError ? cause.status : null;
}

function isDefiniteRejection(cause: unknown): boolean {
  return cause instanceof BackendApiError && cause.status >= 400 && cause.status < 500;
}

function unreadCountFrom(value: number): number {
  return Math.max(0, Math.min(100, value));
}

export function useInbox(): InboxState {
  const [status, setStatus] = useState<InboxStatus>("loading");
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loadErrorStatus, setLoadErrorStatus] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [messageIsError, setMessageIsError] = useState(false);

  const mounted = useRef(false);
  const busyRef = useRef(false);
  const loadingMoreRef = useRef(false);
  const loadedOnce = useRef(false);
  const viewVersion = useRef(0);
  const pageController = useRef<AbortController | null>(null);
  const moreController = useRef<AbortController | null>(null);
  const seenCursors = useRef(new Set<string>());
  const pendingKeys = useRef(new Map<string, string>());
  // True when the last first-page load succeeded; read-all only claims success on a confirmed refresh.
  const lastLoadOk = useRef(false);

  const reload = useCallback(async () => {
    if (!mounted.current) return;
    const version = ++viewVersion.current;
    pageController.current?.abort();
    moreController.current?.abort();
    loadingMoreRef.current = false;
    setLoadingMore(false);
    seenCursors.current.clear();
    const controller = new AbortController();
    pageController.current = controller;
    setStatus("loading");
    setLoadError(null);
    setLoadErrorStatus(null);
    setMessage(null);
    lastLoadOk.current = false;

    try {
      const page = await listNotifications({ signal: controller.signal });
      if (!mounted.current || version !== viewVersion.current) return;
      loadedOnce.current = true;
      lastLoadOk.current = true;
      // A fresh page ends any pending read-all retry: a replayed key would return the stale first result.
      pendingKeys.current.delete("read-all");
      setItems(page.items);
      setUnreadCount(unreadCountFrom(page.unread_count));
      setNextCursor(page.next_cursor);
      setStatus("ready");
    } catch (cause) {
      if (cause instanceof Error && cause.name === "AbortError") return;
      if (!mounted.current || version !== viewVersion.current) return;
      setLoadError(errorMessage(cause));
      setLoadErrorStatus(errorStatus(cause));
      setStatus(loadedOnce.current ? "ready" : "error");
    } finally {
      if (pageController.current === controller) pageController.current = null;
    }
  }, []);

  useEffect(() => {
    mounted.current = true;
    let effectActive = true;
    void Promise.resolve().then(() => {
      if (effectActive) void reload();
    });
    return () => {
      effectActive = false;
      mounted.current = false;
      viewVersion.current += 1;
      pageController.current?.abort();
      moreController.current?.abort();
    };
  }, [reload]);

  const loadMore = useCallback(async () => {
    if (!mounted.current || status !== "ready" || !nextCursor || busyRef.current || loadingMoreRef.current) return;
    const cursor = nextCursor;
    if (seenCursors.current.has(cursor)) {
      setNextCursor(null);
      return;
    }
    seenCursors.current.add(cursor);
    const version = viewVersion.current;
    const controller = new AbortController();
    moreController.current = controller;
    loadingMoreRef.current = true;
    setLoadingMore(true);
    setMessage(null);

    try {
      const page = await listNotifications({ cursor, signal: controller.signal });
      if (!mounted.current || version !== viewVersion.current) return;
      setItems((current) => {
        const ids = new Set(current.map((item) => item.inbox_item_id));
        const additions = page.items.filter((item) => !ids.has(item.inbox_item_id));
        return additions.length ? [...current, ...additions] : current;
      });
      setNextCursor(page.next_cursor && !seenCursors.current.has(page.next_cursor) ? page.next_cursor : null);
    } catch (cause) {
      if (cause instanceof Error && cause.name === "AbortError") {
        if (version === viewVersion.current) seenCursors.current.delete(cursor);
        return;
      }
      if (!mounted.current || version !== viewVersion.current) return;
      seenCursors.current.delete(cursor);
      setMessage(errorMessage(cause));
      setMessageIsError(true);
    } finally {
      if (moreController.current === controller) {
        moreController.current = null;
        loadingMoreRef.current = false;
        if (mounted.current && version === viewVersion.current) setLoadingMore(false);
      }
    }
  }, [nextCursor, status]);

  const markRead = useCallback(async (inboxItemId: string) => {
    if (!mounted.current || busyRef.current) return;
    const target = items.find((item) => item.inbox_item_id === inboxItemId);
    if (!target || target.read_at !== null) return;
    const signature = `read:${inboxItemId}`;
    const key = pendingKeys.current.get(signature) ?? createIdempotencyKey();
    pendingKeys.current.set(signature, key);
    const version = viewVersion.current;
    busyRef.current = true;
    setBusy(true);
    setMessage(null);

    try {
      const updated = await markNotificationRead(inboxItemId, key);
      pendingKeys.current.delete(signature);
      if (!mounted.current || version !== viewVersion.current) return;
      setItems((current) => current.map((item) => item.inbox_item_id === inboxItemId ? updated : item));
      if (target.read_at === null) setUnreadCount((current) => current === 100 ? 100 : Math.max(0, current - 1));
      setMessage(markReadSuccessMessage);
      setMessageIsError(false);
    } catch (cause) {
      if (isDefiniteRejection(cause)) pendingKeys.current.delete(signature);
      if (!mounted.current || version !== viewVersion.current) return;
      const failure = errorMessage(cause);
      // An expired or removed item answers 404: refresh the list so it does not stay stuck as unread.
      if (errorStatus(cause) === 404) await reload();
      if (!mounted.current) return;
      setMessage(failure);
      setMessageIsError(true);
    } finally {
      busyRef.current = false;
      if (mounted.current) setBusy(false);
    }
  }, [items, reload]);

  const markAllRead = useCallback(async () => {
    if (!mounted.current || busyRef.current || unreadCount === 0) return;
    const signature = "read-all";
    const key = pendingKeys.current.get(signature) ?? createIdempotencyKey();
    pendingKeys.current.set(signature, key);
    const version = viewVersion.current;
    busyRef.current = true;
    setBusy(true);
    setMessage(null);

    try {
      await markAllNotificationsRead(key);
      pendingKeys.current.delete(signature);
      if (!mounted.current || version !== viewVersion.current) return;
      // The server marked everything unread at that moment: show it at once, then confirm with a fresh page.
      const readAt = new Date().toISOString();
      setItems((current) => current.map((item) => (item.read_at === null ? { ...item, read_at: readAt } : item)));
      setUnreadCount(0);
      await reload();
      if (mounted.current) {
        setMessage(lastLoadOk.current ? markAllSuccessMessage : markAllUnconfirmedMessage);
        setMessageIsError(false);
      }
    } catch (cause) {
      if (isDefiniteRejection(cause)) pendingKeys.current.delete(signature);
      if (!mounted.current || version !== viewVersion.current) return;
      setMessage(errorMessage(cause));
      setMessageIsError(true);
    } finally {
      busyRef.current = false;
      if (mounted.current) setBusy(false);
    }
  }, [reload, unreadCount]);

  const retryable = !(status === "error" && (loadErrorStatus === 404 || loadError === NOTIFICATION_NOT_FOUND_MESSAGE));
  return {
    status,
    items,
    unreadCount,
    nextCursor,
    loadingMore,
    busy,
    errorMessage: loadError,
    errorStatus: loadErrorStatus,
    message,
    messageIsError,
    retryable,
    loadMore,
    reload,
    markRead,
    markAllRead,
  };
}
