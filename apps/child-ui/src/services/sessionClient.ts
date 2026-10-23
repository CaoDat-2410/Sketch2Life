import { childApiFetch } from './apiClient'

export interface SessionVerification {
  valid: boolean
  classroomName: string
  teacherName: string
}

export async function verifySessionPin(pin: string): Promise<SessionVerification> {
  return {
    valid: pin.length === 4,
    classroomName: 'Lớp Chồi Xanh Montessori',
    teacherName: 'Cô Mai',
  }
}
