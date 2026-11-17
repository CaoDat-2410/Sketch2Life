export interface CanvasFit {
  readonly scale: number;
  readonly x: number;
  readonly y: number;
}

/** Contain source artwork inside a stage and leave a modest, consistent margin. */
export function fitCanvasToStage(
  sourceWidth: number,
  sourceHeight: number,
  stageWidth: number,
  stageHeight: number,
  padding = 0.88,
): CanvasFit {
  if (
    ![sourceWidth, sourceHeight, stageWidth, stageHeight, padding].every(Number.isFinite)
    || sourceWidth <= 0 || sourceHeight <= 0 || stageWidth <= 0 || stageHeight <= 0
    || padding <= 0 || padding > 1
  ) throw new Error('CANVAS_FIT_DIMENSIONS_INVALID');

  const scale = Math.min(stageWidth / sourceWidth, stageHeight / sourceHeight) * padding;
  return {
    scale,
    x: (stageWidth - sourceWidth * scale) / 2,
    y: (stageHeight - sourceHeight * scale) / 2,
  };
}
