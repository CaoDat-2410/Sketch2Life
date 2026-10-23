import { useState } from 'react'

export function useEmotionFeedback() {
  const [emotion, setEmotion] = useState<string>('Vui vẻ')
  const [isSubmitted, setIsSubmitted] = useState(false)

  const submitEmotion = (choice: string) => {
    setEmotion(choice)
    setIsSubmitted(true)
  }

  return { emotion, isSubmitted, submitEmotion }
}
