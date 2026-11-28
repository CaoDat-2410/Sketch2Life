import type { ParentApiPort } from '../ports/ParentPorts';
import type { ParentActionIdentity } from '../ports/ParentPorts';
import type { ParentPaymentProvider } from '../parentQuota';
import type { ParentShareField, PushEndpointRegistrationV1 } from '../../domain/types';
import { ParentApplicationError } from '../ParentApplicationError';

/** Application actions for Parent history, sharing, notifications and quota. */
export class ParentPlatformUseCases {
  constructor(private readonly api: ParentApiPort) {}

  listRuns(profileId?: string, cursor?: string | null) {
    return this.api.listStoryRuns(profileId, cursor);
  }

  cancelRun(runId: string) {
    if (!runId.trim()) throw new ParentApplicationError('PARENT_STORY_RUN_REQUIRED', 'Chưa chọn buổi học.');
    return this.api.cancelStoryRun(runId);
  }

  deleteRun(runId: string) {
    if (!runId.trim()) throw new ParentApplicationError('PARENT_STORY_RUN_REQUIRED', 'Chưa chọn buổi học.');
    return this.api.deleteStoryRun(runId);
  }

  /** FR-C-08: the run becomes DELETE_PENDING; the answer is the content-free lifecycle projection. */
  cancelRunV1(runId: string, expectedRevision: number, actionIdentity: string) {
    if (!runId.trim()) throw new ParentApplicationError('PARENT_STORY_RUN_REQUIRED', 'Chưa chọn buổi học.');
    return this.api.cancelStoryRunV1(runId, expectedRevision, actionIdentity);
  }

  /** FR-C-08: delete of a COMPLETED, FAILED or ABANDONED run. */
  deleteRunV1(runId: string, actionIdentity: string) {
    if (!runId.trim()) throw new ParentApplicationError('PARENT_STORY_RUN_REQUIRED', 'Chưa chọn buổi học.');
    return this.api.deleteStoryRunV1(runId, actionIdentity);
  }

  listShares(profileId: string, cursor?: string | null) {
    this.requireId(profileId, 'PARENT_PROFILE_REQUIRED');
    return this.api.listProfileShares(profileId, 25, cursor);
  }

  inviteTeacher(profileId: string, grantedFields: ParentShareField[], actionIdentity: string) {
    this.requireId(profileId, 'PARENT_PROFILE_REQUIRED');
    const allowed = new Set<ParentShareField>(['DISPLAY_NAME', 'AGE_BAND', 'INTERESTS_SUMMARY']);
    const fields = [...new Set(grantedFields)];
    if (fields.length < 1 || fields.length > 3 || fields.some((field) => !allowed.has(field))) {
      throw new ParentApplicationError('INVALID_REQUEST', 'Yêu cầu chưa hợp lệ.');
    }
    return this.api.createProfileShare(profileId, fields.sort(), actionIdentity);
  }

  getShareGrant(grantId: string) {
    this.requireId(grantId, 'PROFILE_SHARE_REQUIRED');
    return this.api.getProfileShare(grantId);
  }

  revokeShare(grantId: string, revision: number, actionIdentity: string) {
    this.requireId(grantId, 'PROFILE_SHARE_REQUIRED');
    if (!Number.isInteger(revision) || revision < 1) {
      throw new ParentApplicationError('INVALID_REQUEST', 'Trạng thái chia sẻ chưa hợp lệ.');
    }
    return this.api.revokeProfileShare(grantId, revision, actionIdentity);
  }

  listShareDeliveries(grantId: string, cursor?: string | null) {
    this.requireId(grantId, 'PROFILE_SHARE_REQUIRED');
    return this.api.listProfileShareDeliveries(grantId, 25, cursor);
  }

  listDeliveries(profileId: string, cursor?: string | null) {
    this.requireId(profileId, 'PARENT_PROFILE_REQUIRED');
    return this.api.listLessonDeliveries(profileId, cursor);
  }

  submitFeedback(lessonId: string, feedbackText: string, actionIdentity: string) {
    this.requireId(lessonId, 'LESSON_REQUIRED');
    const value = feedbackText.trim();
    const characterCount = Array.from(value).length;
    if (!characterCount || characterCount > 1200) {
      throw new ParentApplicationError('LESSON_FEEDBACK_INVALID', 'Phản hồi cần có nội dung, tối đa 1.200 ký tự.');
    }
    return this.api.submitLessonFeedback(lessonId, value, actionIdentity);
  }

  getLessonFeedback(lessonId: string) {
    this.requireId(lessonId, 'LESSON_REQUIRED');
    return this.api.getParentLessonFeedback(lessonId);
  }

  listLessonFeedbackReplies(lessonId: string, cursor?: string | null) {
    this.requireId(lessonId, 'LESSON_REQUIRED');
    return this.api.listParentLessonFeedbackReplies(lessonId, 25, cursor);
  }

  listNotifications(cursor?: string | null, limit?: number) {
    return this.api.listNotifications(cursor, limit);
  }

  markNotificationRead(notificationId: string, actionIdentity: string) {
    this.requireId(notificationId, 'NOTIFICATION_REQUIRED');
    return this.api.markNotificationRead(notificationId, actionIdentity);
  }

  markAllNotificationsRead(actionIdentity: string) {
    return this.api.markAllNotificationsRead(actionIdentity);
  }

  registerPushEndpointV1(input: PushEndpointRegistrationV1, actionIdentity: string) {
    return this.api.registerPushEndpointV1(input, actionIdentity);
  }

  deletePushEndpointV1(endpointId: string, expectedVersion: number, actionIdentity: string) {
    return this.api.deletePushEndpointV1(endpointId, expectedVersion, actionIdentity);
  }

  getVideoQuota() {
    return this.api.getVideoQuota();
  }

  getQuotaProducts() {
    return this.api.getQuotaProducts();
  }

  getQuotaInvoices(limit = 50) {
    return this.api.getQuotaInvoices(limit);
  }

  getQuotaPaymentSettings() {
    return this.api.getQuotaPaymentSettings();
  }

  checkoutQuotaProduct(productId: string, provider: ParentPaymentProvider, actionIdentity: string) {
    this.requireId(productId, 'QUOTA_PRODUCT_REQUIRED');
    return this.api.checkoutQuotaProduct(productId, provider, actionIdentity);
  }

  reconcileQuotaInvoice(invoiceId: string) {
    this.requireId(invoiceId, 'QUOTA_INVOICE_REQUIRED');
    return this.api.reconcileQuotaInvoice(invoiceId);
  }

  cancelQuotaInvoice(invoiceId: string) {
    this.requireId(invoiceId, 'QUOTA_INVOICE_REQUIRED');
    return this.api.cancelQuotaInvoice(invoiceId);
  }

  private requireId(value: string, code: string): void {
    if (!value.trim()) throw new ParentApplicationError(code, 'Thiếu thông tin cần thiết.');
  }
}
