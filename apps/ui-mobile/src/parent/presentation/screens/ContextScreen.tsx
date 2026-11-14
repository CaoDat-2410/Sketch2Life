import React from 'react';
import { ActivityIndicator, Text } from 'react-native';
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
      title="Kiểm tra ngữ cảnh"
      subtitle="Người lớn xem lại chủ đề và gợi ý trước khi xác nhận buổi học."
      step={stepLabel}
      onBack={props.onBack}
    >
      {props.profile ? <Card>
        <SectionTitle>Hồ sơ được chọn</SectionTitle>
        <Text style={{ color: palette.ink, fontSize: 16, fontWeight: '700' }}>
          {props.profile.display_name} · {props.profile.age_months} tháng
        </Text>
      </Card> : null}

      <Card>
        <SectionTitle>Chủ đề và gợi ý từ người lớn</SectionTitle>
        {snapshot ? <>
          <Text style={{ color: palette.ink, fontSize: 14, lineHeight: 21 }}>Chủ đề: {snapshot.topic}</Text>
          <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 21 }}>Gợi ý: {snapshot.adult_confirmed_idea}</Text>
          {snapshot.interests_summary ? <Text style={{ color: palette.muted, fontSize: 13, lineHeight: 19 }}>
            Sở thích đã lưu: {snapshot.interests_summary}
          </Text> : null}
        </> : props.busy ? <ActivityIndicator color={palette.blue} /> : <Text style={{ color: palette.muted }}>
          Hãy chuẩn bị buổi học để xem lại chủ đề và gợi ý.
        </Text>}
        {lessonPin ? <Notice text="Bài học đã chọn được gắn với buổi học này." tone="success" /> : null}
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
