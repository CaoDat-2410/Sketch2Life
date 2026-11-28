import { afterEach, describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { parseTeacherSketchDeck, TeacherDeckPresentation, type TeacherSketchDeck } from "../TeacherDeckPresentation";

afterEach(cleanup);

function serverDeckWithSteps(
  stepCount: number,
  includeSecondSlide = false,
  placementForStep: (index: number) => string = (index) => `Position ${index + 1}`,
) {
  return {
    schema_version: "sketch2life.teacher-sketch-deck.v1",
    status: "DRAFT",
    aspect_ratio: "16:9",
    review_required: true,
    topic: "Cat",
    target_age_months: 48,
    slides: [
      {
        slide_index: 1,
        kind: "drawing_guide",
        title: "Draw a cat",
        activity_ref: null,
        bullets: [],
        steps: Array.from({ length: stepCount }, (_, index) => ({
          step_index: index + 1,
          instruction: "V\u1ebd b\u01b0\u1edbc " + (index + 1),
          placement: placementForStep(index),
        })),
        goal: [],
        materials: [],
        preparation: [],
        instructions: [],
        safety_notes: [],
      },
      ...(includeSecondSlide ? [{
        slide_index: 2,
        kind: "orientation",
        title: "Opening",
        activity_ref: null,
        bullets: [],
        steps: [],
        goal: [],
        materials: [],
        preparation: [],
        instructions: [],
        safety_notes: [],
      }] : []),
    ],
  };
}

function deckWithDrawing(source: "catalog" | "recipe" | "ai_draft" = "recipe"): TeacherSketchDeck {
  const parsed = parseTeacherSketchDeck(serverDeckWithSteps(4));
  if (!parsed) throw new Error("The four-step deck should parse");
  const whole = {
    viewbox: [0, 0, 100, 100] as const,
    source,
    sha256: "a".repeat(64),
  };
  return {
    ...parsed,
    slides: parsed.slides.map((slide) => ({
      ...slide,
      steps: slide.steps.map((step, index) => ({
        ...step,
        drawing: {
          ...whole,
          strokes: [{
            kind: "line" as const,
            x1: index * 10,
            y1: 0,
            x2: index * 10 + 5,
            y2: 5,
            stroke: "#1f2937",
            stroke_width: 2,
          }],
        },
      })),
    })),
  };
}

describe("parseTeacherSketchDeck", () => {
  it("accepts three-step legacy guides and eight-step guides", () => {
    expect(parseTeacherSketchDeck(serverDeckWithSteps(3))?.slides[0]?.steps).toHaveLength(3);
    expect(parseTeacherSketchDeck(serverDeckWithSteps(8))?.slides[0]?.steps).toHaveLength(8);
  });

  it("rejects drawing guides with fewer than three or more than eight steps", () => {
    expect(parseTeacherSketchDeck(serverDeckWithSteps(2))).toBeNull();
    expect(parseTeacherSketchDeck(serverDeckWithSteps(9))).toBeNull();
  });
});

describe("TeacherDeckPresentation", () => {
  it("shows and navigates the drawing steps", () => {
    const deck = parseTeacherSketchDeck(serverDeckWithSteps(8));
    expect(deck).not.toBeNull();
    if (!deck) throw new Error("The eight-step server deck should parse");

    render(<TeacherDeckPresentation deck={deck} onClose={() => undefined} />);

    for (let step = 1; step <= 8; step += 1) {
      const stepButton = screen.getByRole("button", { name: `Bước ${step}` });
      expect(stepButton.className).toContain("focus-visible:ring-2");
      fireEvent.click(stepButton);
      expect(stepButton.getAttribute("aria-current")).toBe("step");
      expect(screen.getByText(`Bước ${step} / 8`)).toBeTruthy();
      expect(screen.getByText(`Vẽ bước ${step}`)).toBeTruthy();
    }

  });

  it("composes prior solid strokes and highlights the current step accessibly", () => {
    render(<TeacherDeckPresentation deck={deckWithDrawing()} onClose={() => undefined} />);

    const image = screen.getByRole("img", { name: "Minh họa nét vẽ cho Draw a cat, bước 1 trên 4" });
    expect(image.querySelectorAll("line")).toHaveLength(1);
    expect(image.querySelector("line")?.getAttribute("stroke")).toBe("#2563eb");

    fireEvent.click(screen.getByRole("button", { name: "Bước 2" }));
    const lines = [...screen.getByRole("img").querySelectorAll("line")];
    expect(lines).toHaveLength(2);
    expect(lines.map((line) => line.getAttribute("stroke"))).toEqual(["#1f2937", "#2563eb"]);
  });

  it("asks the teacher to check AI draft drawings", () => {
    render(<TeacherDeckPresentation deck={deckWithDrawing("ai_draft")} onClose={() => undefined} />);

    expect(screen.getByText("Bản vẽ AI còn là bản nháp; giáo viên cần kiểm tra.")).toBeTruthy();
  });

  it("hides the generic placement and shows a specific placement", () => {
    const deck = parseTeacherSketchDeck(serverDeckWithSteps(4, false, (index) => (
      index === 0 ? "trên trang vẽ" : "trên dòng kẻ"
    )));
    if (!deck) throw new Error("The drawing guide should parse");

    render(<TeacherDeckPresentation deck={deck} onClose={() => undefined} />);

    expect(screen.queryByText("trên trang vẽ")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Bước 2" }));
    expect(screen.getByText("trên dòng kẻ")).toBeTruthy();
  });

  it("labels the step advance and the next-slide action", () => {
    const deck = parseTeacherSketchDeck(serverDeckWithSteps(3, true));
    if (!deck) throw new Error("The two-slide drawing guide should parse");

    render(<TeacherDeckPresentation deck={deck} onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Bước tiếp theo" }));
    expect(screen.getByText("Bước 2 / 3")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Bước 3" }));

    fireEvent.click(screen.getByRole("button", { name: "Slide tiếp theo" }));
    expect(screen.getByText("Slide 2 / 2")).toBeTruthy();
  });

  it("labels the final guide action as a restart and keeps its existing behavior", () => {
    const deck = parseTeacherSketchDeck(serverDeckWithSteps(3));
    if (!deck) throw new Error("The drawing guide should parse");

    render(<TeacherDeckPresentation deck={deck} onClose={() => undefined} />);

    fireEvent.click(screen.getByRole("button", { name: "Bước 3" }));
    fireEvent.click(screen.getByRole("button", { name: "Bắt đầu lại" }));

    expect(screen.getByText("Slide 1 / 1")).toBeTruthy();
    expect(screen.getByText("Bước 1 / 3")).toBeTruthy();
  });


});

describe("TeacherDeckPresentation drawing layout", () => {
  afterEach(cleanup);

  it("puts the step text beside the drawing without the missing-drawing note", () => {
    render(<TeacherDeckPresentation deck={deckWithDrawing()} onClose={() => undefined} />);
    const text = screen.getByTestId("deck-step-text");
    const drawing = screen.getByRole("img");
    expect(text.contains(drawing)).toBe(false);
    expect(drawing.closest(".teacher-deck-guide")?.contains(text)).toBe(true);
    expect(drawing.closest("section")?.className).toContain("teacher-deck-drawing-slide");
    expect(screen.queryByText(/chưa có hình vẽ mẫu/)).toBeNull();
  });

  it("says that there is no sample drawing only when the guide has none", () => {
    const deck = parseTeacherSketchDeck(serverDeckWithSteps(4));
    if (!deck) throw new Error("The drawing guide should parse");
    render(<TeacherDeckPresentation deck={deck} onClose={() => undefined} />);
    expect(screen.getByText("Bài này chưa có hình vẽ mẫu. Giáo viên hướng dẫn trẻ theo từng bước bằng lời.")).toBeTruthy();
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.queryByText(/dữ liệu hợp lệ/)).toBeNull();
  });
});

describe("TeacherDeckPresentation drawing source note", () => {
  afterEach(cleanup);

  it.each(["catalog", "recipe"] as const)("marks a %s picture as a reference sample", (source) => {
    render(<TeacherDeckPresentation deck={deckWithDrawing(source)} onClose={() => undefined} />);
    expect(screen.getByText("Hình mẫu tham khảo, không theo đúng từng bước hướng dẫn.")).toBeTruthy();
    expect(screen.queryByText(/Bản vẽ AI/)).toBeNull();
  });

  it("keeps the AI draft warning for an AI picture", () => {
    render(<TeacherDeckPresentation deck={deckWithDrawing("ai_draft")} onClose={() => undefined} />);
    expect(screen.getByText(/Bản vẽ AI còn là bản nháp/)).toBeTruthy();
    expect(screen.queryByText(/Hình mẫu tham khảo/)).toBeNull();
  });
});

describe("TeacherDeckPresentation recipe captions", () => {
  afterEach(cleanup);

  function captionedDeck(): TeacherSketchDeck {
    const deck = deckWithDrawing("recipe");
    const [slide, ...rest] = deck.slides;
    const steps = slide.steps.map((step, index) => ({
      ...step,
      drawing: step.drawing && { ...step.drawing, ...(index === 0 ? { caption: "Vẽ đầu mèo tròn." } : {}) },
    }));
    return { ...deck, slides: [{ ...slide, steps }, ...rest] };
  }

  it("shows the recipe words under the picture, and none on a step without new strokes", () => {
    render(<TeacherDeckPresentation deck={captionedDeck()} onClose={() => undefined} />);
    expect(screen.getByTestId("drawing-caption").textContent).toBe("Vẽ đầu mèo tròn.");
    expect(screen.getByText("Hình mẫu tham khảo, vẽ theo lời dưới hình.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Bước tiếp theo" }));

    expect(screen.queryByTestId("drawing-caption")).toBeNull();
    expect(screen.getByText("Hình mẫu tham khảo, vẽ theo lời dưới hình.")).toBeTruthy();
  });

  it("keeps an older stored recipe deck with its previous note", () => {
    render(<TeacherDeckPresentation deck={deckWithDrawing("recipe")} onClose={() => undefined} />);
    expect(screen.queryByTestId("drawing-caption")).toBeNull();
    expect(screen.getByText("Hình mẫu tham khảo, không theo đúng từng bước hướng dẫn.")).toBeTruthy();
  });
});


it("renders the presentation outside the shell and retains keyboard controls", () => {
  const deck = parseTeacherSketchDeck(serverDeckWithSteps(4, true))!;
  const shell = document.createElement("div");
  document.body.appendChild(shell);
  let closed = false;
  const view = render(<TeacherDeckPresentation deck={deck} onClose={() => { closed = true; }} />, { container: shell });
  const dialog = screen.getByRole("dialog");
  expect(dialog.parentElement).toBe(document.body);
  expect(shell.contains(dialog)).toBe(false);
  fireEvent.keyDown(window, { key: "ArrowRight" });
  expect(screen.getByRole("region", { name: "Slide 2: Opening" })).toBeTruthy();
  fireEvent.keyDown(window, { key: "Escape" });
  expect(closed).toBe(true);
  view.unmount();
  shell.remove();
});
