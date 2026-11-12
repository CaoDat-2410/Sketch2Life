export function serializeStrokes(strokes: any[]): string {
  return JSON.stringify(strokes)
}

export function deserializeStrokes(raw: string): any[] {
  try {
    return JSON.parse(raw)
  } catch {
    return []
  }
}
