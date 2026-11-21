import { useEffect, useState } from "react";
import { PageHeading } from "../../../../shared/components/FeatureAvailability";
import { classService, classStateLabel, type Be1Class } from "../services/classService";
import { TeacherAssignmentCard } from "./TeacherAssignmentCard";

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
  return <div className="s2l-page manager-business-page">
    <PageHeading eyebrow="School Manager" title="Phân công giáo viên" description="Xem lớp và phân công giáo viên phụ trách." />
    <section className="manager-business-card manager-business-class-picker">
      {state === "loading" && <p role="status">Đang tải danh sách lớp…</p>}
      {state === "error" && <><p role="alert">Không tải được danh sách lớp.</p><button className="manager-business-button" onClick={() => { setState("loading"); setReload((n) => n + 1); }}>Tải lại</button></>}
      {state === "loaded" && classes.length === 0 && <p role="status">Chưa có lớp nào trong trường.</p>}
      {state === "loaded" && classes.length > 0 && <>
        <label htmlFor="assignment-class">Chọn lớp</label>
        <select id="assignment-class" value={selected} onChange={(event) => setSelected(event.target.value)}>{classes.map((item) => <option key={item.class_id} value={item.class_id}>{item.display_name}</option>)}</select>
        <ul>{classes.map((item) => <li key={item.class_id}>{item.display_name} · {classStateLabel(item.state)} · {item.has_active_teacher === undefined ? "Chưa rõ giáo viên phụ trách" : item.has_active_teacher ? "Đã có giáo viên phụ trách" : "Chưa có giáo viên phụ trách"}</li>)}</ul>
      </>}
    </section>
    {state === "loaded" && selectedClass && <TeacherAssignmentCard key={selectedClass.class_id} selectedClass={selectedClass} onAssigned={() => setReload((n) => n + 1)} />}
  </div>;
}
