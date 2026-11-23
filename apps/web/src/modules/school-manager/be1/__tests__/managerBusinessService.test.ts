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

  it("reads the T-7a roster count summary through the BE1 route", async () => {
    const signal = new AbortController().signal;
    mocks.adminBe1Request.mockResolvedValueOnce({ contract: "Be1ClassRosterSummaryV1", class_id: "class/one", active_profile_count: 3 });
    await expect(managerBusinessService.rosterSummary("class/one", signal)).resolves.toEqual({
      contract: "Be1ClassRosterSummaryV1", class_id: "class/one", active_profile_count: 3,
    });
    expect(mocks.adminBe1Request).toHaveBeenCalledWith(
      "/organizations/org%20%2Fqa/classes/class%2Fone/profiles",
      { signal },
    );
  });

  it("refuses a Teacher-shaped roster body instead of passing child names to the Manager screen", async () => {
    mocks.adminBe1Request.mockResolvedValueOnce({
      contract: "Be1ManagedProfileListV1",
      items: [{ child_id: "c-1", class_id: "class-1", display_name: "Synthetic An", age_months: 60 }],
    });
    await expect(managerBusinessService.rosterSummary("class-1")).rejects.toThrow("không đúng contract");
  });

  it("reads every consent page and keeps only the Manager item fields", async () => {
    mocks.adminBe1Request
      .mockResolvedValueOnce({ contract: "Be1ConsentListManagerV1", items: [{ consent_id: "k-1", state: "PENDING", effective: false }], next_cursor: "cur 2" })
      .mockResolvedValueOnce({ contract: "Be1ConsentListManagerV1", items: [{ consent_id: "k-2", state: "ACTIVE", effective: false, child_id: "leak", purpose_ref: "leak" }], next_cursor: null });
    const items = await managerBusinessService.consents("class-1");
    expect(items).toEqual([
      { consent_id: "k-1", state: "PENDING", effective: false },
      { consent_id: "k-2", state: "ACTIVE", effective: false },
    ]);
    expect(mocks.adminBe1Request).toHaveBeenNthCalledWith(1, "/organizations/org%20%2Fqa/classes/class-1/consents?limit=100", {});
    expect(mocks.adminBe1Request).toHaveBeenNthCalledWith(2, "/organizations/org%20%2Fqa/classes/class-1/consents?limit=100&cursor=cur+2", {});
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
