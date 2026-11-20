import { AdminSelect } from '../components/AdminSelect'
import { useState } from "react";
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
  type Quota,
  type Subscription,
  readAllPages,
} from "../services/adminService";
import { useAdminQuery, useAdminCommand, useAdminCursor, money, date, short } from '../components/adminHooks'
import { Heading, Button, Field, Form, Feedback, LoadBoundary, Table, Refresh, CursorPager, Status, Empty } from '../components/AdminUI'

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
              Thao tác chỉ ghi nhận giao dịch test, không thu tiền thật.
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
      <Heading
        title="Đối soát thanh toán"
      />
      <SandboxGate>
        <BillingWorkspace />
      </SandboxGate>
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
            + Tạo hóa đơn test
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
              <Field label="Giá test (VND)">
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
              Tạo gói test
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
          <h2>Xác nhận giao dịch test</h2>
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
                {paid ? "Ghi nhận đã thanh toán test" : "Ghi nhận thất bại"}
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
            emptyDetail="Tạo hóa đơn test để kiểm tra quy trình đối soát; không phát sinh thanh toán thật."
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
export function QuotaPage() {
  return (
    <div className="pa-page">
      <Heading
        title="Hạn mức video"
      />
      <SandboxGate>
        <QuotaWorkspace />
      </SandboxGate>
    </div>
  );
}
function QuotaWorkspace() {
  const [scope, setScope] = useState<Scope>({
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
                  <h2>Cấp hạn mức tháng test</h2>
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
                      Cấp hạn mức test
                    </Button>
                  </Form>
                </section>
                <section className="pa-panel pa-padded">
                  <h2>Kiểm tra trừ hạn mức</h2>
                  <p className="pa-muted">
                    Trừ một lượt trong sổ hạn mức test. Không tạo video hoặc gọi
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
    <div className="pa-page">
      <Heading
        title="Sức chứa lớp học"
      />
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
  return (
    <>
      <Feedback {...cmd} />
      {quote && (
        <aside className="pa-notice" role="status">
          Đã tạo hóa đơn test {short(quote.invoice_id)} ·{" "}
          {money(quote.amount_vnd)}.{" "}
          <Link to="?panel=billing">Mở đối soát để thanh toán →</Link>
        </aside>
      )}
      <div className="pa-toolbar">
        <Button onClick={() => setShowPrice(!showPrice)}>
          + Tạo bảng giá test
        </Button>
        <Refresh onClick={refresh} />
      </div>
      {showPrice && (
        <section className="pa-panel pa-padded">
          <h2>Bảng giá mới</h2>
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
            <div className="pa-form-grid">
              <Field label="Chu kỳ">
                <AdminSelect
                  value={cycle}
                  onChange={(e) => setCycle(Number(e.target.value))}
                >
                  <option value={1}>Theo tháng</option>
                  <option value={12}>Theo năm</option>
                </AdminSelect>
              </Field>
              <Field label="Giá cơ bản test (10 lớp)">
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
            <Button primary type="submit" disabled={cmd.busy}>
              Lưu bảng giá test
            </Button>
          </Form>
        </section>
      )}
      <section className="pa-panel pa-padded">
        <h2>
          {selected
            ? "Điều chỉnh gói của " + schoolName(selected.organization_ref)
            : "Đăng ký gói test"}
        </h2>
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
          <div className="pa-form-grid">
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
                  <Field label="Bảng giá">
                    <AdminSelect
                      required
                      value={price}
                      onChange={(e) => setPrice(e.target.value)}
                    >
                      <option value="">Chọn bảng giá test</option>
                      {prices.data?.items.map((p) => (
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
              <Field label="Tổng số lớp bổ sung (ngoài 10 lớp cơ bản)">
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
                : "Tạo báo giá test"}
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
        <section className="pa-panel">
          <Table
            items={q.data?.items ?? []}
            rowKey={(r) => r.subscription_id}
            emptyText="Chưa có gói sức chứa"
            emptyDetail="Đăng ký gói test cho một trường để theo dõi sức chứa lớp học."
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
          <CursorPager
            page={pagination.page}
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
