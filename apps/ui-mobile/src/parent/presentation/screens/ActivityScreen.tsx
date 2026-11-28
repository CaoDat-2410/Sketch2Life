import React from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type {
  ParentActivityListV1,
  ParentActivitySuggestionSetV1,
  ParentActivityV1,
  SuggestedActivity,
} from '../../domain/types';
import { Card, ConfirmButton, Notice, PrimaryButton, ScreenFrame, SectionTitle, SecondaryButton, palette } from '../components/ui';

export const ACTIVITY_COPY = {
  aiSuggestionLabel: 'Gợi ý AI',
  aiReviewRequired: 'Đây là gợi ý AI. Người lớn cần xem lại trước khi dùng.',
  suggestionSetDescription: 'Người lớn xem lại các gợi ý trước khi chọn hoạt động.',
  aiReviewed: 'Gợi ý AI đã được người lớn xem lại và chọn làm hoạt động chính.',
  selectionRetry: 'Chưa xác nhận được lựa chọn. Danh sách và lựa chọn của bạn được giữ lại; hãy thử lưu lại.',
} as const;

type ActivityList = ParentActivityListV1 | ParentActivitySuggestionSetV1;
type ActivityOptionData = ParentActivityV1 | SuggestedActivity;

type Props = {
  stepLabel: string;
  topic: string;
  subject: string;
  activities: ActivityList | null;
  selectedIndex: number | null;
  loading: boolean;
  saving: boolean;
  attempted: boolean;
  error: string;
  onRetry: () => void;
  onSelect: (index: number) => void;
  onContinue: () => void;
  onCancel: () => void;
  onBack?: () => void;
};

export function ActivityScreen(props: Props): React.JSX.Element {
  const suggestionSet = props.activities && 'activities' in props.activities ? props.activities : null;
  const items: readonly ActivityOptionData[] = props.activities
    ? ('items' in props.activities ? props.activities.items : props.activities.activities)
    : [];
  const noCandidate = Boolean(props.activities && 'basis' in props.activities && props.activities.basis.no_candidate);
  const hasSelection = props.selectedIndex !== null && Boolean(items[props.selectedIndex]);

  return (
    <ScreenFrame
      title="Hoạt động cùng bé"
      subtitle="Người lớn chọn hoạt động chính trước khi bắt đầu câu chuyện."
      step={props.stepLabel}
      onBack={props.onBack}
      visualTone="creative"
    >
      <Card variant="creative" style={styles.contextCard}>
        <View style={styles.contextIcon}><Ionicons name="color-palette-outline" size={21} color={palette.creativePrimary} /></View>
        <View style={styles.contextCopy}>
          <Text style={styles.eyebrow}>BỨC TRANH</Text>
          <Text numberOfLines={1} style={styles.contextSubject}>{props.subject.trim() || 'Chủ thể đã xác nhận'}</Text>
        </View>
        {props.topic.trim() ? <View style={styles.topicPill}><Text numberOfLines={1} style={styles.topicText}>{props.topic.trim()}</Text></View> : null}
      </Card>

      {props.loading && !props.activities ? (
        <Card variant="creative" style={styles.stateCard}><ActivityIndicator color={palette.creativePrimary} /><Text style={styles.description}>Đang soạn danh sách hoạt động…</Text><Text style={styles.description}>Lần đầu có thể mất vài phút. Bạn không cần bấm lại.</Text></Card>
      ) : noCandidate ? (
        <Card variant="creative" style={styles.stateCard}>
          <SectionTitle variant="creative">Chưa có hoạt động phù hợp</SectionTitle>
          <Text style={styles.description}>Buổi học này chưa thể bắt đầu câu chuyện. Bạn có thể dừng buổi học trong lịch sử.</Text>
          <ConfirmButton
            label="Dừng buổi học"
            title="Dừng buổi học này?"
            message="Buổi học sẽ dừng và không thể tiếp tục."
            confirmLabel="Dừng buổi học"
            destructive
            onConfirm={props.onCancel}
          />
        </Card>
      ) : !props.activities ? (
        <Card variant="creative" style={styles.stateCard}>
          <SectionTitle variant="creative">Chưa tải được hoạt động</SectionTitle>
          {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
          <PrimaryButton variant="creative" label={props.attempted ? 'Tải lại danh sách' : 'Tải danh sách hoạt động'} busy={props.loading} disabled={props.loading} onPress={props.onRetry} />
        </Card>
      ) : (
        <>
          <View style={styles.resultsHeading}>
          <SectionTitle variant="creative">Chọn một hoạt động</SectionTitle>
            <Text style={styles.description}>
              {suggestionSet?.selection_mode === 'AI_GENERATED_FALLBACK'
                ? 'Gợi ý mới · người lớn xem cùng bé.'
                : suggestionSet
                  ? ACTIVITY_COPY.suggestionSetDescription
                  : props.activities && 'basis' in props.activities && props.activities.basis.pinned_lesson
                    ? 'Chọn hoạt động từ bài học đã ghim.'
                    : 'Chọn hoạt động từ danh sách phù hợp.'}
            </Text>
          </View>
          {items.map((activity, index) => {
            const versionId = 'source_lesson_version_id' in activity
              ? activity.source_lesson_version_id
              : activity.activity_ref?.version_id;
            const activityIndex = 'source_activity_index' in activity
              ? activity.source_activity_index
              : activity.activity_ref?.activity_index;
            return <ActivityOption
              key={`${activity.source}-${versionId ?? 'draft'}-${activityIndex ?? index}-${activity.title}`}
              activity={activity}
              selected={props.selectedIndex === index}
              onPress={() => props.onSelect(index)}
            />;
          })}
          {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
          {props.selectedIndex !== null ? <Notice variant="creative" text="Bạn có thể đổi lựa chọn cho đến khi câu chuyện bắt đầu." tone="info" /> : null}
          {props.attempted && props.error ? <SecondaryButton variant="creative" label="Tải lại danh sách" disabled={props.loading || props.saving} onPress={props.onRetry} /> : null}
          <PrimaryButton
            variant="creative"
            label="Lưu lựa chọn và tiếp tục"
            busy={props.saving}
            disabled={!hasSelection || props.loading || props.saving}
            onPress={props.onContinue}
          />
        </>
      )}
    </ScreenFrame>
  );
}

function ActivityOption({ activity, selected, onPress }: { activity: ActivityOptionData; selected: boolean; onPress: () => void }): React.JSX.Element {
  const aiDraft = activity.source === 'AI_GENERATED_DRAFT' || activity.source === 'AI_DRAFT';
  const lessonTitle = 'lesson_title' in activity ? activity.lesson_title : activity.source_lesson_title;
  const lessonTopic = 'lesson_topic' in activity ? activity.lesson_topic : null;
  return (
    <Pressable accessibilityRole="radio" accessibilityState={{ checked: selected }} accessibilityLabel={`Chọn hoạt động ${activity.title}`} onPress={onPress} style={({ pressed }) => [styles.optionPressable, pressed && styles.pressed]}>
      <Card variant="creative" style={[styles.activityCard, selected && styles.activityCardSelected]}>
        <View style={styles.activityHeader}>
          <View style={[styles.activityIcon, selected && styles.activityIconSelected]}><Ionicons name={activityIcon(activity.activity_kind)} size={20} color={palette.creativePrimary} /></View>
          <View style={styles.activityTitleBlock}>
            <Text style={styles.activityTitle}>{activity.title}</Text>
            <Text style={styles.activityKind}>{activityKindLabel(activity.activity_kind)} · {activitySourceLabel(activity.source)}</Text>
          </View>
          <View style={[styles.radio, selected && styles.radioSelected]}>{selected ? <View style={styles.radioDot} /> : null}</View>
        </View>
        <View style={styles.objectiveBox}>
          <Text style={styles.fieldLabel}>MỤC TIÊU</Text>
          <Text style={styles.bodyText}>{activity.objective}</Text>
        </View>
        {aiDraft ? <Text style={styles.aiReviewText}>{ACTIVITY_COPY.aiReviewRequired}</Text> : null}
        {lessonTitle ? <Text style={styles.sourceText}>Bài học · {lessonTitle}{lessonTopic ? ` · ${lessonTopic}` : ''}</Text> : null}
        {activity.materials_text ? <Text style={styles.bodyText}>Chuẩn bị · {activity.materials_text}</Text> : null}
        {activity.preparation_text ? <Text style={styles.detailText}>{activity.preparation_text}</Text> : null}
        <View style={styles.instructionBox}>
          <Text style={styles.fieldLabel}>CÁCH CÙNG LÀM</Text>
          <Text style={styles.bodyText}>{activity.instructions_text}</Text>
        </View>
        {activity.observation_notes ? <Text style={styles.detailText}>Quan sát · {activity.observation_notes}</Text> : null}
        {activity.safety_notes ? <View style={styles.safetyBox}><Ionicons name="shield-checkmark-outline" size={16} color="#87600A" /><Text style={styles.safetyText}>{activity.safety_notes}</Text></View> : null}
      </Card>
    </Pressable>
  );
}

function activityKey(activity: ActivityOptionData, index: number): string {
  if ('activity_ref' in activity && activity.activity_ref) {
    return `${activity.activity_ref.lesson_id}-${activity.activity_ref.version_id}-${activity.activity_ref.activity_index}`;
  }
  if ('source_lesson_id' in activity && activity.source_lesson_id && activity.source_lesson_version_id) {
    return `${activity.source_lesson_id}-${activity.source_lesson_version_id}-${activity.source_activity_index ?? index}`;
  }
  return `activity-${index}`;
}

function activitySourceLabel(source: ActivityOptionData['source']): string {
  if (source === 'AI_GENERATED_DRAFT' || source === 'AI_DRAFT') return ACTIVITY_COPY.aiSuggestionLabel;
  if (source === 'PINNED_LESSON') return 'Bài học đã ghim';
  if (source === 'PUBLIC') return 'Bài học công khai';
  return source === 'SHARED' || source === 'PUBLISHED_SHARED_LESSON' ? 'Bài học được chia sẻ' : 'Bài học đã ghim';
}

function activityKindLabel(kind: ActivityOptionData['activity_kind']): string {
  if (kind === 'indoor') return 'Trong nhà';
  if (kind === 'outdoor') return 'Ngoài trời';
  return 'Trong nhà hoặc ngoài trời';
}

function activityIcon(kind: ActivityOptionData['activity_kind']): React.ComponentProps<typeof Ionicons>['name'] {
  if (kind === 'indoor') return 'home-outline';
  if (kind === 'outdoor') return 'leaf-outline';
  return 'sunny-outline';
}

const styles = StyleSheet.create({
  contextCard: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: '#FFFEFF', paddingVertical: 10 },
  contextIcon: { width: 40, height: 40, borderRadius: 14, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.creativeLavender },
  contextCopy: { flex: 1, minWidth: 0, gap: 2 },
  eyebrow: { color: palette.creativePrimary, fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.6 },
  contextSubject: { color: palette.creativeInk, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  description: { color: palette.creativeMuted, fontSize: 13, lineHeight: 19, flexShrink: 1 },
  topicPill: { alignSelf: 'center', backgroundColor: '#F4ECFF', borderRadius: 999, maxWidth: '38%', paddingHorizontal: 9, paddingVertical: 6 },
  topicText: { color: palette.creativePrimary, fontSize: 10, lineHeight: 14, fontWeight: '800' },
  stateCard: { gap: 14, backgroundColor: '#FFFEFF' },
  resultsHeading: { gap: 5 },
  optionPressable: { minWidth: 0 },
  pressed: { opacity: 0.86 },
  activityCard: { gap: 12, backgroundColor: '#FFFEFF', borderWidth: 1.4, borderColor: palette.creativeBorder },
  activityCardSelected: { borderWidth: 2.4, borderColor: palette.creativePrimary, backgroundColor: '#FBF7FF' },
  activityHeader: { flexDirection: 'row', alignItems: 'center', gap: 10, minWidth: 0 },
  activityIcon: { width: 42, height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF' },
  activityIconSelected: { backgroundColor: '#E8D7FF' },
  activityTitleBlock: { flex: 1, minWidth: 0, gap: 3 },
  activityTitle: { color: palette.creativeInk, fontSize: 15, lineHeight: 20, fontWeight: '800', flexShrink: 1 },
  activityKind: { color: palette.creativeMuted, fontSize: 11, lineHeight: 15 },
  radio: { width: 24, height: 24, borderRadius: 12, borderWidth: 1.7, borderColor: '#B6A4CA', alignItems: 'center', justifyContent: 'center' },
  radioSelected: { borderColor: palette.creativePrimary },
  radioDot: { width: 12, height: 12, borderRadius: 6, backgroundColor: palette.creativePrimary },
  objectiveBox: { gap: 4, borderRadius: 13, padding: 11, backgroundColor: '#F8F3FF' },
  fieldLabel: { color: palette.creativePrimary, fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.45 },
  bodyText: { color: palette.creativeInk, fontSize: 13, lineHeight: 19, flexShrink: 1 },
  detailText: { color: palette.creativeMuted, fontSize: 12, lineHeight: 18 },
  instructionBox: { gap: 4 },
  sourceText: { color: palette.creativeMuted, fontSize: 11, lineHeight: 16, fontWeight: '700' },
  aiReviewText: { color: palette.creativePrimary, fontSize: 12, lineHeight: 18, fontWeight: '700' },
  safetyBox: { flexDirection: 'row', alignItems: 'flex-start', gap: 7, borderRadius: 12, padding: 10, backgroundColor: '#FFF5D9' },
  safetyText: { flex: 1, color: '#72530D', fontSize: 12, lineHeight: 17 },
});
