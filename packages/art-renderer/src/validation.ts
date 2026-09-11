import {
  ArtAnimationPlanSchema,
  type ArtAnimationPlan,
  type Motion,
} from './contracts';

export class ArtPlanValidationError extends Error {
  public constructor(public readonly reasons: readonly string[]) {
    super(`Invalid art animation plan: ${reasons.join('; ')}`);
    this.name = 'ArtPlanValidationError';
  }
}

function motionTargetsAreKnown(plan: ArtAnimationPlan): readonly string[] {
  const objectIds = new Set(plan.objects.map((object) => object.id));
  return plan.motions
    .filter((motion) => !objectIds.has(motion.targetId))
    .map((motion) => `Motion ${motion.id} references unknown target ${motion.targetId}.`);
}

function motionIdsAreUnique(motions: readonly Motion[]): readonly string[] {
  const seen = new Set<string>();
  const duplicateIds: string[] = [];

  for (const motion of motions) {
    if (seen.has(motion.id)) {
      duplicateIds.push(`Motion id ${motion.id} is duplicated.`);
    }
    seen.add(motion.id);
  }

  return duplicateIds;
}

export function validateArtAnimationPlan(input: unknown): ArtAnimationPlan {
  const parsed = ArtAnimationPlanSchema.safeParse(input);
  if (!parsed.success) {
    throw new ArtPlanValidationError(
      parsed.error.issues.map((issue) => `${issue.path.join('.') || 'plan'}: ${issue.message}`),
    );
  }

  const reasons = [...motionTargetsAreKnown(parsed.data), ...motionIdsAreUnique(parsed.data.motions)];
  if (reasons.length > 0) {
    throw new ArtPlanValidationError(reasons);
  }

  return parsed.data;
}
