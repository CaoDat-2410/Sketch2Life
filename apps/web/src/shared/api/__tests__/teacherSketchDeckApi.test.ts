import { afterEach, describe, expect, it, vi } from "vitest";
import { teacherOccurrenceApi, type CreateSketchDeckInput } from "../teacherOccurrenceApi";

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  window.sketch2lifeAuth = undefined;
  window.sketch2lifeConfig = undefined;
});

function response(status: number, body: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers({ "X-Request-ID": "deck-request-1" }),
    text: async () => JSON.stringify(body),
  } as Response;
}

function setup(reply: Response) {
  window.sketch2lifeAuth = { getIdToken: vi.fn(async () => "teacher-token") };
  const fetcher = vi.fn(async (_url: string, _init: RequestInit) => reply);
  vi.stubGlobal("fetch", fetcher);
  return fetcher;
}

describe("Teacher Sketch Deck API", () => {
  it("reads the current deck for one encoded occurrence", async () => {
    const current = {
      contract: "SketchDeckCurrentV1",
      occurrence_id: "occ 1",
      current_revision: null,
      steps: [],
      stale: false,
      presentable: false,
    };
    const fetcher = setup(response(200, current));

    await expect(teacherOccurrenceApi.getSketchDeck("occ 1")).resolves.toEqual(current);
    expect(fetcher.mock.calls[0][0]).toContain("/v1/lesson-occurrences/occ%201/sketch-decks");
    expect(fetcher.mock.calls[0][1].method).toBeUndefined();
  });

  it("sends the reviewed plan identity, exact drawing inputs, and command key", async () => {
    const revision = {
      contract: "SketchDeckRevisionV1",
      sketch_deck_revision_id: "deck-rev-1",
      occurrence_id: "occ-1",
      plan_revision_id: "plan-rev-9",
      revision_no: 1,
      plan_content_hash: "a".repeat(64),
      review_confirmed: true,
      topic: "A leaf",
      drawing_steps: [
        { action: "Draw the midrib", placement: "Down the page" },
        { action: "Add a vein", placement: "On the left" },
        { action: "Add another vein", placement: "On the right" },
        { action: "Outline the leaf", placement: "Around the veins" },
      ],
      subject_knowledge: ["Leaves have veins."],
      target_age_band: "age-36-71-months-v1",
      deck_schema_version: "sketch2life.teacher-sketch-deck.v1",
      state: "GENERATING",
      content_hash: null,
      created_at: "2026-11-26T00:00:00Z",
      ready_at: null,
      superseded_at: null,
    };
    const fetcher = setup(response(202, revision));
    const input: CreateSketchDeckInput = {
      expected_plan_revision_id: "plan-rev-9",
      expected_plan_hash: "a".repeat(64),
      review_confirmed: true,
      topic: "A leaf",
      drawing_steps: revision.drawing_steps,
      subject_knowledge: ["Leaves have veins."],
    };

    await expect(teacherOccurrenceApi.createSketchDeck("occ-1", input, "deck-key-1")).resolves.toEqual(revision);
    const [url, init] = fetcher.mock.calls[0];
    const headers = new Headers(init.headers);
    expect(url).toContain("/v1/lesson-occurrences/occ-1/sketch-decks");
    expect(init.method).toBe("POST");
    expect(headers.get("Idempotency-Key")).toBe("deck-key-1");
    expect(headers.get("Authorization")).toBe("Bearer teacher-token");
    expect(JSON.parse(String(init.body))).toEqual(input);
  });
});
