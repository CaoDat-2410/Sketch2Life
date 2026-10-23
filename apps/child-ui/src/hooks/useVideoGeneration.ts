import { useState, useEffect } from 'react'

export function useVideoGeneration() {
  const [progress, setProgress] = useState(10)
  const [isDone, setIsDone] = useState(false)

  useEffect(() => {
    const timer = setInterval(() => {
      setProgress((p) => {
        if (p >= 100) {
          clearInterval(timer)
          setIsDone(true)
          return 100
        }
        return p + 25
      })
    }, 800)
    return () => clearInterval(timer)
  }, [])

  return { progress, isDone }
}
