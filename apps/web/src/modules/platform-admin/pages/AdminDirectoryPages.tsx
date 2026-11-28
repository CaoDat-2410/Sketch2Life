import { AdminSelect } from '../components/AdminSelect'
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  ArrowUpRight,
  Building2,
  Check,
  Users,
  Activity,
  ShieldCheck,
  Plus,
  MessageSquareText,
  CircleCheck,
  CirclePause,
  CircleOff,
  Pencil,
  Save,
  X,
  Database,
  Server,
  Clock3,
  RefreshCw,
  Trash2,
  TriangleAlert,
  ListFilter,
} from "lucide-react";
import { backendApi, createIdempotencyKey } from "../../../shared/api/backendApi";
import { useSessionScopedDraft, type SessionDraftAuth } from "../../../shared/hooks/useSessionScopedDraft";
import { authService } from "../../school-manager/be1/services/authService";
import { feedbackAuthorLabel } from "../../../shared/api/feedbackLabels";
import { eventLabel, events } from "../components/dashboard/adminEventLabels";
import {
  read,
  readAllPages,
  query,
  type Page,
  type Organization,
  type OrganizationSummary,
  type Operation,
  type Operations,
  type Audit,
  type AuditRetention,
  type AuditRetentionPreview,
  type Lifecycle,
  type Inbox,
  type Settings,
  type AdminSession,
  type Grant,
  type Feedback as FeedbackItem,
  type Thread,
  type Delivery,
} from "../services/adminService";
import {
  useAdminQuery,
  useAdminCommand,
  useAdminCursor,
  date,
  short,
  label,
  adminError,
} from "../components/adminHooks";
import {
  Heading,
  Button,
  Field,
  Form,
  Feedback,
  LoadBoundary,
  Table,
  Empty,
  Refresh,
  CursorPager,
  SearchForm,
  Status,
} from "../components/AdminUI";
import {
  Button as CozyButton,
  DataTable,
  EmptyState,
  Section,
  StatCard,
  StatusBadge,
  type StatAccent,
  type StatusTone,
} from "../../../shared/ui";

type ApiHealth = { status: "ok"; service: string };
async function readApiHealth(): Promise<ApiHealth> {
  try {
    const response = await fetch("/health", { cache: "no-store" });
    if (!response.ok) throw new Error("Health probe failed");
    const health = (await response.json()) as ApiHealth;
    if (health.status !== "ok") throw new Error("Health probe failed");
    return health;
  } catch {
    throw new Error("Không thể xác nhận trạng thái dịch vụ.");
  }
}

function apiServiceLabel(service?: string): string {
  if (!service) return "Dịch vụ Sketch2Life";
  if (/sketch2life/i.test(service) && /\bapi\b/i.test(service)) return "Dịch vụ Sketch2Life";
  if (/^api$/i.test(service.trim())) return "Dịch vụ nền tảng";
  return service;
}

function lowercaseTitleKeepingAcronyms(title: string): string {
  return title.replace(/\S+/gu, (word) => /^[\p{Lu}\p{N}]+$/u.test(word) ? word : word.toLocaleLowerCase("vi-VN"));
}

export { DashboardOverviewPage as OverviewPage } from "../components/dashboard/DashboardOverviewPage";

type OrganizationCreateDraft = {
  open: boolean;
  name: string;
  actionKeys: Record<string, string>;
};

const EMPTY_ORGANIZATION_CREATE_DRAFT: OrganizationCreateDraft = { open: false, name: "", actionKeys: {} };
const draftAuth: SessionDraftAuth = {
  getCurrentUser: () => authService.getCurrentUser(),
  observe: (callback) => authService.observe((user) => callback(user)),
};

export function OrganizationsPage() {
  const [params, setParams] = useSearchParams();
  const search = params.get("search") ?? "";
  const state = params.get("state") ?? "";
  const pagination = useAdminCursor(JSON.stringify([search, state]));
  const [createDraft, setCreateDraft, clearCreateDraft] = useSessionScopedDraft(
    "platform-admin:organization-create",
    EMPTY_ORGANIZATION_CREATE_DRAFT,
    draftAuth,
  );
  const { name, open: creating, actionKeys } = createDraft;
  const [editing, setEditing] = useState<Organization | null>(null);
  const [editName, setEditName] = useState("");
  const [editState, setEditState] = useState("");
  const q = useAdminQuery(
    () => read<Page<Organization>>("/organizations" + query({ search, state, cursor: pagination.cursor, limit: 25 })),
    JSON.stringify([search, state, pagination.cursor]),
  );
  const stats = useAdminQuery(
    () => read<OrganizationSummary>("/organizations/summary"),
    "organization-statistics",
  );
  const cmd = useAdminCommand();
  const editCmd = useAdminCommand();
  const reload = () => { q.reload(); stats.reload(); };
  const clearFilter = () => { setParams({ panel: "orgs" }); };
  return (
    <div className="pa-page pa-organizations">
      <Heading title="Trường học">
        <Button primary disabled={creating} onClick={() => setCreateDraft((current) => ({ ...current, open: true }))}>
          <Plus size={18} aria-hidden="true" />Thêm trường học
        </Button>
        <Refresh onClick={reload} disabled={q.loading || stats.loading} />
      </Heading>
      <Feedback {...cmd} />
      {creating && (
        <section className="pa-panel pa-padded pa-organization-create" aria-label="Thêm trường học">
          <div className="pa-org-create-heading">
            <span><Building2 size={21} aria-hidden="true" /></span>
            <div><h2>Thêm trường học</h2></div>
          </div>
          <Form onSubmit={() => {
            if (cmd.busy || !name.trim()) return;
            const submittedName = name.trim();
            const idempotencyKey = actionKeys[submittedName] ?? createIdempotencyKey();
            if (!actionKeys[submittedName]) {
              setCreateDraft((current) => ({ ...current, actionKeys: { ...current.actionKeys, [submittedName]: idempotencyKey } }));
            }
            void cmd.run(
              () => cmd.send("/organizations", { display_name: submittedName }, undefined, "POST", idempotencyKey),
              () => { clearCreateDraft(); pagination.reset(); reload(); },
            );
          }}>
            <Field label="Tên trường học">
              <input autoFocus required maxLength={200} value={name}
                placeholder="Ví dụ: Trường Mầm non Hoa Mai" disabled={cmd.busy}
                onChange={(e) => setCreateDraft((current) => ({ ...current, name: e.target.value }))} />
            </Field>
            <div className="pa-actions">
              <Button primary type="submit" disabled={cmd.busy || !name.trim()}>
                {cmd.busy ? "Đang tạo…" : "Tạo trường học"}
              </Button>
              <Button disabled={cmd.busy} onClick={clearCreateDraft}>Hủy</Button>
            </div>
          </Form>
        </section>
      )}
      {editing && (
        <section className="pa-panel pa-padded pa-organization-edit" aria-labelledby="pa-org-edit-title">
          <div className="pa-org-create-heading">
            <span><Pencil size={19} aria-hidden="true" /></span>
            <div><h2 id="pa-org-edit-title">Chỉnh sửa trường học</h2><p>{editing.display_name}</p></div>
          </div>
          <Feedback {...editCmd} />
          <Form onSubmit={() => {
            if (editCmd.busy || !editName.trim()) return;
            const payload = { display_name: editName.trim(), ...(editState ? { state: editState } : {}) };
            void editCmd.run(
              () => editCmd.send(
                "/organizations/" + encodeURIComponent(editing.organization_id),
                payload,
                editing.revision,
                "PATCH",
              ),
              () => { setEditing(null); setEditName(""); setEditState(""); pagination.reset(); reload(); },
            );
          }}>
            <Field label="Tên trường học">
              <input autoFocus required maxLength={200} value={editName} disabled={editCmd.busy}
                onChange={(event) => setEditName(event.target.value)} />
            </Field>
            <Field label="Trạng thái">
              <AdminSelect value={editState} disabled={editCmd.busy} onChange={(event) => setEditState(event.target.value)}>
                <option value="">Giữ nguyên trạng thái hiện tại</option>
                <option value="active">Đang hoạt động</option>
                <option value="paused">Tạm dừng</option>
                <option value="disabled">Ngừng hoạt động</option>
              </AdminSelect>
            </Field>
            <div className="pa-actions">
              <Button primary type="submit" disabled={editCmd.busy || !editName.trim()}>
                <Save size={16} aria-hidden="true" />{editCmd.busy ? "Đang lưu…" : "Lưu thay đổi"}
              </Button>
              <Button disabled={editCmd.busy} onClick={() => { setEditing(null); setEditName(""); setEditState(""); }}>
                <X size={16} aria-hidden="true" />Hủy
              </Button>
            </div>
          </Form>
          <p className="pa-org-edit-note">Thay đổi trạng thái không tự động thay đổi lớp học hoặc tài khoản trong trường.</p>
        </section>
      )}
      <section className="pa-org-search-panel" aria-label="Tìm trường học">
        <SearchForm key={search} initialValue={search} placeholder="Tìm tên trường học, mã trường..."
          onSearch={(value) => { setParams({ panel: "orgs", ...(value ? { search: value } : {}), ...(state ? { state } : {}) }); }}
          controls={
          <div className="pa-org-state-filter">
            <AdminSelect id="school-state-filter" aria-label="Lọc theo trạng thái trường học" value={state}
              onChange={(event) => {
                const value = event.target.value;
                setParams({ panel: "orgs", ...(search ? { search } : {}), ...(value ? { state: value } : {}) });
              }}>
              <option value="">Tất cả trạng thái</option>
              <option value="active">Đang hoạt động</option>
              <option value="paused">Tạm dừng</option>
              <option value="disabled">Ngừng hoạt động</option>
            </AdminSelect>
          </div>
          } />
        {(search || state) && <div className="pa-org-active-filter">
          <span>
            Đang lọc {search && <>theo <strong>“{search}”</strong></>}
            {search && state && " · "}
            {state && <strong>{state === "active" ? "Đang hoạt động" : state === "paused" ? "Tạm dừng" : "Ngừng hoạt động"}</strong>}
          </span>
          <Button onClick={clearFilter}>Xóa bộ lọc</Button>
        </div>}
      </section>
      <section className="pa-org-stats" aria-label="Thống kê trường học" aria-live="polite">
        {([
          { key: "total", label: "Tổng số trường học", icon: Building2 },
          { key: "active", label: "Đang hoạt động", icon: CircleCheck },
          { key: "paused", label: "Tạm dừng", icon: CirclePause },
          { key: "disabled", label: "Ngừng hoạt động", icon: CircleOff },
        ] as const).map(({ key, label: title, icon: Icon }) => <div className={"pa-org-stat is-" + key} key={key}>
          <span className="pa-org-stat-icon" aria-hidden="true"><Icon size={20} /></span>
          <span className="pa-org-stat-label">{title}</span>
          <strong>{typeof stats.data?.[key] === "number" ? stats.data[key].toLocaleString("vi-VN") : "—"}</strong>
        </div>)}
        {stats.error && <p className="pa-org-stats-error">Chưa tải được thống kê. <button type="button" onClick={stats.reload}>Thử lại</button></p>}
        {!!stats.data?.other && <p className="pa-org-stats-note">{stats.data.other.toLocaleString("vi-VN")} trường đang ở trạng thái hệ thống khác.</p>}
      </section>
      <LoadBoundary {...q}>
        <section className="pa-panel pa-org-directory" aria-label="Danh sách trường học">
          <div className="pa-org-list-heading">
            <div className="pa-org-list-title">
              <span><Building2 size={21} aria-hidden="true" /></span>
              <div><h2>Danh sách trường học</h2></div>
            </div>
            <span className="pa-org-result-count">{q.data?.total ?? 0} kết quả</span>
          </div>
          {q.data?.items.length ? <Table className="pa-organizations-table-scroll" items={q.data.items} rowKey={(row) => row.organization_id}
            columns={[
              { title: "Trường học", render: (row) => <div className="pa-person">
                <span className="pa-avatar" aria-hidden="true">{row.display_name.replace(/^\[TEST\]\s*/, "").split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]).join("").toUpperCase()}</span>
                <strong>{row.display_name}</strong>
              </div> },
              { title: "Mã trường", render: (row) => <code className="pa-org-code" title={row.organization_id}
                tabIndex={0} aria-label={"Mã trường: " + row.organization_id}>{short(row.organization_id)}</code> },
              { title: "Trạng thái", render: (row) => <span className={"pa-status pa-status-" + row.state.toLowerCase()}>
                {row.state.toLowerCase() === "active" ? "Hoạt động"
                  : ["paused", "suspended"].includes(row.state.toLowerCase()) ? "Tạm dừng"
                  : ["disabled", "inactive"].includes(row.state.toLowerCase()) ? "Ngừng hoạt động" : label(row.state)}
              </span> },
              { title: "Thao tác", render: (row) => <div className="pa-organization-actions">
                <button type="button" className="pa-org-edit-button" onClick={() => {
                  setEditing(row); setEditName(row.display_name); setEditState(""); editCmd.clear();
                }} aria-label={"Chỉnh sửa " + row.display_name}>
                  <Pencil size={15} aria-hidden="true" />Sửa thông tin
                </button>
                <Link className="pa-org-feedback-link" to={"?panel=feedback&org=" + row.organization_id}>
                  <MessageSquareText size={17} aria-hidden="true" />Phản hồi<ArrowUpRight size={15} aria-hidden="true" />
                </Link>
              </div> },
            ]} /> : <Empty text={search || state ? "Không tìm thấy trường phù hợp" : "Chưa có trường học"}
              detail={search || state ? "Thử từ khóa, trạng thái khác hoặc xóa bộ lọc để xem toàn bộ danh sách." : "Thêm trường học đầu tiên để bắt đầu quản lý."}
              action={<Button onClick={() => { if (search || state) clearFilter(); else setCreateDraft((current) => ({ ...current, open: true })); }}>{search || state ? "Xóa bộ lọc" : "Thêm trường học"}</Button>} />}
          <CursorPager page={pagination.page} count={q.data?.items.length ?? 0} total={q.data?.total}
            nextCursor={q.data?.next_cursor} onNext={pagination.next} onPrevious={pagination.back} disabled={q.loading} />
        </section>
      </LoadBoundary>
    </div>
  );
}
function healthTone(value: string): StatusTone {
  switch (value) {
    case "healthy": return "success";
    case "unavailable":
    case "error": return "danger";
    case "not_configured":
    case "idle": return "warn";
    case "loading": return "info";
    default: return "neutral";
  }
}

function healthAccent(value: string): StatAccent {
  switch (healthTone(value)) {
    case "success": return "mint";
    case "warn": return "butter";
    case "danger": return "coral";
    case "info": return "sky";
    case "neutral": return "neutral";
  }
}

function operationTone(value: string): StatusTone {
  switch (value.toLowerCase()) {
    case "healthy":
    case "active":
    case "approved":
    case "completed":
    case "sent":
    case "published":
    case "paid": return "success";
    case "failed":
    case "exception":
    case "unavailable":
    case "error":
    case "rejected":
    case "disabled": return "danger";
    case "queued":
    case "pending":
    case "requested":
    case "not_configured":
    case "idle": return "warn";
    case "running":
    case "sending":
    case "received": return "info";
    default: return "neutral";
  }
}

export function OperationsPage() {
  const q = useAdminQuery(() => read<Operations>("/operations"), "operations");
  const apiHealth = useAdminQuery(readApiHealth, "platform-api-health");
  const refresh = () => {
    q.reload();
    apiHealth.reload();
  };
  const apiState = apiHealth.loading
    ? "loading"
    : apiHealth.error || !apiHealth.data
      ? "error"
      : "healthy";
  const broker = q.data?.broker;
  const workerStatus = broker?.status === "not_configured"
    ? "not_configured"
    : broker?.status === "unavailable"
      ? "unavailable"
      : broker?.active_workers
        ? "healthy"
        : q.loading
          ? "loading"
          : "idle";
  const healthCards = [
    {
      title: "Dịch vụ nền tảng",
      status: apiState,
      detail: apiHealth.loading ? "Đang kiểm tra phản hồi" : apiHealth.error || "Dịch vụ phản hồi bình thường",
      value: apiServiceLabel(apiHealth.data?.service),
      icon: Activity,
    },
    {
      title: "Cơ sở dữ liệu",
      status: q.data?.database?.status ?? (q.loading ? "loading" : "unavailable"),
      detail: q.data?.database?.response_ms == null ? "Chưa có số đo mới" : `Phản hồi ${q.data.database.response_ms} ms`,
      value: q.data?.database?.status === "healthy" ? "Kết nối ổn định" : "Chưa xác nhận",
      icon: Database,
    },
    {
      title: "Bộ nhớ đệm / hàng đợi",
      status: broker?.status ?? (q.loading ? "loading" : "unavailable"),
      detail: broker?.status === "not_configured" ? "Chưa cấu hình kết nối" : broker?.response_ms == null ? "Chưa có số đo mới" : `Phản hồi ${broker.response_ms} ms`,
      value: broker?.status === "healthy" ? `${broker.queue_count ?? 0} hàng đợi · ${broker.transport_pending_count ?? 0} tác vụ chờ` : "Chưa xác nhận",
      icon: Server,
    },
    {
      title: "Tiến trình xử lý đang hoạt động",
      status: workerStatus,
      detail: broker?.active_workers == null ? "Số tiến trình xử lý chưa khả dụng" : `${broker.active_workers} tiến trình xử lý có tín hiệu hoạt động còn hạn`,
      value: broker?.active_workers == null ? "—" : String(broker.active_workers),
      icon: Users,
    },
  ] as const;
  const healthLabel = (value: string) => ({
    healthy: "Đang hoạt động",
    loading: "Đang kiểm tra",
    error: "Không thể xác nhận",
    unavailable: "Không khả dụng",
    not_configured: "Chưa cấu hình",
    idle: "Chưa có tiến trình xử lý",
  })[value as "healthy" | "loading" | "error" | "unavailable" | "not_configured" | "idle"] ?? "Chưa rõ trạng thái";
  // typeLabel is shown in the "Loại" column when a row carries no job type of its own.
  const tables: Array<{ title: string; typeLabel: string; rows: Operation[] }> = q.data ? [
    { title: "Công việc AI", typeLabel: "Công việc AI", rows: q.data.jobs },
    { title: "Sự kiện chờ xử lý", typeLabel: "Hàng đợi sự kiện", rows: q.data.core_outbox },
    { title: "Gửi email", typeLabel: "Email hệ thống", rows: q.data.email },
    { title: "Vòng đời dữ liệu", typeLabel: "Vòng đời dữ liệu", rows: q.data.lifecycle },
  ] : [];

  return (
    <div className="s2l-ops-page box-border -mx-[clamp(22px,4vw,58px)] -mt-[33px] -mb-[64px] flex min-h-screen min-w-0 flex-col gap-5 bg-cream px-[clamp(22px,4vw,58px)] pt-[33px] pb-[64px] font-ui text-ink max-[1120px]:-mx-[25px] max-[1120px]:px-[25px] max-[820px]:-mt-[26px] max-[620px]:-mx-[15px] max-[620px]:-mt-[22px] max-[620px]:-mb-[42px] max-[620px]:px-[15px] max-[620px]:pt-[22px] max-[620px]:pb-[42px]">
      <Heading title="Giám sát vận hành">
        <CozyButton className="max-[620px]:w-full" onClick={refresh} disabled={q.loading || apiHealth.loading} iconLeft={<RefreshCw size={16} aria-hidden="true" />}>Tải lại</CozyButton>
      </Heading>
      <Section title="Tình trạng hệ thống" variant="plain">
        <div aria-live="polite" className="pa-ops-grid grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {healthCards.map(({ title, status, detail, value, icon: Icon }) => (
            <StatCard
              key={title}
              label={title}
              value={value}
              helperText={detail}
              icon={<Icon size={19} aria-hidden="true" />}
              accent={healthAccent(status)}
              badge={<StatusBadge tone={healthTone(status)} dot size="sm">{healthLabel(status)}</StatusBadge>}
            />
          ))}
        </div>
      </Section>
      <LoadBoundary {...q}>
        {q.data?.queue && <div aria-label="Tóm tắt hàng đợi" className="pa-ops-grid grid min-w-0 grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Tác vụ đang chờ"
            value={q.data.queue.queued_jobs.toLocaleString("vi-VN")}
            icon={<Clock3 size={19} aria-hidden="true" />}
            accent="primary"
            helperText={q.data.queue.oldest_queued_at ? `Cũ nhất từ ${date(q.data.queue.oldest_queued_at)}` : "Không có tác vụ đang chờ"}
          />
          <StatCard
            label="Đang xử lý"
            value={q.data.queue.running_jobs.toLocaleString("vi-VN")}
            icon={<Activity size={19} aria-hidden="true" />}
            accent="mint"
          />
          <StatCard
            label="Cần chú ý"
            value={q.data.queue.failed_jobs.toLocaleString("vi-VN")}
            icon={<TriangleAlert size={19} aria-hidden="true" />}
            accent={q.data.queue.failed_jobs > 0 ? "coral" : "mint"}
            helperText="Thất bại có thể thử lại, thất bại cuối hoặc bị chặn"
          />
          <StatCard
            label="Tác vụ trên bộ nhớ đệm"
            value={q.data.broker?.transport_pending_count?.toLocaleString("vi-VN") ?? "—"}
            icon={<Server size={19} aria-hidden="true" />}
            accent="butter"
            helperText={q.data.queue.last_dispatched_at ? `Gửi gần nhất ${date(q.data.queue.last_dispatched_at)}` : "Chưa ghi nhận lần gửi gần đây"}
          />
        </div>}
        {q.data && <div className="grid min-w-0 grid-cols-1 items-stretch gap-4 xl:grid-cols-2">
          {tables.map(({ title, typeLabel, rows }) => (
            <Section title={title} key={title}>
              <DataTable
                caption={title}
                rows={rows}
                getRowKey={(row) => row.state + (row.job_type ?? "")}
                density="dense"
                columns={[
                  {
                    key: "state",
                    header: "Trạng thái",
                    render: (row) => <StatusBadge tone={operationTone(row.state)} size="sm">{label(row.state)}</StatusBadge>,
                  },
                  { key: "type", header: "Loại", render: (row) => row.job_type ?? typeLabel },
                  { key: "count", header: "Số lượng", numeric: true, render: (row) => row.count },
                ]}
                emptyState={<EmptyState title={`Chưa có bản ghi ${lowercaseTitleKeepingAcronyms(title)}`} />}
              />
            </Section>
          ))}
        </div>}
      </LoadBoundary>
    </div>
  );
}
export function LifecyclePage() {
  const [state, setState] = useState("");
  const pagination = useAdminCursor(state);
  const q = useAdminQuery(
    () =>
      read<Page<Lifecycle>>("/lifecycle" + query({ state, cursor: pagination.cursor, limit: 25 })),
    JSON.stringify([state, pagination.cursor]),
  );
  return (
    <div className="pa-page">
      <Heading
        title="Vòng đời dữ liệu"
      >
        <Refresh onClick={q.reload} />
      </Heading>
      <Field label="Trạng thái xử lý dữ liệu">
        <AdminSelect value={state} onChange={(event) => setState(event.target.value)}>
          <option value="">Tất cả trạng thái</option>
          {["requested", "running", "awaiting_external_purge", "completed", "exception"].map((value) => <option key={value} value={value}>{label(value)}</option>)}
        </AdminSelect>
      </Field>
      <LoadBoundary {...q}>
        <section className="pa-panel">
          <Table
            items={q.data?.items ?? []}
            rowKey={(r) => r.request_id}
            emptyText="Chưa có yêu cầu xử lý dữ liệu"
            columns={[
              {
                title: "Yêu cầu",
                render: (r) => (
                  <>
                    <Status value={r.request_type} />
                    <small>{short(r.request_id)}</small>
                  </>
                ),
              },
              {
                title: "Trạng thái",
                render: (r) => <Status value={r.state} />,
              },
              { title: "Còn chờ", render: (r) => r.unresolved_items },
              { title: "Ngày tạo", render: (r) => date(r.created_at) },
              { title: "Hoàn tất", render: (r) => date(r.completed_at) },
            ]}
          />
          <CursorPager
            page={pagination.page}
            total={q.data?.total}
            count={q.data?.items.length ?? 0}
            nextCursor={q.data?.next_cursor}
            onNext={pagination.next}
            onPrevious={pagination.back}
          />
        </section>
      </LoadBoundary>
    </div>
  );
}
const resourceTypeLabels: Record<string, string> = {
  lesson_feedback: "Phản hồi học liệu",
  adult_account: "Tài khoản nhân sự",
  adult_assignment: "Phân công nhân sự",
  platform_lesson: "Học liệu nền tảng",
  story_run: "Lượt kể chuyện",
  lesson_occurrence: "Buổi dạy",
  child_profile: "Hồ sơ trẻ",
  lesson_presentation_revision: "Phiên bản trình chiếu",
  consent: "Xác nhận phụ huynh",
  organization: "Trường học",
  parent_group: "Nhóm phụ huynh",
  parent_group_membership: "Thành viên nhóm phụ huynh",
  teacher_assignment_transfer: "Chuyển giao phân công giáo viên",
  lesson: "Bài học",
  lesson_access_grant: "Quyền truy cập bài học",
  lesson_source_document: "Tài liệu nguồn bài học",
  lesson_document_revision: "Phiên bản tài liệu buổi dạy",
  lesson_plan_revision: "Phiên bản kế hoạch buổi dạy",
  lesson_presentation: "Bài trình chiếu",
  lesson_presentation_svg_draft: "Bản nháp SVG cho bài trình chiếu",
  class: "Lớp học",
  data_request: "Yêu cầu dữ liệu",
  audit_policy: "Chính sách lưu kiểm toán",
  catalog: "Danh mục hoạt động",
  organization_subscription: "Gói dịch vụ tổ chức",
  quota_invoice: "Hóa đơn hạn mức",
  gallery: "Bộ sưu tập",
  observation: "Ghi nhận học tập",
  artifact: "Tệp nội dung",
  canvas: "Bảng vẽ",
  canvas_checkpoint: "Bản chụp bảng vẽ",
  session: "Buổi học",
  device_grant: "Quyền truy cập thiết bị",
  synthetic_eligibility_proof: "Bằng chứng đủ điều kiện thử nghiệm",
  group: "Nhóm học",
  membership: "Thành viên nhóm",
  child_turn: "Lượt hoạt động của trẻ",
  profile_share_grant: "Quyền chia sẻ hồ sơ",
  upload_session: "Phiên tải tệp lên",
  core_resource: "Tài nguyên hệ thống",
};
const resourceTypeLabel = (value: string) =>
  resourceTypeLabels[value.toLowerCase().replaceAll(" ", "_")] ?? "Tài nguyên khác";
export function AuditPage() {
  const [action, setAction] = useState("");
  const [draftDays, setDraftDays] = useState<{ revision: number; value: number | null } | null>(null);
  const [preview, setPreview] = useState<AuditRetentionPreview | null>(null);
  const [previewError, setPreviewError] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [purgeConfirmed, setPurgeConfirmed] = useState(false);
  const pagination = useAdminCursor(action);
  const q = useAdminQuery(
    () => read<Page<Audit>>("/audit" + query({ action, cursor: pagination.cursor, limit: 25 })),
    JSON.stringify([action, pagination.cursor]),
  );
  const retention = useAdminQuery(() => read<AuditRetention>("/audit/retention"), "audit-retention");
  const retentionCommand = useAdminCommand();
  const draftRetentionDays = draftDays && retention.data && draftDays.revision === retention.data.revision
    ? draftDays.value
    : retention.data?.retention_days ?? null;
  const invalidRetentionDays = typeof draftRetentionDays === "number"
    && (!Number.isInteger(draftRetentionDays) || draftRetentionDays < 1 || draftRetentionDays > 36500);
  const saveRetention = () => {
    if (!retention.data || retentionCommand.busy) return;
    const retentionDays = draftRetentionDays;
    void retentionCommand.run(
      () => retentionCommand.send("/audit/retention", { retention_days: retentionDays }, retention.data!.revision, "PUT"),
      () => { setDraftDays(null); setPreview(null); setPurgeConfirmed(false); retention.reload(); },
    );
  };
  const loadPreview = async () => {
    if (previewLoading) return;
    setPreviewLoading(true);
    setPreviewError("");
    setPreview(null);
    setPurgeConfirmed(false);
    try {
      setPreview(await read<AuditRetentionPreview>("/audit/retention/preview"));
    } catch (cause) {
      setPreviewError(adminError(cause));
    } finally {
      setPreviewLoading(false);
    }
  };
  const purgeBatch = () => {
    if (!preview?.cutoff || !preview.batch_count || !purgeConfirmed || retentionCommand.busy) return;
    void retentionCommand.run(
      () => retentionCommand.send(
        "/audit/retention/purge",
        { cutoff: preview.cutoff, expected_count: preview.batch_count },
        preview.policy_revision,
      ),
      () => { setPreview(null); setPurgeConfirmed(false); retention.reload(); q.reload(); },
    );
  };
  return (
    <div className="pa-page pa-audit-page">
      <Heading
        title="Nhật ký kiểm toán"
      >
        <Refresh onClick={() => { q.reload(); retention.reload(); }} />
      </Heading>
      <section className="pa-panel pa-audit-log">
        <div className="pa-audit-log-toolbar">
          <div className="pa-audit-log-title">
            <span className="pa-audit-log-icon"><ListFilter size={18} aria-hidden="true" /></span>
            <div><h2>Lịch sử thao tác</h2></div>
          </div>
          <Field label="Lọc theo thao tác">
            <AdminSelect value={action} onChange={(e) => setAction(e.target.value)}>
              <option value="">Tất cả thao tác</option>
              {Object.entries(events).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
            </AdminSelect>
          </Field>
          {q.data && <div className="pa-audit-result-count"><strong>{(q.data.total ?? q.data.items.length).toLocaleString("vi-VN")}</strong><span>sự kiện</span></div>}
        </div>
        <LoadBoundary {...q}>
          <Table
            items={q.data?.items ?? []}
            rowKey={(r) => r.audit_id}
            emptyText="Chưa có sự kiện kiểm toán"
            emptyDetail="Các thay đổi và quyết định quản trị sẽ được ghi lại tại đây."
            columns={[
              {
                title: "Thao tác",
                render: (r) => <span className="pa-audit-event"><span className="pa-audit-event-mark" aria-hidden="true" /><strong>{eventLabel(r.action)}</strong></span>,
              },
              {
                title: "Phạm vi",
                render: (r) => <span className="pa-audit-scope-cell">
                  <span className={"pa-audit-scope-tag" + (r.organization_id === "platform" ? " is-platform" : "")}>
                    {r.organization_id === "platform" ? <ShieldCheck size={14} aria-hidden="true" /> : <Building2 size={14} aria-hidden="true" />}
                    {r.organization_id === "platform" ? "Nền tảng" : "Tổ chức"}
                  </span>
                  {r.organization_id !== "platform" && <code title={r.organization_id}>{short(r.organization_id)}</code>}
                </span>,
              },
              {
                title: "Tài nguyên",
                render: (r) => <span className="pa-audit-resource-cell" title={r.resource_id}>
                  <strong>{resourceTypeLabel(r.resource_type)}</strong>
                  {r.resource_id && <small>{short(r.resource_id)}</small>}
                </span>,
              },
              {
                title: "Người thực hiện",
                render: (r) => r.actor_ref ? <span className="pa-audit-actor"><Users size={14} aria-hidden="true" /><code title={r.actor_ref}>{short(r.actor_ref)}</code></span> : <span className="pa-audit-unknown">—</span>,
              },
              { title: "Thời gian", render: (r) => <time className="pa-audit-time" dateTime={r.created_at}><Clock3 size={14} aria-hidden="true" />{date(r.created_at)}</time> },
            ]}
          />
          <CursorPager
            page={pagination.page}
            total={q.data?.total}
            count={q.data?.items.length ?? 0}
            nextCursor={q.data?.next_cursor}
            onNext={pagination.next}
            onPrevious={pagination.back}
          />
        </LoadBoundary>
      </section>
      <details className="pa-panel pa-audit-retention">
        <summary>Chính sách lưu nhật ký{retention.data && (retention.data.retention_days == null ? " · Vô thời hạn" : " · " + retention.data.retention_days + " ngày")}</summary>
        <div className="pa-audit-retention-heading">
          <span className="pa-audit-retention-icon"><ShieldCheck size={19} aria-hidden="true" /></span>
          <div><h2 id="pa-audit-retention-title">Chính sách lưu nhật ký</h2>
            {retention.data && <p>{retention.data.retention_days == null
              ? "Chưa đặt hạn: giữ vô thời hạn, không tự động xóa."
              : `Giữ ${retention.data.retention_days} ngày; chỉ dọn khi được xác nhận thủ công.`}</p>}</div>
          <div className="pa-audit-heading-meta">
            {retention.data && <span className={"pa-audit-policy-state" + (retention.data.retention_days == null ? " is-indefinite" : " is-limited")}>
              {retention.data.retention_days == null ? "Giữ vô thời hạn" : `Giữ ${retention.data.retention_days} ngày`}
            </span>}
            <span className="pa-audit-revision">Phiên bản {retention.data?.revision ?? "—"}</span>
          </div>
        </div>
        <div className="pa-audit-retention-body">
          {retention.loading ? <p className="pa-audit-retention-state" role="status">Đang tải chính sách lưu nhật ký…</p>
            : retention.error ? <div className="pa-audit-retention-state is-error" role="alert">{retention.error}
              <Button onClick={retention.reload}>Tải lại chính sách</Button></div>
              : <>
                <div className="pa-audit-policy-fields">
                  <Field label="Thời hạn lưu (ngày)">
                    <input type="number" min={1} max={36500} inputMode="numeric"
                      value={draftRetentionDays == null ? "" : draftRetentionDays} placeholder="Không giới hạn"
                      aria-invalid={invalidRetentionDays}
                      disabled={retentionCommand.busy}
                      step={1}
                      onChange={(event) => retention.data && setDraftDays({
                        revision: retention.data.revision,
                        value: event.target.value ? Number(event.target.value) : null,
                      })} />
                  </Field>
                  {invalidRetentionDays && <p role="alert">Nhập số nguyên từ 1 đến 36.500 ngày.</p>}
                  <Button primary onClick={saveRetention}
                    disabled={!retention.data || retentionCommand.busy || invalidRetentionDays || draftRetentionDays === retention.data?.retention_days}>
                    <Save size={16} aria-hidden="true" />{retentionCommand.busy ? "Đang lưu…" : "Lưu chính sách"}
                  </Button>
                </div>
                <div className="pa-audit-retention-facts" aria-live="polite" aria-label="Tổng quan lưu trữ nhật ký">
                  <div><span>Tổng nhật ký</span><strong>{retention.data?.total_entries?.toLocaleString("vi-VN") ?? "—"}</strong></div>
                  <div><span>Đến hạn theo chính sách</span><strong>{retention.data?.eligible_count?.toLocaleString("vi-VN") ?? "—"}</strong></div>
                  <div><span>Bản ghi lâu đời nhất</span><strong>{date(retention.data?.oldest_entry_at)}</strong></div>
                  <div><span>Lần dọn gần nhất</span><strong>{retention.data?.last_purged_at ? `${date(retention.data.last_purged_at)} · ${retention.data.last_purged_count} bản ghi` : "Chưa từng dọn"}</strong></div>
                </div>
                <div className="pa-audit-retention-actions">
                  <Button primary onClick={() => void loadPreview()} disabled={previewLoading || retentionCommand.busy}>
                    <Clock3 size={16} aria-hidden="true" />{previewLoading ? "Đang xem trước…" : "Xem trước bản ghi đến hạn"}
                  </Button>
                  <span>Chỉ dọn sau khi xem trước và xác nhận riêng.</span>
                </div>
                <Feedback {...retentionCommand} />
                {previewError && <p className="pa-audit-preview-error" role="alert">{previewError}</p>}
                {preview && <div className="pa-audit-preview" aria-live="polite">
                  <div className="pa-audit-preview-copy">
                    <strong>{preview.candidate_count ? `${preview.candidate_count.toLocaleString("vi-VN")} bản ghi đã quá hạn` : "Chưa có nhật ký đến hạn"}</strong>
                    <span>{preview.cutoff ? `Mốc chính sách: trước ${date(preview.cutoff)}.` : "Chính sách hiện giữ nhật ký vô thời hạn."}
                      {preview.batch_count > 0 ? ` Lô tiếp theo tối đa ${preview.batch_count} bản ghi cũ nhất.` : " Không có gì cần dọn."}</span>
                    {preview.candidate_count > preview.batch_limit && <small>Còn nhiều hơn một lô; các lô tiếp theo cần xem trước riêng.</small>}
                  </div>
                  {preview.batch_count > 0 && <div className="pa-audit-purge-confirm">
                    <label><input type="checkbox" checked={purgeConfirmed} onChange={(event) => setPurgeConfirmed(event.target.checked)} />
                      Tôi xác nhận dọn lô gồm tối đa {preview.batch_count} nhật ký đã quá hạn.</label>
                    <Button onClick={purgeBatch} disabled={!purgeConfirmed || retentionCommand.busy}>
                      <Trash2 size={16} aria-hidden="true" />{retentionCommand.busy ? "Đang dọn…" : `Dọn ${preview.batch_count} bản ghi`}
                    </Button>
                  </div>}
                </div>}
                {retention.data && <p className="pa-audit-policy-footnote"><TriangleAlert size={15} aria-hidden="true" />
                  Đổi thời hạn chỉ áp dụng cho các lần dọn thủ công tiếp theo; nhật ký cũ không bị xóa khi lưu chính sách.</p>}
              </>}
        </div>
      </details>
    </div>
  );
}
export function PermissionsPage({ initialAccount }: { initialAccount?: string } = {}) {
  const [account, setAccount] = useState(initialAccount ?? ""),
    [search, setSearch] = useState(""),
    [reason, setReason] = useState("");
  const q = useAdminQuery(
    () =>
      Promise.all([
        backendApi.listAllPlatformAccounts({
          role: "platform_admin",
          state: "active",
          search,
        }),
        read<AdminSession>("/session"),
      ]),
    search,
  );
  const permissions = useAdminQuery(
    () =>
      account
        ? read<{ items: Grant[] }>("/accounts/" + account + "/permissions")
        : Promise.resolve({ items: [] as Grant[] }),
    account,
  );
  const cmd = useAdminCommand(),
    grant = permissions.data?.items.find(
      (g) => g.permission === "content_admin",
    );
  return (
    <div className="pa-page">
      <Heading
        title="Quyền duyệt nội dung"
      />
      <Feedback {...cmd} />
      <SearchForm placeholder="Tìm quản trị viên" onSearch={(value) => { setSearch(value); setAccount(""); setReason(""); }} />
      <LoadBoundary {...q}>
        {q.data?.[0].items.length === 0 ? (
          <Empty text="Không tìm thấy quản trị viên" detail="Thử tìm theo email hoặc tên khác để cấp quyền duyệt nội dung." action={search ? <Button onClick={() => { setSearch(""); setAccount(""); }}>Xóa bộ lọc</Button> : undefined} />
        ) : (
        <section className="pa-panel pa-padded">
          <Form
            onSubmit={() =>
              cmd.run(
                () =>
                  cmd.send(
                    "/accounts/" + account + "/permissions/content-admin",
                    {
                      active: !grant?.active,
                      expected_revision: grant?.revision ?? 0,
                      reason: reason.trim(),
                    },
                    undefined,
                    "PUT",
                  ),
                () => {
                  setReason("");
                  permissions.reload();
                  q.reload();
                },
              )
            }
          >
            <Field label="Quản trị viên">
              <AdminSelect
                required
                value={account}
                onChange={(e) => setAccount(e.target.value)}
              >
                <option value="">Chọn tài khoản</option>
                {q.data?.[0].items.map((a) => (
                  <option key={a.account_id} value={a.account_id}>
                    {a.display_name ?? a.email ?? short(a.account_id)}
                    {a.account_id === q.data?.[1].account_id ? " (Bạn)" : ""}
                  </option>
                ))}
              </AdminSelect>
            </Field>
            {account && (
              <LoadBoundary {...permissions}>
                <p>
                  Quyền duyệt nội dung:{" "}
                  <Status value={grant?.effective ? "active" : "disabled"} />
                </p>
                <Field label="Lý do thay đổi">
                  <textarea
                    required
                    maxLength={500}
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </Field>
                <Button
                  primary
                  type="submit"
                  disabled={
                    cmd.busy ||
                    !reason.trim() ||
                    account === q.data?.[1].account_id
                  }
                >
                  {grant?.active ? "Thu hồi quyền" : "Cấp quyền duyệt"}
                </Button>
                {account === q.data?.[1].account_id && (
                  <p className="pa-muted">
                    Bạn không thể tự cấp hoặc thu hồi quyền của mình.
                  </p>
                )}
              </LoadBoundary>
            )}
          </Form>
        </section>
        )}
      </LoadBoundary>
    </div>
  );
}
export function InboxPage() {
  const pagination = useAdminCursor("inbox");
  const q = useAdminQuery(
    () => read<Page<Inbox>>("/inbox" + query({ cursor: pagination.cursor, limit: 25 })),
    JSON.stringify(["inbox", pagination.cursor]),
  );
  const cmd = useAdminCommand();
  return (
    <div className="pa-page">
      <Heading
        title="Hộp thư"
        description={q.data ? `${q.data.unread_count} chưa đọc` : undefined}
      >
        <Refresh onClick={q.reload} />
      </Heading>
      <Feedback {...cmd} />
      <LoadBoundary {...q}>
        <section className="pa-panel">
          {q.data?.items.length ? (
            q.data.items.map((n) => (
              <article key={n.item_id} className="pa-list-row">
                <span className={"pa-dot" + (n.is_read ? " is-read" : "")} />
                <div>
                  <strong>{eventLabel(n.kind)}</strong>
                  <small>{date(n.created_at)}</small>
                </div>
                {n.is_read ? (
                  <span className="pa-muted">
                    <Check size={16} /> Đã đọc
                  </span>
                ) : (
                  <Button
                    disabled={cmd.busy}
                    onClick={() =>
                      cmd.run(
                        () => cmd.send("/inbox/" + n.item_id + "/read"),
                        q.reload,
                      )
                    }
                  >
                    Đánh dấu đã đọc
                  </Button>
                )}
              </article>
            ))
          ) : (
            <Empty text="Chưa có thông báo" />
          )}
          <CursorPager
            page={pagination.page}
            count={q.data?.items.length ?? 0}
            nextCursor={q.data?.next_cursor}
            onNext={pagination.next}
            onPrevious={pagination.back}
          />
        </section>
      </LoadBoundary>
    </div>
  );
}
export function SettingsPage() {
  const q = useAdminQuery(() => read<Settings>("/settings"), "settings"),
    [deliveryState, setDeliveryState] = useState(""),
    pagination = useAdminCursor(deliveryState),
    deliveries = useAdminQuery(
      () =>
        read<Page<Delivery>>(
          "/email-deliveries" + query({ state: deliveryState, cursor: pagination.cursor, limit: 25 }),
        ),
      JSON.stringify([deliveryState, pagination.cursor]),
    );
  return (
    <div className="pa-page">
      <Heading
        title="Email hệ thống"
      >
        <Refresh
          onClick={() => {
            q.reload();
            deliveries.reload();
          }}
        />
      </Heading>
      <LoadBoundary {...q}>
        {q.data && (
          <section className="pa-panel pa-padded">
            <h2>Môi trường hiện tại</h2>
            <dl className="pa-facts">
              <dt>Môi trường</dt>
              <dd>{q.data.environment === "local" ? "nội bộ" : q.data.environment}</dd>
              <dt>Thanh toán thật</dt>
              <dd>{q.data.real_payments_enabled ? "Đang bật" : "Đã tắt"}</dd>
              <dt>Thanh toán thử nghiệm</dt>
              <dd>
                {q.data.billing_sandbox_enabled ? "Đang bật" : "Đã tắt"}
              </dd>
              <dt>Dịch vụ email</dt>
              <dd>
                {q.data.smtp_configured ? "Đã cấu hình" : "Chưa cấu hình"}
              </dd>
            </dl>
          </section>
        )}
      </LoadBoundary>
      <section className="pa-panel">
        <h2 className="pa-section-heading">Lịch sử gửi email</h2>
        <div className="pa-padded">
          <Field label="Trạng thái gửi email">
            <AdminSelect value={deliveryState} onChange={(event) => setDeliveryState(event.target.value)}>
              <option value="">Tất cả trạng thái</option>
              <option value="pending">Đang chờ</option>
              <option value="sending">Đang gửi</option>
              <option value="sent">Đã gửi</option>
              <option value="failed">Thất bại</option>
            </AdminSelect>
          </Field>
        </div>
        <LoadBoundary {...deliveries}>
          <Table
            items={deliveries.data?.items ?? []}
            rowKey={(r) => r.delivery_id}
            emptyText="Chưa có lịch sử gửi email"
            emptyDetail="Email thiết lập tài khoản và khôi phục mật khẩu sẽ được theo dõi tại đây."
            columns={[
              {
                title: "Loại email",
                render: (r) =>
                  r.template === "password_setup" ? "Thiết lập tài khoản"
                    : r.template === "password_recovery" ? "Khôi phục mật khẩu" : "Thông báo hệ thống",
              },
              {
                title: "Trạng thái",
                render: (r) => <Status value={r.state} />,
              },
              { title: "Số lần gửi", render: (r) => r.attempts },
              {
                title: "Kết quả",
                render: (r) => r.state === "failed"
                  ? "Không gửi được. Kiểm tra SMTP, sau đó gửi lại từ Tài khoản & vai trò."
                  : r.state === "sent" ? "Đã chuyển đến máy chủ email" : r.state === "sending" ? "Tiến trình xử lý đang gửi" : "Chờ tiến trình xử lý",
              },
              { title: "Thời gian", render: (r) => date(r.created_at) },
            ]}
          />
          <CursorPager
            page={pagination.page}
            total={deliveries.data?.total}
            count={deliveries.data?.items.length ?? 0}
            nextCursor={deliveries.data?.next_cursor}
            onNext={pagination.next}
            onPrevious={pagination.back}
          />
        </LoadBoundary>
      </section>
    </div>
  );
}
export function FeedbackPage({
  initialOrganization = "",
}: {
  initialOrganization?: string;
}) {
  const [org, setOrg] = useState(initialOrganization),
    [selected, setSelected] = useState(""),
    [body, setBody] = useState(""),
    pagination = useAdminCursor(org),
    messagePagination = useAdminCursor(org + ":" + selected);
  const schools = useAdminQuery(
    () => readAllPages<Organization>("/organizations"),
    "feedback-schools",
  );
  const q = useAdminQuery(
    () =>
      org
        ? read<Page<FeedbackItem>>(
            "/organizations/" +
              org +
              "/feedback" +
              query({ cursor: pagination.cursor, limit: 25 }),
          )
        : Promise.resolve({ items: [], total: 0 }),
    JSON.stringify([org, pagination.cursor]),
  );
  const thread = useAdminQuery(
      () =>
        selected
          ? read<Thread>(
              "/organizations/" +
                org +
                "/feedback/" +
                selected +
                query({ cursor: messagePagination.cursor, limit: 25 }),
            )
          : Promise.resolve(null),
      JSON.stringify([org, selected, messagePagination.cursor]),
    ),
    cmd = useAdminCommand();
  return (
    <div className="pa-page">
      <Heading
        title="Phản hồi học liệu"
      />
      <Feedback {...cmd} />
      <LoadBoundary {...schools}>
        <Field label="Trường học">
          <AdminSelect
            value={org}
            onChange={(e) => {
              setOrg(e.target.value);
              setSelected("");
              setBody("");
            }}
          >
            <option value="">Chọn trường học</option>
            {schools.data?.items.map((o) => (
              <option key={o.organization_id} value={o.organization_id}>
                {o.display_name}
              </option>
            ))}
          </AdminSelect>
        </Field>
      </LoadBoundary>
      {!schools.loading && !schools.error && !org && (
        <Empty text={schools.data?.items.length ? "Chọn trường để xem phản hồi" : "Chưa có trường học"}
          action={!schools.data?.items.length ? <Link className="pa-button" to="?panel=orgs">Quản lý trường học</Link> : undefined} />
      )}
      {org && (
        <div className="pa-two-column">
          <section className="pa-panel">
            <LoadBoundary {...q}>
              <Table
                items={q.data?.items ?? []}
                rowKey={(r) => r.thread_id}
                emptyText="Chưa có cuộc trao đổi"
                columns={[
                  {
                    title: "Cuộc trao đổi",
                    render: (r) => (
                      <Button
                        onClick={() => {
                          setSelected(r.thread_id);
                          setBody("");
                        }}
                      >
                        Giáo án {r.lesson_title?.trim() || "Chưa rõ tiêu đề"}{r.version_no ? ` · Phiên bản ${r.version_no}` : ""}
                      </Button>
                    ),
                  },
                  { title: "Ngày tạo", render: (r) => date(r.created_at) },
                ]}
              />
              <CursorPager
                page={pagination.page}
                total={q.data?.total}
                count={q.data?.items.length ?? 0}
                nextCursor={q.data?.next_cursor}
                onNext={pagination.next}
                onPrevious={pagination.back}
              />
            </LoadBoundary>
          </section>
          <section className="pa-panel pa-padded">
            {selected ? (
              <LoadBoundary {...thread}>
                {thread.data && (
                  <>
                    <h2>{thread.data.lesson_title?.trim() || "Nội dung trao đổi"}{thread.data.version_no ? ` · Phiên bản ${thread.data.version_no}` : ""}</h2>
                    <div className="pa-messages">
                      {thread.data.items.map((m) => (
                        <article
                          className={
                            "pa-message" + (m.from_you ? " is-own" : "")
                          }
                          key={m.message_id}
                        >
                          <strong>{feedbackAuthorLabel(m.author_role, m.author_display_name, m.from_you)}</strong>
                          <p>{m.body}</p>
                          <small>{date(m.created_at)}</small>
                        </article>
                      ))}
                    </div>
                    <CursorPager
                      page={messagePagination.page}
                      count={thread.data.items.length}
                      nextCursor={thread.data.next_cursor}
                      onNext={messagePagination.next}
                      onPrevious={messagePagination.back}
                    />
                    <Form
                      onSubmit={() =>
                        cmd.run(
                          () =>
                            cmd.send(
                              "/organizations/" +
                                org +
                                "/feedback/" +
                                selected +
                                "/replies",
                              { body: body.trim() },
                              thread.data!.revision,
                            ),
                          () => {
                            setBody("");
                            thread.reload();
                            q.reload();
                          },
                        )
                      }
                    >
                      <Field label="Phản hồi của bạn">
                        <textarea
                          required
                          maxLength={2000}
                          value={body}
                          onChange={(e) => setBody(e.target.value)}
                        />
                      </Field>
                      <Button
                        primary
                        type="submit"
                        disabled={cmd.busy || !body.trim()}
                      >
                        Gửi phản hồi
                      </Button>
                    </Form>
                  </>
                )}
              </LoadBoundary>
            ) : (
              <Empty text="Chọn một cuộc trao đổi" />
            )}
          </section>
        </div>
      )}
    </div>
  );
}
