import {describe, expect, it} from 'vitest';

import {getSpriteCycleFrameIndex, getSpriteCycleTransform} from '../src/spriteCycle';

const frameReads = [0, 1, 2, 3].map((index) => ({assetId: `motion.flyer.frame-${String(index + 1).padStart(2, '0')}`}));

describe('Pixi sprite cycle clock', () => {
  it('maps elapsed time to a deterministic loop frame and hides outside the beat', () => {
    const cycle = {
      playbackKind: 'FRAME_SEQUENCE' as const,
      loopMode: 'LOOP' as const,
      frameRate: 4,
      startSeconds: 5,
      endSeconds: 10,
      frameReads,
    };
    expect(getSpriteCycleFrameIndex(cycle, 4.99)).toBeNull();
    expect(getSpriteCycleFrameIndex(cycle, 5)).toBe(0);
    expect(getSpriteCycleFrameIndex(cycle, 5.26)).toBe(1);
    expect(getSpriteCycleFrameIndex(cycle, 6)).toBe(0);
    expect(getSpriteCycleFrameIndex(cycle, 10)).toBeNull();
    expect(getSpriteCycleFrameIndex(cycle, Number.NaN)).toBeNull();
  });

  it('holds the final one-shot frame and treats slider motion as one texture plus a bounded transform', () => {
    const oneShot = {
      playbackKind: 'FRAME_SEQUENCE' as const,
      loopMode: 'ONCE' as const,
      frameRate: 2,
      startSeconds: 0,
      endSeconds: 5,
      frameReads,
    };
    expect(getSpriteCycleFrameIndex(oneShot, 3.9)).toBe(3);

    const slider = {
      playbackKind: 'TRANSFORM_DRIVEN' as const,
      behaviorClassId: 'slider',
      startSeconds: 0,
      endSeconds: 4,
    };
    expect(getSpriteCycleFrameIndex({...slider, loopMode: 'LOOP' as const, frameRate: 6, frameReads: frameReads.slice(0, 1)}, 1)).toBe(0);
    expect(getSpriteCycleTransform(slider, 1).offsetX).toBeGreaterThan(0);
    expect(getSpriteCycleTransform(slider, 4).offsetX).toBe(0);
  });
});
