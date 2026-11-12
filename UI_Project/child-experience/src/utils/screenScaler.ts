export function computeTabletScale(width: number, _height: number): number {
  const baseWidth = 1024
  return Math.min(width / baseWidth, 1.2)
}
