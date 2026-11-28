import { describe, expect, it } from "vitest";
import { toTeacherSketchDeck } from "../teacherSketchDeckAdapter";
import type { CurrentSketchDeck, SketchDeckRevision, SketchDeckStep } from "../../../../shared/api/teacherOccurrenceApi";

const revision: SketchDeckRevision = {
  contract: "SketchDeckRevisionV1",
  sketch_deck_revision_id: "deck-rev-1",
  occurrence_id: "occ-1",
  plan_revision_id: "plan-rev-1",
  revision_no: 1,
  plan_content_hash: "a".repeat(64),
  review_confirmed: true,
  topic: "A tree",
  drawing_steps: [],
  subject_knowledge: [],
  target_age_band: "age-36-71-months-v1",
  deck_schema_version: "sketch2life.teacher-sketch-deck.v1",
  state: "READY",
  content_hash: "b".repeat(64),
  created_at: "2026-11-26T00:00:00Z",
  ready_at: "2026-11-26T00:00:01Z",
  superseded_at: null,
};

function step(index: number, group = "guide-a", activity: string | null = "activity-a"): SketchDeckStep {
  return {
    sketch_deck_step_id: `step-${group}-${index}`,
    plan_activity_id: activity,
    instruction_group_key: group,
    step_index: index,
    step_kind: "DRAW",
    subject_key: "tree",
    short_title: `Tree part ${index}`,
    child_facing_prompt: `Draw tree part ${index}.`,
    teacher_explanation: `Teacher note ${index}.`,
    bounded_layout_hints: { region: `region-${index}` },
    line_sketch_asset_ref: null,
    line_sketch_asset_version: null,
    source_job_ref: null,
    state: "READY",
    created_at: "2026-11-26T00:00:00Z",
  };
}

function drawingHint(index: number) {
  return {
    viewbox: [0, 0, 100, 100],
    strokes: [{ kind: "line", x1: index, y1: 0, x2: index + 1, y2: 1, stroke: "#1f2937", stroke_width: 2 }],
    source: "recipe",
    sha256: "c".repeat(64),
  };
}

function current(steps: SketchDeckStep[], overrides: Partial<SketchDeckRevision> = {}): CurrentSketchDeck {
  return {
    contract: "SketchDeckCurrentV1",
    occurrence_id: "occ-1",
    current_revision: { ...revision, ...overrides },
    steps,
    stale: false,
    presentable: true,
  };
}

describe("Teacher Sketch Deck adapter", () => {
  it("maps backend instruction groups and source text into the existing presentation shape", () => {
    const deck = toTeacherSketchDeck(current([
      ...Array.from({ length: 4 }, (_, index) => step(index + 1)),
      ...Array.from({ length: 4 }, (_, index) => step(index + 1, "guide-b", "activity-b")),
    ]));

    expect(deck).not.toBeNull();
    expect(deck).toMatchObject({ topic: "A tree", ageMonths: 54 });
    expect(deck?.slides).toHaveLength(2);
    expect(deck?.slides[0]).toMatchObject({
      slideIndex: 1, kind: "drawing_guide", title: "Tree part 1", activityRef: "activity-a",
      bullets: [], goal: [], materials: [], preparation: [], instructions: [], safetyNotes: [],
    });
    expect(deck?.slides[0].steps).toHaveLength(4);
    expect(deck?.slides[0].steps[0]).toEqual({ stepIndex: 1, instruction: "Draw tree part 1.", placement: "Teacher note 1." });
    expect(deck?.slides[1]).toMatchObject({ slideIndex: 2, kind: "drawing_guide", activityRef: "activity-b" });
    expect(deck?.slides[1].steps).toHaveLength(4);
  });

  it("fails closed for unsupported age bands and invalid groups", () => {
    expect(toTeacherSketchDeck(current(Array.from({ length: 4 }, (_, index) => step(index + 1)), { target_age_band: "unknown" }))).toBeNull();
    expect(toTeacherSketchDeck(current([step(1)]))).toBeNull();
  });

  it("maps one structured drawing stroke group onto each step", () => {
    const steps = Array.from({ length: 4 }, (_, index) => ({
      ...step(index + 1),
      bounded_layout_hints: { drawing: drawingHint(index) },
    }));

    const deck = toTeacherSketchDeck(current(steps));

    expect(deck?.slides[0]?.steps.map((item) => item.drawing?.strokes[0])).toEqual(
      [0, 1, 2, 3].map((index) => ({
        kind: "line", x1: index, y1: 0, x2: index + 1, y2: 1, stroke: "#1f2937", stroke_width: 2,
      })),
    );
  });

  it("hides malformed or incomplete drawing metadata while keeping the text steps", () => {
    const steps = Array.from({ length: 4 }, (_, index) => ({
      ...step(index + 1),
      bounded_layout_hints: { drawing: drawingHint(index) },
    }));
    const third = steps[2];
    if (!third) throw new Error("The four-step guide should include a third step");
    steps[2] = {
      ...third,
      bounded_layout_hints: {
        drawing: { ...drawingHint(2), strokes: [{ kind: "path", d: "M0 0" }] },
      } as unknown as typeof third.bounded_layout_hints,
    };

    const deck = toTeacherSketchDeck(current(steps));

    expect(deck?.slides[0]?.steps.every((item) => item.drawing === undefined)).toBe(true);
    expect(deck?.slides[0]?.steps.map((item) => item.instruction)).toHaveLength(4);
  });

  it("orders slides by approved activity order, keeps group key order, and prefers plan titles", () => {
    const deck = toTeacherSketchDeck(current([
      ...Array.from({ length: 4 }, (_, index) => step(index + 1, "z-guide", "activity-b")),
      ...Array.from({ length: 4 }, (_, index) => step(index + 1, "b-guide", "activity-a")),
      ...Array.from({ length: 4 }, (_, index) => step(index + 1, "a-guide", "activity-a")),
    ]), [
      { plan_activity_id: "activity-b", order: 2, title: null },
      { plan_activity_id: "activity-a", order: 1, title: "Plan activity A" },
    ]);

    expect(deck?.slides.map((slide) => slide.activityRef)).toEqual(["activity-a", "activity-a", "activity-b"]);
    expect(deck?.slides.map((slide) => slide.title)).toEqual(["Plan activity A", "Plan activity A", "Tree part 1"]);
    expect(deck?.slides[0].steps[0].instruction).toBe("Draw tree part 1.");
  });
});
