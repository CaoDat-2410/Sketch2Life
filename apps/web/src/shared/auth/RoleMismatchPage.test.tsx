import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { RoleMismatchPage } from "./RoleMismatchPage";

afterEach(() => cleanup());

it("shows the role mismatch message and calls the existing logout action", () => {
  const onLogout = vi.fn();
  render(<RoleMismatchPage roleLabel="Giáo viên" onLogout={onLogout} />);

  expect(screen.getByRole("alert")).toBeTruthy();
  expect(screen.getByRole("heading", { name: "Không thể mở cổng Giáo viên" })).toBeTruthy();
  expect(screen.getByText("Phiên hiện tại chưa được xác nhận cho cổng này. Đăng xuất rồi đăng nhập lại bằng tài khoản có quyền phù hợp.")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Đăng xuất và quay lại" }));
  expect(onLogout).toHaveBeenCalledOnce();
});
