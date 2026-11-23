import { useRef, useState } from 'react';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { createParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ActivitySuggestionResult } from '../../application/ports/ParentPorts';
import type { ParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import { parseStoryDraft } from '../../domain/storyDraft';
import { isResolvedTopicConsistent } from '../../domain/topicMatching';
import type {
  LessonDetail,
  LessonInvitation,
  LessonSummary,
  ParentDrawingCandidateV1,
  ParentGroupInvitation,
  ParentProfileDeletePendingV1,
  ParentProfileViewV1,
  ParentStoryRunV1,
  ParentTopicCardV1,
  ParentTopicSuggestionSetV1,
  ParentDrawingSubjectCardV1,
  ParentDrawingSubjectSuggestionSetV1,
  ParentUser,
  StoryDraft,
  SuggestedActivity,
} from '../../domain/types';
import { requireLiveStoryRun } from '../../application/storyRunResult';
import type { SvgTopicStrokeGuideDraftV1 } from '../../domain/svgGuide';
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
  isTerminalFailedStoryRun,
  isRecoverableStoryOutputFailure,
  isSafePreDispatchDrawingError,
  readErrorCode,
  terminalDrawingFailureMessage,
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
  const [selectedTopicId, setSelectedTopicId] = useState('');
  const [topicDraftId, setTopicDraftId] = useState('');
  const [topicSuggestionSets, setTopicSuggestionSets] = useState<ParentTopicSuggestionSetV1[]>([]);
  const [topicSuggestions, setTopicSuggestions] = useState<ParentTopicCardV1[]>([]);
  const [topicSuggestionBusy, setTopicSuggestionBusy] = useState(false);
  const [topicSuggestionError, setTopicSuggestionError] = useState('');
  const lastTopicSuggestionSetId = useRef('');
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
  const [svgGuideDraft, setSvgGuideDraft] = useState<SvgTopicStrokeGuideDraftV1 | null>(null);
  const [drawingGuideIndex, setDrawingGuideIndex] = useState(0);
  const [photo, setPhotoValue] = useState<SelectedPhoto | null>(null);
  const [audio, setAudioValue] = useState<SelectedAudio | null>(null);
  const [contextRun, setContextRun] = useState<ParentStoryRunV1 | null>(null);
  const [contextConfirmed, setContextConfirmed] = useState(false);
  const [candidate, setCandidate] = useState<ParentDrawingCandidateV1 | null>(null);
  const [subject, setSubject] = useState('');
  const [subjectConfirmed, setSubjectConfirmed] = useState(false);
  const [understandingRevision, setUnderstandingRevision] = useState(0);
  const [activitySuggestions, setActivitySuggestions] = useState<ActivitySuggestionResult | null>(null);
  const [selectedActivityIndex, setSelectedActivityIndex] = useState<number | null>(null);
  const [activityBusy, setActivityBusy] = useState(false);
  const [activityAttempted, setActivityAttempted] = useState(false);
  const [activityError, setActivityError] = useState('');
  const [activitySelectionPersisted, setActivitySelectionPersisted] = useState(false);
  const [activitySelectionBusy, setActivitySelectionBusy] = useState(false);
  const [story, setStory] = useState<StoryDraft | null>(null);
  const [storyDraftCurrent, setStoryDraftCurrent] = useState(false);
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
  const activitySuggestionAction = useRef<RetainedActionIdentity | null>(null);
  const activitySelectionAction = useRef<RetainedActionIdentity | null>(null);
  const activitySuggestionInFlight = useRef(false);
  const activitySelectionInFlight = useRef(false);
  const storyRevisionAction = useRef<RetainedActionIdentity | null>(null);
  const scriptConfirmationAction = useRef<RetainedActionIdentity | null>(null);
  const runCreationInFlight = useRef(false);
  const drawingAnalysisInFlight = useRef(false);
  const drawingAnalysisAttemptedRunId = useRef<string | null>(null);
  const drawingAnalysisRetryRunId = useRef<string | null>(null);

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
    setStep('entry');
  }

  async function beginTopicPath(): Promise<void> {
    const draftId = createDraftUuid();
    const previousTopicSetId = lastTopicSuggestionSetId.current;
    setTopicDraftId(draftId);
    setTopic('');
    setSelectedTopicId('');
    setIntendedDrawingSubject('');
    setSubjectSuggestions([]);
    setTopicSuggestionSets([]);
    setSubjectSuggestionSets([]);
    setTopicSuggestionError('');
    setSubjectSuggestionError('');
    setStep('topic');
    await loadTopicSuggestionSet(draftId, previousTopicSetId ? [previousTopicSetId] : []);
  }

  async function loadTopicSuggestionSet(draftId: string, excludedSetIds: string[]): Promise<void> {
    setTopicSuggestionBusy(true);
    setTopicSuggestionError('');
    try {
      const result = await application.learning.listTopicSuggestions(draftId, excludedSetIds);
      if (
        result.contract !== 'ParentTopicSuggestionSetV1'
        || result.draft_id !== draftId
        || result.cards.length !== 3
        || new Set(result.cards.map((card) => card.topic_id)).size !== 3
        || excludedSetIds.includes(result.set_id)
      ) {
        throw new ParentApplicationError('PARENT_TOPIC_SUGGESTION_INVALID', 'Chưa nhận được ba gợi ý chủ đề hợp lệ.');
      }
      setTopicSuggestionSets((current) => [...current, result]);
      setTopicSuggestions([...result.cards]);
      lastTopicSuggestionSetId.current = result.set_id;
    } catch (cause) {
      setTopicSuggestionError(topicSuggestionErrorMessage(cause));
    } finally {
      setTopicSuggestionBusy(false);
    }
  }

  async function refreshTopicSuggestions(): Promise<void> {
    if (!topicDraftId || topicSuggestionBusy) return;
    const excluded = topicSuggestionSets.map((set) => set.set_id);
    await loadTopicSuggestionSet(topicDraftId, excluded);
  }

  function selectTopicCard(card: ParentTopicCardV1): void {
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
    if (selectedTopic.length < 2 || !topicDraftId || topicSuggestionBusy) {
      setTopicSuggestionError('Chọn một chủ đề hoặc nhập chủ đề riêng trước khi tiếp tục.');
      return;
    }
    const topicId = selectedTopicId || 'custom';
    setSubjectSuggestionBusy(true);
    setSubjectSuggestionError('');
    setIntendedDrawingSubject('');
    try {
      const result = await application.learning.listDrawingSubjectSuggestions({
        draftId: topicDraftId,
        topicId,
        topic: selectedTopic,
        excludedSetIds: subjectSuggestionSets.map((set) => set.set_id),
        excludedSubjects: subjectSuggestionSets.flatMap((set) =>
          set.cards.flatMap((card) => [card.title_vi, card.guide_subject]),
        ),
      });
      const contractMatches = result?.contract === 'ParentDrawingSubjectSuggestionSetV1';
      const draftMatches = result?.draft_id === topicDraftId;
      const topicConsistent = typeof result?.topic_id === 'string'
        && typeof result?.topic === 'string'
        && isResolvedTopicConsistent({
          selectedTopicId: selectedTopicId || 'custom',
          selectedTopic,
          resolvedTopicId: result.topic_id,
          resolvedTopic: result.topic,
        });
      const cards = Array.isArray(result?.cards) ? result.cards : [];
      const uniqueSubjectCount = new Set(cards.map((card) => card?.subject_id).filter((id) => typeof id === 'string')).size;
      const setIsFresh = !subjectSuggestionSets.some((set) => set.set_id === result?.set_id);
      if (!contractMatches || !draftMatches || !topicConsistent || cards.length !== 3 || uniqueSubjectCount !== 3 || !setIsFresh) {
        if (__DEV__) {
          console.warn('parent_topic_subject_contract_rejected', {
            contract_matches: contractMatches,
            draft_matches: draftMatches,
            topic_consistent: topicConsistent,
            card_count: cards.length,
            unique_subject_count: uniqueSubjectCount,
            set_is_fresh: setIsFresh,
          });
        }
        throw new ParentApplicationError('PARENT_SUBJECT_SUGGESTION_INVALID', 'Chưa nhận được ba gợi ý phù hợp.');
      }
      setSelectedTopicId(result.topic_id);
      setTopic(result.topic);
      setSubjectSuggestionSets((current) => [...current, result]);
      setSubjectSuggestions([...result.cards]);
      setStep('subject');
    } catch (cause) {
      setTopicSuggestionError(topicSuggestionErrorMessage(cause));
      setSubjectSuggestionError(topicSuggestionErrorMessage(cause));
    } finally {
      setSubjectSuggestionBusy(false);
    }
  }

  async function refreshSubjectSuggestions(): Promise<void> {
    if (!topicDraftId || !topic || subjectSuggestionBusy) return;
    setSubjectSuggestionBusy(true);
    setSubjectSuggestionError('');
    try {
      const result = await application.learning.listDrawingSubjectSuggestions({
        draftId: topicDraftId,
        topicId: selectedTopicId,
        topic,
        excludedSetIds: subjectSuggestionSets.map((set) => set.set_id),
        excludedSubjects: subjectSuggestionSets.flatMap((set) =>
          set.cards.flatMap((card) => [card.title_vi, card.guide_subject]),
        ),
      });
      if (
        result.draft_id !== topicDraftId
        || result.cards.length !== 3
        || result.topic_id !== selectedTopicId
        || new Set(result.cards.map((card) => card.subject_id)).size !== 3
        || subjectSuggestionSets.some((set) => set.set_id === result.set_id)
      ) {
        throw new ParentApplicationError('PARENT_SUBJECT_SUGGESTION_INVALID', 'Chưa nhận được ba gợi ý khác cho chủ đề này.');
      }
      setSubjectSuggestionSets((current) => [...current, result]);
      setSubjectSuggestions([...result.cards]);
      setIntendedDrawingSubject('');
      setCustomSubjectValidated(false);
    } catch (cause) {
      setSubjectSuggestionError(topicSuggestionErrorMessage(cause));
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
    if (customDrawingSubject.trim().length < 2 || !selectedTopicId || !topic) return;
    setSubjectSuggestionBusy(true);
    setSubjectValidationMessage('');
    try {
      const result = await application.learning.validateCustomSubject({
        topicId: selectedTopicId,
        topic,
        subject: customDrawingSubject.trim(),
      });
      setSubjectValidationMessage(result.message_vi);
      if (result.decision === 'ON_TOPIC' && result.normalized_subject) {
        setIntendedDrawingSubject(result.normalized_subject);
        setCustomSubjectValidated(true);
      } else {
        setIntendedDrawingSubject('');
        setCustomSubjectValidated(false);
      }
    } catch (cause) {
      setSubjectValidationMessage(displayError(cause));
      setCustomSubjectValidated(false);
    } finally {
      setSubjectSuggestionBusy(false);
    }
  }

  function continueFromSubjectSelection(): void {
    if (!intendedDrawingSubject.trim()) return;
    setIdea('');
    setStep('idea');
  }

  function skipTopicSelection(): void {
    setTopic('');
    setSelectedTopicId('');
    setIntendedDrawingSubject('');
    setIdea('');
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
        setTopic(detail.topic);
        setSelectedTopicId('lesson');
        setIntendedDrawingSubject(detail.drawing_subject);
        setIdea('');
        setGuideEnabled(true);
        setSvgGuideDraft(null);
        setGuideError('');
        setStep('drawing-guide');
        await loadSvgGuide(detail.topic, detail.drawing_subject);
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

  async function loadSvgGuide(topicValue: string, intendedSubjectValue: string): Promise<boolean> {
    setGuideBusy(true);
    setGuideBase64('');
    setGuideError('');
    setSvgGuideDraft(null);
    try {
      const draft = await application.learning.generateSketchGuide(
        topicValue.trim(),
        intendedSubjectValue.trim() || topicValue.trim(),
      );
      if (draft.contract !== 'SvgTopicStrokeGuideSourceDraftV1'
        || draft.status !== 'DRAFT'
        || draft.review_required !== true
        || draft.persisted !== false
        || draft.guide.stages.length < 4
        || draft.guide.stages.length > 8) {
        throw new ParentApplicationError('PARENT_SVG_GUIDE_INVALID', 'Máy chủ chưa trả về hướng dẫn SVG 4–8 bước hợp lệ.');
      }
      setSvgGuideDraft(draft);
      return true;
    } catch (cause) {
      setGuideError(parentSvgGuideFailureMessage(cause));
      return false;
    } finally {
      setGuideBusy(false);
    }
  }

  async function createGuide(): Promise<void> {
    if (!guideEnabled || !topic.trim()) return;
    const loaded = await loadSvgGuide(topic, intendedDrawingSubject || lesson?.drawing_subject || topic);
    if (loaded) {
      setDrawingGuideIndex(0);
      setStep('drawing-guide');
    }
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
    setPhotoValue({ ...value, locked: false, analysisError: undefined, analysisRetryable: false } as SelectedPhoto);
    setError('');
  }

  function setPhotoMessage(message: string, retryable = false): void {
    setPhotoValue((current) => current
      ? { ...current, analysisError: message, analysisTerminal: false, analysisRetryable: retryable }
      : current);
  }

  function setTerminalDrawingFailure(errorCode: unknown): void {
    setPhotoValue((current) => current
      ? {
        ...current,
        locked: true,
        analysisError: terminalDrawingFailureMessage(errorCode),
        analysisTerminal: true,
        analysisRetryable: false,
      }
      : current);
  }

  function resetActivityReview(): void {
    setActivitySuggestions(null);
    setSelectedActivityIndex(null);
    setActivityBusy(false);
    setActivityAttempted(false);
    setActivityError('');
    setActivitySelectionPersisted(false);
    setActivitySelectionBusy(false);
    activitySuggestionAction.current = null;
    activitySelectionAction.current = null;
    activitySuggestionInFlight.current = false;
    activitySelectionInFlight.current = false;
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
        intendedDrawingSubject,
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
      drawingAnalysisAttemptedRunId.current = null;
      drawingAnalysisRetryRunId.current = null;
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
    if (guideEnabled && topic.trim()) {
      if (svgGuideDraft) setStep('drawing-guide');
      else if (guideError) {
        setGuideEnabled(false);
        setGuideError('');
        setStep('capture');
      }
      else void createGuide();
    } else {
      setStep('capture');
    }
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
    setStoryDraftCurrent(
      run.run_state === 'SCRIPT_REVIEW'
      && (run.story_status === 'DRAFT' || run.story_status === 'CONFIRMED')
      && run.story_revision_no === readModel.value.storyRevisionNo
      && run.story_sha256 === readModel.value.storySha256,
    );
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
    // A new controller starts with local revision 0. Do not treat that empty
    // client snapshot as a stale update when hydrating a persisted server run.
    const sameClientRun = contextRun?.run_id === run.run_id;
    const revisionChanged = sameClientRun
      && readModel.understandingRevision !== understandingRevision;
    const contextChanged = Boolean(sameClientRun && contextRun && (
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
      setStoryDraftCurrent(false);
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
    const storyPending = isActiveOrUnreconciledStoryRun(run)
      || run.run_state === 'SCRIPT_GENERATING'
      || run.run_state === 'SCRIPT_GENERATION_UNKNOWN';
    if (storyPending) {
      // The server owns the in-flight state. Resume at its status screen and never
      // present activity/story actions that could create a second command.
      setStoryDraftCurrent(false);
      setStoryConfirmed(false);
      setStep('story');
      setError('');
      return true;
    }
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
    const isManualPreDispatchRetry = selectedPhoto.analysisRetryable === true
      && drawingAnalysisRetryRunId.current !== runId;
    drawingAnalysisInFlight.current = true;
    setBusy('understanding');
    setError('');
    let uploadAttempted = false;
    try {
      const latest = await getLatestRun(runId);
      setContextRun(latest);
      if (isTerminalFailedStoryRun(latest)) {
        setTerminalDrawingFailure(latest.error_code);
        return;
      }
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
        if (!isManualPreDispatchRetry) {
          setPhotoMessage('Chưa có phiên tải lên có thể tiếp tục. Không gửi lại ảnh; hãy kiểm tra trạng thái buổi học sau.');
          return;
        }
      }
      if (isManualPreDispatchRetry) {
        drawingAnalysisRetryRunId.current = runId;
        setPhotoValue((current) => current
          ? { ...current, analysisError: undefined, analysisRetryable: false }
          : current);
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
      resetActivityReview();
      setStep('understanding');
    } catch (cause) {
      if (uploadAttempted) {
        try {
          const latest = await getLatestRun(runId);
          setContextRun(latest);
          if (isTerminalFailedStoryRun(latest)) {
            setTerminalDrawingFailure(latest.error_code ?? readErrorCode(cause));
          } else if (latest.current_input_revision !== 1) {
            if (!adoptServerUnderstanding(latest)) {
              setPhotoMessage('Ảnh đã được gắn với buổi học nhưng máy chủ chưa trả về kết quả xem xét. Không gửi lại ảnh trong buổi học này.');
            }
          } else {
            setPhotoMessage(
              safeParentFlowErrorMessage(cause),
              drawingAnalysisRetryRunId.current !== runId && isSafePreDispatchDrawingError(cause),
            );
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
      const createdRun = await createContextRun();
      if (createdRun) await analyzeDrawingForRun(createdRun.run_id);
      return;
    }
    await analyzeDrawingForRun(contextRun.run_id);
  }

  async function closeUnresolvedDrawingRun(): Promise<void> {
    if (busy || !contextRun || !photo?.analysisError) return;
    if (!photo.analysisTerminal && (contextRun.current_input_revision ?? 0) <= 1) return;
    const runId = contextRun.run_id;
    setBusy('close-run');
    setError('');
    try {
      // A FAILED run is already closed server-side (active lock released) and is not
      // cancel-eligible (SRS UC-11). Re-read it and only leave it locally; deleting
      // its content stays an explicit history action (UC-07).
      const latest = await getLatestRun(runId);
      if (!isTerminalFailedStoryRun(latest)) {
        const receipt = await timeRequest(
          'parent-story-run-cancel',
          () => application.platform.cancelRun(runId),
        );
        if (receipt.lifecycle.run_id !== runId || receipt.lifecycle.run_state !== 'DELETE_PENDING') {
          throw new ParentApplicationError('PARENT_STORY_REVISION_INVALID', 'The cancelled run did not match the active Parent run.');
        }
      }
      setContextRun(null);
      setActiveRun(null);
      setContextConfirmed(false);
      setCandidate(null);
      setSubject('');
      setSubjectConfirmed(false);
      setUnderstandingRevision(0);
      resetActivityReview();
      setStory(null);
      setStoryDraftCurrent(false);
      setStoryDisplayedRunId('');
      setStoryRevisionNo(null);
      setStorySha256('');
      setStoryAttempted(false);
      setStoryConfirmed(false);
      setRewriteCount(0);
      setRewriteInstruction('');
      setPhotoValue((current) => current
        ? { ...current, locked: false, analysisError: undefined, analysisTerminal: false } as SelectedPhoto
        : null);
      drawingAnalysisAttemptedRunId.current = null;
      drawingAnalysisRetryRunId.current = null;
      runCreationAction.current = null;
      contextConfirmationAction.current = null;
      subjectConfirmationAction.current = null;
      storyRevisionAction.current = null;
      scriptConfirmationAction.current = null;
      setStep('capture');
      setError('Buổi cũ đã được đóng. Ảnh vẫn ở thiết bị; tiếp tục sẽ tạo một buổi mới.');
    } catch (cause) {
      setPhotoMessage(safeParentFlowErrorMessage(cause));
    } finally {
      setBusy('');
    }
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
      resetActivityReview();
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

  async function requestActivitySuggestions(): Promise<void> {
    if (activityBusy || activitySuggestionInFlight.current || (activityAttempted && activitySuggestions)) return;
    if (!ensureLearningProfileAllowed(profile)) return;
    const run = contextRun;
    if (!run || !contextConfirmed || !subjectConfirmed || !isConfirmedRunSubject(run, subject)) {
      setActivityError('Xác nhận chủ thể và ngữ cảnh của buổi học trước khi tìm hoạt động.');
      return;
    }

    setActivityBusy(true);
    activitySuggestionInFlight.current = true;
    try {
      const latest = await getLatestRun(run.run_id);
      if (isActiveOrUnreconciledStoryRun(latest)
        || latest.run_state === 'SCRIPT_GENERATING'
        || latest.run_state === 'SCRIPT_GENERATION_UNKNOWN') {
        adoptServerUnderstanding(latest);
        return;
      }
      const latestUnderstanding = readRunUnderstanding(latest);
      if (latest.context_revision !== run.context_revision
        || latest.context_snapshot_sha256 !== run.context_snapshot_sha256
        || !latestUnderstanding
        || latestUnderstanding.understandingRevision !== understandingRevision
        || !isConfirmedRunSubject(latest, subject)) {
        setActivityError(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }));
        return;
      }
      setActivityAttempted(true);
      setActivityError('');
      setActivitySuggestions(null);
      setSelectedActivityIndex(null);
      setActivitySelectionPersisted(false);
      setActivitySelectionBusy(false);
      activitySelectionAction.current = null;
      const actionIdentity = retainedActionIdentity(
        activitySuggestionAction,
        JSON.stringify([run.run_id, understandingRevision, latest.context_revision, latest.context_snapshot_sha256]),
      );
      const result = await timeRequest(
        'activity-suggestions',
        () => application.learning.suggestActivities(run.run_id, understandingRevision, actionIdentity),
      );
      if (result.story_run_id !== run.run_id
        || !result.suggestion_set_id
        || !Number.isInteger(result.set_revision)
        || result.understanding_revision !== understandingRevision
        || !/^[0-9a-f]{64}$/.test(result.activities_snapshot_sha256)
        || result.contract !== 'ParentActivitySuggestionSetV1'
        || result.review_required !== true
        || !Array.isArray(result.activities)
        || result.activities.length === 0) {
        throw new ParentApplicationError('PARENT_ACTIVITY_RESPONSE_INVALID', 'Chưa nhận được danh sách hoạt động hợp lệ.');
      }
      setActivitySuggestions(result);
      activitySuggestionAction.current = null;
    } catch (cause) {
      setActivityError(safeParentFlowErrorMessage(cause));
      // A retry is a new user action. There are no automatic retries for a Modal-backed request.
      activitySuggestionAction.current = null;
    } finally {
      activitySuggestionInFlight.current = false;
      setActivityBusy(false);
    }
  }

  async function chooseActivity(index: number): Promise<void> {
    if (activitySelectionInFlight.current
      || !activitySuggestions
      || !contextRun
      || !Number.isInteger(index)
      || index < 0
      || index >= activitySuggestions.activities.length) return;
    if (selectedActivityIndex === index && activitySelectionPersisted) return;

    const suggestionSetId = activitySuggestions.suggestion_set_id;
    const runId = contextRun.run_id;
    const actionIdentity = retainedActionIdentity(
      activitySelectionAction,
      JSON.stringify([runId, suggestionSetId, understandingRevision, index]),
    );
    setSelectedActivityIndex(index);
    setActivitySelectionPersisted(false);
    setActivitySelectionBusy(true);
    activitySelectionInFlight.current = true;
    setActivityError('');
    try {
      const receipt = await timeRequest('activity-selection', () => application.learning.selectActivity({
        runId,
        suggestionSetId,
        revision: understandingRevision,
        activityIndex: index,
        actionIdentity,
      }));
      if (receipt.contract !== 'ParentActivitySelectionReceiptV1'
        || receipt.story_run_id !== runId
        || receipt.suggestion_set_id !== suggestionSetId
        || receipt.understanding_revision !== understandingRevision
        || receipt.activity_index !== index
        || !receipt.activity_selection_id
        || !/^[0-9a-f]{64}$/.test(receipt.activity_snapshot_sha256)) {
        throw new ParentApplicationError('PARENT_ACTIVITY_SELECTION_RESPONSE_INVALID', 'Chưa xác nhận được lựa chọn đã lưu.');
      }
      setActivitySelectionPersisted(true);
    } catch (cause) {
      setActivitySelectionPersisted(false);
      setActivityError(safeParentFlowErrorMessage(cause));
      activitySelectionAction.current = null;
    } finally {
      activitySelectionInFlight.current = false;
      setActivitySelectionBusy(false);
    }
  }

  async function requestStory(instruction?: string, allowSameActionRetry = false): Promise<void> {
    if (busy) return;
    if (!ensureLearningProfileAllowed(profile)) return;
    if (selectedActivityIndex === null || !activitySuggestions?.activities[selectedActivityIndex]) {
      setError('Chọn một hoạt động phù hợp trước khi tạo câu chuyện.');
      return;
    }
    if (!activitySelectionPersisted) {
      setError('Chưa thể tạo câu chuyện: lựa chọn hoạt động chưa được lưu vào buổi học.');
      return;
    }
    const runId = contextRun?.run_id;
    const normalizedInstruction = instruction?.trim() ?? '';
    const expectedContextRevision = contextRun?.context_revision;
    const expectedContextHash = contextRun?.context_snapshot_sha256 ?? '';
    const signature = runId
      ? JSON.stringify([runId, expectedContextRevision, expectedContextHash, understandingRevision, normalizedInstruction || null, storyRevisionNo, storySha256])
      : '';
    const sameRetainedAction = Boolean(signature && storyRevisionAction.current?.signature === signature);
    const failedGeneration = isRecoverableStoryOutputFailure(contextRun);
    const canRequest = canRequestStoryRevision({
      runId,
      understandingRevision,
      storyPresent: Boolean(story),
      storyAttempted,
      failedGeneration,
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
      const latestFailedGeneration = isRecoverableStoryOutputFailure(latest);
      const newAdultRewriteAfterFailure = isRewrite && latestFailedGeneration && !sameRetainedAction;
      if (storyRevisionAction.current && !sameRetainedAction && !newAdultRewriteAfterFailure) {
        setError('Hãy kiểm tra và gửi lại yêu cầu viết đang chờ trước khi bắt đầu yêu cầu khác.');
        return;
      }
      if (latest.story_status === 'FAILED'
        && !newAdultRewriteAfterFailure
        && (!sameRetainedAction || latest.retryable !== true)) {
        setError(safeParentFlowErrorMessage({ code: 'PARENT_STORY_REVISION_INVALID' }));
        return;
      }
      if (newAdultRewriteAfterFailure) storyRevisionAction.current = null;
      if (!story && latestHasStory) {
        adoptServerStory(latest);
        return;
      }

      const actionIdentity = retainedActionIdentity(storyRevisionAction, signature);
      const isNewAction = !sameRetainedAction;
      setStoryAttempted(true);
      if (isRewrite) setStoryDraftCurrent(false);
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
      setStoryDraftCurrent(true);
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
      if (runId) {
        setStoryDraftCurrent(false);
        if (isRewrite) setStoryConfirmed(false);
        try {
          const latest = await getLatestRun(runId);
          setContextRun(latest);
          setActiveRun(latest);
          if (isRecoverableStoryOutputFailure(latest)) {
            const failedRevisionNo = latest.story_revision_no ?? 1;
            setStoryRevisionNo(failedRevisionNo);
            setRewriteCount(Math.max(0, failedRevisionNo - 1));
            storyRevisionAction.current = null;
          }
          const currentDraft = latest.run_state === 'SCRIPT_REVIEW'
            && (latest.story_status === 'DRAFT' || latest.story_status === 'CONFIRMED');
          if (currentDraft && !adoptServerStory(latest)) {
            setStoryDraftCurrent(false);
          }
        } catch {
          setStoryDraftCurrent(false);
        }
      }
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
    setSubjectSuggestionSets([]); setSubjectSuggestions([]); setIntendedDrawingSubject(''); setCustomDrawingSubject('');
    setSubjectValidationMessage(''); setCustomSubjectValidated(false); setSvgGuideDraft(null);
    setTopicSuggestionBusy(false); setTopicSuggestionError(''); setSubjectSuggestionBusy(false); setSubjectSuggestionError('');
    setContextRun(null); setContextConfirmed(false); setProfileFieldErrors({});
    setAudioValue(null); setDrawingGuideIndex(0); setUnderstandingRevision(0); setSubjectConfirmed(false);
    resetActivityReview();
    setStory(null); setStoryDraftCurrent(false); setStoryDisplayedRunId(''); setStoryRevisionNo(null); setStorySha256('');
    setStoryAttempted(false); setStoryConfirmed(false); setRewriteCount(0); setRewriteInstruction('');
    setGuideBase64(''); setGuideEnabled(false); setEvents([]); setError(''); setBusy('');
    setActivitySelectionPersisted(false);
    profileCreateAction.current = null;
    profilePatchActions.current.clear();
    profileDeleteActions.current.clear();
    runCreationAction.current = null;
    drawingAnalysisAttemptedRunId.current = null;
    drawingAnalysisRetryRunId.current = null;
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
    guideBase64, guideBusy, guideError, svgGuideDraft, photo, setPhoto, audio, setAudio,
    selectedTopicId, topicSuggestions, topicSuggestionBusy, topicSuggestionError,
    subjectSuggestionSets, subjectSuggestions, subjectSuggestionBusy, subjectSuggestionError,
    intendedDrawingSubject, customDrawingSubject, subjectValidationMessage,
    beginTopicPath, beginLessonPath: () => void openLessons('picker'),
    selectTopicCard, setCustomTopic, refreshTopicSuggestions, continueTopicSelection, skipTopicSelection,
    selectDrawingSubject, setCustomSubject, validateCustomDrawingSubject, refreshSubjectSuggestions,
    continueFromSubjectSelection,
    contextRun, contextConfirmed, candidate, subject, setSubject, subjectConfirmed, understandingRevision,
    activitySuggestions, selectedActivityIndex, activityBusy, activityAttempted, activityError,
    activitySelectionPersisted, activitySelectionBusy, requestActivitySuggestions, chooseActivity,
    story, storyDraftCurrent, storyDisplayedRunId, storyRevisionNo,
    storySha256, storyAttempted,
    storyConfirmed, rewriteCount, rewriteInstruction, setRewriteInstruction, events, busy, error, authError, bootstrapBusy,
    loadParentData, authenticate, signInWithGoogle, resetPassword, createProfileAndReturn, updateProfile,
    selectProfile, requestProfileDeletion, refreshPendingDeletion, continueWithProfile, openLessons, chooseLesson, acceptLessonInvitation,
    declineLessonInvitation, acceptGroupInvitation, createGuide, openDrawingGuide, openContextReview, confirmContext,
    continueToCapture, analyzeDrawingForCurrentRun, closeUnresolvedDrawingRun, confirmSubject,
    requestStory, confirmStory, drawingGuideIndex, setDrawingGuideIndex,
    resumeActiveRun, changePassword, resetCurrentPassword, signOut,
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

function parentSvgGuideFailureMessage(cause: unknown): string {
  const code = readErrorCode(cause);
  if (code === 'CURATED_SVG_GUIDE_NOT_FOUND') {
    return 'Chưa có hướng dẫn nét vẽ đã duyệt cho đối tượng này. Hãy tiếp tục để chụp tranh mà không cần gợi ý.';
  }
  if (code === 'CURATED_SVG_GUIDE_UNAVAILABLE') {
    return 'Kho hướng dẫn SVG đang tạm thời không sẵn sàng. Bạn vẫn có thể tiếp tục chụp tranh không cần gợi ý.';
  }
  if (isParentSessionExpired(cause)) return safeParentIdentityErrorMessage(cause);
  return `${safeParentFlowErrorMessage(cause)} Gợi ý nét vẽ không bắt buộc; bạn có thể tiếp tục mà không cần gợi ý.`;
}

function topicSuggestionErrorMessage(cause: unknown): string {
  const code = readErrorCode(cause);
  if (isParentSessionExpired(cause)) return safeParentIdentityErrorMessage(cause);
  if (code && ['ACCOUNT_ROLE_MISMATCH', 'ACTION_NOT_ALLOWED', 'PARENT_PROFILE_NOT_AUTHORIZED'].includes(code)) {
    return safeParentIdentityErrorMessage(cause);
  }
  if (code === 'PARENT_TOPIC_SUBJECT_AI_NOT_ENABLED') {
    return 'Chủ đề này chưa có gợi ý sẵn. Hãy chọn một chủ đề gần nhất trong ba thẻ hoặc sửa nội dung.';
  }
  if (code === 'PARENT_TOPIC_SUBJECT_AI_OUTCOME_UNKNOWN') {
    return 'Chưa xác nhận được kết quả cho chủ đề tự nhập. Hãy chọn một chủ đề có sẵn trước khi thử lại.';
  }
  if (code === 'PARENT_TOPIC_SUBJECT_AI_OUTPUT_INVALID') {
    return 'Gợi ý chưa vượt qua kiểm tra an toàn. Hãy chọn chủ đề gợi ý hoặc thử chủ đề khác.';
  }
  if (code === 'PARENT_TOPIC_TEXT_NOT_ALLOWED') {
    return 'Chỉ nhập tên chủ đề chung; không nhập tên hay thông tin riêng của trẻ.';
  }
  if (code === 'PARENT_TOPIC_ID_LABEL_MISMATCH') {
    return 'Chủ đề đã thay đổi. Hãy chọn lại thẻ chủ đề hoặc sửa ô nhập.';
  }
  if (code === 'PARENT_SUBJECT_SUGGESTION_INVALID') {
    return 'Ba gợi ý chưa khớp với chủ đề. Hãy chọn lại chủ đề hoặc thử đổi gợi ý.';
  }
  if (code === 'SUGGESTION_SET_UNAVAILABLE') {
    return 'Chưa tạo được bộ gợi ý mới. Hãy chọn một trong các thẻ đang hiển thị hoặc đổi chủ đề.';
  }
  return 'Chưa tải được gợi ý đối tượng cho chủ đề này. Hãy kiểm tra kết nối rồi thử lại.';
}

function createDraftUuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (character) => {
    const random = Math.floor(Math.random() * 16);
    return (character === 'x' ? random : (random & 0x3) | 0x8).toString(16);
  });
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
