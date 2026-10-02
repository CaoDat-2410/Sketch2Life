import {describe, expect, it} from 'vitest';

import {
  PixiRendererShowEnvelopeV2Schema,
  PixiRendererShowEnvelopeV1Schema,
  RendererLoadCommandV4Schema,
  RendererLoadCommandV3Schema,
} from '../src/contractsPixiShow';
import {RendererLoadCommandV2Schema} from '../src/contractsV2';

const animationPlan = {
  contractName: 'VisualAnimationPlanV2',
  contractVersion: '2.0',
  planId: 'visual-1',
  sessionId: 'session-1',
  experienceSpecRef: {id: 'spec-1', version: 1},
  packageId: 'rig-session-1',
  archetype: 'bird',
  tier: 'CUTOUT_MICRO_MOTION',
  durationSeconds: 20,
  tracks: [{
    trackId: 'root-motion',
    boneId: 'root',
    profile: 'breathe',
    keyframes: [{atSeconds: 0, pose: {}}, {atSeconds: 20, pose: {}}],
  }],
  learningBridgeVi: 'Cùng khám phá nhé.',
};

const commandBase = {
  contractName: 'RendererLoadCommandV2',
  contractVersion: '2.0',
  protocolVersion: '2',
  sequence: 1,
  rendererInstanceId: 'renderer-1',
  sessionId: 'session-1',
  expectedSessionVersion: 3,
  experienceSpecRef: {id: 'spec-1', version: 1},
  sourceReadEndpoint: '/v1/renderer/source',
  sourceReadCapability: 's'.repeat(48),
  sourceSha256: 'a'.repeat(64),
  packageReadEndpoint: '/v1/renderer/rig-package',
  packageReadCapability: 'p'.repeat(48),
  packageSha256: 'b'.repeat(64),
  animationPlan,
};

const plan = {
  contractName: 'PixiShowPlanV1',
  contractVersion: '1.0',
  planId: 'show-1',
  sessionId: 'session-1',
  packageId: 'rig-session-1',
  sourceSha256: 'a'.repeat(64),
  sourceSubjectRegion: {x: 0.4, y: 0.2, width: 0.2, height: 0.4},
  experienceSpecRef: {id: 'spec-1', version: 1},
  confirmedSubjectId: 'anchor-bird',
  visualSubjectHintId: 'BIRD',
  behaviorClass: 'FLYER',
  durationSeconds: 20,
  selectedAssetIds: ['approved-flower'],
  beats: [
    {beatId: 'notice', startSeconds: 0, endSeconds: 4, action: 'NOTICE', targetRole: 'SOURCE_SUBJECT', x: 0.5, y: 0.5},
    {beatId: 'meet-flower', startSeconds: 5, endSeconds: 10, action: 'INTERACT', targetRole: 'SUPPLEMENTAL_ASSET', assetId: 'approved-flower', x: 0.15, y: 0.8},
    {beatId: 'settle', startSeconds: 12, endSeconds: 17, action: 'SETTLE', targetRole: 'SOURCE_SUBJECT', x: 0.5, y: 0.5},
  ],
  endingStill: true,
};

const read = {
  assetId: 'approved-flower',
  readEndpoint: '/v1/renderer/pixi-asset',
  readCapability: 'r'.repeat(48),
  sha256: 'c'.repeat(64),
  byteLength: 124,
  contentType: 'image/png',
};

const cycle = {
  cycleId: 'motion.flyer-songbird.v2',
  behaviorClassId: 'flyer',
  variantId: 'songbird',
  playbackKind: 'FRAME_SEQUENCE',
  loopMode: 'LOOP',
  frameRate: 6,
  startSeconds: 0,
  endSeconds: 6,
  x: 0.82,
  y: 0.18,
  scale: 0.4,
  frameReads: Array.from({length: 4}, (_, index) => ({
    ...read,
    assetId: `motion.flyer-songbird.v2.frame-${String(index + 1).padStart(2, '0')}`,
  })),
};

describe('additive Pixi show contracts', () => {
  it('keeps the existing V2 command valid while accepting the additive V3 show command', () => {
    expect(RendererLoadCommandV2Schema.safeParse(commandBase).success).toBe(true);
    expect(RendererLoadCommandV3Schema.safeParse({
      ...commandBase,
      contractName: 'RendererLoadCommandV3',
      contractVersion: '3.0',
      protocolVersion: '3',
      showPlan: plan,
      assetReads: [read],
    }).success).toBe(true);
  });

  it('rejects stale show identity, an unselected sprite capability, and an unsafe still window', () => {
    const command = {
      ...commandBase,
      contractName: 'RendererLoadCommandV3',
      contractVersion: '3.0',
      protocolVersion: '3',
      showPlan: plan,
      assetReads: [read],
    };
    expect(RendererLoadCommandV3Schema.safeParse({
      ...command,
      sourceSha256: 'd'.repeat(64),
    }).success).toBe(false);
    expect(RendererLoadCommandV3Schema.safeParse({
      ...command,
      assetReads: [{...read, assetId: 'invented-id'}],
    }).success).toBe(false);
    expect(RendererLoadCommandV3Schema.safeParse({
      ...command,
      showPlan: {...plan, beats: [...plan.beats.slice(0, 2), {...plan.beats[2], endSeconds: 19}]},
    }).success).toBe(false);
  });

  it('validates the server envelope before mobile converts it into a launch command', () => {
    const envelope = {
      contractName: 'PixiRendererShowEnvelopeV1',
      contractVersion: '1.0',
      rendererLaunchV2: {
        contractName: 'PixiRendererLaunchV2',
        contractVersion: '2.0',
        sessionId: 'session-1',
        expectedSessionVersion: 3,
        experienceSpecRef: {id: 'spec-1', version: 1},
        sourceReadEndpoint: '/v1/renderer/source',
        sourceReadCapability: 's'.repeat(48),
        sourceSha256: 'a'.repeat(64),
        packageReadEndpoint: '/v1/renderer/rig-package',
        packageReadCapability: 'p'.repeat(48),
        packageSha256: 'b'.repeat(64),
        packageReadExpiresAt: '2026-10-01T00:00:00Z',
        partMaskReads: [],
        rigParts: [],
        animationPlan,
        fallbackLaunch: {},
      },
      showPlan: plan,
      assetReads: [read],
    };
    expect(PixiRendererShowEnvelopeV1Schema.safeParse(envelope).success).toBe(true);
    expect(PixiRendererShowEnvelopeV1Schema.safeParse({
      ...envelope,
      rendererLaunchV2: {...envelope.rendererLaunchV2, packageReadCapability: 'x'},
    }).success).toBe(false);
  });

  it('adds V4 cycle reads while preserving V3 validation and independent gate states', () => {
    const baseV3 = {
      ...commandBase,
      contractName: 'RendererLoadCommandV3',
      contractVersion: '3.0',
      protocolVersion: '3',
      showPlan: plan,
      assetReads: [read],
    };
    const v4 = {
      ...baseV3,
      contractName: 'RendererLoadCommandV4',
      contractVersion: '4.0',
      protocolVersion: '4',
      spriteCycleStatus: 'READY',
      spriteCycle: cycle,
    };
    expect(RendererLoadCommandV4Schema.safeParse(v4).success).toBe(true);
    expect(RendererLoadCommandV4Schema.safeParse({...v4, spriteCycleStatus: 'BLOCKED'}).success).toBe(false);
    expect(RendererLoadCommandV4Schema.safeParse({
      ...v4,
      spriteCycle: {...cycle, behaviorClassId: 'swimmer'},
    }).success).toBe(false);
    expect(RendererLoadCommandV4Schema.safeParse({
      ...v4,
      spriteCycle: {...cycle, x: 0.5, y: 0.4},
    }).success).toBe(false);
    expect(RendererLoadCommandV4Schema.safeParse({
      ...baseV3,
      contractName: 'RendererLoadCommandV4',
      contractVersion: '4.0',
      protocolVersion: '4',
      spriteCycleStatus: 'BLOCKED',
      spriteCycleReasonCode: 'RIGHTS_NOT_CLEARED',
    }).success).toBe(true);
  });

  it('validates the additive V2 show envelope status/cycle consistency', () => {
    const launch = {
      contractName: 'PixiRendererLaunchV2',
      contractVersion: '2.0',
      sessionId: 'session-1',
      expectedSessionVersion: 3,
      experienceSpecRef: {id: 'spec-1', version: 1},
      sourceReadEndpoint: '/v1/renderer/source',
      sourceReadCapability: 's'.repeat(48),
      sourceSha256: 'a'.repeat(64),
      packageReadEndpoint: '/v1/renderer/rig-package',
      packageReadCapability: 'p'.repeat(48),
      packageSha256: 'b'.repeat(64),
      packageReadExpiresAt: '2026-10-01T00:00:00Z',
      partMaskReads: [],
      rigParts: [],
      animationPlan,
      fallbackLaunch: {},
    };
    const envelope = {
      contractName: 'PixiRendererShowEnvelopeV2',
      contractVersion: '2.0',
      rendererLaunchV2: launch,
      showPlan: plan,
      assetReads: [read],
      spriteCycleStatus: 'READY',
      spriteCycle: cycle,
    };
    expect(PixiRendererShowEnvelopeV2Schema.safeParse(envelope).success).toBe(true);
    expect(PixiRendererShowEnvelopeV2Schema.safeParse({
      ...envelope,
      spriteCycleStatus: 'BLOCKED',
      spriteCycleReasonCode: 'RIGHTS_NOT_CLEARED',
    }).success).toBe(false);
  });
});
