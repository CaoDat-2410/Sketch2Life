import { afterEach, describe, expect, it, vi } from "vitest";
import { teacherRunApi } from "../teacherRunApi";

afterEach(() => { vi.unstubAllGlobals(); window.sketch2lifeAuth = undefined; });

describe("Teacher settled run deletion", () => {
  it("sends a keyed body-free DELETE and returns the 202 lifecycle envelope", async () => {
    window.sketch2lifeAuth = { getIdToken: async () => "token" };
    const envelope = { request_id: "request-1", lifecycle: { run_id: "run-1", run_state: "DELETE_PENDING", revision: 3, version: 1, lifecycle_request_ref: "request-ref", purge_state: "PENDING" } };
    const fetcher = vi.fn(async () => new Response(JSON.stringify(envelope), { status: 202 }));
    vi.stubGlobal("fetch", fetcher);

    await expect(teacherRunApi.delete("run/one", "delete-key")).resolves.toEqual(envelope);
    const [url, init] = fetcher.mock.calls[0] as unknown as [string, RequestInit];
    expect(url.endsWith("/v1/story-runs/run%2Fone")).toBe(true);
    expect(init.method).toBe("DELETE");
    expect(new Headers(init.headers).get("Idempotency-Key")).toBe("delete-key");
    expect(init.body).toBeUndefined();
  });
});
