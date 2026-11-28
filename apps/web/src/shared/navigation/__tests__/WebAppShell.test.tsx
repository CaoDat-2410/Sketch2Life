import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  PLATFORM_ADMIN_NAVIGATION,
  SCHOOL_MANAGER_NAVIGATION,
  TEACHER_NAVIGATION,
  WebAppShell,
} from "../WebAppShell";
import { InboxPage } from "../../notifications/InboxPage";
import * as notificationsApi from "../../api/notificationsApi";
import { authService } from "../../../modules/school-manager/be1/services/authService";

vi.mock("../../../modules/school-manager/be1/services/authService", () => ({
  authService: {
    observe: () => () => undefined,
    changePassword: vi.fn(),
  },
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

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

function openPlatformAccountPopover() {
  fireEvent.click(document.querySelector(".s2l-topbar-account summary") as HTMLElement);
}

function renderRoleShell(roleLabel: string, navigation: typeof TEACHER_NAVIGATION, portal: "teacher" | "manager", initialPath: string, navStatus?: Partial<Record<string, "pending" | "done" | "failed" | undefined>>) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <WebAppShell
        portal={portal}
        roleLabel={roleLabel}
        roleSubtitle={portal === "teacher" ? "Nội dung dành cho giáo viên" : "Nội dung dành cho quản lý"}
        navigation={navigation}
        navStatus={navStatus}
        loginHref="/login"
        modeLabel={portal === "teacher" ? "Phiên đã xác minh" : "Phiên đang hoạt động"}
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

  it("uses the system email label as the settings panel breadcrumb", () => {
    renderPlatformShell("/platform/a02-platform-operations?panel=settings");
    expect(screen.getByText("Email hệ thống", { selector: '[aria-current="page"]' })).toBeTruthy();
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

  it("keeps learning and classroom groups open by default and remembers another group preference", () => {
    renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t01-lesson-workspace");
    const learning = screen.getByRole("button", { name: "Học liệu" });
    const teaching = screen.getByRole("button", { name: "Lên lớp" });
    const account = screen.getByRole("button", { name: "Tài khoản" });
    expect(learning.getAttribute("aria-expanded")).toBe("true");
    expect(teaching.getAttribute("aria-expanded")).toBe("true");
    expect(account.getAttribute("aria-expanded")).toBe("false");

    fireEvent.click(account);
    expect(account.getAttribute("aria-expanded")).toBe("true");
    fireEvent.click(screen.getByRole("link", { name: "Giáo án" }));
    expect(learning.getAttribute("aria-expanded")).toBe("true");
    expect(teaching.getAttribute("aria-expanded")).toBe("true");
    expect(account.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("link", { name: "Giáo án" }).getAttribute("aria-current")).toBe("page");
  });

  it("shows one brand block and one footer in all three portals, without captions or mode chips", () => {
    const teacher = renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t01-lesson-workspace");
    expect(screen.queryByText("Nội dung dành cho giáo viên")).toBeNull();
    expect(screen.queryByText("Quyền được kiểm tra theo phiên")).toBeNull();
    expect(document.querySelector(".s2l-mode-chip")).toBeNull();
    expect(document.querySelector(".s2l-session-status")?.textContent).toBe("Phiên đã xác minh");
    expect(screen.getByRole("button", { name: "Đổi mật khẩu" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Đăng xuất" })).toBeTruthy();
    teacher.unmount();

    const manager = renderRoleShell("Quản lý trường", SCHOOL_MANAGER_NAVIGATION, "manager", "/school");
    expect(screen.queryByText("Nội dung dành cho quản lý")).toBeNull();
    expect(screen.queryByText("Quyền được kiểm tra theo phiên")).toBeNull();
    expect(document.querySelector(".s2l-mode-chip")).toBeNull();
    expect(document.querySelector(".s2l-brand-wordmark")?.textContent).toBe("Sketch2LifeQuản lý trường");
    expect(document.querySelector(".s2l-session-status")?.textContent).toBe("Phiên đang hoạt động");
    expect(screen.getByRole("button", { name: "Đổi mật khẩu" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Đăng xuất" })).toBeTruthy();
    manager.unmount();

    renderPlatformShell();
    expect(document.querySelector(".s2l-brand-wordmark")?.textContent).toBe("Sketch2LifePlatform Admin");
    expect(screen.getByRole("button", { name: "Đổi mật khẩu" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Đăng xuất" })).toBeTruthy();
  });

  it("shows read-only Admin account details", () => {
    vi.spyOn(authService, "observe").mockImplementation((callback) => {
      callback({ displayName: "Anh Khoa", email: "admin@example.com" } as never);
      return () => undefined;
    });
    renderPlatformShell();
    openPlatformAccountPopover();

    const popover = document.querySelector(".s2l-topbar-popover") as HTMLElement;
    expect(within(popover).getByText("Anh Khoa")).toBeTruthy();
    expect(within(popover).getByText("admin@example.com")).toBeTruthy();
    expect(within(popover).getByText("Quản trị viên")).toBeTruthy();
    expect(within(popover).queryByRole("link", { name: "Cài đặt tài khoản" })).toBeNull();
  });

  it("shows the Admin fallback name only once when no display name is available", () => {
    renderPlatformShell();
    openPlatformAccountPopover();

    const popover = document.querySelector(".s2l-topbar-popover") as HTMLElement;
    expect(within(popover).getAllByText("Quản trị viên")).toHaveLength(1);
    expect(within(popover).getByText("Tài khoản của tôi")).toBeTruthy();
  });

  it("removes account settings links from all three roles", () => {
    const teacher = renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t01-lesson-workspace");
    expect(screen.queryByRole("link", { name: "Cài đặt" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Cài đặt tài khoản" })).toBeNull();
    teacher.unmount();

    const manager = renderRoleShell("Quản lý trường", SCHOOL_MANAGER_NAVIGATION, "manager", "/school/account");
    expect(screen.getByRole("link", { name: "Thông tin tài khoản" })).toBeTruthy();
    expect(screen.queryByRole("link", { name: "Cài đặt" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Cài đặt tài khoản" })).toBeNull();
    manager.unmount();

    renderPlatformShell();
    openPlatformAccountPopover();
    expect(screen.queryByRole("link", { name: "Cài đặt tài khoản" })).toBeNull();
    expect(screen.queryByRole("link", { name: "Cài đặt" })).toBeNull();
  });

  it("gives every menu item of a role its own icon", () => {
    for (const groups of [TEACHER_NAVIGATION, SCHOOL_MANAGER_NAVIGATION, PLATFORM_ADMIN_NAVIGATION]) {
      const icons = groups.flatMap((group) => group.items.map((item) => item.icon));
      expect(new Set(icons).size).toBe(icons.length);
    }
  });

  it("shows the Teacher SVG catalog as an available learning resource", () => {
    const catalog = TEACHER_NAVIGATION.flatMap((group) => group.items).find((item) => item.href === "/teacher/svg-catalog");
    expect(catalog?.label).toBe("Danh mục SVG");
    expect(catalog?.state).toBe("available");
  });

  it("keeps the requested Teacher navigation order and distinct AI icon", () => {
    expect(TEACHER_NAVIGATION.map((group) => group.label)).toEqual(["", "Học liệu", "Lên lớp", "Tài khoản"]);
    expect(TEACHER_NAVIGATION.map((group) => group.items.map((item) => item.label))).toEqual([
      ["Tổng quan"],
      ["Giáo án", "Gợi ý giáo án AI", "Nhập tài liệu", "Hoạt động", "Danh mục SVG", "Phản hồi giáo án"],
      ["Lớp được phân công", "Buổi dạy", "Lịch sử buổi dạy"],
      ["Hộp thư", "Hồ sơ cá nhân"],
    ]);
    const lesson = TEACHER_NAVIGATION.flatMap((group) => group.items).find((item) => item.href === "/teacher/t02-lesson-authoring");
    const aiSuggestion = TEACHER_NAVIGATION.flatMap((group) => group.items).find((item) => item.href === "/teacher/t13-ai-lesson-workflow");
    expect(aiSuggestion?.icon).not.toBe(lesson?.icon);
    expect(TEACHER_NAVIGATION.flatMap((group) => group.items).some((item) => item.href === "/teacher/t02-presentation")).toBe(false);
  });

  it("lists the Teacher, School Manager, and Platform Admin additions as available", () => {
    const entries = [TEACHER_NAVIGATION, SCHOOL_MANAGER_NAVIGATION, PLATFORM_ADMIN_NAVIGATION].flatMap((groups) => groups.flatMap((group) => group.items));
    for (const expected of [
      { href: "/teacher/t14-feedback", label: "Phản hồi giáo án" },
      { href: "/teacher/t09-history", label: "Lịch sử buổi dạy" },
      { href: "/teacher/t11-profile", label: "Hồ sơ cá nhân" },
      { href: "/teacher/t12-activities", label: "Hoạt động" },
      { href: "/school/data-requests", label: "Yêu cầu dữ liệu" },
      { href: "/school/account", label: "Thông tin tài khoản" },
      { href: "/platform/a02-platform-operations?panel=svgcatalog", label: "Danh mục SVG" },
      { href: "/platform/a02-platform-operations?panel=settings", label: "Email hệ thống" },
    ]) {
      expect(entries.find((item) => item.href === expected.href)).toMatchObject({ ...expected, state: "available" });
    }
  });

  it("renders the School Manager breadcrumb and keeps its active group expanded", () => {
    renderRoleShell("School Manager", SCHOOL_MANAGER_NAVIGATION, "manager", "/school");
    expect(screen.getByRole("link", { name: "Không gian quản lý" }).getAttribute("href")).toBe("/school");
    expect(screen.getByRole("button", { name: "Nhà trường" }).getAttribute("aria-expanded")).toBe("true");
  });

  it("shows the active Teacher page title in breadcrumb even with query parameters", () => {
    renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t02-presentation?occurrence=occ-1");
    expect(screen.getByRole("link", { name: "Không gian giáo viên" }).getAttribute("href")).toBe("/teacher/t01-lesson-workspace");
    expect(screen.getByText("Trình bày giáo án", { selector: '[aria-current="page"]' })).toBeTruthy();
  });
});

describe("Teacher AI navigation status", () => {
  it.each([
    ["pending", "Đang xử lý yêu cầu AI", "lucide-loader-circle"],
    ["done", "Yêu cầu AI đã xong", "lucide-check"],
    ["failed", "Yêu cầu AI chưa thành công", "lucide-triangle-alert"],
  ] as const)("shows the %s icon, accessible label, title and live announcement", (status, label, iconClass) => {
    renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t01-lesson-workspace", {
      "/teacher/t13-ai-lesson-workflow": status,
    });
    const link = screen.getByRole("link", { name: "Gợi ý giáo án AI " + label });
    expect(link.getAttribute("title")).toBe(label);
    expect(link.querySelector(".s2l-nav-ai-status")?.getAttribute("aria-hidden")).toBe("true");
    const statusIcon = link.querySelector(".s2l-nav-ai-status svg");
    expect(statusIcon?.getAttribute("aria-hidden")).toBe("true");
    expect(statusIcon?.getAttribute("class")).toContain(iconClass);
    expect(screen.getByRole("status").textContent).toContain("Gợi ý giáo án AI: " + label);
  });

  it("keeps the link name unchanged when no status is supplied", () => {
    renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t01-lesson-workspace");
    const link = screen.getByRole("link", { name: "Gợi ý giáo án AI" });
    expect(link.getAttribute("title")).toBeNull();
    expect(link.querySelector(".s2l-visually-hidden")).toBeNull();
  });

  it("keeps the live region available with a collapsed group and closed phone menu", () => {
    renderRoleShell("Giáo viên", TEACHER_NAVIGATION, "teacher", "/teacher/t09-history", {
      "/teacher/t13-ai-lesson-workflow": "failed",
    });
    const liveRegion = document.querySelector('[role="status"][aria-live="polite"]');
    expect(liveRegion?.textContent).toContain("Gợi ý giáo án AI: Yêu cầu AI chưa thành công");
    expect(liveRegion?.closest("aside")).toBeNull();
    expect(screen.getByRole("button", { name: "Học liệu" }).getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("button", { name: "Lên lớp" }).getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByRole("button", { name: "Tài khoản" }).getAttribute("aria-expanded")).toBe("false");
    expect(screen.getByRole("button", { name: "Mở điều hướng" }).getAttribute("aria-expanded")).toBe("false");
  });
});


describe("inbox navigation badge", () => {
  it.each([
    ["teacher", TEACHER_NAVIGATION, "/teacher/t01-lesson-workspace", "Tài khoản"],
    ["manager", SCHOOL_MANAGER_NAVIGATION, "/school", "Thông báo"],
  ] as const)("shows the collapsed and expanded badge for %s", async (portal, navigation, route, group) => {
    vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue({ contract: "NotificationPageV1", items: [], next_cursor: null, unread_count: 3 });
    renderRoleShell("Role", navigation, portal, route);
    const toggle = await screen.findByRole("button", { name: `${group}, 3 thông báo chưa đọc` });
    expect(toggle.querySelector(".s2l-nav-unread")?.getAttribute("aria-hidden")).toBe("true");
    fireEvent.click(toggle);
    expect(screen.getByRole("link", { name: "Hộp thư, 3 thông báo chưa đọc" }).querySelector(".s2l-nav-unread")?.textContent).toBe("3");
    expect(toggle.querySelector(".s2l-nav-unread")).toBeNull();
  });

  it("caps the visible and accessible count at 99+", async () => {
    vi.spyOn(notificationsApi, "listNotifications").mockResolvedValue({ contract: "NotificationPageV1", items: [], next_cursor: null, unread_count: 105 });
    renderRoleShell("Role", TEACHER_NAVIGATION, "teacher", "/teacher/t10-inbox");
    const link = await screen.findByRole("link", { name: "Hộp thư, hơn 99 thông báo chưa đọc" });
    expect(link.querySelector(".s2l-nav-unread")?.textContent).toBe("99+");
  });

  it("refreshes the badge after an inbox item is marked read", async () => {
    const item: notificationsApi.NotificationItem = { contract: "NotificationV1", inbox_item_id: "one", notification_type: "CLASS_ARCHIVED", template_version: 1, safe_parameters: {}, created_at: "2026-11-20T10:00:00Z", read_at: null, expires_at: null };
    let count = 1;
    vi.spyOn(notificationsApi, "listNotifications").mockImplementation(async (options) => ({ contract: "NotificationPageV1", items: options?.limit === 1 ? [] : [item], next_cursor: null, unread_count: count }));
    vi.spyOn(notificationsApi, "markNotificationRead").mockImplementation(async () => { count = 0; return { ...item, read_at: "2026-11-20T12:00:00Z" }; });
    render(<MemoryRouter initialEntries={["/teacher/t10-inbox"]}><WebAppShell portal="teacher" roleLabel="Teacher" navigation={TEACHER_NAVIGATION} loginHref="/login" modeLabel="" onLogout={() => undefined}><InboxPage /></WebAppShell></MemoryRouter>);
    expect(await screen.findByRole("link", { name: "H\u1ed9p th\u01b0, 1 th\u00f4ng b\u00e1o ch\u01b0a \u0111\u1ecdc" })).toBeTruthy();
    fireEvent.click(await screen.findByRole("button", { name: "Th\u00f4ng b\u00e1o m\u1edbi: \u0111\u00e1nh d\u1ea5u \u0111\u00e3 \u0111\u1ecdc" }));
    expect(await screen.findByRole("link", { name: "H\u1ed9p th\u01b0" })).toBeTruthy();
  });

  it("does not fetch for the admin menu", () => {
    const list = vi.spyOn(notificationsApi, "listNotifications");
    renderPlatformShell();
    expect(list).not.toHaveBeenCalled();
  });
});
