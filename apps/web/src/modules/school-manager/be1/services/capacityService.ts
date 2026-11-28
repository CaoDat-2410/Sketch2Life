import { parseApiError } from "../../../../shared/api/errorEnvelope";
import { AdminBe1Error } from "./be1Client";
import { authService } from "./authService";

export interface ScheduledCapacityChange {
  addon_slots: number;
  capacity: number;
  effective_at: string;
  suspend_class_refs: string[];
}

export interface Be1OrganizationCapacity {
  contract: "Be1OrganizationCapacityV1";
  organization_id: string;
  subscription_id: string | null;
  capacity: number;
  active_class_count: number;
  available_slots: number;
  subscription_state: string;
  revision: number;
  period_start: string | null;
  period_end: string | null;
  scheduled_change: ScheduledCapacityChange | null;
}

export type CapacityCommand =
  | { action: "cancel_renewal" | "resume_renewal" }
  | { action: "downgrade"; addon_slots: number; suspend_class_refs: string[] };

export interface CapacityResponse {
  data: Be1OrganizationCapacity;
  etag: string;
  revision: number;
}

export class CapacityServiceError extends AdminBe1Error {
  readonly current_version?: number;

  constructor(message: string, status: number, code: string, currentVersion?: number, requestId?: string, retryable = false) {
    super(message, status, code, requestId, retryable);
    this.name = "CapacityServiceError";
    this.current_version = currentVersion;
  }
}

type CapacityRequestResponse<T> = { data: T; etag: string | null };

async function requestCapacity<T>(path: string, init: RequestInit = {}): Promise<CapacityRequestResponse<T>> {
  const baseUrl = import.meta.env.VITE_BE1_BASE_URL?.trim();
  if (!baseUrl) throw new Error("BE1 is not configured.");

  const headers = new Headers(init.headers);
  headers.set("Authorization", "Bearer " + await authService.getIdToken());
  headers.set("Accept", "application/json");
  headers.set("X-Request-ID", crypto.randomUUID());
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  // This page needs the response ETag and current_version, which adminBe1Request does not expose.
  const response = await fetch(baseUrl.replace(/\/+$/, "") + "/api/be1/v1" + path, {
    ...init,
    headers,
    signal: init.signal ?? AbortSignal.timeout(15_000),
  });
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const parsed = parseApiError(body, response.status, response.headers.get("X-Request-ID"));
    throw new CapacityServiceError(
      parsed.message,
      response.status,
      parsed.code,
      parsed.currentVersion,
      parsed.requestId,
      parsed.retryable,
    );
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    throw new Error("BE1 returned an invalid capacity response.");
  }
  return { data: body as T, etag: response.headers.get("ETag") };
}

function organizationPath(organizationId: string): string {
  if (!organizationId.trim()) throw new CapacityServiceError("Organization is required.", 400, "INVALID_REQUEST");
  return "/organizations/" + encodeURIComponent(organizationId) + "/capacity";
}

function isCount(value: unknown, maximum = Number.MAX_SAFE_INTEGER): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 && value <= maximum;
}

function parseCapacity(value: unknown, organizationId: string): Be1OrganizationCapacity {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("BE1 returned an invalid capacity response.");
  }
  const item = value as Record<string, unknown>;
  const scheduled = item.scheduled_change;
  const scheduledRecord = scheduled && typeof scheduled === "object" && !Array.isArray(scheduled)
    ? scheduled as Record<string, unknown>
    : null;
  const suspendRefs = scheduledRecord?.suspend_class_refs;
  const validScheduled = scheduled === null || (
    !!scheduledRecord
    && isCount(scheduledRecord.addon_slots, 1000)
    && isCount(scheduledRecord.capacity, 1010)
    && typeof scheduledRecord.effective_at === "string"
    && Array.isArray(suspendRefs)
    && suspendRefs.length <= 1010
    && suspendRefs.every((ref: unknown) => typeof ref === "string")
  );
  if (
    item.contract !== "Be1OrganizationCapacityV1"
    || item.organization_id !== organizationId
    || !(item.subscription_id === null || typeof item.subscription_id === "string")
    || !isCount(item.capacity, 1010) || item.capacity < 10
    || !isCount(item.active_class_count)
    || !isCount(item.available_slots)
    || typeof item.subscription_state !== "string"
    || !isCount(item.revision)
    || !(item.period_start === null || typeof item.period_start === "string")
    || !(item.period_end === null || typeof item.period_end === "string")
    || !validScheduled
  ) {
    throw new Error("BE1 returned an invalid capacity response.");
  }
  return {
    contract: "Be1OrganizationCapacityV1",
    organization_id: item.organization_id,
    subscription_id: item.subscription_id,
    capacity: item.capacity,
    active_class_count: item.active_class_count,
    available_slots: item.available_slots,
    subscription_state: item.subscription_state,
    revision: item.revision,
    period_start: item.period_start,
    period_end: item.period_end,
    scheduled_change: scheduled === null ? null : {
      addon_slots: (scheduled as ScheduledCapacityChange).addon_slots,
      capacity: (scheduled as ScheduledCapacityChange).capacity,
      effective_at: (scheduled as ScheduledCapacityChange).effective_at,
      suspend_class_refs: [...(scheduled as ScheduledCapacityChange).suspend_class_refs],
    },
  };
}

function responseEtag(header: string | null, revision: number): string {
  const expected = '"' + revision + '"';
  if (header !== null && header !== expected) {
    throw new Error("BE1 returned an invalid capacity revision.");
  }
  return header ?? expected;
}

function validateCommand(body: CapacityCommand): void {
  if (body.action === "cancel_renewal" || body.action === "resume_renewal") {
    if (Object.keys(body).length !== 1 || Object.keys(body)[0] !== "action") {
      throw new CapacityServiceError("Capacity command is invalid.", 400, "INVALID_REQUEST");
    }
    return;
  }
  if (
    body.action !== "downgrade"
    || Object.keys(body).sort().join(",") !== "action,addon_slots,suspend_class_refs"
    || !isCount(body.addon_slots, 1000)
    || !Array.isArray(body.suspend_class_refs)
    || body.suspend_class_refs.length > 1010
    || !body.suspend_class_refs.every((ref) => typeof ref === "string")
  ) {
    throw new CapacityServiceError("Capacity command is invalid.", 400, "INVALID_REQUEST");
  }
}

export interface CapacityQuote {
  price_id: string; cycle_months: number; base_amount_vnd: number; slot_amount_vnd: number;
  quantity: number; current_addon_slots: number; resulting_capacity: number; period_start: string;
  period_end: string; remaining_time_ratio: string; amount_vnd: number; formula: string;
  quoted_at: string; momo_checkout_enabled: boolean; vnpay_checkout_enabled: boolean; synthetic_sandbox_price: true;
}
export interface CapacityPurchase {
  invoice_id: string; kind: "START" | "RENEW" | "ADDON"; state: string; provider: string; units: number; amount_vnd: number;
  created_at?: string | null; activated: boolean; attempts: { state: string; checkout_url: string | null; expires_at: string | null }[];
}
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Invalid capacity response");
  return value as Record<string, unknown>;
}
function parseQuote(value: unknown): CapacityQuote {
  const v = record(value);
  if (!["price_id", "period_start", "period_end", "remaining_time_ratio", "formula", "quoted_at"].every(k => typeof v[k] === "string")
    || !["cycle_months", "base_amount_vnd", "slot_amount_vnd", "quantity", "current_addon_slots", "resulting_capacity", "amount_vnd"].every(k => isCount(v[k]))
    || typeof v.momo_checkout_enabled !== "boolean" || typeof v.vnpay_checkout_enabled !== "boolean" || v.synthetic_sandbox_price !== true) throw new Error("Invalid capacity quote");
  return v as unknown as CapacityQuote;
}
function parsePurchase(value: unknown): CapacityPurchase {
  const v = record(value);
  if (typeof v.invoice_id !== "string" || (v.kind !== "START" && v.kind !== "RENEW" && v.kind !== "ADDON")
    || typeof v.state !== "string" || typeof v.provider !== "string"
    || !isCount(v.units) || !isCount(v.amount_vnd) || typeof v.activated !== "boolean" || !Array.isArray(v.attempts)) throw new Error("Invalid capacity purchase");
  for (const entry of v.attempts) {
    const a = record(entry);
    if (typeof a.state !== "string" || !(a.checkout_url === null || typeof a.checkout_url === "string") || !(a.expires_at === null || typeof a.expires_at === "string")) throw new Error("Invalid payment attempt");
  }
  return v as unknown as CapacityPurchase;
}
export function safeCapacityCheckoutUrl(value: string): string {
  const url = new URL(value);
  if (url.protocol !== "https:" || !url.hostname || url.username || url.password) throw new Error("Invalid checkout URL");
  return url.href;
}

export const capacityService = {
  quote: async (organizationId: string, quantity: number): Promise<CapacityQuote> => {
    if (!isCount(quantity, 1000) || quantity < 1) throw new CapacityServiceError("Invalid quantity", 400, "INVALID_REQUEST");
    const { data } = await requestCapacity<unknown>(organizationPath(organizationId) + "/quote?addon_slots=" + quantity);
    return parseQuote(data);
  },
  purchases: async (organizationId: string, invoiceId?: string): Promise<CapacityPurchase[]> => {
    const { data } = await requestCapacity<unknown>(organizationPath(organizationId) + "/purchases?limit=100" + (invoiceId ? "&invoice_id=" + encodeURIComponent(invoiceId) : ""));
    const v = record(data);
    if (!Array.isArray(v.items) || !isCount(v.total)) throw new Error("Invalid capacity purchases");
    return v.items.map(parsePurchase);
  },
  checkout: async (organizationId: string, quote: CapacityQuote, provider: "MOMO" | "VNPAY", key: string): Promise<{ state: string; checkout_url: string | null }> => {
    const quantity = quote.quantity;
    if (!isCount(quantity, 1000) || quantity < 1 || !/^[\x21-\x7E]{1,128}$/.test(key)) throw new CapacityServiceError("Invalid checkout", 400, "INVALID_REQUEST");
    const { data } = await requestCapacity<unknown>(organizationPath(organizationId) + "/checkout", {
      method: "POST", headers: { "Idempotency-Key": key }, body: JSON.stringify({ addon_slots: quantity, provider, expected_amount_vnd: quote.amount_vnd, price_id: quote.price_id, period_end: quote.period_end, quoted_at: quote.quoted_at }),
    });
    const v = record(data);
    if (typeof v.invoice_id !== "string" || typeof v.state !== "string" || !(v.checkout_url === null || typeof v.checkout_url === "string")) throw new Error("Invalid checkout response");
    return {
      state: v.state as string,
      checkout_url: v.state !== "PENDING" || v.checkout_url === null ? null : safeCapacityCheckoutUrl(v.checkout_url as string),
    };
  },
  purchaseAction: async (organizationId: string, invoiceId: string, action: "reconcile" | "cancel"): Promise<void> => {
    const { data } = await requestCapacity<unknown>(organizationPath(organizationId) + "/purchases/" + encodeURIComponent(invoiceId) + "/" + action, { method: "POST" });
    const v = record(data);
    if (v.invoice_id !== invoiceId || typeof v.state !== "string") throw new Error("Invalid purchase status");
  },
  getCapacity: async (organizationId: string, signal?: AbortSignal): Promise<CapacityResponse> => {
    const { data, etag } = await requestCapacity<unknown>(
      organizationPath(organizationId),
      {
        headers: { "Cache-Control": "private, no-store" },
        ...(signal ? { signal } : {}),
      },
    );
    const capacity = parseCapacity(data, organizationId);
    return {
      data: capacity,
      etag: responseEtag(etag, capacity.revision),
      revision: capacity.revision,
    };
  },

  configureCapacity: async (
    organizationId: string,
    revision: number,
    body: CapacityCommand,
    idempotencyKey: string,
  ): Promise<CapacityResponse> => {
    if (!isCount(revision)) throw new CapacityServiceError("Capacity revision is invalid.", 400, "INVALID_REQUEST");
    if (!/^[\x21-\x7E]{1,128}$/.test(idempotencyKey)) {
      throw new CapacityServiceError("Idempotency key is invalid.", 400, "INVALID_IDEMPOTENCY_KEY");
    }
    validateCommand(body);
    const { data, etag } = await requestCapacity<unknown>(
      organizationPath(organizationId),
      {
        method: "PATCH",
        headers: {
          "If-Match": '"' + revision + '"',
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify(body),
      },
    );
    const capacity = parseCapacity(data, organizationId);
    return {
      data: capacity,
      etag: responseEtag(etag, capacity.revision),
      revision: capacity.revision,
    };
  },
};
