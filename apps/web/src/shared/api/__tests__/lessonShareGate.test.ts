import { describe, expect, it } from "vitest";
import { privateShareGate } from "../lessonShareGate";

describe("private share gate", () => {
  it.each(["DRAFT", "PENDING_REVIEW", "CHANGES_REQUESTED", "APPROVED"] as const)("allows an active version in %s", (reviewState) => {
    const lesson = {
      state: "ACTIVE" as const,
      current_version: { version_id: "version-1", review_state: reviewState },
    };
    expect(privateShareGate(lesson)).toEqual({ allowed: true });
  });

  it("blocks only a missing current version or an archived lesson", () => {
    expect(privateShareGate({ state: "ACTIVE", current_version: null })).toEqual({ allowed: false, reason: "NO_CURRENT_VERSION" });
    expect(privateShareGate({ state: "ARCHIVED", current_version: { version_id: "version-1" } })).toEqual({ allowed: false, reason: "ARCHIVED" });
  });
});
