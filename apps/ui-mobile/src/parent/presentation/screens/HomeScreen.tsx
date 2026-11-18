import React, { useMemo, useState } from 'react';
import {
  Image,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
  useWindowDimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { ParentProfileViewV1, ParentStoryRunV1 } from '../../domain/types';
import { Notice, ScreenScrollView } from '../components/ui';

type Props = {
  profiles: ParentProfileViewV1[];
  selectedProfile: ParentProfileViewV1 | null;
  activeRun: ParentStoryRunV1 | null;
  error: string;
  onStart: () => void;
  onPickFromLibrary?: () => void;
  onManageProfiles: () => void;
  onSelectProfile?: (profile: ParentProfileViewV1) => void;
  onOpenNotifications?: () => void;
  onOpenLessons: () => void;
  onOpenDrawingGuide?: () => void;
  onResumeRun: () => void;
};

const colors = {
  background: '#FFFAF6',
  surface: '#FFFFFF',
  primary: '#7435D5',
  primaryDeep: '#54239A',
  lavender: '#EDE3FF',
  lavenderSoft: '#F6F0FF',
  coral: '#FF745F',
  ink: '#281451',
  muted: '#70667C',
  line: '#E7DDF0',
  blue: '#DDF1FF',
  blueDeep: '#315E87',
};

const terminalRunStates = new Set(['COMPLETED', 'FAILED', 'ABANDONED', 'DELETE_PENDING', 'DELETED']);
const roundedFont = Platform.OS === 'android' ? 'sans-serif-rounded' : undefined;

export function HomeScreen({
  profiles,
  selectedProfile,
  activeRun,
  error,
  onStart,
  onPickFromLibrary = onStart,
  onManageProfiles,
  onSelectProfile,
  onOpenNotifications = () => undefined,
  onOpenLessons,
  onOpenDrawingGuide = onStart,
  onResumeRun,
}: Props): React.JSX.Element {
  const { width } = useWindowDimensions();
  const compact = width < 420;
  const [profilePickerVisible, setProfilePickerVisible] = useState(false);
  const visibleRun = activeRun && !terminalRunStates.has(activeRun.run_state) ? activeRun : null;
  const activeRunProfile = visibleRun
    ? profiles.find((profile) => profile.profile_id === visibleRun.parent_profile_id) ?? null
    : null;
  const selectedLabel = selectedProfile?.display_name?.trim() || '';

  return (
    <SafeAreaView edges={['top', 'right', 'left']} style={styles.safeRoot}>
      <View style={styles.root}>
        <View pointerEvents="none" style={styles.backgroundGlowTop} />
        <ScreenScrollView
          style={styles.scroll}
          contentContainerStyle={[styles.content, compact && styles.contentCompact]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <View style={styles.brandRow}>
              <Image
                source={require('../../../../assets/splash/logo.png')}
                resizeMode="contain"
                style={styles.logo}
                accessibilityLabel="Sketch2Life"
              />
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Mở thông báo"
                hitSlop={8}
                onPress={onOpenNotifications}
                style={({ pressed }) => [styles.notificationButton, pressed && styles.pressed]}
              >
                <Ionicons name="notifications-outline" size={22} color={colors.ink} accessible={false} />
              </Pressable>
            </View>

            <View style={[styles.welcomePanel, compact && styles.welcomePanelCompact]}>
              <View style={styles.greetingBlock}>
                <Text accessibilityRole="header" style={[styles.greeting, compact && styles.greetingCompact]}>
                  Chào mừng trở lại!
                </Text>
                <Text style={styles.greetingSubtitle}>Cùng bé biến nét vẽ thành những câu chuyện kỳ diệu.</Text>
              </View>
              <WelcomeArtwork />
            </View>

            <Pressable
              accessibilityRole="button"
              accessibilityLabel={selectedLabel ? `Hồ sơ bé ${selectedLabel}. Chọn hồ sơ khác` : 'Chọn hồ sơ của bé'}
              accessibilityHint="Mở danh sách hồ sơ trẻ trong gia đình"
              onPress={() => setProfilePickerVisible(true)}
              style={({ pressed }) => [styles.profileSelector, pressed && styles.pressed]}
            >
              <ProfileAvatar name={selectedLabel} size={40} />
              <View style={styles.profileSelectorCopy}>
                <Text style={styles.profileOverline}>ĐANG CÙNG BÉ</Text>
                <Text numberOfLines={1} style={styles.profileName}>{selectedLabel || 'Chọn hồ sơ của bé'}</Text>
              </View>
              <Ionicons name="chevron-down" size={18} color={colors.primary} accessible={false} />
            </Pressable>
          </View>

          {error ? <Notice text={error} tone="warning" /> : null}

          <HeroBanner
            compact={compact}
            onStart={onStart}
            onPickFromLibrary={onPickFromLibrary}
          />

          {visibleRun ? (
            <ContinueCard
              run={visibleRun}
              childName={activeRunProfile?.display_name ?? ''}
              onPress={onResumeRun}
            />
          ) : null}

          <View style={styles.exploreSection}>
            <View style={styles.sectionHeading}>
              <View style={styles.sectionHeadingCopy}>
                <Text accessibilityRole="header" style={styles.sectionTitle}>Khám phá cùng bé</Text>
                <Text style={styles.sectionSubtitle}>Những ý tưởng nhỏ cho giờ sáng tạo hôm nay.</Text>
              </View>
              <View style={styles.sectionSpark}>
                <Ionicons name="sparkles" size={17} color={colors.primary} accessible={false} />
              </View>
            </View>
            <View style={styles.exploreGrid}>
              <ExploreCard
                kind="lessons"
                title="Bài học"
                subtitle="Khám phá nội dung được chia sẻ cho gia đình"
                onPress={onOpenLessons}
              />
              <ExploreCard
                kind="drawing"
                title="Hướng dẫn vẽ"
                subtitle="Cùng bé bắt đầu từ những nét đơn giản"
                onPress={onOpenDrawingGuide}
              />
            </View>
          </View>
        </ScreenScrollView>

        <ProfilePickerModal
          visible={profilePickerVisible}
          profiles={profiles}
          selectedProfileId={selectedProfile?.profile_id ?? null}
          onClose={() => setProfilePickerVisible(false)}
          onSelect={(profile) => {
            onSelectProfile?.(profile);
            setProfilePickerVisible(false);
          }}
          onManage={() => {
            setProfilePickerVisible(false);
            onManageProfiles();
          }}
        />
      </View>
    </SafeAreaView>
  );
}

function WelcomeArtwork(): React.JSX.Element {
  return (
    <View style={styles.welcomeArt} accessible={false}>
      <View style={styles.welcomeArtHalo} />
      <View style={styles.welcomePaper}>
        <View style={styles.welcomeSun} />
        <View style={styles.welcomeCloud} />
        <View style={styles.welcomeHill} />
        <View style={styles.welcomeStem} />
        <View style={styles.welcomeLeaf} />
      </View>
      <View style={styles.welcomePencil}>
        <View style={styles.welcomePencilBand} />
      </View>
      <View style={styles.welcomePencilTip} />
      <View style={styles.welcomeSpark} />
      <View style={styles.welcomeDot} />
    </View>
  );
}

function HeroBanner({
  compact,
  onStart,
  onPickFromLibrary,
}: {
  compact: boolean;
  onStart: () => void;
  onPickFromLibrary: () => void;
}): React.JSX.Element {
  return (
    <View style={styles.heroCard}>
      <View style={styles.heroArtworkStage}>
        <LinearGradient
          colors={['#D8ECFF', '#E9E3FF', '#F6E8FF']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={StyleSheet.absoluteFill}
        />
        <View style={styles.heroSunGlow} />
        <View style={styles.heroOrb} />
        <Image
          source={require('../../../../assets/home/home-story-hero.png')}
          resizeMode="cover"
          style={styles.heroIllustration}
          accessible={false}
        />
      </View>

      <View style={[styles.heroCopy, compact && styles.heroCopyCompact]}>
        <Text accessibilityRole="header" style={styles.heroTitle}>Từ nét vẽ đến câu chuyện</Text>
        <Text style={styles.heroSubtitle}>Chụp tranh của bé để tạo video riêng.</Text>
        <View style={[styles.heroActions, compact && styles.heroActionsCompact]}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Chụp tranh ngay"
            onPress={onStart}
            style={({ pressed }) => [styles.primaryAction, compact && styles.heroActionCompact, pressed && styles.actionPressed]}
          >
            <Ionicons name="camera-outline" size={19} color="#FFFFFF" accessible={false} />
            <Text numberOfLines={1} style={styles.primaryActionText}>Chụp tranh ngay</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Chọn ảnh từ thư viện"
            onPress={onPickFromLibrary}
            style={({ pressed }) => [styles.secondaryAction, compact && styles.heroActionCompact, pressed && styles.actionPressed]}
          >
            <Ionicons name="images-outline" size={18} color={colors.primary} accessible={false} />
            <Text numberOfLines={1} style={styles.secondaryActionText}>Chọn ảnh từ thư viện</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

function ContinueCard({
  run,
  childName,
  onPress,
}: {
  run: ParentStoryRunV1;
  childName: string;
  onPress: () => void;
}): React.JSX.Element {
  const state = runProgressState(run);
  const title = storyTitle(run);

  return (
    <View style={styles.continueSection}>
      <Text style={styles.continueSectionTitle}>Tiếp tục sáng tạo</Text>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel={`Tiếp tục ${title}${childName ? ` của ${childName}` : ''}. ${state.label}`}
        onPress={onPress}
        style={({ pressed }) => [styles.continueCard, pressed && styles.pressed]}
      >
        <View style={styles.continueThumb}>
          <Image
            source={require('../../../../assets/home/home-story-hero.png')}
            resizeMode="contain"
            style={styles.continueThumbImage}
            accessible={false}
          />
        </View>
        <View style={styles.continueCopy}>
          <Text numberOfLines={1} style={styles.continueTitle}>{title}</Text>
          <Text numberOfLines={1} style={styles.continueMeta}>{childName ? `Hồ sơ ${childName}` : 'Buổi sáng tạo đang mở'}</Text>
          <View style={styles.runStateRow}>
            <View style={styles.runStateDot} />
            <Text numberOfLines={2} style={styles.runStateText}>{state.label}</Text>
          </View>
          {state.step !== null ? <RunProgress currentStep={state.step} /> : null}
        </View>
        <View style={styles.continueButton}>
          <Text style={styles.continueButtonText}>Tiếp tục</Text>
          <Ionicons name="arrow-forward" size={15} color={colors.primary} accessible={false} />
        </View>
      </Pressable>
    </View>
  );
}

function RunProgress({ currentStep }: { currentStep: number }): React.JSX.Element {
  const labels = ['Tranh', 'Chủ thể', 'Kịch bản', 'Video'];
  return (
    <View accessibilityLabel={`Tiến trình: ${labels[currentStep]}`} style={styles.progressTrack}>
      {labels.map((label, index) => (
        <View key={label} style={styles.progressUnit}>
          <View style={[styles.progressSegment, index <= currentStep && styles.progressSegmentActive]} />
          <Text numberOfLines={1} style={[styles.progressLabel, index === currentStep && styles.progressLabelActive]}>{label}</Text>
        </View>
      ))}
    </View>
  );
}

function ExploreCard({
  kind,
  title,
  subtitle,
  onPress,
}: {
  kind: 'lessons' | 'drawing';
  title: string;
  subtitle: string;
  onPress: () => void;
}): React.JSX.Element {
  const isLessons = kind === 'lessons';
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${title}. ${subtitle}`}
      onPress={onPress}
      style={({ pressed }) => [styles.exploreCard, pressed && styles.pressed]}
    >
      <View style={[styles.exploreArtwork, isLessons ? styles.lessonArtwork : styles.drawingArtwork]}>
        {isLessons ? <LessonArtwork /> : <DrawingArtwork />}
        <View style={[styles.artworkBadge, isLessons ? styles.lessonBadge : styles.drawingBadge]}>
          <Ionicons name={isLessons ? 'book-outline' : 'brush-outline'} size={14} color={colors.primary} accessible={false} />
        </View>
      </View>
      <View style={styles.exploreCopy}>
        <Text numberOfLines={1} style={styles.exploreTitle}>{title}</Text>
        <Text numberOfLines={2} style={styles.exploreSubtitle}>{subtitle}</Text>
        <View style={styles.exploreLinkRow}>
          <Text style={styles.exploreLink}>{isLessons ? 'Mở thư viện' : 'Bắt đầu vẽ'}</Text>
          <Ionicons name="arrow-forward" size={15} color={colors.primary} accessible={false} />
        </View>
      </View>
    </Pressable>
  );
}

function LessonArtwork(): React.JSX.Element {
  return (
    <View style={styles.lessonArtCanvas} accessible={false}>
      <View style={styles.bookShadow} />
      <View style={styles.bookLeftPage}>
        <View style={styles.bookSun} />
        <View style={styles.bookHillOne} />
        <View style={styles.bookHillTwo} />
        <View style={styles.bookStem} />
        <View style={styles.bookLeafTop} />
        <View style={styles.bookLeafBottom} />
      </View>
      <View style={styles.bookRightPage}>
        <View style={styles.bookLineOne} />
        <View style={styles.bookLineTwo} />
        <View style={styles.bookLineThree} />
      </View>
      <View style={styles.bookSpine} />
      <View style={styles.bookSparkOne} />
      <View style={styles.bookSparkTwo} />
    </View>
  );
}

function DrawingArtwork(): React.JSX.Element {
  return (
    <View style={styles.drawingArtCanvas} accessible={false}>
      <View style={styles.paperSheet}>
        <View style={styles.paperSun} />
        <View style={styles.paperCloudLeft} />
        <View style={styles.paperCloudRight} />
        <View style={styles.paperStem} />
        <View style={styles.paperLeafLeft} />
        <View style={styles.paperLeafRight} />
        <View style={styles.paperGround} />
        <View style={styles.paperFlower} />
      </View>
      <View style={styles.crayonOne} />
      <View style={styles.crayonTwo} />
      <View style={styles.paperSpark} />
    </View>
  );
}

function ProfileAvatar({ name, size }: { name: string; size: number }): React.JSX.Element {
  const initials = useMemo(() => name.trim().slice(0, 1).toLocaleUpperCase('vi-VN'), [name]);
  return (
    <View style={[styles.avatar, { width: size, height: size, borderRadius: size / 2 }]}>
      {initials ? (
        <Text style={[styles.avatarText, { fontSize: size * 0.42 }]}>{initials}</Text>
      ) : (
        <Ionicons name="happy-outline" size={size * 0.48} color={colors.primaryDeep} accessible={false} />
      )}
      <View style={styles.avatarDot} />
    </View>
  );
}

function ProfilePickerModal({
  visible,
  profiles,
  selectedProfileId,
  onClose,
  onSelect,
  onManage,
}: {
  visible: boolean;
  profiles: ParentProfileViewV1[];
  selectedProfileId: string | null;
  onClose: () => void;
  onSelect: (profile: ParentProfileViewV1) => void;
  onManage: () => void;
}): React.JSX.Element {
  return (
    <Modal visible={visible} animationType="slide" transparent statusBarTranslucent onRequestClose={onClose}>
      <View style={styles.modalRoot}>
        <Pressable accessibilityRole="button" accessibilityLabel="Đóng chọn hồ sơ" style={styles.modalScrim} onPress={onClose} />
        <SafeAreaView edges={['bottom']} style={styles.profileSheet}>
          <View style={styles.sheetHandle} />
          <View style={styles.sheetTitleRow}>
            <View>
              <Text style={styles.sheetTitle}>Chọn hồ sơ bé</Text>
              <Text style={styles.sheetSubtitle}>Mỗi câu chuyện gắn với một hồ sơ.</Text>
            </View>
            <Pressable accessibilityRole="button" accessibilityLabel="Đóng" onPress={onClose} style={styles.sheetClose}>
              <Ionicons name="close" size={21} color={colors.ink} accessible={false} />
            </Pressable>
          </View>
          <View style={styles.profileOptions}>
            {profiles.map((profile) => {
              const selected = profile.profile_id === selectedProfileId;
              return (
                <Pressable
                  key={profile.profile_id}
                  accessibilityRole="button"
                  accessibilityState={{ selected }}
                  accessibilityLabel={`Chọn hồ sơ ${profile.display_name}`}
                  onPress={() => onSelect(profile)}
                  style={({ pressed }) => [styles.profileOption, selected && styles.profileOptionSelected, pressed && styles.pressed]}
                >
                  <ProfileAvatar name={profile.display_name} size={42} />
                  <View style={styles.profileOptionCopy}>
                    <Text numberOfLines={1} style={styles.profileOptionName}>{profile.display_name}</Text>
                    <Text style={styles.profileOptionMeta}>Hồ sơ của bé</Text>
                  </View>
                  {selected ? <Ionicons name="checkmark-circle" size={22} color={colors.primary} accessible={false} /> : <Ionicons name="ellipse-outline" size={20} color="#B7A8C5" accessible={false} />}
                </Pressable>
              );
            })}
            {!profiles.length ? <Text style={styles.emptyProfiles}>Tạo hồ sơ của bé để bắt đầu.</Text> : null}
          </View>
          <Pressable accessibilityRole="button" onPress={onManage} style={({ pressed }) => [styles.manageProfilesButton, pressed && styles.pressed]}>
            <Ionicons name="people-outline" size={18} color={colors.primary} accessible={false} />
            <Text style={styles.manageProfilesText}>Quản lý hồ sơ</Text>
            <Ionicons name="arrow-forward" size={16} color={colors.primary} accessible={false} />
          </Pressable>
        </SafeAreaView>
      </View>
    </Modal>
  );
}

function storyTitle(run: ParentStoryRunV1): string {
  const story = run.story;
  if (typeof story === 'object' && story !== null && 'title' in story && typeof story.title === 'string' && story.title.trim()) {
    return story.title.trim();
  }
  return run.context_snapshot.topic?.trim() || run.subject_label?.trim() || 'Buổi sáng tạo đang mở';
}

function runProgressState(run: ParentStoryRunV1): { label: string; step: number | null } {
  if (run.job_state === 'AWAITING_RECONCILIATION') return { label: 'Đang xác minh kết quả', step: null };
  if (run.job_state === 'RUNNING' && run.run_state === 'VIDEO_ADMISSION_PENDING') return { label: 'Đang tạo video', step: 3 };

  const states: Record<string, { label: string; step: number | null }> = {
    CONTEXT_PENDING: { label: 'Đang chuẩn bị buổi vẽ', step: 0 },
    INPUT_PROCESSING: { label: 'Đang xử lý ảnh tranh', step: 0 },
    SUBJECT_REVIEW: { label: 'Chờ xác nhận chủ thể', step: 1 },
    PREPARATION_REVIEW: { label: 'Đang chuẩn bị nội dung', step: 2 },
    SCRIPT_GENERATING: { label: 'Đang tạo câu chuyện', step: 2 },
    SCRIPT_GENERATION_UNKNOWN: { label: 'Đang xác minh câu chuyện', step: 2 },
    SCRIPT_REVIEW: { label: 'Chờ xem lại câu chuyện', step: 2 },
    VIDEO_ADMISSION_PENDING: { label: 'Đang chờ tạo video', step: 3 },
  };
  return states[run.run_state] ?? { label: 'Buổi sáng tạo đang mở', step: null };
}

const styles = StyleSheet.create({
  safeRoot: { flex: 1, backgroundColor: colors.background },
  root: { flex: 1, backgroundColor: colors.background },
  backgroundGlowTop: { position: 'absolute', top: -150, right: -120, width: 290, height: 290, borderRadius: 145, backgroundColor: '#F0E8FF', opacity: 0.58 },
  scroll: { flex: 1 },
  content: { width: '100%', maxWidth: 640, alignSelf: 'center', paddingHorizontal: 20, paddingTop: 8, paddingBottom: 24, gap: 20 },
  contentCompact: { paddingHorizontal: 16, paddingTop: 4, gap: 16 },
  header: { gap: 13 },
  brandRow: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  logo: { width: 142, height: 48 },
  notificationButton: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: '#F0E7F5', shadowColor: colors.ink, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 1 },
  welcomePanel: { minHeight: 112, paddingHorizontal: 15, paddingVertical: 12, borderRadius: 23, backgroundColor: '#F5EFFF', borderWidth: 1, borderColor: '#E8DDF7', flexDirection: 'row', alignItems: 'center', gap: 8, overflow: 'hidden', shadowColor: '#4E2B72', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.06, shadowRadius: 11, elevation: 2 },
  welcomePanelCompact: { minHeight: 108, paddingHorizontal: 13, paddingVertical: 10 },
  greetingBlock: { flex: 1, minWidth: 0, gap: 5 },
  greeting: { color: colors.ink, fontFamily: roundedFont, fontSize: 24, lineHeight: 30, fontWeight: '800', letterSpacing: -0.45, flexShrink: 1 },
  greetingCompact: { fontSize: 22, lineHeight: 27 },
  greetingSubtitle: { color: colors.muted, fontFamily: roundedFont, fontSize: 12, lineHeight: 17, flexShrink: 1 },
  welcomeArt: { width: 82, height: 82, flexShrink: 0, alignItems: 'center', justifyContent: 'center' },
  welcomeArtHalo: { position: 'absolute', right: 1, top: 7, width: 67, height: 67, borderRadius: 34, backgroundColor: '#E8DCFA' },
  welcomePaper: { position: 'absolute', left: 7, top: 14, width: 45, height: 54, borderRadius: 8, backgroundColor: '#FFFEFC', borderWidth: 1, borderColor: '#DED0E9', overflow: 'hidden', transform: [{ rotate: '-8deg' }] },
  welcomeSun: { position: 'absolute', right: 7, top: 7, width: 9, height: 9, borderRadius: 5, backgroundColor: '#FFC84D' },
  welcomeCloud: { position: 'absolute', left: 7, top: 12, width: 17, height: 7, borderRadius: 8, backgroundColor: '#B9E2FC' },
  welcomeHill: { position: 'absolute', left: -5, bottom: 6, width: 52, height: 20, borderRadius: 18, backgroundColor: '#B9E1A8', transform: [{ rotate: '-7deg' }] },
  welcomeStem: { position: 'absolute', left: 24, bottom: 12, width: 2, height: 21, borderRadius: 1, backgroundColor: '#6E9B66' },
  welcomeLeaf: { position: 'absolute', left: 20, bottom: 27, width: 12, height: 7, borderRadius: 8, backgroundColor: '#85C891', transform: [{ rotate: '-28deg' }] },
  welcomePencil: { position: 'absolute', right: 9, top: 15, width: 12, height: 47, borderRadius: 6, backgroundColor: '#FFB847', borderWidth: 1, borderColor: '#E9A02C', transform: [{ rotate: '23deg' }] },
  welcomePencilBand: { position: 'absolute', left: -1, right: -1, top: 8, height: 5, backgroundColor: '#9A63D8' },
  welcomePencilTip: { position: 'absolute', right: 5, top: 57, width: 0, height: 0, borderLeftWidth: 6, borderRightWidth: 6, borderTopWidth: 10, borderLeftColor: 'transparent', borderRightColor: 'transparent', borderTopColor: '#805744', transform: [{ rotate: '23deg' }] },
  welcomeSpark: { position: 'absolute', right: 6, top: 6, width: 8, height: 8, backgroundColor: '#FFC84D', transform: [{ rotate: '45deg' }] },
  welcomeDot: { position: 'absolute', left: 2, bottom: 8, width: 6, height: 6, borderRadius: 3, backgroundColor: colors.coral },
  profileSelector: { minHeight: 58, paddingHorizontal: 11, paddingVertical: 8, borderRadius: 20, backgroundColor: colors.surface, flexDirection: 'row', alignItems: 'center', gap: 10, borderWidth: 1, borderColor: '#EEE5F2' },
  profileSelectorCopy: { flex: 1, minWidth: 0, gap: 1 },
  profileOverline: { color: colors.muted, fontFamily: roundedFont, fontSize: 9, lineHeight: 12, fontWeight: '800', letterSpacing: 0.8 },
  profileName: { color: colors.ink, fontFamily: roundedFont, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  avatar: { position: 'relative', alignItems: 'center', justifyContent: 'center', backgroundColor: colors.lavender, borderWidth: 1.5, borderColor: '#E0D0FA' },
  avatarText: { color: colors.primaryDeep, fontFamily: roundedFont, fontWeight: '800' },
  avatarDot: { position: 'absolute', right: -1, bottom: 0, width: 10, height: 10, borderRadius: 5, backgroundColor: colors.coral, borderWidth: 2, borderColor: colors.surface },
  heroCard: { borderRadius: 26, overflow: 'hidden', backgroundColor: colors.lavender, borderWidth: 1, borderColor: '#E4D5FB', shadowColor: '#4B2A70', shadowOffset: { width: 0, height: 9 }, shadowOpacity: 0.1, shadowRadius: 18, elevation: 3 },
  heroArtworkStage: { aspectRatio: 2, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  heroSunGlow: { position: 'absolute', top: -78, right: 28, width: 180, height: 180, borderRadius: 90, backgroundColor: 'rgba(255,255,255,0.48)' },
  heroOrb: { position: 'absolute', left: -38, bottom: -90, width: 180, height: 180, borderRadius: 90, backgroundColor: 'rgba(255,255,255,0.28)' },
  heroIllustration: { width: '100%', height: '100%' },
  heroCopy: { paddingHorizontal: 17, paddingTop: 14, paddingBottom: 16, gap: 7, backgroundColor: 'rgba(255,255,255,0.88)' },
  heroCopyCompact: { paddingHorizontal: 14, paddingTop: 12, paddingBottom: 14 },
  heroTitle: { color: colors.ink, fontFamily: roundedFont, fontSize: 20, lineHeight: 26, fontWeight: '800', letterSpacing: -0.25, flexShrink: 1 },
  heroSubtitle: { color: colors.muted, fontFamily: roundedFont, fontSize: 13, lineHeight: 19, flexShrink: 1 },
  heroActions: { flexDirection: 'row', alignItems: 'stretch', gap: 8, marginTop: 5 },
  heroActionsCompact: { flexDirection: 'column' },
  heroActionCompact: { flex: 0, minHeight: 48, flexDirection: 'row', justifyContent: 'center' },
  primaryAction: { flex: 1.04, minWidth: 0, minHeight: 52, paddingHorizontal: 10, paddingVertical: 8, borderRadius: 18, backgroundColor: colors.primary, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, shadowColor: colors.primaryDeep, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 7, elevation: 3 },
  primaryActionText: { color: '#FFFFFF', fontFamily: roundedFont, fontSize: 13, lineHeight: 17, fontWeight: '800', flexShrink: 1, textAlign: 'center' },
  secondaryAction: { flex: 0.96, minWidth: 0, minHeight: 52, paddingHorizontal: 9, paddingVertical: 7, borderRadius: 18, backgroundColor: '#F4EDFF', borderWidth: 1, borderColor: '#D8C5F8', flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6 },
  secondaryActionText: { color: colors.primaryDeep, fontFamily: roundedFont, fontSize: 12, lineHeight: 16, fontWeight: '700', flexShrink: 1, textAlign: 'center' },
  continueSection: { gap: 10 },
  continueSectionTitle: { color: colors.ink, fontFamily: roundedFont, fontSize: 18, lineHeight: 24, fontWeight: '800' },
  continueCard: { minHeight: 128, padding: 12, borderRadius: 22, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.line, flexDirection: 'row', alignItems: 'center', gap: 10, shadowColor: colors.ink, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.05, shadowRadius: 10, elevation: 1 },
  continueThumb: { width: 74, height: 92, borderRadius: 17, overflow: 'hidden', backgroundColor: '#E7E5FF', alignItems: 'center', justifyContent: 'center' },
  continueThumbImage: { width: 118, height: 92, maxWidth: '160%' },
  continueCopy: { flex: 1, minWidth: 0, alignSelf: 'stretch', justifyContent: 'center', gap: 5 },
  continueTitle: { color: colors.ink, fontFamily: roundedFont, fontSize: 14, lineHeight: 18, fontWeight: '800' },
  continueMeta: { color: colors.muted, fontFamily: roundedFont, fontSize: 11, lineHeight: 15 },
  runStateRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  runStateDot: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.coral },
  runStateText: { flex: 1, color: colors.primaryDeep, fontFamily: roundedFont, fontSize: 10, lineHeight: 14, fontWeight: '700' },
  progressTrack: { flexDirection: 'row', gap: 4, marginTop: 1 },
  progressUnit: { flex: 1, minWidth: 0, gap: 3 },
  progressSegment: { height: 3, borderRadius: 2, backgroundColor: '#E7E0ED' },
  progressSegmentActive: { backgroundColor: colors.primary },
  progressLabel: { color: '#897E91', fontFamily: roundedFont, fontSize: 8, lineHeight: 10 },
  progressLabelActive: { color: colors.primaryDeep, fontWeight: '800' },
  continueButton: { alignSelf: 'flex-start', minHeight: 34, paddingHorizontal: 9, borderRadius: 12, backgroundColor: colors.lavenderSoft, flexDirection: 'row', alignItems: 'center', gap: 4 },
  continueButtonText: { color: colors.primaryDeep, fontFamily: roundedFont, fontSize: 10, lineHeight: 13, fontWeight: '800' },
  exploreSection: { gap: 12 },
  sectionHeading: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  sectionHeadingCopy: { flex: 1, minWidth: 0, gap: 3 },
  sectionTitle: { color: colors.ink, fontFamily: roundedFont, fontSize: 19, lineHeight: 25, fontWeight: '800', letterSpacing: -0.25 },
  sectionSubtitle: { color: colors.muted, fontFamily: roundedFont, fontSize: 12, lineHeight: 17, flexShrink: 1 },
  sectionSpark: { width: 34, height: 34, borderRadius: 17, backgroundColor: colors.lavender, alignItems: 'center', justifyContent: 'center' },
  exploreGrid: { flexDirection: 'row', gap: 12 },
  exploreCard: { flex: 1, minWidth: 0, overflow: 'hidden', borderRadius: 22, backgroundColor: colors.surface, borderWidth: 1, borderColor: '#ECE3F1', shadowColor: colors.ink, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.05, shadowRadius: 9, elevation: 1 },
  exploreArtwork: { height: 112, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  lessonArtwork: { backgroundColor: '#FFF0CF' },
  drawingArtwork: { backgroundColor: '#E5F4FF' },
  artworkBadge: { position: 'absolute', left: 9, top: 9, width: 28, height: 28, borderRadius: 10, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'rgba(255,255,255,0.9)' },
  lessonBadge: { backgroundColor: '#FFF9EC' },
  drawingBadge: { backgroundColor: '#F6FBFF' },
  lessonArtCanvas: { width: 146, height: 100, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', transform: [{ rotate: '-4deg' }] },
  bookShadow: { position: 'absolute', bottom: 10, width: 118, height: 16, borderRadius: 10, backgroundColor: 'rgba(111,70,136,0.12)' },
  bookLeftPage: { position: 'relative', width: 54, height: 66, borderTopLeftRadius: 13, borderBottomLeftRadius: 8, backgroundColor: '#FFFDF6', borderWidth: 1.5, borderColor: '#9B73C1', overflow: 'hidden' },
  bookRightPage: { width: 54, height: 66, borderTopRightRadius: 13, borderBottomRightRadius: 8, backgroundColor: '#FFF8EB', borderWidth: 1.5, borderColor: '#9B73C1', overflow: 'hidden', alignItems: 'center' },
  bookSpine: { position: 'absolute', width: 4, height: 66, backgroundColor: '#8457AD' },
  bookSun: { position: 'absolute', right: 8, top: 8, width: 13, height: 13, borderRadius: 7, backgroundColor: '#FFC84D' },
  bookHillOne: { position: 'absolute', bottom: 12, left: -7, width: 50, height: 24, borderRadius: 25, backgroundColor: '#B8E2A7', transform: [{ rotate: '-6deg' }] },
  bookHillTwo: { position: 'absolute', bottom: 8, right: -8, width: 39, height: 20, borderRadius: 20, backgroundColor: '#89C991' },
  bookStem: { position: 'absolute', left: 25, bottom: 17, width: 3, height: 27, borderRadius: 2, backgroundColor: '#56845A' },
  bookLeafTop: { position: 'absolute', left: 18, bottom: 35, width: 16, height: 9, borderRadius: 10, backgroundColor: '#81C993', transform: [{ rotate: '-26deg' }] },
  bookLeafBottom: { position: 'absolute', left: 27, bottom: 26, width: 14, height: 8, borderRadius: 9, backgroundColor: '#9ED9A6', transform: [{ rotate: '24deg' }] },
  bookLineOne: { width: 31, height: 3, marginTop: 23, borderRadius: 2, backgroundColor: '#E8C6A4' },
  bookLineTwo: { width: 35, height: 3, marginTop: 5, borderRadius: 2, backgroundColor: '#E8C6A4' },
  bookLineThree: { width: 27, height: 3, marginTop: 5, borderRadius: 2, backgroundColor: '#E8C6A4' },
  bookSparkOne: { position: 'absolute', right: 2, top: 4, width: 8, height: 8, backgroundColor: '#FFB842', transform: [{ rotate: '45deg' }] },
  bookSparkTwo: { position: 'absolute', left: 7, top: 13, width: 6, height: 6, borderRadius: 3, backgroundColor: '#FF8B75' },
  drawingArtCanvas: { width: 150, height: 105, alignItems: 'center', justifyContent: 'center', transform: [{ rotate: '3deg' }] },
  paperSheet: { width: 86, height: 75, borderRadius: 8, backgroundColor: '#FFFEFC', borderWidth: 1.5, borderColor: '#DCC7E8', transform: [{ rotate: '-7deg' }], overflow: 'hidden' },
  paperSun: { position: 'absolute', top: 10, right: 13, width: 14, height: 14, borderRadius: 8, backgroundColor: '#FFD153' },
  paperCloudLeft: { position: 'absolute', top: 14, left: 12, width: 20, height: 8, borderRadius: 8, backgroundColor: '#B9E2FC' },
  paperCloudRight: { position: 'absolute', top: 23, right: 17, width: 16, height: 6, borderRadius: 7, backgroundColor: '#C4E9FA' },
  paperStem: { position: 'absolute', left: 43, bottom: 17, width: 3, height: 31, borderRadius: 2, backgroundColor: '#56845A' },
  paperLeafLeft: { position: 'absolute', left: 29, bottom: 35, width: 18, height: 9, borderRadius: 10, backgroundColor: '#9ED9A6', transform: [{ rotate: '-25deg' }] },
  paperLeafRight: { position: 'absolute', left: 43, bottom: 30, width: 17, height: 8, borderRadius: 9, backgroundColor: '#83C994', transform: [{ rotate: '24deg' }] },
  paperGround: { position: 'absolute', left: 8, right: 7, bottom: 12, height: 4, borderRadius: 5, backgroundColor: '#B7D889' },
  paperFlower: { position: 'absolute', left: 18, bottom: 17, width: 9, height: 9, borderRadius: 5, backgroundColor: '#FF9C88', borderWidth: 2, borderColor: '#FFD457' },
  crayonOne: { position: 'absolute', right: 25, bottom: 11, width: 12, height: 46, borderRadius: 6, backgroundColor: '#FF836F', borderWidth: 1, borderColor: '#E3695A', transform: [{ rotate: '24deg' }] },
  crayonTwo: { position: 'absolute', right: 40, bottom: 11, width: 11, height: 39, borderRadius: 6, backgroundColor: '#8C65D3', borderWidth: 1, borderColor: '#7350B6', transform: [{ rotate: '-17deg' }] },
  paperSpark: { position: 'absolute', left: 17, top: 14, width: 8, height: 8, backgroundColor: '#FFC84D', transform: [{ rotate: '45deg' }] },
  exploreCopy: { minHeight: 113, paddingHorizontal: 12, paddingTop: 10, paddingBottom: 11, gap: 5 },
  exploreTitle: { color: colors.ink, fontFamily: roundedFont, fontSize: 15, lineHeight: 20, fontWeight: '800' },
  exploreSubtitle: { minHeight: 32, color: colors.muted, fontFamily: roundedFont, fontSize: 10, lineHeight: 15, flexShrink: 1 },
  exploreLinkRow: { marginTop: 'auto', flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 4 },
  exploreLink: { color: colors.primaryDeep, fontFamily: roundedFont, fontSize: 10, lineHeight: 14, fontWeight: '800' },
  pressed: { opacity: 0.82, transform: [{ scale: 0.99 }] },
  actionPressed: { opacity: 0.88, transform: [{ scale: 0.985 }] },
  modalRoot: { flex: 1, justifyContent: 'flex-end' },
  modalScrim: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(34,20,50,0.34)' },
  profileSheet: { paddingHorizontal: 20, paddingTop: 10, paddingBottom: 12, borderTopLeftRadius: 28, borderTopRightRadius: 28, backgroundColor: colors.background, gap: 17 },
  sheetHandle: { alignSelf: 'center', width: 38, height: 4, borderRadius: 2, backgroundColor: '#D5CBDC' },
  sheetTitleRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  sheetTitle: { color: colors.ink, fontFamily: roundedFont, fontSize: 20, lineHeight: 27, fontWeight: '800' },
  sheetSubtitle: { marginTop: 2, color: colors.muted, fontFamily: roundedFont, fontSize: 12, lineHeight: 17 },
  sheetClose: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#F1EAF7', alignItems: 'center', justifyContent: 'center' },
  profileOptions: { gap: 8, maxHeight: 300 },
  profileOption: { minHeight: 62, paddingHorizontal: 10, paddingVertical: 8, borderRadius: 17, backgroundColor: colors.surface, borderWidth: 1, borderColor: '#EEE5F2', flexDirection: 'row', alignItems: 'center', gap: 10 },
  profileOptionSelected: { borderColor: colors.primary, backgroundColor: '#F8F3FF' },
  profileOptionCopy: { flex: 1, minWidth: 0, gap: 2 },
  profileOptionName: { color: colors.ink, fontFamily: roundedFont, fontSize: 14, lineHeight: 19, fontWeight: '800' },
  profileOptionMeta: { color: colors.muted, fontFamily: roundedFont, fontSize: 11, lineHeight: 15 },
  emptyProfiles: { paddingVertical: 16, color: colors.muted, fontFamily: roundedFont, fontSize: 13, lineHeight: 19, textAlign: 'center' },
  manageProfilesButton: { minHeight: 48, paddingHorizontal: 14, borderRadius: 16, backgroundColor: colors.lavender, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  manageProfilesText: { flex: 1, color: colors.primaryDeep, fontFamily: roundedFont, fontSize: 13, lineHeight: 18, fontWeight: '800' },
});
