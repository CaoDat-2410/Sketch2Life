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
  ParentVideoCandidateV1,
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
  video: parentConfig.apiBaseUrl
    ? { capability: 'video' as const, state: 'available' as const }
    : createUnavailableCapabilityState('video', 'capability-not-configured'),
};

const unavailableShareOperation: ParentOperationState<void> =
  createUnavailableOperationState<void>(unavailableReason);
const runHistoryLoadError = 'Không tải được lịch sử buổi học. Vui lòng thử lại.';
const runActionMessages = {
  reload: 'Buổi học vừa thay đổi; danh sách đã được tải lại.',
  remove: 'Buổi học không còn trong danh sách.',
  error: 'Chưa thực hiện được thao tác. Vui lòng thử lại.',
} as const;

/** Parent platform operations and the local synthetic video-candidate flow. */
export function useParentPlatformController(
  application: ParentApplicationModule,
  activeRunId: string | null,
) {
  const [sharesProfileId, setSharesProfileId] = useState('');
  const [deliveriesProfileId, setDeliveriesProfileId] = useState('');
  const [runs, setRuns] = useState<ParentStoryRunSummary[]>([]);
  const [runsCursor, setRunsCursor] = useState<string | null>(null);
  const [runsProfileId, setRunsProfileId] = useState<string | undefined>(undefined);
  const [runsBusy, setRunsBusy] = useState(false);
  const [runsError, setRunsError] = useState('');
  const runActionKeys = useRef(new Map<string, string>());
  const runsRequest = useRef(0);
  const videoRequestKey = useRef<{ signature: string; key: string } | null>(null);
  const videoJobRequestId = useRef(0);
  const videoJobRequest = useRef<{
    runId: string;
    requestId: number;
    promise: Promise<ParentOperationState<void>>;
  } | null>(null);
  const [videoCandidate, setVideoCandidate] = useState<ParentVideoCandidateV1 | null>(null);
  const [videoBusy, setVideoBusy] = useState(false);
  const [videoError, setVideoError] = useState('');
  const [videoCandidateLookupRunId, setVideoCandidateLookupRunId] = useState<string | null>(null);
  const [videoRequestAttemptedRunId, setVideoRequestAttemptedRunId] = useState<string | null>(null);
  const [videoPreviewSource, setVideoPreviewSource] = useState<{ uri: string; headers: Record<string, string> } | null>(null);
  const currentVideoCandidate = videoCandidate?.story_run_id === activeRunId ? videoCandidate : null;

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

  function loadVideoJob(runId: string): Promise<ParentOperationState<void>> {
    if (platformCapabilities.video.state !== 'available') {
      return Promise.resolve(createUnavailableOperationState('capability-not-configured'));
    }
    if (videoJobRequest.current?.runId === runId) return videoJobRequest.current.promise;
    const requestId = videoJobRequestId.current + 1;
    videoJobRequestId.current = requestId;
    setVideoBusy(true);
    setVideoError('');
    setVideoCandidateLookupRunId(null);
    const promise = (async (): Promise<ParentOperationState<void>> => {
      try {
        const envelope = await application.platform.getCurrentVideoCandidate(runId);
        if (requestId !== videoJobRequestId.current) return { state: 'confirmed', value: undefined };
        setVideoCandidate(envelope.video_candidate);
        setVideoPreviewSource(null);
        setVideoCandidateLookupRunId(runId);
        if (envelope.video_candidate) setVideoRequestAttemptedRunId(runId);
        return envelope.video_candidate
          ? { state: 'confirmed', value: undefined }
          : { state: 'idle' };
      } catch (cause) {
        if (requestId === videoJobRequestId.current) {
          setVideoError(videoCandidateErrorMessage(cause));
        }
        return { state: 'failed', retry: 'same-job-check-required' };
      } finally {
        if (requestId === videoJobRequestId.current) {
          setVideoBusy(false);
          videoJobRequest.current = null;
        }
      }
    })();
    videoJobRequest.current = { runId, requestId, promise };
    return promise;
  }

  async function requestVideo(runId: string, storyRevision: number, storySha256: string): Promise<ParentOperationState<void>> {
    if (platformCapabilities.video.state !== 'available') return createUnavailableOperationState('capability-not-configured');
    const signature = `${runId}:${storyRevision}:${storySha256}`;
    const identity = videoRequestKey.current?.signature === signature
      ? videoRequestKey.current.key
      : createParentActionIdentity();
    videoRequestKey.current = { signature, key: identity };
    setVideoBusy(true);
    setVideoError('');
    setVideoRequestAttemptedRunId(runId);
    try {
      const envelope = await application.platform.requestVideoCandidate(
        runId, storyRevision, storySha256, identity,
      );
      setVideoCandidate(envelope.video_candidate);
      setVideoPreviewSource(null);
      return { state: 'confirmed', value: undefined };
    } catch (cause) {
      setVideoError(videoCandidateErrorMessage(cause));
      return { state: 'failed', retry: 'same-job-check-required' };
    } finally {
      setVideoBusy(false);
    }
  }

  async function loadVideoPreview(runId: string, candidateId: string): Promise<ParentOperationState<void>> {
    if (!videoCandidate?.preview_available || videoCandidate.state !== 'CANDIDATE_READY') {
      return { state: 'failed', retry: 'not-retryable' };
    }
    setVideoBusy(true);
    setVideoError('');
    try {
      const source = await application.platform.getVideoCandidatePreviewSource(runId, candidateId);
      setVideoPreviewSource(source);
      return { state: 'confirmed', value: undefined };
    } catch (cause) {
      setVideoError(videoCandidateErrorMessage(cause));
      return { state: 'failed', retry: 'user-action-required' };
    } finally {
      setVideoBusy(false);
    }
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
    videoCandidate: currentVideoCandidate,
    videoJobStage: videoStageFor(currentVideoCandidate),
    videoOperationState: currentVideoCandidate
      ? { state: 'confirmed', value: undefined }
      : activeRunId && videoRequestAttemptedRunId === activeRunId
        ? { state: 'failed', retry: 'same-job-check-required' }
        : platformCapabilities.video.state === 'available'
          ? { state: 'idle' }
          : createUnavailableOperationState('capability-not-configured'),
    videoBusy,
    videoError,
    videoCandidateLookupComplete: Boolean(activeRunId && videoCandidateLookupRunId === activeRunId),
    videoRequestAttempted: Boolean(activeRunId && videoRequestAttemptedRunId === activeRunId),
    videoPreviewSource,
    loadVideoJob,
    requestVideo,
    loadVideoPreview,
    markVideoUnsuitable,
    regenerateVideo,
    completeRun,
    capabilities: platformCapabilities,
  };
}

function videoStageFor(candidate: ParentVideoCandidateV1 | null): ParentJobStageState {
  if (!candidate) return { state: 'idle', stage: 'idle' };
  if (candidate.state === 'FAILED') return { state: 'failed', stage: 'failed' };
  if (candidate.state === 'AWAITING_RECONCILIATION') return { state: 'reconciling', stage: 'reconciling' };
  if (candidate.state === 'CANDIDATE_READY') return { state: 'confirmed', stage: 'completed' };
  if (candidate.state === 'GENERATING') return { state: 'pending', stage: 'processing' };
  return { state: 'pending', stage: 'queued' };
}

function videoCandidateErrorMessage(error: unknown): string {
  const code = error instanceof ParentApplicationError ? error.code : '';
  const messages: Record<string, string> = {
    PARENT_VIDEO_CANDIDATE_DISABLED: 'Tạo video thử nghiệm hiện đang tắt trên backend.',
    SYNTHETIC_PROFILE_REQUIRED: 'Chỉ hồ sơ kiểm thử mới được tạo video thử nghiệm.',
    VIDEO_CANDIDATE_ALREADY_REQUESTED: 'Buổi học này đã có một yêu cầu video. Hãy kiểm tra trạng thái hiện tại.',
    VIDEO_DISPATCH_OUTCOME_UNKNOWN: 'Chưa xác định được yêu cầu đã tới Modal hay chưa. Hãy kiểm tra trạng thái, không gửi yêu cầu mới.',
    VIDEO_CANDIDATE_NOT_READY: 'Video thử nghiệm chưa sẵn sàng để xem.',
    VIDEO_SCRIPT_CONFIRMATION_REQUIRED: 'Cần xác nhận đúng phiên bản câu chuyện trước.',
    VIDEO_ACTIVITY_SELECTION_REQUIRED: 'Cần lưu hoạt động chính trước khi tạo video.',
  };
  if (messages[code]) return messages[code];
  if (error instanceof ParentApplicationError && error.code === 'REQUEST_TIMEOUT') {
    return 'Chưa nhận được xác nhận từ máy chủ. Hãy kiểm tra trạng thái, không gửi yêu cầu mới.';
  }
  return 'Chưa thể xử lý video thử nghiệm. Hãy kiểm tra trạng thái buổi học rồi thử lại sau.';
}
