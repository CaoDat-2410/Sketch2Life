import React from 'react';
import { ActivityIndicator, StatusBar, Text, View } from 'react-native';
import type { ParentApplicationModule } from '../application/ports/ParentApplicationModule';
import type { ParentMainTab } from './screens/ParentBottomBar';
import type { AppStep } from './navigation/workflowTypes';
import { useParentController } from './navigation/useParentController';
import { useParentPlatformController } from './navigation/useParentPlatformController';
import { AccountScreen } from './screens/AccountScreen';
import { ActivityScreen } from './screens/ActivityScreen';
import { AuthScreen } from './screens/AuthScreen';
import { CaptureScreen } from './screens/CaptureScreen';
import { ContextScreen } from './screens/ContextScreen';
import { HandoffScreen } from './screens/HandoffScreen';
import { HomeScreen } from './screens/HomeScreen';
import { LessonGalleryScreen } from './screens/LessonGalleryScreen';
import { LessonPickerScreen } from './screens/LessonPickerScreen';
import { NotificationsScreen } from './screens/NotificationsScreen';
import { ParentBottomBar } from './screens/ParentBottomBar';
import { ProfileFormScreen } from './screens/ProfileFormScreen';
import { ProfileScreen } from './screens/ProfileScreen';
import { QuotaScreen } from './screens/QuotaScreen';
import { SettingsScreen } from './screens/SettingsScreen';
import { StoryHistoryScreen } from './screens/StoryHistoryScreen';
import { ProfileSharingScreen } from './screens/ProfileSharingScreen';
import { LessonHistoryScreen } from './screens/LessonHistoryScreen';
import { TranscriptReviewScreen } from './screens/TranscriptReviewScreen';
import { StoryScreen } from './screens/StoryScreen';
import { TopicScreen } from './screens/TopicScreen';
import { UnderstandingScreen } from './screens/UnderstandingScreen';
import { Notice, palette, ScreenFrame } from './components/ui';

type Props = { application: ParentApplicationModule };

export default function ParentExpoApp({ application }: Props): React.JSX.Element {
  const parent = useParentController(application);
  const platform = useParentPlatformController(application);

  function openHistory(): void {
    parent.setStep('history');
    void platform.loadRuns(parent.profile?.parent_profile_id);
  }

  function openSharing(): void {
    const selected = parent.profile ?? parent.profiles[0] ?? null;
    if (!selected) {
      parent.setStep('profile');
      return;
    }
    parent.setProfile(selected);
    parent.setStep('profile-sharing');
    void platform.loadShares(selected.parent_profile_id);
  }

  function openDeliveredLessons(): void {
    const selected = parent.profile ?? parent.profiles[0] ?? null;
    if (!selected) {
      parent.setStep('profile');
      return;
    }
    parent.setProfile(selected);
    parent.setStep('lesson-history');
    void platform.loadDeliveries(selected.parent_profile_id);
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
    if (parent.activeRun) return parent.resumeActiveRun();

    const selectedProfile = parent.profiles.find((item) => item.parent_profile_id === parent.profile?.parent_profile_id)
      ?? parent.profiles[0];
    if (selectedProfile?.authorization_current) parent.continueWithProfile(selectedProfile);
    else parent.setStep('profile');
  }

  function mainSection(activeTab: ParentMainTab, content: React.ReactNode): React.JSX.Element {
    return <View style={{ flex: 1 }}>{content}<ParentBottomBar activeTab={activeTab} onNavigate={navigateMainTab} /></View>;
  }

  if (parent.step === 'auth') {
    return <>
      <StatusBar barStyle="dark-content" backgroundColor="#F6F9FC" />
      <AuthScreen
        busy={parent.busy === 'auth' || parent.bootstrapBusy}
        error={parent.authError || (parent.bootstrapBusy ? 'Đang xác thực tài khoản và tải hồ sơ…' : '')}
        googleAndroidClientId={parent.publicSettings.googleAndroidClientId}
        googleWebClientId={parent.publicSettings.googleWebClientId}
        onSignIn={(email, password) => parent.authenticate('signin', email, password)}
        onSignUp={(email, password) => parent.authenticate('signup', email, password)}
        onReset={parent.resetPassword}
        onGoogleSignIn={parent.signInWithGoogle}
      />
    </>;
  }

  if (parent.bootstrapBusy) {
    return <View style={{ flex: 1, backgroundColor: '#F6F9FC', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
      <ActivityIndicator color={palette.blue} />
      <Text style={{ color: palette.muted }}>Đang tải hồ sơ và quyền xử lý…</Text>
    </View>;
  }

  if (parent.step === 'profile') {
    return mainSection('profiles', <ProfileScreen
      profiles={parent.profiles}
      selectedProfileId={parent.profile?.parent_profile_id ?? parent.profiles[0]?.parent_profile_id ?? ''}
      activeRun={parent.activeRun}
      busy={parent.busy}
      error={parent.error}
      onSelect={parent.setProfile}
      onCreate={() => parent.setStep('profile-create')}
      onEdit={(profile) => { parent.setProfileBeingEdited(profile); parent.setStep('profile-edit'); }}
      onAuthorize={(profile) => void parent.authorizeProfile(profile)}
      onRevoke={(profile) => void parent.revokeProfileAuthorization(profile)}
      onArchive={(profile) => void parent.archiveProfile(profile)}
      onContinue={parent.continueWithProfile}
      onResumeRun={parent.resumeActiveRun}
      onBackHome={() => { parent.clearError(); parent.setStep('home'); }}
    />);
  }

  if (parent.step === 'home') {
    return mainSection('home', <HomeScreen
      profiles={parent.profiles}
      activeRun={parent.activeRun}
      error={parent.error}
      onStart={() => { parent.clearError(); parent.setStep('profile'); }}
      onManageProfiles={() => { parent.clearError(); parent.setStep('profile'); }}
      onOpenLessons={() => void parent.openLessons('gallery')}
      onOpenAccount={() => parent.setStep('account')}
      onOpenSettings={() => parent.setStep('settings')}
      onOpenNotifications={openNotifications}
      onOpenQuota={openQuota}
      onOpenHistory={openHistory}
      onOpenSharing={openSharing}
      onOpenDeliveredLessons={openDeliveredLessons}
      onResumeRun={parent.resumeActiveRun}
      onSignOut={() => void parent.signOut()}
    />);
  }

  if (parent.step === 'profile-create' || parent.step === 'profile-edit') {
    const isEditing = parent.step === 'profile-edit';
    return <ProfileFormScreen
      mode={isEditing ? 'edit' : 'create'}
      profile={parent.profileBeingEdited}
      policy={parent.policy}
      busy={parent.busy === 'profile' || parent.busy === 'profile-update'}
      error={parent.error}
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
    return mainSection('home', <AccountScreen
      user={parent.currentUser}
      busy={parent.busy === 'password'}
      error={parent.accountError}
      onChangePassword={parent.changePassword}
      onResetPassword={parent.resetCurrentPassword}
      onSignOut={() => void parent.signOut()}
      onBack={() => parent.setStep('home')}
    />);
  }

  if (parent.step === 'settings') {
    return mainSection('home', <SettingsScreen
      sketchGuideEnabled={parent.guideEnabled}
      onSketchGuideEnabled={parent.setGuideEnabled}
      onOpenAccount={() => parent.setStep('account')}
      onOpenProfiles={() => parent.setStep('profile')}
      onOpenNotifications={openNotifications}
      onOpenQuota={openQuota}
      onOpenHistory={openHistory}
      onOpenSharing={openSharing}
      onOpenDeliveredLessons={openDeliveredLessons}
      onBack={() => parent.setStep('home')}
    />);
  }

  if (parent.step === 'notifications') return mainSection('home', <NotificationsScreen
    items={platform.notifications}
    loading={platform.notificationsBusy}
    error={platform.notificationsError}
    hasMore={Boolean(platform.notificationsCursor)}
    onLoad={() => void platform.loadNotifications()}
    onLoadMore={() => void platform.loadNotifications(platform.notificationsCursor)}
    onMarkRead={(id) => void platform.markNotificationRead(id)}
    onBack={() => parent.setStep('home')}
  />);
  if (parent.step === 'quota') return mainSection('home', <QuotaScreen
    quota={platform.quota}
    loading={platform.quotaBusy}
    error={platform.quotaError}
    onLoad={() => void platform.loadQuota()}
    onBack={() => parent.setStep('home')}
  />);
  if (parent.step === 'history') return mainSection('home', <StoryHistoryScreen
    runs={platform.runs}
    loading={platform.runsBusy}
    error={platform.runsError}
    hasMore={Boolean(platform.runsCursor)}
    onLoad={() => void platform.loadRuns(parent.profile?.parent_profile_id)}
    onLoadMore={() => void platform.loadRuns(undefined, platform.runsCursor)}
    onCancel={(runId) => void platform.cancelRun(runId)}
    onDelete={(runId) => void platform.deleteRun(runId)}
    onBack={() => parent.setStep('home')}
  />);
  if (parent.step === 'profile-sharing') return mainSection('home', <ProfileSharingScreen
    profile={parent.profile ?? parent.profiles[0] ?? null}
    grants={platform.shares}
    loading={platform.sharesBusy}
    error={platform.sharesError}
    onInvite={platform.inviteTeacher}
    onRevoke={(grantId) => void platform.revokeShare(grantId)}
    onBack={() => parent.setStep('home')}
  />);
  if (parent.step === 'lesson-history') return mainSection('home', <LessonHistoryScreen
    deliveries={platform.deliveries}
    loading={platform.deliveriesBusy}
    error={platform.deliveriesError}
    hasMore={Boolean(platform.deliveriesCursor)}
    onLoad={() => { const id = parent.profile?.parent_profile_id; if (id) void platform.loadDeliveries(id); }}
    onLoadMore={() => void platform.loadDeliveries(platform.deliveriesProfileId, platform.deliveriesCursor)}
    onSubmitFeedback={platform.submitFeedback}
    onBack={() => parent.setStep('home')}
  />);

  return renderLearningStep(parent);
}

function renderLearningStep(parent: ReturnType<typeof useParentController>): React.JSX.Element {
  const step: AppStep = parent.step;
  const hasAudio = Boolean(parent.audio);
  const stepLabel = (plain: number, withAudio: number): string =>
    hasAudio ? `${withAudio} / 8` : `${plain} / 7`;
  if (step === 'topic') return <TopicScreen
    topic={parent.topic}
    idea={parent.idea}
    audio={parent.audio}
    guideEnabled={parent.guideEnabled}
    guideBase64={parent.guideBase64}
    guideBusy={parent.guideBusy}
    guideError={parent.guideError}
    lesson={parent.lesson}
    stepLabel={stepLabel(1, 1)}
    onTopic={parent.setTopic}
    onIdea={parent.setIdea}
    onAudio={parent.setAudio}
    onGuideToggle={parent.setGuideEnabled}
    onGenerateGuide={() => void parent.createGuide()}
    onOpenLessons={() => void parent.openLessons('picker')}
    onContinue={() => parent.setStep('capture')}
    onBack={parent.backToProfile}
  />;
  if (step === 'lessons') return <LessonPickerScreen
    lessons={parent.lessons}
    selectedId={parent.lesson?.lesson_id ?? ''}
    loading={parent.lessonLoading}
    loadingId={parent.lessonLoadingId}
    error={parent.lessonError}
    onSelect={(id) => void parent.chooseLesson(id)}
    onClear={() => { parent.setLesson(null); parent.setStep('topic'); }}
    onBack={() => parent.setStep('topic')}
  />;
  if (step === 'capture') return <CaptureScreen photo={parent.photo} stepLabel={stepLabel(2, 2)} onPhoto={parent.setPhoto} onContinue={() => parent.setStep('context')} onBack={() => parent.setStep('topic')} />;
  if (step === 'context' && parent.profile && parent.policy && parent.photo) return <ContextScreen
    profile={parent.profile}
    policyVersion={parent.policy.policy_version}
    topic={parent.topic}
    idea={parent.idea}
    lesson={parent.lesson}
    photo={parent.photo}
    stepLabel={stepLabel(3, 3)}
    busy={parent.busy === 'understanding' || parent.busy === 'transcription'}
    error={parent.error}
    onConfirm={() => void parent.confirmContextAndAnalyze()}
    onBack={() => parent.setStep('capture')}
  />;
  if (step === 'transcript-review') return <TranscriptReviewScreen
    stepLabel={stepLabel(4, 4)}
    transcript={parent.transcript}
    text={parent.transcriptText}
    busy={parent.transcriptBusy || parent.busy === 'understanding'}
    error={parent.transcriptError}
    onText={parent.setTranscriptText}
    onConfirm={() => void parent.confirmReviewedTranscript()}
    onContinueWithoutAudio={() => void parent.continueWithoutAudio()}
    onBack={() => parent.setStep('context')}
  />;
  if (step === 'understanding' && parent.candidate) return <UnderstandingScreen
    candidate={parent.candidate}
    stepLabel={stepLabel(4, 5)}
    subject={parent.subject}
    busy={parent.busy === 'subject'}
    error={parent.error}
    onSubject={parent.setSubject}
    onConfirm={() => void parent.confirmSubject()}
    onBack={() => parent.setStep('context')}
  />;
  if (step === 'activity') return <ActivityScreen
    stepLabel={stepLabel(5, 6)}
    activities={parent.activities}
    source={parent.activitySource}
    busy={parent.busy === 'activity'}
    requested={parent.activityAttempted}
    error={parent.activityError}
    onSuggest={() => void parent.requestActivities()}
    onSkip={() => parent.setStep('story')}
    onBack={() => parent.setStep('understanding')}
  />;
  if (step === 'story') return <StoryScreen
    stepLabel={stepLabel(6, 7)}
    story={parent.story}
    rewriteCount={parent.rewriteCount}
    rewriteInstruction={parent.rewriteInstruction}
    busy={parent.busy === 'story' || parent.busy === 'rewrite' || parent.busy === 'confirm-story'}
    attempted={parent.storyAttempted}
    canConfirm={Boolean(parent.run?.story_revision_no && parent.storySha256)}
    error={parent.error}
    confirmed={parent.storyConfirmed}
    onRewriteInstruction={parent.setRewriteInstruction}
    onGenerate={() => void parent.requestStory()}
    onRewrite={() => void parent.requestStory(parent.rewriteInstruction)}
    onConfirm={() => void parent.confirmStory()}
    onBack={() => parent.setStep('activity')}
  />;
  if (step === 'handoff') return <HandoffScreen
    storyTitle={parent.story?.title ?? ''}
    events={parent.events}
    onRestart={() => { parent.resetWorkflow(); parent.setStep('home'); }}
  />;

  return <ScreenFrame title="Không thể mở bước này" subtitle="Dữ liệu buổi học chưa đủ để tiếp tục." onBack={parent.backToProfile}>
    <Notice text={parent.error || 'Tải lại hồ sơ rồi thử lại.'} tone="error" />
  </ScreenFrame>;
}
