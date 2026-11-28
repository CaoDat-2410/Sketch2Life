import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { AccountRoleOverview, OrganizationStateOverview, ProcessingDistribution } from "../DashboardPanels";
import { integerAxis } from "../dashboardData";

afterEach(cleanup);

describe("dashboard column charts", () => {
  it("builds a whole-number axis from zero", () => {
    expect(integerAxis(0)).toEqual({ max: 1, ticks: [0, 1] });
    expect(integerAxis(3)).toEqual({ max: 3, ticks: [0, 1, 2, 3] });
    expect(integerAxis(8)).toEqual({ max: 8, ticks: [0, 2, 4, 6, 8] });
    expect(integerAxis(11)).toEqual({ max: 15, ticks: [0, 5, 10, 15] });
    expect(integerAxis(132)).toEqual({ max: 150, ticks: [0, 50, 100, 150] });
    for (const value of [1, 7, 19, 250, 999, 12345]) {
      const axis = integerAxis(value);
      expect(axis.max).toBeGreaterThanOrEqual(value);
      expect(axis.ticks.length).toBeLessThanOrEqual(5);
      expect(axis.ticks.every(Number.isInteger)).toBe(true);
    }
  });

  it("shows a value on every school-state column, keeps zero as a labelled empty column and repeats the figures as text", () => {
    const { container } = render(<OrganizationStateOverview summary={{ total: 10, active: 6, paused: 2, disabled: 2, other: 0 } as never} />);
    const chart = screen.getByRole("img", { name: /Trường đang hoạt động chiếm 60% trong tổng số 10 trường/ });
    const columns = [...chart.querySelectorAll(".pa-columns-item")];
    expect(columns.map((column) => column.querySelector("b")?.textContent)).toEqual(["6", "2", "2", "0"]);
    expect(columns.map((column) => column.querySelector("small")?.textContent)).toEqual(["Đang hoạt động", "Tạm dừng", "Đã ngừng", "Trạng thái khác"]);
    expect(columns[3].className).toContain("is-empty");
    expect((columns[3].querySelector(".pa-columns-bar") as HTMLElement).style.height).toBe("0%");
    expect((columns[0].querySelector(".pa-columns-bar") as HTMLElement).style.height).toBe("100%");
    expect((columns[1].querySelector(".pa-columns-bar") as HTMLElement).style.height).toMatch(/^33\.3/);
    expect(container.querySelector(".pa-dashboard-gauge, .pa-donut")).toBeNull();
    const legend = screen.getByRole("list", { name: "Số trường theo trạng thái" });
    expect(within(legend).getAllByRole("listitem").map((item) => item.textContent)).toEqual([
      "Đang hoạt động660%", "Tạm dừng220%", "Đã ngừng220%", "Trạng thái khác00%",
    ]);
  });

  it("draws account roles and processing records as columns with a text alternative", () => {
    render(<AccountRoleOverview total={8} consistent rows={[{ label: "Phụ huynh", count: 5, percentage: 62.5 }, { label: "Giáo viên", count: 3, percentage: 37.5 }] as never} />);
    expect(screen.getByRole("img", { name: "Số tài khoản theo vai trò: Phụ huynh 5, Giáo viên 3" })).toBeTruthy();
    expect(screen.getByRole("list", { name: "Tỷ lệ tài khoản theo vai trò" }).textContent).toContain("62,5%");
    cleanup();

    const { container } = render(<ProcessingDistribution operations={{ jobs: [{ state: "running", count: 2 }], email: [{ state: "sent", count: 6 }], core_outbox: [], lifecycle: [] } as never} />);
    expect(container.querySelector(".pa-donut")).toBeNull();
    expect(screen.getByRole("img", { name: /Phân bố 8 bản ghi/ })).toBeTruthy();
    const rows = within(screen.getByRole("table", { name: "Số bản ghi theo nhóm" })).getAllByRole("row");
    expect(rows.slice(1).map((row) => row.textContent)).toEqual(["Tác vụ xử lý225%", "Thư điện tử675%", "Sự kiện đã ghi nhận00%", "Yêu cầu dữ liệu00%"]);
  });
});
