export type AdultRole = 'admin' | 'guide' | 'parent';

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: AdultRole;
  status: 'active' | 'suspended' | 'pending';
  createdAt: string;
  lastLoginAt?: string;
}
