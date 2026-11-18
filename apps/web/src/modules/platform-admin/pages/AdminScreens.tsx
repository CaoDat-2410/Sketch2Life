import React, { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { MgIcon } from "../components/MgIcon";
import {
  apiBaseUrl,
  backendApi,
  backendMessage,
  hasFirebaseAuthBridge,
} from "../../../shared/backendApi";

type HealthState = "blocked" | "loading" | "ready" | "error";
type HealthResult = { status: "ok"; service: string };

const PANEL_TITLES: Record<string, string> = {
  orgs: "Tổ chức",
  queues: "Queue & jobs",
  lifecycle: "Vòng đời dữ liệu",
  audit: "Nhật ký kiểm toán",
  catalog: "Danh mục hoạt động",
  permissions: "Quyền & vai trò",
  quota: "Quota & chính sách",
  billing: "Đối soát billing",
  feedback: "Feedback",
  inbox: "Hộp thư",
  settings: "Cài đặt",
};

function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: React.ReactNode }) {
  return (
    <div className="admin-page-heading">
      <div className="admin-page-heading-copy">
        <p className="admin-eyebrow"><span aria-hidden="true" />{eyebrow}</p>
        <div className="admin-page-heading-row"><div><h1>{title}</h1><p>{description}</p></div>{action && <div className="admin-page-actions">{action}</div>}</div>
      </div>
    </div>
  );
}

function BlockedFlow({ title, description, dependencies, permissionNote }: { title: string; description: string; dependencies: string[]; permissionNote?: string }) {
  return (
    <section className="admin-blocked-card">
      <div className="admin-blocked-heading"><span className="admin-blocked-icon" aria-hidden="true"><MgIcon name="lock" size={21} variant="standard" /></span><div><p className="admin-status-label">Chưa khả dụng</p><h2>{title}</h2></div></div>
      <p className="admin-blocked-description">{description}</p>
      {permissionNote && <p className="admin-permission-note"><MgIcon name="shield" size={16} variant="navigation" />{permissionNote}</p>}
      <div className="admin-dependency-box"><strong>Cần có API / contract</strong><ul>{dependencies.map((item) => <li key={item}>{item}</li>)}</ul></div>
    </section>
  );
}

function isLoopbackApi(): boolean {
  try {
    const hostname = new URL(apiBaseUrl()).hostname;
    return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
  } catch {
    return false;
  }
}

function OverviewUnavailableCard({ title, icon, detail }: { title: string; icon: "layers" | "doc" | "audit"; detail: string }) {
  return (
    <article className="admin-overview-card">
      <div className="admin-overview-card-heading">
        <span className="admin-overview-icon" aria-hidden="true"><MgIcon name={icon} size={21} variant="navigation" /></span>
        <h2>{title}</h2>
      </div>
      <span className="admin-overview-status is-unavailable">Chưa khả dụng</span>
      <p className="admin-overview-detail">{detail}</p>
    </article>
  );
}

function LocalHealthPanel() {
  const [state, setState] = useState<HealthState>("blocked");
  const [health, setHealth] = useState<HealthResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const canCallLocalHealth = hasFirebaseAuthBridge() && isLoopbackApi();

  useEffect(() => {
    let active = true;
    setHealth(null);
    setError(null);
    if (!hasFirebaseAuthBridge() || !isLoopbackApi()) {
      setState("blocked");
      return () => { active = false; };
    }
    setState("loading");
    backendApi.health()
      .then((result) => { if (active) { setHealth(result); setState("ready"); } })
      .catch((cause: unknown) => { if (active) { setError(backendMessage(cause)); setState("error"); } });
    return () => { active = false; };
  }, [reload]);

  const stateContent: Record<HealthState, { label: string; detail: string }> = {
    blocked: { label: "Chưa xác minh", detail: "Cần phiên Firebase và API loopback để đọc GET /health." },
    loading: { label: "Đang kiểm tra", detail: "Đang chờ phản hồi từ GET /health local." },
    ready: { label: "Đã phản hồi", detail: health ? `GET /health trả về ${health.service}.` : "API đã phản hồi." },
    error: { label: "Không đọc được", detail: error ?? "GET /health chưa trả trạng thái." },
  };

  return (
    <article className="admin-overview-card" aria-labelledby="admin-health-heading">
      <div className="admin-overview-card-heading">
        <span className="admin-overview-icon" aria-hidden="true"><MgIcon name="chart" size={21} variant="navigation" /></span>
        <h2 id="admin-health-heading">Sức khỏe hệ thống</h2>
        {canCallLocalHealth && <button type="button" className="admin-health-retry" aria-label="Kiểm tra lại health local" disabled={state === "loading"} onClick={() => setReload((value) => value + 1)}><MgIcon name="refresh" size={16} variant="navigation" /></button>}
      </div>
      <span className={`admin-overview-status is-${state}`} role={state === "error" ? "alert" : "status"}>{stateContent[state].label}</span>
      <p className="admin-overview-detail">{stateContent[state].detail}</p>
      {state === "ready" && <small className="admin-overview-footnote">Chỉ xác nhận GET /health; không đại diện trạng thái queue, billing hoặc toàn nền tảng.</small>}
    </article>
  );
}

function AdminOverview() {
  return (
    <div className="admin-page admin-overview">
      <PageHeading eyebrow="VẬN HÀNH NỀN TẢNG" title="Tổng quan hệ thống" description="Theo dõi trạng thái dịch vụ và các khối chức năng chính." />
      <section className="admin-overview-grid" aria-label="Trạng thái các dịch vụ nền tảng">
        <LocalHealthPanel />
        <OverviewUnavailableCard title="Hàng đợi công việc" icon="layers" detail="Chưa có API tổng hợp trạng thái queue và job." />
        <OverviewUnavailableCard title="Đối soát billing" icon="doc" detail="Chưa có API invoice, payment attempt và provider event." />
        <OverviewUnavailableCard title="Sự kiện vòng đời" icon="audit" detail="Chưa có API trạng thái deletion và offboarding." />
      </section>
    </div>
  );
}

const FLOWS: Record<string, { description: string; dependencies: string[]; permissionNote?: string }> = {
  orgs: {
    description: "Chưa có API liệt kê tổ chức hoặc xác minh permission scope cho Platform Admin. Không hiển thị tên/tình trạng trường giả.",
    dependencies: ["Organization directory và scoped context", "Admin role/capability discovery, revoke và audit", "Thông báo denied không tiết lộ resource ngoài quyền"],
  },
  queues: {
    description: "Chỉ có health endpoint tổng quát. API chưa có queue/job summaries hoặc reconciliation state cho platform operations.",
    dependencies: ["Queue/job status theo service và operation", "Awaiting reconciliation, provider unavailable, retry/dead-letter state", "Metadata-only lỗi; không hiển thị child media/story hoặc secrets"],
  },
  lifecycle: {
    description: "Không có feed cho deletion/offboarding backlog hoặc trạng thái pending/read-only trong adapter hiện tại.",
    dependencies: ["Lifecycle event list với resource scope và current state", "Pending/retry/retention-safe transitions và audit", "Cross-system completion proof trước khi báo hoàn tất"],
  },
  audit: {
    description: "SRS yêu cầu audit trail, nhưng chưa có API đọc audit. Trang không dựng sự kiện hoặc lỗi mẫu.",
    dependencies: ["Audit feed có actor/capability/resource/action/time", "Tenant-safe filters và phân trang", "Metadata-only errors; che token, credential, child data và media"],
  },
  catalog: {
    description: "Chưa có API cho Activity Catalog draft, immutable revision, review, publish, hide hoặc conflict. Content Admin là permission, không phải role mới.",
    dependencies: ["Catalog list/detail và immutable version reads", "Draft/revise/review/publish/hide commands có version precondition", "Content Admin capability và audit actor"],
    permissionNote: "Content Admin phải được backend cấp riêng bên trong Platform Admin; điều hướng này không cấp permission.",
  },
  permissions: {
    description: "Không có API để đọc Admin role/capability hoặc permission assignments. Không suy ra quyền từ tên route hay session preview.",
    dependencies: ["Platform Admin identity/capability discovery", "Content Admin grant/revoke và role mismatch response", "Session expiry/re-entry và audit trail"],
  },
  quota: {
    description: "Không có API tổng hợp quota, grants, usage hoặc policy revisions. Không hiển thị số dư hoặc điều chỉnh chính sách giả.",
    dependencies: ["Quota summary theo school/Teacher/Parent scope", "Policy revision read/write với audit", "Grant/top-up và callback đối soát đã xác minh"],
  },
  billing: {
    description: "Không có API platform để đối soát invoice/payment/provider events. Không báo paid từ redirect hoặc hiển thị giao dịch giả.",
    dependencies: ["Invoice/payment attempt và provider event receipt reads", "Reconciliation state và idempotent retry command", "Chỉ callback có signature hợp lệ mới cập nhật trạng thái và capacity"],
  },
  feedback: {
    description: "Chưa có API feedback thread cho platform support. SRS giữ phạm vi reply trong organization liên quan.",
    dependencies: ["Feedback thread read/reply có tenant scope", "Capability riêng và audit cho phản hồi platform", "Không đưa media trẻ vào trao đổi"],
  },
  inbox: {
    description: "Chưa có API inbox/read state. Biểu tượng chuông không gắn unread count hoặc chấm chưa đọc.",
    dependencies: ["Inbox items theo recipient/capability", "Read state, phân trang, empty/error", "Không làm lộ sự tồn tại của notification ngoài phạm vi"],
  },
  settings: {
    description: "Chưa có API cấu hình Platform Admin, provider hoặc notification. Không thêm công tắc vận hành giả.",
    dependencies: ["Versioned settings contract", "Permission, confirmation và audit cho cấu hình thay đổi", "Provider health không thay thế trạng thái reconciliation"],
  },
};

function AdminUnavailablePanel({ panel }: { panel: string }) {
  const title = PANEL_TITLES[panel] ?? "Trạng thái khả dụng";
  const flow = FLOWS[panel] ?? { description: "Luồng này chưa có API/capability contract trong frontend adapter hiện tại.", dependencies: ["Versioned API, scoped authorization và audit trail"] };
  return (
    <div className="admin-page">
      <PageHeading eyebrow="PLATFORM ADMIN / QUYỀN CÓ SCOPE" title={title} description="Màn hình giữ trạng thái phụ thuộc cho đến khi có API và capability được xác nhận." />
      <BlockedFlow title={title} description={flow.description} dependencies={flow.dependencies} permissionNote={flow.permissionNote} />
    </div>
  );
}

export function A01ContentModerationPage() {
  return (
    <div className="admin-page">
      <PageHeading eyebrow="NỘI DUNG / MODERATION" title="Duyệt học liệu" description="Mở nội dung theo đúng revision được yêu cầu trước khi ẩn hoặc cho phép hiển thị." />
      <BlockedFlow
        title="Chưa thể tải hàng đợi moderation"
        description="Có command moderation theo lesson_id và revision, nhưng thiếu API liệt kê hàng đợi và đọc exact revision/content. Không gọi command với ID hoặc revision tự tạo."
        dependencies={["Permission Platform Admin được backend xác nhận", "Moderation queue và exact immutable-version detail", "Conflict/stale revision handling và reason/audit", "Hình ảnh/media trẻ không tự động xuất hiện trong review"]}
      />
    </div>
  );
}

export function A02PlatformOperationsPage() {
  const location = useLocation();
  const panel = new URLSearchParams(location.search).get("panel");
  if (!panel) return <AdminOverview />;
  return <AdminUnavailablePanel panel={panel} />;
}
