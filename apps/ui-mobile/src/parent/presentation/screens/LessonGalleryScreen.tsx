import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { LessonDetail, LessonInvitation, LessonSummary, ParentGroupInvitation } from '../../domain/types';
import { Card, ChoiceRow, Notice, PrimaryButton, ScreenFrame, SecondaryButton, SectionTitle, TextButton, palette } from '../components/ui';
import { ALL_LESSONS_TOPIC, buildLessonCatalogViewModel } from './catalogViewModel';

function lessonInvitationStateLabel(state: string): string {
  switch (state.toUpperCase()) {
    case 'PENDING':
    case 'INVITED': return 'Đang chờ phản hồi';
    case 'ACCEPTED':
    case 'ACTIVE': return 'Đã được chấp nhận';
    case 'DECLINED': return 'Đã từ chối';
    case 'REVOKED': return 'Đã thu hồi';
    case 'EXPIRED': return 'Đã hết hạn';
    default: return 'Chưa xác định trạng thái';
  }
}

function parentGroupInvitationStateLabel(state: ParentGroupInvitation['state']): string {
  switch (state) {
    case 'INVITED': return 'Đang chờ bạn chấp nhận';
    case 'ACTIVE': return 'Đã tham gia';
    case 'REVOKED': return 'Đã thu hồi';
    case 'EXPIRED': return 'Đã hết hạn';
  }
}

type Props = {
  lessons: LessonSummary[];
  selectedLesson: LessonDetail | null;
  selectedPresetVersionId: string | null;
  lessonInvitations: LessonInvitation[];
  groupInvitations: ParentGroupInvitation[];
  loading: boolean;
  loadingId: string;
  error: string;
  onOpenLesson: (lessonId: string) => void;
  onUseLesson: (lesson: LessonDetail) => void;
  onAcceptLessonInvitation: (invitationId: string) => void;
  onDeclineLessonInvitation: (invitationId: string) => void;
  onAcceptGroupInvitation: (membershipId: string) => void;
  onBack: () => void;
  mode?: 'gallery' | 'picker';
};

export function LessonGalleryScreen(props: Props): React.JSX.Element {
  const isPicker = props.mode === 'picker';
  const [selectedTopic, setSelectedTopic] = useState(ALL_LESSONS_TOPIC);
  const catalog = buildLessonCatalogViewModel(props.lessons, selectedTopic);
  const showTopicFilters = !isPicker && catalog.topics.length > 1;

  return (
    <ScreenFrame
      title={isPicker ? 'Chọn bài giảng' : 'Thư viện bài giảng'}
      subtitle={isPicker ? 'Chọn và ghim phiên bản bài giảng bạn muốn dùng.' : 'Bài giảng được chia sẻ hoặc công khai cho phụ huynh.'}
      step={isPicker ? 'Thư viện' : undefined}
      onBack={props.onBack}
    >
      {props.error ? <Notice text={props.error} tone="error" /> : null}
      {props.loading ? <Card><Text style={styles.mutedText}>Đang tải thư viện…</Text></Card> : null}

      {props.selectedLesson ? (
        <Card style={styles.detailCard}>
          <SectionTitle>{props.selectedLesson.title}</SectionTitle>
          <Text style={styles.detailMeta}>
            {props.selectedLesson.topic} · phiên bản {props.selectedLesson.version_no} · mã {props.selectedLesson.version_id}
          </Text>
          <Text style={styles.detailMeta}>SHA-256: {props.selectedLesson.content_sha256}</Text>
          <View style={styles.detailSection}>
            <Text style={styles.sectionLabel}>Hướng dẫn vẽ</Text>
            <Text style={styles.bodyText}>{props.selectedLesson.drawing_steps_text}</Text>
          </View>
          <View style={styles.detailSection}>
            <Text style={styles.sectionLabel}>Điểm khám phá cùng bé</Text>
            <Text style={styles.bodyText}>{props.selectedLesson.subject_learning_notes}</Text>
          </View>
          {props.selectedLesson.objectives.length > 0 ? (
            <View style={styles.detailSection}>
              <Text style={styles.sectionLabel}>Mục tiêu</Text>
              {props.selectedLesson.objectives.map((objective, index) => (
                <Text key={`${objective}-${index}`} style={styles.bodyText}>• {objective}</Text>
              ))}
            </View>
          ) : null}
          {props.selectedLesson.activities.map((activity, index) => (
            <View key={`${activity.title}-${index}`} style={styles.activity}>
              <Text style={styles.activityTitle}>{activity.title}</Text>
              <Text style={styles.activityDescription}>{activity.objective}</Text>
            </View>
          ))}
          <PrimaryButton
            label={props.selectedPresetVersionId === props.selectedLesson.version_id ? 'Đã chọn cho buổi tiếp theo' : 'Dùng bài giảng này'}
            disabled={props.selectedPresetVersionId === props.selectedLesson.version_id}
            onPress={() => props.onUseLesson(props.selectedLesson!)}
          />
        </Card>
      ) : null}

      <Card style={styles.catalogCard}>
        <View style={styles.catalogHeading}>
          <SectionTitle>Bài giảng</SectionTitle>
        </View>

        {showTopicFilters ? (
          <View style={styles.topicFilters}>
            {catalog.topics.map((topic) => {
              const selected = catalog.selectedTopic === topic;
              return (
                <Pressable
                  key={topic}
                  accessibilityRole="button"
                  accessibilityLabel={topic}
                  accessibilityState={{ selected }}
                  onPress={() => setSelectedTopic(topic)}
                  style={({ pressed }) => [
                    styles.topicChip,
                    selected && styles.topicChipSelected,
                    pressed && styles.topicChipPressed,
                  ]}
                >
                  <Text style={[styles.topicChipText, selected && styles.topicChipTextSelected]}>{topic}</Text>
                </Pressable>
              );
            })}
          </View>
        ) : null}

        {catalog.emptyState === 'no-lessons' && !props.loading && !props.error ? (
          <Text style={styles.emptyText}>Chưa có bài giảng được chia sẻ.</Text>
        ) : null}

        {catalog.visibleLessons.map((lesson) => (
          <ChoiceRow
            key={`${lesson.lesson_id}:${lesson.version_id}`}
            title={lesson.title}
            detail={`${lesson.topic} · phiên bản ${lesson.version_id} · ${lesson.activity_count} hoạt động · ${lesson.access_source === 'PUBLIC' ? 'Công khai' : 'Được chia sẻ'}`}
            selected={props.selectedLesson?.lesson_id === lesson.lesson_id && props.selectedLesson.version_id === lesson.version_id}
            onPress={() => props.onOpenLesson(lesson.lesson_id)}
          />
        ))}

        {props.loadingId ? <Text style={styles.loadingDetail}>Đang tải nội dung…</Text> : null}
      </Card>

      {!isPicker ? (
        <>
          <Card style={styles.invitationCard}>
            <SectionTitle>Lời mời bài giảng</SectionTitle>
            {!props.loading && !props.error && props.lessonInvitations.length === 0 ? (
              <Text style={styles.emptyText}>Không có lời mời đang chờ.</Text>
            ) : null}
            {props.lessonInvitations.map((item) => {
              const canRespond = item.state.toUpperCase() === 'PENDING' || item.state.toUpperCase() === 'INVITED';
              const actionBusy = props.loadingId === item.access_grant_id;
              return (
                <View key={item.access_grant_id} style={styles.invitationItem}>
                  <Text style={styles.invitationTitle}>Bài giảng được mời chia sẻ</Text>
                  <Text style={styles.invitationMeta}>Trạng thái từ máy chủ: {lessonInvitationStateLabel(item.state)}</Text>
                  {canRespond ? <>
                    <PrimaryButton label={actionBusy ? 'Đang kiểm tra…' : 'Chấp nhận'} busy={actionBusy} disabled={Boolean(props.loadingId)} onPress={() => props.onAcceptLessonInvitation(item.access_grant_id)} />
                    <TextButton label="Từ chối lời mời" disabled={Boolean(props.loadingId)} onPress={() => props.onDeclineLessonInvitation(item.access_grant_id)} />
                  </> : null}
                </View>
              );
            })}
          </Card>

          <Card style={styles.invitationCard}>
            <SectionTitle>Lời mời nhóm phụ huynh</SectionTitle>
            {!props.loading && !props.error && props.groupInvitations.length === 0 ? (
              <Text style={styles.emptyText}>Không có lời mời đang chờ.</Text>
            ) : null}
            {props.groupInvitations.map((item) => {
              const actionBusy = props.loadingId === item.membership_id;
              return (
                <View key={item.membership_id} style={styles.invitationItem}>
                  <Text style={styles.invitationTitle}>Nhóm phụ huynh</Text>
                  <Text style={styles.invitationMeta}>Trạng thái từ máy chủ: {parentGroupInvitationStateLabel(item.state)}</Text>
                  {item.state === 'INVITED' ? <SecondaryButton
                    label={actionBusy ? 'Đang kiểm tra…' : 'Chấp nhận lời mời'}
                    disabled={Boolean(props.loadingId)}
                    onPress={() => props.onAcceptGroupInvitation(item.membership_id)}
                  /> : null}
                </View>
              );
            })}
          </Card>
        </>
      ) : null}
    </ScreenFrame>
  );
}

const styles = StyleSheet.create({
  detailCard: {
    padding: 18,
  },
  detailMeta: {
    color: palette.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  detailSection: {
    gap: 5,
  },
  sectionLabel: {
    color: palette.ink,
    fontSize: 14,
    fontWeight: '800',
  },
  bodyText: {
    color: palette.ink,
    fontSize: 14,
    lineHeight: 21,
  },
  activity: {
    gap: 4,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: palette.border,
    paddingTop: 10,
  },
  activityTitle: {
    color: palette.ink,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '700',
  },
  activityDescription: {
    color: palette.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  catalogCard: {
    padding: 18,
  },
  catalogHeading: {
    minHeight: 26,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  topicFilters: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  topicChip: {
    minHeight: 48,
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: palette.border,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 7,
    backgroundColor: palette.white,
  },
  topicChipSelected: {
    borderColor: palette.blue,
    backgroundColor: palette.paleBlue,
  },
  topicChipPressed: {
    opacity: 0.78,
  },
  topicChipText: {
    color: palette.muted,
    fontSize: 13,
    lineHeight: 18,
    fontWeight: '700',
  },
  topicChipTextSelected: {
    color: palette.blue,
  },
  emptyText: {
    color: palette.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  mutedText: {
    color: palette.muted,
    fontSize: 14,
    lineHeight: 20,
  },
  loadingDetail: {
    color: palette.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  invitationCard: {
    padding: 18,
  },
  invitationItem: {
    gap: 7,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: palette.border,
    paddingTop: 10,
  },
  invitationTitle: {
    color: palette.ink,
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '700',
  },
  invitationMeta: {
    color: palette.muted,
    fontSize: 12,
    lineHeight: 18,
  },
});
