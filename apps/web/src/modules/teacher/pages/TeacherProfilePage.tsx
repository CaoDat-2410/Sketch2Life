import { useEffect, useState } from "react";
import { GraduationCap, RefreshCw } from "lucide-react";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { BackendApiError } from "../../../shared/api/backendApi";
import { teacherWorkspaceApi, type TeacherAccountProfile } from "../../../shared/api/teacherWorkspaceApi";

function safeProfileError(cause: unknown): string {
  if (cause instanceof BackendApiError) {
    if (cause.status === 404 || cause.status === 403) return "Không tìm thấy dữ liệu hoặc bạn không có quyền truy cập.";
    if (cause.status === 503 || cause.status === 0) return "Hồ sơ hiện chưa thể tải. Hãy thử lại sau.";
  }
  return "Hồ sơ hiện chưa thể tải. Hãy thử lại sau.";
}

export function TeacherProfilePage() {
  const [profile, setProfile] = useState<TeacherAccountProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    teacherWorkspaceApi.profile()
      .then((value) => { if (active) setProfile(value); })
      .catch((cause: unknown) => { if (active) setError(safeProfileError(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [reload]);

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading eyebrow="Tài khoản" title="Hồ sơ cá nhân" description="Thông tin tài khoản của bạn." action={<button type="button" className="s2l-button" disabled={loading} onClick={() => setReload((value) => value + 1)}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>} />
      {loading && <p className="s2l-data-card" role="status">Đang tải hồ sơ…</p>}
      {error && <div className="s2l-alert" role="alert">{error}</div>}
      {profile && !error && <section className="s2l-data-card" aria-label="Thông tin tài khoản">
        <div className="tp-profile-head">
          <span className="tp-profile-avatar" aria-hidden="true">{(profile.display_name ?? profile.email ?? "?").trim().slice(0, 1).toUpperCase()}</span>
          <div className="tp-profile-name">
            <h2 className="tp-profile-heading"><GraduationCap size={18} aria-hidden="true" /> <span>{profile.display_name ?? "Chưa có tên hiển thị"}</span></h2>
          </div>
        </div>
        <dl className="tp-profile-list">
          <div><dt>Thư điện tử</dt><dd>{profile.email ?? "Chưa có thông tin"}</dd></div>
          <div><dt>Vai trò</dt><dd>Giáo viên</dd></div>
        </dl>
      </section>}
    </div>
  );
}
