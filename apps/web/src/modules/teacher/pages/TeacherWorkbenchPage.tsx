import { useEffect, useState } from "react";
import { ArrowRight, BookOpen, CalendarDays, RefreshCw, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { FeatureAvailability, PageHeading } from "../../../shared/FeatureAvailability";
import {
  BackendApiError,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
  type Be1Class,
  type LessonSummary,
} from "../../../shared/backendApi";

type WorkbenchSnapshot = { classes: Be1Class[]; lessons: LessonSummary[] };

export function TeacherWorkbenchPage() {
  const [snapshot, setSnapshot] = useState<WorkbenchSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    if (!hasFirebaseAuthBridge()) {
      setError("Chưa có phiên Firebase Authentication để tải dữ liệu Teacher.");
      setLoading(false);
      return () => { active = false; };
    }
    const organizationId = configuredOrganizationId();
    if (!organizationId) {
      setError("Chưa cấu hình organization_id cho các API Teacher.");
      setLoading(false);
      return () => { active = false; };
    }

    setLoading(true);
    setError(null);
    backendApi.assignments(organizationId)
      .then(async (identity) => {
        const teacherAssignments = identity.assignments.filter(
          (assignment) => assignment.role === "teacher" && assignment.active !== false,
        );
        if (teacherAssignments.length === 0) {
          throw new BackendApiError("Tài khoản không có assignment Teacher đang hoạt động trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        const assignedClassIds = new Set(teacherAssignments.flatMap((assignment) => assignment.class_id ? [assignment.class_id] : []));
        const [classPage, lessonPage] = await Promise.all([
          backendApi.classes(organizationId),
          backendApi.lessons(organizationId),
        ]);
        if (!active) return;
        setSnapshot({
          classes: classPage.items.filter((item) => assignedClassIds.has(item.class_id)),
          lessons: lessonPage.items,
        });
      })
      .catch((cause: unknown) => { if (active) setError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reload]);

  return (
    <div className="s2l-page">
      <PageHeading eyebrow="Teacher · Không gian làm việc" title="Tổng quan" description="Lớp được phân công và học liệu trong organization hiện hành." action={<button type="button" className="s2l-button" onClick={() => setReload((value) => value + 1)} disabled={loading}><RefreshCw size={16} aria-hidden="true" />Làm mới</button>} />

      {error && <div className="s2l-alert" role="alert">{error}</div>}
      {loading && <div className="s2l-data-card" role="status">Đang tải dữ liệu trong assignment Teacher…</div>}

      <section className="s2l-dashboard-grid" aria-label="Tóm tắt công việc">
        <article className="s2l-data-card s2l-dashboard-card">
          <div className="s2l-dashboard-card-title"><span className="s2l-summary-icon"><Users size={19} aria-hidden="true" /></span><div><h2>Lớp được phân công</h2><p>Phạm vi theo assignment Teacher</p></div></div>
          {snapshot && snapshot.classes.length > 0 ? <ul className="s2l-record-list">{snapshot.classes.slice(0, 4).map((item) => <li key={item.class_id}><Link to={"/teacher/t05-classes-and-children/" + encodeURIComponent(item.class_id)}><span><strong>{item.display_name}</strong><small>{item.state}</small></span><ArrowRight size={16} aria-hidden="true" /></Link></li>)}</ul> : <p className="s2l-empty-copy">{snapshot ? "API chưa trả lớp trong assignment này." : error ? "Lớp chưa thể hiển thị khi dữ liệu chưa tải được." : "Đang chờ phiên đã xác minh."}</p>}
          <Link className="s2l-card-link" to="/teacher/t05-classes-and-children">Mở danh sách lớp <ArrowRight size={15} aria-hidden="true" /></Link>
        </article>

        <article className="s2l-data-card s2l-dashboard-card">
          <div className="s2l-dashboard-card-title"><span className="s2l-summary-icon"><BookOpen size={19} aria-hidden="true" /></span><div><h2>Học liệu</h2><p>Lesson trong organization hiện hành</p></div></div>
          {snapshot && snapshot.lessons.length > 0 ? <ul className="s2l-record-list">{snapshot.lessons.slice(0, 4).map((item) => <li key={item.lesson_id}><Link to="/teacher/t02-lesson-authoring"><span><strong>{item.title}</strong><small>Bản {item.current_version_no} · {item.review_state}</small></span><ArrowRight size={16} aria-hidden="true" /></Link></li>)}</ul> : <p className="s2l-empty-copy">{snapshot ? "Chưa có giáo án trong phạm vi tài khoản." : error ? "Học liệu chưa thể hiển thị khi dữ liệu chưa tải được." : "Đang chờ phiên đã xác minh."}</p>}
          <Link className="s2l-card-link" to="/teacher/t02-lesson-authoring">Mở giáo án <ArrowRight size={15} aria-hidden="true" /></Link>
        </article>
      </section>

      <section className="s2l-dashboard-grid s2l-dashboard-grid-secondary" aria-label="Các chức năng cần API">
        <article className="s2l-data-card s2l-dashboard-card">
          <div className="s2l-dashboard-card-title"><span className="s2l-summary-icon"><CalendarDays size={19} aria-hidden="true" /></span><div><h2>Buổi dạy</h2><p>Occurrence và kế hoạch theo lớp</p></div></div>
          <p className="s2l-empty-copy">Chưa có API occurrence, Sketch Deck hoặc checklist để tạo và theo dõi buổi dạy.</p>
          <Link className="s2l-card-link" to="/teacher/t04-session-sketch-deck">Xem yêu cầu API <ArrowRight size={15} aria-hidden="true" /></Link>
        </article>
        <FeatureAvailability
          title="Quota và lịch sử"
          summary="Không hiển thị lượt quota, video job hoặc số liệu hoạt động nếu backend chưa trả dữ liệu có nguồn."
          requirement="SRS yêu cầu quota/reconciliation theo scope cùng lịch sử occurrence và StoryRun."
          dependencies={["API quota theo organization.", "API lịch sử occurrence/job có trạng thái reconciliation."]}
        />
      </section>
    </div>
  );
}
