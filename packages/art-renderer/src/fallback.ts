import type {ArtAnimationPlan, FallbackReason, Motion} from './contracts';

export interface FallbackPlan {
  readonly plan: ArtAnimationPlan;
  readonly reason: FallbackReason;
  readonly mode: 'WHOLE_DRAWING_REVEAL' | 'TRANSFORM_ONLY';
}

/**
 * Replace risky extraction-dependent motions with a whole-drawing reveal and
 * conservative transforms. The original source asset and provenance remain.
 */
export function buildPreservingFallbackPlan(
  plan: ArtAnimationPlan,
  reason: FallbackReason,
): FallbackPlan {
  const fallbackObjects = plan.objects.map((object) => ({
    ...object,
    extractionStatus: 'FALLBACK_REQUIRED' as const,
  }));

  const fallbackMotions: Motion[] = fallbackObjects.flatMap((object, index) => [
    {
      id: `fallback-reveal-${object.id}`,
      sceneId: `fallback-${index + 1}`,
      kind: 'DRAW_REVEAL' as const,
      targetId: object.id,
      durationSeconds: 1.2,
    },
    {
      id: `fallback-emphasis-${object.id}`,
      sceneId: `fallback-${index + 1}`,
      kind: 'SCALE' as const,
      targetId: object.id,
      durationSeconds: 0.6,
      scale: 1.05,
    },
  ]);

  return {
    reason,
    mode: 'WHOLE_DRAWING_REVEAL',
    plan: {
      ...plan,
      planId: `${plan.planId}:fallback:${reason.toLowerCase()}`,
      objects: fallbackObjects,
      motions: fallbackMotions,
    },
  };
}
