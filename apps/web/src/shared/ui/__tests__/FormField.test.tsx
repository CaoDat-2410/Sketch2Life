import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { FormField, Select } from "..";

afterEach(() => cleanup());

describe("shared FormField", () => {
  it("wires label htmlFor and control id automatically and preserves explicit id", () => {
    const { rerender } = render(
      <FormField label="Tên lớp">
        <input />
      </FormField>,
    );
    const autoInput = screen.getByLabelText("Tên lớp") as HTMLInputElement;
    expect(autoInput.id).toBeTruthy();

    rerender(
      <FormField label="Mã lớp" htmlFor="explicit-class-code">
        <input id="explicit-class-code" />
      </FormField>,
    );
    const explicitInput = screen.getByLabelText("Mã lớp") as HTMLInputElement;
    expect(explicitInput.id).toBe("explicit-class-code");
  });

  it("renders a consistent required asterisk marker and aria-required without altering accessible name", () => {
    render(
      <FormField label="Email tài khoản" htmlFor="email-field" required>
        <input id="email-field" type="email" />
      </FormField>,
    );
    const input = screen.getByLabelText("Email tài khoản");
    expect(input.getAttribute("aria-required")).toBe("true");
    const marker = screen.getByText("*");
    expect(marker.getAttribute("aria-hidden")).toBe("true");
    expect(marker.className).toContain("cozy-form-required");
    expect(marker.parentElement?.className).toContain("cozy-form-label-group");
    expect(screen.getByText("Email tài khoản").tagName).toBe("LABEL");
  });

  it("renders help text and wires aria-describedby", () => {
    render(
      <FormField label="Tên buổi dạy" htmlFor="session-name" help="Tên ngắn giúp dễ nhận biết.">
        <input id="session-name" />
      </FormField>,
    );
    const input = screen.getByLabelText("Tên buổi dạy");
    const help = screen.getByText("Tên ngắn giúp dễ nhận biết.");
    expect(help.id).toBe("session-name-help");
    expect(help.className).toContain("cozy-form-hint");
    expect(input.getAttribute("aria-describedby")).toContain("session-name-help");
  });

  it("renders inline error with role=alert, danger token class, and aria-invalid", () => {
    render(
      <FormField
        label="Mật khẩu mới"
        htmlFor="new-password"
        help="Ít nhất 6 ký tự."
        error="Mật khẩu chưa đủ dài."
      >
        <input id="new-password" type="password" />
      </FormField>,
    );
    const input = screen.getByLabelText("Mật khẩu mới");
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toBe("Mật khẩu chưa đủ dài.");
    expect(alert.className).toContain("cozy-form-error");
    expect(input.getAttribute("aria-invalid")).toBe("true");
    expect(input.getAttribute("aria-describedby")).toContain("new-password-error");
    expect(input.getAttribute("aria-describedby")).toContain("new-password-help");
  });

  it("wires aria-describedby and aria-invalid onto shared Select", () => {
    render(
      <FormField label="Trạng thái" htmlFor="state-select" required error="Chọn trạng thái.">
        <Select id="state-select" value="" onChange={() => undefined}>
          <option value="">Chọn</option>
          <option value="active">Đang hoạt động</option>
        </Select>
      </FormField>,
    );
    const trigger = screen.getByRole("combobox", { name: "Trạng thái" });
    expect(trigger.getAttribute("aria-required")).toBe("true");
    expect(trigger.getAttribute("aria-invalid")).toBe("true");
    expect(trigger.getAttribute("aria-describedby")).toBe("state-select-error");
  });
});
