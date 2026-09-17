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
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, radius, shadows } from './src/theme';
import type { ScreenId, ScreenMeta } from './src/types';
import {
  SplashScreen,
  OnboardingScreen,
  DashboardScreen,
  ChildProfileScreen,
  CaptureScreen,
  VoiceScreen,
  AiProcessingScreen,
  SceneUnderstandingScreen,
  StoryPreviewScreen,
  VideoPlayerScreen,
  ActivityRecommendScreen,
  ActivityDetailScreen,
  FeedbackLoopScreen,
} from './src/screens';
import { AppProvider, useAppContext } from './src/context/AppContext';

// Screen metadata for dev quick-switch (only active when ?dev=true)
const SCREENS: ScreenMeta[] = [
  { id: 'splash', title: '1. Splash Screen', subtitle: 'Khởi động & linh vật', flow: 'flow1', workflowStep: 1, stepName: 'Splash' },
  { id: 'onboarding', title: '2. Onboarding', subtitle: '3 giá trị cốt lõi', flow: 'flow1', workflowStep: 1, stepName: 'Onboarding' },
  { id: 'dashboard', title: '3. Home Dashboard', subtitle: 'Trang chủ phụ huynh', flow: 'flow1', workflowStep: 1, stepName: 'Dashboard' },
  { id: 'profile', title: '4. Child Profile', subtitle: 'Hồ sơ trẻ & consent', flow: 'flow1', workflowStep: 1, stepName: 'Bước 1: Hồ sơ' },
  { id: 'capture', title: '5. Capture / Upload', subtitle: 'Thêm tranh vẽ của bé', flow: 'flow1', workflowStep: 1, stepName: 'Bước 1: Tranh vẽ' },
  { id: 'voice', title: '6. Voice Recording', subtitle: 'Kể chuyện bằng giọng nói', flow: 'flow1', workflowStep: 1, stepName: 'Bước 1: Lời kể' },
  { id: 'ai_processing', title: '7. AI Processing', subtitle: 'ASR + VLM Fusion (70%)', flow: 'flow2', workflowStep: 2, stepName: 'Bước 2: Xử lý AI' },
  { id: 'scene_understanding', title: '8. Scene Understanding', subtitle: 'Hiểu tranh (Gate A)', flow: 'flow2', workflowStep: 2, stepName: 'Bước 2: Gate A' },
  { id: 'story_preview', title: '9. Story Preview', subtitle: 'Phase 1: Art Animation', flow: 'flow2', workflowStep: 5, stepName: 'Bước 5: Hoạt hình' },
  { id: 'video_player', title: '10. Full Video Player', subtitle: 'Phase 2: Micro-Video', flow: 'flow2', workflowStep: 6, stepName: 'Bước 6: Video thật' },
  { id: 'activity_recommend', title: '11. Activity Recommendation', subtitle: 'Gợi ý Montessori (Gate B)', flow: 'flow2', workflowStep: 3, stepName: 'Bước 3: Gate B' },
  { id: 'activity_detail', title: '12. Activity Detail', subtitle: 'Phase 3: Off-Screen', flow: 'flow2', workflowStep: 7, stepName: 'Bước 7: Ngoài đời' },
  { id: 'feedback', title: '13. Feedback Loop', subtitle: 'Đánh giá & quan sát', flow: 'flow2', workflowStep: 8, stepName: 'Bước 8: Phản hồi' },
];

function MainAppContent() {
  const { width: windowWidth } = useWindowDimensions();
  const { currentScreen, navigate, toastMessage } = useAppContext();

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
      case 'splash':
        return <SplashScreen />;
      case 'onboarding':
        return <OnboardingScreen />;
      case 'dashboard':
        return <DashboardScreen />;
      case 'profile':
        return <ChildProfileScreen />;
      case 'capture':
        return <CaptureScreen />;
      case 'voice':
        return <VoiceScreen />;
      case 'ai_processing':
        return <AiProcessingScreen />;
      case 'scene_understanding':
        return <SceneUnderstandingScreen />;
      case 'story_preview':
        return <StoryPreviewScreen />;
      case 'video_player':
        return <VideoPlayerScreen />;
      case 'activity_recommend':
        return <ActivityRecommendScreen />;
      case 'activity_detail':
        return <ActivityDetailScreen />;
      case 'feedback':
        return <FeedbackLoopScreen />;
      default:
        return <SplashScreen />;
    }
  };

  return (
    <SafeAreaView style={styles.outerContainer}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />

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
              <Text style={styles.stepNumText}>{currentIndex + 1}/13</Text>
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
          {currentScreen !== 'splash' && (
            <View style={styles.mobileStatusBar}>
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
          <View style={styles.screenBody}>
            {renderScreen()}
          </View>

          {/* Virtual Home Bar */}
          <View style={styles.homeBarContainer}>
            <View style={styles.homeBarIndicator} />
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <AppProvider>
      <MainAppContent />
    </AppProvider>
  );
}

const styles = StyleSheet.create({
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
  homeBarContainer: {
    height: 18,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
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
