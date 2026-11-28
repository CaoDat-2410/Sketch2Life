import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { DateField, FormField, formatDateDdMmYyyy, formatDateTimeDdMmYyyy } from "..";

afterEach(() => cleanup());

describe("shared DateField", () => {
  it("shows Vietnamese placeholder when empty and not focused, and hides it on focus", () => {
    render(
      <FormField label="Ngày dự kiến" htmlFor="test-date">
        <DateField id="test-date" value="" onChange={() => undefined} />
      </FormField>,
    );
    const input = screen.getByLabelText("Ngày dự kiến") as HTMLInputElement;
    expect(input.type).toBe("date");
    expect(screen.getByText("Chọn ngày (ngày/tháng/năm)")).toBeTruthy();

    fireEvent.focus(input);
    expect(screen.queryByText("Chọn ngày (ngày/tháng/năm)")).toBeNull();

    fireEvent.blur(input);
    expect(screen.getByText("Chọn ngày (ngày/tháng/năm)")).toBeTruthy();
  });

  it("shows datetime-local Vietnamese placeholder when empty", () => {
    render(
      <FormField label="Hết hạn" htmlFor="test-dt">
        <DateField id="test-dt" type="datetime-local" value="" onChange={() => undefined} />
      </FormField>,
    );
    expect(screen.getByText("Chọn ngày và giờ (ngày/tháng/năm)")).toBeTruthy();
  });

  it("echoes dd/mm/yyyy for date and dd/mm/yyyy HH:mm for datetime-local while keeping ISO value", () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <FormField label="Ngày dạy" htmlFor="d1">
        <DateField id="d1" type="date" value="2026-11-26" onChange={onChange} />
      </FormField>,
    );
    expect(screen.queryByText("Chọn ngày (ngày/tháng/năm)")).toBeNull();
    expect(screen.getByText("Đã chọn: 26/11/2026")).toBeTruthy();

    rerender(
      <FormField label="Hết hạn" htmlFor="d2">
        <DateField id="d2" type="datetime-local" value="2026-11-26T14:30" onChange={onChange} />
      </FormField>,
    );
    expect(screen.getByText("Đã chọn: 26/11/2026 14:30")).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Hết hạn"), { target: { value: "2026-12-01T09:15" } });
    expect(onChange).toHaveBeenCalledTimes(1);
  });

  it("formats ISO dates into dd/mm/yyyy consistently", () => {
    expect(formatDateDdMmYyyy("2026-11-05")).toBe("05/11/2026");
    expect(formatDateTimeDdMmYyyy("2026-11-05T08:05")).toBe("05/11/2026 08:05");
  });
});
