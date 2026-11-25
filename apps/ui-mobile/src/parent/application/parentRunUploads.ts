import type { ParentActionIdentity } from './ports/ParentPorts';
import { ParentApplicationError } from './ParentApplicationError';
import { isAssetRef } from './parentPhaseB';

/**
 * Sends one drawing or one voice recording through the generic upload sessions (goal v3 T-2a, SRS
 * l.1654-1658) and returns the opaque `asset_ref` that `/assets` or `/idea` then names. The adapter
 * (`GenericUploadSessionsApi`) and the device bytes and SHA-256 sit behind ports, so this orchestration is
 * unit tested without a network.
 */
export type RunUploadPurpose = 'RUN_ARTWORK' | 'RUN_AUDIO';

export interface UploadSessionView {
  upload_id: string;
  state: string;
  part_size_bytes: number;
  expected_parts: number;
  accepted_parts: Array<{ part_no: number; byte_length: number; sha256: string }>;
  revision: number;
  asset_ref: string | null;
  asset_state: 'READY' | null;
  error_code: string | null;
}

export interface UploadSessionsPort {
  create(
    input: { purpose: RunUploadPurpose; target_ref: string; media_type: string; expected_size_bytes: number; expected_sha256: string },
    idempotencyKey: ParentActionIdentity,
    signal?: AbortSignal,
  ): Promise<UploadSessionView>;
  putPart(uploadId: string, partNo: number, bytes: Uint8Array, partSha256: string, signal?: AbortSignal): Promise<unknown>;
  complete(
    uploadId: string,
    input: { expected_size_bytes: number; expected_sha256: string },
    idempotencyKey: ParentActionIdentity,
    signal?: AbortSignal,
  ): Promise<UploadSessionView>;
}

export interface BinaryDigestPort {
  /** Lowercase hex SHA-256. */
  sha256Hex(bytes: Uint8Array): Promise<string>;
}

/** The two keys of one upload are made once and kept for every retry of the same file (replay, not a new session). */
export interface RunUploadKeys {
  create: ParentActionIdentity;
  complete: ParentActionIdentity;
}

export const RUN_UPLOAD_LIMITS: Record<RunUploadPurpose, { maxBytes: number; mediaTypes: readonly string[] }> = {
  // SRS l.983, T-2a-DEC-4: JPEG, PNG and WebP up to 20 MiB; the phone sends JPEG or PNG.
  RUN_ARTWORK: { maxBytes: 20 * 1024 * 1024, mediaTypes: ['image/jpeg', 'image/png'] },
  // BR-23, T-2c-DEC-2: 20,000,000 bytes and two minutes; `audio/mp4` and `audio/wav` (Q-2c-1).
  RUN_AUDIO: { maxBytes: 20_000_000, mediaTypes: ['audio/mp4', 'audio/wav'] },
};

export async function uploadRunMedia(input: {
  uploads: UploadSessionsPort;
  digest: BinaryDigestPort;
  purpose: RunUploadPurpose;
  runId: string;
  mediaType: string;
  bytes: Uint8Array;
  keys: RunUploadKeys;
  signal?: AbortSignal;
}): Promise<{ assetRef: string; uploadId: string }> {
  const limits = RUN_UPLOAD_LIMITS[input.purpose];
  if (!limits.mediaTypes.includes(input.mediaType)) {
    throw new ParentApplicationError('UNSUPPORTED_MEDIA_TYPE', 'Định dạng tệp chưa được hỗ trợ.');
  }
  if (input.bytes.byteLength < 1 || input.bytes.byteLength > limits.maxBytes) {
    throw new ParentApplicationError(input.purpose === 'RUN_AUDIO' ? 'AUDIO_TOO_LARGE' : 'MEDIA_TOO_LARGE', 'Tệp quá lớn hoặc trống.');
  }
  const fileSha256 = await input.digest.sha256Hex(input.bytes);
  let session: UploadSessionView;
  try {
    session = await input.uploads.create({
      purpose: input.purpose,
      target_ref: input.runId,
      media_type: input.mediaType,
      expected_size_bytes: input.bytes.byteLength,
      expected_sha256: fileSha256,
    }, input.keys.create, input.signal);
  } catch (cause) {
    // A failed create response happens before the client sends any image bytes or starts AI work.
    // Keep the stage explicit so the UI can offer its single safe retry with the same idempotency key.
    if (cause instanceof ParentApplicationError && cause.status === 503) {
      throw new ParentApplicationError(
        'UPLOAD_SESSION_CREATE_UNAVAILABLE',
        'The upload session could not be created before the file was sent.',
        cause.requestId,
        cause.status,
        {
          ...(cause.correlationId ? { correlationId: cause.correlationId } : {}),
          ...(cause.retryable === undefined ? {} : { retryable: cause.retryable }),
        },
      );
    }
    throw cause;
  }

  const partSize = session.part_size_bytes;
  const expectedParts = Math.ceil(input.bytes.byteLength / partSize);
  if (!Number.isInteger(partSize) || partSize < 1 || session.expected_parts !== expectedParts) {
    throw new ParentApplicationError('INVALID_API_RESPONSE', 'Máy chủ trả về cấu hình tải lên không khớp.');
  }
  if (session.state === 'COMPLETED' && isAssetRef(session.asset_ref) && session.asset_state === 'READY') {
    return { assetRef: session.asset_ref, uploadId: session.upload_id };
  }
  if (session.state !== 'OPEN') {
    throw new ParentApplicationError(session.error_code ?? 'UPLOAD_NOT_OPEN', 'Phiên tải lên không còn mở.');
  }

  for (let partNo = 1; partNo <= expectedParts; partNo += 1) {
    if (input.signal?.aborted) throw new ParentApplicationError('REQUEST_CANCELLED', 'Đã dừng tải lên.');
    const start = (partNo - 1) * partSize;
    const part = input.bytes.subarray(start, Math.min(start + partSize, input.bytes.byteLength));
    const partSha256 = await input.digest.sha256Hex(part);
    const accepted = session.accepted_parts.find((item) => item.part_no === partNo);
    // A part the server already holds with the same hash is not sent again (resume after a lost answer).
    if (accepted && accepted.sha256 === partSha256 && accepted.byte_length === part.byteLength) continue;
    await input.uploads.putPart(session.upload_id, partNo, part, partSha256, input.signal);
  }

  const completed = await input.uploads.complete(session.upload_id, {
    expected_size_bytes: input.bytes.byteLength,
    expected_sha256: fileSha256,
  }, input.keys.complete, input.signal);
  if (completed.state !== 'COMPLETED' || completed.asset_state !== 'READY' || !isAssetRef(completed.asset_ref)) {
    throw new ParentApplicationError(completed.error_code ?? 'UPLOAD_NOT_COMPLETED', 'Chưa xác nhận được tệp đã tải lên.');
  }
  return { assetRef: completed.asset_ref, uploadId: completed.upload_id };
}

const BASE64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
const BASE64_INDEX = (() => {
  const table = new Int16Array(128).fill(-1);
  for (let index = 0; index < BASE64.length; index += 1) table[BASE64.charCodeAt(index)] = index;
  return table;
})();

/** Decodes standard base64 (padding optional) without `atob`, which older JS engines may lack. */
export function base64ToBytes(base64: string): Uint8Array {
  const clean = base64.replace(/[\r\n\s]/g, '').replace(/=+$/, '');
  if (clean.length % 4 === 1 || /[^A-Za-z0-9+/]/.test(clean)) {
    throw new ParentApplicationError('INVALID_BASE64', 'Không đọc được dữ liệu tệp.');
  }
  const out = new Uint8Array(Math.floor((clean.length * 3) / 4));
  let outIndex = 0;
  let buffer = 0;
  let bits = 0;
  for (let index = 0; index < clean.length; index += 1) {
    buffer = ((buffer << 6) | BASE64_INDEX[clean.charCodeAt(index)]) & 0xffffff;
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      out[outIndex] = (buffer >> bits) & 0xff;
      outIndex += 1;
    }
  }
  return out;
}
