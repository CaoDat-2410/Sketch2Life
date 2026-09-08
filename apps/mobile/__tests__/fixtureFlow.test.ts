import {
  FIXTURE_CONTRACTS,
  createInitialFixtureFlow,
  reduceFixtureFlow,
} from '../src/features/fixture/fixtureFlow';
import {
  initialFixtureRendererState,
  receiveFixtureRendererEvent,
} from '../src/features/fixture/rendererLifecycle';

describe('fixture UI flow state machine', () => {
  it('traverses the approved end-to-end flow with canonical P1 identity', () => {
    let state = createInitialFixtureFlow();
    state = reduceFixtureFlow(state, {type: 'RUN_FIXTURE_AI'});
    state = reduceFixtureFlow(state, {type: 'CONFIRM_GATE_A'});
    state = reduceFixtureFlow(state, {type: 'APPROVE_GATE_B'});
    state = reduceFixtureFlow(state, {type: 'PLAY_EXPERIENCE'});
    state = reduceFixtureFlow(state, {type: 'START_ACTIVITY'});
    state = reduceFixtureFlow(state, {type: 'SUBMIT_FEEDBACK'});

    expect(state.step).toBe('complete');
    expect(state.feedbackSubmitted).toBe(true);
    expect(FIXTURE_CONTRACTS.activityId).toBe('ACT-0004');
    expect(FIXTURE_CONTRACTS.objectiveId).toBe('OBJ_MOVEMENT_COORDINATION');
    expect(state.sessionVersion).toBe(6);
  });

  it('accepts a live backend proposal but still requires Gate A', () => {
    let state = reduceFixtureFlow(createInitialFixtureFlow(), {type: 'START_LIVE_AI'});
    expect(state.step).toBe('capture');
    expect(state.aiStatus).toBe('loading');
    state = reduceFixtureFlow(state, {type: 'LIVE_AI_SUCCEEDED', label: 'butterfly'});

    expect(state.step).toBe('gate-a');
    expect(state.aiMode).toBe('live-backend');
    expect(state.gateAConfirmed).toBe(false);
  });

  it('keeps the activity handoff reachable when media falls back', () => {
    let state = createInitialFixtureFlow();
    for (const type of ['RUN_FIXTURE_AI', 'CONFIRM_GATE_A', 'APPROVE_GATE_B'] as const) {
      state = reduceFixtureFlow(state, {type});
    }
    state = reduceFixtureFlow(state, {type: 'SIMULATE_MEDIA_FALLBACK'});
    state = reduceFixtureFlow(state, {type: 'PLAY_EXPERIENCE'});

    expect(state.mediaStatus).toBe('fallback');
    expect(state.step).toBe('handoff');
  });

  it('does not skip gates or mutate on duplicate commands', () => {
    const initial = createInitialFixtureFlow();
    expect(reduceFixtureFlow(initial, {type: 'APPROVE_GATE_B'})).toEqual(initial);
    const proposed = reduceFixtureFlow(initial, {type: 'RUN_FIXTURE_AI'});
    expect(reduceFixtureFlow(proposed, {type: 'RUN_FIXTURE_AI'})).toEqual(proposed);
  });
});

describe('fixture renderer lifecycle', () => {
  it('ignores duplicate and out-of-order bridge events', () => {
    let state = initialFixtureRendererState;
    state = receiveFixtureRendererEvent(state, {sequence: 2, type: 'RENDERER_READY'});
    state = receiveFixtureRendererEvent(state, {sequence: 2, type: 'PLAYBACK_PROGRESS'});
    state = receiveFixtureRendererEvent(state, {sequence: 1, type: 'RENDERER_ERROR'});

    expect(state).toEqual({status: 'ready', lastSequence: 2, acceptedEvents: 1});
    state = receiveFixtureRendererEvent(state, {sequence: 3, type: 'PLAYBACK_PROGRESS'});
    expect(state.status).toBe('playing');
  });
});
