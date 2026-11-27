/**
 * FEAT-094: the two defects of the app runs, as pure functions (no React, no storage).
 */
import type { ParentProfileRecordV1, ParentProfileViewV1 } from '../domain/types';

export const ACTIVITY_PENDING_RETRY_MS = 15_000;
/** A cold model start takes several minutes; the app keeps waiting this long before it asks the adult to retry. */
export const ACTIVITY_PENDING_LIMIT_MS = 8 * 60_000;

/**
 * The profile of a resumed run. Right after signing in the profile list may not be loaded yet, so it is read from the
 * server instead of asking the adult to choose a profile for a session that already has one.
 */
export async function resolveResumeProfile(
  loaded: readonly ParentProfileViewV1[],
  profileId: string | null | undefined,
  read: (profileId: string) => Promise<ParentProfileRecordV1>,
): Promise<ParentProfileViewV1 | null> {
  if (!profileId) return null;
  const known = loaded.find((profile) => profile.profile_id === profileId);
  if (known) return known;
  try {
    const record = await read(profileId);
    return record.state === 'ACTIVE' && record.profile_id === profileId ? record : null;
  } catch {
    return null;
  }
}

/**
 * Runs one idempotent command again while the server says it is still working. The caller passes the same action
 * identity every time, so a repeated call replays the stored result and never starts a second one.
 */
export async function waitForPendingResult<T>(
  call: () => Promise<T>,
  options: {
    isPending: (cause: unknown) => boolean;
    sleep?: (milliseconds: number) => Promise<void>;
    now?: () => number;
    stopped?: () => boolean;
  },
): Promise<T> {
  const sleep = options.sleep ?? ((milliseconds: number) => new Promise<void>((resolve) => setTimeout(resolve, milliseconds)));
  const now = options.now ?? Date.now;
  const deadline = now() + ACTIVITY_PENDING_LIMIT_MS;
  for (;;) {
    try {
      return await call();
    } catch (cause) {
      if (!options.isPending(cause) || options.stopped?.() || now() >= deadline) throw cause;
      await sleep(ACTIVITY_PENDING_RETRY_MS);
      if (options.stopped?.() || now() >= deadline) throw cause;
    }
  }
}
