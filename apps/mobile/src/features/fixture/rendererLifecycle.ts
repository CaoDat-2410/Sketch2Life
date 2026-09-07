export type FixtureRendererEvent = Readonly<{
  sequence: number;
  type: 'RENDERER_READY' | 'PLAYBACK_PROGRESS' | 'RENDERER_ERROR';
}>;

export type FixtureRendererState = Readonly<{
  status: 'idle' | 'ready' | 'playing' | 'error';
  lastSequence: number;
  acceptedEvents: number;
}>;

export const initialFixtureRendererState: FixtureRendererState = {
  status: 'idle',
  lastSequence: 0,
  acceptedEvents: 0,
};

/** Fixture bridge semantics used by the Android-facing E2E harness. */
export function receiveFixtureRendererEvent(
  state: FixtureRendererState,
  event: FixtureRendererEvent,
): FixtureRendererState {
  if (!Number.isInteger(event.sequence) || event.sequence <= state.lastSequence) {
    return state;
  }

  const status =
    event.type === 'RENDERER_READY'
      ? 'ready'
      : event.type === 'PLAYBACK_PROGRESS'
        ? 'playing'
        : 'error';

  return {
    status,
    lastSequence: event.sequence,
    acceptedEvents: state.acceptedEvents + 1,
  };
}
