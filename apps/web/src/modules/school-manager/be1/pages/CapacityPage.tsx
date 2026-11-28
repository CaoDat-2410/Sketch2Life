import { useCallback, useEffect, useRef, useState } from "react";
import { Gauge, RefreshCw } from "lucide-react";
import { createIdempotencyKey } from "../../../../shared/api/backendApi";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { Button } from "../../../../shared/ui";
import { AdminBe1Error } from "../services/be1Client";
import { capacityService, safeCapacityCheckoutUrl, type Be1OrganizationCapacity, type CapacityCommand, type CapacityQuote, type CapacityPurchase } from "../services/capacityService";
import { classService, type Be1Class } from "../services/classService";
import { managerBusinessService, type Be1Organization } from "../services/managerBusinessService";

type ConfirmAction = "cancel_renewal" | "downgrade" | null;
type CapacityPageData = { organization: Be1Organization; capacity: Be1OrganizationCapacity };

function number(value: number) {
  return new Intl.NumberFormat("vi-VN").format(value);
}

function formatDate(value: string | null, withTime = false) {
  if (!value || !Number.isFinite(Date.parse(value))) return "Chưa có thông tin";
  return new Date(value).toLocaleString("vi-VN", withTime
    ? { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }
    : { day: "2-digit", month: "2-digit", year: "numeric" });
}

function checkoutLink(value: string | null): string | null {
  if (!value) return null;
  try { return safeCapacityCheckoutUrl(value); } catch { return null; }
}

function purchaseLabel(item: CapacityPurchase) {
  if (item.state === "PAID") return item.activated ? "Đã kích hoạt" : "Đã thanh toán, chờ xử lý thủ công";
  const labels: Record<string, string> = {
    PENDING: "Đang chờ thanh toán", FAILED: "Thanh toán thất bại", CANCELED: "Đã hủy",
  };
  return labels[item.state] ?? "Trạng thái chưa xác định";
}

function purchaseKindLabel(kind: CapacityPurchase["kind"]) {
  const labels: Record<CapacityPurchase["kind"], string> = {
    START: "Đăng ký gói",
    RENEW: "Gia hạn gói",
    ADDON: "Mua thêm slot",
  };
  return labels[kind];
}

function attemptLabel(state: string) {
  const labels: Record<string, string> = {
    REQUESTING: "Đang tạo yêu cầu", OPEN: "Đang chờ thanh toán", UNKNOWN: "Chờ xác minh",
    FAILED: "Thanh toán thất bại", CANCELED: "Đã hủy", PAID: "Đã thanh toán",
  };
  return labels[state] ?? "Trạng thái chưa xác định";
}

function providerLabel(provider: string) {
  return provider === "MOMO" ? "MoMo" : provider === "VNPAY" ? "VNPay" : provider === "SANDBOX" ? "Thử nghiệm (quản trị)" : "Cổng thanh toán chưa xác định";
}

function supportsPurchaseActions(provider: string) {
  return provider === "MOMO" || provider === "VNPAY";
}

function subscriptionLabel(state: string) {
  const labels: Record<string, string> = {
    NONE: "Chưa có gói",
    ACTIVE: "Đang hoạt động",
    GRACE: "Đang trong thời gian gia hạn",
    CANCEL_AT_PERIOD_END: "Đã tắt gia hạn cuối kỳ",
  };
  return labels[state] ?? "Trạng thái chưa xác định";
}

function errorText(cause: unknown) {
  if (cause instanceof AdminBe1Error) {
    if (cause.status === 403 || cause.status === 404) return "Không có quyền hoặc không tìm thấy thông tin sức chứa.";
    if (cause.code === "DOWNGRADE_SCHEDULED") return "Đã lên lịch hạ sức chứa; chưa thể mua thêm slot trong kỳ này.";
    if (cause.code === "PAYMENT_ATTEMPT_ALREADY_OPEN") return "Đã có đơn mua slot đang chờ; hãy kiểm tra trạng thái đơn đó.";
    if (cause.code === "SUBSCRIPTION_REQUIRED" || cause.code === "SUBSCRIPTION_NOT_ACTIVE") return "Cần có gói đang hoạt động để mua thêm slot.";
    if (cause.code === "MOMO_AMOUNT_OUT_OF_RANGE" || cause.code === "VNPAY_AMOUNT_OUT_OF_RANGE") return "Số tiền nằm ngoài giới hạn của cổng thanh toán.";
    if (cause.code === "STALE_REVISION") return "Thông tin sức chứa đã thay đổi. Hãy xem lại trước khi xác nhận.";
    if (cause.code === "SUBSCRIPTION_PERIOD_ENDED") return "Kỳ gói đã kết thúc. Hãy tải lại thông tin sức chứa.";
    if (cause.code === "CLASS_SELECTION_REQUIRED") return "Hãy chọn đủ số lớp cần tạm ngưng trước khi xác nhận.";
    if (cause.code === "INVALID_CAPACITY_DOWNGRADE") return "Mức sức chứa hoặc danh sách lớp chưa hợp lệ. Hãy kiểm tra lại lựa chọn.";
    if (cause.code === "INVALID_IDEMPOTENCY_KEY") return "Không thể gửi thao tác này. Hãy thử lại.";
    if (cause.status === 503 || cause.code === "DEPENDENCY_UNAVAILABLE") return "Dịch vụ thanh toán đang tạm thời chưa sẵn sàng. Hãy thử lại sau.";
    if (cause.status === 400 || cause.status === 422) return "Yêu cầu chưa hợp lệ. Hãy kiểm tra lại lựa chọn.";
  }
  return "Không thể tải hoặc cập nhật sức chứa lúc này. Hãy thử lại sau.";
}

function emptyCapacityMessage(cause: unknown) {
  return cause instanceof AdminBe1Error
    ? errorText(cause)
    : "Không thể tải hoặc cập nhật sức chứa lúc này. Hãy thử lại sau.";
}

export function CapacityPage() {
  const [pageData, setPageData] = useState<CapacityPageData | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [commandError, setCommandError] = useState("");
  const [notice, setNotice] = useState("");
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);
  const [downgradeOpen, setDowngradeOpen] = useState(false);
  const [loadingClasses, setLoadingClasses] = useState(false);
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [classLoadError, setClassLoadError] = useState("");
  const [addonSlots, setAddonSlots] = useState("");
  const [selectedClassRefs, setSelectedClassRefs] = useState<string[]>([]);
  const [purchaseQuantity, setPurchaseQuantity] = useState("1");
  const [quote, setQuote] = useState<CapacityQuote | null>(null);
  const [purchases, setPurchases] = useState<CapacityPurchase[]>([]);
  const [provider, setProvider] = useState<"MOMO" | "VNPAY">("MOMO");
  const actionKeys = useRef(new Map<string, string>());

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const organization = await managerBusinessService.organization(signal);
      const result = await capacityService.getCapacity(organization.organization_id, signal);
      if (!signal?.aborted) {
        setPageData({ organization, capacity: result.data });
        const returnedInvoice = new URLSearchParams(window.location.search).get("invoice");
        void Promise.all([
          capacityService.purchases(organization.organization_id),
          returnedInvoice ? capacityService.purchases(organization.organization_id, returnedInvoice) : Promise.resolve([]),
        ]).then(([recent, returned]) => {
          if (!signal?.aborted) setPurchases([...returned, ...recent.filter(item => !returned.some(match => match.invoice_id === item.invoice_id))]);
        }).catch(() => { if (!signal?.aborted) setCommandError("Không tải được lịch sử mua slot. Hãy tải lại."); });
        setError("");
      }
    } catch (cause) {
      if (!signal?.aborted) {
        setPageData(null);
        setError(emptyCapacityMessage(cause));
      }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const refresh = () => {
    setLoading(true);
    setError("");
    setCommandError("");
    setNotice("");
    void load();
  };

  const clearActionKeys = () => actionKeys.current.clear();
  const data = pageData?.capacity ?? null;
  const organization = pageData?.organization ?? null;
  const hasSubscription = Boolean(data?.subscription_id && data.subscription_state !== "NONE");
  const canManageRenewal = data?.subscription_state === "ACTIVE" || data?.subscription_state === "GRACE";
  const canResumeRenewal = data?.subscription_state === "CANCEL_AT_PERIOD_END";

  const activeAddonValue = addonSlots.trim() !== "" && /^\d+$/.test(addonSlots) ? Number(addonSlots) : null;
  const targetCapacity = activeAddonValue === null ? null : 10 + activeAddonValue;
  const validDowngrade = Boolean(
    data
    && activeAddonValue !== null
    && activeAddonValue <= 1000
    && targetCapacity !== null
    && targetCapacity < data.capacity,
  );
  const classesToSuspend = validDowngrade && data && targetCapacity !== null
    ? Math.max(0, data.active_class_count - targetCapacity)
    : 0;
  const hasEnoughClasses = classes.length >= (data?.active_class_count ?? 0);
  const exactSelection = selectedClassRefs.length === classesToSuspend;

  const loadActiveClasses = async () => {
    setLoadingClasses(true);
    setClassLoadError("");
    try {
      const result = await classService.listClasses("active");
      setClasses(result.filter((item) => item.state === "active"));
    } catch {
      setClassLoadError("Không tải được danh sách lớp. Hãy thử lại.");
    } finally {
      setLoadingClasses(false);
    }
  };

  const openDowngrade = () => {
    if (!data) return;
    setAddonSlots(String(Math.max(0, Math.min(1000, data.capacity - 11))));
    setSelectedClassRefs([]);
    setClasses([]);
    setClassLoadError("");
    setCommandError("");
    setNotice("");
    setConfirmAction(null);
    setDowngradeOpen(true);
    clearActionKeys();
    void loadActiveClasses();
  };

  const reloadAfterStale = async () => {
    setConfirmAction(null);
    setDowngradeOpen(false);
    setClasses([]);
    setSelectedClassRefs([]);
    setLoading(true);
    setError("");
    await load();
    setCommandError("Thông tin sức chứa đã thay đổi. Hãy xem lại trước khi xác nhận.");
  };

  const configure = async (action: "cancel_renewal" | "resume_renewal" | "downgrade") => {
    if (!data || !organization || busy) return;
    let body: CapacityCommand;
    let signature: string;
    if (action === "downgrade") {
      if (!validDowngrade || !exactSelection || !hasEnoughClasses || activeAddonValue === null) return;
      const refs = classes.filter((item) => selectedClassRefs.includes(item.class_id)).map((item) => item.class_id);
      body = { action, addon_slots: activeAddonValue, suspend_class_refs: refs };
      signature = "downgrade:" + JSON.stringify([activeAddonValue, refs]);
    } else {
      body = { action };
      signature = action;
    }
    const key = actionKeys.current.get(signature) ?? createIdempotencyKey();
    actionKeys.current.set(signature, key);
    setBusy(true);
    setCommandError("");
    setNotice("");
    try {
      const result = await capacityService.configureCapacity(organization.organization_id, data.revision, body, key);
      actionKeys.current.delete(signature);
      setPageData((current) => current ? { ...current, capacity: result.data } : current);
      setConfirmAction(null);
      setDowngradeOpen(false);
      setSelectedClassRefs([]);
      setNotice(action === "cancel_renewal"
        ? "Đã tắt gia hạn. Gói hiện tại còn hiệu lực đến hết kỳ."
        : action === "resume_renewal"
          ? "Đã bật lại gia hạn cho kỳ tiếp theo."
          : "Đã lên lịch hạ sức chứa vào cuối kỳ.");
    } catch (cause) {
      if (cause instanceof AdminBe1Error && cause.status >= 400 && cause.status < 500) {
        actionKeys.current.delete(signature);
      }
      if (cause instanceof AdminBe1Error && cause.code === "STALE_REVISION") {
        actionKeys.current.delete(signature);
        await reloadAfterStale();
      } else {
        setCommandError(errorText(cause));
      }
    } finally {
      setBusy(false);
    }
  };

  const refreshPurchases = async () => {
    if (organization) setPurchases(await capacityService.purchases(organization.organization_id));
  };
  const showQuote = async () => {
    if (!organization || busy) return;
    setBusy(true); setCommandError(""); setQuote(null);
    try {
      const result = await capacityService.quote(organization.organization_id, Number(purchaseQuantity));
      setQuote(result); setProvider(result.momo_checkout_enabled ? "MOMO" : "VNPAY");
    } catch (cause) { setCommandError(errorText(cause)); } finally { setBusy(false); }
  };
  const buy = async () => {
    if (!organization || !quote || busy) return;
    const signature = JSON.stringify(["purchase", quote.quantity, provider, quote.price_id, quote.period_end, quote.quoted_at, quote.amount_vnd]);
    const key = actionKeys.current.get(signature) ?? createIdempotencyKey();
    actionKeys.current.set(signature, key); setBusy(true); setCommandError("");
    try {
      const result = await capacityService.checkout(organization.organization_id, quote, provider, key);
      if (result.state !== "PENDING") actionKeys.current.delete(signature);
      if (result.state === "PENDING" && result.checkout_url) window.location.assign(result.checkout_url);
      else {
        await refreshPurchases();
        setNotice(result.state === "PENDING" ? "Đơn đang chờ cổng xác nhận. Hãy kiểm tra trạng thái." : "Hãy kiểm tra trạng thái giao dịch bên dưới.");
      }
    } catch (cause) {
      if (cause instanceof AdminBe1Error && cause.status >= 400 && cause.status < 500) actionKeys.current.delete(signature);
      if (cause instanceof AdminBe1Error && cause.status === 409 && cause.code === "CAPACITY_QUOTE_CHANGED") {
        setQuote(null);
        try {
          const updated = await capacityService.quote(organization.organization_id, quote.quantity);
          setQuote(updated);
          setProvider(updated.momo_checkout_enabled ? "MOMO" : "VNPAY");
          setCommandError("Báo giá đã thay đổi. Hãy xem lại số tiền mới và bấm thanh toán để xác nhận lại.");
        } catch (refreshError) { setCommandError(errorText(refreshError)); }
      } else setCommandError(errorText(cause));
    } finally { setBusy(false); }
  };
  const purchaseAction = async (invoiceId: string, action: "reconcile" | "cancel") => {
    if (!organization || busy) return;
    setBusy(true); setCommandError("");
    try { await capacityService.purchaseAction(organization.organization_id, invoiceId, action); actionKeys.current.clear(); await refreshPurchases(); await load(); }
    catch (cause) { setCommandError(errorText(cause)); } finally { setBusy(false); }
  };

  const toggleClass = (classId: string, checked: boolean) => {
    clearActionKeys();
    setCommandError("");
    setNotice("");
    setConfirmAction(null);
    setSelectedClassRefs((current) => checked
      ? current.includes(classId) || current.length >= classesToSuspend ? current : [...current, classId]
      : current.filter((item) => item !== classId));
  };

  const updateAddonSlots = (value: string) => {
    clearActionKeys();
    setCommandError("");
    setNotice("");
    setConfirmAction(null);
    setSelectedClassRefs([]);
    setAddonSlots(value);
  };

  return (
    <div className="s2l-page manager-business-page manager-capacity-page">
      <PageHeading
        eyebrow="Quản lý trường"
        title="Sức chứa lớp"
        description={organization?.display_name ?? "Theo dõi sức chứa và trạng thái gói của trường."}
        action={<button type="button" className="manager-business-button" onClick={refresh} disabled={loading || busy}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>}
      />

      {error && <section className="manager-quota-alert" role="alert"><strong>Không tải được sức chứa</strong><span>{error}</span><button type="button" onClick={refresh} disabled={loading}>Thử lại</button></section>}
      {commandError && <p className="manager-business-alert" role="alert">{commandError}</p>}
      {notice && <p className="manager-quota-notice" role="status">{notice}</p>}
      {loading && !data && !error && <section className="manager-business-card" role="status">Đang tải sức chứa của trường…</section>}

      {data && <>
        <section className="manager-quota-stats" aria-label="Tổng quan sức chứa">
          <article><span>Sức chứa hiện tại</span><strong>{number(data.capacity)}</strong><small>lớp</small></article>
          <article><span>Lớp đang hoạt động</span><strong>{number(data.active_class_count)}</strong><small>lớp</small></article>
          <article><span>Còn chỗ</span><strong>{number(data.available_slots)}</strong><small>lớp</small></article>
          <article><span>Trạng thái gói</span><strong>{subscriptionLabel(data.subscription_state)}</strong></article>
        </section>

        <section className="manager-business-card manager-quota-section">
          <div className="manager-business-card-heading">
            <div><p className="manager-business-eyebrow">Kỳ sức chứa</p><h2><Gauge size={18} />Thông tin gói</h2></div>
            <span className={hasSubscription ? "manager-business-chip" : "manager-business-chip is-pending"}>{subscriptionLabel(data.subscription_state)}</span>
          </div>
          <dl className="s2l-class-details">
            <div><dt>Bắt đầu kỳ</dt><dd>{formatDate(data.period_start)}</dd></div>
            <div><dt>Kết thúc kỳ</dt><dd>{formatDate(data.period_end)}</dd></div>
          </dl>
          {!hasSubscription && <div className="manager-quota-empty">Trường chưa có gói sức chứa. Sức chứa mặc định gồm 10 lớp.</div>}
        </section>

        <section className="manager-business-card manager-quota-section">
          <h2>Mua thêm slot lớp</h2>
          <p className="manager-business-alert">Giá thử nghiệm giả lập (sandbox), chưa phải giá thương mại chính thức.</p>
          {hasSubscription && (data.subscription_state === "ACTIVE" || data.subscription_state === "CANCEL_AT_PERIOD_END") ? <>
            <label htmlFor="purchase-slots">Số slot muốn mua thêm</label>
            <input
              id="purchase-slots" className="cozy-input" type="number" min={1} max={1000} step={1}
              value={purchaseQuantity} onChange={(event) => { setPurchaseQuantity(event.target.value); setQuote(null); }}
            />
            <Button type="button" variant="secondary" disabled={busy || !/^\d+$/.test(purchaseQuantity) || Number(purchaseQuantity) < 1 || Number(purchaseQuantity) > 1000} onClick={() => void showQuote()}>
              Xem báo giá
            </Button>
            {quote && <div className="cozy-form-section cozy-form-stack">
              <p>Phí gói cơ bản cho 10 slot: {number(quote.base_amount_vnd)} ₫ (tham khảo, không thu lần này)</p>
              <p>Chu kỳ gói: {quote.cycle_months % 12 === 0 ? `${number(quote.cycle_months / 12)} năm` : `${number(quote.cycle_months)} tháng`}</p>
              <p>Đơn giá mỗi slot: {number(quote.slot_amount_vnd)} ₫ · Số lượng: {quote.quantity}</p>
              <p>Sức chứa sau khi mua: {number(quote.resulting_capacity)} lớp</p>
              <p>Tỷ lệ thời gian còn lại: {new Intl.NumberFormat("vi-VN", { style: "percent", maximumFractionDigits: 2 }).format(Number(quote.remaining_time_ratio))}</p>
              <p>Số lượng × đơn giá × tỷ lệ thời gian còn lại; làm tròn nửa lên đến đồng.</p>
              <strong>Tổng tạm tính: {number(quote.amount_vnd)} ₫</strong>
              <p>Ngày gia hạn không thay đổi: {formatDate(quote.period_end)}</p>
              {(quote.momo_checkout_enabled || quote.vnpay_checkout_enabled) ? <>
                <fieldset>
                  <legend>Chọn cổng thanh toán</legend>
                  {quote.momo_checkout_enabled && <label><input type="radio" name="capacity-provider" checked={provider === "MOMO"} onChange={() => setProvider("MOMO")} /> MoMo</label>}
                  {quote.vnpay_checkout_enabled && <label><input type="radio" name="capacity-provider" checked={provider === "VNPAY"} onChange={() => setProvider("VNPAY")} /> VNPay</label>}
                </fieldset>
                <Button type="button" variant="primary" disabled={busy} onClick={() => void buy()}>Thanh toán</Button>
              </> : <p>Chưa có cổng thanh toán khả dụng.</p>}
            </div>}
          </> : <p>Cần có gói đang hoạt động để mua thêm slot lớp.</p>}
          <h3>Hóa đơn sức chứa</h3>
          {(() => {
            const invoiceId = new URLSearchParams(window.location.search).get("invoice");
            if (!invoiceId) return null;
            const returned = purchases.find((item) => item.invoice_id === invoiceId);
            return <p role="status">{returned ? `Trạng thái giao dịch: ${purchaseLabel(returned)}.` : "Chưa có thông tin giao dịch trả về."}</p>;
          })()}
          {purchases.map((item) => <div className="manager-quota-product" key={item.invoice_id}>
            <p>Mã đơn: {item.invoice_id.slice(0, 8)} · {purchaseKindLabel(item.kind)} · {providerLabel(item.provider)} · {item.provider === "SANDBOX" ? `${number(item.units)} slot bổ sung trong gói` : `${number(item.units)} slot`} · {number(item.amount_vnd)} ₫ · {purchaseLabel(item)}</p>
            {item.created_at && <p>Ngày tạo: {formatDate(item.created_at, true)}</p>}
            {item.attempts.map((attempt, index) => <p key={index}>
              Trạng thái cổng: {attemptLabel(attempt.state)} {attempt.expires_at && <>· Hết hạn: {formatDate(attempt.expires_at, true)}</>}
              {supportsPurchaseActions(item.provider) && item.state === "PENDING" && (!attempt.expires_at || Date.parse(attempt.expires_at) > Date.now()) && checkoutLink(attempt.checkout_url) && <> · <a href={checkoutLink(attempt.checkout_url) ?? undefined} target="_blank" rel="noreferrer">Mở lại thanh toán</a></>}
            </p>)}
            {supportsPurchaseActions(item.provider) && item.state === "PENDING" && <>
              <Button type="button" variant="secondary" disabled={busy} onClick={() => void purchaseAction(item.invoice_id, "reconcile")}>Kiểm tra trạng thái</Button>
              {item.provider === "VNPAY" && item.attempts.some((attempt) => attempt.expires_at && Date.parse(attempt.expires_at) <= Date.now()) && <Button type="button" variant="secondary" disabled={busy} onClick={() => void purchaseAction(item.invoice_id, "cancel")}>Hủy đơn đã hết hạn</Button>}
            </>}
          </div>)}
        </section>

        {data.scheduled_change && <section className="manager-business-card manager-quota-section" aria-label="Thay đổi đã lên lịch">
          <div className="manager-business-card-heading"><div><p className="manager-business-eyebrow">Đã lên lịch</p><h2>Hạ sức chứa vào cuối kỳ</h2></div></div>
          <dl className="s2l-class-details">
            <div><dt>Sức chứa mới</dt><dd>{number(data.scheduled_change.capacity)} lớp</dd></div>
            <div><dt>Slot bổ sung</dt><dd>{number(data.scheduled_change.addon_slots)}</dd></div>
            <div><dt>Thời điểm áp dụng</dt><dd>{formatDate(data.scheduled_change.effective_at, true)}</dd></div>
            <div><dt>Lớp sẽ tạm ngưng</dt><dd>{number(data.scheduled_change.suspend_class_refs.length)} lớp</dd></div>
          </dl>
        </section>}

        {hasSubscription && <section className="manager-business-card manager-quota-section">
          <div className="manager-business-card-heading"><div><p className="manager-business-eyebrow">Thao tác gói</p><h2>Quản lý gia hạn và sức chứa</h2></div></div>
          {canManageRenewal && <div className="cozy-form-actions" style={{ marginTop: 0 }}>
            <Button type="button" variant="secondary" disabled={busy || loading} onClick={() => { setConfirmAction("cancel_renewal"); setCommandError(""); }}>
              Tắt gia hạn
            </Button>
            <Button type="button" variant="secondary" disabled={busy || loading || data.capacity <= 10} onClick={openDowngrade}>
              Lên lịch hạ sức chứa
            </Button>
          </div>}
          {canResumeRenewal && <Button type="button" variant="primary" disabled={busy || loading} onClick={() => void configure("resume_renewal")}>
            {busy ? "Đang cập nhật…" : "Bật lại gia hạn"}
          </Button>}

          {confirmAction === "cancel_renewal" && <div className="cozy-form-section cozy-form-stack" role="group" aria-labelledby="capacity-cancel-confirm">
            <p id="capacity-cancel-confirm" className="manager-business-subtle" style={{ marginTop: 0 }}>
              Gói hiện tại vẫn có hiệu lực đến hết kỳ. Xác nhận tắt gia hạn cho kỳ tiếp theo?
            </p>
            <div className="cozy-form-actions" style={{ marginTop: 0 }}>
              <Button type="button" variant="secondary" disabled={busy} onClick={() => setConfirmAction(null)}>Để sau</Button>
              <Button type="button" variant="primary" loading={busy} disabled={busy} onClick={() => void configure("cancel_renewal")}>
                {busy ? "Đang gửi…" : "Xác nhận tắt gia hạn"}
              </Button>
            </div>
          </div>}

          {downgradeOpen && <div className="cozy-form-section cozy-form-stack" aria-labelledby="capacity-downgrade-heading">
            <h3 id="capacity-downgrade-heading">Chọn sức chứa mới</h3>
            <label htmlFor="capacity-addon-slots">Số slot bổ sung sau khi hạ</label>
            <input
              id="capacity-addon-slots"
              className="cozy-input"
              type="number"
              min={0}
              max={Math.min(1000, data.capacity - 11)}
              step={1}
              value={addonSlots}
              disabled={busy || loadingClasses}
              onChange={(event) => updateAddonSlots(event.target.value)}
            />
            {data.capacity <= 10 && <p className="manager-business-subtle">Sức chứa không thể thấp hơn 10 lớp.</p>}
            {validDowngrade && <p className="manager-business-subtle">
              Sức chứa mới là {number(targetCapacity ?? 10)} lớp. Chọn đúng {number(classesToSuspend)} lớp cần tạm ngưng.
            </p>}
            {classLoadError && <p className="manager-business-alert" role="alert">{classLoadError}</p>}
            {loadingClasses && <p role="status">Đang tải danh sách lớp…</p>}
            {!loadingClasses && !classLoadError && !hasEnoughClasses && <p className="manager-business-alert" role="alert">
              Danh sách lớp đang hoạt động chưa đầy đủ. Hãy tải lại danh sách trước khi tiếp tục.
            </p>}
            {!loadingClasses && !classLoadError && classes.length > 0 && validDowngrade && <fieldset className="manager-quota-product">
              <legend>Lớp đang hoạt động</legend>
              {classes.map((item) => {
                const checked = selectedClassRefs.includes(item.class_id);
                return <label key={item.class_id} className="cozy-form-inline-action">
                  <input
                    type="checkbox"
                    checked={checked}
                    aria-label={"Tạm ngưng lớp " + item.display_name}
                    disabled={busy || classesToSuspend === 0 || (!checked && selectedClassRefs.length >= classesToSuspend)}
                    onChange={(event) => toggleClass(item.class_id, event.target.checked)}
                  />
                  {item.display_name}
                </label>;
              })}
            </fieldset>}
            {confirmAction === "downgrade" && <div className="cozy-form-section cozy-form-stack" role="group" aria-labelledby="capacity-downgrade-confirm">
              <p id="capacity-downgrade-confirm" className="manager-business-subtle" style={{ marginTop: 0 }}>
                Sức chứa sẽ giảm xuống {number(targetCapacity ?? 10)} lớp vào cuối kỳ ({formatDate(data.period_end)}). {number(selectedClassRefs.length)} lớp đã chọn sẽ tạm ngưng khi thay đổi có hiệu lực.
              </p>
              <div className="cozy-form-actions" style={{ marginTop: 0 }}>
                <Button type="button" variant="secondary" disabled={busy} onClick={() => setConfirmAction(null)}>Sửa lựa chọn</Button>
                <Button type="button" variant="primary" loading={busy} disabled={busy || !validDowngrade || !hasEnoughClasses || !exactSelection} onClick={() => void configure("downgrade")}>
                  {busy ? "Đang gửi…" : "Xác nhận hạ sức chứa"}
                </Button>
              </div>
            </div>}
            {classLoadError && <Button type="button" variant="secondary" disabled={loadingClasses || busy} onClick={() => void loadActiveClasses()}>Tải lại danh sách lớp</Button>}
            {!confirmAction && <div className="cozy-form-actions" style={{ marginTop: 0 }}>
              <Button type="button" variant="secondary" disabled={busy} onClick={() => { setDowngradeOpen(false); setSelectedClassRefs([]); clearActionKeys(); }}>Hủy</Button>
              <Button
                type="button"
                variant="primary"
                disabled={busy || loadingClasses || Boolean(classLoadError) || !validDowngrade || !hasEnoughClasses || !exactSelection}
                onClick={() => { setConfirmAction("downgrade"); setCommandError(""); }}
              >
                Xem lại thay đổi
              </Button>
            </div>}
          </div>}

          {!canManageRenewal && !canResumeRenewal && <p className="manager-business-subtle">Thao tác gói hiện chưa khả dụng.</p>}
        </section>}

      </>}
    </div>
  );
}

export default CapacityPage;
