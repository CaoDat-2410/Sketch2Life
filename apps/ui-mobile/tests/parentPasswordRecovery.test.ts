import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://parent.example.test' },
}));

import { ParentAuth, ParentAuthError } from '../src/parent/infrastructure/auth/ParentAuth';

const response = (body: unknown, status: number): Response => new Response(JSON.stringify(body), {
  status,
  headers: { 'Content-Type': 'application/json' },
});

describe('parent password recovery', () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    vi.stubGlobal('__DEV__', false);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('posts the trimmed address to the public backend endpoint', async () => {
    fetchMock.mockResolvedValue(response({ status: 'RECOVERY_REQUESTED' }, 202));

    await new ParentAuth().resetPassword('  parent@example.test  ');

    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('https://parent.example.test/api/auth/v1/password-recovery');
    expect(init.method).toBe('POST');
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' });
    expect(init.headers).not.toHaveProperty('Authorization');
    expect(JSON.parse(String(init.body))).toEqual({ email: 'parent@example.test' });
  });

  it('accepts only the neutral 202 recovery response', async () => {
    fetchMock.mockResolvedValue(response({ status: 'RECOVERY_REQUESTED' }, 202));
    await expect(new ParentAuth().resetPassword('parent@example.test')).resolves.toBeUndefined();

    fetchMock.mockResolvedValue(response({ status: 'EMAIL_NOT_FOUND' }, 202));
    await expect(new ParentAuth().resetPassword('parent@example.test'))
      .rejects.toMatchObject({ code: 'PASSWORD_RECOVERY_UNAVAILABLE' });
  });

  it('maps 429 to the retry-later message', async () => {
    fetchMock.mockResolvedValue(response({ detail: { code: 'RATE_LIMITED' } }, 429));

    await expect(new ParentAuth().resetPassword('parent@example.test')).rejects.toMatchObject({
      code: 'RATE_LIMITED',
      message: 'Thử lại sau ít phút.',
    });
  });

  it('maps 422 to the existing invalid-email error', async () => {
    fetchMock.mockResolvedValue(response({ detail: [{ msg: 'invalid' }] }, 422));

    await expect(new ParentAuth().resetPassword('parent@example.test')).rejects.toMatchObject({
      code: 'INVALID_EMAIL',
      message: 'Email chưa đúng định dạng.',
    });
  });

  it('maps network and server failures to neutral retry copy', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('network failed'));
    await expect(new ParentAuth().resetPassword('parent@example.test')).rejects.toMatchObject({
      code: 'PASSWORD_RECOVERY_UNAVAILABLE',
      message: 'Chưa gửi được yêu cầu, hãy thử lại sau.',
    });

    fetchMock.mockResolvedValue(response({ detail: 'server error' }, 503));
    await expect(new ParentAuth().resetPassword('parent@example.test')).rejects.toMatchObject({
      code: 'PASSWORD_RECOVERY_UNAVAILABLE',
      message: 'Chưa gửi được yêu cầu, hãy thử lại sau.',
    });
  });

  it('rejects invalid addresses without calling fetch', async () => {
    await expect(new ParentAuth().resetPassword('not-an-email')).rejects.toMatchObject({
      code: 'INVALID_EMAIL',
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('never includes the submitted address in an error message', async () => {
    const email = 'private-parent@example.test';
    fetchMock
      .mockResolvedValueOnce(response({ detail: { code: 'RATE_LIMITED', message: email } }, 429))
      .mockResolvedValueOnce(response({ detail: [{ msg: email }] }, 422))
      .mockRejectedValueOnce(new Error(email))
      .mockResolvedValueOnce(response({ status: email }, 202));

    for (let index = 0; index < 4; index += 1) {
      const error = await new ParentAuth().resetPassword(email).then(
        () => null,
        (rejected: unknown) => rejected as Error,
      );
      expect(error).toBeInstanceOf(ParentAuthError);
      expect(error?.message).not.toContain(email);
    }
  });
});
