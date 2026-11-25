import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  PARENT_DRAWING_TERMINAL_MESSAGE,
  hasUsedDrawingRetake,
  isSafePreDispatchDrawingError,
  isTerminalFailedStoryRun,
  terminalDrawingFailureMessage,
} from '../src/parent/presentation/navigation/parentFlowV1';
import { ParentApplicationError } from '../src/parent/application/ParentApplicationError';

describe('terminal drawing failure recovery', () => {
  it('restores the one-retake limit from the server input revision after app restart', () => {
    expect(hasUsedDrawingRetake(1)).toBe(false);
    expect(hasUsedDrawingRetake(2)).toBe(true);
    expect(hasUsedDrawingRetake(null)).toBe(false);
    expect(hasUsedDrawingRetake(2.5)).toBe(false);

    const source = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
    const resume = source.slice(source.indexOf('async function resumeActiveRun'), source.indexOf('// Goal v3 Phase B'));
    const restoreRetake = resume.indexOf('retakeUsed.current = hasUsedDrawingRetake(run.current_input_revision)');
    expect(restoreRetake).toBeGreaterThan(-1);
    expect(restoreRetake).toBeLessThan(resume.indexOf('await resumePhaseBRun(run)'));
  });

  it('treats only a FAILED run as terminal', () => {
    expect(isTerminalFailedStoryRun({ run_state: 'FAILED', job_state: 'FAILED', retryable: false })).toBe(true);
    expect(isTerminalFailedStoryRun({ run_state: 'INPUT_PROCESSING', job_state: 'AWAITING_RECONCILIATION' })).toBe(false);
    expect(isTerminalFailedStoryRun({ run_state: 'SUBJECT_REVIEW' })).toBe(false);
    expect(isTerminalFailedStoryRun(null)).toBe(false);
  });

  it('explains the failure and the only safe action without "still waiting" wording', () => {
    const message = terminalDrawingFailureMessage('DRAWING_OUTPUT_INVALID');
    expect(message).toContain('Chưa đọc được tranh lần này');
    expect(message).toContain(PARENT_DRAWING_TERMINAL_MESSAGE);
    expect(message).not.toContain('chưa trả về kết quả');
    expect(terminalDrawingFailureMessage(null)).toBe(PARENT_DRAWING_TERMINAL_MESSAGE);
  });

  it('checks run_state before the attached-photo "awaiting result" branches and does not cancel a FAILED run', () => {
    const source = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
    const analyze = source.slice(source.indexOf('async function analyzeDrawingForRun'), source.indexOf('async function analyzeDrawingForCurrentRun'));
    const terminalCheck = analyze.indexOf('if (isTerminalFailedStoryRun(latest))');
    expect(terminalCheck).toBeGreaterThan(-1);
    expect(terminalCheck).toBeLessThan(analyze.indexOf('if (revision > 1 &&'));
    const catchBlock = analyze.slice(analyze.indexOf('} catch (cause) {'));
    expect(catchBlock.indexOf('isTerminalFailedStoryRun(latest)')).toBeGreaterThan(-1);
    expect(catchBlock.indexOf('isTerminalFailedStoryRun(latest)')).toBeLessThan(catchBlock.indexOf('analysisError: safeParentFlowErrorMessage(cause)'));
    const close = source.slice(source.indexOf('async function closeUnresolvedDrawingRun'), source.indexOf('async function confirmSubject'));
    expect(close.indexOf('if (!isTerminalFailedStoryRun(latest))')).toBeLessThan(close.indexOf('cancelRunV1(runId'));
  });

  it('shows a close action instead of "Kiểm tra trạng thái buổi học" for a terminal run', () => {
    const screen = readFileSync(new URL('../src/parent/presentation/screens/CaptureScreen.tsx', import.meta.url), 'utf8');
    expect(screen).toContain('analysisFailed && !retakeAvailable');
    expect(screen).toContain('Đóng buổi và bắt đầu lại');
  });

  it('shows server drawing errors and allows status/close actions without a local photo after resume', () => {
    const screen = readFileSync(new URL('../src/parent/presentation/screens/CaptureScreen.tsx', import.meta.url), 'utf8');
    const route = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
    expect(screen).toContain('flowError ? <Notice variant="creative" text={flowError}');
    expect(screen).toContain("runExists && !photo ? 'Kiểm tra trạng thái buổi học'");
    expect(route).toContain('flowError={parent.error}');
    expect(route).toContain("analysisFailed={parent.contextRun?.run_state === 'INPUT_REVIEW'");
    expect(route).toContain('onCheckStatus={() => void parent.resumeActiveRun()}');
  });

  it('starts a fresh topic draft after closing a terminal drawing failure', () => {
    const source = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
    const close = source.slice(source.indexOf('async function closeUnresolvedDrawingRun'), source.indexOf('function renameSecondarySubject'));
    expect(close).toContain('await beginTopicPath()');
    expect(close).not.toContain("setStep('topic')");
  });

  it('allows a retry only for typed 503 failures proven to happen before inference dispatch', () => {
    for (const code of [
      'MODAL_AI_NOT_ENABLED',
      'PARENT_ARTWORK_SCAN_UNAVAILABLE',
      'PARENT_ARTWORK_STORAGE_UNAVAILABLE',
      'PARENT_STORY_RUN_STORE_UNAVAILABLE',
      'UPLOAD_SESSION_CREATE_UNAVAILABLE',
    ]) {
      expect(isSafePreDispatchDrawingError(new ParentApplicationError(code, 'safe', 'req-1', 503))).toBe(true);
    }

    expect(isSafePreDispatchDrawingError(new ParentApplicationError('DRAWING_OUTCOME_UNKNOWN', 'safe', 'req-2', 504))).toBe(false);
    expect(isSafePreDispatchDrawingError(new ParentApplicationError('DRAWING_OUTPUT_INVALID', 'safe', 'req-3', 502))).toBe(false);
    expect(isSafePreDispatchDrawingError(new ParentApplicationError('PARENT_DRAWING_RESULT_STORE_UNAVAILABLE', 'safe', 'req-4', 503))).toBe(false);
    expect(isSafePreDispatchDrawingError(new ParentApplicationError('PARENT_STORY_RUN_STORE_UNAVAILABLE', 'safe'))).toBe(false);
    expect(isSafePreDispatchDrawingError(new Error('network failure'))).toBe(false);
  });

  it('rechecks the same run revision and consumes only one explicit UI retry', () => {
    const source = readFileSync(new URL('../src/parent/presentation/navigation/useParentController.ts', import.meta.url), 'utf8');
    const analyze = source.slice(source.indexOf('async function analyzeDrawingForRun'), source.indexOf('async function analyzeDrawingForCurrentRun'));
    expect(analyze).toContain('selectedPhoto.analysisRetryable === true');
    expect(analyze).toContain('drawingAnalysisRetryRunId.current !== runId');
    expect(analyze.indexOf('if (revision > 1 && !retakeAvailable')).toBeLessThan(analyze.indexOf('application.learning.attachDrawingV1'));
    expect(analyze).toContain('isSafePreDispatchDrawingError(cause)');
    expect(analyze).toContain('drawingAnalysisRetryRunId.current = runId');

    const screen = readFileSync(new URL('../src/parent/presentation/screens/CaptureScreen.tsx', import.meta.url), 'utf8');
    expect(screen).toContain("photo?.analysisRetryable ? 'Thử lại nhận diện tranh'");
  });
});
