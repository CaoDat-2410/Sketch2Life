export interface LocalStrokeCache {
  sessionId: string
  childName: string
  strokes: any[]
  timestamp: number
}

export class DrawingStorage {
  private static cache: LocalStrokeCache | null = null

  static save(data: LocalStrokeCache) {
    this.cache = data
  }

  static get(): LocalStrokeCache | null {
    return this.cache
  }
}
