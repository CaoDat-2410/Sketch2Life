import React from 'react';
import { Text, View } from 'react-native';
import type { SuggestedActivity } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  stepLabel: string;
  activities: SuggestedActivity[];
  source: string;
  busy: boolean;
  requested: boolean;
  error: string;
  onSuggest: () => void;
  onSkip: () => void;
  onBack: () => void;
};

export function ActivityScreen(props: Props): React.JSX.Element {
  const pinnedActivities = props.activities.filter((activity) => activity.source === 'PINNED_LESSON');
  const pinExample = pinnedActivities[0];
  return (
    <ScreenFrame title="Hoạt động trong bài học" subtitle="Hoạt động chính chưa khả dụng. Bạn vẫn có thể tiếp tục tạo kịch bản." step={props.stepLabel} onBack={props.onBack}>
      <Notice text="Hoạt động chính: chưa khả dụng. Chưa thể chọn hoạt động, tạo bản nháp hoặc thay thế hoạt động." tone="warning" />
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {pinExample ? <Notice
        text={'Chỉ đọc từ phiên bản đã ghim · ' + (pinExample.source_lesson_version_id ?? 'không rõ phiên bản') + ' · SHA-256 ' + (pinExample.source_content_sha256 ?? 'không rõ hash')}
      /> : null}
      {pinnedActivities.length ? <Card>
        <SectionTitle>Hoạt động chỉ để tham khảo</SectionTitle>
        <Text style={{ color: palette.muted, fontSize: 13, lineHeight: 19 }}>
          Danh sách này đến từ đúng bài học đã ghim và không có thao tác chọn.
        </Text>
      </Card> : <Card>
        <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 21 }}>
          Chưa có hoạt động của phiên bản ghim để hiển thị.
        </Text>
      </Card>}
      {pinnedActivities.map((activity, index) => (
        <Card key={String(index) + '-' + activity.title}>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <SectionTitle>{activity.title}</SectionTitle>
            <Text style={{ color: palette.blue, fontSize: 11, fontWeight: '800' }}>{activityKindLabel(activity.activity_kind)}</Text>
          </View>
          <Text style={{ color: palette.muted, fontSize: 12, fontWeight: '700' }}>{sourceLabel(activity)}</Text>
          <Text style={{ color: palette.ink, fontSize: 14, lineHeight: 20 }}>{activity.objective}</Text>
          <Text style={{ color: palette.muted, fontSize: 13, lineHeight: 19 }}>
            Chuẩn bị: {activity.materials_text || 'Không có vật liệu đặc biệt'}{activity.preparation_text ? ' · ' + activity.preparation_text : ''}
          </Text>
          <Text style={{ color: palette.ink, fontSize: 14, lineHeight: 21 }}>{activity.instructions_text}</Text>
          {activity.safety_notes ? <Notice text={'Lưu ý: ' + activity.safety_notes} tone="warning" /> : null}
        </Card>
      ))}
      <PrimaryButton label="Tiếp tục đến kịch bản" disabled={props.busy} onPress={props.onSkip} />
    </ScreenFrame>
  );
}

function sourceLabel(activity: SuggestedActivity): string {
  return 'Bài đã ghim · ' + (activity.source_lesson_title ?? 'bài học')
    + ' · phiên bản ' + (activity.source_lesson_version_id ?? 'không rõ');
}

function activityKindLabel(kind: SuggestedActivity['activity_kind']): string {
  if (kind === 'indoor') return 'TRONG NHÀ';
  if (kind === 'mixed') return 'TRONG NHÀ VÀ NGOÀI TRỜI';
  return 'NGOÀI TRỜI';
}
