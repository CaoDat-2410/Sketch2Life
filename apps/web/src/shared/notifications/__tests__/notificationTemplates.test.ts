import { describe, expect, it } from "vitest";
import { resolveNotificationText } from "../notificationTemplates";

describe("notification templates", () => {
  it("uses the neutral title for unknown types and versions", () => {
    expect(resolveNotificationText("UNREGISTERED_TYPE", 1)).toEqual({ title: "Thông báo mới" });
    expect(resolveNotificationText("CLASS_ARCHIVED", 9999)).toEqual({ title: "Thông báo mới" });
  });

  it("does not accept producer parameters as display text", () => {
    const safeParameters = { label: "DO_NOT_RENDER" };
    const text = resolveNotificationText("UNREGISTERED_TYPE", 1);
    expect(JSON.stringify(text)).not.toContain(safeParameters.label);
  });
});
