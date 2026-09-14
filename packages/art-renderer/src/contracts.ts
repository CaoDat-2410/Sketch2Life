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
});

export const TransformSchema = z.object({
  position: StagePointSchema.default({x: 0.5, y: 0.5}),
  scale: z.number().finite().min(0.05).max(4).default(1),
  rotationDegrees: z.number().finite().min(-360).max(360).default(0),
  opacity: normalizedNumber.default(1),
});

const DEFAULT_TRANSFORM = {
  position: {x: 0.5, y: 0.5},
  scale: 1,
  rotationDegrees: 0,
  opacity: 1,
};

export const ChildArtAssetSchema = z
  .object({
    sourceAssetId: z.string().min(1),
    sourceAssetVersion: z.string().min(1),
    uri: z.string().min(1),
    assetKind: z.enum(['WHOLE_DRAWING', 'CROP', 'TRANSPARENT_PNG', 'MASK']),
    cropVersion: z.string().min(1).optional(),
    maskVersion: z.string().min(1).optional(),
    sourceSha256: z.string().regex(/^[a-f0-9]{64}$/).optional(),
  })
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
  label: z.string().min(1),
  asset: ChildArtAssetSchema,
  initialTransform: TransformSchema.default(DEFAULT_TRANSFORM),
  extractionStatus: z.enum(['READY', 'FALLBACK_REQUIRED']).default('READY'),
});

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
  planId: z.string().min(1),
  planVersion: z.string().min(1),
  stage: z.object({
    width: z.number().finite().min(240).max(4096),
    height: z.number().finite().min(240).max(4096),
  }),
  objects: z.array(ArtObjectSchema).min(1),
  motions: z.array(MotionSchema).min(1).max(100),
});

export type StagePoint = z.infer<typeof StagePointSchema>;
export type Transform = z.infer<typeof TransformSchema>;
export type ChildArtAsset = z.infer<typeof ChildArtAssetSchema>;
export type ArtObject = z.infer<typeof ArtObjectSchema>;
export type Motion = z.infer<typeof MotionSchema>;
export type ArtAnimationPlan = z.infer<typeof ArtAnimationPlanSchema>;

export interface RendererBootstrap {
  readonly protocolVersion: typeof ART_RENDERER_PROTOCOL_VERSION;
  readonly rendererInstanceId: string;
}

export type PlaybackEvent =
  | Readonly<{type: 'PLAYBACK_STARTED'; planId: string}>
  | Readonly<{type: 'PLAYBACK_COMPLETED'; planId: string}>
  | Readonly<{type: 'FALLBACK_APPLIED'; planId: string; reason: FallbackReason}>
  | Readonly<{type: 'PLAYBACK_FAILED'; planId: string; reason: string}>;

export const FALLBACK_REASONS = [
  'EXTRACTION_UNAVAILABLE',
  'MASK_INVALID',
  'ASSET_LOAD_FAILED',
  'MOTION_COMPILE_FAILED',
] as const;

export type FallbackReason = (typeof FALLBACK_REASONS)[number];
