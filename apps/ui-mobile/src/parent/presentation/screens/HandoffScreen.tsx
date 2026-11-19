import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { ParentCapabilityState, ParentJobStageState } from '../../application/ports/ParentCapabilityPorts';
import type { TimedEvent } from '../navigation/workflowTypes';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  storyTitle: string;
  events: TimedEvent[];
  videoCapability: ParentCapabilityState;
  jobStage: ParentJobStageState;
  onResumeActiveRun: () => void;
};

export function HandoffScreen({ storyTitle, events, videoCapability, jobStage, onResumeActiveRun }: Props): React.JSX.Element {
  const videoMessage = videoCapability.state === 'unavailable'
    ? 'Tạo video chưa khả dụng vì dịch vụ chưa được xác nhận.'
    : handoffJobStageMessage(jobStage);
  const videoTone = videoCapability.state === 'unavailable' || jobStage.state === 'failed'
    ? 'warning'
    : jobStage.state === 'confirmed' ? 'success' : 'info';

  return (
    <ScreenFrame title="Trạng thái buổi học" subtitle="Tiến độ được máy chủ ghi nhận.">
      <Card style={styles.statusCard}>
        <Text style={styles.handoffStoryTitle}>{storyTitle || 'Kịch bản đã xác nhận'}</Text>
        <Notice text={videoMessage} tone={videoTone} />
      </Card>
      {events.length ? <Card style={styles.eventsCard}>
        <SectionTitle>Các bước xử lý</SectionTitle>
        {events.map((event, index) => <View key={`${event.stage}-${index}`} style={[styles.eventRow, { borderBottomWidth: index === events.length - 1 ? 0 : 1.3 }]}>
          <Text style={[styles.eventSymbol, { color: event.status === 'PASS' ? palette.green : palette.red }]}>{event.status === 'PASS' ? '✓' : '!'}</Text>
          <View style={styles.eventCopy}>
            <Text style={styles.eventTitle}>{eventStageLabel(event.stage)}</Text>
            <Text style={[styles.eventResult, { color: event.status === 'PASS' ? palette.green : palette.red }]}>{event.status === 'PASS' ? 'Đã xác nhận' : 'Chưa hoàn tất'}</Text>
          </View>
        </View>)}
      </Card> : null}
      <PrimaryButton label="Tiếp tục buổi học đang mở" onPress={onResumeActiveRun} />
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  statusCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  eventsCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  eventRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, paddingVertical: 8, borderBottomColor: '#CFC3B3', minWidth: 0 },
  handoffStoryTitle: { color: palette.ink, fontSize: 16, lineHeight: 20, fontWeight: '800', flexShrink: 1, minWidth: 0 },
  eventSymbol: { fontSize: 17, lineHeight: 25, fontWeight: '800', flexShrink: 0 },
  eventCopy: { flex: 1, gap: 2, minWidth: 0 },
  eventTitle: { color: palette.ink, fontSize: 11, lineHeight: 15, fontWeight: '700', flexShrink: 1, minWidth: 0 },
  eventResult: { fontSize: 10, lineHeight: 14, fontWeight: '700', flexShrink: 1, minWidth: 0 },
});

function eventStageLabel(stage: string): string {
  const labels: Record<string, string> = {
    'parent-story-run-create': 'Mở buổi học',
    'drawing-understanding': 'Phân tích tranh',
    'story-rewrite': 'Viết lại kịch bản',
    'story-create': 'Tạo kịch bản',
  };
  return labels[stage] ?? 'Giai đoạn chưa xác định';
}

function handoffJobStageMessage(stage: ParentJobStageState): string {
  if (stage.state === 'idle') return 'Chưa có tác vụ video.';
  if (stage.state === 'pending') return 'Video đang được xử lý.';
  if (stage.state === 'reconciling') return 'Đang kiểm tra trạng thái; chưa gửi lại yêu cầu.';
  if (stage.state === 'confirmed') return 'Tác vụ hoàn tất; trình phát chưa khả dụng.';
  if (stage.state === 'failed') return 'Tác vụ video thất bại.';
  return 'Trạng thái tác vụ video chưa khả dụng.';
}
