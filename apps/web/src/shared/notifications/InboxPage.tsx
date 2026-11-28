import { PageHeading } from "../components/FeatureAvailability";
import { NOTIFICATION_NOT_FOUND_MESSAGE } from "../api/notificationsApi";
import { resolveNotificationText } from "./notificationTemplates";
import { useInbox } from "./useInbox";

const dateTime = new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" });

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateTime.format(date);
}

function unreadLabel(count: number): string {
  return count === 100 ? "99+" : String(count);
}

export function InboxPage() {
  const inbox = useInbox();
  const hasItems = inbox.items.length > 0;

  return (
    <div className="s2l-page tw-page">
      <PageHeading eyebrow="Thông báo" title="Hộp thư" description="Thông báo trong ứng dụng của tài khoản hiện tại." />

      {inbox.status === "loading" && (
        <div className="s2l-data-card" role="status" aria-busy="true">
          Đang tải hộp thư…
        </div>
      )}

      {inbox.status === "error" && (
        <section className="s2l-data-card" aria-labelledby="inbox-error-heading">
          <h2 id="inbox-error-heading">Không thể tải hộp thư</h2>
          <p role="alert">{inbox.errorMessage ?? "Không thể hoàn tất yêu cầu."}</p>
          {inbox.retryable && <button type="button" className="s2l-button tw-btn" onClick={() => void inbox.reload()}>Thử lại</button>}
        </section>
      )}

      {inbox.status === "ready" && inbox.errorMessage && (
        <section className="s2l-alert" aria-live="polite">
          <p>{inbox.errorMessage}</p>
          {inbox.errorStatus !== 404 && inbox.errorMessage !== NOTIFICATION_NOT_FOUND_MESSAGE && <button type="button" className="s2l-button tw-btn" disabled={inbox.busy} onClick={() => void inbox.reload()}>Thử lại</button>}
        </section>
      )}

      {(inbox.status === "ready" || hasItems) && inbox.unreadCount > 0 && (
        <p className="s2l-empty-copy tw-meta" aria-label={`Thông báo chưa đọc: ${unreadLabel(inbox.unreadCount)}`}>
          Chưa đọc: <strong>{unreadLabel(inbox.unreadCount)}</strong>
        </p>
      )}

      {inbox.message ? (
        <p className={inbox.messageIsError ? "s2l-alert" : "s2l-empty-copy"} aria-live="polite">
          {inbox.message}
        </p>
      ) : null}

      {inbox.status === "ready" && !hasItems && (
        <p className="s2l-empty-copy">Hộp thư hiện đang trống.</p>
      )}

      {hasItems && (
        <section className="s2l-data-card" aria-label="Danh sách thông báo" aria-busy={inbox.status === "loading" || inbox.loadingMore}>
          <div className="tw-row tw-between tw-wrap">
            <h2 className="tw-h2">Thông báo</h2>
            <button
              type="button"
              className="s2l-button tw-btn"
              disabled={inbox.busy || inbox.status !== "ready" || inbox.unreadCount === 0}
              onClick={() => void inbox.markAllRead()}
            >
              Đánh dấu tất cả đã đọc
            </button>
          </div>
          <ul className="s2l-record-list" aria-label="Thông báo trong hộp thư">
            {inbox.items.map((item) => {
              const text = resolveNotificationText(item.notification_type, item.template_version);
              const unread = item.read_at === null;
              return (
                <li key={item.inbox_item_id}>
                  <article className="tw-row tw-between tw-wrap" data-unread={unread ? "true" : undefined}>
                    <div>
                      <h3 className="tw-h2">{text.title}</h3>
                      {text.body && <p>{text.body}</p>}
                      {unread
                        ? <p className="tw-chip">Chưa đọc</p>
                        : <p className="s2l-empty-copy">Đã đọc <time dateTime={item.read_at!}>{formatTime(item.read_at!)}</time></p>}
                      <p className="s2l-empty-copy"><time dateTime={item.created_at}>{formatTime(item.created_at)}</time></p>
                    </div>
                    {unread && (
                      <button
                        type="button"
                        className="s2l-button tw-btn"
                        disabled={inbox.busy || inbox.status !== "ready"}
                        aria-label={`${text.title}: đánh dấu đã đọc`}
                        onClick={() => void inbox.markRead(item.inbox_item_id)}
                      >
                        Đánh dấu đã đọc
                      </button>
                    )}
                  </article>
                </li>
              );
            })}
          </ul>
          {inbox.nextCursor && (
            <button
              type="button"
              className="s2l-button tw-btn"
              disabled={inbox.status !== "ready" || inbox.loadingMore || inbox.busy}
              onClick={() => void inbox.loadMore()}
            >
              {inbox.loadingMore ? "Đang tải thêm…" : "Tải thêm"}
            </button>
          )}
        </section>
      )}
    </div>
  );
}
