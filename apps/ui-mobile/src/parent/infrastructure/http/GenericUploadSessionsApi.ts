import { parentConfig } from '../config';
import type { AuthTokenPort, ParentActionIdentity } from '../../application/ports/ParentPorts';
import { ParentApiError, assertVisibleAsciiKey } from './ParentApi';
import { executeParentRequest, readJsonObject, type ParentHttpDependencies } from './ParentHttpTransport';

/**
 * Generic upload sessions (goal v3 T-2a, SRS l.1654-1658): `/v1/upload-sessions`.
 * Literal contract: create (keyed), raw binary parts of at most 4 MiB, get, complete (keyed) and
 * abort (keyed, strong `If-Match`). The server never returns a bucket, object key or URL; the
 * `asset_ref` it answers is an opaque handle. This adapter is not wired to any screen yet:
 * the capture flow switches with T-2b and audio with T-2c. Lesson Library uploads are a
 * different contract and stay out of this file.
 */
export const GENERIC_UPLOAD_PART_MAX_BYTES = 4 * 1024 * 1024;

const JSON_TIMEOUT_MS = 30_000;
const PART_TIMEOUT_MS = 120_000;
const SHA256_HEX = /^[0-9a-f]{64}$/;
const OPAQUE_ID = /^[A-Za-z0-9._:-]{1,128}$/;
const UPLOAD_ID = /^[A-Za-z0-9._:-]{1,64}$/;

/** Parent purposes only: OCCURRENCE_DOCUMENT is a Teacher purpose and answers a Parent the uniform 404. */
export type GenericUploadPurpose = 'RUN_ARTWORK' | 'RUN_AUDIO';
export type GenericUploadState = 'OPEN' | 'COMPLETED' | 'ABORTED' | 'EXPIRED' | 'FAILED';

export interface GenericUploadAcceptedPartV1 {
  part_no: number;
  byte_length: number;
  sha256: string;
}

export interface GenericUploadSessionV1 {
  contract: 'GenericUploadSessionV1' | 'GenericUploadCompletionV1';
  upload_id: string;
  purpose: GenericUploadPurpose;
  target_ref: string;
  state: GenericUploadState;
  part_size_bytes: number;
  expected_parts: number;
  accepted_parts: GenericUploadAcceptedPartV1[];
  byte_count: number;
  expires_at: string;
  revision: number;
  /** Opaque handle once the session is COMPLETED; never a storage key or URL. */
  asset_ref: string | null;
  asset_state: 'READY' | null;
  error_code: string | null;
  /** Present on the complete answer (`GenericUploadCompletionV1`) only. */
  scanner_name?: string;
  scanner_version?: string;
}

export interface CreateGenericUploadV1 {
  purpose: GenericUploadPurpose;
  target_ref: string;
  media_type: string;
  expected_size_bytes: number;
  expected_sha256: string;
  file_name?: string | null;
}

export interface CompleteGenericUploadV1 {
  expected_size_bytes: number;
  expected_sha256: string;
}

export interface GenericUploadPartReceiptV1 {
  contract: 'GenericUploadPartReceiptV1';
  upload_id: string;
  part_no: number;
  byte_length: number;
  sha256: string;
  accepted: boolean;
  accepted_part_count: number;
  byte_count: number;
  revision: number;
}

export class GenericUploadSessionsApi {
  private readonly dependencies: ParentHttpDependencies;

  constructor(
    auth: AuthTokenPort,
    fetcher: typeof fetch = fetch,
    apiBaseUrl: string = parentConfig.apiBaseUrl,
  ) {
    this.dependencies = { auth, fetcher, apiBaseUrl };
  }

  /** Creates a session. RUN_AUDIO is a valid purpose; the server decides whether it is enabled. */
  async create(input: CreateGenericUploadV1, idempotencyKey: ParentActionIdentity, signal?: AbortSignal): Promise<GenericUploadSessionV1> {
    assertVisibleAsciiKey(idempotencyKey);
    assertCreateInput(input);
    return this.send<GenericUploadSessionV1>('/v1/upload-sessions', 'POST', JSON.stringify(input), {
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey,
    }, JSON_TIMEOUT_MS, signal);
  }

  async get(uploadId: string, signal?: AbortSignal): Promise<GenericUploadSessionV1> {
    return this.send<GenericUploadSessionV1>(sessionPath(uploadId), 'GET', undefined, {}, JSON_TIMEOUT_MS, signal);
  }

  /**
   * Sends one raw part (1 to 4 MiB, `Content-Type: application/octet-stream`, `X-Part-SHA256`).
   * The server accepts no `Content-Range`. The caller computes the lowercase hex SHA-256.
   */
  async putPart(
    uploadId: string,
    partNo: number,
    bytes: Uint8Array,
    partSha256: string,
    signal?: AbortSignal,
  ): Promise<GenericUploadPartReceiptV1> {
    const path = sessionPath(uploadId);
    if (!Number.isInteger(partNo) || partNo < 1) throw localError('INVALID_UPLOAD_PART', 400);
    if (bytes.byteLength < 1) throw localError('INVALID_UPLOAD_PART_SIZE', 400);
    if (bytes.byteLength > GENERIC_UPLOAD_PART_MAX_BYTES) throw localError('INVALID_UPLOAD_PART_SIZE', 413);
    if (!SHA256_HEX.test(partSha256)) throw localError('INVALID_UPLOAD_PART_HASH', 400);
    return this.send<GenericUploadPartReceiptV1>(`${path}/parts/${partNo}`, 'PUT', exactBuffer(bytes), {
      'Content-Type': 'application/octet-stream',
      'X-Part-SHA256': partSha256,
    }, PART_TIMEOUT_MS, signal);
  }

  /** Verifies parts, media type and the malware scan, then returns the 202 completion with the asset handle. */
  async complete(
    uploadId: string,
    input: CompleteGenericUploadV1,
    idempotencyKey: ParentActionIdentity,
    signal?: AbortSignal,
  ): Promise<GenericUploadSessionV1> {
    assertVisibleAsciiKey(idempotencyKey);
    assertSizeAndHash(input.expected_size_bytes, input.expected_sha256);
    return this.send<GenericUploadSessionV1>(`${sessionPath(uploadId)}/complete`, 'POST', JSON.stringify({
      expected_size_bytes: input.expected_size_bytes,
      expected_sha256: input.expected_sha256,
    }), {
      'Content-Type': 'application/json',
      'Idempotency-Key': idempotencyKey,
    }, JSON_TIMEOUT_MS, signal);
  }

  /** Aborts an open session with the strong `If-Match: "<revision>"` of the last answer. */
  async abort(
    uploadId: string,
    revision: number,
    idempotencyKey: ParentActionIdentity,
    signal?: AbortSignal,
  ): Promise<GenericUploadSessionV1> {
    assertVisibleAsciiKey(idempotencyKey);
    const path = sessionPath(uploadId);
    if (!Number.isInteger(revision) || revision < 1) throw localError('INVALID_UPLOAD_REVISION', 400);
    return this.send<GenericUploadSessionV1>(path, 'DELETE', undefined, {
      'Idempotency-Key': idempotencyKey,
      'If-Match': `"${revision}"`,
    }, JSON_TIMEOUT_MS, signal);
  }

  private send<T>(
    path: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE',
    body: string | ArrayBuffer | undefined,
    headers: Record<string, string>,
    timeoutMs: number,
    signal?: AbortSignal,
  ): Promise<T> {
    return executeParentRequest(
      this.dependencies,
      { path, method, headers, body, timeoutMs, signal },
      (response, requestId) => readJsonObject<T>(response, requestId),
    );
  }
}

function sessionPath(uploadId: string): string {
  if (!UPLOAD_ID.test(uploadId)) throw localError('INVALID_UPLOAD_ID', 400);
  return `/v1/upload-sessions/${encodeURIComponent(uploadId)}`;
}

function assertCreateInput(input: CreateGenericUploadV1): void {
  if (!OPAQUE_ID.test(input.target_ref)) throw localError('INVALID_UPLOAD_TARGET', 400);
  if (typeof input.media_type !== 'string' || input.media_type.length < 1 || input.media_type.length > 128) {
    throw localError('INVALID_UPLOAD_MEDIA_TYPE', 400);
  }
  assertSizeAndHash(input.expected_size_bytes, input.expected_sha256);
}

function assertSizeAndHash(size: number, sha256: string): void {
  if (!Number.isInteger(size) || size < 1) throw localError('INVALID_UPLOAD_SIZE', 400);
  if (!SHA256_HEX.test(sha256)) throw localError('INVALID_UPLOAD_HASH', 400);
}

/** The exact bytes of the view, so a sub-array never sends its whole backing buffer. */
function exactBuffer(bytes: Uint8Array): ArrayBuffer {
  if (bytes.byteOffset === 0 && bytes.byteLength === bytes.buffer.byteLength && bytes.buffer instanceof ArrayBuffer) {
    return bytes.buffer;
  }
  return bytes.slice().buffer as ArrayBuffer;
}

function localError(code: string, status: number): ParentApiError {
  return new ParentApiError(code, 'local-request', status);
}
