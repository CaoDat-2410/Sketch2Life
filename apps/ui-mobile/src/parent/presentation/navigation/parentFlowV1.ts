import type {
  LessonDetail,
  ParentLessonVersionPinV1,
  ParentCandidate,
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

export type DrawingGuideParseResult =
  | { kind: 'steps'; steps: string[] }
  | { kind: 'empty'; reason: 'missing' | 'ambiguous' };

export function parseDrawingGuideSteps(value: string | null | undefined): DrawingGuideParseResult {
  const text = value?.trim() ?? '';
  if (!text) return { kind: 'empty', reason: 'missing' };

  const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const numbered = lines.map((line) => {
    const match = line.match(/^(?:(?:step|bước)\s*)?(\d+)\s*[.)、:：-]\s*(.+)$/i);
    return match ? { number: Number(match[1]), text: match[2].trim() } : null;
  });
  if (numbered.every((item): item is { number: number; text: string } => item !== null)) {
    const isSequential = numbered.every((item, index) => item.number === index + 1 && Boolean(item.text));
    return isSequential
      ? { kind: 'steps', steps: numbered.map((item) => item.text) }
      : { kind: 'empty', reason: 'ambiguous' };
  }

  const bullets = lines.map((line) => line.match(/^[-*•]\s+(.+)$/));
  if (bullets.every((match) => match !== null)) {
    const steps = bullets.map((match) => match?.[1].trim() ?? '');
    return steps.every(Boolean)
      ? { kind: 'steps', steps }
      : { kind: 'empty', reason: 'ambiguous' };
  }

  return { kind: 'empty', reason: 'ambiguous' };
}

export function clampDrawingGuideIndex(index: number, stepCount: number): number {
  if (!Number.isFinite(index) || stepCount <= 0) return 0;
  return Math.min(Math.max(Math.trunc(index), 0), stepCount - 1);
}

export function moveDrawingGuideIndex(index: number, stepCount: number, direction: -1 | 1): number {
  return clampDrawingGuideIndex(index + direction, stepCount);
}

export function canContinueToCapture(contextConfirmed: boolean): boolean {
  return contextConfirmed;
}

export function canAnalyzeDrawing(input: {
  runId: string | null | undefined;
  contextConfirmed: boolean;
  photoSelected: boolean;
}): boolean {
  return Boolean(input.runId?.trim() && input.contextConfirmed && input.photoSelected);
}

export function canConfirmDrawingSubject(input: {
  runId: string | null | undefined;
  candidatePresent: boolean;
  understandingRevision: number | null | undefined;
  subject: string;
  explicitAdultAction: boolean;
}): boolean {
  return Boolean(
    input.runId?.trim()
    && input.candidatePresent
    && Number.isInteger(input.understandingRevision)
    && (input.understandingRevision ?? 0) >= 1
    && input.subject.trim()
    && input.explicitAdultAction,
  );
}

export function readDrawingCandidate(value: unknown): ParentCandidate | null {
  if (!isRecord(value) || !Array.isArray(value.visible_features)) return null;
  if (!value.visible_features.every((feature) => typeof feature === 'string')) return null;
  if (typeof value.confidence !== 'number' || !Number.isFinite(value.confidence)
    || value.confidence < 0 || value.confidence > 1) return null;
  if (value.adult_confirmation_required !== true || typeof value.decision !== 'string') return null;
  if (value.candidate_subject !== undefined && value.candidate_subject !== null
    && typeof value.candidate_subject !== 'string') return null;

  return {
    candidate_subject: typeof value.candidate_subject === 'string' ? value.candidate_subject : null,
    visible_features: [...value.visible_features],
    confidence: value.confidence,
    adult_confirmation_required: true,
    decision: value.decision,
  };
}

export type ValidatedStoryRevisionReadModel = {
  runId: string;
  storyRevisionNo: number;
  storySha256: string;
  storyStatus: string | null;
  story: unknown;
};

export type StoryRevisionReadModelResult =
  | { kind: 'valid'; value: ValidatedStoryRevisionReadModel }
  | {
      kind: 'invalid';
      reason:
        | 'STORY_RUN_MISSING'
        | 'RUN_ID_MISMATCH'
        | 'STORY_REVISION_NO_MISSING'
        | 'STORY_REVISION_NO_INVALID'
        | 'STORY_SHA256_MISSING'
        | 'STORY_SHA256_INVALID';
    };

/** Read nested revision pins validated at runtime; shared ParentStoryRunV1 stays frozen. */
export function readStoryRevisionReadModel(
  value: unknown,
  expectedRunId: string,
): StoryRevisionReadModelResult {
  if (!isRecord(value) || !isRecord(value.story_run)) {
    return { kind: 'invalid', reason: 'STORY_RUN_MISSING' };
  }

  const storyRun = value.story_run;
  if (typeof storyRun.run_id !== 'string' || storyRun.run_id !== expectedRunId) {
    return { kind: 'invalid', reason: 'RUN_ID_MISMATCH' };
  }
  if (storyRun.story_revision_no === undefined || storyRun.story_revision_no === null) {
    return { kind: 'invalid', reason: 'STORY_REVISION_NO_MISSING' };
  }
  if (!Number.isInteger(storyRun.story_revision_no) || Number(storyRun.story_revision_no) < 1) {
    return { kind: 'invalid', reason: 'STORY_REVISION_NO_INVALID' };
  }
  if (storyRun.story_sha256 === undefined || storyRun.story_sha256 === null || storyRun.story_sha256 === '') {
    return { kind: 'invalid', reason: 'STORY_SHA256_MISSING' };
  }
  if (typeof storyRun.story_sha256 !== 'string' || !/^[0-9a-f]{64}$/.test(storyRun.story_sha256)) {
    return { kind: 'invalid', reason: 'STORY_SHA256_INVALID' };
  }

  return {
    kind: 'valid',
    value: {
      runId: storyRun.run_id,
      storyRevisionNo: storyRun.story_revision_no as number,
      storySha256: storyRun.story_sha256,
      storyStatus: typeof storyRun.story_status === 'string' ? storyRun.story_status : null,
      story: storyRun.story,
    },
  };
}

export function canRequestStoryRevision(input: {
  runId: string | null | undefined;
  understandingRevision: number | null | undefined;
  storyPresent: boolean;
  storyAttempted: boolean;
  rewriteCount: number;
  rewriteInstruction: string;
  storyConfirmed: boolean;
  subjectConfirmed: boolean;
  allowSameActionRetry: boolean;
}): boolean {
  if (!input.runId?.trim() || !Number.isInteger(input.understandingRevision)
    || (input.understandingRevision ?? 0) < 1 || input.storyConfirmed || !input.subjectConfirmed) return false;

  const isRewrite = Boolean(input.rewriteInstruction.trim());
  if (!isRewrite) return !input.storyPresent && (!input.storyAttempted || input.allowSameActionRetry);
  return input.storyPresent && (input.rewriteCount < 3 || input.allowSameActionRetry);
}

export function canConfirmDisplayedStory(input: {
  runId: string | null | undefined;
  displayedRunId: string | null | undefined;
  storyPresent: boolean;
  subjectConfirmed: boolean;
  storyConfirmed: boolean;
  storyRevisionNo: number | null | undefined;
  storySha256: string | null | undefined;
}): boolean {
  return Boolean(
    input.runId?.trim()
    && input.displayedRunId === input.runId
    && input.storyPresent
    && input.subjectConfirmed
    && !input.storyConfirmed
    && Number.isInteger(input.storyRevisionNo)
    && (input.storyRevisionNo ?? 0) >= 1
    && typeof input.storySha256 === 'string'
    && /^[0-9a-f]{64}$/.test(input.storySha256),
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
    PARENT_CONTEXT_NOT_CONFIRMED: 'Người lớn cần xác nhận ngữ cảnh trước khi tiếp tục.',
    PARENT_DRAWING_REQUIRED: 'Hãy chọn ảnh tranh trước khi tiếp tục xem xét.',
    PARENT_DRAWING_RESULT_INVALID: 'Chưa thể đọc kết quả xem xét tranh. Hãy kiểm tra trạng thái trước khi gửi lại.',
    PARENT_SUBJECT_CONFIRMATION_INVALID: 'Chưa thể xác nhận chủ thể của bức tranh.',
    PARENT_STORY_REVISION_INVALID: 'Chưa thể xác nhận đúng phiên bản kịch bản. Hãy kiểm tra lại buổi học.',
    PARENT_STORY_NOT_CONFIRMABLE: 'Kịch bản chưa có đủ thông tin để xác nhận.',
    PARENT_STORY_REWRITE_LIMIT: 'Đã dùng hết 3 lượt gợi ý viết lại.',
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
