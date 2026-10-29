import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  StatusBar,
  Platform,
  useWindowDimensions,
  Animated,
  Modal,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from './src/theme';
import type { ScreenId, ScreenMeta } from './src/types';
import {
  LoginScreen,
  ChildProfileScreen,
  ParentProfileListScreen,
  ParentProfileDetailScreen,
  ParentHomeScreen,
  TopicSelectionScreen,
  SketchGuideScreen,
  ParentCaptureScreen,
  StoryInputScreen,
  TranscriptReviewScreen,
  ParentSubjectReviewScreen,
  ActivitySelectionScreen,
  ActivityContextReviewScreen,
  ParentAiProcessingScreen,
  StoryReviewScreen,
  StoryboardScreen,
  ScriptConfirmScreen,
  ParentVideoProcessingScreen,
  SafetyGateScreen,
  PlaybackScreen,
  CompletionScreen,
  HistoryScreen,
  QuotaScreen,
  NotificationsSettingsScreen,
  IntroVideoScreen,
} from './src/screens';
import { AppProvider, useAppContext } from './src/context/AppContext';

// Screen metadata for dev quick-switch (only active when ?dev=true)
const SCREENS: ScreenMeta[] = [
  { id: 'login', title: '1. Parent Login', subtitle: 'Đăng nhập phụ huynh', flow: 'flow1', workflowStep: 1, stepName: 'Login' },
  { id: 'profile_list', title: '2. Profile List', subtitle: 'Danh sách hồ sơ trẻ', flow: 'flow1', workflowStep: 1, stepName: 'Profiles' },
  { id: 'profile_detail', title: '3. Profile Detail', subtitle: 'Chi tiết hồ sơ trẻ', flow: 'flow1', workflowStep: 1, stepName: 'Profile detail' },
  { id: 'parent_home', title: '4. Parent Home', subtitle: 'Trang chủ phụ huynh', flow: 'flow1', workflowStep: 1, stepName: 'Parent home' },
  { id: 'topic_selection', title: '5. Topic Selection', subtitle: 'Chọn chủ đề & độ khó', flow: 'flow1', workflowStep: 1, stepName: 'Topic' },
  { id: 'sketch_guide', title: '6. Optional Sketch Guide', subtitle: 'Hướng dẫn vẽ chung', flow: 'flow1', workflowStep: 1, stepName: 'Sketch guide' },
  { id: 'capture', title: '7. Capture / Upload', subtitle: 'Một tranh vẽ của bé', flow: 'flow1', workflowStep: 1, stepName: 'Capture' },
  { id: 'voice', title: '8. Story Input', subtitle: 'Text hoặc audio', flow: 'flow1', workflowStep: 1, stepName: 'Narration' },
  { id: 'transcript_review', title: '9. Transcript Review', subtitle: 'Kiểm tra lời kể', flow: 'flow1', workflowStep: 1, stepName: 'Transcript review' },
  { id: 'activity_selection', title: '10. Activity Catalog', subtitle: 'Chọn hoạt động đã duyệt', flow: 'flow2', workflowStep: 3, stepName: 'Activity' },
  { id: 'activity_context_review', title: '11. Activity Context', subtitle: 'Duyệt hoạt động & hồ sơ', flow: 'flow2', workflowStep: 3, stepName: 'Context' },
  { id: 'ai_processing', title: '12. Story Processing', subtitle: 'Xử lý bất đồng bộ', flow: 'flow2', workflowStep: 4, stepName: 'Processing' },
  { id: 'story_review', title: '13. Story Review', subtitle: 'Duyệt bản story', flow: 'flow2', workflowStep: 4, stepName: 'Story review' },
  { id: 'storyboard', title: '14. Storyboard', subtitle: '5–15 cảnh', flow: 'flow2', workflowStep: 5, stepName: 'Storyboard' },
  { id: 'script_confirm', title: '15. Script Confirmation', subtitle: 'Xác nhận kịch bản', flow: 'flow2', workflowStep: 5, stepName: 'Script' },
  { id: 'video_processing', title: '16. Video Job', subtitle: 'Tạo video bất đồng bộ', flow: 'flow2', workflowStep: 6, stepName: 'Video job' },
  { id: 'safety_gate', title: '17. Safety Gate', subtitle: 'Kiểm tra an toàn', flow: 'flow2', workflowStep: 7, stepName: 'Safety' },
  { id: 'playback', title: '18. Playback', subtitle: 'Xem video', flow: 'flow2', workflowStep: 8, stepName: 'Playback' },
  { id: 'completion', title: '19. Completion', subtitle: 'Hoàn tất / huỷ / xoá', flow: 'flow2', workflowStep: 8, stepName: 'Completion' },
  { id: 'history', title: '20. History', subtitle: 'Lịch sử run/video', flow: 'flow1', workflowStep: 8, stepName: 'History' },
  { id: 'quota', title: '21. Quota', subtitle: 'Quota tháng hiện tại', flow: 'flow1', workflowStep: 8, stepName: 'Quota' },
  { id: 'notifications_settings', title: '22. Notifications & Settings', subtitle: 'Thông báo và dữ liệu', flow: 'flow1', workflowStep: 8, stepName: 'Settings' },
];

function MainAppContent() {
  const { width: windowWidth } = useWindowDimensions();
  const { currentScreen, navigate, toastMessage, workflowError, dismissWorkflowError } = useAppContext();

  // The branded intro is a one-shot startup gate. Developer deep links can
  // bypass it with ?dev=true, ?screen=..., or ?intro=false; native startup
  // always shows the video before entering the existing Login screen.
  const [introComplete, setIntroComplete] = useState<boolean>(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('intro') === 'true') return false;
      return params.get('dev') === 'true' || params.has('screen') || params.get('intro') === 'false';
    }
    return false;
  });

  // Check if developer mode is enabled via query param (?dev=true)
  const [isDevMode, setIsDevMode] = useState<boolean>(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      return params.get('dev') === 'true';
    }
    return false;
  });

  const [devDrawerOpen, setDevDrawerOpen] = useState(false);
  const [tapClockCount, setTapClockCount] = useState(0);

  // Hidden feature: Triple-tap the status bar clock to toggle dev mode
  const handleClockTap = () => {
    if (Platform.OS !== 'web') return;
    setTapClockCount((prev) => {
      if (prev + 1 >= 3) {
        setIsDevMode((mode) => !mode);
        return 0;
      }
      return prev + 1;
    });
  };

  // Support auto-scrolling for visual inspection when ?scroll=number is provided
  useEffect(() => {
    if (Platform.OS === 'web' && typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const scrollVal = params.get('scroll');
      if (scrollVal) {
        setTimeout(() => {
          const scrollPx = parseInt(scrollVal, 10) || 500;
          const all = document.querySelectorAll('*');
          for (let i = 0; i < all.length; i++) {
            const el = all[i];
            if (el.scrollHeight > el.clientHeight && el.clientHeight > 300) {
              el.scrollTop = scrollPx;
            }
          }
        }, 450);
      }
    }
  }, [currentScreen]);

  const isDesktopWeb = Platform.OS === 'web' && windowWidth > 540;
  const currentIndex = SCREENS.findIndex((s) => s.id === currentScreen);
  const currentMeta = SCREENS[currentIndex] || SCREENS[0];

  const renderScreen = () => {
    switch (currentScreen) {
      case 'login':
        return <LoginScreen />;
      case 'profile_list':
        return <ParentProfileListScreen />;
      case 'profile_detail':
        return <ParentProfileDetailScreen />;
      case 'parent_home':
        return <ParentHomeScreen />;
      case 'topic_selection':
        return <TopicSelectionScreen />;
      case 'sketch_guide':
        return <SketchGuideScreen />;
      case 'profile':
        return <ChildProfileScreen />;
      case 'capture':
        return <ParentCaptureScreen />;
      case 'voice':
        return <StoryInputScreen />;
      case 'ai_processing':
        return <ParentAiProcessingScreen />;
      case 'scene_understanding':
        return <ParentSubjectReviewScreen />;
      case 'activity_selection':
        return <ActivitySelectionScreen />;
      case 'activity_context_review':
        return <ActivityContextReviewScreen />;
      case 'transcript_review':
        return <TranscriptReviewScreen />;
      case 'story_review':
        return <StoryReviewScreen />;
      case 'storyboard':
        return <StoryboardScreen />;
      case 'script_confirm':
        return <ScriptConfirmScreen />;
      case 'video_processing':
        return <ParentVideoProcessingScreen />;
      case 'safety_gate':
        return <SafetyGateScreen />;
      case 'playback':
        return <PlaybackScreen />;
      case 'completion':
        return <CompletionScreen />;
      case 'history':
        return <HistoryScreen />;
      case 'quota':
        return <QuotaScreen />;
      case 'notifications_settings':
        return <NotificationsSettingsScreen />;
      default:
        return <LoginScreen />;
    }
  };

  if (!introComplete) {
    return <IntroVideoScreen onFinished={() => setIntroComplete(true)} />;
  }

  return (
    <SafeAreaView style={styles.outerContainer}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      {Platform.OS === 'android' && Number(Platform.Version) >= 35 && (
        <View
          pointerEvents="none"
          style={{ height: StatusBar.currentHeight ?? 0, backgroundColor: '#EFF6FF' }}
        />
      )}

      {/* Optional Developer Quick Bar: ONLY visible if ?dev=true or 3x tap clock */}
      {isDevMode && (
        <View style={styles.floatingNavPill}>
          <TouchableOpacity
            style={[styles.navArrowBtn, currentIndex === 0 && styles.navArrowBtnDisabled]}
            disabled={currentIndex === 0}
            onPress={() => currentIndex > 0 && navigate(SCREENS[currentIndex - 1].id)}
          >
            <Ionicons name="chevron-back" size={14} color={currentIndex === 0 ? '#CBD5E1' : '#1E293B'} />
          </TouchableOpacity>

          <TouchableOpacity
            activeOpacity={0.85}
            style={styles.navTitleBtn}
            onPress={() => setDevDrawerOpen(!devDrawerOpen)}
          >
            <View style={styles.stepNumBadge}>
              <Text style={styles.stepNumText}>{currentIndex + 1}/{SCREENS.length}</Text>
            </View>
            <Text style={styles.navScreenText} numberOfLines={1}>
              {currentMeta.title}
            </Text>
            <Ionicons name={devDrawerOpen ? 'chevron-up' : 'chevron-down'} size={13} color="#2563EB" />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navArrowBtn, currentIndex === SCREENS.length - 1 && styles.navArrowBtnDisabled]}
            disabled={currentIndex === SCREENS.length - 1}
            onPress={() => currentIndex < SCREENS.length - 1 && navigate(SCREENS[currentIndex + 1].id)}
          >
            <Ionicons name="chevron-forward" size={14} color={currentIndex === SCREENS.length - 1 ? '#CBD5E1' : '#1E293B'} />
          </TouchableOpacity>

          <TouchableOpacity onPress={() => setIsDevMode(false)} style={{ marginLeft: 6 }}>
            <Ionicons name="close-circle" size={16} color="#94A3B8" />
          </TouchableOpacity>
        </View>
      )}

      {/* Dev Switcher Drawer */}
      {isDevMode && devDrawerOpen && (
        <View style={styles.drawerModal}>
          <View style={styles.drawerHeader}>
            <Text style={styles.drawerHeading}>CHỌN MÀN HÌNH NHANH (DEV MODE)</Text>
            <TouchableOpacity onPress={() => setDevDrawerOpen(false)}>
              <Ionicons name="close" size={20} color={colors.textSoft} />
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.drawerScroll} showsVerticalScrollIndicator={true}>
            <View style={styles.drawerGrid}>
              {SCREENS.map((item) => {
                const isActive = item.id === currentScreen;
                return (
                  <TouchableOpacity
                    key={item.id}
                    onPress={() => {
                      navigate(item.id);
                      setDevDrawerOpen(false);
                    }}
                    style={[styles.drawerItem, isActive && styles.drawerItemActive]}
                  >
                    <Text style={[styles.drawerItemTitle, isActive && styles.drawerItemTitleActive]}>
                      {item.title}
                    </Text>
                    <Text style={styles.drawerItemSub}>{item.subtitle}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </ScrollView>
        </View>
      )}

      {/* Main Mobile App Frame */}
      <View style={[styles.appContainer, isDevMode && { paddingTop: 46 }]}>
        <View style={[styles.phoneChassis, !isDesktopWeb && styles.phoneChassisNative]}>
          {/* Native Mobile Status Bar (hidden on splash because splash hero image fills the bezel) */}
          {Platform.OS === 'web' && currentScreen !== 'splash' && (
            <View style={[styles.mobileStatusBar, currentScreen === 'login' && styles.mobileStatusBarLoginOverlay]}>
              <TouchableOpacity activeOpacity={0.7} onPress={handleClockTap}>
                <Text style={styles.statusBarClock}>9:41</Text>
              </TouchableOpacity>
              <View style={styles.dynamicIsland}>
                <View style={styles.islandCamera} />
              </View>
              <View style={styles.statusBarIcons}>
                <Ionicons name="cellular" size={12} color="#1F2937" style={{ marginRight: 4 }} />
                <Ionicons name="wifi" size={12} color="#1F2937" style={{ marginRight: 4 }} />
                <Ionicons name="battery-full" size={14} color="#1F2937" />
              </View>
            </View>
          )}

          {/* Floating Native Toast Banner */}
          {toastMessage && (
            <View style={styles.toastContainer}>
              <View style={styles.toastPill}>
                <Ionicons name="checkmark-circle" size={16} color="#10B981" />
                <Text style={styles.toastText}>{toastMessage}</Text>
              </View>
            </View>
          )}

          {/* Active Screen */}
          <View style={[styles.screenBody, currentScreen === 'login' && styles.screenBodyLoginFullBleed]}>
            {renderScreen()}
          </View>

          {/* Virtual Home Bar */}
          {Platform.OS === 'web' && (
            <View style={[styles.homeBarContainer, currentScreen === 'login' && styles.homeBarLoginOverlay]}>
              <View style={styles.homeBarIndicator} />
            </View>
          )}
        </View>
      </View>
      <Modal
        transparent
        visible={Boolean(workflowError)}
        animationType="fade"
        onRequestClose={dismissWorkflowError}
      >
        <View style={styles.errorBackdrop}>
          <View style={styles.errorCard} accessibilityRole="alert">
            <View style={styles.errorIcon}>
              <Ionicons name="cloud-offline-outline" size={28} color="#E11D48" />
            </View>
            <Text style={styles.errorTitle}>Mình chưa làm được bước này</Text>
            <Text style={styles.errorMessage}>{workflowError}</Text>
            <View style={styles.errorActions}>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="Quay về bước chọn ảnh"
                style={[styles.errorButton, styles.errorSecondaryButton]}
                onPress={() => {
                  dismissWorkflowError();
                  navigate('capture');
                }}
              >
                <Text style={styles.errorSecondaryText}>Về bước ảnh</Text>
              </TouchableOpacity>
              <TouchableOpacity
                accessibilityRole="button"
                accessibilityLabel="Đóng thông báo lỗi"
                style={styles.errorButton}
                onPress={dismissWorkflowError}
              >
                <Text style={styles.errorButtonText}>Đóng</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

// BaoVC expanded screens registered for full 8-step workflow
// Fallback error screen integration wired
export default function App() {
  return (
    <AppProvider>
      <MainAppContent />
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  errorBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  errorCard: {
    width: '100%',
    maxWidth: 360,
    borderRadius: 24,
    backgroundColor: '#FFFFFF',
    padding: 24,
    alignItems: 'center',
  },
  errorIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#FFF1F2',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  errorTitle: { fontSize: 19, fontWeight: '900', color: '#172033', textAlign: 'center' },
  errorMessage: { fontSize: 15, lineHeight: 22, color: '#475569', textAlign: 'center', marginTop: 8 },
  errorActions: { flexDirection: 'row', gap: 10, marginTop: 20 },
  errorButton: {
    minHeight: 48,
    minWidth: 126,
    borderRadius: 24,
    backgroundColor: '#2563EB',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 16,
  },
  errorButtonText: { color: '#FFFFFF', fontSize: 16, fontWeight: '800' },
  errorSecondaryButton: { backgroundColor: '#EFF6FF', borderWidth: 1, borderColor: '#93C5FD' },
  errorSecondaryText: { color: '#1D4ED8', fontSize: 15, fontWeight: '800' },
  outerContainer: {
    flex: 1,
    backgroundColor: '#0F172A',
    overflow: 'hidden',
  },
  appContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Platform.OS === 'web' ? 14 : 0,
  },
  phoneChassis: {
    flex: 1,
    width: '100%',
    maxWidth: 416,
    maxHeight: Platform.OS === 'web' ? 844 : undefined,
    backgroundColor: colors.white,
    borderRadius: Platform.OS === 'web' ? 44 : 0,
    overflow: 'hidden',
    borderWidth: Platform.OS === 'web' ? 10 : 0,
    borderColor: '#1E293B',
    ...shadows.card,
    position: 'relative',
  },
  phoneChassisNative: {
    maxWidth: '100%',
    maxHeight: '100%',
    borderRadius: 0,
    borderWidth: 0,
  },
  mobileStatusBar: {
    height: 38,
    backgroundColor: colors.white,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    borderBottomWidth: 0.5,
    borderBottomColor: '#F1F5F9',
  },
  mobileStatusBarLoginOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    zIndex: 30,
    backgroundColor: 'transparent',
    borderBottomWidth: 0,
  },
  statusBarClock: {
    fontSize: 12,
    fontWeight: '800',
    color: '#1F2937',
  },
  dynamicIsland: {
    width: 90,
    height: 20,
    backgroundColor: '#0F172A',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  islandCamera: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#1E293B',
    marginLeft: 40,
  },
  statusBarIcons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  screenBody: {
    flex: 1,
    width: '100%',
    overflow: 'hidden',
    backgroundColor: colors.white,
  },
  screenBodyLoginFullBleed: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
  },
  homeBarContainer: {
    height: 18,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
  },
  homeBarLoginOverlay: {
    position: 'absolute',
    right: 0,
    bottom: 0,
    left: 0,
    zIndex: 30,
    backgroundColor: 'transparent',
  },
  homeBarIndicator: {
    width: 130,
    height: 4,
    backgroundColor: '#94A3B8',
    borderRadius: 2,
  },
  toastContainer: {
    position: 'absolute',
    top: 48,
    left: 16,
    right: 16,
    zIndex: 999,
    alignItems: 'center',
  },
  toastPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#1E293B',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 24,
    ...shadows.card,
  },
  toastText: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.white,
  },

  // Dev Quick-Switch Pill (Only shown if ?dev=true)
  floatingNavPill: {
    position: 'absolute',
    top: 6,
    alignSelf: 'center',
    zIndex: 999,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 24,
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    ...shadows.card,
  },
  navArrowBtn: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  navArrowBtnDisabled: {
    opacity: 0.3,
  },
  navTitleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    gap: 4,
  },
  stepNumBadge: {
    backgroundColor: '#2563EB',
    paddingHorizontal: 5,
    paddingVertical: 2,
    borderRadius: 6,
  },
  stepNumText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  navScreenText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#1E293B',
    maxWidth: 130,
  },
  drawerModal: {
    position: 'absolute',
    top: 46,
    alignSelf: 'center',
    width: '94%',
    maxWidth: 420,
    maxHeight: 480,
    backgroundColor: '#FFFFFF',
    borderRadius: radius.lg,
    padding: 14,
    zIndex: 1000,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    ...shadows.card,
  },
  drawerHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  drawerHeading: {
    fontSize: 11,
    fontWeight: '900',
    color: colors.textHeading,
    letterSpacing: 0.5,
  },
  drawerScroll: {
    marginTop: 8,
  },
  drawerGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  drawerItem: {
    width: '48%',
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: '#E2E8F0',
    borderRadius: 10,
    padding: 8,
  },
  drawerItemActive: {
    backgroundColor: '#EFF6FF',
    borderColor: '#3B82F6',
  },
  drawerItemTitle: {
    fontSize: 11,
    fontWeight: '800',
    color: colors.textHeading,
  },
  drawerItemTitleActive: {
    color: '#1D4ED8',
  },
  drawerItemSub: {
    fontSize: 9,
    color: colors.textSoft,
    marginTop: 2,
  },
});
