import { backendApi } from '../../../shared/api/backendApi'

export type AccountRole = 'parent' | 'teacher' | 'school_manager' | 'platform_admin'
export type AccountState = 'active' | 'disabled'

export interface ManagedAccount {
  account_id: string
  email: string | null
  display_name: string | null
  role: AccountRole | null
  state: AccountState
  revision: number
}

export const userService = {
  listUsers: (filters: {
    role?: AccountRole
    state?: AccountState
    search?: string
    limit?: number
    offset?: number
  } = {}) => backendApi.listPlatformAccounts(filters),
  createAccount: (payload: {
    email: string
    display_name: string
    role: AccountRole
    organization_id?: string
  }) => backendApi.createPlatformAccount(payload),
  updateAccount: (
    accountId: string,
    payload: { role?: AccountRole; state?: AccountState; organization_id?: string },
  ) => backendApi.updatePlatformAccount(accountId, payload),
}
