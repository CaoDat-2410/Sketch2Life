import { useEffect, useState } from 'react'
import type { User } from 'firebase/auth'
import { authService } from '../services/authService';

export function useAuth() {
  const [user, setUser] = useState<User | null>(() => authService.getCurrentUser())
  useEffect(() => authService.observe(setUser), [])
  return { user, isAuthenticated: !!user };
}
