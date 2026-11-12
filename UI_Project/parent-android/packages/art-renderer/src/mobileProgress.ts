export const MOBILE_PROGRESS_INTERVAL_MS = 250;

/** Keep native chrome traffic bounded without delaying controls or phase changes. */
export function shouldPostMobileProgress(
  state: string,
  previousKey: string,
  nextKey: string,
  elapsedMs: number,
  flush = false,
): boolean {
  return flush
    || state !== 'PLAYING'
    || previousKey !== nextKey
    || elapsedMs >= MOBILE_PROGRESS_INTERVAL_MS;
}
