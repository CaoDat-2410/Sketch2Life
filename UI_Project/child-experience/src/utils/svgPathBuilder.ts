import { Point } from '../types/drawing'

export function pointsToSvgPath(points: Point[]): string {
  if (points.length === 0) return ''
  const [first, ...rest] = points
  let d = `M ${first.x} ${first.y}`
  for (const p of rest) {
    d += ` L ${p.x} ${p.y}`
  }
  return d
}
