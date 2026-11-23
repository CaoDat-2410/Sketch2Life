import { describe, expect, it, vi } from 'vitest';
import type { AuthTokenPort } from '../src/parent/application/ports/ParentPorts';
import { ParentApplicationError } from '../src/parent/application/ParentApplicationError';
import { ParentPlatformUseCases } from '../src/parent/application/use-cases/ParentPlatformUseCases';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import { isParentStoryRunLifecycleEnvelope } from '../src/parent/domain/types';
import { requireLiveStoryRun } from '../src/parent/application/storyRunResult';
import { parentRecoveryGroupForError, safeParentFlowErrorMessage } from '../src/parent/presentation/navigation/parentFlowV1';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { apiBaseUrl: 'https://api.example.test' },
}));

type Reply = { status: number; body: Record<string, unknown> };
type FetchCall = { url: string; init: RequestInit };

function createApi(replies: Reply[]) {
  const calls: FetchCall[] = [];
  const auth: AuthTokenPort = { getIdToken: vi.fn(async () => 'synthetic-token') };
  const fetcher = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    calls.push({ url: String(input), init });
    const reply = replies.shift() ?? { status: 200, body: {} };
    return {
      ok: reply.status >= 200 && reply.status < 300,
      status: reply.status,
      headers: new Headers({ 'X-Request-ID': 'synthetic-response-request' }),
      json: async () => reply.body,
    } as Response;
  }) as unknown as typeof fetch;
  return { api: new ParentApi(auth, fetcher, 'https://api.example.test'), calls };
}

const header = (call: FetchCall, name: string) => new Headers(call.init.headers).get(name);

const lifecycle = {
  run_id: 'synthetic-run',
  run_state: 'DELETE_PENDING',
  revision: 3,
  version: 4,
  lifecycle_request_ref: 'synthetic-lifecycle',
  purge_state: 'PENDING',
};

describe('Parent run lifecycle client (FR-C-08)', () => {
  it('cancels with the expected revision and an idempotency key', async () => {
    const { api, calls } = createApi([{ status: 202, body: { request_id: 'r1', lifecycle } }]);

    const result = await api.cancelStoryRunV1('synthetic-run', 3, 'cancel-action-1');

    expect(result.lifecycle.run_state).toBe('DELETE_PENDING');
    expect(calls).toHaveLength(1);
    expect(`${calls[0].init.method} ${new URL(calls[0].url).pathname}`).toBe('POST /v1/story-runs/synthetic-run/cancel');
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ expected_revision: 3 });
    expect(header(calls[0], 'Idempotency-Key')).toBe('cancel-action-1');
  });

  it('deletes without a body and with an idempotency key', async () => {
    const { api, calls } = createApi([{ status: 202, body: { request_id: 'r2', lifecycle } }]);

    await api.deleteStoryRunV1('synthetic-run', 'delete-action-1');

    expect(`${calls[0].init.method} ${new URL(calls[0].url).pathname}`).toBe('DELETE /v1/story-runs/synthetic-run');
    expect(calls[0].init.body).toBeUndefined();
    expect(header(calls[0], 'Idempotency-Key')).toBe('delete-action-1');
  });

  it('refuses a key that the server would refuse, before any request', () => {
    const { api, calls } = createApi([]);

    expect(() => api.cancelStoryRunV1('synthetic-run', 1, '')).toThrow(ParentApiError);
    expect(() => api.deleteStoryRunV1('synthetic-run', 'k'.repeat(129))).toThrow(ParentApiError);
    expect(() => api.deleteStoryRunV1('synthetic-run', 'khoa-khong-ascii-é')).toThrow(ParentApiError);
    expect(() => api.deleteStoryRunV1('synthetic-run', 'key with space')).toThrow(ParentApiError);
    expect(() => api.deleteStoryRunV1('synthetic-run', 'k'.repeat(128))).not.toThrow();
    expect(calls).toHaveLength(0);
  });

  it('applies the server key rule to the four story commands before fetch', async () => {
    const calls = [
      (api: ParentApi, key: string) => api.createStoryRunV1({ parent_profile_id: 'p', topic: 't', adult_confirmed_idea: 'i' }, key),
      (api: ParentApi, key: string) => api.confirmStoryRunContextV1('synthetic-run', {} as never, key),
      (api: ParentApi, key: string) => api.confirmStoryRunSubjectV1('synthetic-run', 1, 'subject', key),
      (api: ParentApi, key: string) => api.confirmStoryRunScriptV1('synthetic-run', 1, 'a'.repeat(64), key),
    ];
    for (const call of calls) {
      const rejecting = createApi([]);
      for (const bad of ['', 'k'.repeat(129), 'key with space', 'khoa-khong-ascii-é']) {
        expect(() => call(rejecting.api, bad)).toThrow(ParentApiError);
      }
      expect(rejecting.calls).toHaveLength(0);
      for (const good of ['k', 'k'.repeat(128), '!~']) {
        const accepting = createApi([{ status: 200, body: { request_id: 'r', story_run: { run_id: 'synthetic-run' } } }]);
        await call(accepting.api, good).catch(() => undefined);
        expect(accepting.calls).toHaveLength(1);
        expect(header(accepting.calls[0], 'Idempotency-Key')).toBe(good);
      }
    }
  });

  it('reads a purged run as the lifecycle projection and a live run as the full run', async () => {
    const { api } = createApi([
      { status: 200, body: { request_id: 'r3', lifecycle: { ...lifecycle, run_state: 'DELETED', purge_state: 'COMPLETED' } } },
      { status: 200, body: { request_id: 'r4', story_run: { run_id: 'synthetic-run' } } },
    ]);

    const purged = await api.getStoryRunV1('synthetic-run');
    const live = await api.getStoryRunV1('synthetic-run');

    expect(isParentStoryRunLifecycleEnvelope(purged)).toBe(true);
    expect(isParentStoryRunLifecycleEnvelope(live)).toBe(false);
    if (isParentStoryRunLifecycleEnvelope(purged)) expect(purged.lifecycle.run_state).toBe('DELETED');
  });

  it('keeps the 404 and the 409 as typed errors with the current version', async () => {
    const { api } = createApi([
      { status: 404, body: { code: 'RESOURCE_NOT_FOUND', message: 'x', correlation_id: 'c1', retryable: false } },
      { status: 409, body: { code: 'STALE_REVISION', message: 'x', correlation_id: 'c2', retryable: false, current_version: 5 } },
      { status: 409, body: { code: 'INVALID_STATE_TRANSITION', message: 'x', correlation_id: 'c3', retryable: false } },
    ]);

    const notFound = await api.deleteStoryRunV1('missing', 'k1').catch((cause: unknown) => cause);
    const stale = await api.cancelStoryRunV1('synthetic-run', 1, 'k2').catch((cause: unknown) => cause);
    const invalidState = await api.deleteStoryRunV1('synthetic-run', 'k3').catch((cause: unknown) => cause);

    expect(notFound).toMatchObject({ code: 'RESOURCE_NOT_FOUND', status: 404 });
    expect(stale).toMatchObject({ code: 'STALE_REVISION', status: 409, currentVersion: 5 });
    expect(invalidState).toMatchObject({ code: 'INVALID_STATE_TRANSITION', status: 409 });
    expect(parentRecoveryGroupForError(notFound)).toBe('resource-refresh');
    expect(parentRecoveryGroupForError(stale)).toBe('review-current-state');
  });

  it('passes the use case through and refuses an empty run id', async () => {
    const api = {
      cancelStoryRunV1: vi.fn(async () => ({ request_id: 'r', lifecycle })),
      deleteStoryRunV1: vi.fn(async () => ({ request_id: 'r', lifecycle })),
    };
    const useCases = new ParentPlatformUseCases(api as never);

    await useCases.cancelRunV1('run-1', 2, 'action-1');
    await useCases.deleteRunV1('run-2', 'action-2');

    expect(api.cancelStoryRunV1).toHaveBeenCalledWith('run-1', 2, 'action-1');
    expect(api.deleteStoryRunV1).toHaveBeenCalledWith('run-2', 'action-2');
    expect(() => useCases.cancelRunV1(' ', 1, 'a')).toThrow(ParentApplicationError);
    expect(() => useCases.deleteRunV1('', 'a')).toThrow(ParentApplicationError);
  });

  it('has Vietnamese messages and a recovery group for the two lifecycle states', () => {
    for (const code of ['DELETE_PENDING', 'DELETED']) {
      expect(parentRecoveryGroupForError({ code })).toBe('lifecycle-pending');
      expect(safeParentFlowErrorMessage({ code })).toMatch(/xóa/);
    }
  });

  it('stops a flow that needs a live run when the server answers with the lifecycle projection', () => {
    const live = { request_id: 'r', story_run: { run_id: 'synthetic-run' } } as never;
    expect(requireLiveStoryRun(live)).toBe(live);
    for (const state of ['DELETE_PENDING', 'DELETED'] as const) {
      const purged = { request_id: 'r5', lifecycle: { ...lifecycle, run_state: state } } as never;
      expect(() => requireLiveStoryRun(purged)).toThrow(ParentApplicationError);
      try {
        requireLiveStoryRun(purged);
      } catch (cause) {
        expect(cause).toMatchObject({ code: state, requestId: 'r5' });
      }
    }
  });

  it('turns a lifecycle answer of a confirmation or revision route into a typed error', async () => {
    const answer = { status: 200, body: { request_id: 'r6', lifecycle: { ...lifecycle, run_state: 'DELETED' } } };
    const { api } = createApi([answer, answer, answer, answer, answer]);

    const results = await Promise.all([
      api.confirmStoryRunContextV1('synthetic-run', { expected_context_revision: 1, expected_context_snapshot_sha256: 'h' } as never, 'a1').catch((c: unknown) => c),
      api.confirmStoryRunSubjectV1('synthetic-run', 1, 'diều', 'a2').catch((c: unknown) => c),
      api.confirmStoryRunScriptV1('synthetic-run', 1, 'h', 'a3').catch((c: unknown) => c),
      api.createStoryRevisionV1('synthetic-run', 1, undefined, 'a4').catch((c: unknown) => c),
      api.selectActivityV1('synthetic-run', {
        expected_revision: 3,
        activity: { lesson_id: 'lesson-1', version_id: 'version-1', content_sha256: 'a'.repeat(64), activity_index: 0 },
      }, 'a5').catch((c: unknown) => c),
    ]);

    for (const result of results) {
      expect(result).toMatchObject({ code: 'DELETED', requestId: 'r6' });
      expect(parentRecoveryGroupForError(result)).toBe('lifecycle-pending');
    }
  });
});
