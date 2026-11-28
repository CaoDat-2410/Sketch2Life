import type { CurrentSketchDeck, PlanActivity, SketchDeckStep } from "../../../shared/api/teacherOccurrenceApi";
import { parseProgressiveDrawing, type ProgressiveDrawing, type TeacherSketchDeck } from "../components/TeacherDeckPresentation";

// These are the same generic target months the backend uses for these lesson age bands.
const WORKER_TARGET_MONTHS_BY_AGE_BAND: Readonly<Record<string, number>> = {
  "age-36-71-months-v1": 54,
  "age-72-107-months-v1": 90,
  "age-108-120-months-v1": 114,
};

function groupIdentity(step: SketchDeckStep): string {
  return `${step.plan_activity_id ?? ""}\u0000${step.instruction_group_key}`;
}

function groupDrawings(steps: readonly SketchDeckStep[]): ProgressiveDrawing[] | null {
  const raw = steps.map((step) => step.bounded_layout_hints.drawing);
  if (!raw.some((drawing) => drawing !== undefined)) return null;
  const parsed = raw.map(parseProgressiveDrawing);
  if (parsed.some((drawing) => drawing === null)) return null;
  const drawings = parsed.filter((drawing): drawing is ProgressiveDrawing => drawing !== null);
  const first = drawings[0];
  if (!first
    || !drawings.every((drawing) => (
      drawing.sha256 === first.sha256
      && drawing.source === first.source
      && drawing.viewbox.every((value, index) => value === first.viewbox[index])
    ))
    || !drawings.some((drawing) => drawing.strokes.length > 0)) return null;
  return drawings;
}

/** Maps only persisted backend values into the legacy presentation shape. */
export function toTeacherSketchDeck(
  current: CurrentSketchDeck,
  planActivities?: readonly Pick<PlanActivity, "plan_activity_id" | "order" | "title">[],
): TeacherSketchDeck | null {
  const revision = current.current_revision;
  const ageMonths = revision ? WORKER_TARGET_MONTHS_BY_AGE_BAND[revision.target_age_band] : undefined;
  if (!revision || !revision.topic.trim() || ageMonths === undefined || current.steps.length === 0) return null;

  const groups = new Map<string, SketchDeckStep[]>();
  for (const step of current.steps) {
    const key = groupIdentity(step);
    groups.set(key, [...(groups.get(key) ?? []), step]);
  }

  const planActivityOrder = new Map<string, number>();
  for (const activity of planActivities ?? []) {
    if (activity.plan_activity_id) planActivityOrder.set(activity.plan_activity_id, activity.order);
  }
  const planActivityById = new Map(
    (planActivities ?? [])
      .filter((activity): activity is typeof activity & { plan_activity_id: string } => Boolean(activity.plan_activity_id))
      .map((activity) => [activity.plan_activity_id, activity]),
  );
  const orderedGroups = [...groups.entries()].sort(([leftKey, leftSteps], [rightKey, rightSteps]) => {
    const leftActivity = leftSteps[0]?.plan_activity_id ?? null;
    const rightActivity = rightSteps[0]?.plan_activity_id ?? null;
    const leftOrder = leftActivity ? planActivityOrder.get(leftActivity) ?? Number.MAX_SAFE_INTEGER : Number.MAX_SAFE_INTEGER;
    const rightOrder = rightActivity ? planActivityOrder.get(rightActivity) ?? Number.MAX_SAFE_INTEGER : Number.MAX_SAFE_INTEGER;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    const leftGroupKey = leftKey.slice(leftKey.indexOf("\u0000") + 1);
    const rightGroupKey = rightKey.slice(rightKey.indexOf("\u0000") + 1);
    return leftGroupKey.localeCompare(rightGroupKey);
  });

  const slides: TeacherSketchDeck["slides"] = [];
  for (const [, group] of orderedGroups) {
    const ordered = [...group].sort((left, right) => left.step_index - right.step_index);
    if (ordered.length < 4 || ordered.length > 8) return null;
    if (ordered.some((step, index) => step.step_index !== index + 1 || !step.short_title.trim() || !step.child_facing_prompt.trim())) return null;
    const drawings = groupDrawings(ordered);

    const planTitle = planActivityById.get(ordered[0].plan_activity_id ?? "")?.title?.trim();
    slides.push({
      slideIndex: slides.length + 1,
      kind: "drawing_guide",
      title: planTitle || ordered[0].short_title,
      activityRef: ordered[0].plan_activity_id,
      bullets: [],
      steps: ordered.map((step) => ({
        stepIndex: step.step_index,
        instruction: step.child_facing_prompt,
        // This legacy slot renders as unlabelled supporting text, so keep the backend's teacher explanation verbatim.
        placement: step.teacher_explanation,
        ...(drawings ? { drawing: drawings[step.step_index - 1] } : {}),
      })),
      goal: [],
      materials: [],
      preparation: [],
      instructions: [],
      safetyNotes: [],
    });
  }

  return slides.length ? { topic: revision.topic, ageMonths, slides } : null;
}
