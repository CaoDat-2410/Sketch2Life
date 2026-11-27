/**
 * FEAT-094 Amendment A: the learning points of a story, honest video progress, and the two defects of the app runs
 * (resume without a loaded profile list; a slow first activity request).
 */
import { describe, expect, it } from 'vitest';
import {
  ACTIVITY_PENDING_LIMIT_MS,
  resolveResumeProfile,
  waitForPendingResult,
} from '../src/parent/application/parentResilience';
import { videoProgressFraction, videoStageRows } from '../src/parent/application/videoWait';
import { learningNote, parseStoryDraft } from '../src/parent/domain/storyDraft';

const scene = (index: number) => ({
  scene_index: index, title: `Cảnh ${index}`, action: 'Gà đi.', narration: 'Gà đi.',
  start_ms: (index - 1) * 10_000, duration_ms: 10_000,
});
const draft = (learning?: unknown) => ({
  schema_version: 'sketch2life.story-revision.v1', language: 'vi', title: 'Gà Vàng',
  story: { opening: 'Một.', middle: 'Hai.', ending: 'Ba.' }, duration_ms: 50_000,
  scenes: [1, 2, 3, 4, 5].map(scene), ...(learning === undefined ? {} : { learning }),
});

describe('learning points of a story', () => {
  it('keeps the points the server sends', () => {
    const learning = { fact_source: 'AI_DRAFT', verified: false, points: ['Gà là một loài chim.'] };
    expect(parseStoryDraft(draft(learning))?.learning).toEqual(learning);
  });

  it('keeps a story without them, or with a null value, as before', () => {
    expect(parseStoryDraft(draft())?.learning).toBeUndefined();
    expect(parseStoryDraft(draft(null))?.learning).toBeUndefined();
  });

  it('refuses points it cannot show honestly', () => {
    expect(parseStoryDraft(draft({ fact_source: 'WEB', verified: true, points: ['x'] }))).toBeNull();
    expect(parseStoryDraft(draft({ fact_source: 'CARD', verified: 'yes', points: ['x'] }))).toBeNull();
    expect(parseStoryDraft(draft({ fact_source: 'CARD', verified: true, points: [] }))).toBeNull();
  });

  it('tells the adult how far each source was checked', () => {
    expect(learningNote({ fact_source: 'CARD', verified: true, points: ['x'] })).toBeNull();
    expect(learningNote({ fact_source: 'AI_DRAFT', verified: false, points: ['x'] })).toContain('AI soạn');
    expect(learningNote({ fact_source: 'LESSON', verified: false, points: ['x'] })).toContain('ghi chú bài học');
  });
});

const progress = (stage: string, scene: number | null) => ({
  stage, scene_index: scene, scene_count: 5, started_at: '2026-11-26T09:00:00Z', eta_seconds: 400,
}) as never;

describe('video progress', () => {
  it('counts the prepared scenes as well as the rendered ones', () => {
    expect(videoStageRows(progress('PREPARING_SCENES', 3))[1].label).toContain('(3/5)');
  });

  it('grows from planning to checking and stays inside 0 and 1', () => {
    const order = [
      progress('PLANNING', null), progress('PREPARING_SCENES', 1), progress('PREPARING_SCENES', 5),
      progress('RENDERING', 1), progress('RENDERING', 5), progress('ASSEMBLING', null), progress('CHECKING', null),
    ].map(videoProgressFraction);
    expect([...order].sort((a, b) => a - b)).toEqual(order);
    expect(order[0]).toBeGreaterThan(0);
    expect(order[order.length - 1]).toBeLessThan(1);
    expect(videoProgressFraction(null)).toBe(0);
  });
});

describe('resume after signing in', () => {
  const profile = { profile_id: 'p1', state: 'ACTIVE' } as never;

  it('uses the loaded profile without asking the server', async () => {
    const loaded = await resolveResumeProfile([profile], 'p1', async () => { throw new Error('not needed'); });
    expect(loaded).toBe(profile);
  });

  it('reads the profile of the run when the list is not loaded yet', async () => {
    await expect(resolveResumeProfile([], 'p1', async () => profile)).resolves.toBe(profile);
  });

  it('gives nothing for a profile being deleted, an unknown id or a failed read', async () => {
    const deleting = { profile_id: 'p1', state: 'DELETE_PENDING' } as never;
    await expect(resolveResumeProfile([], 'p1', async () => deleting)).resolves.toBeNull();
    await expect(resolveResumeProfile([], null, async () => profile)).resolves.toBeNull();
    await expect(resolveResumeProfile([], 'p1', async () => { throw new Error('offline'); })).resolves.toBeNull();
  });
});

describe('a slow first activity request', () => {
  const pending = (cause: unknown) => (cause as { code?: string }).code === 'PENDING';

  it('asks again with the same action until the answer is ready', async () => {
    let calls = 0;
    const waited: number[] = [];
    const result = await waitForPendingResult(async () => {
      calls += 1;
      if (calls < 3) throw { code: 'PENDING' };
      return 'ready';
    }, { isPending: pending, sleep: async (ms) => { waited.push(ms); }, now: () => 0 });
    expect(result).toBe('ready');
    expect(calls).toBe(3);
    expect(waited).toEqual([15_000, 15_000]);
  });

  it('gives up with the last error after the limit', async () => {
    let clock = 0;
    await expect(waitForPendingResult(async () => { throw { code: 'PENDING' }; }, {
      isPending: pending, sleep: async () => { clock += ACTIVITY_PENDING_LIMIT_MS; }, now: () => clock,
    })).rejects.toEqual({ code: 'PENDING' });
  });

  it('passes other errors on at once and stops when the adult leaves', async () => {
    await expect(waitForPendingResult(async () => { throw { code: 'OTHER' }; }, {
      isPending: pending, sleep: async () => {}, now: () => 0,
    })).rejects.toEqual({ code: 'OTHER' });
    let calls = 0;
    await expect(waitForPendingResult(async () => { calls += 1; throw { code: 'PENDING' }; }, {
      isPending: pending, sleep: async () => {}, now: () => 0, stopped: () => true,
    })).rejects.toEqual({ code: 'PENDING' });
    expect(calls).toBe(1);
  });
});
