import { BackendApiError, apiBaseUrl, createIdempotencyKey } from "./backendApi";
import { parseApiError } from "./errorEnvelope";

export interface NotificationItem {
  contract: "NotificationV1";
  inbox_item_id: string;
  notification_type: string;
  template_version: number;
  safe_parameters: Record<string, boolean | number | string>;
  created_at: string;
  read_at: string | null;
  expires_at: string | null;
}

export interface NotificationPage {
  contract: "NotificationPageV1";
  items: NotificationItem[];
  next_cursor: string | null;
  unread_count: number;
}

export interface NotificationReadAll {
  contract: "NotificationReadAllV1";
  marked_count: number;
}

export const NOTIFICATIONS_PAGE_LIMIT = 25;
export const NOTIFICATIONS_TIMEOUT_MS = 15_000;

const visibleAscii = /^[\x21-\x7E]{1,128}$/;
export const NOTIFICATION_NOT_FOUND_MESSAGE = "Không tìm thấy nội dung hoặc bạn không có quyền truy cập.";

function keyedHeaders(key: string): Headers {
  if (!visibleAscii.test(key)) {
    throw new BackendApiError("Khóa yêu cầu không hợp lệ.", "INVALID_IDEMPOTENCY_KEY", 400);
  }
  const headers = new Headers({ "Idempotency-Key": key });
  return headers;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertContract<T extends { contract: string }>(body: unknown, expected: T["contract"]): T {
  if (!isRecord(body) || body.contract !== expected) {
    throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", 502);
  }
  return body as T;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  const requestId = headers.get("X-Request-ID") ?? createIdempotencyKey();
  headers.set("X-Request-ID", requestId);

  let token: string | null = null;
  try {
    token = await window.sketch2lifeAuth?.getIdToken() ?? null;
  } catch {
    token = null;
  }
  if (!token) {
    throw new BackendApiError("Phiên đăng nhập chưa sẵn sàng.", "AUTHENTICATION_REQUIRED", 401, requestId);
  }
  headers.set("Authorization", `Bearer ${token}`);
  if (init.body !== undefined && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  // One deadline for the whole exchange (headers and body), merged with the caller's abort signal.
  const controller = new AbortController();
  let timedOut = false;
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, NOTIFICATIONS_TIMEOUT_MS);
  const forwardAbort = () => controller.abort();
  if (init.signal?.aborted) controller.abort();
  else init.signal?.addEventListener("abort", forwardAbort, { once: true });
  const failed = (cause: unknown): never => {
    if (timedOut) throw new BackendApiError("Dịch vụ phản hồi quá lâu. Vui lòng thử lại.", "REQUEST_TIMEOUT", 0, requestId);
    if (cause instanceof Error && cause.name === "AbortError") throw cause;
    throw new BackendApiError("Không kết nối được dịch vụ.", "NETWORK_ERROR", 0, requestId);
  };

  try {
    let response: Response;
    try {
      response = await fetch(`${apiBaseUrl()}${path}`, { ...init, headers, signal: controller.signal });
    } catch (cause) {
      return failed(cause);
    }
    let text: string;
    try {
      text = await response.text();
    } catch (cause) {
      return failed(cause);
    }
    let body: unknown = null;
    if (text) {
      try {
        body = JSON.parse(text) as unknown;
      } catch {
        throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", response.status, response.headers.get("X-Request-ID") ?? requestId);
      }
    }
    if (!response.ok) {
      const parsed = parseApiError(body, response.status, response.headers.get("X-Request-ID") ?? requestId);
      const message = response.status === 404 || parsed.code === "RESOURCE_NOT_FOUND"
        ? NOTIFICATION_NOT_FOUND_MESSAGE
        : parsed.message;
      throw new BackendApiError(message, parsed.code, response.status, parsed.requestId);
    }
    return body as T;
  } finally {
    clearTimeout(timer);
    init.signal?.removeEventListener("abort", forwardAbort);
  }
}

function validateItem(item: unknown): NotificationItem {
  return assertContract<NotificationItem>(item, "NotificationV1");
}

function validateKey(key: string): void {
  keyedHeaders(key);
}

export async function listNotifications(
  options: { limit?: number; cursor?: string; signal?: AbortSignal } = {},
): Promise<NotificationPage> {
  const query = new URLSearchParams();
  query.set("limit", String(options.limit ?? NOTIFICATIONS_PAGE_LIMIT));
  if (options.cursor !== undefined) query.set("cursor", options.cursor);
  const page = assertContract<NotificationPage>(
    await request<unknown>(`/v1/notifications?${query.toString()}`, { signal: options.signal }),
    "NotificationPageV1",
  );
  if (!Array.isArray(page.items)) {
    throw new BackendApiError("Dịch vụ trả về dữ liệu không hợp lệ.", "INVALID_RESPONSE", 502);
  }
  return { ...page, items: page.items.map(validateItem) };
}

export async function markNotificationRead(inboxItemId: string, idempotencyKey: string): Promise<NotificationItem> {
  validateKey(idempotencyKey);
  const result = await request<unknown>(`/v1/notifications/${encodeURIComponent(inboxItemId)}/read`, {
    method: "POST",
    headers: keyedHeaders(idempotencyKey),
  });
  return validateItem(result);
}

export async function markAllNotificationsRead(idempotencyKey: string): Promise<NotificationReadAll> {
  validateKey(idempotencyKey);
  const result = await request<unknown>("/v1/notifications/read-all", {
    method: "POST",
    headers: keyedHeaders(idempotencyKey),
  });
  return assertContract<NotificationReadAll>(result, "NotificationReadAllV1");
}
