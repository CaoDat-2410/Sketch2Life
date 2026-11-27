import { ParentApplicationError } from '../../application/ParentApplicationError';
import type { SvgGuideLevel } from '../../domain/svgGuide';

/** The adult's free-text idea narrows the curated lookup; blank means "topic only". */
export function sketchGuideRequestSubject(idea: string): string | undefined {
  const trimmed = idea.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

/** FEAT-097: the profile's age picks the level; only the level is sent to the server (FR-AI-15). */
export function guideLevelForAge(ageMonths: number | null | undefined): SvgGuideLevel {
  return typeof ageMonths === 'number' && ageMonths >= 72 ? 'simple' : 'beginner';
}

export function sketchGuideFailureMessage(cause: unknown): string {
  if (cause instanceof ParentApplicationError && cause.status === 404) {
    return 'Chưa có mẫu nét vẽ cho chủ đề này. Bạn vẫn có thể tiếp tục chụp tranh.';
  }
  return 'Chưa tải được gợi ý nét vẽ. Hãy thử lại hoặc tiếp tục không cần gợi ý.';
}
