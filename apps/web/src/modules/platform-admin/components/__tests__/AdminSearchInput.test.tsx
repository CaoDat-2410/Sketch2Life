import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { AdminSearchInput } from "../AdminSearchInput";
import { SearchForm } from "../AdminUI";

afterEach(cleanup);

function expectSingleSearchBox(input: HTMLInputElement) {
  const label = input.closest("label");
  expect(label).not.toBeNull();

  let borderedAncestors = 0;
  let ancestor = input.parentElement;
  while (ancestor && ancestor !== label) {
    if ([...ancestor.classList].some((token) => token === "border" || token.startsWith("border-"))) {
      borderedAncestors += 1;
    }
    ancestor = ancestor.parentElement;
  }

  expect(borderedAncestors).toBe(1);
  expect(label?.classList.contains("border")).toBe(false);
}

describe("Platform Admin search input", () => {
  it("keeps one bordered box, an accessible name, and reports typed values", () => {
    const onValueChange = vi.fn();
    render(
      <AdminSearchInput
        label="Search by account"
        placeholder="Email or display name"
        value=""
        onValueChange={onValueChange}
      />,
    );

    const input = screen.getByRole("searchbox", { name: "Search by account" }) as HTMLInputElement;
    expectSingleSearchBox(input);
    fireEvent.change(input, { target: { value: "hoa mai" } });
    expect(onValueChange).toHaveBeenCalledWith("hoa mai");
  });

  it("uses the same single-box structure in SearchForm and submits typed text", () => {
    const onSearch = vi.fn();
    render(<SearchForm placeholder="Find an administrator" onSearch={onSearch} />);

    const input = screen.getByRole("searchbox", { name: "Find an administrator" }) as HTMLInputElement;
    expectSingleSearchBox(input);
    fireEvent.change(input, { target: { value: " hoa mai " } });
    fireEvent.submit(input.closest("form") as HTMLFormElement);
    expect(onSearch).toHaveBeenCalledWith("hoa mai");
  });
});
