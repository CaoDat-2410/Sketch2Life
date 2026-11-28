import { describe, expect, it, vi } from 'vitest';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://parent.example.test' },
}));

function policyEnvelope(overrides: Record<string, unknown> = {}) {
  return {
    contract: 'ParentConsentPolicyV1',
    request_id: 'request-1',
    policy: {
      purpose_code: 'SYNTHETIC_TEST_ONLY',
      policy_version: 'parent-consent-placeholder-v0',
      consent_text: 'Văn bản chính sách do API trả về.',
      consent_text_sha256: 'a'.repeat(64),
      policy_state: 'PLACEHOLDER_NOT_APPROVED',
      data_origin_scope: 'SYNTHETIC_TEST',
      effective_from: null,
      purposes: [{ purpose_code: 'SYNTHETIC_TEST_ONLY', text_key: 'parent.consent.placeholder.synthetic_test_only' }],
      links: [],
      acceptance_recording: 'NOT_AVAILABLE',
    },
    ...overrides,
  };
}

function apiWith(status: number, body: unknown) {
  const fetcher = vi.fn(async () => new Response(JSON.stringify(body), { status })) as unknown as typeof fetch;
  const api = new ParentApi({ getIdToken: vi.fn(async () => 'parent-token') }, fetcher, 'https://parent.example.test');
  return { api, fetcher };
}

describe('Phase E Parent consent policy', () => {
  it('reads the policy from the exact route and preserves API text and version', async () => {
    const { api, fetcher } = apiWith(200, policyEnvelope());
    const response = await api.getConsentPolicy();

    expect(response.policy.consent_text).toBe('Văn bản chính sách do API trả về.');
    expect(response.policy.policy_version).toBe('parent-consent-placeholder-v0');
    expect(response.policy.policy_state).toBe('PLACEHOLDER_NOT_APPROVED');
    expect(fetcher).toHaveBeenCalledWith(
      'https://parent.example.test/v1/parent/consent-policy',
      expect.objectContaining({ method: 'GET' }),
    );
  });

  it('fails closed when required policy fields are missing', async () => {
    const invalid = policyEnvelope({ policy: { policy_version: 'bad' } });
    const { api } = apiWith(200, invalid);
    const error = await api.getConsentPolicy().catch((failure: unknown) => failure);
    expect(error).toBeInstanceOf(ParentApiError);
    expect(error).toMatchObject({ code: 'INVALID_API_RESPONSE', status: 200 });
  });

  it('preserves unavailable status without exposing a response body', async () => {
    const { api } = apiWith(503, { code: 'DATABASE_UNAVAILABLE', message: 'raw response body' });
    const error = await api.getConsentPolicy().catch((failure: unknown) => failure);
    expect(error).toMatchObject({ code: 'DATABASE_UNAVAILABLE', status: 503 });
    expect((error as Error).message).not.toContain('raw response body');
  });
});
