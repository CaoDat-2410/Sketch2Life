import React from 'react';
import { Text, View } from 'react-native';
import type { SuggestedActivity } from '../../domain/types';
import { Card, Notice, PrimaryButton, SecondaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';

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
  const usedFallback = props.source === 'AI_GENERATED_FALLBACK';
  return (
    <ScreenFrame title="Gợi ý hoạt động" subtitle="Bước này là tùy chọn. Bỏ qua vẫn tiếp tục tạo kịch bản." step={props.stepLabel} onBack={props.onBack}>
      {usedFallback ? <Notice text="Chưa tìm thấy hoạt động phù hợp trong bài học được chia sẻ. Đây là 3 bản nháp AI; người lớn vui lòng xem lại." tone="warning" /> : null}
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {!props.requested && !props.error ? <Card><Text style={{ color: palette.muted, fontSize: 14, lineHeight: 21 }}>AI sẽ tìm hoạt động phù hợp trong các bài học con có thể xem.</Text><PrimaryButton label="Tìm hoạt động phù hợp" busy={props.busy} onPress={props.onSuggest} /></Card> : null}
      {props.activities.map((activity, index) => (
        <Card key={`${index}-${activity.title}`}>
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}><SectionTitle>{activity.title}</SectionTitle><Text style={{ color: palette.blue, fontSize: 11, fontWeight: '800' }}>NGOÀI TRỜI</Text></View>
          <Text style={{ color: palette.muted, fontSize: 12, fontWeight: '700' }}>{sourceLabel(activity)}</Text>
          {activity.match_reason && activity.source !== 'AI_GENERATED_DRAFT' ? <Text style={{ color: palette.ink, fontSize: 13, lineHeight: 19 }}>Phù hợp vì: {activity.match_reason}</Text> : null}
          <Text style={{ color: palette.ink, fontSize: 14, lineHeight: 20 }}>{activity.objective}</Text>
          <Text style={{ color: palette.muted, fontSize: 13, lineHeight: 19 }}>Chuẩn bị: {activity.materials_text || 'Không có vật liệu đặc biệt'}{activity.preparation_text ? ` · ${activity.preparation_text}` : ''}</Text>
          <Text style={{ color: palette.ink, fontSize: 14, lineHeight: 21 }}>{activity.instructions_text}</Text>
          {activity.safety_notes ? <Notice text={`Lưu ý: ${activity.safety_notes}`} tone="warning" /> : null}
        </Card>
      ))}
      {props.requested && !props.error && !props.activities.length ? <Notice text="Chưa có hoạt động để xem. Bạn có thể tiếp tục đến kịch bản." /> : null}
      {props.requested || props.error ? <PrimaryButton label="Tiếp tục đến kịch bản" disabled={props.busy} onPress={props.onSkip} /> : <SecondaryButton label="Bỏ qua gợi ý" disabled={props.busy} onPress={props.onSkip} />}
    </ScreenFrame>
  );
}

function sourceLabel(activity: SuggestedActivity): string {
  if (activity.source === 'PINNED_LESSON') return `Bài đã chọn · ${activity.source_lesson_title ?? 'bài học'}`;
  if (activity.source === 'PUBLISHED_SHARED_LESSON') return `Bài đã chia sẻ · ${activity.source_lesson_title ?? 'bài học'}`;
  return 'Gợi ý mới từ AI · bản nháp';
}
