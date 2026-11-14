import React from 'react';
import { Text } from 'react-native';
import type { LessonSummary } from '../../domain/types';
import { Card, ChoiceRow, Notice, ScreenFrame, palette } from '../components/ui';

type Props = {
  lessons: LessonSummary[];
  selectedId: string;
  loading: boolean;
  loadingId: string;
  error: string;
  onSelect: (lessonId: string) => void;
  onClear: () => void;
  onBack: () => void;
};

export function LessonPickerScreen(props: Props): React.JSX.Element {
  return (
    <ScreenFrame title="Thư viện giáo án" subtitle="Chọn và ghim phiên bản bài giảng bạn muốn dùng." step="Thư viện" onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {props.loading ? <Card><Text style={{ color: palette.muted }}>Đang tải giáo án…</Text></Card> : null}
      {!props.loading && !props.error && props.lessons.length === 0 ? <Notice text="Chưa có giáo án phù hợp. Bạn chưa thể tiếp tục nếu chưa ghim một phiên bản bài giảng." /> : null}
      {props.lessons.map((lesson) => (
        <Card key={lesson.lesson_id}>
          <ChoiceRow title={lesson.title} detail={`${lesson.topic} · phiên bản ${lesson.version_id} · ${lesson.activity_count} hoạt động`} selected={props.selectedId === lesson.lesson_id} onPress={() => props.onSelect(lesson.lesson_id)} />
          {props.loadingId === lesson.lesson_id ? <Text style={{ color: palette.muted, fontSize: 13 }}>Đang mở phiên bản…</Text> : null}
        </Card>
      ))}
    </ScreenFrame>
  );
}
