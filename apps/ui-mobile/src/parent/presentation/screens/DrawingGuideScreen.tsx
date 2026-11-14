import React from 'react';
import { StyleSheet, Text } from 'react-native';
import type { LessonDetail } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, SecondaryButton, palette } from '../components/ui';
import { clampDrawingGuideIndex, parseDrawingGuideSteps } from '../navigation/parentFlowV1';

type Props = {
  lesson: LessonDetail;
  stepLabel: string;
  currentIndex: number;
  onIndexChange: (index: number) => void;
  onContinue: () => void;
  onBack: () => void;
};

export function DrawingGuideScreen(props: Props): React.JSX.Element {
  const guide = parseDrawingGuideSteps(props.lesson.drawing_steps_text);
  const stepCount = guide.kind === 'steps' ? guide.steps.length : 0;
  const currentIndex = clampDrawingGuideIndex(props.currentIndex, stepCount);
  return (
    <ScreenFrame
      title="Gợi ý vẽ (tùy chọn)"
      subtitle="Có thể bỏ qua hướng dẫn bất cứ lúc nào. Không ảnh hưởng việc chụp tranh."
      step={props.stepLabel}
      onBack={props.onBack}
    >
      <Card style={styles.guideCard}>
        <SectionTitle>{props.lesson.title}</SectionTitle>
        <Text style={styles.lessonPinText}>
          Phiên bản bài học đã ghim vẫn được giữ nguyên trong buổi học.
        </Text>
        {guide.kind === 'steps' ? <>
          <Text accessibilityRole="header" style={styles.currentStep}>
            Bước {currentIndex + 1} / {stepCount}
          </Text>
          <Text style={styles.stepText}>{guide.steps[currentIndex]}</Text>
          <SecondaryButton
            label={currentIndex + 1 < stepCount ? 'Bước tiếp' : 'Quay lại bước đầu'}
            onPress={() => props.onIndexChange(currentIndex + 1 < stepCount ? currentIndex + 1 : 0)}
          />
        </> : <Notice text="Hướng dẫn 4–8 bước có thứ tự hiện chưa khả dụng. Bạn vẫn có thể tiếp tục." tone="warning" />}
      </Card>
      <PrimaryButton label="Bỏ qua hướng dẫn" onPress={props.onContinue} />
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  guideCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  lessonPinText: { color: palette.muted, fontSize: 14, lineHeight: 21, minWidth: 0, flexShrink: 1 },
  currentStep: { color: palette.ink, fontSize: 10, lineHeight: 14, fontWeight: '800', paddingHorizontal: 8, paddingVertical: 5, borderRadius: 12, borderWidth: 1.2, borderColor: palette.outline, backgroundColor: palette.butter, alignSelf: 'flex-start', flexShrink: 1 },
  stepText: { color: palette.ink, fontSize: 15, lineHeight: 23, minWidth: 0, flexShrink: 1 },
});
