import { afterEach, describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { ParentApi } from '../src/parent/infrastructure/http/ParentApi';
import {
  canResumeInvoicePayment,
  CHECKOUT_URL_MISSING_COPY,
  CheckoutIdentityMap,
  enabledQuotaProviders,
  invoicePaymentAttempt,
  pollParentInvoice,
  quotaPaymentErrorMessage,
  readParentQuotaInvoices,
  readParentQuotaPaymentSettings,
  reconcileSecondsRemaining,
  RECONCILE_COOLDOWN_MS,
  withReconcileCooldown,
} from '../src/parent/application/parentQuota';
import type { ParentQuotaInvoice, ParentQuotaPaymentSettings } from '../src/parent/domain/types';
import { isVideoQuotaExceededError, safeParentFlowErrorMessage } from '../src/parent/presentation/navigation/parentFlowV1';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { firebaseApiKey: 'synthetic-firebase-key', apiBaseUrl: 'https://api.synthetic.test' },
}));

const summary = {
  owner_kind: 'PARENT_ACCOUNT',
  available_units: 4,
  granted_units: 6,
  used_units: 2,
  grants: [{ grant_id: 'grant-1', kind: 'INCLUDED', units: 2, used: 1, available: 1, period: '2026-11', expires_at: '2026-12-01T00:00:00Z' }],
  allocation: null,
};
const product = {
  product_id: 'product-1',
  offer_id: 'offer-1',
  version: 3,
  display_name: 'Gói mua thêm',
  offer_kind: 'TOP_UP',
  cycle_months: null,
  units: 5,
  amount_vnd: 249000,
  active: true,
};
const invoice: ParentQuotaInvoice = {
  invoice_id: 'invoice-1',
  units: 5,
  amount_vnd: 249000,
  state: 'PENDING',
  provider: 'MOMO',
  payment_mode: 'MANUAL',
  created_at: null,
  attempts: [{ provider: 'MOMO', state: 'OPEN', checkout_url: 'https://sandbox.momo.test/pay', expires_at: '2026-12-01T00:00:00Z' }],
};
const paymentSettings: ParentQuotaPaymentSettings = {
  real_payments_enabled: true,
  momo_checkout_enabled: true,
  vnpay_checkout_enabled: false,
  momo_sandbox_enabled: true,
  vnpay_sandbox_enabled: true,
  monthly_auto_renew_enabled: false,
};

afterEach(() => {
  vi.useRealTimers();
});

describe('Parent quota and payment contracts', () => {
  it('calls all seven Parent billing routes with web-compatible methods, query, headers, and body', async () => {
    const payloads = [
      summary,
      { items: [product] },
      { items: [invoice], total: 1 },
      paymentSettings,
      { invoice_id: 'invoice-2', state: 'PENDING', checkout_url: 'https://sandbox.momo.test/checkout' },
      { invoice_id: 'invoice-1', state: 'PAID', reconciled: true },
      { invoice_id: 'invoice-1', state: 'CANCELED', canceled: true, reconciled: true },
    ];
    const requests: { url: string; init?: RequestInit }[] = [];
    const fetcher = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      requests.push({ url: String(input), init });
      const body = payloads.shift();
      return new Response(JSON.stringify(body), { status: requests.length === 5 ? 201 : 200 });
    }) as unknown as typeof fetch;
    const auth = { getIdToken: vi.fn(async () => 'verified-parent-token') };
    const api = new ParentApi(auth, fetcher, 'https://api.synthetic.test');

    await api.getVideoQuota();
    await api.getQuotaProducts();
    await api.getQuotaInvoices(50);
    await api.getQuotaPaymentSettings();
    await api.checkoutQuotaProduct('product-1', 'MOMO', 'checkout-key-1');
    await api.reconcileQuotaInvoice('invoice/1');
    await api.cancelQuotaInvoice('invoice/1');

    expect(requests.map(({ url, init }) => [url, init?.method])).toEqual([
      ['https://api.synthetic.test/api/be1/v1/billing/video-quota', 'GET'],
      ['https://api.synthetic.test/api/be1/v1/billing/video-quota/products', 'GET'],
      ['https://api.synthetic.test/api/be1/v1/billing/video-quota/invoices?limit=50', 'GET'],
      ['https://api.synthetic.test/api/be1/v1/billing/video-quota/payment-settings', 'GET'],
      ['https://api.synthetic.test/api/be1/v1/billing/video-quota/checkout', 'POST'],
      ['https://api.synthetic.test/api/be1/v1/billing/video-quota/invoices/invoice%2F1/reconcile', 'POST'],
      ['https://api.synthetic.test/api/be1/v1/billing/video-quota/invoices/invoice%2F1/cancel', 'POST'],
    ]);
    expect(new Headers(requests[0].init?.headers).get('Authorization')).toBe('Bearer verified-parent-token');
    expect(new Headers(requests[4].init?.headers).get('Idempotency-Key')).toBe('checkout-key-1');
    expect(JSON.parse(String(requests[4].init?.body))).toEqual({ product_id: 'product-1', provider: 'MOMO', payment_mode: 'MANUAL' });
    expect(requests[5].init?.body).toBeUndefined();
    expect(requests[6].init?.body).toBeUndefined();
  });

  it('reads invoice fields from the web contract and hides checkout links after expiry', () => {
    const page = readParentQuotaInvoices({ items: [invoice], total: 1 });
    expect(page?.items[0]).toMatchObject({
      invoice_id: 'invoice-1', state: 'PENDING', provider: 'MOMO', payment_mode: 'MANUAL',
      attempts: [{ provider: 'MOMO', state: 'OPEN', checkout_url: invoice.attempts[0].checkout_url }],
    });
    expect(canResumeInvoicePayment(invoice, Date.parse('2026-11-30T00:00:00Z'))).toBe(true);
    expect(canResumeInvoicePayment(invoice, Date.parse('2026-12-02T00:00:00Z'))).toBe(false);
    expect(invoicePaymentAttempt({ ...invoice, state: 'PAID' })).toBeUndefined();
    expect(readParentQuotaPaymentSettings(paymentSettings)).toEqual(paymentSettings);
  });

  it('gates provider buttons by settings and labels enabled sandbox providers', () => {
    expect(enabledQuotaProviders(paymentSettings)).toEqual([{ provider: 'MOMO', sandbox: true }]);
    expect(enabledQuotaProviders({ ...paymentSettings, vnpay_checkout_enabled: true })).toEqual([
      { provider: 'MOMO', sandbox: true },
      { provider: 'VNPAY', sandbox: true },
    ]);
    expect(enabledQuotaProviders({ ...paymentSettings, momo_checkout_enabled: false })).toEqual([]);
  });

  it('reuses a checkout key on retry and clears it after success or an input change', () => {
    const keys = new CheckoutIdentityMap();
    let next = 0;
    const create = () => `test-key-${++next}`;
    expect(keys.get('product-1', 'MOMO', create)).toBe('test-key-1');
    expect(keys.get('product-1', 'MOMO', create)).toBe('test-key-1');
    keys.complete('product-1', 'MOMO');
    expect(keys.get('product-1', 'MOMO', create)).toBe('test-key-2');
    expect(keys.get('product-2', 'VNPAY', create)).toBe('test-key-3');
    expect(keys.get('product-1', 'MOMO', create)).toBe('test-key-4');
  });

  it.each(['PAID', 'FAILED', 'CANCELED'] as const)('polls until invoice state is %s', async (terminalState) => {
    vi.useFakeTimers();
    const terminalInvoice = { ...invoice, state: terminalState };
    const fetchInvoices = vi.fn()
      .mockResolvedValueOnce({ items: [invoice], total: 1 })
      .mockResolvedValueOnce({ items: [terminalInvoice], total: 1 });
    const promise = pollParentInvoice({
      invoiceId: invoice.invoice_id,
      fetchInvoices,
      wait: (milliseconds) => new Promise<void>((resolve) => setTimeout(resolve, milliseconds)),
    });
    await vi.advanceTimersByTimeAsync(0);
    await vi.advanceTimersByTimeAsync(2_000);
    await expect(promise).resolves.toMatchObject({ state: 'terminal', invoice: { state: terminalState } });
    expect(fetchInvoices).toHaveBeenCalledTimes(2);
  });

  it('applies the five-minute reconcile cooldown and clears it after a terminal response', () => {
    const started = withReconcileCooldown({}, 'invoice-1', RECONCILE_COOLDOWN_MS);
    expect(reconcileSecondsRemaining(started, 'invoice-1', 0)).toBe(300);
    expect(reconcileSecondsRemaining(started, 'invoice-1', 296_000)).toBe(4);
    const cleared = withReconcileCooldown(started, 'invoice-1', null);
    expect(reconcileSecondsRemaining(cleared, 'invoice-1', 1)).toBe(0);
  });

  it('uses safe checkout and error copy without exposing error codes or URLs', () => {
    expect(CHECKOUT_URL_MISSING_COPY).toBe('Chưa thể mở trang thanh toán. Hãy thử lại sau.');
    expect(quotaPaymentErrorMessage({ code: 'PAYMENT_PROVIDER_NOT_AVAILABLE', message: 'https://private.test/body' })).toBe(
      'Thanh toán hiện chưa sẵn sàng. Bạn vẫn có thể xem các gói và giá.',
    );
    const fallback = quotaPaymentErrorMessage({ code: 'PRIVATE_PROVIDER_CODE', message: 'https://private.test/body' });
    expect(fallback).not.toContain('PRIVATE_PROVIDER_CODE');
    expect(fallback).not.toContain('https://');
    expect(CHECKOUT_URL_MISSING_COPY).not.toMatch(/https?:\/\//);
  });

  it('opens the system browser, resumes polling through AppState, and clears screen-only invoice data', () => {
    const controller = readFileSync(new URL('../src/parent/presentation/navigation/useParentPlatformController.ts', import.meta.url), 'utf8');
    expect(controller).toContain('Linking.openURL(checkoutUrl)');
    expect(controller).toContain("AppState.addEventListener('change'");
    expect(controller).toContain('quotaPollCancel.current?.()');
    expect(controller).toContain('setQuotaInvoices([])');
    expect(controller).not.toContain('sessionStorage');
    expect(controller).not.toContain('AsyncStorage');
  });

  it('keeps VIDEO_QUOTA_EXCEEDED mapped to the safe message and the purchase action', () => {
    const videoScreen = readFileSync(new URL('../src/parent/presentation/screens/VideoScreen.tsx', import.meta.url), 'utf8');
    expect(isVideoQuotaExceededError({ code: 'VIDEO_QUOTA_EXCEEDED' })).toBe(true);
    expect(isVideoQuotaExceededError({ code: 'PRIVATE_CODE' })).toBe(false);
    const message = safeParentFlowErrorMessage({ code: 'VIDEO_QUOTA_EXCEEDED' });
    expect(message).toBe('Hiện chưa còn lượt tạo video khả dụng. Hãy xem tóm tắt hạn mức hoặc mua thêm lượt.');
    expect(message).not.toContain('VIDEO_QUOTA_EXCEEDED');
    expect(videoScreen).toContain('label="Mua thêm lượt"');
    expect(videoScreen).toContain('onPress={props.onOpenQuota}');
    expect(videoScreen).toContain('quotaSummary');
  });

  it('loads the quota summary once after exhaustion and keeps purchase available if it fails', () => {
    const app = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
    const videoScreen = readFileSync(new URL('../src/parent/presentation/screens/VideoScreen.tsx', import.meta.url), 'utf8');
    expect(app).toContain('platform.loadQuotaSummary().then');
    expect(app).toContain('[parent.videoQuotaExceeded]');
    expect(app).toContain('quotaSummary={videoQuotaSummaryLoaded ? platform.quota : null}');
    expect(videoScreen).toContain("grant.kind === 'INCLUDED'");
    expect(videoScreen).toContain("grant.kind === 'TOP_UP'");
    expect(videoScreen).toContain('Lượt tháng còn {remainingByGrantKind.included} · lượt mua thêm còn {remainingByGrantKind.topUp}.');
    expect(videoScreen).toContain('props.quotaExceeded ? <SecondaryButton variant="creative" label="Mua thêm lượt"');
    expect(videoScreen).not.toContain('props.quotaExceeded && props.quotaSummary ? <SecondaryButton');
  });
});
