import { useEffect, useState } from "react";
import { ArrowRight, BookOpen, CalendarDays, RefreshCw, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { TeacherQuotaCard } from "../components/TeacherQuotaCard";
import { StatusBadge } from "../../../shared/ui";
import { teacherStatusMeta } from "../services/teacherStatus";
import {
  BackendApiError,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  hasFirebaseAuthBridge,
  type Be1Class,
  type LessonSummary,
} from "../../../shared/api/backendApi";

type WorkbenchSnapshot = { classes: Be1Class[]; lessons: LessonSummary[] };

export function TeacherWorkbenchPage() {
  const [snapshot, setSnapshot] = useState<WorkbenchSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    if (!hasFirebaseAuthBridge()) {
      setError("Chưa có phiên đăng nhập để tải dữ liệu giáo viên.");
      setLoading(false);
      return () => { active = false; };
    }
    const organizationId = configuredOrganizationId();
    if (!organizationId) {
      setError("Chưa cấu hình tổ chức cho không gian làm việc.");
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
          throw new BackendApiError("Tài khoản chưa được phân công vai trò giáo viên trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        const assignedClassIds = new Set(teacherAssignments.flatMap((assignment) => assignment.class_id ? [assignment.class_id] : []));
        const [classPage, lessonPage] = await Promise.all([
          backendApi.classes(organizationId, "all"),
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
      <PageHeading eyebrow="Giáo viên · Không gian làm việc" title="Tổng quan" description="Lớp được phân công và giáo án trong tổ chức." action={<button type="button" className="s2l-button" onClick={() => setReload((value) => value + 1)} disabled={loading}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>} />

      {error && <div className="s2l-alert" role="alert">{error}</div>}
      {loading && <div className="s2l-data-card" role="status">Đang tải dữ liệu lớp và giáo án…</div>}

      <section className="s2l-dashboard-grid" aria-label="Tóm tắt công việc">
        <article className="s2l-data-card s2l-dashboard-card">
          <div className="s2l-dashboard-card-title"><span className="s2l-summary-icon"><Users size={19} aria-hidden="true" /></span><div><h2>Lớp được phân công</h2><p>Danh sách lớp bạn đang phụ trách</p></div></div>
          {snapshot && snapshot.classes.length > 0 ? <ul className="s2l-record-list">{snapshot.classes.slice(0, 4).map((item) => <li key={item.class_id}><Link to={"/teacher/t05-classes-and-children/" + encodeURIComponent(item.class_id)}><span><strong>{item.display_name}</strong><small>{item.state === "suspended" ? "Tạm ngưng · chỉ đọc" : item.state === "active" ? "Đang hoạt động" : item.state}</small></span><ArrowRight size={16} aria-hidden="true" /></Link></li>)}</ul> : <p className="s2l-empty-copy">{snapshot ? "Hiện chưa có lớp được phân công." : error ? "Lớp chưa thể hiển thị khi dữ liệu chưa tải được." : "Đang chờ xác minh tài khoản."}</p>}
          <Link className="s2l-card-link" to="/teacher/t05-classes-and-children">Mở danh sách lớp <ArrowRight size={15} aria-hidden="true" /></Link>
        </article>

        <article className="s2l-data-card s2l-dashboard-card">
          <div className="s2l-dashboard-card-title"><span className="s2l-summary-icon"><BookOpen size={19} aria-hidden="true" /></span><div><h2>Giáo án</h2><p>Giáo án trong tổ chức</p></div></div>
          {snapshot && snapshot.lessons.length > 0 ? <ul className="s2l-record-list">{snapshot.lessons.slice(0, 4).map((item) => <li key={item.lesson_id}><Link to="/teacher/t02-lesson-authoring"><span><strong>{item.title}</strong><small style={{ display: "inline-flex", flexWrap: "wrap", alignItems: "center", gap: 6 }}>Phiên bản {item.current_version_no} <StatusBadge tone={teacherStatusMeta(item.review_state).tone}>{teacherStatusMeta(item.review_state).label}</StatusBadge></small></span><ArrowRight size={16} aria-hidden="true" /></Link></li>)}</ul> : <p className="s2l-empty-copy">{snapshot ? "Chưa có giáo án trong phạm vi tài khoản." : error ? "Giáo án chưa thể hiển thị khi dữ liệu chưa tải được." : "Đang chờ xác minh tài khoản."}</p>}
          <Link className="s2l-card-link" to="/teacher/t02-lesson-authoring">Mở giáo án <ArrowRight size={15} aria-hidden="true" /></Link>
        </article>
      </section>

      <section className="s2l-dashboard-grid s2l-dashboard-grid-secondary" aria-label="Công cụ giảng dạy">
        <article className="s2l-data-card s2l-dashboard-card">
          <div className="s2l-dashboard-card-title"><span className="s2l-summary-icon"><CalendarDays size={19} aria-hidden="true" /></span><div><h2>Buổi dạy</h2><p>Lên lịch và theo dõi buổi dạy theo lớp</p></div></div>
          <ol className="teacher-overview-steps" aria-label="Trình tự một buổi dạy">
            <li><b aria-hidden="true">1</b><span>Chọn lớp và tạo buổi dạy</span></li>
            <li><b aria-hidden="true">2</b><span>Đính kèm tài liệu, xác nhận kế hoạch</span></li>
            <li><b aria-hidden="true">3</b><span>Trình chiếu cho lớp</span></li>
          </ol>
          <div className="teacher-overview-links">
            <Link className="s2l-card-link" to="/teacher/t04-session-sketch-deck">Mở buổi dạy <ArrowRight size={15} aria-hidden="true" /></Link>
            <Link className="s2l-card-link" to="/teacher/t09-history">Lịch sử buổi dạy <ArrowRight size={15} aria-hidden="true" /></Link>
          </div>
        </article>
        <TeacherQuotaCard reloadKey={reload} />
      </section>
    </div>
  );
}
