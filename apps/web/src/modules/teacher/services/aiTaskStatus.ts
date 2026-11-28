import { useSyncExternalStore } from 'react'

export type AiTaskStatus = 'pending' | 'done' | 'failed'
declare const svgTaskKeyBrand: unique symbol
export type SvgTaskKey = string & { readonly [svgTaskKeyBrand]: true }
export type AiTaskKey = 'suggestion' | SvgTaskKey
export type AiTaskMark = Readonly<{ status: AiTaskStatus; runId: number }>

export const AI_TASK_SEEN_DELAY_MS = 4_000

const tasks = new Map<AiTaskKey, AiTaskMark>()
const listeners = new Set<() => void>()
let nextRunId = 0

export function svgTaskStatusKey(occurrenceId: string): SvgTaskKey {
  return ('svg:' + occurrenceId) as SvgTaskKey
}

const emit = () => listeners.forEach((listener) => listener())
const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => { listeners.delete(listener) }
}

export function getAiTaskMark(key: AiTaskKey): AiTaskMark | undefined {
  return tasks.get(key)
}

export function getAiTaskAggregateStatus(): AiTaskStatus | undefined {
  let hasDone = false
  let hasFailed = false
  for (const { status } of tasks.values()) {
    if (status === 'pending') return 'pending'
    if (status === 'failed') hasFailed = true
    if (status === 'done') hasDone = true
  }
  if (hasFailed) return 'failed'
  if (hasDone) return 'done'
  return undefined
}

export function useAiTaskMark(key: AiTaskKey): AiTaskMark | undefined {
  return useSyncExternalStore(subscribe, () => getAiTaskMark(key))
}

export function useAiTaskAggregateStatus(): AiTaskStatus | undefined {
  return useSyncExternalStore(subscribe, getAiTaskAggregateStatus)
}

export function beginAiTask(key: AiTaskKey): number {
  const runId = ++nextRunId
  tasks.set(key, { status: 'pending', runId })
  emit()
  return runId
}

export function finishAiTask(key: AiTaskKey, runId: number, status: Exclude<AiTaskStatus, 'pending'>): boolean {
  const current = tasks.get(key)
  if (!current || current.runId !== runId || current.status !== 'pending') return false
  tasks.set(key, { status, runId })
  emit()
  return true
}

export function clearAiTaskStatus(key: AiTaskKey): boolean {
  if (!tasks.delete(key)) return false
  emit()
  return true
}

function clearAiTaskStatusesWhere(matches: (key: AiTaskKey) => boolean) {
  let changed = false
  for (const key of tasks.keys()) {
    if (matches(key)) changed = tasks.delete(key) || changed
  }
  if (changed) emit()
}

export function clearAiWorkflowTaskStatuses() {
  clearAiTaskStatusesWhere((key) => key === 'suggestion')
}

export function clearSvgTaskStatuses() {
  clearAiTaskStatusesWhere((key) => key.startsWith('svg:'))
}

export function clearAiTaskStatusIfCurrent(key: AiTaskKey, runId: number): boolean {
  const current = tasks.get(key)
  if (!current || current.runId !== runId || current.status === 'pending') return false
  tasks.delete(key)
  emit()
  return true
}

export function scheduleAiTaskStatusSeen(key: AiTaskKey, runId: number): () => void {
  const current = tasks.get(key)
  if (!current || current.runId !== runId || current.status === 'pending') return () => undefined
  const timer = globalThis.setTimeout(() => {
    clearAiTaskStatusIfCurrent(key, runId)
  }, AI_TASK_SEEN_DELAY_MS)
  return () => globalThis.clearTimeout(timer)
}
