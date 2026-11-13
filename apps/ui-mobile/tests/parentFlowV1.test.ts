import { describe, expect, it } from 'vitest';
import type {
  LessonDetail,
  ParentProfileDeletePendingV1,
  ParentProfilePageV1,
  ParentProfileViewV1,
} from '../src/parent/domain/types';
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
