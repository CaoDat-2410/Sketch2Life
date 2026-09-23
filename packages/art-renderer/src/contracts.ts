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

export const SourceRegionSchema = z.object({
  x: normalizedNumber,
  y: normalizedNumber,
  width: z.number().finite().gt(0).max(1),
  height: z.number().finite().gt(0).max(1),
}).strict().superRefine((region, context) => {
  if (region.x + region.width > 1 || region.y + region.height > 1) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Source region must stay inside the image.'});
  }
});

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
    sourceRegion: SourceRegionSchema.optional(),
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

    if (asset.assetKind === 'CROP' && asset.sourceRegion === undefined) {
      context.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'CROP assets require sourceRegion provenance.',
        path: ['sourceRegion'],
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
  interactive: z.boolean().default(false),
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
export type SourceRegion = z.infer<typeof SourceRegionSchema>;

const SubjectCandidateSchema = z.object({
  candidateId: z.string().regex(/^[a-z0-9-]+$/),
  labelVi: z.string().min(1).max(60),
  sourceClaimIds: z.array(z.string().min(1)).min(1).max(8),
  confidence: z.number().finite().min(0).max(1),
  confidenceBand: z.enum(['HIGH', 'MEDIUM', 'LOW']),
  imageCovered: z.boolean(),
  narrationCovered: z.boolean(),
  relationRefs: z.array(z.string().min(1)).max(8),
}).strict();

export const SubjectCandidateSetSchema = z.object({
  contractName: z.literal('SubjectCandidateSetV1'),
  contractVersion: z.literal('1.0'),
  sessionId: z.string().min(1).max(120),
  sourceArtifactRef: z.string().min(1).max(300),
  sourceArtifactSha256: z.string().regex(/^[a-f0-9]{64}$/),
  maxItems: z.literal(3),
  items: z.array(SubjectCandidateSchema).min(1).max(3),
  originalArtPreserved: z.literal(true),
}).strict();

export const SceneExplorationPlanSchema = z.object({
  contractName: z.literal('SceneExplorationPlanV1'),
  contractVersion: z.literal('1.0'),
  sessionId: z.string().min(1).max(120),
  experienceSpecRef: VersionedRefSchema,
  sourceArtifactRef: z.string().min(1).max(300),
  primarySubjectRef: z.string().min(1).max(120),
  primaryLabelVi: z.string().min(1).max(60),
  relationLabelVi: z.string().min(1).max(80).optional(),
  learningBridgeVi: z.string().min(1).max(240),
  beats: z.array(z.object({
    beatId: z.string().regex(/^[a-z][a-z0-9-]*$/),
    order: z.number().int().min(1).max(4),
    effect: z.enum(['REVEAL', 'FOCUS', 'TRACE_RELATION', 'ZOOM_OUT']),
    targetRef: z.string().min(1).max(120).optional(),
    labelVi: z.string().min(1).max(60),
    captionVi: z.string().min(1).max(180),
    startSeconds: z.number().finite().min(0).max(30),
    endSeconds: z.number().finite().gt(0).max(30),
    tapEnabled: z.boolean(),
  }).strict().superRefine((beat, context) => {
    if (beat.endSeconds <= beat.startSeconds) {
      context.addIssue({code: z.ZodIssueCode.custom, message: 'Beat end must be after start.'});
    }
  })).min(2).max(4),
  tapToDiscover: z.literal(true),
  videoExecuted: z.literal(false),
}).strict();

export const SceneFocusPlanSchema = z.object({
  contractName: z.literal('SceneFocusPlanV1'),
  contractVersion: z.literal('1.0'),
  sessionId: z.string().min(1).max(120),
  experienceSpecRef: VersionedRefSchema,
  sourceArtifactRef: z.string().min(1).max(300),
  sourceArtifactSha256: z.string().regex(/^[a-f0-9]{64}$/),
  extractionStatus: z.enum(['READY', 'FALLBACK_REQUIRED']),
  targets: z.array(z.object({
    targetRef: z.string().min(1).max(120),
    labelVi: z.string().min(1).max(60),
    sourceRegion: SourceRegionSchema.optional(),
    regionConfidence: z.number().finite().min(0).max(1).optional(),
    depthLayer: z.number().int().min(0).max(2),
    hitSlop: z.number().finite().min(0).max(0.25),
    assetKind: z.enum(['CROP', 'TRANSPARENT_PNG', 'MASK']).optional(),
    extractionVersion: z.string().min(1).optional(),
  }).strict().superRefine((target, context) => {
    if (target.sourceRegion !== undefined && (
      target.regionConfidence === undefined || target.assetKind === undefined || target.extractionVersion === undefined
    )) {
      context.addIssue({code: z.ZodIssueCode.custom, message: 'Localized targets require provenance.'});
    }
  })).max(3),
  fallbackReason: z.enum(['NO_LOCALIZER', 'REGION_INVALID', 'CUTOUT_FAILED']).optional(),
}).strict().superRefine((plan, context) => {
  if (plan.extractionStatus === 'READY' && plan.targets.length === 0) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Ready focus plans require targets.'});
  }
  if (plan.extractionStatus === 'FALLBACK_REQUIRED' && plan.targets.length > 0) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Fallback focus plans cannot expose regions.'});
  }
  if (plan.extractionStatus === 'FALLBACK_REQUIRED' && plan.fallbackReason === undefined) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Fallback focus plans require a reason.'});
  }
});

export type SceneFocusPlan = z.infer<typeof SceneFocusPlanSchema>;

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
  z.object({
    type: z.literal('DISCOVERED_ENTITY'),
    planId: z.string().min(1).max(120),
    objectId: z.string().min(1).max(120),
    labelVi: z.string().min(1).max(60),
  }).strict(),
  z.object({
    type: z.literal('FOCUS_CHANGED'),
    planId: z.string().min(1).max(120),
    objectId: z.string().min(1).max(120),
  }).strict(),
]);

export const MAX_RENDERER_MESSAGE_BYTES = 4096;
export type RendererBootstrap = z.infer<typeof RendererBootstrapSchema>;
export type PlaybackEvent = z.infer<typeof PlaybackEventSchema>;

export const PLAYBACK_CONTROL_ACTIONS = [
  'PLAY',
  'PAUSE',
  'REPLAY',
  'SEEK_RELATIVE_SECONDS',
  'SEEK_TO_SECONDS',
] as const;

export const RendererControlCommandSchema = z.object({
  protocolVersion: z.literal(ART_RENDERER_PROTOCOL_VERSION),
  rendererInstanceId: z.string().min(1).max(120),
  sequence: z.number().int().min(1),
  type: z.literal('PLAYBACK_CONTROL'),
  action: z.enum(PLAYBACK_CONTROL_ACTIONS),
  seconds: z.number().finite().min(-30).max(300).optional(),
}).strict().superRefine((command, context) => {
  const needsSeconds = command.action === 'SEEK_RELATIVE_SECONDS' || command.action === 'SEEK_TO_SECONDS';
  if (needsSeconds && command.seconds === undefined) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Seek controls require seconds.', path: ['seconds']});
  }
  if (!needsSeconds && command.seconds !== undefined) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'This control does not accept seconds.', path: ['seconds']});
  }
});

export const RendererPlaybackStateEnvelopeSchema = z.object({
  protocolVersion: z.literal(ART_RENDERER_PROTOCOL_VERSION),
  rendererInstanceId: z.string().min(1).max(120),
  sequence: z.number().int().min(1),
  type: z.literal('PLAYBACK_STATE'),
  positionSeconds: z.number().finite().min(0).max(300),
  durationSeconds: z.number().finite().min(0).max(300),
  state: z.enum(['READY', 'PLAYING', 'PAUSED', 'COMPLETED']),
}).strict();

export type RendererControlCommand = z.infer<typeof RendererControlCommandSchema>;
export type RendererPlaybackStateEnvelope = z.infer<typeof RendererPlaybackStateEnvelopeSchema>;

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
  sceneExplorationPlan: SceneExplorationPlanSchema.optional(),
  sceneFocusPlan: SceneFocusPlanSchema.optional(),
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
    manifest.assets.filter((asset) => asset.role === 'ORIGINAL_ART').length !== 1
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Renderer requires exactly one preserved original asset.'});
  }
  if (
    plan.plan.objects.some((object) => object.asset.uri !== 'source:original-art')
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Pixi objects must load from the source capability.'});
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
