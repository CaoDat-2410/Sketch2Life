import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const theme = readFileSync(resolve(process.cwd(), "src/shared/styles/tokens.css"), "utf8");
const customProperties = new Set(theme.match(/--s2l-ui-[a-z0-9-]+(?=\s*:)/g) ?? []);

describe("cozy portal palette tokens", () => {
  it("binds the visible teacher header band to both real page headers", () => {
    const css = readFileSync(resolve(process.cwd(), "src/shared/styles/koi-wave1.css"), "utf8");
    const session = readFileSync(resolve(process.cwd(), "src/modules/teacher/pages/TeacherOccurrencePage.tsx"), "utf8");
    const lesson = readFileSync(resolve(process.cwd(), "src/modules/teacher/pages/TeacherApiLessonPage.tsx"), "utf8");
    expect(session).toMatch(/className="s2l-data-card koi-teacher-band"/);
    expect(lesson).toMatch(/className="tw-row tw-between tw-wrap koi-teacher-band teacher-lesson-heading"/);
    expect(css).toMatch(/\.koi-teacher-band\.koi-teacher-band\s*\{[^}]*background:\s*var\(--s2l-ui-hero-wash\)\s*!important/);
  });
  it("keeps key control foreground and background token pairs at WCAG AA", () => {
    const value = (name) => {
      const raw = theme.match(new RegExp(`${name}:\\s*([^;]+);`))?.[1].trim();
      if (raw?.startsWith("var(")) return value(raw.slice(4, -1));
      return raw;
    };
    const luminance = (hex) => {
      const rgb = hex.match(/[\da-f]{2}/gi).map((part) => parseInt(part, 16) / 255);
      return rgb.map((v) => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4)
        .reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
    };
    for (const background of ["#E6D8F8", "#F1E4F6", "#FBE9EC"]) {
      const levels = [luminance(value("--s2l-ui-ink")), luminance(background)].sort((a, b) => b - a);
      expect((levels[0] + 0.05) / (levels[1] + 0.05), `hero ink on ${background}`).toBeGreaterThanOrEqual(4.5);
    }
    for (const [ink, background] of [
      ["--s2l-ui-on-primary", "--s2l-ui-primary"],
      ["--s2l-ui-primary-disabled-ink", "--s2l-ui-primary-disabled"],
      ["--s2l-ui-danger-ink", "--s2l-ui-danger-soft"],
      ["--s2l-ui-success-ink", "--s2l-ui-success-soft"],
      ["--s2l-ui-neutral-ink", "--s2l-ui-neutral-soft"],
      ["--s2l-ui-ink", "--s2l-ui-sidebar"],
      ["--s2l-ui-ink", "--s2l-ui-cream"],
      ["--s2l-ui-primary-hover", "--s2l-ui-active-nav"],
    ]) {
      const levels = [luminance(value(ink)), luminance(value(background))].sort((a, b) => b - a);
      expect((levels[0] + 0.05) / (levels[1] + 0.05), `${ink} on ${background}`).toBeGreaterThanOrEqual(4.5);
    }
  });
  it("exposes primary, accent and status variables from the single token file", () => {
    [
      "--s2l-ui-primary",
      "--s2l-ui-primary-soft",
      "--s2l-ui-primary-ink",
      "--s2l-ui-primary-hover",
      "--s2l-ui-on-primary",
      "--s2l-ui-primary-gradient-start",
      "--s2l-ui-primary-gradient-end",
      "--s2l-ui-primary-disabled",
      "--s2l-ui-primary-disabled-ink",
      "--s2l-ui-focus",
      "--s2l-ui-section-header",
      "--s2l-ui-row-hover",
      "--s2l-ui-row-selected",
      "--s2l-ui-sidebar",
      "--s2l-ui-chart-violet",
      "--s2l-ui-chart-coral",
      "--s2l-ui-chart-butter",
      "--s2l-ui-chart-sky",
      "--s2l-ui-chart-mint",
      "--s2l-ui-coral",
      "--s2l-ui-butter",
      "--s2l-ui-sky",
      "--s2l-ui-mint",
      "--s2l-ui-success-soft",
      "--s2l-ui-success-ink",
      "--s2l-ui-warn-soft",
      "--s2l-ui-warn-ink",
      "--s2l-ui-danger-soft",
      "--s2l-ui-danger-ink",
      "--s2l-ui-info-soft",
      "--s2l-ui-info-ink",
      "--s2l-ui-neutral-soft",
      "--s2l-ui-neutral-ink",
    ].forEach((name) => expect(customProperties.has(name), `${name} is defined`).toBe(true));

    // Tokens are declared on :root so every route, including 404, gets them.
    // Dark mode is out of scope; no dark block exists.
    expect(theme).toContain(":root {");
    expect(theme).not.toContain('data-theme="dark"');
    expect(theme).toContain("--s2l-ui-primary: #7435D5;");
    expect(theme).toContain("--s2l-ui-cream: #FFFAF6;");
    expect(theme).not.toContain("var(--color-accent, #245b9b)");
    expect(theme).not.toContain("var(--color-accent-strong, #1d4c82)");
  });
});
