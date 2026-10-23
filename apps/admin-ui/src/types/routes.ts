export const ADMIN_ROUTES = {
  LOGIN: '/login',
  DASHBOARD: '/',
  USERS: '/users',
  CLASSES: '/classes',
  CONTENT: '/content',
  AI_POLICY: '/ai-policy',
  DATA_REQUESTS: '/data-requests',
  DELETE_REQUEST_DETAIL: '/data-requests/:id',
  LOGS: '/logs',
  MONITORING: '/monitoring',
  REPORTS: '/reports',
  SETTINGS: '/settings',
} as const;

export type AdminRoute = typeof ADMIN_ROUTES[keyof typeof ADMIN_ROUTES];
