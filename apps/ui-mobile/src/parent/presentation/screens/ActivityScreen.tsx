import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { ActivitySuggestionResult } from '../../application/ports/ParentPorts';
import type { SuggestedActivity } from '../../domain/types';
import { Card, Notice, PrimaryButton, ScreenFrame, SectionTitle, palette } from '../components/ui';
import { ParentAiLoadingState } from '../components/ParentAiLoadingState';

type Props = {
  stepLabel: string;
  topic: string;
  subject: string;
  suggestions: ActivitySuggestionResult | null;
  selectedIndex: number | null;
  selectionPersisted: boolean;
  selectionBusy: boolean;
  loading: boolean;
  attempted: boolean;
  error: string;
  onSuggest: () => void;
  onSelect: (index: number) => void;
  onContinue: () => void;
  onBack: () => void;
};

export function ActivityScreen(props: Props): React.JSX.Element {
  const hasSelection = props.selectedIndex !== null
    && Boolean(props.suggestions?.activities[props.selectedIndex]);
  const selectionMode = props.suggestions?.selection_mode;

  return (
    <ScreenFrame
      title="Hoạt động cùng bé"
      subtitle="Chọn một hoạt động chính trước khi tạo câu chuyện."
      step={props.stepLabel}
      onBack={props.onBack}
      visualTone="creative"
    >
      <Card variant="creative" style={styles.introCard}>
        <View style={styles.introIcon}>
          <Ionicons name="sparkles" size={22} color={palette.creativePrimary} />
        </View>
        <View style={styles.introCopy}>
          <Text style={styles.eyebrow}>GỢI Ý THEO BỨC TRANH</Text>
          <SectionTitle variant="creative">Một ý tưởng để cùng làm</SectionTitle>
          <Text style={styles.description}>
            {props.subject.trim()
              ? `Chủ thể đã xác nhận: ${props.subject.trim()}`
              : 'Gợi ý sẽ dựa trên chủ thể người lớn đã xác nhận.'}
          </Text>
          {props.topic.trim() ? <Text style={styles.topicText}>Chủ đề · {props.topic.trim()}</Text> : null}
        </View>
      </Card>

      {props.loading ? (
        <ParentAiLoadingState
          testID="parent-activity-ai-loading"
          title="Đang tìm hoạt động phù hợp"
          description="Hệ thống đang kiểm tra bài học đã chia sẻ. Nếu chưa có hoạt động phù hợp, AI sẽ tạo gợi ý để người lớn xem lại."
          note="Giữ màn hình này đến khi có kết quả. Không gửi lại khi yêu cầu đang chạy."
        />
      ) : !props.suggestions ? (
        <Card variant="creative" style={styles.emptyCard}>
          <View style={styles.emptyArtwork}>
            <View style={styles.emptyGlow} />
            <View style={styles.artPage}>
              <View style={styles.artSun} />
              <View style={styles.artHill} />
              <View style={styles.artStem} />
              <View style={styles.artLeafOne} />
              <View style={styles.artLeafTwo} />
            </View>
            <View style={styles.artSparkleOne}><Ionicons name="sparkles" size={18} color="#ECA90A" /></View>
            <View style={styles.artSparkleTwo}><Ionicons name="star" size={13} color="#9B68E8" /></View>
          </View>
          <View style={styles.emptyCopy}>
            <SectionTitle variant="creative">
              {props.error ? 'Chưa lấy được gợi ý' : 'Tìm hoạt động hợp với tranh'}
            </SectionTitle>
            {!props.error ? (
              <Text style={styles.description}>
                {props.attempted
                  ? 'Chưa có gợi ý được lưu cho buổi học này.'
                  : 'Gợi ý dựa trên chủ thể và ngữ cảnh đã xác nhận.'}
              </Text>
            ) : null}
          </View>
          {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
          <PrimaryButton
            variant="creative"
            label={props.attempted ? 'Thử lấy gợi ý lại' : 'Tìm hoạt động phù hợp'}
            busy={props.loading}
            onPress={props.onSuggest}
          />
        </Card>
      ) : (
        <>
          <View style={styles.resultsHeading}>
            <View style={styles.resultsCopy}>
              <SectionTitle variant="creative">Chọn một hoạt động</SectionTitle>
              <Text style={styles.description}>
                {selectionMode === 'CATALOG_SELECTION'
                  ? 'Các hoạt động được chọn từ nội dung bài học phù hợp.'
                  : 'Chưa tìm thấy hoạt động phù hợp trong thư viện. Đây là gợi ý AI để người lớn xem lại.'}
              </Text>
            </View>
            <View style={[styles.modeBadge, selectionMode === 'AI_GENERATED_FALLBACK' && styles.draftBadge]}>
              <Text style={[styles.modeBadgeText, selectionMode === 'AI_GENERATED_FALLBACK' && styles.draftBadgeText]}>
                {selectionMode === 'CATALOG_SELECTION' ? 'BÀI HỌC' : 'BẢN NHÁP'}
              </Text>
            </View>
          </View>

          {props.suggestions.activities.map((activity, index) => (
            <ActivityOption
              key={`${activity.source}-${activity.source_lesson_version_id ?? 'draft'}-${activity.source_activity_index ?? index}-${activity.title}`}
              activity={activity}
              selected={props.selectedIndex === index}
              onPress={() => props.onSelect(index)}
            />
          ))}

          {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}
          {hasSelection && props.selectionBusy ? (
            <Notice
              variant="creative"
              text="Đang lưu lựa chọn vào buổi học…"
              tone="warning"
            />
          ) : null}
          {hasSelection && !props.selectionBusy && !props.selectionPersisted ? (
            <Notice
              variant="creative"
              text="Chưa lưu được lựa chọn. Hãy chọn lại để thử lưu trước khi tiếp tục."
              tone="warning"
            />
          ) : null}
          {hasSelection && props.selectionPersisted ? (
            <Text style={styles.savedText}>Đã lưu lựa chọn cho buổi học này.</Text>
          ) : null}
          <PrimaryButton
            variant="creative"
            label={props.selectionBusy ? 'Đang lưu lựa chọn…' : 'Tiếp tục đến câu chuyện'}
            disabled={!hasSelection || !props.selectionPersisted || props.selectionBusy}
            onPress={props.onContinue}
          />
        </>
      )}
    </ScreenFrame>
  );
}

function ActivityOption({ activity, selected, onPress }: {
  activity: SuggestedActivity;
  selected: boolean;
  onPress: () => void;
}): React.JSX.Element {
  return (
    <Pressable
      accessibilityRole="radio"
      accessibilityState={{ checked: selected }}
      accessibilityLabel={`Chọn hoạt động ${activity.title}`}
      onPress={onPress}
      style={({ pressed }) => [styles.optionPressable, pressed && styles.pressed]}
    >
      <Card variant="creative" style={[styles.activityCard, selected && styles.activityCardSelected]}>
        <View style={styles.activityHeader}>
          <View style={[styles.activityIcon, selected && styles.activityIconSelected]}>
            <Ionicons name={activityIcon(activity.activity_kind)} size={20} color={palette.creativePrimary} />
          </View>
          <View style={styles.activityTitleBlock}>
            <Text style={styles.activityTitle}>{activity.title}</Text>
            <Text style={styles.activityKind}>{activityKindLabel(activity.activity_kind)}</Text>
          </View>
          <View style={[styles.radio, selected && styles.radioSelected]}>
            {selected ? <View style={styles.radioDot} /> : null}
          </View>
        </View>

        {activity.source !== 'AI_GENERATED_DRAFT' && activity.match_reason ? (
          <Text style={styles.matchReason}>{activity.match_reason}</Text>
        ) : null}
        <View style={styles.objectiveBox}>
          <Text style={styles.fieldLabel}>MỤC TIÊU</Text>
          <Text style={styles.bodyText}>{activity.objective}</Text>
        </View>
        <View style={styles.detailRow}>
          <Ionicons name="color-palette-outline" size={16} color={palette.creativePrimary} />
          <Text style={styles.bodyText}>
            Chuẩn bị: {activity.materials_text || 'Không yêu cầu vật liệu đặc biệt'}
          </Text>
        </View>
        {activity.preparation_text ? <Text style={styles.detailText}>{activity.preparation_text}</Text> : null}
        <View style={styles.instructionBox}>
          <Text style={styles.fieldLabel}>CÁCH CÙNG LÀM</Text>
          <Text style={styles.bodyText}>{activity.instructions_text}</Text>
        </View>
        {activity.safety_notes ? (
          <View style={styles.safetyBox}>
            <Ionicons name="shield-checkmark-outline" size={16} color="#87600A" />
            <Text style={styles.safetyText}>{activity.safety_notes}</Text>
          </View>
        ) : null}
        {activity.source_lesson_title ? (
          <Text style={styles.sourceText}>Nguồn · {activity.source_lesson_title}
            {activity.source_lesson_version_id ? ` · ${activity.source_lesson_version_id}` : ''}
          </Text>
        ) : activity.source === 'AI_GENERATED_DRAFT' ? (
          <Text style={styles.sourceText}>Gợi ý AI · cần người lớn xem lại</Text>
        ) : null}
      </Card>
    </Pressable>
  );
}

function activityKindLabel(kind: SuggestedActivity['activity_kind']): string {
  if (kind === 'indoor') return 'Trong nhà';
  if (kind === 'outdoor') return 'Ngoài trời';
  return 'Trong nhà hoặc ngoài trời';
}

function activityIcon(kind: SuggestedActivity['activity_kind']): React.ComponentProps<typeof Ionicons>['name'] {
  if (kind === 'indoor') return 'home-outline';
  if (kind === 'outdoor') return 'leaf-outline';
  return 'sunny-outline';
}

const styles = StyleSheet.create({
  introCard: { flexDirection: 'row', alignItems: 'flex-start', gap: 12, backgroundColor: '#FFFEFF' },
  introIcon: { width: 44, height: 44, borderRadius: 16, alignItems: 'center', justifyContent: 'center', backgroundColor: palette.creativeLavender },
  introCopy: { flex: 1, minWidth: 0, gap: 5 },
  eyebrow: { color: palette.creativePrimary, fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.6 },
  description: { color: palette.creativeMuted, fontSize: 13, lineHeight: 19, flexShrink: 1 },
  topicText: { color: palette.creativePrimary, fontSize: 12, lineHeight: 17, fontWeight: '700' },
  emptyCard: { gap: 14, backgroundColor: '#FFFEFF' },
  emptyArtwork: { height: 154, borderRadius: 20, overflow: 'hidden', alignItems: 'center', justifyContent: 'center', backgroundColor: '#F4ECFF' },
  emptyGlow: { position: 'absolute', width: 145, height: 145, borderRadius: 80, backgroundColor: '#E5D4FF', opacity: 0.75 },
  artPage: { width: 88, height: 104, borderRadius: 13, backgroundColor: '#FFFEFF', borderWidth: 1.5, borderColor: '#DAC7F2', overflow: 'hidden', transform: [{ rotate: '-7deg' }] },
  artSun: { position: 'absolute', width: 15, height: 15, borderRadius: 8, right: 15, top: 15, backgroundColor: '#FFD267' },
  artHill: { position: 'absolute', width: 100, height: 42, bottom: -18, left: -9, borderRadius: 30, backgroundColor: '#BFE7D2' },
  artStem: { position: 'absolute', width: 4, height: 35, left: 44, bottom: 23, borderRadius: 2, backgroundColor: '#65A67E' },
  artLeafOne: { position: 'absolute', width: 22, height: 12, left: 25, bottom: 39, borderRadius: 14, backgroundColor: '#8CD6AA', transform: [{ rotate: '-25deg' }] },
  artLeafTwo: { position: 'absolute', width: 22, height: 12, left: 45, bottom: 31, borderRadius: 14, backgroundColor: '#A3DDB4', transform: [{ rotate: '22deg' }] },
  artSparkleOne: { position: 'absolute', top: 25, right: '23%' },
  artSparkleTwo: { position: 'absolute', bottom: 29, left: '24%' },
  emptyCopy: { gap: 6 },
  resultsHeading: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, paddingHorizontal: 2 },
  resultsCopy: { flex: 1, minWidth: 0, gap: 5 },
  modeBadge: { minHeight: 27, paddingHorizontal: 10, borderRadius: 999, backgroundColor: '#E6F5EC', alignItems: 'center', justifyContent: 'center' },
  modeBadgeText: { color: '#286344', fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.35 },
  draftBadge: { backgroundColor: '#FFF1D0' },
  draftBadgeText: { color: '#795408' },
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
  matchReason: { color: palette.creativePrimary, fontSize: 12, lineHeight: 17, fontWeight: '700' },
  objectiveBox: { gap: 4, borderRadius: 13, padding: 11, backgroundColor: '#F8F3FF' },
  fieldLabel: { color: palette.creativePrimary, fontSize: 9, lineHeight: 13, fontWeight: '800', letterSpacing: 0.45 },
  bodyText: { color: palette.creativeInk, fontSize: 13, lineHeight: 19, flexShrink: 1 },
  detailRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 7 },
  detailText: { color: palette.creativeMuted, fontSize: 12, lineHeight: 18, paddingLeft: 23 },
  instructionBox: { gap: 4 },
  safetyBox: { flexDirection: 'row', alignItems: 'flex-start', gap: 7, borderRadius: 12, padding: 10, backgroundColor: '#FFF5D9' },
  safetyText: { flex: 1, color: '#72530D', fontSize: 12, lineHeight: 17 },
  sourceText: { color: palette.creativeMuted, fontSize: 10, lineHeight: 15 },
  savedText: { color: '#286344', fontSize: 12, lineHeight: 18, fontWeight: '700', paddingHorizontal: 3 },
});
