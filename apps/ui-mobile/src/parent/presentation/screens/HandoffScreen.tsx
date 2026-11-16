import React from 'react';
import { Text, View } from 'react-native';
import type { TimedEvent } from '../navigation/workflowTypes';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  storyTitle: string;
  events: TimedEvent[];
  onRestart: () => void;
};

export function HandoffScreen({ storyTitle, events, onRestart }: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Kịch bản đã sẵn sàng" subtitle="Người lớn đã xác nhận nội dung cuối." step="Hoàn tất phần kiểm thử">
      <Card>
        <Text style={{ color: palette.green, fontSize: 38, fontWeight: '800' }}>✓</Text>
        <SectionTitle>{storyTitle || 'Kịch bản đã xác nhận'}</SectionTitle>
        <Notice text="Buổi kiểm thử dừng trước bước tạo video. Tranh gốc và kịch bản được giữ trong run theo quyền truy cập hiện hành." tone="success" />
      </Card>
      <Card>
        <SectionTitle>Kết quả các yêu cầu</SectionTitle>
        {events.map((event, index) => <View key={`${event.stage}-${index}`} style={{ flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 7, borderBottomWidth: index === events.length - 1 ? 0 : 1, borderBottomColor: '#E7EDF4' }}><Text style={{ color: palette.ink, fontSize: 13, flex: 1 }}>{event.status === 'PASS' ? '✓' : '×'} {event.stage}</Text><Text style={{ color: event.status === 'PASS' ? palette.green : palette.red, fontSize: 12, fontWeight: '800' }}>{(event.durationMs / 1000).toFixed(1)} giây</Text></View>)}
      </Card>
      <PrimaryButton label="Về hồ sơ" onPress={onRestart} />
    </ScreenFrame>
  );
}
