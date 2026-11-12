import { useState, useCallback } from 'react'

export function useChildSession() {
  const [sessionCode, setSessionCode] = useState<string>('')
  const [kidName, setKidName] = useState<'Mây' | 'Lá'>('Mây')
  const [isReady, setIsReady] = useState(false)

  const joinSession = useCallback((code: string, kid: 'Mây' | 'Lá') => {
    setSessionCode(code)
    setKidName(kid)
    setIsReady(false)
  }, [])

  const markReady = useCallback(() => {
    setIsReady(true)
  }, [])

  return { sessionCode, kidName, isReady, joinSession, markReady }
}
