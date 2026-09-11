import {describe, expect, it} from 'vitest';

import butterflyPlan from '../fixtures/butterfly/art_animation_plan.json';
import {
  ArtPlanValidationError,
  buildPreservingFallbackPlan,
  compileMotionPlan,
  createRendererBenchmarkSample,
  loadChildArtAssetInstructions,
  validateArtAnimationPlan,
} from '../src/index';

describe('art animation fixture protocol', () => {
  it('compiles the butterfly plan with the complete approved scene flow', () => {
    const plan = validateArtAnimationPlan(butterflyPlan);
    const motions = compileMotionPlan(plan);

    expect(motions.map((motion) => motion.kind)).toEqual(['DRAW_REVEAL', 'SCALE', 'FLY']);
    expect(motions.map((motion) => motion.sceneId)).toEqual([
      'scene-1-reveal',
      'scene-2-flutter',
      'scene-3-fly',
    ]);
  });

  it('preserves source, crop, and mask provenance in rendering instructions', () => {
    const plan = validateArtAnimationPlan(butterflyPlan);
    const [asset] = loadChildArtAssetInstructions(plan);

    expect(asset).toMatchObject({
      objectId: 'butterfly',
      sourceAssetId: 'drawing-butterfly-001',
      sourceAssetVersion: '1',
    });
  });

  it('rejects unknown motion names and unknown target IDs before rendering', () => {
    const unknownMotion = structuredClone(butterflyPlan) as Record<string, unknown>;
    const motions = unknownMotion.motions as Array<Record<string, unknown>>;
    motions[0].kind = 'WARP';

    expect(() => validateArtAnimationPlan(unknownMotion)).toThrow(ArtPlanValidationError);

    const unknownTarget = structuredClone(butterflyPlan) as Record<string, unknown>;
    const unknownTargetMotions = unknownTarget.motions as Array<Record<string, unknown>>;
    unknownTargetMotions[0].targetId = 'not-in-source-art';
    expect(() => validateArtAnimationPlan(unknownTarget)).toThrow(/unknown target/);
  });

  it('rejects unbounded coordinate and duration values before rendering', () => {
    const invalidPlan = structuredClone(butterflyPlan) as Record<string, unknown>;
    const motions = invalidPlan.motions as Array<Record<string, unknown>>;
    motions[2].durationSeconds = 31;
    motions[2].to = {x: 1.1, y: 0.4};

    expect(() => validateArtAnimationPlan(invalidPlan)).toThrow(ArtPlanValidationError);
  });

  it('falls back without replacing the child source asset', () => {
    const plan = validateArtAnimationPlan(butterflyPlan);
    const fallback = buildPreservingFallbackPlan(plan, 'MASK_INVALID');

    expect(fallback.mode).toBe('WHOLE_DRAWING_REVEAL');
    expect(fallback.plan.objects[0].asset.sourceAssetId).toBe('drawing-butterfly-001');
    expect(fallback.plan.motions.every((motion) => ['DRAW_REVEAL', 'SCALE'].includes(motion.kind))).toBe(
      true,
    );
  });

  it('records a reproducible fixture benchmark sample', () => {
    expect(createRendererBenchmarkSample('fixture-butterfly-art-animation', 1000, 2000, 60)).toMatchObject({
      fixtureId: 'fixture-butterfly-art-animation',
      startupMilliseconds: 1000,
      averageFramesPerSecond: 60,
    });
  });
});
