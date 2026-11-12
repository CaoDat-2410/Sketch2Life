export interface KidProfile {
  name: 'Mây' | 'Lá'
  avatarKey: string
  status: 'active' | 'waiting' | 'offline'
}

export interface SessionInfo {
  code: string
  classroomName: string
  currentScreen: string
}
