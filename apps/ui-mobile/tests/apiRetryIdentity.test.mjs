import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { randomUUID } = vi.hoisted(() => ({ randomUUID: vi.fn() }));
vi.mock('expo-crypto', () => ({ randomUUID }));

import { DemoApiClient } from '../src/demo/api.ts';

describe('DemoApiClient retry identity', () => {
  let fetchMock;
  let id = 0;

  beforeEach(() => {
    id = 0;
    randomUUID.mockImplementation(() => `uuid-${++id}`);
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
  });

  it('replays an identical command with the same key after the response is lost', async () => {
    fetchMock
      .mockRejectedValueOnce(new TypeError('socket closed'))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'SUCCEEDED' }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'SUCCEEDED' }), { status: 200 }));
    const client = new DemoApiClient('http://localhost:8000');

    await expect(client.runUnderstanding('session-a', 3)).rejects.toMatchObject({ code: 'NETWORK_ERROR' });
    await client.runUnderstanding('session-a', 3);
    await client.runUnderstanding('session-a', 4);

    const first = JSON.parse(fetchMock.mock.calls[0][1].body);
    const retry = JSON.parse(fetchMock.mock.calls[1][1].body);
    const nextAction = JSON.parse(fetchMock.mock.calls[2][1].body);
    expect(retry.idempotency_key).toBe(first.idempotency_key);
    expect(retry.session_id).toBe(first.session_id);
    expect(retry.request_id).not.toBe(first.request_id);
    expect(nextAction.idempotency_key).not.toBe(retry.idempotency_key);
  });

  it('reuses the created session identity after an ambiguous response', async () => {
    fetchMock
      .mockRejectedValueOnce(new TypeError('socket closed'))
      .mockResolvedValueOnce(new Response(JSON.stringify({ session_id: 'session-a' }), { status: 201 }));
    const client = new DemoApiClient('http://localhost:8000');

    await expect(client.createSession()).rejects.toMatchObject({ code: 'NETWORK_ERROR' });
    await client.createSession();

    const first = JSON.parse(fetchMock.mock.calls[0][1].body);
    const retry = JSON.parse(fetchMock.mock.calls[1][1].body);
    expect(retry.idempotency_key).toBe(first.idempotency_key);
    expect(retry.session_id).toBe(first.session_id);
  });

  it('uses a fresh key after a definitive rejection', async () => {
    const rejection = new Response(JSON.stringify({ failure: {
      code: 'INVALID_COMMAND', safe_message: 'Not accepted.', retryable: false,
    } }), { status: 422 });
    fetchMock
      .mockResolvedValueOnce(rejection)
      .mockResolvedValueOnce(new Response(JSON.stringify({ status: 'SUCCEEDED' }), { status: 200 }));
    const client = new DemoApiClient('http://localhost:8000');

    await expect(client.runUnderstanding('session-a', 3)).rejects.toMatchObject({ code: 'INVALID_COMMAND' });
    await client.runUnderstanding('session-a', 3);

    const first = JSON.parse(fetchMock.mock.calls[0][1].body);
    const next = JSON.parse(fetchMock.mock.calls[1][1].body);
    expect(next.idempotency_key).not.toBe(first.idempotency_key);
  });
});
