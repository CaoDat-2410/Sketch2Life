import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import type { ParentStoryRunV1 } from '../src/parent/domain/types';
import { classifyRewriteProgress } from '../src/parent/application/parentPhaseB';
import {
  isRecoverableFirstStoryFailure,
  isRecoverableStoryOutputFailure,
  STORY_RECOVERY_COPY,
} from '../src/parent/presentation/navigation/parentFlowV1';

describe('Parent failed story recovery eligibility', () => {
  const eligible = {
    run_state: 'FAILED',
    error_code: 'STORY_OUTPUT_INVALID',
    job_state: 'FAILED',
    retryable: false,
    story_status: 'FAILED',
  } as const;

  it('retains the dev eligibility helper for the deterministic quality-rejected story state', () => {
    expect(isRecoverableStoryOutputFailure(eligible)).toBe(true);
    expect(isRecoverableStoryOutputFailure({ ...eligible, error_code: 'MODAL_EXECUTION_FAILED' })).toBe(false);
    expect(isRecoverableStoryOutputFailure({ ...eligible, job_state: 'AWAITING_RECONCILIATION' })).toBe(false);
    expect(isRecoverableStoryOutputFailure({ ...eligible, retryable: true })).toBe(false);
    expect(isRecoverableStoryOutputFailure({ ...eligible, story_status: 'AWAITING_RECONCILIATION' })).toBe(false);
    expect(isRecoverableStoryOutputFailure({ ...eligible, run_state: 'SCRIPT_GENERATION_UNKNOWN' })).toBe(false);
    expect(isRecoverableStoryOutputFailure(null)).toBe(false);
  });
});

const controllerSource = readFileSync(
  new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url),
  'utf8',
);

const recoveryStart = controllerSource.indexOf('async function recoverFirstStory');
const followStart = controllerSource.indexOf('async function followStoryRecovery', recoveryStart);
const cancelStart = controllerSource.indexOf('async function cancelEmptyActivityRun', followStart);
const recoverySource = controllerSource.slice(recoveryStart, followStart);
const followSource = controllerSource.slice(followStart, cancelStart);

describe('first story failure recovery controller contract', () => {
  it('retains one dedicated recovery identity until the outcome is definitive', () => {
    expect(controllerSource).toContain('const storyRecoveryAction = useRef<RetainedActionIdentity | null>(null)');
    expect(recoverySource).toContain('retainedActionIdentity(storyRecoveryAction, storyRecoverySignature(run.run_id, hint))');
    expect(recoverySource).not.toContain('storyRewriteAction');
    expect(recoverySource).not.toContain('readStoryRevisionReadModel');

    const catchStart = recoverySource.indexOf('} catch (cause) {');
    const finallyStart = recoverySource.indexOf('} finally {', catchStart);
    const catchSource = recoverySource.slice(catchStart, finallyStart);
    expect(catchSource).toContain("cause.code === 'STALE_REVISION'");
    expect(catchSource).toContain("cause.code === 'STORY_REWRITE_LIMIT_REACHED'");
    expect(catchSource).toContain("cause.code === 'INVALID_STATE_TRANSITION'");
    expect(catchSource).not.toContain("cause.code === 'ACTIVE_RUN_EXISTS'");
    expect(catchSource).not.toContain("cause.code === 'PARENT_REWRITE_HINT_INVALID'");
    expect(followSource).toContain("if (progress.kind === 'ready')");
    expect(followSource).toContain("if (run.run_state === 'FAILED')");
    expect(followSource).toContain('storyRecoveryAction.current = null');

    const resetStart = controllerSource.indexOf('function resetWorkflow(): void');
    const resetEnd = controllerSource.indexOf('return {', resetStart);
    expect(controllerSource.slice(resetStart, resetEnd)).toContain('storyRecoveryAction.current = null');
  });

  it('preserves profile and Phase A guards and follows accepted work before dispatch', () => {
    expect(recoverySource).toContain('if (busy || !run || !ensureLearningProfileAllowed(profile)) return;');
    expect(recoverySource).toContain('readVideoPanel(run, { spentRevisionNo: spentStoryRevisionNo, confirmedRevisionNo: confirmedStoryRevisionNo }).onlyCancel');
    expect(recoverySource).toContain("latest.run_state === 'SCRIPT_GENERATING' || latest.run_state === 'STORY_GENERATING'");
    expect(recoverySource).toContain("latest.run_state === 'SCRIPT_GENERATION_UNKNOWN'");
    expect(recoverySource).toContain("latest.run_state === 'PREPARATION_REVIEW'");
    expect(recoverySource).toContain('await handleStoryGateResult(latest, false)');
    expect(recoverySource.indexOf("latest.run_state === 'SCRIPT_GENERATING'"))
      .toBeLessThan(recoverySource.indexOf('application.learning.rewriteStoryV1'));
    expect(recoverySource.indexOf("latest.run_state === 'SCRIPT_GENERATION_UNKNOWN'"))
      .toBeLessThan(recoverySource.indexOf('application.learning.rewriteStoryV1'));
    expect(recoverySource.indexOf("latest.run_state === 'PREPARATION_REVIEW'"))
      .toBeLessThan(recoverySource.indexOf('application.learning.rewriteStoryV1'));
    expect(recoverySource).toContain("timeRequest('story-recovery'");

    const gateStart = controllerSource.indexOf('async function handleStoryGateResult');
    const firstWaitStart = controllerSource.indexOf('async function followFirstStory', gateStart);
    const gateSource = controllerSource.slice(gateStart, firstWaitStart);
    expect(gateSource).toContain("if (run.run_state === 'PREPARATION_REVIEW')");
    expect(gateSource).toContain("run.main_activity?.state !== 'SELECTED'");
    expect(gateSource).toContain('run.context_confirmed !== true');
  });

  it('uses the recovery prompt only for eligible first-story failures at both existing failure sites', () => {
    const gateStart = controllerSource.indexOf('async function handleStoryGateResult');
    const firstWaitStart = controllerSource.indexOf('async function followFirstStory', gateStart);
    const gateSource = controllerSource.slice(gateStart, firstWaitStart);
    const firstWaitEnd = controllerSource.indexOf('async function recoverFirstStory', firstWaitStart);
    const firstWaitSource = controllerSource.slice(firstWaitStart, firstWaitEnd);

    expect(gateSource).toContain('isRecoverableFirstStoryFailure(run)');
    expect(firstWaitSource).toContain('isRecoverableFirstStoryFailure(latest, runId)');
    expect(gateSource).toContain('Chưa tạo được câu chuyện. Hãy bắt đầu một buổi học mới.');
    expect(firstWaitSource).toContain('Chưa tạo được câu chuyện. Hãy bắt đầu một buổi học mới.');
    expect(gateSource).toContain('STORY_RECOVERY_COPY.eligibleFailure');
    expect(firstWaitSource).toContain('STORY_RECOVERY_COPY.eligibleFailure');
    expect(followSource).not.toContain('Câu chuyện hiện tại vẫn được giữ');
  });

  it('closes a failed revision 2 without claiming that a story was kept', () => {
    const failedRecovery = {
      run_id: 'synthetic-run',
      run_state: 'FAILED',
      story_revision_no: 2,
      story_status: 'FAILED',
      job_state: 'FAILED',
      error_code: 'STORY_OUTPUT_INVALID',
      retryable: false,
    } as unknown as ParentStoryRunV1;

    expect(classifyRewriteProgress(failedRecovery, { fromRevisionNo: 1, toRevisionNo: 2 }))
      .toEqual({ kind: 'closed', state: 'FAILED' });
    expect(isRecoverableFirstStoryFailure(failedRecovery, 'synthetic-run')).toBe(false);
    expect(followSource).toContain('STORY_RECOVERY_COPY.terminalFailure');
    expect(followSource).not.toContain('Câu chuyện hiện tại vẫn được giữ');
    expect(STORY_RECOVERY_COPY.terminalFailure)
      .toBe('Vẫn chưa tạo được câu chuyện nên buổi học đã dừng. Chưa có câu chuyện nào để xem. Bạn có thể xem lịch sử hoặc bắt đầu một buổi học mới.');
  });
});
