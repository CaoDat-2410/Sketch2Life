import { parentConfig } from '../config';
import { ParentApplicationError, type ParentApplicationErrorMetadata, type ParentSafeFieldError } from '../../application/ParentApplicationError';
import type {
  AuthTokenPort,
  ParentActionIdentity,
  ParentApiPort,
  ParentDrawingMediaType,
} from '../../application/ports/ParentPorts';
import type {
  ConsentPolicy,
  LessonDetail,
  LessonInvitation,
  LessonSummary,
  ParentAudioTranscription,
  ParentCandidate,
  ParentGroupInvitation,
  ParentLessonDeliveryPage,
  ParentNotification,
  ParentNotificationPage,
  ParentProfile,
  ParentProfileCreateV1,
  ParentProfileDeletePendingV1,
  ParentProfilePageV1,
  ParentProfilePatchV1,
  ParentProfileRecordV1,
  ParentProfileReferenceV1,
  ParentProfileViewV1,
  ParentProfileShareGrant,
  ParentProfileSharePage,
  ParentRunLifecycleReceipt,
  ParentActiveStoryRunEnvelopeV1,
  ParentStoryRunHistoryPage,
  ParentTranscriptConfirmation,
  ParentVideoQuota,
  ParentStoryContextConfirmationV1,
  ParentStoryRevisionResultV1,
  ParentStoryRunCreateV1,
  ParentStoryRunEnvelopeV1,
  ParentStoryRunV1,
  ParentStoryScriptConfirmationV1,
  ParentStorySubjectConfirmationV1,
  StoryRun,
  SuggestedActivity,
} from '../../domain/types';

export class ParentApiError extends ParentApplicationError {
  constructor(code: string, requestId: string, status?: number, metadata: ParentApplicationErrorMetadata = {}) {
    super(code, apiErrorMessage(code), requestId, status, metadata);
    this.name = 'ParentApiError';
  }
}

export class ParentApi implements ParentApiPort {
  constructor(
    private readonly auth: AuthTokenPort,
    private readonly fetcher: typeof fetch = fetch,
    private readonly apiBaseUrl: string = parentConfig.apiBaseUrl,
  ) {}

  getConsentPolicy() {
    return this.request<{ request_id: string; policy: ConsentPolicy }>('/api/parent/v1/consent-policy', 'GET');
  }

  listProfiles() {
    return this.request<{ request_id: string; profiles: ParentProfile[] }>('/api/parent/v1/child-profiles', 'GET');
  }

  listProfilesV1(limit = 25, cursor?: string | null) {
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
      return Promise.reject(new ParentApiError('INVALID_LIMIT', 'local-request'));
    }
    const query = new URLSearchParams({ limit: String(limit) });
    if (cursor !== undefined && cursor !== null) query.set('cursor', cursor);
    return this.request<ParentProfilePageV1>(`/v1/parent/profiles?${query.toString()}`, 'GET');
  }

  getProfileV1(profileId: string) {
    return this.request<ParentProfileRecordV1>(`/v1/parent/profiles/${encodeURIComponent(profileId)}`, 'GET');
  }

  createProfileV1(input: ParentProfileCreateV1, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 128, true);
    return this.request<ParentProfileReferenceV1>(
      '/v1/parent/profiles',
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  patchProfileV1(profileId: string, input: ParentProfilePatchV1, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 128, true);
    return this.request<ParentProfileViewV1>(
      `/v1/parent/profiles/${encodeURIComponent(profileId)}`,
      'PATCH',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  requestProfileDeletionV1(profileId: string, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 128, true);
    return this.request<ParentProfileDeletePendingV1>(
      `/v1/parent/profiles/${encodeURIComponent(profileId)}`,
      'DELETE',
      undefined,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  createProfile(input: {
    age_months: number;
    display_name: string;
    interests_summary: string;
    consent_accepted: true;
    consent_policy_version: string;
  }) {
    return this.request<{ request_id: string; profile: ParentProfile }>('/api/parent/v1/child-profiles', 'POST', input);
  }

  updateProfile(profileId: string, input: {
    expected_revision: number;
    age_months: number;
    display_name: string;
    interests_summary: string;
  }) {
    return this.request<{ request_id: string; profile: ParentProfile }>(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}`,
      'PATCH',
      input,
    );
  }

  grantAuthorization(profileId: string, policyVersion: string) {
    return this.request<{ request_id: string; profile: ParentProfile }>(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}/data-authorizations`,
      'POST',
      { consent_accepted: true, consent_policy_version: policyVersion },
    );
  }

  revokeAuthorization(profileId: string) {
    return this.request<{ request_id: string; profile: ParentProfile }>(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}/data-authorizations`,
      'DELETE',
    );
  }

  archiveProfile(profileId: string) {
    return this.request<{ request_id: string; profile: ParentProfile }>(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}`,
      'DELETE',
    );
  }

  getActiveStoryRun() {
    return this.request<{ request_id: string; story_run: StoryRun | null }>('/api/parent/v1/story-runs/active/current', 'GET');
  }

  getStoryRun(runId: string) {
    return this.request<{ request_id: string; story_run: StoryRun }>(`/api/parent/v1/story-runs/${encodeURIComponent(runId)}`, 'GET');
  }

  getActiveStoryRunV1() {
    return this.request<ParentActiveStoryRunEnvelopeV1>('/v1/story-runs/active/current', 'GET');
  }

  getStoryRunV1(runId: string) {
    return this.request<ParentStoryRunEnvelopeV1>(`/v1/story-runs/${encodeURIComponent(runId)}`, 'GET');
  }

  createStoryRunV1(input: ParentStoryRunCreateV1, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 256);
    return this.request<ParentStoryRunEnvelopeV1>(
      '/v1/story-runs',
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  confirmStoryRunContextV1(runId: string, input: ParentStoryContextConfirmationV1, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 256);
    return this.request<ParentStoryRunEnvelopeV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/context-confirmation`,
      'POST',
      input,
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  confirmStoryRunSubjectV1(runId: string, revision: number, subject: string, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 256);
    return this.request<ParentStorySubjectConfirmationV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/subject-confirmation`,
      'POST',
      { expected_understanding_revision: revision, confirmed_subject: subject },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  confirmStoryRunScriptV1(runId: string, revision: number, sha256: string, actionIdentity: ParentActionIdentity) {
    assertIdempotencyKey(actionIdentity, 256);
    return this.request<ParentStoryScriptConfirmationV1>(
      `/v1/story-runs/${encodeURIComponent(runId)}/script-confirmation`,
      'POST',
      { expected_revision: revision, story_sha256: sha256 },
      30_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  createStoryRevisionV1(
    runId: string,
    revision: number,
    rewriteInstruction: string | undefined,
    actionIdentity: ParentActionIdentity,
  ) {
    assertIdempotencyKey(actionIdentity, 200);
    return this.request<ParentStoryRevisionResultV1>(
      `/api/parent/v1/ai/story-runs/${encodeURIComponent(runId)}/story-revisions`,
      'POST',
      {
        expected_understanding_revision: revision,
        ...(rewriteInstruction?.trim() ? { rewrite_instruction: rewriteInstruction.trim() } : {}),
      },
      1_850_000,
      { 'Idempotency-Key': actionIdentity },
    );
  }

  listStoryRuns(profileId?: string, cursor?: string | null) {
    const query = new URLSearchParams({ limit: '20' });
    if (profileId) query.set('profile_id', profileId);
    if (cursor) query.set('cursor', cursor);
    return this.request<ParentStoryRunHistoryPage>(`/api/parent/v1/story-runs?${query.toString()}`, 'GET');
  }

  cancelStoryRun(runId: string) {
    return this.request<ParentRunLifecycleReceipt>(
      `/api/parent/v1/story-runs/${encodeURIComponent(runId)}/cancel`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  deleteStoryRun(runId: string) {
    return this.request<ParentRunLifecycleReceipt>(
      `/api/parent/v1/story-runs/${encodeURIComponent(runId)}`,
      'DELETE',
      undefined,
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  listLessons() {
    return this.request<{ contract: string; items: LessonSummary[]; next_cursor: string | null }>(
      '/api/lesson-library/v1/me/lessons?source=ALL&limit=50', 'GET', undefined, 30_000,
    );
  }

  listLessonInvitations() {
    return this.request<{ contract: string; items: LessonInvitation[]; next_cursor: string | null }>(
      '/api/lesson-library/v1/me/lesson-invitations?limit=50',
      'GET',
    );
  }

  acceptLessonInvitation(invitationId: string) {
    return this.request<unknown>(
      `/api/lesson-library/v1/me/lesson-invitations/${encodeURIComponent(invitationId)}/accept`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  declineLessonInvitation(invitationId: string) {
    return this.request<unknown>(
      `/api/lesson-library/v1/me/lesson-invitations/${encodeURIComponent(invitationId)}/decline`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  listParentGroupInvitations() {
    return this.request<{ contract: string; items: ParentGroupInvitation[]; next_cursor: string | null }>(
      '/api/lesson-library/v1/me/parent-group-invitations?limit=50',
      'GET',
    );
  }

  acceptParentGroupInvitation(membershipId: string) {
    return this.request<unknown>(
      `/api/lesson-library/v1/me/parent-group-invitations/${encodeURIComponent(membershipId)}/accept`,
      'POST',
      undefined,
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  getLesson(lessonId: string) {
    return this.request<LessonDetail>(`/api/lesson-library/v1/me/lessons/${encodeURIComponent(lessonId)}`, 'GET');
  }

  generateSketchGuide(topic: string) {
    return this.request<{
      request_id: string;
      modal_call_id?: string;
      status: string;
      review_required: true;
      model?: { id: string; revision: string };
      image_base64: string;
      asset?: Record<string, unknown>;
    }>('/api/parent/v1/ai/sketch-guides', 'POST', { topic, difficulty: 'beginner', step_count: 3 }, 910_000);
  }

  createStoryRun(input: {
    parent_profile_id: string;
    expected_profile_revision_id: string;
    consent_policy_version: string;
    topic: string;
    adult_confirmed_idea: string;
    context_confirmed: true;
    lesson_id?: string;
    lesson_version_id?: string;
  }) {
    return this.request<{ request_id: string; story_run: StoryRun }>('/api/parent/v1/story-runs', 'POST', input);
  }

  analyzeDrawing(storyRunId: string, imageBase64: string, mediaType: ParentDrawingMediaType) {
    return this.request<{
      request_id: string;
      modal_call_id?: string;
      candidate?: ParentCandidate;
      run_input_revision?: number;
      understanding_revision?: number;
    }>('/api/parent/v1/ai/drawing-understandings', 'POST', {
      story_run_id: storyRunId,
      image_base64: imageBase64,
      media_type: mediaType,
    }, 1_850_000);
  }

  confirmSubject(storyRunId: string, revision: number, subject: string) {
    return this.request<{ request_id: string; story_run_id: string; understanding_revision: number; decision: string }>(
      `/api/parent/v1/story-runs/${encodeURIComponent(storyRunId)}/subject-confirmations`,
      'POST',
      { expected_understanding_revision: revision, confirmed_subject: subject },
    );
  }

  suggestActivities(storyRunId: string, revision: number) {
    void storyRunId;
    void revision;
    return Promise.reject(new ParentApiError('ROUTE_NOT_MOUNTED', 'local-request')) as Promise<{
      request_id: string;
      modal_call_id?: string;
      contract: 'ParentActivitySuggestionResponseV2';
      selection_mode: 'CATALOG_SELECTION' | 'AI_GENERATED_FALLBACK';
      catalog_candidate_count: number;
      review_required: true;
      activities: SuggestedActivity[];
    }>;
  }

  generateStory(storyRunId: string, revision: number, rewriteInstruction?: string) {
    return this.request<{
      request_id: string;
      modal_call_id?: string;
      story?: unknown;
      story_sha256?: string;
      story_run?: StoryRun;
    }>(`/api/parent/v1/ai/story-runs/${encodeURIComponent(storyRunId)}/story-revisions`, 'POST', {
      expected_understanding_revision: revision,
      ...(rewriteInstruction?.trim() ? { rewrite_instruction: rewriteInstruction.trim() } : {}),
    }, 1_850_000);
  }

  confirmStory(storyRunId: string, revision: number, sha256: string) {
    return this.request<{ request_id: string; story_run: StoryRun }>(
      `/api/parent/v1/story-runs/${encodeURIComponent(storyRunId)}/story-revision-confirmations`,
      'POST',
      { expected_revision: revision, story_sha256: sha256 },
    );
  }

  async transcribeAudio(storyRunId: string, audio: { uri: string; file_name: string; media_type: string }) {
    const baseUrl = this.apiBaseUrl.replace(/\/+$/, '');
    if (!baseUrl) throw new Error('Thiếu SKETCH2LIFE_MOBILE_API_BASE_URL trong .env gốc.');
    const requestId = `parent-expo-${Date.now().toString(36)}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 650_000);
    const form = new FormData();
    form.append('audio', {
      uri: audio.uri,
      name: audio.file_name,
      type: audio.media_type,
    } as unknown as Blob);
    try {
      const response = await this.fetcher(
        `${baseUrl}/api/parent/v1/story-runs/${encodeURIComponent(storyRunId)}/audio-transcriptions`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${await this.auth.getIdToken()}`,
            Accept: 'application/json',
            'X-Request-ID': requestId,
            'Idempotency-Key': createIdempotencyKey(),
          },
          body: form,
          signal: controller.signal,
        },
      );
      const payload = await response.json().catch(() => null) as Record<string, unknown> | null;
      if (!response.ok) {
        throw apiErrorFromResponse(payload, response.status, requestId, response.headers);
      }
      if (!payload || typeof payload !== 'object') throw new ParentApiError('INVALID_API_RESPONSE', requestId, response.status);
      return payload as unknown as ParentAudioTranscription;
    } catch (error) {
      if (error instanceof ParentApiError) throw error;
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ParentApiError('REQUEST_TIMEOUT', requestId, 408);
      }
      throw new ParentApiError('NETWORK_ERROR', requestId);
    } finally {
      clearTimeout(timeout);
    }
  }

  confirmTranscript(storyRunId: string, revision: number, transcriptText: string) {
    return this.request<ParentTranscriptConfirmation>(
      `/api/parent/v1/story-runs/${encodeURIComponent(storyRunId)}/transcript-confirmations`,
      'POST',
      { expected_revision: revision, transcript_text: transcriptText },
    );
  }

  listProfileShares(profileId: string) {
    return this.request<ParentProfileSharePage>(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}/shares`, 'GET',
    );
  }

  createProfileShare(profileId: string, teacherSubject: string) {
    return this.request<{ request_id: string; grant: ParentProfileShareGrant }>(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}/shares`,
      'POST',
      { teacher_subject: teacherSubject },
      30_000,
      { 'Idempotency-Key': createIdempotencyKey() },
    );
  }

  revokeProfileShare(profileId: string, grantId: string) {
    return this.request<{ request_id: string; grant: ParentProfileShareGrant }>(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}/shares/${encodeURIComponent(grantId)}`,
      'DELETE',
    );
  }

  listLessonDeliveries(profileId: string, cursor?: string | null) {
    const query = new URLSearchParams({ profile_id: profileId, limit: '20' });
    if (cursor) query.set('cursor', cursor);
    return this.request<ParentLessonDeliveryPage>(
      `/api/lesson-library/v1/me/deliveries?${query.toString()}`, 'GET',
    );
  }

  submitLessonFeedback(occurrenceId: string, profileId: string, feedbackText: string) {
    return this.request<{
      contract: 'LessonDeliveryFeedbackV1';
      feedback_id: string;
      feedback_text: string;
      created_at: string;
      updated_at: string;
    }>(
      `/api/lesson-library/v1/me/deliveries/${encodeURIComponent(occurrenceId)}/feedback`,
      'POST',
      { parent_profile_id: profileId, feedback_text: feedbackText },
    );
  }

  listNotifications(cursor?: string | null) {
    const query = new URLSearchParams({ limit: '20' });
    if (cursor) query.set('cursor', cursor);
    return this.request<ParentNotificationPage>(`/api/notifications/v1/inbox?${query.toString()}`, 'GET');
  }

  markNotificationRead(notificationId: string) {
    return this.request<ParentNotification>(
      `/api/notifications/v1/inbox/${encodeURIComponent(notificationId)}/read`, 'POST',
    );
  }

  getVideoQuota() {
    return this.request<ParentVideoQuota>('/api/billing/v1/video-quota', 'GET');
  }

  private async request<T>(
    path: string,
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
    body?: unknown,
    timeoutMs = 30_000,
    additionalHeaders: Record<string, string> = {},
  ): Promise<T> {
    const baseUrl = this.apiBaseUrl.replace(/\/+$/, '');
    if (!baseUrl) throw new Error('Thiếu SKETCH2LIFE_MOBILE_API_BASE_URL trong .env gốc.');
    const requestId = `parent-expo-${Date.now().toString(36)}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await this.fetcher(`${baseUrl}${path}`, {
        method,
        headers: {
          Authorization: `Bearer ${await this.auth.getIdToken()}`,
          Accept: 'application/json',
          'X-Request-ID': requestId,
          ...additionalHeaders,
          ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
        signal: controller.signal,
      });
      const payload = await response.json().catch(() => null) as Record<string, unknown> | null;
      if (!response.ok) {
        throw apiErrorFromResponse(payload, response.status, requestId, response.headers);
      }
      if (!payload || typeof payload !== 'object') throw new ParentApiError('INVALID_API_RESPONSE', requestId, response.status);
      return payload as T;
    } catch (error) {
      if (error instanceof ParentApiError) throw error;
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ParentApiError('REQUEST_TIMEOUT', requestId, 408);
      }
      throw new ParentApiError('NETWORK_ERROR', requestId);
    } finally {
      clearTimeout(timeout);
    }
  }
}

function apiErrorMessage(code: string): string {
  const messages: Record<string, string> = {
    REQUEST_TIMEOUT: 'Yêu cầu quá thời gian chờ. Trạng thái AI có thể chưa rõ; không tự gửi lại.',
    NETWORK_ERROR: 'Không kết nối được máy chủ.',
    REQUEST_CONFLICT: 'Dữ liệu đã thay đổi. Hãy tải lại trạng thái trước khi tiếp tục.',
    ACTION_NOT_ALLOWED: 'Tài khoản này chưa thể thực hiện thao tác vừa chọn.',
    PARENT_STORE_UNAVAILABLE: 'Hồ sơ đang tạm thời không khả dụng. Vui lòng thử lại sau.',
    ACTIVE_RUN_EXISTS: 'Hồ sơ đang có một buổi học chưa hoàn tất.',
    STALE_REVISION: 'Dữ liệu đã thay đổi. Hãy tải lại và kiểm tra trước khi tiếp tục.',
    INVALID_STATE_TRANSITION: 'Trạng thái hồ sơ đã thay đổi. Hãy tải lại hồ sơ.',
    INVALID_LIMIT: 'Không thể tải danh sách hồ sơ lúc này.',
    ROUTE_NOT_MOUNTED: 'Tính năng này chưa sẵn sàng.',
    IDEMPOTENCY_KEY_INVALID: 'Thao tác chưa thể gửi. Vui lòng bắt đầu lại thao tác.',
    PARENT_PROFILE_NOT_AUTHORIZED: 'Hồ sơ chưa có quyền xử lý dữ liệu còn hiệu lực.',
    PARENT_STORY_ACTIVE_RUN_EXISTS: 'Hồ sơ đang có một buổi học chưa hoàn tất.',
    MODAL_OUTCOME_UNKNOWN: 'Modal chưa xác nhận kết quả. Không tự gửi lại yêu cầu này.',
    MODAL_MODEL_OUTPUT_INVALID: 'AI đã phản hồi nhưng dữ liệu không đúng cấu trúc yêu cầu.',
    MODAL_MODEL_REVISION_MISMATCH: 'Phiên bản model trả về không khớp cấu hình.',
    MODAL_FUNCTION_UNAVAILABLE: 'Dịch vụ AI hiện chưa sẵn sàng.',
  };
  return messages[code] ?? 'Yêu cầu chưa hoàn tất. Vui lòng kiểm tra lại rồi thử lại sau.';
}

function apiErrorFromResponse(
  payload: Record<string, unknown> | null,
  status: number,
  fallbackRequestId: string,
  headers?: Headers,
): ParentApiError {
  const detail = isRecord(payload?.detail) ? payload.detail : null;
  const code = safeErrorCode(payload?.code) ?? safeErrorCode(detail?.code) ?? `HTTP_${status}`;
  const requestId = safeIdentifier(payload?.request_id)
    ?? safeIdentifier(detail?.request_id)
    ?? safeIdentifier(headers?.get('X-Request-ID'))
    ?? fallbackRequestId;
  const correlationId = safeIdentifier(payload?.correlation_id) ?? safeIdentifier(detail?.correlation_id) ?? undefined;
  const retryableValue = typeof payload?.retryable === 'boolean'
    ? payload.retryable
    : typeof detail?.retryable === 'boolean' ? detail.retryable : undefined;
  const retryAfterValue = finiteNumber(payload?.retry_after_seconds)
    ?? finiteNumber(detail?.retry_after_seconds);
  const currentVersion = primitiveVersion(payload?.current_version) ?? primitiveVersion(detail?.current_version);
  const fieldErrors = safeFieldErrors(payload?.field_errors) ?? safeFieldErrors(detail?.field_errors);
  const metadata: ParentApplicationErrorMetadata = {
    ...(correlationId ? { correlationId } : {}),
    ...(retryableValue === undefined ? {} : { retryable: retryableValue }),
    ...(retryAfterValue === undefined ? {} : { retryAfterSeconds: retryAfterValue }),
    ...(currentVersion === undefined ? {} : { currentVersion }),
    ...(fieldErrors ? { fieldErrors } : {}),
  };
  return new ParentApiError(code, requestId, status, metadata);
}

function safeFieldErrors(value: unknown): ParentSafeFieldError[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const fields: Record<string, string> = {
    display_name: 'display_name',
    age_months: 'age_months',
    interests_summary: 'interests_summary',
    expected_revision: 'expected_revision',
    cursor: 'cursor',
    limit: 'limit',
    profile_id: 'profile_id',
    'idempotency-key': 'idempotency_key',
    idempotency_key: 'idempotency_key',
    lesson_version: 'lesson_version',
    topic: 'topic',
    adult_confirmed_idea: 'adult_confirmed_idea',
  };
  const codes = new Set([
    'REQUIRED', 'EMPTY', 'TOO_LONG', 'OUT_OF_RANGE', 'INVALID_TYPE', 'INVALID_FORMAT',
    'UNKNOWN_FIELD', 'INVALID_CURSOR', 'INVALID_LIMIT', 'STALE_REVISION',
  ]);
  const result: ParentSafeFieldError[] = [];
  for (const item of value) {
    if (!isRecord(item) || typeof item.field !== 'string' || typeof item.code !== 'string') continue;
    const field = fields[item.field.toLowerCase()];
    const code = item.code.toUpperCase();
    if (field && codes.has(code)) result.push({ field, code });
  }
  return result;
}

function safeErrorCode(value: unknown): string | null {
  if (typeof value !== 'string' || value.length > 80 || !/^[A-Za-z0-9_]+$/.test(value)) return null;
  return value;
}

function safeIdentifier(value: unknown): string | null {
  return typeof value === 'string' && value.length > 0 && value.length <= 200 ? value : null;
}

function finiteNumber(value: unknown): number | undefined {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : undefined;
}

function primitiveVersion(value: unknown): string | number | undefined {
  return typeof value === 'string' || (typeof value === 'number' && Number.isFinite(value)) ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function stringValue(value: unknown): string | null {
  return typeof value === 'string' ? value : null;
}

function assertIdempotencyKey(key: ParentActionIdentity, maxLength: number, printableAscii = false): void {
  const validLength = key.length >= 1 && key.length <= maxLength;
  const validCharacters = !printableAscii || /^[\x20-\x7E]+$/.test(key);
  if (!validLength || !validCharacters) {
    throw new ParentApiError('IDEMPOTENCY_KEY_INVALID', 'local-request', 400);
  }
}

function createIdempotencyKey(): string {
  return `parent-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 14)}`;
}
