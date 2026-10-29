import { useState, useCallback } from 'react'

export interface Point { x: number; y: number }
export interface Stroke { points: Point[]; color: string; size: number }

export function useDrawingCanvas() {
  const [strokes, setStrokes] = useState<Stroke[]>([])
  const [redoStack, setRedoStack] = useState<Stroke[]>([])

  const addStroke = useCallback((stroke: Stroke) => {
    setStrokes((prev) => [...prev, stroke])
    setRedoStack([])
  }, [])

  const undo = useCallback(() => {
    if (strokes.length === 0) return
    const last = strokes[strokes.length - 1]
    setStrokes((prev) => prev.slice(0, -1))
    setRedoStack((prev) => [...prev, last])
  }, [strokes])

  const redo = useCallback(() => {
    if (redoStack.length === 0) return
    const next = redoStack[redoStack.length - 1]
    setRedoStack((prev) => prev.slice(0, -1))
    setStrokes((prev) => [...prev, next])
  }, [redoStack])

  const clear = useCallback(() => {
    setStrokes([])
    setRedoStack([])
  }, [])

  return { strokes, addStroke, undo, redo, clear, canUndo: strokes.length > 0, canRedo: redoStack.length > 0 }
}
