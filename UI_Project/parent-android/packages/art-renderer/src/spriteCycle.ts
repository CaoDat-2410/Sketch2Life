import type {PixiSpriteCycleReadV1} from './contractsPixiShow';

/** Return a deterministic frame index from the master show clock, or null outside the beat. */
export function getSpriteCycleFrameIndex(
  cycle: Pick<PixiSpriteCycleReadV1, 'playbackKind' | 'loopMode' | 'frameRate' | 'startSeconds' | 'endSeconds' | 'frameReads'>,
  positionSeconds: number,
): number | null {
  if (!Number.isFinite(positionSeconds) || positionSeconds < cycle.startSeconds || positionSeconds >= cycle.endSeconds) {
    return null;
  }
  if (cycle.playbackKind === 'TRANSFORM_DRIVEN' || cycle.frameReads.length === 1) return 0;
  const rawIndex = Math.floor((positionSeconds - cycle.startSeconds) * cycle.frameRate);
  if (cycle.loopMode === 'LOOP') return rawIndex % cycle.frameReads.length;
  return Math.min(cycle.frameReads.length - 1, rawIndex);
}

/** A tiny bounded slide path for the explicitly single-frame slider class. */
export function getSpriteCycleTransform(
  cycle: Pick<PixiSpriteCycleReadV1, 'playbackKind' | 'behaviorClassId' | 'startSeconds' | 'endSeconds'>,
  positionSeconds: number,
): {offsetX: number; offsetY: number} {
  if (
    cycle.playbackKind !== 'TRANSFORM_DRIVEN'
    || cycle.behaviorClassId !== 'slider'
    || !Number.isFinite(positionSeconds)
    || positionSeconds < cycle.startSeconds
    || positionSeconds >= cycle.endSeconds
  ) return {offsetX: 0, offsetY: 0};
  const progress = (positionSeconds - cycle.startSeconds) / (cycle.endSeconds - cycle.startSeconds);
  return {offsetX: Math.sin(progress * Math.PI * 2) * 24, offsetY: 0};
}
