import { readFileSync } from 'node:fs';
import { describe, expect, it, vi } from 'vitest';
import { runHistoryStateLabel } from '../src/parent/application/parentRunHistory';
import type { ParentStoryRunSummary } from '../src/parent/domain/types';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import {
  parentRecoveryGroupForError,
  readSubjectConfirmationOutcome,
  safeParentFlowErrorMessage,
} from '../src/parent/presentation/navigation/parentFlowV1';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { firebaseApiKey: 'synthetic-firebase-key', apiBaseUrl: 'https://parent.example.test' },
}));

function apiWith(status: number, body: Record<string, unknown>) {
  const fetcher = vi.fn(async () => new Response(JSON.stringify(body), { status }));
  const api = new ParentApi({ getIdToken: async () => 'synthetic-token' }, fetcher as unknown as typeof fetch, 'https://parent.example.test');
  return { api, fetcher };
}

const expected = { runId: 'run-1', understandingRevision: 2, subjectEdited: false };
const body = (overrides: Record<string, unknown> = {}) => ({
  request_id: 'r', story_run_id: 'run-1', understanding_revision: 2, decision: 'CONFIRMED', run_revision: 5, ...overrides,
});

describe('Phase B subject confirmation (202, RERUN_REQUESTED)', () => {
  it('returns the 202 body, including a rerun request, instead of treating it as an error', async () => {
    const { api } = apiWith(202, body({ decision: 'RERUN_REQUESTED' }));
    const response = await api.confirmStoryRunSubjectV1('run-1', 2, 'con bướm', 'key-1');
    expect(response.decision).toBe('RERUN_REQUESTED');
    expect(response.run_revision).toBe(5);
  });

  it('separates a confirmed subject, a pending rerun and an invalid answer', () => {
    expect(readSubjectConfirmationOutcome(body(), expected)).toBe('confirmed');
    expect(readSubjectConfirmationOutcome(body({ decision: 'RERUN_REQUESTED' }), expected)).toBe('rerun-requested');
    expect(readSubjectConfirmationOutcome(body({ decision: 'SOMETHING_NEW' }), expected)).toBe('invalid');
    expect(readSubjectConfirmationOutcome(body({ story_run_id: 'run-2' }), expected)).toBe('invalid');
    expect(readSubjectConfirmationOutcome(body({ understanding_revision: '2' }), expected)).toBe('invalid');
    expect(readSubjectConfirmationOutcome(null, expected)).toBe('invalid');
    expect(readSubjectConfirmationOutcome('text', expected)).toBe('invalid');
  });

  it('accepts the next revision only for an edited subject that the server confirmed at once', () => {
    const edited = { ...expected, subjectEdited: true };
    expect(readSubjectConfirmationOutcome(body({ understanding_revision: 3 }), edited)).toBe('confirmed');
    expect(readSubjectConfirmationOutcome(body({ understanding_revision: 3 }), expected)).toBe('invalid');
    expect(readSubjectConfirmationOutcome(body({ understanding_revision: 4 }), edited)).toBe('invalid');
    expect(readSubjectConfirmationOutcome(body({ decision: 'RERUN_REQUESTED', understanding_revision: 3 }), edited)).toBe('invalid');
  });

  it('never shows a rerun as confirmed: the controller reads the outcome and refreshes the run', () => {
    const source = readFileSync('src/parent/presentation/navigation/useParentController.ts', 'utf8');
    expect(source).toContain("outcome === 'rerun-requested'");
    expect(source).toContain("code: 'SUBJECT_RERUN_PENDING'");
    expect(source).not.toContain("response.decision !== 'CONFIRMED'");
  });
});

describe('Phase B error and state degradation', () => {
  it('keeps a wrong-role 404 and unknown new codes on safe Vietnamese messages', async () => {
    const { api } = apiWith(404, { code: 'RESOURCE_NOT_FOUND' });
    const error = await api.getStoryRunV1('run-1').catch((cause: unknown) => cause);
    expect(error).toBeInstanceOf(ParentApiError);
    expect((error as ParentApiError).status).toBe(404);
    expect(safeParentFlowErrorMessage(error)).toBe('Không tìm thấy nội dung hoặc bạn không thể truy cập nội dung này.');
    expect(parentRecoveryGroupForError(error)).toBe('resource-refresh');
    expect(safeParentFlowErrorMessage({ code: 'PROFILE_NOT_FOUND' })).toBe('Hồ sơ không còn khả dụng.');
    for (const code of ['INVALID_REQUEST', 'SOME_FUTURE_CODE']) {
      const message = safeParentFlowErrorMessage({ code });
      expect(message).toBe('Chưa thể hoàn tất thao tác. Vui lòng kiểm tra lại sau.');
      expect(message).not.toContain(code);
    }
    // The two video failure codes of T-1c now have calm Vietnamese copy and lead back to the story review.
    for (const code of ['VIDEO_TECHNICAL_FAILURE', 'VIDEO_DEADLINE_EXCEEDED']) {
      const message = safeParentFlowErrorMessage({ code });
      expect(message).toContain('Lượt này vẫn được tính');
      expect(message).not.toContain(code);
      expect(parentRecoveryGroupForError({ code })).toBe('story-review');
    }
    for (const code of [
      'PARENT_ACTIVITY_SELECTION_REQUIRED', 'DEPENDENCY_UNAVAILABLE', 'PARENT_STORY_RUN_STORE_UNAVAILABLE',
      'SUBJECT_NOT_CONFIRMED', 'STALE_REVISION', 'INVALID_STATE_TRANSITION', 'VIDEO_REGENERATION_LIMIT_REACHED',
      'VIDEO_SAFETY_BLOCKED', 'STORAGE_UNAVAILABLE', 'PROVIDER_UNAVAILABLE',
    ]) {
      const message = safeParentFlowErrorMessage({ code, message: `private ${code}` });
      expect(message).not.toContain(code);
      expect(message).not.toContain(`private ${code}`);
    }
  });

  it('routes a completed history row into a fresh run read and playback grant', () => {
    const historyScreen = readFileSync('src/parent/presentation/screens/StoryHistoryScreen.tsx', 'utf8');
    const controller = readFileSync('src/parent/presentation/navigation/useParentController.ts', 'utf8');
    expect(historyScreen).toContain("run.run_state === 'COMPLETED'");
    expect(historyScreen).toContain('props.onWatch(run.run_id)');
    const start = controller.indexOf('async function watchHistoryRun');
    const end = controller.indexOf('function onPlaybackError', start);
    const watch = controller.slice(start, end);
    expect(watch).toContain('readLiveRun(runId)');
    expect(watch).toContain("run.run_state !== 'COMPLETED'");
    expect(watch).toContain("run.video?.state !== 'READY'");
    expect(watch).toContain('application.learning.openPlaybackV1(runId)');
  });

  it('re-confirms only the same spent story revision after a fresh run read', () => {
    const controller = readFileSync('src/parent/presentation/navigation/useParentController.ts', 'utf8');
    const start = controller.indexOf('async function confirmStory');
    const end = controller.indexOf('async function resumeActiveRun', start);
    const confirm = controller.slice(start, end);
    expect(confirm).toContain('getLatestRun(runId)');
    expect(confirm).toContain("latest.story_confirmation_required === true");
    expect(confirm).toContain("latest.story_status === 'CONFIRMED'");
    expect(confirm).toContain('latest.story_revision_no !== revisionNo');
    expect(confirm).toContain('latest.story_sha256 !== revisionSha256');
    expect(confirm).toContain('retainedActionIdentity(scriptConfirmationAction, signature)');
    expect(confirm).toContain('scriptConfirmationAction.current = null');
    expect(confirm).toContain('application.learning.confirmScriptV1(runId, revisionNo, revisionSha256, actionIdentity)');
  });

  it('words the pending subject rerun and routes it to the subject review', () => {
    expect(safeParentFlowErrorMessage({ code: 'SUBJECT_RERUN_PENDING' })).toContain('xem lại bức tranh');
    expect(parentRecoveryGroupForError({ code: 'SUBJECT_RERUN_PENDING' })).toBe('subject-review');
  });

  it('labels INPUT_REVIEW and degrades unknown or new run states without throwing', () => {
    const run = (run_state: string): ParentStoryRunSummary => ({
      run_id: 'a', parent_profile_id: 'p', run_state, revision: 1, deleting: false,
      can_cancel: true, can_delete: false, created_at: '2026-11-21T00:00:00Z', updated_at: '2026-11-21T00:00:00Z',
    });
    expect(runHistoryStateLabel(run('INPUT_REVIEW'))).toBe('Chờ xem lại ảnh và ý tưởng');
    for (const state of ['VIDEO_QUEUED', 'VIDEO_READY', 'SAFETY_BLOCKED', 'DELETED', 'NOT_A_STATE']) {
      expect(() => runHistoryStateLabel(run(state))).not.toThrow();
    }
    expect(runHistoryStateLabel(run('VIDEO_QUEUED'))).toBe('Video đang chờ xử lý');
    expect(runHistoryStateLabel(run('VIDEO_READY'))).toBe('Video đã sẵn sàng');
    expect(runHistoryStateLabel(run('NOT_A_STATE'))).toBe('Trạng thái chưa xác định');
    for (const file of ['HomeScreen', 'StoryHistoryScreen']) {
      expect(readFileSync(`src/parent/presentation/screens/${file}.tsx`, 'utf8')).toContain('Chờ xem lại ảnh và ý tưởng');
    }
  });
});

describe('Phase B Idempotency-Key rules (1 to 128 visible ASCII on the /v1/story-runs commands)', () => {
  it('refuses an empty, 129-character or non-visible key before any request, and accepts 128', async () => {
    const { api, fetcher } = apiWith(202, body());
    const confirm = (key: string) => api.confirmStoryRunSubjectV1('run-1', 2, 'con bướm', key);
    for (const bad of ['', 'k'.repeat(129), 'has space', 'khoa-é']) {
      expect(() => confirm(bad)).toThrow(ParentApiError);
    }
    expect(fetcher).not.toHaveBeenCalled();
    await confirm('k'.repeat(128));
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
