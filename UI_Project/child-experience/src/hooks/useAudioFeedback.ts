import { useCallback } from 'react'

export function useAudioFeedback() {
  const playChime = useCallback((_type: 'click' | 'success' | 'alert') => {
    // Audio trigger stub for tactile child interface
  }, [])

  return { playChime }
}
