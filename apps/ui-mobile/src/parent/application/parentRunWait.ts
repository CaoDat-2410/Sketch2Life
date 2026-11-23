/**
 * Waits for a run (or a transcript) to leave the server-working states (goal v3 Phase B). Every Phase B
 * 202 returns no job reference (Q-J), so the adult app follows the story run itself: the same bounds as
 * the job poller (2 s to 10 s, doubling backoff), a total budget, a pause while the app is in the
 * background and a stop when the caller aborts (screen left, sign-out). Nothing here sends a command.
 */
export const RUN_WAIT_MIN_MS = 2_000;
export const RUN_WAIT_MAX_MS = 10_000;
/** The AI job deadline is six hours (SRS l.615); the screen stops waiting much earlier and lets the adult come back. */
export const RUN_WAIT_DEFAULT_BUDGET_MS = 8 * 60_000;

export interface RunWaitAppState {
  currentState: string | null;
  addEventListener(event: 'change', listener: (state: string) => void): { remove(): void };
}

export type RunWaitSleep = (ms: number, signal: AbortSignal) => Promise<void>;

export type RunWaitResult<T> = { value: T; timedOut: false } | { value: T | null; timedOut: true };

export class RunWaitCancelled extends Error {
  constructor() {
    super('RUN_WAIT_CANCELLED');
    this.name = 'RunWaitCancelled';
  }
}

export async function waitForRun<T>(options: {
  /** One read; its failure ends the wait, except for the transient ones `isTransient` accepts. */
  read: (signal: AbortSignal) => Promise<T>;
  /** True when the value is no longer a server-working state. */
  isSettled: (value: T) => boolean;
  sleep: RunWaitSleep;
  signal?: AbortSignal;
  appState?: RunWaitAppState;
  now?: () => number;
  budgetMs?: number;
  isTransient?: (error: unknown) => boolean;
  /** Called with every value read, settled or not (the screen shows progress). */
  onValue?: (value: T) => void;
}): Promise<RunWaitResult<T>> {
  const now = options.now ?? Date.now;
  const budgetMs = options.budgetMs ?? RUN_WAIT_DEFAULT_BUDGET_MS;
  const startedAt = now();
  const controller = new AbortController();
  const abortFromCaller = () => controller.abort();
  options.signal?.addEventListener('abort', abortFromCaller, { once: true });
  // Only `background` pauses: `inactive` and `unknown` never announce a return, so they must not freeze the wait.
  let foreground = options.appState ? options.appState.currentState !== 'background' : true;
  const foregroundWaiters = new Set<() => void>();
  const subscription = options.appState?.addEventListener('change', (next) => {
    foreground = next !== 'background';
    if (foreground) for (const wake of [...foregroundWaiters]) wake();
  });
  const cancelled = () => options.signal?.aborted === true || controller.signal.aborted;

  const waitForForeground = () => new Promise<void>((resolve, reject) => {
    const done = () => { foregroundWaiters.delete(wake); controller.signal.removeEventListener('abort', onAbort); };
    const wake = () => { done(); resolve(); };
    const onAbort = () => { done(); reject(new RunWaitCancelled()); };
    if (cancelled()) { reject(new RunWaitCancelled()); return; }
    foregroundWaiters.add(wake);
    controller.signal.addEventListener('abort', onAbort, { once: true });
  });

  let last: T | null = null;
  let waitMs = RUN_WAIT_MIN_MS;
  let transientFailures = 0;
  try {
    for (;;) {
      if (cancelled()) throw new RunWaitCancelled();
      if (!foreground) {
        await waitForForeground();
        continue;
      }
      try {
        const value = await options.read(controller.signal);
        // A read that finished after the caller left must not write anything (sign-out, a new action).
        if (cancelled()) throw new RunWaitCancelled();
        transientFailures = 0;
        last = value;
        options.onValue?.(value);
        if (options.isSettled(value)) return { value, timedOut: false };
      } catch (error) {
        if (cancelled()) throw new RunWaitCancelled();
        if (error instanceof RunWaitCancelled) throw error;
        const transient = options.isTransient?.(error) === true;
        if (!transient || transientFailures >= 3) throw error;
        transientFailures += 1;
      }
      if (now() - startedAt + waitMs > budgetMs) return { value: last, timedOut: true };
      try {
        await options.sleep(waitMs, controller.signal);
      } catch {
        if (cancelled()) throw new RunWaitCancelled();
      }
      waitMs = Math.min(Math.round(waitMs * 1.5), RUN_WAIT_MAX_MS);
    }
  } finally {
    subscription?.remove();
    options.signal?.removeEventListener('abort', abortFromCaller);
  }
}

export function delayWithSignal(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) { reject(new RunWaitCancelled()); return; }
    const onAbort = () => { clearTimeout(timer); reject(new RunWaitCancelled()); };
    const timer = setTimeout(() => { signal.removeEventListener('abort', onAbort); resolve(); }, ms);
    signal.addEventListener('abort', onAbort, { once: true });
  });
}
