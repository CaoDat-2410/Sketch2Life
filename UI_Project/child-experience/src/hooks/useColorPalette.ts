import { useState } from 'react'

export function useColorPalette(initialColor = '#1685F8') {
  const [selectedColor, setSelectedColor] = useState(initialColor)
  const [tool, setTool] = useState<'pen' | 'eraser'>('pen')
  const [brushSize, setBrushSize] = useState(6)

  const selectColor = (c: string) => {
    setSelectedColor(c)
    setTool('pen')
  }

  const activateEraser = () => {
    setTool('eraser')
  }

  return { selectedColor, tool, brushSize, selectColor, activateEraser, setBrushSize }
}
