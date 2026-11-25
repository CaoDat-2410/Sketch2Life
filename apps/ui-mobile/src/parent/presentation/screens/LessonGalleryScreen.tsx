import React, { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { LessonDetail, LessonInvitation, LessonSummary, ParentGroupInvitation, ParentGroupMembershipV1 } from '../../domain/types';
import { Card, Notice, ScreenFrame, SecondaryButton, SectionTitle, TextButton, palette } from '../components/ui';
import { ALL_LESSONS_TOPIC, buildLessonCatalogViewModel } from './catalogViewModel';
import { canLeaveParentGroupMembership } from '../navigation/workflowTypes';

type Props = {
  lessons: LessonSummary[];
  selectedLesson: LessonDetail | null;
  selectedPresetVersionId: string | null;
  lessonInvitations: LessonInvitation[];
  groupInvitations: ParentGroupInvitation[];
  groupMemberships: ParentGroupMembershipV1[];
  searchQuery: string;
  searchTopic: string;
  hasMoreLessons: boolean;
  hasMoreGroupMemberships: boolean;
  groupMembershipsLoading: boolean;
  loading: boolean;
  loadingId: string;
  error: string;
  onOpenLesson: (lessonId: string) => void;
  onUseLesson: (lesson: LessonDetail) => void;
  onAcceptLessonInvitation: (invitationId: string) => void;
  onDeclineLessonInvitation: (invitationId: string) => void;
  onAcceptGroupInvitation: (membershipId: string) => void;
  onDeclineGroupInvitation: (membershipId: string) => void;
  onLeaveGroup: (membership: ParentGroupMembershipV1) => void;
  onSearchLessons: (query: string, topic: string) => void;
  onLoadMoreLessons: () => void;
  onLoadMoreGroupMemberships: () => void;
  onBack: () => void;
  mode?: 'gallery' | 'picker';
};

function lessonInvitationStateLabel(state: string): string {
  switch (state.toUpperCase()) {
    case 'PENDING':
    case 'INVITED': return 'Đang chờ phản hồi';
    case 'ACCEPTED':
    case 'ACTIVE': return 'Đã chấp nhận';
    case 'DECLINED': return 'Đã từ chối';
    case 'REVOKED': return 'Đã thu hồi';
    case 'EXPIRED': return 'Đã hết hạn';
    default: return 'Chưa xác định';
  }
}

function parentGroupInvitationStateLabel(state: ParentGroupInvitation['state']): string {
  switch (state) {
    case 'INVITED': return 'Đang chờ bạn chấp nhận';
    case 'ACTIVE': return 'Đã tham gia';
    case 'REVOKED': return 'Đã thu hồi';
    case 'EXPIRED': return 'Đã hết hạn';
    case 'DECLINED': return 'Đã từ chối';
  }
}

function accessLabel(source: LessonSummary['access_source']): string {
  return source === 'PUBLIC' ? 'Công khai' : 'Được chia sẻ';
}

function expiryLabel(value: string | null): string | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return `Có hiệu lực đến ${date.toLocaleDateString('vi-VN')}`;
}

function confirmLeaveGroup(membership: ParentGroupMembershipV1, onConfirm: () => void): void {
  Alert.alert(
    'Xác nhận rời nhóm',
    'Bạn sẽ mất quyền truy cập các bài học được chia sẻ qua nhóm này. Nhà trường có thể mời bạn tham gia lại sau.',
    [
      { text: 'Hủy', style: 'cancel' },
      { text: 'Rời nhóm', style: 'destructive', onPress: onConfirm },
    ],
  );
}

function StatusPill({ label, selected = false }: { label: string; selected?: boolean }): React.JSX.Element {
  return (
    <View style={[styles.statusPill, selected && styles.statusPillSelected]}>
      <Text style={[styles.statusPillText, selected && styles.statusPillTextSelected]} numberOfLines={1}>{label}</Text>
    </View>
  );
}

function PrimaryLessonButton({
  label,
  onPress,
  disabled = false,
  busy = false,
}: {
  label: string;
  onPress: () => void;
  disabled?: boolean;
  busy?: boolean;
}): React.JSX.Element {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ disabled: disabled || busy, busy }}
      disabled={disabled || busy}
      onPress={onPress}
      style={({ pressed }) => [styles.primaryLessonButton, (disabled || busy) && styles.primaryLessonButtonDisabled, pressed && styles.lessonRowPressed]}
    >
      {busy ? <ActivityIndicator color={colors.purple} /> : null}
      <Text style={[styles.primaryLessonButtonText, (disabled || busy) && styles.primaryLessonButtonTextDisabled]}>{label}</Text>
    </Pressable>
  );
}

function LessonRow({
  lesson,
  isOpen,
  isPreset,
  busy,
  onPress,
}: {
  lesson: LessonSummary;
  isOpen: boolean;
  isPreset: boolean;
  busy: boolean;
  onPress: () => void;
}): React.JSX.Element {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${lesson.title}, ${lesson.topic || 'bài học'}, ${lesson.activity_count} hoạt động, ${accessLabel(lesson.access_source)}`}
      accessibilityState={{ selected: isOpen, busy }}
      onPress={onPress}
      disabled={busy}
      style={({ pressed }) => [styles.lessonRow, isOpen && styles.lessonRowOpen, pressed && styles.lessonRowPressed]}
    >
      <View style={[styles.lessonIconTile, isOpen && styles.lessonIconTileOpen]}>
        {busy
          ? <ActivityIndicator size="small" color={colors.purple} />
          : <Ionicons name="book-outline" size={23} color={colors.purple} accessible={false} />}
      </View>
      <View style={styles.lessonRowCopy}>
        <Text style={styles.lessonTitle} numberOfLines={2}>{lesson.title}</Text>
        <Text style={styles.lessonTopic} numberOfLines={1}>{lesson.topic || 'Bài học'}</Text>
        <View style={styles.lessonMetaRow}>
          <StatusPill label={accessLabel(lesson.access_source)} />
          <Text style={styles.activityCount}>{lesson.activity_count} hoạt động</Text>
        </View>
      </View>
      <View style={styles.lessonRowEnd}>
        {isPreset ? <StatusPill label="Đang dùng" selected /> : isOpen ? <StatusPill label="Đang xem" /> : null}
        <Ionicons name="chevron-forward" size={19} color={colors.mutedPurple} accessible={false} />
      </View>
    </Pressable>
  );
}

function DetailSection({
  icon,
  title,
  children,
}: React.PropsWithChildren<{ icon: React.ComponentProps<typeof Ionicons>['name']; title: string }>): React.JSX.Element {
  return (
    <View style={styles.detailSection}>
      <View style={styles.detailSectionHeading}>
        <Ionicons name={icon} size={18} color={colors.purple} accessible={false} />
        <Text style={styles.detailSectionTitle}>{title}</Text>
      </View>
      {children}
    </View>
  );
}

export function LessonGalleryScreen(props: Props): React.JSX.Element {
  const isPicker = props.mode === 'picker';
  const [selectedTopic, setSelectedTopic] = useState(ALL_LESSONS_TOPIC);
  const [searchQuery, setSearchQuery] = useState(props.searchQuery);
  const [searchTopic, setSearchTopic] = useState(props.searchTopic);
  const catalog = buildLessonCatalogViewModel(props.lessons, selectedTopic);
  const showTopicFilters = !isPicker && catalog.topics.length > 1;
  const selectedVersion = props.selectedLesson
    ? props.selectedPresetVersionId === props.selectedLesson.version_id
    : false;

  return (
    <ScreenFrame
      title={isPicker ? 'Chọn bài học' : 'Thư viện bài học'}
      subtitle={isPicker ? 'Chọn bài học phù hợp cho buổi sáng tạo cùng bé.' : 'Những bài học công khai và được chia sẻ với gia đình.'}
      step={isPicker ? 'Thư viện' : undefined}
      onBack={props.onBack}
      visualTone="creative"
      safeAreaEdges={isPicker ? ['top', 'right', 'bottom', 'left'] : ['top', 'right', 'left']}
    >
      {props.error ? <Notice text={props.error} tone="error" /> : null}

      <Card style={styles.searchCard}>
        <TextInput
          accessibilityLabel="Tìm bài học"
          autoCapitalize="none"
          maxLength={100}
          onChangeText={setSearchQuery}
          onSubmitEditing={() => props.onSearchLessons(searchQuery, searchTopic)}
          placeholder="Tìm bài học"
          returnKeyType="search"
          style={styles.searchInput}
          value={searchQuery}
        />
        <TextInput
          accessibilityLabel="Chủ đề tùy chọn"
          maxLength={120}
          onChangeText={setSearchTopic}
          onSubmitEditing={() => props.onSearchLessons(searchQuery, searchTopic)}
          placeholder="Chủ đề (không bắt buộc)"
          returnKeyType="search"
          style={styles.searchInput}
          value={searchTopic}
        />
        <Pressable accessibilityRole="button" accessibilityState={{ disabled: props.loading }} disabled={props.loading} onPress={() => props.onSearchLessons(searchQuery, searchTopic)} style={styles.searchButton}>
          <Ionicons name="search" size={17} color="#FFFFFF" accessible={false} />
          <Text style={styles.searchButtonText}>Tìm kiếm</Text>
        </Pressable>
      </Card>

      <Card style={styles.catalogCard}>
        <View style={styles.catalogHeader}>
          <View style={styles.sectionIconTile}>
            <Ionicons name="library-outline" size={22} color={colors.purple} accessible={false} />
          </View>
          <View style={styles.catalogHeadingCopy}>
            <SectionTitle>{isPicker ? 'Chọn từ thư viện' : 'Khám phá bài học'}</SectionTitle>
            {props.lessons.length > 0 ? <Text style={styles.sectionCaption}>
              {props.lessons.length === 1 ? '1 bài học phù hợp' : `${props.lessons.length} bài học phù hợp`}
            </Text> : null}
          </View>
        </View>

        {showTopicFilters ? (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.topicFilters}
            bounces={false}
            overScrollMode="never"
          >
            {catalog.topics.map((topic) => {
              const selected = catalog.selectedTopic === topic;
              return (
                <Pressable
                  key={topic}
                  accessibilityRole="button"
                  accessibilityLabel={`Chủ đề ${topic}`}
                  accessibilityState={{ selected }}
                  onPress={() => setSelectedTopic(topic)}
                  style={({ pressed }) => [styles.topicChip, selected && styles.topicChipSelected, pressed && styles.topicChipPressed]}
                >
                  <Text style={[styles.topicChipText, selected && styles.topicChipTextSelected]}>{topic}</Text>
                </Pressable>
              );
            })}
          </ScrollView>
        ) : null}

        {props.loading && props.lessons.length === 0 ? (
          <View style={styles.loadingState}>
            <ActivityIndicator color={colors.purple} />
            <Text style={styles.stateBody}>Đang tải bài học…</Text>
          </View>
        ) : null}

        {catalog.emptyState === 'no-lessons' && !props.loading && !props.error ? (
          <View style={styles.emptyState}>
            <View style={styles.emptyIconTile}>
              <Ionicons name="book-outline" size={29} color={colors.purple} accessible={false} />
            </View>
            <Text style={styles.emptyTitle}>Chưa có bài học</Text>
            <Text style={styles.stateBody}>Bài học công khai hoặc được chia sẻ sẽ xuất hiện tại đây.</Text>
          </View>
        ) : null}

        {catalog.visibleLessons.map((lesson) => (
          <LessonRow
            key={`${lesson.lesson_id}:${lesson.version_id}`}
            lesson={lesson}
            isOpen={props.selectedLesson?.lesson_id === lesson.lesson_id && props.selectedLesson.version_id === lesson.version_id}
            isPreset={props.selectedPresetVersionId === lesson.version_id}
            busy={props.loadingId === lesson.lesson_id}
            onPress={() => props.onOpenLesson(lesson.lesson_id)}
          />
        ))}
      </Card>

      {props.hasMoreLessons ? (
        <Pressable accessibilityRole="button" accessibilityState={{ busy: props.loading, disabled: props.loading }} disabled={props.loading} onPress={props.onLoadMoreLessons} style={styles.loadMoreButton}>
          {props.loading ? <ActivityIndicator size="small" color={colors.purple} /> : null}
          <Text style={styles.loadMoreText}>{props.loading ? 'Đang tải…' : 'Xem thêm bài học'}</Text>
        </Pressable>
      ) : null}

      {props.loadingId && props.selectedLesson === null && props.lessons.length > 0 ? (
        <View style={styles.inlineLoading}>
          <ActivityIndicator size="small" color={colors.purple} />
          <Text style={styles.stateBody}>Đang mở chi tiết bài học…</Text>
        </View>
      ) : null}

      {props.selectedLesson ? (
        <Card style={styles.detailCard}>
          <View style={styles.detailTopline}>
            <View style={styles.detailBadge}>
              <Ionicons name="sparkles-outline" size={14} color={colors.purple} accessible={false} />
              <Text style={styles.detailBadgeText}>CHI TIẾT BÀI HỌC</Text>
            </View>
            {selectedVersion ? <StatusPill label="Đang dùng" selected /> : null}
          </View>
          <Text style={styles.detailTitle}>{props.selectedLesson.title}</Text>
          <Text style={styles.detailMeta}>
            {[props.selectedLesson.topic, `Phiên bản ${props.selectedLesson.version_no}`, accessLabel(props.selectedLesson.access_source)]
              .filter(Boolean).join('  ·  ')}
          </Text>

          {props.selectedLesson.drawing_subject.trim() ? (
            <View style={styles.subjectCallout}>
              <Ionicons name="color-palette-outline" size={20} color={colors.purple} accessible={false} />
              <View style={styles.subjectCopy}>
                <Text style={styles.subjectLabel}>Cùng bé vẽ</Text>
                <Text style={styles.subjectTitle}>{props.selectedLesson.drawing_subject}</Text>
              </View>
            </View>
          ) : null}

          {props.selectedLesson.objectives.length > 0 ? (
            <DetailSection icon="compass-outline" title="Bé sẽ khám phá">
              {props.selectedLesson.objectives.map((objective, index) => (
                <View key={`${objective}-${index}`} style={styles.bulletRow}>
                  <View style={styles.bullet} />
                  <Text style={styles.bodyText}>{objective}</Text>
                </View>
              ))}
            </DetailSection>
          ) : null}

          {props.selectedLesson.drawing_steps_text.trim() ? (
            <DetailSection icon="create-outline" title="Các bước vẽ">
              <Text style={styles.bodyText}>{props.selectedLesson.drawing_steps_text}</Text>
            </DetailSection>
          ) : null}

          {props.selectedLesson.subject_learning_notes.trim() ? (
            <DetailSection icon="chatbubble-ellipses-outline" title="Gợi ý trò chuyện">
              <Text style={styles.bodyText}>{props.selectedLesson.subject_learning_notes}</Text>
            </DetailSection>
          ) : null}

          {props.selectedLesson.script_following_allowed && props.selectedLesson.script_direction?.trim() ? (
            <DetailSection icon="musical-notes-outline" title="Gợi ý kể chuyện">
              <Text style={styles.bodyText}>{props.selectedLesson.script_direction}</Text>
            </DetailSection>
          ) : null}

          {props.selectedLesson.activities.length > 0 ? (
            <DetailSection icon="leaf-outline" title={`Hoạt động cùng bé · ${props.selectedLesson.activities.length}`}>
              {props.selectedLesson.activities.map((activity, index) => (
                <View key={`${activity.title}-${index}`} style={styles.activityItem}>
                  <Text style={styles.activityTitle}>{activity.title}</Text>
                  {activity.objective.trim() ? <Text style={styles.bodyText}>{activity.objective}</Text> : null}
                  {activity.materials_text.trim() ? <Text style={styles.activityMeta}>Chuẩn bị: {activity.materials_text}</Text> : null}
                  {activity.instructions_text.trim() ? <Text style={styles.bodyText}>{activity.instructions_text}</Text> : null}
                  {activity.safety_notes.trim() ? <Text style={styles.safetyNote}>Lưu ý an toàn: {activity.safety_notes}</Text> : null}
                </View>
              ))}
            </DetailSection>
          ) : null}

          <PrimaryLessonButton
            label={selectedVersion ? 'Bài học đã được chọn' : isPicker ? 'Chọn bài học này' : 'Dùng bài học này'}
            disabled={selectedVersion}
            onPress={() => props.onUseLesson(props.selectedLesson!)}
          />
        </Card>
      ) : null}

      {!isPicker ? (
        <>
          <Card style={styles.invitationCard}>
            <View style={styles.invitationHeading}>
              <View style={styles.sectionIconTileSmall}>
                <Ionicons name="mail-open-outline" size={19} color={colors.purple} accessible={false} />
              </View>
              <SectionTitle>Lời mời bài học</SectionTitle>
            </View>
            {!props.loading && !props.error && props.lessonInvitations.length === 0 ? (
              <Text style={styles.stateBody}>Chưa có lời mời bài học nào.</Text>
            ) : null}
            {props.lessonInvitations.map((item) => {
              const canRespond = ['PENDING', 'INVITED'].includes(item.state.toUpperCase());
              const actionBusy = props.loadingId === item.access_grant_id;
              const expires = expiryLabel(item.expires_at);
              return (
                <View key={item.access_grant_id} style={styles.invitationItem}>
                  <View style={styles.invitationItemTitleRow}>
                    <Text style={styles.invitationTitle}>Bài học được chia sẻ với bạn</Text>
                    <StatusPill label={lessonInvitationStateLabel(item.state)} selected={canRespond} />
                  </View>
                  {expires ? <Text style={styles.activityMeta}>{expires}</Text> : null}
                  {canRespond ? (
                    <View style={styles.invitationActions}>
                      <PrimaryLessonButton
                        label={actionBusy ? 'Đang xử lý…' : 'Chấp nhận'}
                        busy={actionBusy}
                        disabled={Boolean(props.loadingId)}
                        onPress={() => props.onAcceptLessonInvitation(item.access_grant_id)}
                      />
                      <TextButton
                        label="Từ chối"
                        disabled={Boolean(props.loadingId)}
                        onPress={() => props.onDeclineLessonInvitation(item.access_grant_id)}
                      />
                    </View>
                  ) : null}
                </View>
              );
            })}
          </Card>

          <Card style={styles.invitationCard}>
            <View style={styles.invitationHeading}>
              <View style={styles.sectionIconTileSmall}>
                <Ionicons name="people-outline" size={19} color={colors.purple} accessible={false} />
              </View>
              <SectionTitle>Lời mời nhóm phụ huynh</SectionTitle>
            </View>
            {!props.loading && !props.error && props.groupInvitations.length === 0 ? (
              <Text style={styles.stateBody}>Chưa có lời mời nhóm nào.</Text>
            ) : null}
            {props.groupInvitations.map((item) => {
              const actionBusy = props.loadingId === item.membership_id;
              return (
                <View key={item.membership_id} style={styles.invitationItem}>
                  <View style={styles.invitationItemTitleRow}>
                    <Text style={styles.invitationTitle}>Nhóm phụ huynh</Text>
                    <StatusPill label={parentGroupInvitationStateLabel(item.state)} selected={item.state === 'INVITED'} />
                  </View>
                  {item.state === 'INVITED' ? (
                    <View style={styles.groupInvitationActions}>
                      <SecondaryButton
                        label={actionBusy ? 'Đang xử lý…' : 'Chấp nhận'}
                        disabled={Boolean(props.loadingId)}
                        onPress={() => props.onAcceptGroupInvitation(item.membership_id)}
                      />
                      <TextButton
                        label="Từ chối"
                        disabled={Boolean(props.loadingId)}
                        onPress={() => props.onDeclineGroupInvitation(item.membership_id)}
                      />
                    </View>
                  ) : null}
                </View>
              );
            })}
          </Card>

          <Card style={styles.invitationCard}>
            <View style={styles.invitationHeading}>
              <View style={styles.sectionIconTileSmall}>
                <Ionicons name="people-outline" size={19} color={colors.purple} accessible={false} />
              </View>
              <SectionTitle>Nhóm của tôi</SectionTitle>
            </View>
            {!props.loading && props.groupMemberships.length === 0 ? (
              <Text style={styles.stateBody}>Bạn chưa tham gia nhóm nào.</Text>
            ) : null}
            {props.groupMemberships.map((membership) => {
              const canLeave = canLeaveParentGroupMembership(membership);
              const actionBusy = props.loadingId === `group:${membership.membership_id}:leave`;
              return (
                <View key={membership.membership_id} style={styles.membershipItem}>
                  <Text style={styles.invitationTitle}>Nhóm phụ huynh</Text>
                  <StatusPill label="Đã tham gia" selected />
                  {canLeave ? (
                    <TextButton
                      label={actionBusy ? 'Đang xử lý…' : 'Rời nhóm'}
                      disabled={Boolean(props.loadingId)}
                      onPress={() => confirmLeaveGroup(membership, () => props.onLeaveGroup(membership))}
                    />
                  ) : null}
                </View>
              );
            })}
            {props.hasMoreGroupMemberships ? (
              <Pressable accessibilityRole="button" accessibilityState={{ busy: props.groupMembershipsLoading, disabled: props.groupMembershipsLoading }} disabled={props.groupMembershipsLoading} onPress={props.onLoadMoreGroupMemberships} style={styles.loadMoreButton}>
                {props.groupMembershipsLoading ? <ActivityIndicator size="small" color={colors.purple} /> : null}
                <Text style={styles.loadMoreText}>{props.groupMembershipsLoading ? 'Đang tải…' : 'Xem thêm nhóm'}</Text>
              </Pressable>
            ) : null}
          </Card>
        </>
      ) : null}
    </ScreenFrame>
  );
}

const colors = {
  purple: '#7435D5',
  deepPurple: '#281451',
  lavender: '#F1E7FF',
  softLavender: '#F8F3FF',
  border: '#E4D6F5',
  mutedPurple: '#796C8D',
  warmSurface: '#FFFAF6',
};

const styles = StyleSheet.create({
  searchCard: { backgroundColor: '#FFFEFC', borderColor: colors.border, borderRadius: 20, borderWidth: 1, gap: 9, padding: 13 },
  searchInput: { minHeight: 46, borderColor: colors.border, borderRadius: 13, borderWidth: 1, color: colors.deepPurple, fontSize: 14, paddingHorizontal: 12 },
  searchButton: { minHeight: 44, alignItems: 'center', alignSelf: 'flex-start', backgroundColor: colors.purple, borderRadius: 13, flexDirection: 'row', gap: 7, justifyContent: 'center', paddingHorizontal: 14 },
  searchButtonText: { color: '#FFFFFF', fontSize: 13, fontWeight: '800' },
  loadMoreButton: { minHeight: 48, alignItems: 'center', backgroundColor: colors.lavender, borderRadius: 15, flexDirection: 'row', gap: 8, justifyContent: 'center' },
  loadMoreText: { color: colors.deepPurple, fontSize: 13, fontWeight: '800' },
  catalogCard: {
    backgroundColor: '#FFFEFC',
    borderColor: colors.border,
    borderRadius: 23,
    borderWidth: 1.2,
    gap: 15,
    padding: 16,
    minWidth: 0,
  },
  catalogHeader: { alignItems: 'center', flexDirection: 'row', gap: 12, minWidth: 0 },
  sectionIconTile: {
    alignItems: 'center',
    backgroundColor: colors.lavender,
    borderRadius: 16,
    height: 46,
    justifyContent: 'center',
    width: 46,
  },
  catalogHeadingCopy: { flex: 1, gap: 2, minWidth: 0 },
  sectionCaption: { color: palette.muted, fontSize: 12, lineHeight: 17 },
  topicFilters: { alignItems: 'center', gap: 8, paddingRight: 4 },
  topicChip: {
    alignItems: 'center',
    backgroundColor: colors.warmSurface,
    borderColor: colors.border,
    borderRadius: 999,
    borderWidth: 1,
    justifyContent: 'center',
    minHeight: 42,
    paddingHorizontal: 15,
  },
  topicChipSelected: { backgroundColor: colors.purple, borderColor: colors.purple },
  topicChipPressed: { opacity: 0.78 },
  topicChipText: { color: colors.deepPurple, fontSize: 13, fontWeight: '700' },
  topicChipTextSelected: { color: '#FFFFFF' },
  lessonRow: {
    alignItems: 'center',
    backgroundColor: colors.warmSurface,
    borderColor: '#EEE5F6',
    borderRadius: 18,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 11,
    minHeight: 92,
    paddingHorizontal: 11,
    paddingVertical: 11,
  },
  lessonRowOpen: { backgroundColor: colors.softLavender, borderColor: '#CDB6EF' },
  lessonRowPressed: { opacity: 0.82 },
  lessonIconTile: {
    alignItems: 'center',
    backgroundColor: '#F1E7FF',
    borderRadius: 14,
    height: 48,
    justifyContent: 'center',
    width: 48,
  },
  lessonIconTileOpen: { backgroundColor: '#E5D4FF' },
  lessonRowCopy: { flex: 1, gap: 3, minWidth: 0 },
  lessonTitle: { color: colors.deepPurple, fontSize: 15, fontWeight: '800', lineHeight: 20 },
  lessonTopic: { color: palette.muted, fontSize: 12, lineHeight: 16 },
  lessonMetaRow: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginTop: 3 },
  statusPill: {
    alignSelf: 'flex-start',
    backgroundColor: '#F1E7FF',
    borderRadius: 999,
    justifyContent: 'center',
    minHeight: 23,
    paddingHorizontal: 9,
    paddingVertical: 3,
  },
  statusPillSelected: { backgroundColor: '#E8D9FF' },
  statusPillText: { color: colors.deepPurple, fontSize: 10, fontWeight: '700', lineHeight: 14 },
  statusPillTextSelected: { color: colors.purple },
  activityCount: { color: colors.mutedPurple, fontSize: 11, lineHeight: 15 },
  lessonRowEnd: { alignItems: 'flex-end', gap: 7, justifyContent: 'center' },
  loadingState: { alignItems: 'center', flexDirection: 'row', gap: 11, paddingVertical: 14 },
  inlineLoading: { alignItems: 'center', flexDirection: 'row', gap: 10, paddingHorizontal: 5, paddingVertical: 3 },
  stateBody: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1 },
  emptyState: { alignItems: 'center', gap: 8, paddingHorizontal: 18, paddingVertical: 23 },
  emptyIconTile: {
    alignItems: 'center',
    backgroundColor: colors.lavender,
    borderRadius: 22,
    height: 62,
    justifyContent: 'center',
    marginBottom: 3,
    width: 62,
  },
  emptyTitle: { color: colors.deepPurple, fontSize: 17, fontWeight: '800', lineHeight: 23, textAlign: 'center' },
  detailCard: {
    backgroundColor: '#FFFEFC',
    borderColor: colors.border,
    borderRadius: 23,
    borderWidth: 1.2,
    gap: 15,
    padding: 17,
    minWidth: 0,
  },
  detailTopline: { alignItems: 'center', flexDirection: 'row', justifyContent: 'space-between', gap: 8 },
  detailBadge: { alignItems: 'center', backgroundColor: colors.lavender, borderRadius: 999, flexDirection: 'row', gap: 5, minHeight: 27, paddingHorizontal: 10 },
  detailBadgeText: { color: colors.purple, fontSize: 10, fontWeight: '800', letterSpacing: 0.4 },
  detailTitle: { color: colors.deepPurple, fontSize: 21, fontWeight: '800', lineHeight: 27 },
  detailMeta: { color: colors.mutedPurple, fontSize: 12, lineHeight: 17 },
  subjectCallout: { alignItems: 'center', backgroundColor: colors.softLavender, borderRadius: 16, flexDirection: 'row', gap: 11, padding: 13 },
  subjectCopy: { flex: 1, gap: 2, minWidth: 0 },
  subjectLabel: { color: colors.mutedPurple, fontSize: 11, lineHeight: 15 },
  subjectTitle: { color: colors.deepPurple, fontSize: 15, fontWeight: '800', lineHeight: 21 },
  detailSection: { gap: 9, minWidth: 0 },
  detailSectionHeading: { alignItems: 'center', flexDirection: 'row', gap: 8 },
  detailSectionTitle: { color: colors.deepPurple, fontSize: 14, fontWeight: '800', lineHeight: 20, flexShrink: 1 },
  bulletRow: { alignItems: 'flex-start', flexDirection: 'row', gap: 9, paddingLeft: 2 },
  bullet: { backgroundColor: colors.purple, borderRadius: 4, height: 7, marginTop: 6, width: 7 },
  bodyText: { color: palette.ink, flexShrink: 1, fontSize: 13, lineHeight: 19, minWidth: 0 },
  activityItem: { backgroundColor: colors.warmSurface, borderRadius: 15, gap: 7, padding: 12 },
  activityTitle: { color: colors.deepPurple, fontSize: 14, fontWeight: '800', lineHeight: 19 },
  activityMeta: { color: colors.mutedPurple, fontSize: 12, lineHeight: 17 },
  safetyNote: { backgroundColor: '#FFF5D9', borderRadius: 10, color: '#604800', fontSize: 12, lineHeight: 17, padding: 9 },
  invitationCard: {
    backgroundColor: '#FFFEFC',
    borderColor: colors.border,
    borderRadius: 21,
    borderWidth: 1.1,
    gap: 13,
    padding: 15,
    minWidth: 0,
  },
  invitationHeading: { alignItems: 'center', flexDirection: 'row', gap: 10 },
  sectionIconTileSmall: { alignItems: 'center', backgroundColor: colors.lavender, borderRadius: 13, height: 38, justifyContent: 'center', width: 38 },
  invitationItem: { borderTopColor: '#EEE5F6', borderTopWidth: 1, gap: 9, paddingTop: 12 },
  invitationItemTitleRow: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 8, justifyContent: 'space-between' },
  invitationTitle: { color: colors.deepPurple, flex: 1, fontSize: 14, fontWeight: '800', lineHeight: 19, minWidth: 0 },
  invitationActions: { gap: 4 },
  groupInvitationActions: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  membershipItem: { alignItems: 'center', borderTopColor: '#EEE5F6', borderTopWidth: 1, flexDirection: 'row', gap: 10, minHeight: 50, paddingTop: 9 },
  primaryLessonButton: {
    alignItems: 'center',
    backgroundColor: colors.purple,
    borderRadius: 17,
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    minHeight: 52,
    paddingHorizontal: 18,
  },
  primaryLessonButtonDisabled: { backgroundColor: '#EAE1F2' },
  primaryLessonButtonText: { color: '#FFFFFF', fontSize: 15, fontWeight: '800', lineHeight: 20, textAlign: 'center' },
  primaryLessonButtonTextDisabled: { color: colors.mutedPurple },
});
