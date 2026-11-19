import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { ParentCandidate } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  candidate: ParentCandidate;
  stepLabel: string;
  subject: string;
  busy: boolean;
  error: string;
  onSubject: (value: string) => void;
  onConfirm: () => void;
  onBack: () => void;
};

export function UnderstandingScreen(props: Props): React.JSX.Element {
  const confidence = Math.max(0, Math.min(100, Math.round(props.candidate.confidence * 100)));
  return (
    <ScreenFrame title="Xác nhận chủ thể" subtitle="Người lớn kiểm tra trước khi tiếp tục." step={props.stepLabel === '5 / 7' ? '4 / 7' : props.stepLabel} onBack={props.onBack}>
      <Card style={styles.candidateCard}>
        <Notice text="CẦN XÁC NHẬN" tone="warning" />
        <View style={styles.headingRow}>
          <View style={styles.headingCopy}><SectionTitle>Ứng viên chủ thể</SectionTitle></View>
          <Text style={styles.confidenceBadge}>{confidence}%</Text>
        </View>
        <Field label="Chủ thể người lớn xác nhận" value={props.subject} onChangeText={props.onSubject} placeholder="Nhập chủ thể trong tranh" />
        <View style={styles.featureList}>
          <Text style={styles.featureTitle}>Đặc điểm nhìn thấy</Text>
          {props.candidate.visible_features.map((feature, index) => <Text key={`${index}-${feature}`} style={styles.featureText}>• {feature}</Text>)}
          {props.candidate.visible_features.length === 0 ? <Text style={styles.emptyFeatures}>Chưa có đặc điểm được cung cấp.</Text> : null}
        </View>
        <Notice text="Người lớn có thể sửa chủ thể. Chỉ tiếp tục sau khi xác nhận." />
        <Notice text="Chưa có dữ liệu xác định chủ đề có khớp với tranh hay không. Người lớn có thể sửa chủ thể; bài học đã ghim được giữ nguyên." tone="warning" />
      </Card>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      <PrimaryButton label="Xác nhận chủ thể này" busy={props.busy} disabled={!props.subject.trim()} onPress={props.onConfirm} />
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  candidateCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  headingRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, minWidth: 0 },
  headingCopy: { flex: 1, minWidth: 0 },
  confidenceBadge: { color: palette.ink, fontSize: 9, lineHeight: 13, fontWeight: '800', minHeight: 24, textAlignVertical: 'center', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 12, borderWidth: 1.3, borderColor: palette.outline, backgroundColor: palette.butter },
  featureList: { gap: 7, padding: 12, borderRadius: 12, borderWidth: 1.3, borderColor: palette.outline, backgroundColor: palette.white, minWidth: 0 },
  featureTitle: { color: palette.ink, fontSize: 12, lineHeight: 16, fontWeight: '800', minWidth: 0, flexShrink: 1 },
  featureText: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
  emptyFeatures: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
});
