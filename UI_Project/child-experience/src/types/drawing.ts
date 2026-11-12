export interface Point {
  x: number
  y: number
}

export interface Stroke {
  points: Point[]
  color: string
  size: number
}

export type Tool = 'pen' | 'eraser'

export interface CanvasDimensions {
  width: number
  height: number
}
