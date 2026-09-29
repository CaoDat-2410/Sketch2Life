import {afterEach, describe, expect, it, vi} from 'vitest';

vi.mock('pixi.js', () => {
  class MockContainer {
    children: MockSprite[] = [];
    sortableChildren = false;
    addChild(child: MockSprite): void { this.children.push(child); }
    removeChildren(): MockSprite[] { const children = this.children; this.children = []; return children; }
    destroy(): void { this.children = []; }
  }
  class MockTexture {
    constructor(readonly source: unknown) {}
    static from(source: unknown): MockTexture { return new MockTexture(source); }
    destroy(): void {}
  }
  class MockSprite {
    anchor = point();
    pivot = point();
    position = point();
    scale = point(1, 1);
    rotation = 0;
    zIndex = 0;
    constructor(readonly texture: MockTexture) {}
    destroy(): void {}
  }
  return {Container: MockContainer, Sprite: MockSprite, Texture: MockTexture};
});

import {createAutoRigPlayer} from '../src/autoRigPlayer';

function point(x = 0, y = 0) {
  return {x, y, set(nextX: number, nextY = nextX): void { this.x = nextX; this.y = nextY; }};
}

class MemoryCanvas {
  width = 64;
  height = 64;
  pixels = new Uint8ClampedArray(this.width * this.height * 4);
  context = {
    getImageData: (_x: number, _y: number, _width: number, _height: number) => ({data: this.pixels}),
    createImageData: (width: number, height: number) => ({data: new Uint8ClampedArray(width * height * 4)}),
    putImageData: (image: {data: Uint8ClampedArray}) => { this.pixels = new Uint8ClampedArray(image.data); },
  };
  getContext(): typeof this.context { return this.context; }
}

const neutral = {rotationDegrees: 0, translateX: 0, translateY: 0, scaleX: 1, scaleY: 1};
const sourceHash = 'a'.repeat(64);
const maskHashes = ['b', 'c', 'd'].map((letter) => letter.repeat(64));
const packageFixture = {
  contractName: 'RiggedArtworkPackageV1',
  contractVersion: '1.0',
  packageId: 'rig-player-fixture',
  sessionId: 'player-fixture',
  sourceArtifactRef: 'artifact:source',
  sourceSha256: sourceHash,
  target: {canonicalEntityId: 'anchor-butterfly', normalizedLabel: 'con bướm', confidence: 0.95, semanticTags: ['insect']},
  archetype: 'butterfly',
  tier: 'FULL_AUTO_RIG',
  rig: {
    contractName: 'RigDefinitionV1',
    contractVersion: '1.0',
    archetype: 'butterfly',
    sourceRegion: {x: 0.125, y: 0.1875, width: 0.765625, height: 0.609375},
    vertices: [
      {x: 0, y: 0, u: 0, v: 0}, {x: 1, y: 0, u: 1, v: 0},
      {x: 0, y: 1, u: 0, v: 1}, {x: 1, y: 1, u: 1, v: 1},
    ],
    triangles: [{a: 0, b: 2, c: 1}, {a: 1, b: 2, c: 3}],
    bones: [
      {boneId: 'root', parentId: null, pivotX: 0.5, pivotY: 0.5, maxRotationDegrees: 8},
      {boneId: 'left-wing', parentId: 'root', pivotX: 0.3, pivotY: 0.5, maxRotationDegrees: 18},
      {boneId: 'right-wing', parentId: 'root', pivotX: 0.7, pivotY: 0.5, maxRotationDegrees: 18},
    ],
    weights: [0, 1, 2, 3].map((vertexIndex) => ({vertexIndex, influences: [{boneId: 'root', weight: 1}]})),
  },
  parts: [
    {partId: 'left-wing', role: 'left-wing', boneId: 'left-wing', sourceRegion: {x: 0.125, y: 0.28, width: 0.28, height: 0.42}, confidence: 0.9, maskArtifactRef: 'artifact:left', maskSha256: maskHashes[0]},
    {partId: 'body', role: 'body', boneId: 'root', sourceRegion: {x: 0.4, y: 0.1875, width: 0.2, height: 0.61}, confidence: 0.9, maskArtifactRef: 'artifact:body', maskSha256: maskHashes[1]},
    {partId: 'right-wing', role: 'right-wing', boneId: 'right-wing', sourceRegion: {x: 0.61, y: 0.28, width: 0.28, height: 0.42}, confidence: 0.9, maskArtifactRef: 'artifact:right', maskSha256: maskHashes[2]},
  ],
  derivedArtifacts: [
    {artifactRef: 'artifact:parent', sha256: 'e'.repeat(64), contentType: 'image/png', byteLength: 100, role: 'ORIGINAL_DERIVED_MASK', sourceSha256: sourceHash, operation: 'fixture SAM mask', operationVersion: '1'},
    ...['left', 'body', 'right'].map((part, index) => ({artifactRef: `artifact:${part}`, sha256: maskHashes[index], contentType: 'image/png', byteLength: 100, role: 'ORIGINAL_DERIVED_PART_MASK', sourceSha256: sourceHash, operation: 'fixture SAM part mask', operationVersion: '1'})),
  ],
  validation: {contractName: 'RigValidationResultV1', contractVersion: '1.0', valid: true, selectedTier: 'FULL_AUTO_RIG', reasonCodes: [], validatorVersion: '1'},
  pipelineVersion: '1',
  createdAt: '2026-09-28T00:00:00Z',
  originalArtPreserved: true,
};

const planFixture = {
  contractName: 'VisualAnimationPlanV2',
  contractVersion: '2.0',
  planId: 'visual-player-fixture',
  sessionId: 'player-fixture',
  experienceSpecRef: {id: 'spec-player-fixture', version: 1},
  packageId: 'rig-player-fixture',
  archetype: 'butterfly',
  tier: 'FULL_AUTO_RIG',
  durationSeconds: 20,
  tracks: [{
    trackId: 'left-wing-beats',
    boneId: 'left-wing',
    profile: 'flutter',
    keyframes: [
      {atSeconds: 0, pose: neutral},
      {atSeconds: 2, pose: {...neutral, rotationDegrees: 14}},
      {atSeconds: 4, pose: neutral},
      {atSeconds: 14.4, pose: neutral},
    ],
    repeat: 0,
  }],
  learningBridgeVi: 'Cùng xem đôi cánh chuyển động nhé.',
  maxMotionLevel: 2,
};

function fillRect(canvas: MemoryCanvas, x0: number, y0: number, x1: number, y1: number, color: readonly number[]): void {
  for (let y = y0; y <= y1; y += 1) {
    for (let x = x0; x <= x1; x += 1) {
      const offset = (y * canvas.width + x) * 4;
      canvas.pixels.set(color, offset);
    }
  }
}

function makeFixtureCanvases(): {source: MemoryCanvas; parent: MemoryCanvas; parts: Map<string, MemoryCanvas>} {
  const source = new MemoryCanvas();
  for (let offset = 0; offset < source.pixels.length; offset += 4) source.pixels.set([250, 249, 245, 255], offset);
  fillRect(source, 8, 18, 25, 44, [235, 120, 30, 255]);
  fillRect(source, 26, 12, 38, 50, [20, 130, 240, 255]);
  fillRect(source, 39, 18, 56, 44, [235, 120, 30, 255]);
  const parent = new MemoryCanvas();
  for (let offset = 0; offset < parent.pixels.length; offset += 4) parent.pixels.set([0, 0, 0, 255], offset);
  const parts = new Map<string, MemoryCanvas>();
  for (const id of ['left-wing', 'body', 'right-wing']) {
    const part = new MemoryCanvas();
    for (let offset = 0; offset < part.pixels.length; offset += 4) part.pixels.set([0, 0, 0, 255], offset);
    parts.set(id, part);
  }
  const boxes = [
    ['left-wing', 8, 18, 25, 44],
    ['body', 26, 12, 38, 50],
    ['right-wing', 39, 18, 56, 44],
  ] as const;
  for (const [id, x0, y0, x1, y1] of boxes) {
    fillRect(parent, x0, y0, x1, y1, [255, 255, 255, 255]);
    const part = parts.get(id);
    if (part !== undefined) fillRect(part, x0, y0, x1, y1, [255, 255, 255, 255]);
  }
  return {source, parent, parts};
}

afterEach(() => vi.unstubAllGlobals());

describe('Pixi independent part playback', () => {
  it('builds separate semantic sprites, follows wing keyframes, and rests through 20s', () => {
    vi.stubGlobal('document', {createElement: () => new MemoryCanvas()});
    const stage = {
      children: [] as {children: unknown[]}[],
      addChild(child: {children: unknown[]}): void { this.children.push(child); },
    };
    const app = {
      stage,
      renderer: {resize: vi.fn()},
      ticker: {add: vi.fn(), remove: vi.fn()},
    };
    const {source, parent, parts} = makeFixtureCanvases();
    const player = createAutoRigPlayer({app: app as never});

    player.load(
      packageFixture,
      planFixture,
      source as never,
      parent as never,
      parts as never,
    );

    const sprites = stage.children[0].children as {rotation: number; zIndex: number}[];
    expect(sprites).toHaveLength(4); // reconstructed paper plus three source-derived part layers
    expect(player.getPlaybackState()).toMatchObject({durationSeconds: 20, state: 'READY'});
    player.seekTo(1);
    expect(sprites.some((sprite) => Math.abs(sprite.rotation) > 0.1)).toBe(true);
    player.seekTo(19);
    expect(sprites.every((sprite) => Math.abs(sprite.rotation) < 0.001)).toBe(true);
    player.destroy();
  });

  it('clears partially composed Pixi layers when invalid part masks degrade to fallback', () => {
    vi.stubGlobal('document', {createElement: () => new MemoryCanvas()});
    const stage = {
      children: [] as {children: unknown[]}[],
      addChild(child: {children: unknown[]}): void { this.children.push(child); },
    };
    const app = {stage, renderer: {resize: vi.fn()}, ticker: {add: vi.fn(), remove: vi.fn()}};
    const {source, parent} = makeFixtureCanvases();
    const player = createAutoRigPlayer({app: app as never});
    expect(() => player.load(packageFixture, planFixture, source as never, parent as never, new Map())).toThrow('PART_MASKS_REQUIRED');
    expect(stage.children[0].children).toHaveLength(0);
    player.destroy();
  });
});
