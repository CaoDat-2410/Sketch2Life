import { AppState } from 'react-native';
import { parentConfig } from '../config';
import type { AuthTokenPort } from '../../application/ports/ParentPorts';
import { ParentApiError } from './ParentApi';
import { executeParentRequest, readJsonObject, type ParentHttpDependencies } from './ParentHttpTransport';

/**
 * Job status polling (goal v3 T0.4, SRS l.779, l.786, l.806): `GET /v1/jobs/{job_id}`.
 * ETag / If-None-Match with 304, `poll_after_ms` clamped to 2 s to 10 s (an own 2 s doubling
 * backoff when the server sends no hint), stop on terminal states, pause while the app is not in
 * the foreground and resume when it returns, stop on abort or unmount. `failed_retryable` is not
 * terminal: the contract keeps the job alive for another attempt. Not wired to any screen yet.
 */
export const JOB_POLL_MIN_MS = 2_000;
export const JOB_POLL_MAX_MS = 10_000;
const REQUEST_TIMEOUT_MS = 30_000;
const MAX_CONSECUTIVE_TRANSIENT_FAILURES = 3;
const JOB_ID = /^[A-Za-z0-9_.:-]{1,120}$/;
const ETAG_VALUE = /^[\x20-\x7E]{1,200}$/;

export type AiJobState =
  | 'queued'
  | 'running'
  | 'succeeded'
  | 'failed_retryable'
  | 'failed_exhausted'
  | 'blocked_unsafe'
  | 'cancelled';

export interface AiJobStatusV1 {
  job_id: string;
  target_kind: string;
  target_ref: string;
  job_revision: number;
  attempt_number: number;
  target_revision: number;
  input_hash: string;
  state: AiJobState;
  result_disposition: 'accepted' | 'stale' | 'rejected' | null;
  correlation_id: string;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  completed_at: string | null;
  progress: { kind: 'unknown' | 'stages' | 'percentage'; value: number | null; stage_label: string | null };
  failure: { code: string; retryable: boolean; public_message: string; attempts_remaining: number | null } | null;
  /** Opaque artifact refs; the server lists them only when the result is eligible for the caller. */
  result_refs: Array<{ artifact_ref: string; sha256: string }>;
  poll_after_ms: number | null;
}

export interface JobStatusReadResult {
  status: AiJobStatusV1 | null;
  etag: string | null;
  notModified: boolean;
}

export interface AppStatePort {
  currentState: string | null;
  addEventListener(event: 'change', listener: (state: string) => void): { remove(): void };
}

export type JobPollSleep = (ms: number, signal: AbortSignal) => Promise<void>;

const JOB_STATES: ReadonlySet<string> = new Set<AiJobState>([
  'queued', 'running', 'succeeded', 'failed_retryable', 'failed_exhausted', 'blocked_unsafe', 'cancelled',
]);
const TERMINAL_STATES: ReadonlySet<string> = new Set<AiJobState>([
  'succeeded', 'failed_exhausted', 'blocked_unsafe', 'cancelled',
]);
const TRANSIENT_CODES: ReadonlySet<string> = new Set([
  'NETWORK_ERROR', 'REQUEST_TIMEOUT', 'HTTP_429', 'HTTP_502', 'HTTP_503', 'HTTP_504',
  'DATABASE_UNAVAILABLE', 'IDENTITY_PROVIDER_UNAVAILABLE', 'BE1_RUNTIME_UNAVAILABLE',
]);

export function isTerminalJobState(state: AiJobState): boolean {
  return TERMINAL_STATES.has(state);
}

export class JobStatusPoller {
  private readonly dependencies: ParentHttpDependencies;

  constructor(
    auth: AuthTokenPort,
    fetcher: typeof fetch = fetch,
    apiBaseUrl: string = parentConfig.apiBaseUrl,
    private readonly appState: AppStatePort = AppState as unknown as AppStatePort,
    private readonly sleep: JobPollSleep = delay,
  ) {
    this.dependencies = { auth, fetcher, apiBaseUrl };
  }

  /** One conditional read. A 304 answers `{ status: null, notModified: true }` with the ETag. */
  async get(jobId: string, etag?: string | null, signal?: AbortSignal): Promise<JobStatusReadResult> {
    if (!JOB_ID.test(jobId)) throw new ParentApiError('INVALID_JOB_ID', 'local-request', 400);
    const conditional: Record<string, string> = etag && ETAG_VALUE.test(etag) ? { 'If-None-Match': etag } : {};
    return executeParentRequest(
      this.dependencies,
      {
        path: `/v1/jobs/${encodeURIComponent(jobId)}`,
        method: 'GET',
        headers: conditional,
        timeoutMs: REQUEST_TIMEOUT_MS,
        signal,
      },
      async (response, requestId): Promise<JobStatusReadResult> => {
        const nextEtag = response.headers.get('ETag');
        if (response.status === 304) return { status: null, etag: nextEtag, notModified: true };
        const payload = await readJsonObject<Record<string, unknown>>(response, requestId);
        return { status: parseJobStatus(payload, requestId, response.status), etag: nextEtag, notModified: false };
      },
    );
  }

  /**
   * Polls until a terminal state and resolves with it. `onUpdate` receives each new revision.
   * While the app is not active the loop pauses (the in-flight request and the wait are
   * cancelled) and it reads again right away when the app returns to the foreground.
   * Aborting `signal` (screen unmount, user cancel) rejects with `REQUEST_CANCELLED`.
   * A persistent API error (for example the uniform 404) rejects; a few consecutive transient
   * failures are retried with the backoff first.
   */
  async poll(jobId: string, onUpdate: (status: AiJobStatusV1) => void, signal?: AbortSignal): Promise<AiJobStatusV1> {
    if (!JOB_ID.test(jobId)) throw new ParentApiError('INVALID_JOB_ID', 'local-request', 400);
    let foreground = this.appState.currentState === 'active';
    let attempt: AbortController | null = null;
    const foregroundWaiters = new Set<() => void>();
    const subscription = this.appState.addEventListener('change', (next) => {
      foreground = next === 'active';
      if (!foreground) {
        attempt?.abort();
      } else {
        for (const wake of [...foregroundWaiters]) wake();
      }
    });

    const waitForForeground = () => new Promise<void>((resolve, reject) => {
      const done = () => {
        foregroundWaiters.delete(wake);
        signal?.removeEventListener('abort', cancelled);
      };
      const wake = () => { done(); resolve(); };
      const cancelled = () => { done(); reject(cancelledError()); };
      if (signal?.aborted) { reject(cancelledError()); return; }
      foregroundWaiters.add(wake);
      signal?.addEventListener('abort', cancelled, { once: true });
    });

    let current: AiJobStatusV1 | null = null;
    let etag: string | null = null;
    let fallbackWaitMs = JOB_POLL_MIN_MS;
    let transientFailures = 0;
    try {
      for (;;) {
        if (signal?.aborted) throw cancelledError();
        if (!foreground) {
          await waitForForeground();
          continue;
        }
        const controller = new AbortController();
        attempt = controller;
        const stopFromCaller = () => controller.abort();
        signal?.addEventListener('abort', stopFromCaller, { once: true });
        try {
          const read = await this.get(jobId, etag, controller.signal);
          transientFailures = 0;
          if (read.etag) etag = read.etag;
          const previousRevision = current?.job_revision ?? null;
          if (read.status) {
            current = read.status;
            if (current.job_revision !== previousRevision) {
              onUpdate(current);
              fallbackWaitMs = JOB_POLL_MIN_MS;
            }
          } else if (!current) {
            // A 304 answers a conditional request, and none is sent before a body was read.
            throw new ParentApiError('INVALID_API_RESPONSE', 'job-not-cached', 502);
          }
          if (isTerminalJobState(current.state)) return current;
          const waitMs = nextWaitMs(current.poll_after_ms, fallbackWaitMs);
          if (current.poll_after_ms === null) fallbackWaitMs = Math.min(fallbackWaitMs * 2, JOB_POLL_MAX_MS);
          await this.sleep(waitMs, controller.signal);
        } catch (error) {
          if (signal?.aborted) throw cancelledError();
          // Paused or otherwise cancelled attempt: the top of the loop waits for the foreground.
          if (controller.signal.aborted || isCancelled(error)) continue;
          const transient = error instanceof ParentApiError && (TRANSIENT_CODES.has(error.code) || error.retryable === true);
          if (!transient || transientFailures >= MAX_CONSECUTIVE_TRANSIENT_FAILURES) throw error;
          transientFailures += 1;
          const waitMs = nextWaitMs(null, fallbackWaitMs);
          fallbackWaitMs = Math.min(fallbackWaitMs * 2, JOB_POLL_MAX_MS);
          try {
            await this.sleep(waitMs, controller.signal);
          } catch (sleepError) {
            if (signal?.aborted) throw cancelledError();
            if (!controller.signal.aborted && !isCancelled(sleepError)) throw sleepError;
          }
        } finally {
          signal?.removeEventListener('abort', stopFromCaller);
          attempt = null;
        }
      }
    } finally {
      subscription.remove();
    }
  }
}

/** The server hint wins (clamped); without a hint the doubling fallback is used. */
function nextWaitMs(hint: number | null, fallbackMs: number): number {
  const wanted = hint === null ? fallbackMs : hint;
  return Math.min(Math.max(wanted, JOB_POLL_MIN_MS), JOB_POLL_MAX_MS);
}

function parseJobStatus(payload: Record<string, unknown>, requestId: string, status: number): AiJobStatusV1 {
  const hint = payload.poll_after_ms;
  const valid = typeof payload.job_id === 'string'
    && typeof payload.state === 'string' && JOB_STATES.has(payload.state)
    && typeof payload.job_revision === 'number' && Number.isInteger(payload.job_revision) && payload.job_revision >= 1
    && (hint === null || hint === undefined || (typeof hint === 'number' && Number.isFinite(hint) && hint >= 0));
  if (!valid) throw new ParentApiError('INVALID_API_RESPONSE', requestId, status);
  return {
    ...payload,
    progress: payload.progress ?? { kind: 'unknown', value: null, stage_label: null },
    failure: payload.failure ?? null,
    result_refs: Array.isArray(payload.result_refs) ? payload.result_refs : [],
    poll_after_ms: typeof hint === 'number' ? hint : null,
  } as unknown as AiJobStatusV1;
}

function cancelledError(): ParentApiError {
  return new ParentApiError('REQUEST_CANCELLED', 'local-request');
}

function isCancelled(error: unknown): boolean {
  return error instanceof ParentApiError && error.code === 'REQUEST_CANCELLED';
}

function delay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) { reject(cancelledError()); return; }
    const onAbort = () => { clearTimeout(timer); reject(cancelledError()); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', onAbort); resolve(); }, ms);
    signal.addEventListener('abort', onAbort, { once: true });
  });
}
