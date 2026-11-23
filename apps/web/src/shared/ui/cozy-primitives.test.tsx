import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Section } from "./Section";
import { StatCard } from "./StatCard";

describe("cozy shared primitives", () => {
  it("supports plain titled sections for metric grids", () => {
    const { container } = render(<Section title="Tình trạng hệ thống" variant="plain"><div>metrics</div></Section>);
    expect(screen.getByRole("heading", { name: "Tình trạng hệ thống" })).toBeTruthy();
    expect(container.querySelector("section")?.className).toContain("overflow-visible");
    expect(container.querySelector("section")?.className).not.toContain("border-rule");
  });

  it("keeps numbers prominent and status sentences compact", () => {
    const { container } = render(<><StatCard label="Tác vụ" value={42} /><StatCard label="Trạng thái" value="Chưa xác nhận" /></>);
    const values = container.querySelectorAll("article p");
    expect(values[1].className).toContain("text-2xl");
    expect(values[3].className).toContain("text-lg");
    expect(values[3].className).toContain("font-semibold");
  });
});
