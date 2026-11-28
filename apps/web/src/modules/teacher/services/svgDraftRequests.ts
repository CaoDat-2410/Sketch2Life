// The slide SVG draft takes minutes (the worker may start cold). The pending call, its idempotency key and its answer
// live here, outside the screen: leaving the slides page loses nothing, a second call is not sent while one is open
// (the server has no in-progress claim, so a repeat would draw a second time), and a retry of the same request reuses
// the key so a drawing the server already finished is returned instead of redrawn. Memory only; cleared on sign-out.
import { useSyncExternalStore } from 'react'
import { createIdempotencyKey, BackendApiError } from '../../../shared/api/backendApi'
import type { PresentationSvgDraft } from '../../../shared/api/teacherPresentationApi'
import { authService } from '../../school-manager/be1/services/authService'
import { beginAiTask, clearSvgTaskStatuses, finishAiTask, svgTaskStatusKey } from './aiTaskStatus'

/** The longest the server waits for the worker. */
const SERVER_WAIT_MS = 900_000
/** A connection lost after this long may have left the server still drawing. */
const LOST_AFTER_MS = 60_000

export type SvgDraftRequest = Readonly<{
  signature: string
  startedAt: number
} & (
  | { status: 'pending' }
  | { status: 'done'; draft: PresentationSvgDraft }
  | { status: 'failed'; cause: unknown; blockedUntil: number | null }
)>

const requests = new Map<string, SvgDraftRequest>()
const keys = new Map<string, string>()
const cooldowns = new Map<string, number>()
const listeners = new Set<() => void>()
let generation = 0
let owner: string | null | undefined
let watching = false

const emit = () => listeners.forEach((listener) => listener())

export function clearSvgDraftRequests() {
  requests.clear()
  keys.clear()
  cooldowns.clear()
  generation += 1
  clearSvgTaskStatuses()
  emit()
}

/** Forget the answer once the Teacher has decided on the draft or the page has shown a failure. */
export function dismissSvgDraftRequest(occurrenceId: string) {
  const request = requests.get(occurrenceId)
  if (request?.status === 'pending') return
  if (request?.status === 'failed' && request.blockedUntil !== null && Date.now() < request.blockedUntil) return
  requests.delete(occurrenceId)
  emit()
}

function watchAccount() {
  if (watching) return
  watching = true
  authService.observe((user) => {
    const next = user?.uid ?? null
    if (owner !== undefined && owner !== next) clearSvgDraftRequests()
    owner = next
  })
}

export function startSvgDraftRequest(occurrenceId: string, signature: string, send: (key: string) => Promise<PresentationSvgDraft>) {
  watchAccount()
  const open = requests.get(occurrenceId)
  if (open?.status === 'pending') return
  if (open?.status === 'failed' && open.blockedUntil !== null && Date.now() < open.blockedUntil) return
  const cooldownUntil = cooldowns.get(occurrenceId)
  if (cooldownUntil !== undefined && Date.now() < cooldownUntil) return
  cooldowns.delete(occurrenceId)
  const key = keys.get(signature) ?? createIdempotencyKey()
  keys.set(signature, key)
  const startedAt = Date.now()
  const started = generation
  const taskKey = svgTaskStatusKey(occurrenceId)
  const taskRunId = beginAiTask(taskKey)
  requests.set(occurrenceId, { signature, startedAt, status: 'pending' })
  emit()
  void send(key).then(
    (draft) => {
      if (started !== generation) return
      keys.delete(signature)
      requests.set(occurrenceId, { signature, startedAt, status: 'done', draft })
      finishAiTask(taskKey, taskRunId, 'done')
      emit()
    },
    (cause: unknown) => {
      if (started !== generation) return
      const status = cause instanceof BackendApiError ? cause.status : 0
      // A refusal (4xx) ends this request. A server or network failure keeps the key for the retry.
      if (status >= 400 && status < 500) keys.delete(signature)
      const failedAt = Date.now()
      const lost = status === 0 && failedAt - startedAt >= LOST_AFTER_MS
      if (status === 429 && cause instanceof BackendApiError) {
        const retry = (cause as BackendApiError & { retryAfterSeconds?: number }).retryAfterSeconds ?? 3600
        const until = failedAt + retry * 1000
        if (until > failedAt) cooldowns.set(occurrenceId, until)
      }
      requests.set(occurrenceId, { signature, startedAt, status: 'failed', cause, blockedUntil: lost ? startedAt + SERVER_WAIT_MS : null })
      finishAiTask(taskKey, taskRunId, 'failed')
      emit()
    },
  )
}

const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

export function useSvgDraftRequest(occurrenceId: string): SvgDraftRequest | undefined {
  watchAccount()
  return useSyncExternalStore(subscribe, () => requests.get(occurrenceId))
}

export function useSvgDraftCooldownUntil(occurrenceId: string): number | null {
  watchAccount()
  return useSyncExternalStore(subscribe, () => {
    const until = cooldowns.get(occurrenceId)
    return until ?? null
  })
}

export function expireSvgDraftCooldown(occurrenceId: string, expectedUntil: number) {
  if (cooldowns.get(occurrenceId) !== expectedUntil || Date.now() < expectedUntil) return
  cooldowns.delete(occurrenceId)
  emit()
}
