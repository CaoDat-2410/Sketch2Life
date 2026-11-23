import { describe, expect, it } from 'vitest';
import { isRecoverableStoryOutputFailure } from '../src/parent/presentation/navigation/parentFlowV1';

describe('Parent failed story recovery eligibility', () => {
  const eligible = {
    run_state: 'FAILED',
    error_code: 'STORY_OUTPUT_INVALID',
    job_state: 'FAILED',
    retryable: false,
    story_status: 'FAILED',
  } as const;

  it('allows only the deterministic quality-rejected story state', () => {
    expect(isRecoverableStoryOutputFailure(eligible)).toBe(true);
    expect(isRecoverableStoryOutputFailure({ ...eligible, error_code: 'MODAL_EXECUTION_FAILED' })).toBe(false);
    expect(isRecoverableStoryOutputFailure({ ...eligible, job_state: 'AWAITING_RECONCILIATION' })).toBe(false);
    expect(isRecoverableStoryOutputFailure({ ...eligible, retryable: true })).toBe(false);
    expect(isRecoverableStoryOutputFailure({ ...eligible, story_status: 'AWAITING_RECONCILIATION' })).toBe(false);
    expect(isRecoverableStoryOutputFailure({ ...eligible, run_state: 'SCRIPT_GENERATION_UNKNOWN' })).toBe(false);
    expect(isRecoverableStoryOutputFailure(null)).toBe(false);
  });
});
