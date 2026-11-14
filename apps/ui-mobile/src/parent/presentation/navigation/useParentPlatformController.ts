import { useState } from 'react';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import {
  createUnavailableCapabilityState,
  createUnavailableOperationState,
  type ParentCapabilityUnavailableReason,
  type ParentJobStageState,
  type ParentOperationState,
} from '../../application/ports/ParentCapabilityPorts';
import type {
  ParentLessonDelivery,
  ParentNotification,
  ParentProfileShareGrant,
  ParentVideoQuota,
  StoryRun,
} from '../../domain/types';

const unavailableReason: ParentCapabilityUnavailableReason = 'route-not-in-be-handoff';
const unavailableMessage = 'Chức năng này chưa có tuyến dịch vụ được xác nhận. Chưa có thao tác nào được gửi.';

const platformCapabilities = {
  runs: createUnavailableCapabilityState('run-history', unavailableReason),
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

/** Keeps absent platform routes local and visibly unavailable until a contract is approved. */
export function useParentPlatformController(application: ParentApplicationModule) {
  void application;
  const [sharesProfileId, setSharesProfileId] = useState('');
  const [deliveriesProfileId, setDeliveriesProfileId] = useState('');

  async function loadRuns(profileId?: string, cursor: string | null = null): Promise<ParentOperationState<void>> {
    void cursor;
    void profileId;
    return unavailableShareOperation;
  }

  async function requestRunLifecycle(runId: string, operation: 'cancel' | 'delete'): Promise<ParentOperationState<void>> {
    void runId;
    void operation;
    return unavailableShareOperation;
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
    runs: [] as StoryRun[],
    runsCursor: null as string | null,
    runsProfileId: undefined as string | undefined,
    runsBusy: false,
    runsError: unavailableMessage,
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
