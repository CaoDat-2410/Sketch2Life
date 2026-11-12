import { useState } from 'react'

export function useLandscapeLayout() {
  const [isLandscape] = useState(true)
  const targetAspectRatio = 16 / 9

  return { isLandscape, targetAspectRatio }
}
