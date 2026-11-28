import { describe, expect, it, vi } from 'vitest';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://parent.example.test' },
}));

type Call = { url: string; init: RequestInit };
const PROFILE_ID = '00000000-0000-4000-8000-000000000002';
const GRANT_ID = '00000000-0000-4000-8000-000000000001';

function reply(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}

function grant(overrides: Record<string, unknown> = {}) {
  return {
    contract: 'ParentShareGrantV1',
    share_grant_id: GRANT_ID,
    profile_id: PROFILE_ID,
    state: 'INVITED',
    granted_fields: ['DISPLAY_NAME'],
    created_at: '2026-11-25T00:00:00Z',
    invitation_expires_at: '2027-02-23T00:00:00Z',
    accepted_at: null,
    expires_at: null,
    revoked_at: null,
    revision: 1,
    ...overrides,
  };
}

function apiWith(replies: Response[]) {
  const calls: Call[] = [];
  const queue = [...replies];
  const fetcher = vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return queue.shift() ?? reply(500, {});
  }) as unknown as typeof fetch;
  const api = new ParentApi({ getIdToken: vi.fn(async () => 'parent-token') }, fetcher, 'https://parent.example.test');
  return { api, calls };
}

function headerOf(call: Call, name: string): string | null {
  return new Headers(call.init.headers).get(name);
}

describe('Phase E Parent profile share grants', () => {
  it('creates, pages, reads, revokes with strong If-Match, and lists deliveries', async () => {
    const created = { ...grant(), invitation_code: 'one_time_code_12345678' };
    const page = { contract: 'ParentShareGrantListV1', items: [grant()], next_cursor: 'next-page' };
    const detail = grant({ state: 'ACTIVE', accepted_at: '2026-11-25T01:00:00Z', expires_at: '2027-02-23T01:00:00Z', revision: 4 });
    const revoked = grant({ state: 'REVOKED', revoked_at: '2026-11-25T02:00:00Z', revision: 5 });
    const deliveries = {
      contract: 'ParentShareDeliveryListV1',
      share_grant_id: GRANT_ID,
      content_access: 'ENDED',
      items: [{ delivered_at: '2026-11-24T00:00:00Z', title: null }],
      next_cursor: null,
    };
    const { api, calls } = apiWith([
      reply(201, created), reply(200, page), reply(200, detail), reply(200, revoked), reply(200, deliveries),
    ]);

    const result = await api.createProfileShare(PROFILE_ID, ['DISPLAY_NAME'], 'create-key-1');
    expect(result.invitation_code).toBe('one_time_code_12345678');
    await api.listProfileShares(PROFILE_ID, 25, 'next-page');
    await api.getProfileShare(GRANT_ID);
    await api.revokeProfileShare(GRANT_ID, 4, 'revoke-key-1');
    const deliveryPage = await api.listProfileShareDeliveries(GRANT_ID, 25, 'opaque+cursor');

    expect(calls[0].url).toBe('https://parent.example.test/v1/parent/share-grants');
    expect(calls[0].init.method).toBe('POST');
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ profile_id: PROFILE_ID, granted_fields: ['DISPLAY_NAME'] });
    expect(headerOf(calls[0], 'Idempotency-Key')).toBe('create-key-1');
    expect(calls[1].url).toBe(`https://parent.example.test/v1/parent/share-grants?profile_id=${PROFILE_ID}&limit=25&cursor=next-page`);
    expect(calls[2].url).toBe(`https://parent.example.test/v1/parent/share-grants/${GRANT_ID}`);
    expect(calls[3].url).toBe(`https://parent.example.test/v1/parent/share-grants/${GRANT_ID}/revoke`);
    expect(calls[3].init.method).toBe('POST');
    expect(calls[3].init.body).toBeUndefined();
    expect(headerOf(calls[3], 'If-Match')).toBe('"4"');
    expect(headerOf(calls[3], 'Idempotency-Key')).toBe('revoke-key-1');
    expect(calls[4].url).toBe(`https://parent.example.test/v1/parent/share-grants/${GRANT_ID}/deliveries?limit=25&cursor=opaque%2Bcursor`);
    expect(deliveryPage.content_access).toBe('ENDED');
  });

  it('accepts a null invitation code on an idempotent replay and rejects malformed grant responses', async () => {
    const { api } = apiWith([
      reply(201, { ...grant(), invitation_code: null }),
      reply(200, { ...grant(), granted_fields: ['SUPPORT_NEEDS'] }),
    ]);
    await expect(api.createProfileShare(PROFILE_ID, ['DISPLAY_NAME'], 'create-key-1'))
      .resolves.toMatchObject({ invitation_code: null });
    const error = await api.getProfileShare(GRANT_ID).catch((failure: unknown) => failure);
    expect(error).toBeInstanceOf(ParentApiError);
    expect(error).toMatchObject({ code: 'INVALID_API_RESPONSE', status: 200 });
  });

  it('surfaces database unavailability as a typed safe error', async () => {
    const { api } = apiWith([reply(503, { code: 'DATABASE_UNAVAILABLE', message: 'do not display this body' })]);
    const error = await api.listProfileShares(PROFILE_ID).catch((failure: unknown) => failure);
    expect(error).toMatchObject({ code: 'DATABASE_UNAVAILABLE', status: 503 });
    expect((error as Error).message).not.toContain('do not display this body');
  });
});
