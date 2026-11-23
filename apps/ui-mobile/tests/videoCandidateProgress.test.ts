import { describe, expect, it } from 'vitest';
import { videoCandidateProgressFor } from '../src/parent/presentation/screens/videoCandidateProgress';

describe('Parent video candidate progress', () => {
  it.each([
    ['STAGING', ['current', 'upcoming', 'upcoming', 'upcoming']],
    ['DISPATCHING', ['complete', 'current', 'upcoming', 'upcoming']],
    ['QUEUED', ['complete', 'current', 'upcoming', 'upcoming']],
    ['GENERATING', ['complete', 'complete', 'current', 'upcoming']],
    ['CANDIDATE_READY', ['complete', 'complete', 'complete', 'complete']],
  ] as const)('maps %s to the matching visible phases', (candidateState, expectedStates) => {
    const progress = videoCandidateProgressFor(candidateState);
    expect(progress?.map((step) => step.state)).toEqual(expectedStates);
  });

  it.each(['FAILED', 'AWAITING_RECONCILIATION'] as const)(
    'does not show a false progress track for %s',
    (candidateState) => {
      expect(videoCandidateProgressFor(candidateState)).toBeNull();
    },
  );
});
