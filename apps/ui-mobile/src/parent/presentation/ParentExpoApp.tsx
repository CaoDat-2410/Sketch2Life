import React from 'react';
import { ActivityIndicator, StatusBar, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import type { ParentApplicationModule } from '../application/ports/ParentApplicationModule';
import { rewritesLeft } from '../application/parentPhaseB';
import type { ParentMainTab } from './screens/ParentBottomBar';
import type { AppStep } from './navigation/workflowTypes';
import {
  canAnalyzeDrawing,
  canBeginContextStep,
  canConfirmDisplayedStory,
  lessonVersionPinFromDetail,
  selectProfileById,
} from './navigation/parentFlowV1';
import { useParentController } from './navigation/useParentController';
import { useParentPlatformController } from './navigation/useParentPlatformController';
import { AccountScreen } from './screens/AccountScreen';
import { ActivityScreen } from './screens/ActivityScreen';
import { AuthScreen } from './screens/AuthScreen';
import { CaptureScreen } from './screens/CaptureScreen';
import { ContextScreen } from './screens/ContextScreen';
import { DrawingSubjectScreen } from './screens/DrawingSubjectScreen';
import { DrawingGuideScreen } from './screens/DrawingGuideScreen';
import { HandoffScreen } from './screens/HandoffScreen';
import { HomeScreen } from './screens/HomeScreen';
import { IdeaScreen } from './screens/IdeaScreen';
import { TranscriptReviewScreen } from './screens/TranscriptReviewScreen';
import { VideoScreen } from './screens/VideoScreen';
import { LessonGalleryScreen } from './screens/LessonGalleryScreen';
import { LessonHistoryScreen } from './screens/LessonHistoryScreen';
import { LessonPickerScreen } from './screens/LessonPickerScreen';
import { LearningPathScreen } from './screens/LearningPathScreen';
import { NotificationsScreen } from './screens/NotificationsScreen';
import { ParentBottomBar } from './screens/ParentBottomBar';
import { ParentVisualPreviewHarness } from './ParentVisualPreviewHarness';
import { ProfileFormScreen } from './screens/ProfileFormScreen';
import { ProfileScreen } from './screens/ProfileScreen';
import { SettingsScreen } from './screens/SettingsScreen';
import { ProfileSharingScreen } from './screens/ProfileSharingScreen';
import { StoryScreen } from './screens/StoryScreen';
import { StoryHistoryScreen } from './screens/StoryHistoryScreen';
import { QuotaScreen } from './screens/QuotaScreen';
import { TopicScreen } from './screens/TopicScreen';
import { UnderstandingScreen } from './screens/UnderstandingScreen';
import { Notice, palette, ScreenFrame } from './components/ui';

type Props = { application: ParentApplicationModule };

export default function ParentExpoApp({ application }: Props): React.JSX.Element {
  const visualPreviewEnabled = __DEV__ && process.env.EXPO_PUBLIC_FEAT081_VISUAL_PREVIEW === 'true';

  return <>
    <StatusBar barStyle="dark-content" backgroundColor={palette.background} />
    {visualPreviewEnabled ? <ParentVisualPreviewHarness /> : <ParentExpoAppContent application={application} />}
  </>;
}

function ParentExpoAppContent({ application }: Props): React.JSX.Element {
  const parent = useParentController(application);
  const platform = useParentPlatformController(application);
  const selectedProfile = selectProfileById(parent.profiles, parent.selectedProfileId);
  // The inbox and the run list belong to one account: they are cleared on sign-out and on another sign-in.
  const accountSubject = parent.currentUser?.subject ?? null;
  React.useEffect(() => { platform.resetAccountData(); }, [accountSubject]);
  const [historyReturnStep, setHistoryReturnStep] = React.useState<'home' | 'profile'>('profile');
  const [pendingCaptureSource, setPendingCaptureSource] = React.useState<'camera' | 'gallery' | null>(null);
  const [drawingGuideEntryRequested, setDrawingGuideEntryRequested] = React.useState(false);

  React.useEffect(() => {
    if (!drawingGuideEntryRequested || parent.step !== 'topic') return;
    parent.setGuideEnabled(true);
    setDrawingGuideEntryRequested(false);
  }, [drawingGuideEntryRequested, parent.step, parent.setGuideEnabled]);

  function openHistory(returnStep: 'home' | 'profile' = 'profile'): void {
    setHistoryReturnStep(returnStep);
    parent.setStep('history');
    void platform.loadRuns(parent.profile?.profile_id);
  }

  function openSharing(): void {
    const selected = parent.profile ?? selectedProfile;
    if (!selected) {
      parent.setStep('profile');
      return;
    }
    parent.selectProfile(selected);
    parent.setStep('profile-sharing');
    void platform.loadShares(selected.profile_id);
  }

  function openDeliveredLessons(): void {
    const selected = parent.profile ?? selectedProfile;
    if (!selected) {
      parent.setStep('profile');
      return;
    }
    parent.selectProfile(selected);
    parent.setStep('lesson-history');
    void platform.loadDeliveries(selected.profile_id);
  }

  function openNotifications(): void {
    parent.setStep('notifications');
    void platform.loadNotifications();
  }

  function openQuota(): void {
    parent.setStep('quota');
    void platform.loadQuota();
  }

  function navigateMainTab(tab: ParentMainTab): void {
    parent.clearError();
    if (tab === 'home') return parent.setStep('home');
    if (tab === 'profiles') return parent.setStep('profile');
    if (tab === 'lessons') return void parent.openLessons('gallery');
    if (tab === 'activity') return openHistory('home');
  }

  function startCaptureFlow(source: 'camera' | 'gallery'): void {
    parent.clearError();
    if (parent.activeRun) {
      setPendingCaptureSource(null);
      void parent.resumeActiveRun();
      return;
    }

    setPendingCaptureSource(source);
    if (selectedProfile) parent.continueWithProfile(selectedProfile);
    else parent.setStep('profile');
  }

  function startOrResume(): void {
    startCaptureFlow('camera');
  }

  function openDrawingGuide(): void {
    parent.clearError();
    if (parent.activeRun) {
      void parent.resumeActiveRun();
      return;
    }
    setDrawingGuideEntryRequested(true);
    if (selectedProfile) parent.continueWithProfile(selectedProfile);
    else parent.setStep('profile');
  }

  function mainSection(activeTab: ParentMainTab, content: React.ReactNode): React.JSX.Element {
    return <View style={{ flex: 1 }}>{content}<ParentBottomBar
      activeTab={activeTab}
      onNavigate={navigateMainTab}
      onStart={startOrResume}
      startLabel={parent.activeRun ? 'Tiếp tục' : 'Bắt đầu'}
    /></View>;
  }

  if (parent.step === 'auth') {
    return <AuthScreen
      busy={parent.busy === 'auth' || parent.bootstrapBusy}
      error={parent.authError || (parent.bootstrapBusy ? 'Đang xác thực tài khoản và tải hồ sơ…' : '')}
      googleAndroidClientId={parent.publicSettings.googleAndroidClientId}
      googleWebClientId={parent.publicSettings.googleWebClientId}
      onSignIn={(email, password) => parent.authenticate('signin', email, password)}
      onSignUp={(email, password) => parent.authenticate('signup', email, password)}
      onReset={parent.resetPassword}
      onGoogleSignIn={parent.signInWithGoogle}
      onClearAuthError={parent.clearAuthError}
    />;
  }

  if (parent.bootstrapBusy) {
    return <SafeAreaView edges={['top', 'right', 'bottom', 'left']} style={{ flex: 1, backgroundColor: palette.background, alignItems: 'center', justifyContent: 'center', gap: 12 }}>
      <ActivityIndicator color={palette.blue} />
      <Text style={{ color: palette.muted }}>Đang tải hồ sơ và quyền xử lý…</Text>
    </SafeAreaView>;
  }

  if (parent.step === 'profile') {
    return mainSection('profiles', <ProfileScreen
      profiles={parent.profiles}
      pendingDeletions={parent.pendingDeletions}
      selectedProfileId={parent.selectedProfileId}
      activeRun={parent.activeRun}
      busy={parent.busy}
      pendingDeletionLoadingId={parent.pendingDeletionLoadingId}
      consentState={parent.consentState}
      error={parent.error}
      onSelect={parent.selectProfile}
      onCreate={() => {
        parent.clearProfileFormErrors();
        parent.clearError();
        parent.setProfileBeingEdited(null);
        parent.setStep('profile-create');
      }}
      onEdit={(profile) => { parent.clearProfileFormErrors(); parent.setProfileBeingEdited(profile); parent.setStep('profile-edit'); }}
      onRequestDeletion={(profile) => void parent.requestProfileDeletion(profile)}
      onRefreshPendingDeletion={(profileId) => void parent.refreshPendingDeletion(profileId)}
      onContinue={parent.continueWithProfile}
      onOpenAccount={() => parent.setStep('account')}
      onOpenSettings={() => parent.setStep('settings')}
      onOpenNotifications={openNotifications}
      onOpenQuota={openQuota}
      onOpenHistory={openHistory}
      onOpenSharing={openSharing}
      onOpenDeliveredLessons={openDeliveredLessons}
      onSignOut={() => void parent.signOut()}
    />);
  }

  if (parent.step === 'home') {
    return mainSection('home', <HomeScreen
      profiles={parent.profiles}
      selectedProfile={selectedProfile}
      activeRun={parent.activeRun}
      error={parent.error}
      onStart={() => startCaptureFlow('camera')}
      onPickFromLibrary={() => startCaptureFlow('gallery')}
      onManageProfiles={() => { parent.clearError(); parent.setStep('profile'); }}
      onSelectProfile={parent.selectProfile}
      onOpenNotifications={openNotifications}
      onOpenLessons={() => void parent.openLessons('gallery')}
      onOpenDrawingGuide={openDrawingGuide}
      onResumeRun={parent.resumeActiveRun}
    />);
  }

  if (parent.step === 'profile-create' || parent.step === 'profile-edit') {
    const isEditing = parent.step === 'profile-edit';
    return <ProfileFormScreen
      key={isEditing ? parent.profileBeingEdited?.revision_no : 'create'}
      mode={isEditing ? 'edit' : 'create'}
      profile={parent.profileBeingEdited}
      busy={parent.busy === 'profile' || parent.busy === 'profile-update'}
      error={parent.error}
      fieldErrors={parent.profileFieldErrors}
      onCreate={parent.createProfileAndReturn}
      onUpdate={parent.updateProfile}
      onBack={() => { parent.clearError(); parent.setStep('profile'); }}
    />;
  }

  if (parent.step === 'lesson-library') {
    return mainSection('lessons', <LessonGalleryScreen
      mode="gallery"
      lessons={parent.lessons}
      selectedLesson={parent.galleryLesson}
      selectedPresetVersionId={parent.lesson?.version_id ?? null}
      lessonInvitations={parent.lessonInvitations}
      groupInvitations={parent.groupInvitations}
      loading={parent.lessonLoading}
      loadingId={parent.lessonLoadingId}
      error={parent.lessonError}
      onOpenLesson={(lessonId) => void parent.chooseLesson(lessonId)}
      onUseLesson={parent.setLesson}
      onAcceptLessonInvitation={(id) => void parent.acceptLessonInvitation(id)}
      onDeclineLessonInvitation={(id) => void parent.declineLessonInvitation(id)}
      onAcceptGroupInvitation={(id) => void parent.acceptGroupInvitation(id)}
      onBack={() => parent.setStep('home')}
    />);
  }

  if (parent.step === 'account') {
    return mainSection('profiles', <AccountScreen
      user={parent.currentUser}
      busy={parent.busy === 'password'}
      error={parent.accountError}
      onChangePassword={parent.changePassword}
      onResetPassword={parent.resetCurrentPassword}
      onBack={() => parent.setStep('profile')}
    />);
  }

  if (parent.step === 'settings') {
    return mainSection('profiles', <SettingsScreen
      sketchGuideEnabled={parent.guideEnabled}
      onSketchGuideEnabled={parent.setGuideEnabled}
      onBack={() => parent.setStep('profile')}
    />);
  }

  if (parent.step === 'notifications') return mainSection('profiles', <NotificationsScreen
    capability={platform.capabilities.notifications}
    items={platform.notifications}
    unreadCount={platform.notificationsUnreadCount}
    loading={platform.notificationsBusy}
    error={platform.notificationsError}
    hasMore={Boolean(platform.notificationsCursor)}
    onLoad={() => void platform.loadNotifications()}
    onLoadMore={() => void platform.loadNotifications(platform.notificationsCursor)}
    onMarkRead={(id) => void platform.markNotificationRead(id)}
    onMarkAllRead={() => void platform.markAllNotificationsRead()}
    onBack={() => parent.setStep('profile')}
  />);
  if (parent.step === 'quota') return mainSection('profiles', <QuotaScreen
    capability={platform.capabilities.quota}
    quota={platform.quota}
    loading={platform.quotaBusy}
    error={platform.quotaError}
    onLoad={() => void platform.loadQuota()}
    onBack={() => parent.setStep('profile')}
  />);
  if (parent.step === 'history') return mainSection('activity', <StoryHistoryScreen
    capability={platform.capabilities.runs}
    runs={platform.runs}
    loading={platform.runsBusy}
    error={platform.runsError}
    hasMore={Boolean(platform.runsCursor)}
    onLoad={() => void platform.loadRuns(parent.profile?.profile_id)}
    onLoadMore={() => void platform.loadRuns(parent.profile?.profile_id, platform.runsCursor)}
    onCancel={(id) => void platform.cancelRun(id)}
    onDelete={(id) => void platform.deleteRun(id)}
    onWatch={(id) => void parent.watchHistoryRun(id)}
    onBack={() => parent.setStep(historyReturnStep)}
  />);
  if (parent.step === 'profile-sharing') return mainSection('profiles', <ProfileSharingScreen
    profile={parent.profile ?? selectedProfile}
    grants={platform.shares}
    loading={platform.sharesBusy}
    error={platform.sharesError}
    capability={platform.shareCapability}
    inviteState={platform.shareInviteState}
    revokeState={platform.shareRevokeState}
    onInvite={platform.inviteTeacher}
    onRevoke={platform.revokeShare}
    onBack={() => parent.setStep('profile')}
  />);
  if (parent.step === 'lesson-history') return mainSection('profiles', <LessonHistoryScreen
    capability={platform.capabilities.deliveries}
    deliveries={platform.deliveries}
    loading={platform.deliveriesBusy}
    error={platform.deliveriesError}
    hasMore={Boolean(platform.deliveriesCursor)}
    onLoad={() => void platform.loadDeliveries(parent.profile?.profile_id ?? '')}
    onLoadMore={() => void platform.loadDeliveries(parent.profile?.profile_id ?? '', platform.deliveriesCursor)}
    onSubmitFeedback={(id, text) => platform.submitFeedback(id, text).then(() => undefined)}
    onBack={() => parent.setStep('profile')}
  />);

  return renderLearningStep(parent, platform, pendingCaptureSource, () => setPendingCaptureSource(null));
}

function renderLearningStep(
  parent: ReturnType<typeof useParentController>,
  platform: ReturnType<typeof useParentPlatformController>,
  pendingCaptureSource: 'camera' | 'gallery' | null,
  onCaptureIntentHandled: () => void,
): React.JSX.Element {
  const step: AppStep = parent.step;
  const stepLabel = (number: number): string => `${number} / 8`;
  const lessonPin = lessonVersionPinFromDetail(parent.lesson);
  const canOpenGuide = canBeginContextStep({
    profileId: parent.profile?.profile_id ?? '', topic: parent.topic, adultIdea: parent.idea, lessonPin,
  });
  const canAnalyze = canAnalyzeDrawing({
    runId: parent.contextRun?.run_id,
    contextConfirmed: parent.contextConfirmed,
    photoSelected: Boolean(parent.photo),
  });
  // A story the server already holds (resume, rewrite, video) needs no activity selection again.
  const storyReady = Boolean(
    parent.contextRun?.run_id
    && parent.contextConfirmed
    && parent.subjectConfirmed
    && (parent.contextRun.main_activity?.state === 'SELECTED' || parent.story),
  );
  const storyBlockedReason = 'Hãy hoàn tất lựa chọn hoạt động và xác nhận ngữ cảnh trước khi xem câu chuyện.';
  const canConfirmStory = canConfirmDisplayedStory({
    runId: parent.contextRun?.run_id,
    displayedRunId: parent.storyDisplayedRunId,
    storyPresent: Boolean(parent.story),
    subjectConfirmed: parent.subjectConfirmed,
    storyConfirmed: parent.storyConfirmed && !parent.storyConfirmationRequired,
    storyRevisionNo: parent.storyRevisionNo,
    storySha256: parent.storySha256,
  });
  if (step === 'entry') return <LearningPathScreen
    error={parent.error}
    onTopic={() => void parent.beginTopicPath()}
    onLesson={parent.beginLessonPath}
    onBack={() => parent.setStep('home')}
  />;
  if (step === 'topic') return <TopicScreen
    topic={parent.topic}
    selectedTopicId={parent.selectedTopicId}
    cards={parent.topicSuggestions}
    loading={parent.topicSuggestionBusy}
    error={parent.topicSuggestionError}
    canContinue={parent.topic.trim().length >= 2 && !parent.topicSuggestionBusy && !parent.subjectSuggestionBusy}
    stepLabel={stepLabel(1)}
    onSelect={parent.selectTopicCard}
    onTopic={parent.setCustomTopic}
    onRefresh={() => void parent.refreshTopicSuggestions()}
    onContinue={() => void parent.continueTopicSelection()}
    onSkip={parent.skipTopicSelection}
    onBack={() => parent.setStep('entry')}
  />;
  if (step === 'subject') return <DrawingSubjectScreen
    topic={parent.topic}
    topicId={parent.selectedTopicId}
    cards={parent.subjectSuggestions}
    generationSource={parent.subjectSuggestionSets.at(-1)?.generation_source ?? null}
    selectedSubject={parent.intendedDrawingSubject}
    customSubject={parent.customDrawingSubject}
    loading={parent.subjectSuggestionBusy}
    validating={parent.subjectSuggestionBusy}
    error={parent.subjectSuggestionError}
    validationMessage={parent.subjectValidationMessage}
    canContinue={Boolean(parent.intendedDrawingSubject.trim())
      && (!parent.customDrawingSubject.trim() || parent.subjectValidationMessage.length > 0)
      && !parent.subjectSuggestionBusy}
    onSelect={parent.selectDrawingSubject}
    onCustomSubject={parent.setCustomSubject}
    onValidate={() => void parent.validateCustomDrawingSubject()}
    onRefresh={() => void parent.refreshSubjectSuggestions()}
    onContinue={parent.continueFromSubjectSelection}
    onBack={() => parent.setStep('topic')}
  />;
  if (step === 'idea') return <IdeaScreen
    topic={parent.topic}
    idea={parent.idea}
    audio={parent.audio}
    guideEnabled={parent.guideEnabled}
    guideBase64={parent.guideBase64}
    guideBusy={parent.guideBusy}
    guideError={parent.guideError}
    lesson={parent.lesson}
    stepLabel={stepLabel(2)}
    canContinue={canOpenGuide}
    error={parent.error}
    onIdea={parent.setIdea}
    onAudio={parent.setAudio}
    onGuideToggle={parent.setGuideEnabled}
    onGenerateGuide={() => void parent.createGuide()}
    onOpenLessons={() => void parent.openLessons('picker')}
    onContinue={parent.openDrawingGuide}
    onBack={() => parent.setStep(parent.lesson ? 'drawing-guide' : parent.selectedTopicId ? 'subject' : 'topic')}
  />;
  if (step === 'drawing-guide' && parent.lesson) return <DrawingGuideScreen
    lesson={parent.lesson}
    stepLabel={stepLabel(3)}
    currentIndex={parent.drawingGuideIndex}
    onIndexChange={parent.setDrawingGuideIndex}
    onContinue={parent.openContextReview}
    onBack={() => parent.setStep('idea')}
  />;
  if (step === 'lessons') return <LessonPickerScreen
    lessons={parent.lessons}
    selectedId={parent.lesson?.lesson_id ?? ''}
    loading={parent.lessonLoading}
    loadingId={parent.lessonLoadingId}
    error={parent.lessonError}
    onSelect={(id) => void parent.chooseLesson(id)}
    onClear={() => { parent.setLesson(null); parent.setStep('idea'); }}
    onBack={() => parent.setStep('idea')}
  />;
  if (step === 'context') return <ContextScreen
    profile={parent.profile}
    contextRun={parent.contextRun}
    stepLabel={stepLabel(6)}
    busy={parent.busy === 'context-create' || parent.busy === 'context-confirmation'}
    confirmed={parent.contextConfirmed}
    error={parent.error}
    onRetryCreate={() => void parent.retryContextCreation()}
    onConfirm={() => void parent.confirmContext()}
    onContinue={parent.continueToCapture}
    onBack={parent.contextRun?.context_confirmed ? undefined : parent.contextRun ? () => parent.setStep('activity') : () => parent.setStep('drawing-guide')}
  />;
  if (step === 'capture') return <CaptureScreen
    photo={parent.photo}
    stepLabel={stepLabel(4)}
    canAnalyze={canAnalyze}
    analysisBusy={parent.busy === 'context-create' || parent.busy === 'understanding'}
    runExists={Boolean(parent.contextRun?.run_id)}
    initialCaptureSource={pendingCaptureSource}
    onCaptureIntentHandled={onCaptureIntentHandled}
    onPhoto={parent.setPhoto}
    onContinue={() => void parent.analyzeDrawingForCurrentRun()}
    onBack={() => parent.leaveWait(parent.contextRun ? 'context' : 'idea')}
  />;
  if (step === 'understanding' && parent.candidate) return <UnderstandingScreen
    candidate={parent.candidate}
    stepLabel={stepLabel(5)}
    subject={parent.subject}
    busy={parent.busy === 'subject'}
    error={parent.error}
    onSubject={parent.setSubject}
    subjectRoles={parent.subjectRoles}
    onRenameSecondary={parent.renameSecondarySubject}
    onToggleSecondary={parent.toggleSecondarySubject}
    onMakeMain={parent.makeMainSubject}
    onConfirm={() => void parent.confirmSubject()}
    onBack={() => parent.leaveWait('capture')}
  />;
  if (step === 'activity') return <ActivityScreen
    stepLabel={stepLabel(7)}
    topic={parent.topic}
    subject={parent.subject}
    activities={parent.activitySuggestions}
    selectedIndex={parent.selectedActivityIndex}
    loading={parent.activityBusy}
    saving={parent.busy === 'activity-selection'}
    attempted={parent.activityAttempted}
    error={parent.activityError || parent.error}
    onRetry={() => void parent.requestActivityList(true)}
    onSelect={parent.chooseActivity}
    onContinue={() => void parent.selectActivity()}
    onCancel={() => void parent.cancelEmptyActivityRun()}
    onBack={() => parent.setStep(parent.contextRun?.context_confirmed ? 'context' : 'understanding')}
  />;
  if (step === 'transcript') return <TranscriptReviewScreen
    stepLabel={stepLabel(5)}
    transcript={parent.transcript}
    waiting={parent.transcriptWaiting}
    text={parent.transcriptText}
    edited={parent.transcriptEdited}
    busy={parent.busy === 'transcript-confirm'}
    error={parent.error}
    onText={parent.setTranscriptText}
    onConfirm={() => void parent.confirmTranscriptReview()}
    onRefresh={() => void parent.refreshTranscript()}
    onBack={() => parent.leaveWait('capture')}
  />;
  if (step === 'video') return <VideoScreen
    stepLabel={stepLabel(8)}
    panel={parent.videoPanel}
    busy={['video-request', 'video-playback', 'video-unsuitable', 'video-complete', 'video-refresh'].includes(parent.busy) ? parent.busy : ''}
    error={parent.error}
    playback={parent.playback}
    reason={parent.videoReason}
    markingUnsuitable={parent.markingUnsuitable}
    onReason={parent.setVideoReason}
    onRequest={() => void parent.requestVideo()}
    onPlay={() => void parent.playVideo()}
    onPlaybackError={parent.onPlaybackError}
    onStartUnsuitable={parent.startUnsuitable}
    onCancelUnsuitable={parent.cancelUnsuitable}
    onConfirmUnsuitable={() => void parent.markVideoUnsuitable()}
    onComplete={() => void parent.completeRun()}
    onBackToStory={() => parent.leaveWait('story')}
    onOpenHistory={() => parent.leaveWait('history')}
    onRefresh={() => void parent.refreshVideo()}
    onBack={() => parent.leaveWait(parent.videoBackStep)}
  />;
  if (step === 'story') return <StoryScreen
    stepLabel={stepLabel(8)}
    story={parent.story}
    storyReady={storyReady}
    blockedReason={storyBlockedReason}
    rewriteCount={parent.rewriteCount}
    rewriteInstruction={parent.rewriteInstruction}
    busy={parent.busy === 'story' || parent.busy === 'rewrite' || parent.busy === 'confirm-story'}
    attempted={parent.storyAttempted}
    canConfirm={canConfirmStory}
    error={parent.error}
    confirmed={parent.storyConfirmed}
    rewriting={parent.busy === 'rewrite'}
    rewriteNotice={parent.rewriteNotice}
    rewriteAfterVideo={parent.rewriteAfterVideo}
    confirmationRequired={parent.storyConfirmationRequired}
    onlyCancel={parent.storyOnlyCancel}
    rewritesLeft={rewritesLeft(parent.storyRevisionNo)}
    onOpenVideo={() => void parent.openVideoStep()}
    onRewriteInstruction={parent.setRewriteInstruction}
    onRewrite={() => void parent.rewriteStory(parent.rewriteInstruction)}
    onConfirm={() => void parent.confirmStory()}
    onRefresh={() => void parent.refreshStory()}
    onOpenHistory={() => parent.leaveWait('history')}
    onBack={() => parent.leaveWait(parent.story ? 'home' : 'activity')}
  />;
  if (step === 'handoff') return <HandoffScreen
    storyTitle={parent.story?.title ?? ''}
    events={parent.events}
    videoCapability={platform.capabilities.video}
    jobStage={{ state: 'idle', stage: 'idle' }}
    onResumeActiveRun={parent.resumeActiveRun}
  />;

  return <ScreenFrame title="Không thể mở bước này" subtitle="Dữ liệu buổi học chưa đủ để tiếp tục." onBack={parent.backToProfile}>
    <Notice text={parent.error || 'Tải lại hồ sơ rồi thử lại.'} tone="error" />
  </ScreenFrame>;
}
