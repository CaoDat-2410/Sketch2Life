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
import {
  canStartProfileLearning,
  createUnavailableParentConsentState,
  isParentSessionExpired,
  parentProfileAgeEligibility,
  safeParentIdentityErrorMessage,
} from './workflowTypes';
import type {
  AppStep,
  ParentActiveRunCheckState,
  ParentConsentUiState,
  SelectedAudio,
  SelectedPhoto,
  TimedEvent,
} from './workflowTypes';
import {
  PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE,
  isCurrentAuthorizedLesson,
} from './workflowTypes';
import {
  isActiveOrUnreconciledStoryRun,
  isConfirmedRunSubject,
  isWithinOfflinePhotoLimit,
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
  readRunPinnedLessonActivities,
  readRunUnderstanding,
  readDrawingCandidate,
  reconcileProfileRecord,
  safeParentFlowErrorMessage,
  safeProfileFieldMessages,
  selectProfileById,
} from './parentFlowV1';

const consentState: ParentConsentUiState = createUnavailableParentConsentState('route-not-in-be-handoff');

type ActiveRunPreflightResult =
  | { state: 'confirmed'; activeRun: ParentStoryRunV1 | null }
  | { state: 'unavailable' };

type LessonLibrarySnapshot = {
  summaries: LessonSummary[] | null;
  lessonInvitations: LessonInvitation[] | null;
  groupInvitations: ParentGroupInvitation[] | null;
};

type SelectedPhotoWithRunLock = SelectedPhoto & { locked?: boolean };

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
  const [activeRunCheck, setActiveRunCheck] = useState<ParentActiveRunCheckState>('checking');
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
  const [photo, setPhotoValue] = useState<SelectedPhoto | null>(null);
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
  const runCreationAction = useRef<RetainedActionIdentity | null>(null);
  const profilePatchActions = useRef(new Map<string, RetainedActionIdentity>());
  const profileDeleteActions = useRef(new Map<string, RetainedActionIdentity>());
  const activeRunCheckInFlight = useRef<Promise<ActiveRunPreflightResult> | null>(null);
  const invitationActionsInFlight = useRef(new Set<string>());
  const contextConfirmationAction = useRef<RetainedActionIdentity | null>(null);
  const subjectConfirmationAction = useRef<RetainedActionIdentity | null>(null);
  const storyRevisionAction = useRef<RetainedActionIdentity | null>(null);
  const scriptConfirmationAction = useRef<RetainedActionIdentity | null>(null);
  const runCreationInFlight = useRef(false);
  const drawingAnalysisInFlight = useRef(false);
  const drawingAnalysisAttemptedRunId = useRef<string | null>(null);

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

  function inspectActiveRun(): Promise<ActiveRunPreflightResult> {
    if (activeRunCheckInFlight.current) return activeRunCheckInFlight.current;
    setActiveRunCheck('checking');
    const request = (async (): Promise<ActiveRunPreflightResult> => {
      try {
        const result = await application.learning.getActiveRunV1();
        const confirmedRun = result.story_run ?? null;
        setActiveRun(confirmedRun);
        setActiveRunCheck('confirmed');
        return { state: 'confirmed', activeRun: confirmedRun };
      } catch {
        setActiveRun(null);
        setActiveRunCheck('unavailable');
        return { state: 'unavailable' };
      } finally {
        activeRunCheckInFlight.current = null;
      }
    })();
    activeRunCheckInFlight.current = request;
    return request;
  }

  async function loadParentData(): Promise<void> {
    setBootstrapBusy(true);
    setError('');
    try {
      const user = await application.account.currentUser();
      if (!user) throw new Error('Không tìm thấy phiên đăng nhập.');
      setCurrentUser(user);
      const [profilesResult, runResult] = await Promise.allSettled([
        loadAllProfiles(),
        inspectActiveRun(),
      ]);
      if (profilesResult.status === 'fulfilled') {
        setProfiles(profilesResult.value);
      } else {
        setError(safeProfileActionError(profilesResult.reason));
      }
      if (runResult.status === 'rejected' || runResult.value.state === 'unavailable') {
        setError(PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE);
      }
      setStep('home');
    } catch (cause) {
      setError(safeProfileActionError(cause));
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
      setAuthError(safeParentIdentityErrorMessage(cause));
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
      setAuthError(safeParentIdentityErrorMessage(cause));
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
      setError(safeProfileActionError(cause));
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
      setError(safeProfileActionError(cause));
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
    } catch (cause) {
      setError(safeProfileActionError(cause));
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
      if (record.state === 'DELETE_PENDING') {
        const reconciled = reconcileProfileRecord(profiles, pendingDeletions, record);
        setProfiles(reconciled.profiles);
        setPendingDeletions(reconciled.pendingDeletions);
      } else {
        setError('Máy chủ chưa xác nhận thay đổi trạng thái xóa. Hồ sơ vẫn bị khóa trong ứng dụng.');
      }
    } catch (cause) {
      setError(safeProfileActionError(cause));
    } finally {
      setPendingDeletionLoadingId('');
    }
  }

  async function continueWithProfile(target: ParentProfileViewV1): Promise<void> {
    setError('');
    const preflight = await inspectActiveRun();
    if (preflight.state === 'unavailable') {
      setError(PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE);
      return;
    }
    if (preflight.activeRun) {
      setError(safeParentFlowErrorMessage({ code: 'ACTIVE_RUN_EXISTS' }));
      return;
    }
    if (!ensureLearningProfileAllowed(target)) return;
    resetWorkflow();
    setProfile(target);
    setSelectedProfileId(target.profile_id);
    setStep('topic');
  }

  function ensureLearningProfileAllowed(target: ParentProfileViewV1 | null): boolean {
    if (!target) {
      setError('Chọn một hồ sơ để kiểm tra điều kiện bắt đầu.');
      return false;
    }
    if (isProfileDeletionPending(target.profile_id, pendingDeletions)) {
      setError('Hồ sơ đang chờ xử lý yêu cầu xóa và không thể được sử dụng.');
      return false;
    }
    const ageEligibility = parentProfileAgeEligibility(target);
    if (ageEligibility !== 'supported') {
      setError(profileAgeEligibilityMessage(ageEligibility));
      return false;
    }
    if (!canStartProfileLearning(ageEligibility, consentState.status)) {
      setError(consentStatusMessage(consentState.status));
      return false;
    }
    return true;
  }
  async function openLessons(mode: 'gallery' | 'picker' = 'picker'): Promise<LessonLibrarySnapshot> {
    setGalleryMode(mode);
    setGalleryLesson(null);
    setStep(mode === 'gallery' ? 'lesson-library' : 'lessons');
    setLessonLoading(true);
    setLessonError('');
    setLessons([]);
    setLessonInvitations([]);
    setGroupInvitations([]);
    let snapshot: LessonLibrarySnapshot = {
      summaries: null,
      lessonInvitations: mode === 'gallery' ? null : [],
      groupInvitations: mode === 'gallery' ? null : [],
    };
    try {
      const [pageResult, lessonInviteResult, groupInviteResult] = await Promise.allSettled([
        application.lessons.list(),
        mode === 'gallery' ? application.lessons.listInvitations() : Promise.resolve(null),
        mode === 'gallery' ? application.lessons.listGroupInvitations() : Promise.resolve(null),
      ] as const);
      let nextError = '';
      if (pageResult.status === 'fulfilled') {
        const allowedLessons = pageResult.value.items.filter((item) => item.access_source === 'PUBLIC' || item.access_source === 'SHARED');
        setLessons(allowedLessons);
        snapshot = { ...snapshot, summaries: allowedLessons };
        if (lesson && !allowedLessons.some((item) => item.lesson_id === lesson.lesson_id && item.version_id === lesson.version_id)) {
          setLesson(null);
          nextError = 'Bài giảng đã thay đổi quyền hoặc phiên bản. Hãy kiểm tra lại trước khi tiếp tục.';
        }
      } else {
        if (lesson) setLesson(null);
        nextError = displayError(pageResult.reason);
      }
      if (mode === 'gallery') {
        if (lessonInviteResult.status === 'fulfilled' && lessonInviteResult.value) {
          setLessonInvitations(lessonInviteResult.value.items);
          snapshot = { ...snapshot, lessonInvitations: lessonInviteResult.value.items };
        } else {
          if (!nextError) nextError = displayError(lessonInviteResult.status === 'rejected' ? lessonInviteResult.reason : null);
        }
        if (groupInviteResult.status === 'fulfilled' && groupInviteResult.value) {
          setGroupInvitations(groupInviteResult.value.items);
          snapshot = { ...snapshot, groupInvitations: groupInviteResult.value.items };
        } else {
          if (!nextError) nextError = displayError(groupInviteResult.status === 'rejected' ? groupInviteResult.reason : null);
        }
      }
      setLessonError(nextError);
    } finally {
      setLessonLoading(false);
    }
    return snapshot;
  }

  async function chooseLesson(lessonId: string): Promise<void> {
    setLessonLoadingId(lessonId);
    setLessonError('');
    try {
      const summaries = lessons.filter((item) => item.lesson_id === lessonId);
      const summary = summaries[0];
      if (summaries.length !== 1 || !summary) {
        setLessonError('Danh sách bài giảng đã thay đổi. Hãy tải lại thư viện rồi chọn lại.');
        return;
      }
      const detail = await application.lessons.get(lessonId);
      if (!isCurrentAuthorizedLesson(summary, detail)) {
        setLessonError('Phiên bản hoặc quyền truy cập bài giảng đã thay đổi. Hãy kiểm tra lại thư viện.');
        return;
      }
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
    await respondToInvitation(`lesson:${invitationId}`, () => application.lessons.acceptInvitation(invitationId), {
      kind: 'lesson', id: invitationId, expected: ['ACCEPTED', 'ACTIVE'],
    });
  }

  async function declineLessonInvitation(invitationId: string): Promise<void> {
    await respondToInvitation(`lesson:${invitationId}`, () => application.lessons.declineInvitation(invitationId), {
      kind: 'lesson', id: invitationId, expected: ['DECLINED'],
    });
  }

  async function acceptGroupInvitation(membershipId: string): Promise<void> {
    await respondToInvitation(`group:${membershipId}`, () => application.lessons.acceptGroupInvitation(membershipId), {
      kind: 'group', id: membershipId, expected: ['ACTIVE'],
    });
  }

  async function respondToInvitation(
    actionKey: string,
    action: () => Promise<unknown>,
    verification: {
      kind: 'lesson' | 'group';
      id: string;
      expected: string[];
    },
  ): Promise<void> {
    if (invitationActionsInFlight.current.has(actionKey)) return;
    invitationActionsInFlight.current.add(actionKey);
    setLessonLoadingId(verification.id);
    setLessonError('');
    let actionError = '';
    try {
      await action();
    } catch (cause) {
      actionError = displayError(cause);
    }
    try {
      const refreshed = await openLessons('gallery');
      const listWasRefreshed = refreshed.summaries !== null
        && refreshed.lessonInvitations !== null
        && refreshed.groupInvitations !== null;
      if (!listWasRefreshed) {
        setLessonError('Chưa thể xác nhận trạng thái lời mời từ máy chủ. Hãy kiểm tra lại trước khi thử tiếp.');
      } else {
        const actual = verification.kind === 'lesson'
          ? refreshed.lessonInvitations?.find((item) => item.access_grant_id === verification.id)?.state
          : refreshed.groupInvitations?.find((item) => item.membership_id === verification.id)?.state;
        if (actual && verification.expected.includes(actual.toUpperCase())) {
          setLessonError('');
        } else if (actionError) {
          setLessonError(actionError);
        } else {
          setLessonError('Máy chủ chưa xác nhận thay đổi lời mời. Trạng thái hiện tại vẫn theo máy chủ.');
        }
      }
    } catch {
      setLessonError('Chưa thể kiểm tra trạng thái lời mời từ máy chủ. Hãy kiểm tra lại trước khi thử tiếp.');
    } finally {
      invitationActionsInFlight.current.delete(actionKey);
      setLessonLoadingId('');
    }
  }

  async function createGuide(): Promise<void> {
    if (!guideEnabled) return;
    setGuideBase64('');
    setGuideError('Gợi ý nét vẽ tự động 4–8 bước chưa khả dụng. Bạn vẫn có thể tiếp tục với hướng dẫn của bài học đã ghim.');
  }

  function setAudio(value: SelectedAudio | null): void {
    setAudioValue(null);
    if (value) setError('Chuyển giọng nói thành chữ chưa khả dụng. Bạn vẫn có thể tiếp tục bằng ý tưởng đã nhập.');
  }

  function setPhoto(value: SelectedPhoto): void {
    if ((photo as SelectedPhotoWithRunLock | null)?.locked
      || (contextRun && (contextRun.current_input_revision ?? 0) > 1)) {
      setPhotoValue((current) => current
        ? { ...current, analysisError: 'Ảnh đã được gắn với buổi học này và không thể thay bằng ảnh khác.' }
        : current);
      return;
    }
    setPhotoValue({ ...value, locked: false, analysisError: undefined } as SelectedPhoto);
    setError('');
  }

  function setPhotoMessage(message: string): void {
    setPhotoValue((current) => current ? { ...current, analysisError: message } : current);
  }

  async function createContextRun(): Promise<void> {
    if (busy || runCreationInFlight.current || !ensureLearningProfileAllowed(profile)) return;
    const selectedPhoto = photo;
    const targetProfile = profile;
    if (!selectedPhoto || !isWithinOfflinePhotoLimit(selectedPhoto.fileSizeBytes)) {
      setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_REQUIRED' }));
      return;
    }
    if (contextRun) {
      setPhotoMessage('Buổi học đã được tạo. Hãy kiểm tra ngữ cảnh trước khi tiếp tục.');
      setStep('context');
      return;
    }
    if (!targetProfile) return;
    const pin = lessonVersionPinFromDetail(lesson);
    if (!canBeginContextStep({
      profileId: targetProfile.profile_id, topic, adultIdea: idea, lessonPin: pin,
    })) {
      setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_LESSON_PIN_REQUIRED' }));
      return;
    }

    runCreationInFlight.current = true;
    setBusy('context-create');
    setError('');
    setPhotoMessage('');
    try {
      const preflight = await inspectActiveRun();
      if (preflight.state === 'unavailable') {
        setPhotoMessage(PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE);
        return;
      }
      if (preflight.activeRun) {
        setPhotoMessage(safeParentFlowErrorMessage({ code: 'ACTIVE_RUN_EXISTS' }));
        return;
      }
      const signature = JSON.stringify([targetProfile.profile_id, topic.trim(), idea.trim(), pin]);
      const actionIdentity = retainedActionIdentity(runCreationAction, signature);
      const receipt = await timeRequest('parent-story-run-create', () => application.learning.createRunAfterPhotoV1({
        profileId: targetProfile.profile_id,
        topic,
        adultIdea: idea,
        lessonPin: pin,
        actionIdentity,
      }));
      const run = receipt.story_run;
      const returnedPin = run.lesson_pin_snapshot;
      const pinMatches = pin
        ? Boolean(returnedPin
          && returnedPin.lesson_id === pin.lesson_id
          && returnedPin.version_id === pin.version_id
          && returnedPin.content_sha256 === pin.content_sha256)
        : returnedPin == null;
      if (!run.run_id.trim()
        || run.parent_profile_id !== targetProfile.profile_id
        || !pinMatches
        || !/^[0-9a-f]{64}$/.test(run.context_snapshot_sha256)) {
        throw new ParentApplicationError('PARENT_CONTEXT_SNAPSHOT_INVALID', 'The returned run did not match the reviewed profile and lesson pin.');
      }
      setPhotoValue({ ...selectedPhoto, locked: true, analysisError: undefined } as SelectedPhoto);
      setContextRun(run);
      setActiveRun(run);
      setContextConfirmed(run.context_confirmed === true);
      drawingAnalysisAttemptedRunId.current = null;
      setStep('capture');
      runCreationAction.current = null;
    } catch (cause) {
      setPhotoMessage(safeParentFlowErrorMessage(cause));
    } finally {
      runCreationInFlight.current = false;
      setBusy('');
    }
  }

  async function openContextReview(): Promise<void> {
    if (!ensureLearningProfileAllowed(profile)) return;
    const lessonPin = lessonVersionPinFromDetail(lesson);
    if (!canBeginContextStep({
      profileId: profile?.profile_id ?? '', topic, adultIdea: idea, lessonPin,
    })) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_CONTEXT_REQUIRED' }));
      return;
    }
    setError('');
    setStep('capture');
  }

  function openDrawingGuide(): void {
    if (!ensureLearningProfileAllowed(profile)) return;
    const lessonPin = lessonVersionPinFromDetail(lesson);
    if (!canBeginContextStep({
      profileId: profile?.profile_id ?? '', topic, adultIdea: idea, lessonPin,
    })) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_CONTEXT_REQUIRED' }));
      return;
    }
    setError('');
    setDrawingGuideIndex(0);
    setStep(lesson ? 'drawing-guide' : 'capture');
  }

  function continueToCapture(): void {
    if (!ensureLearningProfileAllowed(profile)) return;
    if (!contextRun) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_CONTEXT_NOT_CONFIRMED' }));
      return;
    }
    const hasConfirmedSubject = subjectConfirmed && isConfirmedRunSubject(contextRun, subject);
    if (!hasConfirmedSubject && contextRun.current_input_revision === 1) {
      setSubjectConfirmed(false);
      setError('');
      setStep('capture');
      return;
    }
    if (!canContinueToCapture(contextConfirmed) || !hasConfirmedSubject) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_CONTEXT_NOT_CONFIRMED' }));
      return;
    }
    setError('');
    setStep('activity');
  }

  async function getLatestRun(runId: string): Promise<ParentStoryRunV1> {
    const receipt = await application.learning.getRunV1(runId);
    if (receipt.story_run.run_id !== runId) {
      throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'The refreshed run did not match the current run.');
    }
    setContextRun(receipt.story_run);
    setActiveRun(receipt.story_run);
    setContextConfirmed(receipt.story_run.context_confirmed === true);
    return receipt.story_run;
  }

  function adoptServerStory(run: ParentStoryRunV1): boolean {
    const readModel = readStoryRevisionReadModel({ story_run: run }, run.run_id);
    if (readModel.kind !== 'valid') return false;
    const parsedStory = parseStoryDraft(readModel.value.story);
    if (!parsedStory) return false;
    setStory({
      ...parsedStory,
      revisionId: readModel.value.storyRevisionId,
      revisionNo: readModel.value.storyRevisionNo,
      sha256: readModel.value.storySha256,
    });
    setStoryDisplayedRunId(readModel.value.runId);
    setStoryRevisionNo(readModel.value.storyRevisionNo);
    setStorySha256(readModel.value.storySha256);
    setRewriteCount(Math.max(0, readModel.value.storyRevisionNo - 1));
    setStoryAttempted(true);
    setStoryConfirmed(run.story_status === 'CONFIRMED');
    storyRevisionAction.current = null;
    scriptConfirmationAction.current = null;
    return true;
  }

  function adoptServerUnderstanding(run: ParentStoryRunV1): boolean {
    const readModel = readRunUnderstanding(run);
    if (!readModel) return false;
    const revisionChanged = readModel.understandingRevision !== understandingRevision;
    const contextChanged = Boolean(contextRun && (
      run.context_revision !== contextRun.context_revision
      || run.context_snapshot_sha256 !== contextRun.context_snapshot_sha256
    ));
    setContextRun(run);
    setActiveRun(run);
    setContextConfirmed(run.context_confirmed === true);
    setCandidate(readModel.candidate);
    setSubject(readModel.subject);
    setUnderstandingRevision(readModel.understandingRevision);
    const confirmed = isConfirmedRunSubject(run, readModel.subject);
    setSubjectConfirmed(confirmed);
    setActivities(confirmed ? readRunPinnedLessonActivities(run.lesson_pin_snapshot) : []);
    setActivityAttempted(confirmed);
    setActivitySource(confirmed ? 'Pinned activities from the exact server run snapshot.' : '');
    setActivityError(confirmed ? 'Chưa thể chọn hoặc gợi ý hoạt động.' : '');
    if (revisionChanged || contextChanged || !confirmed) {
      setStory(null);
      setStoryDisplayedRunId('');
      setStoryRevisionNo(null);
      setStorySha256('');
      setStoryAttempted(false);
      setStoryConfirmed(false);
      setRewriteCount(0);
      storyRevisionAction.current = null;
      scriptConfirmationAction.current = null;
    }
    setPhotoValue((current) => current ? { ...current, locked: true } as SelectedPhoto : current);
    if (!revisionChanged && !contextChanged && confirmed && run.story_revision_id && run.context_confirmed === true) {
      if (adoptServerStory(run)) {
        setStep('story');
      } else {
        setStep('home');
        setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
      }
    } else {
      setStep(confirmed
        ? (run.context_confirmed === true ? 'activity' : 'context')
        : 'understanding');
    }
    return true;
  }

  async function confirmContext(): Promise<void> {
    if (busy || !contextRun) return;
    if (!ensureLearningProfileAllowed(profile)) return;
    const run = contextRun;
    if (!subjectConfirmed || !isConfirmedRunSubject(run, subject)) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_SUBJECT_REQUIRED' }));
      return;
    }
    const signature = JSON.stringify([run.run_id, run.context_revision, run.context_snapshot_sha256]);
    setBusy('context-confirmation');
    setError('');
    try {
      if (contextConfirmationAction.current) {
        const latest = await getLatestRun(run.run_id);
        if (latest.context_confirmed === true) {
          setContextConfirmed(true);
          contextConfirmationAction.current = null;
          return;
        }
        if (latest.context_revision !== run.context_revision
          || latest.context_snapshot_sha256 !== run.context_snapshot_sha256) {
          contextConfirmationAction.current = null;
          setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
          return;
        }
      }
      const actionIdentity = retainedActionIdentity(contextConfirmationAction, signature);
      const result = await application.learning.confirmRunContextV1(run, actionIdentity);
      const confirmedRun = result.story_run;
      setContextRun(confirmedRun);
      setActiveRun(confirmedRun);
      if (confirmedRun.run_id !== run.run_id
        || confirmedRun.context_revision !== run.context_revision
        || confirmedRun.context_snapshot_sha256 !== run.context_snapshot_sha256
        || confirmedRun.context_confirmed !== true) {
        setContextConfirmed(false);
        setError(safeParentFlowErrorMessage({ code: 'PARENT_CONTEXT_SNAPSHOT_INVALID' }));
        return;
      }
      setContextConfirmed(true);
      contextConfirmationAction.current = null;
      setSubjectConfirmed(isConfirmedRunSubject(confirmedRun, subject));
      const pinnedActivities = readRunPinnedLessonActivities(confirmedRun.lesson_pin_snapshot);
      setActivityAttempted(true);
      setActivities(pinnedActivities);
      setActivitySource('Pinned activities from the exact server run snapshot.');
      setActivityError('Chưa thể chọn hoặc gợi ý hoạt động.');
    } catch (cause) {
      if (cause instanceof ParentApplicationError && cause.code === 'STALE_REVISION') {
        contextConfirmationAction.current = null;
        try {
          const latest = await getLatestRun(run.run_id);
          setContextRun(latest);
          setContextConfirmed(latest.context_confirmed === true);
          const latestUnderstanding = readRunUnderstanding(latest);
          if (!latestUnderstanding) {
            setSubjectConfirmed(false);
            setStep('home');
          } else if (latestUnderstanding.understandingRevision !== understandingRevision
            || !isConfirmedRunSubject(latest, subject)
            || latest.context_revision !== run.context_revision
            || latest.context_snapshot_sha256 !== run.context_snapshot_sha256) {
            adoptServerUnderstanding(latest);
          }
        } catch {
          setContextConfirmed(false);
          setSubjectConfirmed(false);
          setStep('home');
        }
      }
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function analyzeDrawingForRun(runId: string | null | undefined): Promise<void> {
    if (busy || drawingAnalysisInFlight.current) return;
    if (!ensureLearningProfileAllowed(profile)) return;
    const selectedPhoto = photo;
    if (typeof runId !== 'string' || !selectedPhoto || !isWithinOfflinePhotoLimit(selectedPhoto.fileSizeBytes)) {
      setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_REQUIRED' }));
      return;
    }
    drawingAnalysisInFlight.current = true;
    setBusy('understanding');
    setError('');
    let uploadAttempted = false;
    try {
      const latest = await getLatestRun(runId);
      const revision = latest.current_input_revision;
      if (typeof revision !== 'number' || !Number.isInteger(revision) || revision < 1) {
        setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
        return;
      }
      if (revision > 1) {
        if (adoptServerUnderstanding(latest)) return;
        setPhotoMessage('Ảnh đã được gắn với buổi học nhưng máy chủ chưa trả về kết quả xem xét. Không gửi lại ảnh trong buổi học này.');
        return;
      }
      if (revision !== 1) {
        setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
        return;
      }
      if (isActiveOrUnreconciledStoryRun(latest)) {
        setPhotoMessage(safeParentFlowErrorMessage({ code: 'AWAITING_RECONCILIATION' }));
        return;
      }
      if (drawingAnalysisAttemptedRunId.current === runId) {
        setPhotoMessage('Chưa có phiên tải lên có thể tiếp tục. Không gửi lại ảnh; hãy kiểm tra trạng thái buổi học sau.');
        return;
      }
      uploadAttempted = true;
      drawingAnalysisAttemptedRunId.current = runId;
      const understanding = await timeRequest(
        'drawing-understanding',
        () => application.learning.understandDrawing(runId, selectedPhoto.base64, selectedPhoto.mediaType),
      );
      const returnedCandidate = readDrawingCandidate(understanding.candidate);
      const understandingRevision = understanding.understanding_revision;
      const inputRevision = understanding.run_input_revision;
      if (!returnedCandidate
        || typeof understandingRevision !== 'number'
        || !Number.isInteger(understandingRevision)
        || understandingRevision < 1
        || inputRevision !== revision + 1) {
        setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
        return;
      }
      const updatedRun = {
        ...latest,
        current_input_revision: inputRevision,
        understanding_revision: understandingRevision,
        candidate: returnedCandidate,
        subject_label: returnedCandidate.candidate_subject ?? null,
      };
      setContextRun(updatedRun);
      setActiveRun(updatedRun);
      setPhotoValue((current) => current ? { ...current, locked: true, analysisError: undefined } as SelectedPhoto : current);
      setCandidate(returnedCandidate);
      setSubject(returnedCandidate.candidate_subject ?? '');
      setUnderstandingRevision(understandingRevision);
      setSubjectConfirmed(false);
      setStep('understanding');
    } catch (cause) {
      if (uploadAttempted) {
        try {
          const latest = await getLatestRun(runId);
          if (latest.current_input_revision !== 1) {
            if (!adoptServerUnderstanding(latest)) {
              setPhotoMessage('Ảnh đã được gắn với buổi học nhưng máy chủ chưa trả về kết quả xem xét. Không gửi lại ảnh trong buổi học này.');
            }
          } else {
            setPhotoMessage('Chưa xác nhận được kết quả tranh. Không có phiên tải lên để tiếp tục và ảnh sẽ không được gửi lại tự động.');
          }
        } catch {
          setPhotoMessage(PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE);
        }
      } else {
        setPhotoMessage(safeParentFlowErrorMessage(cause));
      }
    } finally {
      drawingAnalysisInFlight.current = false;
      setBusy('');
    }
  }

  async function analyzeDrawingForCurrentRun(): Promise<void> {
    if (!contextRun) {
      await createContextRun();
      return;
    }
    await analyzeDrawingForRun(contextRun.run_id);
  }

  async function confirmSubject(): Promise<void> {
    if (busy) return;
    if (!ensureLearningProfileAllowed(profile)) return;
    const run = contextRun;
    const runId = run?.run_id;
    if (!canConfirmDrawingSubject({
      runId,
      candidatePresent: Boolean(candidate),
      understandingRevision,
      subject,
      explicitAdultAction: true,
    }) || !runId || !run) {
      setError(safeParentFlowErrorMessage({ code: 'PARENT_SUBJECT_REQUIRED' }));
      return;
    }
    const confirmedSubject = subject.trim();
    const signature = JSON.stringify([runId, understandingRevision, confirmedSubject]);
    setBusy('subject');
    setError('');
    try {
      if (subjectConfirmationAction.current) {
        const latest = await getLatestRun(runId);
        const currentUnderstanding = readRunUnderstanding(latest);
        if (!currentUnderstanding) {
          subjectConfirmationAction.current = null;
          setSubjectConfirmed(false);
          setError(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
          return;
        }
        if (isConfirmedRunSubject(latest, confirmedSubject)) {
          setCandidate(currentUnderstanding.candidate);
          setSubject(currentUnderstanding.subject);
          setUnderstandingRevision(currentUnderstanding.understandingRevision);
          setSubjectConfirmed(true);
          setActivities(readRunPinnedLessonActivities(latest.lesson_pin_snapshot));
          setActivityAttempted(true);
          setActivitySource('Pinned activities from the exact server run snapshot.');
          setActivityError('Chưa thể chọn hoặc gợi ý hoạt động.');
          setStep(latest.context_confirmed === true ? 'activity' : 'context');
          subjectConfirmationAction.current = null;
          return;
        }
        if (currentUnderstanding.understandingRevision !== understandingRevision) {
          subjectConfirmationAction.current = null;
          adoptServerUnderstanding(latest);
          setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
          return;
        }
        if (subjectConfirmationAction.current.signature !== signature) {
          setError('Hãy kiểm tra kết quả hiện tại rồi gửi lại cùng lựa chọn chủ thể đang chờ.');
          return;
        }
      }
      const actionIdentity = retainedActionIdentity(subjectConfirmationAction, signature);
      const response = await application.learning.confirmSubjectV1(runId, understandingRevision, confirmedSubject, actionIdentity);
      if (response.story_run_id !== runId
        || response.understanding_revision !== understandingRevision
        || response.decision !== 'CONFIRMED') {
        throw new ParentApplicationError('PARENT_SUBJECT_CONFIRMATION_INVALID', 'Subject confirmation did not match the reviewed result.');
      }
      const decision = confirmedSubject === candidate?.candidate_subject ? 'CONFIRMED_BY_ADULT' : 'CORRECTED_BY_ADULT';
      const confirmedRun: ParentStoryRunV1 = {
        ...run,
        understanding_revision: response.understanding_revision,
        subject_label: confirmedSubject,
        candidate: candidate ? { ...candidate, candidate_subject: confirmedSubject, decision } : null,
      };
      setContextRun(confirmedRun);
      setActiveRun(confirmedRun);
      setUnderstandingRevision(response.understanding_revision);
      setCandidate(confirmedRun.candidate ?? null);
      setSubjectConfirmed(true);
      setActivities(readRunPinnedLessonActivities(confirmedRun.lesson_pin_snapshot));
      setActivityAttempted(true);
      setActivitySource('Pinned activities from the exact server run snapshot.');
      setActivityError('Chưa thể chọn hoặc gợi ý hoạt động.');
      setStep('context');
      subjectConfirmationAction.current = null;
    } catch (cause) {
      if (cause instanceof ParentApplicationError && cause.code === 'STALE_REVISION') {
        subjectConfirmationAction.current = null;
        try {
          const latest = await getLatestRun(runId);
          const currentUnderstanding = readRunUnderstanding(latest);
          if (currentUnderstanding) {
            adoptServerUnderstanding(latest);
          } else {
            setSubjectConfirmed(false);
            setStep('home');
            setError(PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE);
          }
        } catch {
          setSubjectConfirmed(false);
          setStep('home');
          setError(PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE);
        }
      }
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function requestActivities(): Promise<void> {
    if (!ensureLearningProfileAllowed(profile)) return;
    const pinned = readRunPinnedLessonActivities(contextRun?.lesson_pin_snapshot);
    setActivityAttempted(true);
    setActivities(pinned);
    setActivitySource(pinned.length ? 'PINNED_LESSON' : 'NONE');
    setActivityError('Chưa thể chọn, gợi ý hoặc thay thế hoạt động.');
  }
  async function requestStory(instruction?: string, allowSameActionRetry = false): Promise<void> {
    if (busy) return;
    if (!ensureLearningProfileAllowed(profile)) return;
    const runId = contextRun?.run_id;
    const normalizedInstruction = instruction?.trim() ?? '';
    const expectedContextRevision = contextRun?.context_revision;
    const expectedContextHash = contextRun?.context_snapshot_sha256 ?? '';
    const signature = runId
      ? JSON.stringify([runId, expectedContextRevision, expectedContextHash, understandingRevision, normalizedInstruction || null, storyRevisionNo, storySha256])
      : '';
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

    const isRewrite = Boolean(normalizedInstruction);
    setBusy(isRewrite ? 'rewrite' : 'story');
    setError('');
    try {
      const latest = await getLatestRun(runId);
      const latestUnderstanding = readRunUnderstanding(latest);
      if (latest.context_revision !== expectedContextRevision
        || latest.context_snapshot_sha256 !== expectedContextHash) {
        storyRevisionAction.current = null;
        if (latestUnderstanding) adoptServerUnderstanding(latest);
        setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      if (latest.context_confirmed !== true
        || !latestUnderstanding
        || latestUnderstanding.understandingRevision !== understandingRevision
        || !isConfirmedRunSubject(latest, subject)) {
        if (latestUnderstanding) adoptServerUnderstanding(latest);
        setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      if (isActiveOrUnreconciledStoryRun(latest)) {
        setError(safeParentFlowErrorMessage({ code: 'AWAITING_RECONCILIATION' }));
        return;
      }

      const latestRead = readStoryRevisionReadModel({ story_run: latest }, runId);
      const latestHasStory = latestRead.kind === 'valid' && parseStoryDraft(latestRead.value.story) !== null;
      if (latest.story_status === 'CONFIRMED' && latestHasStory) {
        adoptServerStory(latest);
        setContextRun(latest);
        setActiveRun(latest);
        return;
      }
      if (latest.story_status === 'CONFIRMED') {
        setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
        return;
      }
      const latestMatchesDisplayed = latestRead.kind === 'valid'
        && latestRead.value.storyRevisionNo === storyRevisionNo
        && latestRead.value.storySha256 === storySha256;
      if (latestHasStory && !latestMatchesDisplayed) {
        adoptServerStory(latest);
        setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      if (latest.story_revision_id && latest.story_status === 'DRAFT' && !latestHasStory) {
        setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
        return;
      }
      if (storyRevisionAction.current && !sameRetainedAction) {
        setError('Hãy kiểm tra và gửi lại yêu cầu viết đang chờ trước khi bắt đầu yêu cầu khác.');
        return;
      }
      if (latest.story_status === 'FAILED' && (!sameRetainedAction || latest.retryable !== true)) {
        setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
        return;
      }
      if (!story && latestHasStory) {
        adoptServerStory(latest);
        return;
      }

      const actionIdentity = retainedActionIdentity(storyRevisionAction, signature);
      const isNewAction = !sameRetainedAction;
      setStoryAttempted(true);
      if (isRewrite && isNewAction) setRewriteCount((count) => count + 1);
      const receipt = await timeRequest(
        isRewrite ? 'story-rewrite' : 'story-create',
        () => application.learning.createStoryRevisionV1(
          runId,
          understandingRevision,
          normalizedInstruction || undefined,
          actionIdentity,
        ),
      );
      const readModel = readStoryRevisionReadModel(receipt, runId);
      if (readModel.kind !== 'valid' || readModel.value.storyStatus !== 'DRAFT') {
        throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'Story response lacks a validated draft revision pin.');
      }
      const returnedRun = receipt.story_run;
      if (!returnedRun || returnedRun.run_id !== runId) {
        throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'Story response lacks the current server run.');
      }
      const parsedStory = parseStoryDraft(readModel.value.story);
      if (!parsedStory) {
        throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'Story response does not match the required schema.');
      }
      const pinnedStory = {
        ...parsedStory,
        revisionId: readModel.value.storyRevisionId,
        revisionNo: readModel.value.storyRevisionNo,
        sha256: readModel.value.storySha256,
      };
      setStory(pinnedStory);
      setStoryDisplayedRunId(readModel.value.runId);
      setStoryRevisionNo(readModel.value.storyRevisionNo);
      setStorySha256(readModel.value.storySha256);
      setRewriteCount(Math.max(0, readModel.value.storyRevisionNo - 1));
      setContextRun(returnedRun);
      setActiveRun(returnedRun);
      setRewriteInstruction('');
      storyRevisionAction.current = null;
      scriptConfirmationAction.current = null;
    } catch (cause) {
      if (cause instanceof ParentApplicationError && cause.code === 'STALE_REVISION') {
        storyRevisionAction.current = null;
        try {
          const latest = await getLatestRun(runId);
          const latestUnderstanding = readRunUnderstanding(latest);
          if (latestUnderstanding) adoptServerUnderstanding(latest);
        } catch {
          setStoryConfirmed(false);
        }
      }
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function confirmStory(): Promise<void> {
    if (busy) return;
    if (!ensureLearningProfileAllowed(profile)) return;
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
    const revisionNo = storyRevisionNo;
    const revisionSha256 = storySha256;
    const expectedContextRevision = contextRun?.context_revision;
    const expectedContextHash = contextRun?.context_snapshot_sha256 ?? '';
    const signature = JSON.stringify([runId, revisionNo, revisionSha256]);
    setBusy('confirm-story');
    setError('');
    try {
      const latest = await getLatestRun(runId);
      if (latest.context_confirmed !== true
        || latest.context_revision !== expectedContextRevision
        || latest.context_snapshot_sha256 !== expectedContextHash
        || latest.understanding_revision !== understandingRevision
        || !isConfirmedRunSubject(latest, subject)) {
        const latestUnderstanding = readRunUnderstanding(latest);
        if (latestUnderstanding) adoptServerUnderstanding(latest);
        setStoryConfirmed(false);
        setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      if (latest.story_status === 'CONFIRMED'
        && latest.story_revision_no === revisionNo
        && latest.story_sha256 === revisionSha256) {
        if (!adoptServerStory(latest)) {
          setStoryConfirmed(false);
          setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
          return;
        }
        setStoryConfirmed(true);
        return;
      }
      if (latest.story_status !== 'DRAFT'
        || latest.story_revision_no !== revisionNo
        || latest.story_sha256 !== revisionSha256) {
        if (latest.story_revision_id) adoptServerStory(latest);
        setStoryConfirmed(false);
        setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      if (scriptConfirmationAction.current && scriptConfirmationAction.current.signature !== signature) {
        setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      const actionIdentity = retainedActionIdentity(scriptConfirmationAction, signature);
      const receipt = await application.learning.confirmScriptV1(runId, revisionNo, revisionSha256, actionIdentity);
      const confirmedRun = receipt.story_run;
      if (confirmedRun.run_id !== runId
        || confirmedRun.story_revision_no !== revisionNo
        || confirmedRun.story_sha256 !== revisionSha256
        || confirmedRun.story_status !== 'CONFIRMED') {
        throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'Script confirmation did not match the displayed revision.');
      }
      setContextRun(confirmedRun);
      setActiveRun(confirmedRun);
      setStoryConfirmed(true);
      scriptConfirmationAction.current = null;
    } catch (cause) {
      if (cause instanceof ParentApplicationError && cause.code === 'STALE_REVISION') {
        try {
          const latest = await getLatestRun(runId);
          if (latest.story_revision_id) adoptServerStory(latest);
          scriptConfirmationAction.current = null;
        } catch {
          setStoryConfirmed(false);
        }
      }
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function resumeActiveRun(): Promise<void> {
    const preflight = await inspectActiveRun();
    if (preflight.state === 'unavailable') {
      setError(PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE);
      return;
    }
    if (!preflight.activeRun) {
      setError('Máy chủ chưa xác nhận buổi học nào đang mở.');
      return;
    }
    const run = preflight.activeRun;
    const selected = selectProfileById(profiles, run.parent_profile_id);
    if (!ensureLearningProfileAllowed(selected)) return;
    resetWorkflow();
    if (selected) {
      setProfile(selected);
      setSelectedProfileId(selected.profile_id);
    }
    setContextRun(run);
    setActiveRun(run);
    setContextConfirmed(run.context_confirmed === true);
    setTopic(run.context_snapshot.topic);
    setIdea(run.context_snapshot.adult_confirmed_idea);
    if (readRunUnderstanding(run)) {
      if (adoptServerUnderstanding(run)) return;
    }
    if (run.current_input_revision === 1) {
      setStep('capture');
      return;
    }
    setStep('home');
    setError('Buổi học đã có ảnh được máy chủ ghi nhận nhưng chưa có kết quả xem xét. Không gửi lại ảnh; hãy kiểm tra trạng thái sau.');
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
    try {
      await application.account.signOut();
      setAuthError('');
    } catch (cause) {
      setAuthError(safeParentIdentityErrorMessage(cause));
    } finally {
      setCurrentUser(null);
      setProfiles([]);
      setProfile(null);
      setSelectedProfileId('');
      setProfileBeingEdited(null);
      setPendingDeletions([]);
      setActiveRun(null);
      setActiveRunCheck('checking');
      setStep('auth');
      resetWorkflow();
    }
  }

  function resetWorkflow(): void {
    setTopic(''); setIdea(''); setLesson(null); setPhotoValue(null); setCandidate(null); setSubject('');
    setContextRun(null); setContextConfirmed(false); setProfileFieldErrors({});
    setAudioValue(null); setDrawingGuideIndex(0); setUnderstandingRevision(0); setSubjectConfirmed(false);
    setActivities([]); setActivitySource(''); setActivityAttempted(false); setActivityError('');
    setStory(null); setStoryDisplayedRunId(''); setStoryRevisionNo(null); setStorySha256('');
    setStoryAttempted(false); setStoryConfirmed(false); setRewriteCount(0); setRewriteInstruction('');
    setGuideBase64(''); setGuideEnabled(false); setEvents([]); setError(''); setBusy('');
    profileCreateAction.current = null;
    profilePatchActions.current.clear();
    profileDeleteActions.current.clear();
    runCreationAction.current = null;
    drawingAnalysisAttemptedRunId.current = null;
    contextConfirmationAction.current = null;
    subjectConfirmationAction.current = null;
    storyRevisionAction.current = null;
    scriptConfirmationAction.current = null;
  }

  return {
    step, setStep, currentUser, profiles, profile, setProfile, selectedProfileId, profileBeingEdited, setProfileBeingEdited,
    pendingDeletions, pendingDeletionLoadingId, profileFieldErrors, consentState,
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
  return safeParentIdentityErrorMessage(cause);
}

function safeProfileActionError(cause: unknown): string {
  return isParentSessionExpired(cause)
    ? safeParentIdentityErrorMessage(cause)
    : safeParentFlowErrorMessage(cause);
}

function profileAgeEligibilityMessage(eligibility: 'legacy-read-only' | 'unavailable'): string {
  if (eligibility === 'legacy-read-only') {
    return 'Hồ sơ thuộc dải tuổi cũ (121–155 tháng), chỉ có thể xem hoặc xóa; không thể bắt đầu buổi học.';
  }
  return 'Chưa xác nhận được nhóm tuổi và phiên bản của hồ sơ. Hãy kiểm tra lại trước khi tiếp tục.';
}

function consentStatusMessage(status: ParentConsentUiState['status']): string {
  if (status.state === 'unavailable') {
    return 'Chưa thể xác nhận trạng thái đồng ý từ máy chủ. Ghi nhận hoặc thu hồi đồng ý hiện chưa khả dụng.';
  }
  if (status.state === 'pending') return 'Yêu cầu xác nhận sự đồng ý vẫn đang chờ máy chủ.';
  if (status.state === 'revoked') return 'Quyền xử lý đã bị thu hồi. Chưa thể bắt đầu buổi học.';
  if (status.state === 'confirmed') return 'Hãy kiểm tra lại phiên bản đồng ý trước khi tiếp tục.';
  return 'Chưa có trạng thái đồng ý được máy chủ xác nhận. Chưa thể bắt đầu buổi học.';
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
