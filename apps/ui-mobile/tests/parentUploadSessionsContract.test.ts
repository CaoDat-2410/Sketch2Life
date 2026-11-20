import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/parent/infrastructure/config', () => ({ parentConfig: { apiBaseUrl: 'https://api.example.test' } }));

import type { AuthTokenPort } from '../src/parent/application/ports/ParentPorts';
import { ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import {
  GENERIC_UPLOAD_PART_MAX_BYTES,
  GenericUploadSessionsApi,
} from '../src/parent/infrastructure/http/GenericUploadSessionsApi';

type Call = { url: string; init: RequestInit };

const SHA_A = 'a'.repeat(64);
const SHA_B = 'b'.repeat(64);
const session = {
  contract: 'GenericUploadSessionV1',
  upload_id: 'upl-1',
  purpose: 'RUN_ARTWORK',
  target_ref: 'run-1',
  state: 'OPEN',
  part_size_bytes: GENERIC_UPLOAD_PART_MAX_BYTES,
  expected_parts: 1,
  accepted_parts: [],
  byte_count: 0,
  expires_at: '2026-11-20T01:00:00Z',
  revision: 3,
  asset_ref: null,
  asset_state: null,
  error_code: null,
};

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(headers),
    json: async () => body,
  } as Response;
}

function client(reply: () => Response = () => jsonResponse(200, session, { ETag: '"3"' })) {
  const calls: Call[] = [];
  const auth: AuthTokenPort = { getIdToken: vi.fn(async () => 'test-token') };
  const fetcher = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    calls.push({ url: String(input), init });
    return reply();
  }) as unknown as typeof fetch;
  return { api: new GenericUploadSessionsApi(auth, fetcher, 'https://api.example.test/'), calls, fetcher };
}

const header = (call: Call, name: string) => new Headers(call.init.headers).get(name);

describe('generic upload session adapter', () => {
  it('creates a session with the caller key and the exact request body', async () => {
    const { api, calls } = client();
    const input = {
      purpose: 'RUN_ARTWORK' as const, target_ref: 'run-1', media_type: 'image/png',
      expected_size_bytes: 3, expected_sha256: SHA_A, file_name: 'drawing.png',
    };
    const created = await api.create(input, 'create-action-1');

    expect(created.upload_id).toBe('upl-1');
    expect(calls).toHaveLength(1);
    expect(calls[0].init.method).toBe('POST');
    expect(new URL(calls[0].url).pathname).toBe('/v1/upload-sessions');
    expect(header(calls[0], 'Idempotency-Key')).toBe('create-action-1');
    expect(header(calls[0], 'Authorization')).toBe('Bearer test-token');
    expect(header(calls[0], 'Content-Type')).toBe('application/json');
    expect(header(calls[0], 'X-Request-ID')).toMatch(/^parent-[0-9a-z]+-[0-9a-z]{12}$/);
    expect(JSON.parse(String(calls[0].init.body))).toEqual(input);
  });

  it.each(['RUN_ARTWORK', 'RUN_AUDIO'] as const)('sends purpose %s and leaves the decision to the server', async (purpose) => {
    const { api, calls } = client();
    await api.create({ purpose, target_ref: 'run-1', media_type: 'image/png', expected_size_bytes: 1, expected_sha256: SHA_A }, 'k');
    expect(JSON.parse(String(calls[0].init.body)).purpose).toBe(purpose);
  });

  it('refuses invalid idempotency keys before any request', async () => {
    const { api, calls } = client();
    const input = { purpose: 'RUN_ARTWORK' as const, target_ref: 'run-1', media_type: 'image/png', expected_size_bytes: 1, expected_sha256: SHA_A };
    const done = { expected_size_bytes: 1, expected_sha256: SHA_A };
    for (const key of ['', 'key with space', 'x'.repeat(129), 'clé-é']) {
      await expect(api.create(input, key)).rejects.toMatchObject({ code: 'IDEMPOTENCY_KEY_INVALID' });
      await expect(api.complete('upl-1', done, key)).rejects.toMatchObject({ code: 'IDEMPOTENCY_KEY_INVALID' });
      await expect(api.abort('upl-1', 3, key)).rejects.toMatchObject({ code: 'IDEMPOTENCY_KEY_INVALID' });
    }
    await expect(api.create(input, 'x'.repeat(128))).resolves.toBeDefined();
    expect(calls).toHaveLength(1);
  });

  it('refuses malformed create input locally', async () => {
    const { api, calls } = client();
    const base = { purpose: 'RUN_ARTWORK' as const, target_ref: 'run-1', media_type: 'image/png', expected_size_bytes: 1, expected_sha256: SHA_A };
    await expect(api.create({ ...base, target_ref: 'run/1' }, 'k')).rejects.toMatchObject({ code: 'INVALID_UPLOAD_TARGET' });
    await expect(api.create({ ...base, expected_size_bytes: 0 }, 'k')).rejects.toMatchObject({ code: 'INVALID_UPLOAD_SIZE' });
    await expect(api.create({ ...base, expected_sha256: SHA_A.toUpperCase() }, 'k')).rejects.toMatchObject({ code: 'INVALID_UPLOAD_HASH' });
    await expect(api.create({ ...base, media_type: '' }, 'k')).rejects.toMatchObject({ code: 'INVALID_UPLOAD_MEDIA_TYPE' });
    expect(calls).toHaveLength(0);
  });

  it('reads a session and rejects an upload id outside the opaque alphabet', async () => {
    const { api, calls } = client();
    await api.get('upl-1');
    expect(calls[0].init.method).toBe('GET');
    expect(new URL(calls[0].url).pathname).toBe('/v1/upload-sessions/upl-1');
    expect(calls[0].init.body).toBeUndefined();
    await expect(api.get('../jobs/x')).rejects.toMatchObject({ code: 'INVALID_UPLOAD_ID' });
    await expect(api.get('')).rejects.toMatchObject({ code: 'INVALID_UPLOAD_ID' });
    expect(calls).toHaveLength(1);
  });

  it('sends a raw part with the part hash, no Content-Range and no JSON content type', async () => {
    const { api, calls } = client(() => jsonResponse(200, { contract: 'GenericUploadPartReceiptV1', upload_id: 'upl-1', part_no: 2, byte_length: 3, sha256: SHA_B, accepted: true, accepted_part_count: 1, byte_count: 3, revision: 4 }));
    const receipt = await api.putPart('upl-1', 2, new Uint8Array([1, 2, 3]), SHA_B);

    expect(receipt.accepted).toBe(true);
    expect(calls[0].init.method).toBe('PUT');
    expect(new URL(calls[0].url).pathname).toBe('/v1/upload-sessions/upl-1/parts/2');
    expect(header(calls[0], 'Content-Type')).toBe('application/octet-stream');
    expect(header(calls[0], 'X-Part-SHA256')).toBe(SHA_B);
    expect(header(calls[0], 'Content-Range')).toBeNull();
    expect(header(calls[0], 'Idempotency-Key')).toBeNull();
    expect(Array.from(new Uint8Array(calls[0].init.body as ArrayBuffer))).toEqual([1, 2, 3]);
  });

  it('sends only the bytes of a sub-array view, not its whole backing buffer', async () => {
    const { api, calls } = client();
    const backing = new Uint8Array([9, 9, 1, 2, 3, 9]);
    await api.putPart('upl-1', 1, backing.subarray(2, 5), SHA_B);
    const sent = calls[0].init.body as ArrayBuffer;
    expect(sent.byteLength).toBe(3);
    expect(Array.from(new Uint8Array(sent))).toEqual([1, 2, 3]);
  });

  it('enforces the 4 MiB part limit, an empty part, the lowercase hash and the part number', async () => {
    const { api, calls } = client();
    await api.putPart('upl-1', 1, new Uint8Array(GENERIC_UPLOAD_PART_MAX_BYTES), SHA_B);
    expect(calls).toHaveLength(1);
    await expect(api.putPart('upl-1', 2, new Uint8Array(GENERIC_UPLOAD_PART_MAX_BYTES + 1), SHA_B)).rejects.toMatchObject({ code: 'INVALID_UPLOAD_PART_SIZE', status: 413 });
    await expect(api.putPart('upl-1', 2, new Uint8Array(0), SHA_B)).rejects.toMatchObject({ code: 'INVALID_UPLOAD_PART_SIZE' });
    await expect(api.putPart('upl-1', 2, new Uint8Array(1), SHA_B.toUpperCase())).rejects.toMatchObject({ code: 'INVALID_UPLOAD_PART_HASH' });
    await expect(api.putPart('upl-1', 0, new Uint8Array(1), SHA_B)).rejects.toMatchObject({ code: 'INVALID_UPLOAD_PART' });
    await expect(api.putPart('upl-1', 1.5, new Uint8Array(1), SHA_B)).rejects.toMatchObject({ code: 'INVALID_UPLOAD_PART' });
    expect(calls).toHaveLength(1);
  });

  it('completes with a key and only the size and hash', async () => {
    const { api, calls } = client(() => jsonResponse(202, { ...session, contract: 'GenericUploadCompletionV1', state: 'COMPLETED', asset_ref: 'upl_upl-1', asset_state: 'READY', scanner_name: 'clamav', scanner_version: '1' }));
    const done = await api.complete('upl-1', { expected_size_bytes: 8, expected_sha256: SHA_A }, 'complete-action');

    expect(done.asset_ref).toBe('upl_upl-1');
    expect(calls[0].init.method).toBe('POST');
    expect(new URL(calls[0].url).pathname).toBe('/v1/upload-sessions/upl-1/complete');
    expect(header(calls[0], 'Idempotency-Key')).toBe('complete-action');
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ expected_size_bytes: 8, expected_sha256: SHA_A });
  });

  it('aborts with a key and the strong current revision in If-Match', async () => {
    const { api, calls } = client();
    await api.abort('upl-1', 3, 'abort-action');
    expect(calls[0].init.method).toBe('DELETE');
    expect(new URL(calls[0].url).pathname).toBe('/v1/upload-sessions/upl-1');
    expect(header(calls[0], 'Idempotency-Key')).toBe('abort-action');
    expect(header(calls[0], 'If-Match')).toBe('"3"');
    expect(calls[0].init.body).toBeUndefined();
    await expect(api.abort('upl-1', 0, 'abort-action')).rejects.toMatchObject({ code: 'INVALID_UPLOAD_REVISION' });
    await expect(api.abort('upl-1', 1.2, 'abort-action')).rejects.toMatchObject({ code: 'INVALID_UPLOAD_REVISION' });
    expect(calls).toHaveLength(1);
  });

  it('preserves the error envelope of a stale revision (detail form) without leaking the token', async () => {
    const { api } = client(() => jsonResponse(409, {
      detail: { code: 'STALE_REVISION', current_version: 5, request_id: 'req-9', correlation_id: 'corr-9', retryable: false },
    }, { ETag: '"5"' }));
    const error = await api.abort('upl-1', 3, 'abort-action').catch((cause: unknown) => cause) as ParentApiError;

    expect(error).toBeInstanceOf(ParentApiError);
    expect(error).toMatchObject({ code: 'STALE_REVISION', status: 409, requestId: 'req-9', correlationId: 'corr-9', currentVersion: 5, retryable: false });
    expect(JSON.stringify([error.message, error.code, error.requestId])).not.toContain('test-token');
  });

  it('preserves the top-level envelope, safe field errors and the request id header', async () => {
    const { api } = client(() => jsonResponse(400, {
      code: 'INVALID_REQUEST',
      field_errors: [{ field: 'If-Match', code: 'INVALID_FORMAT' }, { field: 'purpose', code: 'INVALID_FORMAT' }, { field: 'secret_column', code: 'INVALID_FORMAT' }],
    }, { 'X-Request-ID': 'server-req-1' }));
    const error = await api.abort('upl-1', 3, 'abort-action').catch((cause: unknown) => cause) as ParentApiError;

    expect(error).toMatchObject({ code: 'INVALID_REQUEST', status: 400, requestId: 'server-req-1' });
    expect(error.fieldErrors).toEqual([{ field: 'if_match', code: 'INVALID_FORMAT' }, { field: 'purpose', code: 'INVALID_FORMAT' }]);
  });

  it.each([
    [422, 'UPLOAD_CHECKSUM_MISMATCH'],
    [415, 'UNSUPPORTED_MEDIA_TYPE'],
    [413, 'MEDIA_TOO_LARGE'],
    [409, 'UPLOAD_SESSION_STATE_CONFLICT'],
    [503, 'STORAGE_UNAVAILABLE'],
  ])('keeps the server code for HTTP %i %s', async (status, code) => {
    const { api } = client(() => jsonResponse(status, { detail: { code } }));
    await expect(api.complete('upl-1', { expected_size_bytes: 1, expected_sha256: SHA_A }, 'k')).rejects.toMatchObject({ code, status });
  });

  it('falls back to HTTP_<status> and flags a body that is not a JSON object', async () => {
    const failing = client(() => jsonResponse(500, null));
    await expect(failing.api.get('upl-1')).rejects.toMatchObject({ code: 'HTTP_500', status: 500 });
    const listBody = client(() => jsonResponse(200, [1]));
    await expect(listBody.api.get('upl-1')).rejects.toMatchObject({ code: 'INVALID_API_RESPONSE' });
  });

  it('maps network failures, caller aborts and a missing base URL', async () => {
    const auth: AuthTokenPort = { getIdToken: vi.fn(async () => 'test-token') };
    const offline = new GenericUploadSessionsApi(auth, vi.fn(async () => { throw new TypeError('Network request failed'); }) as unknown as typeof fetch, 'https://api.example.test');
    await expect(offline.get('upl-1')).rejects.toMatchObject({ code: 'NETWORK_ERROR' });

    const hanging = vi.fn((_url: RequestInfo | URL, init: RequestInit = {}) => new Promise<Response>((_resolve, reject) => {
      init.signal?.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })));
    })) as unknown as typeof fetch;
    const controller = new AbortController();
    const pending = new GenericUploadSessionsApi(auth, hanging, 'https://api.example.test').get('upl-1', controller.signal);
    await vi.waitFor(() => expect(hanging).toHaveBeenCalled());
    controller.abort();
    await expect(pending).rejects.toMatchObject({ code: 'REQUEST_CANCELLED' });

    const noBase = new GenericUploadSessionsApi(auth, vi.fn() as unknown as typeof fetch, '');
    await expect(noBase.get('upl-1')).rejects.toMatchObject({ code: 'API_UNAVAILABLE' });
  });

  it('aborts a part upload on the caller signal and times it out after 120 seconds', async () => {
    const auth: AuthTokenPort = { getIdToken: vi.fn(async () => 'test-token') };
    const hanging = vi.fn((_url: RequestInfo | URL, init: RequestInit = {}) => new Promise<Response>((_resolve, reject) => {
      init.signal?.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })));
    })) as unknown as typeof fetch;
    const controller = new AbortController();
    const api = new GenericUploadSessionsApi(auth, hanging, 'https://api.example.test');
    const cancelled = api.putPart('upl-1', 1, new Uint8Array(1), SHA_B, controller.signal);
    await vi.waitFor(() => expect(hanging).toHaveBeenCalled());
    controller.abort();
    await expect(cancelled).rejects.toMatchObject({ code: 'REQUEST_CANCELLED' });

    vi.useFakeTimers();
    try {
      const pending = api.putPart('upl-1', 1, new Uint8Array(1), SHA_B);
      const assertion = expect(pending).rejects.toMatchObject({ code: 'REQUEST_TIMEOUT', status: 408 });
      await vi.advanceTimersByTimeAsync(119_000);
      await vi.advanceTimersByTimeAsync(1_500);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  it('times out a hanging request', async () => {
    vi.useFakeTimers();
    try {
      const auth: AuthTokenPort = { getIdToken: vi.fn(async () => 'test-token') };
      const hanging = vi.fn((_url: RequestInfo | URL, init: RequestInit = {}) => new Promise<Response>((_resolve, reject) => {
        init.signal?.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })));
      })) as unknown as typeof fetch;
      const pending = new GenericUploadSessionsApi(auth, hanging, 'https://api.example.test').get('upl-1');
      const assertion = expect(pending).rejects.toMatchObject({ code: 'REQUEST_TIMEOUT', status: 408 });
      await vi.advanceTimersByTimeAsync(30_001);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  it('keeps storage locations, credentials and logging out of the adapter code', () => {
    for (const file of ['GenericUploadSessionsApi.ts', 'JobStatusPoller.ts', 'ParentHttpTransport.ts']) {
      const source = readFileSync(new URL(`../src/parent/infrastructure/http/${file}`, import.meta.url), 'utf8');
      expect(source).not.toMatch(/amazonaws|s3:\/\/|presign|X-Amz|runpod|lightning|firebasestorage/i);
      expect(source).not.toMatch(/console\.|AsyncStorage|SecureStore/);
    }
  });
});
