import React, { useMemo, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Circle, Defs, Ellipse, LinearGradient as SvgGradient, Path, Rect, Stop } from 'react-native-svg';
import type { ParentCapabilityState } from '../../application/ports/ParentCapabilityPorts';
import type { ParentNotification } from '../../domain/types';
import { ScreenScrollView } from '../components/ui';

type Props = {
  capability: ParentCapabilityState;
  items: ParentNotification[];
  loading: boolean;
  error: string;
  hasMore: boolean;
  onLoad: () => void;
  onLoadMore: () => void;
  onMarkRead: (notificationId: string) => void;
  onBack: () => void;
};

type NotificationFilter = 'all' | 'system' | 'lessons' | 'stories' | 'other';
type NotificationGroup = { key: string; label: string; items: ParentNotification[] };

const filters: { id: NotificationFilter; label: string }[] = [
  { id: 'all', label: 'Tất cả' },
  { id: 'system', label: 'Hệ thống' },
  { id: 'lessons', label: 'Bài học' },
  { id: 'stories', label: 'Câu chuyện' },
  { id: 'other', label: 'Khác' },
];

export function NotificationsScreen(props: Props): React.JSX.Element {
  const [activeFilter, setActiveFilter] = useState<NotificationFilter>('all');
  const notifications = useMemo(() => {
    const ordered = [...props.items].sort((a, b) => dateValue(b.created_at) - dateValue(a.created_at));
    return activeFilter === 'all' ? ordered : ordered.filter((item) => categoryFor(item) === activeFilter);
  }, [activeFilter, props.items]);
  const groups = useMemo(() => groupByDay(notifications), [notifications]);

  return (
    <LinearGradient colors={['#FFFAF6', '#FCF8FF', '#FFFAF6']} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.screen}>
      <SafeAreaView edges={['top', 'right', 'left']} style={styles.safeArea}>
        <View style={styles.header}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Quay lại"
            onPress={props.onBack}
            style={({ pressed }) => [styles.backButton, pressed && styles.pressed]}
          >
            <Ionicons name="arrow-back" size={21} color="#4E2677" accessible={false} />
          </Pressable>
          <View style={styles.headerCopy}>
            <Text accessibilityRole="header" style={styles.heading}>Thông báo</Text>
            <Text style={styles.subtitle}>Thông tin dành riêng cho tài khoản phụ huynh.</Text>
          </View>
        </View>

        <ScreenScrollView
          style={styles.scroll}
          contentContainerStyle={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {props.capability.state === 'unavailable' ? (
            <View style={styles.centeredState}>
              <UnavailableInbox reason={props.capability.reason} />
            </View>
          ) : (
            <>
              <FilterBar activeFilter={activeFilter} onSelect={setActiveFilter} />
              {props.error ? <ErrorState message={props.error} onRetry={props.onLoad} loading={props.loading} /> : null}
              {props.loading && !props.items.length ? <LoadingState /> : null}
              {!props.loading && !props.error && !props.items.length ? <EmptyInbox /> : null}
              {notifications.length ? (
                <View style={styles.groups}>
                  {groups.map((group) => (
                    <View key={group.key} style={styles.group}>
                      <View style={styles.groupHeading}>
                        <Text style={styles.groupTitle}>{group.label}</Text>
                        <Text style={styles.groupCount}>{group.items.length} tin</Text>
                      </View>
                      {group.items.map((item) => (
                        <NotificationCard key={item.notification_id} item={item} loading={props.loading} onMarkRead={props.onMarkRead} />
                      ))}
                    </View>
                  ))}
                </View>
              ) : null}
              {props.items.length > 0 && !notifications.length ? (
                <View style={styles.filteredEmpty}>
                  <View style={styles.filteredEmptyIcon}>
                    <Ionicons name="notifications-off-outline" size={22} color="#7435D5" accessible={false} />
                  </View>
                  <Text style={styles.filteredEmptyText}>Chưa có thông báo trong mục này.</Text>
                </View>
              ) : null}
              {props.loading && props.items.length ? <LoadingFooter /> : null}
              {props.hasMore && notifications.length ? <LoadMoreButton loading={props.loading} onPress={props.onLoadMore} /> : null}
            </>
          )}
        </ScreenScrollView>
      </SafeAreaView>
    </LinearGradient>
  );
}

function FilterBar({ activeFilter, onSelect }: { activeFilter: NotificationFilter; onSelect: (filter: NotificationFilter) => void }): React.JSX.Element {
  return (
    <ScreenScrollView
      horizontal
      accessibilityRole="tablist"
      style={styles.filterScroll}
      contentContainerStyle={styles.filterRow}
      showsHorizontalScrollIndicator={false}
    >
      {filters.map((filter) => {
        const selected = activeFilter === filter.id;
        return (
          <Pressable
            key={filter.id}
            accessibilityRole="tab"
            accessibilityLabel={filter.label}
            accessibilityState={{ selected }}
            onPress={() => onSelect(filter.id)}
            style={({ pressed }) => [styles.filterChip, selected && styles.filterChipSelected, pressed && styles.filterChipPressed]}
          >
            <Text style={[styles.filterText, selected && styles.filterTextSelected]}>{filter.label}</Text>
          </Pressable>
        );
      })}
    </ScreenScrollView>
  );
}

function UnavailableInbox({ reason }: { reason: Extract<ParentCapabilityState, { state: 'unavailable' }>['reason'] }): React.JSX.Element {
  const message = reason === 'route-not-in-be-handoff'
    ? 'Dịch vụ thông báo chưa được kết nối trong phiên bản hiện tại.'
    : 'Dịch vụ thông báo chưa được cấu hình cho tài khoản này.';

  return (
    <View style={styles.unavailableCard}>
      <LinearGradient colors={['#F5EAFF', '#EEE4FF']} style={styles.unavailableIcon}>
        <Ionicons name="lock-closed" size={25} color="#7435D5" accessible={false} />
      </LinearGradient>
      <Text style={styles.stateTitle}>Hộp thư chưa khả dụng</Text>
      <Text style={styles.stateCopy}>{message}</Text>
      <View style={styles.unavailableHint}>
        <Ionicons name="information-circle-outline" size={18} color="#684193" accessible={false} />
        <Text style={styles.unavailableHintText}>Danh sách chưa tải không cho biết bạn có hay không có thông báo mới.</Text>
      </View>
    </View>
  );
}

function EmptyInbox(): React.JSX.Element {
  return (
    <View style={styles.emptyState}>
      <EmptyInboxIllustration />
      <Text style={styles.stateTitle}>Chưa có thông báo nào</Text>
      <Text style={styles.stateCopy}>Các thông báo mới sẽ xuất hiện tại đây.</Text>
    </View>
  );
}

function EmptyInboxIllustration(): React.JSX.Element {
  return (
    <View style={styles.illustrationFrame}>
      <Svg width="100%" height="100%" viewBox="0 0 280 190" preserveAspectRatio="xMidYMid meet" accessible={false}>
        <Defs>
          <SvgGradient id="mailboxBody" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor="#A45AF0" />
            <Stop offset="0.55" stopColor="#8138D6" />
            <Stop offset="1" stopColor="#6128B1" />
          </SvgGradient>
          <SvgGradient id="mailboxPost" x1="0" y1="0" x2="1" y2="0">
            <Stop offset="0" stopColor="#C9A4F7" />
            <Stop offset="0.5" stopColor="#A975E6" />
            <Stop offset="1" stopColor="#8750CC" />
          </SvgGradient>
          <SvgGradient id="birdBody" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor="#8BDCF6" />
            <Stop offset="1" stopColor="#40B9E3" />
          </SvgGradient>
          <SvgGradient id="letter" x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor="#FFF8D8" />
            <Stop offset="1" stopColor="#FFE69A" />
          </SvgGradient>
        </Defs>
        <Circle cx="139" cy="93" r="85" fill="#F4EBFF" />
        <Path d="M20 132c0-8 7-14 15-14 3-11 19-13 25-3 10-2 17 5 17 13 0 7-6 12-14 12H34c-8 0-14-3-14-8Z" fill="#FFF" opacity="0.9" />
        <Path d="M209 120c0-7 6-12 13-12 3-9 17-10 22-2 8-2 14 4 14 11 0 6-5 10-12 10h-25c-7 0-12-3-12-7Z" fill="#FFF" opacity="0.8" />
        <Ellipse cx="143" cy="169" rx="74" ry="10" fill="#DCCAF2" opacity="0.65" />
        <Rect x="130" y="111" width="24" height="58" rx="10" fill="url(#mailboxPost)" />
        <Rect x="117" y="151" width="50" height="12" rx="6" fill="#9C70D1" />
        <Path d="M78 72c0-17 13-30 30-30h69c17 0 30 13 30 30v55c0 13-10 23-23 23h-83c-13 0-23-10-23-23V72Z" fill="url(#mailboxBody)" />
        <Path d="M180 43h-69c-17 0-30 13-30 30v8c0-13 12-23 27-23h74c12 0 22 9 24 21v-7c0-16-11-29-26-29Z" fill="#B981F4" opacity="0.6" />
        <Path d="M186 73h-70c-9 0-16 7-16 16v31c0 9 7 16 16 16h70c9 0 16-7 16-16V89c0-9-7-16-16-16Z" fill="#FDF9FF" />
        <Rect x="122" y="82" width="47" height="6" rx="3" fill="#D9C7EF" />
        <Path d="m108 99 43 29 43-29" fill="none" stroke="#D8C5EF" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
        <Rect x="99" y="103" width="20" height="7" rx="3.5" fill="#FFCB4D" />
        <Circle cx="216" cy="61" r="20" fill="url(#birdBody)" />
        <Path d="M204 59c-12-11-22-7-25 1 8 7 15 9 24 6Z" fill="#9D70E5" />
        <Path d="M231 58 246 63 231 70Z" fill="#FFB844" />
        <Circle cx="222" cy="55" r="2.8" fill="#34234B" />
        <Path d="M211 74c5 5 11 5 16 0" fill="none" stroke="#2B96C0" strokeWidth="2.5" strokeLinecap="round" />
        <Path d="M198 87c-8 6-11 13-9 20m20-1 5 8m10-8-1 9" fill="none" stroke="#7E51C4" strokeWidth="3" strokeLinecap="round" />
        <Path d="m178 64 15-12 14 14-15 12Z" fill="url(#letter)" stroke="#E8C967" strokeWidth="2" />
        <Path d="m179 65 12 8 14-8" fill="none" stroke="#E8C967" strokeWidth="1.8" strokeLinejoin="round" />
        <Path d="M46 155c2-8 8-11 14-10 4-7 15-5 16 3 6 3 5 11-2 14H54c-6 0-9-3-8-7Z" fill="#A9D9B2" />
        <Path d="M63 155v-13m0 7-6-5m6 8 6-6" fill="none" stroke="#5A9F6B" strokeWidth="2.4" strokeLinecap="round" />
        <Circle cx="64" cy="137" r="4" fill="#FF8D9A" />
        <Circle cx="59" cy="140" r="3.3" fill="#FFB84D" />
        <Circle cx="69" cy="141" r="3.3" fill="#C794F3" />
        <Circle cx="219" cy="143" r="3" fill="#FFC84A" />
        <Path d="m219 137 1-5m4 8 4-3m-11 0-3-4" fill="none" stroke="#EBAE30" strokeWidth="2" strokeLinecap="round" />
        <Path d="m92 31 3-7m12 9 5-5m94 21 5-5" fill="none" stroke="#F7B83F" strokeWidth="3" strokeLinecap="round" />
        <Circle cx="89" cy="43" r="3" fill="#E4C7FF" />
      </Svg>
    </View>
  );
}

function NotificationCard({ item, loading, onMarkRead }: { item: ParentNotification; loading: boolean; onMarkRead: (id: string) => void }): React.JSX.Element {
  const meta = metadataFor(item);
  const unread = !item.read_at;

  return (
    <View style={[styles.notificationCard, unread ? styles.unreadCard : styles.readCard]}>
      <View style={[styles.notificationIcon, { backgroundColor: meta.iconBackground }]}>
        <Ionicons name={meta.icon} size={21} color={meta.iconColor} accessible={false} />
      </View>
      <View style={styles.notificationCopy}>
        <View style={styles.notificationMeta}>
          <View style={[styles.categoryTag, { backgroundColor: meta.tagBackground }]}>
            <Text style={[styles.categoryText, { color: meta.iconColor }]}>{meta.category}</Text>
          </View>
          <View style={styles.timeAndUnread}>
            <Text style={styles.notificationTime}>{formatTime(item.created_at)}</Text>
            {unread ? <View accessibilityLabel="Chưa đọc" style={styles.unreadDot} /> : null}
          </View>
        </View>
        <Text style={styles.notificationTitle}>{item.title}</Text>
        {unread ? (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Đánh dấu đã đọc: ${item.title}`}
            accessibilityState={{ disabled: loading }}
            disabled={loading}
            onPress={() => onMarkRead(item.notification_id)}
            style={({ pressed }) => [styles.markReadButton, pressed && styles.markReadPressed]}
          >
            <Ionicons name="checkmark-circle-outline" size={16} color="#7435D5" accessible={false} />
            <Text style={styles.markReadText}>Đánh dấu đã đọc</Text>
          </Pressable>
        ) : null}
      </View>
    </View>
  );
}

function ErrorState({ message, onRetry, loading }: { message: string; onRetry: () => void; loading: boolean }): React.JSX.Element {
  return (
    <View accessibilityRole="alert" style={styles.errorCard}>
      <View style={styles.errorIcon}><Ionicons name="alert-circle" size={19} color="#A83D63" accessible={false} /></View>
      <View style={styles.errorCopy}>
        <Text style={styles.errorTitle}>Chưa tải được thông báo</Text>
        <Text style={styles.errorText}>{message}</Text>
        <Pressable accessibilityRole="button" accessibilityLabel="Thử tải lại thông báo" disabled={loading} onPress={onRetry} style={styles.retryButton}>
          {loading ? <ActivityIndicator size="small" color="#7435D5" /> : <Ionicons name="refresh" size={16} color="#7435D5" accessible={false} />}
          <Text style={styles.retryText}>Thử tải lại</Text>
        </Pressable>
      </View>
    </View>
  );
}

function LoadingState(): React.JSX.Element {
  return (
    <View accessibilityRole="progressbar" style={styles.loadingCard}>
      <ActivityIndicator size="small" color="#7435D5" />
      <Text style={styles.loadingText}>Đang tải hộp thư…</Text>
    </View>
  );
}

function LoadingFooter(): React.JSX.Element {
  return <View style={styles.loadingFooter}><ActivityIndicator size="small" color="#7435D5" /><Text style={styles.loadingText}>Đang cập nhật…</Text></View>;
}

function LoadMoreButton({ loading, onPress }: { loading: boolean; onPress: () => void }): React.JSX.Element {
  return (
    <Pressable accessibilityRole="button" accessibilityLabel="Xem thêm thông báo" accessibilityState={{ busy: loading, disabled: loading }} disabled={loading} onPress={onPress} style={({ pressed }) => [styles.loadMoreButton, pressed && styles.loadMorePressed]}>
      {loading ? <ActivityIndicator size="small" color="#7435D5" /> : null}
      <Text style={styles.loadMoreText}>{loading ? 'Đang tải…' : 'Xem thêm thông báo'}</Text>
      {!loading ? <Ionicons name="chevron-down" size={17} color="#7435D5" accessible={false} /> : null}
    </Pressable>
  );
}

function categoryFor(item: ParentNotification): NotificationFilter {
  switch (item.kind) {
    case 'LESSON_FEEDBACK':
    case 'LESSON_REPLY':
      return 'lessons';
    case 'PROFILE_SHARE_INVITATION':
    case 'PROFILE_SHARE_ACCEPTED':
      return 'other';
  }
}

function metadataFor(item: ParentNotification): { category: string; icon: React.ComponentProps<typeof Ionicons>['name']; iconColor: string; iconBackground: string; tagBackground: string } {
  switch (item.kind) {
    case 'LESSON_FEEDBACK':
      return { category: 'Bài học', icon: 'school-outline', iconColor: '#7041B7', iconBackground: '#EEE4FF', tagBackground: '#F2EAFF' };
    case 'LESSON_REPLY':
      return { category: 'Bài học', icon: 'chatbubble-ellipses-outline', iconColor: '#7041B7', iconBackground: '#EEE4FF', tagBackground: '#F2EAFF' };
    case 'PROFILE_SHARE_INVITATION':
      return { category: 'Khác', icon: 'person-add-outline', iconColor: '#278A84', iconBackground: '#DDF5EF', tagBackground: '#E8F8F3' };
    case 'PROFILE_SHARE_ACCEPTED':
      return { category: 'Khác', icon: 'people-outline', iconColor: '#278A84', iconBackground: '#DDF5EF', tagBackground: '#E8F8F3' };
  }
}

function groupByDay(items: ParentNotification[]): NotificationGroup[] {
  const byDay = new Map<string, NotificationGroup>();
  items.forEach((item) => {
    const date = new Date(item.created_at);
    const key = Number.isNaN(date.getTime()) ? 'unknown' : `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
    const group = byDay.get(key) ?? { key, label: dateLabel(date), items: [] };
    group.items.push(item);
    byDay.set(key, group);
  });
  return [...byDay.values()];
}

function dateLabel(date: Date): string {
  if (Number.isNaN(date.getTime())) return 'Ngày khác';
  const today = new Date();
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const dateStart = new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
  const daysAgo = Math.round((todayStart - dateStart) / 86_400_000);
  if (daysAgo === 0) return 'Hôm nay';
  if (daysAgo === 1) return 'Hôm qua';
  return date.toLocaleDateString('vi-VN', { day: 'numeric', month: 'long' });
}

function dateValue(value: string): number {
  const timestamp = new Date(value).getTime();
  return Number.isNaN(timestamp) ? 0 : timestamp;
}

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '' : date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  safeArea: { flex: 1 },
  header: { minHeight: 82, paddingHorizontal: 18, paddingTop: 7, paddingBottom: 12, flexDirection: 'row', alignItems: 'center', gap: 13 },
  backButton: { width: 48, height: 48, borderRadius: 24, borderWidth: 1.3, borderColor: '#E4D2F4', backgroundColor: '#F7F0FF', alignItems: 'center', justifyContent: 'center' },
  pressed: { opacity: 0.82 },
  headerCopy: { flex: 1, minWidth: 0, gap: 3 },
  heading: { color: '#281451', fontSize: 22, lineHeight: 28, fontWeight: '800' },
  subtitle: { color: '#74677D', fontSize: 12, lineHeight: 17, flexShrink: 1 },
  scroll: { flex: 1, minHeight: 0 },
  content: { width: '100%', maxWidth: 560, alignSelf: 'center', paddingHorizontal: 16, paddingTop: 7, paddingBottom: 22, gap: 16, flexGrow: 1 },
  centeredState: { flexGrow: 1, minHeight: 280, justifyContent: 'center', paddingVertical: 16 },
  filterScroll: { flexGrow: 0, marginHorizontal: -16 },
  filterRow: { paddingHorizontal: 16, gap: 8, alignItems: 'center' },
  filterChip: { minHeight: 44, paddingHorizontal: 15, borderRadius: 22, alignItems: 'center', justifyContent: 'center', backgroundColor: '#F1E7FF', borderWidth: 1, borderColor: '#E9DDF5' },
  filterChipSelected: { backgroundColor: '#7435D5', borderColor: '#7435D5' },
  filterChipPressed: { opacity: 0.82 },
  filterText: { color: '#542A82', fontSize: 13, lineHeight: 18, fontWeight: '700' },
  filterTextSelected: { color: '#FFFFFF', fontWeight: '800' },
  groups: { gap: 17 },
  group: { gap: 9 },
  groupHeading: { minHeight: 25, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 2 },
  groupTitle: { color: '#382052', fontSize: 16, lineHeight: 21, fontWeight: '800' },
  groupCount: { color: '#8A7D95', fontSize: 11, lineHeight: 16, fontWeight: '600' },
  notificationCard: { flexDirection: 'row', alignItems: 'flex-start', gap: 11, padding: 13, borderRadius: 20, borderWidth: 1, shadowColor: '#4A2B68', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.055, shadowRadius: 9, elevation: 1 },
  readCard: { backgroundColor: '#FFFEFF', borderColor: '#F0E8F5' },
  unreadCard: { backgroundColor: '#F7F1FF', borderColor: '#E8D9F8' },
  notificationIcon: { width: 42, height: 42, borderRadius: 15, alignItems: 'center', justifyContent: 'center', marginTop: 1 },
  notificationCopy: { flex: 1, minWidth: 0 },
  notificationMeta: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8, minWidth: 0 },
  categoryTag: { minHeight: 22, paddingHorizontal: 8, borderRadius: 11, alignItems: 'center', justifyContent: 'center' },
  categoryText: { fontSize: 10, lineHeight: 14, fontWeight: '800' },
  timeAndUnread: { flexDirection: 'row', alignItems: 'center', gap: 7, flexShrink: 0 },
  notificationTime: { color: '#8A7D95', fontSize: 11, lineHeight: 15, fontWeight: '600' },
  unreadDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#8B3FE8' },
  notificationTitle: { marginTop: 6, color: '#352047', fontSize: 14, lineHeight: 20, fontWeight: '700', flexShrink: 1 },
  markReadButton: { alignSelf: 'flex-start', flexDirection: 'row', alignItems: 'center', gap: 6, minHeight: 44, marginTop: 4, paddingHorizontal: 8, borderRadius: 12 },
  markReadPressed: { backgroundColor: '#EEE3FC' },
  markReadText: { color: '#7435D5', fontSize: 12, lineHeight: 16, fontWeight: '700' },
  unavailableCard: { width: '100%', alignItems: 'center', paddingHorizontal: 20, paddingTop: 26, paddingBottom: 22, borderRadius: 24, backgroundColor: '#FFFEFF', borderWidth: 1, borderColor: '#EEE5F4', shadowColor: '#4A2B68', shadowOffset: { width: 0, height: 5 }, shadowOpacity: 0.06, shadowRadius: 13, elevation: 2 },
  unavailableIcon: { width: 58, height: 58, borderRadius: 20, alignItems: 'center', justifyContent: 'center', marginBottom: 14 },
  stateTitle: { color: '#281451', fontSize: 19, lineHeight: 25, fontWeight: '800', textAlign: 'center' },
  stateCopy: { maxWidth: 330, marginTop: 6, color: '#74677D', fontSize: 13, lineHeight: 19, textAlign: 'center', flexShrink: 1 },
  unavailableHint: { width: '100%', flexDirection: 'row', alignItems: 'flex-start', gap: 8, marginTop: 18, padding: 12, borderRadius: 15, backgroundColor: '#F4EEFC' },
  unavailableHintText: { flex: 1, color: '#5C4374', fontSize: 12, lineHeight: 17, flexShrink: 1 },
  emptyState: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 14, paddingTop: 6, paddingBottom: 18 },
  illustrationFrame: { width: '100%', maxWidth: 280, height: 190, marginBottom: 7 },
  filteredEmpty: { minHeight: 132, alignItems: 'center', justifyContent: 'center', gap: 10, padding: 18, borderRadius: 20, backgroundColor: '#FFFEFF', borderWidth: 1, borderColor: '#F0E8F5' },
  filteredEmptyIcon: { width: 42, height: 42, borderRadius: 15, backgroundColor: '#F1E7FF', alignItems: 'center', justifyContent: 'center' },
  filteredEmptyText: { color: '#74677D', fontSize: 13, lineHeight: 19, textAlign: 'center' },
  errorCard: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, padding: 13, borderRadius: 18, backgroundColor: '#FFF1F5', borderWidth: 1, borderColor: '#F1D6E0' },
  errorIcon: { width: 30, height: 30, borderRadius: 10, backgroundColor: '#FFE3EC', alignItems: 'center', justifyContent: 'center' },
  errorCopy: { flex: 1, minWidth: 0, gap: 3 },
  errorTitle: { color: '#672A45', fontSize: 13, lineHeight: 18, fontWeight: '800' },
  errorText: { color: '#704B5B', fontSize: 12, lineHeight: 17, flexShrink: 1 },
  retryButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', alignSelf: 'flex-start', gap: 6, paddingHorizontal: 8 },
  retryText: { color: '#7435D5', fontSize: 12, lineHeight: 16, fontWeight: '800' },
  loadingCard: { minHeight: 88, flexDirection: 'row', justifyContent: 'center', alignItems: 'center', gap: 10, borderRadius: 20, backgroundColor: '#FFFEFF', borderWidth: 1, borderColor: '#F0E8F5' },
  loadingFooter: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9 },
  loadingText: { color: '#74677D', fontSize: 13, lineHeight: 18 },
  loadMoreButton: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, borderRadius: 16, backgroundColor: '#F1E7FF' },
  loadMorePressed: { opacity: 0.82 },
  loadMoreText: { color: '#5B2B89', fontSize: 13, lineHeight: 18, fontWeight: '800' },
});
