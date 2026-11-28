import { afterEach, describe, expect, it, vi } from 'vitest';

const CONFIG_MODULE = '../src/parent/infrastructure/config';
const AUTH_MODULE = '../src/parent/infrastructure/auth/ParentAuth';
const originalEmulatorEnv = process.env.EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL;

const mockParentConfig = vi.hoisted(() => ({
  firebaseApiKey: 'test-api-key',
  apiBaseUrl: 'https://parent.example.test',
  firebaseAuthEmulatorUrl: '',
}));

const response = (body: unknown, status = 200): Response => new Response(JSON.stringify(body), {
  status,
  headers: { 'Content-Type': 'application/json' },
});

const firebaseSession = (expiresIn = '3600') => ({
  localId: 'test-parent-uid',
  idToken: 'test-id-token',
  refreshToken: 'test-refresh-token',
  expiresIn,
  email: 'parent@example.test',
});

async function loadRuntimeConfig(options: {
  dev: boolean;
  platform: string;
  emulatorUrl?: string;
}) {
  if (options.emulatorUrl === undefined) {
    delete process.env.EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL;
  } else {
    process.env.EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL = options.emulatorUrl;
  }
  vi.stubGlobal('__DEV__', options.dev);
  vi.resetModules();
  vi.doUnmock(CONFIG_MODULE);
  vi.doMock('expo-constants', () => ({ default: { expoConfig: null } }));
  vi.doMock('react-native', () => ({ Platform: { OS: options.platform } }));
  return import(CONFIG_MODULE) as Promise<typeof import('../src/parent/infrastructure/config')>;
}

async function createAuth(options: {
  dev: boolean;
  apiKey?: string;
  emulatorUrl?: string;
}) {
  vi.stubGlobal('__DEV__', options.dev);
  Object.assign(mockParentConfig, {
    firebaseApiKey: options.apiKey ?? 'test-api-key',
    apiBaseUrl: 'https://parent.example.test',
    firebaseAuthEmulatorUrl: options.emulatorUrl ?? '',
  });
  vi.resetModules();
  vi.doMock(CONFIG_MODULE, () => ({ parentConfig: mockParentConfig }));
  const { ParentAuth } = await import(AUTH_MODULE);
  return new ParentAuth();
}

function stubFirebaseFetch(signInExpiresIn = '3600') {
  const urls: string[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    urls.push(url);
    if (url.includes('accounts:signInWithPassword') || url.includes('accounts:signInWithIdp')) {
      return response(firebaseSession(signInExpiresIn));
    }
    if (url.includes('accounts:update') || url.includes('securetoken.googleapis.com')) {
      return response(firebaseSession());
    }
    if (url.endsWith('/api/auth/v1/me')) return response({ role: 'parent', state: 'active' });
    throw new Error('Unexpected synthetic request.');
  });
  vi.stubGlobal('fetch', fetchMock);
  return { urls, fetchMock };
}

afterEach(() => {
  if (originalEmulatorEnv === undefined) delete process.env.EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL;
  else process.env.EXPO_PUBLIC_FIREBASE_AUTH_EMULATOR_URL = originalEmulatorEnv;
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.doUnmock(CONFIG_MODULE);
  vi.doUnmock('expo-constants');
  vi.doUnmock('react-native');
  vi.resetModules();
});

describe('parent Firebase Auth emulator config', () => {
  it('defaults to an empty frozen emulator URL', async () => {
    const { parentConfig } = await loadRuntimeConfig({ dev: true, platform: 'ios' });

    expect(parentConfig.firebaseAuthEmulatorUrl).toBe('');
    expect(Object.isFrozen(parentConfig)).toBe(true);
  });

  it.each(['http://localhost:9099', 'http://127.0.0.1:9099'])(
    'rewrites %s to the Android host',
    async (emulatorUrl) => {
      const { parentConfig } = await loadRuntimeConfig({ dev: true, platform: 'android', emulatorUrl });

      expect(parentConfig.firebaseAuthEmulatorUrl).toBe('http://10.0.2.2:9099');
    },
  );

  it('keeps localhost unchanged off Android', async () => {
    const { parentConfig } = await loadRuntimeConfig({
      dev: true,
      platform: 'ios',
      emulatorUrl: 'http://localhost:9099',
    });

    expect(parentConfig.firebaseAuthEmulatorUrl).toBe('http://localhost:9099');
  });

  it('ignores emulator configuration in release builds', async () => {
    const { parentConfig } = await loadRuntimeConfig({
      dev: false,
      platform: 'android',
      emulatorUrl: 'http://localhost:9099',
    });

    expect(parentConfig.firebaseAuthEmulatorUrl).toBe('');
  });

  it.each([
    'not a URL',
    'https://localhost:9099',
    'http://auth.example.test:9099',
    'http://localhost',
    'http://localhost:65536',
    'http://localhost:9099/path',
  ])('ignores invalid emulator URL %s', async (emulatorUrl) => {
    const { parentConfig } = await loadRuntimeConfig({ dev: true, platform: 'ios', emulatorUrl });

    expect(parentConfig.firebaseAuthEmulatorUrl).toBe('');
  });
});

describe('ParentAuth emulator REST routing', () => {
  it('keeps production sign-in and refresh URLs when unset', async () => {
    const auth = await createAuth({ dev: true });
    const { urls } = stubFirebaseFetch('1');

    await auth.signIn('parent@example.test', 'test-password');

    expect(urls).toContain('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=test-api-key');
    expect(urls).toContain('https://securetoken.googleapis.com/v1/token?key=test-api-key');
  });

  it('routes password sign-in and refresh to the emulator with a fake key when API key is empty', async () => {
    const auth = await createAuth({ dev: true, apiKey: '', emulatorUrl: 'http://127.0.0.1:9099' });
    const { urls } = stubFirebaseFetch('1');

    await auth.signIn('parent@example.test', 'test-password');

    expect(urls).toContain('http://127.0.0.1:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key');
    expect(urls).toContain('http://127.0.0.1:9099/securetoken.googleapis.com/v1/token?key=fake-api-key');
  });

  it('routes Google sign-in and password update to the emulator', async () => {
    const auth = await createAuth({ dev: true, apiKey: '', emulatorUrl: 'http://localhost:9099' });
    const { urls } = stubFirebaseFetch();

    await auth.signInWithGoogle('test-google-id-token');
    await auth.changePassword('current-password', 'new-password');

    expect(urls).toContain('http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key=fake-api-key');
    expect(urls).toContain('http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=fake-api-key');
    expect(urls).toContain('http://localhost:9099/identitytoolkit.googleapis.com/v1/accounts:update?key=fake-api-key');
  });

  it('uses production endpoints in release mode even if an emulator URL is present', async () => {
    const auth = await createAuth({ dev: false, emulatorUrl: 'http://localhost:9099' });
    const { urls } = stubFirebaseFetch('1');

    await auth.signIn('parent@example.test', 'test-password');

    expect(urls).toContain('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=test-api-key');
    expect(urls).toContain('https://securetoken.googleapis.com/v1/token?key=test-api-key');
    expect(urls.some((url) => url.includes('localhost:9099'))).toBe(false);
  });
});
