export type EmotionType = 'Vui vẻ' | 'Hào hứng' | 'Tự hào' | 'Bình yên'

export interface FeelingSubmission {
  childName: string
  emotion: EmotionType
  timestamp: number
}
