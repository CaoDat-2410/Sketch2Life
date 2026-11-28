import { ModalPortal } from "../../../../shared/ui/ModalPortal";
import { useMemo, useRef, useState, type FormEvent } from "react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { Alert, EmptyState } from "../../../../shared/ui";
import { AdminBe1Error, adminOrganizationId } from "../services/be1Client";
import { authService } from "../services/authService";
import {
  managerBusinessService,
  type Be1DataRequest,
  type Be1DataRequestState,
  type Be1DataRequestType,
} from "../services/managerBusinessService";
import "../styles/manager-business.css";

const SESSION_REQUEST_IDS_KEY = "s2l.manager.data-request-ids.v1";

function sessionRequestIdsKey(): string {
  let organizationId = "unconfigured";
  let accountId = "";
  try { organizationId = adminOrganizationId(); } catch { /* Keep local state usable before configuration loads. */ }
  try { accountId = authService.getCurrentUser()?.uid ?? ""; } catch { /* Account scope is optional when auth is unavailable. */ }
  return `${SESSION_REQUEST_IDS_KEY}:${encodeURIComponent(organizationId)}${accountId ? `:${encodeURIComponent(accountId)}` : ""}`;
}

type DataRequestDisplay = {
  request_id: string;
  request_type?: Be1DataRequestType;
  state: Be1DataRequestState;
  unresolved_items?: number;
  completion_claimed: boolean;
};

function loadCreatedRequestIds(storageKey: string): string[] {
  try {
    const raw = window.sessionStorage.getItem(storageKey);
    if (!raw) return [];
    const value: unknown = JSON.parse(raw);
    return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string" && item.length > 0) : [];
  } catch {
    return [];
  }
}

function saveCreatedRequestIds(storageKey: string, ids: string[]) {
  try {
    window.sessionStorage.setItem(storageKey, JSON.stringify(ids));
  } catch {
    // The page still keeps the ids in component state when session storage is unavailable.
  }
}

function requestStateLabel(state: Be1DataRequestState, completionClaimed: boolean) {
  switch (state) {
    case "requested": return "Đã ghi nhận";
    case "running": return "Đang xử lý";
    case "awaiting_external_purge": return "Đang chờ xóa dữ liệu bên ngoài";
    case "completed": return completionClaimed ? "Đã hoàn tất" : "Chờ xác nhận hoàn tất";
    case "exception": return "Cần xử lý";
    default: return "Trạng thái không xác định";
  }
}

function requestTypeLabel(requestType: Be1DataRequestType) {
  return requestType === "export" ? "Xuất dữ liệu" : "Yêu cầu xóa dữ liệu";
}

function safeErrorMessage(cause: unknown, kind: "create" | "lookup") {
  if (cause instanceof AdminBe1Error) {
    if (cause.status === 404) return "Không tìm thấy yêu cầu hoặc bạn không có quyền truy cập.";
    if (cause.status === 403) return "Không có quyền thực hiện thao tác này.";
    if (cause.status === 0) {
      return kind === "create"
        ? "Chưa rõ kết quả. Hãy kiểm tra trạng thái trước khi gửi lại."
        : "Không kết nối được để kiểm tra trạng thái. Hãy thử lại.";
    }
    return cause.message;
  }
  return kind === "create"
    ? "Chưa rõ kết quả. Hãy kiểm tra trạng thái trước khi gửi lại."
    : "Không thể kiểm tra trạng thái lúc này. Hãy thử lại.";
}

export function DataRequestsPage() {
  const requestIdsStorageKey = useMemo(() => sessionRequestIdsKey(), []);
  const [requestType, setRequestType] = useState<Be1DataRequestType>("export");
  const [targetRef, setTargetRef] = useState("");
  const [createdRequestIds, setCreatedRequestIds] = useState<string[]>(() => loadCreatedRequestIds(requestIdsStorageKey));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const submitLockRef = useRef(false);
  const [formError, setFormError] = useState("");
  const [requestMessage, setRequestMessage] = useState("");
  const [deleteConfirmationOpen, setDeleteConfirmationOpen] = useState(false);
  const [result, setResult] = useState<DataRequestDisplay | null>(null);
  const [lookupId, setLookupId] = useState("");
  const [isLookingUp, setIsLookingUp] = useState(false);
  const lookupLockRef = useRef(false);
  const [lookupError, setLookupError] = useState("");

  const submitRequest = async () => {
    if (submitLockRef.current) return;
    const safeTargetRef = targetRef;
    if (!safeTargetRef || safeTargetRef.length > 256) {
      setFormError("Nhập tham chiếu gồm từ 1 đến 256 ký tự.");
      return;
    }

    submitLockRef.current = true;
    setIsSubmitting(true);
    setFormError("");
    setRequestMessage("");
    try {
      const created = await managerBusinessService.createDataRequest(requestType, safeTargetRef);
      const nextIds = [created.request_id, ...createdRequestIds.filter((id) => id !== created.request_id)];
      setCreatedRequestIds(nextIds);
      saveCreatedRequestIds(requestIdsStorageKey, nextIds);
      setLookupId(created.request_id);
      setResult({
        request_id: created.request_id,
        request_type: requestType,
        state: created.state,
        completion_claimed: created.completion_claimed,
      });
      setRequestMessage("Đã ghi nhận yêu cầu.");
    } catch (cause) {
      setFormError(safeErrorMessage(cause, "create"));
    } finally {
      submitLockRef.current = false;
      setIsSubmitting(false);
      setDeleteConfirmationOpen(false);
    }
  };

  const handleCreateSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError("");
    setRequestMessage("");
    if (requestType === "delete") {
      setDeleteConfirmationOpen(true);
      return;
    }
    void submitRequest();
  };

  const checkRequest = async (id = lookupId) => {
    const safeId = id;
    if (!safeId.trim()) {
      setLookupError("Nhập mã yêu cầu để kiểm tra.");
      return;
    }
    if (lookupLockRef.current) return;
    lookupLockRef.current = true;
    setIsLookingUp(true);
    setLookupError("");
    try {
      const request: Be1DataRequest = await managerBusinessService.getDataRequest(safeId);
      setResult(request);
      setLookupId(request.request_id);
    } catch (cause) {
      setResult(null);
      setLookupError(safeErrorMessage(cause, "lookup"));
    } finally {
      lookupLockRef.current = false;
      setIsLookingUp(false);
    }
  };

  return (
    <div className="s2l-page manager-business-page manager-data-requests">
      <PageHeading
        eyebrow="Quản lý trường"
        title="Yêu cầu dữ liệu"
        description="Tạo yêu cầu xuất hoặc xóa dữ liệu trong phạm vi nhà trường, rồi kiểm tra trạng thái bằng mã yêu cầu."
      />

      <section className="manager-business-card manager-data-request-card" aria-labelledby="manager-data-request-create-title">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">Khởi tạo</p>
            <h2 id="manager-data-request-create-title">Tạo yêu cầu</h2>
          </div>
        </div>
        <form className="manager-business-data-form" onSubmit={handleCreateSubmit}>
          <fieldset className="manager-data-request-types">
            <legend>Loại yêu cầu</legend>
            <label>
              <input type="radio" name="manager-data-request-type" value="export" checked={requestType === "export"} onChange={() => setRequestType("export")} />
              Xuất dữ liệu
            </label>
            <label>
              <input type="radio" name="manager-data-request-type" value="delete" checked={requestType === "delete"} onChange={() => setRequestType("delete")} />
              Xóa dữ liệu
            </label>
          </fieldset>

          <label className="manager-data-request-target" htmlFor="manager-data-request-target-ref">
            Tham chiếu đích
            <input
              id="manager-data-request-target-ref"
              name="target_ref"
              type="text"
              value={targetRef}
              minLength={1}
              maxLength={256}
              required
              aria-describedby="manager-data-request-target-help"
              onChange={(event) => setTargetRef(event.target.value)}
            />
          </label>
          <p id="manager-data-request-target-help" className="manager-business-subtle manager-data-request-help">
            Nhập mã tham chiếu được cung cấp, chẳng hạn mã trẻ, lớp hoặc tổ chức.
          </p>
          {formError && <Alert role="alert" tone="danger">{formError}</Alert>}
          {requestMessage && <Alert role="status">{requestMessage}</Alert>}
          <button type="submit" className="manager-business-button is-primary" disabled={isSubmitting}>
            {isSubmitting ? "Đang gửi…" : "Gửi yêu cầu"}
          </button>
        </form>
      </section>

      <section className="manager-business-card manager-data-request-card" aria-labelledby="manager-data-request-lookup-title">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">Tra cứu</p>
            <h2 id="manager-data-request-lookup-title">Kiểm tra trạng thái</h2>
          </div>
        </div>
        <form className="manager-data-request-lookup" onSubmit={(event) => { event.preventDefault(); void checkRequest(); }}>
          <label htmlFor="manager-data-request-id">Mã yêu cầu</label>
          <div className="manager-data-request-lookup-row">
            <input
              id="manager-data-request-id"
              name="request_id"
              type="text"
              value={lookupId}
              onChange={(event) => setLookupId(event.target.value)}
              required
            />
            <button type="submit" className="manager-business-button" disabled={isLookingUp}>
              {isLookingUp ? "Đang kiểm tra…" : "Kiểm tra trạng thái"}
            </button>
          </div>
        </form>
        {lookupError && <Alert role="alert" tone="danger">{lookupError}</Alert>}
        {isLookingUp && <Alert role="status">Đang tải trạng thái yêu cầu…</Alert>}

        {result && (
          <article className="manager-data-request-result" aria-label="Kết quả yêu cầu dữ liệu">
            <p className="manager-business-eyebrow">{result.request_type ? requestTypeLabel(result.request_type) : "Yêu cầu dữ liệu"}</p>
            <h3>{result.request_id}</h3>
            <p><strong>Trạng thái:</strong> {requestStateLabel(result.state, result.completion_claimed)}</p>
            {result.unresolved_items !== undefined && <p><strong>Mục chưa xử lý:</strong> {result.unresolved_items}</p>}
            <p>{result.completion_claimed ? "Hệ thống xác nhận yêu cầu đã hoàn tất." : "Hệ thống chưa xác nhận yêu cầu hoàn tất."}</p>
          </article>
        )}
      </section>

      <section className="manager-business-card manager-data-request-card" aria-labelledby="manager-data-request-session-title">
        <div className="manager-business-card-heading">
          <div>
            <p className="manager-business-eyebrow">Phiên hiện tại</p>
            <h2 id="manager-data-request-session-title">Mã yêu cầu đã tạo</h2>
          </div>
          <span className="manager-business-chip">{createdRequestIds.length}</span>
        </div>
        <p className="manager-business-subtle">Mã chỉ được lưu trong phiên trình duyệt này. Hệ thống chưa có lịch sử để khôi phục mã sau khi phiên kết thúc.</p>
        {createdRequestIds.length === 0 ? (
          <EmptyState title="Chưa có mã yêu cầu nào trong phiên này." />
        ) : (
          <ul className="manager-data-request-id-list" aria-label="Mã yêu cầu đã tạo trong phiên này">
            {createdRequestIds.map((id) => (
              <li key={id}>
                <code>{id}</code>
                <button type="button" className="manager-business-button" disabled={isLookingUp} onClick={() => { setLookupId(id); void checkRequest(id); }}>
                  Kiểm tra trạng thái
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {deleteConfirmationOpen && (
        <ModalPortal><div className="manager-business-confirm-backdrop">
          <section
            className="manager-business-card manager-business-confirm-dialog"
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="manager-data-delete-title"
            aria-describedby="manager-data-delete-copy"
          >
            <h2 id="manager-data-delete-title">Xác nhận yêu cầu xóa dữ liệu</h2>
            <p id="manager-data-delete-copy">Yêu cầu này có thể dẫn đến xóa không thể khôi phục. Màn hình không có chức năng hủy yêu cầu. Hãy kiểm tra tham chiếu trước khi tiếp tục.</p>
            <div className="manager-business-confirm-actions">
              <button type="button" className="manager-business-button" disabled={isSubmitting} onClick={() => setDeleteConfirmationOpen(false)}>Quay lại</button>
              <button type="button" className="manager-business-button is-primary is-danger" disabled={isSubmitting} onClick={() => void submitRequest()}>
                {isSubmitting ? "Đang gửi…" : "Gửi yêu cầu xóa"}
              </button>
            </div>
          </section>
        </div></ModalPortal>
      )}
    </div>
  );
}
