import type {ArtAnimationPlan, Motion} from './contracts';

export interface CompiledMotion {
  readonly id: string;
  readonly sceneId: string;
  readonly kind: Motion['kind'];
  readonly targetId: string;
  readonly durationSeconds: number;
  readonly to?: Motion['to'];
  readonly scale?: number;
  readonly rotationDegrees?: number;
  readonly opacity?: number;
}

/**
 * The renderer receives only the closed, pre-validated language. Keeping this
 * compiler deterministic prevents free-form model text from driving playback.
 */
export function compileMotionPlan(plan: ArtAnimationPlan): readonly CompiledMotion[] {
  return plan.motions.map((motion) => ({
    id: motion.id,
    sceneId: motion.sceneId,
    kind: motion.kind,
    targetId: motion.targetId,
    durationSeconds: motion.durationSeconds,
    to: motion.to,
    scale: motion.scale,
    rotationDegrees: motion.rotationDegrees,
    opacity: motion.opacity,
  }));
}
