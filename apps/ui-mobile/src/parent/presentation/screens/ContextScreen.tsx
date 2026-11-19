import React from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import type { ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, SecondaryButton, palette } from '../components/ui';
import { isConfirmedRunSubject } from '../navigation/parentFlowV1';

type Props = {
  profile: ParentProfileViewV1 | null;
  contextRun: ParentStoryRunV1 | null;
  stepLabel: string;
  busy: boolean;
  confirmed: boolean;
  error: string;
  onRetryCreate: () => void;
  onConfirm: () => void;
  onContinue: () => void;
  onBack?: () => void;
};

export function ContextScreen(props: Props): React.JSX.Element {
  const snapshot = props.contextRun?.context_snapshot;
  const lessonPin = props.contextRun?.lesson_pin_snapshot;
  const stepLabel = (props.contextRun?.understanding_revision ?? 0) > 0 ? '5 / 7' : props.stepLabel;
  const subject = props.contextRun?.subject_label ?? '';
  const subjectConfirmed = Boolean(props.contextRun && subject && isConfirmedRunSubject(props.contextRun, subject));
  const awaitingDrawing = props.contextRun?.current_input_revision === 1
    && (props.contextRun.understanding_revision ?? 0) < 1;

  return (
    <ScreenFrame
      title="Rà soát thông tin buổi"
      subtitle="Chỉ xem dữ liệu cần cho buổi học này."
      step={stepLabel}
      onBack={props.onBack}
    >
      {props.profile ? <Card style={styles.profileCard}>
        <SectionTitle>Hồ sơ được chọn</SectionTitle>
        <Text style={styles.profileText}>
          {props.profile.display_name} · {props.profile.age_months} tháng
        </Text>
      </Card> : null}

      <Card style={styles.snapshotCard}>
        <SectionTitle>Hồ sơ và bản nội dung</SectionTitle>
        {snapshot ? <>
          {props.contextRun?.profile_revision_ref ? <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Bản hồ sơ</Text>
            <Text style={styles.snapshotText}>{props.contextRun.profile_revision_ref}</Text>
          </View> : null}
          {snapshot.age_months !== undefined ? <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Tuổi trong buổi học</Text>
            <Text style={styles.snapshotText}>{snapshot.age_months} tháng</Text>
          </View> : null}
          {snapshot.interests_summary ? <Text style={styles.snapshotInterest}>
            Sở thích được phép dùng: {snapshot.interests_summary}
          </Text> : null}
          <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Chủ đề</Text>
            <Text style={styles.snapshotText}>{snapshot.topic || 'Chưa nhập chủ đề.'}</Text>
          </View>
          <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Ý tưởng của gia đình</Text>
            <Text style={styles.snapshotTextMuted}>{snapshot.adult_confirmed_idea || 'Chưa có ý tưởng được xác nhận.'}</Text>
          </View>
          {lessonPin ? <View style={styles.snapshotRow}>
            <Text style={styles.snapshotLabel}>Bài học đã ghim</Text>
            <Text style={styles.snapshotText}>Phiên bản {lessonPin.version_no} · {lessonPin.version_id}</Text>
          </View> : null}
        </> : props.busy ? <ActivityIndicator color={palette.blue} /> : <Text style={styles.snapshotEmpty}>
          Thông tin buổi học sẽ xuất hiện sau khi tạo buổi.
        </Text>}
      </Card>

      {props.contextRun && !subjectConfirmed ? <Notice
        text="Hãy xem và xác nhận chủ thể của tranh trước khi xác nhận ngữ cảnh."
        tone="warning"
      /> : null}
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {props.confirmed ? <>
        <Notice text="Ngữ cảnh đã được xác nhận." tone="success" />
        <SecondaryButton label="Tiếp tục" disabled={props.busy} onPress={props.onContinue} />
      </> : props.contextRun ? <PrimaryButton
        label="Xác nhận ngữ cảnh"
        busy={props.busy}
        disabled={props.busy || !subjectConfirmed}
        onPress={props.onConfirm}
      /> : <PrimaryButton
        label={props.error ? 'Thử lại' : 'Tạo buổi học'}
        busy={props.busy}
        disabled={props.busy}
        onPress={props.onRetryCreate}
      />}
      {awaitingDrawing ? <SecondaryButton
        label="Quay lại xem tranh"
        disabled={props.busy}
        onPress={props.onContinue}
      /> : null}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  profileCard: { backgroundColor: palette.white, gap: 8, minWidth: 0 },
  profileText: { color: palette.ink, fontSize: 16, lineHeight: 22, fontWeight: '700', minWidth: 0, flexShrink: 1 },
  snapshotCard: { backgroundColor: palette.white, gap: 14, minWidth: 0 },
  snapshotRow: { gap: 4, minWidth: 0 },
  snapshotLabel: { color: palette.muted, fontSize: 10, lineHeight: 14, fontWeight: '800', minWidth: 0, flexShrink: 1 },
  snapshotText: { color: palette.ink, fontSize: 14, lineHeight: 21, minWidth: 0, flexShrink: 1 },
  snapshotTextMuted: { color: palette.muted, fontSize: 14, lineHeight: 21, minWidth: 0, flexShrink: 1 },
  snapshotInterest: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
  snapshotEmpty: { color: palette.muted, fontSize: 13, lineHeight: 18, minWidth: 0, flexShrink: 1 },
});
