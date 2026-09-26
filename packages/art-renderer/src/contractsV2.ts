import {z} from 'zod';

const normalized = z.number().finite().min(0).max(1);
const identifier = z.string().regex(/^[a-z][a-z0-9_-]*$/);

export const RigArchetypeSchema = z.enum([
  'butterfly',
  'bird',
  'flower',
  'tree_branch',
  'fish',
  'biped',
  'rigid',
  'generic_organic',
  'unknown',
]);

export const RigDeliveryTierSchema = z.enum([
  'FULL_AUTO_RIG',
  'CUTOUT_MICRO_MOTION',
  'BBOX_VISUAL_FOCUS',
  'WHOLE_DRAWING_V1',
]);

export const RigTargetV1Schema = z.object({
  canonicalEntityId: z.string().min(1).max(160),
  normalizedLabel: z.string().min(1).max(160),
  confidence: normalized,
  semanticTags: z.array(z.string().min(1).max(80)).max(32).default([]),
}).strict();

export const RigDefinitionV1Schema = z.object({
  contractName: z.literal('RigDefinitionV1'),
  contractVersion: z.literal('1.0'),
  archetype: RigArchetypeSchema,
  sourceRegion: z.object({
    x: normalized,
    y: normalized,
    width: z.number().finite().gt(0).max(1),
    height: z.number().finite().gt(0).max(1),
  }).strict(),
  vertices: z.array(z.object({x: normalized, y: normalized, u: normalized, v: normalized}).strict()).min(4).max(1024),
  triangles: z.array(z.object({a: z.number().int().min(0).max(1023), b: z.number().int().min(0).max(1023), c: z.number().int().min(0).max(1023)}).strict()).min(2).max(2048),
  bones: z.array(z.object({
    boneId: identifier,
    parentId: identifier.nullable().default(null),
    pivotX: normalized,
    pivotY: normalized,
    maxRotationDegrees: z.number().finite().min(0).max(30),
  }).strict()).min(1).max(32),
  weights: z.array(z.object({
    vertexIndex: z.number().int().min(0).max(1023),
    influences: z.array(z.object({boneId: identifier, weight: z.number().finite().gt(0).max(1)}).strict()).min(1).max(4),
  }).strict()).min(4).max(1024),
}).strict().superRefine((rig, context) => {
  const boneIds = new Set(rig.bones.map((bone) => bone.boneId));
  if (boneIds.size !== rig.bones.length) context.addIssue({code: z.ZodIssueCode.custom, message: 'Bone IDs must be unique.'});
  if (rig.weights.length !== rig.vertices.length) context.addIssue({code: z.ZodIssueCode.custom, message: 'Every vertex requires weights.'});
  for (const triangle of rig.triangles) {
    if (Math.max(triangle.a, triangle.b, triangle.c) >= rig.vertices.length) context.addIssue({code: z.ZodIssueCode.custom, message: 'Triangle index is outside the vertex array.'});
  }
  for (const weights of rig.weights) {
    if (weights.vertexIndex >= rig.vertices.length) context.addIssue({code: z.ZodIssueCode.custom, message: 'Weight vertex is unknown.'});
    if (Math.abs(weights.influences.reduce((sum, item) => sum + item.weight, 0) - 1) > 1e-4) context.addIssue({code: z.ZodIssueCode.custom, message: 'Weights must sum to one.'});
    if (weights.influences.some((item) => !boneIds.has(item.boneId))) context.addIssue({code: z.ZodIssueCode.custom, message: 'Weight bone is unknown.'});
  }
});

export const RiggedArtworkPackageV1Schema = z.object({
  contractName: z.literal('RiggedArtworkPackageV1'),
  contractVersion: z.literal('1.0'),
  packageId: z.string().min(1).max(160),
  sessionId: z.string().min(1).max(120),
  sourceArtifactRef: z.string().min(1).max(300),
  sourceSha256: z.string().regex(/^[a-f0-9]{64}$/),
  target: RigTargetV1Schema,
  archetype: RigArchetypeSchema,
  tier: RigDeliveryTierSchema,
  rig: RigDefinitionV1Schema.nullable().optional(),
  derivedArtifacts: z.array(z.unknown()).max(4).default([]),
  validation: z.object({
    contractName: z.literal('RigValidationResultV1'),
    contractVersion: z.literal('1.0'),
    valid: z.boolean(),
    selectedTier: RigDeliveryTierSchema,
    reasonCodes: z.array(z.string().min(1).max(80)).max(16).default([]),
    validatorVersion: z.string().regex(/^[1-9][0-9]*$/),
  }).strict(),
  pipelineVersion: z.string().regex(/^[1-9][0-9]*$/),
  createdAt: z.string().datetime({offset: true}),
  originalArtPreserved: z.literal(true),
}).strict().superRefine((value, context) => {
  if (value.tier === 'FULL_AUTO_RIG' && value.rig === undefined) context.addIssue({code: z.ZodIssueCode.custom, message: 'Full auto-rig requires rig data.'});
  if (value.validation.selectedTier !== value.tier) context.addIssue({code: z.ZodIssueCode.custom, message: 'Validation tier drift.'});
});

export const BonePoseV2Schema = z.object({
  rotationDegrees: z.number().finite().min(-30).max(30).default(0),
  translateX: z.number().finite().min(-0.15).max(0.15).default(0),
  translateY: z.number().finite().min(-0.15).max(0.15).default(0),
  scaleX: z.number().finite().min(0.8).max(1.2).default(1),
  scaleY: z.number().finite().min(0.8).max(1.2).default(1),
}).strict();

export const VisualAnimationPlanV2Schema = z.object({
  contractName: z.literal('VisualAnimationPlanV2'),
  contractVersion: z.literal('2.0'),
  planId: z.string().min(1).max(160),
  sessionId: z.string().min(1).max(120),
  experienceSpecRef: z.object({id: z.string().min(1), version: z.number().int().min(1)}).strict(),
  packageId: z.string().min(1).max(160),
  archetype: RigArchetypeSchema,
  tier: RigDeliveryTierSchema,
  durationSeconds: z.number().finite().min(1).max(30),
  tracks: z.array(z.object({
    trackId: identifier,
    boneId: identifier,
    profile: z.enum(['flutter', 'sway', 'breathe', 'tilt', 'swim', 'step', 'focus']),
    keyframes: z.array(z.object({atSeconds: z.number().finite().min(0).max(30), pose: BonePoseV2Schema}).strict()).min(2).max(16),
    repeat: z.number().int().min(0).max(4).default(0),
  }).strict()).max(32),
  learningBridgeVi: z.string().min(1).max(300),
  maxMotionLevel: z.union([z.literal(0), z.literal(1), z.literal(2)]).default(2),
}).strict();

export const RendererLoadCommandV2Schema = z.object({
  contractName: z.literal('RendererLoadCommandV2'),
  contractVersion: z.literal('2.0'),
  protocolVersion: z.literal('2'),
  sequence: z.literal(1),
  rendererInstanceId: z.string().min(1).max(120),
  sessionId: z.string().min(1).max(120),
  expectedSessionVersion: z.number().int().min(0),
  experienceSpecRef: z.object({id: z.string().min(1), version: z.number().int().min(1)}).strict(),
  sourceReadEndpoint: z.literal('/v1/renderer/source'),
  sourceReadCapability: z.string().min(40).max(200),
  sourceSha256: z.string().regex(/^[a-f0-9]{64}$/),
  packageReadEndpoint: z.literal('/v1/renderer/rig-package'),
  packageReadCapability: z.string().min(40).max(200),
  packageSha256: z.string().regex(/^[a-f0-9]{64}$/),
  animationPlan: VisualAnimationPlanV2Schema,
}).strict();

export type RigDefinitionV1 = z.infer<typeof RigDefinitionV1Schema>;
export type RiggedArtworkPackageV1 = z.infer<typeof RiggedArtworkPackageV1Schema>;
export type VisualAnimationPlanV2 = z.infer<typeof VisualAnimationPlanV2Schema>;
export type RendererLoadCommandV2 = z.infer<typeof RendererLoadCommandV2Schema>;
