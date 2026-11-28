import { useEffect, useRef, useState } from 'react';
import { AppState, Linking } from 'react-native';
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
import {
  cancelResultMessage,
  CHECKOUT_URL_MISSING_COPY,
  CheckoutIdentityMap,
  enabledQuotaProviders,
  getOpenParentInvoice,
  isCheckoutUrlOpenable,
  paymentAttemptExpired,
  pollParentInvoice,
  quotaPaymentErrorMessage,
  reconcileResultMessage,
  RECONCILE_COOLDOWN_MS,
  reconcileSecondsRemaining,
  terminalInvoiceMessage,
  withReconcileCooldown,
  type ParentPaymentMessage,
  type ParentPaymentProvider,
} from '../../application/parentQuota';
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
  ParentLessonFeedbackReplyPageV1,
  ParentLessonFeedbackStateV1,
  ParentLessonFeedbackV1,
  ParentNotification,
  ParentShareDeliveryPageV1,
  ParentShareField,
  ParentShareGrantCreatedV1,
  ParentShareGrantV1,
  ParentStoryRunSummary,
  ParentVideoQuota,
  ParentQuotaProduct,
  ParentQuotaInvoice,
  ParentQuotaPaymentSettings,
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
const quotaCapability = apiConfigured('quota');
const unavailableNotificationOperation = createUnavailableOperationState<void>(
  notificationCapability.state === 'unavailable' ? notificationCapability.reason : unavailableReason,
);
const unavailableQuotaOperation = createUnavailableOperationState<void>(
  quotaCapability.state === 'unavailable' ? quotaCapability.reason : unavailableReason,
);

const platformCapabilities = {
  runs: runHistoryCapability,
  sharing: apiConfigured('profile-sharing'),
  deliveries: createUnavailableCapabilityState('lesson-history', unavailableReason),
  notifications: notificationCapability,
  quota: quotaCapability,
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

function parentShareFailureMessage(failure: unknown): string {
  if (failure instanceof ParentApplicationError) {
    if (failure.status === 403 || failure.status === 404
      || failure.code === 'RESOURCE_NOT_FOUND' || failure.code.endsWith('_NOT_FOUND')) {
      return 'Thông tin chia sẻ hiện chưa khả dụng.';
    }
    if (failure.status === 503 || failure.code === 'DATABASE_UNAVAILABLE') {
      return 'Chia sẻ hồ sơ hiện chưa khả dụng. Hãy thử lại sau.';
    }
    if (failure.code === 'RESOURCE_CONFLICT') {
      return 'Hồ sơ đã có đủ lời mời đang mở. Hãy thu hồi một lời mời hoặc thử lại sau.';
    }
    if (failure.code === 'STALE_REVISION') {
      return 'Quyền chia sẻ vừa thay đổi. Trạng thái mới đã được tải lại.';
    }
    if (failure.code === 'INVALID_STATE_TRANSITION') {
      return 'Quyền chia sẻ này không còn hoạt động.';
    }
  }
  return 'Chưa thể hoàn tất thao tác chia sẻ. Hãy thử lại sau.';
}

/** Run history is live (FEAT-081 C3b); the other absent platform routes stay local and unavailable. */
export function useParentPlatformController(application: ParentApplicationModule) {
  const [sharesProfileId, setSharesProfileId] = useState('');
  const [shares, setShares] = useState<ParentShareGrantV1[]>([]);
  const [sharesCursor, setSharesCursor] = useState<string | null>(null);
  const [sharesBusy, setSharesBusy] = useState(false);
  const [sharesError, setSharesError] = useState('');
  const [sharesUnavailable, setSharesUnavailable] = useState(false);
  const sharesRequest = useRef(0);
  const shareInviteRequest = useRef(false);
  const shareRevokeRequest = useRef(false);
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

  async function loadShares(profileId: string, cursor: string | null = null): Promise<ParentOperationState<void>> {
    if (!profileId.trim()) return { state: 'failed', retry: 'not-retryable' };
    const requestedCursor = profileId === sharesProfileId ? cursor : null;
    const requestNumber = sharesRequest.current + 1;
    sharesRequest.current = requestNumber;
    if (profileId !== sharesProfileId) setShares([]);
    setSharesProfileId(profileId);
    setSharesBusy(true);
    setSharesError('');
    try {
      const page = await application.platform.listShares(profileId, requestedCursor);
      if (requestNumber !== sharesRequest.current) return { state: 'confirmed', value: undefined };
      setShares((current) => {
        const merged = new Map((requestedCursor === null ? [] : current)
          .map((grant) => [grant.share_grant_id, grant] as const));
        for (const grant of page.items) merged.set(grant.share_grant_id, grant);
        return [...merged.values()];
      });
      setSharesCursor(page.next_cursor);
      setSharesUnavailable(false);
      return { state: 'confirmed', value: undefined };
    } catch (failure) {
      if (requestNumber !== sharesRequest.current) return { state: 'failed', retry: 'user-action-required' };
      setSharesUnavailable(failure instanceof ParentApplicationError && failure.status === 503);
      setSharesError(parentShareFailureMessage(failure));
      return { state: 'failed', retry: 'user-action-required' };
    } finally {
      if (requestNumber === sharesRequest.current) setSharesBusy(false);
    }
  }

  async function inviteTeacher(
    profileId: string,
    grantedFields: ParentShareField[],
    actionIdentity: string,
  ): Promise<ParentShareGrantCreatedV1> {
    if (shareInviteRequest.current) throw new ParentApplicationError('REQUEST_PENDING', 'Request pending.');
    shareInviteRequest.current = true;
    setSharesBusy(true);
    setSharesError('');
    try {
      const created = await application.platform.inviteTeacher(profileId, grantedFields, actionIdentity);
      const { invitation_code: _invitationCode, ...grant } = created;
      setShares((current) => [grant, ...current.filter((item) => item.share_grant_id !== grant.share_grant_id)]);
      setSharesUnavailable(false);
      return created;
    } catch (failure) {
      setSharesUnavailable(failure instanceof ParentApplicationError && failure.status === 503);
      setSharesError(parentShareFailureMessage(failure));
      throw failure;
    } finally {
      shareInviteRequest.current = false;
      setSharesBusy(false);
    }
  }

  function getShareGrant(grantId: string): Promise<ParentShareGrantV1> {
    return application.platform.getShareGrant(grantId);
  }

  async function revokeShare(
    grantId: string,
    revision: number,
    actionIdentity: string,
  ): Promise<ParentShareGrantV1> {
    if (shareRevokeRequest.current) throw new ParentApplicationError('REQUEST_PENDING', 'Request pending.');
    shareRevokeRequest.current = true;
    setSharesBusy(true);
    setSharesError('');
    try {
      const revoked = await application.platform.revokeShare(grantId, revision, actionIdentity);
      setShares((current) => current.map((grant) => grant.share_grant_id === revoked.share_grant_id ? revoked : grant));
      return revoked;
    } catch (failure) {
      setSharesUnavailable(failure instanceof ParentApplicationError && failure.status === 503);
      setSharesError(parentShareFailureMessage(failure));
      if (failure instanceof ParentApplicationError && failure.code === 'STALE_REVISION' && sharesProfileId) {
        void loadShares(sharesProfileId, null);
      }
      throw failure;
    } finally {
      shareRevokeRequest.current = false;
      setSharesBusy(false);
    }
  }

  function listShareDeliveries(grantId: string, cursor: string | null = null): Promise<ParentShareDeliveryPageV1> {
    return application.platform.listShareDeliveries(grantId, cursor);
  }

  async function loadDeliveries(profileId: string, cursor: string | null = null): Promise<ParentOperationState<void>> {
    setDeliveriesProfileId(profileId);
    void cursor;
    return unavailableShareOperation;
  }

  function submitFeedback(
    lessonId: string,
    text: string,
    actionIdentity = createParentActionIdentity(),
  ): Promise<ParentLessonFeedbackV1> {
    return application.platform.submitFeedback(lessonId, text, actionIdentity);
  }

  function getLessonFeedback(lessonId: string): Promise<ParentLessonFeedbackStateV1> {
    return application.platform.getLessonFeedback(lessonId);
  }

  function listLessonFeedbackReplies(
    lessonId: string,
    cursor: string | null = null,
  ): Promise<ParentLessonFeedbackReplyPageV1> {
    return application.platform.listLessonFeedbackReplies(lessonId, cursor);
  }

  const [notifications, setNotifications] = useState<ParentNotification[]>([]);
  const [notificationsCursor, setNotificationsCursor] = useState<string | null>(null);
  const [notificationsUnreadCount, setNotificationsUnreadCount] = useState<number | null>(null);
  const [notificationsBusy, setNotificationsBusy] = useState(false);
  const [notificationsError, setNotificationsError] = useState('');
  const notificationActionKeys = useRef(new Map<string, string>());
  const notificationsRequest = useRef(0);
  const [quota, setQuota] = useState<ParentVideoQuota | null>(null);
  const [quotaProducts, setQuotaProducts] = useState<ParentQuotaProduct[]>([]);
  const [quotaInvoices, setQuotaInvoices] = useState<ParentQuotaInvoice[]>([]);
  const [quotaPaymentSettings, setQuotaPaymentSettings] = useState<ParentQuotaPaymentSettings | null>(null);
  const [quotaBusy, setQuotaBusy] = useState(false);
  const [quotaCheckoutBusy, setQuotaCheckoutBusy] = useState(false);
  const [quotaActionInvoiceId, setQuotaActionInvoiceId] = useState('');
  const [quotaError, setQuotaError] = useState('');
  const [quotaPaymentStatus, setQuotaPaymentStatus] = useState<ParentPaymentMessage | null>(null);
  const [quotaReconcileCooldowns, setQuotaReconcileCooldowns] = useState<Record<string, number>>({});
  const [quotaClock, setQuotaClock] = useState(Date.now());
  const [quotaReturnInvoiceId, setQuotaReturnInvoiceId] = useState('');
  const quotaCheckoutKeys = useRef(new CheckoutIdentityMap());
  const quotaRequest = useRef(0);
  const quotaSummaryRequest = useRef(0);
  const quotaScreenGeneration = useRef(0);
  const quotaScreenActive = useRef(false);
  const quotaReturnInvoiceIdRef = useRef('');
  const checkoutWasOpened = useRef(false);
  const quotaPollCancel = useRef<(() => void) | null>(null);
  const quotaResumeHandler = useRef<() => void>(() => undefined);
  const appStateCurrent = useRef(AppState.currentState);

  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState) => {
      const wasAway = appStateCurrent.current === 'background' || appStateCurrent.current === 'inactive';
      appStateCurrent.current = nextState;
      if (nextState === 'active' && wasAway && checkoutWasOpened.current) {
        quotaResumeHandler.current();
      }
    });
    return () => subscription.remove();
  }, []);

  /** Sign-out or another account: nothing of the previous account's inbox or run list may stay in memory. */
  function resetAccountData(): void {
    sharesRequest.current += 1;
    setShares([]);
    setSharesCursor(null);
    setSharesProfileId('');
    setSharesBusy(false);
    setSharesError('');
    setSharesUnavailable(false);
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
    setQuota(null);
    quotaSummaryRequest.current += 1;
    clearQuotaScreenState();
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

  async function loadQuotaSummary(): Promise<ParentOperationState<void>> {
    if (quotaCapability.state !== 'available') return unavailableQuotaOperation;
    const requestNumber = quotaSummaryRequest.current + 1;
    quotaSummaryRequest.current = requestNumber;
    try {
      const summary = await application.platform.getVideoQuota();
      if (requestNumber !== quotaSummaryRequest.current) return { state: 'confirmed', value: undefined };
      setQuota(summary);
      return { state: 'confirmed', value: undefined };
    } catch (failure) {
      if (requestNumber !== quotaSummaryRequest.current) return { state: 'failed', retry: 'user-action-required' };
      setQuotaError(quotaPaymentErrorMessage(failure));
      return { state: 'failed', retry: 'user-action-required' };
    }
  }

  async function loadQuota(): Promise<ParentOperationState<void>> {
    if (quotaCapability.state !== 'available') return unavailableQuotaOperation;
    quotaScreenActive.current = true;
    const screenGeneration = quotaScreenGeneration.current;
    const requestNumber = quotaRequest.current + 1;
    quotaRequest.current = requestNumber;
    const summaryRequestNumber = quotaSummaryRequest.current + 1;
    quotaSummaryRequest.current = summaryRequestNumber;
    setQuotaBusy(true);
    setQuotaError('');
    try {
      const [summary, products, invoices, paymentSettings] = await Promise.all([
        application.platform.getVideoQuota(),
        application.platform.getQuotaProducts(),
        application.platform.getQuotaInvoices(50),
        application.platform.getQuotaPaymentSettings(),
      ]);
      if (requestNumber !== quotaRequest.current || screenGeneration !== quotaScreenGeneration.current) return { state: 'confirmed', value: undefined };
      if (summaryRequestNumber === quotaSummaryRequest.current) setQuota(summary);
      setQuotaProducts(products);
      setQuotaInvoices(invoices.items);
      setQuotaPaymentSettings(paymentSettings);
      return { state: 'confirmed', value: undefined };
    } catch (failure) {
      if (requestNumber !== quotaRequest.current || screenGeneration !== quotaScreenGeneration.current) return { state: 'failed', retry: 'user-action-required' };
      setQuotaError(quotaPaymentErrorMessage(failure));
      return { state: 'failed', retry: 'user-action-required' };
    } finally {
      if (requestNumber === quotaRequest.current && screenGeneration === quotaScreenGeneration.current) setQuotaBusy(false);
    }
  }

  async function openQuotaCheckoutLink(invoiceId: string, checkoutUrl: string): Promise<void> {
    if (!quotaScreenActive.current) return;
    const screenGeneration = quotaScreenGeneration.current;
    if (!isCheckoutUrlOpenable(checkoutUrl)) {
      setQuotaPaymentStatus({ kind: 'pending', text: CHECKOUT_URL_MISSING_COPY });
      return;
    }
    quotaReturnInvoiceIdRef.current = invoiceId;
    setQuotaReturnInvoiceId(invoiceId);
    checkoutWasOpened.current = true;
    setQuotaPaymentStatus({ kind: 'pending', text: 'Đang chờ xác nhận thanh toán…' });
    setQuotaError('');
    try {
      await Linking.openURL(checkoutUrl);
    } catch {
      if (screenGeneration !== quotaScreenGeneration.current) return;
      checkoutWasOpened.current = false;
      quotaReturnInvoiceIdRef.current = '';
      setQuotaReturnInvoiceId('');
      setQuotaPaymentStatus({ kind: 'pending', text: 'Không mở được trang thanh toán. Hóa đơn vẫn được giữ; hãy kiểm tra trạng thái.' });
      void loadQuota();
    }
  }

  async function checkoutQuotaProduct(productId: string, provider: ParentPaymentProvider): Promise<void> {
    if (!quotaScreenActive.current || quotaCheckoutBusy || quotaCapability.state !== 'available') return;
    const providerIsEnabled = quotaPaymentSettings
      && enabledQuotaProviders(quotaPaymentSettings).some((item) => item.provider === provider);
    if (!providerIsEnabled) {
      setQuotaError('Thanh toán hiện chưa sẵn sàng. Bạn vẫn có thể xem các gói và giá.');
      return;
    }
    if (getOpenParentInvoice(quotaInvoices)) {
      setQuotaError('Đã có giao dịch chưa nhận được kết quả cuối. Mở lại nếu liên kết còn hạn, hoặc kiểm tra trạng thái sau khi liên kết hết hạn.');
      return;
    }
    const key = quotaCheckoutKeys.current.get(productId, provider, createParentActionIdentity);
    const screenGeneration = quotaScreenGeneration.current;
    setQuotaCheckoutBusy(true);
    setQuotaError('');
    setQuotaPaymentStatus(null);
    try {
      const result = await application.platform.checkoutQuotaProduct(productId, provider, key);
      if (screenGeneration !== quotaScreenGeneration.current || !quotaScreenActive.current) return;
      quotaCheckoutKeys.current.complete(productId, provider);
      if (!result.checkout_url || !isCheckoutUrlOpenable(result.checkout_url)) {
        setQuotaPaymentStatus({ kind: 'pending', text: CHECKOUT_URL_MISSING_COPY });
        await loadQuota();
        return;
      }
      await openQuotaCheckoutLink(result.invoice_id, result.checkout_url);
    } catch (failure) {
      if (screenGeneration !== quotaScreenGeneration.current) return;
      setQuotaError(quotaPaymentErrorMessage(failure));
    } finally {
      if (screenGeneration === quotaScreenGeneration.current) setQuotaCheckoutBusy(false);
    }
  }

  async function resumeQuotaPayment(invoiceId: string, checkoutUrl: string): Promise<void> {
    await openQuotaCheckoutLink(invoiceId, checkoutUrl);
  }

  async function reconcileQuotaInvoice(invoiceId: string): Promise<void> {
    if (!quotaScreenActive.current || quotaActionInvoiceId || quotaCapability.state !== 'available') return;
    const screenGeneration = quotaScreenGeneration.current;
    if (reconcileSecondsRemaining(quotaReconcileCooldowns, invoiceId, quotaClock) > 0) return;
    setQuotaReconcileCooldowns((current) => withReconcileCooldown(current, invoiceId, Date.now() + RECONCILE_COOLDOWN_MS));
    setQuotaActionInvoiceId(invoiceId);
    setQuotaError('');
    setQuotaPaymentStatus(null);
    try {
      const result = await application.platform.reconcileQuotaInvoice(invoiceId);
      if (screenGeneration !== quotaScreenGeneration.current || !quotaScreenActive.current) return;
      if (['PAID', 'FAILED', 'CANCELED'].includes(result.state)) {
        setQuotaReconcileCooldowns((current) => withReconcileCooldown(current, invoiceId, null));
      }
      setQuotaPaymentStatus(reconcileResultMessage(result));
      await loadQuota();
    } catch (failure) {
      if (screenGeneration !== quotaScreenGeneration.current) return;
      setQuotaError(quotaPaymentErrorMessage(failure));
      if (failure instanceof ParentApplicationError && (failure.status ?? 0) >= 500) {
        setQuotaPaymentStatus({ kind: 'pending', text: 'Chưa nhận được kết quả đối soát có thể xác minh. Hóa đơn chưa chuyển trạng thái và quota chưa thay đổi. Chờ hết thời gian đếm ngược rồi mới kiểm tra lại.' });
      }
    } finally {
      if (screenGeneration === quotaScreenGeneration.current) setQuotaActionInvoiceId('');
    }
  }

  async function cancelExpiredQuotaInvoice(invoiceId: string): Promise<void> {
    if (!quotaScreenActive.current || quotaActionInvoiceId || quotaCapability.state !== 'available') return;
    const screenGeneration = quotaScreenGeneration.current;
    const invoice = quotaInvoices.find((item) => item.invoice_id === invoiceId);
    const attempt = invoice?.attempts.find((item) => ['REQUESTING', 'OPEN', 'UNKNOWN'].includes(item.state));
    if (!invoice || invoice.provider !== 'VNPAY' || !attempt?.expires_at || !paymentAttemptExpired(attempt.expires_at, quotaClock)) return;
    setQuotaReconcileCooldowns((current) => withReconcileCooldown(current, invoiceId, null));
    setQuotaActionInvoiceId(invoiceId);
    setQuotaError('');
    setQuotaPaymentStatus(null);
    try {
      const result = await application.platform.cancelQuotaInvoice(invoiceId);
      if (screenGeneration !== quotaScreenGeneration.current || !quotaScreenActive.current) return;
      if (['PAID', 'FAILED', 'CANCELED'].includes(result.state)) {
        setQuotaReconcileCooldowns((current) => withReconcileCooldown(current, invoiceId, null));
      }
      setQuotaPaymentStatus(cancelResultMessage(result));
      await loadQuota();
    } catch (failure) {
      if (screenGeneration !== quotaScreenGeneration.current) return;
      setQuotaError(quotaPaymentErrorMessage(failure));
      if (failure instanceof ParentApplicationError && (failure.status ?? 0) >= 500) {
        setQuotaPaymentStatus({ kind: 'pending', text: 'Chưa xác minh được với VNPay nên hóa đơn chưa bị hủy. Kiểm tra lại sau để tránh hủy nhầm giao dịch đã trả tiền.' });
      }
    } finally {
      if (screenGeneration === quotaScreenGeneration.current) setQuotaActionInvoiceId('');
    }
  }

  async function resumeQuotaReturnPolling(): Promise<void> {
    const invoiceId = quotaReturnInvoiceIdRef.current;
    if (!quotaScreenActive.current || !invoiceId || !checkoutWasOpened.current || quotaPollCancel.current) return;
    checkoutWasOpened.current = false;
    const screenGeneration = quotaScreenGeneration.current;
    let cancelled = false;
    const cancel = () => { cancelled = true; };
    quotaPollCancel.current = cancel;
    setQuotaPaymentStatus({ kind: 'pending', text: 'Đang chờ cổng thanh toán xác nhận giao dịch…' });
    const result = await pollParentInvoice({
      invoiceId,
      fetchInvoices: () => application.platform.getQuotaInvoices(50),
      onInvoices: (page) => setQuotaInvoices(page.items),
      shouldContinue: () => !cancelled
        && screenGeneration === quotaScreenGeneration.current
        && quotaScreenActive.current
        && quotaReturnInvoiceIdRef.current === invoiceId,
    });
    if (screenGeneration !== quotaScreenGeneration.current || !quotaScreenActive.current) return;
    if (quotaPollCancel.current === cancel) quotaPollCancel.current = null;
    if (result.state === 'cancelled') return;
    quotaReturnInvoiceIdRef.current = '';
    setQuotaReturnInvoiceId('');
    if (result.state === 'terminal') {
      setQuotaPaymentStatus(terminalInvoiceMessage(result.invoice));
      await loadQuotaSummary();
    } else {
      setQuotaPaymentStatus({ kind: 'pending', text: 'Chưa nhận được xác nhận cuối từ cổng. Hóa đơn vẫn được giữ; dùng “Kiểm tra trạng thái” trong danh sách hóa đơn.' });
    }
  }

  quotaResumeHandler.current = () => { void resumeQuotaReturnPolling(); };

  function clearQuotaScreenState(): void {
    quotaScreenGeneration.current += 1;
    quotaScreenActive.current = false;
    quotaRequest.current += 1;
    quotaPollCancel.current?.();
    quotaPollCancel.current = null;
    quotaReturnInvoiceIdRef.current = '';
    checkoutWasOpened.current = false;
    quotaCheckoutKeys.current.reset();
    setQuotaProducts([]);
    setQuotaInvoices([]);
    setQuotaPaymentSettings(null);
    setQuotaBusy(false);
    setQuotaCheckoutBusy(false);
    setQuotaActionInvoiceId('');
    setQuotaError('');
    setQuotaPaymentStatus(null);
    setQuotaReconcileCooldowns({});
    setQuotaReturnInvoiceId('');
  }

  useEffect(() => {
    const cooldownPending = Object.values(quotaReconcileCooldowns).some((until) => until > quotaClock);
    const expiryPending = quotaInvoices.some((invoice) => invoice.state === 'PENDING'
      && invoice.attempts.some((attempt) => attempt.expires_at && Date.parse(attempt.expires_at) > quotaClock));
    if (!cooldownPending && !expiryPending) return undefined;
    const timer = setInterval(() => setQuotaClock(Date.now()), 1_000);
    return () => clearInterval(timer);
  }, [quotaClock, quotaInvoices, quotaReconcileCooldowns]);

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
    shares,
    sharesCursor,
    sharesProfileId,
    sharesBusy,
    sharesError,
    shareCapability: sharesUnavailable
      ? createUnavailableCapabilityState('profile-sharing', unavailableReason)
      : platformCapabilities.sharing,
    loadShares,
    inviteTeacher,
    revokeShare,
    getShareGrant,
    listShareDeliveries,
    deliveries: [] as ParentLessonDelivery[],
    deliveriesCursor: null as string | null,
    deliveriesProfileId,
    deliveriesBusy: false,
    deliveriesError: unavailableMessage,
    loadDeliveries,
    submitFeedback,
    getLessonFeedback,
    listLessonFeedbackReplies,
    notifications,
    notificationsCursor,
    notificationsUnreadCount,
    notificationsBusy,
    notificationsError: notificationCapability.state === 'available' ? notificationsError : unavailableMessage,
    loadNotifications,
    markNotificationRead,
    markAllNotificationsRead,
    quota,
    quotaProducts,
    quotaInvoices,
    quotaPaymentSettings,
    quotaBusy,
    quotaCheckoutBusy,
    quotaActionInvoiceId,
    quotaError: quotaCapability.state === 'available' ? quotaError : unavailableMessage,
    quotaPaymentStatus,
    quotaReconcileCooldowns,
    quotaClock,
    quotaReturnInvoiceId,
    enabledQuotaProviders: quotaPaymentSettings ? enabledQuotaProviders(quotaPaymentSettings) : [],
    quotaReconcileSecondsRemaining: (invoiceId: string) => reconcileSecondsRemaining(quotaReconcileCooldowns, invoiceId, quotaClock),
    loadQuota,
    loadQuotaSummary,
    checkoutQuotaProduct,
    resumeQuotaPayment,
    reconcileQuotaInvoice,
    cancelExpiredQuotaInvoice,
    clearQuotaScreenState,
    capabilities: platformCapabilities,
  };
}
