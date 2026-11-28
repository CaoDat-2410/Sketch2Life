import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { UsersPage } from "../UsersPage";
import { PortalSessionProvider } from "../../../../shared/auth/PortalSessionContext";
import { BackendApiError, backendApi } from "../../../../shared/api/backendApi";
import * as adminService from "../../services/adminService";

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

describe("Platform Admin account creation roles (SRS UC-13)", () => {
  it("does not offer Teacher when creating an account, but keeps it in the role filter", async () => {
    vi.spyOn(backendApi, "listPlatformAccounts").mockResolvedValue({
      items: [], total: 0, limit: 25, next_cursor: null,
    });
    vi.spyOn(adminService, "readAllPages").mockResolvedValue({ items: [], total: 0 });
    render(<MemoryRouter><PortalSessionProvider><UsersPage /></PortalSessionProvider></MemoryRouter>);
    await screen.findByText("Chưa có tài khoản");

    fireEvent.click(screen.getByRole("button", { name: "Tạo tài khoản" }));
    expect(screen.getByText(/Tài khoản giáo viên do Quản lý trường mời/)).toBeTruthy();
    fireEvent.click(screen.getByRole("combobox", { name: "Vai trò sản phẩm" }));
    expect(screen.getByRole("option", { name: "Quản lý trường" }).getAttribute("aria-selected")).toBe("true");
    expect(screen.queryByRole("option", { name: "Giáo viên" })).toBeNull();
    fireEvent.pointerDown(document.body);

    fireEvent.click(screen.getByRole("combobox", { name: "Lọc theo vai trò" }));
    expect(screen.getByRole("option", { name: "Giáo viên" })).toBeTruthy();
  });

  it("offers active schools only and explains the server's unavailable-school response", async () => {
    vi.spyOn(backendApi, "listPlatformAccounts").mockResolvedValue({
      items: [], total: 0, limit: 25, next_cursor: null,
    });
    vi.spyOn(adminService, "readAllPages").mockResolvedValue({ items: [
      { organization_id: "active-school", display_name: "Trường đang hoạt động", state: "ACTIVE", revision: 1 },
      { organization_id: "suspended-school", display_name: "Trường tạm ngưng", state: "suspended", revision: 1 },
    ], total: 2 });
    const createAccount = vi.spyOn(backendApi, "createPlatformAccount").mockRejectedValue(
      new BackendApiError("Yêu cầu chưa đáp ứng điều kiện nghiệp vụ.", "ORGANIZATION_UNAVAILABLE", 422),
    );
    render(<MemoryRouter><PortalSessionProvider><UsersPage /></PortalSessionProvider></MemoryRouter>);
    await screen.findByText("Chưa có tài khoản");
    fireEvent.click(screen.getByRole("button", { name: "Tạo tài khoản" }));

    const schoolChoice = screen.getByRole("combobox", { name: "Trường học cho tài khoản mới" });
    await waitFor(() => expect((schoolChoice as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(schoolChoice);
    expect(screen.queryByRole("option", { name: "Trường tạm ngưng" })).toBeNull();
    fireEvent.click(screen.getByRole("option", { name: "Trường đang hoạt động" }));
    fireEvent.change(screen.getByLabelText("Email tài khoản"), { target: { value: "manager@example.test" } });
    fireEvent.change(screen.getByLabelText("Tên hiển thị"), { target: { value: "Quản lý thử nghiệm" } });
    fireEvent.submit(screen.getByRole("heading", { name: "Tạo tài khoản" }).closest("form")!);

    expect(await screen.findByText("Trường được chọn không tồn tại hoặc không còn hoạt động. Hãy tải lại danh sách và chọn một trường đang hoạt động.")).toBeTruthy();
    expect(createAccount).toHaveBeenCalledWith(
      { email: "manager@example.test", display_name: "Quản lý thử nghiệm", role: "school_manager", organization_id: "active-school" },
      expect.any(String),
    );
  });

  it("explains when the organization list has no active school", async () => {
    vi.spyOn(backendApi, "listPlatformAccounts").mockResolvedValue({
      items: [], total: 0, limit: 25, next_cursor: null,
    });
    vi.spyOn(adminService, "readAllPages").mockResolvedValue({ items: [
      { organization_id: "suspended-school", display_name: "Trường tạm ngưng", state: "suspended", revision: 1 },
    ], total: 1 });
    render(<MemoryRouter><PortalSessionProvider><UsersPage /></PortalSessionProvider></MemoryRouter>);
    await screen.findByText("Chưa có tài khoản");
    fireEvent.click(screen.getByRole("button", { name: "Tạo tài khoản" }));

    expect(await screen.findByText(/Hiện không có trường nào ở trạng thái đang hoạt động/)).toBeTruthy();
    expect((screen.getByRole("combobox", { name: "Trường học cho tài khoản mới" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
