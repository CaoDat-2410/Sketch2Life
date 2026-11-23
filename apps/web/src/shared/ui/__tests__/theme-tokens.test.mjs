import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const theme = readFileSync(resolve(process.cwd(), "src/shared/styles/sketch2life-theme.css"), "utf8");
const customProperties = new Set(theme.match(/--s2l-ui-[a-z0-9-]+(?=\s*:)/g) ?? []);

describe("cozy portal palette tokens", () => {
  it("exposes primary, accent, status, and dark-theme variables", () => {
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

    expect(theme).toContain('html[data-cozy="1"] {');
    expect(theme).toContain('html[data-cozy="1"][data-theme="dark"]:not([data-portal="entry"]) {');
    expect(theme).toContain("--s2l-ui-primary: #7435D5;");
    expect(theme).toContain("--s2l-ui-cream: #FFFAF6;");
    expect(theme).not.toContain("var(--color-accent, #245b9b)");
    expect(theme).not.toContain("var(--color-accent-strong, #1d4c82)");
  });
});
