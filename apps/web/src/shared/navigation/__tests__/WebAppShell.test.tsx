import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  PLATFORM_ADMIN_NAVIGATION,
  SCHOOL_MANAGER_NAVIGATION,
  TEACHER_NAVIGATION,
  WebAppShell,
} from "../WebAppShell";

vi.mock("../../../modules/school-manager/be1/services/authService", () => ({
  authService: {
    observe: () => () => undefined,
    changePassword: vi.fn(),
  },
}));

afterEach(cleanup);

function renderPlatformShell(initialPath = "/platform/a02-platform-operations") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <WebAppShell
        portal="platform"
        roleLabel="Platform Admin"
        roleSubtitle=""
        navigation={PLATFORM_ADMIN_NAVIGATION}
        loginHref="/login"
        modeLabel=""
        onLogout={() => undefined}
      >
        <main>Page content</main>
      </WebAppShell>
    </MemoryRouter>,
  );
}

function renderRoleShell(roleLabel: string, navigation: typeof TEACHER_NAVIGATION, portal: "teacher" | "manager", initialPath: string) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <WebAppShell
        portal={portal}
        roleLabel={roleLabel}
        roleSubtitle=""
        navigation={navigation}
        loginHref="/login"
        modeLabel=""
        onLogout={() => undefined}
      >
        <main>Page content</main>
      </WebAppShell>
    </MemoryRouter>,
  );
}

describe("Platform Admin navigation groups", () => {
  it("connects each native toggle to its list and keeps the active group open", () => {
    renderPlatformShell("/platform/accounts");
    const groupToggle = screen.getByRole("button", { name: "Quản lý" });
    const groupId = groupToggle.getAttribute("aria-controls");

    expect(groupToggle.tagName).toBe("BUTTON");
    expect(groupId).toBeTruthy();
    expect(groupToggle.getAttribute("aria-expanded")).toBe("true");
    const groupContent = document.getElementById(groupId ?? "");
    expect(groupContent).toBeTruthy();
    expect(groupContent?.hasAttribute("hidden")).toBe(false);

    fireEvent.click(groupToggle);
    expect(groupToggle.getAttribute("aria-expanded")).toBe("true");
  });

  it("keeps a non-active group preference when navigating to another page", () => {
    renderPlatformShell();
    const financeToggle = screen.getByRole("button", { name: "Tài chính & hạn mức" });
    fireEvent.click(financeToggle);
    expect(financeToggle.getAttribute("aria-expanded")).toBe("true");

    fireEvent.click(screen.getByRole("link", { name: "Tài khoản & vai trò" }));
    expect(screen.getByRole("link", { name: "Tài khoản & vai trò" }).getAttribute("aria-current")).toBe("page");
    expect(screen.getByRole("button", { name: "Tài chính & hạn mức" }).getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("button", { name: "Quản lý" }).getAttribute("aria-expanded")).toBe("true");
  });
});

describe("cozy role shell", () => {
  it("uses the approved logo chip in all three authenticated portals", () => {
    const admin = renderPlatformShell();
    expect(screen.getByRole("img", { name: "Sketch2Life" }).getAttribute("src")).toContain("sketch2life-logo-mark-128.png");
    admin.unmount();

    const teacher = renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t01-lesson-workspace");
    expect(screen.getByRole("img", { name: "Sketch2Life" }).getAttribute("src")).toContain("sketch2life-logo-mark-128.png");
    teacher.unmount();

    renderRoleShell("School Manager", SCHOOL_MANAGER_NAVIGATION, "manager", "/school");
    expect(screen.getByRole("img", { name: "Sketch2Life" }).getAttribute("src")).toContain("sketch2life-logo-mark-128.png");
  });

  it("keeps the active Teacher navigation group open and remembers another group preference", () => {
    renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t01-lesson-workspace");
    const teaching = screen.getByRole("button", { name: "Dạy học" });
    const account = screen.getByRole("button", { name: "Tài khoản" });
    expect(teaching.getAttribute("aria-expanded")).toBe("true");
    expect(account.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(account);
    expect(account.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(screen.getByRole("link", { name: "Giáo án" }));
    expect(teaching.getAttribute("aria-expanded")).toBe("true");
    expect(account.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("link", { name: "Giáo án" }).getAttribute("aria-current")).toBe("page");
  });

  it("renders the School Manager breadcrumb and keeps its active group expanded", () => {
    renderRoleShell("School Manager", SCHOOL_MANAGER_NAVIGATION, "manager", "/school");
    expect(screen.getByRole("link", { name: "Không gian quản lý" }).getAttribute("href")).toBe("/school");
    expect(screen.getByRole("button", { name: "Nhà trường" }).getAttribute("aria-expanded")).toBe("true");
  });
});
