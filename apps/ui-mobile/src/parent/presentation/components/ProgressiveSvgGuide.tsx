import React, { useEffect, useRef, useState } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import type {
  ProgressiveStrokeGuideV1,
  SvgDocumentV1,
  SvgReferenceIllustrationDocumentV1,
} from '../../domain/svgGuide';
import { estimateSvgPathLength, orderedVisiblePathIds } from '../../domain/svgGuide';

const AnimatedPath = Animated.createAnimatedComponent(Path);
const CURRENT_STROKE = '#3867F6';
const COMPLETED_STROKE = '#17243E';

type Props = Readonly<{
  document: SvgDocumentV1;
  referenceIllustration?: SvgReferenceIllustrationDocumentV1;
  showFinalReferenceAlongside?: boolean;
  sourceExactPathSequence?: boolean;
  guide: ProgressiveStrokeGuideV1;
  stageIndex: number;
}>;

export function ProgressiveSvgGuide({
  document,
  referenceIllustration,
  showFinalReferenceAlongside = false,
  sourceExactPathSequence = false,
  guide,
  stageIndex,
}: Props): React.JSX.Element {
  const currentStage = guide.stages[stageIndex];
  const pathById = new Map(document.paths.map((path) => [path.path_id, path] as const));
  const visiblePaths = orderedVisiblePathIds(guide, stageIndex).flatMap((pathId) => {
    const path = pathById.get(pathId);
    return path ? [path] : [];
  });
  const justAdded = new Set(currentStage?.new_path_ids ?? []);
  const dashOffsetByPath = useRef(new Map<string, Animated.Value>()).current;
  const [completedStages, setCompletedStages] = useState<ReadonlySet<string>>(() => new Set());
  const stageKey = `${guide.guide_id}:${currentStage?.step_index ?? stageIndex}`;
  const currentStageComplete = completedStages.has(stageKey);
  const referencePathById = new Map(
    (referenceIllustration?.paths ?? []).map((path) => [path.path_id, path] as const),
  );

  const getDashOffset = (pathId: string): Animated.Value => {
    let value = dashOffsetByPath.get(pathId);
    if (!value) {
      value = new Animated.Value(0);
      dashOffsetByPath.set(pathId, value);
    }
    return value;
  };

  useEffect(() => {
    if (currentStageComplete || !currentStage) return undefined;
    const animations = (currentStage?.animation_order ?? []).map((pathId, index) => {
      const path = pathById.get(pathId);
      const length = path ? estimateSvgPathLength(path.d) : 1;
      const offset = getDashOffset(pathId);
      offset.setValue(length);
      return Animated.timing(offset, {
        toValue: 0,
        duration: sourceExactPathSequence ? 850 : 950,
        delay: index * (sourceExactPathSequence ? 65 : 220),
        useNativeDriver: false,
      });
    });
    const sequence = Animated.parallel(animations);
    sequence.start(({ finished }) => {
      if (finished) {
        setCompletedStages((previous) => {
          const next = new Set(previous);
          next.add(stageKey);
          return next;
        });
      }
    });
    return () => sequence.stop();
  }, [guide.guide_id, stageIndex, currentStageComplete, sourceExactPathSequence]);

  const canvasStyle = {
    width: '100%' as const,
    aspectRatio: 1,
    overflow: 'hidden' as const,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#E7ECF3',
    backgroundColor: '#fff',
  };
  const guideImage = (
    <Svg width="100%" height="100%" viewBox={document.view_box} style={StyleSheet.absoluteFill}>
      {visiblePaths.map((path) => {
        const isCurrentPath = justAdded.has(path.path_id);
        const hasFinishedDrawing = !isCurrentPath || currentStageComplete;
        const sourceStyle = referencePathById.get(path.path_id);
        const strokeLinecap = sourceExactPathSequence
          ? sourceStyle?.stroke_linecap ?? 'butt'
          : 'round';
        const strokeLinejoin = sourceExactPathSequence
          ? sourceStyle?.stroke_linejoin ?? 'miter'
          : 'round';
        const strokeMiterlimit = sourceExactPathSequence
          ? sourceStyle?.stroke_miterlimit ?? 4
          : undefined;
        if (hasFinishedDrawing) {
          return (
            <Path
              key={path.path_id}
              d={path.d}
              fill="none"
              stroke={COMPLETED_STROKE}
              strokeWidth={path.stroke_width}
              strokeLinecap={strokeLinecap}
              strokeLinejoin={strokeLinejoin}
              strokeMiterlimit={strokeMiterlimit}
            />
          );
        }
        const length = estimateSvgPathLength(path.d);
        return (
          <AnimatedPath
            key={path.path_id}
            d={path.d}
            fill="none"
            stroke={CURRENT_STROKE}
            strokeWidth={path.stroke_width + (sourceExactPathSequence ? 0.25 : 0.5)}
            strokeDasharray={[length, length]}
            strokeDashoffset={getDashOffset(path.path_id)}
            strokeLinecap={strokeLinecap}
            strokeLinejoin={strokeLinejoin}
            strokeMiterlimit={strokeMiterlimit}
          />
        );
      })}
    </Svg>
  );
  const referenceImage = referenceIllustration ? (
    <Svg width="100%" height="100%" viewBox={referenceIllustration.view_box} style={StyleSheet.absoluteFill}>
      {referenceIllustration.paths.map((path) => (
        <Path
          key={path.path_id}
          d={path.d}
          fill={path.fill}
          stroke={path.stroke}
          strokeWidth={path.stroke_width}
          strokeLinecap={path.stroke_linecap}
          strokeLinejoin={path.stroke_linejoin}
          strokeMiterlimit={path.stroke_miterlimit}
        />
      ))}
    </Svg>
  ) : null;

  return (
    <View style={{ width: '100%' }}>
      {showFinalReferenceAlongside && referenceImage ? (
        <View style={{ flexDirection: 'row', gap: 10 }}>
          <View style={{ flex: 1, minWidth: 0 }}>
            <Text style={styles.figureLabel}>Hình nét</Text>
            <View accessible accessibilityLabel="Hình vẽ hoàn chỉnh bằng nét" style={canvasStyle}>
              {guideImage}
            </View>
          </View>
          <View style={{ flex: 1, minWidth: 0 }}>
            <Text style={styles.figureLabel}>Hình màu gốc</Text>
            <View accessible accessibilityLabel="Hình minh họa màu gốc" style={canvasStyle}>
              {referenceImage}
            </View>
          </View>
        </View>
      ) : (
        <View
          accessible
          accessibilityLabel={`Gợi ý nét vẽ, bước ${stageIndex + 1} trên ${guide.stages.length}`}
          style={{ ...canvasStyle, aspectRatio: 1 }}
        >
          {guideImage}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  figureLabel: {
    color: '#546174',
    fontSize: 12,
    fontWeight: '800',
    marginBottom: 7,
    textAlign: 'center',
  },
});
