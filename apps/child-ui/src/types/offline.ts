export interface OfflineActivity {
  id: string
  title: string
  durationMinutes: number
  materialList: string[]
  montessoriArea: 'botanical' | 'sensory' | 'fine_motor'
}
