import type { AuthTokenPort } from '../../application/ports/ParentPorts';
import { ParentApiError, apiErrorFromResponse, createRequestId } from './ParentApi';

/**
 * Small request helper shared by the generic upload session adapter and the job status poller.
 * It mirrors `ParentApi.request` (bearer token, `X-Request-ID`, timeout, error envelope) but also
 * supports raw binary bodies, a caller abort signal and a response that is not always JSON (304).
 * It never logs and never puts a token, URL or storage detail into an error.
 */
export interface ParentHttpDependencies {
  auth: AuthTokenPort;
  fetcher: typeof fetch;
  apiBaseUrl: string;
}

export interface ParentHttpRequest {
  path: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  /** A JSON string or raw bytes; the caller sets the matching `Content-Type`. */
  body?: string | ArrayBuffer;
  timeoutMs: number;
  signal?: AbortSignal;
}

/**
 * Sends one request and lets `handle` read the response inside the same timeout window.
 * Failures become `ParentApiError`: `REQUEST_CANCELLED` (caller abort), `REQUEST_TIMEOUT` (408),
 * `API_UNAVAILABLE` (no base URL) or `NETWORK_ERROR`.
 */
export async function executeParentRequest<T>(
  dependencies: ParentHttpDependencies,
  request: ParentHttpRequest,
  handle: (response: Response, requestId: string) => Promise<T>,
): Promise<T> {
  const requestId = createRequestId();
  const baseUrl = dependencies.apiBaseUrl.replace(/\/+$/, '');
  if (!baseUrl) throw new ParentApiError('API_UNAVAILABLE', requestId);
  if (request.signal?.aborted) throw new ParentApiError('REQUEST_CANCELLED', requestId);

  const controller = new AbortController();
  let timedOut = false;
  const timeout = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, request.timeoutMs);
  const abortFromCaller = () => controller.abort();
  request.signal?.addEventListener('abort', abortFromCaller, { once: true });
  try {
    const response = await dependencies.fetcher(`${baseUrl}${request.path}`, {
      method: request.method,
      headers: {
        Authorization: `Bearer ${await dependencies.auth.getIdToken()}`,
        Accept: 'application/json',
        'X-Request-ID': requestId,
        ...request.headers,
      },
      ...(request.body === undefined ? {} : { body: request.body }),
      signal: controller.signal,
    });
    return await handle(response, requestId);
  } catch (error) {
    // An abort or timeout while the body is read must not look like a bad body: check them first.
    if (request.signal?.aborted) throw new ParentApiError('REQUEST_CANCELLED', requestId);
    if (timedOut) throw new ParentApiError('REQUEST_TIMEOUT', requestId, 408);
    if (error instanceof ParentApiError) throw error;
    throw new ParentApiError('NETWORK_ERROR', requestId);
  } finally {
    clearTimeout(timeout);
    request.signal?.removeEventListener('abort', abortFromCaller);
  }
}

/** Reads a JSON object body; a non-2xx answer becomes the preserved error envelope. */
export async function readJsonObject<T>(response: Response, requestId: string): Promise<T> {
  const payload = await response.json().catch(() => null) as Record<string, unknown> | null;
  if (!response.ok) throw apiErrorFromResponse(payload, response.status, requestId, response.headers);
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    throw new ParentApiError('INVALID_API_RESPONSE', requestId, response.status);
  }
  return payload as T;
}
