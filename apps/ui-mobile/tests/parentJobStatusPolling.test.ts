import { describe, expect, it, vi } from 'vitest';

vi.mock('../src/parent/infrastructure/config', () => ({ parentConfig: { apiBaseUrl: 'https://api.example.test' } }));
vi.mock('react-native', () => ({ AppState: { currentState: 'active', addEventListener: () => ({ remove: () => undefined }) } }));

import type { AuthTokenPort } from '../src/parent/application/ports/ParentPorts';
import {
  JobStatusPoller,
  isTerminalJobState,
  type AiJobState,
  type AiJobStatusV1,
  type AppStatePort,
} from '../src/parent/infrastructure/http/JobStatusPoller';

type Call = { url: string; init: RequestInit };
type Reply = Response | (() => Response) | Error;

const status = (state: AiJobState, revision: number, pollAfterMs: number | null = null): AiJobStatusV1 => ({
  job_id: 'job-1', target_kind: 'LESSON_SOURCE_DOCUMENT', target_ref: 'doc-1', job_revision: revision,
  attempt_number: 1, target_revision: 1, input_hash: 'a'.repeat(64), state,
  result_disposition: state === 'succeeded' ? 'accepted' : null, correlation_id: 'corr-1',
  created_at: '2026-11-20T00:00:00Z', updated_at: '2026-11-20T00:00:00Z',
  started_at: state === 'queued' ? null : '2026-11-20T00:00:01Z',
  completed_at: isTerminalJobState(state) ? '2026-11-20T00:00:02Z' : null,
  progress: { kind: 'unknown', value: null, stage_label: null }, failure: null, result_refs: [], poll_after_ms: pollAfterMs,
});

function reply(statusCode: number, body?: unknown, etag: string | null = '"1"'): Response {
  return {
    ok: statusCode >= 200 && statusCode < 300,
    status: statusCode,
    headers: new Headers(etag ? { ETag: etag } : {}),
    json: async () => body,
  } as Response;
}

function fakeAppState(initial = 'active') {
  let listener: ((state: string) => void) | undefined;
  const remove = vi.fn();
  const state: AppStatePort = {
    currentState: initial,
    addEventListener: vi.fn((_event, next) => { listener = next; return { remove }; }),
  };
  return {
    state,
    remove,
    change: (next: string) => { state.currentState = next; listener?.(next); },
  };
}

function scriptedFetch(replies: Reply[]) {
  const calls: Call[] = [];
  const fetcher = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    calls.push({ url: String(input), init });
    const next = replies.shift();
    if (next === undefined) throw new Error('no reply scripted');
    if (next instanceof Error) throw next;
    return typeof next === 'function' ? next() : next;
  }) as unknown as typeof fetch;
  return { fetcher, calls };
}

/** A fetch that never answers until its signal aborts (an in-flight request). */
function hangingFetch() {
  return vi.fn((_url: RequestInfo | URL, init: RequestInit = {}) => new Promise<Response>((_resolve, reject) => {
    init.signal?.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })));
  })) as unknown as typeof fetch;
}

const auth: AuthTokenPort = { getIdToken: vi.fn(async () => 'test-token') };
const instantSleep = (waits: number[]) => vi.fn(async (ms: number) => { waits.push(ms); });
/** A sleep that stays pending until its signal aborts, like the real timer. */
const pendingSleep = vi.fn((_ms: number, signal: AbortSignal) => new Promise<void>((_resolve, reject) => {
  signal.addEventListener('abort', () => reject(new Error('sleep aborted')), { once: true });
}));

function poller(fetcher: typeof fetch, appState: AppStatePort, sleep = instantSleep([])) {
  return new JobStatusPoller(auth, fetcher, 'https://api.example.test/', appState, sleep);
}

const flush = () => new Promise<void>((resolve) => setTimeout(resolve, 0));

describe('job status poller', () => {
  it('uses ETag conditional reads, doubles the fallback wait and stops at the terminal state', async () => {
    const { fetcher, calls } = scriptedFetch([
      reply(200, status('queued', 1), '"1"'),
      reply(304, undefined, '"1"'),
      reply(200, status('succeeded', 2), '"2"'),
    ]);
    const waits: number[] = [];
    const updates: AiJobStatusV1[] = [];
    const result = await poller(fetcher, fakeAppState().state, instantSleep(waits)).poll('job-1', (job) => updates.push(job));

    expect(result.state).toBe('succeeded');
    expect(updates.map((job) => job.state)).toEqual(['queued', 'succeeded']);
    expect(waits).toEqual([2_000, 4_000]);
    expect(calls).toHaveLength(3);
    expect(new URL(calls[0].url).pathname).toBe('/v1/jobs/job-1');
    expect(calls[0].init.method).toBe('GET');
    expect(new Headers(calls[0].init.headers).get('If-None-Match')).toBeNull();
    expect(new Headers(calls[1].init.headers).get('If-None-Match')).toBe('"1"');
    expect(new Headers(calls[2].init.headers).get('If-None-Match')).toBe('"1"');
    expect(new Headers(calls[0].init.headers).get('Authorization')).toBe('Bearer test-token');
  });

  it('caps the fallback wait at ten seconds', async () => {
    const replies: Reply[] = [reply(200, status('running', 1), '"1"')];
    for (let index = 0; index < 5; index += 1) replies.push(reply(304, undefined, '"1"'));
    replies.push(reply(200, status('succeeded', 2), '"2"'));
    const waits: number[] = [];
    await poller(scriptedFetch(replies).fetcher, fakeAppState().state, instantSleep(waits)).poll('job-1', vi.fn());
    expect(waits).toEqual([2_000, 4_000, 8_000, 10_000, 10_000, 10_000]);
  });

  it('follows the server poll_after_ms hint clamped to 2 to 10 seconds', async () => {
    const { fetcher } = scriptedFetch([
      reply(200, status('queued', 1, 3_000), '"1"'),
      reply(200, status('running', 2, 500), '"2"'),
      reply(200, status('running', 3, 60_000), '"3"'),
      reply(200, status('succeeded', 4), '"4"'),
    ]);
    const waits: number[] = [];
    await poller(fetcher, fakeAppState().state, instantSleep(waits)).poll('job-1', vi.fn());
    expect(waits).toEqual([3_000, 2_000, 10_000]);
  });

  it('keeps polling a failed_retryable job and reports each new revision once', async () => {
    const { fetcher } = scriptedFetch([
      reply(200, status('running', 1), '"1"'),
      reply(200, status('failed_retryable', 2), '"2"'),
      reply(200, status('failed_retryable', 2), '"2b"'),
      reply(200, status('running', 3), '"3"'),
      reply(200, status('succeeded', 4), '"4"'),
    ]);
    const updates: string[] = [];
    const result = await poller(fetcher, fakeAppState().state).poll('job-1', (job) => updates.push(`${job.job_revision}:${job.state}`));
    expect(result.state).toBe('succeeded');
    expect(updates).toEqual(['1:running', '2:failed_retryable', '3:running', '4:succeeded']);
  });

  it.each(['succeeded', 'failed_exhausted', 'blocked_unsafe', 'cancelled'] as const)('stops on the terminal state %s', async (state) => {
    const { fetcher, calls } = scriptedFetch([reply(200, status(state, 1))]);
    const sleep = instantSleep([]);
    const result = await poller(fetcher, fakeAppState().state, sleep).poll('job-1', vi.fn());
    expect(result.state).toBe(state);
    expect(calls).toHaveLength(1);
    expect(sleep).not.toHaveBeenCalled();
  });

  it('does not treat failed_retryable, queued or running as terminal', () => {
    for (const state of ['queued', 'running', 'failed_retryable'] as const) expect(isTerminalJobState(state)).toBe(false);
  });

  it('pauses an in-flight request in the background and resumes with a conditional read in the foreground', async () => {
    const appState = fakeAppState();
    const calls: Call[] = [];
    const replies: Array<(init: RequestInit) => Promise<Response>> = [
      async () => reply(200, status('running', 1), '"1"'),
      (init) => new Promise<Response>((_resolve, reject) => {
        init.signal?.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })));
      }),
      async () => reply(200, status('succeeded', 2), '"2"'),
    ];
    const fetcher = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      calls.push({ url: String(input), init });
      return replies.shift()!(init);
    }) as unknown as typeof fetch;
    // The first wait ends at once; the second request is the in-flight one that gets paused.
    let sleeps = 0;
    const sleep = vi.fn(async () => { sleeps += 1; });
    const pending = poller(fetcher, appState.state, sleep).poll('job-1', vi.fn());

    await vi.waitFor(() => expect(calls).toHaveLength(2));
    appState.change('background');
    await flush();
    expect(calls).toHaveLength(2);

    appState.change('active');
    await expect(pending).resolves.toMatchObject({ state: 'succeeded' });
    expect(calls).toHaveLength(3);
    expect(new Headers(calls[2].init.headers).get('If-None-Match')).toBe('"1"');
    expect(sleeps).toBe(1);
    expect(appState.remove).toHaveBeenCalledTimes(1);
  });

  it('cancels the wait in the background, sends nothing while paused and resumes on the foreground', async () => {
    const appState = fakeAppState();
    const { fetcher, calls } = scriptedFetch([
      reply(200, status('running', 1), '"1"'),
      reply(200, status('succeeded', 2), '"2"'),
    ]);
    const pending = poller(fetcher, appState.state, pendingSleep).poll('job-1', vi.fn());

    await vi.waitFor(() => expect(pendingSleep).toHaveBeenCalled());
    appState.change('background');
    await flush();
    await flush();
    expect(calls).toHaveLength(1);

    appState.change('inactive');
    await flush();
    expect(calls).toHaveLength(1);

    appState.change('active');
    await expect(pending).resolves.toMatchObject({ state: 'succeeded' });
    expect(calls).toHaveLength(2);
  });

  it('does not send a request while the app starts in the background', async () => {
    const appState = fakeAppState('background');
    const { fetcher, calls } = scriptedFetch([reply(200, status('succeeded', 1))]);
    const pending = poller(fetcher, appState.state).poll('job-1', vi.fn());
    await flush();
    expect(calls).toHaveLength(0);
    appState.change('active');
    await expect(pending).resolves.toMatchObject({ state: 'succeeded' });
    expect(calls).toHaveLength(1);
  });

  it('stops on abort: cancels the request, rejects and removes the AppState listener', async () => {
    const appState = fakeAppState();
    const controller = new AbortController();
    const fetcher = hangingFetch();
    const pending = poller(fetcher, appState.state).poll('job-1', vi.fn(), controller.signal);
    await vi.waitFor(() => expect(fetcher).toHaveBeenCalled());
    controller.abort();
    await expect(pending).rejects.toMatchObject({ code: 'REQUEST_CANCELLED' });
    expect(appState.remove).toHaveBeenCalledTimes(1);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });

  it('stops on abort during the wait and while paused in the background', async () => {
    const waiting = new AbortController();
    const first = scriptedFetch([reply(200, status('running', 1))]);
    const appState = fakeAppState();
    const duringWait = poller(first.fetcher, appState.state, pendingSleep).poll('job-1', vi.fn(), waiting.signal);
    await vi.waitFor(() => expect(first.fetcher).toHaveBeenCalled());
    await flush();
    waiting.abort();
    await expect(duringWait).rejects.toMatchObject({ code: 'REQUEST_CANCELLED' });
    expect(first.calls).toHaveLength(1);

    const pausedController = new AbortController();
    const pausedState = fakeAppState('background');
    const second = scriptedFetch([]);
    const duringPause = poller(second.fetcher, pausedState.state).poll('job-1', vi.fn(), pausedController.signal);
    await flush();
    pausedController.abort();
    await expect(duringPause).rejects.toMatchObject({ code: 'REQUEST_CANCELLED' });
    expect(second.calls).toHaveLength(0);
    expect(pausedState.remove).toHaveBeenCalledTimes(1);
  });

  it('rejects at once when the signal is already aborted', async () => {
    const controller = new AbortController();
    controller.abort();
    const { fetcher, calls } = scriptedFetch([reply(200, status('succeeded', 1))]);
    await expect(poller(fetcher, fakeAppState().state).poll('job-1', vi.fn(), controller.signal)).rejects.toMatchObject({ code: 'REQUEST_CANCELLED' });
    expect(calls).toHaveLength(0);
  });

  it('rejects a 304 that arrives before any status body', async () => {
    const { fetcher } = scriptedFetch([reply(304, undefined, '"1"')]);
    await expect(poller(fetcher, fakeAppState().state).poll('job-1', vi.fn())).rejects.toMatchObject({ code: 'INVALID_API_RESPONSE' });
  });

  it('rejects an unknown job state instead of polling forever', async () => {
    const { fetcher } = scriptedFetch([reply(200, { ...status('queued', 1), state: 'paused' })]);
    await expect(poller(fetcher, fakeAppState().state).poll('job-1', vi.fn())).rejects.toMatchObject({ code: 'INVALID_API_RESPONSE' });
  });

  it('preserves the uniform 404 envelope and does not retry it', async () => {
    const { fetcher, calls } = scriptedFetch([reply(404, { detail: { code: 'RESOURCE_NOT_FOUND', request_id: 'req-404' } }, null)]);
    await expect(poller(fetcher, fakeAppState().state).poll('job-1', vi.fn())).rejects.toMatchObject({
      code: 'RESOURCE_NOT_FOUND', status: 404, requestId: 'req-404',
    });
    expect(calls).toHaveLength(1);
  });

  it('retries a few transient failures with the backoff, then gives up', async () => {
    const waits: number[] = [];
    const recovering = scriptedFetch([
      reply(503, { detail: { code: 'DATABASE_UNAVAILABLE' } }, null),
      new TypeError('Network request failed'),
      reply(200, status('succeeded', 1)),
    ]);
    await expect(poller(recovering.fetcher, fakeAppState().state, instantSleep(waits)).poll('job-1', vi.fn())).resolves.toMatchObject({ state: 'succeeded' });
    expect(waits).toEqual([2_000, 4_000]);

    const failing = scriptedFetch([1, 2, 3, 4].map(() => reply(503, { detail: { code: 'DATABASE_UNAVAILABLE' } }, null)));
    await expect(poller(failing.fetcher, fakeAppState().state).poll('job-1', vi.fn())).rejects.toMatchObject({ code: 'DATABASE_UNAVAILABLE' });
    expect(failing.calls).toHaveLength(4);
  });

  it('treats the real server outage codes, 429 and retryable errors as transient', async () => {
    const cases: Array<[number, unknown]> = [
      [503, { detail: { code: 'IDENTITY_PROVIDER_UNAVAILABLE' } }],
      [503, { detail: { code: 'BE1_RUNTIME_UNAVAILABLE' } }],
      [429, { detail: { code: 'RATE_LIMITED', retryable: true } }],
    ];
    for (const [statusCode, body] of cases) {
      const { fetcher, calls } = scriptedFetch([reply(statusCode, body, null), reply(200, status('succeeded', 1))]);
      await expect(poller(fetcher, fakeAppState().state).poll('job-1', vi.fn())).resolves.toMatchObject({ state: 'succeeded' });
      expect(calls).toHaveLength(2);
    }
  });

  it('survives background and foreground arriving before the aborted request settles', async () => {
    const appState = fakeAppState();
    const calls: Call[] = [];
    const fetcher = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      calls.push({ url: String(input), init });
      if (calls.length === 1) {
        return new Promise<Response>((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => setTimeout(() => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })), 5));
        });
      }
      return reply(200, status('succeeded', 1));
    }) as unknown as typeof fetch;
    const pending = poller(fetcher, appState.state).poll('job-1', vi.fn());
    await vi.waitFor(() => expect(calls).toHaveLength(1));
    appState.change('background');
    appState.change('active');
    await expect(pending).resolves.toMatchObject({ state: 'succeeded' });
    expect(calls).toHaveLength(2);
    expect(appState.remove).toHaveBeenCalledTimes(1);
  });

  it('reports a timeout while the body is read as a timeout, not as a bad body', async () => {
    vi.useFakeTimers();
    try {
      const fetcher = vi.fn(async (_url: RequestInfo | URL, init: RequestInit = {}) => ({
        ok: true,
        status: 200,
        headers: new Headers(),
        json: () => new Promise((_resolve, reject) => {
          init.signal?.addEventListener('abort', () => reject(Object.assign(new Error('aborted'), { name: 'AbortError' })));
        }),
      }) as unknown as Response) as unknown as typeof fetch;
      const pending = poller(fetcher, fakeAppState().state).get('job-1');
      const assertion = expect(pending).rejects.toMatchObject({ code: 'REQUEST_TIMEOUT', status: 408 });
      await vi.advanceTimersByTimeAsync(30_001);
      await assertion;
    } finally {
      vi.useRealTimers();
    }
  });

  it('fills missing optional blocks so a screen never reads undefined', async () => {
    const { progress, failure, result_refs, ...partial } = status('succeeded', 1);
    void progress; void failure; void result_refs;
    const { fetcher } = scriptedFetch([reply(200, partial)]);
    const result = await poller(fetcher, fakeAppState().state).poll('job-1', vi.fn());
    expect(result.progress).toEqual({ kind: 'unknown', value: null, stage_label: null });
    expect(result.result_refs).toEqual([]);
    expect(result.failure).toBeNull();
  });

  it('does not retry a rejected token (401)', async () => {
    const { fetcher, calls } = scriptedFetch([reply(401, { code: 'AUTH_REQUIRED' }, null)]);
    await expect(poller(fetcher, fakeAppState().state).poll('job-1', vi.fn())).rejects.toMatchObject({ code: 'AUTH_REQUIRED', status: 401 });
    expect(calls).toHaveLength(1);
  });

  it('refuses a job id outside the opaque alphabet before any request', async () => {
    const { fetcher, calls } = scriptedFetch([]);
    const subject = poller(fetcher, fakeAppState().state);
    await expect(subject.poll('job/../x', vi.fn())).rejects.toMatchObject({ code: 'INVALID_JOB_ID' });
    await expect(subject.get('', null)).rejects.toMatchObject({ code: 'INVALID_JOB_ID' });
    expect(calls).toHaveLength(0);
  });

  it('reads once: 200 returns the body and ETag, a 304 returns notModified with the ETag', async () => {
    const { fetcher, calls } = scriptedFetch([
      reply(200, status('running', 7, 4_000), '"job:job-1:7:x"'),
      reply(304, undefined, '"job:job-1:7:x"'),
    ]);
    const subject = poller(fetcher, fakeAppState().state);
    const first = await subject.get('job-1');
    expect(first).toMatchObject({ notModified: false, etag: '"job:job-1:7:x"' });
    expect(first.status?.poll_after_ms).toBe(4_000);
    const second = await subject.get('job-1', first.etag);
    expect(second).toEqual({ status: null, etag: '"job:job-1:7:x"', notModified: true });
    expect(new Headers(calls[1].init.headers).get('If-None-Match')).toBe('"job:job-1:7:x"');
  });

  it('subscribes to AppState once per poll and removes the listener when the job ends', async () => {
    const appState = fakeAppState();
    const { fetcher } = scriptedFetch([reply(200, status('running', 1)), reply(200, status('succeeded', 2))]);
    await poller(fetcher, appState.state).poll('job-1', vi.fn());
    expect(appState.state.addEventListener).toHaveBeenCalledTimes(1);
    expect(appState.remove).toHaveBeenCalledTimes(1);
  });
});
