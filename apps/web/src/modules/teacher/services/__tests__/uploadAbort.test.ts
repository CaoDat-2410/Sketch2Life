import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { abortKeyFor, abortUploadWithRevision } from "../uploadAbort";

const jsonResponse = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

const session = (state: string, revision: number) => ({
  contract: "UploadSessionV1",
  upload_session_id: "upload-1",
  state,
  part_size_bytes: 4194304,
  expected_parts: 2,
  accepted_part_numbers: [1],
  expires_at: "2026-11-20T00:00:00Z",
  revision,
});

const envelope = (code: string) => ({
  code,
  message: "Thông báo máy chủ.",
  correlation_id: "corr-1",
  retryable: false,
  request_id: "corr-1",
});

type Call = { method: string; headers: Headers };

function stubFetch(responses: Response[]): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal("fetch", vi.fn(async (_url: string, init: RequestInit) => {
    calls.push({ method: init.method ?? "GET", headers: new Headers(init.headers) });
    const next = responses.shift();
    if (!next) throw new Error("unexpected request");
    return next;
  }));
  return calls;
}

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-test" };
  window.sketch2lifeAuth = {
    signIn: vi.fn(async () => undefined),
    getIdToken: vi.fn(async () => "unit-test-id-token"),
    signOut: vi.fn(async () => undefined),
  };
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  delete window.sketch2lifeConfig;
  delete window.sketch2lifeAuth;
});

describe("abortKeyFor", () => {
  it("reuses the stored key only for the same revision", () => {
    expect(abortKeyFor({ abortKey: "k-2", abortRevision: 2 }, 2)).toBe("k-2");
    expect(abortKeyFor({ abortKey: "k-2", abortRevision: 2 }, 3)).not.toBe("k-2");
    expect(abortKeyFor(null, 2)).toBeTruthy();
  });
});

describe("abortUploadWithRevision", () => {
  it("reads the status first and sends its revision with a key", async () => {
    const calls = stubFetch([jsonResponse(session("OPEN", 2), 200), jsonResponse(session("ABORTED", 3), 202)]);
    const remembered: Array<[string, number]> = [];
    const outcome = await abortUploadWithRevision("upload-1", { remember: (key, revision) => remembered.push([key, revision]) });
    expect(outcome.kind).toBe("aborted");
    expect(calls[1].method).toBe("DELETE");
    expect(calls[1].headers.get("If-Match")).toBe('"2"');
    expect(calls[1].headers.get("Idempotency-Key")).toBe(remembered[0][0]);
    expect(remembered[0][1]).toBe(2);
  });

  it("uses the create response revision without a status read", async () => {
    const calls = stubFetch([jsonResponse(session("ABORTED", 2), 202)]);
    await abortUploadWithRevision("upload-1", { knownRevision: 1 });
    expect(calls).toHaveLength(1);
    expect(calls[0].headers.get("If-Match")).toBe('"1"');
  });

  it("retries once with a new key after a stale answer", async () => {
    const calls = stubFetch([
      jsonResponse(session("OPEN", 2), 200),
      jsonResponse(envelope("STALE_REVISION"), 409),
      jsonResponse(session("OPEN", 3), 200),
      jsonResponse(session("ABORTED", 4), 202),
    ]);
    const outcome = await abortUploadWithRevision("upload-1", { record: { abortKey: "old", abortRevision: 2 } });
    expect(outcome.kind).toBe("aborted");
    expect(calls[1].headers.get("Idempotency-Key")).toBe("old");
    expect(calls[3].headers.get("If-Match")).toBe('"3"');
    expect(calls[3].headers.get("Idempotency-Key")).not.toBe("old");
  });

  it("treats 410 and a state conflict as an already closed session", async () => {
    stubFetch([
      jsonResponse(session("OPEN", 2), 200),
      jsonResponse(envelope("UPLOAD_SESSION_EXPIRED"), 410),
      jsonResponse(session("EXPIRED", 3), 200),
    ]);
    expect((await abortUploadWithRevision("upload-1")).kind).toBe("closed");
    stubFetch([
      jsonResponse(session("OPEN", 2), 200),
      jsonResponse(envelope("UPLOAD_SESSION_STATE_CONFLICT"), 409),
      jsonResponse(session("FAILED", 3), 200),
    ]);
    expect((await abortUploadWithRevision("upload-1")).kind).toBe("closed");
  });

  it("reports a COMPLETED session so the caller recovers it instead of clearing", async () => {
    stubFetch([jsonResponse(session("COMPLETED", 4), 200)]);
    expect((await abortUploadWithRevision("upload-1")).kind).toBe("completed");
    stubFetch([
      jsonResponse(session("OPEN", 2), 200),
      jsonResponse(envelope("UPLOAD_SESSION_STATE_CONFLICT"), 409),
      jsonResponse(session("COMPLETED", 4), 200),
    ]);
    expect((await abortUploadWithRevision("upload-1")).kind).toBe("completed");
  });

  it("does not send a DELETE for a session that the status already shows closed", async () => {
    const calls = stubFetch([jsonResponse(session("FAILED", 3), 200)]);
    expect((await abortUploadWithRevision("upload-1")).kind).toBe("closed");
    expect(calls).toHaveLength(1);
  });
});
