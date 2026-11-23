import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { classService, type Be1CreatedClassResponse } from "../services/classService";

beforeEach(() => {
  vi.stubEnv("VITE_BE1_BASE_URL", "https://api.example.test");
  vi.stubEnv("VITE_BE1_ORGANIZATION_ID", "org-test");
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

async function stubFetch() {
  const calls: Array<{ url: string; init: RequestInit }> = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return new Response(
      JSON.stringify({ contract: "Be1ClassV1", class_id: "class-9", display_name: "Lớp Mầm", state: "active", assignment_revision: 1 }),
      { status: 201, headers: { "Content-Type": "application/json" } },
    );
  }));
  const { authService } = await import("../services/authService");
  vi.spyOn(authService, "getIdToken").mockResolvedValue("unit-test-id-token");
  return calls;
}

describe("classService.createClass Idempotency-Key", () => {
  it("sends a fresh key per action and types state and assignment_revision", async () => {
    const calls = await stubFetch();

    const first: Be1CreatedClassResponse = await classService.createClass("Lớp Mầm");
    await classService.createClass("Lớp Mầm");

    const key1 = new Headers(calls[0].init.headers).get("Idempotency-Key");
    const key2 = new Headers(calls[1].init.headers).get("Idempotency-Key");
    expect(key1).toBeTruthy();
    expect(key2).toBeTruthy();
    expect(key1).not.toBe(key2);
    expect(calls[0].url).toBe("https://api.example.test/api/be1/v1/organizations/org-test/classes");
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ display_name: "Lớp Mầm" });
    expect(first.state).toBe("active");
    expect(first.assignment_revision).toBe(1);
  });

  it("reuses the same key when the same action is retried", async () => {
    const calls = await stubFetch();

    await classService.createClass("Lớp Mầm", "action-key-1");
    await classService.createClass("Lớp Mầm", "action-key-1");

    expect(new Headers(calls[0].init.headers).get("Idempotency-Key")).toBe("action-key-1");
    expect(new Headers(calls[1].init.headers).get("Idempotency-Key")).toBe("action-key-1");
  });
});
