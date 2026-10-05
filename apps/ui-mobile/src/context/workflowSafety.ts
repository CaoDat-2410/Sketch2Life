import type { NarrationInput } from '../demo/api';

export type SupportedImageMimeType = 'image/jpeg' | 'image/png';
export type SourceImageMimeType = SupportedImageMimeType | 'image/webp' | 'image/heic' | 'image/heif';
export type ImagePickerMetadata = {
  format: SourceImageMimeType | null;
  metadataConflict: boolean;
  metadataMissing: boolean;
  unsupportedAnimation: boolean;
};

export const MAX_SOURCE_IMAGE_BYTES = 15_000_000;
// Leave enough room for common 12 MP phone photos (e.g. 4032 x 3024) to be
// safely resized to the backend's 4 MP admission limit. Keep the bound explicit:
// the native manipulator still decodes the original before resizing it.
export const MAX_SOURCE_IMAGE_PIXELS = 16_000_000;
export const MAX_SOURCE_IMAGE_EDGE = 6_000;
export type FeedbackObservationCode =
  | 'STARTED_INDEPENDENTLY'
  | 'COMPLETED_STEPS'
  | 'ASKED_FOR_HELP'
  | 'CHANGED_APPROACH'
  | 'STOPPED_EARLY';

export const FEEDBACK_OBSERVATIONS: ReadonlyArray<{
  code: FeedbackObservationCode;
  label: string;
  emoji: string;
  group: 'fineMotor' | 'cognitive';
}> = [
  { code: 'STARTED_INDEPENDENTLY', label: 'Tự bắt đầu một bước', emoji: '🌱', group: 'fineMotor' },
  { code: 'COMPLETED_STEPS', label: 'Hoàn thành các bước', emoji: '🧩', group: 'fineMotor' },
  { code: 'CHANGED_APPROACH', label: 'Thử cách làm khác', emoji: '✂️', group: 'fineMotor' },
  { code: 'ASKED_FOR_HELP', label: 'Chủ động nhờ hỗ trợ', emoji: '🤝', group: 'cognitive' },
  { code: 'STOPPED_EARLY', label: 'Dừng hoạt động sớm', emoji: '⏸️', group: 'cognitive' },
];

export function acquireSingleFlight(lock: { current: boolean }): boolean {
  if (lock.current) return false;
  lock.current = true;
  return true;
}

export function releaseSingleFlight(lock: { current: boolean }): void {
  lock.current = false;
}

export function normalizeSupportedImage(
  fileName: string | null | undefined,
  mimeType: string | null | undefined,
): { fileName: string; mimeType: SupportedImageMimeType } | null {
  const name = fileName?.trim() || '';
  const extension = name.match(/\.([^.\\/]+)$/)?.[1]?.toLowerCase() ?? '';
  const mime = mimeType?.split(';', 1)[0]?.trim().toLowerCase() ?? '';
  const mimeFromExtension = extension === 'png'
    ? 'image/png'
    : ['jpg', 'jpeg'].includes(extension) ? 'image/jpeg' : null;
  const mimeFromMetadata = mime === 'image/png'
    ? 'image/png'
    : ['image/jpeg', 'image/jpg'].includes(mime) ? 'image/jpeg' : null;

  if ((extension && !mimeFromExtension) || (mime && !mimeFromMetadata)) return null;
  if (mimeFromExtension && mimeFromMetadata && mimeFromExtension !== mimeFromMetadata) return null;
  const resolvedMime = mimeFromMetadata ?? mimeFromExtension;
  if (!resolvedMime) return null;

  const canonicalExtension = resolvedMime === 'image/png' ? 'png' : 'jpg';
  const normalizedFileName = name
    ? extension ? name : `${name}.${canonicalExtension}`
    : `drawing.${canonicalExtension}`;
  return { fileName: normalizedFileName, mimeType: resolvedMime };
}

export function inspectImagePickerMetadata(
  fileName: string | null | undefined,
  mimeType: string | null | undefined,
): ImagePickerMetadata {
  const extension = fileName?.trim().match(/\.([^.\\/]+)$/)?.[1]?.toLowerCase() ?? '';
  const mime = mimeType?.split(';', 1)[0]?.trim().toLowerCase() ?? '';
  const byExtension: Record<string, SourceImageMimeType> = {
    jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp',
    heic: 'image/heic', heif: 'image/heif',
  };
  const byMime: Record<string, SourceImageMimeType> = {
    'image/jpg': 'image/jpeg', 'image/jpeg': 'image/jpeg', 'image/png': 'image/png',
    'image/webp': 'image/webp', 'image/heic': 'image/heic', 'image/heif': 'image/heif',
  };
  const extensionFormat = byExtension[extension] ?? null;
  const mimeFormat = byMime[mime] ?? null;
  const unsupportedAnimation = mime === 'image/gif' || mime === 'image/apng'
    || ['gif', 'apng'].includes(extension);
  return {
    format: mimeFormat ?? extensionFormat,
    metadataConflict: Boolean(mimeFormat && extensionFormat && mimeFormat !== extensionFormat),
    metadataMissing: !mimeFormat && !extensionFormat,
    unsupportedAnimation,
  };
}

export function sourceImageExceedsDecodeBudget(width: number, height: number): boolean {
  return !Number.isFinite(width) || !Number.isFinite(height)
    || width < 1 || height < 1
    || width * height > MAX_SOURCE_IMAGE_PIXELS
    || Math.max(width, height) > MAX_SOURCE_IMAGE_EDGE;
}

export function targetImageDimensions(
  width: number,
  height: number,
  maxPixels = 4_000_000,
  maxEdge = 4_096,
): { width: number; height: number } | null {
  if (!Number.isFinite(width) || !Number.isFinite(height) || width < 1 || height < 1) return null;
  const scale = Math.min(
    1,
    Math.sqrt(maxPixels / (width * height)),
    maxEdge / Math.max(width, height),
  );
  return {
    width: Math.max(1, Math.floor(width * scale)),
    height: Math.max(1, Math.floor(height * scale)),
  };
}

export type NarrationValidation =
  | { ok: true; narration: NarrationInput }
  | { ok: false; message: string };

export function prepareNarration(
  mode: 'none' | 'text' | 'audio',
  text: string,
  audio: {
    artifactRef?: string;
    sha256?: string;
    byteLength?: number;
    contentType?: string;
    mimeType?: string;
  } | null,
): NarrationValidation {
  if (mode === 'none') return { ok: true, narration: { kind: 'NONE' } };
  if (mode === 'text') {
    const cleaned = text.trim();
    return cleaned
      ? { ok: true, narration: { kind: 'TEXT', text: cleaned, language: 'vi', provenance: 'TEXT_TYPED' } }
      : { ok: false, message: 'Hãy nhập lời kể hoặc chọn Không thêm lời kể.' };
  }
  if (!audio?.artifactRef || !audio.sha256 || !audio.byteLength) {
    return { ok: false, message: 'Lời kể chưa được upload. Quay lại bước ảnh và thử lại.' };
  }
  return {
    ok: true,
    narration: {
      kind: 'AUDIO',
      artifact_ref: audio.artifactRef,
      sha256: audio.sha256,
      content_type: audio.contentType || audio.mimeType || 'audio/mp4',
      byte_length: audio.byteLength,
      provenance: 'RECORDED_AUDIO',
    },
  };
}
