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
  load(packageInput: unknown, planInput: unknown, sourceTexture: Texture, sourceCanvas?: HTMLCanvasElement): void;
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
    load(packageInput: unknown, planInput: unknown, sourceTexture: Texture, sourceCanvas?: HTMLCanvasElement): void {
      timeline?.kill();
      idleTimeline?.kill();
      idleTimeline = null;
      stopTicker();
      scene.removeChildren().forEach((child) => child.destroy());
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
      const hasDerivedMask = parsedPackage.derivedArtifacts.some((artifact) => {
        if (typeof artifact !== 'object' || artifact === null) return false;
        const candidate = artifact as {role?: unknown; sourceSha256?: unknown};
        return candidate.role === 'ORIGINAL_DERIVED_MASK' && candidate.sourceSha256 === parsedPackage.sourceSha256;
      });
      const packageRegion = hasDerivedMask ? parsedPackage.rig.sourceRegion : detectedRegion;
      if (packageRegion === null && parsedPackage.rig.sourceRegion.width > 0.85 && parsedPackage.rig.sourceRegion.height > 0.85) {
        throw new Error('A full-frame mesh is not eligible for V2 subject motion.');
      }
      const rig: RigDefinitionV1 = packageRegion === null
        ? parsedPackage.rig
        : {...parsedPackage.rig, sourceRegion: packageRegion};
      activeRig = rig;
      partMeshes = [];
      if (sourceCanvas !== undefined && packageRegion !== null) {
        const background = backgroundSprite(sourceCanvas, packageRegion);
        background.zIndex = 0;
        scene.addChild(background);
      }
      if (rig.archetype === 'butterfly' && packageRegion !== null) {
        const butterfly = butterflyPartMeshes(rig, sourceTexture);
        partMeshes = butterfly.states;
        butterfly.meshes.forEach((part, index) => {
          part.zIndex = 10 + index;
          scene.addChild(part);
        });
      } else {
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
