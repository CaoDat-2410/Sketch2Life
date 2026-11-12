export interface StoryStep {
  stepNumber: number
  title: string
  description: string
  illustrationKey: string
}

export interface BotanicalLesson {
  id: string
  topic: string
  steps: StoryStep[]
}
