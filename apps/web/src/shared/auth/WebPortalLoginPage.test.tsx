import { afterEach, describe, expect, it, vi } from "vitest";
import { useState } from "react";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { BackendApiError } from "../api/backendApi";
import { WebPortalLoginPage, type WebPortalAppRole } from "./WebPortalLoginPage";

afterEach(() => cleanup());

function renderLogin(overrides: {
  onAuthenticate?: (role: WebPortalAppRole, email: string, password: string) => Promise<void>;
  onResetPassword?: (email: string) => Promise<void>;
} = {}) {
  const onRoleChange = vi.fn();
  const onAuthenticate = overrides.onAuthenticate ?? vi.fn(async () => undefined);
  const onResetPassword = overrides.onResetPassword ?? vi.fn(async () => undefined);

  function LoginHarness() {
    const [role, setRole] = useState<WebPortalAppRole>("TEACHER");
    return (
      <MemoryRouter initialEntries={["/login?role=teacher"]}>
        <WebPortalLoginPage
          portalRole={role}
          onRoleChange={(nextRole) => { onRoleChange(nextRole); setRole(nextRole); }}
          onAuthenticate={onAuthenticate}
          onResetPassword={onResetPassword}
        />
      </MemoryRouter>
    );
  }

  return { ...render(<LoginHarness />), onRoleChange, onAuthenticate, onResetPassword };
}

describe("WebPortalLoginPage", () => {
  it("shows all three portal tabs and switches the selected role", async () => {
    const { onRoleChange } = renderLogin();
    const group = screen.getByRole("group", { name: "Chọn vai trò đăng nhập" });
    const teacher = within(group).getByRole("button", { name: "Giáo viên" });
    const manager = within(group).getByRole("button", { name: "Quản lý trường" });
    const admin = within(group).getByRole("button", { name: "Quản trị nền tảng" });

    expect(teacher.getAttribute("aria-pressed")).toBe("true");
    expect(manager.getAttribute("aria-pressed")).toBe("false");
    expect(admin.getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(manager);

    await waitFor(() => expect(manager.getAttribute("aria-pressed")).toBe("true"));
    expect(onRoleChange).toHaveBeenCalledWith("MANAGER");
    expect(screen.getByRole("heading", { name: "Quản lý hoạt động trường" })).toBeTruthy();
    expect(screen.getByText("Quản lý lớp học, giáo viên và học liệu của trường.")).toBeTruthy();
    fireEvent.click(admin);
    await waitFor(() => expect(admin.getAttribute("aria-pressed")).toBe("true"));
    expect(screen.getByRole("heading", { name: "Vận hành nền tảng" })).toBeTruthy();
    expect(screen.getByText("Quản lý tài khoản và hoạt động nền tảng.")).toBeTruthy();
  });

  it("keeps the existing Vietnamese login copy and toggles password visibility", () => {
    renderLogin();

    expect(screen.getByRole("heading", { name: "Chuẩn bị buổi học" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Đăng nhập" })).toBeTruthy();
    expect(screen.getByText("Chào mừng bạn trở lại Sketch2Life.")).toBeTruthy();
    expect(screen.getByText("Mở các lớp được phân công, giáo án và tài liệu của bạn.")).toBeTruthy();
    expect(screen.getByLabelText("Email tài khoản")).toBeTruthy();
    const password = screen.getByLabelText("Mật khẩu") as HTMLInputElement;
    expect(password.type).toBe("password");

    fireEvent.click(screen.getByRole("button", { name: "Hiện mật khẩu" }));
    expect(password.type).toBe("text");
    expect(screen.getByRole("button", { name: "Ẩn mật khẩu" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("button", { name: "Quên mật khẩu?" })).toBeTruthy();
  });

  it("toggles recovery mode and announces a reset notice", async () => {
    const { onResetPassword } = renderLogin();
    fireEvent.click(screen.getByRole("button", { name: "Quên mật khẩu?" }));

    expect(screen.getByRole("heading", { name: "Quên mật khẩu?" })).toBeTruthy();
    expect(screen.queryByLabelText("Mật khẩu")).toBeNull();
    fireEvent.change(screen.getByLabelText("Email tài khoản"), { target: { value: "preview@example.invalid" } });
    fireEvent.submit(document.querySelector(".s2l-login-form")!);

    expect((await screen.findByRole("status")).textContent).toContain("Nếu email đã được đăng ký, bạn sẽ nhận được liên kết đặt lại mật khẩu.");
    expect(onResetPassword).toHaveBeenCalledWith("preview@example.invalid");
    expect((screen.getByRole("button", { name: "Gửi liên kết đặt lại" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("announces authentication errors through the alert role", async () => {
    const onAuthenticate = vi.fn(async () => {
      throw new BackendApiError("Synthetic sign-in failure", "PREVIEW_AUTH_FAILURE", 0);
    });
    renderLogin({ onAuthenticate });
    fireEvent.submit(document.querySelector(".s2l-login-form")!);

    expect((await screen.findByRole("alert")).textContent).toContain("Synthetic sign-in failure");
    expect(onAuthenticate).toHaveBeenCalledWith("TEACHER", "", "");
  });

  it("disables the submit action while authentication is pending", async () => {
    const onAuthenticate = vi.fn(() => new Promise<void>(() => undefined));
    renderLogin({ onAuthenticate });
    fireEvent.submit(document.querySelector(".s2l-login-form")!);

    await waitFor(() => expect((screen.getByRole("button", { name: "Đang xử lý…" }) as HTMLButtonElement).disabled).toBe(true));
    expect(screen.getByRole("group", { name: "Chọn vai trò đăng nhập" }).querySelectorAll("button:disabled")).toHaveLength(3);
  });
});
