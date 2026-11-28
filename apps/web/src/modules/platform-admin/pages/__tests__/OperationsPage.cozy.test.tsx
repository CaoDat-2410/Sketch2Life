import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { A02PlatformOperationsPage } from "../AdminScreens";
import { Heading } from "../../components/AdminUI";
import { PageHeader } from "../../../../shared/ui";
import type { Operations } from "../../services/adminService";

const emptyOperations: Operations = {
  database: { status: "healthy", response_ms: 31 },
  broker: { status: "healthy", response_ms: 18, queue_count: 2, transport_pending_count: 0, active_workers: 2 },
  queue: { queued_jobs: 0, running_jobs: 0, failed_jobs: 0, oldest_queued_at: null, last_dispatched_at: null, last_started_at: null, last_finished_at: null },
  jobs: [],
  core_outbox: [],
  email: [],
  lifecycle: [],
};

function mockApi(operations: Operations) {
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const requestUrl = String(input);
    const body = requestUrl.endsWith("/health")
      ? { status: "ok", service: "Sketch2Life API" }
      : operations;
    return new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } });
  }));
}

function renderOperationsPage() {
  return render(<MemoryRouter initialEntries={["/platform/a02-platform-operations?panel=queues"]}><A02PlatformOperationsPage /></MemoryRouter>);
}

beforeEach(() => {
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "synthetic-ops-test-token") };
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  delete window.sketch2lifeAuth;
});

describe("Platform Admin operations cozy pilot", () => {
  it("renders Heading and PageHeader content without an aria-hidden illustration chip", () => {
    const { container } = render(<>
      <Heading title="School directory" description="Manage school access">
        <button type="button">Create school</button>
      </Heading>
      <PageHeader title="Audit trail" description="Recent administrator actions" actions={<button type="button">Reload</button>} />
    </>);

    const headers = [...container.querySelectorAll("header")];
    expect(headers).toHaveLength(2);
    expect(headers.every((header) => header.querySelector('span[aria-hidden="true"]') === null)).toBe(true);
    expect(screen.getByRole("heading", { name: "School directory" })).toBeTruthy();
    expect(screen.getByText("Manage school access")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Create school" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Audit trail" })).toBeTruthy();
    expect(screen.getByText("Recent administrator actions")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Reload" })).toBeTruthy();
  });

  it("shows healthy API, database, broker, and active workers", async () => {
    mockApi(emptyOperations);
    renderOperationsPage();
    expect(await screen.findByText("Dịch vụ Sketch2Life")).toBeTruthy();
    expect(screen.getAllByText("Đang hoạt động")).toHaveLength(4);
    expect(screen.getByText("Kết nối ổn định")).toBeTruthy();
  });

  it("keeps unavailable and not_configured dependency states explicit", async () => {
    mockApi({
      ...emptyOperations,
      database: { status: "unavailable", response_ms: 812 },
      broker: { status: "not_configured", response_ms: null, queue_count: null, transport_pending_count: null, active_workers: null },
      queue: { ...emptyOperations.queue, queued_jobs: 12, running_jobs: 3, failed_jobs: 7 },
      jobs: [{ state: "failed", count: 7, job_type: "story_generation" }],
    });
    renderOperationsPage();
    expect(await screen.findByText("Không khả dụng")).toBeTruthy();
    expect(screen.getAllByText("Chưa cấu hình")).toHaveLength(2);
    expect(screen.getByText("Phản hồi 812 ms")).toBeTruthy();
    expect(screen.getByText("Cần chú ý").closest("article")?.textContent).toContain("7");
  });

  it("formats queue summary numbers for vi-VN and keeps existing empty table copy", async () => {
    mockApi({
      ...emptyOperations,
      queue: {
        queued_jobs: 1234567,
        running_jobs: 2345,
        failed_jobs: 12,
        oldest_queued_at: null,
        last_dispatched_at: null,
        last_started_at: null,
        last_finished_at: null,
      },
      broker: { ...emptyOperations.broker, transport_pending_count: 8765 },
    });
    renderOperationsPage();
    expect(await screen.findByText("1.234.567")).toBeTruthy();
    expect(screen.getByText("2.345")).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy();
    expect(screen.getByText("8.765")).toBeTruthy();
    expect(screen.getByText("Chưa có bản ghi công việc AI")).toBeTruthy();
    expect(screen.getByText("Chưa có bản ghi sự kiện chờ xử lý")).toBeTruthy();
    expect(screen.getByText("Chưa có bản ghi gửi email")).toBeTruthy();
    expect(screen.getByText("Chưa có bản ghi vòng đời dữ liệu")).toBeTruthy();
  });
});
