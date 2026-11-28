import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BackendApiError } from "../backendApi";
import { fallbackMessage } from "../errorEnvelope";
import { teacherProfileApi } from "../teacherProfileApi";

function response(status: number, body?: unknown, headers: Record<string, string> = {}): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "response-1", ...headers }),
    text: async () => (body === undefined ? "" : JSON.stringify(body)),
  } as Response;
}

const envelope = (code: string, extra: Record<string, unknown> = {}) => ({
  code,
  message: "Server detail must not be shown by the support panel.",
  correlation_id: "corr-1",
  retryable: false,
  ...extra,
});

function setup(replies: Response[]) {
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

function call(fetcher: ReturnType<typeof setup>, index = 0) {
  const [url, init] = fetcher.mock.calls[index];
  return {
    url: new URL(url),
    init,
    headers: new Headers(init.headers),
    body: init.body ? JSON.parse(String(init.body)) as Record<string, unknown> : undefined,
  };
}

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-test" };
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") } as never;
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

describe("Teacher profile revision routes", () => {
  it("loads one 100-row page on demand and passes an opaque cursor unchanged", async () => {
    const cursor = "opaque /+?=cursor";
    const fetcher = setup([
      response(200, { contract: "Be1ProfileRevisionPageV1", items: [], next_cursor: cursor }),
      response(200, { contract: "Be1ProfileRevisionPageV1", items: [], next_cursor: null }),
    ]);
    await teacherProfileApi.listProfileRevisions("org/1", "class/2", "child/3");
    await teacherProfileApi.listProfileRevisions("org/1", "class/2", "child/3", cursor);

    expect(call(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org%2F1/classes/class%2F2/profiles/child%2F3/revisions");
    expect(call(fetcher).url.search).toBe("?limit=100");
    expect(call(fetcher, 1).url.searchParams.get("cursor")).toBe(cursor);
    expect(call(fetcher, 1).url.searchParams.get("limit")).toBe("100");
    expect(call(fetcher).init.method).toBe("GET");
    expect(call(fetcher).init.cache).toBe("no-store");
    expect(call(fetcher).headers.get("Authorization")).toBe("Bearer token-1");
  });

  it("reads one revision through its encoded route and disables cache", async () => {
    const revision = {
      contract: "Be1ProfileRevisionV1",
      child_id: "child-1",
      profile_revision_id: "rev/2",
      revision_no: 2,
      display_name: "Synthetic Test",
      age_months: 72,
      age_band: { band_version: 1, band_code: "AGE_72_107" },
      structured_interests: [],
      revision_hash: "abc",
      created_at: "2026-11-24T00:00:00Z",
    };
    const fetcher = setup([response(200, revision)]);
    await expect(teacherProfileApi.getProfileRevision("org", "class", "child", "rev/2")).resolves.toEqual(revision);
    expect(call(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org/classes/class/profiles/child/revisions/rev%2F2");
    expect(call(fetcher).init.method).toBe("GET");
    expect(call(fetcher).init.cache).toBe("no-store");
  });

  it("PATCHes only changed profile fields, includes expected_revision and one idempotency key", async () => {
    const result = { contract: "Be1ProfileEditResultV1", child_id: "child-1", profile_revision_id: "rev-4", revision_no: 4, revision_hash: "hash-4" };
    const fetcher = setup([response(200, result, { ETag: '"4"' })]);
    await teacherProfileApi.editProfile("org", "class", "child", { expected_revision: 3, age_months: 84 }, "key-123");
    expect(call(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org/classes/class/profiles/child");
    expect(call(fetcher).init.method).toBe("PATCH");
    expect(call(fetcher).headers.get("Idempotency-Key")).toBe("key-123");
    expect(call(fetcher).init.cache).toBe("no-store");
    expect(call(fetcher).body).toEqual({ expected_revision: 3, age_months: 84 });
    expect(call(fetcher).body).not.toHaveProperty("class_id");
  });

  it("refuses null, empty edits and malformed idempotency keys before fetch", async () => {
    const fetcher = setup([]);
    await expect(teacherProfileApi.editProfile("org", "class", "child", { expected_revision: 2 }, "key-1"))
      .rejects.toMatchObject({ code: "INVALID_REQUEST", status: 400 });
    await expect(teacherProfileApi.editProfile("org", "class", "child", { expected_revision: 2, display_name: null as never }, "key-1"))
      .rejects.toMatchObject({ code: "INVALID_REQUEST", status: 400 });
    await expect(teacherProfileApi.editProfile("org", "class", "child", { expected_revision: 2, age_months: 60 }, "bad key"))
      .rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY", status: 400 });
    expect(fetcher).not.toHaveBeenCalled();
  });
});

describe("Teacher support-needs routes", () => {
  it("reads support needs only from the profile path with cache disabled", async () => {
    const value = { contract: "Be1SupportNeedsV1", child_id: "child-1", revision: 2, category: "fixture category", note: "fixture note" };
    const fetcher = setup([response(200, value)]);
    await expect(teacherProfileApi.getSupportNeeds("org", "class", "child")).resolves.toEqual(value);
    expect(call(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org/classes/class/profiles/child/support-needs");
    expect(call(fetcher).init.method).toBe("GET");
    expect(call(fetcher).init.cache).toBe("no-store");
    expect(call(fetcher).url.search).toBe("");
  });

  it("PUTs both required nullable fields, expected_revision and the key, without class_id", async () => {
    const result = { contract: "Be1SupportNeedsWriteV1", child_id: "child-1", revision: 1 };
    const fetcher = setup([response(200, result)]);
    await teacherProfileApi.putSupportNeeds("org", "class", "child", {
      expected_revision: 0,
      category: "fixture category",
      note: null,
    }, "write-key-1");
    expect(call(fetcher).url.pathname).toBe("/api/be1/v1/organizations/org/classes/class/profiles/child/support-needs");
    expect(call(fetcher).init.method).toBe("PUT");
    expect(call(fetcher).headers.get("Idempotency-Key")).toBe("write-key-1");
    expect(call(fetcher).init.cache).toBe("no-store");
    expect(call(fetcher).body).toEqual({ expected_revision: 0, category: "fixture category", note: null });
    expect(call(fetcher).body).not.toHaveProperty("class_id");
  });

  it("preserves STALE_REVISION current_version and maps support unavailability safely", async () => {
    const fetcher = setup([
      response(409, envelope("STALE_REVISION", { current_version: 9 })),
      response(503, envelope("SUPPORT_NEEDS_UNAVAILABLE")),
    ]);
    const stale = await teacherProfileApi.putSupportNeeds("org", "class", "child", {
      expected_revision: 2, category: "fixture", note: null,
    }, "key-a").then(() => null, (cause: unknown) => cause as BackendApiError & { currentVersion?: number });
    expect(stale).toMatchObject({ code: "STALE_REVISION", currentVersion: 9 });
    const unavailable = await teacherProfileApi.getSupportNeeds("org", "class", "child").then(() => null, (cause: unknown) => cause as BackendApiError);
    expect(unavailable).toMatchObject({ code: "SUPPORT_NEEDS_UNAVAILABLE", status: 503, message: "Mục này chưa khả dụng." });
    expect(fallbackMessage("SUPPORT_NEEDS_UNAVAILABLE", 503)).toBe("Mục này chưa khả dụng.");
    expect(call(fetcher).headers.get("Idempotency-Key")).toBe("key-a");
  });

  it("keeps diagnosis field errors as field and code only", async () => {
    const fetcher = setup([response(400, envelope("INVALID_REQUEST", {
      field_errors: [{ field: "note", code: "DIAGNOSIS_LIKE", message: "fixture value must not be copied" }],
    }))]);
    await expect(teacherProfileApi.putSupportNeeds("org", "class", "child", {
      expected_revision: 0, category: null, note: "fixture value",
    }, "key-b")).rejects.toMatchObject({
      code: "INVALID_REQUEST",
      fieldErrors: [{ field: "note", code: "DIAGNOSIS_LIKE" }],
    });
    expect(call(fetcher).url.search).toBe("");
  });
});
