import { useRef, useState } from 'react';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { createParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import { parseStoryDraft } from '../../domain/storyDraft';
import type {
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
  SuggestedActivity,
} from '../../domain/types';
import type { AppStep, SelectedAudio, SelectedPhoto, TimedEvent } from './workflowTypes';
import {
  canAnalyzeDrawing,
  canBeginContextStep,
  canConfirmDisplayedStory,
  canConfirmDrawingSubject,
  canContinueToCapture,
  canRequestStoryRevision,
  isProfileDeletionPending,
  lessonVersionPinFromDetail,
  mergeProfilePage,
  readStoryRevisionReadModel,
  nextProfileCursor,
  readDrawingCandidate,
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
  const [drawingGuideIndex, setDrawingGuideIndex] = useState(0);
  const [photo, setPhoto] = useState<SelectedPhoto | null>(null);
  const [audio, setAudioValue] = useState<SelectedAudio | null>(null);
  const [contextRun, setContextRun] = useState<ParentStoryRunV1 | null>(null);
  const [contextConfirmed, setContextConfirmed] = useState(false);
  const [candidate, setCandidate] = useState<ParentCandidate | null>(null);
  const [subject, setSubject] = useState('');
  const [subjectConfirmed, setSubjectConfirmed] = useState(false);
  const [understandingRevision, setUnderstandingRevision] = useState(0);
  const [activities, setActivities] = useState<SuggestedActivity[]>([]);
  const [activitySource, setActivitySource] = useState('');
  const [activityAttempted, setActivityAttempted] = useState(false);
  const [activityError, setActivityError] = useState('');
  const [story, setStory] = useState<StoryDraft | null>(null);
  const [storyDisplayedRunId, setStoryDisplayedRunId] = useState('');
  const [storyRevisionNo, setStoryRevisionNo] = useState<number | null>(null);
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
  const subjectConfirmationAction = useRef<RetainedActionIdentity | null>(null);
  const storyRevisionAction = useRef<RetainedActionIdentity | null>(null);
  const scriptConfirmationAction = useRef<RetainedActionIdentity | null>(null);
  const drawingAnalysisInFlight = useRef(false);

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
      storyRunCreateAction.current = null;
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function openContextReview(): Promise<void> {
    const lessonPin = lessonVersionPinFromDetail(lesson);
    if (!canBeginContextStep({
      profileId: profile?.profile_id ?? '', topic, adultIdea: idea, lessonPin,
    })) {
      const code = !profile || !topic.trim() || !idea.trim() ? 'PARENT_CONTEXT_REQUIRED' : 'PARENT_LESSON_PIN_REQUIRED';
      setError(safeParentFlowErrorMessage({ code }));
      return;
    }
    setError('');
    setStep('context');
  }

  function openDrawingGuide(): void {
    const lessonPin = lessonVersionPinFromDetail(lesson);
    if (!canBeginContextStep({
      profileId: profile?.profile_id ?? '', topic, adultIdea: idea, lessonPin,
    })) {
      const code = !profile || !topic.trim() || !idea.trim() ? 'PARENT_CONTEXT_REQUIRED' : 'PARENT_LESSON_PIN_REQUIRED';
      setError(safeParentFlowErrorMessage({ code }));
      return;
    }
    setError('');
    setDrawingGuideIndex(0);
    setStep('drawing-guide');
  }

  function continueToCapture(): void {
    if (!contextRun || !canContinueToCapture(contextConfirmed)) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_CONTEXT_NOT_CONFIRMED' }));
      return;
    }
    setError('');
    setStep('capture');
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
      contextConfirmationAction.current = null;
      setSubjectConfirmed(false);
      setActivityAttempted(false);
      setActivities([]);
      setActivitySource('');
      setActivityError('');
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }
  async function analyzeDrawingForRun(runId: string | null | undefined): Promise<void> {
    if (busy || drawingAnalysisInFlight.current) return;
    const selectedPhoto = photo;
    if (typeof runId !== 'string'
      || !canAnalyzeDrawing({ runId, contextConfirmed, photoSelected: Boolean(selectedPhoto) })
      || !selectedPhoto) {
      setError(safeParentFlowErrorMessage({ code: contextConfirmed ? 'PARENT_DRAWING_REQUIRED' : 'PARENT_CONTEXT_NOT_CONFIRMED' }));
      return;
    }
    drawingAnalysisInFlight.current = true;
    setBusy('understanding');
    setError('');
    setCandidate(null);
    setSubject('');
    setSubjectConfirmed(false);
    setUnderstandingRevision(0);
    try {
      const understanding = await timeRequest(
        'Qwen3.5-VL · hiểu tranh',
        () => application.learning.understandDrawing(runId, selectedPhoto.base64, selectedPhoto.mediaType),
      );
      const returnedCandidate = readDrawingCandidate(understanding.candidate);
      const revision = understanding.understanding_revision;
      if (!returnedCandidate || typeof revision !== 'number' || !Number.isInteger(revision) || revision < 1) {
        setError(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
        return;
      }
      setCandidate(returnedCandidate);
      setSubject(returnedCandidate.candidate_subject ?? '');
      setUnderstandingRevision(revision);
      setSubjectConfirmed(false);
      setStep('understanding');
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      drawingAnalysisInFlight.current = false;
      setBusy('');
    }
  }

  async function analyzeDrawingForCurrentRun(): Promise<void> {
    await analyzeDrawingForRun(contextRun?.run_id);
  }

  async function confirmSubject(): Promise<void> {
    if (busy) return;
    const runId = contextRun?.run_id;
    if (!canConfirmDrawingSubject({
      runId,
      candidatePresent: Boolean(candidate),
      understandingRevision,
      subject,
      explicitAdultAction: true,
    }) || !runId) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_SUBJECT_REQUIRED' }));
      return;
    }
    const confirmedSubject = subject.trim();
    const signature = JSON.stringify([runId, understandingRevision, confirmedSubject]);
    const actionIdentity = retainedActionIdentity(subjectConfirmationAction, signature);
    setBusy('subject');
    setError('');
    try {
      const response = await application.learning.confirmSubjectV1(runId, understandingRevision, confirmedSubject, actionIdentity);
      if (response.story_run_id !== runId || response.understanding_revision !== understandingRevision) {
        throw new ParentApplicationError('PARENT_SUBJECT_CONFIRMATION_INVALID', 'Subject confirmation did not match the reviewed result.');
      }
      setUnderstandingRevision(response.understanding_revision);
      setCandidate((current) => current ? { ...current, candidate_subject: confirmedSubject, decision: response.decision } : current);
      setSubjectConfirmed(true);
      setActivityAttempted(false);
      setActivities([]);
      setActivityError('');
      setStep('activity');
      subjectConfirmationAction.current = null;
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
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
  async function requestStory(instruction?: string, allowSameActionRetry = false): Promise<void> {
    if (busy) return;
    const runId = contextRun?.run_id;
    const normalizedInstruction = instruction?.trim() ?? '';
    const signature = runId ? JSON.stringify([runId, understandingRevision, normalizedInstruction || null]) : '';
    const sameRetainedAction = Boolean(signature && storyRevisionAction.current?.signature === signature);
    const canRequest = canRequestStoryRevision({
      runId,
      understandingRevision,
      storyPresent: Boolean(story),
      storyAttempted,
      rewriteCount,
      rewriteInstruction: normalizedInstruction,
      storyConfirmed,
      subjectConfirmed,
      allowSameActionRetry: allowSameActionRetry || sameRetainedAction,
    });
    if (!canRequest || !runId) {
      const code = normalizedInstruction && rewriteCount >= 3 ? 'PARENT_STORY_REWRITE_LIMIT' : 'PARENT_STORY_REVISION_INVALID';
      setError(safeParentFlowErrorMessage({ code }));
      return;
    }
    const isNewAction = !sameRetainedAction;
    const actionIdentity = retainedActionIdentity(storyRevisionAction, signature);
    const isRewrite = Boolean(normalizedInstruction);
    setStoryAttempted(true);
    if (isRewrite && isNewAction) setRewriteCount((count) => count + 1);
    setBusy(isRewrite ? 'rewrite' : 'story');
    setError('');
    try {
      const receipt = await timeRequest(
        isRewrite ? 'Qwen3.5 · viết lại kịch bản' : 'Qwen3.5 · tạo kịch bản',
        () => application.learning.createStoryRevisionV1(
          runId,
          understandingRevision,
          normalizedInstruction || undefined,
          actionIdentity,
        ),
      );
      const readModel = readStoryRevisionReadModel(receipt, runId);
      if (readModel.kind !== 'valid') {
        throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'Story response lacks a validated revision pin.');
      }
      const parsedStory = parseStoryDraft(readModel.value.story);
      if (!parsedStory) {
        throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'Story response does not match the required schema.');
      }
      setStory(parsedStory);
      setStoryDisplayedRunId(readModel.value.runId);
      setStoryRevisionNo(readModel.value.storyRevisionNo);
      setStorySha256(readModel.value.storySha256);
      setRewriteInstruction('');
      storyRevisionAction.current = null;
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function confirmStory(): Promise<void> {
    if (busy) return;
    const runId = contextRun?.run_id;
    if (!canConfirmDisplayedStory({
      runId,
      displayedRunId: storyDisplayedRunId,
      storyPresent: Boolean(story),
      subjectConfirmed,
      storyConfirmed,
      storyRevisionNo,
      storySha256,
    }) || !runId || storyRevisionNo === null) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_NOT_CONFIRMABLE' }));
      return;
    }
    const signature = JSON.stringify([runId, storyRevisionNo, storySha256]);
    const actionIdentity = retainedActionIdentity(scriptConfirmationAction, signature);
    setBusy('confirm-story');
    setError('');
    try {
      const receipt = await application.learning.confirmScriptV1(runId, storyRevisionNo, storySha256, actionIdentity);
      setContextRun(receipt.story_run);
      setActiveRun(null);
      setStoryConfirmed(true);
      scriptConfirmationAction.current = null;
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
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
    setTopic(''); setIdea(''); setLesson(null); setPhoto(null); setCandidate(null); setSubject('');
    setContextRun(null); setContextConfirmed(false); setProfileFieldErrors({});
    setAudioValue(null); setDrawingGuideIndex(0); setUnderstandingRevision(0); setSubjectConfirmed(false);
    setActivities([]); setActivitySource(''); setActivityAttempted(false); setActivityError('');
    setStory(null); setStoryDisplayedRunId(''); setStoryRevisionNo(null); setStorySha256('');
    setStoryAttempted(false); setStoryConfirmed(false); setRewriteCount(0); setRewriteInstruction('');
    setGuideBase64(''); setGuideEnabled(false); setEvents([]); setError(''); setBusy('');
    profileCreateAction.current = null;
    profilePatchActions.current.clear();
    profileDeleteActions.current.clear();
    storyRunCreateAction.current = null;
    contextConfirmationAction.current = null;
    subjectConfirmationAction.current = null;
    storyRevisionAction.current = null;
    scriptConfirmationAction.current = null;
  }

  return {
    step, setStep, currentUser, profiles, profile, setProfile, selectedProfileId, profileBeingEdited, setProfileBeingEdited,
    pendingDeletions, pendingDeletionLoadingId, profileFieldErrors,
    publicSettings: application.publicSettings,
    activeRun, topic, setTopic, idea, setIdea, lesson, setLesson, lessons, lessonLoading, lessonLoadingId, lessonError,
    galleryMode, galleryLesson, lessonInvitations, groupInvitations, accountError, guideEnabled, setGuideEnabled,
    guideBase64, guideBusy, guideError, photo, setPhoto, audio, setAudio,
    contextRun, contextConfirmed, candidate, subject, setSubject, subjectConfirmed, understandingRevision,
    activities, activitySource, activityAttempted, activityError, story, storyDisplayedRunId, storyRevisionNo,
    storySha256, storyAttempted,
    storyConfirmed, rewriteCount, rewriteInstruction, setRewriteInstruction, events, busy, error, authError, bootstrapBusy,
    loadParentData, authenticate, signInWithGoogle, resetPassword, createProfileAndReturn, updateProfile,
    selectProfile, requestProfileDeletion, refreshPendingDeletion, continueWithProfile, openLessons, chooseLesson, acceptLessonInvitation,
    declineLessonInvitation, acceptGroupInvitation, createGuide, openDrawingGuide, openContextReview, confirmContext,
    continueToCapture, analyzeDrawingForCurrentRun, confirmSubject,
    requestActivities, requestStory, confirmStory, drawingGuideIndex, setDrawingGuideIndex,
    resumeActiveRun, changePassword, resetCurrentPassword, signOut,
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
