import type { NarrationInput } from '../demo/api';

export type SupportedImageMimeType = 'image/jpeg' | 'image/png';
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
