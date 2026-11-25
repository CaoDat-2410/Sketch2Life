import { describe, expect, it } from 'vitest';
import {
  captionAt,
  formatEta,
  videoBecameReady,
  videoChipModel,
  videoFailedNow,
  videoStageRows,
  waitChecklist,
} from '../src/parent/application/videoWait';
import { readVideoPanel } from '../src/parent/application/parentPhaseB';
import type { ParentStoryRunV1 } from '../src/parent/domain/types';

const progress = (stage: any, scene: number | null = null) => ({
  stage, scene_index: scene, scene_count: 5, started_at: '2026-11-25T09:00:00Z', eta_seconds: 400,
});

function run(state: string, extra: Record<string, unknown> = {}, runState = 'VIDEO_GENERATING'): ParentStoryRunV1 {
  return {
    run_id: 'r1', run_state: runState, run_revision: 3,
    video: {
      current_generation_id: 'g1', generation_no: 1, kind: 'INITIAL', state, job: null, scenes: [],
      playback: { state: state === 'READY' ? 'AVAILABLE' : 'HIDDEN', asset_ref: null, token_route: null },
      video_requests_used: 1, video_requests_remaining: 2, admission_pending: false, history: [], ...extra,
    },
  } as unknown as ParentStoryRunV1;
}

describe('video stage list', () => {
  it('marks earlier stages done, the current one active and later ones pending', () => {
    const rows = videoStageRows(progress('RENDERING', 2) as any);
    expect(rows.map((row) => row.status)).toEqual(['done', 'done', 'active', 'pending', 'pending', 'pending']);
    expect(rows[2].label).toContain('(2/5)');
  });

  it('shows everything pending before the worker reports', () => {
    expect(videoStageRows(null).every((row) => row.status === 'pending')).toBe(true);
  });
});

describe('estimates', () => {
  it('rounds up to whole minutes and never promises', () => {
    expect(formatEta(400)).toBe('khoảng 7 phút');
    expect(formatEta(30)).toBe('khoảng 1 phút');
    expect(formatEta(0)).toBe('Sắp xong');
    expect(formatEta(null)).toBe('Sắp xong');
  });
});

describe('waiting checklist', () => {
  it('uses the adult activity lines, bounded', () => {
    const items = waitChecklist({ instructions_text: '1. Tìm một chiếc lá rơi trong sân.\n2. Cùng bé đặt lá lên giấy và tô viền.\n3. Hỏi bé lá có màu gì.' });
    expect(items.map((item) => item.label)).toEqual([
      'Tìm một chiếc lá rơi trong sân.', 'Cùng bé đặt lá lên giấy và tô viền.', 'Hỏi bé lá có màu gì.',
    ]);
  });

  it('falls back to gentle outdoor ideas', () => {
    expect(waitChecklist(null).length).toBe(3);
    expect(waitChecklist({ instructions_text: 'ok' }).length).toBe(3);
  });
});

describe('captions', () => {
  const cues = [
    { start_ms: 0, end_ms: 900, text: 'Rùa đi.', lane: 'narration' as const },
    { start_ms: 1000, end_ms: 2000, text: 'Chào lá!', lane: 'dialogue' as const },
  ];
  it('shows the cue only inside its window', () => {
    expect(captionAt(cues, 500)?.text).toBe('Rùa đi.');
    expect(captionAt(cues, 950)).toBeNull();
    expect(captionAt(cues, 2000)).toBeNull();
    expect(captionAt(null, 10)).toBeNull();
  });
});

describe('status chip and notifications', () => {
  it('shows the stage and the estimate while a video is made elsewhere', () => {
    const chip = videoChipModel(run('GENERATING', { progress: progress('RENDERING', 2) }), false);
    expect(chip.visible).toBe(true);
    expect(chip.text).toContain('Tạo các cảnh');
    expect(chip.text).toContain('7 phút');
  });

  it('is hidden on the video step, and without a video', () => {
    expect(videoChipModel(run('GENERATING'), true).visible).toBe(false);
    expect(videoChipModel({ run_id: 'r' } as ParentStoryRunV1, false).visible).toBe(false);
  });

  it('shows a badge when the video is ready', () => {
    const chip = videoChipModel(run('READY', {}, 'VIDEO_READY'), false);
    expect(chip).toMatchObject({ visible: true, badge: true });
  });

  it('notifies once on the transition only', () => {
    expect(videoBecameReady(run('GENERATING'), run('READY', {}, 'VIDEO_READY'))).toBe(true);
    expect(videoBecameReady(run('READY', {}, 'VIDEO_READY'), run('READY', {}, 'VIDEO_READY'))).toBe(false);
    expect(videoBecameReady(null, run('READY', {}, 'VIDEO_READY'))).toBe(false);
    expect(videoFailedNow(run('GENERATING'), run('FAILED'))).toBe(true);
    expect(videoFailedNow(run('FAILED'), run('FAILED'))).toBe(false);
  });
});

describe('video panel', () => {
  it('carries the server progress and captions through', () => {
    const cues = [{ start_ms: 0, end_ms: 900, text: 'Rùa đi.', lane: 'narration' }];
    const panel = readVideoPanel(run('GENERATING', { progress: progress('NARRATING'), captions: cues }));
    expect(panel.progress?.stage).toBe('NARRATING');
    expect(panel.captions).toEqual(cues);
    expect(panel.inFlight).toBe(true);
  });
});
