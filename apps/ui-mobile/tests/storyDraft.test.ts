import { describe, expect, it } from 'vitest';
import { parseStoryDraft } from '../src/parent/domain/storyDraft';

function validStory() {
  const scenes = Array.from({ length: 5 }, (_, index) => ({
    scene_index: index + 1,
    title: `Cảnh ${index + 1}`,
    action: 'Nhân vật quan sát khu vườn.',
    narration: 'Bé tìm hiểu điều mới quanh mình.',
    start_ms: index * 6_000,
    duration_ms: 6_000,
  }));

  return {
    schema_version: 'sketch2life.story-revision.v1',
    language: 'vi',
    title: 'Chuyến khám phá khu vườn',
    story: { opening: 'Mở đầu.', middle: 'Diễn biến.', ending: 'Kết thúc.' },
    duration_ms: 30_000,
    scenes,
  };
}

describe('Parent story revision domain parser', () => {
  it('accepts a Vietnamese 5-scene story with continuous timing', () => {
    expect(parseStoryDraft(validStory())).toMatchObject({
      schema_version: 'sketch2life.story-revision.v1',
      language: 'vi',
      duration_ms: 30_000,
      scenes: expect.arrayContaining([expect.objectContaining({ scene_index: 5, start_ms: 24_000 })]),
    });
  });

  it('rejects a story outside the required scene range', () => {
    const story = validStory();
    story.scenes.pop();
    story.duration_ms = 24_000;

    expect(parseStoryDraft(story)).toBeNull();
  });

  it('rejects gaps, overlaps, and totals that do not match scene durations', () => {
    const story = validStory();
    story.scenes[2].start_ms += 1;

    expect(parseStoryDraft(story)).toBeNull();
  });

  it('rejects non-Vietnamese or unsupported schema revisions', () => {
    expect(parseStoryDraft({ ...validStory(), language: 'en' })).toBeNull();
    expect(parseStoryDraft({ ...validStory(), schema_version: 'story.v0' })).toBeNull();
  });
});
