import {useEffect, useMemo, useReducer, useRef, useState} from 'react';
import {
  AccessibilityInfo,
  Animated,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import {FixtureFlowScreen} from '../../features/fixture/FixtureFlowScreen';
import {ParentAuthScreen} from '../../features/auth/ParentAuthScreen';
import {ParentHomeScreen} from '../../features/home/ParentHomeScreen';
import {ChildProfilesScreen} from '../../features/profile/ChildProfilesScreen';
import {ParentLessonLibraryScreen} from '../../features/lesson/ParentLessonLibraryScreen';
import {ParentLessonDetailScreen} from '../../features/lesson/ParentLessonDetailScreen';
import {ParentRunSetupScreen} from '../../features/capture/ParentRunSetupScreen';
import {ParentCaptureScreen} from '../../features/capture/ParentCaptureScreen';
import {VoiceCaptureScreen} from '../../features/capture/VoiceCaptureScreen';
import {UnderstandingReviewScreen} from '../../features/gate-a/UnderstandingReviewScreen';
import {ContextReviewScreen} from '../../features/gate-a/ContextReviewScreen';
import {ParentActivitySuggestionsScreen} from '../../features/activity-bridge/ParentActivitySuggestionsScreen';
import {StoryReviewScreen} from '../../features/gate-b/StoryReviewScreen';
import {GenerationStatusScreen} from '../../features/experience/GenerationStatusScreen';
import {VideoPlaybackScreen} from '../../features/experience/VideoPlaybackScreen';
import {RunCompletionScreen} from '../../features/experience/RunCompletionScreen';
import {ActivityRecommendationsScreen} from '../../features/activity-bridge/ActivityRecommendationsScreen';
import {RunHistoryScreen} from '../../features/history/RunHistoryScreen';
import {ProfileSharingScreen} from '../../features/sharing/ProfileSharingScreen';
import {QuotaSummaryScreen} from '../../features/quota/QuotaSummaryScreen';
import {LessonFeedbackScreen} from '../../features/feedback/LessonFeedbackScreen';
import {SessionFeedbackScreen} from '../../features/feedback/SessionFeedbackScreen';
import {VideoSuitabilityReviewScreen} from '../../features/feedback/VideoSuitabilityReviewScreen';
import {NotificationInboxScreen} from '../../features/notifications/NotificationInboxScreen';
import {ParentSettingsScreen} from '../../features/settings/ParentSettingsScreen';
import {InfoBanner} from '../../shared/ui/FeedbackState';
import {ParentIcon} from '../../shared/ui/ParentCard';
import {ParentBottomNavigation} from '../../shared/ui/ParentBottomNavigation';
import {sketchColors} from '../../shared/ui/SketchTokens';
import {
  createInitialParentState,
  parentMainRoutes,
  reduceParentNavigation,
  type ParentAppState,
  type ParentFlowProps,
  type ParentRoute,
} from './parentRoutes';

export function ParentNavigator(): React.JSX.Element {
  const [state, dispatch] = useReducer(reduceParentNavigation, undefined, createInitialParentState);
  const [reduceMotion, setReduceMotion] = useState(false);
  const transition = useRef(new Animated.Value(1)).current;
  const flowProps = useMemo<ParentFlowProps>(() => ({
    state,
    dispatch,
    onNavigate: (route) => dispatch({type: 'NAVIGATE', route}),
    onNotice: (message) => dispatch({type: 'SHOW_NOTICE', value: message}),
  }), [state]);
  const isAuth = state.route === 'login' || state.route === 'register' || state.route === 'recovery';
  const hasBottomNavigation = state.previewMode && parentMainRoutes.includes(state.route);

  useEffect(() => {
    let mounted = true;
    AccessibilityInfo.isReduceMotionEnabled().then((enabled) => {
      if (mounted) setReduceMotion(enabled);
    }).catch(() => undefined);
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduceMotion);
    return () => {
      mounted = false;
      subscription.remove();
    };
  }, []);

  useEffect(() => {
    transition.setValue(reduceMotion ? 1 : 0.97);
    Animated.timing(transition, {
      toValue: 1,
      duration: reduceMotion ? 0 : 180,
      useNativeDriver: true,
    }).start();
  }, [reduceMotion, state.route, transition]);

  useEffect(() => {
    if (!state.notice) return undefined;
    const timer = setTimeout(() => dispatch({type: 'CLEAR_NOTICE'}), 5200);
    return () => clearTimeout(timer);
  }, [state.notice]);

  const navigate = (route: ParentRoute): void => dispatch({type: 'NAVIGATE', route});
  const screen = renderScreen(state, flowProps, dispatch, navigate);
  const scrollRoutes: readonly ParentRoute[] = [
    'lesson-detail', 'run-setup', 'capture', 'voice', 'understanding', 'context', 'activity-suggestions', 'story-review',
    'generation', 'video-player', 'video-review', 'activities', 'completion', 'session-feedback', 'history', 'sharing', 'quota',
    'feedback', 'notifications', 'settings',
  ];
  const scrollableScreen = scrollRoutes.includes(state.route)
    ? <ScrollView contentContainerStyle={styles.routeContent} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>{screen}</ScrollView>
    : screen;

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content"/>
      {!isAuth ? (
        <View style={styles.topBar}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={hasBottomNavigation ? 'Về trang chủ' : 'Quay lại'}
            onPress={() => hasBottomNavigation ? navigate('home') : dispatch({type: 'BACK'})}
            style={({pressed}) => [styles.backButton, pressed ? styles.pressed : undefined]}>
            <ParentIcon name={hasBottomNavigation ? 'home' : 'back'} size={22}/>
          </Pressable>
          <View style={styles.brand}>
            <View style={styles.brandMark}><ParentIcon name="spark" color={sketchColors.white} size={17}/></View>
            <View><Text style={styles.brandName}>Sketch2Life</Text><Text style={styles.brandSubtitle}>Không gian gia đình</Text></View>
          </View>
          {hasBottomNavigation ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Mở thông báo"
              onPress={() => navigate('notifications')}
              style={({pressed}) => [styles.noticeButton, pressed ? styles.pressed : undefined]}>
              <ParentIcon name="notifications" size={19}/>
            </Pressable>
          ) : <View style={styles.noticeSpacer}/>}
        </View>
      ) : null}
      {state.notice ? <View style={styles.notice}><InfoBanner title="Thông tin" body={state.notice}/></View> : null}
      <Animated.View style={[styles.screen, {opacity: transition, transform: [{translateY: transition.interpolate({inputRange: [0.97, 1], outputRange: [5, 0]})}]}]}>
        {scrollableScreen}
      </Animated.View>
      {hasBottomNavigation ? <ParentBottomNavigation activeRoute={state.route} onNavigate={navigate}/> : null}
    </SafeAreaView>
  );
}

function renderScreen(
  state: ParentAppState,
  props: ParentFlowProps,
  dispatch: ParentFlowProps['dispatch'],
  navigate: (route: ParentRoute) => void,
): React.JSX.Element {
  switch (state.route) {
    case 'login':
    case 'register':
    case 'recovery':
      return <ParentAuthScreen mode={state.route} onModeChange={(mode) => navigate(mode)} onEnterPreview={() => dispatch({type: 'ENTER_PREVIEW'})} onNotice={props.onNotice}/>;
    case 'home': return <ParentHomeScreen {...props}/>;
    case 'profiles': return <ChildProfilesScreen {...props}/>;
    case 'lesson-library': return <ParentLessonLibraryScreen {...props}/>;
    case 'lesson-detail': return <ParentLessonDetailScreen {...props}/>;
    case 'run-setup': return <ParentRunSetupScreen {...props}/>;
    case 'capture': return <ParentCaptureScreen {...props}/>;
    case 'voice': return <VoiceCaptureScreen {...props}/>;
    case 'understanding': return <UnderstandingReviewScreen {...props}/>;
    case 'context': return <ContextReviewScreen {...props}/>;
    case 'activity-suggestions': return <ParentActivitySuggestionsScreen {...props}/>;
    case 'story-review': return <StoryReviewScreen {...props}/>;
    case 'generation': return <GenerationStatusScreen {...props}/>;
    case 'video-player': return <VideoPlaybackScreen {...props}/>;
    case 'video-review': return <VideoSuitabilityReviewScreen {...props}/>;
    case 'activities': return <ActivityRecommendationsScreen {...props}/>;
    case 'completion': return <RunCompletionScreen {...props}/>;
    case 'session-feedback': return <SessionFeedbackScreen {...props}/>;
    case 'history': return <RunHistoryScreen {...props}/>;
    case 'sharing': return <ProfileSharingScreen {...props}/>;
    case 'quota': return <QuotaSummaryScreen {...props}/>;
    case 'feedback': return <LessonFeedbackScreen {...props}/>;
    case 'notifications': return <NotificationInboxScreen {...props}/>;
    case 'settings': return <ParentSettingsScreen {...props}/>;
    case 'fixture': return __DEV__ ? <FixtureFlowScreen/> : <ParentHomeScreen {...props}/>;
    default: return assertNever(state.route);
  }
}

function assertNever(value: never): never {
  throw new Error(`Unhandled Parent route: ${String(value)}`);
}

const styles = StyleSheet.create({
  safeArea: {flex: 1, backgroundColor: sketchColors.canvas},
  topBar: {minHeight: 64, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12, borderBottomWidth: 1, borderColor: sketchColors.line, backgroundColor: sketchColors.surface},
  backButton: {width: 44, height: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 15, backgroundColor: sketchColors.surfaceMuted},
  pressed: {opacity: 0.72},
  brand: {flex: 1, flexDirection: 'row', alignItems: 'center', gap: 9},
  brandMark: {width: 35, height: 35, alignItems: 'center', justifyContent: 'center', borderRadius: 13, backgroundColor: sketchColors.green},
  brandName: {color: sketchColors.ink, fontSize: 13, fontWeight: '900'},
  brandSubtitle: {color: sketchColors.muted, fontSize: 9, marginTop: 2},
  noticeButton: {width: 44, height: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 15},
  noticeSpacer: {width: 44, height: 44},
  notice: {paddingHorizontal: 12, paddingTop: 8},
  screen: {flex: 1, minHeight: 0},
  routeContent: {flexGrow: 1, paddingBottom: 14},
});
