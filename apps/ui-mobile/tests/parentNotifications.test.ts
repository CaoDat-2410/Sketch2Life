import { describe, expect, it, vi } from 'vitest';
import {
  applyNotificationRead,
  classifyNotificationInbox,
  mergeNotificationPage,
  notificationActionOutcome,
  notificationActionSignature,
  notificationUnreadCountLabel,
  readNotificationPageV1,
  readNotificationReadAllV1,
  readNotificationV1,
  retainedNotificationActionKey,
} from '../src/parent/application/parentNotifications';
import type { ParentNotification, ParentNotificationPage } from '../src/parent/domain/types';
import { ParentApi, ParentApiError } from '../src/parent/infrastructure/http/ParentApi';
import { safeParentFlowErrorMessage } from '../src/parent/presentation/navigation/parentFlowV1';

vi.mock('../src/parent/infrastructure/config', () => ({
  parentConfig: { firebaseApiKey: 'synthetic-firebase-key', apiBaseUrl: 'https://parent.example.test' },
}));

const inboxItem = (overrides: Record<string, unknown> = {}) => ({
  contract: 'NotificationV1',
  inbox_item_id: 'notification-1',
  notification_type: 'LESSON_REPLY',
  template_version: 1,
  safe_parameters: { count: 2, opaque_ref: 'ref-1' },
  created_at: '2026-11-21T09:00:00Z',
  read_at: null,
  expires_at: null,
  ...overrides,
});

const page = (items: unknown[] = [inboxItem()], overrides: Record<string, unknown> = {}) => ({
  contract: 'NotificationPageV1',
  items,
  next_cursor: null,
  unread_count: 1,
  ...overrides,
});

function apiWith(fetcher: typeof fetch) {
  return new ParentApi({ getIdToken: vi.fn(async () => 'synthetic-token') }, fetcher, 'https://parent.example.test');
}

describe('NotificationV1 runtime readers', () => {
  it('accepts only the named contract fields and safe parameter values', () => {
    expect(readNotificationV1(inboxItem())).toMatchObject({
      contract: 'NotificationV1', inbox_item_id: 'notification-1', read_at: null,
    });
    expect(readNotificationPageV1(page())).toMatchObject({
      contract: 'NotificationPageV1', unread_count: 1, items: [{ inbox_item_id: 'notification-1' }],
    });
    expect(readNotificationReadAllV1({ contract: 'NotificationReadAllV1', marked_count: 3 })).toEqual({
      contract: 'NotificationReadAllV1', marked_count: 3,
    });
  });

  it('rejects extra fields, unsafe parameters, malformed timestamps and invalid counts', () => {
    expect(readNotificationV1({ ...inboxItem(), title: 'private text' })).toBeNull();
    expect(readNotificationV1(inboxItem({ safe_parameters: { child_name: 'Mia' } }))).toBeNull();
    expect(readNotificationV1(inboxItem({ created_at: 'not a date' }))).toBeNull();
    expect(readNotificationPageV1(page([], { unread_count: 101 }))).toBeNull();
    expect(readNotificationReadAllV1({ contract: 'NotificationReadAllV1', marked_count: -1 })).toBeNull();
  });
});

describe('Parent notification API routes', () => {
  it('GETs the first page with limit 25 and validates the response', async () => {
    const mockFetcher = vi.fn(async () => new Response(JSON.stringify(page()), { status: 200 }));
    const result = await apiWith(mockFetcher as unknown as typeof fetch).listNotifications();
    expect(result.items[0].inbox_item_id).toBe('notification-1');
    const [url, init] = mockFetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('https://parent.example.test/v1/notifications?limit=25');
    expect(init.method).toBe('GET');
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer synthetic-token');
    expect(new Headers(init.headers).get('Accept')).toBe('application/json');
    expect(new Headers(init.headers).has('Content-Type')).toBe(false);
    expect(init.body).toBeUndefined();
  });

  it('uses the requested 100 limit and cursor, and rejects invalid limits before fetch', async () => {
    const mockFetcher = vi.fn(async () => new Response(JSON.stringify(page([], { unread_count: 100 })), { status: 200 }));
    await apiWith(mockFetcher as unknown as typeof fetch).listNotifications('cursor / next', 100);
    const [url] = mockFetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('https://parent.example.test/v1/notifications?limit=100&cursor=cursor+%2F+next');
    const api = apiWith(mockFetcher as unknown as typeof fetch);
    await expect(api.listNotifications(null, 0)).rejects.toMatchObject({ code: 'INVALID_LIMIT', status: 400 });
    expect(mockFetcher).toHaveBeenCalledTimes(1);
  });

  it('rejects a malformed successful list response instead of showing an empty inbox', async () => {
    const mockFetcher = vi.fn(async () => new Response(JSON.stringify({ contract: 'NotificationPageV1', items: [] }), { status: 200 }));
    await expect(apiWith(mockFetcher as unknown as typeof fetch).listNotifications()).rejects.toMatchObject({ code: 'INVALID_API_RESPONSE', status: 200 });
    expect(mockFetcher).toHaveBeenCalledTimes(1);
  });

  it('POSTs one read with its key and no body or content type', async () => {
    const read = inboxItem({ read_at: '2026-11-21T10:00:00Z' });
    const mockFetcher = vi.fn(async () => new Response(JSON.stringify(read), { status: 200 }));
    const result = await apiWith(mockFetcher as unknown as typeof fetch).markNotificationRead('notification-1', 'action-key-1');
    expect(result.read_at).toBe('2026-11-21T10:00:00Z');
    const [url, init] = mockFetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('https://parent.example.test/v1/notifications/notification-1/read');
    expect(init.method).toBe('POST');
    expect(new Headers(init.headers).get('Idempotency-Key')).toBe('action-key-1');
    expect(new Headers(init.headers).has('Content-Type')).toBe(false);
    expect(init.body).toBeUndefined();
  });

  it('POSTs read-all with its key and validates the durable receipt', async () => {
    const mockFetcher = vi.fn(async () => new Response(JSON.stringify({ contract: 'NotificationReadAllV1', marked_count: 7 }), { status: 200 }));
    const receipt = await apiWith(mockFetcher as unknown as typeof fetch).markAllNotificationsRead('action-key-all');
    expect(receipt).toEqual({ contract: 'NotificationReadAllV1', marked_count: 7 });
    const [url, init] = mockFetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('https://parent.example.test/v1/notifications/read-all');
    expect(init.method).toBe('POST');
    expect(new Headers(init.headers).get('Idempotency-Key')).toBe('action-key-all');
    expect(new Headers(init.headers).has('Content-Type')).toBe(false);
    expect(init.body).toBeUndefined();
  });

  it('refuses invalid action keys and mismatched or unread read-one responses', async () => {
    const mockFetcher = vi.fn(async () => new Response(JSON.stringify(inboxItem()), { status: 200 }));
    const api = apiWith(mockFetcher as unknown as typeof fetch);
    for (const key of ['', 'k'.repeat(129), 'space in key', 'non-ascii-é']) {
      expect(() => api.markNotificationRead('notification-1', key)).toThrow(ParentApiError);
      expect(() => api.markAllNotificationsRead(key)).toThrow(ParentApiError);
    }
    await expect(api.markNotificationRead('notification-1', 'valid-key')).rejects.toMatchObject({ code: 'INVALID_API_RESPONSE' });
    expect(mockFetcher).toHaveBeenCalledTimes(1);
  });

  it('keeps a uniform 404 code and status without retaining or showing raw response data', async () => {
    const mockFetcher = vi.fn(async () => new Response(JSON.stringify({
      code: 'RESOURCE_NOT_FOUND', message: 'secret teacher-owned run payload', data: { child_name: 'private' },
    }), { status: 404 }));
    const api = apiWith(mockFetcher as unknown as typeof fetch);
    const operations = [
      () => api.listNotifications(),
      () => api.markNotificationRead('notification-1', 'read-key'),
      () => api.markAllNotificationsRead('read-all-key'),
    ];
    for (const operation of operations) {
      const error = await operation().catch((cause: unknown) => cause);
      expect(error).toBeInstanceOf(ParentApiError);
      expect(error).toMatchObject({ code: 'RESOURCE_NOT_FOUND', status: 404 });
      expect(safeParentFlowErrorMessage(error)).toBe('Không tìm thấy nội dung hoặc bạn không thể truy cập nội dung này.');
      expect(String(error)).not.toContain('secret teacher-owned run payload');
      expect(error).not.toHaveProperty('data');
      expect(error).not.toHaveProperty('body');
    }
    expect(mockFetcher).toHaveBeenCalledTimes(operations.length);
  });
});

describe('Notification inbox state and controller helpers', () => {
  it('classifies unavailable, loading, error, empty and content without inventing success', () => {
    expect(classifyNotificationInbox({ available: false, loading: false, hasError: false, itemCount: 0 })).toBe('unavailable');
    expect(classifyNotificationInbox({ available: true, loading: true, hasError: false, itemCount: 0 })).toBe('loading');
    expect(classifyNotificationInbox({ available: true, loading: false, hasError: true, itemCount: 0 })).toBe('error');
    expect(classifyNotificationInbox({ available: true, loading: false, hasError: false, itemCount: 0 })).toBe('empty');
    expect(classifyNotificationInbox({ available: true, loading: false, hasError: true, itemCount: 1 })).toBe('content');
  });

  it('merges cursor pages without duplicates and leaves capped unread counts until refresh', () => {
    const firstItem = readNotificationV1(inboxItem()) as ParentNotification;
    const secondItem = readNotificationV1(inboxItem({ inbox_item_id: 'notification-2' })) as ParentNotification;
    const firstPage = readNotificationPageV1(page([firstItem], { next_cursor: 'cursor-1', unread_count: 100 })) as ParentNotificationPage;
    const nextPage = readNotificationPageV1(page([firstItem, secondItem], { next_cursor: 'cursor-2', unread_count: 100 })) as ParentNotificationPage;
    const initial = mergeNotificationPage([], firstPage, null);
    const merged = mergeNotificationPage(initial.items, nextPage, 'cursor-1');
    expect(merged.items.map((item) => item.inbox_item_id)).toEqual(['notification-1', 'notification-2']);
    expect(merged.nextCursor).toBe('cursor-2');
    expect(merged.unreadCount).toBe(100);
    const updated = readNotificationV1(inboxItem({ read_at: '2026-11-21T10:00:00Z' })) as ParentNotification;
    expect(applyNotificationRead(merged.items, 100, updated)).toMatchObject({ unreadCount: 100, shouldRefresh: true });
    expect(notificationUnreadCountLabel(100)).toBe('100+');
  });

  it('retains one idempotency key per action signature and reloads stale 404 state', () => {
    const keys = new Map<string, string>();
    let created = 0;
    const create = () => `action-${++created}`;
    const one = notificationActionSignature('read-one', 'notification-1');
    const all = notificationActionSignature('read-all');
    expect(retainedNotificationActionKey(keys, one, create)).toBe('action-1');
    expect(retainedNotificationActionKey(keys, one, create)).toBe('action-1');
    expect(retainedNotificationActionKey(keys, all, create)).toBe('action-2');
    expect(notificationActionOutcome('RESOURCE_NOT_FOUND', 404)).toBe('reload');
    expect(notificationActionOutcome('NETWORK_ERROR', undefined)).toBe('error');
  });
});
