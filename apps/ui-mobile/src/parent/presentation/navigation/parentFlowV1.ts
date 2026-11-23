import { ParentApplicationError } from '../../application/ParentApplicationError';
import type {
  Activity,
  LessonDetail,
  ParentLessonVersionPinV1,
  ParentDrawingCandidateV1,
  ParentProfileDeletePendingV1,
  ParentProfilePageV1,
  ParentProfileRecordV1,
  ParentStoryRunV1,
  ParentProfileViewV1,
  SuggestedActivity,
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

export function readPinnedLessonActivities(
  lesson: LessonDetail | null,
  runPin: ParentLessonVersionPinV1 | null | undefined,
): SuggestedActivity[] {
  const detailPin = lessonVersionPinFromDetail(lesson);
  if (!lesson || !detailPin || !runPin
    || detailPin.lesson_id !== runPin.lesson_id
    || detailPin.version_id !== runPin.version_id
    || detailPin.content_sha256 !== runPin.content_sha256) {
    return [];
  }
  return lesson.activities.map((activity, index) => ({
    ...activity,
    source: 'PINNED_LESSON',
    source_lesson_id: lesson.lesson_id,
    source_lesson_title: lesson.title,
    source_lesson_version_id: lesson.version_id,
    source_content_sha256: lesson.content_sha256,
    source_activity_index: index,
    match_reason: null,
  }));
}

export function readRunPinnedLessonActivities(
  snapshot: ParentStoryRunV1['lesson_pin_snapshot'],
): SuggestedActivity[] {
  const activities = snapshot?.activities;
  if (!snapshot
    || !snapshot.lesson_id.trim()
    || !snapshot.version_id.trim()
    || !/^[0-9a-f]{64}$/.test(snapshot.content_sha256)
    || !Array.isArray(activities)
    || activities.some((activity: unknown) => !isValidPinnedActivity(activity))) {
    return [];
  }
  return activities.map((activity: Activity, index: number) => ({
    ...activity,
    source: 'PINNED_LESSON',
    source_lesson_id: snapshot.lesson_id,
    source_lesson_title: snapshot.title ?? null,
    source_lesson_version_id: snapshot.version_id,
    source_content_sha256: snapshot.content_sha256,
    source_activity_index: index,
    match_reason: null,
  }));
}

export function canBeginContextStep(input: {
  profileId: string;
  topic: string;
  adultIdea: string;
  lessonPin: ParentLessonVersionPinV1 | null;
}): boolean {
  if (!input.profileId.trim()) return false;
  if (!input.lessonPin) return true;
  return Boolean(input.lessonPin.lesson_id.trim()
    && input.lessonPin.version_id.trim()
    && /^[0-9a-f]{64}$/.test(input.lessonPin.content_sha256));
}

export function isWithinOfflinePhotoLimit(fileSizeBytes: number | null | undefined): boolean {
  return typeof fileSizeBytes === 'number'
    && Number.isFinite(fileSizeBytes)
    && fileSizeBytes >= 0
    && fileSizeBytes <= 20 * 1024 * 1024;
}

export function isWithinOfflineAudioLimit(durationMs: number, fileSizeBytes: number): boolean {
  return Number.isFinite(durationMs)
    && durationMs >= 0
    && durationMs <= 120_000
    && isWithinOfflinePhotoLimit(fileSizeBytes);
}

export type DrawingGuideParseResult =
  | { kind: 'steps'; steps: string[] }
  | { kind: 'empty'; reason: 'missing' | 'ambiguous' };

export function parseDrawingGuideSteps(value: string | null | undefined): DrawingGuideParseResult {
  const text = value?.trim() ?? '';
  if (!text) return { kind: 'empty', reason: 'missing' };

  const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  if (lines.length < 4 || lines.length > 8) return { kind: 'empty', reason: 'ambiguous' };
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
  return input.photoSelected;
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

export function readDrawingCandidate(value: unknown): ParentDrawingCandidateV1 | null {
  if (!isRecord(value) || !Array.isArray(value.visible_features)) return null;
  if (!value.visible_features.every((feature) => typeof feature === 'string')) return null;
  if (typeof value.confidence !== 'number' || !Number.isFinite(value.confidence)
    || value.confidence < 0 || value.confidence > 1) return null;
  if (value.adult_confirmation_required !== true || typeof value.decision !== 'string') return null;
  if (value.candidate_subject !== undefined && value.candidate_subject !== null
    && typeof value.candidate_subject !== 'string') return null;

  const decision: ParentDrawingCandidateV1['decision'] = value.decision === 'CONFIRMED_BY_ADULT'
    || value.decision === 'CORRECTED_BY_ADULT'
    ? value.decision
    : 'REVIEW_REQUIRED';

  return {
    candidate_subject: typeof value.candidate_subject === 'string' ? value.candidate_subject : null,
    visible_features: [...value.visible_features],
    confidence: value.confidence,
    adult_confirmation_required: true,
    decision,
  };
}

export function readRunUnderstanding(value: unknown): {
  candidate: ParentDrawingCandidateV1;
  understandingRevision: number;
  subject: string;
} | null {
  if (!isRecord(value)) return null;
  const candidate = readDrawingCandidate(value.candidate);
  const revision = value.understanding_revision;
  if (!candidate || typeof revision !== 'number' || !Number.isInteger(revision) || revision < 1) return null;
  return {
    candidate,
    understandingRevision: revision,
    subject: typeof value.subject_label === 'string' && value.subject_label.trim()
      ? value.subject_label
      : candidate.candidate_subject ?? '',
  };
}

export function isConfirmedRunSubject(value: unknown, expectedSubject: string): boolean {
  if (!isRecord(value)) return false;
  const candidate = readDrawingCandidate(value.candidate);
  return typeof value.subject_label === 'string'
    && value.subject_label.trim() === expectedSubject.trim()
    && (candidate?.decision === 'CONFIRMED_BY_ADULT'
      || candidate?.decision === 'CORRECTED_BY_ADULT');
}

export function isActiveOrUnreconciledStoryRun(value: unknown): boolean {
  if (!isRecord(value)) return true;
  return value.run_state === 'SCRIPT_GENERATING'
    || value.run_state === 'SCRIPT_GENERATION_UNKNOWN'
    || value.story_status === 'GENERATING'
    || value.story_status === 'AWAITING_RECONCILIATION'
    || value.job_state === 'QUEUED'
    || value.job_state === 'RUNNING'
    || value.job_state === 'AWAITING_RECONCILIATION';
}

/** A run the server already closed as FAILED: no job is pending and it can never produce a result. */
export function isTerminalFailedStoryRun(value: unknown): boolean {
  return isRecord(value) && value.run_state === 'FAILED';
}

export const PARENT_DRAWING_TERMINAL_MESSAGE =
  'Buổi này đã dừng vì chưa đọc được tranh. Ảnh sẽ không được gửi lại. Hãy đóng buổi rồi bắt đầu buổi mới.';

export function terminalDrawingFailureMessage(errorCode: unknown): string {
  const detail = typeof errorCode === 'string' && errorCode
    ? safeParentFlowErrorMessage({ code: errorCode })
    : '';
  return detail ? `${detail} ${PARENT_DRAWING_TERMINAL_MESSAGE}` : PARENT_DRAWING_TERMINAL_MESSAGE;
}

export function isStaleRevisionError(error: unknown): boolean {
  return readErrorCode(error) === 'STALE_REVISION';
}

export type ValidatedStoryRevisionReadModel = {
  runId: string;
  storyRevisionId: string;
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
        | 'STORY_REVISION_ID_MISSING'
        | 'STORY_REVISION_ID_INVALID'
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
  if (storyRun.story_revision_id === undefined || storyRun.story_revision_id === null || storyRun.story_revision_id === '') {
    return { kind: 'invalid', reason: 'STORY_REVISION_ID_MISSING' };
  }
  if (typeof storyRun.story_revision_id !== 'string'
    || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(storyRun.story_revision_id)) {
    return { kind: 'invalid', reason: 'STORY_REVISION_ID_INVALID' };
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
      storyRevisionId: storyRun.story_revision_id.toLowerCase(),
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
  failedGeneration: boolean;
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
  return (input.storyPresent || input.failedGeneration)
    && (input.rewriteCount < 3 || input.allowSameActionRetry);
}

export function isRecoverableStoryOutputFailure(
  run: Pick<ParentStoryRunV1, 'run_state' | 'error_code' | 'job_state' | 'retryable' | 'story_status'> | null | undefined,
): boolean {
  return run?.run_state === 'FAILED'
    && run.error_code === 'STORY_OUTPUT_INVALID'
    && run.job_state === 'FAILED'
    && run.story_status === 'FAILED'
    && run.retryable === false;
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

export type ParentRecoveryGroup =
  | 'authentication'
  | 'resource-refresh'
  | 'action-denied'
  | 'resume-active-run'
  | 'teacher-only'
  | 'review-current-state'
  | 'transcript-review'
  | 'subject-review'
  | 'context-review'
  | 'story-review'
  | 'quota-summary'
  | 'provider-hold'
  | 'reconciliation'
  | 'wait-retry-after'
  | 'lifecycle-pending'
  | 'unavailable'
  | 'unknown';

const parentRecoveryGroups: Record<string, ParentRecoveryGroup> = {
  AUTH_REQUIRED: 'authentication',
  INVALID_TOKEN: 'authentication',
  TOKEN_EXPIRED: 'authentication',
  RESOURCE_NOT_FOUND: 'resource-refresh',
  ACTION_NOT_ALLOWED: 'action-denied',
  ACTIVE_RUN_EXISTS: 'resume-active-run',
  MULTI_CHILD_NOT_SUPPORTED: 'teacher-only',
  STALE_REVISION: 'review-current-state',
  OCR_NOT_SUPPORTED: 'teacher-only',
  UNSUPPORTED_LESSON_TYPE: 'teacher-only',
  LESSON_FILE_TOO_LARGE: 'teacher-only',
  TRANSCRIPT_NOT_CONFIRMED: 'transcript-review',
  SUBJECT_NOT_CONFIRMED: 'subject-review',
  PROFILE_CONTEXT_NOT_CONFIRMED: 'context-review',
  LESSON_PLAN_NOT_APPROVED: 'teacher-only',
  STORY_REWRITE_LIMIT_REACHED: 'story-review',
  PARENT_STORY_REWRITE_LIMIT: 'story-review',
  VIDEO_REGENERATION_LIMIT_REACHED: 'quota-summary',
  VIDEO_QUOTA_EXCEEDED: 'quota-summary',
  AI_COST_LIMIT_REACHED: 'provider-hold',
  PROVIDER_UNAVAILABLE: 'provider-hold',
  MODAL_FUNCTION_UNAVAILABLE: 'provider-hold',
  MODAL_AI_NOT_ENABLED: 'provider-hold',
  PARENT_ARTWORK_SCAN_UNAVAILABLE: 'provider-hold',
  PARENT_ARTWORK_STORAGE_UNAVAILABLE: 'provider-hold',
  PARENT_STORY_RUN_STORE_UNAVAILABLE: 'provider-hold',
  STORY_OUTPUT_INVALID: 'provider-hold',
  STORY_TEXT_INCOMPLETE: 'provider-hold',
  MODAL_OUTCOME_UNKNOWN: 'reconciliation',
  DRAWING_OUTCOME_UNKNOWN: 'reconciliation',
  DRAWING_OUTPUT_TRUNCATED: 'provider-hold',
  DRAWING_OUTPUT_INVALID: 'provider-hold',
  DRAWING_OUTPUT_EMPTY: 'provider-hold',
  DRAWING_WORKER_FAILED_TERMINAL: 'provider-hold',
  AWAITING_RECONCILIATION: 'reconciliation',
  SUBSCRIPTION_RESTRICTED: 'teacher-only',
  CLASS_CAPACITY_REACHED: 'teacher-only',
  RATE_LIMITED: 'wait-retry-after',
  DELETE_PENDING: 'lifecycle-pending',
  DELETED: 'lifecycle-pending',
  CAPABILITY_UNAVAILABLE: 'unavailable',
  ROUTE_NOT_IN_BE_HANDOFF: 'unavailable',
};

const safePreDispatchDrawingErrorCodes = new Set([
  'MODAL_AI_NOT_ENABLED',
  'PARENT_ARTWORK_SCAN_UNAVAILABLE',
  'PARENT_ARTWORK_STORAGE_UNAVAILABLE',
  'PARENT_STORY_RUN_STORE_UNAVAILABLE',
]);

export function isSafePreDispatchDrawingError(error: unknown): error is ParentApplicationError {
  return error instanceof ParentApplicationError
    && error.status === 503
    && safePreDispatchDrawingErrorCodes.has(error.code);
}

export function parentRecoveryGroupForError(error: unknown): ParentRecoveryGroup {
  const code = readErrorCode(error);
  return code ? parentRecoveryGroups[code] ?? 'unknown' : 'unknown';
}

export function safeParentFlowErrorMessage(error: unknown): string {
  const code = readErrorCode(error);
  const messages: Record<string, string> = {
    ACTION_NOT_ALLOWED: 'Tài khoản hiện không thể thực hiện thao tác này.',
    PARENT_STORE_UNAVAILABLE: 'Hồ sơ đang tạm thời không khả dụng. Vui lòng thử lại sau.',
    STALE_REVISION: 'Hồ sơ đã thay đổi. Hãy kiểm tra thông tin mới nhất rồi lưu lại.',
    INVALID_STATE_TRANSITION: 'Hồ sơ đã thay đổi trạng thái. Hãy kiểm tra lại trước khi tiếp tục.',
    ACTIVE_RUN_EXISTS: 'Hồ sơ đang có buổi học chưa hoàn tất. Hãy tiếp tục buổi học hiện tại.',
    RESOURCE_NOT_FOUND: 'Không tìm thấy nội dung hoặc bạn không thể truy cập nội dung này.',
    DELETED: 'Buổi học đã được xóa.',
    MULTI_CHILD_NOT_SUPPORTED: 'Thao tác này chưa khả dụng trong luồng dành cho phụ huynh.',
    OCR_NOT_SUPPORTED: 'Thao tác này chưa khả dụng trong luồng dành cho phụ huynh.',
    UNSUPPORTED_LESSON_TYPE: 'Thao tác này chưa khả dụng trong luồng dành cho phụ huynh.',
    LESSON_FILE_TOO_LARGE: 'Thao tác này chưa khả dụng trong luồng dành cho phụ huynh.',
    TRANSCRIPT_NOT_CONFIRMED: 'Hãy xem lại và xác nhận nội dung đã nghe trước khi tiếp tục.',
    SUBJECT_NOT_CONFIRMED: 'Hãy xem lại và xác nhận chủ thể trước khi tiếp tục.',
    PROFILE_CONTEXT_NOT_CONFIRMED: 'Hãy xem lại và xác nhận ngữ cảnh trước khi tiếp tục.',
    LESSON_PLAN_NOT_APPROVED: 'Thao tác này chưa khả dụng trong luồng dành cho phụ huynh.',
    STORY_REWRITE_LIMIT_REACHED: 'Đã dùng hết lượt viết lại. Bạn có thể xác nhận kịch bản hiện tại hoặc dừng.',
    VIDEO_REGENERATION_LIMIT_REACHED: 'Đã dùng hết lượt tạo lại video. Trạng thái video hiện tại vẫn do máy chủ xác nhận.',
    VIDEO_QUOTA_EXCEEDED: 'Máy chủ chưa xác nhận quyền tạo video. Hãy xem tóm tắt hạn mức nếu có.',
    AI_COST_LIMIT_REACHED: 'Hệ thống tạm thời chưa thể nhận yêu cầu này. Chưa xác nhận tiêu hạn mức.',
    PROVIDER_UNAVAILABLE: 'Dịch vụ tạo nội dung hiện chưa khả dụng. Hãy kiểm tra trạng thái trước khi thử lại.',
    MODAL_FUNCTION_UNAVAILABLE: 'Dịch vụ tạo nội dung hiện chưa khả dụng.',
    MODAL_AI_NOT_ENABLED: 'Dịch vụ tạo nội dung hiện chưa khả dụng.',
    PARENT_ARTWORK_SCAN_UNAVAILABLE: 'Chưa kiểm tra được ảnh. Có thể thử lại một lần khi dịch vụ sẵn sàng.',
    PARENT_ARTWORK_STORAGE_UNAVAILABLE: 'Chưa lưu được ảnh vào buổi học. Có thể thử lại một lần.',
    PARENT_STORY_RUN_STORE_UNAVAILABLE: 'Chưa lưu được trạng thái xử lý. Không gửi lại hoặc xác nhận bản nháp cũ; hãy kiểm tra lại buổi học.',
    STORY_OUTPUT_INVALID: 'Kịch bản chưa đạt yêu cầu nên máy chủ không lưu bản mới. Bản nháp trước cũng chưa thể xác nhận.',
    STORY_TEXT_INCOMPLETE: 'Kịch bản chưa hoàn chỉnh nên máy chủ đã từ chối bản mới. Không xác nhận bản nháp trước.',
    MODAL_OUTCOME_UNKNOWN: 'Chưa xác nhận được kết quả. Hãy kiểm tra trạng thái trước khi thử lại.',
    DRAWING_OUTCOME_UNKNOWN: 'Chưa xác nhận được kết quả đọc tranh. Hãy kiểm tra trạng thái trước khi gửi lại.',
    DRAWING_OUTPUT_TRUNCATED: 'Kết quả đọc tranh chưa hoàn tất. Hãy thử lại sau.',
    DRAWING_OUTPUT_INVALID: 'Chưa đọc được tranh lần này. Hãy thử lại sau.',
    DRAWING_OUTPUT_EMPTY: 'AI chưa trả về kết quả nhận diện. Hãy thử lại sau.',
    DRAWING_WORKER_FAILED_TERMINAL: 'Dịch vụ phân tích tranh gặp lỗi. Hãy thử lại sau.',
    AWAITING_RECONCILIATION: 'Đang kiểm tra trạng thái yêu cầu. Không gửi yêu cầu trùng lặp.',
    SUBSCRIPTION_RESTRICTED: 'Thao tác này chưa khả dụng trong luồng dành cho phụ huynh.',
    CLASS_CAPACITY_REACHED: 'Thao tác này chưa khả dụng trong luồng dành cho phụ huynh.',
    RATE_LIMITED: 'Hãy chờ theo hướng dẫn của máy chủ trước khi thử lại.',
    DELETE_PENDING: 'Yêu cầu xóa đang chờ máy chủ xác nhận.',
    CAPABILITY_UNAVAILABLE: 'Tính năng này chưa có tuyến dịch vụ được xác nhận.',
    ROUTE_NOT_IN_BE_HANDOFF: 'Tính năng này chưa có tuyến dịch vụ được xác nhận.',
    PARENT_LESSON_PIN_REQUIRED: 'Hãy chọn một bài học trước khi bắt đầu.',
    PARENT_CONTEXT_REQUIRED: 'Hãy chọn hồ sơ trước khi tiếp tục.',
    PARENT_CONTEXT_SNAPSHOT_INVALID: 'Chưa thể xác nhận ngữ cảnh của buổi học này.',
    PARENT_CONTEXT_NOT_CONFIRMED: 'Người lớn cần xác nhận ngữ cảnh trước khi tiếp tục.',
    PARENT_DRAWING_REQUIRED: 'Hãy chọn ảnh tranh trước khi tiếp tục xem xét.',
    PARENT_DRAWING_RESULT_INVALID: 'Chưa thể đọc kết quả xem xét tranh. Hãy kiểm tra trạng thái trước khi gửi lại.',
    PARENT_ACTIVITY_QUALITY_GATE_REJECTED: 'Gợi ý hoạt động chưa đạt kiểm tra chất lượng. Máy chủ đã loại bỏ và chưa lưu gợi ý để chọn.',
    PARENT_SUBJECT_CONFIRMATION_INVALID: 'Chưa thể xác nhận chủ thể của bức tranh.',
    PARENT_STORY_REVISION_INVALID: 'Chưa thể xác nhận đúng phiên bản kịch bản. Hãy kiểm tra lại buổi học.',
    PARENT_STORY_NOT_CONFIRMABLE: 'Kịch bản chưa có đủ thông tin để xác nhận.',
    PARENT_STORY_REWRITE_LIMIT: 'Đã dùng hết 3 lượt gợi ý viết lại.',
    INVALID_LIMIT: 'Chưa tải được danh sách hồ sơ. Vui lòng thử lại.',
  };
  if (code === 'RATE_LIMITED' && isRecord(error)
    && typeof error.retryAfterSeconds === 'number'
    && Number.isFinite(error.retryAfterSeconds)
    && error.retryAfterSeconds > 0) {
    return 'Hãy chờ ' + Math.ceil(error.retryAfterSeconds) + ' giây rồi kiểm tra lại.';
  }
  const message = (code && messages[code]) || 'Chưa thể hoàn tất thao tác. Vui lòng kiểm tra lại sau.';
  if (code && parentRecoveryGroups[code] === 'provider-hold' && isRecord(error)
    && typeof error.correlationId === 'string'
    && /^[A-Za-z0-9._:-]{1,120}$/.test(error.correlationId)) {
    return message + ' Mã tham chiếu: ' + error.correlationId + '.';
  }
  return message;
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

export function readErrorCode(value: unknown): string | null {
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

function isValidPinnedActivity(value: unknown): value is Activity {
  if (!isRecord(value)) return false;
  return typeof value.title === 'string'
    && typeof value.objective === 'string'
    && typeof value.materials_text === 'string'
    && typeof value.preparation_text === 'string'
    && typeof value.instructions_text === 'string'
    && typeof value.observation_notes === 'string'
    && typeof value.safety_notes === 'string'
    && (value.activity_kind === 'indoor' || value.activity_kind === 'outdoor' || value.activity_kind === 'mixed');
}
