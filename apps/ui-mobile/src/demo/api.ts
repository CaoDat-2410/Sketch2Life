import * as Crypto from 'expo-crypto';

export const DEMO_ACTOR_REF = 'demo:local';
export const MAX_IMAGE_BYTES = 5_000_000;

export type AuthTokenProvider = () => Promise<string | null>;

export interface WorkflowResult<T = Record<string, unknown>> {
  contract_name: 'MobileWorkflowResultV1';
  contract_version: '1.0';
  status: 'ACCEPTED' | 'SUCCEEDED' | 'BLOCKED' | 'FAILED';
  request_id: string;
  session_id: string;
  expected_session_version: number;
  observed_session_version: number;
  payload: T | null;
  failure?: {
    code: string;
    retryable: boolean;
    safe_message: string;
  } | null;
}

export interface P1ContextOption {
  contract_name: 'P1ContextOptionV1';
  contract_version: '1.0';
  template_ref: { id: string; version: number };
  activity_ref: { id: string; version: number };
  age_months_min: number;
  age_months_max: number;
  readiness_ids: string[];
  prerequisite_activity_ids: string[];
  material_option_ids: string[];
  minimum_supervision: 'NONE' | 'NEARBY' | 'DIRECT';
  policy_constraints: string[];
}

export interface P1ContextOptions {
  contract_name: 'P1ContextOptionsV1';
  contract_version: '1.0';
  session_id: string;
  expected_session_version: number;
  age_months: number;
  confirmed_anchor_label: string;
  options: P1ContextOption[];
}

export class DemoApiError extends Error {
  readonly code: string;
  readonly statusCode: number;
  readonly retryable: boolean;

  constructor(message: string, code: string, statusCode: number, retryable = false) {
    super(message);
    this.name = 'DemoApiError';
    this.code = code;
    this.statusCode = statusCode;
    this.retryable = retryable;
  }
}

const defaultApiUrl = 'http://10.0.2.2:8000';
const configuredApiUrl = process.env.EXPO_PUBLIC_API_URL || defaultApiUrl;
export const API_BASE_URL = configuredApiUrl.replace(/\/+$/, '');

function newId(prefix: string): string {
  return `${prefix}-${Crypto.randomUUID()}`;
}

function toError(value: unknown, statusCode: number): DemoApiError {
  if (typeof value === 'object' && value !== null) {
    const body = value as {
      failure?: { code?: unknown; safe_message?: unknown; retryable?: unknown };
    };
    if (body.failure && typeof body.failure === 'object') {
      return new DemoApiError(
        typeof body.failure.safe_message === 'string'
          ? body.failure.safe_message
          : 'Backend rejected the request.',
        typeof body.failure.code === 'string' ? body.failure.code : 'REQUEST_FAILED',
        statusCode,
        body.failure.retryable === true,
      );
    }
  }
  return new DemoApiError('Backend returned an unreadable response.', 'INVALID_RESPONSE', statusCode);
}

export class DemoApiClient {
  readonly baseUrl: string;
  private readonly getAuthToken?: AuthTokenProvider;

  constructor(baseUrl = API_BASE_URL, getAuthToken?: AuthTokenProvider) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
    this.getAuthToken = getAuthToken;
  }

  async createSession(): Promise<WorkflowResult<Record<string, unknown>>> {
    const sessionId = Crypto.randomUUID();
    const requestId = newId('req');
    return this.jsonRequest('/v1/sessions', {
      request_id: requestId,
      idempotency_key: newId('idem'),
      session_id: sessionId,
      expected_session_version: 0,
      actor_ref: DEMO_ACTOR_REF,
      payload: { operation: 'CREATE_SESSION' },
    }, 30_000, 'POST');
  }

  async uploadImage(
    sessionId: string,
    version: number,
    image: { uri: string; fileName: string; mimeType: string },
  ): Promise<WorkflowResult<Record<string, unknown>>> {
    const form = new FormData();
    form.append('image', {
      uri: image.uri,
      name: image.fileName,
      type: image.mimeType,
    } as unknown as Blob);
    const requestId = newId('req');
    return this.request(`/v1/sessions/${encodeURIComponent(sessionId)}/media/image`, {
      method: 'POST',
      headers: {
        ...this.metaHeaders(version, requestId, newId('idem')),
        'X-Synthetic-Non-Child-Confirmed': 'true',
      },
      body: form,
    }, 30_000);
  }

  runUnderstanding(sessionId: string, version: number) {
    return this.command(sessionId, version, 'POST', '/understanding', {
      operation: 'RUN_UNDERSTANDING',
      user_initiated: true,
    }, 150_000);
  }

  confirmGateA(
    sessionId: string,
    version: number,
    claimIds: string[],
    primaryAnchorId: string,
    correction: string | null,
  ) {
    return this.command(sessionId, version, 'POST', '/gate-a/confirm', {
      operation: 'CONFIRM_GATE_A',
      user_initiated: true,
      primary_anchor_id: primaryAnchorId,
      confirmation: {
        contract_name: 'GateAConfirmationV1',
        contract_version: '1.0',
        meaning_version: 1,
        confirmed_claim_ids: claimIds,
        correction,
      },
    });
  }

  async readContextOptions(sessionId: string, version: number, ageMonths: number) {
    const requestId = newId('req');
    return this.request<WorkflowResult<P1ContextOptions>>(
      `/v1/sessions/${encodeURIComponent(sessionId)}/p1/context-options?age_months=${ageMonths}`,
      {
        method: 'GET',
        headers: this.metaHeaders(version, requestId),
      },
      30_000,
    );
  }

  setP1Context(sessionId: string, version: number, context: Record<string, unknown>) {
    return this.command(sessionId, version, 'PUT', '/p1-context', {
      operation: 'SET_P1_CONTEXT',
      user_initiated: true,
      context: {
        contract_name: 'P1ContextV1',
        contract_version: '1.0',
        session_id: sessionId,
        expected_session_version: version,
        gate_a_confirmed: true,
        ...context,
      },
    });
  }

  runP1Filter(sessionId: string, version: number) {
    return this.command(sessionId, version, 'POST', '/p1-filter', {
      operation: 'RUN_P1_FILTER',
      user_initiated: true,
    });
  }

  prepareExperience(sessionId: string, version: number) {
    return this.command(sessionId, version, 'POST', '/experience/prepare', {
      operation: 'PREPARE_EXPERIENCE',
      user_initiated: true,
    });
  }

  approveGateB(sessionId: string, version: number) {
    return this.command(sessionId, version, 'POST', '/gate-b/approve', {
      operation: 'APPROVE_GATE_B',
      user_initiated: true,
      approved: true,
    });
  }

  prepareRenderer(sessionId: string, version: number) {
    return this.command(sessionId, version, 'POST', '/renderer/launch', {
      operation: 'PREPARE_RENDERER',
      user_initiated: true,
    });
  }

  completeHandoff(sessionId: string, version: number) {
    return this.command(sessionId, version, 'POST', '/handoff', {
      operation: 'COMPLETE_HANDOFF',
      user_initiated: true,
    });
  }

  requestRetake(sessionId: string, version: number) {
    return this.command(sessionId, version, 'POST', '/media/retake', {
      operation: 'REQUEST_RETAKE',
      user_initiated: true,
    });
  }

  recordFeedback(
    sessionId: string,
    version: number,
    completionStatus: 'COMPLETED' | 'PARTIAL' | 'NOT_ATTEMPTED',
    interestScore: number | null,
    independenceScore: number | null,
  ) {
    return this.command(sessionId, version, 'POST', '/feedback', {
      operation: 'RECORD_FEEDBACK',
      user_initiated: true,
      feedback: {
        completion_status: completionStatus,
        interest_score: interestScore,
        independence_score: independenceScore,
        observation_tags: [],
      },
    });
  }

  async readGallery(sessionId: string, version: number) {
    const requestId = newId('req');
    return this.request<WorkflowResult<Record<string, unknown>>>(
      `/v1/sessions/${encodeURIComponent(sessionId)}/gallery`,
      {
        method: 'GET',
        headers: this.metaHeaders(version, requestId, newId('idem')),
      },
      30_000,
    );
  }

  async refreshSession(sessionId: string, version: number) {
    const requestId = newId('req');
    return this.request<WorkflowResult<Record<string, unknown>>>(
      `/v1/sessions/${encodeURIComponent(sessionId)}`,
      {
        method: 'GET',
        headers: this.metaHeaders(version, requestId, newId('idem')),
      },
      30_000,
    );
  }

  private command(
    sessionId: string,
    version: number,
    method: 'POST' | 'PUT',
    suffix: string,
    payload: Record<string, unknown>,
    timeoutMs = 30_000,
  ) {
    return this.jsonRequest(
      `/v1/sessions/${encodeURIComponent(sessionId)}${suffix}`,
      {
        request_id: newId('req'),
        idempotency_key: newId('idem'),
        session_id: sessionId,
        expected_session_version: version,
        actor_ref: DEMO_ACTOR_REF,
        payload,
      },
      timeoutMs,
      method,
    );
  }

  private jsonRequest<T = WorkflowResult<Record<string, unknown>>>(
    path: string,
    body: Record<string, unknown>,
    timeoutMs: number,
    method: 'POST' | 'PUT',
  ) {
    return this.request<T>(path, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }, timeoutMs);
  }

  private metaHeaders(
    version: number,
    requestId: string,
    idempotencyKey?: string,
  ): Record<string, string> {
    return {
      'X-Request-ID': requestId,
      'X-Expected-Session-Version': String(version),
      'X-Actor-Ref': DEMO_ACTOR_REF,
      ...(idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {}),
    };
  }

  private async request<T>(path: string, init: RequestInit, timeoutMs: number): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    const headers = new Headers(init.headers);
    try {
      if (this.getAuthToken) {
        const token = await this.getAuthToken();
        if (token) headers.set('Authorization', `Bearer ${token}`);
      }
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers,
        signal: controller.signal,
      });
      const body: unknown = await response.json().catch(() => null);
      if (!response.ok || (typeof body === 'object' && body !== null && 'status' in body && body.status === 'FAILED')) {
        throw toError(body, response.status);
      }
      return body as T;
    } catch (error) {
      if (error instanceof DemoApiError) throw error;
      if (error instanceof Error && error.name === 'AbortError') {
        throw new DemoApiError(
          'Request timed out. No automatic retry was sent; tap the action again only if you choose.',
          'REQUEST_TIMEOUT',
          408,
          true,
        );
      }
      throw new DemoApiError(
        'Could not reach the backend. Check the API address and server, then retry explicitly.',
        'NETWORK_ERROR',
        0,
        true,
      );
    } finally {
      clearTimeout(timer);
    }
  }
}

export function createDemoApi(tokenProvider?: AuthTokenProvider): DemoApiClient {
  return new DemoApiClient(API_BASE_URL, tokenProvider);
}
