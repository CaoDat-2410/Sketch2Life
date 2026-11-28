import { useEffect, useState } from "react";
import { listNotifications } from "../api/notificationsApi";

const unreadChangedEvent = "s2l:notifications-read";

export function notifyNotificationsRead() {
  window.dispatchEvent(new Event(unreadChangedEvent));
}

export function useUnreadCount(enabled: boolean, route: string): number | null {
  const [count, setCount] = useState<number | null>(null);

  useEffect(() => {
    if (!enabled) {
      setCount(null);
      return;
    }
    let active = true;
    let controller: AbortController | undefined;
    const refresh = () => {
      controller?.abort();
      const current = new AbortController();
      controller = current;
      void listNotifications({ limit: 1, signal: current.signal }).then((page) => {
        if (active && !current.signal.aborted) {
          const value = page.unread_count;
          setCount(Number.isInteger(value) && value > 0 ? value : null);
        }
      }).catch(() => {
        if (active && !current.signal.aborted) setCount(null);
      });
    };
    const onVisible = () => { if (document.visibilityState === "visible") refresh(); };
    refresh();
    window.addEventListener("focus", refresh);
    window.addEventListener(unreadChangedEvent, refresh);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      active = false;
      controller?.abort();
      window.removeEventListener("focus", refresh);
      window.removeEventListener(unreadChangedEvent, refresh);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [enabled, route]);

  return enabled ? count : null;
}
