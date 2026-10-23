export function computeTabletScale(width: number, height: number): number {
  const baseWidth = 1024
  return Math.min(width / baseWidth, 1.2)
}
