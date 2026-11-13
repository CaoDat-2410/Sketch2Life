import { describe, expect, it } from 'vitest';
import type {
  LessonDetail,
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
  isProfileDeletionPending,
  lessonVersionPinFromDetail,
  mergeProfilePage,
  moveDrawingGuideIndex,
  nextProfileCursor,
  parseDrawingGuideSteps,
  readDrawingCandidate,
  readStoryRevisionReadModel,
  reconcileProfileRecord,
  safeParentFlowErrorMessage,
  safeProfileFieldMessages,
  selectProfileById,
} from '../src/parent/presentation/navigation/parentFlowV1';

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

  it('requires a complete lesson pin for context entry and does not require a photo', () => {
    const complete = { lesson_id: 'lesson-1', version_id: 'version-2', content_sha256: 'lesson-hash' };
    expect(canBeginContextStep({
      profileId: firstProfile.profile_id, topic: 'mây', adultIdea: 'diều', lessonPin: complete,
    })).toBe(true);
    expect(canBeginContextStep({
      profileId: firstProfile.profile_id, topic: 'mây', adultIdea: 'diều', lessonPin: null,
    })).toBe(false);
    expect(canBeginContextStep({
      profileId: firstProfile.profile_id, topic: 'mây', adultIdea: 'diều',
      lessonPin: { ...complete, content_sha256: ' ' },
    })).toBe(false);
  });

  it('parses only explicitly numbered or bulleted guide steps and preserves their wording', () => {
    expect(parseDrawingGuideSteps('Bước 1: Vẽ vòng tròn nhỏ.\nBước 2: Thêm hai cánh bên cạnh.')).toEqual({
      kind: 'steps', steps: ['Vẽ vòng tròn nhỏ.', 'Thêm hai cánh bên cạnh.'],
    });
    expect(parseDrawingGuideSteps('- Chọn màu xanh.\n• Tô phần cánh.')).toEqual({
      kind: 'steps', steps: ['Chọn màu xanh.', 'Tô phần cánh.'],
    });
    expect(parseDrawingGuideSteps('')).toEqual({ kind: 'empty', reason: 'missing' });
    expect(parseDrawingGuideSteps('Vẽ thân trước rồi thêm cánh.')).toEqual({ kind: 'empty', reason: 'ambiguous' });
    expect(parseDrawingGuideSteps('1. Vẽ thân.\n3. Thêm cánh.')).toEqual({ kind: 'empty', reason: 'ambiguous' });
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

  it('keeps capture and drawing analysis behind explicit context confirmation and a selected photo', () => {
    expect(canContinueToCapture(false)).toBe(false);
    expect(canContinueToCapture(true)).toBe(true);
    expect(canAnalyzeDrawing({ runId: 'synthetic-run', contextConfirmed: false, photoSelected: true })).toBe(false);
    expect(canAnalyzeDrawing({ runId: 'synthetic-run', contextConfirmed: true, photoSelected: false })).toBe(false);
    expect(canAnalyzeDrawing({ runId: 'synthetic-run', contextConfirmed: true, photoSelected: true })).toBe(true);
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
    const response = { story_run: {
      run_id: 'synthetic-run', story_revision_no: 2, story_sha256: storySha256,
      story_status: 'DRAFT', story: { opening: 'synthetic story' },
    } };
    expect(readStoryRevisionReadModel(response, 'synthetic-run')).toEqual({
      kind: 'valid',
      value: {
        runId: 'synthetic-run', storyRevisionNo: 2, storySha256,
        storyStatus: 'DRAFT', story: { opening: 'synthetic story' },
      },
    });
    expect(readStoryRevisionReadModel({ story_run: { run_id: 'synthetic-run', story_sha256: storySha256 } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_REVISION_NO_MISSING' });
    expect(readStoryRevisionReadModel({ story_run: { ...response.story_run, story_revision_no: 0 } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_REVISION_NO_INVALID' });
    expect(readStoryRevisionReadModel({ story_run: { ...response.story_run, story_revision_no: 1.5 } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_REVISION_NO_INVALID' });
    expect(readStoryRevisionReadModel({ story_run: { run_id: 'synthetic-run', story_revision_no: 2 } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_SHA256_MISSING' });
    expect(readStoryRevisionReadModel({ story_run: { ...response.story_run, story_sha256: 'ABC' } }, 'synthetic-run'))
      .toMatchObject({ kind: 'invalid', reason: 'STORY_SHA256_INVALID' });
    expect(readStoryRevisionReadModel({ story_run: { ...response.story_run, story_revision_no: 2 } }, 'synthetic-run'))
      .toMatchObject({ kind: 'valid' });
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
