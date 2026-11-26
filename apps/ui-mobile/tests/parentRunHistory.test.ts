import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';
import {
  applyLifecycleProjection,
  mergeRunHistoryPage,
  retainedRunActionKey,
  runActionOutcome,
  runActionSignature,
  runHistoryDateLabel,
  runHistoryStateLabel,
} from '../src/parent/application/parentRunHistory';
import type { ParentStoryRunSummary } from '../src/parent/domain/types';
import { ParentApi } from '../src/parent/infrastructure/http/ParentApi';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { firebaseApiKey: 'synthetic-firebase-key', apiBaseUrl: 'https://parent.example.test' },
}));

const run = (id: string, overrides: Partial<ParentStoryRunSummary> = {}): ParentStoryRunSummary => ({
  run_id: id,
  parent_profile_id: 'profile-1',
  run_state: 'COMPLETED',
  revision: 2,
  deleting: false,
  can_cancel: false,
  can_delete: true,
  created_at: '2026-11-19T08:00:00+00:00',
  updated_at: '2026-11-19T08:00:00+00:00',
  ...overrides,
});

describe('FEAT-081 C3b run history helpers', () => {
  it('replaces on a null cursor, appends without duplicates and stops on a cursor that does not advance', () => {
    const first = mergeRunHistoryPage([run('old')], { items: [run('a'), run('b')], next_cursor: 'c2' }, null);
    expect(first.runs.map((item) => item.run_id)).toEqual(['a', 'b']);
    const second = mergeRunHistoryPage(first.runs, { items: [run('b'), run('c')], next_cursor: 'c3' }, 'c2');
    expect(second.runs.map((item) => item.run_id)).toEqual(['a', 'b', 'c']);
    expect(second.nextCursor).toBe('c3');
    expect(mergeRunHistoryPage(second.runs, { items: [], next_cursor: 'c3' }, 'c3').nextCursor).toBeNull();
  });

  it('keeps one key per action, run and revision', () => {
    const store = new Map<string, string>();
    let counter = 0;
    const create = () => `key-${(counter += 1)}`;
    const first = retainedRunActionKey(store, runActionSignature('cancel', run('a')), create);
    const retry = retainedRunActionKey(store, runActionSignature('cancel', run('a')), create);
    const moved = retainedRunActionKey(store, runActionSignature('cancel', run('a', { revision: 3 })), create);
    expect(retry).toBe(first);
    expect(moved).not.toBe(first);
  });

  it('patches the item from the lifecycle projection after a 202', () => {
    const patched = applyLifecycleProjection([run('a'), run('b')], {
      request_id: 'r',
      lifecycle: { run_id: 'a', run_state: 'DELETE_PENDING', revision: 3, version: 3, lifecycle_request_ref: 'l', purge_state: 'PENDING' },
    });
    expect(patched[0]).toMatchObject({ deleting: true, can_cancel: false, can_delete: false, revision: 3, parent_profile_id: null });
    expect(patched[1]).toEqual(run('b'));
  });

  it('maps action failures to reload, remove or error', () => {
    expect(runActionOutcome('STALE_REVISION', 409)).toBe('reload');
    expect(runActionOutcome('INVALID_STATE_TRANSITION', 409)).toBe('reload');
    expect(runActionOutcome('RESOURCE_NOT_FOUND', 404)).toBe('remove');
    expect(runActionOutcome('NETWORK_ERROR', undefined)).toBe('error');
  });

  it('labels a run by date and state without story content', () => {
    expect(runHistoryDateLabel(run('a'))).toMatch(/^Buổi ngày \d{2}\/\d{2}\/2026$/);
    expect(runHistoryStateLabel(run('a', { deleting: true, run_state: 'DELETE_PENDING' }))).toBe('Đang xóa');
    expect(runHistoryStateLabel(run('a', { run_state: 'SOMETHING_NEW' }))).toBe('Trạng thái chưa xác định');
  });
});

describe('FEAT-081 C3b API request', () => {
  it('lists runs with limit, cursor and profile filter on the live route', async () => {
    const fetcher = vi.fn(async () => new Response(JSON.stringify({ request_id: 'r', items: [], next_cursor: null }), { status: 200 }));
    const api = new ParentApi({ getIdToken: async () => 'synthetic-token' }, fetcher as unknown as typeof fetch, 'https://api.synthetic.test');
    await api.listStoryRuns('profile-1', 'cursor-2');
    const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('https://api.synthetic.test/v1/story-runs?limit=25&cursor=cursor-2&parent_profile_id=profile-1');
    expect(init.method).toBe('GET');
  });
});

describe('FEAT-081 C3b copy (the UI-copy validator does not scan src/parent)', () => {
  const screen = readFileSync(new URL('../src/parent/presentation/screens/StoryHistoryScreen.tsx', import.meta.url), 'utf8');
  const controller = readFileSync(new URL('../src/parent/presentation/navigation/useParentPlatformController.ts', import.meta.url), 'utf8');
  const learningController = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
  it('states that cancel and delete remove the session content for good', () => {
    expect(screen).toContain('Buổi học sẽ dừng và nội dung của buổi sẽ bị xóa, không khôi phục được.');
    expect(screen).toContain('Nội dung của buổi sẽ bị xóa và không khôi phục được.');
    expect(screen).not.toContain('context_snapshot');
    expect(controller).toContain('Không tải được lịch sử buổi học. Vui lòng thử lại.');
    expect(controller).toContain('Buổi học vừa thay đổi; danh sách đã được tải lại.');
    // The reload message is set after the reload, which clears errors first (review C3B-IMPL-R1-01).
    expect(controller.indexOf('setRunsError(runActionMessages[outcome])'))
      .toBeGreaterThan(controller.indexOf('await loadRuns(runsProfileId, null)'));
    expect(controller).toContain('requestNumber !== runsRequest.current');
  });

  it('loads the list whenever the history screen is shown, whichever way the Parent got there', () => {
    const app = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
    expect(app).toContain("if (parent.step !== 'history') return;");
    expect(app).toContain('}, [parent.step, parent.profile?.profile_id, accountSubject]);');
    // One loader only: the entry points set the step and the effect loads.
    const open = app.slice(app.indexOf('function openHistory'), app.indexOf('function openSharing'));
    expect(open).not.toContain('loadRuns');
  });

  it('offers a completed-row watch action that fetches the full run before playback', () => {
    expect(screen).toContain("run.run_state === 'COMPLETED'");
    expect(screen).toContain('Xem lại video');
    expect(screen).toContain('props.onWatch(run.run_id)');
    const start = learningController.indexOf('async function watchHistoryRun');
    const end = learningController.indexOf('function onPlaybackError', start);
    const watch = learningController.slice(start, end);
    expect(watch).toContain('readLiveRun(runId)');
    expect(watch).toContain('application.learning.openPlaybackV1(runId)');
    expect(watch).toContain("setVideoBackStep('history')");
  });
});
