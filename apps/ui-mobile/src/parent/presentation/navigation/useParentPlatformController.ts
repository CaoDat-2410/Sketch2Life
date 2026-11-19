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
import { ParentApplicationError } from '../../application/ParentApplicationError';
import { createParentActionIdentity } from '../../application/ports/ParentPorts';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import {
  createUnavailableCapabilityState,
  createUnavailableOperationState,
  type ParentCapabilityState,
  type ParentCapabilityUnavailableReason,
  type ParentJobStageState,
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

// FEAT-081 C3b: run history is available whenever the live API is configured.
const runHistoryCapability: ParentCapabilityState = parentConfig.apiBaseUrl
  ? { capability: 'run-history', state: 'available' }
  : createUnavailableCapabilityState('run-history', 'capability-not-configured');

const platformCapabilities = {
  runs: runHistoryCapability,
  sharing: createUnavailableCapabilityState('profile-sharing', unavailableReason),
  deliveries: createUnavailableCapabilityState('lesson-history', unavailableReason),
  notifications: createUnavailableCapabilityState('notifications', unavailableReason),
  quota: createUnavailableCapabilityState('quota', unavailableReason),
  jobStatus: createUnavailableCapabilityState('job-status', unavailableReason),
  video: createUnavailableCapabilityState('video', unavailableReason),
};

const unavailableShareOperation: ParentOperationState<void> =
  createUnavailableOperationState<void>(unavailableReason);
const unavailableJobStage: ParentJobStageState = { state: 'unavailable', stage: 'unavailable' };

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

  async function loadNotifications(cursor: string | null = null): Promise<ParentOperationState<void>> {
    void cursor;
    return unavailableShareOperation;
  }

  async function markNotificationRead(notificationId: string): Promise<ParentOperationState<void>> {
    void notificationId;
    return unavailableShareOperation;
  }

  async function loadQuota(): Promise<ParentOperationState<void>> {
    return unavailableShareOperation;
  }

  async function loadVideoJob(runId: string): Promise<ParentOperationState<void>> {
    void runId;
    return unavailableShareOperation;
  }

  async function requestVideo(runId: string, storySha256: string): Promise<ParentOperationState<void>> {
    void runId;
    void storySha256;
    return unavailableShareOperation;
  }

  async function markVideoUnsuitable(runId: string, videoId: string): Promise<ParentOperationState<void>> {
    void runId;
    void videoId;
    return unavailableShareOperation;
  }

  async function regenerateVideo(runId: string, storySha256: string): Promise<ParentOperationState<void>> {
    void runId;
    void storySha256;
    return unavailableShareOperation;
  }

  async function completeRun(runId: string): Promise<ParentOperationState<void>> {
    void runId;
    return unavailableShareOperation;
  }

  return {
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
    notifications: [] as ParentNotification[],
    notificationsCursor: null as string | null,
    notificationsBusy: false,
    notificationsError: unavailableMessage,
    loadNotifications,
    markNotificationRead,
    quota: null as ParentVideoQuota | null,
    quotaBusy: false,
    quotaError: unavailableMessage,
    loadQuota,
    videoJobStage: unavailableJobStage,
    videoOperationState: unavailableShareOperation,
    loadVideoJob,
    requestVideo,
    markVideoUnsuitable,
    regenerateVideo,
    completeRun,
    capabilities: platformCapabilities,
  };
}
