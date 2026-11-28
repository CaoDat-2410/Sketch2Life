import { useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Building2,
  CircleCheck,
  CircleOff,
  Clock3,
  ListFilter,
  Mail,
  ShieldCheck,
  Users,
} from "lucide-react";
import { backendApi } from "../../../../shared/api/backendApi";
import {
  read,
  type Inbox,
  type Invoice,
  type Operations,
  type Organization,
  type OrganizationSummary,
  type Page,
  type Settings,
} from "../../services/adminService";
import { useAdminQuery, date, money } from "../adminHooks";
import { Empty, Heading, LoadBoundary, Refresh, Status, Table } from "../AdminUI";
import { Tabs } from "../../../../shared/ui";
import {
  ACCOUNT_ROLE_DEFINITIONS,
  buildAccountRoleCounts,
  cappedSourceNote,
  isTestPaymentMode,
  summarizeInvoices,
  summarizePayments,
  type CashFlowRange,
  type PaymentRecord,
} from "./dashboardData";
import { eventLabel } from "./adminEventLabels";
import {
  AccountRoleOverview,
  CashFlowChart,
  OperationsOverview,
  OrganizationStateOverview,
  ProcessingDistribution,
  RecentPaymentEvents,
} from "./DashboardPanels";

export function DashboardOverviewPage() {
  const [activeTab, setActiveTab] = useState("overview");
  const [cashFlowRange, setCashFlowRange] = useState<CashFlowRange>("7d");
  const [currentDate] = useState(() =>
    new Intl.DateTimeFormat("vi-VN", {
      day: "numeric",
      month: "long",
      year: "numeric",
      timeZone: "Asia/Ho_Chi_Minh",
    }).format(new Date()),
  );
  const schools = useAdminQuery(
    () => read<Page<Organization>>("/organizations?limit=5"),
    "overview-schools",
  );
  const schoolSummary = useAdminQuery(
    () => read<OrganizationSummary>("/organizations/summary"),
    "overview-school-summary",
  );
  const accounts = useAdminQuery(
    () => backendApi.listPlatformAccounts({ limit: 1 }),
    "overview-accounts",
  );
  const accountRoles = useAdminQuery(async () => {
    const [all, rolePages] = await Promise.all([
      backendApi.listPlatformAccounts({ limit: 1 }),
      Promise.all(ACCOUNT_ROLE_DEFINITIONS.map(({ role }) => backendApi.listPlatformAccounts({ role, limit: 1 }))),
    ]);
    return buildAccountRoleCounts(all.total, rolePages.map((page) => page.total));
  }, "overview-account-roles");
  const operations = useAdminQuery(
    () => read<Operations>("/operations"),
    "overview-operations",
  );
  const inbox = useAdminQuery(
    () => read<Page<Inbox>>("/inbox?limit=3"),
    "overview-inbox",
  );
  const pendingLessons = useAdminQuery(
    () => read<Page<unknown>>("/lessons?state=PENDING_REVIEW&limit=1"),
    "overview-pending-lessons",
  );
  const invoices = useAdminQuery(
    () => read<Page<Invoice & { created_at: string | null }>>("/billing/quota-invoices?limit=100"),
    "overview-quota-invoices",
  );
  const paymentEvents = useAdminQuery(
    () => read<Page<PaymentRecord>>("/billing/quota-payment-events?limit=500"),
    "overview-payment-events",
  );
  const settings = useAdminQuery(
    () => read<Settings>("/settings"),
    "overview-payment-settings",
  );
  const reload = () => {
    schools.reload();
    schoolSummary.reload();
    accounts.reload();
    accountRoles.reload();
    operations.reload();
    inbox.reload();
    pendingLessons.reload();
    invoices.reload();
    paymentEvents.reload();
    settings.reload();
  };
  const loading = [
    schools.loading,
    schoolSummary.loading,
    accounts.loading,
    accountRoles.loading,
    operations.loading,
    inbox.loading,
    pendingLessons.loading,
    invoices.loading,
    paymentEvents.loading,
    settings.loading,
  ].some(Boolean);
  const shortcuts = [
    { title: "Quản lý trường học", icon: Building2, to: "?panel=orgs" },
    { title: "Tài khoản", icon: Users, to: "/platform/accounts" },
    { title: "Thư viện học liệu", icon: BookOpen, to: "/platform/a01-content-moderation" },
    { title: "Phân quyền", icon: ShieldCheck, to: "?panel=permissions" },
  ];
  const tabs = [
    { value: "overview", label: "Tổng quan" },
    { value: "finance", label: "Tài chính" },
    { value: "operations", label: "Vận hành" },
  ] as const;
  const invoicesNote = invoices.data
    ? cappedSourceNote(invoices.data.total, invoices.data.items.length, "hóa đơn")
    : null;
  const eventsNote = paymentEvents.data
    ? cappedSourceNote(paymentEvents.data.total, paymentEvents.data.items.length, "giao dịch")
    : null;
  const paymentSummary = paymentEvents.data ? summarizePayments(paymentEvents.data.items) : null;
  const invoiceSummary = invoices.data ? summarizeInvoices(invoices.data.items) : null;

  return (
    <div className="pa-page pa-dashboard pa-dashboard-v2 pa-dashboard-v3">
      <Heading title="Tổng quan">
        <span className="pa-current-date">{currentDate}</span>
        <Refresh onClick={reload} disabled={loading} />
      </Heading>

      <section className="pa-metrics pa-dashboard-metrics" aria-label="Số liệu tổng quan">
        <Link className="pa-dashboard-metric is-violet" to="?panel=orgs">
          <span className="pa-metric-icon"><Building2 size={19} aria-hidden="true" /></span>
          <span>Trường học</span>
          <strong>{schoolSummary.loading ? "…" : schoolSummary.error ? "—" : schoolSummary.data?.total ?? "—"}</strong>
          {schoolSummary.error && <small>Không tải được số liệu</small>}
          <ArrowUpRight size={16} aria-hidden="true" />
        </Link>
        <Link className="pa-dashboard-metric is-green" to="/platform/accounts">
          <span className="pa-metric-icon"><Users size={19} aria-hidden="true" /></span>
          <span>Tài khoản</span>
          <strong>{accounts.loading ? "…" : accounts.error ? "—" : accounts.data?.total ?? "—"}</strong>
          {accounts.error && <small>Không tải được số liệu</small>}
          <ArrowUpRight size={16} aria-hidden="true" />
        </Link>
        <Link className="pa-dashboard-metric is-gold" to="/platform/a01-content-moderation?state=PENDING_REVIEW">
          <span className="pa-metric-icon"><ListFilter size={19} aria-hidden="true" /></span>
          <span>Học liệu chờ duyệt</span>
          <strong>{pendingLessons.loading ? "…" : pendingLessons.error ? "—" : pendingLessons.data?.total ?? "—"}</strong>
          {pendingLessons.error && <small>Không tải được số liệu</small>}
          <ArrowUpRight size={16} aria-hidden="true" />
        </Link>
        <Link className="pa-dashboard-metric is-coral" to="?panel=inbox">
          <span className="pa-metric-icon"><Mail size={19} aria-hidden="true" /></span>
          <span>Thông báo chưa đọc</span>
          <strong>{inbox.loading ? "…" : inbox.error ? "—" : inbox.data?.unread_count ?? "—"}</strong>
          {inbox.error && <small>Không tải được số liệu</small>}
          <ArrowUpRight size={16} aria-hidden="true" />
        </Link>
      </section>

      <Tabs
        items={tabs}
        value={activeTab}
        onValueChange={setActiveTab}
        label="Các mục quản trị"
        idPrefix="pa-overview"
        className="pa-dashboard-tablist"
      />

      <div
        className="pa-dashboard-tabpanel"
        id={"pa-overview-panel-" + activeTab}
        role="tabpanel"
        aria-labelledby={"pa-overview-tab-" + activeTab}
        tabIndex={0}
      >
        {activeTab === "overview" && (
          <div className="pa-dashboard-overview">
            <div className="pa-dashboard-summary-grid">
              <section className="pa-panel pa-dashboard-panel" aria-labelledby="pa-dashboard-school-states-title">
                <div className="pa-dashboard-panel-heading">
                  <div><h2 id="pa-dashboard-school-states-title">Trạng thái trường học</h2><p>Tỷ lệ và số lượng theo trạng thái hiện tại.</p></div>
                </div>
                <LoadBoundary {...schoolSummary}>
                  {schoolSummary.data && <OrganizationStateOverview summary={schoolSummary.data} />}
                </LoadBoundary>
              </section>
              <section className="pa-panel pa-dashboard-panel" aria-labelledby="pa-dashboard-account-roles-title">
                <div className="pa-dashboard-panel-heading">
                  <div><h2 id="pa-dashboard-account-roles-title">Tài khoản theo vai trò</h2><p>Tỷ lệ trên tổng số tài khoản.</p></div>
                </div>
                <LoadBoundary {...accountRoles}>
                  {accountRoles.data && <AccountRoleOverview {...accountRoles.data} />}
                </LoadBoundary>
              </section>
            </div>

            <div className="pa-dashboard-overview-lower">
              <section className="pa-panel pa-dashboard-panel pa-dashboard-schools" aria-labelledby="pa-dashboard-schools-title">
                <div className="pa-dashboard-panel-heading">
                  <div>
                    <h2 id="pa-dashboard-schools-title">Trường học mới nhất</h2>
                    <p>{schools.data ? "Hiển thị " + schools.data.items.length + " trên " + (schoolSummary.data?.total ?? "—") + " trường" : "Tối đa 5 trường học gần đây."}</p>
                  </div>
                  <Link to="?panel=orgs">Xem tất cả <ArrowUpRight size={14} aria-hidden="true" /></Link>
                </div>
                <LoadBoundary {...schools}>
                  {schools.data && <Table
                    items={schools.data.items}
                    rowKey={(school) => school.organization_id}
                    emptyText="Chưa có trường học"
                    emptyDetail="Các trường học sẽ xuất hiện tại đây."
                    caption="Trường học mới nhất"
                    columns={[
                      { title: "Trường học", render: (school) => (
                        <div className="pa-school-cell"><span aria-hidden="true">{school.display_name.replace(/^\[TEST\]\s*/, "").split(/\s+/).slice(0, 2).map((word) => word[0]).join("").toUpperCase()}</span><strong>{school.display_name}</strong></div>
                      ) },
                      { title: "Trạng thái", render: (school) => <Status value={school.state} /> },
                      { title: "Thao tác", render: (school) => <Link className="pa-school-open"
                        aria-label={"Mở " + school.display_name}
                        to={"?panel=orgs&search=" + encodeURIComponent(school.display_name)}
                      >Mở <ArrowUpRight size={15} aria-hidden="true" /></Link> },
                    ]}
                  />}
                </LoadBoundary>
              </section>

              <section className="pa-panel pa-dashboard-panel pa-dashboard-notifications" aria-labelledby="pa-dashboard-notifications-title">
                <div className="pa-dashboard-panel-heading">
                  <div><h2 id="pa-dashboard-notifications-title">Thông báo gần đây</h2></div>
                  <span className="pa-notification-count" aria-label="Số thông báo chưa đọc">
                    {inbox.loading ? "…" : inbox.error ? "—" : inbox.data?.unread_count ?? "—"}
                  </span>
                </div>
                <LoadBoundary {...inbox}>
                  {inbox.data?.items.length ? (
                    <div className="pa-notification-feed">
                      {inbox.data.items.slice(0, 3).map((notification) => (
                        <Link
                          to="?panel=inbox"
                          className={"pa-notification" + (notification.is_read ? " is-read" : "")}
                          key={notification.item_id}
                        >
                          <span className="pa-notification-icon"><Mail size={16} aria-hidden="true" /></span>
                          <div><strong>{eventLabel(notification.kind)}</strong><small>{date(notification.created_at)}</small></div>
                          {!notification.is_read && <span className="pa-dot" aria-label="Chưa đọc" />}
                          <ArrowUpRight className="pa-notification-arrow" size={15} aria-hidden="true" />
                        </Link>
                      ))}
                    </div>
                  ) : <Empty text="Chưa có thông báo mới" />}
                </LoadBoundary>
                <Link className="pa-inbox-more" to="?panel=inbox">Xem tất cả thông báo <ArrowRight size={16} aria-hidden="true" /></Link>
              </section>

              <section className="pa-panel pa-dashboard-panel pa-dashboard-shortcuts" aria-labelledby="pa-dashboard-shortcuts-title">
                <div className="pa-dashboard-panel-heading"><div><h2 id="pa-dashboard-shortcuts-title">Truy cập nhanh</h2></div></div>
                <div className="pa-shortcuts">
                  {shortcuts.map((item) => (
                    <Link className="pa-shortcut" key={item.title} to={item.to}>
                      <span className="pa-shortcut-icon"><item.icon size={20} aria-hidden="true" /></span>
                      <strong>{item.title}</strong>
                      <ArrowRight size={17} aria-hidden="true" />
                    </Link>
                  ))}
                </div>
              </section>
            </div>
          </div>
        )}

        {activeTab === "finance" && (
          <div className="pa-dashboard-finance">
            <section className="pa-panel pa-dashboard-payment-mode" aria-labelledby="pa-dashboard-payment-mode-title">
              <div className="pa-dashboard-panel-heading"><div><h2 id="pa-dashboard-payment-mode-title">Trạng thái thanh toán</h2></div></div>
              <LoadBoundary {...settings}>
                {settings.data && (isTestPaymentMode(settings.data)
                  ? <p className="pa-dashboard-test-label" role="status">Dữ liệu thử nghiệm</p>
                  : <p className="pa-dashboard-live-label" role="status">Đang ghi nhận giao dịch thật</p>)}
              </LoadBoundary>
            </section>

            <div className="pa-dashboard-finance-notes">
              {eventsNote && <p>{eventsNote}</p>}
              {invoicesNote && <p>{invoicesNote}</p>}
            </div>

            <div className="pa-dashboard-money-grid">
              <div className="pa-dashboard-boundary-contents">
                <LoadBoundary {...paymentEvents}>
                  {paymentSummary && <article className="pa-panel pa-dashboard-money-card is-green">
                    <span className="pa-dashboard-money-icon"><CircleCheck size={19} aria-hidden="true" /></span>
                    <span className="pa-dashboard-money-label">Đã thu</span>
                    <strong>{money(paymentSummary.amountVnd)}</strong>
                    <small>{paymentSummary.count.toLocaleString("vi-VN")} giao dịch thành công</small>
                  </article>}
                </LoadBoundary>
              </div>
              <div className="pa-dashboard-boundary-contents">
                <LoadBoundary {...invoices}>
                  {invoiceSummary && <div className="pa-dashboard-invoice-metrics">
                    <article className="pa-panel pa-dashboard-money-card is-gold">
                      <span className="pa-dashboard-money-icon"><Clock3 size={19} aria-hidden="true" /></span>
                      <span className="pa-dashboard-money-label">Chờ thanh toán</span>
                      <strong>{money(invoiceSummary.pendingAmountVnd)}</strong>
                      <small>{invoiceSummary.pendingCount.toLocaleString("vi-VN")} hóa đơn đang chờ</small>
                    </article>
                    <article className="pa-panel pa-dashboard-money-card is-coral">
                      <span className="pa-dashboard-money-icon"><CircleOff size={19} aria-hidden="true" /></span>
                      <span className="pa-dashboard-money-label">Không thành công</span>
                      <strong>{money(invoiceSummary.unsuccessfulAmountVnd)}</strong>
                      <small>{invoiceSummary.unsuccessfulCount.toLocaleString("vi-VN")} hóa đơn thất bại hoặc đã hủy</small>
                    </article>
                  </div>}
                </LoadBoundary>
              </div>
            </div>

            <div className="pa-dashboard-finance-grid">
              <section className="pa-panel pa-dashboard-panel pa-dashboard-cash-panel" aria-labelledby="pa-dashboard-cash-title">
                <div className="pa-dashboard-panel-heading"><div><h2 id="pa-dashboard-cash-title">Dòng tiền</h2><p>Khoản thu thành công và số tiền cộng dồn theo thời gian.</p></div></div>
                <LoadBoundary {...paymentEvents}>
                  {paymentEvents.data && <CashFlowChart
                    events={paymentEvents.data.items}
                    range={cashFlowRange}
                    onRangeChange={setCashFlowRange}
                  />}
                </LoadBoundary>
              </section>
              <section className="pa-panel pa-dashboard-panel pa-dashboard-recent-payments" aria-labelledby="pa-dashboard-recent-payments-title">
                <div className="pa-dashboard-panel-heading"><div><h2 id="pa-dashboard-recent-payments-title">Giao dịch gần đây</h2><p>Giao dịch mới nhất đã tải.</p></div></div>
                <LoadBoundary {...paymentEvents}>
                  {paymentEvents.data && <RecentPaymentEvents events={paymentEvents.data.items} />}
                </LoadBoundary>
              </section>
            </div>
          </div>
        )}

        {activeTab === "operations" && (
          <section className="pa-dashboard-operations-section" aria-labelledby="pa-dashboard-operations-title">
            <div className="pa-dashboard-section-intro"><h2 id="pa-dashboard-operations-title">Tình trạng vận hành</h2><p>Số liệu hiện tại từ các dịch vụ của nền tảng.</p></div>
            <LoadBoundary {...operations}>
              {operations.data && <OperationsOverview operations={operations.data}>
                <section className="pa-panel pa-dashboard-panel pa-dashboard-distribution-panel" aria-labelledby="pa-dashboard-distribution-title">
                  <div className="pa-dashboard-panel-heading">
                    <div><h2 id="pa-dashboard-distribution-title">Phân bố bản ghi xử lý</h2><p>Số bản ghi theo nhóm hoạt động.</p></div>
                  </div>
                  <ProcessingDistribution operations={operations.data} />
                </section>
              </OperationsOverview>}
            </LoadBoundary>
          </section>
        )}
      </div>
    </div>
  );
}
