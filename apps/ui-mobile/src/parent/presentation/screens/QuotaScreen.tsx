import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import type { ParentVideoQuota } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, palette } from '../components/ui';

type Props = {
  capability: ParentCapabilityState;
  quota: ParentVideoQuota | null;
  loading: boolean;
  error: string;
  onLoad: () => void;
  onBack: () => void;
};

export function QuotaScreen(props: Props): React.JSX.Element {
  const { quota, loading, error, onLoad, onBack } = props;
  if (props.capability.state === 'unavailable') {
    return <ScreenFrame title="Lượt tạo video" subtitle="Thông tin sử dụng của gia đình." onBack={onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']} contentCentered>
      <View style={styles.stateCard}>
        <View style={styles.stateIcon}><Ionicons name="videocam-outline" size={24} color="#7435D5" accessible={false} /></View>
        <Text style={styles.stateTitle}>Lượt sử dụng chưa khả dụng</Text>
      </View>
    </ScreenFrame>;
  }

  const numbersReady = quota?.configuration_state === 'CONFIGURED'
    && quota.granted !== null && quota.used !== null && quota.available !== null;
  const ratio = numbersReady && quota.granted! > 0
    ? Math.max(0, Math.min(100, (quota.used! / quota.granted!) * 100))
    : 0;

  return (
    <ScreenFrame title="Lượt tạo video" subtitle="Theo dõi lượt dùng của gia đình." onBack={onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']}>
      <Card style={styles.summaryCard}>
        <View style={styles.summaryHeading}>
          <View style={styles.summaryIcon}><Ionicons name="videocam-outline" size={22} color="#7435D5" accessible={false} /></View>
          <View style={styles.summaryCopy}>
            <Text style={styles.summaryTitle}>Số lượt sử dụng</Text>
          </View>
        </View>
        {error ? <Notice variant="creative" text={error} tone="error" /> : null}

        {loading && !quota ? (
          <View style={styles.loadingState}><ActivityIndicator color="#7435D5" /><Text style={styles.helper}>Đang tải số liệu…</Text></View>
        ) : !quota && !error ? (
          <View style={styles.inlineState}>
            <Ionicons name="time-outline" size={18} color="#9A6C08" accessible={false} />
            <Text style={styles.inlineStateText}>Chưa có số liệu để hiển thị.</Text>
          </View>
        ) : !quota ? null : quota.configuration_state === 'NOT_CONFIGURED' ? (
          <View style={styles.inlineState}>
            <Ionicons name="hourglass-outline" size={18} color="#9A6C08" accessible={false} />
            <Text style={styles.inlineStateText}>Hạn mức chưa được thiết lập.</Text>
          </View>
        ) : numbersReady ? (
          <>
            <View style={styles.totalPanel}>
              <Text style={styles.totalLabel}>Còn lại</Text>
              <View style={styles.totalValueRow}>
                <Text style={styles.totalValue}>{quota.available}</Text>
                <Text style={styles.totalUnit}>lượt</Text>
              </View>
              <Text style={styles.usageText}>Đã dùng {quota.used} / {quota.granted} lượt</Text>
              <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: 100, now: ratio }} style={styles.track}>
                <View style={[styles.progress, { width: `${ratio}%` }]} />
              </View>
            </View>
            <View style={styles.periodRow}>
              <Ionicons name="calendar-clear-outline" size={17} color="#77658B" accessible={false} />
              <View style={styles.periodCopy}>
                <Text style={styles.periodLabel}>Kỳ sử dụng</Text>
                <Text style={styles.periodValue}>{formatDate(quota.period_start)} – {formatDate(quota.period_end)}</Text>
              </View>
            </View>
          </>
        ) : (
          <View style={styles.inlineState}>
            <Ionicons name="information-circle-outline" size={18} color="#376388" accessible={false} />
            <Text style={styles.infoStateText}>Chưa đủ dữ liệu hạn mức để hiển thị.</Text>
          </View>
        )}

        <PrimaryButton variant="creative" label="Cập nhật số liệu" busy={loading} onPress={onLoad} />
      </Card>
    </ScreenFrame>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('vi-VN');
}

const styles = StyleSheet.create({
  summaryCard: { gap: 16, backgroundColor: '#FFFEFF', borderColor: '#E5D7F2', borderWidth: 1.4, borderRadius: 23 },
  summaryHeading: { minWidth: 0, flexDirection: 'row', alignItems: 'center', gap: 10 },
  summaryIcon: { width: 44, height: 44, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  summaryCopy: { flex: 1, minWidth: 0, gap: 2 },
  summaryTitle: { color: '#281451', fontSize: 15, lineHeight: 20, fontWeight: '800' },
  totalPanel: { padding: 16, borderRadius: 19, backgroundColor: '#F5EEFF', borderWidth: 1, borderColor: '#E9DDF8' },
  totalLabel: { color: '#665576', fontSize: 12, lineHeight: 17, fontWeight: '700' },
  totalValueRow: { flexDirection: 'row', alignItems: 'baseline', gap: 7, marginTop: 2 },
  totalValue: { color: '#4F1C86', fontSize: 38, lineHeight: 44, fontWeight: '900', fontVariant: ['tabular-nums'] },
  totalUnit: { color: '#5B347B', fontSize: 14, lineHeight: 19, fontWeight: '800' },
  usageText: { color: '#6F6278', fontSize: 12, lineHeight: 17, marginTop: 4 },
  track: { height: 8, borderRadius: 4, marginTop: 12, backgroundColor: '#E2D5F1', overflow: 'hidden' },
  progress: { height: '100%', borderRadius: 4, backgroundColor: '#8A42DE' },
  periodRow: { minHeight: 48, flexDirection: 'row', alignItems: 'center', gap: 9, paddingHorizontal: 2 },
  periodCopy: { flex: 1, minWidth: 0, gap: 2 },
  periodLabel: { color: '#77658B', fontSize: 10, lineHeight: 14, fontWeight: '700' },
  periodValue: { color: '#332342', fontSize: 12, lineHeight: 17, fontWeight: '700', flexShrink: 1 },
  inlineState: { minHeight: 54, paddingHorizontal: 12, paddingVertical: 10, borderRadius: 15, flexDirection: 'row', alignItems: 'center', gap: 9, backgroundColor: '#FFF3D1' },
  inlineStateText: { flex: 1, color: '#72530D', fontSize: 12, lineHeight: 17, fontWeight: '700' },
  infoStateText: { flex: 1, color: '#315D7C', fontSize: 12, lineHeight: 17, fontWeight: '700' },
  loadingState: { minHeight: 96, alignItems: 'center', justifyContent: 'center', gap: 8 },
  helper: { color: '#756A80', fontSize: 11, lineHeight: 16, flexShrink: 1 },
  stateCard: { alignItems: 'center', gap: 10, paddingHorizontal: 24, paddingVertical: 26, borderRadius: 24, backgroundColor: '#FFFEFF', borderWidth: 1.2, borderColor: '#E5D7F2' },
  stateIcon: { width: 58, height: 58, borderRadius: 20, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  stateTitle: { color: '#281451', fontSize: 19, lineHeight: 25, fontWeight: '800', textAlign: 'center' },
});
