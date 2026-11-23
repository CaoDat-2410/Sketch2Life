import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ArrowLeft, ArrowRight, Plus, RefreshCw } from "lucide-react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { Alert, Button, FormField } from "../../../../shared/ui";
import { AdminBe1Error } from "../services/be1Client";
import { managerBusinessService, type ParentGroup } from "../services/managerBusinessService";

function errorMessage(cause: unknown) {
  return cause instanceof Error ? cause.message : "Không hoàn tất được yêu cầu nhóm phụ huynh.";
}

function createIdempotencyKey() {
  if (typeof globalThis.crypto?.randomUUID === "function") {
    return globalThis.crypto.randomUUID();
  }
  return "manager-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2);
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? "Ngày tạo chưa được cung cấp" : date.toLocaleDateString("vi-VN");
}

export function ParentGroupsPage() {
  const [groups, setGroups] = useState<ParentGroup[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [cursorHistory, setCursorHistory] = useState<Array<string | undefined>>([undefined]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [creating, setCreating] = useState(false);
  const [creationError, setCreationError] = useState("");
  const [creationSuccess, setCreationSuccess] = useState("");
  const [retryKey, setRetryKey] = useState<string | null>(null);
  const cursor = cursorHistory[cursorHistory.length - 1];

  const loadGroups = useCallback(async (pageCursor?: string, signal?: AbortSignal) => {
    try {
      const page = await managerBusinessService.parentGroups(pageCursor, signal);
      if (!signal?.aborted) {
        setGroups(page.items);
        setNextCursor(page.next_cursor);
      }
    } catch (cause: unknown) {
      if (!signal?.aborted) {
        setGroups([]);
        setNextCursor(null);
        setListError(errorMessage(cause));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    managerBusinessService.parentGroups(cursor, controller.signal)
      .then((page) => {
        if (!controller.signal.aborted) {
          setGroups(page.items);
          setNextCursor(page.next_cursor);
          setListError("");
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setGroups([]);
          setNextCursor(null);
          setListError(errorMessage(cause));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [cursor]);

  const createGroup = async (event: FormEvent) => {
    event.preventDefault();
    const name = displayName.trim();
    if (!name || creating) return;
    const idempotencyKey = retryKey ?? createIdempotencyKey();
    setCreating(true);
    setCreationError("");
    setCreationSuccess("");
    try {
      const created = await managerBusinessService.createParentGroup(name, idempotencyKey);
      setDisplayName("");
      setRetryKey(null);
      setCreationSuccess("Đã tạo nhóm “" + created.display_name + "” theo xác nhận của backend.");
      setLoading(true);
      setListError("");
      await loadGroups(cursor);
    } catch (cause: unknown) {
      setCreationError(errorMessage(cause));
      const requestWasRejected = cause instanceof AdminBe1Error
        && cause.status >= 400
        && cause.status < 500
        && cause.status !== 408;
      setRetryKey(requestWasRejected ? null : idempotencyKey);
    } finally {
      setCreating(false);
    }
  };

  const requestOutcomeUnknown = retryKey !== null;
  const pageNumber = cursorHistory.length;

  return (
    <div className="s2l-page manager-business-page">
      <PageHeading
        eyebrow="School Manager · Lesson Library"
        title="Nhóm phụ huynh"
        description="Danh sách và tạo nhóm được xác minh theo organization hiện hành."
        action={
          <button
            type="button"
            className="manager-business-button"
            onClick={() => {
              setLoading(true);
              setListError("");
              void loadGroups(cursor);
            }}
            disabled={loading}
          >
            <RefreshCw size={16} aria-hidden="true" />
            Làm mới
          </button>
        }
      />

      {listError && <Alert className="manager-business-alert" tone="danger" role="alert">{listError}</Alert>}

      <div className="manager-business-split">
        <section className="manager-business-card cozy-form-card cozy-form-card--wide cozy-form-stack">
          <div className="manager-business-card-heading">
            <div>
              <p className="manager-business-eyebrow">POST · Idempotency-Key</p>
              <h2>Tạo nhóm trong trường</h2>
            </div>
            <span className="manager-business-chip">school_admin</span>
          </div>
          <form className="manager-business-create-form cozy-form-stack" onSubmit={(event) => void createGroup(event)}>
            <FormField
              label="Tên nhóm phụ huynh"
              htmlFor="parent-group-name"
              required
              help="Nếu mạng ngắt và kết quả chưa rõ, gửi lại sẽ dùng cùng mã yêu cầu để tránh tạo trùng."
            >
              <input
                id="parent-group-name"
                className="cozy-input"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                minLength={1}
                maxLength={120}
                required
                disabled={creating || requestOutcomeUnknown}
                placeholder="Ví dụ: Phụ huynh lớp Lá 1"
              />
            </FormField>
            {creationError && <Alert role="alert" tone="danger">{creationError}</Alert>}
            {creationSuccess && <Alert role="status" tone="success">{creationSuccess}</Alert>}
            {!creating && !displayName.trim() && (
              <p className="cozy-form-disabled-hint">Nhập tên nhóm phụ huynh để bật nút tạo nhóm.</p>
            )}
            <div className="cozy-form-actions" style={{ marginTop: 0 }}>
              <Button
                type="submit"
                variant="primary"
                loading={creating}
                disabled={creating || !displayName.trim()}
                iconLeft={<Plus size={16} aria-hidden="true" />}
              >
                {creating ? "Đang gửi…" : requestOutcomeUnknown ? "Gửi lại cùng yêu cầu" : "Tạo nhóm"}
              </Button>
            </div>
          </form>
        </section>

        <section className="manager-business-card">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">GET · Lesson Library</p>
            <h2>Nhóm đã tạo</h2>
          </div>
          {groups.length > 0 && <span className="manager-business-chip">{groups.length} nhóm</span>}
        </div>
        {loading ? (
          <p className="manager-business-state" role="status">Đang tải danh sách nhóm…</p>
        ) : groups.length === 0 ? (
          <p className="manager-business-state">Organization chưa có nhóm phụ huynh nào.</p>
        ) : (
          <ul className="manager-business-group-list">
            {groups.map((group) => (
              <li key={group.parent_group_id}>
                <span className="manager-business-avatar" aria-hidden="true">{group.display_name.slice(0, 1).toLocaleUpperCase()}</span>
                <span className="manager-business-group-copy">
                  <strong>{group.display_name}</strong>
                  <small><time dateTime={group.created_at}>{formatDate(group.created_at)}</time> · {group.state === "ACTIVE" ? "Đang hoạt động" : "Đã lưu trữ"}</small>
                </span>
              </li>
            ))}
          </ul>
        )}
        <div className="manager-business-pagination">
          <span>Trang {pageNumber}</span>
          <div>
            <button
              type="button"
              className="manager-business-button"
              onClick={() => {
                setLoading(true);
                setListError("");
                setCursorHistory((history) => history.slice(0, -1));
              }}
              disabled={loading || pageNumber <= 1}
            >
              <ArrowLeft size={15} aria-hidden="true" /> Trước
            </button>
            <button
              type="button"
              className="manager-business-button"
              onClick={() => {
                if (!nextCursor) return;
                setLoading(true);
                setListError("");
                setCursorHistory((history) => [...history, nextCursor]);
              }}
              disabled={loading || !nextCursor}
            >
              Tiếp <ArrowRight size={15} aria-hidden="true" />
            </button>
          </div>
        </div>
      </section>
      </div>

      <section className="manager-business-card manager-business-limitation">
        <div>
          <p className="manager-business-eyebrow">Chưa khả dụng</p>
          <h2>Mời thành viên và thu hồi membership</h2>
          <p>
            Chưa có API tra cứu Parent trong organization và chưa có API đọc danh sách membership
            để kiểm tra đúng người, revision trước khi gửi hoặc thu hồi lời mời.
          </p>
        </div>
        <span className="manager-business-chip is-pending">Chờ API</span>
      </section>
    </div>
  );
}
