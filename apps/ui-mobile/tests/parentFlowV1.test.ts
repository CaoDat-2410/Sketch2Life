import { describe, expect, it } from 'vitest';
import type {
  LessonDetail,
  LessonSummary,
  ParentProfileDeletePendingV1,
  ParentProfilePageV1,
  ParentProfileViewV1,
} from '../src/parent/domain/types';
import {
  canAnalyzeDrawing,
  canBeginContextStep,
  canConfirmDisplayedStory,
  canConfirmDrawingSubject,
  canContinueToCapture,
  canRequestStoryRevision,
  clampDrawingGuideIndex,
  isActiveOrUnreconciledStoryRun,
  isConfirmedRunSubject,
  isWithinOfflineAudioLimit,
  isWithinOfflinePhotoLimit,
  isProfileDeletionPending,
  lessonVersionPinFromDetail,
  mergeProfilePage,
  moveDrawingGuideIndex,
  nextProfileCursor,
  parseDrawingGuideSteps,
  parentRecoveryGroupForError,
  readDrawingCandidate,
  readRunPinnedLessonActivities,
  readStoryRevisionReadModel,
  reconcileProfileRecord,
  safeParentFlowErrorMessage,
  safeProfileFieldMessages,
  selectProfileById,
} from '../src/parent/presentation/navigation/parentFlowV1';
import {
  canStartProfileLearning,
  isCurrentAuthorizedLesson,
  parentProfileAgeEligibility,
  parentStoryRunCreationGate,
  parentShareGrantExpiryState,
  parentShareGrantStateLabel,
  toParentProfileMutationInput,
} from '../src/parent/presentation/navigation/workflowTypes';

const firstProfile: ParentProfileViewV1 = {
  profile_id: 'synthetic-profile-1', revision_no: 1, revision_hash: 'revision-hash-1',
  state: 'ACTIVE', display_name: 'Bé Mây', age_months: 72, age_band_ref: 'age-6',
  age_band_version: 'age-6-v1', interests_summary: null, data_origin: 'PARENT_CREATED',
};
const secondProfile: ParentProfileViewV1 = {
  ...firstProfile, profile_id: 'synthetic-profile-2', revision_no: 2,
  revision_hash: 'revision-hash-2', display_name: 'Bé Sóc',
};

describe('parentFlowV1 pure flow decisions', () => {
  it('uses the age range and requires paired age-band fields when present', () => {
    expect(parentProfileAgeEligibility(firstProfile)).toBe('supported');
    expect(parentProfileAgeEligibility({
      ...firstProfile, age_months: 72, age_band_ref: null, age_band_version: null,
    })).toBe('supported');
    expect(parentProfileAgeEligibility({
      ...firstProfile, age_months: 36, age_band_ref: null, age_band_version: null,
    })).toBe('supported');
    expect(parentProfileAgeEligibility({
      ...firstProfile, age_months: 120, age_band_ref: null, age_band_version: null,
    })).toBe('supported');
    expect(parentProfileAgeEligibility({
      ...firstProfile, age_months: 121, age_band_ref: null, age_band_version: null,
    })).toBe('legacy-read-only');
    expect(parentProfileAgeEligibility({
      ...firstProfile, age_months: 155, age_band_ref: null, age_band_version: null,
    })).toBe('legacy-read-only');
    expect(parentProfileAgeEligibility({
      ...firstProfile, age_months: 35, age_band_ref: null, age_band_version: null,
    })).toBe('unavailable');
    expect(parentProfileAgeEligibility({
      ...firstProfile, age_months: 156, age_band_ref: null, age_band_version: null,
    })).toBe('unavailable');
    expect(parentProfileAgeEligibility({
      age_months: 72, age_band_ref: 'synthetic-age-6', age_band_version: null,
    })).toBe('unavailable');
    expect(parentProfileAgeEligibility({
      age_months: 72, age_band_ref: null, age_band_version: 'synthetic-age-6-v1',
    })).toBe('unavailable');
  });

  it('keeps unavailable consent informational while server revocation blocks profile learning', () => {
    expect(canStartProfileLearning('supported', {
      state: 'confirmed', source: 'server', policyRevision: 'synthetic-policy-rev-1',
    })).toBe(true);
    expect(canStartProfileLearning('legacy-read-only', {
      state: 'confirmed', source: 'server', policyRevision: 'synthetic-policy-rev-1',
    })).toBe(false);
    for (const status of [
      { state: 'unknown' as const },
      { state: 'pending' as const },
      { state: 'unavailable' as const, reason: 'route-not-in-be-handoff' as const },
    ]) {
      expect(canStartProfileLearning('supported', status)).toBe(true);
    }
    expect(canStartProfileLearning('supported', { state: 'revoked' })).toBe(false);
    expect(canStartProfileLearning('supported', {
      state: 'confirmed', source: 'server', policyRevision: ' ',
    })).toBe(false);
  });

  it('keeps child gender optional and strips it from every profile mutation draft', () => {
    const values = ['', 'boy', 'girl', 'prefer_not_to_say'] as const;
    for (const childGender of values) {
      const payload = toParentProfileMutationInput({
        displayName: 'Synthetic child', ageMonths: 72, interests: 'synthetic interest', childGender,
      });
      expect(payload).toEqual({
        displayName: 'Synthetic child', ageMonths: 72, interests: 'synthetic interest',
      });
      expect(payload).not.toHaveProperty('childGender');
      expect(payload).not.toHaveProperty('child_gender');
    }
  });

  it('labels all server share states and only treats an unexpired active grant as active', () => {
    const states = ['INVITED', 'ACTIVE', 'DECLINED', 'REVOKED', 'EXPIRED'] as const;
    for (const state of states) expect(parentShareGrantStateLabel(state).length).toBeGreaterThan(0);
    const now = Date.parse('2026-11-13T00:00:00.000Z');
    expect(parentShareGrantExpiryState('ACTIVE', '2027-02-11T00:00:00.000Z', now)).toBe('active');
    expect(parentShareGrantExpiryState('ACTIVE', '2026-11-12T23:59:59.000Z', now)).toBe('expired');
    expect(parentShareGrantExpiryState('INVITED', '2027-02-11T00:00:00.000Z', now)).toBe('not-active');
    expect(parentShareGrantExpiryState('REVOKED', '2027-02-11T00:00:00.000Z', now)).toBe('not-active');
  });

  it('merges profile pages by id and preserves opaque cursor values', () => {
    const page: ParentProfilePageV1 = {
      request_id: 'synthetic-request',
      items: [{ ...firstProfile, revision_no: 2, revision_hash: 'revision-hash-1b' }, secondProfile],
      next_cursor: 'opaque +/?= cursor',
    };

    expect(mergeProfilePage([firstProfile], page)).toEqual([
      { ...firstProfile, revision_no: 2, revision_hash: 'revision-hash-1b' },
      secondProfile,
    ]);
    expect(nextProfileCursor(page)).toBe('opaque +/?= cursor');
    expect(nextProfileCursor({ ...page, next_cursor: null })).toBeNull();
  });

  it('selects a profile only by an explicit selected id', () => {
    expect(selectProfileById([firstProfile, secondProfile], 'synthetic-profile-2')).toBe(secondProfile);
    expect(selectProfileById([firstProfile, secondProfile], '')).toBeNull();
    expect(selectProfileById([firstProfile, secondProfile], 'missing-profile')).toBeNull();
  });

  it('keeps deletion pending visible and reconciles only from a profile record', () => {
    const pending: ParentProfileDeletePendingV1 = {
      profile_id: firstProfile.profile_id, state: 'DELETE_PENDING', request_id: 'synthetic-delete-request',
    };
    const requested = reconcileProfileRecord([firstProfile, secondProfile], [], pending);
    expect(requested.profiles).toEqual([secondProfile]);
    expect(requested.pendingDeletions).toEqual([pending]);
    expect(isProfileDeletionPending(firstProfile.profile_id, requested.pendingDeletions)).toBe(true);

    const restored = reconcileProfileRecord(requested.profiles, requested.pendingDeletions, firstProfile);
    expect(restored.profiles).toEqual([secondProfile, firstProfile]);
    expect(restored.pendingDeletions).toEqual([]);
    expect(isProfileDeletionPending(firstProfile.profile_id, restored.pendingDeletions)).toBe(false);
  });

  it('allows an optional topic but requires an exact pinned lesson before starting a run', () => {
    const complete = { lesson_id: 'lesson-1', version_id: 'version-2', content_sha256: 'a'.repeat(64) };
    expect(canBeginContextStep({ profileId: firstProfile.profile_id, topic: '', adultIdea: '', lessonPin: complete })).toBe(true);
    expect(canBeginContextStep({ profileId: firstProfile.profile_id, topic: '', adultIdea: '', lessonPin: null })).toBe(false);
    expect(canBeginContextStep({
      profileId: firstProfile.profile_id, topic: '', adultIdea: '', lessonPin: { ...complete, content_sha256: 'short' },
    })).toBe(false);
    expect(canBeginContextStep({ profileId: '', topic: '', adultIdea: '', lessonPin: null })).toBe(false);
  });

  it('requires a confirmed active-run check, no active run, a photo, and an available API before creating a run', () => {
    expect(parentStoryRunCreationGate({
      activeRunCheck: 'checking', activeRun: false, photoSelected: true, apiAvailable: true,
    })).toBe('active-run-check-required');
    expect(parentStoryRunCreationGate({
      activeRunCheck: 'confirmed', activeRun: true, photoSelected: true, apiAvailable: true,
    })).toBe('active-run-exists');
    expect(parentStoryRunCreationGate({
      activeRunCheck: 'confirmed', activeRun: false, photoSelected: false, apiAvailable: true,
    })).toBe('photo-required');
    expect(parentStoryRunCreationGate({
      activeRunCheck: 'confirmed', activeRun: false, photoSelected: true, apiAvailable: false,
    })).toBe('api-unavailable');
    expect(parentStoryRunCreationGate({
      activeRunCheck: 'confirmed', activeRun: false, photoSelected: true, apiAvailable: true,
    })).toBe('ready');
  });

  it('accepts only a current, authorized lesson detail matching the listed version and content hash', () => {
    const summary: LessonSummary = {
      lesson_id: 'synthetic-lesson', version_id: 'synthetic-version-2', title: 'Synthetic lesson',
      topic: 'Synthetic topic', target_age_band_ref: 'synthetic-age-band', target_age_band_version: 2,
      activity_count: 1, access_source: 'SHARED',
    };
    const detail: LessonDetail = {
      ...summary, contract: 'ParentLessonDetailV1', version_no: 2, content_sha256: 'a'.repeat(64),
      objectives: [], drawing_subject: 'Synthetic subject', drawing_steps_text: 'Synthetic steps',
      subject_learning_notes: 'Synthetic notes', script_direction: null, script_following_allowed: false,
      access_expires_at: '2026-11-14T00:00:00.000Z', activities: [{
        title: 'Synthetic activity', objective: 'Synthetic objective', materials_text: '',
        preparation_text: '', instructions_text: '', observation_notes: '', safety_notes: '', activity_kind: 'indoor',
      }],
    };
    const now = Date.parse('2026-11-13T00:00:00.000Z');
    expect(isCurrentAuthorizedLesson(summary, detail, now)).toBe(true);
    expect(isCurrentAuthorizedLesson(summary, { ...detail, version_id: 'stale-version' }, now)).toBe(false);
    expect(isCurrentAuthorizedLesson(summary, { ...detail, content_sha256: 'short' }, now)).toBe(false);
    expect(isCurrentAuthorizedLesson(summary, { ...detail, access_expires_at: '2026-11-12T00:00:00.000Z' }, now)).toBe(false);
  });

  it('accepts only explicitly ordered guides with four to eight steps', () => {
    const fourSteps = '1. Draw a circle.\n2. Add two wings.\n3. Add small dots.\n4. Color the wings.';
    const eightSteps = '- one\n- two\n- three\n- four\n- five\n- six\n- seven\n- eight';
    expect(parseDrawingGuideSteps(fourSteps)).toEqual({
      kind: 'steps', steps: ['Draw a circle.', 'Add two wings.', 'Add small dots.', 'Color the wings.'],
    });
    expect(parseDrawingGuideSteps(eightSteps)).toEqual({
      kind: 'steps', steps: ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight'],
    });
    expect(parseDrawingGuideSteps('1. one\n2. two\n3. three')).toEqual({ kind: 'empty', reason: 'ambiguous' });
    expect(parseDrawingGuideSteps('1. one\n2. two\n3. three\n4. four\n5. five\n6. six\n7. seven\n8. eight\n9. nine'))
      .toEqual({ kind: 'empty', reason: 'ambiguous' });
    expect(parseDrawingGuideSteps('')).toEqual({ kind: 'empty', reason: 'missing' });
    expect(parseDrawingGuideSteps('Draw a body, then add wings.')).toEqual({ kind: 'empty', reason: 'ambiguous' });
    expect(parseDrawingGuideSteps('1. Draw body.\n3. Add wings.')).toEqual({ kind: 'empty', reason: 'ambiguous' });
  });

  it('clamps guide navigation at both ends and does not mutate the lesson pin or run', () => {
    const lessonPin = Object.freeze({ lesson_id: 'lesson-1', version_id: 'version-2', content_sha256: 'lesson-hash' });
    const run = Object.freeze({ run_id: 'synthetic-run', run_state: 'CONTEXT_PENDING' });
    expect(clampDrawingGuideIndex(-5, 3)).toBe(0);
    expect(clampDrawingGuideIndex(8, 3)).toBe(2);
    expect(moveDrawingGuideIndex(0, 3, -1)).toBe(0);
    expect(moveDrawingGuideIndex(1, 3, 1)).toBe(2);
    expect(moveDrawingGuideIndex(2, 3, 1)).toBe(2);
    expect(clampDrawingGuideIndex(2, 0)).toBe(0);
    expect(lessonPin).toEqual({ lesson_id: 'lesson-1', version_id: 'version-2', content_sha256: 'lesson-hash' });
    expect(run).toEqual({ run_id: 'synthetic-run', run_state: 'CONTEXT_PENDING' });
  });

  it('allows photo-first capture and analysis before the later context confirmation', () => {
    expect(canContinueToCapture(false)).toBe(false);
    expect(canContinueToCapture(true)).toBe(true);
    expect(canAnalyzeDrawing({ runId: null, contextConfirmed: false, photoSelected: true })).toBe(true);
    expect(canAnalyzeDrawing({ runId: 'synthetic-run', contextConfirmed: false, photoSelected: true })).toBe(true);
    expect(canAnalyzeDrawing({ runId: 'synthetic-run', contextConfirmed: true, photoSelected: false })).toBe(false);
    expect(canAnalyzeDrawing({ runId: 'synthetic-run', contextConfirmed: true, photoSelected: true })).toBe(true);
  });

  it('enforces the offline photo cap and exposes only validated exact run-pin activities', () => {
    expect(isWithinOfflinePhotoLimit(20 * 1024 * 1024)).toBe(true);
    expect(isWithinOfflinePhotoLimit(20 * 1024 * 1024 + 1)).toBe(false);
    expect(isWithinOfflinePhotoLimit(null)).toBe(false);
    expect(isWithinOfflineAudioLimit(120_000, 20 * 1024 * 1024)).toBe(true);
    expect(isWithinOfflineAudioLimit(120_001, 20 * 1024 * 1024)).toBe(false);
    expect(isWithinOfflineAudioLimit(120_000, 20 * 1024 * 1024 + 1)).toBe(false);
    const snapshot = {
      lesson_id: 'synthetic-lesson', version_id: 'synthetic-version', content_sha256: 'c'.repeat(64),
      title: 'Synthetic lesson', topic: 'Synthetic topic', drawing_subject: 'Synthetic subject',
      subject_learning_notes: 'Synthetic notes', script_direction: null, script_following_allowed: false,
      activities: [{
        title: 'Synthetic activity', objective: 'Synthetic objective', materials_text: '', preparation_text: '',
        instructions_text: 'Synthetic instructions', observation_notes: '', safety_notes: '', activity_kind: 'indoor' as const,
      }],
    };
    expect(readRunPinnedLessonActivities(snapshot)).toMatchObject([{
      source: 'PINNED_LESSON', source_lesson_id: 'synthetic-lesson',
      source_lesson_version_id: 'synthetic-version', source_content_sha256: 'c'.repeat(64), source_activity_index: 0,
    }]);
    expect(readRunPinnedLessonActivities({ ...snapshot, content_sha256: 'bad' })).toEqual([]);
    expect(isConfirmedRunSubject({
      subject_label: 'synthetic kite',
      candidate: { candidate_subject: 'synthetic kite', visible_features: [], confidence: 0.8, adult_confirmation_required: true, decision: 'CONFIRMED_BY_ADULT' },
    }, 'synthetic kite')).toBe(true);
    expect(isConfirmedRunSubject({
      subject_label: 'synthetic kite',
      candidate: { candidate_subject: 'synthetic kite', visible_features: [], confidence: 0.8, adult_confirmation_required: true, decision: 'REVIEW_REQUIRED' },
    }, 'synthetic kite')).toBe(false);
    expect(isActiveOrUnreconciledStoryRun({ story_status: 'GENERATING', job_state: 'RUNNING' })).toBe(true);
    expect(isActiveOrUnreconciledStoryRun({ story_status: 'DRAFT', job_state: 'SUCCEEDED' })).toBe(false);
  });

  it('requires a returned candidate, valid revision, subject and explicit adult action', () => {
    const input = {
      runId: 'synthetic-run', candidatePresent: true, understandingRevision: 2,
      subject: 'con bướm', explicitAdultAction: true,
    };
    expect(canConfirmDrawingSubject(input)).toBe(true);
    expect(canConfirmDrawingSubject({ ...input, candidatePresent: false })).toBe(false);
    expect(canConfirmDrawingSubject({ ...input, understandingRevision: 0 })).toBe(false);
    expect(canConfirmDrawingSubject({ ...input, explicitAdultAction: false })).toBe(false);
    expect(readDrawingCandidate({
      candidate_subject: 'con bướm', visible_features: ['hai cánh'], confidence: 0.9,
      adult_confirmation_required: true, decision: 'REVIEW_REQUIRED',
    })).toEqual({
      candidate_subject: 'con bướm', visible_features: ['hai cánh'], confidence: 0.9,
      adult_confirmation_required: true, decision: 'REVIEW_REQUIRED',
    });
    expect(readDrawingCandidate({
      candidate_subject: 'con bướm', visible_features: [3], confidence: 0.9,
      adult_confirmation_required: true, decision: 'REVIEW_REQUIRED',
    })).toBeNull();
    expect(readDrawingCandidate({
      candidate_subject: 'con bướm', visible_features: [], confidence: 0.9,
      adult_confirmation_required: false, decision: 'CONFIRMED',
    })).toBeNull();
  });

  it('validates the nested V1 story read model before exposing revision and hash pins', () => {
    const storySha256 = 'a'.repeat(64);
    const storyRevisionId = '00000000-0000-4000-8000-000000000001';
    const response = { story_run: {
      story_revision_id: storyRevisionId, run_id: 'synthetic-run', story_revision_no: 2,
      story_sha256: storySha256, story_status: 'DRAFT', story: { opening: 'synthetic story' },
    } };
    expect(readStoryRevisionReadModel(response, 'synthetic-run')).toEqual({
      kind: 'valid',
      value: {
        runId: 'synthetic-run', storyRevisionId, storyRevisionNo: 2, storySha256,
        storyStatus: 'DRAFT', story: { opening: 'synthetic story' },
      },
    });
    expect(readStoryRevisionReadModel({ story_run: { run_id: 'synthetic-run', story_sha256: storySha256 } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_REVISION_ID_MISSING' });
    expect(readStoryRevisionReadModel({ story_run: { ...response.story_run, story_revision_no: 0 } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_REVISION_NO_INVALID' });
    expect(readStoryRevisionReadModel({ story_run: { ...response.story_run, story_revision_no: 1.5 } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_REVISION_NO_INVALID' });
    expect(readStoryRevisionReadModel({ story_run: { ...response.story_run, story_sha256: 'ABC' } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_SHA256_INVALID' });
    expect(readStoryRevisionReadModel({ story_run: { ...response.story_run, story_revision_id: 'bad-id' } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_REVISION_ID_INVALID' });
    expect(readStoryRevisionReadModel(response, 'another-run')).toMatchObject({ kind: 'invalid', reason: 'RUN_ID_MISMATCH' });
  });

  it('allows at most three rewrites and blocks revision requests after confirmation', () => {
    const base = {
      runId: 'synthetic-run', understandingRevision: 1, storyPresent: true,
      storyAttempted: true, rewriteCount: 2, rewriteInstruction: 'thêm một đám mây', storyConfirmed: false,
      subjectConfirmed: true, allowSameActionRetry: false,
    };
    expect(canRequestStoryRevision(base)).toBe(true);
    expect(canRequestStoryRevision({ ...base, rewriteCount: 3 })).toBe(false);
    expect(canRequestStoryRevision({ ...base, rewriteCount: 3, allowSameActionRetry: true })).toBe(true);
    expect(canRequestStoryRevision({ ...base, storyConfirmed: true })).toBe(false);
    expect(canRequestStoryRevision({ ...base, rewriteInstruction: '' })).toBe(false);
    expect(canRequestStoryRevision({ ...base, subjectConfirmed: false })).toBe(false);
    expect(canRequestStoryRevision({
      ...base, storyPresent: false, rewriteInstruction: '', storyAttempted: true, allowSameActionRetry: true,
    })).toBe(true);
  });

  it('confirms only the displayed story with the exact validated run, revision and hash', () => {
    const valid = {
      runId: 'synthetic-run', displayedRunId: 'synthetic-run', storyPresent: true,
      subjectConfirmed: true, storyConfirmed: false,
      storyRevisionNo: 3, storySha256: 'b'.repeat(64),
    };
    expect(canConfirmDisplayedStory(valid)).toBe(true);
    expect(canConfirmDisplayedStory({ ...valid, displayedRunId: 'different-run' })).toBe(false);
    expect(canConfirmDisplayedStory({ ...valid, storyRevisionNo: null })).toBe(false);
    expect(canConfirmDisplayedStory({ ...valid, subjectConfirmed: false })).toBe(false);
    expect(canConfirmDisplayedStory({ ...valid, storyConfirmed: true })).toBe(false);
    expect(canConfirmDisplayedStory({ ...valid, storySha256: 'bad-hash' })).toBe(false);
  });

  it('maps a selected lesson to a complete version pin only', () => {
    const lesson: LessonDetail = {
      contract: 'ParentLessonDetailV1', lesson_id: 'lesson-1', version_id: 'version-2', title: 'Mây',
      topic: 'Thiên nhiên', target_age_band_ref: 'age-6', target_age_band_version: 1,
      activity_count: 0, access_source: 'PUBLIC', version_no: 2, content_sha256: 'lesson-hash',
      objectives: [], drawing_subject: 'Mây', drawing_steps_text: '', subject_learning_notes: '',
      script_direction: null, script_following_allowed: false, access_expires_at: null, activities: [],
    };
    expect(lessonVersionPinFromDetail(lesson)).toEqual({
      lesson_id: 'lesson-1', version_id: 'version-2', content_sha256: 'lesson-hash',
    });
    expect(lessonVersionPinFromDetail({ ...lesson, content_sha256: '' })).toBeNull();
  });

  it('maps role, storage, stale and deletion errors without exposing server text', () => {
    expect(safeParentFlowErrorMessage({ code: 'ACTION_NOT_ALLOWED', message: 'private server detail' }))
      .toBe('Tài khoản hiện không thể thực hiện thao tác này.');
    expect(safeParentFlowErrorMessage({ code: 'PARENT_STORE_UNAVAILABLE', message: 'private server detail' }))
      .toBe('Hồ sơ đang tạm thời không khả dụng. Vui lòng thử lại sau.');
    expect(safeParentFlowErrorMessage({ code: 'STALE_REVISION' }))
      .toBe('Hồ sơ đã thay đổi. Hãy kiểm tra thông tin mới nhất rồi lưu lại.');
    expect(safeParentFlowErrorMessage({ code: 'INVALID_STATE_TRANSITION' }))
      .toBe('Hồ sơ đã thay đổi trạng thái. Hãy kiểm tra lại trước khi tiếp tục.');
    expect(safeParentFlowErrorMessage({ code: 'UNKNOWN', message: 'private child detail' }))
      .not.toContain('private child detail');
  });

  it('maps recovery groups to safe Parent review or unavailable actions', () => {
    const recoveryCases = [
      ['AUTH_REQUIRED', 'authentication'],
      ['RESOURCE_NOT_FOUND', 'resource-refresh'],
      ['ACTION_NOT_ALLOWED', 'action-denied'],
      ['ACTIVE_RUN_EXISTS', 'resume-active-run'],
      ['MULTI_CHILD_NOT_SUPPORTED', 'teacher-only'],
      ['STALE_REVISION', 'review-current-state'],
      ['TRANSCRIPT_NOT_CONFIRMED', 'transcript-review'],
      ['SUBJECT_NOT_CONFIRMED', 'subject-review'],
      ['PROFILE_CONTEXT_NOT_CONFIRMED', 'context-review'],
      ['PARENT_STORY_REWRITE_LIMIT', 'story-review'],
      ['VIDEO_QUOTA_EXCEEDED', 'quota-summary'],
      ['MODAL_AI_NOT_ENABLED', 'provider-hold'],
      ['MODAL_OUTCOME_UNKNOWN', 'reconciliation'],
      ['RATE_LIMITED', 'wait-retry-after'],
      ['DELETE_PENDING', 'lifecycle-pending'],
      ['CAPABILITY_UNAVAILABLE', 'unavailable'],
      ['UNRECOGNIZED_SYNTHETIC_CODE', 'unknown'],
    ] as const;

    for (const [code, expectedGroup] of recoveryCases) {
      expect(parentRecoveryGroupForError({ code })).toBe(expectedGroup);
    }
    for (const code of [
      'OCR_NOT_SUPPORTED', 'UNSUPPORTED_LESSON_TYPE', 'LESSON_FILE_TOO_LARGE',
      'LESSON_PLAN_NOT_APPROVED', 'SUBSCRIPTION_RESTRICTED', 'CLASS_CAPACITY_REACHED',
    ]) {
      expect(parentRecoveryGroupForError({ code })).toBe('teacher-only');
    }
  });

  it('maps only safe profile field errors to localized field messages', () => {
    expect(safeProfileFieldMessages({ fieldErrors: [
      { field: 'display_name', code: 'TOO_LONG' },
      { field: 'age_months', code: 'OUT_OF_RANGE' },
      { field: 'private_child_field', code: 'REQUIRED' },
    ] })).toEqual({
      display_name: 'Tên gọi dài quá. Hãy rút gọn rồi thử lại.',
      age_months: 'Tuổi cần trong khoảng từ 36 đến 120 tháng.',
    });
  });
});
