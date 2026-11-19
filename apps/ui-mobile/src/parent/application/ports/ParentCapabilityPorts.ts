export type ParentCapabilityId =
  | 'identity'
  | 'profiles'
  | 'consent'
  | 'profile-sharing'
  | 'run-history'
  | 'lesson-history'
  | 'notifications'
  | 'lessons'
  | 'story-creation'
  | 'job-status'
  | 'video'
  | 'quota';

export type ParentCapabilityUnavailableReason =
  | 'capability-not-configured'
  | 'route-not-in-be-handoff';

export type ParentCapabilityState =
  | { capability: ParentCapabilityId; state: 'available' }
  | {
      capability: ParentCapabilityId;
      state: 'unavailable';
      reason: ParentCapabilityUnavailableReason;
    };

export type ParentOperationState<T> =
  | { state: 'idle' }
  | { state: 'pending' }
  | { state: 'reconciling' }
  | { state: 'confirmed'; value: T }
  | { state: 'unavailable'; reason: ParentCapabilityUnavailableReason }
  | { state: 'failed'; retry: 'same-job-check-required' | 'user-action-required' | 'not-retryable' };

export type ParentJobStageState =
  | { state: 'idle'; stage: 'idle' }
  | { state: 'pending'; stage: 'queued' | 'processing' }
  | { state: 'reconciling'; stage: 'reconciling' }
  | { state: 'confirmed'; stage: 'completed' }
  | { state: 'failed'; stage: 'failed' }
  | { state: 'unavailable'; stage: 'unavailable' };

export interface ParentCapabilityPort {
  capabilityState(capability: ParentCapabilityId): ParentCapabilityState;
}

export interface ParentOperationPort {
  operationState<T>(): ParentOperationState<T>;
}

export function createUnavailableCapabilityState(
  capability: ParentCapabilityId,
  reason: ParentCapabilityUnavailableReason,
): ParentCapabilityState {
  return { capability, state: 'unavailable', reason };
}

export function createUnavailableOperationState<T>(
  reason: ParentCapabilityUnavailableReason,
): ParentOperationState<T> {
  return { state: 'unavailable', reason };
}
