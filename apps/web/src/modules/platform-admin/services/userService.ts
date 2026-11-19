import { backendApi, createIdempotencyKey } from '../../../shared/api/backendApi'

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
    cursor?: string
  } = {}) => backendApi.listPlatformAccounts(filters),
  createAccount: (payload: {
    email: string
    display_name: string
    role: AccountRole
    organization_id?: string
  }, idempotencyKey: string) => backendApi.createPlatformAccount(payload, idempotencyKey),
  updateAccount: (
    accountId: string,
    payload: { role?: AccountRole; state?: AccountState; organization_id?: string },
    idempotencyKey: string,
  ) => backendApi.updatePlatformAccount(accountId, payload, idempotencyKey),
}

// FEAT-066 C5 (SRS 21.1, 21.4): one key per exact command, reused only for a retry of that command.
export function keyForSignature(store: Map<string, string>, signature: string): string {
  let key = store.get(signature)
  if (!key) {
    key = createIdempotencyKey()
    store.set(signature, key)
  }
  return key
}
