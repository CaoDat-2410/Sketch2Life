import {describe, expect, it} from 'vitest';

import {detectPrimaryForegroundRegion} from '../src/foregroundRegion';

function rgba(width: number, height: number, blocks: Array<[number, number, number, number]>): Uint8ClampedArray {
  const pixels = new Uint8ClampedArray(width * height * 4);
  for (const [left, top, right, bottom] of blocks) {
    for (let y = top; y < bottom; y += 1) {
      for (let x = left; x < right; x += 1) pixels[(y * width + x) * 4 + 3] = 255;
    }
  }
  return pixels;
}

describe('primary foreground region', () => {
  it('prefers a central subject over border scenery', () => {
    const result = detectPrimaryForegroundRegion(
      rgba(100, 80, [[25, 15, 70, 60], [0, 74, 100, 80], [82, 4, 95, 17]]),
      100,
      80,
    );
    expect(result).not.toBeNull();
    expect(result!.x).toBeGreaterThan(0.15);
    expect(result!.width).toBeLessThan(0.7);
  });

  it('rejects a full-frame foreground mask', () => {
    expect(detectPrimaryForegroundRegion(rgba(20, 20, [[0, 0, 20, 20]]), 20, 20)).toBeNull();
  });

  it('returns null for an empty canvas', () => {
    expect(detectPrimaryForegroundRegion(rgba(20, 20, []), 20, 20)).toBeNull();
  });
});
