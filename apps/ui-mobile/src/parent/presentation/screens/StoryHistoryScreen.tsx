import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import type { ParentStoryRunSummary } from '../../domain/types';
import { runHistoryDateLabel } from '../../application/parentRunHistory';
import { Card, ConfirmButton, Notice, PrimaryButton, ScreenFrame, palette } from '../components/ui';

type Props = {
  capability: ParentCapabilityState;
  runs: ParentStoryRunSummary[];
  loading: boolean;
  error: string;
  hasMore: boolean;
  onLoad: () => void;
  onLoadMore: () => void;
  onCancel: (runId: string) => void;
  onDelete: (runId: string) => void;
  onBack: () => void;
};

export function StoryHistoryScreen(props: Props): React.JSX.Element {
  if (props.capability.state === 'unavailable') {
    return (
      <ScreenFrame
        title="Lịch sử buổi học"
        subtitle="Các buổi sáng tạo của hồ sơ đang chọn."
        onBack={props.onBack}
        visualTone="creative"
        safeAreaEdges={['top', 'right', 'left']}
        contentCentered
      >
        <UnavailableHistoryState />
      </ScreenFrame>
    );
  }

  return (
    <ScreenFrame title="Lịch sử buổi học" subtitle="Các buổi sáng tạo gần đây." onBack={props.onBack} visualTone="creative" safeAreaEdges={['top', 'right', 'left']}>
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {props.error ? <PrimaryButton variant="creative" label="Thử tải lại" busy={props.loading} onPress={props.onLoad} /> : null}
      {props.runs.length > 0 ? (
        <View style={styles.listHeading}>
          <View style={styles.listHeadingIcon}><Ionicons name="time-outline" size={18} color={historyColors.purple} accessible={false} /></View>
          <View style={styles.listHeadingCopy}>
            <Text style={styles.listHeadingTitle}>Các buổi gần đây</Text>
            <Text style={styles.listHeadingHint}>{props.runs.length} buổi đang hiển thị</Text>
          </View>
        </View>
      ) : null}
      {!props.runs.length && !props.loading && !props.error ? (
        <Card style={styles.emptyCard}>
          <HistoryIllustration compact />
          <Text style={styles.emptyTitle}>Chưa có buổi nào</Text>
          <Text style={styles.runDescription}>Các buổi đã bắt đầu sẽ xuất hiện ở đây.</Text>
          <PrimaryButton variant="creative" label="Tải lại" onPress={props.onLoad} />
        </Card>
      ) : null}
      {props.runs.map((run) => {
        // FEAT-081 C3b: the server decides what is allowed (summary flags, SRS line 1518, D-214).
        const canCancel = run.can_cancel && !run.deleting;
        const canDelete = run.can_delete && !run.deleting;
        const storyTitle = runHistoryDateLabel(run);
        return (
          <Card key={run.run_id} style={styles.runCard}>
            <View style={styles.runHeading}>
              <View style={styles.runIcon}><Ionicons name={runIcon(run.run_state)} size={19} color={historyColors.purple} accessible={false} /></View>
              <View style={styles.runTitleCopy}>
                <Text style={styles.runEyebrow}>BUỔI SÁNG TẠO</Text>
                <Text style={styles.runTitle}>{storyTitle}</Text>
              </View>
            </View>
            <View style={styles.runMetaRow}>
              <View style={styles.runStatePill}>
                <View style={[styles.runStateDot, run.run_state === 'COMPLETED' && styles.runStateDotComplete, run.run_state === 'FAILED' && styles.runStateDotFailed]} />
                <Text style={styles.runStateText}>{run.deleting ? 'Đang xóa' : runStateLabel(run.run_state)}</Text>
              </View>
            </View>
            {canCancel ? <ConfirmButton
              label="Hủy buổi đang mở"
              title="Hủy buổi học?"
              message="Buổi học sẽ dừng và nội dung của buổi sẽ bị xóa, không khôi phục được."
              confirmLabel="Hủy buổi"
              destructive
              onConfirm={() => props.onCancel(run.run_id)}
            /> : null}
            {canDelete ? <ConfirmButton
              label="Yêu cầu xóa buổi"
              title="Yêu cầu xóa dữ liệu buổi này?"
              message="Nội dung của buổi sẽ bị xóa và không khôi phục được. Trạng thái sẽ cập nhật tại đây."
              confirmLabel="Yêu cầu xóa"
              destructive
              onConfirm={() => props.onDelete(run.run_id)}
            /> : null}
          </Card>
        );
      })}
      {props.loading ? <Notice text="Đang tải…" /> : null}
      {props.hasMore ? <PrimaryButton variant="creative" label="Xem thêm" busy={props.loading} onPress={props.onLoadMore} /> : null}
    </ScreenFrame>
  );
}

function UnavailableHistoryState(): React.JSX.Element {
  const entrance = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.spring(entrance, {
      toValue: 1,
      stiffness: 125,
      damping: 19,
      mass: 0.9,
      useNativeDriver: true,
    });
    animation.start();
    return () => animation.stop();
  }, [entrance]);

  return (
    <Animated.View
      style={[
        styles.unavailableShell,
        {
          opacity: entrance,
          transform: [
            { translateY: entrance.interpolate({ inputRange: [0, 1], outputRange: [12, 0] }) },
            { scale: entrance.interpolate({ inputRange: [0, 1], outputRange: [0.985, 1] }) },
          ],
        },
      ]}
    >
      <View style={styles.unavailableCard}>
        <HistoryIllustration />
        <Text style={styles.unavailableTitle}>Lịch sử chưa khả dụng</Text>
        <Text style={styles.unavailableDescription}>
          Dịch vụ chưa có hợp đồng được xác nhận.
        </Text>
      </View>
    </Animated.View>
  );
}

function HistoryIllustration({ compact = false }: { compact?: boolean }): React.JSX.Element {
  return (
    <Svg width={compact ? 124 : 174} height={compact ? 98 : 138} viewBox="0 0 174 138" accessible={false}>
      <Circle cx="85" cy="69" r="61" fill={historyColors.lavender} />
      <Circle cx="40" cy="34" r="5" fill={historyColors.gold} />
      <Path d="M40 24v-5m0 30v-5m-11-10h-5m37 0h-5" stroke={historyColors.gold} strokeWidth="2.5" strokeLinecap="round" />
      <Rect x="43" y="24" width="69" height="83" rx="16" fill="#FFFFFF" stroke={historyColors.border} strokeWidth="2" />
      <Rect x="54" y="39" width="25" height="7" rx="3.5" fill="#E8D9FF" />
      <Rect x="54" y="54" width="46" height="5" rx="2.5" fill="#E7DFF0" />
      <Circle cx="58" cy="72" r="4" fill={historyColors.purple} />
      <Path d="M69 72h30M58 86h4m7 0h31" stroke="#C7B3E2" strokeWidth="4" strokeLinecap="round" />
      <Circle cx="121" cy="91" r="27" fill="#FFF0C2" stroke="#FFFFFF" strokeWidth="5" />
      <Circle cx="121" cy="91" r="18" fill="#FFFFFF" stroke={historyColors.purple} strokeWidth="2.5" />
      <Path d="M121 80v12l8 5" fill="none" stroke={historyColors.purple} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      <Circle cx="121" cy="91" r="2.5" fill={historyColors.purple} />
      <Path d="M143 42l2.5 5.5 5.5 2.5-5.5 2.5-2.5 5.5-2.5-5.5-5.5-2.5 5.5-2.5 2.5-5.5z" fill={historyColors.gold} />
      <Circle cx="31" cy="103" r="3" fill="#F4B6A7" />
    </Svg>
  );
}

const historyColors = {
  purple: '#7435D5',
  deepPurple: '#281451',
  lavender: '#F1E7FF',
  border: '#E4D6F5',
  gold: '#F6B830',
};

const styles = StyleSheet.create({
  unavailableShell: {
    backgroundColor: '#E9DFF5',
    borderRadius: 30,
    padding: 1.5,
    shadowColor: historyColors.deepPurple,
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.08,
    shadowRadius: 22,
    elevation: 4,
    minWidth: 0,
  },
  unavailableCard: {
    alignItems: 'center',
    backgroundColor: '#FFFEFC',
    borderColor: '#F0E9F6',
    borderRadius: 29,
    borderWidth: 1,
    gap: 13,
    paddingHorizontal: 21,
    paddingVertical: 23,
    minWidth: 0,
  },
  unavailableTitle: { color: historyColors.deepPurple, fontSize: 21, fontWeight: '800', lineHeight: 28, textAlign: 'center' },
  unavailableDescription: { color: '#6C6175', fontSize: 14, lineHeight: 21, maxWidth: 340, textAlign: 'center' },
  emptyCard: { alignItems: 'center', backgroundColor: '#FFFEFC', gap: 11, minWidth: 0, paddingVertical: 22 },
  emptyTitle: { color: historyColors.deepPurple, fontSize: 18, fontWeight: '800', lineHeight: 24, textAlign: 'center' },
  listHeading: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 9, paddingHorizontal: 2 },
  listHeadingIcon: { width: 34, height: 34, borderRadius: 12, alignItems: 'center', justifyContent: 'center', backgroundColor: historyColors.lavender },
  listHeadingCopy: { flex: 1, minWidth: 0, gap: 1 },
  listHeadingTitle: { color: historyColors.deepPurple, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  listHeadingHint: { color: '#776A84', fontSize: 10, lineHeight: 14 },
  runCard: { backgroundColor: '#FFFEFC', gap: 11, minWidth: 0, borderColor: '#E5D8F0', borderWidth: 1.2, borderRadius: 22 },
  runHeading: { flexDirection: 'row', alignItems: 'center', gap: 10, minWidth: 0 },
  runIcon: { width: 42, height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  runTitleCopy: { flex: 1, minWidth: 0, gap: 3 },
  runEyebrow: { color: historyColors.purple, fontSize: 10, fontWeight: '800', letterSpacing: 0.8, lineHeight: 14 },
  runTitle: { color: historyColors.deepPurple, fontSize: 17, lineHeight: 23, fontWeight: '800', flexShrink: 1, minWidth: 0 },
  runMetaRow: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  topicPill: { minHeight: 27, flexDirection: 'row', alignItems: 'center', gap: 5, paddingHorizontal: 9, borderRadius: 14, backgroundColor: '#F6F1FB' },
  runStatePill: { alignItems: 'center', backgroundColor: historyColors.lavender, borderRadius: 999, flexDirection: 'row', gap: 6, minHeight: 28, paddingHorizontal: 10 },
  runStateDot: { backgroundColor: historyColors.purple, borderRadius: 4, height: 7, width: 7 },
  runStateDotComplete: { backgroundColor: '#397A55' },
  runStateDotFailed: { backgroundColor: '#B54E50' },
  runStateText: { color: historyColors.deepPurple, fontSize: 11, fontWeight: '700', lineHeight: 15 },
  runMeta: { color: palette.muted, fontSize: 12, lineHeight: 17, flexShrink: 1, minWidth: 0 },
  runDescription: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, minWidth: 0, textAlign: 'center' },
});

function runIcon(value: string): React.ComponentProps<typeof Ionicons>['name'] {
  if (value === 'COMPLETED') return 'checkmark-circle-outline';
  if (value === 'FAILED') return 'alert-circle-outline';
  return 'hourglass-outline';
}

function runStateLabel(value: string): string {
  const labels: Record<string, string> = {
    INPUT_PROCESSING: 'Đang xử lý ảnh',
    INPUT_REVIEW: 'Chờ xem lại ảnh và ý tưởng',
    SUBJECT_REVIEW: 'Chờ xác nhận chủ thể',
    PREPARATION_REVIEW: 'Đang chuẩn bị nội dung',
    SCRIPT_GENERATING: 'Đang tạo kịch bản',
    SCRIPT_GENERATION_UNKNOWN: 'Đang xác minh kết quả',
    SCRIPT_REVIEW: 'Chờ người lớn xem kịch bản',
    VIDEO_ADMISSION_PENDING: 'Đang chờ xử lý',
    DELETE_PENDING: 'Đang chờ dọn dữ liệu',
    FAILED: 'Không hoàn tất',
    COMPLETED: 'Đã hoàn tất',
    ABANDONED: 'Đã đóng',
    DELETED: 'Đã xóa',
  };
  return labels[value] ?? 'Trạng thái chưa xác định';
}
