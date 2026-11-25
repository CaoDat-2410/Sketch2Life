import { ParentApplicationError } from '../../application/ParentApplicationError';

/** The adult's free-text idea narrows the curated lookup; blank means "topic only". */
export function sketchGuideRequestSubject(idea: string): string | undefined {
  const trimmed = idea.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

export function sketchGuideFailureMessage(cause: unknown): string {
  if (cause instanceof ParentApplicationError && cause.status === 404) {
    return 'Chưa có mẫu nét vẽ cho chủ đề này. Bạn vẫn có thể tiếp tục chụp tranh.';
  }
  return 'Chưa tải được gợi ý nét vẽ. Hãy thử lại hoặc tiếp tục không cần gợi ý.';
}
