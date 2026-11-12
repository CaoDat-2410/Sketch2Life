import { useState } from 'react'

export function useLessonStory() {
  const [currentStep, setCurrentStep] = useState(1)
  const totalSteps = 3

  const nextStep = () => {
    if (currentStep < totalSteps) setCurrentStep((s) => s + 1)
  }

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep((s) => s - 1)
  }

  return { currentStep, totalSteps, nextStep, prevStep }
}
