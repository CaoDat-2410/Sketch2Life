import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import {
  applyNotificationRead,
  notificationCopyForType,
  readNotificationV1,
} from '../src/parent/application/parentNotifications';
import type { ParentNotification } from '../src/parent/domain/types';

const reminderPayload = {
  contract: 'NotificationV1',
  inbox_item_id: 'reminder-1',
  notification_type: 'RUN_WAIT_REMINDER',
  template_version: 1,
  safe_parameters: {},
  created_at: '2026-11-25T09:00:00Z',
  read_at: null,
  expires_at: null,
};

describe('Parent run-wait reminder', () => {
  it('renders safe Vietnamese copy, a history action, and the generic fallback for unknown types', () => {
    const reminderCopy = notificationCopyForType('RUN_WAIT_REMINDER');
    expect(reminderCopy).toEqual({
      title: 'Một câu chuyện đang chờ bạn',
      body: 'Khi thuận tiện, bạn có thể quay lại buổi học để tiếp tục bước tiếp theo.',
      action: 'story-history',
      actionLabel: 'Xem lịch sử buổi học',
    });
    expect(notificationCopyForType('FUTURE_NOTIFICATION')).toEqual({
      title: 'Bạn có một cập nhật mới trong ứng dụng.',
      body: null,
      action: null,
      actionLabel: null,
    });

    const screen = readFileSync(new URL('../src/parent/presentation/screens/NotificationsScreen.tsx', import.meta.url), 'utf8');
    const app = readFileSync(new URL('../src/parent/presentation/ParentExpoApp.tsx', import.meta.url), 'utf8');
    expect(screen).toContain('notificationCopyForType(item.notification_type)');
    expect(screen).toContain('{copy.title}');
    expect(screen).toContain('{copy.body}');
    expect(screen).toContain("copy.action === 'story-history'");
    expect(screen).toContain('onPress={onOpenStoryHistory}');
    expect(app).toContain("onOpenStoryHistory={() => openHistory('profile')}");
    expect(screen).toContain('onMarkRead(item.inbox_item_id)');
    expect(screen).not.toContain('safe_parameters');
  });

  it('keeps reminder read state working and never turns unknown parameters into UI copy', () => {
    const reminder = readNotificationV1(reminderPayload) as ParentNotification;
    const updatedReminder = { ...reminder, read_at: '2026-11-25T09:05:00Z' };
    expect(applyNotificationRead([reminder], 1, updatedReminder)).toMatchObject({
      items: [{ notification_type: 'RUN_WAIT_REMINDER', read_at: '2026-11-25T09:05:00Z' }],
      unreadCount: 0,
      shouldRefresh: false,
    });

    const opaqueValue = 'PRIVATE_PARAMETER_SENTINEL';
    const unknownItem = readNotificationV1({
      ...reminderPayload,
      notification_type: 'FUTURE_NOTIFICATION',
      safe_parameters: { opaque_ref: opaqueValue },
    }) as ParentNotification;
    const copy = notificationCopyForType(unknownItem.notification_type);
    expect(Object.values(copy).join(' ')).not.toContain(opaqueValue);
    expect(Object.values(copy).join(' ')).not.toContain('RUN_WAIT_REMINDER');
    expect(Object.values(copy).join(' ')).not.toContain('VIDEO_QUOTA_EXCEEDED');
  });
});
