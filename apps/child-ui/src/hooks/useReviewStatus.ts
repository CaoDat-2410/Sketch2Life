import { useState } from 'react'

export type GateStatus = 'idle' | 'pending' | 'approved' | 'needs_revision'

export function useReviewStatus() {
  const [status, setStatus] = useState<GateStatus>('idle')
  const [feedback, setFeedback] = useState<string | null>(null)

  const submitForReview = () => {
    setStatus('pending')
    setTimeout(() => {
      setStatus('approved')
      setFeedback('Bức tranh rất đẹp và sinh động!')
    }, 2000)
  }

  return { status, feedback, submitForReview }
}
