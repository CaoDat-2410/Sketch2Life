import { useEffect, useRef, useState } from 'react';
import { AppState } from 'react-native';
import * as Crypto from 'expo-crypto';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { createParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import { parseStoryDraft } from '../../domain/storyDraft';
import { isResolvedTopicConsistent } from '../../domain/topicMatching';
import {
  buildSubjectRolesRequest,
  initialSubjectRoles,
  mainSubjectLabel,
  promoteToMain,
  setRoleLabel,
  toggleSecondaryUse,
  type SubjectRolesRequest,
} from '../../domain/subjectRoles';
import type {
  LessonDetail,
  LessonInvitation,
  LessonSummary,
  ParentDrawingCandidateV1,
  ParentDrawingSubjectCardV1,
  ParentDrawingSubjectSuggestionSetV1,
  ParentActivityListV1,
  ParentActivitySelectionRequestV1,
  ParentCustomSubjectValidationV1,
  ParentGroupInvitation,
  ParentProfileDeletePendingV1,
  ParentPlaybackSourceV1,
  ParentProfileViewV1,
  ParentSubjectRoleV1,
  ParentTopicCardV1,
  ParentTopicSuggestionSetV1,
  ParentRunTranscriptV1,
  ParentStoryRunV1,
  ParentUser,
  ParentVideoReasonCodeV1,
  StoryDraft,
} from '../../domain/types';
import { requireLiveStoryRun } from '../../application/storyRunResult';
import {
  BACKGROUND_RUN_STATES,
  classifyDrawingProgress,
  rewriteRangeForRun,
  classifyRewriteProgress,
  classifyTranscript,
  isClosedRunState,
  readVideoPanel,
  readActivityListV1,
} from '../../application/parentPhaseB';
import {
  RunWaitCancelled,
  delayWithSignal,
  waitForRun,
  type RunWaitAppState,
} from '../../application/parentRunWait';
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
  isProfileDeletionPending,
  lessonVersionPinFromDetail,
  mergeProfilePage,
  readStoryRevisionReadModel,
  nextProfileCursor,
  readRunUnderstanding,
  readSubjectConfirmationOutcome,
  readDrawingCandidate,
  reconcileProfileRecord,
  safeParentFlowErrorMessage,
  safeProfileFieldMessages,
  subjectRolesIssueMessage,
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
  const [videoBackStep, setVideoBackStep] = useState<AppStep>('home');
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
  const [selectedTopicId, setSelectedTopicId] = useState('');
  const [topicDraftId, setTopicDraftId] = useState('');
  const [topicSuggestionSets, setTopicSuggestionSets] = useState<ParentTopicSuggestionSetV1[]>([]);
  const [topicSuggestions, setTopicSuggestions] = useState<ParentTopicCardV1[]>([]);
  const [topicSuggestionBusy, setTopicSuggestionBusy] = useState(false);
  const [topicSuggestionError, setTopicSuggestionError] = useState('');
  const lastTopicSuggestionSetId = useRef('');
  const topicSuggestionRequestId = useRef('');
  const subjectSuggestionRequestId = useRef('');
  const [subjectSuggestionSets, setSubjectSuggestionSets] = useState<ParentDrawingSubjectSuggestionSetV1[]>([]);
  const [subjectSuggestions, setSubjectSuggestions] = useState<ParentDrawingSubjectCardV1[]>([]);
  const [subjectSuggestionBusy, setSubjectSuggestionBusy] = useState(false);
  const [subjectSuggestionError, setSubjectSuggestionError] = useState('');
  const [intendedDrawingSubject, setIntendedDrawingSubject] = useState('');
  const [customDrawingSubject, setCustomDrawingSubject] = useState('');
  const [subjectValidationMessage, setSubjectValidationMessage] = useState('');
  const [customSubjectValidated, setCustomSubjectValidated] = useState(false);
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
  const [candidate, setCandidate] = useState<ParentDrawingCandidateV1 | null>(null);
  const [subject, setSubject] = useState('');
  const [subjectRoles, setSubjectRoles] = useState<ParentSubjectRoleV1[]>([]);
  useEffect(() => {
    setSubjectRoles(candidate ? initialSubjectRoles(candidate) : []);
  }, [candidate]);
  const [subjectConfirmed, setSubjectConfirmed] = useState(false);
  const [understandingRevision, setUnderstandingRevision] = useState(0);
  const [activitySuggestions, setActivitySuggestions] = useState<ParentActivityListV1 | null>(null);
  const [selectedActivityIndex, setSelectedActivityIndex] = useState<number | null>(null);
  const [activityBusy, setActivityBusy] = useState(false);
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
  const [transcript, setTranscript] = useState<ParentRunTranscriptV1 | null>(null);
  const [transcriptText, setTranscriptTextValue] = useState('');
  const [transcriptWaiting, setTranscriptWaiting] = useState(false);
  const [retakeAvailable, setRetakeAvailable] = useState(false);
  const [playback, setPlayback] = useState<ParentPlaybackSourceV1 | null>(null);
  const [videoReason, setVideoReason] = useState<ParentVideoReasonCodeV1 | null>(null);
  const [markingUnsuitable, setMarkingUnsuitable] = useState(false);
  const [spentStoryRevisionNo, setSpentStoryRevisionNo] = useState<number | null>(null);
  const [confirmedStoryRevisionNo, setConfirmedStoryRevisionNo] = useState<number | null>(null);
  const [rewriteNotice, setRewriteNotice] = useState('');
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
  const scriptConfirmationAction = useRef<RetainedActionIdentity | null>(null);
  const activitySelectionAction = useRef<RetainedActionIdentity | null>(null);
  const activityCancelAction = useRef<RetainedActionIdentity | null>(null);
  const runCreationInFlight = useRef(false);
  const drawingAnalysisInFlight = useRef(false);
  const drawingUploadAction = useRef<RetainedKeySet<'create' | 'complete' | 'attach'> | null>(null);
  const voiceUploadAction = useRef<RetainedKeySet<'create' | 'complete' | 'idea'> | null>(null);
  const audioSubmittedRunId = useRef<string | null>(null);
  const transcriptCorrectionAction = useRef<RetainedActionIdentity | null>(null);
  const transcriptConfirmAction = useRef<RetainedActionIdentity | null>(null);
  const storyRewriteAction = useRef<RetainedActionIdentity | null>(null);
  const videoRequestAction = useRef<RetainedActionIdentity | null>(null);
  const videoUnsuitableAction = useRef<RetainedActionIdentity | null>(null);
  const completeRunAction = useRef<RetainedActionIdentity | null>(null);
  const waitAbort = useRef<AbortController | null>(null);
  const playbackOpenedAt = useRef(0);
  const playbackAutoRetries = useRef(0);
  const retakeUsed = useRef(false);
  const busyEpoch = useRef(0);
  /** Set when the adult leaves a waiting screen: a chain that was already running may not start another wait. */
  const waitsBlocked = useRef(false);

  // A wait must never outlive the controller (sign-out, unmount): it only reads, but it holds a timer.
  useEffect(() => () => { waitAbort.current?.abort(); }, []);

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
      const message = safeParentIdentityErrorMessage(cause);
      if (__DEV__) {
        const stage = cause && typeof cause === 'object' && 'diagnosticStage' in cause
          && typeof cause.diagnosticStage === 'string'
          ? cause.diagnosticStage
          : 'unknown_auth_stage';
        const diagnostic = cause instanceof ParentApplicationError
          ? `${stage}:${cause.code}`
          : cause instanceof Error
            ? cause.name
            : 'UNKNOWN_AUTH_FAILURE';
        console.warn('parent_auth_ui_failure', { diagnostic });
        setAuthError(`${message} (${diagnostic})`);
      } else {
        setAuthError(message);
      }
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
    setStep('entry');
  }

  async function beginTopicPath(): Promise<void> {
    const draftId = Crypto.randomUUID();
    topicSuggestionRequestId.current = Crypto.randomUUID();
    subjectSuggestionRequestId.current = '';
    const previousSetId = lastTopicSuggestionSetId.current;
    setTopicDraftId(draftId);
    setTopic('');
    setSelectedTopicId('');
    setIntendedDrawingSubject('');
    setCustomDrawingSubject('');
    setSubjectSuggestions([]);
    setSubjectSuggestionSets([]);
    setSubjectSuggestionError('');
    setTopicSuggestionSets([]);
    setTopicSuggestions([]);
    setTopicSuggestionError('');
    setStep('topic');
    await loadTopicSuggestionSet(draftId, previousSetId ? [previousSetId] : []);
  }

  async function loadTopicSuggestionSet(draftId: string, excludedSetIds: string[]): Promise<void> {
    if (!topicSuggestionRequestId.current) topicSuggestionRequestId.current = Crypto.randomUUID();
    const requestId = topicSuggestionRequestId.current;
    setTopicSuggestionBusy(true);
    setTopicSuggestionError('');
    try {
      const result = await application.learning.listTopicSuggestions(draftId, excludedSetIds, requestId);
      if (result.contract !== 'ParentTopicSuggestionSetV1'
        || result.request_id !== requestId
        || result.draft_id !== draftId
        || result.cards.length !== 3
        || new Set(result.cards.map((card) => card.topic_id)).size !== 3
        || excludedSetIds.includes(result.set_id)) {
        throw new ParentApplicationError('PARENT_TOPIC_SUGGESTION_INVALID', 'Chưa nhận được ba gợi ý chủ đề hợp lệ.');
      }
      setTopicSuggestionSets((current) => [...current, result]);
      setTopicSuggestions([...result.cards]);
      lastTopicSuggestionSetId.current = result.set_id;
      topicSuggestionRequestId.current = '';
    } catch (cause) {
      setTopicSuggestionError(safeParentFlowErrorMessage(cause));
    } finally {
      setTopicSuggestionBusy(false);
    }
  }

  async function refreshTopicSuggestions(): Promise<void> {
    if (!topicDraftId || topicSuggestionBusy) return;
    if (!topicSuggestionRequestId.current) topicSuggestionRequestId.current = Crypto.randomUUID();
    await loadTopicSuggestionSet(topicDraftId, topicSuggestionSets.map((set) => set.set_id));
  }

  function selectTopicCard(card: ParentTopicCardV1): void {
    subjectSuggestionRequestId.current = '';
    setTopic(card.title_vi);
    setSelectedTopicId(card.topic_id);
    setSubjectSuggestions([]);
    setSubjectSuggestionSets([]);
    setIntendedDrawingSubject('');
    setCustomDrawingSubject('');
    setSubjectValidationMessage('');
    setCustomSubjectValidated(false);
    setTopicSuggestionError('');
  }

  function setCustomTopic(value: string): void {
    subjectSuggestionRequestId.current = '';
    setTopic(value);
    setSelectedTopicId('custom');
    setSubjectSuggestions([]);
    setSubjectSuggestionSets([]);
    setIntendedDrawingSubject('');
    setCustomDrawingSubject('');
    setSubjectValidationMessage('');
    setCustomSubjectValidated(false);
    setSubjectSuggestionError('');
  }

  async function continueTopicSelection(): Promise<void> {
    const selectedTopic = topic.trim();
    if (selectedTopic.length < 2 || !topicDraftId || topicSuggestionBusy || subjectSuggestionBusy) {
      setTopicSuggestionError('Chọn một chủ đề hoặc nhập chủ đề riêng trước khi tiếp tục.');
      return;
    }
    if (!subjectSuggestionRequestId.current) subjectSuggestionRequestId.current = Crypto.randomUUID();
    const requestId = subjectSuggestionRequestId.current;
    setSubjectSuggestionBusy(true);
    setSubjectSuggestionError('');
    try {
      const result = await application.learning.listDrawingSubjectSuggestions({
        draftId: topicDraftId,
        topicId: selectedTopicId || 'custom',
        topic: selectedTopic,
        requestId,
        excludedSetIds: subjectSuggestionSets.map((set) => set.set_id),
        excludedSubjects: subjectSuggestionSets.flatMap((set) => set.cards.flatMap((card) => [card.title_vi, card.guide_subject])),
      });
      const cards = Array.isArray(result.cards) ? result.cards : [];
      const customInputRequired = result.generation_source === 'CUSTOM_INPUT_REQUIRED';
      const cardShapeValid = customInputRequired
        ? cards.length === 0 && result.topic_id.startsWith('custom-')
        : cards.length === 3 && new Set(cards.map((card) => card.subject_id)).size === 3;
      if (result.contract !== 'ParentDrawingSubjectSuggestionSetV1'
        || result.request_id !== requestId
        || result.draft_id !== topicDraftId
        || !isResolvedTopicConsistent({
          selectedTopicId: selectedTopicId || 'custom',
          selectedTopic,
          resolvedTopicId: result.topic_id,
          resolvedTopic: result.topic,
        })
        || !cardShapeValid
        || subjectSuggestionSets.some((set) => set.set_id === result.set_id)) {
        throw new ParentApplicationError('PARENT_SUBJECT_SUGGESTION_INVALID', 'Chưa nhận được gợi ý phù hợp với chủ đề.');
      }
      setSelectedTopicId(result.topic_id);
      setTopic(result.topic);
      setSubjectSuggestionSets((current) => [...current, result]);
      setSubjectSuggestions([...result.cards]);
      setStep('subject');
      subjectSuggestionRequestId.current = '';
    } catch (cause) {
      const message = safeParentFlowErrorMessage(cause);
      setTopicSuggestionError(message);
      setSubjectSuggestionError(message);
    } finally {
      setSubjectSuggestionBusy(false);
    }
  }

  async function refreshSubjectSuggestions(): Promise<void> {
    if (!topicDraftId || !topic || subjectSuggestionBusy || subjectSuggestions.length === 0) return;
    if (!subjectSuggestionRequestId.current) subjectSuggestionRequestId.current = Crypto.randomUUID();
    const requestId = subjectSuggestionRequestId.current;
    setSubjectSuggestionBusy(true);
    setSubjectSuggestionError('');
    try {
      const result = await application.learning.listDrawingSubjectSuggestions({
        draftId: topicDraftId,
        topicId: selectedTopicId,
        topic,
        requestId,
        excludedSetIds: subjectSuggestionSets.map((set) => set.set_id),
        excludedSubjects: subjectSuggestionSets.flatMap((set) => set.cards.flatMap((card) => [card.title_vi, card.guide_subject])),
      });
      if (result.request_id !== requestId
        || result.generation_source !== 'CURATED_CATALOG'
        || result.draft_id !== topicDraftId
        || result.cards.length !== 3
        || result.topic_id !== selectedTopicId
        || new Set(result.cards.map((card) => card.subject_id)).size !== 3
        || subjectSuggestionSets.some((set) => set.set_id === result.set_id)) {
        throw new ParentApplicationError('PARENT_SUBJECT_SUGGESTION_INVALID', 'Chưa nhận được ba gợi ý khác cho chủ đề này.');
      }
      setSubjectSuggestionSets((current) => [...current, result]);
      setSubjectSuggestions([...result.cards]);
      setIntendedDrawingSubject('');
      setCustomSubjectValidated(false);
      subjectSuggestionRequestId.current = '';
    } catch (cause) {
      setSubjectSuggestionError(safeParentFlowErrorMessage(cause));
    } finally {
      setSubjectSuggestionBusy(false);
    }
  }

  function selectDrawingSubject(card: ParentDrawingSubjectCardV1): void {
    setIntendedDrawingSubject(card.guide_subject);
    setCustomDrawingSubject('');
    setCustomSubjectValidated(false);
    setSubjectValidationMessage('');
  }

  function setCustomSubject(value: string): void {
    setCustomDrawingSubject(value);
    setCustomSubjectValidated(false);
    setIntendedDrawingSubject('');
    setSubjectValidationMessage('');
  }

  async function validateCustomDrawingSubject(): Promise<void> {
    const proposed = customDrawingSubject.trim();
    if (proposed.length < 2 || !selectedTopicId || !topic || subjectSuggestionBusy) return;
    setSubjectSuggestionBusy(true);
    setSubjectValidationMessage('');
    try {
      const result: ParentCustomSubjectValidationV1 = await application.learning.validateCustomSubject({
        topicId: selectedTopicId,
        topic,
        subject: proposed,
      });
      if (result.contract !== 'ParentCustomSubjectValidationV1') {
        throw new ParentApplicationError('PARENT_CUSTOM_SUBJECT_INVALID', 'Máy chủ chưa xác nhận được chủ đề của đối tượng.');
      }
      setCustomSubjectValidated(result.decision === 'ON_TOPIC');
      setIntendedDrawingSubject(result.decision === 'ON_TOPIC' ? (result.normalized_subject ?? proposed) : '');
      setSubjectValidationMessage(result.message_vi);
    } catch (cause) {
      setCustomSubjectValidated(false);
      setIntendedDrawingSubject('');
      setSubjectValidationMessage(safeParentFlowErrorMessage(cause));
    } finally {
      setSubjectSuggestionBusy(false);
    }
  }

  function continueFromSubjectSelection(): void {
    if (!intendedDrawingSubject.trim() || (customDrawingSubject.trim() && !customSubjectValidated)) return;
    setIdea((current) => current.trim() || intendedDrawingSubject.trim());
    setStep('idea');
  }

  function skipTopicSelection(): void {
    setTopic('');
    setSelectedTopicId('');
    setSubjectSuggestions([]);
    setSubjectSuggestionSets([]);
    setIntendedDrawingSubject('');
    setCustomDrawingSubject('');
    setSubjectValidationMessage('');
    setCustomSubjectValidated(false);
    setStep('idea');
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
    if (!canStartProfileLearning(ageEligibility, consentState.status, target.data_origin)) {
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
    // T-2c, Q-2c-1: the server accepts `audio/mp4` and `audio/wav` up to two minutes and 20 MB.
    if (value && value.mediaType !== 'audio/mp4' && value.mediaType !== 'audio/wav') {
      setAudioValue(null);
      setError('Định dạng bản ghi âm chưa được hỗ trợ. Bạn vẫn có thể nhập ý tưởng bằng chữ.');
      return;
    }
    setAudioValue(value);
    audioSubmittedRunId.current = null;
    voiceUploadAction.current = null;
    setError('');
  }

  function setPhoto(value: SelectedPhoto): void {
    // One retake is allowed after a recoverable analysis failure (T-2b); otherwise the drawing is fixed to the run.
    if (!retakeAvailable && ((photo as SelectedPhotoWithRunLock | null)?.locked
      || (contextRun && (contextRun.current_input_revision ?? 0) > 1))) {
      setPhotoValue((current) => current
        ? { ...current, analysisError: 'Ảnh đã được gắn với buổi học này và không thể thay bằng ảnh khác.' }
        : current);
      return;
    }
    setPhotoValue({ ...value, locked: false, analysisError: undefined } as SelectedPhoto);
    setError('');
  }

  function setPhotoMessage(message: string): void {
    // After a resume there is no photo in memory: the message still has to reach the adult.
    if (message && !photo) setError(message);
    setPhotoValue((current) => current ? { ...current, analysisError: message } : current);
  }

  function resetActivityReview(): void {
    setActivitySuggestions(null);
    setSelectedActivityIndex(null);
    setActivityBusy(false);
    setActivityAttempted(false);
    setActivityError('');
    activitySelectionAction.current = null;
    activityCancelAction.current = null;
  }

  async function createContextRun(): Promise<ParentStoryRunV1 | null> {
    if (busy || runCreationInFlight.current || !ensureLearningProfileAllowed(profile)) return null;
    const selectedPhoto = photo;
    const targetProfile = profile;
    if (!selectedPhoto || !isWithinOfflinePhotoLimit(selectedPhoto.fileSizeBytes)) {
      setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_REQUIRED' }));
      return null;
    }
    if (contextRun) {
      return contextRun;
    }
    if (!targetProfile) return null;
    const pin = lessonVersionPinFromDetail(lesson);
    if (!canBeginContextStep({
      profileId: targetProfile.profile_id, topic, adultIdea: idea, lessonPin: pin,
    })) {
      setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_CONTEXT_REQUIRED' }));
      return null;
    }

    runCreationInFlight.current = true;
    setBusy('context-create');
    setError('');
    setPhotoMessage('');
    try {
      const preflight = await inspectActiveRun();
      if (preflight.state === 'unavailable') {
        setPhotoMessage(PARENT_RUN_PREFLIGHT_UNAVAILABLE_MESSAGE);
        return null;
      }
      if (preflight.activeRun) {
        setPhotoMessage(safeParentFlowErrorMessage({ code: 'ACTIVE_RUN_EXISTS' }));
        return null;
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
      resetActivityReview();
      setStep('capture');
      runCreationAction.current = null;
      return run;
    } catch (cause) {
      setPhotoMessage(safeParentFlowErrorMessage(cause));
      return null;
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
    void requestActivityList();
  }

  async function getLatestRun(runId: string): Promise<ParentStoryRunV1> {
    const receipt = requireLiveStoryRun(await application.learning.getRunV1(runId));
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
    resetActivityReview();
    if (revisionChanged || contextChanged || !confirmed) {
      setStory(null);
      setStoryDisplayedRunId('');
      setStoryRevisionNo(null);
      setStorySha256('');
      setStoryAttempted(false);
      setStoryConfirmed(false);
      setRewriteCount(0);
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
      setStep(confirmed ? 'activity' : 'understanding');
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
    const busyToken = beginBusy('context-confirmation');
    setError('');
    try {
      if (contextConfirmationAction.current) {
        const latest = await getLatestRun(run.run_id);
        if (latest.context_confirmed === true) {
          setContextConfirmed(true);
          contextConfirmationAction.current = null;
          await handleStoryGateResult(latest, false);
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
      await handleStoryGateResult(confirmedRun);
    } catch (cause) {
      let handledConflict = false;
      if (cause instanceof ParentApplicationError && (cause.code === 'STALE_REVISION' || cause.code === 'INVALID_STATE_TRANSITION')) {
        contextConfirmationAction.current = null;
        try {
          const latest = await readLiveRun(run.run_id);
          await handleStoryGateResult(latest, false);
          handledConflict = true;
        } catch {
          setContextConfirmed(false);
          setSubjectConfirmed(false);
          setStep('home');
        }
      }
      if (!handledConflict) setError(safeParentFlowErrorMessage(cause));
    } finally {
      endBusy(busyToken);
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
    const busyToken = beginBusy('understanding');
    setError('');
    try {
      const latest = await getLatestRun(runId);
      const revision = latest.current_input_revision;
      if (typeof revision !== 'number' || !Number.isInteger(revision) || revision < 1) {
        setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
        return;
      }
      const stage = classifyDrawingProgress(latest);
      if (revision > 1 && !retakeAvailable && stage.kind !== 'awaiting-drawing') {
        // The server already holds a drawing for this run: it is never sent again. Follow what the server did with it.
        await handleOrWaitDrawing(latest);
        return;
      }
      if (revision === 1 && isActiveOrUnreconciledStoryRun(latest)) {
        setPhotoMessage(safeParentFlowErrorMessage({ code: 'AWAITING_RECONCILIATION' }));
        return;
      }
      // T-2b: the upload session and the attach each keep their own key per file, so a repeated tap replays.
      const signature = JSON.stringify([runId, revision, selectedPhoto.uri, selectedPhoto.fileSizeBytes ?? null]);
      const keys = retainedKeySet(drawingUploadAction, signature, ['create', 'complete', 'attach'] as const);
      const accepted = await timeRequest('drawing-attach', () => application.learning.attachDrawingV1({
        runId,
        runRevision: latest.run_revision,
        photo: { base64: selectedPhoto.base64, mediaType: selectedPhoto.mediaType },
        keys,
      }));
      drawingUploadAction.current = null;
      if (retakeAvailable) retakeUsed.current = true;
      setRetakeAvailable(false);
      setPhotoValue((current) => current ? { ...current, locked: true, analysisError: undefined } as SelectedPhoto : current);
      const attached: ParentStoryRunV1 = {
        ...latest,
        run_revision: accepted.run_revision,
        current_input_revision: accepted.input_revision,
        run_state: accepted.run_state as ParentStoryRunV1['run_state'],
      };
      adoptPolledRun(attached);
      await submitVoiceIdea(attached);
      await settleDrawingStage(runId);
    } catch (cause) {
      if (cause instanceof RunWaitCancelled) return;
      if (isDefinitiveClientError(cause)) drawingUploadAction.current = null;
      setPhotoMessage(safeParentFlowErrorMessage(cause));
    } finally {
      drawingAnalysisInFlight.current = false;
      endBusy(busyToken);
    }
  }

  async function analyzeDrawingForCurrentRun(): Promise<void> {
    if (!contextRun) {
      const createdRun = await createContextRun();
      if (createdRun) await analyzeDrawingForRun(createdRun.run_id);
      return;
    }
    await analyzeDrawingForRun(contextRun.run_id);
  }

  function renameSecondarySubject(entityId: ParentSubjectRoleV1['entity_id'], label: string): void {
    setSubjectRoles((current) => setRoleLabel(current, entityId, label));
  }

  function toggleSecondarySubject(entityId: ParentSubjectRoleV1['entity_id']): void {
    setSubjectRoles((current) => toggleSecondaryUse(current, entityId));
  }

  function makeMainSubject(entityId: ParentSubjectRoleV1['entity_id']): void {
    const next = promoteToMain(subjectRoles, entityId, subject.trim() || mainSubjectLabel(subjectRoles));
    setSubjectRoles(next);
    setSubject(mainSubjectLabel(next));
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
    const rolesRequest: SubjectRolesRequest = buildSubjectRolesRequest(subjectRoles, confirmedSubject);
    if (rolesRequest.kind === 'invalid') {
      setError(subjectRolesIssueMessage(rolesRequest.reason));
      return;
    }
    const approvedRoles = rolesRequest.kind === 'ok' ? rolesRequest.roles : undefined;
    const signature = JSON.stringify([runId, understandingRevision, confirmedSubject, approvedRoles ?? null]);
    const busyToken = beginBusy('subject');
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
          setStep('activity');
          subjectConfirmationAction.current = null;
          await requestActivityList();
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
      const response = await application.learning.confirmSubjectV1(
        runId,
        understandingRevision,
        confirmedSubject,
        actionIdentity,
        approvedRoles,
      );
      const subjectEdited = confirmedSubject !== (candidate?.candidate_subject ?? '').trim();
      const outcome = readSubjectConfirmationOutcome(response, {
        runId,
        understandingRevision,
        subjectEdited,
        rolesProvided: approvedRoles !== undefined,
      });
      if (outcome === 'invalid') {
        throw new ParentApplicationError('PARENT_SUBJECT_CONFIRMATION_INVALID', 'Subject confirmation did not match the reviewed result.');
      }
      if (outcome === 'rerun-requested') {
        // SRS l.394: an edited subject runs the visual understanding again. Nothing is confirmed yet;
        // the app follows the run until the new revision is ready, then asks for the second confirmation.
        subjectConfirmationAction.current = null;
        setSubjectConfirmed(false);
        const result = await waitRun(runId, (candidateRun) => candidateRun.run_state !== 'INPUT_PROCESSING', { onRun: adoptPolledRun });
        const rerunRun = result.value;
        const refreshed = rerunRun ? readRunUnderstanding(rerunRun) : null;
        if (!rerunRun || result.timedOut) {
          setError(safeParentFlowErrorMessage({ code: 'SUBJECT_RERUN_PENDING' }));
        } else if (rerunRun.run_state === 'SUBJECT_REVIEW' && refreshed && refreshed.understandingRevision > understandingRevision) {
          adoptServerUnderstanding(rerunRun);
        } else if (rerunRun.run_state === 'SUBJECT_REVIEW') {
          // A failed rerun returns to the unchanged revision: the adult may confirm it or edit again.
          setError('Chưa xem lại được bức tranh theo chủ thể bạn sửa. Bạn có thể xác nhận kết quả hiện tại hoặc sửa lại.');
        } else if (rerunRun.run_state === 'INPUT_REVIEW') {
          await handleDrawingProgress(rerunRun);
        } else {
          setError(safeParentFlowErrorMessage({ code: isClosedRunState(rerunRun.run_state) ? rerunRun.run_state : 'PARENT_DRAWING_RESULT_INVALID' }));
        }
        return;
      }
      const decision = subjectEdited ? 'CORRECTED_BY_ADULT' : 'CONFIRMED_BY_ADULT';
      const confirmedRun: ParentStoryRunV1 = {
        ...run,
        understanding_revision: response.understanding_revision,
        subject_label: confirmedSubject,
        candidate: candidate
          ? {
            ...candidate,
            candidate_subject: confirmedSubject,
            decision,
            ...(approvedRoles ? { subject_roles: approvedRoles } : {}),
          }
          : null,
      };
      setContextRun(confirmedRun);
      setActiveRun(confirmedRun);
      setUnderstandingRevision(response.understanding_revision);
      setCandidate(confirmedRun.candidate ?? null);
      setSubjectConfirmed(true);
      resetActivityReview();
      setStep('activity');
      subjectConfirmationAction.current = null;
      await requestActivityList();
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
      endBusy(busyToken);
    }
  }

  async function requestActivityList(force = false, sourceRun?: ParentStoryRunV1): Promise<void> {
    if (!sourceRun && (activityBusy || (!force && activityAttempted && activitySuggestions))) return;
    if (!ensureLearningProfileAllowed(profile)) return;
    const run = sourceRun ?? contextRun;
    const sourceUnderstanding = run ? readRunUnderstanding(run) : null;
    const sourceSubject = sourceUnderstanding?.subject ?? subject;
    const sourceRevision = sourceUnderstanding?.understandingRevision ?? understandingRevision;
    if (!run || (!sourceRun && !subjectConfirmed) || !isConfirmedRunSubject(run, sourceSubject)) {
      setActivityError(safeParentFlowErrorMessage({ code: 'SUBJECT_NOT_CONFIRMED' }));
      return;
    }

    setActivityAttempted(true);
    setActivityBusy(true);
    setActivityError('');
    try {
      const latest = await readLiveRun(run.run_id);
      if (latest.run_state !== 'PREPARATION_REVIEW') {
        await handleStoryGateResult(latest, false);
        return;
      }
      if (!isConfirmedRunSubject(latest, sourceSubject) || latest.understanding_revision !== sourceRevision) {
        setActivityError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      const response = await timeRequest('activity-list', () => application.learning.listActivitiesV1(run.run_id));
      const activityList = readActivityListV1(response);
      if (!activityList) {
        throw new ParentApplicationError('PARENT_ACTIVITY_LIST_INVALID', 'The activity list did not match the approved response shape.');
      }
      setActivitySuggestions(activityList);
      const selectedRef = latest.main_activity?.state === 'SELECTED' ? latest.main_activity.selected?.activity_ref : null;
      const selectedIndex = selectedRef
        ? activityList.items.findIndex((item) => JSON.stringify(item.activity_ref) === JSON.stringify(selectedRef))
        : -1;
      setSelectedActivityIndex(selectedIndex >= 0 ? selectedIndex : null);
      adoptPolledRun(latest);
    } catch (cause) {
      setActivityError(safeParentFlowErrorMessage(cause));
    } finally {
      setActivityBusy(false);
    }
  }

  function chooseActivity(index: number): void {
    if (!activitySuggestions || !Number.isInteger(index) || index < 0 || index >= activitySuggestions.items.length) return;
    setSelectedActivityIndex(index);
    setActivityError('');
  }

  async function selectActivity(): Promise<void> {
    if (busy || activityBusy || !ensureLearningProfileAllowed(profile)) return;
    const selected = selectedActivityIndex === null ? null : activitySuggestions?.items[selectedActivityIndex] ?? null;
    const runId = contextRun?.run_id;
    if (!runId || !selected) {
      setActivityError('Chọn một hoạt động trong danh sách trước khi tiếp tục.');
      return;
    }

    const busyToken = beginBusy('activity-selection');
    setError('');
    setActivityError('');
    try {
      const latest = await readLiveRun(runId);
      if (latest.run_state !== 'PREPARATION_REVIEW') {
        await handleStoryGateResult(latest, false);
        return;
      }
      if (latest.understanding_revision !== understandingRevision || !isConfirmedRunSubject(latest, subject)) {
        setActivityError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      const signature = JSON.stringify([runId, latest.run_revision, selected.activity_ref]);
      const actionIdentity = retainedActionIdentity(activitySelectionAction, signature);
      const request: ParentActivitySelectionRequestV1 = {
        expected_revision: latest.run_revision,
        activity: selected.activity_ref,
      };
      const envelope = await timeRequest('activity-selection', () => application.learning.selectActivityV1(runId, request, actionIdentity));
      activitySelectionAction.current = null;
      await handleStoryGateResult(envelope.story_run);
    } catch (cause) {
      if (cause instanceof ParentApplicationError && (cause.code === 'STALE_REVISION' || cause.code === 'INVALID_STATE_TRANSITION')) {
        activitySelectionAction.current = null;
        try {
          const latest = await readLiveRun(runId);
          await handleStoryGateResult(latest, false);
        } catch (reloadError) {
          setActivityError(safeParentFlowErrorMessage(reloadError));
        }
      } else if (cause instanceof ParentApplicationError && cause.code === 'RESOURCE_NOT_FOUND') {
        activitySelectionAction.current = null;
        setActivitySuggestions(null);
        setSelectedActivityIndex(null);
        setActivityAttempted(false);
        await requestActivityList(true);
        setActivityError('Danh sách hoạt động đã thay đổi. Hãy chọn lại.');
      } else {
        if (isDefinitiveClientError(cause)) activitySelectionAction.current = null;
        setActivityError(safeParentFlowErrorMessage(cause));
      }
    } finally {
      endBusy(busyToken);
    }
  }

  async function handleStoryGateResult(run: ParentStoryRunV1, reloadIfBothGatesRemain = true): Promise<void> {
    adoptPolledRun(run);
    if (run.run_state === 'SCRIPT_GENERATING' || run.run_state === 'STORY_GENERATING') {
      await followFirstStory(run.run_id);
      return;
    }
    if (run.run_state === 'SCRIPT_REVIEW') {
      if (!adoptServerStory(run)) {
        setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
        return;
      }
      setStep(run.story_status === 'CONFIRMED' && run.story_confirmation_required !== true ? 'video' : 'story');
      return;
    }
    if (run.run_state === 'PREPARATION_REVIEW') {
      if (run.main_activity?.state !== 'SELECTED') {
        setStep('activity');
        void requestActivityList();
        return;
      }
      if (run.context_confirmed !== true) {
        setStep('context');
        return;
      }
      if (reloadIfBothGatesRemain) {
        try {
          const latest = await readLiveRun(run.run_id);
          if (latest.run_state !== 'PREPARATION_REVIEW') {
            await handleStoryGateResult(latest, false);
            return;
          }
          adoptPolledRun(latest);
        } catch {
          // Show the safe not-ready state below; never loop on a gate command.
        }
      }
      setStep('story');
      setStoryAttempted(true);
      setError('Câu chuyện chưa sẵn sàng. Hãy kiểm tra lại trạng thái buổi học sau.');
      return;
    }
    if (['VIDEO_ADMISSION_PENDING', 'VIDEO_QUEUED', 'VIDEO_GENERATING', 'VIDEO_SAFETY_VALIDATING', 'VIDEO_READY', 'COMPLETED'].includes(run.run_state)) {
      await openVideoStep(run.run_id);
      return;
    }
    if (run.run_state === 'FAILED') {
      setStep('story');
      setStoryAttempted(true);
      setError('Chưa tạo được câu chuyện. Hãy bắt đầu một buổi học mới.');
      return;
    }
    setStep('story');
    setStoryAttempted(true);
    setError('Buổi học chưa sẵn sàng. Hãy kiểm tra lại trạng thái sau.');
  }

  async function followFirstStory(runId: string): Promise<void> {
    const busyToken = beginBusy('story');
    setStep('story');
    setStoryAttempted(true);
    setError('');
    try {
      const result = await waitRun(
        runId,
        (run) => run.run_state !== 'SCRIPT_GENERATING' && run.run_state !== 'STORY_GENERATING',
        { onRun: adoptPolledRun },
      );
      const latest = result.value;
      if (!latest || result.timedOut) {
        setError('Câu chuyện đang được tạo. Hãy kiểm tra lại sau; không gửi yêu cầu tạo trùng.');
        return;
      }
      if (latest.run_state === 'SCRIPT_REVIEW' && latest.story_status === 'DRAFT' && adoptServerStory(latest)) {
        adoptPolledRun(latest);
        setStep('story');
        return;
      }
      if (latest.run_state === 'FAILED') {
        setError('Chưa tạo được câu chuyện. Hãy bắt đầu một buổi học mới.');
        return;
      }
      if (latest.run_state === 'SCRIPT_GENERATION_UNKNOWN') {
        setError(safeParentFlowErrorMessage({ code: 'AWAITING_RECONCILIATION' }));
        return;
      }
      await handleStoryGateResult(latest, false);
    } catch (cause) {
      if (!(cause instanceof RunWaitCancelled)) setError(safeParentFlowErrorMessage(cause));
    } finally {
      endBusy(busyToken);
    }
  }

  async function cancelEmptyActivityRun(): Promise<void> {
    const runId = contextRun?.run_id;
    if (busy || !runId || !ensureLearningProfileAllowed(profile)) return;
    const busyToken = beginBusy('activity-cancel');
    setActivityError('');
    setError('');
    try {
      const latest = await readLiveRun(runId);
      const signature = JSON.stringify([runId, latest.run_revision, 'cancel-no-activity']);
      const actionIdentity = retainedActionIdentity(activityCancelAction, signature);
      await timeRequest('activity-cancel', () => application.platform.cancelRunV1(runId, latest.run_revision, actionIdentity));
      activityCancelAction.current = null;
      setContextRun(null);
      setActiveRun(null);
      resetActivityReview();
      setStep('home');
    } catch (cause) {
      if (isDefinitiveClientError(cause)) activityCancelAction.current = null;
      setActivityError(safeParentFlowErrorMessage(cause));
    } finally {
      endBusy(busyToken);
    }
  }
  async function refreshStory(): Promise<void> {
    const runId = contextRun?.run_id;
    if (busy || !runId) return;
    const busyToken = beginBusy('story');
    setError('');
    try {
      const latest = await readLiveRun(runId);
      if (latest.run_state === 'SCRIPT_GENERATING' || latest.run_state === 'STORY_GENERATING') {
        await followFirstStory(runId);
        return;
      }
      if (latest.run_state === 'SCRIPT_GENERATION_UNKNOWN') {
        adoptPolledRun(latest);
        setError(safeParentFlowErrorMessage({ code: 'AWAITING_RECONCILIATION' }));
        return;
      }
      if (latest.run_state === 'SCRIPT_REVIEW') {
        if (!adoptServerStory(latest)) {
          setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
          return;
        }
        adoptPolledRun(latest);
        setStep(latest.story_status === 'CONFIRMED' && latest.story_confirmation_required !== true ? 'video' : 'story');
        return;
      }
      await handleStoryGateResult(latest, false);
    } catch (cause) {
      setError(safeParentFlowErrorMessage(cause));
    } finally {
      endBusy(busyToken);
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
      storyConfirmed: storyConfirmed && contextRun?.story_confirmation_required !== true,
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
        && latest.story_sha256 === revisionSha256
        && latest.story_confirmation_required !== true) {
        if (!adoptServerStory(latest)) {
          setStoryConfirmed(false);
          setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
          return;
        }
        setStoryConfirmed(true);
        return;
      }
      const reconfirmingSpentStory = latest.story_status === 'CONFIRMED'
        && latest.story_confirmation_required === true
        && (latest.run_state === 'SCRIPT_REVIEW' || latest.run_state === 'SAFETY_BLOCKED');
      if ((!reconfirmingSpentStory && latest.story_status !== 'DRAFT')
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
      setConfirmedStoryRevisionNo(revisionNo);
      scriptConfirmationAction.current = null;
    } catch (cause) {
      if (cause instanceof ParentApplicationError && ['STALE_REVISION', 'INVALID_STATE_TRANSITION', 'VIDEO_REGENERATION_LIMIT_REACHED'].includes(cause.code)) {
        scriptConfirmationAction.current = null;
        try {
          const latest = await getLatestRun(runId);
          if (latest.story_revision_id) adoptServerStory(latest);
          setStoryConfirmed(latest.story_status === 'CONFIRMED');
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
    if (await resumePhaseBRun(run)) return;
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
  // ---------------------------------------------------------------------------------------------
  // Goal v3 Phase B (SRS l.1664-1676): waits on the run, voice idea and transcript, async rewrites,
  // video request and playback, closeout states. The run detail is the single source of truth; every
  // command keeps its action identity per signature, so a repeated tap replays instead of re-sending.
  // ---------------------------------------------------------------------------------------------

  /** `busy` belongs to the latest action: an older, cancelled one must not clear it (review F7b). */
  function beginBusy(label: string): number {
    busyEpoch.current += 1;
    waitsBlocked.current = false;
    setBusy(label);
    return busyEpoch.current;
  }

  function endBusy(token: number): void {
    if (busyEpoch.current === token) setBusy('');
  }

  /** Leaves a waiting screen: the wait stops, nothing it would have shown can steal the navigation, the grant is dropped. */
  function leaveWait(next: AppStep): void {
    stopWait();
    waitsBlocked.current = true;
    busyEpoch.current += 1;
    drawingAnalysisInFlight.current = false;
    setBusy('');
    setPlayback(null);
    setMarkingUnsuitable(false);
    setStep(next);
  }

  function startWait(): AbortSignal {
    if (waitsBlocked.current) {
      // An action that started before the adult left the screen cannot open a new wait (it would navigate later).
      const blocked = new AbortController();
      blocked.abort();
      return blocked.signal;
    }
    waitAbort.current?.abort();
    const controller = new AbortController();
    waitAbort.current = controller;
    return controller.signal;
  }

  function stopWait(): void {
    waitAbort.current?.abort();
    waitAbort.current = null;
  }

  async function readLiveRun(runId: string): Promise<ParentStoryRunV1> {
    const run = requireLiveStoryRun(await application.learning.getRunV1(runId)).story_run;
    if (run.run_id !== runId) {
      throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'The refreshed run did not match the current run.');
    }
    return run;
  }

  /** Reads the run every 2 to 10 seconds until `isSettled`; a closed or cancelled wait ends the loop. */
  async function waitRun(
    runId: string,
    isSettled: (run: ParentStoryRunV1) => boolean,
    options: { budgetMs?: number; onRun?: (run: ParentStoryRunV1) => void } = {},
  ) {
    const signal = startWait();
    return waitForRun<ParentStoryRunV1>({
      read: () => readLiveRun(runId),
      isSettled: (run) => isSettled(run) || isClosedRunState(run.run_state),
      sleep: delayWithSignal,
      signal,
      appState: AppState as unknown as RunWaitAppState,
      budgetMs: options.budgetMs,
      isTransient: isTransientReadError,
      onValue: options.onRun,
    });
  }

  function adoptPolledRun(run: ParentStoryRunV1): void {
    setContextRun(run);
    setActiveRun(run);
    setContextConfirmed(run.context_confirmed === true);
  }

  /** After a drawing, a voice idea or a transcript confirmation: wait for the server, then show what it answered. */
  async function settleDrawingStage(runId: string): Promise<void> {
    const result = await waitRun(runId, (run) => classifyDrawingProgress(run).kind !== 'processing', { onRun: adoptPolledRun });
    if (result.timedOut || !result.value) {
      setPhotoMessage('Việc nhận diện đang mất lâu hơn dự kiến. Ảnh đã được gửi; hãy quay lại sau để xem kết quả.');
      return;
    }
    await handleDrawingProgress(result.value);
  }

  async function handleDrawingProgress(run: ParentStoryRunV1): Promise<void> {
    const progress = classifyDrawingProgress(run);
    if (progress.kind === 'awaiting-drawing') {
      // A run with no analysis job yet (new, or only an idea): the adult still has to attach the drawing.
      adoptPolledRun(run);
      const pending = await application.learning.getTranscriptV1(run.run_id);
      const pendingProgress = classifyTranscript(pending);
      if (pendingProgress.kind === 'review' || pendingProgress.kind === 'waiting') {
        applyTranscript(pending);
        setTranscriptWaiting(pendingProgress.kind === 'waiting');
        setStep('transcript');
        return;
      }
      setStep('capture');
      return;
    }
    if (progress.kind === 'subject-ready') {
      setRetakeAvailable(false);
      if (adoptServerUnderstanding(run)) return;
      setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
      return;
    }
    if (progress.kind === 'beyond-subject') {
      if (readRunUnderstanding(run) && adoptServerUnderstanding(run)) return;
      setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
      return;
    }
    if (progress.kind === 'input-review') {
      const current = await application.learning.getTranscriptV1(run.run_id);
      const transcriptProgress = classifyTranscript(current);
      adoptPolledRun(run);
      if (transcriptProgress.kind === 'review' || transcriptProgress.kind === 'waiting'
        || (transcriptProgress.kind === 'failed' && !progress.analysisFailed)) {
        applyTranscript(current);
        setTranscriptWaiting(transcriptProgress.kind === 'waiting');
        setStep('transcript');
        return;
      }
      if (progress.analysisFailed) {
        if (retakeUsed.current) {
          // T-2b: the server allows one retake only; after it the way on is to cancel the run.
          setRetakeAvailable(false);
          setPhotoMessage('Vẫn chưa nhận diện được bức tranh. Bạn có thể hủy buổi học trong lịch sử rồi bắt đầu lại.');
          setStep('capture');
          return;
        }
        // T-2b: one retake is allowed after a recoverable failure; the photo is unlocked for it.
        setRetakeAvailable(true);
        setPhotoValue((currentPhoto) => currentPhoto ? { ...currentPhoto, locked: false } as SelectedPhoto : currentPhoto);
        setPhotoMessage('Chưa nhận diện được bức tranh. Bạn có thể chụp lại một lần.');
        setStep('capture');
        return;
      }
      setPhotoMessage('Buổi học đang chờ bạn xem lại ảnh và ý tưởng.');
      return;
    }
    if (progress.kind === 'closed') {
      setPhotoMessage(safeParentFlowErrorMessage({ code: progress.state }));
      return;
    }
    setPhotoMessage(safeParentFlowErrorMessage({ code: 'PARENT_DRAWING_RESULT_INVALID' }));
  }

  function applyTranscript(value: ParentRunTranscriptV1): void {
    setTranscript(value);
    setTranscriptTextValue(value.text ?? '');
  }

  function setTranscriptText(value: string): void {
    setTranscriptTextValue(value.slice(0, 500));
  }

  /** The recording is sent once per run, after the drawing; a failure leaves the typed idea usable. */
  async function submitVoiceIdea(run: ParentStoryRunV1): Promise<void> {
    const selectedAudio = audio;
    if (!selectedAudio || audioSubmittedRunId.current === run.run_id) return;
    const signature = JSON.stringify([run.run_id, selectedAudio.uri, selectedAudio.fileName]);
    const keys = retainedKeySet(voiceUploadAction, signature, ['create', 'complete', 'idea'] as const);
    try {
      // The analysis worker bumps the run revision right after the drawing is attached, so the revision is read
      // again just before `/idea` (the backend compares it for equality) instead of reusing the attach answer.
      const accepted = await timeRequest('parent-story-run-idea', () => application.learning.submitVoiceIdeaV1({
        runId: run.run_id,
        currentRunRevision: async () => (await readLiveRun(run.run_id)).run_revision,
        audio: { uri: selectedAudio.uri, mediaType: selectedAudio.mediaType },
        keys,
      }));
      audioSubmittedRunId.current = run.run_id;
      voiceUploadAction.current = null;
      setContextRun((current) => current && current.run_id === run.run_id
        ? { ...current, run_revision: accepted.run_revision } : current);
    } catch (cause) {
      if (isDefinitiveClientError(cause)) voiceUploadAction.current = null;
      setError(`Chưa gửi được bản ghi âm. Bạn vẫn có thể tiếp tục bằng ý tưởng đã nhập. ${safeRunMessage(cause)}`);
    }
  }

  async function refreshTranscript(): Promise<void> {
    const runId = contextRun?.run_id;
    if (!runId || busy) return;
    const busyToken = beginBusy('transcript-load');
    setError('');
    try {
      const signal = startWait();
      const result = await waitForRun<ParentRunTranscriptV1>({
        read: () => application.learning.getTranscriptV1(runId),
        isSettled: (value) => classifyTranscript(value).kind !== 'waiting',
        sleep: delayWithSignal,
        signal,
        appState: AppState as unknown as RunWaitAppState,
        budgetMs: 3 * 60_000,
        isTransient: isTransientReadError,
        onValue: applyTranscript,
      });
      setTranscriptWaiting(result.timedOut);
    } catch (cause) {
      if (cause instanceof RunWaitCancelled) return;
      setError(safeRunMessage(cause));
    } finally {
      endBusy(busyToken);
    }
  }

  /** TD-04: a corrected text is saved first, then the exact revision and hash that the server returns are confirmed. */
  async function confirmTranscriptReview(): Promise<void> {
    const run = contextRun;
    const current = transcript;
    if (busy || !run || !current) return;
    const text = transcriptText.trim();
    if (!text) return;
    const busyToken = beginBusy('transcript-confirm');
    setError('');
    try {
      let target = current;
      const progress = classifyTranscript(current);
      const edited = progress.kind !== 'review' || text !== progress.text.trim();
      if (edited) {
        let accepted;
        if (current.transcript_revision === null) {
          const signature = JSON.stringify([run.run_id, current.run_revision, 'text', text]);
          const key = retainedActionIdentity(transcriptCorrectionAction, signature);
          accepted = await timeRequest('parent-story-run-idea', () => application.learning.submitTextIdeaV1(run.run_id, current.run_revision, text, key));
        } else {
          const signature = JSON.stringify([run.run_id, current.run_revision, current.transcript_revision, text]);
          const key = retainedActionIdentity(transcriptCorrectionAction, signature);
          accepted = await timeRequest('parent-story-run-idea', () => application.learning.correctTranscriptV1({
            runId: run.run_id,
            runRevision: current.run_revision,
            baseRevision: current.transcript_revision as number,
            text,
            actionIdentity: key,
          }));
        }
        void accepted;
        transcriptCorrectionAction.current = null;
        target = await application.learning.getTranscriptV1(run.run_id);
        applyTranscript(target);
      }
      const reread = classifyTranscript(target);
      if (reread.kind === 'confirmed') {
        setStep('capture');
        setBusy('understanding');
        await settleDrawingStage(run.run_id);
        return;
      }
      if (reread.kind !== 'review') {
        setTranscriptWaiting(reread.kind === 'waiting');
        setError('Chưa có bản chép lời mới để xác nhận. Hãy thử tải lại.');
        return;
      }
      const signature = JSON.stringify([run.run_id, reread.revision, reread.sha256]);
      const key = retainedActionIdentity(transcriptConfirmAction, signature);
      await timeRequest('parent-story-run-transcript', () => application.learning.confirmTranscriptV1(run.run_id, reread.revision, reread.sha256, key));
      transcriptConfirmAction.current = null;
      setTranscript(null);
      setTranscriptTextValue('');
      setStep('capture');
      setBusy('understanding');
      await settleDrawingStage(run.run_id);
    } catch (cause) {
      if (cause instanceof RunWaitCancelled) return;
      if (cause instanceof ParentApplicationError && cause.code === 'STALE_REVISION') {
        transcriptConfirmAction.current = null;
        transcriptCorrectionAction.current = null;
        try {
          applyTranscript(await application.learning.getTranscriptV1(run.run_id));
        } catch { /* the message below already asks for a reload */ }
      }
      const tooLong = cause instanceof ParentApplicationError
        && (cause.fieldErrors ?? []).some((item) => (item.field === 'transcript' || item.field === 'text') && item.code === 'TOO_LONG');
      setError(tooLong
        ? 'Ý tưởng đã nhập và nội dung chép lời dài quá 500 ký tự. Hãy rút gọn bản chép lời rồi xác nhận lại.'
        : safeRunMessage(cause));
    } finally {
      endBusy(busyToken);
    }
  }

  /** FR-P-07, T-2d: one more story revision, asynchronous. The previous story stays until the new draft is ready. */
  async function rewriteStory(hint?: string): Promise<void> {
    const run = contextRun;
    if (busy || !run || !ensureLearningProfileAllowed(profile)) return;
    if (readVideoPanel(run, { spentRevisionNo: spentStoryRevisionNo, confirmedRevisionNo: confirmedStoryRevisionNo }).onlyCancel) return;
    const instruction = (hint ?? rewriteInstruction).trim();
    const busyToken = beginBusy('rewrite');
    setError('');
    setRewriteNotice('');
    try {
      const latest = await getLatestRun(run.run_id);
      if (latest.run_state === 'SCRIPT_GENERATING' || latest.run_state === 'STORY_GENERATING') {
        // A rewrite the server already accepted (a slow wait that ended early): follow it, never send another.
        const range = rewriteRangeForRun(latest);
        await followRewrite(run.run_id, range.fromRevisionNo, range.toRevisionNo);
        return;
      }
      const read = readStoryRevisionReadModel({ story_run: latest }, run.run_id);
      if (read.kind !== 'valid' || (latest.run_state !== 'SCRIPT_REVIEW' && latest.run_state !== 'SAFETY_BLOCKED')
        || read.value.storyRevisionNo !== storyRevisionNo || read.value.storySha256 !== storySha256) {
        if (read.kind === 'valid') adoptServerStory(latest);
        setError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      const fromRevisionNo = read.value.storyRevisionNo;
      const signature = JSON.stringify([run.run_id, fromRevisionNo, read.value.storySha256, instruction]);
      const key = retainedActionIdentity(storyRewriteAction, signature);
      const accepted = await timeRequest('story-rewrite', () => application.learning.rewriteStoryV1(latest, instruction || undefined, key));
      setContextRun({ ...latest, run_state: accepted.run_state, run_revision: accepted.run_revision });
      await followRewrite(run.run_id, fromRevisionNo, accepted.story_revision_no);
    } catch (cause) {
      if (cause instanceof RunWaitCancelled) return;
      if (cause instanceof ParentApplicationError && (cause.code === 'STALE_REVISION' || cause.code === 'STORY_REWRITE_LIMIT_REACHED' || cause.code === 'INVALID_STATE_TRANSITION')) {
        storyRewriteAction.current = null;
      }
      setError(safeRunMessage(cause));
    } finally {
      endBusy(busyToken);
    }
  }

  async function followRewrite(runId: string, fromRevisionNo: number, toRevisionNo: number): Promise<void> {
    const result = await waitRun(
      runId,
      (run) => classifyRewriteProgress(run, { fromRevisionNo, toRevisionNo }).kind !== 'generating',
      { onRun: adoptPolledRun },
    );
    const run = result.value;
    if (!run || result.timedOut) {
      setRewriteNotice('Việc viết lại đang mất lâu hơn dự kiến. Câu chuyện hiện tại vẫn được giữ; hãy quay lại sau.');
      return;
    }
    const progress = classifyRewriteProgress(run, { fromRevisionNo, toRevisionNo });
    if (progress.kind === 'ready') {
      storyRewriteAction.current = null;
      if (!adoptServerStory(run)) {
        setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
        return;
      }
      adoptPolledRun(run);
      setRewriteInstruction('');
      setStep('story');
      return;
    }
    if (progress.kind === 'failed') {
      // The attempt is final on the server (T-2d-fix): the next try is a new command with a new key.
      storyRewriteAction.current = null;
      adoptServerStory(run);
      adoptPolledRun(run);
      setRewriteNotice(progress.retryable
        ? 'Chưa viết lại được. Câu chuyện hiện tại vẫn được giữ nguyên; bạn có thể thử lại.'
        : 'Chưa viết lại được. Câu chuyện hiện tại vẫn được giữ nguyên; bạn có thể xác nhận câu chuyện này hoặc dừng buổi học.');
      return;
    }
    if (progress.kind === 'unknown-outcome') {
      setRewriteNotice('Chưa xác nhận được kết quả viết lại. Không gửi lại yêu cầu; hãy kiểm tra lại sau.');
      return;
    }
    if (progress.kind === 'closed') {
      setError(safeParentFlowErrorMessage({ code: progress.state }));
      return;
    }
    setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
  }

  /** Opens the video step with the latest run; a run that is still working is followed until it settles. */
  async function openVideoStep(explicitRunId?: string): Promise<void> {
    // A resume passes the run it just read: the state of this render does not hold it yet.
    const runId = explicitRunId ?? contextRun?.run_id;
    if (!runId) return;
    setVideoBackStep(step === 'story' ? 'story' : step === 'history' ? 'history' : 'home');
    setStep('video');
    setError('');
    const busyToken = beginBusy('video-refresh');
    try {
      const latest = await readLiveRun(runId);
      adoptPolledRun(latest);
      if (BACKGROUND_RUN_STATES.has(latest.run_state)) await followVideo(runId);
    } catch (cause) {
      if (cause instanceof RunWaitCancelled) return;
      setError(safeRunMessage(cause));
    } finally {
      endBusy(busyToken);
    }
  }

  async function followVideo(runId: string): Promise<ParentStoryRunV1 | null> {
    const result = await waitRun(
      runId,
      (run) => !BACKGROUND_RUN_STATES.has(run.run_state),
      { budgetMs: 15 * 60_000, onRun: adoptPolledRun },
    );
    if (result.value) adoptPolledRun(result.value);
    if (result.timedOut) setError('Video đang được tạo. Bạn có thể rời màn hình này và quay lại sau.');
    return result.value;
  }

  async function refreshVideo(): Promise<void> {
    if (busy) return;
    await openVideoStep();
  }

  async function requestVideo(): Promise<void> {
    const run = contextRun;
    if (busy || !run) return;
    const sessionKnowledge = { spentRevisionNo: spentStoryRevisionNo, confirmedRevisionNo: confirmedStoryRevisionNo };
    const panel = readVideoPanel(run, sessionKnowledge);
    if (!panel.canRequest) return;
    if (panel.requiresReason && videoReason === null) return;
    const reason = panel.requiresReason ? videoReason : null;
    const busyToken = beginBusy('video-request');
    setError('');
    try {
      const latest = await readLiveRun(run.run_id);
      adoptPolledRun(latest);
      if (BACKGROUND_RUN_STATES.has(latest.run_state)) {
        // The earlier request got through (a lost answer): follow it instead of sending another.
        setBusy('video-refresh');
        await followVideo(run.run_id);
        return;
      }
      if (!readVideoPanel(latest, sessionKnowledge).canRequest) {
        setError('Chưa thể tạo video ở trạng thái hiện tại. Hãy mở lại buổi học để xem trạng thái mới nhất.');
        return;
      }
      const signature = JSON.stringify([latest.run_id, latest.run_revision, latest.story_sha256, reason]);
      const key = retainedActionIdentity(videoRequestAction, signature);
      await timeRequest('video-request', () => application.learning.requestVideoV1(latest, reason, key));
      videoRequestAction.current = null;
      setVideoReason(null);
      setBusy('video-refresh');
      const followed = await followVideo(run.run_id);
      if (followed?.run_state === 'SCRIPT_REVIEW' && followed.story_revision_id) {
        adoptServerStory(followed);
        setStep('story');
      }
      // The script is spent only once the generation was not rejected at admission (T-1a: a refused admission keeps it).
      if (followed && followed.video && followed.video.state !== 'ADMISSION_REJECTED') {
        setSpentStoryRevisionNo(latest.story_revision_no);
      }
    } catch (cause) {
      if (cause instanceof RunWaitCancelled) return;
      if (cause instanceof ParentApplicationError && cause.code === 'INVALID_STATE_TRANSITION') {
        videoRequestAction.current = null;
        try {
          const latest = await readLiveRun(run.run_id);
          adoptPolledRun(latest);
          if (latest.run_state === 'SCRIPT_REVIEW' && latest.story_confirmation_required === true) setStep('story');
        } catch {
          // Keep the safe command error when the refresh is unavailable.
        }
        setError(safeParentFlowErrorMessage(cause));
      } else {
        if (isDefinitiveClientError(cause)) videoRequestAction.current = null;
        setError(safeRunMessage(cause));
      }
    } finally {
      endBusy(busyToken);
    }
  }

  /** T-1c: the grant is issued fresh for every open; it is never stored beyond the player source. */
  async function playVideo(userInitiated = true): Promise<void> {
    const runId = contextRun?.run_id;
    if (!runId || (busy && busy !== 'video-playback')) return;
    if (userInitiated) playbackAutoRetries.current = 0;
    setBusy('video-playback');
    setError('');
    try {
      const source = await application.learning.openPlaybackV1(runId);
      playbackOpenedAt.current = Date.now();
      setPlayback(source);
    } catch (cause) {
      setPlayback(null);
      setError(safePlaybackMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function watchHistoryRun(runId: string): Promise<void> {
    if (busy || !runId.trim()) return;
    const busyToken = beginBusy('video-playback');
    setVideoBackStep('history');
    setPlayback(null);
    setError('');
    try {
      const run = await readLiveRun(runId);
      adoptRunForLaterSteps(run);
      setActiveRun(null);
      setStep('video');
      if (run.run_state !== 'COMPLETED' || run.video?.state !== 'READY' || run.video.playback.state !== 'AVAILABLE') {
        setError('Video chưa sẵn sàng hoặc không còn phát được.');
        return;
      }
      const source = await application.learning.openPlaybackV1(runId);
      playbackOpenedAt.current = Date.now();
      setPlayback(source);
    } catch (cause) {
      setError(safePlaybackMessage(cause));
    } finally {
      endBusy(busyToken);
    }
  }

  /** A player error usually means the grant expired mid-stream: ask for a new one once, then stop. */
  function onPlaybackError(): void {
    if (Date.now() - playbackOpenedAt.current < 10_000 || playbackAutoRetries.current >= 1) {
      setPlayback(null);
      setError('Chưa phát được video. Hãy thử mở lại.');
      return;
    }
    playbackAutoRetries.current += 1;
    void playVideo(false);
  }

  function startUnsuitable(): void {
    setMarkingUnsuitable(true);
    setVideoReason(null);
    setError('');
  }

  function cancelUnsuitable(): void {
    setMarkingUnsuitable(false);
    setVideoReason(null);
  }

  async function markVideoUnsuitable(): Promise<void> {
    const run = contextRun;
    if (busy || !run || videoReason === null) return;
    setBusy('video-unsuitable');
    setError('');
    try {
      const latest = await readLiveRun(run.run_id);
      adoptPolledRun(latest);
      const signature = JSON.stringify([latest.run_id, latest.run_revision, latest.video?.current_generation_id ?? null, videoReason]);
      const key = retainedActionIdentity(videoUnsuitableAction, signature);
      const envelope = await timeRequest('video-unsuitable', () => application.learning.markVideoUnsuitableV1(latest, videoReason, key));
      videoUnsuitableAction.current = null;
      const updated = envelope.story_run;
      adoptPolledRun(updated);
      adoptServerStory(updated);
      setPlayback(null);
      setMarkingUnsuitable(false);
      setSpentStoryRevisionNo(updated.story_revision_no);
      if (updated.run_state === 'SCRIPT_REVIEW' && updated.story_revision_id) setStep('story');
      // The reason stays selected: the next request asks for one again (T-1b P3-3).
    } catch (cause) {
      if (cause instanceof ParentApplicationError && cause.status !== undefined && cause.status >= 400 && cause.status < 500
        && cause.code !== 'RATE_LIMITED' && cause.code !== 'REQUEST_TIMEOUT') {
        videoUnsuitableAction.current = null;
      }
      setError(safeRunMessage(cause));
    } finally {
      setBusy('');
    }
  }

  async function completeRun(): Promise<void> {
    const run = contextRun;
    if (busy || !run) return;
    setBusy('video-complete');
    setError('');
    try {
      const latest = await readLiveRun(run.run_id);
      adoptPolledRun(latest);
      const signature = JSON.stringify([latest.run_id, latest.run_revision]);
      const key = retainedActionIdentity(completeRunAction, signature);
      const envelope = await timeRequest('video-complete', () => application.learning.completeRunV1(latest, key));
      completeRunAction.current = null;
      setContextRun(envelope.story_run);
      setActiveRun(null);
      setPlayback(null);
    } catch (cause) {
      if (cause instanceof ParentApplicationError && cause.status !== undefined && cause.status >= 400 && cause.status < 500
        && cause.code !== 'RATE_LIMITED' && cause.code !== 'REQUEST_TIMEOUT') {
        completeRunAction.current = null;
      }
      setError(safeRunMessage(cause));
    } finally {
      setBusy('');
    }
  }

  /** Puts the confirmed subject and context of a resumed run back, so the story and video steps can act on it. */
  function adoptRunForLaterSteps(run: ParentStoryRunV1): void {
    adoptServerStory(run);
    adoptPolledRun(run);
    const understanding = readRunUnderstanding(run);
    if (understanding) {
      setCandidate(understanding.candidate);
      setUnderstandingRevision(understanding.understandingRevision);
      setSubject(understanding.subject);
      setSubjectConfirmed(isConfirmedRunSubject(run, understanding.subject));
    }
  }

  /** Resume of a run the server already moved past the subject review (idle app, other device, restart). */
  async function resumePhaseBRun(run: ParentStoryRunV1): Promise<boolean> {
    const state = run.run_state;
    if (state === 'INPUT_PROCESSING' || state === 'INPUT_REVIEW' || state === 'DRAFT') {
      setStep('capture');
      const busyToken = classifyDrawingProgress(run).kind === 'processing' ? beginBusy('understanding') : null;
      try {
        await handleOrWaitDrawing(run);
      } catch (cause) {
        if (!(cause instanceof RunWaitCancelled)) setPhotoMessage(safeRunMessage(cause));
      } finally {
        if (busyToken !== null) endBusy(busyToken);
      }
      return true;
    }
    if (state === 'SCRIPT_GENERATING') {
      adoptRunForLaterSteps(run);
      setStep('story');
      const busyToken = beginBusy('story');
      try {
        await followFirstStory(run.run_id);
      } catch (cause) {
        if (!(cause instanceof RunWaitCancelled)) setError(safeRunMessage(cause));
      } finally {
        endBusy(busyToken);
      }
      return true;
    }
    if (state === 'STORY_GENERATING') {
      adoptRunForLaterSteps(run);
      setStep('story');
      const busyToken = beginBusy('rewrite');
      try {
        const range = rewriteRangeForRun(run);
        await followRewrite(run.run_id, range.fromRevisionNo, range.toRevisionNo);
      } catch (cause) {
        if (!(cause instanceof RunWaitCancelled)) setError(safeRunMessage(cause));
      } finally {
        endBusy(busyToken);
      }
      return true;
    }
    if (state === 'PREPARATION_REVIEW') {
      const understanding = readRunUnderstanding(run);
      if (!understanding || !adoptServerUnderstanding(run)) return false;
      if (!isConfirmedRunSubject(run, understanding.subject)) return true;
      if (run.main_activity?.state === 'SELECTED' && run.context_confirmed !== true) {
        setStep('context');
        return true;
      }
      if (run.main_activity?.state !== 'SELECTED') {
        setStep('activity');
        await requestActivityList(false, run);
        return true;
      }
      await handleStoryGateResult(run);
      return true;
    }
    const videoStates = new Set(['VIDEO_ADMISSION_PENDING', 'VIDEO_QUEUED', 'VIDEO_GENERATING', 'VIDEO_SAFETY_VALIDATING', 'VIDEO_READY']);
    if (state === 'SCRIPT_REVIEW' && run.story_confirmation_required === true && run.story_revision_id) {
      adoptRunForLaterSteps(run);
      setStep('story');
      return true;
    }
    if (state === 'SAFETY_BLOCKED' && run.story_revision_id) {
      adoptRunForLaterSteps(run);
      setStep('story');
      return true;
    }
    if (videoStates.has(state) || (state === 'SCRIPT_REVIEW' && run.story_status === 'CONFIRMED')) {
      adoptRunForLaterSteps(run);
      await openVideoStep(run.run_id);
      return true;
    }
    if (state === 'SCRIPT_REVIEW' && run.story_revision_id) {
      // A draft (or a draft left by a failed rewrite) is shown for review, never dropped for the activity step.
      adoptRunForLaterSteps(run);
      if (run.job_state === 'FAILED') {
        setRewriteNotice(run.retryable
          ? 'Lần viết lại trước chưa thành công. Câu chuyện hiện tại vẫn được giữ nguyên; bạn có thể thử lại.'
          : 'Lần viết lại trước chưa thành công. Câu chuyện hiện tại vẫn được giữ nguyên; bạn có thể xác nhận câu chuyện này hoặc dừng buổi học.');
      }
      setStep('story');
      return true;
    }
    return false;
  }

  async function handleOrWaitDrawing(run: ParentStoryRunV1): Promise<void> {
    const progress = classifyDrawingProgress(run);
    if (progress.kind === 'processing') {
      await settleDrawingStage(run.run_id);
      return;
    }
    await handleDrawingProgress(run);
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
    setAccountError('');
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
    setSelectedTopicId(''); setTopicDraftId(''); setTopicSuggestionSets([]); setTopicSuggestions([]);
    setTopicSuggestionBusy(false); setTopicSuggestionError(''); topicSuggestionRequestId.current = '';
    subjectSuggestionRequestId.current = ''; setSubjectSuggestionSets([]); setSubjectSuggestions([]);
    setSubjectSuggestionBusy(false); setSubjectSuggestionError(''); setIntendedDrawingSubject('');
    setCustomDrawingSubject(''); setSubjectValidationMessage(''); setCustomSubjectValidated(false);
    setContextRun(null); setContextConfirmed(false); setProfileFieldErrors({});
    setAudioValue(null); setDrawingGuideIndex(0); setUnderstandingRevision(0); setSubjectConfirmed(false); setSubjectRoles([]);
    resetActivityReview();
    setStory(null); setStoryDisplayedRunId(''); setStoryRevisionNo(null); setStorySha256('');
    setStoryAttempted(false); setStoryConfirmed(false); setRewriteCount(0); setRewriteInstruction('');
    setVideoBackStep('home');
    setGuideBase64(''); setGuideEnabled(false); setEvents([]); setError(''); setBusy('');
    profileCreateAction.current = null;
    profilePatchActions.current.clear();
    profileDeleteActions.current.clear();
    runCreationAction.current = null;
    stopWait();
    waitsBlocked.current = true;
    retakeUsed.current = false;
    setConfirmedStoryRevisionNo(null);
    drawingUploadAction.current = null;
    voiceUploadAction.current = null;
    audioSubmittedRunId.current = null;
    transcriptCorrectionAction.current = null;
    transcriptConfirmAction.current = null;
    storyRewriteAction.current = null;
    videoRequestAction.current = null;
    videoUnsuitableAction.current = null;
    completeRunAction.current = null;
    setTranscript(null); setTranscriptTextValue(''); setTranscriptWaiting(false); setRetakeAvailable(false);
    setPlayback(null); setVideoReason(null); setMarkingUnsuitable(false); setSpentStoryRevisionNo(null); setRewriteNotice('');
    contextConfirmationAction.current = null;
    subjectConfirmationAction.current = null;
    scriptConfirmationAction.current = null;
  }

  return {
    step, setStep, videoBackStep, currentUser, profiles, profile, setProfile, selectedProfileId, profileBeingEdited, setProfileBeingEdited,
    pendingDeletions, pendingDeletionLoadingId, profileFieldErrors, consentState,
    publicSettings: application.publicSettings,
    activeRun, topic, setTopic, idea, setIdea, lesson, setLesson, lessons, lessonLoading, lessonLoadingId, lessonError,
    selectedTopicId, topicSuggestions, topicSuggestionBusy, topicSuggestionError,
    subjectSuggestionSets, subjectSuggestions, subjectSuggestionBusy, subjectSuggestionError,
    intendedDrawingSubject, customDrawingSubject, subjectValidationMessage,
    beginTopicPath,
    beginLessonPath: () => void openLessons('picker'),
    selectTopicCard, setCustomTopic, refreshTopicSuggestions, continueTopicSelection, skipTopicSelection,
    selectDrawingSubject, setCustomSubject, validateCustomDrawingSubject, refreshSubjectSuggestions,
    continueFromSubjectSelection,
    galleryMode, galleryLesson, lessonInvitations, groupInvitations, accountError, guideEnabled, setGuideEnabled,
    guideBase64, guideBusy, guideError, photo, setPhoto, audio, setAudio,
    contextRun, contextConfirmed, candidate, subject, setSubject, subjectConfirmed, understandingRevision,
    activitySuggestions, selectedActivityIndex, activityBusy, activityAttempted, activityError,
    requestActivityList, chooseActivity, selectActivity, cancelEmptyActivityRun,
    story, storyDisplayedRunId, storyRevisionNo,
    storySha256, storyAttempted,
    storyConfirmed, rewriteCount, rewriteInstruction, setRewriteInstruction, events, busy, error, authError, bootstrapBusy,
    loadParentData, authenticate, signInWithGoogle, resetPassword, createProfileAndReturn, updateProfile,
    selectProfile, requestProfileDeletion, refreshPendingDeletion, continueWithProfile, openLessons, chooseLesson, acceptLessonInvitation,
    declineLessonInvitation, acceptGroupInvitation, createGuide, openDrawingGuide, openContextReview, confirmContext,
    continueToCapture, analyzeDrawingForCurrentRun, confirmSubject,
    subjectRoles, renameSecondarySubject, toggleSecondarySubject, makeMainSubject,
    confirmStory, refreshStory, drawingGuideIndex, setDrawingGuideIndex,
    resumeActiveRun, changePassword, resetCurrentPassword, signOut,
    leaveWait,
    transcript, transcriptText, setTranscriptText, transcriptWaiting, refreshTranscript, confirmTranscriptReview,
    transcriptEdited: transcript !== null && classifyTranscript(transcript).kind === 'review'
      ? transcriptText.trim() !== (transcript.text ?? '').trim()
      : transcriptText.trim().length > 0,
    retakeAvailable, rewriteStory, rewriteNotice,
    videoPanel: readVideoPanel(contextRun, { spentRevisionNo: spentStoryRevisionNo, confirmedRevisionNo: confirmedStoryRevisionNo }),
    playback, videoReason, setVideoReason, markingUnsuitable, startUnsuitable, cancelUnsuitable,
    openVideoStep, refreshVideo, requestVideo, playVideo, onPlaybackError, markVideoUnsuitable, completeRun,
    watchHistoryRun,
    storyConfirmationRequired: contextRun?.story_confirmation_required === true,
    storyOnlyCancel: Boolean(contextRun && readVideoPanel(contextRun, { spentRevisionNo: spentStoryRevisionNo, confirmedRevisionNo: confirmedStoryRevisionNo }).onlyCancel),
    rewriteAfterVideo: Boolean(contextRun?.story_status === 'CONFIRMED' && contextRun.story_confirmation_required === true),
    retryContextCreation: createContextRun,
    resetWorkflow, backToProfile: () => { setStep('profile'); setError(''); },
    clearProfileFormErrors: () => setProfileFieldErrors({}),
    clearAuthError: () => setAuthError(''),
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

type RetainedKeySet<Name extends string> = {
  signature: string;
  keys: Record<Name, ParentActionIdentity>;
};

/** One key per command of a multi-call action (upload create, complete, attach), kept while the file is the same. */
function retainedKeySet<Name extends string>(
  reference: { current: RetainedKeySet<Name> | null },
  signature: string,
  names: readonly Name[],
): Record<Name, ParentActionIdentity> {
  if (!reference.current || reference.current.signature !== signature) {
    const keys = {} as Record<Name, ParentActionIdentity>;
    for (const name of names) keys[name] = createParentActionIdentity();
    reference.current = { signature, keys };
  }
  return reference.current.keys;
}

/** A 4xx other than a timeout or a rate limit is final: the next try needs fresh keys, not a replay. */
function isDefinitiveClientError(cause: unknown): boolean {
  return cause instanceof ParentApplicationError
    && cause.status !== undefined && cause.status >= 400 && cause.status < 500
    && cause.status !== 408 && cause.status !== 429;
}

/** A read that may succeed on the next try (the wait keeps going) versus one that must stop it. */
function isTransientReadError(cause: unknown): boolean {
  if (!(cause instanceof ParentApplicationError)) return false;
  return ['NETWORK_ERROR', 'REQUEST_TIMEOUT', 'HTTP_429', 'HTTP_502', 'HTTP_503', 'HTTP_504', 'RATE_LIMITED'].includes(cause.code)
    || cause.retryable === true;
}

/** Calm wording for run commands: the shared codes say "profile", the object here is the learning session. */
function safeRunMessage(cause: unknown): string {
  const code = cause instanceof ParentApplicationError ? cause.code : null;
  if (code === 'STALE_REVISION' || code === 'INVALID_STATE_TRANSITION') {
    return 'Buổi học đã thay đổi. Hãy mở lại buổi học để xem trạng thái mới nhất.';
  }
  if (code === 'SUBSCRIPTION_RESTRICTED') return 'Gói dịch vụ hiện tại chưa cho phép tạo video.';
  return safeParentFlowErrorMessage(cause);
}

/** The player or the grant failed: never show the grant, the address or a raw code. */
function safePlaybackMessage(cause: unknown): string {
  if (isParentSessionExpired(cause)) return safeParentIdentityErrorMessage(cause);
  if (cause instanceof ParentApplicationError) {
    if (cause.code === 'PLAYBACK_TOKEN_REJECTED') return 'Chưa mở được video. Hãy thử lại sau ít phút.';
    if (cause.code === 'INVALID_STATE_TRANSITION') return 'Video này không còn phát được trong ứng dụng.';
    if (cause.code === 'RESOURCE_NOT_FOUND') return 'Video chưa sẵn sàng hoặc không còn phát được.';
  }
  return safeParentFlowErrorMessage(cause);
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
