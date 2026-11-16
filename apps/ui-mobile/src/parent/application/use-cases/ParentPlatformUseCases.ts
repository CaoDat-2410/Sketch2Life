import type { ParentApiPort } from '../ports/ParentPorts';
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

  listShares(profileId: string) {
    this.requireId(profileId, 'PARENT_PROFILE_REQUIRED');
    return this.api.listProfileShares(profileId);
  }

  inviteTeacher(profileId: string, teacherSubject: string) {
    this.requireId(profileId, 'PARENT_PROFILE_REQUIRED');
    if (!teacherSubject.trim()) {
      throw new ParentApplicationError('TEACHER_ACCOUNT_REQUIRED', 'Nhập mã tài khoản giáo viên được mời.');
    }
    return this.api.createProfileShare(profileId, teacherSubject.trim());
  }

  revokeShare(profileId: string, grantId: string) {
    this.requireId(profileId, 'PARENT_PROFILE_REQUIRED');
    this.requireId(grantId, 'PROFILE_SHARE_REQUIRED');
    return this.api.revokeProfileShare(profileId, grantId);
  }

  listDeliveries(profileId: string, cursor?: string | null) {
    this.requireId(profileId, 'PARENT_PROFILE_REQUIRED');
    return this.api.listLessonDeliveries(profileId, cursor);
  }

  submitFeedback(occurrenceId: string, profileId: string, feedbackText: string) {
    this.requireId(occurrenceId, 'LESSON_DELIVERY_REQUIRED');
    this.requireId(profileId, 'PARENT_PROFILE_REQUIRED');
    const value = feedbackText.trim();
    if (!value || value.length > 1200) {
      throw new ParentApplicationError('LESSON_FEEDBACK_INVALID', 'Phản hồi cần có nội dung, tối đa 1.200 ký tự.');
    }
    return this.api.submitLessonFeedback(occurrenceId, profileId, value);
  }

  listNotifications(cursor?: string | null) {
    return this.api.listNotifications(cursor);
  }

  markNotificationRead(notificationId: string) {
    this.requireId(notificationId, 'NOTIFICATION_REQUIRED');
    return this.api.markNotificationRead(notificationId);
  }

  getVideoQuota() {
    return this.api.getVideoQuota();
  }

  private requireId(value: string, code: string): void {
    if (!value.trim()) throw new ParentApplicationError(code, 'Thiếu thông tin cần thiết.');
  }
}
