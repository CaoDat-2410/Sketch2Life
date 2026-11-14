import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Path, Rect } from 'react-native-svg';
import type {
  Activity,
  LessonDetail,
  LessonInvitation,
  LessonSummary,
  ParentAudioTranscription,
  ParentCandidate,
  ParentGroupInvitation,
  ParentProfileViewV1,
  ParentStoryRunV1,
  ParentUser,
  SuggestedActivity,
  StoryDraft,
} from '../domain/types';
import type { ParentCapabilityState } from '../application/ports/ParentCapabilityPorts';
import { createUnavailableParentConsentState } from './navigation/workflowTypes';
import { Card, Notice, PrimaryButton, ScreenFrame, SecondaryButton, palette } from './components/ui';
import { AccountScreen } from './screens/AccountScreen';
import { ActivityScreen } from './screens/ActivityScreen';
import { AuthScreen } from './screens/AuthScreen';
import { ContextScreen } from './screens/ContextScreen';
import { DrawingGuideScreen } from './screens/DrawingGuideScreen';
import { HandoffScreen } from './screens/HandoffScreen';
import { HomeScreen } from './screens/HomeScreen';
import { LessonGalleryScreen } from './screens/LessonGalleryScreen';
import { LessonHistoryScreen } from './screens/LessonHistoryScreen';
import { LessonPickerScreen } from './screens/LessonPickerScreen';
import { NotificationsScreen } from './screens/NotificationsScreen';
import { ProfileFormScreen } from './screens/ProfileFormScreen';
import { ProfileScreen } from './screens/ProfileScreen';
import { ProfileSharingScreen } from './screens/ProfileSharingScreen';
import { ParentBottomBar } from './screens/ParentBottomBar';
import { QuotaScreen } from './screens/QuotaScreen';
import { SettingsScreen } from './screens/SettingsScreen';
import { StoryHistoryScreen } from './screens/StoryHistoryScreen';
import { StoryScreen } from './screens/StoryScreen';
import { TopicScreen } from './screens/TopicScreen';
import { TranscriptReviewScreen } from './screens/TranscriptReviewScreen';
import { UnderstandingScreen } from './screens/UnderstandingScreen';

const previewTabs = [
  { id: 'auth', label: 'Đăng nhập' },
  { id: 'account', label: 'Tài khoản' },
  { id: 'settings', label: 'Cài đặt' },
  { id: 'home', label: 'Trang chủ' },
  { id: 'home-new', label: 'Trang chủ · buổi mới' },
  { id: 'profiles', label: 'Gia đình' },
  { id: 'family-unselected', label: 'Gia đình · chưa chọn' },
  { id: 'profile-create', label: 'Tạo hồ sơ' },
  { id: 'profile-edit', label: 'Sửa hồ sơ' },
  { id: 'sharing', label: 'Chia sẻ' },
  { id: 'gallery', label: 'Thư viện' },
  { id: 'picker', label: 'Chọn bài' },
  { id: 'topic', label: 'Chủ đề' },
  { id: 'guide', label: 'Gợi ý vẽ' },
  { id: 'capture', label: 'Chụp tranh' },
  { id: 'capture-denied', label: 'Chụp · từ chối quyền' },
  { id: 'capture-selected', label: 'Chụp · đã chọn ảnh' },
  { id: 'transcript', label: 'Bản ghi' },
  { id: 'understanding', label: 'Chủ thể' },
  { id: 'context-before', label: 'Ngữ cảnh trước' },
  { id: 'context-after', label: 'Ngữ cảnh sau' },
  { id: 'activity', label: 'Hoạt động' },
  { id: 'story', label: 'Kịch bản' },
  { id: 'handoff', label: 'Trạng thái' },
  { id: 'history', label: 'Lịch sử buổi' },
  { id: 'lesson-history', label: 'Bài đã học' },
  { id: 'quota', label: 'Lượt dùng' },
  { id: 'notifications', label: 'Thông báo' },
  { id: 'bottom-bar', label: 'Thanh điều hướng' },
] as const;

type PreviewId = (typeof previewTabs)[number]['id'];

const previewActivity: Activity = {
  title: 'Mô phỏng · quan sát chiếc lá',
  objective: 'Mô phỏng · nhận biết hình dáng và màu sắc.',
  materials_text: 'Mô phỏng · giấy và bút màu.',
  preparation_text: 'Mô phỏng · chuẩn bị giấy trên bàn.',
  instructions_text: 'Mô phỏng · cùng bé quan sát chiếc lá.',
  observation_notes: 'Mô phỏng · để bé tự mô tả điều nhìn thấy.',
  safety_notes: 'Mô phỏng · người lớn ở cạnh bé.',
  activity_kind: 'indoor',
};

const previewSuggestedActivity: SuggestedActivity = {
  ...previewActivity,
  source: 'PINNED_LESSON',
  source_lesson_id: 'preview-lesson-01',
  source_lesson_title: 'Mô phỏng · khu vườn nhỏ',
  source_lesson_version_id: 'Mô phỏng · phiên bản 01',
  source_content_sha256: 'Mô phỏng · không phải mã băm thật',
  source_activity_index: 0,
  match_reason: 'Mô phỏng · minh họa hoạt động chỉ đọc.',
};

const previewLessonSummary: LessonSummary = {
  contract: 'ParentLessonSummaryV1',
  lesson_id: 'preview-lesson-01',
  version_id: 'Mô phỏng · phiên bản 01',
  title: 'Mô phỏng · khu vườn nhỏ',
  topic: 'Mô phỏng · cây cối',
  target_age_band_ref: 'preview-only',
  target_age_band_version: 1,
  activity_count: 1,
  access_source: 'PUBLIC',
};

const previewLessons: LessonSummary[] = [
  previewLessonSummary,
  {
    ...previewLessonSummary,
    lesson_id: 'preview-lesson-02',
    version_id: 'Mô phỏng · phiên bản 02',
    title: 'Mô phỏng · chăm sóc hạt giống',
  },
];

const previewLesson: LessonDetail = {
  ...previewLessonSummary,
  contract: 'ParentLessonDetailV1',
  version_no: 1,
  content_sha256: 'Mô phỏng · không phải mã băm thật',
  objectives: ['Mô phỏng · quan sát thiên nhiên quanh bé.'],
  drawing_subject: 'Mô phỏng · một chiếc lá',
  drawing_steps_text: [
    'Mô phỏng · vẽ đường gân chính của lá.',
    'Mô phỏng · thêm các đường gân nhỏ.',
    'Mô phỏng · vẽ viền lá quanh các đường gân.',
    'Mô phỏng · tô màu lá theo ý thích.',
  ].join('\n'),
  subject_learning_notes: 'Mô phỏng · cùng bé quan sát hình dáng chiếc lá.',
  script_direction: null,
  script_following_allowed: false,
  access_expires_at: null,
  activities: [previewActivity],
};

const previewLessonInvitations: LessonInvitation[] = [
  {
    contract: 'LessonAccessGrantV1',
    access_grant_id: 'preview-access-01',
    lesson_id: previewLesson.lesson_id,
    version_id: previewLesson.version_id,
    audience_kind: 'PARENT',
    capability: 'VIEW',
    state: 'INVITED',
    expires_at: null,
    revision: 1,
  },
];

const previewGroupInvitations: ParentGroupInvitation[] = [
  {
    contract: 'ParentGroupMembershipV1',
    membership_id: 'preview-membership-01',
    parent_group_id: 'preview-group-01',
    state: 'INVITED',
    invited_at: '2026-11-14T00:00:00.000Z',
    expires_at: null,
    revision: 1,
  },
];

const previewProfile: ParentProfileViewV1 = {
  profile_id: 'preview-profile-01',
  revision_no: 1,
  revision_hash: 'Mô phỏng · không phải mã băm thật',
  state: 'ACTIVE',
  display_name: 'Mô phỏng · hồ sơ khu vườn',
  age_months: 72,
  age_band_ref: null,
  age_band_version: null,
  interests_summary: 'Mô phỏng · cây cối và màu sắc.',
  data_origin: 'PREVIEW',
};

const previewUser: ParentUser = {
  subject: 'preview-parent-01',
  email: 'phu-huynh@example.invalid',
  role: 'parent',
};

const previewCandidate: ParentCandidate = {
  candidate_subject: 'Mô phỏng · một con bướm',
  visible_features: ['Mô phỏng · đôi cánh đối xứng', 'Mô phỏng · thân bướm ở giữa'],
  confidence: 0.86,
  adult_confirmation_required: true,
  decision: 'PENDING',
};

const previewContextRun: ParentStoryRunV1 = {
  run_id: 'preview-run-01',
  run_state: 'ACTIVE',
  parent_profile_id: previewProfile.profile_id,
  profile_revision_ref: 'preview-profile-revision-01',
  context_revision: 1,
  context_snapshot: {
    age_months: previewProfile.age_months,
    interests_summary: previewProfile.interests_summary,
    topic: 'Mô phỏng · khu vườn nhỏ',
    adult_confirmed_idea: 'Mô phỏng · quan sát lá và bướm.',
  },
  context_snapshot_sha256: 'Mô phỏng · không phải mã băm thật',
  lesson_pin_snapshot: {
    lesson_id: previewLesson.lesson_id,
    version_id: previewLesson.version_id,
    content_sha256: previewLesson.content_sha256,
    title: previewLesson.title,
    topic: previewLesson.topic,
    drawing_subject: previewLesson.drawing_subject,
    subject_learning_notes: previewLesson.subject_learning_notes,
    script_direction: null,
    script_following_allowed: false,
    activities: previewLesson.activities,
  },
  current_input_revision: 1,
  understanding_revision: 1,
  subject_label: 'Mô phỏng · một con bướm',
  candidate: previewCandidate,
};

const previewStory: StoryDraft = {
  schema_version: 'sketch2life.story-revision.v1',
  language: 'vi',
  revisionId: 'preview-story-revision-01',
  revisionNo: 1,
  sha256: 'Mô phỏng · không phải mã băm thật',
  title: 'Mô phỏng · hành trình chiếc lá',
  story: {
    opening: 'Mô phỏng · chiếc lá khẽ rời cành.',
    middle: 'Mô phỏng · chiếc lá gặp một người bạn trong vườn.',
    ending: 'Mô phỏng · chiếc lá tìm được chỗ nghỉ ngơi.',
  },
  duration_ms: 40_000,
  scenes: [
    { scene_index: 1, title: 'Mô phỏng · khởi đầu', action: 'Mô phỏng · lá đung đưa.', narration: 'Mô phỏng · gió thổi nhẹ.', start_ms: 0, duration_ms: 20_000 },
    { scene_index: 2, title: 'Mô phỏng · khám phá', action: 'Mô phỏng · lá gặp bạn mới.', narration: 'Mô phỏng · cùng nhau tìm đường.', start_ms: 20_000, duration_ms: 20_000 },
  ],
};

const previewTranscript: ParentAudioTranscription | null = null;

function ignoreAction(): void {}

type CapturePreviewState = 'empty' | 'camera-denied' | 'photo-selected';

function CapturePreviewScreen({ state }: { state: CapturePreviewState }): React.JSX.Element {
  const hasPhoto = state === 'photo-selected';
  const cameraDenied = state === 'camera-denied';

  return (
    <ScreenFrame title="Chụp hoặc chọn tranh" subtitle="Ảnh tranh giấy là bắt buộc." step="3 / 7" onBack={ignoreAction}>
      <Card style={styles.capturePreviewCard}>
        <Text style={styles.capturePreviewRequired}>BẮT BUỘC</Text>
        {cameraDenied ? <Notice text="Camera chưa được cấp quyền. Vẫn có thể chọn tranh từ thư viện." tone="error" /> : null}
        <PrimaryButton label={hasPhoto ? 'Chụp lại' : 'Mở camera'} onPress={ignoreAction} />
        <SecondaryButton label="Chọn từ thư viện ảnh" onPress={ignoreAction} />
        <View style={styles.capturePreviewImageFrame}>
          <CapturePreviewDrawing selected={hasPhoto} />
        </View>
        {hasPhoto ? (
          <Text style={styles.capturePreviewSimulationLabel}>Ảnh minh họa mô phỏng · không phải tranh thật</Text>
        ) : (
          <Text style={styles.capturePreviewEmptyText}>Ảnh tranh giấy sẽ hiện ở đây</Text>
        )}
      </Card>
      <Notice text="Chỉ tiếp tục sau khi có một ảnh tranh hợp lệ. Chưa mở buổi học trước ảnh." />
      <PrimaryButton label="Tiếp tục sau khi chọn ảnh" disabled={!hasPhoto} onPress={ignoreAction} />
    </ScreenFrame>
  );
}

function CapturePreviewDrawing({ selected }: { selected: boolean }): React.JSX.Element {
  return (
    <Svg width="100%" height="100%" viewBox="0 0 280 190" preserveAspectRatio="xMidYMid meet" accessible={false}>
      <Rect x="1" y="1" width="278" height="188" rx="15" fill="#FFFEF8" />
      <Circle cx="220" cy="42" r="18" fill="#FFF0B8" stroke="#493A2F" strokeWidth="3.5" />
      <Path d="M22 153c30-11 57-9 83 0 25-12 55-10 82 0 27-11 48-10 71 0" fill="none" stroke="#234D2A" strokeWidth="5" strokeLinecap="round" />
      {selected ? (
        <>
          <Path d="M111 148V95m1 24c-20-8-27-22-22-37 18 3 28 17 22 37Zm2-13c20-11 24-25 18-39-17 6-25 22-18 39Z" fill="#DDF1D8" stroke="#493A2F" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          <Path d="M167 93c-13-16-31-10-30 5 1 9 12 17 30 26 18-9 29-17 30-26 1-15-17-21-30-5Z" fill="#F7D7CF" stroke="#493A2F" strokeWidth="3.5" strokeLinejoin="round" />
          <Path d="M167 94v28m-9-22-8-8m26 8 8-8" fill="none" stroke="#493A2F" strokeWidth="3" strokeLinecap="round" />
        </>
      ) : (
        <>
          <Path d="M101 151V91m1 27c-19-9-26-21-22-36 17 3 27 16 22 36Zm2-15c18-10 22-24 17-37-16 6-23 20-17 37Z" fill="#DDF1D8" stroke="#493A2F" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          <Path d="M38 73c8-12 20-13 28 0m-31 8h35m120 40c8-9 18-9 26 0" fill="none" stroke="#9B5A19" strokeWidth="4.5" strokeLinecap="round" />
        </>
      )}
    </Svg>
  );
}

function pendingPreviewAsync(): Promise<void> {
  // Preview actions are inert; never resolve them as a simulated success.
  return new Promise<void>((resolve) => { void resolve; });
}

function pendingPreviewProfile(): Promise<ParentProfileViewV1> {
  // Profile writes are not performed by the preview harness.
  return new Promise<ParentProfileViewV1>((resolve) => { void resolve; });
}

function unavailable(capability: ParentCapabilityState['capability']): ParentCapabilityState {
  return { capability, state: 'unavailable', reason: 'route-not-in-be-handoff' };
}

export function ParentVisualPreviewHarness(): React.JSX.Element {
  const [activePreview, setActivePreview] = useState<PreviewId>('auth');
  const previewScreens: Record<PreviewId, React.JSX.Element> = {
    auth: <AuthScreen
      busy={false}
      error=""
      googleAndroidClientId=""
      googleWebClientId=""
      onSignIn={pendingPreviewAsync}
      onSignUp={pendingPreviewAsync}
      onReset={pendingPreviewAsync}
      onGoogleSignIn={pendingPreviewAsync}
    />,
    account: <AccountScreen user={previewUser} busy={false} error="" onChangePassword={pendingPreviewAsync} onResetPassword={pendingPreviewAsync} onSignOut={ignoreAction} onBack={ignoreAction} />,
    settings: <SettingsScreen
      sketchGuideEnabled={false}
      onSketchGuideEnabled={ignoreAction}
      onOpenAccount={ignoreAction}
      onOpenProfiles={ignoreAction}
      onOpenNotifications={ignoreAction}
      onOpenQuota={ignoreAction}
      onOpenHistory={ignoreAction}
      onOpenSharing={ignoreAction}
      onOpenDeliveredLessons={ignoreAction}
      onBack={ignoreAction}
    />,
    home: <HomeScreen
      profiles={[]}
      selectedProfile={null}
      activeRun={previewContextRun}
      error=""
      onStart={ignoreAction}
      onManageProfiles={ignoreAction}
      onOpenLessons={ignoreAction}
      onOpenAccount={ignoreAction}
      onOpenSettings={ignoreAction}
      onOpenNotifications={ignoreAction}
      onOpenQuota={ignoreAction}
      onOpenHistory={ignoreAction}
      onOpenSharing={ignoreAction}
      onOpenDeliveredLessons={ignoreAction}
      onResumeRun={ignoreAction}
      onSignOut={ignoreAction}
    />,
    'home-new': <HomeScreen
      profiles={[previewProfile]}
      selectedProfile={previewProfile}
      activeRun={null}
      error=""
      onStart={ignoreAction}
      onManageProfiles={ignoreAction}
      onOpenLessons={ignoreAction}
      onOpenAccount={ignoreAction}
      onOpenSettings={ignoreAction}
      onOpenNotifications={ignoreAction}
      onOpenQuota={ignoreAction}
      onOpenHistory={ignoreAction}
      onOpenSharing={ignoreAction}
      onOpenDeliveredLessons={ignoreAction}
      onResumeRun={ignoreAction}
      onSignOut={ignoreAction}
    />,
    profiles: <ProfileScreen
      profiles={[previewProfile]}
      pendingDeletions={[]}
      selectedProfileId={previewProfile.profile_id}
      activeRun={null}
      error=""
      busy=""
      pendingDeletionLoadingId=""
      consentState={createUnavailableParentConsentState('route-not-in-be-handoff')}
      onSelect={ignoreAction}
      onCreate={ignoreAction}
      onEdit={ignoreAction}
      onRequestDeletion={ignoreAction}
      onRefreshPendingDeletion={ignoreAction}
      onContinue={ignoreAction}
      onResumeRun={ignoreAction}
      onBackHome={ignoreAction}
    />,
    'family-unselected': <ProfileScreen
      profiles={[previewProfile]}
      pendingDeletions={[]}
      selectedProfileId=""
      activeRun={null}
      error=""
      busy=""
      pendingDeletionLoadingId=""
      consentState={createUnavailableParentConsentState('route-not-in-be-handoff')}
      onSelect={ignoreAction}
      onCreate={ignoreAction}
      onEdit={ignoreAction}
      onRequestDeletion={ignoreAction}
      onRefreshPendingDeletion={ignoreAction}
      onContinue={ignoreAction}
      onResumeRun={ignoreAction}
      onBackHome={ignoreAction}
    />,
    'profile-create': <ProfileFormScreen mode="create" profile={null} busy={false} error="" fieldErrors={{}} onCreate={pendingPreviewProfile} onUpdate={pendingPreviewProfile} onBack={ignoreAction} />,
    'profile-edit': <ProfileFormScreen mode="edit" profile={previewProfile} busy={false} error="" fieldErrors={{}} onCreate={pendingPreviewProfile} onUpdate={pendingPreviewProfile} onBack={ignoreAction} />,
    sharing: <ProfileSharingScreen
      profile={previewProfile}
      grants={[]}
      loading={false}
      error=""
      capability={unavailable('profile-sharing')}
      inviteState={{ state: 'unavailable', reason: 'route-not-in-be-handoff' }}
      revokeState={{ state: 'unavailable', reason: 'route-not-in-be-handoff' }}
      onInvite={async () => ({ state: 'unavailable', reason: 'route-not-in-be-handoff' })}
      onRevoke={() => ({ state: 'unavailable', reason: 'route-not-in-be-handoff' })}
      onBack={ignoreAction}
    />,
    gallery: <LessonGalleryScreen
      lessons={previewLessons}
      selectedLesson={previewLesson}
      selectedPresetVersionId={null}
      lessonInvitations={previewLessonInvitations}
      groupInvitations={previewGroupInvitations}
      loading={false}
      loadingId=""
      error=""
      onOpenLesson={ignoreAction}
      onUseLesson={ignoreAction}
      onAcceptLessonInvitation={ignoreAction}
      onDeclineLessonInvitation={ignoreAction}
      onAcceptGroupInvitation={ignoreAction}
      onBack={ignoreAction}
    />,
    picker: <LessonPickerScreen
      lessons={previewLessons}
      selectedId=""
      loading={false}
      loadingId=""
      error=""
      onSelect={ignoreAction}
      onClear={ignoreAction}
      onBack={ignoreAction}
    />,
    topic: <TopicScreen
      topic="Mô phỏng · khu vườn nhỏ"
      idea="Mô phỏng · quan sát lá và bướm."
      audio={null}
      guideEnabled={false}
      guideBase64=""
      guideBusy={false}
      guideError=""
      lesson={null}
      stepLabel="2 / 7"
      canContinue={false}
      error=""
      onTopic={ignoreAction}
      onIdea={ignoreAction}
      onAudio={ignoreAction}
      onGuideToggle={ignoreAction}
      onGenerateGuide={ignoreAction}
      onOpenLessons={ignoreAction}
      onContinue={ignoreAction}
      onBack={ignoreAction}
    />,
    guide: <DrawingGuideScreen lesson={previewLesson} stepLabel="3 / 7" currentIndex={1} onIndexChange={ignoreAction} onContinue={ignoreAction} onBack={ignoreAction} />,
    capture: <CapturePreviewScreen state="empty" />,
    'capture-denied': <CapturePreviewScreen state="camera-denied" />,
    'capture-selected': <CapturePreviewScreen state="photo-selected" />,
    transcript: <TranscriptReviewScreen stepLabel="5 / 7" transcript={previewTranscript} text="" busy={false} error="" onText={ignoreAction} onConfirm={ignoreAction} onContinueWithoutAudio={ignoreAction} onBack={ignoreAction} />,
    understanding: <UnderstandingScreen candidate={previewCandidate} stepLabel="5 / 7" subject="Mô phỏng · một con bướm" busy={false} error="" onSubject={ignoreAction} onConfirm={ignoreAction} onBack={ignoreAction} />,
    'context-before': <ContextScreen profile={previewProfile} contextRun={null} stepLabel="3 / 7" busy={false} confirmed={false} error="" onRetryCreate={ignoreAction} onConfirm={ignoreAction} onContinue={ignoreAction} onBack={ignoreAction} />,
    'context-after': <ContextScreen profile={previewProfile} contextRun={previewContextRun} stepLabel="5 / 7" busy={false} confirmed={false} error="" onRetryCreate={ignoreAction} onConfirm={ignoreAction} onContinue={ignoreAction} onBack={ignoreAction} />,
    activity: <ActivityScreen stepLabel="6 / 7" activities={[previewSuggestedActivity]} source="PINNED_LESSON" busy={false} requested={false} error="" onSuggest={ignoreAction} onSkip={ignoreAction} onBack={ignoreAction} />,
    story: <StoryScreen
      videoCapability={unavailable('video')}
      jobStage={{ state: 'idle', stage: 'idle' }}
      stepLabel="7 / 7"
      story={previewStory}
      rewriteCount={0}
      rewriteInstruction=""
      busy={false}
      attempted={false}
      canConfirm={false}
      error=""
      confirmed={false}
      onRewriteInstruction={ignoreAction}
      onGenerate={ignoreAction}
      onRetry={ignoreAction}
      onRewrite={ignoreAction}
      onConfirm={ignoreAction}
      onBack={ignoreAction}
    />,
    handoff: <HandoffScreen storyTitle="Mô phỏng · kịch bản đã xác nhận" events={[]} videoCapability={unavailable('video')} jobStage={{ state: 'unavailable', stage: 'unavailable' }} onResumeActiveRun={ignoreAction} />,
    history: <StoryHistoryScreen capability={unavailable('run-history')} runs={[]} loading={false} error="" hasMore={false} onLoad={ignoreAction} onLoadMore={ignoreAction} onCancel={ignoreAction} onDelete={ignoreAction} onBack={ignoreAction} />,
    'lesson-history': <LessonHistoryScreen capability={unavailable('lesson-history')} deliveries={[]} loading={false} error="" hasMore={false} onLoad={ignoreAction} onLoadMore={ignoreAction} onSubmitFeedback={pendingPreviewAsync} onBack={ignoreAction} />,
    quota: <QuotaScreen capability={unavailable('quota')} quota={null} loading={false} error="" onLoad={ignoreAction} onBack={ignoreAction} />,
    notifications: <NotificationsScreen capability={unavailable('notifications')} items={[]} loading={false} error="" hasMore={false} onLoad={ignoreAction} onLoadMore={ignoreAction} onMarkRead={ignoreAction} onBack={ignoreAction} />,
    'bottom-bar': <View style={styles.bottomBarPreview}><ParentBottomBar activeTab="home" onNavigate={ignoreAction} onStart={ignoreAction} startLabel="Bắt đầu" /></View>,
  };

  return (
    <View style={styles.container}>
      <View style={styles.markerWrap}>
        <Text accessibilityRole="header" numberOfLines={1} allowFontScaling={false} style={styles.marker}>BẢN XEM TRƯỚC · DỮ LIỆU MÔ PHỎNG</Text>
      </View>
      <ScrollView
        horizontal
        style={styles.tabStrip}
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.tabList}
        accessibilityRole="tablist"
      >
        {previewTabs.map((tab) => {
          const selected = activePreview === tab.id;
          return (
            <Pressable
              key={tab.id}
              accessibilityRole="tab"
              accessibilityLabel={tab.label}
              accessibilityState={{ selected }}
              onPress={() => setActivePreview(tab.id)}
              style={({ pressed }) => [styles.tab, selected && styles.selectedTab, pressed && styles.pressedTab]}
            >
              <Text numberOfLines={1} style={[styles.tabText, selected && styles.selectedTabText]}>{tab.label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>
      <View style={styles.screenContent}>{previewScreens[activePreview]}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, minHeight: 0, backgroundColor: palette.background },
  markerWrap: { flexGrow: 0, flexShrink: 0, paddingHorizontal: 14, paddingTop: 4, paddingBottom: 4, backgroundColor: palette.background },
  marker: { color: palette.ink, fontSize: 9, lineHeight: 12, fontWeight: '900', letterSpacing: 0.3, flexShrink: 1 },
  tabStrip: { height: 56, maxHeight: 56, flexGrow: 0, flexShrink: 0 },
  tabList: { minHeight: 56, maxHeight: 56, flexDirection: 'row', alignItems: 'center', gap: 8, paddingHorizontal: 12 },
  tab: { minHeight: 44, justifyContent: 'center', borderWidth: 1.5, borderColor: palette.outline, borderRadius: 999, paddingHorizontal: 12, backgroundColor: palette.white },
  selectedTab: { borderWidth: 2, backgroundColor: palette.butter },
  pressedTab: { opacity: 0.78 },
  tabText: { color: palette.muted, fontSize: 10, lineHeight: 14, fontWeight: '700' },
  selectedTabText: { color: palette.ink },
  screenContent: { flex: 1, minHeight: 0, backgroundColor: palette.background },
  bottomBarPreview: { flex: 1, justifyContent: 'flex-end', backgroundColor: palette.background },
  capturePreviewCard: { backgroundColor: palette.white, gap: 12, minWidth: 0 },
  capturePreviewRequired: { alignSelf: 'flex-start', minHeight: 24, textAlignVertical: 'center', color: palette.ink, fontSize: 9, lineHeight: 13, fontWeight: '800', borderWidth: 1, borderColor: palette.outline, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 4 },
  capturePreviewImageFrame: { width: '100%', aspectRatio: 280 / 190, minHeight: 190, borderRadius: 15, backgroundColor: palette.background, borderWidth: 1.5, borderColor: palette.outline, alignItems: 'center', justifyContent: 'center', overflow: 'hidden' },
  capturePreviewEmptyText: { color: palette.muted, fontSize: 12, lineHeight: 17, textAlign: 'center', minWidth: 0, flexShrink: 1 },
  capturePreviewSimulationLabel: { color: palette.muted, fontSize: 10, lineHeight: 14, textAlign: 'center', minWidth: 0, flexShrink: 1 },
});
