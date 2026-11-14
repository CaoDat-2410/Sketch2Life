import React from 'react';
import { StyleSheet, Text } from 'react-native';
import type { LessonSummary } from '../../domain/types';
import { Card, ChoiceRow, Notice, ScreenFrame, SectionTitle, palette } from '../components/ui';

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
    <ScreenFrame title="Bài học từ thư viện" subtitle="Chỉ nội dung công khai hoặc được chia sẻ mới có thể chọn." step="Thư viện" onBack={props.onBack}>
      <Card style={styles.introCard}>
        <SectionTitle>{props.selectedId ? 'Bài học đang được chọn' : 'Chưa ghim bài học'}</SectionTitle>
        <Text style={styles.introText}>Hãy chọn một phiên bản bài học chính xác để tiếp tục.</Text>
      </Card>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {props.loading ? <Card style={styles.loadingCard}><Text style={styles.loadingText}>Đang tải giáo án…</Text></Card> : null}
      {!props.loading && !props.error && props.lessons.length === 0 ? <Notice text="Chưa có bài học phù hợp. Bạn chưa thể tiếp tục nếu chưa ghim một phiên bản bài học." /> : null}
      {props.lessons.map((lesson) => (
        <Card key={lesson.lesson_id} style={styles.lessonCard}>
          <ChoiceRow title={lesson.title} detail={`${lesson.topic} · phiên bản ${lesson.version_id} · ${lesson.activity_count} hoạt động`} selected={props.selectedId === lesson.lesson_id} onPress={() => props.onSelect(lesson.lesson_id)} />
          {props.loadingId === lesson.lesson_id ? <Text style={styles.loadingText}>Đang mở phiên bản…</Text> : null}
        </Card>
      ))}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  introCard: { backgroundColor: palette.white, gap: 8, minWidth: 0 },
  introText: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
  loadingCard: { backgroundColor: palette.white, minWidth: 0 },
  loadingText: { color: palette.muted, fontSize: 13, lineHeight: 19, minWidth: 0, flexShrink: 1 },
  lessonCard: { backgroundColor: palette.white, gap: 8, minWidth: 0 },
});
