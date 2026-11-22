import { describe, expect, it } from "vitest";
import { BackendApiError } from "../../../../shared/api/backendApi";
import { ActionKeys } from "../actionKeys";

describe("Teacher action keys", () => {
  it("keeps a retry key but changes it for revisions and completed actions", () => {
    const keys = new ActionKeys();
    const action = ["confirm", "selection", 1, "hash"];
    const first = keys.key(...action);
    expect(keys.key(...action)).toBe(first);
    expect(keys.key("confirm", "selection", 2, "hash")).not.toBe(first);
    keys.settled(action, new BackendApiError("", "NETWORK_ERROR", 0));
    expect(keys.key(...action)).toBe(first);
    keys.settled(action, new BackendApiError("", "STALE_REVISION", 409));
    expect(keys.key(...action)).not.toBe(first);
    const draw = keys.key("draw", "occurrence");
    keys.settled(["draw", "occurrence"]);
    expect(keys.key("draw", "occurrence")).not.toBe(draw);
  });
});
