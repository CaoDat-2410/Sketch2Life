import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { authService } from "../../../school-manager/be1/services/authService";
import { clearAiWorkflowSession, useAiWorkflowState } from "../aiWorkflowSession";
import {
  beginAiTask,
  clearAiTaskStatus,
  finishAiTask,
  getAiTaskAggregateStatus,
  getAiTaskMark,
  scheduleAiTaskStatusSeen,
  svgTaskStatusKey,
} from "../aiTaskStatus";
import { clearSvgDraftRequests, startSvgDraftRequest } from "../svgDraftRequests";

afterEach(() => {
  cleanup();
  clearAiWorkflowSession();
  clearSvgDraftRequests();
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("AI task status", () => {
  it("aggregates pending before failed, failed before done, and done before nothing", () => {
    const suggestionRun = beginAiTask("suggestion");
    finishAiTask("suggestion", suggestionRun, "done");
    expect(getAiTaskAggregateStatus()).toBe("done");

    const failedSvgKey = svgTaskStatusKey("occ-failed");
    const failedSvgRun = beginAiTask(failedSvgKey);
    finishAiTask(failedSvgKey, failedSvgRun, "failed");
    expect(getAiTaskAggregateStatus()).toBe("failed");

    const svgRun = beginAiTask(svgTaskStatusKey("occ-1"));
    expect(getAiTaskAggregateStatus()).toBe("pending");
    expect(getAiTaskMark(failedSvgKey)?.status).toBe("failed");
    finishAiTask(svgTaskStatusKey("occ-1"), svgRun, "done");
  });

  it("keeps a failed request failed instead of showing done", () => {
    const runId = beginAiTask("suggestion");
    expect(finishAiTask("suggestion", runId, "failed")).toBe(true);
    expect(getAiTaskMark("suggestion")?.status).toBe("failed");
    expect(getAiTaskAggregateStatus()).toBe("failed");
    expect(finishAiTask("suggestion", runId, "done")).toBe(false);
  });

  it("clears a finished mark after four seconds once seen", () => {
    vi.useFakeTimers();
    const runId = beginAiTask("suggestion");
    finishAiTask("suggestion", runId, "done");
    scheduleAiTaskStatusSeen("suggestion", runId);

    vi.advanceTimersByTime(3_999);
    expect(getAiTaskMark("suggestion")?.status).toBe("done");
    vi.advanceTimersByTime(1);
    expect(getAiTaskMark("suggestion")).toBeUndefined();
  });

  it("does not let an older seen timer clear a new request for the same key", () => {
    vi.useFakeTimers();
    const oldRun = beginAiTask("suggestion");
    finishAiTask("suggestion", oldRun, "done");
    scheduleAiTaskStatusSeen("suggestion", oldRun);

    const newRun = beginAiTask("suggestion");
    vi.advanceTimersByTime(4_000);
    expect(getAiTaskMark("suggestion")).toEqual({ status: "pending", runId: newRun });
  });

  it("ignores a result from before its status was cleared", () => {
    const oldRun = beginAiTask("suggestion");
    clearAiTaskStatus("suggestion");
    expect(finishAiTask("suggestion", oldRun, "done")).toBe(false);
    expect(getAiTaskMark("suggestion")).toBeUndefined();
  });

  it("clears only workflow marks when the workflow session resets", () => {
    beginAiTask("suggestion");
    const svgKey = svgTaskStatusKey("occ-1");
    const svgRun = beginAiTask(svgKey);

    clearAiWorkflowSession();

    expect(getAiTaskMark("suggestion")).toBeUndefined();
    expect(getAiTaskMark(svgKey)?.status).toBe("pending");
    expect(finishAiTask(svgKey, svgRun, "done")).toBe(true);
  });

  it("clears only SVG marks when the SVG request source resets", () => {
    const suggestionRun = beginAiTask("suggestion");
    const svgKey = svgTaskStatusKey("occ-1");
    beginAiTask(svgKey);

    clearSvgDraftRequests();

    expect(getAiTaskMark("suggestion")?.status).toBe("pending");
    expect(getAiTaskMark(svgKey)).toBeUndefined();
    expect(finishAiTask("suggestion", suggestionRun, "done")).toBe(true);
  });

  it("clears each source on an account change and ignores both old results", async () => {
    const observers: Array<Parameters<typeof authService.observe>[0]> = [];
    vi.spyOn(authService, "observe").mockImplementation((callback) => {
      observers.push(callback);
      callback({ uid: "teacher-1" } as never);
      return () => undefined;
    });
    const workflow = renderHook(() => useAiWorkflowState("account-change-test", ""));
    const suggestionRun = beginAiTask("suggestion");
    let finishSvg: ((value: never) => void) | undefined;
    startSvgDraftRequest("occ-1", "account-change-signature", () => new Promise((resolve) => {
      finishSvg = resolve as (value: never) => void;
    }));
    const svgKey = svgTaskStatusKey("occ-1");
    expect(observers).toHaveLength(2);
    expect(getAiTaskMark("suggestion")?.status).toBe("pending");
    expect(getAiTaskMark(svgKey)?.status).toBe("pending");

    act(() => observers.forEach((callback) => callback(null)));

    expect(getAiTaskMark("suggestion")).toBeUndefined();
    expect(getAiTaskMark(svgKey)).toBeUndefined();
    expect(finishAiTask("suggestion", suggestionRun, "done")).toBe(false);
    await act(async () => {
      finishSvg?.({} as never);
      await Promise.resolve();
    });
    expect(getAiTaskMark(svgKey)).toBeUndefined();
    workflow.unmount();
  });
});
