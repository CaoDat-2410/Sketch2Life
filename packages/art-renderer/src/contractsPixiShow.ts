import {z} from 'zod';

import {PartMaskReadV1Schema, RendererLoadCommandV2Schema} from './contractsV2';

const normalized = z.number().finite().min(0).max(1);
const behaviorForSubjectHint = {
  BIRD: ['FLYER', 'WALKER'],
  INSECT: ['FLYER', 'CRAWLER'],
  FISH: ['SWIMMER'],
  QUADRUPED: ['WALKER'],
  BIPED: ['WALKER'],
  PLANT: ['STATIONARY'],
  VEHICLE: ['ROLLER', 'STATIONARY'],
  OBJECT: ['STATIONARY', 'ROLLER'],
  UNKNOWN: ['STATIONARY'],
} as const;
const rolesRequiredForAction = {
  WALK_STEP: ['leg', 'legs', 'left-leg', 'right-leg', 'fore-leg', 'hind-leg'],
  FLAP: ['wing', 'left-wing', 'right-wing'],
  GLIDE: ['wing', 'left-wing', 'right-wing'],
  SWIM: ['tail', 'fin', 'left-fin', 'right-fin'],
  SLITHER: ['body', 'tail'],
  ROLL: ['wheel', 'left-wheel', 'right-wheel'],
} as const;
const staticSupplementActions = new Set(['NOTICE', 'APPROACH', 'INTERACT', 'SETTLE']);

export const PixiShowSourceRegionV1Schema = z.object({
  x: normalized,
  y: normalized,
  width: z.number().finite().gt(0).max(1),
  height: z.number().finite().gt(0).max(1),
}).strict().superRefine((region, context) => {
  if (region.x + region.width > 1 || region.y + region.height > 1) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Source region must stay within the source image.'});
  }
});

export const PixiShowBeatV1Schema = z.object({
  beatId: z.string().regex(/^[a-z][a-z0-9_-]*$/).max(64),
  startSeconds: z.number().finite().min(0).max(30),
  endSeconds: z.number().finite().gt(0).max(30),
  action: z.enum(['NOTICE', 'APPROACH', 'INTERACT', 'WALK_STEP', 'FLAP', 'GLIDE', 'SWIM', 'SLITHER', 'ROLL', 'SETTLE']),
  targetRole: z.enum(['SOURCE_SUBJECT', 'SUPPLEMENTAL_ASSET']),
  assetId: z.string().min(1).max(160).optional(),
  x: z.number().finite().min(0.05).max(0.95),
  y: z.number().finite().min(0.05).max(0.95),
}).strict().superRefine((beat, context) => {
  if (beat.endSeconds <= beat.startSeconds) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Show beat must have positive duration.'});
  }
  if ((beat.targetRole === 'SUPPLEMENTAL_ASSET') !== (beat.assetId !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Supplemental show beats require exactly one asset ID.'});
  }
});

export const PixiShowPlanV1Schema = z.object({
  contractName: z.literal('PixiShowPlanV1'),
  contractVersion: z.literal('1.0'),
  planId: z.string().min(1).max(160),
  sessionId: z.string().min(1).max(120),
  packageId: z.string().min(1).max(160),
  sourceSha256: z.string().regex(/^[a-f0-9]{64}$/),
  sourceSubjectRegion: PixiShowSourceRegionV1Schema,
  experienceSpecRef: z.object({id: z.string().min(1), version: z.number().int().min(1)}).strict(),
  confirmedSubjectId: z.string().min(1).max(160),
  visualSubjectHintId: z.enum(['BIRD', 'INSECT', 'FISH', 'QUADRUPED', 'BIPED', 'PLANT', 'VEHICLE', 'OBJECT', 'UNKNOWN']),
  behaviorClass: z.enum(['WALKER', 'FLYER', 'SWIMMER', 'CRAWLER', 'ROLLER', 'STATIONARY']),
  durationSeconds: z.number().int().min(15).max(30),
  selectedAssetIds: z.array(z.string().min(1).max(160)).min(1).max(3),
  beats: z.array(PixiShowBeatV1Schema).min(3).max(6),
  endingStill: z.literal(true),
  compilerVersion: z.literal('1').default('1'),
}).strict().superRefine((plan, context) => {
  if (new Set(plan.selectedAssetIds).size !== plan.selectedAssetIds.length) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Selected show asset IDs must be unique.'});
  }
  if (plan.beats.at(-1)?.action !== 'SETTLE') {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'The show must settle before its still ending.'});
  }
  const lastBeat = plan.beats.at(-1);
  if (lastBeat && plan.durationSeconds - lastBeat.endSeconds < 2) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'The final still must last at least two seconds.'});
  }
  let previousEnd = -1;
  for (const [index, beat] of plan.beats.entries()) {
    if (beat.startSeconds < previousEnd) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['beats', index], message: 'Show beats must be ordered and non-overlapping.'});
    }
    previousEnd = beat.endSeconds;
    if (beat.endSeconds > plan.durationSeconds) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['beats', index], message: 'Show beat exceeds total duration.'});
    }
    if (beat.assetId !== undefined && !plan.selectedAssetIds.includes(beat.assetId)) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['beats', index, 'assetId'], message: 'Show beat references an unselected asset.'});
    }
  }
  const referenced = new Set(plan.beats.flatMap((beat) => beat.assetId === undefined ? [] : [beat.assetId]));
  if (referenced.size !== plan.selectedAssetIds.length || plan.selectedAssetIds.some((id) => !referenced.has(id))) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['selectedAssetIds'], message: 'Every selected show asset must be used by a beat.'});
  }
});

export const PixiShowPlanV2Schema = z.object({
  ...PixiShowPlanV1Schema.shape,
  contractName: z.literal('PixiShowPlanV2'),
  contractVersion: z.literal('2.0'),
  selectedAssetIds: z.array(z.string().min(1).max(160)).max(3),
}).strict().superRefine((plan, context) => {
  if (new Set(plan.selectedAssetIds).size !== plan.selectedAssetIds.length) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Selected show asset IDs must be unique.'});
  }
  if (plan.beats.at(-1)?.action !== 'SETTLE') {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'The show must settle before its still ending.'});
  }
  const lastBeat = plan.beats.at(-1);
  if (lastBeat && plan.durationSeconds - lastBeat.endSeconds < 2) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'The final still must last at least two seconds.'});
  }
  let previousEnd = -1;
  const referenced = new Set<string>();
  for (const [index, beat] of plan.beats.entries()) {
    if (beat.startSeconds < previousEnd) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['beats', index], message: 'Show beats must be ordered and non-overlapping.'});
    }
    previousEnd = beat.endSeconds;
    if (beat.endSeconds > plan.durationSeconds) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['beats', index], message: 'Show beat exceeds total duration.'});
    }
    if (beat.assetId !== undefined) {
      if (!plan.selectedAssetIds.includes(beat.assetId)) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['beats', index, 'assetId'], message: 'Show beat references an unselected asset.'});
      }
      referenced.add(beat.assetId);
    }
  }
  if (referenced.size !== plan.selectedAssetIds.length || plan.selectedAssetIds.some((id) => !referenced.has(id))) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['selectedAssetIds'], message: 'Every selected show asset must be used by a beat.'});
  }
});

export const PixiShowAssetReadV1Schema = z.object({
  assetId: z.string().min(1).max(160),
  readEndpoint: z.literal('/v1/renderer/pixi-asset'),
  readCapability: z.string().min(40).max(200),
  sha256: z.string().regex(/^[a-f0-9]{64}$/),
  byteLength: z.number().int().min(1).max(1_000_000),
  contentType: z.literal('image/png'),
}).strict();

export const PixiRendererLaunchV2WireSchema = z.object({
  contractName: z.literal('PixiRendererLaunchV2'),
  contractVersion: z.literal('2.0'),
  sessionId: z.string().min(1).max(120),
  expectedSessionVersion: z.number().int().min(0),
  experienceSpecRef: z.object({id: z.string().min(1), version: z.number().int().min(1)}).strict(),
  sourceReadEndpoint: z.literal('/v1/renderer/source'),
  sourceReadCapability: z.string().min(40).max(200),
  sourceSha256: z.string().regex(/^[a-f0-9]{64}$/),
  packageReadEndpoint: z.literal('/v1/renderer/rig-package'),
  packageReadCapability: z.string().min(40).max(200),
  packageSha256: z.string().regex(/^[a-f0-9]{64}$/),
  packageReadExpiresAt: z.string().datetime({offset: true}),
  maskReadEndpoint: z.literal('/v1/renderer/rig-mask').optional(),
  maskReadCapability: z.string().min(40).max(200).optional(),
  maskSha256: z.string().regex(/^[a-f0-9]{64}$/).optional(),
  partMaskReads: z.array(PartMaskReadV1Schema).max(8).default([]),
  rigParts: RendererLoadCommandV2Schema.shape.rigParts,
  animationPlan: RendererLoadCommandV2Schema.shape.animationPlan,
  fallbackLaunch: z.record(z.string(), z.unknown()).default({}),
}).strict().superRefine((launch, context) => {
  const maskFields = [launch.maskReadEndpoint, launch.maskReadCapability, launch.maskSha256];
  if (maskFields.some((value) => value !== undefined) && maskFields.some((value) => value === undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Derived mask fields must be supplied together.'});
  }
});

export const PixiRendererShowEnvelopeV1Schema = z.object({
  contractName: z.literal('PixiRendererShowEnvelopeV1'),
  contractVersion: z.literal('1.0'),
  rendererLaunchV2: PixiRendererLaunchV2WireSchema,
  showPlan: PixiShowPlanV1Schema,
  assetReads: z.array(PixiShowAssetReadV1Schema).min(1).max(3),
}).strict().superRefine((envelope, context) => {
  const launch = envelope.rendererLaunchV2;
  const plan = envelope.showPlan;
  if (
    launch.sessionId !== plan.sessionId
    || launch.sourceSha256 !== plan.sourceSha256
    || launch.animationPlan.packageId !== plan.packageId
    || launch.experienceSpecRef.id !== plan.experienceSpecRef.id
    || launch.experienceSpecRef.version !== plan.experienceSpecRef.version
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Show envelope identity differs from its V2 launch.'});
  }
  const readIds = envelope.assetReads.map((read) => read.assetId);
  if (new Set(readIds).size !== readIds.length || readIds.length !== plan.selectedAssetIds.length || plan.selectedAssetIds.some((id) => !readIds.includes(id))) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['assetReads'], message: 'Asset capabilities must exactly match selected show assets.'});
  }
});

export const RendererLoadCommandV3Schema = z.object({
  ...RendererLoadCommandV2Schema.shape,
  contractName: z.literal('RendererLoadCommandV3'),
  contractVersion: z.literal('3.0'),
  protocolVersion: z.literal('3'),
  showPlan: PixiShowPlanV1Schema,
  assetReads: z.array(PixiShowAssetReadV1Schema).min(1).max(3),
}).strict().superRefine((command, context) => {
  const plan = command.showPlan;
  if (
    command.sessionId !== plan.sessionId
    || command.sourceSha256 !== plan.sourceSha256
    || command.animationPlan.packageId !== plan.packageId
    || command.experienceSpecRef.id !== plan.experienceSpecRef.id
    || command.experienceSpecRef.version !== plan.experienceSpecRef.version
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Show launch identity does not match its V2 renderer data.'});
  }
  if (plan.durationSeconds !== command.animationPlan.durationSeconds) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'durationSeconds'], message: 'Show and renderer timelines must have the same duration.'});
  }
  if (!(behaviorForSubjectHint[plan.visualSubjectHintId] as readonly string[]).includes(plan.behaviorClass)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'behaviorClass'], message: 'Behavior is incompatible with the visual subject hint.'});
  }
  const readIds = command.assetReads.map((read) => read.assetId);
  if (new Set(readIds).size !== readIds.length || readIds.length !== plan.selectedAssetIds.length || plan.selectedAssetIds.some((id) => !readIds.includes(id))) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['assetReads'], message: 'Asset capabilities must exactly match selected show assets.'});
  }
  const maskFields = [command.maskReadEndpoint, command.maskReadCapability, command.maskSha256];
  if (maskFields.some((value) => value !== undefined) && maskFields.some((value) => value === undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Derived mask fields must be supplied together.'});
  }
  const readPartIds = command.partMaskReads.map((part) => part.partId).sort();
  const rigPartIds = command.rigParts.map((part) => part.partId).sort();
  if (JSON.stringify(readPartIds) !== JSON.stringify(rigPartIds)) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Part mask reads must match rig parts.'});
  }
  const roles = new Set(command.rigParts.map((part) => part.role.toLowerCase().replaceAll('_', '-')));
  for (const [index, beat] of plan.beats.entries()) {
    if (beat.targetRole === 'SUPPLEMENTAL_ASSET') {
      if (!staticSupplementActions.has(beat.action)) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index, 'action'], message: 'Static sprites cannot claim articulated motion.'});
      }
      if (beat.x < 0.12 || beat.x > 0.88 || beat.y < 0.12 || beat.y > 0.88) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index], message: 'Supplemental sprite placement must remain inside the safe stage.'});
      }
      const region = plan.sourceSubjectRegion;
      if (
        region.x - 0.14 <= beat.x && beat.x <= region.x + region.width + 0.14
        && region.y - 0.14 <= beat.y && beat.y <= region.y + region.height + 0.14
      ) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index], message: 'Supplemental sprite placement overlaps the child drawing.'});
      }
      continue;
    }
    const requiredRoles = rolesRequiredForAction[beat.action as keyof typeof rolesRequiredForAction];
    if (requiredRoles !== undefined) {
      if (command.animationPlan.tier !== 'FULL_AUTO_RIG' || !requiredRoles.some((role) => roles.has(role))) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index, 'action'], message: 'Source motion exceeds the verified rig capability.'});
      }
      const behavior = beat.action === 'WALK_STEP' ? 'WALKER'
        : ['FLAP', 'GLIDE'].includes(beat.action) ? 'FLYER'
          : beat.action === 'SWIM' ? 'SWIMMER'
            : beat.action === 'SLITHER' ? 'CRAWLER' : 'ROLLER';
      if (plan.behaviorClass !== behavior) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index, 'action'], message: 'Source motion does not match the selected behavior.'});
      }
    }
  }
});

export const PixiSpriteCycleReadV1Schema = z.object({
  cycleId: z.string().regex(/^motion\.[a-z0-9.-]+$/).max(100),
  behaviorClassId: z.enum([
    'walker.biped', 'walker.quadruped', 'walker.avian', 'runner.biped', 'runner.quadruped',
    'hopper', 'flyer', 'glider', 'swimmer', 'crawler', 'slitherer', 'climber', 'waver',
    'reacher', 'dancer', 'turner', 'swaying_plant', 'growing', 'blooming', 'drifting',
    'falling', 'flowing', 'flickering', 'roller', 'rotator', 'swinger', 'bouncer',
    'slider', 'opener_closer',
  ]),
  variantId: z.string().regex(/^[a-z0-9-]+$/).max(60),
  playbackKind: z.enum(['FRAME_SEQUENCE', 'TRANSFORM_DRIVEN']),
  loopMode: z.enum(['LOOP', 'ONCE']),
  frameRate: z.number().int().min(1).max(12),
  startSeconds: z.number().finite().min(0).max(30),
  endSeconds: z.number().finite().gt(0).max(30),
  x: z.number().finite().min(0.12).max(0.88),
  y: z.number().finite().min(0.12).max(0.88),
  scale: z.number().finite().min(0.2).max(0.6),
  frameReads: z.array(PixiShowAssetReadV1Schema).min(1).max(4),
}).strict().superRefine((cycle, context) => {
  const expectedFrameCount = cycle.playbackKind === 'TRANSFORM_DRIVEN' ? 1 : 4;
  if (cycle.frameReads.length !== expectedFrameCount) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['frameReads'], message: 'Sprite cycle has an invalid frame count.'});
  }
  const frameIds = cycle.frameReads.map((frame) => frame.assetId);
  const expectedIds = Array.from({length: expectedFrameCount}, (_, index) => `${cycle.cycleId}.frame-${String(index + 1).padStart(2, '0')}`);
  if (JSON.stringify(frameIds) !== JSON.stringify(expectedIds)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['frameReads'], message: 'Sprite cycle frame IDs must be complete and ordered.'});
  }
  if (cycle.endSeconds <= cycle.startSeconds) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['endSeconds'], message: 'Sprite cycle beat must have positive duration.'});
  }
  if (cycle.playbackKind === 'TRANSFORM_DRIVEN' && cycle.behaviorClassId !== 'slider') {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['behaviorClassId'], message: 'Single-frame transform motion is only allowed for the slider class.'});
  }
});

export const PixiRendererShowEnvelopeV2Schema = z.object({
  contractName: z.literal('PixiRendererShowEnvelopeV2'),
  contractVersion: z.literal('2.0'),
  rendererLaunchV2: PixiRendererLaunchV2WireSchema,
  showPlan: PixiShowPlanV1Schema,
  assetReads: z.array(PixiShowAssetReadV1Schema).min(1).max(3),
  spriteCycleStatus: z.enum(['READY', 'BLOCKED', 'NOT_APPLICABLE']),
  spriteCycleReasonCode: z.enum([
    'ASSET_UNAVAILABLE', 'INVALID_CYCLE_REQUEST', 'UNKNOWN_CYCLE', 'VISUAL_REVIEW_REQUIRED',
    'RIGHTS_NOT_CLEARED', 'FRAME_QA_REQUIRED', 'CATALOG_NOT_REGISTERED', 'RENDERER_NOT_VERIFIED',
    'RUNTIME_NOT_ELIGIBLE', 'FRAME_QA_FAILED', 'NO_SAFE_PLACEMENT',
  ]).optional(),
  spriteCycle: PixiSpriteCycleReadV1Schema.optional(),
}).strict().superRefine((envelope, context) => {
  const launch = envelope.rendererLaunchV2;
  const plan = envelope.showPlan;
  if (
    launch.sessionId !== plan.sessionId
    || launch.sourceSha256 !== plan.sourceSha256
    || launch.animationPlan.packageId !== plan.packageId
    || launch.experienceSpecRef.id !== plan.experienceSpecRef.id
    || launch.experienceSpecRef.version !== plan.experienceSpecRef.version
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Show envelope identity differs from its V2 launch.'});
  }
  const readIds = envelope.assetReads.map((read) => read.assetId);
  if (new Set(readIds).size !== readIds.length || readIds.length !== plan.selectedAssetIds.length || plan.selectedAssetIds.some((id) => !readIds.includes(id))) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['assetReads'], message: 'Static capabilities must match selected show assets.'});
  }
  if (envelope.spriteCycle && envelope.spriteCycle.endSeconds > plan.durationSeconds) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle', 'endSeconds'], message: 'Sprite cycle exceeds the show duration.'});
  }
  if (envelope.spriteCycleStatus === 'READY' && (envelope.spriteCycle === undefined || envelope.spriteCycleReasonCode !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'READY requires cycle data and no reason.'});
  }
  if (envelope.spriteCycleStatus === 'BLOCKED' && (envelope.spriteCycle !== undefined || envelope.spriteCycleReasonCode === undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'BLOCKED requires a reason and no cycle data.'});
  }
  if (envelope.spriteCycleStatus === 'NOT_APPLICABLE' && (envelope.spriteCycle !== undefined || envelope.spriteCycleReasonCode !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'NOT_APPLICABLE cannot contain cycle data or a reason.'});
  }
  if (envelope.spriteCycle !== undefined) {
    const familyClasses: Record<string, readonly string[]> = {
      BIRD: ['flyer', 'glider', 'walker.avian'],
      INSECT: ['flyer', 'crawler'],
      FISH: ['swimmer'],
      QUADRUPED: ['walker.quadruped', 'runner.quadruped', 'hopper', 'crawler', 'slitherer', 'climber'],
      BIPED: ['walker.biped', 'runner.biped', 'climber', 'waver', 'reacher', 'dancer', 'turner'],
      PLANT: ['swaying_plant', 'growing', 'blooming'],
      VEHICLE: ['roller', 'glider', 'drifting', 'slider', 'rotator'],
      OBJECT: ['roller', 'drifting', 'slider', 'rotator', 'swinger', 'bouncer', 'opener_closer'],
      UNKNOWN: [],
    };
    if (!familyClasses[plan.visualSubjectHintId]?.includes(envelope.spriteCycle.behaviorClassId)) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle', 'behaviorClassId'], message: 'Sprite cycle is incompatible with the confirmed subject family.'});
    }
    const cycle = envelope.spriteCycle;
    const region = plan.sourceSubjectRegion;
    if (
      region.x - 0.14 <= cycle.x && cycle.x <= region.x + region.width + 0.14
      && region.y - 0.14 <= cycle.y && cycle.y <= region.y + region.height + 0.14
    ) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle'], message: 'Sprite cycle overlaps the padded source-subject bounds.'});
    }
    if (plan.beats.some((beat) => beat.targetRole === 'SUPPLEMENTAL_ASSET' && Math.hypot(cycle.x - beat.x, cycle.y - beat.y) < 0.22)) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle'], message: 'Sprite cycle overlaps a static supplemental asset.'});
    }
  }
});

export const PixiRendererShowEnvelopeV3Schema = z.object({
  contractName: z.literal('PixiRendererShowEnvelopeV3'),
  contractVersion: z.literal('3.0'),
  rendererLaunchV2: PixiRendererLaunchV2WireSchema,
  showPlan: PixiShowPlanV2Schema,
  assetReads: z.array(PixiShowAssetReadV1Schema).max(3),
  spriteCycleStatus: z.enum(['READY', 'BLOCKED', 'NOT_APPLICABLE']),
  spriteCycleReasonCode: z.enum([
    'ASSET_UNAVAILABLE', 'INVALID_CYCLE_REQUEST', 'UNKNOWN_CYCLE', 'VISUAL_REVIEW_REQUIRED',
    'RIGHTS_NOT_CLEARED', 'FRAME_QA_REQUIRED', 'CATALOG_NOT_REGISTERED', 'RENDERER_NOT_VERIFIED',
    'RUNTIME_NOT_ELIGIBLE', 'FRAME_QA_FAILED', 'NO_SAFE_PLACEMENT',
  ]).optional(),
  spriteCycle: PixiSpriteCycleReadV1Schema.optional(),
}).strict().superRefine((envelope, context) => {
  const launch = envelope.rendererLaunchV2;
  const plan = envelope.showPlan;
  if (
    launch.sessionId !== plan.sessionId
    || launch.sourceSha256 !== plan.sourceSha256
    || launch.animationPlan.packageId !== plan.packageId
    || launch.experienceSpecRef.id !== plan.experienceSpecRef.id
    || launch.experienceSpecRef.version !== plan.experienceSpecRef.version
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Show envelope identity differs from its V2 launch.'});
  }
  const readIds = envelope.assetReads.map((read) => read.assetId);
  if (new Set(readIds).size !== readIds.length || readIds.length !== plan.selectedAssetIds.length || plan.selectedAssetIds.some((id) => !readIds.includes(id))) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['assetReads'], message: 'Capabilities must exactly match selected show assets.'});
  }
  if (envelope.spriteCycle && envelope.spriteCycle.endSeconds > plan.durationSeconds) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle', 'endSeconds'], message: 'Sprite cycle exceeds the show duration.'});
  }
  if (envelope.spriteCycleStatus === 'READY' && (envelope.spriteCycle === undefined || envelope.spriteCycleReasonCode !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'READY requires cycle data and no reason.'});
  }
  if (envelope.spriteCycleStatus === 'BLOCKED' && (envelope.spriteCycle !== undefined || envelope.spriteCycleReasonCode === undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'BLOCKED requires a reason and no cycle data.'});
  }
  if (envelope.spriteCycleStatus === 'NOT_APPLICABLE' && (envelope.spriteCycle !== undefined || envelope.spriteCycleReasonCode !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'NOT_APPLICABLE cannot contain cycle data or a reason.'});
  }
});

export const RendererLoadCommandV4Schema = z.object({
  ...RendererLoadCommandV3Schema.shape,
  contractName: z.literal('RendererLoadCommandV4'),
  contractVersion: z.literal('4.0'),
  protocolVersion: z.literal('4'),
  spriteCycleStatus: z.enum(['READY', 'BLOCKED', 'NOT_APPLICABLE']),
  spriteCycleReasonCode: z.enum([
    'ASSET_UNAVAILABLE', 'INVALID_CYCLE_REQUEST', 'UNKNOWN_CYCLE', 'VISUAL_REVIEW_REQUIRED',
    'RIGHTS_NOT_CLEARED', 'FRAME_QA_REQUIRED', 'CATALOG_NOT_REGISTERED', 'RENDERER_NOT_VERIFIED',
    'RUNTIME_NOT_ELIGIBLE', 'FRAME_QA_FAILED', 'NO_SAFE_PLACEMENT',
  ]).optional(),
  spriteCycle: PixiSpriteCycleReadV1Schema.optional(),
}).strict().superRefine((command, context) => {
  const {spriteCycle, spriteCycleStatus, spriteCycleReasonCode, ...v4Fields} = command;
  const legacyValidation = RendererLoadCommandV3Schema.safeParse({
    ...v4Fields,
    contractName: 'RendererLoadCommandV3',
    contractVersion: '3.0',
    protocolVersion: '3',
  });
  if (!legacyValidation.success) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'V4 base show must satisfy all V3 invariants.'});
  }
  if (spriteCycleStatus === 'READY' && (spriteCycle === undefined || spriteCycleReasonCode !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'READY requires cycle data and no reason.'});
  }
  if (spriteCycleStatus === 'BLOCKED' && (spriteCycle !== undefined || spriteCycleReasonCode === undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'BLOCKED requires a reason and no cycle data.'});
  }
  if (spriteCycleStatus === 'NOT_APPLICABLE' && (spriteCycle !== undefined || spriteCycleReasonCode !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'NOT_APPLICABLE cannot contain cycle data or a reason.'});
  }
  if (spriteCycle === undefined) return;
  const cycle = spriteCycle;
  if (cycle.endSeconds > command.showPlan.durationSeconds) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle', 'endSeconds'], message: 'Sprite cycle exceeds the show duration.'});
  }
  const familyClasses: Record<string, readonly string[]> = {
    BIRD: ['flyer', 'glider', 'walker.avian'],
    INSECT: ['flyer', 'crawler'],
    FISH: ['swimmer'],
    QUADRUPED: ['walker.quadruped', 'runner.quadruped', 'hopper', 'crawler', 'slitherer', 'climber'],
    BIPED: ['walker.biped', 'runner.biped', 'climber', 'waver', 'reacher', 'dancer', 'turner'],
    PLANT: ['swaying_plant', 'growing', 'blooming'],
    VEHICLE: ['roller', 'glider', 'drifting', 'slider', 'rotator'],
    OBJECT: ['roller', 'drifting', 'slider', 'rotator', 'swinger', 'bouncer', 'opener_closer'],
    UNKNOWN: [],
  };
  if (!familyClasses[command.showPlan.visualSubjectHintId]?.includes(cycle.behaviorClassId)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle', 'behaviorClassId'], message: 'Sprite cycle is incompatible with the confirmed subject family.'});
  }
  const region = command.showPlan.sourceSubjectRegion;
  if (
    region.x - 0.14 <= cycle.x && cycle.x <= region.x + region.width + 0.14
    && region.y - 0.14 <= cycle.y && cycle.y <= region.y + region.height + 0.14
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle'], message: 'Sprite cycle must remain outside the padded source-subject bounds.'});
  }
  for (const [index, beat] of command.showPlan.beats.entries()) {
    if (beat.targetRole === 'SUPPLEMENTAL_ASSET' && Math.hypot(cycle.x - beat.x, cycle.y - beat.y) < 0.22) {
      context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle'], message: `Sprite cycle overlaps supplemental asset beat ${index}.`});
      break;
    }
  }
});

export const RendererLoadCommandV5Schema = z.object({
  ...RendererLoadCommandV4Schema.shape,
  contractName: z.literal('RendererLoadCommandV5'),
  contractVersion: z.literal('5.0'),
  protocolVersion: z.literal('5'),
  showPlan: PixiShowPlanV2Schema,
  assetReads: z.array(PixiShowAssetReadV1Schema).max(3),
}).strict().superRefine((command, context) => {
  const {
    contractName: _contractName,
    contractVersion: _contractVersion,
    protocolVersion: _protocolVersion,
    showPlan,
    assetReads,
    spriteCycle,
    spriteCycleStatus: _spriteCycleStatus,
    spriteCycleReasonCode: _spriteCycleReasonCode,
    ...baseFields
  } = command;
  const baseValidation = RendererLoadCommandV2Schema.safeParse({
    ...baseFields,
    contractName: 'RendererLoadCommandV2',
    contractVersion: '2.0',
    protocolVersion: '2',
  });
  if (!baseValidation.success) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'V5 base renderer command must satisfy V2 invariants.'});
  }
  if (
    command.sessionId !== showPlan.sessionId
    || command.sourceSha256 !== showPlan.sourceSha256
    || command.animationPlan.packageId !== showPlan.packageId
    || command.experienceSpecRef.id !== showPlan.experienceSpecRef.id
    || command.experienceSpecRef.version !== showPlan.experienceSpecRef.version
  ) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan'], message: 'Show launch identity does not match renderer data.'});
  }
  if (showPlan.durationSeconds !== command.animationPlan.durationSeconds) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'durationSeconds'], message: 'Show and renderer timelines must have the same duration.'});
  }
  if (!(behaviorForSubjectHint[showPlan.visualSubjectHintId] as readonly string[]).includes(showPlan.behaviorClass)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'behaviorClass'], message: 'Behavior is incompatible with the visual subject hint.'});
  }
  const readIds = assetReads.map((read) => read.assetId);
  if (new Set(readIds).size !== readIds.length || readIds.length !== showPlan.selectedAssetIds.length || showPlan.selectedAssetIds.some((id) => !readIds.includes(id))) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['assetReads'], message: 'Asset capabilities must exactly match selected show assets.'});
  }
  const maskFields = [command.maskReadEndpoint, command.maskReadCapability, command.maskSha256];
  if (maskFields.some((value) => value !== undefined) && maskFields.some((value) => value === undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Derived mask fields must be supplied together.'});
  }
  const readPartIds = command.partMaskReads.map((part) => part.partId).sort();
  const rigPartIds = command.rigParts.map((part) => part.partId).sort();
  if (JSON.stringify(readPartIds) !== JSON.stringify(rigPartIds)) {
    context.addIssue({code: z.ZodIssueCode.custom, message: 'Part mask reads must match rig parts.'});
  }
  const roles = new Set(command.rigParts.map((part) => part.role.toLowerCase().replaceAll('_', '-')));
  for (const [index, beat] of showPlan.beats.entries()) {
    if (beat.targetRole === 'SUPPLEMENTAL_ASSET') {
      if (!staticSupplementActions.has(beat.action)) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index, 'action'], message: 'Static sprites cannot claim articulated motion.'});
      }
      if (beat.x < 0.12 || beat.x > 0.88 || beat.y < 0.12 || beat.y > 0.88) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index], message: 'Supplemental sprite placement must remain inside the safe stage.'});
      }
      const region = showPlan.sourceSubjectRegion;
      if (region.x - 0.14 <= beat.x && beat.x <= region.x + region.width + 0.14 && region.y - 0.14 <= beat.y && beat.y <= region.y + region.height + 0.14) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index], message: 'Supplemental sprite placement overlaps the child drawing.'});
      }
      continue;
    }
    const requiredRoles = rolesRequiredForAction[beat.action as keyof typeof rolesRequiredForAction];
    if (requiredRoles !== undefined) {
      if (command.animationPlan.tier !== 'FULL_AUTO_RIG' || !requiredRoles.some((role) => roles.has(role))) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index, 'action'], message: 'Source motion exceeds the verified rig capability.'});
      }
      const behavior = beat.action === 'WALK_STEP' ? 'WALKER'
        : ['FLAP', 'GLIDE'].includes(beat.action) ? 'FLYER'
          : beat.action === 'SWIM' ? 'SWIMMER'
            : beat.action === 'SLITHER' ? 'CRAWLER' : 'ROLLER';
      if (showPlan.behaviorClass !== behavior) {
        context.addIssue({code: z.ZodIssueCode.custom, path: ['showPlan', 'beats', index, 'action'], message: 'Source motion does not match the selected behavior.'});
      }
    }
  }
  if (command.spriteCycleStatus === 'READY' && (spriteCycle === undefined || command.spriteCycleReasonCode !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'READY requires cycle data and no reason.'});
  }
  if (command.spriteCycleStatus === 'BLOCKED' && (spriteCycle !== undefined || command.spriteCycleReasonCode === undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'BLOCKED requires a reason and no cycle data.'});
  }
  if (command.spriteCycleStatus === 'NOT_APPLICABLE' && (spriteCycle !== undefined || command.spriteCycleReasonCode !== undefined)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycleStatus'], message: 'NOT_APPLICABLE cannot contain cycle data or a failure reason.'});
  }
  if (spriteCycle === undefined) return;
  if (spriteCycle.endSeconds > showPlan.durationSeconds) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle', 'endSeconds'], message: 'Sprite cycle exceeds the show duration.'});
  }
  const familyClasses: Record<string, readonly string[]> = {
    BIRD: ['flyer', 'glider', 'walker.avian'],
    INSECT: ['flyer', 'crawler'],
    FISH: ['swimmer'],
    QUADRUPED: ['walker.quadruped', 'runner.quadruped', 'hopper', 'crawler', 'slitherer', 'climber'],
    BIPED: ['walker.biped', 'runner.biped', 'climber', 'waver', 'reacher', 'dancer', 'turner'],
    PLANT: ['swaying_plant', 'growing', 'blooming'],
    VEHICLE: ['roller', 'glider', 'drifting', 'slider', 'rotator'],
    OBJECT: ['roller', 'drifting', 'slider', 'rotator', 'swinger', 'bouncer', 'opener_closer'],
    UNKNOWN: [],
  };
  if (!familyClasses[showPlan.visualSubjectHintId]?.includes(spriteCycle.behaviorClassId)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle', 'behaviorClassId'], message: 'Sprite cycle is incompatible with the confirmed subject family.'});
  }
  const region = showPlan.sourceSubjectRegion;
  if (region.x - 0.14 <= spriteCycle.x && spriteCycle.x <= region.x + region.width + 0.14 && region.y - 0.14 <= spriteCycle.y && spriteCycle.y <= region.y + region.height + 0.14) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle'], message: 'Sprite cycle must remain outside the padded source-subject bounds.'});
  }
  if (showPlan.beats.some((beat) => beat.targetRole === 'SUPPLEMENTAL_ASSET' && Math.hypot(spriteCycle.x - beat.x, spriteCycle.y - beat.y) < 0.22)) {
    context.addIssue({code: z.ZodIssueCode.custom, path: ['spriteCycle'], message: 'Sprite cycle overlaps a static supplemental asset.'});
  }
});

export type PixiShowPlanV1 = z.infer<typeof PixiShowPlanV1Schema>;
export type PixiShowPlanV2 = z.infer<typeof PixiShowPlanV2Schema>;
export type PixiShowAssetReadV1 = z.infer<typeof PixiShowAssetReadV1Schema>;
export type PixiRendererLaunchV2Wire = z.infer<typeof PixiRendererLaunchV2WireSchema>;
export type PixiRendererShowEnvelopeV1 = z.infer<typeof PixiRendererShowEnvelopeV1Schema>;
export type RendererLoadCommandV3 = z.infer<typeof RendererLoadCommandV3Schema>;
export type PixiSpriteCycleReadV1 = z.infer<typeof PixiSpriteCycleReadV1Schema>;
export type PixiRendererShowEnvelopeV2 = z.infer<typeof PixiRendererShowEnvelopeV2Schema>;
export type PixiRendererShowEnvelopeV3 = z.infer<typeof PixiRendererShowEnvelopeV3Schema>;
export type RendererLoadCommandV4 = z.infer<typeof RendererLoadCommandV4Schema>;
export type RendererLoadCommandV5 = z.infer<typeof RendererLoadCommandV5Schema>;
