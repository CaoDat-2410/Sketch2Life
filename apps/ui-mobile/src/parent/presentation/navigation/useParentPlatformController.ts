import { useState } from 'react';
import type { ParentApplicationModule } from '../../application/ports/ParentApplicationModule';
import { ParentApplicationError } from '../../application/ParentApplicationError';
import type {
  ParentLessonDelivery,
  ParentNotification,
  ParentProfileShareGrant,
  ParentStoryRunHistoryPage,
  ParentVideoQuota,
  StoryRun,
} from '../../domain/types';

/** Presentation state for API-backed Parent platform pages, separate from the drawing workflow. */
export function useParentPlatformController(application: ParentApplicationModule) {
  const [runs, setRuns] = useState<StoryRun[]>([]);
  const [runsCursor, setRunsCursor] = useState<string | null>(null);
  const [runsProfileId, setRunsProfileId] = useState<string | undefined>();
  const [runsBusy, setRunsBusy] = useState(false);
  const [runsError, setRunsError] = useState('');

  const [shares, setShares] = useState<ParentProfileShareGrant[]>([]);
  const [sharesProfileId, setSharesProfileId] = useState('');
  const [sharesBusy, setSharesBusy] = useState(false);
  const [sharesError, setSharesError] = useState('');

  const [deliveries, setDeliveries] = useState<ParentLessonDelivery[]>([]);
  const [deliveriesCursor, setDeliveriesCursor] = useState<string | null>(null);
  const [deliveriesProfileId, setDeliveriesProfileId] = useState('');
  const [deliveriesBusy, setDeliveriesBusy] = useState(false);
  const [deliveriesError, setDeliveriesError] = useState('');

  const [notifications, setNotifications] = useState<ParentNotification[]>([]);
  const [notificationsCursor, setNotificationsCursor] = useState<string | null>(null);
  const [notificationsBusy, setNotificationsBusy] = useState(false);
  const [notificationsError, setNotificationsError] = useState('');

  const [quota, setQuota] = useState<ParentVideoQuota | null>(null);
  const [quotaBusy, setQuotaBusy] = useState(false);
  const [quotaError, setQuotaError] = useState('');

  async function loadRuns(profileId = runsProfileId, cursor: string | null = null): Promise<void> {
    setRunsBusy(true);
    setRunsError('');
    if (!cursor) setRunsProfileId(profileId);
    try {
      const page: ParentStoryRunHistoryPage = await application.platform.listRuns(profileId, cursor);
      setRuns((current) => cursor ? [...current, ...page.items] : page.items);
      setRunsCursor(page.next_cursor);
    } catch (cause) {
      setRunsError(errorText(cause));
    } finally {
      setRunsBusy(false);
    }
  }

  async function requestRunLifecycle(runId: string, operation: 'cancel' | 'delete'): Promise<void> {
    setRunsBusy(true);
    setRunsError('');
    try {
      const receipt = operation === 'cancel'
        ? await application.platform.cancelRun(runId)
        : await application.platform.deleteRun(runId);
      setRuns((current) => current.map((run) => run.run_id === runId
        ? { ...run, run_state: receipt.run_state }
        : run));
      if (runsProfileId) await loadRuns(runsProfileId);
    } catch (cause) {
      setRunsError(errorText(cause));
    } finally {
      setRunsBusy(false);
    }
  }

  async function loadShares(profileId: string): Promise<void> {
    setSharesProfileId(profileId);
    setSharesBusy(true);
    setSharesError('');
    try {
      const page = await application.platform.listShares(profileId);
      setShares(page.items);
    } catch (cause) {
      setSharesError(errorText(cause));
    } finally {
      setSharesBusy(false);
    }
  }

  async function inviteTeacher(teacherSubject: string): Promise<void> {
    setSharesBusy(true);
    setSharesError('');
    try {
      await application.platform.inviteTeacher(sharesProfileId, teacherSubject);
      await loadShares(sharesProfileId);
    } catch (cause) {
      const message = errorText(cause);
      setSharesError(message);
      throw new Error(message);
    } finally {
      setSharesBusy(false);
    }
  }

  async function revokeShare(grantId: string): Promise<void> {
    setSharesBusy(true);
    setSharesError('');
    try {
      await application.platform.revokeShare(sharesProfileId, grantId);
      await loadShares(sharesProfileId);
    } catch (cause) {
      setSharesError(errorText(cause));
    } finally {
      setSharesBusy(false);
    }
  }

  async function loadDeliveries(profileId: string, cursor: string | null = null): Promise<void> {
    setDeliveriesProfileId(profileId);
    setDeliveriesBusy(true);
    setDeliveriesError('');
    try {
      const page = await application.platform.listDeliveries(profileId, cursor);
      setDeliveries((current) => cursor ? [...current, ...page.items] : page.items);
      setDeliveriesCursor(page.next_cursor);
    } catch (cause) {
      setDeliveriesError(errorText(cause));
    } finally {
      setDeliveriesBusy(false);
    }
  }

  async function submitFeedback(occurrenceId: string, text: string): Promise<void> {
    setDeliveriesBusy(true);
    setDeliveriesError('');
    try {
      const feedback = await application.platform.submitFeedback(occurrenceId, deliveriesProfileId, text);
      setDeliveries((current) => current.map((delivery) => delivery.occurrence_id === occurrenceId
        ? { ...delivery, feedback: {
          feedback_id: feedback.feedback_id,
          feedback_text: feedback.feedback_text,
          created_at: feedback.created_at,
          updated_at: feedback.updated_at,
        } }
        : delivery));
    } catch (cause) {
      const message = errorText(cause);
      setDeliveriesError(message);
      throw new Error(message);
    } finally {
      setDeliveriesBusy(false);
    }
  }

  async function loadNotifications(cursor: string | null = null): Promise<void> {
    setNotificationsBusy(true);
    setNotificationsError('');
    try {
      const page = await application.platform.listNotifications(cursor);
      setNotifications((current) => cursor ? [...current, ...page.items] : page.items);
      setNotificationsCursor(page.next_cursor);
    } catch (cause) {
      setNotificationsError(errorText(cause));
    } finally {
      setNotificationsBusy(false);
    }
  }

  async function markNotificationRead(notificationId: string): Promise<void> {
    try {
      const updated = await application.platform.markNotificationRead(notificationId);
      setNotifications((current) => current.map((item) => item.notification_id === updated.notification_id ? updated : item));
    } catch (cause) {
      setNotificationsError(errorText(cause));
    }
  }

  async function loadQuota(): Promise<void> {
    setQuotaBusy(true);
    setQuotaError('');
    try {
      setQuota(await application.platform.getVideoQuota());
    } catch (cause) {
      setQuotaError(errorText(cause));
    } finally {
      setQuotaBusy(false);
    }
  }

  return {
    runs, runsCursor, runsProfileId, runsBusy, runsError, loadRuns,
    cancelRun: (runId: string) => requestRunLifecycle(runId, 'cancel'),
    deleteRun: (runId: string) => requestRunLifecycle(runId, 'delete'),
    shares, sharesProfileId, sharesBusy, sharesError, loadShares, inviteTeacher, revokeShare,
    deliveries, deliveriesCursor, deliveriesProfileId, deliveriesBusy, deliveriesError, loadDeliveries, submitFeedback,
    notifications, notificationsCursor, notificationsBusy, notificationsError, loadNotifications, markNotificationRead,
    quota, quotaBusy, quotaError, loadQuota,
  };
}

function errorText(cause: unknown): string {
  if (cause instanceof ParentApplicationError) {
    return `${cause.message} · ${cause.code}${cause.requestId ? ` · ${cause.requestId}` : ''}`;
  }
  return cause instanceof Error ? cause.message : 'Có lỗi không xác định.';
}
