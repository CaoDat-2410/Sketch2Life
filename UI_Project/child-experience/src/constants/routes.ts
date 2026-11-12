import { Screen } from '../types/screens'

export const SCREEN_SEQUENCE: Record<Screen, Screen> = {
  join: 'lobby',
  lobby: 'draw',
  draw: 'review',
  advanced: 'review',
  ideas: 'draw',
  review: 'group',
  group: 'gallery',
  gallery: 'learn',
  learn: 'video',
  video: 'offline',
  offline: 'feeling',
  feeling: 'join',
  reconnect: 'lobby',
}
