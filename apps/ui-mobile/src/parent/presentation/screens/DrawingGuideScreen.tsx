import React from 'react';
import { Text } from 'react-native';
import type { LessonDetail } from '../../domain/types';
import {
  clampDrawingGuideIndex,
  moveDrawingGuideIndex,
  parseDrawingGuideSteps,
} from '../navigation/parentFlowV1';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, SecondaryButton, palette } from '../components/ui';

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
  const steps = guide.kind === 'steps' ? guide.steps : [];
  const currentIndex = clampDrawingGuideIndex(props.currentIndex, steps.length);
  const isLastStep = currentIndex >= steps.length - 1;

  return (
    <ScreenFrame
      title="Hướng dẫn vẽ từng bước"
      subtitle="Gợi ý này không bắt buộc. Người lớn có thể xem từng bước trước khi chụp tranh."
      step={props.stepLabel}
      onBack={props.onBack}
    >
      <Card>
        <SectionTitle>Các bước gợi ý</SectionTitle>
        {guide.kind === 'steps' ? <>
          <Text accessibilityLiveRegion="polite" style={{ color: palette.blue, fontSize: 14, fontWeight: '800' }}>
            Bước {currentIndex + 1} trên {steps.length}
          </Text>
          <Text accessibilityRole="text" style={{ color: palette.ink, fontSize: 17, lineHeight: 26 }}>
            {steps[currentIndex]}
          </Text>
          <SecondaryButton
            label="Bước trước"
            disabled={currentIndex === 0}
            onPress={() => props.onIndexChange(moveDrawingGuideIndex(currentIndex, steps.length, -1))}
          />
          {!isLastStep ? <PrimaryButton
            label="Bước tiếp theo"
            onPress={() => props.onIndexChange(moveDrawingGuideIndex(currentIndex, steps.length, 1))}
          /> : null}
        </> : <Notice
          text={guide.reason === 'missing'
            ? 'Bài học này chưa có hướng dẫn vẽ theo bước. Bạn vẫn có thể tiếp tục.'
            : 'Hướng dẫn chưa được chia thành từng bước rõ ràng. Bạn vẫn có thể tiếp tục.'}
        />}
      </Card>
      {guide.kind === 'steps' ? <SecondaryButton label="Bỏ qua hướng dẫn" onPress={props.onContinue} /> : null}
      <PrimaryButton
        label={guide.kind === 'steps' && !isLastStep ? 'Tiếp tục đến bước tiếp theo' : 'Tiếp tục'}
        onPress={guide.kind === 'steps' && !isLastStep
          ? () => props.onIndexChange(moveDrawingGuideIndex(currentIndex, steps.length, 1))
          : props.onContinue}
      />
    </ScreenFrame>
  );
}
