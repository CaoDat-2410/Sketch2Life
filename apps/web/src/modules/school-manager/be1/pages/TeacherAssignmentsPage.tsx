import { useEffect, useState } from "react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { classService, classStateLabel, type Be1Class } from "../services/classService";
import { TeacherAssignmentCard } from "./TeacherAssignmentCard";
import { Alert, EmptyState, Select, StatCard, StatusBadge, type StatusTone } from "../../../../shared/ui";

function classStateTone(state: Be1Class["state"]): StatusTone {
  if (state === "active") return "success";
  if (state === "suspended") return "warn";
  if (state === "archived") return "neutral";
  return "info";
}

export function TeacherAssignmentsPage() {
  const [classes, setClasses] = useState<Be1Class[]>([]);
  const [selected, setSelected] = useState("");
  const [state, setState] = useState<"loading" | "loaded" | "error">("loading");
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    classService.listClasses("all").then((items) => {
      if (!active) return;
      setClasses(items);
      setSelected((previous) => items.some((item) => item.class_id === previous) ? previous : items[0]?.class_id ?? "");
      setState("loaded");
    }).catch(() => { if (active) setState("error"); });
    return () => { active = false; };
  }, [reload]);
  const selectedClass = classes.find((item) => item.class_id === selected);
  const assignedCount = classes.filter((item) => item.has_active_teacher === true).length;
  const unassignedCount = classes.filter((item) => item.has_active_teacher === false).length;
  return <div className="s2l-page manager-business-page">
    <PageHeading eyebrow="School Manager" title="Phân công giáo viên" description="Xem lớp và phân công giáo viên phụ trách." />
    {state === "loaded" && <section className="manager-business-stats" aria-label="Thống kê phân công">
      <StatCard label="Tổng số lớp" value={classes.length} accent="primary" />
      <StatCard label="Có giáo viên phụ trách" value={assignedCount} accent="mint" />
      <StatCard label="Chưa có giáo viên phụ trách" value={unassignedCount} accent="butter" />
    </section>}
    <section className="manager-business-card manager-business-class-picker">
      {state === "loading" && <Alert role="status">Đang tải danh sách lớp…</Alert>}
      {state === "error" && <Alert role="alert" tone="danger"><span>Không tải được danh sách lớp.</span><button className="manager-business-button" onClick={() => { setState("loading"); setReload((n) => n + 1); }}>Tải lại</button></Alert>}
      {state === "loaded" && classes.length === 0 && <EmptyState title="Chưa có lớp nào trong trường." />}
      {state === "loaded" && classes.length > 0 && <>
        <label htmlFor="assignment-class">Chọn lớp</label>
        <Select id="assignment-class" value={selected} onChange={(event) => setSelected(event.target.value)}>{classes.map((item) => <option key={item.class_id} value={item.class_id}>{item.display_name}</option>)}</Select>
        <ul className="manager-business-assignment-list" aria-label="Danh sách lớp và trạng thái phân công">{classes.map((item) => <li key={item.class_id} className={item.class_id === selected ? "is-selected" : undefined} aria-current={item.class_id === selected ? "true" : undefined}>
          <strong>{item.display_name}</strong>
          <div className="manager-business-assignment-badges">
            <StatusBadge tone={classStateTone(item.state)}>{classStateLabel(item.state)}</StatusBadge>
            <StatusBadge tone={item.has_active_teacher === true ? "success" : item.has_active_teacher === false ? "warn" : "neutral"}>
              {item.has_active_teacher === undefined ? "Chưa rõ giáo viên phụ trách" : item.has_active_teacher ? "Đã có giáo viên phụ trách" : "Chưa có giáo viên phụ trách"}
            </StatusBadge>
          </div>
        </li>)}</ul>
      </>}
    </section>
    {state === "loaded" && selectedClass && <TeacherAssignmentCard key={selectedClass.class_id} selectedClass={selectedClass} onAssigned={() => setReload((n) => n + 1)} />}
  </div>;
}
