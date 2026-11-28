import { useCallback, useSyncExternalStore, type Dispatch, type SetStateAction } from 'react'
import { configuredOrganizationId } from '../../../shared/api/backendApi'
import { authService } from '../../school-manager/be1/services/authService'
import { clearAiWorkflowTaskStatuses } from './aiTaskStatus'

const STORAGE_KEY_PREFIX = 'sketch2life:teacher-ai-workflow:v1:'
const RELOAD_MESSAGE = 'Trang đã tải lại khi yêu cầu đang xử lý. Không thể tiếp tục kiểm tra yêu cầu đó; hãy chọn “Soạn mới” nếu muốn gửi lại.'
const SAVE_RELOAD_MESSAGE = 'Lượt lưu trước có thể đã hoàn tất. Bản nháp vẫn được giữ; hãy lưu lại để kiểm tra bằng cùng một mã yêu cầu.'
const valuesByScope = new Map<string, Map<string, unknown>>()
const loadedScopes = new Set<string>()
const scopeGenerations = new Map<string, number>()
const listeners = new Set<() => void>()
let generation = 0
let owner: string | null | undefined
let watching = false

const emit = () => listeners.forEach((listener) => listener())

function sessionStorageOrNull(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.sessionStorage
  } catch {
    return null
  }
}

function currentScope(): string {
  const currentUserId = authService.getCurrentUser()?.uid
  if (!currentUserId || owner !== currentUserId) return 'anonymous'
  let organizationId = ''
  try {
    organizationId = configuredOrganizationId()
  } catch {
    // Without an organization, keep state in memory only.
  }
  return `${owner}\u0000${organizationId}`
}

function storageKeyForScope(scope: string): string | null {
  const separator = scope.indexOf('\u0000')
  if (separator < 1) return null
  const userId = scope.slice(0, separator)
  const organizationId = scope.slice(separator + 1)
  if (!organizationId) return null
  return `${STORAGE_KEY_PREFIX}${encodeURIComponent(userId)}:${encodeURIComponent(organizationId)}`
}

function scopeValues(scope: string): Map<string, unknown> {
  let values = valuesByScope.get(scope)
  if (!values) {
    values = new Map<string, unknown>()
    valuesByScope.set(scope, values)
  }
  if (!loadedScopes.has(scope)) {
    loadedScopes.add(scope)
    const storageKey = storageKeyForScope(scope)
    const storage = sessionStorageOrNull()
    if (storageKey && storage) {
      try {
        const stored = storage.getItem(storageKey)
        const parsed: unknown = stored ? JSON.parse(stored) : null
        if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
          const restored = parsed as Record<string, unknown>
          Object.entries(restored).forEach(([key, value]) => values?.set(key, value))
          if (restored.busy === 'suggestion') {
            values.set('busy', 'interrupted')
            values.set('error', RELOAD_MESSAGE)
            persistScope(scope)
          } else if (restored.busy === 'save') {
            values.set('busy', '')
            if (!restored.savedLesson) values.set('error', SAVE_RELOAD_MESSAGE)
            persistScope(scope)
          } else if (restored.busy === 'deck') {
            values.set('busy', '')
            values.delete('deck')
            values.set('error', '')
            values.set('notice', 'Sketch Deck được tạo từ kế hoạch đã duyệt trong buổi dạy.')
            persistScope(scope)
          }
        }
      } catch {
        try {
          storage.removeItem(storageKey)
        } catch {
          // Ignore unavailable browser storage and keep the in-memory draft.
        }
      }
    }
  }
  return values
}

function persistScope(scope: string) {
  const storageKey = storageKeyForScope(scope)
  const storage = sessionStorageOrNull()
  if (!storageKey || !storage) return
  try {
    storage.setItem(storageKey, JSON.stringify(Object.fromEntries(scopeValues(scope))))
  } catch {
    // Keep the live workflow usable when browser storage is unavailable or full.
  }
}

function removeStoredWorkflowDrafts() {
  const storage = sessionStorageOrNull()
  if (!storage) return
  try {
    for (let index = storage.length - 1; index >= 0; index -= 1) {
      const key = storage.key(index)
      if (key?.startsWith(STORAGE_KEY_PREFIX)) storage.removeItem(key)
    }
  } catch {
    // Ignore unavailable browser storage; in-memory state is still cleared.
  }
}

/** Drop every saved workflow draft. Results of requests started before are ignored when they arrive. */
export function clearAiWorkflowSession() {
  removeStoredWorkflowDrafts()
  valuesByScope.clear()
  loadedScopes.clear()
  scopeGenerations.clear()
  generation += 1
  clearAiWorkflowTaskStatuses()
  emit()
}

/** Clear only the active account and organization's draft so the Teacher can start over. */
export function clearAiWorkflowDraft() {
  const scope = currentScope()
  const storageKey = storageKeyForScope(scope)
  const storage = sessionStorageOrNull()
  if (storageKey && storage) {
    try {
      storage.removeItem(storageKey)
    } catch {
      // Ignore unavailable browser storage; in-memory state is still cleared.
    }
  }
  valuesByScope.delete(scope)
  loadedScopes.delete(scope)
  scopeGenerations.set(scope, (scopeGenerations.get(scope) ?? 0) + 1)
  clearAiWorkflowTaskStatuses()
  emit()
}

function watchAccount() {
  if (watching) return
  watching = true
  owner = authService.getCurrentUser()?.uid
  authService.observe((user) => {
    const next = user?.uid ?? null
    if (next === null || (owner !== undefined && owner !== next)) clearAiWorkflowSession()
    owner = next
    emit()
  })
}

const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

/** Like useState, but the value outlives the screen and reloads in this tab for the same account and organization. */
export function useAiWorkflowState<T>(key: string, initial: T): [T, Dispatch<SetStateAction<T>>] {
  watchAccount()
  const scope = useSyncExternalStore(subscribe, currentScope, () => 'anonymous')
  const value = useSyncExternalStore(
    subscribe,
    () => {
      const values = scopeValues(scope)
      if (!values.has(key)) values.set(key, initial)
      return values.get(key) as T
    },
    () => initial,
  )
  const currentGeneration = useSyncExternalStore(subscribe, () => generation, () => generation)
  const currentScopeGeneration = useSyncExternalStore(
    subscribe,
    () => scopeGenerations.get(scope) ?? 0,
    () => scopeGenerations.get(scope) ?? 0,
  )
  const set = useCallback((next: SetStateAction<T>) => {
    // A setter taken before sign-out or "Soạn mới" must not bring the old draft back.
    if (currentGeneration !== generation || currentScopeGeneration !== (scopeGenerations.get(scope) ?? 0)) return
    const values = scopeValues(scope)
    const previous = values.has(key) ? values.get(key) as T : initial
    values.set(key, typeof next === 'function' ? (next as (value: T) => T)(previous) : next)
    persistScope(scope)
    emit()
  }, [currentGeneration, currentScopeGeneration, initial, key, scope])
  return [value, set]
}
