import { useEffect, useState } from "react";
import { teacherWorkspaceApi, type TeacherActivity } from "../../../shared/api/teacherWorkspaceApi";
import { Button } from "../../../shared/ui";

export type PlanLessonActivity = { kind: "LESSON"; lesson_activity_id: string };
type LessonVersionRef = { lesson_id: string; version_id: string };

interface PlanActivityPickerProps {
  organizationId: string;
  lessonVersionRef: LessonVersionRef | null;
  selection: PlanLessonActivity[];
  onSelectionChange: (selection: PlanLessonActivity[]) => void;
  copiedFromPlan?: boolean;
  disabled?: boolean;
}

type LoadState = "idle" | "loading" | "loaded" | "error";

export function PlanActivityPicker({
  organizationId,
  lessonVersionRef,
  selection,
  onSelectionChange,
  copiedFromPlan = false,
  disabled = false,
}: PlanActivityPickerProps) {
  const lessonId = lessonVersionRef?.lesson_id ?? "";
  const versionId = lessonVersionRef?.version_id ?? "";
  const [activities, setActivities] = useState<TeacherActivity[]>([]);
  const [loadState, setLoadState] = useState<LoadState>(() => lessonVersionRef ? "loading" : "idle");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    if (!lessonId || !versionId) return;

    let active = true;
    const loadActivities = async () => {
      try {
        const pages: TeacherActivity[] = [];
        let cursor: string | undefined;
        do {
          const page = await teacherWorkspaceApi.activities(
            organizationId,
            cursor ? { limit: 100, cursor } : { limit: 100 },
          );
          pages.push(...page.items);
          cursor = page.next_cursor ?? undefined;
        } while (cursor);

        const matching = pages
          .filter((activity) => activity.lesson_id === lessonId && activity.version_id === versionId)
          .sort((left, right) => left.activity_order - right.activity_order);
        if (active) {
          setActivities(matching);
          setLoadState("loaded");
        }
      } catch {
        if (active) {
          setActivities([]);
          setLoadState("error");
        }
      }
    };
    void loadActivities();
    return () => { active = false; };
  }, [lessonId, organizationId, retry, versionId]);

  useEffect(() => {
    if (loadState !== "loaded" || copiedFromPlan) return;
    onSelectionChange(activities.map((activity) => ({ kind: "LESSON", lesson_activity_id: activity.lesson_activity_id })));
  }, [activities, copiedFromPlan, loadState, onSelectionChange]);

  if (!lessonVersionRef) return null;

  const selectedIds = new Set(selection.map((activity) => activity.lesson_activity_id));
  const visibleIds = new Set(activities.map((activity) => activity.lesson_activity_id));
  const retainedFromPlan = selection.filter((activity) => !visibleIds.has(activity.lesson_activity_id));

  const toggleActivity = (lessonActivityId: string, checked: boolean) => {
    const nextIds = new Set(selectedIds);
    if (checked) nextIds.add(lessonActivityId);
    else nextIds.delete(lessonActivityId);
    const available = activities
      .filter((activity) => nextIds.has(activity.lesson_activity_id))
      .map((activity) => ({ kind: "LESSON" as const, lesson_activity_id: activity.lesson_activity_id }));
    const retained = selection.filter((activity) => !visibleIds.has(activity.lesson_activity_id) && nextIds.has(activity.lesson_activity_id));
    onSelectionChange([...available, ...retained]);
  };

  return (
    <div className="cozy-form-stack" role="group" aria-labelledby="plan-pinned-activities-title">
      <h4 id="plan-pinned-activities-title">Hoạt động từ giáo án đã ghim</h4>
      {loadState === "loading" && <p className="s2l-note" role="status">Đang tải hoạt động của giáo án đã ghim…</p>}
      {loadState === "error" && <div>
        <p className="s2l-note" role="alert">Không thể tải hoạt động từ giáo án đã ghim. Có thể lưu kế hoạch với lựa chọn hiện tại.</p>
        <Button type="button" variant="secondary" disabled={disabled} onClick={() => { setLoadState("loading"); setRetry((current) => current + 1); }}>Thử tải lại hoạt động</Button>
      </div>}
      {loadState === "loaded" && activities.length === 0 && <p className="s2l-note">Không thể liệt kê hoạt động của phiên bản giáo án đã ghim vì phiên bản này không còn trong danh sách giáo án đang được duyệt.</p>}
      {loadState === "loaded" && activities.length > 0 && <div className="cozy-form-stack">
        {activities.map((activity) => <label key={activity.lesson_activity_id} className="cozy-form-checkbox-card teacher-plan-activity-checkbox">
          <input
            type="checkbox"
            checked={selectedIds.has(activity.lesson_activity_id)}
            disabled={disabled}
            onChange={(event) => toggleActivity(activity.lesson_activity_id, event.target.checked)}
          />
          <span>{activity.activity_order}. {activity.title}</span>
        </label>)}
      </div>}
      {loadState === "loaded" && copiedFromPlan && retainedFromPlan.length > 0 && <p className="s2l-note">Giữ nguyên {retainedFromPlan.length} hoạt động không có trong danh sách hiện tại từ bản kế hoạch trước.</p>}
    </div>
  );
}
