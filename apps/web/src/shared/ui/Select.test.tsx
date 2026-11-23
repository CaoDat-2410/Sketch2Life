import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { Select, type SelectChangeEvent } from "./Select";

afterEach(cleanup);

function SelectHarness({
  initialValue = "teacher",
  disabled = false,
  required = false,
  ariaLabel,
  onChange = () => undefined,
}: {
  initialValue?: string;
  disabled?: boolean;
  required?: boolean;
  ariaLabel?: string;
  onChange?: (event: SelectChangeEvent) => void;
}) {
  const [value, setValue] = useState(initialValue);
  return (
    <>
      <label htmlFor="role-picker">Role</label>
      <Select
        id="role-picker"
        value={value}
        disabled={disabled}
        required={required}
        aria-label={ariaLabel}
        onChange={(event) => { onChange(event); setValue(event.target.value); }}
      >
        <option value="" disabled>Choose a role</option>
        <option value="parent">Parent</option>
        <option value="teacher">Teacher</option>
        <option value="manager">Manager</option>
      </Select>
    </>
  );
}

describe("shared Select", () => {
  it("opens, chooses an option, and sends the native-compatible change payload", () => {
    const onChange = vi.fn();
    const { container } = render(<SelectHarness onChange={onChange} />);
    const trigger = screen.getByRole("combobox", { name: "Role" });

    fireEvent.click(trigger);
    expect(screen.getByRole("listbox")).toBeTruthy();
    fireEvent.click(screen.getByRole("option", { name: "Parent" }));

    expect(onChange).toHaveBeenCalledWith({ target: { value: "parent" } });
    expect(trigger.textContent).toContain("Parent");
    expect((container.querySelector("select.s2l-select-native") as HTMLSelectElement).value).toBe("parent");
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("supports arrow, Home, End, Enter, and type-ahead keyboard selection", () => {
    render(<SelectHarness initialValue="" ariaLabel="Role" />);
    const trigger = screen.getByRole("combobox", { name: "Role" });

    trigger.focus();
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    fireEvent.keyDown(trigger, { key: "Home" });
    fireEvent.keyDown(trigger, { key: "Enter" });
    expect(trigger.textContent).toContain("Parent");

    fireEvent.keyDown(trigger, { key: "m" });
    expect(screen.getByRole("listbox")).toBeTruthy();
    fireEvent.keyDown(trigger, { key: "End" });
    fireEvent.keyDown(trigger, { key: "Enter" });
    expect(trigger.textContent).toContain("Manager");
  });

  it("skips disabled options and closes on Escape and Tab", () => {
    render(<SelectHarness initialValue="" ariaLabel="Role" />);
    const trigger = screen.getByRole("combobox", { name: "Role" });

    fireEvent.click(trigger);
    fireEvent.keyDown(trigger, { key: "ArrowDown" });
    fireEvent.keyDown(trigger, { key: "Enter" });
    expect(trigger.textContent).toContain("Teacher");

    fireEvent.click(trigger);
    fireEvent.keyDown(trigger, { key: "Escape" });
    expect(screen.queryByRole("listbox")).toBeNull();

    fireEvent.click(trigger);
    fireEvent.keyDown(trigger, { key: "Tab" });
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("keeps disabled and required state on the hidden native control", () => {
    const { container } = render(<SelectHarness initialValue="" disabled required ariaLabel="Role" />);
    const trigger = screen.getByRole("combobox", { name: "Role" }) as HTMLButtonElement;
    const nativeSelect = container.querySelector("select.s2l-select-native") as HTMLSelectElement;

    expect(trigger.disabled).toBe(true);
    expect(nativeSelect.disabled).toBe(true);
    expect(nativeSelect.required).toBe(true);
    fireEvent.click(trigger);
    expect(screen.queryByRole("listbox")).toBeNull();
  });

  it("focuses the visible trigger when required validation reaches the hidden control", () => {
    const { container } = render(<SelectHarness initialValue="" required ariaLabel="Role" />);
    const trigger = screen.getByRole("combobox", { name: "Role" });
    const nativeSelect = container.querySelector("select.s2l-select-native") as HTMLSelectElement;

    expect(nativeSelect.required).toBe(true);
    expect(fireEvent.invalid(nativeSelect)).toBe(false);
    expect(document.activeElement).toBe(trigger);
  });
});
