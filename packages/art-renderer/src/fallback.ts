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
      durationSeconds: 1.1,
      scale: 1.12,
    },
    {
      id: `fallback-drift-${object.id}`,
      sceneId: `fallback-${index + 1}`,
      kind: 'MOVE_TO' as const,
      targetId: object.id,
      durationSeconds: 1.2,
      to: {x: 0.52, y: 0.48},
    },
    {
      id: `fallback-settle-${object.id}`,
      sceneId: `fallback-${index + 1}`,
      kind: 'ROTATE' as const,
      targetId: object.id,
      durationSeconds: 0.8,
      rotationDegrees: 1.4,
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
