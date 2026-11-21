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

function renderRoleShell(roleLabel: string, navigation: typeof TEACHER_NAVIGATION) {
  return render(
    <MemoryRouter initialEntries={["/"]}>
      <WebAppShell
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

describe("Platform Admin brand mark", () => {
  it("renders the approved logo image with its accessible name in the Platform Admin shell", () => {
    renderPlatformShell();

    const logo = screen.getByRole("img", { name: "Sketch2Life" });
    expect(logo.getAttribute("src")).toContain("sketch2life-logo-mark-128.png");
  });

  it("does not render the Platform Admin logo image in the Teacher shell", () => {
    renderRoleShell("Teacher", TEACHER_NAVIGATION);

    expect(screen.queryByRole("img", { name: "Sketch2Life" })).toBeNull();
  });

  it("does not render the Platform Admin logo image in the School Manager shell", () => {
    renderRoleShell("School Manager", SCHOOL_MANAGER_NAVIGATION);

    expect(screen.queryByRole("img", { name: "Sketch2Life" })).toBeNull();
  });
});
