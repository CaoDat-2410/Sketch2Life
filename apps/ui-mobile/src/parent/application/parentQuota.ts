import type {
  ParentQuotaCancelResult,
  ParentQuotaCheckoutResult,
  ParentQuotaInvoice,
  ParentQuotaInvoicePage,
  ParentQuotaPaymentSettings,
  ParentQuotaProduct,
  ParentQuotaReconcileResult,
  ParentVideoQuota,
} from '../domain/types';

export const RECONCILE_COOLDOWN_MS = 5 * 60 * 1000;
export const INVOICE_POLL_INTERVAL_MS = 2_000;
export const INVOICE_POLL_MAX_ATTEMPTS = 30;
export const CHECKOUT_URL_MISSING_COPY = 'Chưa thể mở trang thanh toán. Hãy thử lại sau.';

export type ParentPaymentProvider = 'MOMO' | 'VNPAY';
export type ParentPaymentMessage = { kind: 'pending' | 'success' | 'failure'; text: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isText(value: unknown): value is string {
  return typeof value === 'string';
}

function isNullableText(value: unknown): value is string | null {
  return value === null || isText(value);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isNullableNumber(value: unknown): value is number | null {
  return value === null || isFiniteNumber(value);
}

function isBoolean(value: unknown): value is boolean {
  return typeof value === 'boolean';
}

function readInvoice(value: unknown): ParentQuotaInvoice | null {
  if (!isRecord(value)
    || !isText(value.invoice_id)
    || !isFiniteNumber(value.units)
    || !isFiniteNumber(value.amount_vnd)
    || !isText(value.state)
    || !isText(value.provider)
    || !isText(value.payment_mode)
    || !isNullableText(value.created_at)
    || !Array.isArray(value.attempts)) return null;
  const attempts = value.attempts.map((attempt) => {
    if (!isRecord(attempt)
      || !isText(attempt.provider)
      || !isText(attempt.state)
      || !isNullableText(attempt.checkout_url)
      || !isNullableText(attempt.expires_at)) return null;
    return {
      provider: attempt.provider,
      state: attempt.state,
      checkout_url: attempt.checkout_url,
      expires_at: attempt.expires_at,
    };
  });
  if (attempts.some((attempt) => attempt === null)) return null;
  return {
    invoice_id: value.invoice_id,
    units: value.units,
    amount_vnd: value.amount_vnd,
    state: value.state,
    provider: value.provider,
    payment_mode: value.payment_mode,
    created_at: value.created_at,
    attempts: attempts as ParentQuotaInvoice['attempts'],
  };
}

export function readParentVideoQuota(value: unknown): ParentVideoQuota | null {
  if (!isRecord(value)
    || !isText(value.owner_kind)
    || !isFiniteNumber(value.available_units)
    || !isFiniteNumber(value.granted_units)
    || !isFiniteNumber(value.used_units)
    || !Array.isArray(value.grants)
    || !Object.prototype.hasOwnProperty.call(value, 'allocation')) return null;
  const grants = value.grants.map((grant) => {
    if (!isRecord(grant)
      || !isText(grant.grant_id)
      || !isText(grant.kind)
      || !isFiniteNumber(grant.units)
      || !isFiniteNumber(grant.used)
      || !isFiniteNumber(grant.available)
      || !isNullableText(grant.period)
      || !isNullableText(grant.expires_at)) return null;
    return {
      grant_id: grant.grant_id,
      kind: grant.kind,
      units: grant.units,
      used: grant.used,
      available: grant.available,
      period: grant.period,
      expires_at: grant.expires_at,
    };
  });
  if (grants.some((grant) => grant === null)) return null;
  let allocation: ParentVideoQuota['allocation'] = null;
  if (value.allocation !== null) {
    const candidate = value.allocation;
    if (!isRecord(candidate)
      || !isFiniteNumber(candidate.allocated_unused_units)
      || !isFiniteNumber(candidate.available_school_units)
      || !Array.isArray(candidate.teachers)) return null;
    const teachers = candidate.teachers.map((teacher) => {
      if (!isRecord(teacher)
        || !isText(teacher.teacher_ref)
        || !isText(teacher.allocation_id)
        || !isFiniteNumber(teacher.available_units)
        || !isFiniteNumber(teacher.revision)
        || !isBoolean(teacher.active)) return null;
      return {
        teacher_ref: teacher.teacher_ref,
        allocation_id: teacher.allocation_id,
        available_units: teacher.available_units,
        revision: teacher.revision,
        active: teacher.active,
      };
    });
    if (teachers.some((teacher) => teacher === null)) return null;
    allocation = {
      allocated_unused_units: candidate.allocated_unused_units,
      available_school_units: candidate.available_school_units,
      teachers: teachers as NonNullable<ParentVideoQuota['allocation']>['teachers'],
    };
  }
  return {
    owner_kind: value.owner_kind,
    available_units: value.available_units,
    granted_units: value.granted_units,
    used_units: value.used_units,
    grants: grants as ParentVideoQuota['grants'],
    allocation,
  };
}

export function readParentQuotaProducts(value: unknown): ParentQuotaProduct[] | null {
  if (!isRecord(value) || !Array.isArray(value.items)) return null;
  const items = value.items.map((item) => {
    if (!isRecord(item)
      || !isText(item.product_id)
      || !isText(item.offer_id)
      || !isFiniteNumber(item.version)
      || !isText(item.display_name)
      || (item.offer_kind !== 'MONTHLY' && item.offer_kind !== 'TOP_UP')
      || !isNullableNumber(item.cycle_months)
      || !isFiniteNumber(item.units)
      || !isFiniteNumber(item.amount_vnd)
      || !isBoolean(item.active)) return null;
    return {
      product_id: item.product_id,
      offer_id: item.offer_id,
      version: item.version,
      display_name: item.display_name,
      offer_kind: item.offer_kind,
      cycle_months: item.cycle_months,
      units: item.units,
      amount_vnd: item.amount_vnd,
      active: item.active,
    };
  });
  return items.some((item) => item === null) ? null : items as ParentQuotaProduct[];
}

export function readParentQuotaInvoices(value: unknown): ParentQuotaInvoicePage | null {
  if (!isRecord(value) || !Array.isArray(value.items) || !isFiniteNumber(value.total)) return null;
  const items = value.items.map(readInvoice);
  return items.some((item) => item === null) ? null : { items: items as ParentQuotaInvoice[], total: value.total };
}

export function readParentQuotaPaymentSettings(value: unknown): ParentQuotaPaymentSettings | null {
  if (!isRecord(value)
    || !isBoolean(value.real_payments_enabled)
    || !isBoolean(value.momo_checkout_enabled)
    || !isBoolean(value.vnpay_checkout_enabled)
    || !isBoolean(value.momo_sandbox_enabled)
    || !isBoolean(value.vnpay_sandbox_enabled)
    || !isBoolean(value.monthly_auto_renew_enabled)) return null;
  return {
    real_payments_enabled: value.real_payments_enabled,
    momo_checkout_enabled: value.momo_checkout_enabled,
    vnpay_checkout_enabled: value.vnpay_checkout_enabled,
    momo_sandbox_enabled: value.momo_sandbox_enabled,
    vnpay_sandbox_enabled: value.vnpay_sandbox_enabled,
    monthly_auto_renew_enabled: value.monthly_auto_renew_enabled,
  };
}

export function readParentQuotaCheckoutResult(value: unknown): ParentQuotaCheckoutResult | null {
  if (!isRecord(value) || !isText(value.invoice_id) || !isText(value.state) || !isNullableText(value.checkout_url)) return null;
  return { invoice_id: value.invoice_id, state: value.state, checkout_url: value.checkout_url };
}

export function readParentQuotaReconcileResult(value: unknown): ParentQuotaReconcileResult | null {
  if (!isRecord(value) || !isText(value.invoice_id) || !isText(value.state) || !isBoolean(value.reconciled)) return null;
  return { invoice_id: value.invoice_id, state: value.state, reconciled: value.reconciled };
}

export function readParentQuotaCancelResult(value: unknown): ParentQuotaCancelResult | null {
  if (!isRecord(value)
    || !isText(value.invoice_id)
    || !isText(value.state)
    || !isBoolean(value.canceled)
    || !isBoolean(value.reconciled)) return null;
  return { invoice_id: value.invoice_id, state: value.state, canceled: value.canceled, reconciled: value.reconciled };
}

export function enabledQuotaProviders(settings: ParentQuotaPaymentSettings): { provider: ParentPaymentProvider; sandbox: boolean }[] {
  return [
    ...(settings.momo_checkout_enabled ? [{ provider: 'MOMO' as const, sandbox: settings.momo_sandbox_enabled }] : []),
    ...(settings.vnpay_checkout_enabled ? [{ provider: 'VNPAY' as const, sandbox: settings.vnpay_sandbox_enabled }] : []),
  ];
}

export function isCheckoutUrlOpenable(value: string | null): value is string {
  if (!value) return false;
  try {
    return new URL(value).protocol === 'https:';
  } catch {
    return false;
  }
}

export function invoicePaymentAttempt(invoice: ParentQuotaInvoice) {
  if (invoice.state !== 'PENDING') return undefined;
  return invoice.attempts.find((attempt) => ['REQUESTING', 'OPEN', 'UNKNOWN'].includes(attempt.state));
}

export function paymentAttemptExpired(expiresAt: string | null, now = Date.now()): boolean {
  return Boolean(expiresAt && Number.isFinite(Date.parse(expiresAt)) && Date.parse(expiresAt) <= now);
}

export function canResumeInvoicePayment(invoice: ParentQuotaInvoice, now = Date.now()): boolean {
  const attempt = invoicePaymentAttempt(invoice);
  return Boolean(attempt?.checkout_url && isCheckoutUrlOpenable(attempt.checkout_url) && !paymentAttemptExpired(attempt.expires_at, now));
}

export function getOpenParentInvoice(invoices: readonly ParentQuotaInvoice[]): ParentQuotaInvoice | undefined {
  return invoices.find((invoice) => Boolean(invoicePaymentAttempt(invoice)));
}

export function reconcileSecondsRemaining(cooldowns: Readonly<Record<string, number>>, invoiceId: string, now = Date.now()): number {
  return Math.max(0, Math.ceil(((cooldowns[invoiceId] ?? 0) - now) / 1000));
}

export function withReconcileCooldown(
  cooldowns: Readonly<Record<string, number>>,
  invoiceId: string,
  until: number | null,
): Record<string, number> {
  const next = { ...cooldowns };
  if (until === null) delete next[invoiceId];
  else next[invoiceId] = until;
  return next;
}

export class CheckoutIdentityMap {
  private readonly keys = new Map<string, string>();
  private activeInput = '';

  get(productId: string, provider: ParentPaymentProvider, create: () => string): string {
    const input = `${productId}\u0000${provider}`;
    if (this.activeInput && this.activeInput !== input) this.keys.clear();
    this.activeInput = input;
    const key = this.keys.get(input) ?? create();
    this.keys.set(input, key);
    return key;
  }

  complete(productId: string, provider: ParentPaymentProvider): void {
    const input = `${productId}\u0000${provider}`;
    this.keys.delete(input);
    if (this.activeInput === input) this.activeInput = '';
  }

  reset(): void {
    this.keys.clear();
    this.activeInput = '';
  }
}

export type InvoicePollState = { invoiceId: string; attempts: number };
export type InvoicePollTransition =
  | { state: 'polling'; next: InvoicePollState }
  | { state: 'terminal'; invoice: ParentQuotaInvoice }
  | { state: 'timed-out' };

export function advanceInvoicePoll(state: InvoicePollState, invoices: readonly ParentQuotaInvoice[]): InvoicePollTransition {
  const invoice = invoices.find((item) => item.invoice_id === state.invoiceId);
  if (invoice && ['PAID', 'FAILED', 'CANCELED'].includes(invoice.state)) return { state: 'terminal', invoice };
  const attempts = state.attempts + 1;
  if (attempts >= INVOICE_POLL_MAX_ATTEMPTS) return { state: 'timed-out' };
  return { state: 'polling', next: { invoiceId: state.invoiceId, attempts } };
}

export async function pollParentInvoice(options: {
  invoiceId: string;
  fetchInvoices: () => Promise<ParentQuotaInvoicePage>;
  onInvoices?: (page: ParentQuotaInvoicePage) => void;
  wait?: (milliseconds: number) => Promise<void>;
  shouldContinue?: () => boolean;
}): Promise<{ state: 'terminal'; invoice: ParentQuotaInvoice } | { state: 'timed-out' | 'cancelled' }> {
  const wait = options.wait ?? ((milliseconds: number) => new Promise<void>((resolve) => setTimeout(resolve, milliseconds)));
  let state: InvoicePollState = { invoiceId: options.invoiceId, attempts: 0 };
  for (;;) {
    if (options.shouldContinue && !options.shouldContinue()) return { state: 'cancelled' };
    try {
      const page = await options.fetchInvoices();
      if (options.shouldContinue && !options.shouldContinue()) return { state: 'cancelled' };
      options.onInvoices?.(page);
      const transition = advanceInvoicePoll(state, page.items);
      if (transition.state !== 'polling') return transition;
      state = transition.next;
    } catch {
      const transition = advanceInvoicePoll(state, []);
      if (transition.state !== 'polling') return transition;
      state = transition.next;
    }
    await wait(INVOICE_POLL_INTERVAL_MS);
  }
}

export function terminalInvoiceMessage(invoice: ParentQuotaInvoice): ParentPaymentMessage | null {
  if (invoice.state === 'PAID') return { kind: 'success', text: 'Thanh toán đã được xác nhận; số lượt tạo video đã được cập nhật.' };
  if (invoice.state === 'FAILED') return { kind: 'failure', text: 'Hóa đơn đã hết hạn hoặc giao dịch chưa thành công. Bạn có thể tạo yêu cầu thanh toán mới.' };
  if (invoice.state === 'CANCELED') return { kind: 'failure', text: 'Hóa đơn đã được hủy. Bạn có thể chọn phương thức thanh toán khác.' };
  return null;
}

export function reconcileResultMessage(result: ParentQuotaReconcileResult): ParentPaymentMessage {
  if (result.state === 'PAID') return { kind: 'success', text: 'Thanh toán đã được xác nhận; số lượt tạo video đã được cập nhật.' };
  if (result.state === 'FAILED') return { kind: 'failure', text: 'Hóa đơn đã hết hạn hoặc giao dịch chưa thành công. Bạn có thể tạo yêu cầu thanh toán mới.' };
  if (result.state === 'CANCELED') return { kind: 'success', text: 'Hóa đơn đã được hủy. Bạn có thể chọn phương thức thanh toán khác.' };
  return { kind: 'pending', text: 'Cổng chưa có kết quả cuối. Hóa đơn vẫn được giữ; mở lại liên kết còn hạn hoặc kiểm tra lại sau.' };
}

export function cancelResultMessage(result: ParentQuotaCancelResult): ParentPaymentMessage {
  if (result.state === 'PAID') return { kind: 'success', text: 'Thanh toán đã được xác nhận; số lượt tạo video đã được cập nhật.' };
  if (result.state === 'FAILED') return { kind: 'failure', text: 'Giao dịch chưa thành công. Bạn có thể tạo yêu cầu mới hoặc chọn phương thức khác.' };
  if (result.state === 'CANCELED') return { kind: 'success', text: 'Đã hủy hóa đơn hết hạn. Bạn có thể chọn phương thức thanh toán khác để tạo yêu cầu mới.' };
  return { kind: 'pending', text: 'Chưa nhận được kết quả cuối. Hóa đơn vẫn được giữ an toàn; hãy kiểm tra lại sau.' };
}

export function quotaPaymentErrorMessage(failure: unknown): string {
  const record = isRecord(failure) ? failure : {};
  const code = isText(record.code) ? record.code : '';
  if (code === 'PAYMENT_PROVIDER_NOT_AVAILABLE') return 'Thanh toán hiện chưa sẵn sàng. Bạn vẫn có thể xem các gói và giá.';
  if (code === 'PAYMENT_ATTEMPT_ALREADY_OPEN') return 'Đã có hóa đơn chưa nhận được kết quả cuối. Mở lại nếu liên kết còn hạn hoặc kiểm tra lại sau khi hết hạn.';
  if (code === 'PAYMENT_PROVIDER_UNAVAILABLE') return 'Chưa kết nối được dịch vụ thanh toán. Hóa đơn vẫn được giữ; hãy kiểm tra lại trạng thái sau.';
  if (code === 'PAYMENT_ATTEMPT_NOT_RECONCILABLE') return 'Hóa đơn này không còn giao dịch nào cần kiểm tra.';
  if (code === 'PAYMENT_CHECKOUT_STILL_ACTIVE') return 'Chỉ có thể hủy sau khi liên kết thanh toán hết hạn. Khi còn hạn, liên kết vẫn có thể nhận thanh toán.';
  if (code === 'PAYMENT_CANCEL_PROVIDER_NOT_SUPPORTED') return 'Chưa thể hủy hóa đơn này. Hãy thử lại sau khi hóa đơn hết hạn.';
  if (code === 'PAYMENT_EXPIRY_UNAVAILABLE') return 'Không xác định được hạn thanh toán nên chưa thể hủy an toàn.';
  if (code === 'VNPAY_QUERY_RESPONSE_SIGNATURE_INVALID') return 'Chưa xác minh được giao dịch. Hóa đơn vẫn chưa được xác nhận; đừng thanh toán lại.';
  if (code === 'VNPAY_QUERY_GATEWAY_ERROR') return 'Dịch vụ thanh toán tạm thời gặp lỗi. Hóa đơn chưa được xác minh và số lượt tạo video chưa thay đổi. Hãy thử kiểm tra lại sau.';
  if (code === 'VNPAY_QUERY_RESPONSE_MISMATCH' || code === 'VNPAY_QUERY_INVALID_RESPONSE') return 'Thông tin thanh toán chưa khớp với hóa đơn. Trạng thái và số lượt tạo video chưa thay đổi; hãy thử kiểm tra lại sau.';
  if (code === 'VNPAY_QUERY_REJECTED') return 'Chưa xác nhận được giao dịch. Hóa đơn vẫn được giữ để kiểm tra; đừng tạo yêu cầu thanh toán khác lúc này.';
  if (code === 'MOMO_AMOUNT_OUT_OF_RANGE') return 'Giá gói chưa phù hợp với giới hạn giao dịch. Hãy chọn phương thức thanh toán khác hoặc thử lại sau.';
  if (code === 'INVOICE_NOT_FOUND') return 'Hóa đơn không còn khả dụng.';
  if (code === 'INVALID_API_RESPONSE') return 'Máy chủ trả về dữ liệu chưa đầy đủ. Hãy tải lại trạng thái.';
  if (code === 'NETWORK_ERROR') return 'Không kết nối được máy chủ.';
  if (code === 'REQUEST_TIMEOUT') return 'Yêu cầu quá thời gian chờ. Trạng thái thanh toán có thể chưa rõ; hãy kiểm tra trước khi thử lại.';
  if (code === 'IDEMPOTENCY_KEY_INVALID') return 'Chưa thể gửi yêu cầu thanh toán. Vui lòng bắt đầu lại thao tác.';
  if (record.status === 403) return 'Tài khoản không có quyền thao tác trong phạm vi này.';
  return 'Chưa thể hoàn tất thao tác. Vui lòng kiểm tra lại rồi thử sau.';
}
