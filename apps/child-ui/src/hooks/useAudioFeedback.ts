import { useCallback } from 'react'

export function useAudioFeedback() {
  const playChime = useCallback((type: 'click' | 'success' | 'alert') => {
    // Audio trigger stub for tactile child interface
  }, [])

  return { playChime }
}
