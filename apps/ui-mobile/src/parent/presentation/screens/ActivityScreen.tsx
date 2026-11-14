import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
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
    <ScreenFrame title="Gợi ý hoạt động" subtitle="Hoạt động chính chưa khả dụng. Bạn vẫn có thể tiếp tục tạo kịch bản." step={props.stepLabel} onBack={props.onBack}>
      <Notice text="Hoạt động chính: chưa khả dụng. Chưa thể chọn hoạt động, tạo bản nháp hoặc thay thế hoạt động." tone="warning" />
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {pinExample ? <Notice
        text={'Chỉ đọc từ phiên bản đã ghim · ' + (pinExample.source_lesson_version_id ?? 'không rõ phiên bản') + ' · SHA-256 ' + (pinExample.source_content_sha256 ?? 'không rõ hash')}
      /> : null}
      {pinnedActivities.length ? <Card style={styles.pinnedIntroCard}>
        <SectionTitle>Hoạt động chỉ để tham khảo</SectionTitle>
        <Text style={styles.bodyText}>
          Danh sách này đến từ đúng bài học đã ghim và không có thao tác chọn.
        </Text>
      </Card> : <Card style={styles.emptyCard}>
        <Text style={styles.emptyText}>
          Chưa có hoạt động của phiên bản ghim để hiển thị.
        </Text>
      </Card>}
      {pinnedActivities.map((activity, index) => (
        <Card key={String(index) + '-' + activity.title} style={styles.activityCard}>
          <View style={styles.activityHeading}>
            <Text style={styles.activityTitle}>{activity.title}</Text>
            <Text style={styles.activityKind}>{activityKindLabel(activity.activity_kind)}</Text>
          </View>
          <Text style={styles.sourceText}>{sourceLabel(activity)}</Text>
          <Text style={styles.objectiveText}>{activity.objective}</Text>
          <Text style={styles.bodyText}>
            Chuẩn bị: {activity.materials_text || 'Không có vật liệu đặc biệt'}{activity.preparation_text ? ' · ' + activity.preparation_text : ''}
          </Text>
          <Text style={styles.instructionsText}>{activity.instructions_text}</Text>
          {activity.safety_notes ? <Notice text={'Lưu ý: ' + activity.safety_notes} tone="warning" /> : null}
        </Card>
      ))}
      <PrimaryButton label="Tiếp tục đến kịch bản" disabled={props.busy} onPress={props.onSkip} />
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  pinnedIntroCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  emptyCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  activityCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  activityHeading: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, minWidth: 0 },
  activityTitle: { color: palette.ink, fontSize: 16, lineHeight: 20, fontWeight: '800', flex: 1, flexShrink: 1, minWidth: 0 },
  activityKind: { color: palette.blue, backgroundColor: palette.paleBlue, fontSize: 10, lineHeight: 14, fontWeight: '800', paddingHorizontal: 7, paddingVertical: 3, minHeight: 24, borderWidth: 1, borderColor: '#CFC3B3', borderRadius: 999, flexShrink: 1, minWidth: 0, textAlign: 'right' },
  sourceText: { color: palette.muted, fontSize: 12, lineHeight: 17, fontWeight: '700', flexShrink: 1, minWidth: 0 },
  objectiveText: { color: palette.ink, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  bodyText: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  instructionsText: { color: palette.ink, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
  emptyText: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0 },
});

function sourceLabel(activity: SuggestedActivity): string {
  return 'Bài đã ghim · ' + (activity.source_lesson_title ?? 'bài học')
    + ' · phiên bản ' + (activity.source_lesson_version_id ?? 'không rõ');
}

function activityKindLabel(kind: SuggestedActivity['activity_kind']): string {
  if (kind === 'indoor') return 'TRONG NHÀ';
  if (kind === 'mixed') return 'TRONG NHÀ VÀ NGOÀI TRỜI';
  if (kind === 'outdoor') return 'NGOÀI TRỜI';
  return 'Chưa xác định loại hoạt động';
}
