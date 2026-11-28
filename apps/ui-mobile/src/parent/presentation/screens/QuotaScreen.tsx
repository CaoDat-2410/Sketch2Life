import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import {
  canResumeInvoicePayment,
  enabledQuotaProviders,
  getOpenParentInvoice,
  invoicePaymentAttempt,
  paymentAttemptExpired,
  type ParentPaymentMessage,
  type ParentPaymentProvider,
} from '../../application/parentQuota';
import type {
  ParentQuotaInvoice,
  ParentQuotaPaymentSettings,
  ParentQuotaProduct,
  ParentVideoQuota,
} from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle } from '../components/ui';

type Props = {
  capability: ParentCapabilityState;
  quota: ParentVideoQuota | null;
  products: ParentQuotaProduct[];
  invoices: ParentQuotaInvoice[];
  paymentSettings: ParentQuotaPaymentSettings | null;
  loading: boolean;
  checkoutBusy: boolean;
  actionInvoiceId: string;
  error: string;
  paymentStatus: ParentPaymentMessage | null;
  now: number;
  reconcileSecondsRemaining: (invoiceId: string) => number;
  onLoad: () => void;
  onCheckout: (productId: string, provider: ParentPaymentProvider) => void;
  onResumePayment: (invoiceId: string, url: string) => void;
  onReconcile: (invoiceId: string) => void;
  onCancel: (invoiceId: string) => void;
  onBack: () => void;
};

export function QuotaScreen(props: Props): React.JSX.Element {
  const {
    quota, products, invoices, paymentSettings, loading, checkoutBusy, actionInvoiceId, error,
    paymentStatus, now, reconcileSecondsRemaining, onLoad, onCheckout, onResumePayment,
    onReconcile, onCancel, onBack,
  } = props;

  if (props.capability.state === 'unavailable') {
    return <ScreenFrame title="Lượt tạo video" subtitle="Thông tin sử dụng của gia đình." onBack={onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']} contentCentered>
      <View style={styles.stateCard}>
        <View style={styles.stateIcon}><Ionicons name="videocam-outline" size={24} color="#7435D5" accessible={false} /></View>
        <Text style={styles.stateTitle}>Lượt sử dụng chưa khả dụng</Text>
      </View>
    </ScreenFrame>;
  }

  const openInvoice = getOpenParentInvoice(invoices);
  const openAttempt = openInvoice ? invoicePaymentAttempt(openInvoice) : undefined;
  const openExpired = paymentAttemptExpired(openAttempt?.expires_at ?? null, now);
  const openLinkAvailable = Boolean(openInvoice && canResumeInvoicePayment(openInvoice, now));
  const providers = paymentSettings ? enabledQuotaProviders(paymentSettings) : [];
  const paymentEnvironmentLabel = providers.length === 0
    ? 'Thanh toán trực tuyến chưa khả dụng'
    : 'Có thể thanh toán trực tuyến';
  const includedGrants = quota?.grants.filter((grant) => grant.kind !== 'TOP_UP') ?? [];
  const topUpGrants = quota?.grants.filter((grant) => grant.kind === 'TOP_UP') ?? [];

  return (
    <ScreenFrame title="Lượt tạo video" subtitle="Theo dõi số dư và thanh toán của gia đình." onBack={onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']}>
      {error ? <Notice variant="creative" text={error} tone="error" /> : null}
      {paymentStatus ? <Text accessibilityRole="alert" style={[styles.paymentMessage, paymentStatus.kind === 'success' ? styles.paymentSuccess : paymentStatus.kind === 'failure' ? styles.paymentFailure : styles.paymentPending]}>{paymentStatus.text}</Text> : null}

      <Card style={styles.card}>
        <SectionTitle variant="creative">Số dư lượt video</SectionTitle>
        {loading && !quota ? (
          <View style={styles.loadingState}><ActivityIndicator color="#7435D5" /><Text style={styles.helper}>Đang tải số liệu…</Text></View>
        ) : quota ? (
          <>
            <View style={styles.totalPanel}>
              <Text style={styles.totalLabel}>Còn lại</Text>
              <View style={styles.totalValueRow}><Text style={styles.totalValue}>{number(quota.available_units)}</Text><Text style={styles.totalUnit}>lượt</Text></View>
              <Text style={styles.helper}>Đã dùng {number(quota.used_units)} / {number(quota.granted_units)} lượt</Text>
            </View>
            <GrantGroup title="Lượt được cấp" emptyText="Chưa có lượt được cấp." grants={includedGrants} />
            <GrantGroup title="Lượt mua thêm" emptyText="Chưa có lượt mua thêm." grants={topUpGrants} />
          </>
        ) : !error ? <Text style={styles.helper}>Chưa có số liệu để hiển thị.</Text> : null}
        <PrimaryButton variant="creative" label="Cập nhật số liệu" busy={loading} onPress={onLoad} />
      </Card>

      {openInvoice ? (
        <Card style={styles.pendingCard}>
          <View style={styles.pendingHeading}>
            <Ionicons name="alert-circle-outline" size={21} color="#9A6C08" accessible={false} />
            <Text style={styles.pendingTitle}>{openLinkAvailable ? 'Có hóa đơn đang chờ thanh toán' : openExpired ? 'Liên kết đã hết hạn · chờ xác minh giao dịch' : 'Giao dịch đang chờ xác nhận'}</Text>
          </View>
          <Text style={styles.bodyText}>Có một giao dịch đang chờ. {pendingInvoiceCopy(openAttempt, openExpired, openLinkAvailable)}</Text>
          {openLinkAvailable && openAttempt?.checkout_url ? <SecondaryButton variant="creative" label="Mở lại thanh toán" disabled={Boolean(actionInvoiceId)} onPress={() => onResumePayment(openInvoice.invoice_id, openAttempt.checkout_url!)} /> : null}
          {openInvoice.provider === 'VNPAY' && openExpired ? <SecondaryButton variant="creative" label={actionInvoiceId === openInvoice.invoice_id ? 'Đang xử lý…' : 'Hủy giao dịch đã hết hạn'} disabled={Boolean(actionInvoiceId)} onPress={() => onCancel(openInvoice.invoice_id)} /> : null}
          <SecondaryButton
            variant="creative"
            label={actionInvoiceId === openInvoice.invoice_id ? 'Đang kiểm tra…' : reconcileLabel(openInvoice.invoice_id, reconcileSecondsRemaining)}
            disabled={Boolean(actionInvoiceId) || reconcileSecondsRemaining(openInvoice.invoice_id) > 0}
            onPress={() => onReconcile(openInvoice.invoice_id)}
          />
        </Card>
      ) : null}

      <Card style={styles.card}>
        <View style={styles.sectionHeading}>
          <View style={styles.flex}><SectionTitle variant="creative">Gói lượt video</SectionTitle><Text style={styles.helper}>Gói và giá do hệ thống cung cấp.</Text></View>
          <Text style={styles.environment}>{paymentEnvironmentLabel}</Text>
        </View>
        {!products.length ? <Text style={styles.helper}>Hiện chưa có gói lượt nào được mở bán.</Text> : products.map((product) => (
          <View key={product.product_id} style={styles.productCard}>
            <View style={styles.productTop}><Text style={styles.productKind}>{product.offer_kind === 'MONTHLY' ? 'Gói tháng' : 'Mua thêm'}</Text></View>
            <Text style={styles.productName}>{product.display_name}</Text>
            <Text style={styles.productUnits}>{number(product.units)} lượt video</Text>
            <Text style={styles.productPrice}>{money(product.amount_vnd)}</Text>
            <Text style={styles.helper}>{product.offer_kind === 'MONTHLY' ? 'Lượt được cấp theo tháng dương lịch; thanh toán thủ công mỗi kỳ.' : 'Lượt mua thêm không hết hạn cho đến khi được sử dụng.'}</Text>
            <View style={styles.providerButtons}>
              {providers.map(({ provider }) => (
                <PrimaryButton
                  key={provider}
                  variant="creative"
                  label={providerLabel(provider)}
                  busy={checkoutBusy}
                  disabled={checkoutBusy || Boolean(openInvoice)}
                  onPress={() => onCheckout(product.product_id, provider)}
                />
              ))}
              {providers.length === 0 && paymentSettings?.real_payments_enabled === false ? <SecondaryButton variant="creative" label="Thanh toán chưa khả dụng" disabled onPress={() => undefined} /> : null}
            </View>
          </View>
        ))}
        <Text style={styles.helper}>{paymentSettings?.monthly_auto_renew_enabled ? 'Gia hạn tự động đã sẵn sàng.' : 'Gói tháng hiện thanh toán thủ công.'}</Text>
      </Card>

      <Card style={styles.card}>
        <View style={styles.sectionHeading}><SectionTitle variant="creative">Hóa đơn gần đây</SectionTitle><Text style={styles.environment}>{number(invoices.length)} hóa đơn</Text></View>
        {!invoices.length ? <Text style={styles.helper}>Chưa có giao dịch. Thông tin sẽ xuất hiện sau khi bắt đầu thanh toán.</Text> : invoices.map((invoice, index) => {
          const attempt = invoicePaymentAttempt(invoice);
          const canResume = canResumeInvoicePayment(invoice, now);
          const remaining = reconcileSecondsRemaining(invoice.invoice_id);
          return (
            <View key={`${invoice.invoice_id}-${index}`} style={styles.invoiceRow}>
              <View style={styles.invoiceTop}><Text style={styles.invoiceTitle}>Giao dịch thanh toán</Text><Text style={styles.invoiceState}>{invoiceStateLabel(invoice, attempt, now)}</Text></View>
              <Text style={styles.helper}>{number(invoice.units)} lượt · {providerLabel(invoice.provider)}</Text>
              <Text style={styles.invoiceAmount}>{money(invoice.amount_vnd)}</Text>
              <Text style={styles.helper}>{invoice.created_at ? formatDateTime(invoice.created_at) : 'Ngày tạo chưa có'}</Text>
              {canResume && attempt?.checkout_url ? <SecondaryButton variant="creative" label="Mở lại thanh toán" disabled={Boolean(actionInvoiceId)} onPress={() => onResumePayment(invoice.invoice_id, attempt.checkout_url!)} /> : null}
              {invoice.state === 'PENDING' ? <SecondaryButton
                variant="creative"
                label={actionInvoiceId === invoice.invoice_id ? 'Đang kiểm tra…' : reconcileLabel(invoice.invoice_id, reconcileSecondsRemaining)}
                disabled={Boolean(actionInvoiceId) || remaining > 0}
                onPress={() => onReconcile(invoice.invoice_id)}
              /> : null}
              {invoice.state === 'PENDING' && !canResume ? <Text style={styles.helper}>{attempt?.expires_at && paymentAttemptExpired(attempt.expires_at, now) ? `Liên kết hết hạn lúc ${formatDateTime(attempt.expires_at)}` : 'Đang chờ xác nhận giao dịch'}</Text> : null}
            </View>
          );
        })}
        <Text style={styles.helper}>Đóng trang thanh toán không tự hủy hóa đơn. Liên kết hết hạn cần được xác minh trước khi tạo giao dịch mới.</Text>
      </Card>
    </ScreenFrame>
  );
}

function GrantGroup(props: { title: string; emptyText: string; grants: ParentVideoQuota['grants'] }): React.JSX.Element {
  return <View style={styles.grantGroup}>
    <Text style={styles.grantHeading}>{props.title}</Text>
    {props.grants.length ? props.grants.map((grant) => <View key={grant.grant_id} style={styles.grantRow}>
      <View style={styles.flex}><Text style={styles.grantBalance}>{number(grant.available)} còn / {number(grant.units)} lượt</Text><Text style={styles.helper}>{grant.expires_at ? `Hết hạn ${formatDate(grant.expires_at)}` : grant.period ? `Kỳ ${grant.period}` : 'Không hết hạn'}</Text></View>
      <Text style={styles.helper}>Đã dùng {number(grant.used)}</Text>
    </View>) : <Text style={styles.helper}>{props.emptyText}</Text>}
  </View>;
}

function pendingInvoiceCopy(attempt: ParentQuotaInvoice['attempts'][number] | undefined, expired: boolean, hasCheckout: boolean): string {
  if (hasCheckout && attempt?.expires_at) return `Bạn có thể thanh toán đến ${formatDateTime(attempt.expires_at)}. Lượt chỉ được cộng sau khi giao dịch được xác nhận.`;
  if (hasCheckout) return 'Bạn có thể tiếp tục thanh toán qua liên kết này. Lượt chỉ được cộng sau khi giao dịch được xác nhận.';
  if (expired) return 'Liên kết thanh toán đã hết hạn nhưng giao dịch chưa có kết quả cuối. Đừng thanh toán lại khi chưa xác minh; hãy kiểm tra trạng thái trước khi chọn phương thức khác.';
  return 'Đóng trang thanh toán không hủy hóa đơn. Hóa đơn chưa có liên kết còn hạn để mở lại; hãy kiểm tra trạng thái trước khi thử phương thức khác.';
}

function invoiceStateLabel(invoice: ParentQuotaInvoice, attempt: ParentQuotaInvoice['attempts'][number] | undefined, now: number): string {
  if (invoice.state === 'PAID') return 'Đã thanh toán';
  if (invoice.state === 'FAILED') return 'Thất bại';
  if (invoice.state === 'CANCELED') return 'Đã hủy';
  if (attempt?.state === 'UNKNOWN') return 'Đang đối soát';
  if (attempt?.expires_at && paymentAttemptExpired(attempt.expires_at, now)) return 'Chờ xác minh';
  return 'Chờ thanh toán';
}

function reconcileLabel(invoiceId: string, remaining: (invoiceId: string) => number, idleLabel = 'Kiểm tra trạng thái'): string {
  const seconds = remaining(invoiceId);
  if (seconds <= 0) return idleLabel;
  const minutes = Math.floor(seconds / 60);
  return `Kiểm tra lại sau ${minutes}:${String(seconds % 60).padStart(2, '0')}`;
}

function providerLabel(provider: string): string {
  if (provider === 'MOMO') return 'Thanh toán qua ví điện tử';
  if (provider === 'VNPAY') return 'Thanh toán trực tuyến';
  return 'Phương thức thanh toán';
}

function number(value: number): string { return new Intl.NumberFormat('vi-VN').format(value); }
function money(value: number): string { return `${number(value)} ₫`; }
function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('vi-VN');
}
function formatDateTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

const styles = StyleSheet.create({
  card: { gap: 14, backgroundColor: '#FFFEFF', borderColor: '#E5D7F2', borderWidth: 1.2, borderRadius: 22 },
  pendingCard: { gap: 12, backgroundColor: '#FFF8E7', borderColor: '#F0D99E', borderWidth: 1.2, borderRadius: 20 },
  pendingHeading: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  pendingTitle: { flex: 1, color: '#674B0A', fontSize: 14, lineHeight: 19, fontWeight: '800' },
  bodyText: { color: '#5F526B', fontSize: 12, lineHeight: 18 },
  totalPanel: { padding: 16, borderRadius: 18, backgroundColor: '#F5EEFF', borderWidth: 1, borderColor: '#E9DDF8', gap: 3 },
  totalLabel: { color: '#665576', fontSize: 12, lineHeight: 17, fontWeight: '700' },
  totalValueRow: { flexDirection: 'row', alignItems: 'baseline', gap: 7 },
  totalValue: { color: '#4F1C86', fontSize: 36, lineHeight: 42, fontWeight: '900', fontVariant: ['tabular-nums'] },
  totalUnit: { color: '#5B347B', fontSize: 14, lineHeight: 19, fontWeight: '800' },
  grantGroup: { gap: 7 },
  grantHeading: { color: '#332342', fontSize: 13, lineHeight: 18, fontWeight: '800' },
  grantRow: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 11, borderRadius: 14, backgroundColor: '#FAF7FC' },
  grantBalance: { color: '#332342', fontSize: 12, lineHeight: 17, fontWeight: '800' },
  helper: { color: '#756A80', fontSize: 11, lineHeight: 16 },
  loadingState: { minHeight: 80, alignItems: 'center', justifyContent: 'center', gap: 8 },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  flex: { flex: 1, minWidth: 0, gap: 3 },
  environment: { color: '#69577D', fontSize: 10, lineHeight: 14, fontWeight: '700', textAlign: 'right', flexShrink: 1 },
  productCard: { gap: 8, padding: 14, borderRadius: 17, backgroundColor: '#FBF8FF', borderWidth: 1, borderColor: '#E9DFF2' },
  productTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  productKind: { color: '#6E3AA8', fontSize: 10, lineHeight: 14, fontWeight: '800' },
  productName: { color: '#281451', fontSize: 15, lineHeight: 20, fontWeight: '800' },
  productUnits: { color: '#564266', fontSize: 13, lineHeight: 18, fontWeight: '700' },
  productPrice: { color: '#4F1C86', fontSize: 17, lineHeight: 22, fontWeight: '900' },
  providerButtons: { gap: 8, marginTop: 2 },
  invoiceRow: { gap: 7, paddingVertical: 12, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#E7DDF0' },
  invoiceTop: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  invoiceTitle: { flex: 1, color: '#332342', fontSize: 12, lineHeight: 17, fontWeight: '800' },
  invoiceState: { color: '#6E5C7C', fontSize: 10, lineHeight: 14, fontWeight: '700' },
  invoiceAmount: { color: '#4F1C86', fontSize: 14, lineHeight: 19, fontWeight: '800' },
  paymentMessage: { padding: 12, borderRadius: 14, fontSize: 12, lineHeight: 18, fontWeight: '700' },
  paymentSuccess: { color: '#1C6A47', backgroundColor: '#E5F7EC' },
  paymentFailure: { color: '#9A3535', backgroundColor: '#FFF0EE' },
  paymentPending: { color: '#72530D', backgroundColor: '#FFF3D1' },
  stateCard: { alignItems: 'center', gap: 10, paddingHorizontal: 24, paddingVertical: 26, borderRadius: 24, backgroundColor: '#FFFEFF', borderWidth: 1.2, borderColor: '#E5D7F2' },
  stateIcon: { width: 58, height: 58, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  stateTitle: { color: '#281451', fontSize: 19, lineHeight: 25, fontWeight: '800', textAlign: 'center' },
});
