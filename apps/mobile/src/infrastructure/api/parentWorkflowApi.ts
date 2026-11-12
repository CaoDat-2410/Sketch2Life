import {firebasePublicConfig} from '../auth/firebasePublicConfig';
import type {AuthSessionPort} from '../auth/AuthSessionPort';

export type ParentProfileRevision = Readonly<{
  profile_revision_id: string;
  revision: number;
  age_months: number;
  display_name: string;
  interests_summary: string;
  revision_sha256: string;
  created_at: string;
}>;

export type ParentProfile = Readonly<{
  parent_profile_id: string;
  state: 'ACTIVE' | 'ARCHIVED' | 'DELETED';
  current_revision: ParentProfileRevision;
  authorization_state: 'GRANTED' | 'REVOKED' | 'EXPIRED' | null;
  authorization_policy_version: string | null;
  authorization_current: boolean;
  created_at: string;
  updated_at: string;
}>;

export type ParentConsentPolicy = Readonly<{
  purpose_code: string;
  policy_version: string;
  consent_text: string;
  consent_text_sha256: string;
}>;

export type ParentRunContext = Readonly<{
  schema_version: 'sketch2life.parent-context.v1';
  profile_revision_ref: string;
  age_months: number;
  interests_summary: string;
  topic: string;
  adult_confirmed_idea: string;
  consent_policy_version: string;
}>;

export type ParentStoryRun = Readonly<{
  run_id: string;
  run_state: string;
  parent_profile_id: string;
  profile_revision_ref: string;
  context_revision: number;
  context_snapshot: ParentRunContext;
  context_snapshot_sha256: string;
  current_input_revision: number | null;
  understanding_revision: number | null;
  subject_label: string | null;
  candidate: ParentCandidate | null;
  story_revision_id: string | null;
  story_revision_no: number | null;
  story_status: string | null;
  story_sha256: string | null;
  story: unknown;
  job_state: string | null;
  retryable: boolean;
  error_code: string | null;
  created_at: string;
  updated_at: string;
}>;

export type ParentCandidate = Readonly<{
  candidate_subject?: string | null;
  visible_features: string[];
  confidence: number;
  adult_confirmation_required: true;
  decision: string;
}>;

export type ParentAiReceipt<T> = Readonly<{
  request_id: string;
  modal_call_id?: string;
  model?: {id: string; revision: string};
  review_required?: boolean;
  image_base64?: string;
  drawing_sha256?: string;
  story_run_id?: string;
  run_input_revision?: number;
  understanding_revision?: number;
  candidate?: T;
  story?: T;
  story_sha256?: string;
  story_run?: ParentStoryRun;
}>;

export class ParentWorkflowApiError extends Error {
  constructor(
    readonly code: string,
    readonly requestId: string,
    readonly status?: number,
  ) {
    super(parentApiErrorMessage(code, requestId));
    this.name = 'ParentWorkflowApiError';
  }
}

export class ParentWorkflowApi {
  constructor(private readonly auth: AuthSessionPort) {}

  async getConsentPolicy(): Promise<{request_id: string; policy: ParentConsentPolicy}> {
    return this.request('/api/parent/v1/consent-policy', 'GET');
  }

  async listProfiles(): Promise<{request_id: string; profiles: ParentProfile[]}> {
    return this.request('/api/parent/v1/child-profiles', 'GET');
  }

  async createProfile(input: {
    age_months: number;
    display_name: string;
    interests_summary: string;
    consent_accepted: true;
    consent_policy_version: string;
  }): Promise<{request_id: string; profile: ParentProfile}> {
    return this.request('/api/parent/v1/child-profiles', 'POST', input);
  }

  async updateProfile(profile: ParentProfile, input: {
    age_months: number;
    display_name: string;
    interests_summary: string;
  }): Promise<{request_id: string; profile: ParentProfile}> {
    return this.request(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profile.parent_profile_id)}`,
      'PATCH',
      {...input, expected_revision: profile.current_revision.revision},
    );
  }

  async grantAuthorization(
    profileId: string,
    consentPolicyVersion: string,
  ): Promise<{request_id: string; profile: ParentProfile}> {
    return this.request(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}/data-authorizations`,
      'POST',
      {consent_accepted: true, consent_policy_version: consentPolicyVersion},
    );
  }

  async revokeAuthorization(profileId: string): Promise<{request_id: string; profile: ParentProfile}> {
    return this.request(
      `/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}/data-authorizations`,
      'DELETE',
    );
  }

  async archiveProfile(profileId: string): Promise<{request_id: string; profile: ParentProfile}> {
    return this.request(`/api/parent/v1/child-profiles/${encodeURIComponent(profileId)}`, 'DELETE');
  }

  async createStoryRun(input: {
    parent_profile_id: string;
    expected_profile_revision_id: string;
    consent_policy_version: string;
    topic: string;
    adult_confirmed_idea: string;
    context_confirmed: true;
  }): Promise<{request_id: string; story_run: ParentStoryRun}> {
    return this.request('/api/parent/v1/story-runs', 'POST', input);
  }

  async getStoryRun(runId: string): Promise<{request_id: string; story_run: ParentStoryRun}> {
    return this.request(`/api/parent/v1/story-runs/${encodeURIComponent(runId)}`, 'GET');
  }

  async getActiveStoryRun(): Promise<{request_id: string; story_run: ParentStoryRun | null}> {
    return this.request('/api/parent/v1/story-runs/active/current', 'GET');
  }

  async generateSketchGuide(input: {
    topic: string;
    difficulty: 'beginner';
    step_count: 3;
  }): Promise<ParentAiReceipt<never>> {
    return this.request('/api/parent/v1/ai/sketch-guides', 'POST', input, 910_000);
  }

  async analyzeDrawing(
    storyRunId: string,
    imageBase64: string,
    mediaType: 'image/jpeg' | 'image/png',
  ): Promise<ParentAiReceipt<ParentCandidate>> {
    return this.request(
      '/api/parent/v1/ai/drawing-understandings',
      'POST',
      {story_run_id: storyRunId, image_base64: imageBase64, media_type: mediaType},
      1_850_000,
    );
  }

  async confirmSubject(
    storyRunId: string,
    expectedUnderstandingRevision: number,
    confirmedSubject: string,
  ): Promise<{request_id: string; story_run_id: string; understanding_revision: number}> {
    return this.request(
      `/api/parent/v1/story-runs/${encodeURIComponent(storyRunId)}/subject-confirmations`,
      'POST',
      {
        expected_understanding_revision: expectedUnderstandingRevision,
        confirmed_subject: confirmedSubject,
      },
    );
  }

  async generateStory(
    storyRunId: string,
    expectedUnderstandingRevision: number,
    rewriteInstruction?: string,
  ): Promise<ParentAiReceipt<unknown>> {
    return this.request(
      `/api/parent/v1/ai/story-runs/${encodeURIComponent(storyRunId)}/story-revisions`,
      'POST',
      {
        expected_understanding_revision: expectedUnderstandingRevision,
        ...(rewriteInstruction ? {rewrite_instruction: rewriteInstruction} : {}),
      },
      1_850_000,
    );
  }

  async confirmStory(
    storyRunId: string,
    expectedRevision: number,
    storySha256: string,
  ): Promise<{request_id: string; story_run: ParentStoryRun}> {
    return this.request(
      `/api/parent/v1/story-runs/${encodeURIComponent(storyRunId)}/story-revision-confirmations`,
      'POST',
      {expected_revision: expectedRevision, story_sha256: storySha256},
    );
  }

  private async request<T>(
    path: string,
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE',
    body?: unknown,
    timeoutMs = 30_000,
  ): Promise<T> {
    const baseUrl = firebasePublicConfig.apiBaseUrl.trim().replace(/\/+$/, '');
    if (!baseUrl) throw new Error('Thiếu SKETCH2LIFE_MOBILE_API_BASE_URL trong .env gốc.');
    const requestId = createRequestId();
    const controller = new AbortController();
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);
    try {
      const response = await fetch(`${baseUrl}${path}`, {
        method,
        headers: {
          Authorization: `Bearer ${await this.auth.getIdToken()}`,
          Accept: 'application/json',
          ...(body === undefined ? {} : {'Content-Type': 'application/json'}),
          'X-Request-ID': requestId,
        },
        ...(body === undefined ? {} : {body: JSON.stringify(body)}),
        signal: controller.signal,
      });
      const payload = await response.json().catch(() => null) as Record<string, unknown> | null;
      if (!response.ok) {
        const detail = isRecord(payload?.detail) ? payload.detail : null;
        const code = readString(detail, 'code') ?? `HTTP_${response.status}`;
        throw new ParentWorkflowApiError(code, readString(detail, 'request_id') ?? requestId, response.status);
      }
      if (!payload || typeof payload !== 'object') {
        throw new Error('Backend trả về contract không hợp lệ.');
      }
      return payload as T;
    } catch (cause) {
      if (cause instanceof ParentWorkflowApiError) throw cause;
      if (timedOut || (isRecord(cause) && cause.name === 'AbortError')) {
        throw new ParentWorkflowApiError('REQUEST_OUTCOME_UNKNOWN', requestId);
      }
      if (cause instanceof TypeError) {
        throw new ParentWorkflowApiError('NETWORK_UNAVAILABLE', requestId);
      }
      throw cause;
    } finally {
      clearTimeout(timeout);
    }
  }
}

function parentApiErrorMessage(code: string, requestId: string): string {
  const message = code === 'DRAWING_IMAGE_INVALID'
    ? 'Ảnh không đọc được hoặc vượt giới hạn. Hãy chụp lại tranh rõ hơn.'
    : code === 'DRAWING_IMAGE_TYPE_NOT_ALLOWED'
      ? 'Chỉ hỗ trợ ảnh JPG hoặc PNG. Hãy chọn ảnh khác.'
      : code === 'PARENT_CONSENT_POLICY_UNAVAILABLE'
        ? 'Chưa cấu hình nội dung và phiên bản đồng ý xử lý dữ liệu trong .env gốc.'
        : code === 'PARENT_DATA_AUTHORIZATION_REQUIRED' || code === 'PARENT_CONSENT_REQUIRED'
          ? 'Cần xác nhận quyền xử lý dữ liệu cho hồ sơ này trước khi bắt đầu.'
          : code === 'PARENT_ACTIVE_STORY_RUN_EXISTS'
            ? 'Bạn đang có một buổi tạo kịch bản chưa hoàn tất. Mở lại buổi đó để tiếp tục.'
            : code === 'MODAL_OUTCOME_UNKNOWN' || code === 'REQUEST_OUTCOME_UNKNOWN'
              ? 'Hết thời gian chờ. Yêu cầu có thể vẫn đang xử lý; không gửi lại ngay.'
              : code === 'MODAL_AI_NOT_ENABLED'
                ? 'Dịch vụ AI hiện chưa sẵn sàng.'
                : code === 'MODAL_MODEL_OUTPUT_INVALID' || code === 'DRAWING_WORKER_FAILED_TERMINAL'
                  ? 'AI không tạo được kết quả hợp lệ lần này.'
                  : code === 'NETWORK_UNAVAILABLE'
                    ? 'Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.'
                    : 'Yêu cầu chưa hoàn thành.';
  return `${message} (${code}) · Mã yêu cầu: ${requestId}`;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function readString(value: Record<string, unknown> | null, key: string): string | null {
  const candidate = value?.[key];
  return typeof candidate === 'string' && candidate.length > 0 ? candidate : null;
}

function createRequestId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}
