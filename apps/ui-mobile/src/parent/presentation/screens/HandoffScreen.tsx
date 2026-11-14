import React from 'react';
import { Text, View } from 'react-native';
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
    ? 'Tạo video, kiểm tra an toàn và phát video chưa khả dụng vì chưa có hợp đồng dịch vụ được xác nhận. Không có yêu cầu video nào được gửi.'
    : handoffJobStageMessage(jobStage);

  return (
    <ScreenFrame title="Kịch bản đã xác nhận" subtitle="Trạng thái video và hoàn tất buổi học cần được máy chủ xác nhận." step="Trạng thái buổi học">
      <Card>
        <SectionTitle>{storyTitle || 'Kịch bản đã xác nhận'}</SectionTitle>
        <Notice text={videoMessage} tone="warning" />
        <Notice text="Không có video để phát hoặc tải xuống. Trạng thái hoàn tất chưa được máy chủ xác nhận." tone="info" />
      </Card>
      <Card>
        <SectionTitle>Kết quả các yêu cầu</SectionTitle>
        {events.map((event, index) => <View key={`${event.stage}-${index}`} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 7, borderBottomWidth: index === events.length - 1 ? 0 : 1, borderBottomColor: '#E7EDF4' }}><Text style={{ color: palette.ink, fontSize: 13, flex: 1 }}>{event.status === 'PASS' ? '✓' : '×'} {event.stage}</Text><Text style={{ color: event.status === 'PASS' ? palette.green : palette.red, fontSize: 12, fontWeight: '800' }}>{(event.durationMs / 1000).toFixed(1)} giây</Text></View>)}
      </Card>
      <PrimaryButton label="Tiếp tục buổi học đang mở" onPress={onResumeActiveRun} />
    </ScreenFrame>
  );
}

function handoffJobStageMessage(stage: ParentJobStageState): string {
  if (stage.state === 'idle') return 'Chưa có tác vụ video.';
  if (stage.state === 'pending') return 'Tác vụ video đang chờ xử lý; chưa có kết quả hoàn tất.';
  if (stage.state === 'reconciling') return 'Đang kiểm tra trạng thái tác vụ video. Không gửi yêu cầu trùng lặp.';
  if (stage.state === 'confirmed') return 'Tác vụ video hoàn tất theo trạng thái máy chủ; chưa có trình phát được nối.';
  if (stage.state === 'failed') return 'Tác vụ video thất bại theo trạng thái máy chủ.';
  return 'Trạng thái tác vụ video chưa khả dụng.';
}
