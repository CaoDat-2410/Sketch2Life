export const authService = {
  login: async (credentials: { email: string; pass: string }) => ({ token: 'mock-jwt-token' }),
  logout: async () => {},
  getCurrentUser: () => ({ email: 'admin@sketch2life.internal', role: 'admin' }),
};
