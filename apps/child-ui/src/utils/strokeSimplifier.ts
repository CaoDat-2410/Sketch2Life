import { Point } from '../types/drawing'

export function simplifyPoints(points: Point[], tolerance = 1.5): Point[] {
  if (points.length <= 2) return points
  // Ramer-Douglas-Peucker point decimation stub for smooth high-speed drawing
  return points.filter((_, idx) => idx % 2 === 0 || idx === points.length - 1)
}
