import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, ArrowDownToLine, ArrowUpRight, CreditCard, Gauge, RefreshCw, Users, X } from "lucide-react";
import { Link } from "react-router-dom";
import { createIdempotencyKey } from "../../../../shared/api/backendApi";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { managerBusinessService, type Be1Organization } from "../services/managerBusinessService";
import { AdminBe1Error, adminBe1Request } from "../services/be1Client";
import { teacherCandidateLabel, teacherCandidateLabels } from "../services/classService";

type Product = {
  product_id: string;
  offer_id: string;
  version: number;
  display_name: string;
  offer_kind: "MONTHLY" | "TOP_UP";
  cycle_months: number | null;
  units: number;
  amount_vnd: number;
  active: boolean;
};
type QuotaGrant = {
  grant_id: string;
  kind: string;
  units: number;
  used: number;
  available: number;
  period: string | null;
  expires_at: string | null;
};
type Allocation = {
  allocation_id: string;
  teacher_ref: string;
  available_units: number;
  active: boolean;
  revision: number;
  updated_at: string | null;
  display_name?: string | null;
  email_masked?: string | null;
};
type Summary = {
  owner_kind: string;
  available_units: number;
  granted_units: number;
  used_units: number;
  grants: QuotaGrant[];
  allocation: {
    allocated_unused_units: number;
    available_school_units: number;
    teachers: Allocation[];
  } | null;
};
type Invoice = {
  invoice_id: string;
  units: number;
  amount_vnd: number;
  state: string;
  provider: string;
  payment_mode: string;
  created_at: string | null;
  attempts: { provider: string; state: string; checkout_url: string | null; expires_at: string | null }[];
};
type Teacher = { teacher_ref: string; label?: string; display_name?: string | null; email_masked?: string | null };
type PaymentSettings = {
  real_payments_enabled: boolean;
  momo_checkout_enabled: boolean;
  vnpay_checkout_enabled: boolean;
  momo_sandbox_enabled: boolean;
  vnpay_sandbox_enabled: boolean;
  monthly_auto_renew_enabled: boolean;
};
type Data = {
  organization: Be1Organization;
  summary: Summary;
  products: Product[];
  invoices: Invoice[];
  allocations: Allocation[];
  teachers: Teacher[];
  payments: PaymentSettings;
};
type Focus = "quota" | "billing";
type PaymentStatusMessage = { kind: "pending" | "success" | "failure"; text: string };
const RECONCILE_COOLDOWN_MS = 5 * 60 * 1000;
const RECONCILE_COOLDOWN_STORAGE_KEY = "s2l.schoolBilling.reconcileCooldowns";

function money(value: number) { return new Intl.NumberFormat("vi-VN").format(value) + " ₫"; }
function number(value: number) { return new Intl.NumberFormat("vi-VN").format(value); }
function short(value: string) { return value.length > 15 ? `${value.slice(0, 6)}…${value.slice(-6)}` : value; }
function attemptExpired(expiresAt: string | null) {
  return Boolean(expiresAt && Number.isFinite(Date.parse(expiresAt)) && Date.parse(expiresAt) <= Date.now());
}
function formatPaymentExpiry(expiresAt: string | null) {
  if (!expiresAt || !Number.isFinite(Date.parse(expiresAt))) return "";
  return new Date(expiresAt).toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}
function formatCountdown(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${String(remainingSeconds).padStart(2, "0")}`;
}
function readReconcileCooldowns(): Record<string, number> {
  try {
    const stored = sessionStorage.getItem(RECONCILE_COOLDOWN_STORAGE_KEY);
    const parsed: unknown = stored ? JSON.parse(stored) : {};
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return {};
    return Object.fromEntries(Object.entries(parsed).filter(([, value]) => typeof value === "number" && Number.isFinite(value)));
  } catch {
    return {};
  }
}
function statusLabel(value: string) {
  const labels: Record<string, string> = { PAID: "Đã thanh toán", PENDING: "Chờ thanh toán", FAILED: "Thất bại", CANCELED: "Đã hủy", OPEN: "Đang mở", UNKNOWN: "Đang đối soát", MONTHLY: "Gói tháng", TOP_UP: "Mua thêm", INCLUDED: "Hạn mức hệ thống", ORGANIZATION: "Trường học", MOMO: "MoMo", VNPAY: "VNPay", SANDBOX: "Chạy thử" };
  return labels[value] ?? value;
}
function quotaTeacherLabels(teachers: Teacher[]) {
  const candidates = teachers.map((teacher) => ({
    candidate_ref: teacher.teacher_ref,
    display_name: teacher.display_name ?? null,
    email_masked: teacher.email_masked ?? null,
  }));
  return new Map(teacherCandidateLabels(candidates).map((label, index) => [teachers[index].teacher_ref, label]));
}

function quotaTeacherLabel(
  teacherRef: string,
  labels: Map<string, string>,
  allocation?: Allocation,
) {
  return labels.get(teacherRef) ?? teacherCandidateLabel({
    candidate_ref: teacherRef,
    display_name: allocation?.display_name ?? null,
    email_masked: allocation?.email_masked ?? null,
  });
}
function errorText(cause: unknown) {
  if (cause instanceof AdminBe1Error) {
    if (cause.code === "PAYMENT_PROVIDER_NOT_AVAILABLE") return "Cổng thanh toán đang tắt hoặc chưa cấu hình đầy đủ. Gói và giá vẫn xem được, thanh toán thật chưa mở.";
    if (cause.code === "PAYMENT_ATTEMPT_ALREADY_OPEN") return "Đã có hóa đơn chưa nhận được kết quả cuối. Mở lại nếu liên kết còn hạn, hoặc kiểm tra và hủy đơn VNPay sau khi hết hạn.";
    if (cause.code === "PAYMENT_PROVIDER_UNAVAILABLE") return "Chưa kết nối được với cổng thanh toán. Hóa đơn vẫn được giữ; thử kiểm tra lại trạng thái sau.";
    if (cause.code === "PAYMENT_ATTEMPT_NOT_RECONCILABLE") return "Hóa đơn này không còn giao dịch nào cần kiểm tra.";
    if (cause.code === "PAYMENT_CHECKOUT_STILL_ACTIVE") return "Chỉ hủy được sau khi liên kết VNPay hết hạn. Khi còn hạn, liên kết vẫn có thể nhận thanh toán.";
    if (cause.code === "PAYMENT_CANCEL_PROVIDER_NOT_SUPPORTED") return "Hiện chỉ hỗ trợ hủy hóa đơn VNPay đã hết hạn.";
    if (cause.code === "PAYMENT_EXPIRY_UNAVAILABLE") return "Không xác định được hạn thanh toán nên chưa thể hủy an toàn.";
    if (cause.code === "VNPAY_QUERY_RESPONSE_SIGNATURE_INVALID") return "VNPay chưa trả phản hồi đối soát có chữ ký hợp lệ. Hóa đơn vẫn chưa được xác minh; đừng thanh toán lại. Kiểm tra mã đơn vị và khóa ký chạy thử.";
    if (cause.code === "VNPAY_QUERY_GATEWAY_ERROR") return "Cổng đối soát VNPay đang trả lỗi hệ thống. Hóa đơn chưa được xác minh và hạn mức chưa thay đổi. Hãy thử kiểm tra lại sau hoặc đối chiếu giao dịch trên trang merchant VNPay.";
    if (cause.code === "VNPAY_QUERY_RESPONSE_MISMATCH" || cause.code === "VNPAY_QUERY_INVALID_RESPONSE") return "Thông tin đối soát VNPay chưa khớp hóa đơn. Trạng thái và hạn mức không thay đổi; cần đối chiếu giao dịch với VNPay.";
    if (cause.code === "VNPAY_QUERY_REJECTED") return "VNPay chưa xác nhận được giao dịch. Hóa đơn vẫn được giữ để đối soát; không tạo thanh toán khác lúc này.";
    if (cause.code === "MOMO_AMOUNT_OUT_OF_RANGE") return "Giá gói nằm ngoài giới hạn giao dịch MoMo. Hãy chọn VNPay hoặc liên hệ quản trị viên để kiểm tra giá gói.";
    if (cause.code === "SCHOOL_QUOTA_INSUFFICIENT") return "Số dư hạn mức của trường không đủ cho thao tác này.";
    if (cause.code === "QUOTA_ALLOCATION_IN_USE") return "Không thể thu hồi số lượt đã được dùng.";
    if (cause.status === 403) return "Tài khoản không có quyền thao tác trong trường này.";
  }
  return cause instanceof Error ? cause.message : "Không thể hoàn tất thao tác.";
}

export function SchoolQuotaPage() { return <SchoolQuotaBillingPage focus="quota" />; }
export function SchoolBillingPage() { return <SchoolQuotaBillingPage focus="billing" />; }

function SchoolQuotaBillingPage({ focus }: { focus: Focus }) {
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [commandError, setCommandError] = useState("");
  const [notice, setNotice] = useState("");
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatusMessage | null>(null);
  const [reconcilingInvoiceId, setReconcilingInvoiceId] = useState("");
  const [reconcileCooldowns, setReconcileCooldowns] = useState<Record<string, number>>(readReconcileCooldowns);
  const [reconcileClock, setReconcileClock] = useState(Date.now());
  const [returnInvoiceId, setReturnInvoiceId] = useState(() => new URLSearchParams(window.location.search).get("invoice") ?? "");
  const [busy, setBusy] = useState(false);
  const [selectedTeacher, setSelectedTeacher] = useState("");
  const [units, setUnits] = useState(10);
  const commandKeys = useRef(new Map<string, string>());
  const organizationPath = data?.organization.organization_id
    ? `/organizations/${encodeURIComponent(data.organization.organization_id)}/video-quota`
    : "";

  const load = useCallback(async (signal?: AbortSignal) => {
    try {
      const organization = await managerBusinessService.organization(signal);
      const base = `/organizations/${encodeURIComponent(organization.organization_id)}/video-quota`;
      const [summary, products, invoices, allocations, teachers, payments] = await Promise.all([
        adminBe1Request<Summary>(base, signal ? { signal } : {}),
        adminBe1Request<{ items: Product[] }>(base + "/products", signal ? { signal } : {}),
        adminBe1Request<{ items: Invoice[]; total: number }>(base + "/invoices?limit=50", signal ? { signal } : {}),
        adminBe1Request<{ items: Allocation[]; total: number }>(base + "/allocations", signal ? { signal } : {}),
        adminBe1Request<{ items: Teacher[] }>(base + "/teachers", signal ? { signal } : {}),
        adminBe1Request<PaymentSettings>(base + "/payment-settings", signal ? { signal } : {}),
      ]);
      if (!signal?.aborted) {
        setData({ organization, summary, products: products.items, invoices: invoices.items, allocations: allocations.items, teachers: teachers.items, payments });
        setSelectedTeacher((current) => teachers.items.some((item) => item.teacher_ref === current) ? current : teachers.items[0]?.teacher_ref ?? "");
      }
    } catch (cause) {
      if (!signal?.aborted) { setData(null); setError(errorText(cause)); }
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, []);

  const refresh = () => {
    setLoading(true);
    setError("");
    void load();
  };

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  useEffect(() => {
    const cooldownPending = Object.values(reconcileCooldowns).some((until) => until > reconcileClock);
    const checkoutExpiryPending = data?.invoices.some((invoice) =>
      invoice.state === "PENDING" && invoice.attempts.some((attempt) =>
        ["REQUESTING", "OPEN", "UNKNOWN"].includes(attempt.state)
        && attempt.expires_at
        && Date.parse(attempt.expires_at) > reconcileClock,
      ),
    ) ?? false;
    if (!cooldownPending && !checkoutExpiryPending) return;
    const timer = window.setInterval(() => setReconcileClock(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [data?.invoices, reconcileClock, reconcileCooldowns]);

  useEffect(() => {
    const organizationId = data?.organization.organization_id;
    if (focus !== "billing" || !organizationId || !returnInvoiceId) return;
    let cancelled = false;
    let pollCount = 0;
    let timer = 0;
    const invoicePath = `/organizations/${encodeURIComponent(organizationId)}/video-quota/invoices?limit=50`;
    const stopTracking = (message: PaymentStatusMessage) => {
      setPaymentStatus(message);
      setReturnInvoiceId("");
      const url = new URL(window.location.href);
      url.searchParams.delete("invoice");
      window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`);
    };
    const poll = async () => {
      if (cancelled) return;
      try {
        const result = await adminBe1Request<{ items: Invoice[]; total: number }>(invoicePath);
        if (cancelled) return;
        setData((current) => current ? { ...current, invoices: result.items } : current);
        const invoice = result.items.find((item) => item.invoice_id === returnInvoiceId);
        if (invoice?.state === "PAID") {
          stopTracking({ kind: "success", text: "Thanh toán đã được xác nhận; hạn mức đã được cộng vào số dư trường." });
          return;
        }
        if (invoice?.state === "FAILED") {
          stopTracking({ kind: "failure", text: "Cổng xác nhận giao dịch đã hết hạn hoặc thất bại. Bạn có thể tạo đơn thanh toán mới." });
          return;
        }
        if (invoice?.state === "CANCELED") {
          stopTracking({ kind: "failure", text: "Hóa đơn VNPay đã được hủy. Bạn có thể chọn phương thức thanh toán khác." });
          return;
        }
      } catch {
        // Keep polling briefly: the provider may redirect before the signed callback arrives.
      }
      pollCount += 1;
      if (pollCount >= 30) {
        stopTracking({ kind: "pending", text: "Chưa nhận được xác nhận cuối từ cổng. Hóa đơn vẫn được giữ; dùng “Kiểm tra trạng thái” trong danh sách hóa đơn." });
        return;
      }
      timer = window.setTimeout(() => void poll(), 2000);
    };
    setPaymentStatus({ kind: "pending", text: "Đang chờ cổng thanh toán xác nhận giao dịch…" });
    void poll();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [data?.organization.organization_id, focus, returnInvoiceId]);

  const allocationsByTeacher = useMemo(() => new Map((data?.allocations ?? []).map((item) => [item.teacher_ref, item])), [data?.allocations]);
  const labelsByTeacher = useMemo(() => quotaTeacherLabels(data?.teachers ?? []), [data?.teachers]);
  const activeProviderModes = data ? [
    ...(data.payments.momo_checkout_enabled ? [data.payments.momo_sandbox_enabled] : []),
    ...(data.payments.vnpay_checkout_enabled ? [data.payments.vnpay_sandbox_enabled] : []),
  ] : [];
  const paymentEnvironmentLabel = activeProviderModes.length === 0
    ? "Cổng thanh toán đang tắt"
    : activeProviderModes.every(Boolean)
      ? "Chạy thử · không thu tiền thật"
      : activeProviderModes.every((isSandbox) => !isSandbox)
        ? "Cổng production"
        : "Môi trường hỗn hợp";
  const openPaymentInvoice = data?.invoices.find((invoice) =>
    invoice.state === "PENDING" && invoice.attempts.some((attempt) =>
      ["REQUESTING", "OPEN", "UNKNOWN"].includes(attempt.state),
    ),
  );
  const openPaymentAttempt = openPaymentInvoice?.attempts.find((attempt) => ["REQUESTING", "OPEN", "UNKNOWN"].includes(attempt.state));
  const openPaymentHasCheckout = Boolean(openPaymentAttempt?.checkout_url && !attemptExpired(openPaymentAttempt.expires_at));
  const reconcileSecondsRemaining = (invoiceId: string) => Math.max(0, Math.ceil(((reconcileCooldowns[invoiceId] ?? 0) - reconcileClock) / 1000));
  const reconcileLabel = (invoiceId: string, idleLabel: string) => {
    if (reconcilingInvoiceId === invoiceId) return "Đang kiểm tra…";
    const seconds = reconcileSecondsRemaining(invoiceId);
    return seconds > 0 ? `Kiểm tra lại sau ${formatCountdown(seconds)}` : idleLabel;
  };
  const setInvoiceReconcileCooldown = (invoiceId: string, until: number | null) => {
    const next = { ...reconcileCooldowns };
    if (until === null) delete next[invoiceId];
    else next[invoiceId] = until;
    setReconcileCooldowns(next);
    try {
      sessionStorage.setItem(RECONCILE_COOLDOWN_STORAGE_KEY, JSON.stringify(next));
    } catch {
      // The in-memory guard still prevents repeated queries when storage is unavailable.
    }
  };
  const runCommand = async (keyName: string, path: string, body: unknown, method = "POST", revision?: number) => {
    if (!organizationPath || busy) return;
    const key = commandKeys.current.get(keyName) ?? createIdempotencyKey();
    commandKeys.current.set(keyName, key);
    setBusy(true); setCommandError(""); setNotice("");
    try {
      const headers: Record<string, string> = { "Idempotency-Key": key };
      if (revision !== undefined) headers["If-Match"] = `"${revision}"`;
      await adminBe1Request(path, { method, headers, body: JSON.stringify(body) });
      commandKeys.current.delete(keyName);
      setNotice("Đã cập nhật hạn mức.");
      await load();
    } catch (cause) { setCommandError(errorText(cause)); }
    finally { setBusy(false); }
  };

  const checkout = async (product: Product, provider: "MOMO" | "VNPAY") => {
    if (!organizationPath || busy) return;
    const keyName = `checkout:${product.product_id}:${provider}`;
    const key = commandKeys.current.get(keyName) ?? createIdempotencyKey();
    commandKeys.current.set(keyName, key);
    setBusy(true); setCommandError(""); setNotice("");
    try {
      const result = await adminBe1Request<{ invoice_id: string; state: string; checkout_url: string | null }>(
        organizationPath + "/checkout",
        { method: "POST", headers: { "Idempotency-Key": key }, body: JSON.stringify({ product_id: product.product_id, provider, payment_mode: "MANUAL" }) },
      );
      if (result.checkout_url) window.location.assign(result.checkout_url);
      else throw new Error("Cổng thanh toán chưa trả về liên kết thanh toán.");
    } catch (cause) { setCommandError(errorText(cause)); setBusy(false); }
  };

  const reconcileInvoice = async (invoiceId: string) => {
    if (!organizationPath || reconcilingInvoiceId) return;
    if (reconcileSecondsRemaining(invoiceId) > 0) return;
    setInvoiceReconcileCooldown(invoiceId, Date.now() + RECONCILE_COOLDOWN_MS);
    setReconcilingInvoiceId(invoiceId);
    setCommandError("");
    setPaymentStatus(null);
    try {
      const result = await adminBe1Request<{ invoice_id: string; state: string; reconciled: boolean }>(
        `${organizationPath}/invoices/${encodeURIComponent(invoiceId)}/reconcile`,
        { method: "POST" },
      );
      if (result.state === "PAID") {
        setInvoiceReconcileCooldown(invoiceId, null);
        setPaymentStatus({ kind: "success", text: "Thanh toán đã được xác nhận; hạn mức đã được cộng vào số dư trường." });
      } else if (result.state === "FAILED") {
        setInvoiceReconcileCooldown(invoiceId, null);
        setPaymentStatus({ kind: "failure", text: "Cổng xác nhận giao dịch đã hết hạn hoặc thất bại. Bạn có thể tạo đơn thanh toán mới." });
      } else if (result.state === "CANCELED") {
        setInvoiceReconcileCooldown(invoiceId, null);
        setPaymentStatus({ kind: "success", text: "Hóa đơn đã được hủy. Bạn có thể chọn phương thức thanh toán khác." });
      } else {
        setPaymentStatus({ kind: "pending", text: "Cổng chưa có kết quả cuối. Hóa đơn vẫn được giữ; mở lại liên kết còn hạn hoặc kiểm tra lại sau." });
      }
      await load();
    } catch (cause) {
      setCommandError(errorText(cause));
      if (cause instanceof AdminBe1Error && cause.status >= 500) {
        setPaymentStatus({ kind: "pending", text: "Chưa nhận được kết quả đối soát có thể xác minh. Hóa đơn chưa chuyển trạng thái và hạn mức chưa thay đổi. Chờ hết thời gian đếm ngược rồi mới kiểm tra lại." });
      }
    } finally {
      setReconcilingInvoiceId("");
    }
  };

  const cancelExpiredInvoice = async (invoiceId: string) => {
    if (!organizationPath || reconcilingInvoiceId) return;
    // A stale/manual status-check cooldown must not prevent an explicit cancel attempt.
    setInvoiceReconcileCooldown(invoiceId, null);
    setReconcilingInvoiceId(invoiceId);
    setCommandError("");
    setPaymentStatus(null);
    try {
      const result = await adminBe1Request<{ invoice_id: string; state: string; canceled: boolean; reconciled: boolean }>(
        `${organizationPath}/invoices/${encodeURIComponent(invoiceId)}/cancel`,
        { method: "POST" },
      );
      if (result.state === "PAID") {
        setInvoiceReconcileCooldown(invoiceId, null);
        setPaymentStatus({ kind: "success", text: "VNPay xác nhận đã thanh toán; hạn mức đã được cộng vào số dư trường." });
      } else if (result.state === "FAILED") {
        setInvoiceReconcileCooldown(invoiceId, null);
        setPaymentStatus({ kind: "failure", text: "VNPay xác nhận giao dịch thất bại. Bạn có thể tạo đơn mới hoặc chọn cổng khác." });
      } else if (result.state === "CANCELED") {
        setInvoiceReconcileCooldown(invoiceId, null);
        setPaymentStatus({ kind: "success", text: "Đã hủy hóa đơn hết hạn. Bạn có thể chọn lại VNPay hoặc MoMo để tạo đơn mới." });
      } else {
        setPaymentStatus({ kind: "pending", text: "VNPay chưa xác nhận giao dịch đã đóng. Hóa đơn vẫn được giữ an toàn; kiểm tra lại sau." });
      }
      await load();
    } catch (cause) {
      setCommandError(errorText(cause));
      if (cause instanceof AdminBe1Error && cause.status >= 500) {
        setPaymentStatus({ kind: "pending", text: "Chưa xác minh được với VNPay nên hóa đơn chưa bị hủy. Kiểm tra lại sau để tránh hủy nhầm giao dịch đã trả tiền." });
      }
    } finally {
      setReconcilingInvoiceId("");
    }
  };

  const availableSchoolUnits = data?.summary.allocation?.available_school_units ?? data?.summary.available_units ?? 0;
  const headingTitle = focus === "quota" ? "Hạn mức video" : "Thanh toán của trường";
  return (
    <div className="s2l-page manager-business-page manager-quota-page">
      <PageHeading
        eyebrow="Quản lý trường"
        title={headingTitle}
        description={data?.organization.display_name ?? "Hạn mức và giao dịch trong phạm vi trường được xác minh."}
        action={<button type="button" className="manager-business-button" onClick={refresh} disabled={loading}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>}
      />
      <nav className="manager-quota-tabs" aria-label="Hạn mức và thanh toán">
        <Link className={focus === "quota" ? "is-active" : ""} to="/school/quota"><Gauge size={16} />Hạn mức & phân bổ</Link>
        <Link className={focus === "billing" ? "is-active" : ""} to="/school/billing"><CreditCard size={16} />Gói & hóa đơn</Link>
      </nav>
      {error && <section className="manager-quota-alert" role="alert"><strong>Không tải được dữ liệu</strong><span>{error}</span><button type="button" onClick={refresh}>Thử lại</button></section>}
      {commandError && <p className="manager-business-alert" role="alert">{commandError}</p>}
      {notice && <p className="manager-quota-notice" role="status">{notice}</p>}
      {paymentStatus && <p className={`manager-quota-payment-message is-${paymentStatus.kind}`} role="status">{paymentStatus.text}</p>}
      {loading && !data && !error && <section className="manager-business-card" role="status">Đang tải hạn mức của trường…</section>}
      {data && <>
        <section className="manager-quota-stats" aria-label="Tổng quan hạn mức">
          <article><span>Tổng đã cấp</span><strong>{number(data.summary.granted_units)}</strong><small>lượt</small></article>
          <article><span>Đã sử dụng</span><strong>{number(data.summary.used_units)}</strong><small>lượt</small></article>
          <article><span>Còn cho trường</span><strong>{number(data.summary.allocation?.available_school_units ?? data.summary.available_units)}</strong><small>lượt chưa phân bổ</small></article>
          <article><span>Đang giao giáo viên</span><strong>{number(data.summary.allocation?.allocated_unused_units ?? 0)}</strong><small>lượt chưa dùng</small></article>
        </section>
        {focus === "quota" ? <>
          <section className="manager-business-card manager-quota-section">
            <div className="manager-business-card-heading">
              <div><p className="manager-business-eyebrow">Số dư theo nguồn</p><h2><Gauge size={18} />Lịch sử hạn mức</h2></div>
              <Link className="manager-quota-inline-link" to="/school/billing">Mua hạn mức <ArrowUpRight size={15} /></Link>
            </div>
            {data.summary.grants.length ? <div className="manager-quota-grant-list">{data.summary.grants.map((grant) => <article key={grant.grant_id}>
              <div><strong>{statusLabel(grant.kind)}</strong><small>{grant.period ? `Kỳ ${grant.period}` : grant.expires_at ? `Hết hạn ${new Date(grant.expires_at).toLocaleDateString("vi-VN")}` : "Không hết hạn"}</small></div>
              <div className="manager-quota-grant-metrics"><span>{number(grant.units)} cấp</span><span>{number(grant.used)} dùng</span><strong>{number(grant.available)} còn</strong></div>
            </article>)}</div> : <div className="manager-quota-empty">Trường chưa có hạn mức. Mua gói để bắt đầu phân bổ cho giáo viên.</div>}
          </section>
          <section className="manager-business-card manager-quota-section">
            <div className="manager-business-card-heading">
              <div><p className="manager-business-eyebrow">Hạn mức trường sở hữu</p><h2><Users size={18} />Phân bổ cho giáo viên</h2></div>
              <span className="manager-business-chip">Còn {number(data.summary.allocation?.available_school_units ?? data.summary.available_units)} lượt</span>
            </div>
            <div className="manager-quota-allocation-form">
              <label>Giáo viên<select value={selectedTeacher} onChange={(event) => setSelectedTeacher(event.target.value)} disabled={!data.teachers.length}><option value="">{data.teachers.length ? "Chọn giáo viên" : "Chưa có giáo viên được phân công"}</option>{data.teachers.map((teacher) => <option key={teacher.teacher_ref} value={teacher.teacher_ref}>{quotaTeacherLabel(teacher.teacher_ref, labelsByTeacher)}</option>)}</select></label>
              <label>Số lượt<input type="number" min={1} max={100000} value={units} onChange={(event) => setUnits(event.target.valueAsNumber)} /></label>
              <button type="button" className="manager-business-button is-primary" disabled={busy || availableSchoolUnits <= 0 || !selectedTeacher || !data.teachers.length} onClick={() => {
                const current = allocationsByTeacher.get(selectedTeacher);
                void runCommand(`allocate:${selectedTeacher}:${units}`, organizationPath + "/allocations", { teacher_ref: selectedTeacher, units }, "POST", current?.revision);
              }}><ArrowDownToLine size={16} />Giao hạn mức</button>
              {availableSchoolUnits <= 0 && <span className="manager-business-subtle">Chưa có lượt để giao.</span>}
            </div>
            {!data.allocations.length ? <div className="manager-quota-empty">Chưa phân bổ hạn mức cho giáo viên nào.</div> : <div className="manager-quota-table-wrap"><table className="manager-quota-table"><thead><tr><th>Giáo viên</th><th>Hạn mức chưa dùng</th><th>Cập nhật</th><th>Thao tác</th></tr></thead><tbody>{data.allocations.map((allocation) => <tr key={allocation.allocation_id}>
              <td data-label="Giáo viên"><strong>{quotaTeacherLabel(allocation.teacher_ref, labelsByTeacher, allocation)}</strong></td><td data-label="Hạn mức chưa dùng">{number(allocation.available_units)} lượt</td><td data-label="Cập nhật">{allocation.updated_at ? new Date(allocation.updated_at).toLocaleDateString("vi-VN") : "—"}</td>
              <td data-label="Thao tác"><button type="button" className="manager-quota-reclaim" disabled={busy || allocation.available_units < 1} onClick={() => {
                const amount = Math.min(units, allocation.available_units);
                void runCommand(`reclaim:${allocation.teacher_ref}:${amount}`, organizationPath + "/allocations/reclaim", { teacher_ref: allocation.teacher_ref, units: amount }, "POST", allocation.revision);
              }}>Thu hồi {number(Math.min(units, allocation.available_units))} lượt</button></td>
            </tr>)}</tbody></table></div>}
            <p className="manager-quota-policy">Hạn mức chưa dùng tự trả về số dư trường khi giáo viên rời phân công; hạn mức đã dùng vẫn được tính vào mức sử dụng của trường.</p>
          </section>
        </> : <>
          {openPaymentInvoice && <section className="manager-quota-payment-hold" role="alert">
            <AlertTriangle size={19} aria-hidden="true" />
            <div><strong>{openPaymentHasCheckout ? "Có hóa đơn đang chờ thanh toán" : openPaymentAttempt?.expires_at && attemptExpired(openPaymentAttempt.expires_at) ? "Liên kết đã hết hạn · chờ xác minh giao dịch" : "Giao dịch đang chờ xác nhận"}</strong><span>Hóa đơn {short(openPaymentInvoice.invoice_id)} · {statusLabel(openPaymentInvoice.provider)}. {openPaymentHasCheckout ? `Có thể thanh toán qua liên kết này đến ${formatPaymentExpiry(openPaymentAttempt?.expires_at ?? null)}. Hạn mức chỉ được cộng sau khi cổng xác nhận.` : openPaymentAttempt?.expires_at && attemptExpired(openPaymentAttempt.expires_at) ? `Liên kết hết hạn lúc ${formatPaymentExpiry(openPaymentAttempt.expires_at)} nhưng VNPay chưa gửi kết quả cuối. Đừng thanh toán lại khi chưa xác minh; hãy kiểm tra trạng thái hoặc hủy đơn hết hạn trước khi chọn phương thức khác.` : "Đóng trang thanh toán không hủy hóa đơn. Hóa đơn chưa có liên kết thanh toán để mở lại; hãy kiểm tra trạng thái trước khi thử phương thức khác."}</span></div>
            <div className="manager-quota-hold-actions">
              {openPaymentInvoice.provider === "VNPAY" && openPaymentAttempt?.expires_at && attemptExpired(openPaymentAttempt.expires_at) && <button type="button" className="manager-quota-cancel" disabled={Boolean(reconcilingInvoiceId)} onClick={() => void cancelExpiredInvoice(openPaymentInvoice.invoice_id)}><X size={14} />{reconcilingInvoiceId === openPaymentInvoice.invoice_id ? "Đang xử lý…" : "Hủy đơn đã hết hạn"}</button>}
              <button type="button" className="manager-quota-reconcile" disabled={Boolean(reconcilingInvoiceId) || reconcileSecondsRemaining(openPaymentInvoice.invoice_id) > 0} title={reconcileSecondsRemaining(openPaymentInvoice.invoice_id) > 0 ? "VNPay giới hạn truy vấn trùng; chờ hết thời gian đếm ngược." : undefined} onClick={() => void reconcileInvoice(openPaymentInvoice.invoice_id)}><RefreshCw size={14} className={reconcilingInvoiceId === openPaymentInvoice.invoice_id ? "is-spinning" : undefined} />{reconcileLabel(openPaymentInvoice.invoice_id, "Kiểm tra với cổng")}</button>
            </div>
          </section>}
          <section className="manager-business-card manager-quota-section">
            <div className="manager-business-card-heading"><div><p className="manager-business-eyebrow">Bảng giá do Quản trị nền tảng quản lý</p><h2><CreditCard size={18} />Chọn gói hạn mức</h2></div><span className={data.payments.real_payments_enabled ? "manager-business-chip" : "manager-business-chip is-pending"}>{paymentEnvironmentLabel}</span></div>
            {!data.products.length ? <div className="manager-quota-empty">Hiện chưa có gói hạn mức đang mở bán. Liên hệ Quản trị nền tảng để cấu hình danh mục giá.</div> : <div className="manager-quota-products">{data.products.map((product) => <article key={product.product_id} className="manager-quota-product">
              <div className="manager-quota-product-top"><span className={product.offer_kind === "MONTHLY" ? "is-monthly" : "is-topup"}>{statusLabel(product.offer_kind)}</span><small>Phiên bản {product.version}</small></div>
              <h3>{product.display_name}</h3><div className="manager-quota-product-units">{number(product.units)} <span>lượt video</span></div>
              <strong className="manager-quota-product-price">{money(product.amount_vnd)}</strong>
              <p>{product.offer_kind === "MONTHLY" ? "Hạn mức theo tháng dương lịch; thanh toán thủ công mỗi kỳ." : "Hạn mức mua thêm không hết hạn cho đến khi được sử dụng."}</p>
              <div className="manager-quota-checkout-actions">
                {data.payments.momo_checkout_enabled && <button type="button" disabled={busy || Boolean(openPaymentInvoice)} title={openPaymentInvoice ? "Cần xử lý hóa đơn đang chờ trước" : undefined} onClick={() => void checkout(product, "MOMO")}>Thanh toán MoMo</button>}
                {data.payments.vnpay_checkout_enabled && <button type="button" disabled={busy || Boolean(openPaymentInvoice)} title={openPaymentInvoice ? "Cần xử lý hóa đơn đang chờ trước" : undefined} onClick={() => void checkout(product, "VNPAY")}>Thanh toán VNPay</button>}
                {!data.payments.real_payments_enabled && <button type="button" disabled title="Cổng thanh toán thật chưa được cấu hình">Thanh toán chưa khả dụng</button>}
              </div>
            </article>)}</div>}
            <div className="manager-quota-provider-note">{data.payments.monthly_auto_renew_enabled ? "Gia hạn tự động đã sẵn sàng." : "Gói tháng hiện thanh toán thủ công; tự động gia hạn chỉ mở khi cổng thanh toán hỗ trợ tính năng này."}</div>
          </section>
          <section id="school-invoices" className="manager-business-card manager-quota-section">
            <div className="manager-business-card-heading"><div><p className="manager-business-eyebrow">Lịch sử trường</p><h2>Hóa đơn gần đây</h2></div><span className="manager-business-chip">{data.invoices.length} hóa đơn</span></div>
            {!data.invoices.length ? <div className="manager-quota-empty">Chưa có giao dịch. Hóa đơn sẽ xuất hiện sau khi tạo thanh toán.</div> : <div className="manager-quota-table-wrap"><table className="manager-quota-table"><thead><tr><th>Hóa đơn</th><th>Hạn mức</th><th>Cổng</th><th>Trạng thái</th><th>Số tiền</th><th>Thao tác</th></tr></thead><tbody>{data.invoices.map((invoice) => {
              const paymentAttempt = invoice.attempts.find((attempt) => ["REQUESTING", "OPEN", "UNKNOWN"].includes(attempt.state));
              const canResumePayment = invoice.state === "PENDING" && paymentAttempt?.checkout_url && !attemptExpired(paymentAttempt.expires_at);
              const invoiceStateLabel = invoice.state !== "PENDING" ? statusLabel(invoice.state) : paymentAttempt?.state === "UNKNOWN" ? "Đang đối soát" : paymentAttempt?.expires_at && attemptExpired(paymentAttempt.expires_at) ? "Chờ xác minh" : "Chờ thanh toán";
              const reconcileSeconds = reconcileSecondsRemaining(invoice.invoice_id);
              return <tr key={invoice.invoice_id}><td data-label="Hóa đơn"><strong>{short(invoice.invoice_id)}</strong><small>{invoice.created_at ? new Date(invoice.created_at).toLocaleString("vi-VN") : "—"}</small></td><td data-label="Hạn mức">{number(invoice.units)} lượt</td><td data-label="Cổng">{statusLabel(invoice.provider)}</td><td data-label="Trạng thái"><span className={`manager-quota-status is-${invoice.state.toLowerCase()}`}>{invoiceStateLabel}</span></td><td data-label="Số tiền">{money(invoice.amount_vnd)}</td><td data-label="Thao tác"><div className="manager-quota-invoice-actions">
                {canResumePayment && <><a className="manager-quota-continue" href={paymentAttempt.checkout_url ?? undefined} target="_blank" rel="noreferrer">Mở lại thanh toán <ArrowUpRight size={14} /></a>{paymentAttempt.expires_at && <small>Có hiệu lực đến {formatPaymentExpiry(paymentAttempt.expires_at)}</small>}</>}
                {invoice.state === "PENDING" && <>
                  <button type="button" className="manager-quota-reconcile" disabled={Boolean(reconcilingInvoiceId) || reconcileSeconds > 0} title={reconcileSeconds > 0 ? "VNPay giới hạn truy vấn trùng; chờ hết thời gian đếm ngược." : undefined} onClick={() => void reconcileInvoice(invoice.invoice_id)}><RefreshCw size={13} className={reconcilingInvoiceId === invoice.invoice_id ? "is-spinning" : undefined} />{reconcileLabel(invoice.invoice_id, "Kiểm tra trạng thái")}</button>{!canResumePayment && <small className="manager-quota-no-checkout">{paymentAttempt?.expires_at && attemptExpired(paymentAttempt.expires_at) ? `Liên kết hết hạn lúc ${formatPaymentExpiry(paymentAttempt.expires_at)}` : "Chờ cổng xác nhận"}</small>}
                </>}
                {invoice.state !== "PENDING" && "—"}
              </div></td></tr>;
            })}</tbody></table></div>}
            <p className="manager-quota-policy">Đóng trang thanh toán không tự hủy hóa đơn. Với VNPay, khi liên kết hết hạn, chọn “Hủy đơn hết hạn”; hệ thống xác minh với cổng trước khi cho tạo đơn mới.</p>
          </section>
        </>}
      </>}
    </div>
  );
}
