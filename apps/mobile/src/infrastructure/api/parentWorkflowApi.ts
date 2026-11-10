import {firebasePublicConfig} from '../auth/firebasePublicConfig';
import type {AuthSessionPort} from '../auth/AuthSessionPort';

export type ParentCandidate = Readonly<{
  candidate_subject?: string;
  visible_features?: string[];
  confidence?: number;
  adult_confirmation_required: true;
  decision: string;
}>;

export type ParentAiReceipt<T> = Readonly<{
  request_id: string;
  modal_call_id: string;
  model?: {id: string; revision: string};
  review_required?: boolean;
  image_base64?: string;
  drawing_sha256?: string;
  candidate?: ParentCandidate;
  story?: T;
}>;

export class ParentWorkflowApi {
  constructor(private readonly auth: AuthSessionPort) {}

  async generateSketchGuide(input: {
    topic: string;
    difficulty: 'beginner';
    step_count: 3;
  }): Promise<ParentAiReceipt<never>> {
    return this.post('/api/parent/v1/ai/sketch-guides', input, 910_000);
  }

  async analyzeDrawing(imageBase64: string): Promise<ParentAiReceipt<never>> {
    return this.post(
      '/api/parent/v1/ai/drawing-understandings',
      {image_base64: imageBase64},
      1_850_000,
    );
  }

  async generateStory(input: {
    confirmed_subject: string;
    visible_features: string[];
    child_age_months: number;
    drawing_sha256: string;
    understanding_revision: number;
    context_revision: number;
    adult_confirmed_idea: string;
  }): Promise<ParentAiReceipt<Record<string, unknown>>> {
    return this.post('/api/parent/v1/ai/storyboards', input, 1_850_000);
  }

  private async post<T>(path: string, body: unknown, timeoutMs: number): Promise<T> {
    const baseUrl = firebasePublicConfig.apiBaseUrl.trim().replace(/\/+$/, '');
    if (!baseUrl) throw new Error('Thiếu SKETCH2LIFE_MOBILE_API_BASE_URL trong .env gốc.');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(`${baseUrl}${path}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${await this.auth.getIdToken()}`,
          Accept: 'application/json',
          'Content-Type': 'application/json',
          'X-Request-ID': createRequestId(),
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      const payload = await response.json().catch(() => null) as Record<string, unknown> | null;
      if (!response.ok) {
        const detail = payload?.detail;
        const code = detail && typeof detail === 'object' && 'code' in detail
          ? String((detail as {code: unknown}).code)
          : `HTTP_${response.status}`;
        throw new Error(`Yêu cầu AI thất bại (${code}).`);
      }
      if (!payload || typeof payload !== 'object') {
        throw new Error('Backend trả về contract không hợp lệ.');
      }
      return payload as T;
    } finally {
      clearTimeout(timeout);
    }
  }
}

function createRequestId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`;
}
