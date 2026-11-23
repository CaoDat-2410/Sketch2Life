import type {
  ParentNotification,
  ParentNotificationPage,
  ParentNotificationReadAllV1,
} from '../domain/types';

const notificationItemKeys = [
  'contract',
  'inbox_item_id',
  'notification_type',
  'template_version',
  'safe_parameters',
  'created_at',
  'read_at',
  'expires_at',
] as const;

const notificationPageKeys = ['contract', 'items', 'next_cursor', 'unread_count'] as const;
const notificationReadAllKeys = ['contract', 'marked_count'] as const;
const notificationIdPattern = /^[A-Za-z0-9._:-]{1,64}$/;
const notificationTypePattern = /^[A-Z][A-Z0-9_]{2,63}$/;
const safeParameterKeyPattern = /^[a-z][a-z0-9_]{0,31}$/;
const safeParameterValuePattern = /^[A-Za-z0-9_.:-]{1,64}$/;
const deniedParameterKeyPattern = /(name|child|story|transcript|media|url|email|token|endpoint|address)/i;

export function readNotificationV1(value: unknown): ParentNotification | null {
  if (!isRecord(value) || !hasExactKeys(value, notificationItemKeys)) return null;
  if (value.contract !== 'NotificationV1' || typeof value.inbox_item_id !== 'string'
    || !notificationIdPattern.test(value.inbox_item_id)) return null;
  if (typeof value.notification_type !== 'string' || !notificationTypePattern.test(value.notification_type)) return null;
  if (!isIntegerInRange(value.template_version, 1, 9999) || !isSafeParameters(value.safe_parameters)) return null;
  if (!isDateTime(value.created_at) || !isNullableDateTime(value.read_at) || !isNullableDateTime(value.expires_at)) return null;
  return {
    contract: 'NotificationV1',
    inbox_item_id: value.inbox_item_id,
    notification_type: value.notification_type,
    template_version: value.template_version,
    safe_parameters: value.safe_parameters as ParentNotification['safe_parameters'],
    created_at: value.created_at,
    read_at: value.read_at,
    expires_at: value.expires_at,
  };
}

export function readNotificationPageV1(value: unknown): ParentNotificationPage | null {
  if (!isRecord(value) || !hasExactKeys(value, notificationPageKeys)) return null;
  if (value.contract !== 'NotificationPageV1' || !Array.isArray(value.items)) return null;
  if (value.next_cursor !== null && typeof value.next_cursor !== 'string') return null;
  if (!isIntegerInRange(value.unread_count, 0, 100)) return null;
  const items = value.items.map(readNotificationV1);
  if (items.some((item) => item === null)) return null;
  return {
    contract: 'NotificationPageV1',
    items: items as ParentNotification[],
    next_cursor: value.next_cursor,
    unread_count: value.unread_count,
  };
}

export function readNotificationReadAllV1(value: unknown): ParentNotificationReadAllV1 | null {
  if (!isRecord(value) || !hasExactKeys(value, notificationReadAllKeys)) return null;
  if (value.contract !== 'NotificationReadAllV1' || !isIntegerInRange(value.marked_count, 0, Number.MAX_SAFE_INTEGER)) return null;
  return { contract: 'NotificationReadAllV1', marked_count: value.marked_count };
}

export type NotificationPageMerge = {
  items: ParentNotification[];
  nextCursor: string | null;
  unreadCount: number;
};

/** A null cursor replaces the inbox; a cursor appends without duplicates in server order. */
export function mergeNotificationPage(
  current: ParentNotification[],
  page: ParentNotificationPage,
  requestedCursor: string | null,
): NotificationPageMerge {
  if (requestedCursor === null) {
    return { items: page.items, nextCursor: page.next_cursor, unreadCount: page.unread_count };
  }
  const currentIds = new Set(current.map((item) => item.inbox_item_id));
  const latestById = new Map(current.map((item) => [item.inbox_item_id, item]));
  for (const item of page.items) latestById.set(item.inbox_item_id, item);
  const updatedCurrent = current.map((item) => latestById.get(item.inbox_item_id) as ParentNotification);
  const appended = page.items.filter((item) => !currentIds.has(item.inbox_item_id));
  return {
    items: [...updatedCurrent, ...appended],
    nextCursor: page.next_cursor === requestedCursor ? null : page.next_cursor,
    unreadCount: page.unread_count,
  };
}

export type NotificationReadUpdate = {
  items: ParentNotification[];
  unreadCount: number | null;
  shouldRefresh: boolean;
};

/** Keep the capped 100+ badge until the server provides a fresh count. */
export function applyNotificationRead(
  items: ParentNotification[],
  unreadCount: number | null,
  updated: ParentNotification,
): NotificationReadUpdate {
  const existing = items.find((item) => item.inbox_item_id === updated.inbox_item_id);
  if (!existing) return { items, unreadCount, shouldRefresh: true };
  const wasUnread = existing.read_at === null;
  const nextItems = items.map((item) => (
    item.inbox_item_id === updated.inbox_item_id ? updated : item
  ));
  const shouldRefresh = unreadCount === null || unreadCount === 100;
  const nextUnreadCount = unreadCount === null || unreadCount === 100
    ? unreadCount
    : Math.max(0, unreadCount - (wasUnread && updated.read_at !== null ? 1 : 0));
  return { items: nextItems, unreadCount: nextUnreadCount, shouldRefresh };
}

export type NotificationAction = 'read-one' | 'read-all';

export function notificationActionSignature(action: NotificationAction, inboxItemId?: string): string {
  return action === 'read-all' ? 'read-all' : 'read-one:' + (inboxItemId ?? '');
}

export function retainedNotificationActionKey(
  store: Map<string, string>,
  signature: string,
  createKey: () => string,
): string {
  const existing = store.get(signature);
  if (existing) return existing;
  const key = createKey();
  store.set(signature, key);
  return key;
}

export type NotificationActionOutcome = 'reload' | 'error';

export function notificationActionOutcome(code: string | undefined, status: number | undefined): NotificationActionOutcome {
  return status === 404 || code === 'RESOURCE_NOT_FOUND' ? 'reload' : 'error';
}

export type NotificationInboxViewState = 'unavailable' | 'loading' | 'error' | 'empty' | 'content';

export function classifyNotificationInbox(input: {
  available: boolean;
  loading: boolean;
  hasError: boolean;
  itemCount: number;
}): NotificationInboxViewState {
  if (!input.available) return 'unavailable';
  if (input.loading && input.itemCount === 0) return 'loading';
  if (input.hasError && input.itemCount === 0) return 'error';
  if (input.itemCount === 0) return 'empty';
  return 'content';
}

export function notificationUnreadCountLabel(count: number): string {
  return count === 100 ? '100+' : String(count);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Record<string, unknown>, keys: readonly string[]): boolean {
  const actual = Object.keys(value);
  return actual.length === keys.length && keys.every((key) => Object.prototype.hasOwnProperty.call(value, key));
}

function isSafeParameters(value: unknown): value is Record<string, boolean | number | string> {
  if (!isRecord(value) || Object.keys(value).length > 8) return false;
  return Object.entries(value).every(([key, entry]) => {
    if (!safeParameterKeyPattern.test(key) || deniedParameterKeyPattern.test(key)) return false;
    if (typeof entry === 'boolean') return true;
    if (typeof entry === 'number') return Number.isSafeInteger(entry);
    return typeof entry === 'string' && safeParameterValuePattern.test(entry);
  });
}

function isIntegerInRange(value: unknown, minimum: number, maximum: number): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= minimum && value <= maximum;
}

function isDateTime(value: unknown): value is string {
  return typeof value === 'string'
    && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)
    && Number.isFinite(Date.parse(value));
}

function isNullableDateTime(value: unknown): value is string | null {
  return value === null || isDateTime(value);
}
