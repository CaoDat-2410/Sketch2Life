import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { ConfirmDialog } from "..";

afterEach(() => cleanup());

function DialogHarness({
  tone = "danger",
  confirmLabel = "Xóa",
  onConfirm = vi.fn(),
  onCancel = vi.fn(),
}: {
  tone?: "primary" | "danger";
  confirmLabel?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button type="button" onClick={() => setOpen(true)}>
        Mở xác nhận
      </button>
      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title="Xác nhận thao tác?"
        description="Thao tác này sẽ cập nhật trạng thái hiện tại."
        confirmLabel={confirmLabel}
        tone={tone}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />
    </div>
  );
}

describe("shared ConfirmDialog", () => {
  it("shows visible title, single accessible description, quiet Hủy button, and tone-appropriate action button", () => {
    const onConfirm = vi.fn();
    render(<DialogHarness tone="primary" confirmLabel="Đổi giáo viên" onConfirm={onConfirm} />);

    fireEvent.click(screen.getByRole("button", { name: "Mở xác nhận" }));
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByRole("heading", { name: "Xác nhận thao tác?" })).toBeTruthy();

    const descriptions = within(dialog).getAllByText("Thao tác này sẽ cập nhật trạng thái hiện tại.");
    expect(descriptions).toHaveLength(1);
    expect(descriptions[0].className).toContain("s2l-dialog-description");
    expect(descriptions[0].className).not.toContain("s2l-sr-only");
    expect(dialog.getAttribute("aria-describedby")).toBe(descriptions[0].id);

    const buttons = within(dialog).getAllByRole("button");
    expect(buttons.map((button) => button.textContent)).toEqual(["", "Hủy", "Đổi giáo viên"]);
    expect(buttons[1].className).toContain("s2l-confirm-cancel");
    expect(buttons[2].className).toContain("is-primary");
    expect(buttons[2].className).toContain("bg-primary");
  });

  it("applies danger tone styling for destructive confirmations", () => {
    render(<DialogHarness tone="danger" confirmLabel="Xóa" />);
    fireEvent.click(screen.getByRole("button", { name: "Mở xác nhận" }));
    const action = within(screen.getByRole("dialog")).getByRole("button", { name: "Xóa" });
    expect(action.className).toContain("is-danger");
    expect(action.className).toContain("bg-danger-base");
  });

  it("focuses Hủy initially and returns focus to the trigger button on Escape, Hủy, and close", async () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(<DialogHarness onConfirm={onConfirm} onCancel={onCancel} />);

    const trigger = screen.getByRole("button", { name: "Mở xác nhận" });
    trigger.focus();
    fireEvent.click(trigger);

    const dialog = screen.getByRole("dialog");
    const cancelButton = within(dialog).getByRole("button", { name: "Hủy" });
    await waitFor(() => expect(document.activeElement).toBe(cancelButton));

    fireEvent.keyDown(dialog, { key: "Escape" });
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
    await waitFor(() => expect(document.activeElement).toBe(trigger));

    fireEvent.click(trigger);
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Hủy" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(onCancel).toHaveBeenCalledTimes(2);
    expect(onConfirm).not.toHaveBeenCalled();
    await waitFor(() => expect(document.activeElement).toBe(trigger));

    fireEvent.click(trigger);
    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Đóng" }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(onCancel).toHaveBeenCalledTimes(3);
    expect(onConfirm).not.toHaveBeenCalled();
    await waitFor(() => expect(document.activeElement).toBe(trigger));
  });

  it("cancels on overlay click without calling onConfirm", async () => {
    const onConfirm = vi.fn();
    const onCancel = vi.fn();
    render(<DialogHarness onConfirm={onConfirm} onCancel={onCancel} />);

    fireEvent.click(screen.getByRole("button", { name: "Mở xác nhận" }));
    const dialog = screen.getByRole("dialog");
    await waitFor(() => expect(document.activeElement).toBe(within(dialog).getByRole("button", { name: "Hủy" })));
    const overlay = document.querySelector(".s2l-dialog-overlay");
    expect(overlay).toBeTruthy();
    fireEvent.pointerDown(overlay!, { button: 0 });
    fireEvent.click(overlay!);

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("calls onConfirm exactly once even if the action button is clicked twice while open", () => {
    const onConfirm = vi.fn();
    const onOpenChange = vi.fn();
    render(
      <ConfirmDialog
        open
        onOpenChange={onOpenChange}
        title="Hủy lượt?"
        description="Lượt này sẽ bị xóa."
        confirmLabel="Hủy lượt"
        tone="danger"
        onConfirm={onConfirm}
      />,
    );

    const action = within(screen.getByRole("dialog")).getByRole("button", { name: "Hủy lượt" });
    fireEvent.click(action);
    fireEvent.click(action);

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });
});
