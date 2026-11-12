import {describe, expect, it} from 'vitest';

import {buildV2FallbackPlan} from '../src/v2FallbackPlan';
import type {RendererLoadCommandV2} from '../src/contractsV2';

describe('fixed-camera V2 fallback', () => {
  it('uses short in-frame translations then a 20-second still hold, never zooms or rotates', () => {
    const fallback = buildV2FallbackPlan({
      sourceSha256: 'a'.repeat(64),
      experienceSpecRef: {id: 'spec-fallback', version: 2},
      animationPlan: {planId: 'visual-fallback', learningBridgeVi: 'Cùng khám phá nhé.'},
    } as RendererLoadCommandV2) as {
      objects: Array<{initialTransform: {scale: number; rotationDegrees: number}}>;
      motions: Array<{kind: string; durationSeconds: number; to?: {x: number; y: number}}>;
    };
    const moves = fallback.motions.filter((motion) => motion.to !== undefined);

    expect(fallback.objects[0].initialTransform).toMatchObject({scale: 1, rotationDegrees: 0});
    expect(fallback.motions.some((motion) => motion.kind === 'SCALE' || motion.kind === 'ROTATE')).toBe(false);
    expect(moves.every((motion) => Math.abs(motion.to!.x - 0.5) <= 0.0041)).toBe(true);
    expect(moves.every((motion) => Math.abs(motion.to!.y - 0.5) <= 0.0041)).toBe(true);
    expect(fallback.motions.reduce((total, motion) => total + motion.durationSeconds, 0)).toBe(20);
    expect(fallback.motions.at(-1)).toMatchObject({kind: 'FADE', durationSeconds: 10, opacity: 1});
  });
});
