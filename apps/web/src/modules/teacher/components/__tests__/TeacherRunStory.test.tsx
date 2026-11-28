import { afterEach, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { TeacherRunStory } from "../TeacherRunStory";
import type { TeacherRun } from "../../../../shared/api/teacherRunApi";

afterEach(cleanup);

const run = (scene: { action: string; narration: string }) => ({
  run_id: "run", run_state: "SCRIPT_REVIEW", story_revision_no: 1, story_status: "DRAFT", story_sha256: "h",
  story: { title: "Story", story: { opening: "a", middle: "b", ending: "c" }, scenes: [{ title: "Scene", ...scene }] },
  video: null,
}) as unknown as TeacherRun;

it("shows a narration that repeats the action only once", () => {
  render(<TeacherRunStory run={run({ action: "The cat sits.", narration: "The cat sits." })} execute={vi.fn()} />);
  expect(screen.getAllByText("The cat sits.")).toHaveLength(1);
});

it("keeps an action that differs from the narration", () => {
  render(<TeacherRunStory run={run({ action: "The cat jumps.", narration: "The cat sits." })} execute={vi.fn()} />);
  expect(screen.getByText("The cat jumps.")).toBeTruthy();
  expect(screen.getByText("The cat sits.")).toBeTruthy();
});
