import React from 'react';
import { Text } from 'react-native';
import type { LessonSummary } from '../../domain/types';
import { Card, ChoiceRow, Notice, PrimaryButton, ScreenFrame, palette } from '../components/ui';

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
    <ScreenFrame title="Thư viện giáo án" subtitle="Chỉ tải danh sách khi bạn mở thư viện." step="Tùy chọn" onBack={props.onBack}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {props.loading ? <Card><Text style={{ color: palette.muted }}>Đang tải giáo án…</Text></Card> : null}
      {!props.loading && props.lessons.length === 0 ? <Notice text="Chưa có giáo án phù hợp. Bạn vẫn có thể tiếp tục mà không chọn." /> : null}
      {props.lessons.map((lesson) => (
        <Card key={lesson.lesson_id}>
          <ChoiceRow title={lesson.title} detail={`${lesson.topic} · ${lesson.activity_count} hoạt động`} selected={props.selectedId === lesson.lesson_id} onPress={() => props.onSelect(lesson.lesson_id)} />
          {props.loadingId === lesson.lesson_id ? <Text style={{ color: palette.muted, fontSize: 13 }}>Đang mở phiên bản…</Text> : null}
        </Card>
      ))}
      <PrimaryButton label="Tiếp tục không dùng giáo án" onPress={props.onClear} />
    </ScreenFrame>
  );
}
