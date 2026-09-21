import {z} from 'zod';

export const ART_RENDERER_PROTOCOL_VERSION = '1' as const;

export const MOTION_KINDS = [
  'MOVE',
  'MOVE_TO',
  'SCALE',
  'ROTATE',
  'FADE',
  'FLY',
  'JUMP',
  'DRAW_REVEAL',
] as const;

export type MotionKind = (typeof MOTION_KINDS)[number];

const normalizedNumber = z.number().finite().min(0).max(1);

export const StagePointSchema = z.object({
  x: normalizedNumber,
  y: normalizedNumber,
}).strict();

export const TransformSchema = z.object({
  position: StagePointSchema.default({x: 0.5, y: 0.5}),
  scale: z.number().finite().min(0.05).max(4).default(1),
  rotationDegrees: z.number().finite().min(-360).max(360).default(0),
  opacity: normalizedNumber.default(1),
}).strict();

const DEFAULT_TRANSFORM = {
  position: {x: 0.5, y: 0.5},
  scale: 1,
  rotationDegrees: 0,
  opacity: 1,
};

export const ChildArtAssetSchema = z
  .object({
    sourceAssetId: z.string().min(1),
    sourceAssetVersion: z.string().regex(/^[1-9][0-9]*$/),
    uri: z.string().min(1).max(500),
    assetKind: z.enum(['WHOLE_DRAWING', 'CROP', 'TRANSPARENT_PNG', 'MASK']),
    cropVersion: z.string().regex(/^[1-9][0-9]*$/).optional(),
    maskVersion: z.string().regex(/^[1-9][0-9]*$/).optional(),
    sourceSha256: z.string().regex(/^[a-f0-9]{64}$/),
  })
  .strict()
  .superRefine((asset, context) => {
    if (asset.assetKind === 'CROP' && asset.cropVersion === undefined) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'CROP assets require cropVersion provenance.',
        path: ['cropVersion'],
      });
    }

    if (asset.assetKind === 'MASK' && asset.maskVersion === undefined) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'MASK assets require maskVersion provenance.',
        path: ['maskVersion'],
      });
    }
  });

export const ArtObjectSchema = z.object({
  id: z.string().regex(/^[a-z][a-z0-9_-]*$/),
  label: z.string().min(1).max(200),
  asset: ChildArtAssetSchema,
  initialTransform: TransformSchema.default(DEFAULT_TRANSFORM),
  extractionStatus: z.enum(['READY', 'FALLBACK_REQUIRED']).default('READY'),
}).strict();

export const MotionSchema = z
  .object({
    id: z.string().regex(/^[a-z][a-z0-9_-]*$/),
    sceneId: z.string().regex(/^[a-z][a-z0-9_-]*$/),
    kind: z.enum(MOTION_KINDS),
    targetId: z.string().regex(/^[a-z][a-z0-9_-]*$/),
    durationSeconds: z.number().finite().min(0.05).max(30),
    to: StagePointSchema.optional(),
    scale: z.number().finite().min(0.05).max(4).optional(),
    rotationDegrees: z.number().finite().min(-360).max(360).optional(),
    opacity: normalizedNumber.optional(),
  })
  .strict()
  .superRefine((motion, context) => {
    if (['MOVE', 'MOVE_TO', 'FLY', 'JUMP'].includes(motion.kind) && motion.to === undefined) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: `${motion.kind} requires a normalized destination.`,
        path: ['to'],
      });
    }

    if (motion.kind === 'SCALE' && motion.scale === undefined) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'SCALE requires a bounded scale value.',
        path: ['scale'],
      });
    }

    if (motion.kind === 'ROTATE' && motion.rotationDegrees === undefined) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'ROTATE requires bounded rotationDegrees.',
        path: ['rotationDegrees'],
      });
    }

    if (motion.kind === 'FADE' && motion.opacity === undefined) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'FADE requires bounded opacity.',
        path: ['opacity'],
      });
    }
  });

export const ArtAnimationPlanSchema = z.object({
  contractVersion: z.literal(ART_RENDERER_PROTOCOL_VERSION),
  planId: z.string().min(1).max(120),
  planVersion: z.string().regex(/^[1-9][0-9]*$/),
  stage: z.object({
    width: z.number().int().min(240).max(4096),
    height: z.number().int().min(240).max(4096),
  }).strict(),
  objects: z.array(ArtObjectSchema).min(1),
  motions: z.array(MotionSchema).min(1).max(100),
}).strict();

const VersionedRefSchema = z.object({
  id: z.string().min(1).max(120),
  version: z.number().int().min(1).max(999),
}).strict();

export const ArtAnimationPlanEnvelopeSchema = z.object({
  contractName: z.literal('ArtAnimationPlanV1'),
  contractVersion: z.literal('1.0'),
  sessionId: z.string().min(1).max(120),
  experienceSpecRef: VersionedRefSchema,
  sourceArtifactRef: z.string().min(1).max(300),
  sourceArtifactSha256: z.string().regex(/^[a-f0-9]{64}$/),
  plan: ArtAnimationPlanSchema,
  originalArtPreserved: z.literal(true),
  videoExecuted: z.literal(false),
}).strict().superRefine((envelope, context) => {
  const whole = envelope.plan.objects.filter((object) => object.asset.assetKind === 'WHOLE_DRAWING');
  if (whole.length === 0) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'The original whole drawing is required.'});
  }
  if (envelope.plan.objects.some((object) => object.asset.sourceSha256 !== envelope.sourceArtifactSha256)) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Renderer assets must retain the source hash.'});
  }
  const objectIds = new Set(envelope.plan.objects.map((object) => object.id));
  const motionIds = envelope.plan.motions.map((motion) => motion.id);
  if (new Set(motionIds).size !== motionIds.length) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Renderer motion IDs must be unique.'});
  }
  if (envelope.plan.motions.some((motion) => !objectIds.has(motion.targetId))) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Renderer motion target is unknown.'});
  }
});

const PixiManifestAssetSchema = z.object({
  assetId: z.string().min(1).max(160),
  assetVersion: z.string().regex(/^[1-9][0-9]*$/),
  assetRef: z.string().min(1).max(300),
  sha256: z.string().regex(/^[a-f0-9]{64}$/),
  role: z.enum(['ORIGINAL_ART', 'SUPPLEMENTAL']),
  reviewStatus: z.enum(['SOURCE_ORIGINAL', 'APPROVED']),
  rightsStatus: z.enum(['NOT_APPLICABLE', 'CLEARED']),
}).strict().superRefine((asset, context) => {
  const validOriginal = asset.role === 'ORIGINAL_ART' && asset.reviewStatus === 'SOURCE_ORIGINAL' && asset.rightsStatus === 'NOT_APPLICABLE';
  const validSupplement = asset.role === 'SUPPLEMENTAL' && asset.reviewStatus === 'APPROVED' && asset.rightsStatus === 'CLEARED';
  if (!validOriginal && !validSupplement) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Supplemental assets require visual and rights approval.'});
  }
});

export const PixiArtAssetManifestSchema = z.object({
  contractName: z.literal('PixiArtAssetManifestV1'),
  contractVersion: z.literal('1.0'),
  sessionId: z.string().min(1).max(120),
  experienceSpecRef: VersionedRefSchema,
  sourceArtifactRef: z.string().min(1).max(300),
  sourceArtifactSha256: z.string().regex(/^[a-f0-9]{64}$/),
  assets: z.array(PixiManifestAssetSchema).min(1).max(6),
  originalArtPreserved: z.literal(true),
  providerGenerationCalled: z.literal(false),
}).strict().superRefine((manifest, context) => {
  const originals = manifest.assets.filter((asset) => asset.role === 'ORIGINAL_ART');
  if (originals.length !== 1 || originals[0]?.sha256 !== manifest.sourceArtifactSha256) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Manifest needs one original asset matching the source hash.'});
  }
  const assetIds = manifest.assets.map((asset) => asset.assetId);
  if (new Set(assetIds).size !== assetIds.length) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Manifest asset IDs must be unique.'});
  }
});

export type StagePoint = z.infer<typeof StagePointSchema>;
export type Transform = z.infer<typeof TransformSchema>;
export type ChildArtAsset = z.infer<typeof ChildArtAssetSchema>;
export type ArtObject = z.infer<typeof ArtObjectSchema>;
export type Motion = z.infer<typeof MotionSchema>;
export type ArtAnimationPlan = z.infer<typeof ArtAnimationPlanSchema>;
export type ArtAnimationPlanEnvelope = z.infer<typeof ArtAnimationPlanEnvelopeSchema>;
export type PixiArtAssetManifest = z.infer<typeof PixiArtAssetManifestSchema>;

export const FALLBACK_REASONS = [
  'EXTRACTION_UNAVAILABLE',
  'MASK_INVALID',
  'ASSET_LOAD_FAILED',
  'MOTION_COMPILE_FAILED',
] as const;

export type FallbackReason = (typeof FALLBACK_REASONS)[number];

export const RendererBootstrapSchema = z.object({
  protocolVersion: z.literal(ART_RENDERER_PROTOCOL_VERSION),
  rendererInstanceId: z.string().min(1).max(120),
}).strict();

export const PlaybackEventSchema = z.discriminatedUnion('type', [
  z.object({type: z.literal('PLAYBACK_STARTED'), planId: z.string().min(1).max(120)}).strict(),
  z.object({type: z.literal('PLAYBACK_COMPLETED'), planId: z.string().min(1).max(120)}).strict(),
  z.object({
    type: z.literal('FALLBACK_APPLIED'),
    planId: z.string().min(1).max(120),
    reason: z.enum(FALLBACK_REASONS),
  }).strict(),
  z.object({
    type: z.literal('PLAYBACK_FAILED'),
    planId: z.string().min(1).max(120),
    reason: z.string().min(1).max(160),
  }).strict(),
]);

export const MAX_RENDERER_MESSAGE_BYTES = 4096;
export type RendererBootstrap = z.infer<typeof RendererBootstrapSchema>;
export type PlaybackEvent = z.infer<typeof PlaybackEventSchema>;

export const RendererLoadCommandSchema = z.object({
  contractName: z.literal('RendererLoadCommandV1'),
  contractVersion: z.literal('1.0'),
  protocolVersion: z.literal(ART_RENDERER_PROTOCOL_VERSION),
  sequence: z.literal(1),
  rendererInstanceId: z.string().min(1).max(120),
  sessionId: z.string().min(1).max(120),
  expectedSessionVersion: z.number().int().min(0),
  experienceSpecRef: VersionedRefSchema,
  sourceReadEndpoint: z.literal('/v1/renderer/source'),
  sourceReadCapability: z.string().min(40).max(200),
  assetManifest: PixiArtAssetManifestSchema,
  animationPlan: ArtAnimationPlanEnvelopeSchema,
}).strict().superRefine((command, context) => {
  const plan = command.animationPlan;
  const manifest = command.assetManifest;
  if (
    plan.sessionId !== command.sessionId ||
    manifest.sessionId !== command.sessionId ||
    plan.experienceSpecRef.id !== command.experienceSpecRef.id ||
    plan.experienceSpecRef.version !== command.experienceSpecRef.version ||
    manifest.experienceSpecRef.id !== command.experienceSpecRef.id ||
    manifest.experienceSpecRef.version !== command.experienceSpecRef.version ||
    plan.sourceArtifactRef !== manifest.sourceArtifactRef ||
    plan.sourceArtifactSha256 !== manifest.sourceArtifactSha256 ||
    plan.plan.planId !== command.experienceSpecRef.id ||
    plan.plan.planVersion !== String(command.experienceSpecRef.version)
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Renderer launch identity drift.'});
  }
  if (
    !plan.originalArtPreserved ||
    plan.videoExecuted ||
    manifest.providerGenerationCalled ||
    manifest.assets.length !== 1 ||
    manifest.assets[0]?.role !== 'ORIGINAL_ART'
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Demo renderer accepts original art only.'});
  }
  if (
    plan.plan.objects.length !== 1 ||
    plan.plan.objects[0]?.asset.assetKind !== 'WHOLE_DRAWING' ||
    plan.plan.objects[0]?.asset.uri !== 'source:original-art'
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Demo renderer accepts one whole-source image only.'});
  }
});

export const RendererPlaybackEventEnvelopeSchema = z.object({
  contractName: z.literal('RendererPlaybackEventV1'),
  contractVersion: z.literal('1.0'),
  protocolVersion: z.literal(ART_RENDERER_PROTOCOL_VERSION),
  rendererInstanceId: z.string().min(1).max(120),
  sequence: z.number().int().min(1).max(100),
  sessionId: z.string().min(1).max(120),
  experienceSpecRef: VersionedRefSchema,
  event: PlaybackEventSchema,
}).strict();

export type RendererLoadCommand = z.infer<typeof RendererLoadCommandSchema>;
export type RendererPlaybackEventEnvelope = z.infer<typeof RendererPlaybackEventEnvelopeSchema>;
