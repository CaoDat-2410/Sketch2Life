export const TEACHER_ROUTES = {
  LOGIN: '/login',
  HOME: '/',
  SESSION_SETUP: '/sessions/setup',
  SESSION_LOBBY: '/sessions/lobby',
  SESSION_ORCHESTRATE: '/sessions/live',
  GROUP_WORKSPACE: '/workspace/group',
  AI_SUGGESTION_REVIEW: '/review/ai',
  VIDEO_KNOWLEDGE: '/video/knowledge',
  OFFLINE_ACTIVITIES: '/activities/offline',
  CLASSES_PROFILES: '/classes',
  CLASS_GALLERY: '/gallery',
  LEARNING_PORTFOLIO: '/portfolio',
  OBSERVATION_FEEDBACK: '/observations',
  CONTENT_AUTHORING: '/authoring',
  TEMPLATES_AUTOMATION: '/templates',
} as const;

export type TeacherRoute = typeof TEACHER_ROUTES[keyof typeof TEACHER_ROUTES];
