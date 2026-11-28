import { afterEach, describe, expect, it, vi } from "vitest";
import { BackendApiError } from "../backendApi";
import {
  createPrivateShare,
  PRIVATE_SHARE_GROUP_STATE_MESSAGE,
  PRIVATE_SHARE_NOT_FOUND_MESSAGE,
  PRIVATE_SHARE_VALIDATION_MESSAGE,
  PRIVATE_SHARE_REVOKE_REQUEST_MESSAGE,
  PRIVATE_SHARE_REVOKE_STALE_MESSAGE,
  StaleAccessGrantRevisionError,
  type PrivateShareAudience,
  type PrivateShareInput,
  revokeAccessGrant,
} from "../lessonSharingApi";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

function response(status: number, body?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "response-1" }),
    text: async () => body === undefined ? "" : JSON.stringify(body),
  } as Response;
}

function setup(replies: Response[]) {
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "token-1") };
  const fetcher = vi.fn(async (..._args: [string, RequestInit]) => replies.shift()!);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

function input(audienceKind: PrivateShareAudience): PrivateShareInput {
  return {
    lessonId: "lesson /1",
    versionId: "version-2",
    audienceKind,
    audienceRef: "audience-3",
    capability: "VIEW",
    expiresAt: null,
  };
}

function grant(audienceKind: string) {
  return {
    contract: "LessonAccessGrantV1",
    access_grant_id: "grant-1",
    lesson_id: "lesson /1",
    version_id: "version-2",
    audience_kind: audienceKind,
    audience_ref: "audience-3",
    capability: "VIEW",
    state: "ACTIVE",
    granted_by: "principal-1",
    approved_by: null,
    approved_at: null,
    expires_at: null,
    revoked_at: null,
    revision: 1,
  };
}

function request(fetcher: ReturnType<typeof setup>, index = 0) {
  const [url, init] = fetcher.mock.calls[index];
  return { url, init, headers: new Headers(init.headers), body: init.body === undefined ? undefined : JSON.parse(String(init.body)) as Record<string, unknown> };
}

describe("private lesson sharing API", () => {
  it.each(["ORGANIZATION", "PRINCIPAL", "PARENT_GROUP"] as const)("sends the %s audience request without If-Match", async (audienceKind) => {
    const fetcher = setup([response(201, grant(audienceKind))]);

    await createPrivateShare("org /1", input(audienceKind), "share-key-1");

    const sent = request(fetcher);
    expect(new URL(sent.url).pathname).toBe("/api/lesson-library/v1/organizations/org%20%2F1/lessons/lesson%20%2F1/access-grants");
    expect(sent.init.method).toBe("POST");
    expect(sent.headers.get("Idempotency-Key")).toBe("share-key-1");
    expect(sent.headers.get("Authorization")).toBe("Bearer token-1");
    expect(sent.headers.get("If-Match")).toBeNull();
    expect(sent.body).toEqual({
      contract: "CreateLessonAccessGrantRequestV1",
      version_id: "version-2",
      audience_kind: audienceKind,
      audience_ref: "audience-3",
      capability: "VIEW",
      expires_at: null,
    });
  });

  it("excludes PUBLIC from the audience type", () => {
    // @ts-expect-error PUBLIC uses requestPublicReview and is not a private-share audience.
    const publicAudience: PrivateShareAudience = "PUBLIC";
    expect(publicAudience).toBe("PUBLIC");
  });

  it("rejects PUBLIC at runtime and validates visible-ASCII idempotency keys", async () => {
    const fetcher = setup([]);
    const publicInput = { ...input("ORGANIZATION"), audienceKind: "PUBLIC" } as unknown as PrivateShareInput;

    await expect(createPrivateShare("org-1", publicInput, "key-1")).rejects.toMatchObject({ code: "INVALID_REQUEST" });
    await expect(createPrivateShare("org-1", input("ORGANIZATION"), "bad key")).rejects.toMatchObject({ code: "INVALID_IDEMPOTENCY_KEY" });
    expect(fetcher).not.toHaveBeenCalled();
  });

  it("uses uniform 404 text, no-special-case PUBLICATION_REQUIRED, group-state 409 and 422 copy", async () => {
    const fetcher = setup([
      response(404, { detail: { code: "RESOURCE_NOT_FOUND" } }),
      response(409, { detail: { code: "PUBLICATION_REQUIRED" } }),
      response(409, { detail: { code: "INVALID_TRANSITION" } }),
      response(409, { detail: { code: "INVALID_STATE_TRANSITION" } }),
      response(422, { detail: { code: "INVALID_REQUEST" } }),
      response(409, { detail: { code: "INVALID_TRANSITION" } }),
    ]);

    await expect(createPrivateShare("org-1", input("ORGANIZATION"), "key-1"))
      .rejects.toMatchObject({ status: 404, message: PRIVATE_SHARE_NOT_FOUND_MESSAGE });
    const stale = await createPrivateShare("org-1", input("ORGANIZATION"), "key-2").catch((cause: unknown) => cause);
    expect(stale).toBeInstanceOf(BackendApiError);
    expect(stale).toMatchObject({ status: 409, code: "PUBLICATION_REQUIRED" });
    expect((stale as BackendApiError).message).not.toContain("PUBLICATION_REQUIRED");
    await expect(createPrivateShare("org-1", input("PARENT_GROUP"), "key-3"))
      .rejects.toMatchObject({ status: 409, message: PRIVATE_SHARE_GROUP_STATE_MESSAGE });
    await expect(createPrivateShare("org-1", input("PARENT_GROUP"), "key-4"))
      .rejects.toMatchObject({ status: 409, message: PRIVATE_SHARE_GROUP_STATE_MESSAGE });
    await expect(createPrivateShare("org-1", input("PRINCIPAL"), "key-5"))
      .rejects.toMatchObject({ status: 422, message: PRIVATE_SHARE_VALIDATION_MESSAGE });
    // The group-state copy is only for a group audience: another audience keeps the generic 409 text.
    const other = await createPrivateShare("org-1", input("PRINCIPAL"), "key-6").catch((cause: unknown) => cause);
    expect((other as BackendApiError).message).not.toBe(PRIVATE_SHARE_GROUP_STATE_MESSAGE);
    expect(fetcher).toHaveBeenCalledTimes(6);
  });

  it("revokes with the quoted revision and action key, then parses the returned grant", async () => {
    const revoked = { ...grant("ORGANIZATION"), state: "REVOKED", revision: 2 };
    const fetcher = setup([response(200, revoked)]);

    await expect(revokeAccessGrant("org /1", "lesson /1", "grant /1", 1, "revoke-key-1")).resolves.toEqual(revoked);

    const sent = request(fetcher);
    expect(new URL(sent.url).pathname).toBe("/api/lesson-library/v1/organizations/org%20%2F1/lessons/lesson%20%2F1/access-grants/grant%20%2F1");
    expect(sent.init.method).toBe("DELETE");
    expect(sent.headers.get("If-Match")).toBe('"1"');
    expect(sent.headers.get("Idempotency-Key")).toBe("revoke-key-1");
    expect(sent.headers.get("Authorization")).toBe("Bearer token-1");
    expect(sent.init.body).toBeUndefined();
  });

  it("maps stale revoke revisions and preserves the current version for a retry", async () => {
    setup([response(409, { detail: { code: "STALE_REVISION", current_version: 7 } })]);

    const error = await revokeAccessGrant("org-1", "lesson-1", "grant-1", 2, "revoke-key-2").catch((cause: unknown) => cause);

    expect(error).toBeInstanceOf(StaleAccessGrantRevisionError);
    expect(error).toMatchObject({ status: 409, code: "STALE_REVISION", currentVersion: 7, message: PRIVATE_SHARE_REVOKE_STALE_MESSAGE });
    expect((error as BackendApiError).message).not.toContain("STALE_REVISION");
  });

  it("maps missing grants uniformly and gives bad If-Match requests safe Vietnamese copy", async () => {
    const fetcher = setup([
      response(404, { detail: { code: "RESOURCE_NOT_FOUND" } }),
      response(400, { detail: { code: "INVALID_IF_MATCH" } }),
    ]);

    await expect(revokeAccessGrant("org-1", "lesson-1", "grant-1", 1, "revoke-key-3"))
      .rejects.toMatchObject({ status: 404, message: PRIVATE_SHARE_NOT_FOUND_MESSAGE });
    await expect(revokeAccessGrant("org-1", "lesson-1", "grant-1", 0, "revoke-key-4"))
      .rejects.toMatchObject({ status: 400, message: PRIVATE_SHARE_REVOKE_REQUEST_MESSAGE });
    await expect(revokeAccessGrant("org-1", "lesson-1", "grant-1", 1, "revoke-key-5"))
      .rejects.toMatchObject({ status: 400, message: PRIVATE_SHARE_REVOKE_REQUEST_MESSAGE });
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
});
