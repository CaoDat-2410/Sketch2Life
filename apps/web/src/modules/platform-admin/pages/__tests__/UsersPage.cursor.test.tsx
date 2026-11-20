import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { UsersPage } from "../UsersPage";
import { PortalSessionProvider } from "../../../../shared/auth/PortalSessionContext";
import { backendApi } from "../../../../shared/api/backendApi";
import { keyForSignature } from "../../services/userService";
import * as adminService from "../../services/adminService";

type ListArgs = Parameters<typeof backendApi.listPlatformAccounts>[0];

const account = (index: number) => ({
  account_id: `account-${index}`,
  email: `user${index}@example.test`,
  display_name: `Người dùng ${index}`,
  role: "teacher" as const,
  state: "active" as const,
  revision: 1,
});

const pageOf = (from: number, count: number, next: string | null, total = 60) => ({
  items: Array.from({ length: count }, (_, offset) => account(from + offset)),
  total,
  limit: 25,
  offset: 0,
  next_cursor: next,
});

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

const renderPage = () => render(<MemoryRouter><PortalSessionProvider><UsersPage /></PortalSessionProvider></MemoryRouter>);

describe("Platform Admin accounts cursor paging (FEAT-066 C5)", () => {
  it("confirms the recipient before requesting a setup email and blocks disabled accounts", async () => {
    vi.spyOn(backendApi, 'listPlatformAccounts').mockResolvedValue({ ...pageOf(1, 1, null, 2), items: [account(1), { ...account(2), state: 'disabled' }] });
    const send = vi.fn(async () => ({ delivery_id: 'delivery-1', state: 'pending' }));
    vi.spyOn(adminService, 'commandClient').mockReturnValue(send as ReturnType<typeof adminService.commandClient>);
    renderPage();
    await screen.findByText('Người dùng 1');
    expect(screen.getAllByRole('button', { name: 'Gửi email thiết lập' })).toHaveLength(1);
    fireEvent.click(screen.getByRole('button', { name: 'Gửi email thiết lập' }));
    expect(screen.getByRole('dialog').textContent).toContain('user1@example.test');
    expect(send).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận gửi' }));
    await waitFor(() => expect(send).toHaveBeenCalledWith('/accounts/account-1/setup-email'));
    expect(await screen.findByText(/Đã đưa email thiết lập mật khẩu vào hàng đợi/)).toBeTruthy();
  });
  it("walks forward with next_cursor and back to the previous page start", async () => {
    const list = vi.spyOn(backendApi, "listPlatformAccounts").mockImplementation(async (filters: ListArgs = {}) => {
      if (filters.cursor === "c2") return pageOf(26, 25, "c3");
      if (filters.cursor === "c3") return pageOf(51, 10, null);
      return pageOf(1, 25, "c2");
    });
    renderPage();
    expect(await screen.findByText("Người dùng 1")).toBeTruthy();
    expect(screen.getByText("Trang 1 / 3")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Tiếp/ }));
    expect(await screen.findByText("Người dùng 26")).toBeTruthy();
    expect(screen.getByText("Trang 2 / 3")).toBeTruthy();
    expect(screen.getByText(/Đang hiển thị 26–50 trên 60/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Tiếp/ }));
    expect(await screen.findByText("Người dùng 51")).toBeTruthy();
    expect((screen.getByRole("button", { name: /Tiếp/ }) as HTMLButtonElement).disabled).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: /Trước/ }));
    expect(await screen.findByText("Người dùng 26")).toBeTruthy();
    expect(list.mock.calls.map(([filters]) => filters?.cursor)).toEqual([undefined, "c2", "c3", "c2"]);
    expect(list.mock.calls.every(([filters]) => filters?.limit === 25 && !("offset" in (filters ?? {})))).toBe(true);
  });

  it("resets to the first page when filters change", async () => {
    const list = vi.spyOn(backendApi, "listPlatformAccounts").mockImplementation(async (filters: ListArgs = {}) =>
      filters.cursor === "c2" ? pageOf(26, 25, null) : pageOf(1, 25, "c2"));
    renderPage();
    await screen.findByText("Người dùng 1");
    fireEvent.click(screen.getByRole("button", { name: /Tiếp/ }));
    await screen.findByText("Người dùng 26");
    fireEvent.change(screen.getByPlaceholderText("Email hoặc tên hiển thị"), { target: { value: "abc" } });
    fireEvent.click(screen.getByRole("button", { name: "Tìm tài khoản" }));
    await waitFor(() => expect(list).toHaveBeenLastCalledWith(expect.objectContaining({ search: "abc", cursor: undefined })));
  });

  it("reuses the key for a retried state change and replaces it after success", async () => {
    vi.spyOn(backendApi, "listPlatformAccounts").mockResolvedValue(pageOf(1, 1, null, 1));
    const update = vi.spyOn(backendApi, "updatePlatformAccount")
      .mockRejectedValueOnce(new Error("Mất kết nối"))
      .mockResolvedValue({ ...account(1), state: "disabled", revision: 2 });
    renderPage();
    await screen.findByText("Người dùng 1");
    fireEvent.click(screen.getByRole("button", { name: "Khóa tài khoản" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận" }));
    await waitFor(() => expect(update).toHaveBeenCalledTimes(1));
    await waitFor(() => expect((screen.getByRole("button", { name: "Xác nhận" }) as HTMLButtonElement).disabled).toBe(false));

    fireEvent.click(screen.getByRole("button", { name: "Xác nhận" }));
    await waitFor(() => expect(update).toHaveBeenCalledTimes(2));
    expect(update.mock.calls[1][2]).toBe(update.mock.calls[0][2]);
    expect(update.mock.calls[0][1]).toEqual({ state: "disabled" });
  });
});

describe("Platform Admin accounts after a change (FEAT-066 C5)", () => {
  it("reloads the current page from its own start cursor and uses a new key for the next change", async () => {
    let revision = 1;
    const list = vi.spyOn(backendApi, "listPlatformAccounts").mockImplementation(async (filters: ListArgs = {}) =>
      filters.cursor === "c2"
        ? { ...pageOf(26, 1, null, 26), items: [{ ...account(26), revision, state: revision % 2 ? "active" as const : "disabled" as const }] }
        : pageOf(1, 25, "c2", 26));
    const update = vi.spyOn(backendApi, "updatePlatformAccount").mockImplementation(async () => {
      revision += 1;
      return { ...account(26), revision };
    });
    renderPage();
    await screen.findByText("Người dùng 1");
    fireEvent.click(screen.getByRole("button", { name: /Tiếp/ }));
    await screen.findByText("Người dùng 26");
    fireEvent.click(screen.getByRole("button", { name: "Khóa tài khoản" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận" }));
    await waitFor(() => expect(update).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(list).toHaveBeenLastCalledWith(expect.objectContaining({ cursor: "c2" })));
    fireEvent.click(await screen.findByRole("button", { name: "Mở lại" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận" }));
    await waitFor(() => expect(update).toHaveBeenCalledTimes(2));
    expect(update.mock.calls[1][2]).not.toBe(update.mock.calls[0][2]);
  });
});

describe("backendApi account requests (FEAT-066 C5)", () => {
  it("sends cursor without offset and an Idempotency-Key on create and update", async () => {
    const seen: Array<{ url: string; key: string | null; revision: string | null }> = [];
    vi.stubGlobal("fetch", vi.fn(async (url: string, init: RequestInit) => {
      const headers = new Headers(init.headers);
      seen.push({ url, key: headers.get("Idempotency-Key"), revision: headers.get("If-Match") });
      return new Response(JSON.stringify(pageOf(1, 0, null, 0)), { status: 200, headers: { "Content-Type": "application/json" } });
    }));
    await backendApi.listPlatformAccounts({ limit: 25, cursor: "abc" });
    await backendApi.createPlatformAccount({ email: "a@example.test", display_name: "A", role: "teacher" }, "key-create");
    await backendApi.updatePlatformAccount("account-1", { state: "disabled" }, "key-update", 7);
    expect(seen[0].url).toContain("cursor=abc");
    expect(seen[0].url).toContain("limit=25");
    expect(seen[0].url).not.toContain("offset");
    expect(seen[1].key).toBe("key-create");
    expect(seen[2].key).toBe("key-update");
    expect(seen[2].revision).toBe('"7"');
    vi.unstubAllGlobals();
  });
});

describe("keyForSignature", () => {
  it("keeps one key per signature", () => {
    const store = new Map<string, string>();
    const first = keyForSignature(store, "a");
    expect(keyForSignature(store, "a")).toBe(first);
    expect(keyForSignature(store, "b")).not.toBe(first);
  });
});
