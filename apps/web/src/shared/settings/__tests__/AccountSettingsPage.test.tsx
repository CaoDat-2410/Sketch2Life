import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { BackendApiError } from "../../api/backendApi";
import { getPreferences, updatePreferences, type AccountPreferences } from "../../api/accountPreferencesApi";
import { AccountSettingsPage } from "../AccountSettingsPage";

vi.mock("../../api/accountPreferencesApi", () => ({
  getPreferences: vi.fn(),
  updatePreferences: vi.fn(),
}));

const initial: AccountPreferences = { locale: "vi-VN", email_notifications: true, revision: 4 };
const latest: AccountPreferences = { locale: "vi-VN", email_notifications: false, revision: 5 };

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

beforeEach(() => {
  vi.mocked(getPreferences).mockResolvedValue(initial);
  vi.mocked(updatePreferences).mockResolvedValue(latest);
});

async function chooseNotifications(enabled: boolean) {
  fireEvent.click(screen.getByRole("combobox", { name: "Thông báo qua email" }));
  fireEvent.click(await screen.findByRole("option", {
    name: enabled ? "Nhận thông báo" : "Tắt thông báo tùy chọn",
  }));
}

describe("AccountSettingsPage", () => {
  it("loads labelled preferences and keeps save disabled while unchanged", async () => {
    render(<AccountSettingsPage role="Teacher" />);

    expect(await screen.findByRole("heading", { name: "Cài đặt" })).toBeTruthy();
    expect(document.querySelector(".s2l-page-heading")).toBeTruthy();
    expect(screen.getByText("Thông báo cá nhân")).toBeTruthy();
    expect(screen.queryByText("Đã tải")).toBeNull();
    expect(screen.getByRole("combobox", { name: "Thông báo qua email" })).toBeTruthy();
    expect((screen.getByRole("button", { name: "Lưu tùy chọn" }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByText("Email bảo mật và thiết lập tài khoản vẫn được gửi.")).toBeTruthy();
  });

  it("saves the changed notification choice with the loaded locale and revision", async () => {
    render(<AccountSettingsPage role="Teacher" />);
    await screen.findByRole("heading", { name: "Cài đặt" });
    await chooseNotifications(false);
    fireEvent.click(screen.getByRole("button", { name: "Lưu tùy chọn" }));

    await screen.findByText("Đã lưu thay đổi.");
    expect(screen.getByText("Đã lưu")).toBeTruthy();
    expect(screen.queryByText("Đã tải")).toBeNull();
    expect(updatePreferences).toHaveBeenCalledWith({
      locale: "vi-VN",
      email_notifications: false,
      expected_revision: 4,
    });
    expect((screen.getByRole("button", { name: "Lưu tùy chọn" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("shows the conflict message and replaces the form with the latest revision", async () => {
    vi.mocked(getPreferences).mockResolvedValueOnce(initial).mockResolvedValueOnce(latest);
    vi.mocked(updatePreferences).mockRejectedValueOnce(new BackendApiError("Conflict", "RESOURCE_CONFLICT", 409, "pref-conflict"));
    render(<AccountSettingsPage role="School Manager" />);
    await screen.findByRole("heading", { name: "Cài đặt" });
    await chooseNotifications(false);
    fireEvent.click(screen.getByRole("button", { name: "Lưu tùy chọn" }));

    expect(await screen.findByText(/Dữ liệu đã thay đổi\. Tải lại trước khi thao tác tiếp\./)).toBeTruthy();
    await waitFor(() => expect(getPreferences).toHaveBeenCalledTimes(2));
    expect(screen.getByRole("combobox", { name: "Thông báo qua email" }).textContent).toContain("Tắt thông báo tùy chọn");
  });

  it("shows a load error and retries from Làm mới", async () => {
    vi.mocked(getPreferences).mockRejectedValueOnce(new BackendApiError("Provider unavailable", "PROVIDER_UNAVAILABLE", 503, "pref-load"));
    render(<AccountSettingsPage role="Teacher" />);

    expect((await screen.findByRole("alert")).textContent).toContain("Backend hoặc PostgreSQL hiện chưa sẵn sàng.");
    fireEvent.click(screen.getByRole("button", { name: "Làm mới" }));
    expect(await screen.findByRole("combobox", { name: "Thông báo qua email" })).toBeTruthy();
    expect(getPreferences).toHaveBeenCalledTimes(2);
  });

  it.each([
    [401, "AUTHENTICATION_REQUIRED", "Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Đăng nhập lại."],
    [403, "ACTION_NOT_ALLOWED", "Tài khoản này không có quyền xem hoặc sửa dữ liệu."],
  ])("shows the shared access error for HTTP %s", async (status, code, message) => {
    vi.mocked(getPreferences).mockRejectedValueOnce(new BackendApiError("Request denied", code, status, "pref-denied"));
    render(<AccountSettingsPage role="Teacher" />);

    expect((await screen.findByRole("alert")).textContent).toContain(message);
    expect(screen.getByRole("alert").textContent).toContain("pref-denied");
  });
});
