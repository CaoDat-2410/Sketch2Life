import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { CatalogPage } from "../AdminContentPages";

beforeEach(() => {
  window.sketch2lifeAuth = { getIdToken: async () => "synthetic-catalog-header-token" };
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ items: [], total: 0, next_cursor: null }), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  })));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  delete window.sketch2lifeAuth;
});

describe("Platform Admin activity catalog header", () => {
  it("shows the title, description, and primary action without a decorative chip", () => {
    render(<CatalogPage />);

    const title = screen.getByRole("heading", { level: 1, name: "Danh mục hoạt động" });
    const header = title.closest("header");
    expect(screen.getByText("Quản lý và duyệt hoạt động dùng chung.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Thêm hoạt động" })).toBeTruthy();
    expect(header?.querySelector('span[aria-hidden="true"]')).toBeNull();
  });
});
