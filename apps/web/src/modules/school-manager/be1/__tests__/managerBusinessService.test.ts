import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  adminApiRequest: vi.fn(),
  adminBe1Request: vi.fn(),
  adminOrganizationId: vi.fn(),
}));

vi.mock("../services/be1Client", () => mocks);

import { managerBusinessService } from "../services/managerBusinessService";

describe("School Manager business API adapter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.adminOrganizationId.mockReturnValue("org /qa");
    mocks.adminApiRequest.mockResolvedValue({});
    mocks.adminBe1Request.mockResolvedValue({});
  });

  it("reads the verified organization", async () => {
    await managerBusinessService.organization();
    expect(mocks.adminBe1Request).toHaveBeenCalledWith("/organizations/org%20%2Fqa", {});
  });

  it("reads the minimal class roster through the BE1 route", async () => {
    const signal = new AbortController().signal;
    await managerBusinessService.profiles("class/one", signal);
    expect(mocks.adminBe1Request).toHaveBeenCalledWith(
      "/organizations/org%20%2Fqa/classes/class%2Fone/profiles",
      { signal },
    );
  });

  it("reads consent status without exposing write operations", async () => {
    await managerBusinessService.consents("class-1");
    expect(mocks.adminBe1Request).toHaveBeenCalledWith(
      "/organizations/org%20%2Fqa/classes/class-1/consents",
      {},
    );
  });

  it("lists parent groups with an opaque cursor", async () => {
    await managerBusinessService.parentGroups("next page");
    expect(mocks.adminApiRequest).toHaveBeenCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups?cursor=next+page",
      {},
    );
  });

  it("lists the first page of parent groups without a query string", async () => {
    await managerBusinessService.parentGroups();
    expect(mocks.adminApiRequest).toHaveBeenCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups",
      {},
    );
  });

  it("never sends a page limit for parent groups", async () => {
    await managerBusinessService.parentGroups(undefined);
    await managerBusinessService.parentGroups("c");
    const paths = mocks.adminApiRequest.mock.calls.map((call) => String(call[0]));
    expect(paths).toHaveLength(2);
    paths.forEach((path) => expect(path).not.toContain("limit="));
  });

  it("creates a parent group only with explicit idempotency", async () => {
    await managerBusinessService.createParentGroup("Lớp Lá", "same-request-key");
    expect(mocks.adminApiRequest).toHaveBeenCalledWith(
      "/lesson-library/v1/organizations/org%20%2Fqa/parent-groups",
      {
        method: "POST",
        headers: { "Idempotency-Key": "same-request-key" },
        body: JSON.stringify({
          contract: "CreateParentGroupRequestV1",
          display_name: "Lớp Lá",
        }),
      },
    );
  });
});
