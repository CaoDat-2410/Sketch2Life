import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import { getPreferences } from "../../../shared/api/accountPreferencesApi";
import { TEACHER_NAVIGATION } from "../../../shared/navigation/WebAppShell";
import { TeacherPortalApp } from "../App";

vi.mock("../../../shared/auth/PortalSessionContext", () => ({
  usePortalSession: () => ({
    currentRole: "TEACHER",
    isAuthenticated: true,
    toast: null,
    logout: vi.fn(),
  }),
}));

vi.mock("../../school-manager/be1/services/authService", () => ({
  authService: {
    observe: (callback: (user: null) => void) => { callback(null); return () => undefined; },
    changePassword: vi.fn(),
  },
}));

vi.mock("../../../shared/api/accountPreferencesApi", () => ({
  getPreferences: vi.fn(),
  updatePreferences: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Teacher settings route", () => {
  it("renders the shared settings page with a live navigation link", async () => {
    vi.mocked(getPreferences).mockResolvedValue({ locale: "vi-VN", email_notifications: true, revision: 1 });
    render(<MemoryRouter initialEntries={["/teacher/t08-settings"]}><TeacherPortalApp /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "Cài đặt" })).toBeTruthy();
    expect(screen.getByText("Thông báo cá nhân")).toBeTruthy();
    const settingsLink = screen.getByRole("link", { name: /^Cài đặt$/ });
    expect(settingsLink.getAttribute("href")).toBe("/teacher/t08-settings");
    expect(settingsLink.getAttribute("aria-current")).toBe("page");
    expect(settingsLink.textContent).not.toContain("Chờ API");
    expect(TEACHER_NAVIGATION.flatMap((group) => group.items).find((item) => item.href === "/teacher/t08-settings")?.state).toBe("available");
  });
});
