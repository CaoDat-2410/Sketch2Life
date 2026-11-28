import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { Button, StatusBadge } from "../../../../shared/ui";
import { FormActionBar } from "../FormActionBar";
import { teacherStatusMeta } from "../../services/teacherStatus";

afterEach(() => cleanup());

describe("Teacher FormActionBar and status helper", () => {
  it("places hint and danger action in the leading slot and buttons in the trailing slot", () => {
    const { container } = render(
      <FormActionBar
        hint="Nhập tiêu đề để lưu."
        danger={<Button variant="danger" className="tp-quiet-danger">Lưu trữ giáo án</Button>}
      >
        <Button variant="secondary">Gửi duyệt</Button>
        <Button variant="primary">Lưu cập nhật</Button>
      </FormActionBar>,
    );
    expect(screen.getByText("Nhập tiêu đề để lưu.").className).toContain("tp-form-action-hint");
    expect(screen.getByRole("button", { name: "Lưu trữ giáo án" }).className).toContain("tp-quiet-danger");
    expect(container.querySelector(".tp-form-action-bar-buttons")?.children).toHaveLength(2);
  });

  it("maps backend statuses to Vietnamese labels and tones", () => {
    expect(teacherStatusMeta("APPROVED")).toEqual({ label: "Đã duyệt", tone: "success" });
    expect(teacherStatusMeta("APPROVED", "plan")).toEqual({ label: "Đã xác nhận", tone: "success" });
    expect(teacherStatusMeta("DRAFT")).toEqual({ label: "Bản nháp", tone: "neutral" });
    expect(teacherStatusMeta("PENDING_REVIEW")).toEqual({ label: "Chờ duyệt", tone: "warn" });
    expect(teacherStatusMeta("REJECTED")).toEqual({ label: "Bị từ chối", tone: "danger" });
    expect(teacherStatusMeta("PUBLIC")).toEqual({ label: "Công khai", tone: "info" });
    expect(teacherStatusMeta("PRIVATE")).toEqual({ label: "Riêng tư", tone: "neutral" });

    const meta = teacherStatusMeta("PENDING_REVIEW");
    render(<StatusBadge tone={meta.tone} dot>{meta.label}</StatusBadge>);
    expect(screen.getByText("Chờ duyệt")).toBeTruthy();
  });
});
