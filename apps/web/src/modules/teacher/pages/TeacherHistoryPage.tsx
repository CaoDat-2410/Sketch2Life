import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { RefreshCw } from "lucide-react";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { BackendApiError, configuredOrganizationId } from "../../../shared/api/backendApi";
import type { OccurrenceState } from "../../../shared/api/teacherOccurrenceApi";
import { teacherWorkspaceApi } from "../../../shared/api/teacherWorkspaceApi";
import { formatDateDdMmYyyy, StatusBadge } from "../../../shared/ui";
import { teacherStatusMeta } from "../services/teacherStatus";

const states: Array<{ value: OccurrenceState | ""; label: string }> = [
  { value: "", label: "Tất cả trạng thái" }, { value: "DRAFT", label: "Bản nháp" },
  { value: "DOCUMENT_REVIEW", label: "Rà soát tài liệu" }, { value: "PLAN_REVIEW", label: "Rà soát kế hoạch" },
  { value: "APPROVED", label: "Đã duyệt" }, { value: "SAMPLE_AVAILABLE", label: "Có thể tạo video mẫu" },
  { value: "SAMPLE_USED", label: "Đã dùng video mẫu" }, { value: "ARCHIVED", label: "Đã lưu trữ" },
];
const stateLabel: Record<OccurrenceState, string> = Object.fromEntries(states.filter((item) => item.value).map((item) => [item.value, item.label])) as Record<OccurrenceState, string>;

function safeHistoryError(cause: unknown): string {
  if (cause instanceof BackendApiError) {
    if (cause.status === 404 || cause.status === 403) return "Không tìm thấy dữ liệu hoặc bạn không có quyền truy cập.";
    if (cause.status === 400) return "Bộ lọc hoặc trang lịch sử không hợp lệ.";
    if (cause.status === 503 || cause.status === 0) return "Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.";
  }
  return "Chưa thể tải lịch sử. Hãy thử lại sau.";
}

export function TeacherHistoryPage() {
  const [filter, setFilter] = useState<OccurrenceState | "">("");
  const [items, setItems] = useState<Awaited<ReturnType<typeof teacherWorkspaceApi.history>>["items"]>([]);
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
    teacherWorkspaceApi.history(organizationId, { state: filter || undefined, limit: 25, cursor: cursor ?? undefined })
      .then((page) => {
        if (!active) return;
        setItems((current) => cursor ? [...current, ...page.items] : page.items);
        setNextCursor(page.next_cursor);
      })
      .catch((cause: unknown) => { if (active) setError(safeHistoryError(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [filter, cursor, reload]);

  const reset = (value: OccurrenceState | "") => { setFilter(value); setCursor(null); setItems([]); setReload((n) => n + 1); };

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading eyebrow="Lên lớp" title="Lịch sử buổi dạy" description="Các buổi dạy trong những lớp bạn hiện được phân công." action={<button type="button" className="s2l-button" disabled={loading} onClick={() => { setCursor(null); setItems([]); setReload((value) => value + 1); }}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>} />
      <div className="cozy-form-field tp-history-filter">
        <label className="cozy-form-label" htmlFor="teacher-history-state">Trạng thái</label>
        <select id="teacher-history-state" className="cozy-input" value={filter} disabled={loading} onChange={(event) => reset(event.target.value as OccurrenceState | "")}>
          {states.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
      </div>
      {loading && <p className="s2l-data-card" role="status">Đang tải lịch sử…</p>}
      {error && <div className="s2l-alert" role="alert">{error}</div>}
      {!loading && !error && items.length === 0 && <p className="s2l-data-card">Chưa có buổi dạy trong phạm vi này.</p>}
      {!error && items.length > 0 && <ul className="tp-history-list">{items.map((item) => {
        const stateMeta = teacherStatusMeta(item.state, "session");
        return (
          <li key={item.occurrence_id} className="tp-history-row">
            <span className="tp-history-copy"><strong>{item.title}</strong><span className="tp-chip-row"><small>{formatDateDdMmYyyy(item.scheduled_date ?? item.created_at)}</small><StatusBadge tone={stateMeta.tone}>{stateLabel[item.state]}</StatusBadge></span></span>
            <Link className="s2l-card-link tp-compact" style={{ minHeight: 44, marginTop: 0 }} to={`/teacher/t02-presentation?occurrence=${encodeURIComponent(item.occurrence_id)}`}>Mở trình bày</Link>
          </li>
        );
      })}</ul>}
      {!error && nextCursor && <button type="button" className="s2l-button" disabled={loading} onClick={() => setCursor(nextCursor)}>Tải thêm</button>}
    </div>
  );
}
