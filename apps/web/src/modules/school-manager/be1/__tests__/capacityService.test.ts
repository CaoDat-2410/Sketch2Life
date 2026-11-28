import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { authService } from "../services/authService";
import { capacityService, CapacityServiceError, type Be1OrganizationCapacity } from "../services/capacityService";

function capacity(overrides: Partial<Be1OrganizationCapacity> = {}): Be1OrganizationCapacity {
  return {
    contract: "Be1OrganizationCapacityV1",
    organization_id: "org/qa",
    subscription_id: "subscription-private",
    capacity: 20,
    active_class_count: 12,
    available_slots: 8,
    subscription_state: "ACTIVE",
    revision: 4,
    period_start: "2026-01-01T00:00:00Z",
    period_end: "2026-12-31T00:00:00Z",
    scheduled_change: null,
    ...overrides,
  };
}

function okResponse(body: unknown, etag = '"4"') {
  return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json", ETag: etag } });
}

function requestCall() {
  const fetchMock = vi.mocked(fetch);
  const [url, init] = fetchMock.mock.calls.at(-1) ?? [];
  return { url: String(url), init: init as RequestInit };
}

describe("capacityService", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_BE1_BASE_URL", "https://be1.example.test/");
    vi.spyOn(authService, "getIdToken").mockResolvedValue("test-token");
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("reads the organization capacity and returns the strong ETag and revision", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(okResponse(capacity()));

    const result = await capacityService.getCapacity("org/qa");
    const call = requestCall();
    const headers = new Headers(call.init.headers);

    expect(call.url).toBe("https://be1.example.test/api/be1/v1/organizations/org%2Fqa/capacity");
    expect(call.init.method).toBeUndefined();
    expect(headers.get("Authorization")).toBe("Bearer test-token");
    expect(headers.get("Accept")).toBe("application/json");
    expect(headers.get("Cache-Control")).toBe("private, no-store");
    expect(result).toEqual({ data: capacity(), etag: '"4"', revision: 4 });
  });

  it.each(["cancel_renewal", "resume_renewal"] as const)("sends %s with only the action field", async (action) => {
    const updated = capacity({ revision: 5 });
    vi.mocked(fetch).mockResolvedValueOnce(okResponse(updated, '"5"'));

    const result = await capacityService.configureCapacity("org/qa", 4, { action }, "action-key");
    const call = requestCall();
    const headers = new Headers(call.init.headers);

    expect(call.url).toBe("https://be1.example.test/api/be1/v1/organizations/org%2Fqa/capacity");
    expect(call.init.method).toBe("PATCH");
    expect(headers.get("If-Match")).toBe('"4"');
    expect(headers.get("Idempotency-Key")).toBe("action-key");
    expect(JSON.parse(String(call.init.body))).toEqual({ action });
    expect(result).toEqual({ data: updated, etag: '"5"', revision: 5 });
  });

  it("sends a downgrade with the exact selected references and required fields", async () => {
    const updated = capacity({
      capacity: 15,
      revision: 5,
      scheduled_change: {
        addon_slots: 5,
        capacity: 15,
        effective_at: "2026-12-31T00:00:00Z",
        suspend_class_refs: ["class-private"],
      },
    });
    vi.mocked(fetch).mockResolvedValueOnce(okResponse(updated, '"5"'));

    await capacityService.configureCapacity("org/qa", 4, {
      action: "downgrade",
      addon_slots: 5,
      suspend_class_refs: ["class-private"],
    }, "downgrade-key");
    const call = requestCall();
    const headers = new Headers(call.init.headers);

    expect(call.init.method).toBe("PATCH");
    expect(headers.get("If-Match")).toBe('"4"');
    expect(headers.get("Idempotency-Key")).toBe("downgrade-key");
    expect(JSON.parse(String(call.init.body))).toEqual({
      action: "downgrade",
      addon_slots: 5,
      suspend_class_refs: ["class-private"],
    });
  });

  it("preserves current_version on a typed stale revision error", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({
      code: "STALE_REVISION",
      message: "Please reload.",
      correlation_id: "request-private",
      current_version: 9,
    }), { status: 409, headers: { "Content-Type": "application/json" } }));

    await expect(capacityService.configureCapacity("org/qa", 4, { action: "resume_renewal" }, "action-key"))
      .rejects.toMatchObject<Partial<CapacityServiceError>>({
        code: "STALE_REVISION",
        status: 409,
        current_version: 9,
      });
  });

  it("rejects extra fields on renewal actions before making a request", async () => {
    const body = { action: "resume_renewal", addon_slots: 4 } as never;
    await expect(capacityService.configureCapacity("org/qa", 4, body, "action-key"))
      .rejects.toMatchObject({ code: "INVALID_REQUEST" });
    expect(fetch).not.toHaveBeenCalled();
  });
});


describe("capacity purchase responses", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_BE1_BASE_URL", "https://be1.example.test");
    vi.spyOn(authService, "getIdToken").mockResolvedValue("token");
    vi.stubGlobal("fetch", vi.fn());
  });
  afterEach(() => { vi.restoreAllMocks(); vi.unstubAllEnvs(); vi.unstubAllGlobals(); });
  it("sends the idempotency key and refuses an insecure checkout URL", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(okResponse({ invoice_id: "inv", state: "PENDING", checkout_url: "http://evil.test/" }));
    await expect(capacityService.checkout("org", { quantity: 2, amount_vnd: 5000, price_id: "price", period_end: "2026-12-31T00:00:00Z", quoted_at: "2026-06-01T00:00:00Z" } as Parameters<typeof capacityService.checkout>[1], "VNPAY", "same-key")).rejects.toThrow();
    expect(new Headers(requestCall().init.headers).get("Idempotency-Key")).toBe("same-key");
    expect(JSON.parse(String(requestCall().init.body))).toEqual({ addon_slots: 2, provider: "VNPAY", expected_amount_vnd: 5000, price_id: "price", period_end: "2026-12-31T00:00:00Z", quoted_at: "2026-06-01T00:00:00Z" });
  });
  it("rejects malformed purchase records", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(okResponse({ items: [{ invoice_id: "inv", kind: "ADDON", activated: "yes" }], total: 1 }));
    await expect(capacityService.purchases("org")).rejects.toThrow();
  });
  it("rejects an unrecognized purchase kind", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(okResponse({ items: [{
      invoice_id: "inv", kind: "OTHER", state: "PENDING", provider: "SANDBOX", units: 4,
      amount_vnd: 1000, activated: false, attempts: [],
    }], total: 1 }));
    await expect(capacityService.purchases("org")).rejects.toThrow();
  });
  it.each(["START", "RENEW", "ADDON"] as const)("accepts the declared purchase kind %s", async (kind) => {
    vi.mocked(fetch).mockResolvedValueOnce(okResponse({ items: [{
      invoice_id: "inv", kind, state: "PENDING", provider: "SANDBOX", units: 4,
      amount_vnd: 1000, activated: false, attempts: [],
    }], total: 1 }));
    await expect(capacityService.purchases("org")).resolves.toMatchObject([{ kind }]);
  });
  it("preserves a completed checkout state without following its URL", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(okResponse({ invoice_id: "inv", state: "PAID", checkout_url: "http://evil.test/" }));
    await expect(capacityService.checkout("org", { quantity: 2, amount_vnd: 5000, price_id: "price", period_end: "2026-12-31T00:00:00Z", quoted_at: "2026-06-01T00:00:00Z" } as Parameters<typeof capacityService.checkout>[1], "VNPAY", "key")).resolves.toEqual({ state: "PAID", checkout_url: null });
  });
});
