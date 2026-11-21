import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { Activity } from "lucide-react";
import { Button, Card, CloudDoodle, CrayonStub, DataTable, EmptyState, PageHeader, PencilMark, Section, ScribbleUnderline, StatCard, StatusBadge, Tabs } from "..";

afterEach(() => cleanup());

describe("shared cozy UI primitives", () => {
  it("renders Card content, optional regions, and tone variants", () => {
    render(<Card header={<span>Card header</span>} footer={<span>Card footer</span>} tone="info">Card body</Card>);
    const card = screen.getByRole("article");
    expect(within(card).getByText("Card header")).toBeTruthy();
    expect(within(card).getByText("Card body")).toBeTruthy();
    expect(within(card).getByText("Card footer")).toBeTruthy();
    expect(card.className).toContain("bg-sky-soft");
  });

  it("renders a named Section with description and actions", () => {
    render(<Section title="Queue" description="Current work" actions={<button type="button">Refresh</button>}><p>Rows</p></Section>);
    expect(screen.getByRole("region", { name: "Queue" })).toBeTruthy();
    expect(screen.getByText("Current work")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Refresh" })).toBeTruthy();
  });

  it("renders PageHeader without a decorative illustration chip", () => {
    const { container } = render(<PageHeader title="Operations" description="Status overview" actions={<button type="button">Reload</button>} />);
    const header = container.querySelector("header");
    expect(screen.getByRole("heading", { level: 1, name: "Operations" })).toBeTruthy();
    expect(screen.getByText("Status overview")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Reload" })).toBeTruthy();
    expect(header?.querySelector('span[aria-hidden="true"]')).toBeNull();
    expect(header?.querySelector('svg[aria-hidden="true"]')).toBeNull();
  });

  it("renders StatCard trend content and exposes its loading state", () => {
    const { rerender } = render(<StatCard label="Jobs" value="1,024" icon={<Activity />} trend={{ direction: "up", delta: "12%", tone: "success" }} />);
    expect(screen.getByText("1,024")).toBeTruthy();
    expect(screen.getByText("12%")).toBeTruthy();
    rerender(<StatCard label="Jobs" value="1,024" loading />);
    expect(screen.getByRole("article").getAttribute("aria-busy")).toBe("true");
    expect(screen.queryByText("1,024")).toBeNull();
  });

  it("renders StatusBadge tone, size, and an optional dot", () => {
    const { container } = render(<StatusBadge tone="warn" size="sm" dot>Pending</StatusBadge>);
    expect(screen.getByText("Pending").className).toContain("min-w-0");
    expect(container.querySelector("span.bg-butter")?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.getByText("Pending").parentElement?.className).toContain("bg-butter-soft");
  });

  it("forwards native button props and disables while loading", () => {
    const ref = { current: null as HTMLButtonElement | null };
    render(<Button ref={ref} variant="primary" loading iconLeft={<Activity />}>Save</Button>);
    const button = screen.getByRole("button", { name: "Save" }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    expect(button.getAttribute("aria-busy")).toBe("true");
    expect(ref.current).toBe(button);
    expect(button.className).toContain("bg-primary");
    expect(button.className).toContain("text-on-primary");
  });

  it("moves focus and selection with tab-list arrow keys", () => {
    const onValueChange = vi.fn();
    render(<Tabs label="Views" items={[{ value: "summary", label: "Summary" }, { value: "logs", label: "Logs" }, { value: "settings", label: "Settings", disabled: true }]} value="summary" onValueChange={onValueChange} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs[0].tabIndex).toBe(0);
    fireEvent.keyDown(tabs[0], { key: "ArrowRight" });
    expect(document.activeElement).toBe(tabs[1]);
    expect(onValueChange).toHaveBeenCalledWith("logs");
  });

  it("renders DataTable rows with an accessible caption and numeric cells", () => {
    const columns = [
      { key: "name", header: "Name", render: (row: { name: string; count: number }) => row.name },
      { key: "count", header: "Count", numeric: true, render: (row: { name: string; count: number }) => row.count },
    ];
    render(<DataTable caption="Recent jobs" rows={[{ name: "Drawing", count: 12 }]} columns={columns} getRowKey={(row) => row.name} />);
    const table = screen.getByRole("table", { name: "Recent jobs" });
    expect(within(table).getByRole("row", { name: "Drawing 12" })).toBeTruthy();
    expect(within(table).getByRole("columnheader", { name: "Count" }).className).toContain("text-right");
  });

  it("renders DataTable empty and loading states", () => {
    const columns = [{ key: "name", header: "Name", render: (row: { name: string }) => row.name }];
    const { rerender, container } = render(<DataTable caption="Empty jobs" rows={[]} columns={columns} getRowKey={(row) => row.name} emptyState={<EmptyState title="No jobs" />} />);
    expect(screen.getByText("No jobs")).toBeTruthy();
    rerender(<DataTable caption="Loading jobs" rows={[]} columns={columns} getRowKey={(row) => row.name} loading />);
    expect(screen.getByRole("table", { name: "Loading jobs" }).parentElement?.getAttribute("aria-busy")).toBe("true");
    expect(container.querySelectorAll("tbody tr")).toHaveLength(3);
  });

  it("renders compact EmptyState content and action", () => {
    const { container } = render(<EmptyState title="No records" description="There is nothing to display." action={<Button>Try again</Button>} />);
    expect(screen.getByRole("heading", { level: 3, name: "No records" })).toBeTruthy();
    expect(screen.getByText("There is nothing to display.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
    expect(container.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
  });

  it("renders all illustration accents as decorative SVGs", () => {
    const { container } = render(<><PencilMark /><CrayonStub /><ScribbleUnderline /><CloudDoodle /></>);
    expect(container.querySelectorAll('svg[aria-hidden="true"]')).toHaveLength(4);
  });
});
