import React, { useEffect, useRef, useState } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, G, Path, Polygon, Text as SvgText } from 'react-native-svg';
import type {
  ProgressiveStrokeGuideV1,
  SvgDocumentV1,
  SvgReferenceIllustrationDocumentV1,
} from '../../domain/svgGuide';
import { estimateSvgPathLength, orderedVisiblePathIds, stageStartMarkers } from '../../domain/svgGuide';

const AnimatedPath = Animated.createAnimatedComponent(Path);
const CURRENT_STROKE = '#3867F6';
const COMPLETED_STROKE = '#17243E';
const START_MARK = '#12924F';

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
  const [replayCount, setReplayCount] = useState(0);
  const stageKey = `${guide.guide_id}:${currentStage?.step_index ?? stageIndex}:${replayCount}`;
  const canvasSize = Number(document.view_box.trim().split(/\s+/)[2]) || 100;
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
    // One stroke after another, so the child sees the order (FEAT-097).
    const animations = (currentStage?.animation_order ?? []).map((pathId) => {
      const path = pathById.get(pathId);
      const length = path ? estimateSvgPathLength(path.d) : 1;
      const offset = getDashOffset(pathId);
      offset.setValue(length);
      return Animated.timing(offset, {
        toValue: 0,
        duration: Math.round(Math.min(1500, Math.max(500, (length / canvasSize) * 900))),
        delay: sourceExactPathSequence ? 65 : 250,
        useNativeDriver: false,
      });
    });
    const sequence = Animated.sequence(animations);
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
  }, [guide.guide_id, stageIndex, replayCount, currentStageComplete, sourceExactPathSequence]);

  const startMarkers = stageStartMarkers(
    (currentStage?.animation_order ?? []).flatMap((pathId) => {
      const path = pathById.get(pathId);
      return path ? [path] : [];
    }),
    canvasSize,
  );
  const markedPaths = new Set(startMarkers.map((item) => item.pathId));

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
        const shared = {
          d: path.d,
          fill: 'none',
          strokeLinecap,
          strokeLinejoin,
          strokeMiterlimit,
        } as const;
        if (!isCurrentPath) {
          return <Path key={path.path_id} {...shared} stroke={COMPLETED_STROKE} strokeWidth={path.stroke_width} />;
        }
        const length = estimateSvgPathLength(path.d);
        // A dot has no start mark and is too small to read as dashes: it is drawn solid.
        const hasMarker = markedPaths.has(path.path_id);
        return (
          <G key={path.path_id}>
            {/* SRS 6.2.1: the new stroke stays dashed and highlighted; the solid line shows how it is drawn. */}
            <Path
              {...shared}
              stroke={CURRENT_STROKE}
              strokeOpacity={currentStageComplete ? 1 : 0.35}
              strokeWidth={path.stroke_width}
              strokeDasharray={hasMarker ? [canvasSize * 0.03, canvasSize * 0.025] : undefined}
            />
            {currentStageComplete ? null : <AnimatedPath
              {...shared}
              stroke={CURRENT_STROKE}
              strokeWidth={path.stroke_width * 1.15}
              strokeDasharray={[length, length]}
              strokeDashoffset={getDashOffset(path.path_id)}
            />}
          </G>
        );
      })}
      {startMarkers.map(({ pathId, marker, number }) => {
        const size = canvasSize * 0.04;
        const tip = {
          x: marker.arrow.x + size * 0.6 * Math.cos(marker.angle),
          y: marker.arrow.y + size * 0.6 * Math.sin(marker.angle),
        };
        const wings = [0.55, -0.55].map((spread) => (
          `${tip.x - size * Math.cos(marker.angle + spread)},${tip.y - size * Math.sin(marker.angle + spread)}`
        ));
        return (
          <G key={`start-${pathId}`}>
            <Polygon points={`${tip.x},${tip.y} ${wings.join(' ')}`} fill={START_MARK} />
            <Circle cx={marker.start.x} cy={marker.start.y} r={canvasSize * 0.027} fill={START_MARK} />
            {number === null ? null : <SvgText
              x={marker.start.x}
              y={marker.start.y + canvasSize * 0.013}
              fontSize={canvasSize * 0.038}
              fontWeight="bold"
              fill="#FFFFFF"
              textAnchor="middle"
            >{number}</SvgText>}
          </G>
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
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Xem lại cách vẽ"
        onPress={() => setReplayCount((count) => count + 1)}
        style={styles.replay}
      >
        <Text style={styles.replayLabel}>Xem lại cách vẽ</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  replay: {
    alignSelf: 'center',
    marginTop: 8,
    minHeight: 44,
    paddingHorizontal: 18,
    justifyContent: 'center',
  },
  replayLabel: {
    color: '#3867F6',
    fontSize: 14,
    fontWeight: '800',
  },
  figureLabel: {
    color: '#546174',
    fontSize: 12,
    fontWeight: '800',
    marginBottom: 7,
    textAlign: 'center',
  },
});
