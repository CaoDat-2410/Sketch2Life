import { useState } from 'react'

export interface PeerDrawing {
  id: string
  childName: string
  itemType: 'flower' | 'leaf' | 'sun'
  status: 'drafting' | 'completed'
}

export function useGroupGarden() {
  const [peers] = useState<PeerDrawing[]>([
    { id: '1', childName: 'Mây', itemType: 'flower', status: 'completed' },
    { id: '2', childName: 'Lá', itemType: 'leaf', status: 'drafting' },
    { id: '3', childName: 'Nắng', itemType: 'sun', status: 'completed' },
  ])

  return { peers }
}
