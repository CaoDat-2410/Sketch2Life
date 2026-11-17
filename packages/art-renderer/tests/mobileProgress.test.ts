import {describe, expect, it} from 'vitest';
import {shouldPostMobileProgress} from '../src/mobileProgress';

describe('mobile playback bridge budget', () => {
  it('bounds repeated playing updates to four per second', () => {
    expect(shouldPostMobileProgress('PLAYING', 'same', 'same', 249)).toBe(false);
    expect(shouldPostMobileProgress('PLAYING', 'same', 'same', 250)).toBe(true);
  });
  it('delivers phase changes immediately', () => {
    expect(shouldPostMobileProgress('PLAYING', 'loading', 'intro', 1)).toBe(true);
  });
  it.each(['READY', 'PAUSED', 'COMPLETED'])('delivers %s controls immediately', (state) => {
    expect(shouldPostMobileProgress(state, 'same', 'same', 1)).toBe(true);
  });
  it('flushes a seek/replay update even inside the playing throttle window', () => {
    expect(shouldPostMobileProgress('PLAYING', 'same', 'same', 1, true)).toBe(true);
  });
});
