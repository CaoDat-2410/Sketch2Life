import {describe, expect, it} from 'vitest';

import {RiggedArtworkPackageV1Schema, VisualAnimationPlanV2Schema} from '../src/contractsV2';

const rig = {
  contractName: 'RigDefinitionV1',
  contractVersion: '1.0',
  archetype: 'butterfly',
  sourceRegion: {x: 0, y: 0, width: 1, height: 1},
  vertices: [
    {x: 0, y: 0, u: 0, v: 0},
    {x: 1, y: 0, u: 1, v: 0},
    {x: 0, y: 1, u: 0, v: 1},
    {x: 1, y: 1, u: 1, v: 1},
  ],
  triangles: [{a: 0, b: 2, c: 1}, {a: 1, b: 2, c: 3}],
  bones: [{boneId: 'root', parentId: null, pivotX: 0.5, pivotY: 0.5, maxRotationDegrees: 8}],
  weights: [0, 1, 2, 3].map((vertexIndex) => ({vertexIndex, influences: [{boneId: 'root', weight: 1}]})),
};

const packageFixture = {
  contractName: 'RiggedArtworkPackageV1',
  contractVersion: '1.0',
  packageId: 'rig-session-1',
  sessionId: 'session-1',
  sourceArtifactRef: 'artifact:source',
  sourceSha256: 'a'.repeat(64),
  target: {canonicalEntityId: 'anchor-butterfly', normalizedLabel: 'con bướm', confidence: 0.95, semanticTags: ['insect']},
  archetype: 'butterfly',
  tier: 'CUTOUT_MICRO_MOTION',
  rig,
  derivedArtifacts: [],
  validation: {contractName: 'RigValidationResultV1', contractVersion: '1.0', valid: true, selectedTier: 'CUTOUT_MICRO_MOTION', reasonCodes: ['SEGMENTATION_ADAPTER_UNAVAILABLE'], validatorVersion: '1'},
  pipelineVersion: '1',
  createdAt: '2026-09-25T06:00:00Z',
  originalArtPreserved: true,
};

describe('Renderer V2 contracts', () => {
  it('accepts a bounded source-derived package', () => {
    expect(RiggedArtworkPackageV1Schema.parse(packageFixture).rig?.vertices).toHaveLength(4);
  });

  it('rejects non-normalized weights', () => {
    const invalid = structuredClone(packageFixture);
    invalid.rig.weights[0].influences[0].weight = 0.7;
    expect(RiggedArtworkPackageV1Schema.safeParse(invalid).success).toBe(false);
  });

  it('accepts only bounded semantic tracks', () => {
    const result = VisualAnimationPlanV2Schema.safeParse({
      contractName: 'VisualAnimationPlanV2',
      contractVersion: '2.0',
      planId: 'visual-1',
      sessionId: 'session-1',
      experienceSpecRef: {id: 'spec-1', version: 1},
      packageId: 'rig-session-1',
      archetype: 'butterfly',
      tier: 'CUTOUT_MICRO_MOTION',
      durationSeconds: 2,
      tracks: [{
        trackId: 'flutter',
        boneId: 'root',
        profile: 'flutter',
        keyframes: [
          {atSeconds: 0, pose: {rotationDegrees: 0, translateX: 0, translateY: 0, scaleX: 1, scaleY: 1}},
          {atSeconds: 2, pose: {rotationDegrees: 8, translateX: 0, translateY: 0, scaleX: 1, scaleY: 1}},
        ],
        repeat: 0,
      }],
      learningBridgeVi: 'Bướm tìm hoa như thế nào nhỉ?',
      maxMotionLevel: 2,
    });
    expect(result.success).toBe(true);
  });
});
