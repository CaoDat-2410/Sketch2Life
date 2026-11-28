import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentConsentPolicyV1 } from '../../domain/types';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { Card, Notice, PrimaryButton, ScreenFrame, palette } from '../components/ui';

type Props = {
  onLoad: () => Promise<ParentConsentPolicyV1>;
  onBack: () => void;
};

export function ConsentPolicyScreen({ onLoad, onBack }: Props): React.JSX.Element {
  const [policy, setPolicy] = useState<ParentConsentPolicyV1 | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState('');

  async function load(): Promise<void> {
    setBusy(true);
    setError('');
    try {
      setPolicy(await onLoad());
    } catch (failure) {
      setPolicy(null);
      setError(consentFailureMessage(failure));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => { void load(); }, []);

  return <ScreenFrame
    title="Chính sách đồng ý"
    subtitle="Thông tin chính sách do dịch vụ cung cấp."
    onBack={onBack}
    visualTone="creative"
    safeAreaEdges={['top', 'right', 'left']}
  >
    {busy ? <View style={styles.loading}><ActivityIndicator color={palette.creativePrimary} /><Text style={styles.body}>Đang tải chính sách…</Text></View> : null}
    {error ? <Card variant="creative" style={styles.card}>
      <Notice variant="creative" text={error} tone="warning" />
      <PrimaryButton label="Thử lại" onPress={() => void load()} />
    </Card> : null}
    {policy ? <>
      <Card variant="creative" style={styles.noticeCard}>
        <View style={styles.heading}>
          <View style={styles.icon}><Ionicons name="flask-outline" size={19} color="#895600" accessible={false} /></View>
          <View style={styles.copy}>
            <Text accessibilityRole="header" style={styles.title}>Dữ liệu minh họa</Text>
            <Text style={styles.body}>Chưa thể chấp thuận hoặc ghi nhận đồng ý tại đây.</Text>
          </View>
        </View>
      </Card>
      <Card variant="creative" style={styles.card}>
        <Text style={styles.label}>Trạng thái</Text>
        <Text style={styles.value}>Bản nháp chưa được phê duyệt</Text>
        <Text style={styles.label}>Nội dung chính sách</Text>
        <Text selectable style={styles.policyText}>{policy.policy.consent_text}</Text>
        {policy.policy.purposes.length > 0 ? <Text style={styles.body}>Mục đích xử lý được trình bày trong nội dung chính sách ở trên.</Text> : null}
        <Text style={styles.footer}>Việc chấp thuận chưa khả dụng. Chính sách này không kích hoạt chia sẻ dữ liệu thật.</Text>
      </Card>
    </> : null}
  </ScreenFrame>;
}

function consentFailureMessage(failure: unknown): string {
  if (failure instanceof ParentApplicationError) {
    if (failure.status === 403 || failure.status === 404) return 'Chính sách hiện chưa khả dụng cho tài khoản này.';
    if (failure.status === 503) return 'Chính sách hiện chưa khả dụng. Hãy thử lại sau.';
  }
  return 'Chưa tải được chính sách. Hãy thử lại sau.';
}

const styles = StyleSheet.create({
  loading: { flexDirection: 'row', alignItems: 'center', gap: 10, padding: 14 },
  card: { gap: 12, backgroundColor: '#FFFEFF', borderColor: '#E5D7F2', borderWidth: 1.2, borderRadius: 21 },
  noticeCard: { gap: 10, backgroundColor: '#FFF9E9', borderColor: '#F0D89D', borderWidth: 1.2, borderRadius: 21 },
  heading: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  icon: { width: 39, height: 39, borderRadius: 14, backgroundColor: '#FFF0C4', alignItems: 'center', justifyContent: 'center' },
  copy: { flex: 1, gap: 3 },
  title: { color: '#684500', fontSize: 14, lineHeight: 19, fontWeight: '800' },
  label: { color: '#766783', fontSize: 11, lineHeight: 15, fontWeight: '700' },
  value: { color: '#332342', fontSize: 12, lineHeight: 17, fontWeight: '700' },
  policyText: { color: '#332342', fontSize: 14, lineHeight: 23 },
  body: { color: palette.muted, fontSize: 12, lineHeight: 18, flexShrink: 1 },
  footer: { color: '#805316', fontSize: 11, lineHeight: 17 },
});
