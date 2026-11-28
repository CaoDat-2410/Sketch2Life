import type { TeacherSketchDeck } from "./TeacherDeckPresentation";

type DrawingStep = TeacherSketchDeck["slides"][number]["steps"][number];
type DrawingStroke = NonNullable<DrawingStep["drawing"]>["strokes"][number];

type Props = Readonly<{
  steps: readonly DrawingStep[];
  currentStepIndex: number;
  title: string;
}>;

const BASE_STROKE = "#1f2937";
const CURRENT_STROKE = "#2563eb";
const MIN_STROKE_WIDTH = 3;
const FIT_MARGIN = 0.08;

type ViewBox = readonly [number, number, number, number];

function strokeBounds(stroke: DrawingStroke): [number, number, number, number] {
  switch (stroke.kind) {
    case "circle":
      return [stroke.cx - stroke.r, stroke.cy - stroke.r, stroke.cx + stroke.r, stroke.cy + stroke.r];
    case "ellipse":
      return [stroke.cx - stroke.rx, stroke.cy - stroke.ry, stroke.cx + stroke.rx, stroke.cy + stroke.ry];
    case "rect":
      return [stroke.x, stroke.y, stroke.x + stroke.w, stroke.y + stroke.h];
    case "line":
      return [Math.min(stroke.x1, stroke.x2), Math.min(stroke.y1, stroke.y2), Math.max(stroke.x1, stroke.x2), Math.max(stroke.y1, stroke.y2)];
    case "polyline": {
      const xs = stroke.points.map(([x]) => x);
      const ys = stroke.points.map(([, y]) => y);
      return [Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)];
    }
  }
}

// Zooms on the finished picture (all steps, so the frame never jumps between steps) and never
// shows anything outside the stored viewbox. Falls back to the stored viewbox when unsure.
function fitViewBox(viewbox: ViewBox, steps: readonly DrawingStep[]): ViewBox {
  const strokes = steps.flatMap((step) => step.drawing?.strokes ?? []);
  if (!strokes.length) return viewbox;
  let left = Infinity;
  let top = Infinity;
  let right = -Infinity;
  let bottom = -Infinity;
  for (const stroke of strokes) {
    const [x1, y1, x2, y2] = strokeBounds(stroke);
    left = Math.min(left, x1);
    top = Math.min(top, y1);
    right = Math.max(right, x2);
    bottom = Math.max(bottom, y2);
  }
  const [vx, vy, vw, vh] = viewbox;
  const margin = Math.max(right - left, bottom - top, Math.min(vw, vh) * 0.1) * FIT_MARGIN;
  left = Math.max(vx, left - margin);
  top = Math.max(vy, top - margin);
  right = Math.min(vx + vw, right + margin);
  bottom = Math.min(vy + vh, bottom + margin);
  const width = right - left;
  const height = bottom - top;
  if (![left, top, width, height].every(Number.isFinite) || width <= 0 || height <= 0) return viewbox;
  // A tiny picture is not blown up beyond four times; it would look like a different drawing.
  if (width < vw / 4 || height < vh / 4) {
    const fitWidth = Math.min(vw, Math.max(width, vw / 4));
    const fitHeight = Math.min(vh, Math.max(height, vh / 4));
    const fitLeft = Math.min(Math.max(vx, left - (fitWidth - width) / 2), vx + vw - fitWidth);
    const fitTop = Math.min(Math.max(vy, top - (fitHeight - height) / 2), vy + vh - fitHeight);
    return [fitLeft, fitTop, fitWidth, fitHeight];
  }
  return [left, top, width, height];
}

function SvgStroke({ stroke, color }: { stroke: DrawingStroke; color: string }) {
  const common = {
    fill: "none",
    stroke: color,
    // Strokes keep their pixel width at any zoom, so thin lines get a floor a back row can still see.
    strokeWidth: Math.max(stroke.stroke_width, MIN_STROKE_WIDTH),
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeDasharray: "none",
    vectorEffect: "non-scaling-stroke" as const,
  };
  switch (stroke.kind) {
    case "circle":
      return <circle {...common} cx={stroke.cx} cy={stroke.cy} r={stroke.r} />;
    case "ellipse":
      return <ellipse {...common} cx={stroke.cx} cy={stroke.cy} rx={stroke.rx} ry={stroke.ry} />;
    case "rect":
      return <rect {...common} x={stroke.x} y={stroke.y} width={stroke.w} height={stroke.h} />;
    case "line":
      return <line {...common} x1={stroke.x1} y1={stroke.y1} x2={stroke.x2} y2={stroke.y2} />;
    case "polyline":
      return <polyline {...common} points={stroke.points.map(([x, y]) => `${x},${y}`).join(" ")} />;
  }
}

export function hasTeacherDrawing(steps: readonly DrawingStep[]): boolean {
  const first = steps[0]?.drawing;
  return Boolean(first && steps.every((step) => {
    const drawing = step.drawing;
    return drawing
      && drawing.sha256 === first.sha256
      && drawing.source === first.source
      && drawing.viewbox.every((value, index) => value === first.viewbox[index]);
  }));
}

export function TeacherProgressiveDrawing({ steps, currentStepIndex, title }: Props) {
  if (
    currentStepIndex < 0
    || currentStepIndex >= steps.length
    || !hasTeacherDrawing(steps)
  ) return null;

  const drawing = steps[0].drawing;
  if (!drawing) return null;
  const visibleSteps = steps.slice(0, currentStepIndex + 1);
  const fittedViewBox = fitViewBox(drawing.viewbox, steps);
  // A recipe picture comes with its own words; decks stored before that have none.
  const describesRecipe = drawing.source === "recipe" && steps.some((step) => step.drawing?.caption);
  const caption = describesRecipe ? steps[currentStepIndex]?.drawing?.caption : undefined;

  return (
    <figure className="m-0 flex min-h-0 min-w-0 flex-col rounded-xl border border-slate-200 bg-slate-50 p-2">
      <svg
        className="mx-auto block h-44 w-full sm:h-0 sm:min-h-0 sm:flex-1"
        viewBox={fittedViewBox.join(" ")}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={`Minh họa nét vẽ cho ${title}, bước ${currentStepIndex + 1} trên ${steps.length}`}
      >
        {visibleSteps.flatMap((step, stepIndex) => (step.drawing?.strokes ?? []).map((stroke, strokeIndex) => (
          <SvgStroke
            key={`${stepIndex}-${strokeIndex}`}
            stroke={stroke}
            color={stepIndex === currentStepIndex ? CURRENT_STROKE : BASE_STROKE}
          />
        )))}
      </svg>
      <figcaption className="mt-1 shrink-0 text-center">
        {caption && <p className="mb-1 text-[0.85em] font-semibold leading-snug text-slate-800" data-testid="drawing-caption">{caption}</p>}
        <p className="text-xs font-medium text-amber-900">
          {drawing.source === "ai_draft"
            ? "Bản vẽ AI còn là bản nháp; giáo viên cần kiểm tra."
            : describesRecipe
              ? "Hình mẫu tham khảo, vẽ theo lời dưới hình."
              : "Hình mẫu tham khảo, không theo đúng từng bước hướng dẫn."}
        </p>
      </figcaption>
    </figure>
  );
}

export type { Props as TeacherProgressiveDrawingProps };
