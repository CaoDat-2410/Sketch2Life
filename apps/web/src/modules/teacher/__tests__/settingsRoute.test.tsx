import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
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

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Teacher settings route", () => {
  it("replaces the legacy settings route with the read-only profile", async () => {
    render(<MemoryRouter initialEntries={["/teacher/t08-settings"]}><TeacherPortalApp /></MemoryRouter>);

    expect(await screen.findByRole("heading", { name: "Hồ sơ cá nhân" })).toBeTruthy();
    const profileLink = screen.getByRole("link", { name: "Hồ sơ cá nhân" });
    expect(profileLink.getAttribute("href")).toBe("/teacher/t11-profile");
    expect(profileLink.getAttribute("aria-current")).toBe("page");
    expect(screen.queryByRole("link", { name: "Cài đặt" })).toBeNull();
    expect(TEACHER_NAVIGATION.flatMap((group) => group.items).some((item) => item.href === "/teacher/t08-settings")).toBe(false);
  });
});
