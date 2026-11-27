import { describe, expect, it, vi } from 'vitest';
import { ParentApi } from '../src/parent/infrastructure/http/ParentApi';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { firebaseApiKey: 'synthetic-firebase-key', apiBaseUrl: 'https://parent.example.test' },
}));

describe('FEAT-094 activity suggestions after a reload', () => {
  it('asks for the set that already exists, so a reopened app never starts a second one', async () => {
    const fetcher = vi.fn(async () => new Response('{}', { status: 200 }));
    const api = new ParentApi({ getIdToken: async () => 'synthetic-token' }, fetcher as unknown as typeof fetch, 'https://parent.example.test');

    await api.suggestActivitiesV1('run-1', 2, 'action-1');

    const [, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({ expected_understanding_revision: 2, reuse_latest: true });
  });
});
