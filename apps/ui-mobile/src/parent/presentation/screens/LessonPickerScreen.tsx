import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import type { LessonSummary } from '../../domain/types';
import { Card, Notice, ScreenFrame, SectionTitle, palette } from '../components/ui';

type Props = {
  lessons: LessonSummary[];
  selectedId: string;
  loading: boolean;
  loadingId: string;
  error: string;
  searchQuery: string;
  searchTopic: string;
  hasMore: boolean;
  onSearch: (query: string, topic: string) => void;
  onLoadMore: () => void;
  onSelect: (lessonId: string) => void;
  onClear: () => void;
  onBack: () => void;
};

export function LessonPickerScreen(props: Props): React.JSX.Element {
  const [searchQuery, setSearchQuery] = useState(props.searchQuery);
  const [searchTopic, setSearchTopic] = useState(props.searchTopic);
  const selection = props.lessons.find((lesson) => lesson.lesson_id === props.selectedId);
  const submitSearch = () => props.onSearch(searchQuery, searchTopic);

  return (
    <ScreenFrame
      title="Chọn bài học"
      subtitle="Chọn một bài học phù hợp cho buổi sáng tạo cùng bé."
      step="Thư viện"
      onBack={props.onBack}
      visualTone="creative"
    >
      {props.error ? <Notice variant="creative" text={props.error} tone="error" /> : null}

      <Card variant="creative" style={styles.introCard}>
        <View style={styles.introHeading}>
          <View style={styles.introIcon}>
            <Ionicons name="color-palette-outline" size={23} color={colors.purple} accessible={false} />
          </View>
          <View style={styles.introCopy}>
            <SectionTitle variant="creative">{selection ? 'Bài học đã chọn' : 'Chọn cảm hứng cho bé'}</SectionTitle>
            <Text style={styles.introText}>
              {selection ? selection.title : 'Chọn một bài học để xem và dùng trong buổi sáng tạo.'}
            </Text>
          </View>
        </View>
        {props.lessons.length > 0 ? <View style={styles.countPill}>
          <Ionicons name="library-outline" size={15} color={colors.purple} accessible={false} />
          <Text style={styles.countText}>{props.lessons.length} bài học có thể chọn</Text>
        </View> : null}
      </Card>

      <Card style={styles.searchCard}>
        <TextInput
          accessibilityLabel="Tìm bài học"
          autoCapitalize="none"
          maxLength={100}
          onChangeText={setSearchQuery}
          onSubmitEditing={submitSearch}
          placeholder="Tìm bài học"
          returnKeyType="search"
          style={styles.searchInput}
          value={searchQuery}
        />
        <TextInput
          accessibilityLabel="Chủ đề tùy chọn"
          maxLength={120}
          onChangeText={setSearchTopic}
          onSubmitEditing={submitSearch}
          placeholder="Chủ đề (không bắt buộc)"
          returnKeyType="search"
          style={styles.searchInput}
          value={searchTopic}
        />
        <Pressable accessibilityRole="button" disabled={props.loading} onPress={submitSearch} style={styles.searchButton}>
          <Ionicons name="search" size={17} color="#FFFFFF" accessible={false} />
          <Text style={styles.searchButtonText}>Tìm kiếm</Text>
        </Pressable>
      </Card>

      {props.loading && props.lessons.length === 0 ? (
        <Card variant="creative" style={styles.stateCard}>
          <ActivityIndicator color={colors.purple} />
          <Text style={styles.stateText}>Đang tải bài học…</Text>
        </Card>
      ) : null}

      {!props.loading && !props.error && props.lessons.length === 0 ? (
        <Card variant="creative" style={styles.emptyCard}>
          <View style={styles.emptyIcon}>
            <Ionicons name="book-outline" size={30} color={colors.purple} accessible={false} />
          </View>
          <Text style={styles.emptyTitle}>Chưa có bài học phù hợp</Text>
          <Text style={styles.stateText}>Bài học công khai hoặc được chia sẻ sẽ xuất hiện tại đây.</Text>
        </Card>
      ) : null}

      {props.lessons.map((lesson) => {
        const selected = props.selectedId === lesson.lesson_id;
        const busy = props.loadingId === lesson.lesson_id;
        return (
          <Pressable
            key={lesson.lesson_id}
            accessibilityRole="button"
            accessibilityLabel={`${lesson.title}, ${lesson.topic || 'bài học'}, ${lesson.activity_count} hoạt động`}
            accessibilityState={{ selected, busy }}
            onPress={() => props.onSelect(lesson.lesson_id)}
            disabled={busy || props.loading}
            style={({ pressed }) => [styles.lessonCard, selected && styles.lessonCardSelected, pressed && styles.lessonCardPressed]}
          >
            <View style={[styles.lessonIcon, selected && styles.lessonIconSelected]}>
              {busy
                ? <ActivityIndicator size="small" color={colors.purple} />
                : <Ionicons name="book-outline" size={23} color={colors.purple} accessible={false} />}
            </View>
            <View style={styles.lessonCopy}>
              <Text style={styles.lessonTitle} numberOfLines={2}>{lesson.title}</Text>
              <Text style={styles.lessonTopic} numberOfLines={1}>{lesson.topic || 'Bài học'}</Text>
              <View style={styles.lessonMeta}>
                <View style={styles.accessPill}>
                  <Text style={styles.accessText}>{lesson.access_source === 'PUBLIC' ? 'Công khai' : 'Được chia sẻ'}</Text>
                </View>
                <Text style={styles.activityCount}>{lesson.activity_count} hoạt động</Text>
              </View>
            </View>
            <View style={styles.lessonEnd}>
              {selected ? (
                <View style={styles.selectedMark}>
                  <Ionicons name="checkmark" size={15} color="#FFFFFF" accessible={false} />
                </View>
              ) : (
                <Ionicons name="chevron-forward" size={20} color={colors.mutedPurple} accessible={false} />
              )}
              {selected ? <Text style={styles.selectedLabel}>Đang chọn</Text> : null}
            </View>
          </Pressable>
        );
      })}

      {props.hasMore ? (
        <Pressable accessibilityRole="button" accessibilityState={{ busy: props.loading, disabled: props.loading }} disabled={props.loading} onPress={props.onLoadMore} style={styles.loadMoreButton}>
          {props.loading ? <ActivityIndicator size="small" color={colors.purple} /> : null}
          <Text style={styles.loadMoreText}>{props.loading ? 'Đang tải…' : 'Xem thêm bài học'}</Text>
        </Pressable>
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
};

const styles = StyleSheet.create({
  introCard: {
    backgroundColor: '#FFFEFC',
    borderColor: colors.border,
    borderRadius: 22,
    borderWidth: 1.2,
    gap: 13,
    padding: 16,
    minWidth: 0,
  },
  introHeading: { alignItems: 'center', flexDirection: 'row', gap: 12, minWidth: 0 },
  introIcon: { alignItems: 'center', backgroundColor: colors.lavender, borderRadius: 16, height: 46, justifyContent: 'center', width: 46 },
  introCopy: { flex: 1, gap: 3, minWidth: 0 },
  introText: { color: palette.muted, fontSize: 13, lineHeight: 18, minWidth: 0, flexShrink: 1 },
  countPill: { alignSelf: 'flex-start', alignItems: 'center', backgroundColor: colors.softLavender, borderRadius: 999, flexDirection: 'row', gap: 6, minHeight: 30, paddingHorizontal: 11 },
  countText: { color: colors.deepPurple, fontSize: 11, fontWeight: '700', lineHeight: 15 },
  searchCard: { backgroundColor: '#FFFEFC', borderColor: colors.border, borderRadius: 20, borderWidth: 1, gap: 9, padding: 13 },
  searchInput: { minHeight: 46, borderColor: colors.border, borderRadius: 13, borderWidth: 1, color: colors.deepPurple, fontSize: 14, paddingHorizontal: 12 },
  searchButton: { minHeight: 44, alignItems: 'center', alignSelf: 'flex-start', backgroundColor: colors.purple, borderRadius: 13, flexDirection: 'row', gap: 7, justifyContent: 'center', paddingHorizontal: 14 },
  searchButtonText: { color: '#FFFFFF', fontSize: 13, fontWeight: '800' },
  loadMoreButton: { minHeight: 48, alignItems: 'center', backgroundColor: colors.lavender, borderRadius: 15, flexDirection: 'row', gap: 8, justifyContent: 'center' },
  loadMoreText: { color: colors.deepPurple, fontSize: 13, fontWeight: '800' },
  stateCard: { alignItems: 'center', backgroundColor: '#FFFEFC', borderColor: colors.border, borderRadius: 20, flexDirection: 'row', gap: 11, minWidth: 0 },
  stateText: { color: palette.muted, fontSize: 13, lineHeight: 19, flexShrink: 1, textAlign: 'center' },
  emptyCard: { alignItems: 'center', backgroundColor: '#FFFEFC', borderColor: colors.border, borderRadius: 22, gap: 9, padding: 22, minWidth: 0 },
  emptyIcon: { alignItems: 'center', backgroundColor: colors.lavender, borderRadius: 22, height: 62, justifyContent: 'center', marginBottom: 3, width: 62 },
  emptyTitle: { color: colors.deepPurple, fontSize: 17, fontWeight: '800', lineHeight: 23, textAlign: 'center' },
  lessonCard: {
    alignItems: 'center',
    backgroundColor: '#FFFEFC',
    borderColor: '#EEE5F6',
    borderRadius: 19,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 11,
    minHeight: 94,
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  lessonCardSelected: { backgroundColor: colors.softLavender, borderColor: '#CDB6EF' },
  lessonCardPressed: { opacity: 0.82 },
  lessonIcon: { alignItems: 'center', backgroundColor: colors.lavender, borderRadius: 14, height: 48, justifyContent: 'center', width: 48 },
  lessonIconSelected: { backgroundColor: '#E5D4FF' },
  lessonCopy: { flex: 1, gap: 3, minWidth: 0 },
  lessonTitle: { color: colors.deepPurple, fontSize: 15, fontWeight: '800', lineHeight: 20 },
  lessonTopic: { color: palette.muted, fontSize: 12, lineHeight: 16 },
  lessonMeta: { alignItems: 'center', flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 3 },
  accessPill: { backgroundColor: colors.lavender, borderRadius: 999, justifyContent: 'center', minHeight: 23, paddingHorizontal: 9, paddingVertical: 3 },
  accessText: { color: colors.deepPurple, fontSize: 10, fontWeight: '700', lineHeight: 14 },
  activityCount: { color: colors.mutedPurple, fontSize: 11, lineHeight: 15 },
  lessonEnd: { alignItems: 'center', gap: 4, justifyContent: 'center', minWidth: 42 },
  selectedMark: { alignItems: 'center', backgroundColor: colors.purple, borderRadius: 12, height: 25, justifyContent: 'center', width: 25 },
  selectedLabel: { color: colors.purple, fontSize: 9, fontWeight: '800', lineHeight: 12, textAlign: 'center' },
});
