import { describe, expect, it, vi } from 'vitest';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import { safeParentFlowErrorMessage } from '../src/parent/presentation/navigation/parentFlowV1';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { firebaseApiKey: 'synthetic-firebase-key', apiBaseUrl: 'https://parent.example.test' },
}));

describe('T-4a1 Parent actor guard contract', () => {
  it('maps Teacher-owned run detail and confirmation calls to the same safe 404 without data', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({
      code: 'RESOURCE_NOT_FOUND', message: 'teacher run content must not escape', data: { child_name: 'private' },
    }), { status: 404 }));
    const api = new ParentApi({ getIdToken: async () => 'synthetic-token' }, fetcher as unknown as typeof fetch, 'https://parent.example.test');
    const calls: Array<{
      send: () => Promise<unknown>;
      method: 'GET' | 'POST';
      path: string;
      key?: string;
      body?: Record<string, unknown>;
    }> = [
      {
        send: () => api.getStoryRunV1('teacher-owned-run'),
        method: 'GET',
        path: '/v1/story-runs/teacher-owned-run',
      },
      {
        send: () => api.confirmStoryRunContextV1('teacher-owned-run', {
          expected_context_revision: 1,
          context_snapshot_sha256: 'a'.repeat(64),
          confirmed: true,
        }, 'context-action-1'),
        method: 'POST',
        path: '/v1/story-runs/teacher-owned-run/context-confirmation',
        key: 'context-action-1',
        body: { expected_context_revision: 1, context_snapshot_sha256: 'a'.repeat(64), confirmed: true },
      },
      {
        send: () => api.confirmStoryRunSubjectV1('teacher-owned-run', 2, 'synthetic subject', 'subject-action-1'),
        method: 'POST',
        path: '/v1/story-runs/teacher-owned-run/subject-confirmation',
        key: 'subject-action-1',
        body: { expected_understanding_revision: 2, confirmed_subject: 'synthetic subject' },
      },
      {
        send: () => api.confirmStoryRunScriptV1('teacher-owned-run', 3, 'b'.repeat(64), 'script-action-1'),
        method: 'POST',
        path: '/v1/story-runs/teacher-owned-run/script-confirmation',
        key: 'script-action-1',
        body: { expected_revision: 3, story_sha256: 'b'.repeat(64) },
      },
    ];

    for (const call of calls) {
      for (let attempt = 0; attempt < 2; attempt += 1) {
        const error = await call.send().catch((failure: unknown) => failure);
        expect(error).toBeInstanceOf(ParentApiError);
        expect(error).toMatchObject({ code: 'RESOURCE_NOT_FOUND', status: 404 });
        expect(safeParentFlowErrorMessage(error)).toBe('Không tìm thấy nội dung hoặc bạn không thể truy cập nội dung này.');
        expect(String(error)).not.toContain('teacher run content must not escape');
        expect(error).not.toHaveProperty('data');
      }
    }

    expect(fetcher).toHaveBeenCalledTimes(calls.length * 2);
    for (let index = 0; index < calls.length; index += 1) {
      const first = fetcher.mock.calls[index * 2] as unknown as [string, RequestInit];
      const replay = fetcher.mock.calls[index * 2 + 1] as unknown as [string, RequestInit];
      const expected = calls[index];
      expect(first[0]).toBe(`https://parent.example.test${expected.path}`);
      expect(replay[0]).toBe(first[0]);
      expect(first[1].method).toBe(expected.method);
      expect(replay[1].method).toBe(expected.method);
      expect(first[1].body).toBe(expected.body === undefined ? undefined : JSON.stringify(expected.body));
      expect(replay[1].body).toBe(first[1].body);
      expect(new Headers(first[1].headers).get('Idempotency-Key')).toBe(expected.key ?? null);
      expect(new Headers(replay[1].headers).get('Idempotency-Key')).toBe(expected.key ?? null);
    }
  });
});
