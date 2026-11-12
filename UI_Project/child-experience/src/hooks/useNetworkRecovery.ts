import { useState } from 'react'

export function useNetworkRecovery() {
  const [isOnline, setIsOnline] = useState(true)

  const triggerDisconnect = () => setIsOnline(false)
  const triggerReconnect = () => setIsOnline(true)

  return { isOnline, triggerDisconnect, triggerReconnect }
}
