import { adminApiRequest } from './be1Client'

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

interface AccountPage {
  items: ManagedAccount[]
  total: number
  limit: number
  offset: number
}

export const userService = {
  listUsers: async (filters: {
    role?: AccountRole
    state?: AccountState
    search?: string
    limit?: number
    offset?: number
  } = {}) => {
    const query = new URLSearchParams()
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== '') query.set(key, String(value))
    }
    return adminApiRequest<AccountPage>(`/platform-admin/v1/accounts?${query.toString()}`)
  },
  createAccount: async (payload: {
    email: string
    display_name: string
    role: AccountRole
    organization_id?: string
  }) => adminApiRequest<ManagedAccount>('/platform-admin/v1/accounts', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  updateAccount: async (
    accountId: string,
    payload: { role?: AccountRole; state?: AccountState; organization_id?: string },
  ) => adminApiRequest<ManagedAccount>(`/platform-admin/v1/accounts/${encodeURIComponent(accountId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  }),
}
