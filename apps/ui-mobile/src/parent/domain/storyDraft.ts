import type { StoryDraft, StoryLearning } from './types';

const STORY_SCHEMA_VERSION = 'sketch2life.story-revision.v1';
const MIN_SCENES = 5;
const MAX_SCENES = 15;
const MIN_DURATION_MS = 30_000;
const MAX_DURATION_MS = 90_000;

/** Validates untrusted API data against the Parent story-revision contract. */
export function parseStoryDraft(value: unknown): StoryDraft | null {
  if (!isRecord(value) || value.schema_version !== STORY_SCHEMA_VERSION || value.language !== 'vi') return null;
  if (!isNonEmptyString(value.title) || !isRecord(value.story) || !Array.isArray(value.scenes)) return null;

  const story = value.story;
  const opening = story.opening;
  const middle = story.middle;
  const ending = story.ending;
  if (!isNonEmptyString(opening) || !isNonEmptyString(middle) || !isNonEmptyString(ending)) return null;
  if (value.scenes.length < MIN_SCENES || value.scenes.length > MAX_SCENES || !isInteger(value.duration_ms)) return null;

  let cursor = 0;
  const scenes: StoryDraft['scenes'] = [];
  for (const [index, item] of value.scenes.entries()) {
    if (!isRecord(item)) return null;
    if (item.scene_index !== index + 1 || !isNonEmptyString(item.title) || !isNonEmptyString(item.action) || !isNonEmptyString(item.narration)) return null;
    if (!isInteger(item.start_ms) || !isInteger(item.duration_ms) || item.start_ms !== cursor || Number(item.duration_ms) <= 0) return null;

    const duration = Number(item.duration_ms);
    scenes.push({
      scene_index: index + 1,
      title: item.title,
      action: item.action,
      narration: item.narration,
      start_ms: cursor,
      duration_ms: duration,
    });
    cursor += duration;
  }

  if (cursor !== value.duration_ms || cursor < MIN_DURATION_MS || cursor > MAX_DURATION_MS) return null;
  const learning = parseLearning(value.learning);
  if (learning === null) return null;
  return {
    ...(learning ? { learning } : {}),
    schema_version: STORY_SCHEMA_VERSION,
    language: 'vi',
    title: value.title,
    story: { opening, middle, ending },
    duration_ms: cursor,
    scenes,
  };
}

/** `undefined`: the story has no learning script; `null`: it has one that cannot be shown honestly. */
function parseLearning(value: unknown): StoryLearning | undefined | null {
  if (value === undefined || value === null) return undefined;
  if (!isRecord(value) || typeof value.verified !== 'boolean' || !Array.isArray(value.points)) return null;
  const source = value.fact_source;
  if (source !== 'CARD' && source !== 'LESSON' && source !== 'AI_DRAFT') return null;
  if (value.points.length === 0 || !value.points.every(isNonEmptyString)) return null;
  return { fact_source: source, verified: value.verified, points: [...value.points] };
}

/** What to tell the adult before they confirm facts nobody has checked; `null` for checked facts. */
export function learningNote(learning: StoryLearning): string | null {
  if (learning.verified) return null;
  return learning.fact_source === 'LESSON'
    ? 'Soạn từ ghi chú bài học. Hãy đọc lại trước khi xác nhận.'
    : 'Thông tin do AI soạn, chưa được kiểm chứng. Hãy kiểm tra từng ý trước khi xác nhận.';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function isInteger(value: unknown): value is number {
  return Number.isInteger(value);
}
