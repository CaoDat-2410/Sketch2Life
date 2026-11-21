import { useRef, useState } from 'react';
import { parentConfig } from '../../infrastructure/config';
import {
  applyLifecycleProjection,
  mergeRunHistoryPage,
  retainedRunActionKey,
  runActionOutcome,
  runActionSignature,
  type RunHistoryAction,
} from '../../application/parentRunHistory';
import {
  applyNotificationRead,
  mergeNotificationPage,
  notificationActionOutcome,
  notificationActionSignature,
  retainedNotificationActionKey,
} from '../../application/parentNotifications';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { createParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import { safeParentFlowErrorMessage } from './parentFlowV1';
import {
  createUnavailableCapabilityState,
  createUnavailableOperationState,
  type ParentCapabilityId,
  type ParentCapabilityState,
  type ParentCapabilityUnavailableReason,
  type ParentOperationState,
} from '../../application/ports/ParentCapabilityPorts';
import type {
  ParentLessonDelivery,
  ParentNotification,
  ParentProfileShareGrant,
  ParentStoryRunSummary,
  ParentVideoQuota,
} from '../../domain/types';

const unavailableReason: ParentCapabilityUnavailableReason = 'route-not-in-be-handoff';
const unavailableMessage = 'Chức năng này chưa có tuyến dịch vụ được xác nhận. Chưa có thao tác nào được gửi.';

function apiConfigured(capability: ParentCapabilityId): ParentCapabilityState {
  return parentConfig.apiBaseUrl
    ? { capability, state: 'available' }
    : createUnavailableCapabilityState(capability, 'capability-not-configured');
}

// FEAT-081 C3b: run history is available whenever the live API is configured.
const runHistoryCapability: ParentCapabilityState = parentConfig.apiBaseUrl
  ? { capability: 'run-history', state: 'available' }
  : createUnavailableCapabilityState('run-history', 'capability-not-configured');
const notificationCapability = apiConfigured('notifications');
const unavailableNotificationOperation = createUnavailableOperationState<void>(
  notificationCapability.state === 'unavailable' ? notificationCapability.reason : unavailableReason,
);

const platformCapabilities = {
  runs: runHistoryCapability,
  sharing: createUnavailableCapabilityState('profile-sharing', unavailableReason),
  deliveries: createUnavailableCapabilityState('lesson-history', unavailableReason),
  notifications: notificationCapability,
  quota: createUnavailableCapabilityState('quota', unavailableReason),
  // Goal v3 Phase B: the video request, the run detail and the playback routes are live (the main controller owns them).
  jobStatus: apiConfigured('job-status'),
  video: apiConfigured('video'),
};

const unavailableShareOperation: ParentOperationState<void> =
  createUnavailableOperationState<void>(unavailableReason);

const notificationReloadMessage = 'Thông báo này không còn nữa; danh sách đã được tải lại.';

/** A 4xx (other than a timeout or a rate limit) or a body the app refused is final: the next try needs a new key. */
function isDefinitiveNotificationFailure(failure: unknown): boolean {
  if (!(failure instanceof ParentApplicationError)) return false;
  if (failure.code === 'INVALID_API_RESPONSE') return true;
  return failure.status !== undefined && failure.status >= 400 && failure.status < 500
    && failure.status !== 401 && failure.status !== 408 && failure.status !== 429;
}

const runHistoryLoadError = 'Không tải được lịch sử buổi học. Vui lòng thử lại.';
const runActionMessages = {
  reload: 'Buổi học vừa thay đổi; danh sách đã được tải lại.',
  remove: 'Buổi học không còn trong danh sách.',
  error: 'Chưa thực hiện được thao tác. Vui lòng thử lại.',
} as const;

/** Run history is live (FEAT-081 C3b); the other absent platform routes stay local and unavailable. */
export function useParentPlatformController(application: ParentApplicationModule) {
  const [sharesProfileId, setSharesProfileId] = useState('');
  const [deliveriesProfileId, setDeliveriesProfileId] = useState('');
  const [runs, setRuns] = useState<ParentStoryRunSummary[]>([]);
  const [runsCursor, setRunsCursor] = useState<string | null>(null);
  const [runsProfileId, setRunsProfileId] = useState<string | undefined>(undefined);
  const [runsBusy, setRunsBusy] = useState(false);
  const [runsError, setRunsError] = useState('');
  const runActionKeys = useRef(new Map<string, string>());
  const runsRequest = useRef(0);

  async function loadRuns(profileId?: string, cursor: string | null = null): Promise<ParentOperationState<void>> {
    if (runHistoryCapability.state !== 'available') return unavailableShareOperation;
    // A different profile starts a new list (review C3B-R3-03).
    const requestedCursor = profileId === runsProfileId ? cursor : null;
    // Only the newest load may write the list (review C3B-IMPL-R1-03).
    const requestNumber = runsRequest.current + 1;
    runsRequest.current = requestNumber;
    setRunsBusy(true);
    setRunsError('');
    try {
      const page = await application.platform.listRuns(profileId, requestedCursor);
      if (requestNumber !== runsRequest.current) return { state: 'confirmed', value: undefined };
      const merged = mergeRunHistoryPage(requestedCursor === null ? [] : runs, page, requestedCursor);
      setRuns(merged.runs);
      setRunsCursor(merged.nextCursor);
      setRunsProfileId(profileId);
      return { state: 'confirmed', value: undefined };
    } catch {
      if (requestNumber !== runsRequest.current) return { state: 'failed', retry: 'user-action-required' };
      setRunsError(runHistoryLoadError);
      return { state: 'failed', retry: 'user-action-required' };
    } finally {
      setRunsBusy(false);
    }
  }

  async function requestRunLifecycle(runId: string, operation: RunHistoryAction): Promise<ParentOperationState<void>> {
    const run = runs.find((item) => item.run_id === runId);
    if (!run || runHistoryCapability.state !== 'available') return unavailableShareOperation;
    const allowed = operation === 'cancel' ? run.can_cancel : run.can_delete;
    if (!allowed) return { state: 'failed', retry: 'not-retryable' };
    const signature = runActionSignature(operation, run);
    const key = retainedRunActionKey(runActionKeys.current, signature, createParentActionIdentity);
    setRunsBusy(true);
    setRunsError('');
    try {
      const envelope = operation === 'cancel'
        ? await application.platform.cancelRunV1(run.run_id, run.revision, key)
        : await application.platform.deleteRunV1(run.run_id, key);
      runActionKeys.current.delete(signature);
      setRuns((current) => applyLifecycleProjection(current, envelope));
      return { state: 'confirmed', value: undefined };
    } catch (failure) {
      const outcome = failure instanceof ParentApplicationError
        ? runActionOutcome(failure.code, failure.status)
        : 'error';
      if (outcome === 'remove') setRuns((current) => current.filter((item) => item.run_id !== runId));
      if (outcome === 'reload') {
        runActionKeys.current.delete(signature);
        await loadRuns(runsProfileId, null);
      }
      // Set after the reload, which clears the error first (review C3B-IMPL-R1-01).
      setRunsError(runActionMessages[outcome]);
      return { state: 'failed', retry: outcome === 'error' ? 'user-action-required' : 'not-retryable' };
    } finally {
      setRunsBusy(false);
    }
  }

  async function loadShares(profileId: string): Promise<ParentOperationState<void>> {
    setSharesProfileId(profileId);
    return unavailableShareOperation;
  }

  async function inviteTeacher(teacherSubject: string): Promise<ParentOperationState<void>> {
    void teacherSubject;
    void sharesProfileId;
    return unavailableShareOperation;
  }

  function revokeShare(grantId: string): ParentOperationState<void> {
    void grantId;
    void sharesProfileId;
    return unavailableShareOperation;
  }

  async function loadDeliveries(profileId: string, cursor: string | null = null): Promise<ParentOperationState<void>> {
    setDeliveriesProfileId(profileId);
    void cursor;
    return unavailableShareOperation;
  }

  async function submitFeedback(occurrenceId: string, text: string): Promise<ParentOperationState<void>> {
    void occurrenceId;
    void text;
    void deliveriesProfileId;
    return unavailableShareOperation;
  }

  const [notifications, setNotifications] = useState<ParentNotification[]>([]);
  const [notificationsCursor, setNotificationsCursor] = useState<string | null>(null);
  const [notificationsUnreadCount, setNotificationsUnreadCount] = useState<number | null>(null);
  const [notificationsBusy, setNotificationsBusy] = useState(false);
  const [notificationsError, setNotificationsError] = useState('');
  const notificationActionKeys = useRef(new Map<string, string>());
  const notificationsRequest = useRef(0);

  /** Sign-out or another account: nothing of the previous account's inbox or run list may stay in memory. */
  function resetAccountData(): void {
    notificationsRequest.current += 1;
    notificationActionKeys.current.clear();
    setNotifications([]);
    setNotificationsCursor(null);
    setNotificationsUnreadCount(null);
    setNotificationsBusy(false);
    setNotificationsError('');
    runsRequest.current += 1;
    runActionKeys.current.clear();
    setRuns([]);
    setRunsCursor(null);
    setRunsProfileId(undefined);
    setRunsBusy(false);
    setRunsError('');
  }

  async function loadNotifications(cursor: string | null = null): Promise<ParentOperationState<void>> {
    if (notificationCapability.state !== 'available') return unavailableNotificationOperation;
    const requestedCursor = cursor !== null && cursor === notificationsCursor ? cursor : null;
    const requestNumber = notificationsRequest.current + 1;
    notificationsRequest.current = requestNumber;
    setNotificationsBusy(true);
    setNotificationsError('');
    try {
      const page = await application.platform.listNotifications(requestedCursor, 25);
      if (requestNumber !== notificationsRequest.current) return { state: 'confirmed', value: undefined };
      const merged = mergeNotificationPage(requestedCursor === null ? [] : notifications, page, requestedCursor);
      setNotifications(merged.items);
      setNotificationsCursor(merged.nextCursor);
      setNotificationsUnreadCount(merged.unreadCount);
      return { state: 'confirmed', value: undefined };
    } catch (failure) {
      if (requestNumber !== notificationsRequest.current) return { state: 'failed', retry: 'user-action-required' };
      setNotificationsError(safeParentFlowErrorMessage(failure));
      return { state: 'failed', retry: 'user-action-required' };
    } finally {
      if (requestNumber === notificationsRequest.current) setNotificationsBusy(false);
    }
  }

  async function markNotificationRead(notificationId: string): Promise<ParentOperationState<void>> {
    if (notificationCapability.state !== 'available') return unavailableNotificationOperation;
    if (notifications.find((item) => item.inbox_item_id === notificationId)?.read_at) {
      return { state: 'confirmed', value: undefined };
    }
    const signature = notificationActionSignature('read-one', notificationId);
    const key = retainedNotificationActionKey(notificationActionKeys.current, signature, createParentActionIdentity);
    const startedAt = notificationsRequest.current;
    setNotificationsBusy(true);
    setNotificationsError('');
    try {
      const updated = await application.platform.markNotificationRead(notificationId, key);
      notificationActionKeys.current.delete(signature);
      // A newer load (screen left and opened again, account changed) already replaced the list: do not overwrite it.
      if (notificationsRequest.current !== startedAt) return { state: 'confirmed', value: undefined };
      const next = applyNotificationRead(notifications, notificationsUnreadCount, updated);
      setNotifications(next.items);
      setNotificationsUnreadCount(next.unreadCount);
      if (next.shouldRefresh) await loadNotifications(null);
      return { state: 'confirmed', value: undefined };
    } catch (failure) {
      const outcome = failure instanceof ParentApplicationError
        ? notificationActionOutcome(failure.code, failure.status)
        : 'error';
      if (outcome === 'reload') {
        notificationActionKeys.current.delete(signature);
        await loadNotifications(null);
      } else if (isDefinitiveNotificationFailure(failure)) {
        notificationActionKeys.current.delete(signature);
      }
      setNotificationsError(outcome === 'reload' ? notificationReloadMessage : safeParentFlowErrorMessage(failure));
      return { state: 'failed', retry: outcome === 'error' ? 'user-action-required' : 'not-retryable' };
    } finally {
      if (notificationsRequest.current === startedAt) setNotificationsBusy(false);
    }
  }

  async function markAllNotificationsRead(): Promise<ParentOperationState<void>> {
    if (notificationCapability.state !== 'available') return unavailableNotificationOperation;
    if (notificationsUnreadCount === null || notificationsUnreadCount === 0) {
      return { state: 'confirmed', value: undefined };
    }
    const signature = notificationActionSignature('read-all');
    const key = retainedNotificationActionKey(notificationActionKeys.current, signature, createParentActionIdentity);
    const startedAt = notificationsRequest.current;
    setNotificationsBusy(true);
    setNotificationsError('');
    try {
      await application.platform.markAllNotificationsRead(key);
      notificationActionKeys.current.delete(signature);
      await loadNotifications(null);
      return { state: 'confirmed', value: undefined };
    } catch (failure) {
      const outcome = failure instanceof ParentApplicationError
        ? notificationActionOutcome(failure.code, failure.status)
        : 'error';
      if (outcome === 'reload') {
        notificationActionKeys.current.delete(signature);
        await loadNotifications(null);
      } else if (isDefinitiveNotificationFailure(failure)) {
        notificationActionKeys.current.delete(signature);
      }
      setNotificationsError(outcome === 'reload' ? notificationReloadMessage : safeParentFlowErrorMessage(failure));
      return { state: 'failed', retry: outcome === 'error' ? 'user-action-required' : 'not-retryable' };
    } finally {
      if (notificationsRequest.current === startedAt) setNotificationsBusy(false);
    }
  }

  async function loadQuota(): Promise<ParentOperationState<void>> {
    return unavailableShareOperation;
  }

  return {
    resetAccountData,
    runs,
    runsCursor,
    runsProfileId,
    runsBusy,
    runsError: runHistoryCapability.state === 'available' ? runsError : unavailableMessage,
    loadRuns,
    cancelRun: (runId: string) => requestRunLifecycle(runId, 'cancel'),
    deleteRun: (runId: string) => requestRunLifecycle(runId, 'delete'),
    shares: [] as ParentProfileShareGrant[],
    sharesProfileId,
    sharesBusy: false,
    sharesError: unavailableMessage,
    shareCapability: platformCapabilities.sharing,
    shareInviteState: unavailableShareOperation,
    shareRevokeState: unavailableShareOperation,
    loadShares,
    inviteTeacher,
    revokeShare,
    deliveries: [] as ParentLessonDelivery[],
    deliveriesCursor: null as string | null,
    deliveriesProfileId,
    deliveriesBusy: false,
    deliveriesError: unavailableMessage,
    loadDeliveries,
    submitFeedback,
    notifications,
    notificationsCursor,
    notificationsUnreadCount,
    notificationsBusy,
    notificationsError: notificationCapability.state === 'available' ? notificationsError : unavailableMessage,
    loadNotifications,
    markNotificationRead,
    markAllNotificationsRead,
    quota: null as ParentVideoQuota | null,
    quotaBusy: false,
    quotaError: unavailableMessage,
    loadQuota,
    capabilities: platformCapabilities,
  };
}
