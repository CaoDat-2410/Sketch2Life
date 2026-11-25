import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: {
    firebaseApiKey: 'synthetic-firebase-api-key',
    apiBaseUrl: 'https://parent.example.test',
  },
}));

import { ParentAuth, ParentAuthError } from '../src/parent/infrastructure/auth/ParentAuth';

const response = (body: unknown, status = 200): Response => new Response(JSON.stringify(body), {
  status,
  headers: { 'Content-Type': 'application/json' },
});

const firebaseSession = {
  localId: 'synthetic-parent-uid',
  idToken: 'synthetic-firebase-id-token',
  refreshToken: 'synthetic-firebase-refresh-token',
  expiresIn: '3600',
  email: 'adult@example.test',
};

const parentRoleUnavailable = (): Response => response({ detail: { code: 'ACCOUNT_SETUP_UNAVAILABLE' } }, 403);
const activeParentRole = (): Response => response({ role: 'parent', state: 'active', role_revision: 1 });

describe('Parent identity registration completion and recovery', () => {
  beforeEach(() => vi.stubGlobal('__DEV__', false));
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('completes a missing Parent identity once after email sign-in, without a request body', async () => {
    let meCalls = 0;
    let completionCalls = 0;
    let completionInit: RequestInit | undefined;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('accounts:signInWithPassword')) return response(firebaseSession);
      if (url.endsWith('/api/auth/v1/me')) {
        meCalls += 1;
        return meCalls === 1 ? parentRoleUnavailable() : activeParentRole();
      }
      if (url.endsWith('/api/auth/v1/registrations/complete')) {
        completionCalls += 1;
        completionInit = init;
        return activeParentRole();
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    const user = await new ParentAuth().signIn('adult@example.test', 'synthetic-password');

    expect(user).toMatchObject({ subject: 'synthetic-parent-uid', role: 'parent' });
    expect(completionCalls).toBe(1);
    expect(completionInit?.method).toBe('POST');
    expect(completionInit?.headers).toMatchObject({ Authorization: 'Bearer synthetic-firebase-id-token' });
    expect(completionInit).not.toHaveProperty('body');
    expect(meCalls).toBe(2);
  });

  it('completes a missing Parent identity once after Google sign-in', async () => {
    let meCalls = 0;
    let completionCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('accounts:signInWithIdp')) return response(firebaseSession);
      if (url.endsWith('/api/auth/v1/me')) {
        meCalls += 1;
        return meCalls === 1 ? parentRoleUnavailable() : activeParentRole();
      }
      if (url.endsWith('/api/auth/v1/registrations/complete')) {
        completionCalls += 1;
        expect(init?.method).toBe('POST');
        expect(init).not.toHaveProperty('body');
        expect(init?.headers).toMatchObject({ Authorization: 'Bearer synthetic-firebase-id-token' });
        return activeParentRole();
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    const user = await new ParentAuth().signInWithGoogle('synthetic-google-id-token');

    expect(user).toMatchObject({ subject: 'synthetic-parent-uid', role: 'parent' });
    expect(completionCalls).toBe(1);
    expect(meCalls).toBe(2);
  });

  it('does not call completion when the current-account check succeeds', async () => {
    let completionCalls = 0;
    let meCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('accounts:signInWithPassword')) return response(firebaseSession);
      if (url.endsWith('/api/auth/v1/me')) {
        meCalls += 1;
        return activeParentRole();
      }
      if (url.endsWith('/api/auth/v1/registrations/complete')) completionCalls += 1;
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    await new ParentAuth().signIn('adult@example.test', 'synthetic-password');

    expect(meCalls).toBe(1);
    expect(completionCalls).toBe(0);
  });

  it('keeps the existing generic sign-in message when completion is unavailable', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('accounts:signInWithPassword')) return response(firebaseSession);
      if (url.endsWith('/api/auth/v1/me')) return parentRoleUnavailable();
      if (url.endsWith('/api/auth/v1/registrations/complete')) {
        return response({ detail: { code: 'ACCOUNT_SETUP_UNAVAILABLE' } }, 503);
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(new ParentAuth().signIn('adult@example.test', 'synthetic-password'))
      .rejects.toMatchObject({
        code: 'ACCOUNT_SETUP_UNAVAILABLE',
        message: 'Tài khoản chưa được thiết lập quyền trong Sketch2Life. Hãy liên hệ quản trị viên.',
      } satisfies Partial<ParentAuthError>);
  });

  it('recovers a registration whose response was lost to a network error', async () => {
    let registrationCalls = 0;
    let meCalls = 0;
    let completionCalls = 0;
    let firebaseRequest: Record<string, unknown> | undefined;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/api/auth/v1/registrations')) {
        registrationCalls += 1;
        throw new Error('synthetic registration connection failure');
      }
      if (url.includes('accounts:signInWithPassword')) {
        firebaseRequest = JSON.parse(String(init?.body)) as Record<string, unknown>;
        return response(firebaseSession);
      }
      if (url.endsWith('/api/auth/v1/me')) {
        meCalls += 1;
        return meCalls === 1 ? parentRoleUnavailable() : activeParentRole();
      }
      if (url.endsWith('/api/auth/v1/registrations/complete')) {
        completionCalls += 1;
        expect(init).not.toHaveProperty('body');
        return activeParentRole();
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    const user = await new ParentAuth().signUp('adult@example.test', 'synthetic-password');

    expect(user.role).toBe('parent');
    expect(registrationCalls).toBe(1);
    expect(firebaseRequest).toMatchObject({ email: 'adult@example.test', password: 'synthetic-password' });
    expect(completionCalls).toBe(1);
  });

  it.each([409, 503])('recovers after registration HTTP %i', async (status) => {
    let registrationCalls = 0;
    let meCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith('/api/auth/v1/registrations')) {
        registrationCalls += 1;
        return response({ detail: { code: status === 409 ? 'ACCOUNT_SETUP_UNAVAILABLE' : 'DATABASE_UNAVAILABLE' } }, status);
      }
      if (url.includes('accounts:signInWithPassword')) return response(firebaseSession);
      if (url.endsWith('/api/auth/v1/me')) {
        meCalls += 1;
        return meCalls === 1 ? parentRoleUnavailable() : activeParentRole();
      }
      if (url.endsWith('/api/auth/v1/registrations/complete')) {
        expect(init).not.toHaveProperty('body');
        return activeParentRole();
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    const user = await new ParentAuth().signUp('adult@example.test', 'synthetic-password');

    expect(user.role).toBe('parent');
    expect(registrationCalls).toBe(1);
  });

  it('throws the original registration error when recovery sign-in fails', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/api/auth/v1/registrations')) {
        return response({ detail: { code: 'DATABASE_UNAVAILABLE' } }, 503);
      }
      if (url.includes('accounts:signInWithPassword')) {
        return response({ error: { message: 'INVALID_LOGIN_CREDENTIALS' } }, 400);
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(new ParentAuth().signUp('adult@example.test', 'synthetic-password'))
      .rejects.toMatchObject({
        code: 'DATABASE_UNAVAILABLE',
        message: 'Chưa thể tạo tài khoản lúc này. Hãy thử lại sau.',
      } satisfies Partial<ParentAuthError>);
  });

  it('uses a distinct recoverable error when registration succeeded but sign-in failed', async () => {
    let registrationCalls = 0;
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/api/auth/v1/registrations')) {
        registrationCalls += 1;
        return response({ status: 'IDENTITY_CREATED', role: 'parent', email_verified: false }, 201);
      }
      if (url.includes('accounts:signInWithPassword')) {
        return response({ error: { message: 'TOO_MANY_ATTEMPTS_TRY_LATER' } }, 400);
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(new ParentAuth().signUp('adult@example.test', 'synthetic-password'))
      .rejects.toMatchObject({
        code: 'REGISTRATION_CREATED_SIGNIN_FAILED',
        message: expect.stringContaining('Tài khoản đã được tạo'),
      } satisfies Partial<ParentAuthError>);
    expect(registrationCalls).toBe(1);
  });

  it('preserves a role mismatch after successful registration', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/api/auth/v1/registrations')) {
        return response({ status: 'IDENTITY_CREATED', role: 'parent' }, 201);
      }
      if (url.includes('accounts:signInWithPassword')) return response(firebaseSession);
      if (url.endsWith('/api/auth/v1/me')) return response({ role: 'teacher', state: 'active' });
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(new ParentAuth().signUp('adult@example.test', 'synthetic-password'))
      .rejects.toMatchObject({ code: 'ACCOUNT_ROLE_MISMATCH' } satisfies Partial<ParentAuthError>);
  });

  it('keeps development logs free of email, token, and error-message contents', async () => {
    const email = 'adult-private@example.test';
    const token = 'synthetic-private-id-token';
    const info = vi.spyOn(console, 'info').mockImplementation(() => {});
    vi.stubGlobal('__DEV__', true);
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith('/api/auth/v1/registrations')) {
        throw new Error(`registration failed for ${email} with ${token}`);
      }
      if (url.includes('accounts:signInWithPassword')) {
        throw new Error(`Firebase rejected ${email} with ${token}`);
      }
      throw new Error('Unexpected synthetic request.');
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(new ParentAuth().signUp(email, 'synthetic-password'))
      .rejects.toMatchObject({ code: 'REGISTRATION_NETWORK_ERROR' });

    const logs = JSON.stringify(info.mock.calls);
    expect(logs).not.toContain(email);
    expect(logs).not.toContain(token);
    expect(logs).not.toContain('registration failed');
    expect(logs).not.toContain('Firebase rejected');
  });
});
