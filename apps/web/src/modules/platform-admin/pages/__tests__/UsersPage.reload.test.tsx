import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { UsersPage } from "../UsersPage";
import { PortalSessionProvider } from "../../../../shared/auth/PortalSessionContext";
import { backendApi } from "../../../../shared/api/backendApi";

beforeEach(() => {
  window.sketch2lifeConfig = { organizationId: "org-test" };
  window.sketch2lifeAuth = {
    signIn: vi.fn(async () => undefined),
    getIdToken: vi.fn(async () => "unit-test-id-token"),
    signOut: vi.fn(async () => undefined),
  };
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  delete window.sketch2lifeConfig;
  delete window.sketch2lifeAuth;
});

describe("Platform Admin accounts reload button", () => {
  it("reads the list again without reloading the page", async () => {
    const account = { account_id: "a-1", email: "a@example.test", display_name: "A", role: "parent" as const, state: "pending_verification" as const, revision: 1 };
    const list = vi.spyOn(backendApi, "listPlatformAccounts")
      .mockResolvedValueOnce({ items: [account], total: 1, limit: 25, next_cursor: null })
      .mockResolvedValue({ items: [{ ...account, state: "active" }], total: 1, limit: 25, next_cursor: null });
    render(<MemoryRouter><PortalSessionProvider><UsersPage /></PortalSessionProvider></MemoryRouter>);
    await screen.findByText("Chờ xác minh email", { selector: ".accounts-status" });

    fireEvent.click(screen.getByRole("button", { name: "Tải lại" }));
    await waitFor(() => expect(list).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Đang hoạt động", { selector: ".accounts-status" })).toBeTruthy();
  });
});
