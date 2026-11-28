import { AdminSelect } from '../components/AdminSelect'
import { Layers, School, Tags } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  createIdempotencyKey,
  backendApi,
} from "../../../shared/api/backendApi";
import {
  read,
  query,
  type Page,
  type Organization,
  type Settings,
  type Offer,
  type Invoice,
  type QuotaProduct,
  type QuotaProductEvent,
  type Quota,
  type Subscription,
  readAllPages,
} from "../services/adminService";
import { useAdminQuery, useAdminCommand, useAdminCursor, money, date, short } from '../components/adminHooks'
import { Heading, Button, Field, Form, Feedback, LoadBoundary, Table, Refresh, CursorPager, Status, Empty } from '../components/AdminUI'
import { StatusBadge } from "../../../shared/ui";
import "../styles/admin-billing-events.css";

type Scope = { owner_kind: string; owner_ref: string };
function ScopeFields({
  value,
  onChange,
}: {
  value: Scope;
  onChange: (value: Scope) => void;
}) {
  const q = useAdminQuery(
    () =>
      Promise.all([
        readAllPages<Organization>("/organizations"),
        backendApi.listAllPlatformAccounts({
          role: "parent",
          state: "active",
        }),
      ]),
    "billing-scopes",
  );
  return (
    <LoadBoundary {...q}>
      <div className="pa-form-grid">
        <Field label="Phạm vi">
          <AdminSelect
            value={value.owner_kind}
            onChange={(e) =>
              onChange({ owner_kind: e.target.value, owner_ref: "" })
            }
          >
            <option value="ORGANIZATION">Trường học</option>
            <option value="PARENT_ACCOUNT">Phụ huynh</option>
          </AdminSelect>
        </Field>
        <Field
          label={
            value.owner_kind === "ORGANIZATION"
              ? "Trường học"
              : "Tài khoản phụ huynh"
          }
        >
          <AdminSelect
            required
            value={value.owner_ref}
            onChange={(e) => onChange({ ...value, owner_ref: e.target.value })}
          >
            <option value="">Chọn đối tượng</option>
            {value.owner_kind === "ORGANIZATION"
              ? q.data?.[0].items.map((o) => (
                  <option key={o.organization_id} value={o.organization_id}>
                    {o.display_name}
                  </option>
                ))
              : q.data?.[1].items.map((a) => (
                  <option key={a.account_id} value={a.account_id}>
                    {a.display_name ?? a.email ?? short(a.account_id)}
                  </option>
                ))}
          </AdminSelect>
        </Field>
      </div>
    </LoadBoundary>
  );
}
function SandboxGate({ children }: { children: React.ReactNode }) {
  const q = useAdminQuery(() => read<Settings>("/settings"), "billing-mode");
  return (
    <LoadBoundary {...q}>
      {q.data?.billing_sandbox_enabled ? (
        <>
          <aside className="pa-sandbox">
            <strong>Môi trường thử nghiệm</strong>
            <span>
              Thao tác chỉ ghi nhận giao dịch thử nghiệm, không thu tiền thật.
            </span>
          </aside>
          {children}
        </>
      ) : (
        <Empty
          text="Thanh toán thử nghiệm đang tắt"
          detail="Không thể tạo hoặc xác nhận giao dịch trong môi trường này."
        />
      )}
    </LoadBoundary>
  );
}
export function BillingPage() {
  return (
    <div className="pa-page">
      <Heading title="Đối soát thanh toán" />
      <RealBillingMonitor />
      <details className="pa-panel pa-padded">
        <summary className="font-semibold cursor-pointer">Công cụ thanh toán thử nghiệm</summary>
        <div className="mt-4"><SandboxGate><BillingWorkspace /></SandboxGate></div>
      </details>
    </div>
  );
}

type RealInvoice = Invoice & {
  product_id: string | null;
  provider: string;
  payment_mode: string;
  created_at: string | null;
  attempts: { provider: string; state: string; expires_at: string | null }[];
};
type PaymentEvent = {
  event_id: string;
  invoice_id: string;
  provider: string;
  provider_transaction_ref: string | null;
  amount_vnd: number;
  outcome: string;
  created_at: string | null;
};
function RealBillingMonitor() {
  const [state, setState] = useState("");
  const [reconcileMessage, setReconcileMessage] = useState("");
  const reconcile = useAdminCommand();
  const q = useAdminQuery(
    () => read<Page<RealInvoice>>("/billing/quota-invoices" + query({ state, limit: 100 })),
    "real-quota-invoices:" + state,
  );
  const events = useAdminQuery(
    () => read<Page<PaymentEvent>>("/billing/quota-payment-events?limit=100"),
    "real-quota-payment-events",
  );
  const settings = useAdminQuery(() => read<Settings>("/settings"), "real-payment-settings");
  return (
    <div className="grid gap-4">
      <section className="pa-panel pa-padded grid gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="m-0">Thanh toán</h2>
            <p className="pa-muted mt-1">Chỉ ghi nhận đã trả sau khi máy chủ xác minh phản hồi từ cổng thanh toán.</p>
          </div>
          <div className="pa-actions">
            <Status value={settings.data?.real_payments_enabled ? "active" : "paused"} />
            <Refresh onClick={() => { q.reload(); events.reload(); settings.reload(); }} />
          </div>
        </div>
        <LoadBoundary {...settings}>
          {settings.data && <div className="flex flex-wrap gap-2 text-sm">
            <StatusBadge tone={settings.data.momo_checkout_enabled ? (settings.data.momo_sandbox_enabled ? "warn" : "success") : "neutral"} size="sm" dot>
              MoMo: {settings.data.momo_checkout_enabled ? settings.data.momo_sandbox_enabled ? "Chạy thử sẵn sàng" : "Production sẵn sàng" : "Chưa cấu hình / đang tắt"}
            </StatusBadge>
            <StatusBadge tone={settings.data.vnpay_checkout_enabled ? (settings.data.vnpay_sandbox_enabled ? "warn" : "success") : "neutral"} size="sm" dot>
              VNPay: {settings.data.vnpay_checkout_enabled ? settings.data.vnpay_sandbox_enabled ? "Chạy thử sẵn sàng" : "Production sẵn sàng" : "Chưa cấu hình / đang tắt"}
            </StatusBadge>
            <StatusBadge tone={settings.data.monthly_auto_renew_enabled ? "success" : "neutral"} size="sm" dot>
              Gia hạn tự động: {settings.data.monthly_auto_renew_enabled ? "Đã bật" : "Chưa hỗ trợ"}
            </StatusBadge>
          </div>}
        </LoadBoundary>
      </section>
      <section className="pa-panel">
        <div className="pa-toolbar pa-padded">
          <div><h2 className="m-0">Hóa đơn hạn mức</h2><p className="pa-muted mt-1">Gói tháng thanh toán thủ công và gói mua thêm của Phụ huynh, Trường học.</p></div>
          <Field label="Trạng thái">
            <AdminSelect value={state} onChange={(event) => setState(event.target.value)}>
              <option value="">Tất cả</option><option value="PENDING">Chờ thanh toán</option><option value="PAID">Đã thanh toán</option><option value="FAILED">Thất bại</option><option value="CANCELED">Đã hủy</option>
            </AdminSelect>
          </Field>
        </div>
        <Feedback error={reconcile.error} notice={reconcileMessage} />
        <LoadBoundary {...q}>
          <Table
            items={q.data?.items ?? []}
            rowKey={(row) => row.invoice_id}
            emptyText="Chưa có hóa đơn hạn mức"
            emptyDetail="Hóa đơn mua hạn mức thật sẽ xuất hiện sau khi Phụ huynh hoặc Quản lý trường tạo thanh toán."
            columns={[
              { title: "Hóa đơn", render: (row) => <><strong>{short(row.invoice_id)}</strong><small>{row.created_at ? date(row.created_at) : "—"}</small></> },
              { title: "Đối tượng", render: (row) => <><Status value={row.owner_kind} /><small>{short(row.owner_ref)}</small></> },
              { title: "Hạn mức", render: (row) => <>{row.units.toLocaleString("vi-VN")} lượt<small>{row.payment_mode === "AUTO_RENEW" ? "Gia hạn tự động" : "Thanh toán thủ công"}</small></> },
              { title: "Thanh toán", render: (row) => <><Status value={row.state} /><small>{row.provider}</small></> },
              { title: "Số tiền", render: (row) => money(row.amount_vnd) },
              { title: "Đối soát", render: (row) => row.state === "PENDING"
                ? <Button disabled={reconcile.busy} onClick={() => void reconcile.run(
                    () => reconcile.send<{ state: string; reconciled: boolean }>(`/billing/quota-invoices/${encodeURIComponent(row.invoice_id)}/reconcile`),
                    (result) => {
                      setReconcileMessage(result.reconciled
                        ? `Đã đối soát hóa đơn: ${result.state === "PAID" ? "đã thanh toán" : "thanh toán thất bại"}.`
                        : "Cổng chưa xác nhận kết quả cuối cùng. Hóa đơn vẫn đang chờ đối soát.");
                      q.reload(); events.reload();
                    },
                  )}>{reconcile.busy ? "Đang kiểm tra…" : "Kiểm tra với cổng"}</Button>
                : "—" },
            ]}
          />
        </LoadBoundary>
      </section>
      <section className="pa-panel">
        <div className="pa-padded"><h2 className="m-0">Sự kiện cổng thanh toán</h2></div>
        <LoadBoundary {...events}>
          <Table
            items={events.data?.items ?? []}
            rowKey={(row) => row.event_id}
            emptyText="Chưa nhận phản hồi từ cổng thanh toán"
            emptyDetail="MoMo và VNPay sẽ ghi sự kiện sau khi máy chủ xác minh chữ ký phản hồi từ cổng thanh toán."
            columns={[
              { title: "Cổng", render: (row) => <Status value={row.provider} /> },
              { title: "Hóa đơn", render: (row) => short(row.invoice_id) },
              { title: "Giao dịch", render: (row) => <code>{short(row.provider_transaction_ref ?? row.event_id)}</code> },
              { title: "Kết quả", render: (row) => <Status value={row.outcome} /> },
              { title: "Số tiền", render: (row) => money(row.amount_vnd) },
              { title: "Thời gian", render: (row) => row.created_at ? date(row.created_at) : "—" },
            ]}
          />
        </LoadBoundary>
      </section>
    </div>
  );
}
function BillingWorkspace() {
  const [state, setState] = useState(""),
    [scope, setScope] = useState<Scope>({
      owner_kind: "ORGANIZATION",
      owner_ref: "",
    }),
    [offer, setOffer] = useState(""),
    [units, setUnits] = useState(10),
    [amount, setAmount] = useState(50000),
    [kind, setKind] = useState("ORGANIZATION"),
    [mode, setMode] = useState<"none" | "invoice" | "offer">("none"),
    [selected, setSelected] = useState<Invoice | null>(null);
  const pagination = useAdminCursor(state);
  const q = useAdminQuery(
      () =>
        read<Page<Invoice>>(
          "/billing/sandbox/invoices" + query({ cursor: pagination.cursor, limit: 25, state }),
        ),
      JSON.stringify([state, pagination.cursor]),
    ),
    offers = useAdminQuery(
      () => readAllPages<Offer>("/billing/sandbox/offers"),
      "offers",
    ),
    cmd = useAdminCommand();
  const refresh = () => {
    q.reload();
    offers.reload();
  };
  return (
    <>
      <Feedback {...cmd} />
      <div className="pa-toolbar">
        <div className="pa-actions">
          <Button
            primary
            onClick={() => setMode(mode === "invoice" ? "none" : "invoice")}
          >
            + Tạo hóa đơn thử nghiệm
          </Button>
          <Button onClick={() => setMode(mode === "offer" ? "none" : "offer")}>
            Tạo gói hạn mức
          </Button>
          <Link className="pa-button" to="?panel=capacity">
            Gói sức chứa lớp →
          </Link>
        </div>
        <Refresh onClick={refresh} />
      </div>
      {mode === "offer" && (
        <section className="pa-panel pa-padded">
          <h2>Gói hạn mức mới</h2>
          <Form
            onSubmit={() =>
              cmd.run(
                () =>
                  cmd.send("/billing/sandbox/offers", {
                    owner_kind: kind,
                    units,
                    amount_vnd: amount,
                  }),
                () => {
                  setMode("none");
                  refresh();
                },
              )
            }
          >
            <div className="pa-form-grid">
              <Field label="Dành cho">
                <AdminSelect value={kind} onChange={(e) => setKind(e.target.value)}>
                  <option value="ORGANIZATION">Trường học</option>
                  <option value="PARENT_ACCOUNT">Phụ huynh</option>
                </AdminSelect>
              </Field>
              <Field label="Số lượt video">
                <input
                  required
                  type="number"
                  min={1}
                  max={100000}
                  value={units}
                  onChange={(e) => setUnits(e.target.valueAsNumber)}
                />
              </Field>
              <Field label="Giá thử nghiệm (VND)">
                <input
                  required
                  type="number"
                  min={1}
                  max={2000000000}
                  value={amount}
                  onChange={(e) => setAmount(e.target.valueAsNumber)}
                />
              </Field>
            </div>
            <Button primary type="submit" disabled={cmd.busy}>
              Tạo gói thử nghiệm
            </Button>
          </Form>
        </section>
      )}
      {mode === "invoice" && (
        <section className="pa-panel pa-padded">
          <h2>Tạo hóa đơn thử nghiệm</h2>
          <Form
            onSubmit={() =>
              cmd.run(
                () =>
                  cmd.send("/billing/sandbox/invoices", {
                    ...scope,
                    offer_id: offer,
                  }),
                () => {
                  setMode("none");
                  pagination.reset();
                  refresh();
                },
              )
            }
          >
            <ScopeFields
              value={scope}
              onChange={(s) => {
                setScope(s);
                setOffer("");
              }}
            />
            <LoadBoundary {...offers}>
              <Field label="Gói hạn mức">
                <AdminSelect
                  required
                  value={offer}
                  onChange={(e) => setOffer(e.target.value)}
                >
                  <option value="">Chọn gói</option>
                  {offers.data?.items
                    .filter((o) => o.owner_kind === scope.owner_kind)
                    .map((o) => (
                      <option key={o.offer_id} value={o.offer_id}>
                        {o.units} lượt · {money(o.amount_vnd)}
                      </option>
                    ))}
                </AdminSelect>
              </Field>
            </LoadBoundary>
            <Button
              primary
              type="submit"
              disabled={cmd.busy || !scope.owner_ref || !offer}
            >
              Tạo hóa đơn
            </Button>
          </Form>
        </section>
      )}
      {selected && (
        <section className="pa-panel pa-padded">
          <h2>Xác nhận giao dịch thử nghiệm</h2>
          <p>
            Hóa đơn <code>{short(selected.invoice_id)}</code> ·{" "}
            <strong>{money(selected.amount_vnd)}</strong>
          </p>
          <p className="pa-muted">
            Chọn kết quả để kiểm tra việc cấp hạn mức hoặc kích hoạt gói.
          </p>
          <div className="pa-actions">
            {[true, false].map((paid) => (
              <Button
                key={String(paid)}
                primary={paid}
                disabled={cmd.busy}
                onClick={() =>
                  cmd.run(
                    () =>
                      cmd.send(
                        "/billing/sandbox/invoices/" +
                          selected.invoice_id +
                          "/settle",
                        {
                          paid,
                          amount_vnd: selected.amount_vnd,
                          event_id:
                            "ui-test:" + selected.invoice_id + ":" + paid,
                        },
                        selected.revision,
                      ),
                    () => {
                      setSelected(null);
                      refresh();
                    },
                  )
                }
              >
                {paid ? "Ghi nhận thanh toán thử nghiệm" : "Ghi nhận thất bại"}
              </Button>
            ))}
            <Button disabled={cmd.busy} onClick={() => setSelected(null)}>
              Đóng
            </Button>
          </div>
        </section>
      )}
      <Field label="Trạng thái hóa đơn">
        <AdminSelect
          value={state}
          onChange={(e) => {
            setState(e.target.value);
          }}
        >
          <option value="">Tất cả hóa đơn</option>
          {["PENDING", "PAID", "FAILED"].map((v) => (
            <option key={v} value={v}>
              {v === "PENDING"
                ? "Chờ thanh toán"
                : v === "PAID"
                  ? "Đã thanh toán"
                  : "Thất bại"}
            </option>
          ))}
        </AdminSelect>
      </Field>
      <LoadBoundary {...q}>
        <section className="pa-panel">
          <Table
            items={q.data?.items ?? []}
            rowKey={(r) => r.invoice_id}
            emptyText="Chưa có hóa đơn thử nghiệm"
            emptyDetail="Tạo hóa đơn thử nghiệm để kiểm tra quy trình đối soát; không phát sinh thanh toán thật."
            columns={[
              {
                title: "Hóa đơn",
                render: (r) => (
                  <code title={r.invoice_id}>{short(r.invoice_id)}</code>
                ),
              },
              {
                title: "Phạm vi",
                render: (r) => (
                  <>
                    {r.owner_kind === "ORGANIZATION"
                      ? "Trường học"
                      : "Phụ huynh"}
                    <small title={r.owner_ref}>{short(r.owner_ref)}</small>
                  </>
                ),
              },
              {
                title: "Số tiền",
                render: (r) => <strong>{money(r.amount_vnd)}</strong>,
              },
              {
                title: "Trạng thái",
                render: (r) => <Status value={r.state} />,
              },
              {
                title: "Thao tác",
                render: (r) =>
                  r.state === "PENDING" ? (
                    <Button onClick={() => setSelected(r)}>
                      Kiểm tra thanh toán
                    </Button>
                  ) : (
                    "—"
                  ),
              },
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
    </>
  );
}
export function QuotaPage({ initialScope }: { initialScope?: Scope } = {}) {
  return (
    <div className="pa-page">
      <Heading title="Hạn mức video" />
      <QuotaCatalogWorkspace initialScope={initialScope} />
      <details className="pa-panel pa-padded">
        <summary className="font-semibold cursor-pointer">Công cụ hạn mức thử nghiệm</summary>
        <div className="mt-4"><SandboxGate><QuotaWorkspace initialScope={initialScope} /></SandboxGate></div>
      </details>
    </div>
  );
}

function QuotaCatalogWorkspace({ initialScope }: { initialScope?: Scope }) {
  const [scope, setScope] = useState<Scope>(initialScope ?? { owner_kind: "ORGANIZATION", owner_ref: "" });
  const [editing, setEditing] = useState<QuotaProduct | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [name, setName] = useState("");
  const [ownerKind, setOwnerKind] = useState<QuotaProduct["owner_kind"]>("ORGANIZATION");
  const [offerKind, setOfferKind] = useState<QuotaProduct["offer_kind"]>("TOP_UP");
  const [units, setUnits] = useState(100);
  const [amount, setAmount] = useState(100000);
  const [eventProduct, setEventProduct] = useState<QuotaProduct | null>(null);
  const [eventItems, setEventItems] = useState<QuotaProductEvent[] | null>(null);
  const [eventTotal, setEventTotal] = useState(0);
  const [eventLoading, setEventLoading] = useState(false);
  const [eventError, setEventError] = useState("");
  const eventRequest = useRef(0);
  const products = useAdminQuery(
    () => read<Page<QuotaProduct>>("/billing/quota-products?include_inactive=true"),
    "quota-products",
  );
  const summary = useAdminQuery(
    () => scope.owner_ref ? read<Quota>("/billing/quota" + query(scope)) : Promise.resolve(null),
    "real-quota-summary:" + JSON.stringify(scope),
  );
  const invoices = useAdminQuery(
    () => scope.owner_ref
      ? read<Page<RealInvoice>>("/billing/quota-invoices" + query({ owner_kind: scope.owner_kind, owner_ref: scope.owner_ref, limit: 25 }))
      : Promise.resolve({ items: [], total: 0 }),
    "real-quota-invoices-scope:" + JSON.stringify(scope),
  );
  const cmd = useAdminCommand();
  const refresh = () => { products.reload(); summary.reload(); invoices.reload(); };
  const loadProductEvents = async (product: QuotaProduct) => {
    const requestId = ++eventRequest.current;
    setEventProduct(product);
    setEventItems(null);
    setEventTotal(0);
    setEventError("");
    setEventLoading(true);
    try {
      const result = await read<{ items: QuotaProductEvent[]; total: number }>(
        "/billing/quota-products/" + encodeURIComponent(product.product_id) + "/events" + query({ limit: 100 }),
      );
      if (requestId === eventRequest.current) {
        setEventItems(result.items);
        setEventTotal(result.total);
      }
    } catch {
      if (requestId === eventRequest.current) setEventError("Không tải được lịch sử sự kiện. Vui lòng thử lại.");
    } finally {
      if (requestId === eventRequest.current) setEventLoading(false);
    }
  };
  const closeEventDrawer = () => {
    eventRequest.current += 1;
    setEventProduct(null);
    setEventItems(null);
    setEventError("");
    setEventLoading(false);
  };
  const beginCreate = () => {
    setEditing(null); setName(""); setOwnerKind("ORGANIZATION"); setOfferKind("TOP_UP"); setUnits(100); setAmount(100000); setFormOpen(true); cmd.clear();
  };
  const beginEdit = (product: QuotaProduct) => {
    setEditing(product); setName(product.display_name); setOwnerKind(product.owner_kind); setOfferKind(product.offer_kind); setUnits(product.units); setAmount(product.amount_vnd); setFormOpen(true); cmd.clear();
  };
  const save = () => cmd.run(() => cmd.send<QuotaProduct>(
    editing ? "/billing/quota-products/" + editing.product_id : "/billing/quota-products",
    { display_name: name, owner_kind: ownerKind, offer_kind: offerKind, cycle_months: offerKind === "MONTHLY" ? 1 : null, units, amount_vnd: amount },
    editing?.revision,
    editing ? "PUT" : "POST",
  ), () => { setFormOpen(false); refresh(); });
  const list = products.data?.items ?? [];
  return (
    <div className="grid gap-4">
      <Feedback {...cmd} />
      <section className="pa-panel pa-padded grid gap-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div><h2 className="m-0">Danh mục gói hạn mức</h2><p className="pa-muted mt-1">Mỗi lần đổi giá tạo phiên bản mới; hóa đơn cũ vẫn giữ giá tại thời điểm mua.</p></div>
          <div className="pa-actions"><Button primary onClick={beginCreate}>+ Tạo gói hạn mức</Button><Refresh onClick={refresh} /></div>
        </div>
        <LoadBoundary {...products}>
          <Table
            items={list}
            rowKey={(row) => row.product_id}
            emptyText="Chưa có gói hạn mức"
            emptyDetail="Tạo gói tháng hoặc gói mua thêm. Gói tháng cấp hạn mức theo tháng dương lịch; mua thêm không hết hạn."
            columns={[
              { title: "Gói", render: (row) => <><strong>{row.display_name}</strong><small><Status value={row.owner_kind} /> · v{row.version}</small></> },
              { title: "Loại", render: (row) => <Status value={row.offer_kind} /> },
              { title: "Hạn mức", render: (row) => row.units.toLocaleString("vi-VN") + " lượt" },
              { title: "Giá hiện tại", render: (row) => money(row.amount_vnd) },
              { title: "Trạng thái", render: (row) => <Status value={row.active ? "active" : "disabled"} /> },
              { title: "Quản lý", render: (row) => <div className="pa-actions"><Button onClick={() => beginEdit(row)}>Sửa giá</Button><Button disabled={cmd.busy} onClick={() => cmd.run(() => cmd.send<QuotaProduct>("/billing/quota-products/" + row.product_id + "/state", { active: !row.active }, row.revision), refresh)}>{row.active ? "Tạm ẩn" : "Kích hoạt"}</Button><Button onClick={() => loadProductEvents(row)}>Lịch sử</Button></div> },
            ]}
          />
        </LoadBoundary>
      </section>
      {formOpen && <section className="pa-panel pa-padded">
        <div className="flex items-center justify-between gap-3"><h2>{editing ? "Tạo phiên bản giá mới" : "Tạo gói hạn mức"}</h2><Button onClick={() => setFormOpen(false)}>Đóng</Button></div>
        <p className="pa-muted">Không sửa lịch sử đã bán. Bản cập nhật sẽ thay giá đang hiển thị cho lượt mua mới.</p>
        <Form onSubmit={save}>
          <div className="pa-form-grid">
            <Field label="Tên gói"><input required minLength={2} maxLength={120} value={name} onChange={(event) => setName(event.target.value)} /></Field>
            <Field label="Đối tượng"><AdminSelect value={ownerKind} disabled={!!editing} onChange={(event) => setOwnerKind(event.target.value as QuotaProduct["owner_kind"])}><option value="ORGANIZATION">Trường học</option><option value="PARENT_ACCOUNT">Phụ huynh</option></AdminSelect></Field>
            <Field label="Hình thức"><AdminSelect value={offerKind} disabled={!!editing} onChange={(event) => setOfferKind(event.target.value as QuotaProduct["offer_kind"])}><option value="TOP_UP">Mua thêm · không hết hạn</option><option value="MONTHLY">Gói tháng · tháng dương lịch</option></AdminSelect></Field>
            <Field label="Số lượt video"><input required type="number" min={1} max={100000} value={units} onChange={(event) => setUnits(event.target.valueAsNumber)} /></Field>
            <Field label="Giá bán (VND)"><input required type="number" min={1000} max={2000000000} step={1000} value={amount} onChange={(event) => setAmount(event.target.valueAsNumber)} /></Field>
          </div>
          <Button primary type="submit" disabled={cmd.busy}>Lưu gói</Button>
        </Form>
      </section>}
      <section className="pa-two-column">
        <div className="pa-panel pa-padded grid gap-3">
          <div className="flex items-start justify-between gap-3"><div><h2 className="m-0">Số dư theo phạm vi</h2><p className="pa-muted mt-1">Chỉ đọc sổ hạn mức đã được ghi nhận.</p></div><Refresh onClick={() => { summary.reload(); invoices.reload(); }} /></div>
          <ScopeFields value={scope} onChange={setScope} />
          {!scope.owner_ref ? <Empty text="Chọn trường hoặc phụ huynh" detail="Số dư, lượt đã dùng và hóa đơn sẽ hiện theo đối tượng đã chọn." /> : <LoadBoundary {...summary}>
            {summary.data && <>
              <div className="pa-quota-summary"><div><p>Còn khả dụng</p><strong>{summary.data.available_units}<small> lượt</small></strong></div><div><p>Đã cấp</p><strong>{summary.data.granted_units}<small> lượt</small></strong></div><div><p>Đã dùng</p><strong>{summary.data.used_units}<small> lượt</small></strong></div></div>
              <Table items={summary.data.grants} rowKey={(row) => row.grant_id} emptyText="Chưa có lượt hạn mức" columns={[
                { title: "Nguồn", render: (row) => <Status value={row.kind} /> },
                { title: "Đã cấp", render: (row) => row.units },
                { title: "Đã dùng", render: (row) => row.used },
                { title: "Còn lại", render: (row) => row.available },
                { title: "Hết hạn", render: (row) => row.expires_at ? date(row.expires_at) : "Không hết hạn" },
              ]} />
            </>}
          </LoadBoundary>}
        </div>
        <div className="pa-panel pa-padded">
          <h2>Hóa đơn gần đây</h2>
          {!scope.owner_ref ? <p className="pa-muted">Chọn phạm vi để xem hóa đơn.</p> : <LoadBoundary {...invoices}><Table items={invoices.data?.items ?? []} rowKey={(row) => row.invoice_id} emptyText="Chưa có hóa đơn" columns={[
            { title: "Ngày tạo", render: (row) => row.created_at ? date(row.created_at) : "—" },
            { title: "Lượt", render: (row) => row.units },
            { title: "Cổng", render: (row) => <Status value={row.provider} /> },
            { title: "Trạng thái", render: (row) => <Status value={row.state} /> },
            { title: "Tổng", render: (row) => money(row.amount_vnd) },
          ]} /></LoadBoundary>}
        </div>
      </section>
      {eventProduct && <div className="pa-event-drawer-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) closeEventDrawer(); }}>
        <aside className="pa-event-drawer" role="dialog" aria-modal="true" aria-labelledby="pa-event-drawer-title">
          <header className="pa-event-drawer-header">
            <div><h2 id="pa-event-drawer-title">Lịch sử hạn mức</h2><p>{eventProduct.display_name}</p><code>{eventProduct.product_id}</code></div>
            <Button onClick={closeEventDrawer}>Đóng</Button>
          </header>
          {eventLoading ? <p className="pa-event-drawer-state" role="status">Đang tải lịch sử sự kiện…</p>
            : eventError ? <div className="pa-event-drawer-state" role="alert"><p>{eventError}</p><Button onClick={() => loadProductEvents(eventProduct)}>Thử lại</Button></div>
              : eventItems?.length === 0 ? <p className="pa-event-drawer-state">Chưa có sự kiện nào cho gói này.</p>
                : eventItems && <>
                  <p className="pa-muted">{eventTotal.toLocaleString("vi-VN")} sự kiện</p>
                  <div className="pa-event-drawer-table-wrap">
                    <table className="pa-table">
                      <thead><tr><th>Thời gian</th><th>Thao tác</th><th>Người thực hiện</th><th>Mã gói</th><th>Ảnh chụp</th></tr></thead>
                      <tbody>{eventItems.map((item) => <tr key={item.event_id}>
                        <td>{date(item.created_at)}</td>
                        <td>{item.action}</td>
                        <td>{short(item.actor_ref)}</td>
                        <td>{item.offer_id}</td>
                        <td><details className="pa-event-snapshot"><summary>Chi tiết</summary>
                          {Object.keys(item.snapshot ?? {}).length === 0 ? <p>Không có dữ liệu</p> : <dl>{Object.entries(item.snapshot ?? {}).map(([key, value]) => {
                            const fullValue = snapshotValue(value);
                            const truncated = fullValue.length > 240 ? fullValue.slice(0, 237) + "…" : fullValue;
                            const shortKey = key.length > 120 ? key.slice(0, 117) + "…" : key;
                            return <div key={`${key}-${shortKey}`}><dt>{shortKey}</dt><dd>{truncated}</dd></div>;
                          })}</dl>}
                        </details></td>
                      </tr>)}</tbody>
                    </table>
                  </div>
                </>}
        </aside>
      </div>}
    </div>
  );
}

function snapshotValue(value: unknown): string {
  if (typeof value === "string") return value;
  try {
    const serialized = JSON.stringify(value);
    return serialized === undefined ? String(value) : serialized;
  } catch {
    return String(value);
  }
}

function QuotaWorkspace({ initialScope }: { initialScope?: Scope }) {
  const [scope, setScope] = useState<Scope>(initialScope ?? {
      owner_kind: "ORGANIZATION",
      owner_ref: "",
    }),
    [units, setUnits] = useState(10),
    [admission, setAdmission] = useState(createIdempotencyKey);
  const q = useAdminQuery(
      () =>
        scope.owner_ref
          ? read<Quota>("/billing/sandbox/quota" + query(scope))
          : Promise.resolve(null),
      JSON.stringify(scope),
    ),
    cmd = useAdminCommand();
  return (
    <>
      <Feedback {...cmd} />
      <section className="pa-panel pa-padded">
        <ScopeFields value={scope} onChange={setScope} />
      </section>
      {!scope.owner_ref && <Empty text="Chưa chọn phạm vi hạn mức" detail="Chọn trường học hoặc tài khoản phụ huynh ở phía trên để xem số lượt đã cấp, đã dùng và còn lại." />}
      {scope.owner_ref && (
        <LoadBoundary {...q}>
          {q.data && (
            <>
              <div className="pa-quota-summary">
                <div>
                  <p>Hạn mức còn lại</p>
                  <strong>
                    {q.data.available_units}
                    <small> lượt video</small>
                  </strong>
                </div>
                <Refresh onClick={q.reload} />
              </div>
              <section className="pa-panel">
                <Table
                  items={q.data.grants}
                  rowKey={(r) => r.grant_id}
                  emptyText="Chưa có hạn mức được cấp"
                  emptyDetail="Hạn mức sẽ hiển thị sau khi được cấp cho phạm vi đã chọn."
                  columns={[
                    {
                      title: "Nguồn hạn mức",
                      render: (r) => <Status value={r.kind} />,
                    },
                    { title: "Đã cấp", render: (r) => r.units },
                    { title: "Đã dùng", render: (r) => r.used },
                    {
                      title: "Còn lại",
                      render: (r) => Math.max(0, r.units - r.used),
                    },
                    {
                      title: "Hết hạn",
                      render: (r) =>
                        r.expires_at ? date(r.expires_at) : "Không hết hạn",
                    },
                  ]}
                />
              </section>
              <div className="pa-two-column">
                <section className="pa-panel pa-padded">
                  <h2>Cấp hạn mức tháng thử nghiệm</h2>
                  <p className="pa-muted">
                    Mỗi phạm vi chỉ nhận một lần trong tháng theo giờ Việt Nam.
                  </p>
                  <Form
                    onSubmit={() =>
                      cmd.run(
                        () =>
                          cmd.send("/billing/sandbox/included-grants", {
                            ...scope,
                            units,
                          }),
                        q.reload,
                      )
                    }
                  >
                    <Field label="Số lượt video">
                      <input
                        required
                        type="number"
                        min={1}
                        max={100000}
                        value={units}
                        onChange={(e) => setUnits(e.target.valueAsNumber)}
                      />
                    </Field>
                    <Button primary type="submit" disabled={cmd.busy}>
                      Cấp hạn mức thử nghiệm
                    </Button>
                  </Form>
                </section>
                <section className="pa-panel pa-padded">
                  <h2>Kiểm tra trừ hạn mức</h2>
                  <p className="pa-muted">
                    Trừ một lượt trong sổ hạn mức thử nghiệm. Không tạo video hoặc gọi
                    AI.
                  </p>
                  <Button
                    disabled={cmd.busy || q.data.available_units < 1}
                    onClick={() =>
                      cmd.run(
                        () =>
                          cmd.send("/billing/sandbox/consume", {
                            ...scope,
                            admission_ref: admission,
                          }),
                        () => {
                          setAdmission(createIdempotencyKey());
                          q.reload();
                        },
                      )
                    }
                  >
                    Dùng thử 1 lượt
                  </Button>
                  <p>
                    <Link to="?panel=billing">Tạo hóa đơn mua thêm →</Link>
                  </p>
                </section>
              </div>
            </>
          )}
        </LoadBoundary>
      )}
    </>
  );
}
type Price = {
  price_id: string;
  cycle_months: number;
  base_amount_vnd: number;
  slot_amount_vnd: number;
};
type Quote = { invoice_id: string; amount_vnd: number };
type ClassOption = { class_id: string; display_name: string };
export function CapacityPage() {
  return (
    <div className="pa-page pa-capacity-page">
      <Heading
        title="Sức chứa lớp học"
        description="Quản lý bảng giá và cấp gói mở rộng số lớp cho từng trường học."
      >
        <span className="pa-sandbox-badge">Chạy thử</span>
      </Heading>
      <SandboxGate>
        <CapacityWorkspace />
      </SandboxGate>
    </div>
  );
}
function CapacityWorkspace() {
  const [org, setOrg] = useState(""),
    [price, setPrice] = useState(""),
    [slots, setSlots] = useState(0),
    [cycle, setCycle] = useState(1),
    [base, setBase] = useState(200000),
    [slotPrice, setSlotPrice] = useState(20000),
    [showPrice, setShowPrice] = useState(false),
    [selected, setSelected] = useState<Subscription | null>(null),
    [mode, setMode] = useState("ADDON"),
    [suspended, setSuspended] = useState<string[]>([]),
    [quote, setQuote] = useState<Quote | null>(null);
  const pagination = useAdminCursor("sandbox-capacity-subscriptions");
  const q = useAdminQuery(
      () =>
        read<Page<Subscription>>(
          "/billing/sandbox/subscriptions" + query({ cursor: pagination.cursor, limit: 25 }),
        ),
      JSON.stringify(["sandbox-capacity-subscriptions", pagination.cursor]),
    ),
    schools = useAdminQuery(
      () => readAllPages<Organization>("/organizations"),
      "capacity-schools",
    ),
    prices = useAdminQuery(
      () => readAllPages<Price>("/billing/sandbox/capacity-prices"),
      "prices",
    ),
    classes = useAdminQuery(
      () =>
        selected
          ? readAllPages<ClassOption>(
              "/organizations/" + selected.organization_ref + "/capacity-classes",
            )
          : Promise.resolve({ items: [] }),
      selected?.subscription_id ?? "",
    ),
    cmd = useAdminCommand();
  const schoolName = (id: string) =>
    schools.data?.items.find((s) => s.organization_id === id)?.display_name ??
    short(id);
  function refresh() {
    q.reload();
    prices.reload();
  }
  const subscriptions = q.data?.items ?? [];
  const priceItems = prices.data?.items ?? [];
  const noPrices = prices.data !== undefined && priceItems.length === 0;
  return (
    <>
      <Feedback {...cmd} />
      {quote && (
        <aside className="pa-notice" role="status" aria-live="polite">
          Đã tạo hóa đơn thử nghiệm {short(quote.invoice_id)} ·{" "}
          {money(quote.amount_vnd)}.{" "}
          <Link to="?panel=billing">Mở đối soát để thanh toán →</Link>
        </aside>
      )}
      <div className="pa-toolbar pa-capacity-toolbar">
        <Button onClick={() => setShowPrice(!showPrice)}>
          {showPrice ? "Đóng biểu mẫu bảng giá" : "+ Thêm bảng giá"}
        </Button>
        <Refresh onClick={refresh} />
      </div>
      {showPrice && (
        <section className="pa-panel pa-padded pa-capacity-card">
          <div className="pa-capacity-card-head">
            <span className="pa-capacity-card-icon" aria-hidden="true">
              <Tags size={19} />
            </span>
            <div>
              <h2>Bảng giá mới</h2>
              <p>Thiết lập chu kỳ thanh toán, phí gói cơ bản và đơn giá mỗi lớp bổ sung.</p>
            </div>
          </div>
          <Form
            onSubmit={() =>
              cmd.run(
                () =>
                  cmd.send("/billing/sandbox/capacity-prices", {
                    cycle_months: cycle,
                    base_amount_vnd: base,
                    slot_amount_vnd: slotPrice,
                  }),
                () => {
                  setShowPrice(false);
                  prices.reload();
                },
              )
            }
          >
            <div className="pa-form-grid pa-capacity-form-grid">
              <Field label="Chu kỳ">
                <AdminSelect
                  value={cycle}
                  onChange={(e) => setCycle(Number(e.target.value))}
                >
                  <option value={1}>Theo tháng</option>
                  <option value={12}>Theo năm</option>
                </AdminSelect>
              </Field>
              <Field
                label="Giá cơ bản (VND)"
                hint="Áp dụng cho 10 lớp cơ bản trong chu kỳ đã chọn."
              >
                <input
                  required
                  type="number"
                  min={1}
                  max={2000000000}
                  value={base}
                  onChange={(e) => setBase(e.target.valueAsNumber)}
                />
              </Field>
              <Field label="Giá mỗi lớp bổ sung (VND)">
                <input
                  required
                  type="number"
                  min={1}
                  max={2000000000}
                  value={slotPrice}
                  onChange={(e) => setSlotPrice(e.target.valueAsNumber)}
                />
              </Field>
            </div>
            <div className="pa-actions">
              <Button primary type="submit" disabled={cmd.busy}>
                Lưu bảng giá
              </Button>
              <Button disabled={cmd.busy} onClick={() => setShowPrice(false)}>
                Hủy
              </Button>
            </div>
          </Form>
        </section>
      )}
      <section className="pa-panel pa-padded pa-capacity-card">
        <div className="pa-capacity-card-head">
          <span className="pa-capacity-card-icon" aria-hidden="true">
            <School size={19} />
          </span>
          <div>
            <h2>
              {selected
                ? "Điều chỉnh gói của " + schoolName(selected.organization_ref)
                : "Đăng ký gói sức chứa"}
            </h2>
            <p>
              {selected
                ? "Chọn hình thức điều chỉnh và số lớp bổ sung cho gói đang hoạt động."
                : "Chọn trường học, bảng giá và số lớp bổ sung để tạo báo giá cho trường."}
            </p>
          </div>
        </div>
        <Form
          onSubmit={() =>
            cmd.run(
              () =>
                selected
                  ? mode === "downgrade"
                    ? cmd.send(
                        "/billing/sandbox/subscriptions/" +
                          selected.subscription_id,
                        {
                          action: "downgrade",
                          addon_slots: slots,
                          suspend_class_refs: suspended,
                        },
                        selected.revision,
                        "PATCH",
                      )
                    : cmd.send<Quote>(
                        "/billing/sandbox/subscriptions/" +
                          selected.subscription_id +
                          "/quote",
                        { mode, addon_slots: slots },
                        selected.revision,
                      )
                  : cmd.send<Quote>("/billing/sandbox/subscriptions/quote", {
                      mode: "START",
                      organization_ref: org,
                      price_id: price,
                      addon_slots: slots,
                    }),
              (r) => {
                if (r && typeof r === "object" && "invoice_id" in r)
                  setQuote(r as Quote);
                setSelected(null);
                pagination.reset();
                refresh();
              },
            )
          }
        >
          <div className="pa-form-grid pa-capacity-form-grid">
            {selected ? (
              <Field label="Điều chỉnh">
                <AdminSelect
                  value={mode}
                  onChange={(e) => {
                    setMode(e.target.value);
                    setSuspended([]);
                  }}
                >
                  <option value="ADDON">Tăng sức chứa</option>
                  <option value="RENEW">Gia hạn</option>
                  <option value="downgrade">Hạ sức chứa vào kỳ sau</option>
                </AdminSelect>
              </Field>
            ) : (
              <>
                <LoadBoundary {...schools}>
                  <Field label="Trường học">
                    <AdminSelect
                      required
                      className={!org ? "is-placeholder" : undefined}
                      value={org}
                      onChange={(e) => setOrg(e.target.value)}
                    >
                      <option value="">Chọn trường học</option>
                      {schools.data?.items.map((s) => (
                        <option
                          key={s.organization_id}
                          value={s.organization_id}
                        >
                          {s.display_name}
                        </option>
                      ))}
                    </AdminSelect>
                  </Field>
                </LoadBoundary>
                <LoadBoundary {...prices}>
                  <Field
                    label="Bảng giá"
                    hint={
                      noPrices
                        ? 'Chưa có bảng giá nào. Nhấn "+ Thêm bảng giá" ở phía trên để tạo trước.'
                        : undefined
                    }
                  >
                    <AdminSelect
                      required
                      className={!price ? "is-placeholder" : undefined}
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                    >
                      <option value="">
                        {noPrices
                          ? "Chưa có bảng giá — nhấn + Thêm bảng giá"
                          : "Chọn bảng giá"}
                      </option>
                      {priceItems.map((p) => (
                        <option key={p.price_id} value={p.price_id}>
                          {p.cycle_months === 1 ? "Tháng" : "Năm"} ·{" "}
                          {money(p.base_amount_vnd)} +{" "}
                          {money(p.slot_amount_vnd)}/lớp
                        </option>
                      ))}
                    </AdminSelect>
                  </Field>
                </LoadBoundary>
              </>
            )}
            {mode !== "RENEW" && (
              <Field
                label="Số lớp bổ sung"
                hint="Ngoài 10 lớp cơ bản được cấp sẵn (từ 0 đến 1.000 lớp)."
              >
                <input
                  required
                  type="number"
                  min={0}
                  max={1000}
                  value={slots}
                  onChange={(e) => setSlots(e.target.valueAsNumber)}
                />
              </Field>
            )}
          </div>
          {selected && mode === "downgrade" && (
            <LoadBoundary {...classes}>
              <fieldset className="pa-class-options">
                <legend>Chọn lớp tạm ngưng khi gói mới có hiệu lực</legend>
                <p className="pa-muted">
                  Cần chọn{" "}
                  {Math.max(
                    0,
                    (classes.data?.items.length ?? 0) - (10 + slots),
                  )}{" "}
                  lớp. Dữ liệu và lịch sử được giữ lại.
                </p>
                {classes.data?.items.map((c) => (
                  <label key={c.class_id}>
                    <input
                      type="checkbox"
                      checked={suspended.includes(c.class_id)}
                      onChange={(e) =>
                        setSuspended((old) =>
                          e.target.checked
                            ? [...old, c.class_id]
                            : old.filter((id) => id !== c.class_id),
                        )
                      }
                    />
                    {c.display_name}
                  </label>
                ))}
              </fieldset>
            </LoadBoundary>
          )}
          <div className="pa-actions">
            <Button
              primary
              type="submit"
              disabled={cmd.busy || (!selected && (!org || !price))}
            >
              {mode === "downgrade" && selected
                ? "Xác nhận hạ sức chứa"
                : "Tạo báo giá cho trường"}
            </Button>
            {selected && (
              <Button
                onClick={() => {
                  setSelected(null);
                  setMode("ADDON");
                }}
              >
                Hủy
              </Button>
            )}
          </div>
        </Form>
      </section>
      <LoadBoundary {...q}>
        <section className="pa-panel pa-capacity-table-panel" aria-label="Danh sách gói sức chứa">
          <div className="pa-capacity-list-head">
            <div className="pa-capacity-list-title">
              <span className="pa-capacity-card-icon" aria-hidden="true">
                <Layers size={19} />
              </span>
              <div>
                <h2>Danh sách gói sức chứa</h2>
                <p>Theo dõi sức chứa lớp học, trạng thái và kỳ gia hạn của từng trường.</p>
              </div>
            </div>
            <span className="pa-capacity-count">
              {q.data?.total ?? subscriptions.length} gói
            </span>
          </div>
          {subscriptions.length > 0 ? (
            <Table
              className="pa-capacity-table-scroll"
              caption="Danh sách gói sức chứa lớp học"
              items={subscriptions}
              rowKey={(r) => r.subscription_id}
              columns={[
                {
                  title: "Trường học",
                  render: (r) => (
                    <strong>{schoolName(r.organization_ref)}</strong>
                  ),
                },
                {
                  title: "Sức chứa",
                  render: (r) => (
                    <>
                      {r.capacity} lớp
                      {r.scheduled_addon_slots !== null && (
                        <small>Kỳ sau: {10 + r.scheduled_addon_slots} lớp</small>
                      )}
                    </>
                  ),
                },
                {
                  title: "Trạng thái",
                  render: (r) => <Status value={r.state} />,
                },
                { title: "Hết kỳ", render: (r) => date(r.period_end) },
                {
                  title: "Thao tác",
                  render: (r) => (
                    <div className="pa-actions">
                      <Button
                        disabled={cmd.busy}
                        onClick={() => {
                          setSelected(r);
                          setSlots(r.addon_slots + 1);
                          setMode("ADDON");
                          setSuspended([]);
                        }}
                      >
                        Điều chỉnh
                      </Button>
                      <Button
                        disabled={cmd.busy}
                        onClick={() =>
                          cmd.run(
                            () =>
                              cmd.send(
                                "/billing/sandbox/subscriptions/" +
                                  r.subscription_id,
                                {
                                  action:
                                    r.state === "CANCEL_AT_PERIOD_END"
                                      ? "resume_renewal"
                                      : "cancel_renewal",
                                },
                                r.revision,
                                "PATCH",
                              ),
                            refresh,
                          )
                        }
                      >
                        {r.state === "CANCEL_AT_PERIOD_END"
                          ? "Tiếp tục gia hạn"
                          : "Dừng gia hạn"}
                      </Button>
                    </div>
                  ),
                },
              ]}
            />
          ) : (
            <Empty
              text="Chưa có gói sức chứa"
              detail="Chọn trường học và bảng giá ở biểu mẫu trên để tạo báo giá cho gói đầu tiên."
            />
          )}
          <CursorPager
            page={pagination.page}
            count={subscriptions.length}
            nextCursor={q.data?.next_cursor}
            onNext={pagination.next}
            onPrevious={pagination.back}
          />
        </section>
      </LoadBoundary>
    </>
  );
}
