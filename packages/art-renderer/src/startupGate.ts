export interface RendererStartupGate {
  receive(message: string): void;
  markReady(): void;
  markFailed(): void;
}

/**
 * Holds at most one WebView launch while Pixi initializes and ignores bridge
 * replays after it has been handled. The caller remains responsible for
 * validating the message before passing it to this gate.
 */
export function createRendererStartupGate(
  onReady: (message: string) => void,
  onFailed: (message: string) => void,
): RendererStartupGate {
  let state: 'INITIALIZING' | 'READY' | 'FAILED' = 'INITIALIZING';
  let queuedMessage: string | null = null;
  let handledMessage: string | null = null;

  const handleOnce = (message: string, handler: (message: string) => void) => {
    if (handledMessage !== null) return;
    handledMessage = message;
    handler(message);
  };

  return {
    receive(message) {
      if (state === 'READY') {
        handleOnce(message, onReady);
        return;
      }
      if (state === 'FAILED') {
        handleOnce(message, onFailed);
        return;
      }
      if (queuedMessage === null) queuedMessage = message;
    },
    markReady() {
      if (state !== 'INITIALIZING') return;
      state = 'READY';
      const message = queuedMessage;
      queuedMessage = null;
      if (message !== null) handleOnce(message, onReady);
    },
    markFailed() {
      if (state !== 'INITIALIZING') return;
      state = 'FAILED';
      const message = queuedMessage;
      queuedMessage = null;
      if (message !== null) handleOnce(message, onFailed);
    },
  };
}
