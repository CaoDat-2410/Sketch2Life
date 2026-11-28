import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ParentCandidate, ParentSubjectRoleV1 } from '../../domain/types';
import { Card, Field, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';
import { SecondarySubjectRow } from './SecondarySubjectRow';

type Props = {
  candidate: ParentCandidate;
  stepLabel: string;
  subject: string;
  busy: boolean;
  error: string;
  onSubject: (value: string) => void;
  /** FEAT-087: other objects found in the drawing. Empty for drawings analysed earlier. */
  subjectRoles?: ReadonlyArray<ParentSubjectRoleV1>;
  onRenameSecondary?: (entityId: ParentSubjectRoleV1['entity_id'], label: string) => void;
  onToggleSecondary?: (entityId: ParentSubjectRoleV1['entity_id']) => void;
  onMakeMain?: (entityId: ParentSubjectRoleV1['entity_id']) => void;
  /** FEAT-093: two subjects are too close to call; the main one must be chosen first. */
  needsChoice?: boolean;
  onKeepMain?: () => void;
  onConfirm: () => void;
  onBack: () => void;
};

export function UnderstandingScreen(props: Props): React.JSX.Element {
  const confidence = Math.max(0, Math.min(100, Math.round(props.candidate.confidence * 100)));
  const others = (props.subjectRoles ?? []).filter((role) => role.role !== 'main');
  // The drawing model gives no confidence value; the backend stores 0, so nothing is shown then.
  const hasConfidence = confidence > 0;
  return (
    <ScreenFrame
      title="Nhận diện tranh"
      subtitle="Kiểm tra gợi ý rồi xác nhận chủ thể cùng bé."
      step={props.stepLabel}
      onBack={props.onBack}
      visualTone="creative"
    >
      <Card variant="creative" style={styles.candidateCard}>
        <View style={styles.resultHeader}>
          <View style={styles.resultIcon}>
            <Ionicons name="scan-outline" size={22} color={palette.creativePrimary} />
          </View>
          <View style={styles.resultCopy}>
            <Text style={styles.eyebrow}>GỢI Ý TỪ BỨC TRANH</Text>
            <SectionTitle variant="creative">Chủ thể được nhận diện</SectionTitle>
          </View>
          {hasConfidence ? (
            <View style={styles.confidenceBadge}>
              <Text style={styles.confidenceValue}>{confidence}%</Text>
            </View>
          ) : null}
        </View>

        {hasConfidence ? (
          <>
            <View accessible accessibilityLabel={`Độ tin cậy gợi ý ${confidence} phần trăm`} style={styles.confidenceTrack}>
              <View style={[styles.confidenceFill, { width: `${confidence}%` }]} />
            </View>
            <Text style={styles.confidenceCaption}>Độ tin cậy của gợi ý</Text>
          </>
        ) : null}

        <Field
          variant="creative"
          label="Chủ thể trong tranh"
          value={props.subject}
          onChangeText={props.onSubject}
          placeholder="Ví dụ: một chú thỏ"
          returnKeyType="done"
        />

        <View style={styles.featureList}>
          <Text style={styles.featureTitle}>Những gì hệ thống nhìn thấy</Text>
          {props.candidate.visible_features.map((feature, index) => (
            <View key={`${index}-${feature}`} style={styles.featureRow}>
              <View style={styles.featureDot} />
              <Text style={styles.featureText}>{feature}</Text>
            </View>
          ))}
          {props.candidate.visible_features.length === 0 ? (
            <Text style={styles.emptyFeatures}>Chưa có đặc điểm được cung cấp.</Text>
          ) : null}
        </View>
        <Notice variant="creative" text="Đây là gợi ý để người lớn xem lại. Bạn có thể sửa tên chủ thể trước khi xác nhận." />
      </Card>
      {others.length > 0 ? (
        <Card variant="creative" style={styles.candidateCard}>
          <View style={styles.resultCopy}>
            <Text style={styles.eyebrow}>CÓ THỂ DÙNG TRONG TRUYỆN</Text>
            <SectionTitle variant="creative">Vật khác trong tranh</SectionTitle>
          </View>
          <Text style={styles.confidenceCaption}>Chỉ những vật đang bật mới được đưa vào truyện.</Text>
          {others.map((role) => (
            <SecondarySubjectRow
              key={role.entity_id}
              role={role}
              onRename={(label) => props.onRenameSecondary?.(role.entity_id, label)}
              onToggle={() => props.onToggleSecondary?.(role.entity_id)}
              onMakeMain={() => props.onMakeMain?.(role.entity_id)}
            />
          ))}
        </Card>
      ) : null}
      {props.needsChoice ? (
        <Card variant="creative" style={styles.candidateCard}>
          <SectionTitle variant="creative">Chọn nhân vật chính</SectionTitle>
          <Text style={styles.confidenceCaption}>
            Trong tranh có hai nhân vật gần như nổi bật như nhau. Hãy chọn ai là nhân vật chính của câu chuyện.
          </Text>
          <PrimaryButton
            variant="creative"
            label={`Giữ “${props.subject.trim() || 'chủ thể này'}” làm nhân vật chính`}
            onPress={() => props.onKeepMain?.()}
          />
          <Text style={styles.confidenceCaption}>Hoặc bấm “Đặt làm chủ thể chính” ở vật khác bên dưới.</Text>
        </Card>
      ) : null}
      {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
      <PrimaryButton variant="creative" label="Xác nhận chủ thể" busy={props.busy} disabled={!props.subject.trim() || props.needsChoice === true} onPress={props.onConfirm} />
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  candidateCard: { gap: 13 },
  resultHeader: { flexDirection: 'row', alignItems: 'center', gap: 10, minWidth: 0 },
  resultIcon: { width: 44, height: 44, borderRadius: 15, backgroundColor: palette.creativeLavender, alignItems: 'center', justifyContent: 'center' },
  resultCopy: { flex: 1, minWidth: 0, gap: 3 },
  eyebrow: { color: palette.creativePrimary, fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.5 },
  confidenceBadge: { minWidth: 48, height: 38, borderRadius: 13, paddingHorizontal: 7, backgroundColor: '#FFF2D0', alignItems: 'center', justifyContent: 'center' },
  confidenceValue: { color: '#7D5210', fontSize: 12, lineHeight: 17, fontWeight: '800' },
  confidenceTrack: { height: 7, borderRadius: 999, overflow: 'hidden', backgroundColor: '#EEE8F4' },
  confidenceFill: { height: '100%', borderRadius: 999, backgroundColor: palette.creativePrimary },
  confidenceCaption: { color: palette.creativeMuted, fontSize: 11, lineHeight: 15, marginTop: -8 },
  featureList: { gap: 8, padding: 12, borderRadius: 16, backgroundColor: '#F8F3FF' },
  featureTitle: { color: palette.creativeInk, fontSize: 12, lineHeight: 17, fontWeight: '800' },
  featureRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  featureDot: { width: 6, height: 6, marginTop: 6, borderRadius: 3, backgroundColor: palette.creativePrimary },
  featureText: { flex: 1, color: palette.creativeMuted, fontSize: 13, lineHeight: 18 },
  emptyFeatures: { color: palette.creativeMuted, fontSize: 13, lineHeight: 18 },
});
