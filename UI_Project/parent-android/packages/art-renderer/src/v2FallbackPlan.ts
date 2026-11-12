import type {RendererLoadCommandV2} from './contractsV2';

/** Preserve the V1 Pixi fallback without disguising a whole-art move as a part rig. */
export function buildV2FallbackPlan(command: RendererLoadCommandV2): unknown {
  return {
    contractVersion: '1',
    planId: command.animationPlan.planId,
    planVersion: String(command.experienceSpecRef.version),
    stage: {width: 800, height: 600},
    objects: [{
      id: 'original-art',
      label: command.animationPlan.learningBridgeVi,
      asset: {
        sourceAssetId: 'source-original-art',
        sourceAssetVersion: '1',
        uri: 'source:original-art',
        assetKind: 'WHOLE_DRAWING',
        sourceSha256: command.sourceSha256,
      },
      initialTransform: {
        position: {x: 0.5, y: 0.5},
        scale: 1,
        rotationDegrees: 0,
        opacity: 1,
      },
      extractionStatus: 'READY',
      interactive: false,
    }],
    motions: [
      {id: 'fallback-reveal', sceneId: 'fallback', kind: 'DRAW_REVEAL', targetId: 'original-art', durationSeconds: 2},
      // The fallback keeps the viewport fixed and uses tiny in-frame nudges only. It does not
      // claim independent anatomy or fake flapping by zooming/rotating the full drawing.
      {id: 'fallback-nudge-up', sceneId: 'fallback', kind: 'MOVE_TO', targetId: 'original-art', durationSeconds: 2, to: {x: 0.5, y: 0.496}},
      {id: 'fallback-return-up', sceneId: 'fallback', kind: 'MOVE_TO', targetId: 'original-art', durationSeconds: 2, to: {x: 0.5, y: 0.5}},
      {id: 'fallback-nudge-side', sceneId: 'fallback', kind: 'MOVE_TO', targetId: 'original-art', durationSeconds: 2, to: {x: 0.504, y: 0.5}},
      {id: 'fallback-return-side', sceneId: 'fallback', kind: 'MOVE_TO', targetId: 'original-art', durationSeconds: 2, to: {x: 0.5, y: 0.5}},
      {id: 'fallback-still-hold', sceneId: 'fallback', kind: 'FADE', targetId: 'original-art', durationSeconds: 10, opacity: 1},
    ],
  };
}
