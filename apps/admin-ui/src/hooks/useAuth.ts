import { useState } from 'react';
import { authService } from '../services/authService';

export function useAuth() {
  const [user, setUser] = useState(() => authService.getCurrentUser());
  return { user, isAuthenticated: !!user };
}
