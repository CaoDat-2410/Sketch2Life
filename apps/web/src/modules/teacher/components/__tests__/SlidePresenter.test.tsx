import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { SlidePresenter } from "../SlidePresenter";

const fullscreenRequest = vi.fn<() => Promise<void>>();
const originalFullscreenDescriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "requestFullscreen");

function PresenterFixture() {
  const [slideIndex, setSlideIndex] = useState(0);
  return (
    <SlidePresenter
      revisionLabel="Bản nháp"
      slideIndex={slideIndex}
      slideCount={2}
      onPrevious={() => setSlideIndex((index) => Math.max(0, index - 1))}
      onNext={() => setSlideIndex((index) => Math.min(1, index + 1))}
    >
      {({ isPresenting, trigger }) => (
        <section aria-label="Xem trước slide">
          <div className="preview-heading">Xem trước {trigger}</div>
          <p>Slide nội dung {slideIndex + 1}</p>
          {!isPresenting && <button type="button">Nút trong trang</button>}
        </section>
      )}
    </SlidePresenter>
  );
}

beforeEach(() => {
  fullscreenRequest.mockReset().mockResolvedValue(undefined);
  Object.defineProperty(HTMLElement.prototype, "requestFullscreen", {
    configurable: true,
    writable: true,
    value: fullscreenRequest,
  });
});

afterEach(() => {
  cleanup();
  if (originalFullscreenDescriptor) Object.defineProperty(HTMLElement.prototype, "requestFullscreen", originalFullscreenDescriptor);
  else Reflect.deleteProperty(HTMLElement.prototype, "requestFullscreen");
});

describe("SlidePresenter", () => {
  it("requests browser fullscreen when available and presents with keyboard and button navigation", async () => {
    render(<PresenterFixture />);
    const trigger = screen.getByRole("button", { name: "Trình chiếu" });
    fireEvent.click(trigger);

    const dialog = screen.getByRole("dialog", { name: "Trình chiếu · Bản nháp" });
    expect(fullscreenRequest).toHaveBeenCalledTimes(1);
    expect(dialog.parentElement?.parentElement).toBe(document.body);
    expect(screen.getByText("Slide nội dung 1")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Thoát" })).toBeTruthy();

    fireEvent.keyDown(document, { key: "ArrowRight" });
    expect(screen.getByText("Slide nội dung 2")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Slide trước" }));
    expect(screen.getByText("Slide nội dung 1")).toBeTruthy();
    expect(dialog.getAttribute("aria-modal")).toBe("true");
  });

  it("traps focus while open and returns it to the trigger on Escape", async () => {
    render(<PresenterFixture />);
    const trigger = screen.getByRole("button", { name: "Trình chiếu" });
    fireEvent.click(trigger);

    const exit = screen.getByRole("button", { name: "Thoát" });
    const next = screen.getByRole("button", { name: "Slide sau" });
    await waitFor(() => expect(document.activeElement).toBe(exit));
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(next);
    fireEvent.keyDown(document, { key: "Tab" });
    expect(document.activeElement).toBe(exit);

    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
    await waitFor(() => expect(document.activeElement).toBe(trigger));
  });
});
