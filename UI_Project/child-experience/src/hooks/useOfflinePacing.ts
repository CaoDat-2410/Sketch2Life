import { useState, useEffect } from 'react'

export function useOfflinePacing(initialSeconds = 600) {
  const [remainingSeconds, setRemainingSeconds] = useState(initialSeconds)
  const [isOver, setIsOver] = useState(false)

  useEffect(() => {
    if (remainingSeconds <= 0) {
      setIsOver(true)
      return
    }
    const interval = setInterval(() => {
      setRemainingSeconds((s) => s - 1)
    }, 1000)
    return () => clearInterval(interval)
  }, [remainingSeconds])

  return { remainingSeconds, isOver }
}
