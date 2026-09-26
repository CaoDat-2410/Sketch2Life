import {Container, Mesh, MeshGeometry, Texture, type Application} from 'pixi.js';
import {gsap} from 'gsap';

import {
  RiggedArtworkPackageV1Schema,
  VisualAnimationPlanV2Schema,
  type RigDefinitionV1,
  type RiggedArtworkPackageV1,
  type VisualAnimationPlanV2,
} from './contractsV2';

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
  load(packageInput: unknown, planInput: unknown, sourceTexture: Texture): void;
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

export function createAutoRigPlayer(options: AutoRigPlayerOptions): AutoRigPlayer {
  const scene = new Container();
  scene.sortableChildren = true;
  options.app.stage.addChild(scene);
  let timeline: gsap.core.Timeline | null = null;
  let mesh: Mesh<MeshGeometry> | null = null;
  let geometry: MeshGeometry | null = null;
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
    const rig = packageValue?.rig;
    if (rig == null || geometry === null) return;
    geometry.positions = skinPositions(rig, poses, STAGE_WIDTH, STAGE_HEIGHT);
  };

  return {
    load(packageInput: unknown, planInput: unknown, sourceTexture: Texture): void {
      timeline?.kill();
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

      const rig = parsedPackage.rig;
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
      poses = new Map(rig.bones.map((bone) => [bone.boneId, neutralPose()]));
      state = 'READY';
      publish();
    },

    play(): void {
      if (packageValue?.rig == null || plan === null) throw new Error('Load a valid rig before playback.');
      if (timeline !== null) {
        state = 'PLAYING';
        timeline.play();
        publish();
        return;
      }
      timeline = gsap.timeline({
        paused: true,
        onUpdate: publish,
        onComplete: () => {
          state = 'COMPLETED';
          stopTicker();
          publish();
          options.onCompleted?.();
        },
      });
      for (const track of plan.tracks) {
        const pose = poses.get(track.boneId);
        if (pose === undefined) throw new Error(`Unknown V2 bone target ${track.boneId}.`);
        const [firstFrame, ...remainingFrames] = track.keyframes;
        timeline.set(pose, firstFrame.pose, firstFrame.atSeconds);
        let previousTime = firstFrame.atSeconds;
        for (const frame of remainingFrames) {
          timeline.to(
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
      ticker = deform;
      options.app.ticker.add(ticker);
      state = 'PLAYING';
      timeline.play(0);
      publish();
    },

    pause(): void {
      timeline?.pause();
      state = 'PAUSED';
      publish();
    },

    replay(): void {
      if (timeline === null) throw new Error('Play the rig before replay.');
      if (ticker === null) {
        ticker = deform;
        options.app.ticker.add(ticker);
      }
      state = 'PLAYING';
      timeline.restart();
      publish();
    },

    seekTo(seconds: number): void {
      if (timeline === null) return;
      timeline.time(Math.min(Math.max(seconds, 0), timeline.duration()), false);
      deform();
      publish();
    },

    seekRelative(seconds: number): void {
      if (timeline === null) return;
      timeline.time(Math.min(Math.max(timeline.time() + seconds, 0), timeline.duration()), false);
      deform();
      publish();
    },

    getPlaybackState() {
      return {positionSeconds: timeline?.time() ?? 0, durationSeconds: timeline?.duration() ?? 0, state};
    },

    destroy(): void {
      timeline?.kill();
      timeline = null;
      stopTicker();
      scene.destroy({children: true});
      mesh = null;
      geometry = null;
      packageValue = null;
      plan = null;
      poses.clear();
    },
  };
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
