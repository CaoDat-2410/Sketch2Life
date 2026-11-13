import { useRef, useState } from 'react';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { createParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import { parseStoryDraft } from '../../domain/storyDraft';
import type {
  ParentAudioTranscription,
  LessonDetail,
  LessonInvitation,
  LessonSummary,
  ParentCandidate,
  ParentGroupInvitation,
  ParentProfileDeletePendingV1,
  ParentProfileViewV1,
  ParentStoryRunV1,
  ParentUser,
  StoryDraft,
  StoryRun,
  SuggestedActivity,
} from '../../domain/types';
import type { AppStep, SelectedAudio, SelectedPhoto, TimedEvent } from './workflowTypes';
import {
  canBeginContextStep,
  isProfileDeletionPending,
  lessonVersionPinFromDetail,
  mergeProfilePage,
  nextProfileCursor,
  reconcileProfileRecord,
  safeParentFlowErrorMessage,
  safeProfileFieldMessages,
  selectProfileById,
} from './parentFlowV1';

export function useParentController(application: ParentApplicationModule) {
  const [step, setStep] = useState<AppStep>('auth');
  const [currentUser, setCurrentUser] = useState<ParentUser | null>(null);
  const [profiles, setProfiles] = useState<ParentProfileViewV1[]>([]);
  const [profile, setProfile] = useState<ParentProfileViewV1 | null>(null);
  const [selectedProfileId, setSelectedProfileId] = useState('');
  const [profileBeingEdited, setProfileBeingEdited] = useState<ParentProfileViewV1 | null>(null);
  const [pendingDeletions, setPendingDeletions] = useState<ParentProfileDeletePendingV1[]>([]);
  const [pendingDeletionLoadingId, setPendingDeletionLoadingId] = useState('');
  const [profileFieldErrors, setProfileFieldErrors] = useState(safeProfileFieldMessages(null));
  const [activeRun, setActiveRun] = useState<ParentStoryRunV1 | null>(null);
  const [topic, setTopic] = useState('');
  const [idea, setIdea] = useState('');
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [lessonLoading, setLessonLoading] = useState(false);
  const [lessonLoadingId, setLessonLoadingId] = useState('');
  const [lessonError, setLessonError] = useState('');
  const [galleryMode, setGalleryMode] = useState<'gallery' | 'picker'>('gallery');
  const [galleryLesson, setGalleryLesson] = useState<LessonDetail | null>(null);
  const [lessonInvitations, setLessonInvitations] = useState<LessonInvitation[]>([]);
  const [groupInvitations, setGroupInvitations] = useState<ParentGroupInvitation[]>([]);
  const [accountError, setAccountError] = useState('');
  const [guideEnabled, setGuideEnabled] = useState(false);
  const [guideBase64, setGuideBase64] = useState('');
  const [guideBusy, setGuideBusy] = useState(false);
  const [guideError, setGuideError] = useState('');
  const [photo, setPhoto] = useState<SelectedPhoto | null>(null);
  const [audio, setAudioValue] = useState<SelectedAudio | null>(null);
  const [audioAttempted, setAudioAttempted] = useState(false);
  const [transcript, setTranscript] = useState<ParentAudioTranscription | null>(null);
  const [transcriptText, setTranscriptText] = useState('');
  const [transcriptError, setTranscriptError] = useState('');
  const [run, setRun] = useState<StoryRun | null>(null);
  const [contextRun, setContextRun] = useState<ParentStoryRunV1 | null>(null);
  const [contextConfirmed, setContextConfirmed] = useState(false);
  const [candidate, setCandidate] = useState<ParentCandidate | null>(null);
  const [subject, setSubject] = useState('');
  const [understandingRevision, setUnderstandingRevision] = useState(0);
  const [activities, setActivities] = useState<SuggestedActivity[]>([]);
  const [activitySource, setActivitySource] = useState('');
  const [activityAttempted, setActivityAttempted] = useState(false);
  const [activityError, setActivityError] = useState('');
  const [story, setStory] = useState<StoryDraft | null>(null);
  const [storySha256, setStorySha256] = useState('');
  const [storyAttempted, setStoryAttempted] = useState(false);
  const [storyConfirmed, setStoryConfirmed] = useState(false);
  const [rewriteCount, setRewriteCount] = useState(0);
  const [rewriteInstruction, setRewriteInstruction] = useState('');
  const [events, setEvents] = useState<TimedEvent[]>([]);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [authError, setAuthError] = useState('');
  const [bootstrapBusy, setBootstrapBusy] = useState(false);
  const profileCreateAction = useRef<RetainedActionIdentity | null>(null);
  const profilePatchActions = useRef(new Map<string, RetainedActionIdentity>());
  const profileDeleteActions = useRef(new Map<string, RetainedActionIdentity>());
  const storyRunCreateAction = useRef<RetainedActionIdentity | null>(null);
  const contextConfirmationAction = useRef<RetainedActionIdentity | null>(null);

  async function timeRequest<T>(stage: string, request: () => Promise<T>): Promise<T> {
    const started = Date.now();
    try {
      const result = await request();
      setEvents((items) => [...items, { stage, status: 'PASS', durationMs: Date.now() - started, requestId: requestIdOf(result) }]);
      return result;
    } catch (cause) {
      setEvents((items) => [...items, {
        stage,
        status: 'FAIL',
        durationMs: Date.now() - started,
        requestId: cause instanceof ParentApplicationError ? cause.requestId : undefined,
        code: cause instanceof ParentApplicationError ? cause.code : undefined,
      }]);
      throw cause;
    }
  }

  async function loadAllProfiles(): Promise<ParentProfileViewV1[]> {
    let cursor: string | null = null;
    let loaded: ParentProfileViewV1[] = [];
    const seenCursors = new Set<string>();
    do {
      const page = await application.profiles.listPageV1(25, cursor);
      loaded = mergeProfilePage(loaded, page);
      const nextCursor = nextProfileCursor(page);
      if (nextCursor !== null && seenCursors.has(nextCursor)) {
        throw new ParentApplicationError('INVALID_LIMIT', 'Profile pagination cursor did not advance.');
      }
      if (nextCursor !== null) seenCursors.add(nextCursor);
      cursor = nextCursor;
    } while (cursor !== null);
    return loaded;
  }

  async function loadParentData(): Promise<void> {
    setBootstrapBusy(true);
    setError('');
    try {
      const user = await application.account.currentUser();
      if (!user) throw new Error('Không tìm thấy phiên đăng nhập.');
      setCurrentUser(user);
      setStep('home');
      const [profilesResult, activeResult] = await Promise.allSettled([
        loadAllProfiles(),
        application.learning.getActiveRunV1(),
      ]);
      if (profilesResult.status === 'rejected') {
        setError(safeParentFlowErrorMessage(profilesResult.reason));
        return;
      }
      const activeProfiles = profilesResult.value;
      setProfiles(activeProfiles);
      if (activeResult.status === 'fulfilled') {
        setActiveRun(activeResult.value.story_run);
        const saved = activeResult.value.story_run;
        if (saved) {
          const selected = selectProfileById(activeProfiles, saved.parent_profile_id);
          if (selected) {
            setProfile(selected);
            setSelectedProfileId(selected.profile_id);
          }
          if (saved.run_state === 'CONTEXT_PENDING') {
            setContextRun(saved);
            setContextConfirmed(false);
          }
        }
      } else {
        setError((previous) => previous || safeParentFlowErrorMessage(activeResult.reason));
      }
    } catch (cause) {
      setAuthError(displayError(cause));
    } finally {
      setBootstrapBusy(false);
    }
  }

  async function authenticate(action: 'signin' | 'signup', email: string, password: string): Promise<void> {
    setBusy('auth');
    setAuthError('');
    try {
      if (action === 'signin') await application.account.signIn(email, password);
      else await application.account.signUp(email, password);
      await loadParentData();
    } catch (cause) {
      setAuthError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function signInWithGoogle(idToken: string): Promise<void> {
    setBusy('auth');
    setAuthError('');
    try {
      await application.account.signInWithGoogle(idToken);
      await loadParentData();
    } catch (cause) {
      setAuthError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function createProfile(input: { displayName: string; ageMonths: number; interests: string }): Promise<ParentProfileViewV1> {
    const displayName = input.displayName.trim();
    const interests = input.interests.trim();
    const signature = JSON.stringify([displayName, input.ageMonths, interests || null]);
    const actionIdentity = retainedActionIdentity(profileCreateAction, signature);
    setBusy('profile');
    setError('');
    setProfileFieldErrors({});
    try {
      const created = await application.profiles.createV1({
        age_months: input.ageMonths,
        display_name: displayName,
        interests_summary: interests || null,
      }, actionIdentity);
      const record = await application.profiles.getV1(created.profile_id);
      const reconciled = reconcileProfileRecord(profiles, pendingDeletions, record);
      setProfiles(reconciled.profiles);
      setPendingDeletions(reconciled.pendingDeletions);
      if (record.state !== 'ACTIVE') {
        throw new ParentApplicationError('INVALID_STATE_TRANSITION', 'The new profile is not active.');
      }
      setProfile(record);
      setSelectedProfileId(record.profile_id);
      profileCreateAction.current = null;
      return record;
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
      setProfileFieldErrors(safeProfileFieldMessages(cause));
      throw cause;
    } finally {
      setBusy('');
    }
  }

  async function createProfileAndReturn(input: { displayName: string; ageMonths: number; interests: string }): Promise<ParentProfileViewV1> {
    const created = await createProfile(input);
    setStep('profile');
    return created;
  }

  async function updateProfile(input: { displayName: string; ageMonths: number; interests: string }): Promise<ParentProfileViewV1> {
    if (!profileBeingEdited) throw new ParentApplicationError('INVALID_STATE_TRANSITION', 'No profile is selected.');
    const target = profileBeingEdited;
    const displayName = input.displayName.trim();
    const interests = input.interests.trim();
    const patch = {
      expected_revision: target.revision_no,
      age_months: input.ageMonths,
      display_name: displayName,
      interests_summary: interests || null,
    };
    const signature = JSON.stringify(patch);
    const actionIdentity = retainedMapActionIdentity(profilePatchActions.current, target.profile_id, signature);
    setBusy('profile-update');
    setError('');
    setProfileFieldErrors({});
    try {
      const outcome = await application.profiles.patchV1(target.profile_id, patch, actionIdentity);
      const reconciled = reconcileProfileRecord(profiles, pendingDeletions, outcome.profile);
      setProfiles(reconciled.profiles);
      setPendingDeletions(reconciled.pendingDeletions);
      if (outcome.status === 'STALE') {
        if (outcome.profile.state === 'ACTIVE') {
          setProfileBeingEdited(outcome.profile);
          setProfile(outcome.profile);
          setSelectedProfileId(outcome.profile.profile_id);
          setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
          return outcome.profile;
        }
        setProfileBeingEdited(null);
        setError(safeParentFlowErrorMessage({ code: 'INVALID_STATE_TRANSITION' }));
        throw new ParentApplicationError('INVALID_STATE_TRANSITION', 'The profile is no longer active.');
      }
      setProfile(outcome.profile);
      setSelectedProfileId(outcome.profile.profile_id);
      setProfileBeingEdited(null);
      profilePatchActions.current.delete(target.profile_id);
      setStep('profile');
      return outcome.profile;
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
      setProfileFieldErrors(safeProfileFieldMessages(cause));
      throw cause;
    } finally {
      setBusy('');
    }
  }

  function selectProfile(target: ParentProfileViewV1): void {
    setProfile(target);
    setSelectedProfileId(target.profile_id);
    setError('');
    setProfileFieldErrors({});
  }

  async function requestProfileDeletion(target: ParentProfileViewV1): Promise<void> {
    if (isProfileDeletionPending(target.profile_id, pendingDeletions)) return;
    const actionIdentity = retainedMapActionIdentity(profileDeleteActions.current, target.profile_id, target.profile_id);
    setBusy('profile-delete');
    setError('');
    try {
      const pending = await application.profiles.requestDeletionV1(target.profile_id, actionIdentity);
      const reconciled = reconcileProfileRecord(profiles, pendingDeletions, pending);
      setProfiles(reconciled.profiles);
      setPendingDeletions(reconciled.pendingDeletions);
      if (selectedProfileId === target.profile_id) {
        setProfile(null);
        setSelectedProfileId('');
      }
      await refreshPendingDeletion(target.profile_id);
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
      if (cause instanceof ParentApplicationError && cause.code === 'INVALID_STATE_TRANSITION') {
        await refreshPendingDeletion(target.profile_id);
      }
    } finally {
      setBusy('');
    }
  }

  async function refreshPendingDeletion(profileId: string): Promise<void> {
    setPendingDeletionLoadingId(profileId);
    try {
      const record = await application.profiles.getV1(profileId);
      const reconciled = reconcileProfileRecord(profiles, pendingDeletions, record);
      setProfiles(reconciled.profiles);
      setPendingDeletions(reconciled.pendingDeletions);
      if (record.state === 'ACTIVE') profileDeleteActions.current.delete(profileId);
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setPendingDeletionLoadingId('');
    }
  }

  function continueWithProfile(target: ParentProfileViewV1): void {
    setError('');
    if (activeRun) {
      setError(safeParentFlowErrorMessage({ code: 'ACTIVE_RUN_EXISTS' }));
      return;
    }
    resetWorkflow();
    setProfile(target);
    setSelectedProfileId(target.profile_id);
    setStep('topic');
  }
  async function openLessons(mode: 'gallery' | 'picker' = 'picker'): Promise<void> {
    setGalleryMode(mode);
    setGalleryLesson(null);
    setStep(mode === 'gallery' ? 'lesson-library' : 'lessons');
    setLessonLoading(true);
    setLessonError('');
    try {
      const page = await application.lessons.list();
      setLessons(page.items);
      if (mode === 'gallery') {
        const [lessonInvites, groupInvites] = await Promise.allSettled([
          application.lessons.listInvitations(),
          application.lessons.listGroupInvitations(),
        ]);
        if (lessonInvites.status === 'fulfilled') setLessonInvitations(lessonInvites.value.items);
        else setLessonError(displayError(lessonInvites.reason));
        if (groupInvites.status === 'fulfilled') setGroupInvitations(groupInvites.value.items);
        else setLessonError((previous) => previous || displayError(groupInvites.reason));
      }
    } catch (cause) {
      setLessonError(displayError(cause));
    } finally {
      setLessonLoading(false);
    }
  }

  async function chooseLesson(lessonId: string): Promise<void> {
    setLessonLoadingId(lessonId);
    setLessonError('');
    try {
      const detail = await application.lessons.get(lessonId);
      if (galleryMode === 'picker') {
        setLesson(detail);
        setStep('topic');
      } else {
        setGalleryLesson(detail);
      }
    } catch (cause) {
      setLessonError(displayError(cause));
    } finally {
      setLessonLoadingId('');
    }
  }

  async function acceptLessonInvitation(invitationId: string): Promise<void> {
    await respondToInvitation(() => application.lessons.acceptInvitation(invitationId));
  }

  async function declineLessonInvitation(invitationId: string): Promise<void> {
    await respondToInvitation(() => application.lessons.declineInvitation(invitationId));
  }

  async function acceptGroupInvitation(membershipId: string): Promise<void> {
    await respondToInvitation(() => application.lessons.acceptGroupInvitation(membershipId));
  }

  async function respondToInvitation(action: () => Promise<unknown>): Promise<void> {
    try {
      await action();
      await openLessons('gallery');
    } catch (cause) {
      setLessonError(displayError(cause));
    }
  }

  async function createGuide(): Promise<void> {
    if (!guideEnabled || !topic.trim()) return;
    setGuideBusy(true);
    setGuideError('');
    try {
      const receipt = await timeRequest('FLUX.3 · line-sketch', () => application.learning.generateSketchGuide(topic.trim()));
      if (!receipt.image_base64) throw new Error('Modal không trả về ảnh line-sketch.');
      setGuideBase64(receipt.image_base64);
    } catch (cause) {
      setGuideError(displayError(cause));
    } finally {
      setGuideBusy(false);
    }
  }

  function setAudio(value: SelectedAudio | null): void {
    setAudioValue(value);
    setAudioAttempted(false);
    setTranscript(null);
    setTranscriptText('');
    setTranscriptError('');
  }

  async function createContextRun(): Promise<void> {
    if (busy) return;
    const lessonPin = lessonVersionPinFromDetail(lesson);
    const canStart = Boolean(profile) && canBeginContextStep({
      profileId: profile?.profile_id ?? '', topic, adultIdea: idea, lessonPin,
    });
    if (!canStart || !profile || !lessonPin) {
      const code = !profile || !topic.trim() || !idea.trim() ? 'PARENT_CONTEXT_REQUIRED' : 'PARENT_LESSON_PIN_REQUIRED';
      setError(safeParentFlowErrorMessage({ code }));
      return;
    }
    if (activeRun && activeRun.run_id !== contextRun?.run_id) {
      setError(safeParentFlowErrorMessage({ code: 'ACTIVE_RUN_EXISTS' }));
      return;
    }

    const signature = JSON.stringify([profile.profile_id, topic.trim(), idea.trim(), lessonPin]);
    const actionIdentity = retainedActionIdentity(storyRunCreateAction, signature);
    setBusy('context-create');
    setError('');
    try {
      const result = await application.learning.createRunBeforeDrawingV1({
        profileId: profile.profile_id,
        topic,
        adultIdea: idea,
        lessonPin,
        actionIdentity,
      });
      setContextRun(result.story_run);
      setActiveRun(result.story_run);
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function openContextReview(): Promise<void> {
    setContextRun(null);
    setContextConfirmed(false);
    setStep('context');
    await createContextRun();
  }

  async function confirmContext(): Promise<void> {
    if (busy || !contextRun) return;
    const signature = JSON.stringify([
      contextRun.run_id,
      contextRun.context_revision,
      contextRun.context_snapshot_sha256,
    ]);
    const actionIdentity = retainedActionIdentity(contextConfirmationAction, signature);
    setBusy('context-confirmation');
    setError('');
    try {
      const result = await application.learning.confirmRunContextV1(contextRun, actionIdentity);
      setContextRun(result.story_run);
      setActiveRun(result.story_run);
      setContextConfirmed(true);
      setActivityAttempted(true);
      setActivities([]);
      setActivitySource('');
      setActivityError('');
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }
  async function analyzeDrawingForRun(targetRun: StoryRun): Promise<void> {
    if (!photo) return;
    setBusy('understanding');
    setError('');
    try {
      const understanding = await timeRequest(
        'Qwen3.5-VL · hiểu tranh',
        () => application.learning.understandDrawing(targetRun.run_id, photo.base64, photo.mediaType),
      );
      if (!understanding.candidate) throw new Error('API phản hồi nhưng thiếu candidate chủ thể.');
      setCandidate(understanding.candidate);
      setSubject(understanding.candidate.candidate_subject ?? '');
      setUnderstandingRevision(understanding.understanding_revision ?? 1);
      setStep('understanding');
    } catch (cause) {
      try {
        const [latestRun, latestActiveRun] = await Promise.all([
          application.learning.getRun(targetRun.run_id),
          application.learning.getActiveRunV1(),
        ]);
        setRun(latestRun.story_run);
        setActiveRun(latestActiveRun.story_run);
      } catch {
        // Preserve the original AI failure when the follow-up state refresh also fails.
      }
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function confirmReviewedTranscript(): Promise<void> {
    if (busy) return;
    if (!run || !transcript) {
      setTranscriptError('Chưa có bản nhận dạng để xác nhận. Bạn có thể tiếp tục không dùng âm thanh.');
      return;
    }
    setTranscriptError('');
    setBusy('transcript-confirmation');
    let confirmedText: string | null = null;
    try {
      const receipt = await timeRequest('Parent · xác nhận transcript', () => application.learning.confirmTranscript(
        run.run_id,
        transcript.transcript_revision_no,
        transcriptText,
      ));
      confirmedText = receipt.transcript_text;
      setIdea(receipt.transcript_text);
    } catch (cause) {
      setTranscriptError(displayError(cause));
    } finally {
      setBusy('');
    }
    if (confirmedText !== null) await analyzeDrawingForRun(run);
  }

  async function continueWithoutAudio(): Promise<void> {
    if (!run) {
      setTranscriptError('Chưa tạo được buổi học. Quay lại bước xác nhận rồi thử tiếp.');
      return;
    }
    setTranscript(null);
    setTranscriptText('');
    await analyzeDrawingForRun(run);
  }

  async function confirmSubject(): Promise<void> {
    if (!run || !candidate || !subject.trim() || !understandingRevision) return;
    setBusy('subject');
    setError('');
    try {
      const response = await application.learning.confirmSubject(run.run_id, understandingRevision, subject.trim());
      setUnderstandingRevision(response.understanding_revision);
      setRun((current) => current ? { ...current, subject_label: subject.trim(), run_state: 'PREPARATION_REVIEW' } : current);
      setCandidate({ ...candidate, candidate_subject: subject.trim(), decision: 'CONFIRMED_BY_ADULT' });
      setActivityAttempted(false);
      setActivities([]);
      setActivityError('');
      setStep('activity');
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function requestActivities(): Promise<void> {
    setActivityAttempted(true);
    setActivities([]);
    setActivitySource('');
    setActivityError('');
  }
  async function requestStory(instruction?: string): Promise<void> {
    if (!run || !understandingRevision || (storyAttempted && !instruction) || (rewriteCount >= 3 && instruction)) return;
    setStoryAttempted(true);
    if (instruction) setRewriteCount((count) => count + 1);
    setBusy(instruction ? 'rewrite' : 'story');
    setError('');
    try {
      const { updatedRun, parsed, hash } = await timeRequest(
        instruction ? 'Qwen3.5 · viết lại kịch bản' : 'Qwen3.5 · tạo kịch bản',
        async () => {
          const receipt = await application.learning.generateStory(run.run_id, understandingRevision, instruction, rewriteCount);
          const nextRun = receipt.story_run ?? (await application.learning.getRun(run.run_id)).story_run;
          const parsedStory = parseStoryDraft(receipt.story ?? nextRun.story);
          if (!parsedStory) throw new Error('Story không khớp schema story-revision.v1 (cần 5–15 cảnh, 30–90 giây).');
          const storyHash = receipt.story_sha256 ?? nextRun.story_sha256 ?? '';
          if (!storyHash) throw new Error('Story response thiếu story_sha256.');
          return { updatedRun: nextRun, parsed: parsedStory, hash: storyHash };
        },
      );
      setRun(updatedRun);
      setStory(parsed);
      setStorySha256(hash);
      setRewriteInstruction('');
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  async function confirmStory(): Promise<void> {
    if (!run || !story || !storySha256 || !run.story_revision_no) return;
    setBusy('confirm-story');
    setError('');
    try {
      const receipt = await application.learning.confirmStory(run.run_id, run.story_revision_no, storySha256);
      setRun(receipt.story_run);
      setActiveRun(null);
      setStoryConfirmed(true);
      setStep('handoff');
    } catch (cause) {
      setError(displayError(cause));
    } finally {
      setBusy('');
    }
  }

  function resumeActiveRun(): void {
    if (!activeRun) return;
    const selected = selectProfileById(profiles, activeRun.parent_profile_id);
    if (selected) {
      setProfile(selected);
      setSelectedProfileId(selected.profile_id);
    }
    if (activeRun.run_state === 'CONTEXT_PENDING') {
      setContextRun(activeRun);
      setContextConfirmed(false);
      setTopic(activeRun.context_snapshot.topic);
      setIdea(activeRun.context_snapshot.adult_confirmed_idea);
      setStep('context');
      return;
    }
    setError('Buổi học đang mở đã qua bước ngữ cảnh. Không thể tiếp tục trong bước kiểm tra này.');
  }
  async function changePassword(currentPassword: string, nextPassword: string): Promise<void> {
    setAccountError('');
    setBusy('password');
    try {
      await application.account.changePassword(currentPassword, nextPassword);
    } catch (cause) {
      setAccountError(displayError(cause));
      throw cause;
    } finally {
      setBusy('');
    }
  }

  async function resetCurrentPassword(): Promise<void> {
    if (!currentUser?.email) throw new Error('Không có email đăng nhập để gửi hướng dẫn.');
    await application.account.resetPassword(currentUser.email);
  }

  async function resetPassword(email: string): Promise<void> {
    await application.account.resetPassword(email);
  }

  async function signOut(): Promise<void> {
    await application.account.signOut();
    setCurrentUser(null);
    setProfiles([]);
    setProfile(null);
    setSelectedProfileId('');
    setProfileBeingEdited(null);
    setPendingDeletions([]);
    setActiveRun(null);
    setStep('auth');
    setAuthError('');
    resetWorkflow();
  }

  function resetWorkflow(): void {
    setTopic(''); setIdea(''); setLesson(null); setPhoto(null); setRun(null); setCandidate(null); setSubject('');
    setContextRun(null); setContextConfirmed(false); setProfileFieldErrors({});
    setAudioValue(null); setAudioAttempted(false); setTranscript(null); setTranscriptText(''); setTranscriptError('');
    setUnderstandingRevision(0); setActivities([]); setActivitySource(''); setActivityAttempted(false); setActivityError('');
    setStory(null); setStorySha256(''); setStoryAttempted(false); setStoryConfirmed(false); setRewriteCount(0); setRewriteInstruction('');
    setGuideBase64(''); setGuideEnabled(false); setEvents([]); setError(''); setBusy('');
    profileCreateAction.current = null;
    profilePatchActions.current.clear();
    profileDeleteActions.current.clear();
    storyRunCreateAction.current = null;
    contextConfirmationAction.current = null;
  }

  return {
    step, setStep, currentUser, profiles, profile, setProfile, selectedProfileId, profileBeingEdited, setProfileBeingEdited,
    pendingDeletions, pendingDeletionLoadingId, profileFieldErrors,
    publicSettings: application.publicSettings,
    activeRun, topic, setTopic, idea, setIdea, lesson, setLesson, lessons, lessonLoading, lessonLoadingId, lessonError,
    galleryMode, galleryLesson, lessonInvitations, groupInvitations, accountError, guideEnabled, setGuideEnabled,
    guideBase64, guideBusy, guideError, photo, setPhoto, audio, setAudio, transcript, transcriptText, setTranscriptText,
    transcriptError, audioAttempted, transcriptBusy: busy === 'transcription' || busy === 'transcript-confirmation',
    run, contextRun, contextConfirmed, candidate, subject, setSubject, understandingRevision,
    activities, activitySource, activityAttempted, activityError, story, storySha256, storyAttempted,
    storyConfirmed, rewriteCount, rewriteInstruction, setRewriteInstruction, events, busy, error, authError, bootstrapBusy,
    loadParentData, authenticate, signInWithGoogle, resetPassword, createProfileAndReturn, updateProfile,
    selectProfile, requestProfileDeletion, refreshPendingDeletion, continueWithProfile, openLessons, chooseLesson, acceptLessonInvitation,
    declineLessonInvitation, acceptGroupInvitation, createGuide, openContextReview, confirmContext,
    confirmReviewedTranscript, continueWithoutAudio, confirmSubject,
    requestActivities, requestStory, confirmStory, resumeActiveRun, changePassword, resetCurrentPassword, signOut,
    retryContextCreation: createContextRun,
    resetWorkflow, backToProfile: () => { setStep('profile'); setError(''); },
    clearProfileFormErrors: () => setProfileFieldErrors({}),
    clearError: () => setError(''),
  };
}

function displayError(cause: unknown): string {
  if (cause instanceof ParentApplicationError) {
    return `${cause.message} · ${cause.code}${cause.requestId ? ` · ${cause.requestId}` : ''}`;
  }
  return cause instanceof Error ? cause.message : 'Có lỗi không xác định.';
}

function requestIdOf(value: unknown): string | undefined {
  if (typeof value === 'object' && value !== null && 'request_id' in value) {
    const requestId = (value as { request_id?: unknown }).request_id;
    return typeof requestId === 'string' ? requestId : undefined;
  }
  return undefined;
}

type RetainedActionIdentity = {
  signature: string;
  identity: ParentActionIdentity;
};

function retainedActionIdentity(
  reference: { current: RetainedActionIdentity | null },
  signature: string,
): ParentActionIdentity {
  if (!reference.current || reference.current.signature !== signature) {
    reference.current = { signature, identity: createParentActionIdentity() };
  }
  return reference.current.identity;
}

function retainedMapActionIdentity(
  actions: Map<string, RetainedActionIdentity>,
  action: string,
  signature: string,
): ParentActionIdentity {
  const current = actions.get(action);
  if (current?.signature === signature) return current.identity;
  const retained = { signature, identity: createParentActionIdentity() };
  actions.set(action, retained);
  return retained.identity;
}
