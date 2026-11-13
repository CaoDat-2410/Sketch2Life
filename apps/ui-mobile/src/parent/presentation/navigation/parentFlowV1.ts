import type {
  LessonDetail,
  ParentLessonVersionPinV1,
  ParentProfileDeletePendingV1,
  ParentProfilePageV1,
  ParentProfileRecordV1,
  ParentProfileViewV1,
} from '../../domain/types';

export type ProfileFieldKey = 'display_name' | 'age_months' | 'interests_summary';
export type ProfileFieldMessages = Partial<Record<ProfileFieldKey, string>>;

export function mergeProfilePage(
  current: readonly ParentProfileViewV1[],
  page: ParentProfilePageV1,
): ParentProfileViewV1[] {
  const profilesById = new Map(current.map((profile) => [profile.profile_id, profile]));
  for (const profile of page.items) profilesById.set(profile.profile_id, profile);
  return [...profilesById.values()];
}

export function nextProfileCursor(page: ParentProfilePageV1): string | null {
  return page.next_cursor;
}

export function selectProfileById(
  profiles: readonly ParentProfileViewV1[],
  selectedProfileId: string | null | undefined,
): ParentProfileViewV1 | null {
  if (!selectedProfileId) return null;
  return profiles.find((profile) => profile.profile_id === selectedProfileId) ?? null;
}

export function isProfileDeletionPending(
  profileId: string,
  pendingDeletions: readonly ParentProfileDeletePendingV1[],
): boolean {
  return pendingDeletions.some((pending) => pending.profile_id === profileId);
}

export function reconcileProfileRecord(
  profiles: readonly ParentProfileViewV1[],
  pendingDeletions: readonly ParentProfileDeletePendingV1[],
  record: ParentProfileRecordV1,
): { profiles: ParentProfileViewV1[]; pendingDeletions: ParentProfileDeletePendingV1[] } {
  if (record.state === 'DELETE_PENDING') {
    return {
      profiles: profiles.filter((profile) => profile.profile_id !== record.profile_id),
      pendingDeletions: [
        ...pendingDeletions.filter((pending) => pending.profile_id !== record.profile_id),
        record,
      ],
    };
  }

  return {
    profiles: [...profiles.filter((profile) => profile.profile_id !== record.profile_id), record],
    pendingDeletions: pendingDeletions.filter((pending) => pending.profile_id !== record.profile_id),
  };
}

export function lessonVersionPinFromDetail(lesson: LessonDetail | null): ParentLessonVersionPinV1 | null {
  if (!lesson) return null;
  const pin = {
    lesson_id: lesson.lesson_id.trim(),
    version_id: lesson.version_id.trim(),
    content_sha256: lesson.content_sha256.trim(),
  };
  return pin.lesson_id && pin.version_id && pin.content_sha256 ? pin : null;
}

export function canBeginContextStep(input: {
  profileId: string;
  topic: string;
  adultIdea: string;
  lessonPin: ParentLessonVersionPinV1 | null;
}): boolean {
  return Boolean(
    input.profileId.trim()
    && input.topic.trim()
    && input.adultIdea.trim()
    && input.lessonPin?.lesson_id.trim()
    && input.lessonPin.version_id.trim()
    && input.lessonPin.content_sha256.trim(),
  );
}

export function safeParentFlowErrorMessage(error: unknown): string {
  const code = readErrorCode(error);
  const messages: Record<string, string> = {
    ACTION_NOT_ALLOWED: 'Tài khoản hiện không thể thực hiện thao tác này.',
    PARENT_STORE_UNAVAILABLE: 'Hồ sơ đang tạm thời không khả dụng. Vui lòng thử lại sau.',
    STALE_REVISION: 'Hồ sơ đã thay đổi. Hãy kiểm tra thông tin mới nhất rồi lưu lại.',
    INVALID_STATE_TRANSITION: 'Hồ sơ đã thay đổi trạng thái. Hãy kiểm tra lại trước khi tiếp tục.',
    ACTIVE_RUN_EXISTS: 'Hồ sơ đang có một buổi học chưa hoàn tất.',
    PARENT_LESSON_PIN_REQUIRED: 'Hãy chọn một bài học trước khi bắt đầu.',
    PARENT_CONTEXT_REQUIRED: 'Hãy chọn hồ sơ và nhập chủ đề cùng gợi ý trước khi tiếp tục.',
    PARENT_CONTEXT_SNAPSHOT_INVALID: 'Chưa thể xác nhận ngữ cảnh của buổi học này.',
    INVALID_LIMIT: 'Chưa tải được danh sách hồ sơ. Vui lòng thử lại.',
  };
  return (code && messages[code]) || 'Chưa thể hoàn tất thao tác. Vui lòng thử lại sau.';
}

export function safeProfileFieldMessages(error: unknown): ProfileFieldMessages {
  const fieldErrors = readFieldErrors(error);
  const messages: ProfileFieldMessages = {};
  for (const fieldError of fieldErrors) {
    const field = fieldError.field as ProfileFieldKey;
    if (!['display_name', 'age_months', 'interests_summary'].includes(field)) continue;
    messages[field] = fieldErrorMessage(field, fieldError.code);
  }
  return messages;
}

function readErrorCode(value: unknown): string | null {
  if (!isRecord(value) || typeof value.code !== 'string') return null;
  return /^[A-Z0-9_]{1,80}$/.test(value.code) ? value.code : null;
}

function readFieldErrors(value: unknown): Array<{ field: string; code: string }> {
  if (!isRecord(value) || !Array.isArray(value.fieldErrors)) return [];
  return value.fieldErrors.flatMap((item) => {
    if (!isRecord(item) || typeof item.field !== 'string' || typeof item.code !== 'string') return [];
    return [{ field: item.field.toLowerCase(), code: item.code.toUpperCase() }];
  });
}

function fieldErrorMessage(field: ProfileFieldKey, code: string): string {
  if (field === 'display_name') {
    if (code === 'REQUIRED' || code === 'EMPTY') return 'Hãy nhập tên gọi cho hồ sơ.';
    if (code === 'TOO_LONG') return 'Tên gọi dài quá. Hãy rút gọn rồi thử lại.';
    return 'Hãy kiểm tra lại tên gọi.';
  }
  if (field === 'age_months') {
    if (code === 'OUT_OF_RANGE') return 'Tuổi cần trong khoảng từ 36 đến 120 tháng.';
    return 'Hãy nhập tuổi hợp lệ theo tháng.';
  }
  if (code === 'TOO_LONG') return 'Sở thích dài quá. Hãy rút gọn rồi thử lại.';
  if (code === 'INVALID_TYPE') return 'Hãy kiểm tra lại phần sở thích.';
  return 'Hãy kiểm tra lại phần sở thích.';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
