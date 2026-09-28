import {Container, Mesh, MeshGeometry, Sprite, Texture, type Application} from 'pixi.js';
import {gsap} from 'gsap';

import {
  RiggedArtworkPackageV1Schema,
  VisualAnimationPlanV2Schema,
  type RigDefinitionV1,
  type RiggedArtworkPackageV1,
  type VisualAnimationPlanV2,
} from './contractsV2';
import {detectPrimaryForegroundRegion, type NormalizedRegion} from './foregroundRegion';
import {createSubjectCutoutLayers, requireVerifiedCutoutMask} from './subjectCutout';

interface MutablePose {
  rotationDegrees: number;
  translateX: number;
  translateY: number;
  scaleX: number;
  scaleY: number;
}

export interface AutoRigPlayerOptions {
  readonly app: Application;
  readonly onProgress?: (positionSeconds: number, durationSeconds: number, state: 'READY' | 'PLAYING' | 'PAUSED' | 'COMPLETED') => void;
  readonly onCompleted?: () => void;
}

export interface AutoRigPlayer {
  load(
    packageInput: unknown,
    planInput: unknown,
    sourceTexture: Texture,
    sourceCanvas?: HTMLCanvasElement,
    maskCanvas?: HTMLCanvasElement,
  ): void;
  play(): void;
  pause(): void;
  replay(): void;
  seekTo(seconds: number): void;
  seekRelative(seconds: number): void;
  getPlaybackState(): {positionSeconds: number; durationSeconds: number; state: 'READY' | 'PLAYING' | 'PAUSED' | 'COMPLETED'};
  destroy(): void;
}

const STAGE_WIDTH = 800;
const STAGE_HEIGHT = 600;

interface PartMeshState {
  readonly boneId: string;
  readonly geometry: MeshGeometry;
  readonly rest: Float32Array;
}

export function createAutoRigPlayer(options: AutoRigPlayerOptions): AutoRigPlayer {
  const scene = new Container();
  scene.sortableChildren = true;
  options.app.stage.addChild(scene);
  let timeline: gsap.core.Timeline | null = null;
  let idleTimeline: gsap.core.Timeline | null = null;
  let mesh: Mesh<MeshGeometry> | null = null;
  let cutoutSprite: Sprite | null = null;
  let cutoutPivot = {x: 0, y: 0};
  let cutoutBaseScale = {x: 1, y: 1};
  let geometry: MeshGeometry | null = null;
  let activeRig: RigDefinitionV1 | null = null;
  let partMeshes: PartMeshState[] = [];
  let packageValue: RiggedArtworkPackageV1 | null = null;
  let plan: VisualAnimationPlanV2 | null = null;
  let poses = new Map<string, MutablePose>();
  let ticker: (() => void) | null = null;
  let state: 'READY' | 'PLAYING' | 'PAUSED' | 'COMPLETED' = 'READY';

  const publish = (): void => options.onProgress?.(timeline?.time() ?? 0, timeline?.duration() ?? 0, state);
  const stopTicker = (): void => {
    if (ticker !== null) options.app.ticker.remove(ticker);
    ticker = null;
  };

  const deform = (): void => {
    const rig = activeRig;
    if (rig == null) return;
    if (cutoutSprite !== null) {
      const rootPose = poses.get('root');
      if (rootPose !== undefined) {
        cutoutSprite.position.set(
          cutoutPivot.x + rootPose.translateX * STAGE_WIDTH,
          cutoutPivot.y + rootPose.translateY * STAGE_HEIGHT,
        );
        cutoutSprite.rotation = rootPose.rotationDegrees * Math.PI / 180;
        cutoutSprite.scale.set(cutoutBaseScale.x * rootPose.scaleX, cutoutBaseScale.y * rootPose.scaleY);
      }
      return;
    }
    if (partMeshes.length > 0) {
      const bones = new Map(rig.bones.map((bone) => [bone.boneId, bone]));
      const root = bones.get('root');
      const rootPose = poses.get('root');
      for (const part of partMeshes) {
        const bone = bones.get(part.boneId);
        const pose = poses.get(part.boneId);
        if (bone === undefined || pose === undefined) continue;
        let next = transformPositions(part.rest, rig, bone, pose, STAGE_WIDTH, STAGE_HEIGHT);
        if (part.boneId !== 'root' && root !== undefined && rootPose !== undefined) {
          next = transformPositions(next, rig, root, rootPose, STAGE_WIDTH, STAGE_HEIGHT);
        }
        part.geometry.positions = next;
      }
      return;
    }
    if (geometry !== null) geometry.positions = skinPositions(rig, poses, STAGE_WIDTH, STAGE_HEIGHT);
  };

  const startTicker = (): void => {
    if (ticker !== null) return;
    ticker = deform;
    options.app.ticker.add(ticker);
  };

  const buildTimeline = (animationPlan: VisualAnimationPlanV2): gsap.core.Timeline => {
    const nextTimeline = gsap.timeline({
      paused: true,
      onUpdate: publish,
      onComplete: () => {
        state = 'COMPLETED';
        const rootPose = poses.get('root');
        if (rootPose !== undefined) {
          idleTimeline?.kill();
          idleTimeline = gsap.timeline({repeat: -1, yoyo: true})
            .to(rootPose, {translateY: -0.006, rotationDegrees: 0.8, duration: 1.8, ease: 'sine.inOut'})
            .to(rootPose, {translateY: 0.003, rotationDegrees: -0.5, duration: 2.1, ease: 'sine.inOut'});
          startTicker();
        } else {
          stopTicker();
        }
        deform();
        publish();
        options.onCompleted?.();
      },
    });
    for (const track of animationPlan.tracks) {
      const pose = poses.get(track.boneId);
      if (pose === undefined) throw new Error(`Unknown V2 bone target ${track.boneId}.`);
      const [firstFrame, ...remainingFrames] = track.keyframes;
      nextTimeline.set(pose, firstFrame.pose, firstFrame.atSeconds);
      let previousTime = firstFrame.atSeconds;
      for (const frame of remainingFrames) {
        nextTimeline.to(
          pose,
          {
            ...frame.pose,
            duration: Math.max(frame.atSeconds - previousTime, 0.05),
            ease: 'sine.inOut',
          },
          previousTime,
        );
        previousTime = frame.atSeconds;
      }
    }
    // Keep the authoritative duration stable even when the last semantic track ends early.
    nextTimeline.set({}, {}, animationPlan.durationSeconds);
    return nextTimeline;
  };

  return {
    load(
      packageInput: unknown,
      planInput: unknown,
      sourceTexture: Texture,
      sourceCanvas?: HTMLCanvasElement,
      maskCanvas?: HTMLCanvasElement,
    ): void {
      timeline?.kill();
      idleTimeline?.kill();
      idleTimeline = null;
      stopTicker();
      scene.removeChildren().forEach((child) => child.destroy());
      mesh = null;
      geometry = null;
      cutoutSprite = null;
      cutoutBaseScale = {x: 1, y: 1};
      const parsedPackage = RiggedArtworkPackageV1Schema.parse(packageInput);
      const parsedPlan = VisualAnimationPlanV2Schema.parse(planInput);
      if (parsedPackage.packageId !== parsedPlan.packageId || parsedPackage.sessionId !== parsedPlan.sessionId) {
        throw new Error('Rig package and animation plan identity drift.');
      }
      if (parsedPackage.rig == null || !parsedPackage.validation.valid) {
        throw new Error('Rig package is not eligible for mesh playback.');
      }
      packageValue = parsedPackage;
      plan = parsedPlan;
      options.app.renderer.resize(STAGE_WIDTH, STAGE_HEIGHT);

      const detectedRegion = sourceCanvas === undefined ? null : regionFromCanvas(sourceCanvas);
      const packageRegion = maskCanvas === undefined ? detectedRegion : regionFromMask(sourceCanvas, maskCanvas);
      if (packageRegion === null && parsedPackage.rig.sourceRegion.width > 0.85 && parsedPackage.rig.sourceRegion.height > 0.85) {
        throw new Error('A full-frame mesh is not eligible for V2 subject motion.');
      }
      const rig: RigDefinitionV1 = packageRegion === null
        ? parsedPackage.rig
        : {...parsedPackage.rig, sourceRegion: packageRegion};
      activeRig = rig;
      partMeshes = [];
      requireVerifiedCutoutMask(parsedPackage.tier, maskCanvas !== undefined);
      if (parsedPackage.tier === 'CUTOUT_MICRO_MOTION' && sourceCanvas !== undefined && maskCanvas !== undefined) {
        const sourceContext = sourceCanvas.getContext('2d', {willReadFrequently: true});
        const maskContext = maskCanvas.getContext('2d', {willReadFrequently: true});
        if (sourceContext === null || maskContext === null) throw new Error('MASK_CANVAS_UNAVAILABLE');
        const layers = createSubjectCutoutLayers(
          sourceContext.getImageData(0, 0, sourceCanvas.width, sourceCanvas.height).data,
          maskContext.getImageData(0, 0, maskCanvas.width, maskCanvas.height).data,
          sourceCanvas.width,
          sourceCanvas.height,
        );
        if (!regionMatches(packageRegion, layers.sourceRegion)) throw new Error('MASK_REGION_MISMATCH');
        activeRig = {...rig, sourceRegion: layers.sourceRegion};
        const backgroundCanvas = canvasFromPixels(sourceCanvas.width, sourceCanvas.height, layers.backgroundPixels);
        const cutoutCanvas = canvasFromPixels(sourceCanvas.width, sourceCanvas.height, layers.subjectPixels);
        const background = spriteFromCanvas(backgroundCanvas);
        background.zIndex = 0;
        scene.addChild(background);
        cutoutSprite = new Sprite(Texture.from(cutoutCanvas));
        cutoutSprite.width = STAGE_WIDTH;
        cutoutSprite.height = STAGE_HEIGHT;
        cutoutBaseScale = {x: STAGE_WIDTH / sourceCanvas.width, y: STAGE_HEIGHT / sourceCanvas.height};
        cutoutPivot = {
          x: (layers.sourceRegion.x + layers.sourceRegion.width / 2) * STAGE_WIDTH,
          y: (layers.sourceRegion.y + layers.sourceRegion.height / 2) * STAGE_HEIGHT,
        };
        cutoutSprite.anchor.set(
          (layers.sourceRegion.x + layers.sourceRegion.width / 2),
          (layers.sourceRegion.y + layers.sourceRegion.height / 2),
        );
        cutoutSprite.position.set(cutoutPivot.x, cutoutPivot.y);
        cutoutSprite.zIndex = 10;
        scene.addChild(cutoutSprite);
      } else if (sourceCanvas !== undefined && packageRegion !== null) {
        const background = backgroundSprite(sourceCanvas, packageRegion);
        background.zIndex = 0;
        scene.addChild(background);
      }
      if (parsedPackage.tier !== 'CUTOUT_MICRO_MOTION' && rig.archetype === 'butterfly' && packageRegion !== null) {
        const butterfly = butterflyPartMeshes(rig, sourceTexture);
        partMeshes = butterfly.states;
        butterfly.meshes.forEach((part, index) => {
          part.zIndex = 10 + index;
          scene.addChild(part);
        });
      } else if (cutoutSprite === null) {
        geometry = new MeshGeometry({
          positions: restPositions(rig, STAGE_WIDTH, STAGE_HEIGHT),
          uvs: new Float32Array(rig.vertices.flatMap((vertex) => [
            rig.sourceRegion.x + vertex.u * rig.sourceRegion.width,
            rig.sourceRegion.y + vertex.v * rig.sourceRegion.height,
          ])),
          indices: new Uint32Array(rig.triangles.flatMap((triangle) => [triangle.a, triangle.b, triangle.c])),
        });
        mesh = new Mesh({geometry, texture: sourceTexture});
        mesh.zIndex = 10;
        scene.addChild(mesh);
      }
      poses = new Map(rig.bones.map((bone) => [bone.boneId, neutralPose()]));
      timeline = buildTimeline(parsedPlan);
      timeline.pause(0);
      deform();
      state = 'READY';
      publish();
    },

    play(): void {
      if (packageValue?.rig == null || plan === null || timeline === null) {
        throw new Error('Load a valid rig before playback.');
      }
      if (state === 'COMPLETED' || timeline.time() >= timeline.duration()) timeline.pause(0);
      idleTimeline?.kill();
      idleTimeline = null;
      startTicker();
      state = 'PLAYING';
      timeline.play();
      publish();
    },

    pause(): void {
      if (timeline === null) return;
      idleTimeline?.pause();
      timeline?.pause();
      stopTicker();
      deform();
      state = 'PAUSED';
      publish();
    },

    replay(): void {
      if (timeline === null) throw new Error('Play the rig before replay.');
      idleTimeline?.kill();
      idleTimeline = null;
      startTicker();
      state = 'PLAYING';
      timeline.restart();
      publish();
    },

    seekTo(seconds: number): void {
      if (timeline === null) return;
      const next = Math.min(Math.max(seconds, 0), timeline.duration());
      timeline.time(next, false);
      if (next < timeline.duration() && state === 'COMPLETED') state = 'PAUSED';
      deform();
      publish();
    },

    seekRelative(seconds: number): void {
      if (timeline === null) return;
      const next = Math.min(Math.max(timeline.time() + seconds, 0), timeline.duration());
      timeline.time(next, false);
      if (next < timeline.duration() && state === 'COMPLETED') state = 'PAUSED';
      deform();
      publish();
    },

    getPlaybackState() {
      return {positionSeconds: timeline?.time() ?? 0, durationSeconds: timeline?.duration() ?? 0, state};
    },

    destroy(): void {
      timeline?.kill();
      timeline = null;
      idleTimeline?.kill();
      idleTimeline = null;
      stopTicker();
      scene.destroy({children: true});
      mesh = null;
      geometry = null;
      activeRig = null;
      cutoutSprite = null;
      cutoutBaseScale = {x: 1, y: 1};
      partMeshes = [];
      packageValue = null;
      plan = null;
      poses.clear();
    },
  };
}

function regionFromCanvas(canvas: HTMLCanvasElement): NormalizedRegion | null {
  const context = canvas.getContext('2d', {willReadFrequently: true});
  if (context === null) return null;
  const image = context.getImageData(0, 0, canvas.width, canvas.height);
  return detectPrimaryForegroundRegion(image.data, canvas.width, canvas.height);
}

function backgroundSprite(canvas: HTMLCanvasElement, region: NormalizedRegion): Sprite {
  const background = document.createElement('canvas');
  background.width = canvas.width;
  background.height = canvas.height;
  const context = background.getContext('2d');
  if (context === null) throw new Error('Background canvas is unavailable.');
  context.drawImage(canvas, 0, 0);
  context.fillStyle = '#fffef9';
  context.fillRect(
    Math.floor(region.x * canvas.width),
    Math.floor(region.y * canvas.height),
    Math.ceil(region.width * canvas.width),
    Math.ceil(region.height * canvas.height),
  );
  const sprite = new Sprite(Texture.from(background));
  sprite.width = STAGE_WIDTH;
  sprite.height = STAGE_HEIGHT;
  return sprite;
}

function spriteFromCanvas(canvas: HTMLCanvasElement): Sprite {
  const sprite = new Sprite(Texture.from(canvas));
  sprite.width = STAGE_WIDTH;
  sprite.height = STAGE_HEIGHT;
  return sprite;
}

function canvasFromPixels(width: number, height: number, pixels: Uint8ClampedArray): HTMLCanvasElement {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (context === null) throw new Error('Cutout canvas is unavailable.');
  const image = context.createImageData(width, height);
  image.data.set(pixels);
  context.putImageData(image, 0, 0);
  return canvas;
}

function regionFromMask(source: HTMLCanvasElement | undefined, mask: HTMLCanvasElement): NormalizedRegion {
  if (source === undefined || source.width !== mask.width || source.height !== mask.height) {
    throw new Error('MASK_DIMENSIONS_MISMATCH');
  }
  const context = mask.getContext('2d', {willReadFrequently: true});
  if (context === null) throw new Error('MASK_CANVAS_UNAVAILABLE');
  const pixels = context.getImageData(0, 0, mask.width, mask.height).data;
  const width = mask.width;
  const height = mask.height;
  let minX = width;
  let minY = height;
  let maxX = -1;
  let maxY = -1;
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const offset = (y * width + x) * 4;
      if ((pixels[offset] + pixels[offset + 1] + pixels[offset + 2]) / 3 * pixels[offset + 3] / 255 <= 8) continue;
      minX = Math.min(minX, x);
      minY = Math.min(minY, y);
      maxX = Math.max(maxX, x);
      maxY = Math.max(maxY, y);
    }
  }
  if (maxX < minX || (maxX - minX + 1) * (maxY - minY + 1) / (width * height) > 0.9) {
    throw new Error('MASK_REGION_INVALID');
  }
  return {
    x: minX / width,
    y: minY / height,
    width: (maxX + 1 - minX) / width,
    height: (maxY + 1 - minY) / height,
  };
}

function regionMatches(expected: NormalizedRegion | null, actual: NormalizedRegion): boolean {
  if (expected === null) return false;
  const tolerance = 0.04;
  return actual.x >= expected.x - tolerance
    && actual.y >= expected.y - tolerance
    && actual.x + actual.width <= expected.x + expected.width + tolerance
    && actual.y + actual.height <= expected.y + expected.height + tolerance;
}

function butterflyPartMeshes(
  rig: RigDefinitionV1,
  texture: Texture,
): {meshes: Mesh<MeshGeometry>[]; states: PartMeshState[]} {
  const parts: Array<{boneId: string; region: NormalizedRegion}> = [
    {boneId: 'left-wing', region: relativeRegion(rig.sourceRegion, 0, 0.08, 0.47, 0.84)},
    {boneId: 'right-wing', region: relativeRegion(rig.sourceRegion, 0.53, 0.08, 0.47, 0.84)},
    {boneId: 'root', region: relativeRegion(rig.sourceRegion, 0.38, 0, 0.24, 1)},
  ];
  const meshes: Mesh<MeshGeometry>[] = [];
  const states: PartMeshState[] = [];
  for (const part of parts) {
    const rest = rectanglePositions(part.region, STAGE_WIDTH, STAGE_HEIGHT);
    const partGeometry = new MeshGeometry({
      positions: rest,
      uvs: new Float32Array([
        part.region.x, part.region.y,
        part.region.x + part.region.width, part.region.y,
        part.region.x, part.region.y + part.region.height,
        part.region.x + part.region.width, part.region.y + part.region.height,
      ]),
      indices: new Uint32Array([0, 2, 1, 1, 2, 3]),
    });
    meshes.push(new Mesh({geometry: partGeometry, texture}));
    states.push({boneId: part.boneId, geometry: partGeometry, rest});
  }
  return {meshes, states};
}

function relativeRegion(
  source: NormalizedRegion,
  x: number,
  y: number,
  width: number,
  height: number,
): NormalizedRegion {
  return {
    x: source.x + x * source.width,
    y: source.y + y * source.height,
    width: width * source.width,
    height: height * source.height,
  };
}

function rectanglePositions(region: NormalizedRegion, width: number, height: number): Float32Array {
  const left = region.x * width;
  const top = region.y * height;
  const right = (region.x + region.width) * width;
  const bottom = (region.y + region.height) * height;
  return new Float32Array([left, top, right, top, left, bottom, right, bottom]);
}

function transformPositions(
  rest: Float32Array,
  rig: RigDefinitionV1,
  bone: RigDefinitionV1['bones'][number],
  pose: MutablePose,
  width: number,
  height: number,
): Float32Array {
  const output = new Float32Array(rest.length);
  const pivotX = (rig.sourceRegion.x + bone.pivotX * rig.sourceRegion.width) * width;
  const pivotY = (rig.sourceRegion.y + bone.pivotY * rig.sourceRegion.height) * height;
  const angle = Math.max(-bone.maxRotationDegrees, Math.min(bone.maxRotationDegrees, pose.rotationDegrees)) * Math.PI / 180;
  for (let index = 0; index < rest.length; index += 2) {
    const localX = (rest[index] - pivotX) * pose.scaleX;
    const localY = (rest[index + 1] - pivotY) * pose.scaleY;
    output[index] = pivotX + localX * Math.cos(angle) - localY * Math.sin(angle) + pose.translateX * width;
    output[index + 1] = pivotY + localX * Math.sin(angle) + localY * Math.cos(angle) + pose.translateY * height;
  }
  return output;
}

function neutralPose(): MutablePose {
  return {rotationDegrees: 0, translateX: 0, translateY: 0, scaleX: 1, scaleY: 1};
}

function restPositions(rig: RigDefinitionV1, width: number, height: number): Float32Array {
  const region = rig.sourceRegion;
  return new Float32Array(rig.vertices.flatMap((vertex) => [
    (region.x + vertex.x * region.width) * width,
    (region.y + vertex.y * region.height) * height,
  ]));
}

function skinPositions(
  rig: RigDefinitionV1,
  poses: ReadonlyMap<string, MutablePose>,
  width: number,
  height: number,
): Float32Array {
  const rest = restPositions(rig, width, height);
  const output = new Float32Array(rest.length);
  const bones = new Map(rig.bones.map((bone) => [bone.boneId, bone]));
  for (const vertexWeights of rig.weights) {
    const offset = vertexWeights.vertexIndex * 2;
    const x = rest[offset];
    const y = rest[offset + 1];
    let nextX = 0;
    let nextY = 0;
    for (const influence of vertexWeights.influences) {
      const bone = bones.get(influence.boneId);
      const pose = poses.get(influence.boneId);
      if (bone === undefined || pose === undefined) continue;
      const pivotX = (rig.sourceRegion.x + bone.pivotX * rig.sourceRegion.width) * width;
      const pivotY = (rig.sourceRegion.y + bone.pivotY * rig.sourceRegion.height) * height;
      const angle = Math.max(-bone.maxRotationDegrees, Math.min(bone.maxRotationDegrees, pose.rotationDegrees)) * Math.PI / 180;
      const localX = (x - pivotX) * pose.scaleX;
      const localY = (y - pivotY) * pose.scaleY;
      const transformedX = pivotX + localX * Math.cos(angle) - localY * Math.sin(angle) + pose.translateX * width;
      const transformedY = pivotY + localX * Math.sin(angle) + localY * Math.cos(angle) + pose.translateY * height;
      nextX += transformedX * influence.weight;
      nextY += transformedY * influence.weight;
    }
    output[offset] = nextX;
    output[offset + 1] = nextY;
  }
  return output;
}
