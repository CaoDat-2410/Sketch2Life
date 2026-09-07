export const FIXTURE_FLOW_CONTRACT_VERSION = '1.0' as const;

export type FixtureFlowStep =
  | 'capture'
  | 'gate-a'
  | 'gate-b'
  | 'experience'
  | 'handoff'
  | 'feedback'
  | 'complete';

export type FixtureFlowState = Readonly<{
  step: FixtureFlowStep;
  sessionVersion: number;
  aiStatus: 'idle' | 'loading' | 'ready' | 'error';
  aiMode: 'fixture' | 'live-backend';
  aiError: string | null;
  proposalLabel: string | null;
  gateAConfirmed: boolean;
  gateBApproved: boolean;
  mediaStatus: 'pending' | 'cache-hit' | 'fallback';
  rendererStatus: 'idle' | 'ready' | 'played';
  feedbackSubmitted: boolean;
}>;

export type FixtureFlowAction =
  | Readonly<{type: 'RUN_FIXTURE_AI'}>
  | Readonly<{type: 'START_LIVE_AI'}>
  | Readonly<{type: 'LIVE_AI_SUCCEEDED'; label: string | null}>
  | Readonly<{type: 'LIVE_AI_FAILED'; message: string}>
  | Readonly<{type: 'CONFIRM_GATE_A'}>
  | Readonly<{type: 'APPROVE_GATE_B'}>
  | Readonly<{type: 'PLAY_EXPERIENCE'}>
  | Readonly<{type: 'SIMULATE_MEDIA_FALLBACK'}>
  | Readonly<{type: 'START_ACTIVITY'}>
  | Readonly<{type: 'SUBMIT_FEEDBACK'}>
  | Readonly<{type: 'RESET'}>;

export const FIXTURE_CONTRACTS = Object.freeze({
  sessionId: 'session-fixture-001',
  sourceArtifactId: 'child-drawing-001-whole',
  sourceArtifactVersion: 1,
  activityId: 'ACT-0004',
  activityVersion: 2,
  objectiveId: 'OBJ_MOVEMENT_COORDINATION',
  objectiveVersion: 1,
  understandingLabel: 'butterfly',
  understandingConfidence: 0.94,
  rendererPlanId: 'integration-butterfly-reveal',
  contractVersion: FIXTURE_FLOW_CONTRACT_VERSION,
});

export function createInitialFixtureFlow(): FixtureFlowState {
  return {
    step: 'capture',
    sessionVersion: 1,
    aiStatus: 'idle',
    aiMode: 'fixture',
    aiError: null,
    proposalLabel: null,
    gateAConfirmed: false,
    gateBApproved: false,
    mediaStatus: 'pending',
    rendererStatus: 'idle',
    feedbackSubmitted: false,
  };
}

export function reduceFixtureFlow(
  state: FixtureFlowState,
  action: FixtureFlowAction,
): FixtureFlowState {
  switch (action.type) {
    case 'RUN_FIXTURE_AI':
      return state.step === 'capture'
        ? {
            ...state,
            step: 'gate-a',
            sessionVersion: 2,
            aiStatus: 'ready',
            aiMode: 'fixture',
            aiError: null,
            proposalLabel: FIXTURE_CONTRACTS.understandingLabel,
          }
        : state;
    case 'START_LIVE_AI':
      return state.step === 'capture'
        ? {...state, aiStatus: 'loading', aiMode: 'live-backend', aiError: null}
        : state;
    case 'LIVE_AI_SUCCEEDED':
      return state.step === 'capture' && state.aiStatus === 'loading'
        ? {
            ...state,
            step: 'gate-a',
            sessionVersion: 2,
            aiStatus: 'ready',
            aiMode: 'live-backend',
            aiError: null,
            proposalLabel: action.label,
          }
        : state;
    case 'LIVE_AI_FAILED':
      return state.step === 'capture'
        ? {...state, aiStatus: 'error', aiMode: 'live-backend', aiError: action.message}
        : state;
    case 'CONFIRM_GATE_A':
      return state.step === 'gate-a' && state.aiStatus === 'ready'
        ? {
            ...state,
            step: 'gate-b',
            sessionVersion: 3,
            gateAConfirmed: true,
          }
        : state;
    case 'APPROVE_GATE_B':
      return state.step === 'gate-b' && state.gateAConfirmed
        ? {
            ...state,
            step: 'experience',
            sessionVersion: 4,
            gateBApproved: true,
            mediaStatus: 'cache-hit',
            rendererStatus: 'ready',
          }
        : state;
    case 'PLAY_EXPERIENCE':
      return state.step === 'experience' && state.rendererStatus === 'ready'
        ? {...state, step: 'handoff', rendererStatus: 'played'}
        : state;
    case 'SIMULATE_MEDIA_FALLBACK':
      return state.step === 'experience' ? {...state, mediaStatus: 'fallback'} : state;
    case 'START_ACTIVITY':
      return state.step === 'handoff'
        ? {...state, step: 'feedback', sessionVersion: 5}
        : state;
    case 'SUBMIT_FEEDBACK':
      return state.step === 'feedback'
        ? {...state, step: 'complete', sessionVersion: 6, feedbackSubmitted: true}
        : state;
    case 'RESET':
      return createInitialFixtureFlow();
    default:
      return state;
  }
}
