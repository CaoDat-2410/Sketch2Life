import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { CapacityServiceError, capacityService, type Be1OrganizationCapacity, type CapacityResponse } from "../services/capacityService";
import { classService, type Be1Class } from "../services/classService";
import { managerBusinessService } from "../services/managerBusinessService";
import { CapacityPage } from "../pages/CapacityPage";

const organization = {
  contract: "Be1OrganizationV1" as const,
  organization_id: "org-qa",
  display_name: "Trường kiểm thử",
};

function capacity(overrides: Partial<Be1OrganizationCapacity> = {}): Be1OrganizationCapacity {
  return {
    contract: "Be1OrganizationCapacityV1",
    organization_id: "org-qa",
    subscription_id: "subscription-private",
    capacity: 20,
    active_class_count: 3,
    available_slots: 17,
    subscription_state: "ACTIVE",
    revision: 5,
    period_start: "2026-01-01T00:00:00Z",
    period_end: "2026-12-31T00:00:00Z",
    scheduled_change: null,
    ...overrides,
  };
}

function result(data: Be1OrganizationCapacity): CapacityResponse {
  return { data, etag: '"' + data.revision + '"', revision: data.revision };
}

function activeClasses(count = 3): Be1Class[] {
  return Array.from({ length: count }, (_, index) => ({
    class_id: "class-private-" + (index + 1),
    display_name: "Lớp " + (index + 1),
    state: "active" as const,
  }));
}

function renderPage() {
  return render(<MemoryRouter><CapacityPage /></MemoryRouter>);
}

async function beginDowngrade(classCount = 3) {
  vi.mocked(classService.listClasses).mockResolvedValue(activeClasses(classCount));
  fireEvent.click(await screen.findByRole("button", { name: "Lên lịch hạ sức chứa" }));
  return screen.findByRole("checkbox", { name: "Tạm ngưng lớp Lớp 1" });
}

beforeEach(() => {
  vi.spyOn(managerBusinessService, "organization").mockResolvedValue(organization);
  vi.spyOn(capacityService, "getCapacity").mockResolvedValue(result(capacity()));
  vi.spyOn(capacityService, "configureCapacity").mockImplementation(async (_organizationId, revision, body) => {
    return result(capacity({ revision: revision + 1, scheduled_change: body.action === "downgrade"
      ? {
        addon_slots: body.addon_slots,
        capacity: 10 + body.addon_slots,
        effective_at: "2026-12-31T00:00:00Z",
        suspend_class_refs: body.suspend_class_refs,
      }
      : null }));
  });
  vi.spyOn(classService, "listClasses").mockResolvedValue(activeClasses());
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("CapacityPage", () => {
  it("shows the included capacity and a no-subscription empty state", async () => {
    vi.mocked(capacityService.getCapacity).mockResolvedValueOnce(result(capacity({
      subscription_id: null,
      capacity: 10,
      active_class_count: 2,
      available_slots: 8,
      subscription_state: "NONE",
      period_start: null,
      period_end: null,
    })));

    renderPage();

    expect(await screen.findByText("Trường chưa có gói sức chứa. Sức chứa mặc định gồm 10 lớp.")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Sức chứa lớp" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Tắt gia hạn" })).toBeNull();
    expect(screen.getAllByText("Chưa có gói").length).toBeGreaterThan(0);
  });

  it("shows scheduled downgrade details and gives unknown subscription states a neutral label", async () => {
    vi.mocked(capacityService.getCapacity).mockResolvedValueOnce(result(capacity({
      subscription_state: "FUTURE_PRIVATE_STATE",
      scheduled_change: {
        addon_slots: 5,
        capacity: 15,
        effective_at: "2026-12-31T00:00:00Z",
        suspend_class_refs: ["class-private-1", "class-private-2"],
      },
    })));

    const { container } = renderPage();

    expect((await screen.findAllByText("Trạng thái chưa xác định")).length).toBeGreaterThan(0);
    expect(screen.getByText("Sức chứa mới").parentElement?.textContent).toContain("15 lớp");
    expect(screen.getByText("Lớp sẽ tạm ngưng").parentElement?.textContent).toContain("2 lớp");
    expect(screen.getByText("Thời điểm áp dụng").parentElement?.textContent).toContain(
      new Date("2026-12-31T00:00:00Z").toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }),
    );
    expect(container.textContent).not.toContain("FUTURE_PRIVATE_STATE");
    expect(container.textContent).not.toContain("class-private");
  });

  it("confirms renewal cancellation and reuses the same key on a retry", async () => {
    vi.mocked(capacityService.configureCapacity)
      .mockRejectedValueOnce(new TypeError("network unavailable"))
      .mockResolvedValueOnce(result(capacity({ revision: 6, subscription_state: "CANCEL_AT_PERIOD_END" })));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Tắt gia hạn" }));
    expect(capacityService.configureCapacity).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tắt gia hạn" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tắt gia hạn" }));

    await waitFor(() => expect(capacityService.configureCapacity).toHaveBeenCalledTimes(2));
    const first = vi.mocked(capacityService.configureCapacity).mock.calls[0];
    const second = vi.mocked(capacityService.configureCapacity).mock.calls[1];
    expect(first.slice(0, 3)).toEqual(["org-qa", 5, { action: "cancel_renewal" }]);
    expect(second[3]).toBe(first[3]);
    expect(await screen.findByRole("status")).toBeTruthy();
  });

  it("clears the downgrade key when a selected input changes", async () => {
    vi.mocked(capacityService.getCapacity).mockResolvedValueOnce(result(capacity({
      capacity: 12,
      active_class_count: 12,
      available_slots: 0,
    })));
    vi.mocked(classService.listClasses).mockResolvedValue(activeClasses(12));
    vi.mocked(capacityService.configureCapacity)
      .mockRejectedValueOnce(new TypeError("network unavailable"))
      .mockResolvedValueOnce(result(capacity({ capacity: 10, revision: 6 })));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Lên lịch hạ sức chứa" }));
    fireEvent.click(await screen.findByRole("checkbox", { name: "Tạm ngưng lớp Lớp 1" }));
    fireEvent.click(screen.getByRole("button", { name: "Xem lại thay đổi" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận hạ sức chứa" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    const firstKey = vi.mocked(capacityService.configureCapacity).mock.calls[0][3];

    fireEvent.click(screen.getByRole("button", { name: "Sửa lựa chọn" }));
    fireEvent.change(screen.getByLabelText("Số slot bổ sung sau khi hạ"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("checkbox", { name: "Tạm ngưng lớp Lớp 1" }));
    fireEvent.click(screen.getByRole("checkbox", { name: "Tạm ngưng lớp Lớp 2" }));
    fireEvent.click(screen.getByRole("button", { name: "Xem lại thay đổi" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận hạ sức chứa" }));

    await waitFor(() => expect(capacityService.configureCapacity).toHaveBeenCalledTimes(2));
    const calls = vi.mocked(capacityService.configureCapacity).mock.calls;
    expect(calls[0][2]).toEqual({ action: "downgrade", addon_slots: 1, suspend_class_refs: ["class-private-1"] });
    expect(calls[1][2]).toEqual({ action: "downgrade", addon_slots: 0, suspend_class_refs: ["class-private-1", "class-private-2"] });
    expect(calls[1][3]).not.toBe(firstKey);
  });

  it("reloads after a stale revision and uses the newly loaded revision", async () => {
    vi.mocked(capacityService.getCapacity)
      .mockResolvedValueOnce(result(capacity({ revision: 5 })))
      .mockResolvedValueOnce(result(capacity({ revision: 6 })));
    vi.mocked(capacityService.configureCapacity)
      .mockRejectedValueOnce(new CapacityServiceError("stale", 409, "STALE_REVISION", 6))
      .mockResolvedValueOnce(result(capacity({ revision: 7 })));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Tắt gia hạn" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tắt gia hạn" }));

    expect(await screen.findByText("Thông tin sức chứa đã thay đổi. Hãy xem lại trước khi xác nhận.")).toBeTruthy();
    expect(capacityService.getCapacity).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("button", { name: "Xác nhận tắt gia hạn" })).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Tắt gia hạn" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận tắt gia hạn" }));
    await waitFor(() => expect(capacityService.configureCapacity).toHaveBeenCalledTimes(2));
    expect(vi.mocked(capacityService.configureCapacity).mock.calls[1][1]).toBe(6);
  });

  it.each([
    ["CLASS_SELECTION_REQUIRED", "Hãy chọn đủ số lớp cần tạm ngưng trước khi xác nhận."],
    ["INVALID_CAPACITY_DOWNGRADE", "Mức sức chứa hoặc danh sách lớp chưa hợp lệ. Hãy kiểm tra lại lựa chọn."],
  ])("shows a safe message for %s", async (code, message) => {
    vi.mocked(capacityService.getCapacity).mockResolvedValueOnce(result(capacity({
      capacity: 12,
      active_class_count: 12,
      available_slots: 0,
    })));
    vi.mocked(classService.listClasses).mockResolvedValue(activeClasses(12));
    vi.mocked(capacityService.configureCapacity).mockRejectedValueOnce(new CapacityServiceError("private backend body", 422, code));

    renderPage();
    await beginDowngrade(12);
    fireEvent.click(screen.getByRole("checkbox", { name: "Tạm ngưng lớp Lớp 1" }));
    fireEvent.click(screen.getByRole("button", { name: "Xem lại thay đổi" }));
    fireEvent.click(screen.getByRole("button", { name: "Xác nhận hạ sức chứa" }));

    expect(await screen.findByText(message)).toBeTruthy();
    expect(screen.queryByText("private backend body")).toBeNull();
    expect(screen.queryByText(code)).toBeNull();
  });
});
