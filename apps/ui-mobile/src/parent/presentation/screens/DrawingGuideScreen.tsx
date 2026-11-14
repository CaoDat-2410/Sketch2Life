import React from 'react';
import { Text } from 'react-native';
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
      title="Hướng dẫn vẽ từng bước"
      subtitle="Hướng dẫn là tùy chọn. Người lớn có thể tiếp tục chọn ảnh."
      step={props.stepLabel}
      onBack={props.onBack}
    >
      <Card>
        <SectionTitle>{props.lesson.title}</SectionTitle>
        <Text style={{ color: palette.muted, fontSize: 14, lineHeight: 21 }}>
          Phiên bản bài học đã ghim vẫn được giữ nguyên trong buổi học.
        </Text>
        {guide.kind === 'steps' ? <>
          <Text accessibilityRole="header" style={{ color: palette.ink, fontSize: 16, fontWeight: '800' }}>
            Bước {currentIndex + 1} / {stepCount}
          </Text>
          <Text style={{ color: palette.ink, fontSize: 15, lineHeight: 23 }}>{guide.steps[currentIndex]}</Text>
          <SecondaryButton
            label={currentIndex + 1 < stepCount ? 'Bước tiếp theo' : 'Quay lại bước đầu'}
            onPress={() => props.onIndexChange(currentIndex + 1 < stepCount ? currentIndex + 1 : 0)}
          />
        </> : <Notice text="Hướng dẫn 4–8 bước có thứ tự hiện chưa khả dụng. Bạn vẫn có thể tiếp tục." tone="warning" />}
      </Card>
      <PrimaryButton label="Tiếp tục chọn ảnh" onPress={props.onContinue} />
    </ScreenFrame>
  );
}
