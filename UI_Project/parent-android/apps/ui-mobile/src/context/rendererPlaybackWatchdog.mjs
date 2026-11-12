export const RENDERER_HANDSHAKE_TIMEOUT_MS = 20_000;
export const RENDERER_PREPARATION_TIMEOUT_MS = 90_000;
export const RENDERER_PLAYBACK_HEARTBEAT_TIMEOUT_MS = 8_000;

export function rendererWatchdogDeadline({
  pageActive,
  failed,
  handshakeReceived,
  commandAccepted,
  durationSeconds,
  state,
  lastProgressAt,
  now = Date.now(),
}) {
  if (!pageActive || failed || state === 'PAUSED' || state === 'COMPLETED') return null;
  if (!handshakeReceived) {
    return {stage: 'HANDSHAKE', remainingMs: RENDERER_HANDSHAKE_TIMEOUT_MS};
  }
  if (!commandAccepted || durationSeconds <= 0) {
    return {stage: 'PREPARATION', remainingMs: RENDERER_PREPARATION_TIMEOUT_MS};
  }
  if (state === 'READY') {
    return {stage: 'STARTUP', remainingMs: RENDERER_PLAYBACK_HEARTBEAT_TIMEOUT_MS};
  }
  if (state === 'PLAYING') {
    const elapsed = Math.max(0, now - lastProgressAt);
    return {
      stage: 'PLAYBACK',
      remainingMs: Math.max(1, RENDERER_PLAYBACK_HEARTBEAT_TIMEOUT_MS - elapsed),
    };
  }
  return {stage: 'STARTUP', remainingMs: RENDERER_PLAYBACK_HEARTBEAT_TIMEOUT_MS};
}
