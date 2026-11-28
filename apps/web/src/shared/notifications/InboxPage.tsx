import { PageHeading } from "../components/FeatureAvailability";
import { NOTIFICATION_NOT_FOUND_MESSAGE } from "../api/notificationsApi";
import { resolveNotificationText } from "./notificationTemplates";
import { useInbox } from "./useInbox";
import { Button, formatDateTimeDdMmYyyy } from "../ui";
import "./InboxPage.css";

function unreadLabel(count: number): string {
  return count === 100 ? "99+" : String(count);
}

export function InboxPage() {
  const inbox = useInbox();
  const hasItems = inbox.items.length > 0;

  return (
    <div className="s2l-page tw-page s2l-inbox">
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

      {!hasItems && inbox.status === "ready" && inbox.unreadCount > 0 && (
        <p className="s2l-inbox-count" aria-label={`Thông báo chưa đọc: ${unreadLabel(inbox.unreadCount)}`}>
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
          <div className="s2l-inbox-header">
            <div className="s2l-inbox-heading">
              <h2>Thông báo</h2>
              {inbox.unreadCount > 0 && (
                <p className="s2l-inbox-count" aria-label={`Thông báo chưa đọc: ${unreadLabel(inbox.unreadCount)}`}>
                  Chưa đọc: <strong>{unreadLabel(inbox.unreadCount)}</strong>
                </p>
              )}
            </div>
            <Button variant="secondary" disabled={inbox.busy || inbox.status !== "ready" || inbox.unreadCount === 0} onClick={() => void inbox.markAllRead()}>
              Đánh dấu tất cả đã đọc
            </Button>
          </div>
          <ul className="s2l-inbox-list" aria-label="Thông báo trong hộp thư">
            {inbox.items.map((item) => {
              const text = resolveNotificationText(item.notification_type, item.template_version);
              const unread = item.read_at === null;
              return (
                <li key={item.inbox_item_id}>
                  <article className="s2l-inbox-row" data-unread={unread ? "true" : undefined}>
                    <div className="s2l-inbox-content">
                      <h3>{text.title}</h3>
                      {text.body && <p>{text.body}</p>}
                      <p className="s2l-inbox-meta">
                        {unread ? <span>Chưa đọc</span> : <span>Đã đọc <time dateTime={item.read_at!}>{formatDateTimeDdMmYyyy(item.read_at!, "—")}</time></span>}
                        <span aria-hidden="true">·</span>
                        <time dateTime={item.created_at}>{formatDateTimeDdMmYyyy(item.created_at, "—")}</time>
                      </p>
                    </div>
                    {unread && (
                      <Button
                        variant="secondary"
                        className="s2l-inbox-action"
                        disabled={inbox.busy || inbox.status !== "ready"}
                        aria-label={`${text.title}: đánh dấu đã đọc`}
                        onClick={() => void inbox.markRead(item.inbox_item_id)}
                      >
                        Đánh dấu đã đọc
                      </Button>
                    )}
                  </article>
                </li>
              );
            })}
          </ul>
          {inbox.nextCursor && (
            <Button
              variant="secondary"
              className="s2l-inbox-more"
              disabled={inbox.status !== "ready" || inbox.loadingMore || inbox.busy}
              onClick={() => void inbox.loadMore()}
            >
              {inbox.loadingMore ? "Đang tải thêm…" : "Tải thêm"}
            </Button>
          )}
        </section>
      )}
    </div>
  );
}
