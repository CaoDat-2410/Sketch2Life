import { useEffect, useState } from "react";
import { BookOpen, RefreshCw } from "lucide-react";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { configuredOrganizationId } from "../../../shared/api/backendApi";
import { BackendApiError } from "../../../shared/api/backendApi";
import { teacherWorkspaceApi, type TeacherActivity } from "../../../shared/api/teacherWorkspaceApi";
import { StatusBadge } from "../../../shared/ui";

function safeWorkspaceError(cause: unknown): string {
  if (cause instanceof BackendApiError) {
    if (cause.status === 404 || cause.status === 403) return "Không tìm thấy dữ liệu hoặc bạn không có quyền truy cập.";
    if (cause.status === 400) return "Yêu cầu chưa hợp lệ. Hãy kiểm tra bộ lọc rồi thử lại.";
    if (cause.status === 503 || cause.status === 0) return "Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.";
  }
  return "Chưa thể tải hoạt động. Hãy thử lại sau.";
}
const activityKindLabel = { outdoor: "Ngoài trời", indoor: "Trong lớp", mixed: "Kết hợp" } as const;

export function TeacherActivitiesPage() {
  const [items, setItems] = useState<TeacherActivity[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let active = true;
    const organizationId = configuredOrganizationId();
    setLoading(true);
    setError(null);
    if (!organizationId) {
      setError("Chưa cấu hình tổ chức cho tài khoản giáo viên.");
      setLoading(false);
      return () => { active = false; };
    }
    teacherWorkspaceApi.activities(organizationId, { limit: 25, cursor: cursor ?? undefined })
      .then((page) => {
        if (!active) return;
        setItems((current) => cursor ? [...current, ...page.items] : page.items);
        setNextCursor(page.next_cursor);
      })
      .catch((cause: unknown) => { if (active) setError(safeWorkspaceError(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [cursor, reload]);

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading eyebrow="Giáo viên · Học liệu" title="Hoạt động" description="Hoạt động trong các giáo án đã duyệt." action={<button type="button" className="s2l-button" disabled={loading} onClick={() => { setCursor(null); setItems([]); setReload((value) => value + 1); }}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>} />
      {loading && <p className="s2l-data-card" role="status">Đang tải hoạt động…</p>}
      {error && <div className="s2l-alert" role="alert">{error}</div>}
      {!loading && !error && items.length === 0 && <p className="s2l-data-card">Chưa có hoạt động được duyệt trong phạm vi này.</p>}
      {!error && items.length > 0 && <ul className="tp-activity-list">
        {items.map((item) => <li key={`${item.version_id}:${item.lesson_activity_id}`} className="s2l-data-card tp-activity">
          <div className="tp-activity-head"><div className="tp-activity-title"><h2><BookOpen size={17} aria-hidden="true" /> {item.title}</h2><p>{item.lesson_title}{item.lesson_topic ? ` · ${item.lesson_topic}` : ""} · Phiên bản {item.version_no}</p></div><StatusBadge tone="neutral">{activityKindLabel[item.activity_kind]}</StatusBadge></div>
          <div className="tp-field-grid">
            {item.objective && <p className="tp-field"><strong>Mục tiêu:</strong> <span>{item.objective}</span></p>}
            {item.materials_text && <p className="tp-field"><strong>Vật liệu:</strong> <span>{item.materials_text}</span></p>}
            {item.preparation_text && <p className="tp-field"><strong>Chuẩn bị:</strong> <span>{item.preparation_text}</span></p>}
            {item.instructions_text && <p className="tp-field"><strong>Cách làm:</strong> <span>{item.instructions_text}</span></p>}
            {item.observation_notes && <p className="tp-field"><strong>Quan sát:</strong> <span>{item.observation_notes}</span></p>}
            {item.safety_notes && <p className="tp-field"><strong>An toàn:</strong> <span>{item.safety_notes}</span></p>}
          </div>
        </li>)}
      </ul>}
      {!error && nextCursor && <button type="button" className="s2l-button" disabled={loading} onClick={() => setCursor(nextCursor)}>Tải thêm</button>}
    </div>
  );
}
