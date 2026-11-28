import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { KoiHero } from "../KoiHero";

const mountKoiScene = vi.fn();
vi.mock("../koiScene", () => ({ mountKoiScene: (...args: unknown[]) => mountKoiScene(...args) }));

afterEach(() => {
  cleanup();
  mountKoiScene.mockReset();
  vi.unstubAllGlobals();
});

function stubBrowser({ reducedMotion }: { reducedMotion: boolean }) {
  vi.stubGlobal("WebGLRenderingContext", function WebGLRenderingContext() { /* presence check only */ });
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: reducedMotion && query.includes("reduce"),
    media: query,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
  }));
}

describe("KoiHero", () => {
  it("shows the still picture and never loads the scene when WebGL is missing", async () => {
    const { container } = render(<KoiHero />);
    const stage = container.querySelector(".s2l-koi");
    expect(stage?.getAttribute("aria-hidden")).toBe("true");
    expect(stage?.getAttribute("data-koi-state")).toBe("still");
    const still = container.querySelector("img.s2l-koi-still");
    expect(still?.getAttribute("alt")).toBe("");
    expect(still?.getAttribute("src")).toContain("sketch2life-koi-still.webp");
    expect(container.querySelector("canvas")).toBeNull();
    await Promise.resolve();
    expect(mountKoiScene).not.toHaveBeenCalled();
  });

  it("shows the still picture without bubbles when reduced motion is requested", () => {
    stubBrowser({ reducedMotion: true });
    const { container } = render(<KoiHero />);
    expect(container.querySelector("img.s2l-koi-still")).toBeTruthy();
    expect(container.querySelectorAll(".s2l-koi-bubble")).toHaveLength(0);
    expect(mountKoiScene).not.toHaveBeenCalled();
  });

  it("shows nothing while the model loads, then releases the scene on unmount", async () => {
    stubBrowser({ reducedMotion: false });
    const dispose = vi.fn();
    mountKoiScene.mockReturnValue(dispose);
    const { container, unmount } = render(<KoiHero className="hero-koi" />);
    const stage = container.querySelector(".s2l-koi.hero-koi");
    expect(stage?.getAttribute("data-koi-state")).toBe("loading");
    expect(container.querySelector("img")).toBeNull();
    await vi.waitFor(() => expect(mountKoiScene).toHaveBeenCalledTimes(1));
    expect(mountKoiScene.mock.calls[0][0].modelUrl).toContain("sketch2life-koi.glb");
    unmount();
    expect(dispose).toHaveBeenCalledTimes(1);
  });

  it("falls back to the still picture when the scene reports a failure", async () => {
    stubBrowser({ reducedMotion: false });
    mountKoiScene.mockImplementation(({ onFail }: { onFail: () => void }) => { queueMicrotask(onFail); return () => undefined; });
    const { container } = render(<KoiHero />);
    await vi.waitFor(() => expect(container.querySelector("img.s2l-koi-still")).toBeTruthy());
    expect(container.querySelector(".s2l-koi")?.getAttribute("data-koi-state")).toBe("still");
  });
});
