import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { teacherProfileShareApi } from "../teacherProfileShareApi";

function response(body: unknown): Response {
  return { ok: true, status: 200, headers: new Headers({ ETag: '"1"' }), text: async () => JSON.stringify(body) } as Response;
}
function setup(replies: Response[]) {
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}
function call(fetcher: ReturnType<typeof setup>, index = 0) {
  const [url, init] = fetcher.mock.calls[index] as unknown as [string, RequestInit];
  return { url: new URL(url), init, headers: new Headers(init.headers), body: init.body ? JSON.parse(String(init.body)) as unknown : undefined };
}

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") } as never;
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); window.sketch2lifeAuth = undefined; window.sketch2lifeConfig = undefined; });

describe("Teacher parent profile share routes", () => {
  it("accepts a parent code with an idempotency key and no If-Match", async () => {
    const link = { contract: "Be1ParentShareLinkV1", share_grant_id: "grant-1", child_id: "child-1", state: "ACTIVE", granted_fields: ["DISPLAY_NAME"], accepted_at: "2026-11-25T00:00:00Z", expires_at: "2027-02-23T00:00:00Z", revision: 1 };
    const fetcher = setup([response(link)]);
    await teacherProfileShareApi.accept("org", "class", "child-1", "invite_code_123456", "accept-key");
    expect(call(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org/classes/class/profiles/child-1/parent-share/accept");
    expect(call(fetcher).headers.get("Idempotency-Key")).toBe("accept-key");
    expect(call(fetcher).headers.get("If-Match")).toBeNull();
    expect(call(fetcher).body).toEqual({ invitation_code: "invite_code_123456" });
  });

  it("reads only the granted parent fields and rejects unknown data", async () => {
    const shared = { contract: "Be1ParentSharedProfileV1", share_grant_id: "grant-1", child_id: "child-1", granted_fields: ["DISPLAY_NAME", "AGE_BAND"], expires_at: "2027-02-23T00:00:00Z", fields: { display_name: "Mầm", age_band: { band_ref: "72-107", band_version: 1 } } };
    const fetcher = setup([response(shared)]);
    await expect(teacherProfileShareApi.getSharedProfile("org", "class", "child-1")).resolves.toMatchObject({ fields: shared.fields });
    expect(call(fetcher).url.pathname.endsWith("/parent-share")).toBe(true);
    setup([response({ ...shared, fields: { ...shared.fields, support_needs: "private" } })]);
    await expect(teacherProfileShareApi.getSharedProfile("org", "class", "child-1")).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });
});
