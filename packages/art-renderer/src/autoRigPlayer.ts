import {Container, Sprite, Texture, type Application} from 'pixi.js';
import {gsap} from 'gsap';

import {
  RiggedArtworkPackageV1Schema,
  VisualAnimationPlanV2Schema,
  type RigDefinitionV1,
  type RiggedArtworkPackageV1,
  type VisualAnimationPlanV2,
} from './contractsV2';
import {type NormalizedRegion} from './foregroundRegion';
import {createSubjectCutoutLayers, requireVerifiedCutoutMask} from './subjectCutout';
import {fitCanvasToStage, type CanvasFit} from './canvasFit';

interface MutablePose {
  rotationDegrees: number;
  translateX: number;
  translateY: number;
  scaleX: number;
  scaleY: number;
}

type PlaybackState = 'READY' | 'PLAYING' | 'PAUSED' | 'COMPLETED';

export interface AutoRigPlayerOptions {
  readonly app: Application;
  readonly onProgress?: (positionSeconds: number, durationSeconds: number, state: PlaybackState) => void;
  readonly onCompleted?: () => void;
}

export interface AutoRigPlayer {
  load(
    packageInput: unknown,
    planInput: unknown,
    sourceCanvas?: HTMLCanvasElement,
    maskCanvas?: HTMLCanvasElement,
    partMaskCanvases?: ReadonlyMap<string, HTMLCanvasElement>,
  ): void;
  play(): void;
  pause(): void;
  replay(): void;
  seekTo(seconds: number): void;
  seekRelative(seconds: number): void;
  setShowBeat(action: AutoRigShowAction | null, progress: number): void;
  getPlaybackState(): {positionSeconds: number; durationSeconds: number; state: PlaybackState};
  destroy(): void;
}

export type AutoRigShowAction =
  | 'NOTICE'
  | 'APPROACH'
  | 'INTERACT'
  | 'WALK_STEP'
  | 'FLAP'
  | 'GLIDE'
  | 'SWIM'
  | 'SLITHER'
  | 'ROLL'
  | 'SETTLE';

const STAGE_WIDTH = 800;
const STAGE_HEIGHT = 600;

interface PartSpriteState {
  readonly partId: string;
  readonly boneId: string;
  readonly sprite: Sprite;
}

export function createAutoRigPlayer(options: AutoRigPlayerOptions): AutoRigPlayer {
  const scene = new Container();
  scene.sortableChildren = true;
  options.app.stage.addChild(scene);
  let timeline: gsap.core.Timeline | null = null;
  let cutoutSprite: Sprite | null = null;
  let cutoutPivot = {x: 0, y: 0};
  let artworkFit: CanvasFit = {scale: 1, x: 0, y: 0};
  let sourceSize = {width: STAGE_WIDTH, height: STAGE_HEIGHT};
  let activeRig: RigDefinitionV1 | null = null;
  let partSprites: PartSpriteState[] = [];
  let packageValue: RiggedArtworkPackageV1 | null = null;
  let plan: VisualAnimationPlanV2 | null = null;
  let poses = new Map<string, MutablePose>();
  let ownedTextures: Texture[] = [];
  let ticker: (() => void) | null = null;
  let state: PlaybackState = 'READY';
  let showBeat: {action: AutoRigShowAction; progress: number} | null = null;

  const publish = (): void => options.onProgress?.(timeline?.time() ?? 0, timeline?.duration() ?? 0, state);
  const stopTicker = (): void => {
    if (ticker !== null) options.app.ticker.remove(ticker);
    ticker = null;
  };

  const deform = (): void => {
    const rig = activeRig;
    if (rig === null) return;
    const rootPose = poses.get('root') ?? neutralPose();
    if (cutoutSprite !== null) {
      // Whole-subject fallback may breathe/float by a few pixels, but never scales or rotates
      // the drawing. The camera and original artwork framing remain fixed.
      const showOffset = cutoutShowOffset(showBeat);
      cutoutSprite.position.set(
        cutoutPivot.x + rootPose.translateX * STAGE_WIDTH + showOffset.x,
        cutoutPivot.y + rootPose.translateY * STAGE_HEIGHT + showOffset.y,
      );
      return;
    }

    const bones = new Map(rig.bones.map((bone) => [bone.boneId, bone]));
    for (const part of partSprites) {
      const bone = bones.get(part.boneId);
      const pose = poses.get(part.boneId);
      if (bone === undefined || pose === undefined) continue;
      const sourcePivotX = (rig.sourceRegion.x + bone.pivotX * rig.sourceRegion.width) * sourceSize.width;
      const sourcePivotY = (rig.sourceRegion.y + bone.pivotY * rig.sourceRegion.height) * sourceSize.height;
      const world = composeBoneTransform(bone, pose, rig, bones, poses, sourceSize, artworkFit);
      const role = packageValue?.parts.find((candidate) => candidate.partId === part.partId)?.role ?? '';
      const showMotion = fullRigShowMotion(role, showBeat);
      const rootOffset = bone.boneId === 'root' ? fullRigRootOffset(showBeat) : {x: 0, y: 0};
      part.sprite.position.set(world.x + rootOffset.x, world.y + rootOffset.y);
      part.sprite.rotation = (world.rotationDegrees + showMotion.rotationDegrees) * Math.PI / 180;
      part.sprite.scale.set(
        artworkFit.scale * world.scaleX,
        artworkFit.scale * world.scaleY,
      );
      // Keep this assertion close to the transform: all sprite pivots are source-image coords,
      // so rotation only changes the isolated part around its semantic joint.
      part.sprite.pivot.set(sourcePivotX, sourcePivotY);
    }
  };

  const startTicker = (): void => {
    if (ticker !== null) return;
    ticker = deform;
    options.app.ticker.add(ticker);
  };

  const clearVisuals = (): void => {
    timeline?.kill();
    timeline = null;
    stopTicker();
    scene.removeChildren().forEach((child) => child.destroy());
    for (const texture of ownedTextures) texture.destroy(true);
    ownedTextures = [];
    cutoutSprite = null;
    cutoutPivot = {x: 0, y: 0};
    artworkFit = {scale: 1, x: 0, y: 0};
    sourceSize = {width: STAGE_WIDTH, height: STAGE_HEIGHT};
    partSprites = [];
    activeRig = null;
    packageValue = null;
    plan = null;
    poses.clear();
    showBeat = null;
    state = 'READY';
  };

  const buildTimeline = (animationPlan: VisualAnimationPlanV2): gsap.core.Timeline => {
    const nextTimeline = gsap.timeline({
      paused: true,
      onUpdate: publish,
      onComplete: () => {
        // Every semantic track returns to neutral before the final still hold. Do not start an
        // infinite idle loop here: the completed frame must remain exactly still.
        state = 'COMPLETED';
        deform();
        stopTicker();
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
    // This no-op is the authored final rest: semantic motion stops early, and playback holds
    // the neutral pose until the full 20-second experience ends.
    nextTimeline.set({}, {}, animationPlan.durationSeconds);
    return nextTimeline;
  };

  return {
    load(packageInput, planInput, sourceCanvas, maskCanvas, partMaskCanvases = new Map()): void {
      clearVisuals();
      try {
        const parsedPackage = RiggedArtworkPackageV1Schema.parse(packageInput);
        const parsedPlan = VisualAnimationPlanV2Schema.parse(planInput);
        if (parsedPackage.packageId !== parsedPlan.packageId || parsedPackage.sessionId !== parsedPlan.sessionId) {
          throw new Error('Rig package and animation plan identity drift.');
        }
        if (parsedPackage.rig == null || !parsedPackage.validation.valid) {
          throw new Error('Rig package is not eligible for V2 playback.');
        }
        if (sourceCanvas === undefined || maskCanvas === undefined) {
          throw new Error('SUBJECT_MASK_UNAVAILABLE');
        }
        requireVerifiedCutoutMask(parsedPackage.tier, true);
        const sourceContext = sourceCanvas.getContext('2d', {willReadFrequently: true});
        const maskContext = maskCanvas.getContext('2d', {willReadFrequently: true});
        if (sourceContext === null || maskContext === null) throw new Error('MASK_CANVAS_UNAVAILABLE');
        if (sourceCanvas.width !== maskCanvas.width || sourceCanvas.height !== maskCanvas.height) {
          throw new Error('MASK_DIMENSIONS_MISMATCH');
        }
        const sourcePixels = sourceContext.getImageData(0, 0, sourceCanvas.width, sourceCanvas.height).data;
        const maskPixels = maskContext.getImageData(0, 0, maskCanvas.width, maskCanvas.height).data;
        const layers = createSubjectCutoutLayers(sourcePixels, maskPixels, sourceCanvas.width, sourceCanvas.height);
        const packageRegion = regionFromMask(sourceCanvas, maskCanvas);
        if (!regionMatches(packageRegion, layers.sourceRegion)) throw new Error('MASK_REGION_MISMATCH');
        const rig: RigDefinitionV1 = {...parsedPackage.rig, sourceRegion: layers.sourceRegion};
        activeRig = rig;
        packageValue = parsedPackage;
        plan = parsedPlan;
        options.app.renderer.resize(STAGE_WIDTH, STAGE_HEIGHT);
        sourceSize = {width: sourceCanvas.width, height: sourceCanvas.height};
        artworkFit = fitCanvasToStage(sourceCanvas.width, sourceCanvas.height, STAGE_WIDTH, STAGE_HEIGHT);

        const backgroundCanvas = canvasFromPixels(sourceCanvas.width, sourceCanvas.height, layers.backgroundPixels);
        const background = addCanvasSprite(backgroundCanvas, ownedTextures, artworkFit);
        background.zIndex = 0;
        scene.addChild(background);

        if (parsedPackage.tier === 'CUTOUT_MICRO_MOTION') {
          const cutoutCanvas = canvasFromPixels(sourceCanvas.width, sourceCanvas.height, layers.subjectPixels);
          cutoutSprite = addCanvasSprite(cutoutCanvas, ownedTextures, artworkFit);
          cutoutSprite.anchor.set(
            (layers.sourceRegion.x + layers.sourceRegion.width / 2),
            (layers.sourceRegion.y + layers.sourceRegion.height / 2),
          );
          cutoutPivot = {
            x: artworkFit.x + (layers.sourceRegion.x + layers.sourceRegion.width / 2) * sourceSize.width * artworkFit.scale,
            y: artworkFit.y + (layers.sourceRegion.y + layers.sourceRegion.height / 2) * sourceSize.height * artworkFit.scale,
          };
          cutoutSprite.position.set(cutoutPivot.x, cutoutPivot.y);
          cutoutSprite.zIndex = 10;
          scene.addChild(cutoutSprite);
        } else if (parsedPackage.tier === 'FULL_AUTO_RIG') {
          if (parsedPackage.parts.length < 2 || partMaskCanvases.size !== parsedPackage.parts.length) {
            throw new Error('PART_MASKS_REQUIRED');
          }
          validatePartMasks(parsedPackage, maskPixels, partMaskCanvases, sourceCanvas.width, sourceCanvas.height);
          const orderedParts = [...parsedPackage.parts].sort((left, right) => {
            if (left.boneId === 'root') return 1;
            if (right.boneId === 'root') return -1;
            return 0;
          });
          for (const [index, part] of orderedParts.entries()) {
            const partMask = partMaskCanvases.get(part.partId);
            if (partMask === undefined) throw new Error('PART_MASK_HANDOFF_INVALID');
            const partContext = partMask.getContext('2d', {willReadFrequently: true});
            if (partContext === null) throw new Error('PART_MASK_CANVAS_UNAVAILABLE');
            const partPixels = partContext.getImageData(0, 0, partMask.width, partMask.height).data;
            const partCanvas = canvasFromPixels(
              sourceCanvas.width,
              sourceCanvas.height,
              applyMask(sourcePixels, partPixels, sourceCanvas.width, sourceCanvas.height),
            );
            const sprite = addCanvasSprite(partCanvas, ownedTextures, artworkFit);
            sprite.zIndex = 10 + index;
            scene.addChild(sprite);
            partSprites.push({partId: part.partId, boneId: part.boneId, sprite});
          }
        } else {
          throw new Error('RIG_TIER_NOT_RENDERABLE');
        }

        poses = new Map(rig.bones.map((bone) => [bone.boneId, neutralPose()]));
        timeline = buildTimeline(parsedPlan);
        timeline.pause(0);
        deform();
        state = 'READY';
        publish();
      } catch (error) {
        clearVisuals();
        throw error;
      }
    },

    play(): void {
      if (packageValue?.rig == null || plan === null || timeline === null) {
        throw new Error('Load a valid rig before playback.');
      }
      if (state === 'COMPLETED' || timeline.time() >= timeline.duration()) timeline.pause(0);
      startTicker();
      state = 'PLAYING';
      timeline.play();
      publish();
    },

    pause(): void {
      if (timeline === null) return;
      timeline.pause();
      stopTicker();
      deform();
      state = 'PAUSED';
      publish();
    },

    replay(): void {
      if (timeline === null) throw new Error('Play the rig before replay.');
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

    setShowBeat(action, progress): void {
      showBeat = action === null
        ? null
        : {action, progress: Math.min(1, Math.max(0, progress))};
      deform();
    },

    getPlaybackState() {
      return {positionSeconds: timeline?.time() ?? 0, durationSeconds: timeline?.duration() ?? 0, state};
    },

    destroy(): void {
      clearVisuals();
      scene.destroy({children: true});
      poses.clear();
    },
  };
}

function composeBoneTransform(
  targetBone: RigDefinitionV1['bones'][number],
  targetPose: MutablePose,
  rig: RigDefinitionV1,
  bones: ReadonlyMap<string, RigDefinitionV1['bones'][number]>,
  poses: ReadonlyMap<string, MutablePose>,
  sourceSize: {width: number; height: number},
  artworkFit: CanvasFit,
): {x: number; y: number; rotationDegrees: number; scaleX: number; scaleY: number} {
  const chain: RigDefinitionV1['bones'][number][] = [];
  let current: RigDefinitionV1['bones'][number] | undefined = targetBone;
  while (current !== undefined) {
    chain.unshift(current);
    current = current.parentId === null ? undefined : bones.get(current.parentId);
  }
  let x = artworkFit.x + (rig.sourceRegion.x + targetBone.pivotX * rig.sourceRegion.width) * sourceSize.width * artworkFit.scale;
  let y = artworkFit.y + (rig.sourceRegion.y + targetBone.pivotY * rig.sourceRegion.height) * sourceSize.height * artworkFit.scale;
  let rotationDegrees = 0;
  let scaleX = 1;
  let scaleY = 1;
  for (const bone of chain) {
    const pose = poses.get(bone.boneId) ?? (bone.boneId === targetBone.boneId ? targetPose : neutralPose());
    const root = bone.boneId === 'root';
    const localScaleX = root ? 1 : pose.scaleX;
    const localScaleY = root ? 1 : pose.scaleY;
    const localRotation = root
      ? 0
      : Math.max(-bone.maxRotationDegrees, Math.min(bone.maxRotationDegrees, pose.rotationDegrees));
    const pivotX = artworkFit.x + (rig.sourceRegion.x + bone.pivotX * rig.sourceRegion.width) * sourceSize.width * artworkFit.scale;
    const pivotY = artworkFit.y + (rig.sourceRegion.y + bone.pivotY * rig.sourceRegion.height) * sourceSize.height * artworkFit.scale;
    const angle = localRotation * Math.PI / 180;
    const dx = (x - pivotX) * localScaleX;
    const dy = (y - pivotY) * localScaleY;
    x = pivotX + dx * Math.cos(angle) - dy * Math.sin(angle) + pose.translateX * STAGE_WIDTH;
    y = pivotY + dx * Math.sin(angle) + dy * Math.cos(angle) + pose.translateY * STAGE_HEIGHT;
    rotationDegrees += localRotation;
    scaleX *= localScaleX;
    scaleY *= localScaleY;
  }
  return {x, y, rotationDegrees, scaleX, scaleY};
}

function addCanvasSprite(canvas: HTMLCanvasElement, ownedTextures: Texture[], fit: CanvasFit): Sprite {
  const texture = Texture.from(canvas);
  ownedTextures.push(texture);
  const sprite = new Sprite(texture);
  sprite.scale.set(fit.scale);
  sprite.position.set(fit.x, fit.y);
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

function applyMask(
  source: Uint8ClampedArray,
  mask: Uint8ClampedArray,
  width: number,
  height: number,
): Uint8ClampedArray {
  if (source.length !== width * height * 4 || mask.length !== source.length) {
    throw new Error('PART_MASK_DIMENSIONS_MISMATCH');
  }
  const output = new Uint8ClampedArray(source);
  for (let offset = 0; offset < output.length; offset += 4) {
    const maskAlpha = Math.round((mask[offset] + mask[offset + 1] + mask[offset + 2]) / 3)
      * mask[offset + 3] / 255;
    output[offset + 3] = Math.round(output[offset + 3] * maskAlpha / 255);
  }
  return output;
}

function validatePartMasks(
  packageValue: RiggedArtworkPackageV1,
  parentMask: Uint8ClampedArray,
  partMasks: ReadonlyMap<string, HTMLCanvasElement>,
  width: number,
  height: number,
): void {
  const ids = new Set(packageValue.parts.map((part) => part.partId));
  if (ids.size !== packageValue.parts.length || ids.size !== partMasks.size) {
    throw new Error('PART_MASK_HANDOFF_INVALID');
  }
  const parent = new Uint8Array(width * height);
  const combined = new Uint8Array(width * height);
  let parentCount = 0;
  for (let index = 0; index < parent.length; index += 1) {
    const offset = index * 4;
    parent[index] = Math.round((parentMask[offset] + parentMask[offset + 1] + parentMask[offset + 2]) / 3)
      * parentMask[offset + 3] / 255 >= 128 ? 1 : 0;
    parentCount += parent[index];
  }
  if (parentCount === 0) throw new Error('MASK_AREA_INVALID');
  let unionCount = 0;
  for (const part of packageValue.parts) {
    const canvas = partMasks.get(part.partId);
    if (canvas === undefined || canvas.width !== width || canvas.height !== height) {
      throw new Error('PART_MASK_DIMENSIONS_MISMATCH');
    }
    const context = canvas.getContext('2d', {willReadFrequently: true});
    if (context === null) throw new Error('PART_MASK_CANVAS_UNAVAILABLE');
    const pixels = context.getImageData(0, 0, width, height).data;
    let partCount = 0;
    let outsideCount = 0;
    let overlapCount = 0;
    for (let index = 0; index < parent.length; index += 1) {
      const offset = index * 4;
      const value = Math.round((pixels[offset] + pixels[offset + 1] + pixels[offset + 2]) / 3)
        * pixels[offset + 3] / 255 >= 128 ? 1 : 0;
      if (value === 0) continue;
      partCount += 1;
      if (parent[index] === 0) outsideCount += 1;
      if (combined[index] === 1) overlapCount += 1;
      else {
        combined[index] = 1;
        unionCount += 1;
      }
    }
    if (
      partCount < Math.max(12, parentCount * 0.025)
      || partCount > parentCount * 0.75
      || outsideCount / partCount > 0.08
      || overlapCount / partCount > 0.08
    ) throw new Error('PART_MASK_QUALITY_INVALID');
  }
  if (unionCount / parentCount < 0.85) throw new Error('PART_MASK_COVERAGE_INVALID');
}

function regionFromMask(source: HTMLCanvasElement, mask: HTMLCanvasElement): NormalizedRegion {
  if (source.width !== mask.width || source.height !== mask.height) throw new Error('MASK_DIMENSIONS_MISMATCH');
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

function regionMatches(expected: NormalizedRegion, actual: NormalizedRegion): boolean {
  const tolerance = 0.04;
  return actual.x >= expected.x - tolerance
    && actual.y >= expected.y - tolerance
    && actual.x + actual.width <= expected.x + expected.width + tolerance
    && actual.y + actual.height <= expected.y + expected.height + tolerance;
}

function neutralPose(): MutablePose {
  return {rotationDegrees: 0, translateX: 0, translateY: 0, scaleX: 1, scaleY: 1};
}

function cutoutShowOffset(
  beat: {action: AutoRigShowAction; progress: number} | null,
): {x: number; y: number} {
  if (beat === null) return {x: 0, y: 0};
  const wave = Math.sin(beat.progress * Math.PI * 2);
  switch (beat.action) {
    case 'APPROACH': return {x: 8 * beat.progress, y: -Math.sin(beat.progress * Math.PI) * 2};
    case 'NOTICE': return {x: 0, y: -Math.sin(beat.progress * Math.PI) * 2};
    case 'INTERACT': return {x: 0, y: -wave * 3};
    default: return {x: 0, y: 0};
  }
}

function fullRigRootOffset(
  beat: {action: AutoRigShowAction; progress: number} | null,
): {x: number; y: number} {
  if (beat === null) return {x: 0, y: 0};
  switch (beat.action) {
    case 'APPROACH': return {x: 7 * beat.progress, y: 0};
    case 'NOTICE': return {x: 0, y: -Math.sin(beat.progress * Math.PI) * 2};
    case 'INTERACT': return {x: 0, y: -Math.sin(beat.progress * Math.PI * 2) * 2};
    default: return {x: 0, y: 0};
  }
}

function fullRigShowMotion(
  rawRole: string,
  beat: {action: AutoRigShowAction; progress: number} | null,
): {rotationDegrees: number} {
  if (beat === null) return {rotationDegrees: 0};
  const role = rawRole.toLowerCase().replaceAll('_', '-');
  const wave = Math.sin(beat.progress * Math.PI * 4);
  if (beat.action === 'WALK_STEP' && role.includes('leg')) {
    const side = role.includes('left') || role.includes('fore') ? 1 : -1;
    return {rotationDegrees: wave * 8 * side};
  }
  if (beat.action === 'FLAP' && role.includes('wing')) return {rotationDegrees: wave * 9};
  if (beat.action === 'GLIDE' && role.includes('wing')) {
    return {rotationDegrees: Math.sin(beat.progress * Math.PI) * 2};
  }
  if (beat.action === 'SWIM' && (role.includes('tail') || role.includes('fin'))) {
    return {rotationDegrees: wave * 7};
  }
  if (beat.action === 'SLITHER' && (role.includes('body') || role.includes('tail'))) {
    return {rotationDegrees: wave * 4};
  }
  if (beat.action === 'ROLL' && role.includes('wheel')) {
    return {rotationDegrees: beat.progress * 18};
  }
  return {rotationDegrees: 0};
}
