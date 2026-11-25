import { afterEach, describe, expect, it, vi } from "vitest";
import { teacherQuotaApi } from "../teacherQuotaApi";

afterEach(() => { vi.unstubAllGlobals(); window.sketch2lifeAuth = undefined; });

describe("Teacher quota API", () => {
  it("reads the organization-scoped personal allocation and accepts a null allocation", async () => {
    window.sketch2lifeAuth = { getIdToken: async () => "token" };
    const response = { allocation: null, organization_quota_owner: "ORGANIZATION" };
    const fetcher = vi.fn(async () => new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetcher);

    await expect(teacherQuotaApi.getMyVideoQuota("org /one")).resolves.toEqual(response);
    const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url.endsWith("/api/be1/v1/organizations/org%20%2Fone/video-quota/me")).toBe(true);
    expect(init.method ?? "GET").toBe("GET");
    expect(init.body).toBeUndefined();
    expect(new Headers(init.headers).has("Idempotency-Key")).toBe(false);
  });

  it("rejects a malformed allocation without exposing its fields", async () => {
    window.sketch2lifeAuth = { getIdToken: async () => "token" };
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ allocation: { secret: "do-not-show" }, organization_quota_owner: "ORGANIZATION" }), { status: 200 })));
    await expect(teacherQuotaApi.getMyVideoQuota("org-1")).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });
});
