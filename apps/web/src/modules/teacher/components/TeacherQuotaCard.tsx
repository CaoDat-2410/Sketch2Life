import { useEffect, useState } from "react";
import { BackendApiError, configuredOrganizationId } from "../../../shared/api/backendApi";
import { teacherQuotaApi, type TeacherVideoQuota } from "../../../shared/api/teacherQuotaApi";

function quotaError(cause: unknown): string {
  if (cause instanceof BackendApiError && cause.status === 503) return "Dịch vụ hạn mức video tạm thời chưa sẵn sàng.";
  if (cause instanceof BackendApiError && cause.status === 401) return "Phiên đăng nhập chưa sẵn sàng.";
  return "Chưa tải được số dư lượt tạo video.";
}

export function TeacherQuotaCard({ reloadKey }: { reloadKey: number }) {
  const organizationId = configuredOrganizationId();
  const [retry, setRetry] = useState(0);
  const requestKey = JSON.stringify([organizationId, reloadKey, retry]);
  const [result, setResult] = useState<
    | { key: string; status: "loading" }
    | { key: string; status: "success"; quota: TeacherVideoQuota }
    | { key: string; status: "error"; message: string }
  >({ key: "", status: "loading" });

  useEffect(() => {
    let active = true;
    if (!organizationId) return () => { active = false; };
    teacherQuotaApi.getMyVideoQuota(organizationId)
      .then((quota) => { if (active) setResult({ key: requestKey, status: "success", quota }); })
      .catch((cause: unknown) => { if (active) setResult({ key: requestKey, status: "error", message: quotaError(cause) }); });
    return () => { active = false; };
  }, [organizationId, requestKey]);

  const current = result.key === requestKey ? result : null;
  const loading = !!organizationId && (!current || current.status === "loading");
  const error = !organizationId ? "Chưa cấu hình tổ chức để tải số dư hạn mức." : current?.status === "error" ? current.message : "";
  const quota = current?.status === "success" ? current.quota : null;

  return <article className="s2l-data-card s2l-dashboard-card">
    <div className="s2l-dashboard-card-title"><div><h2>Hạn mức video cá nhân</h2><p>Lượt được phân bổ từ hạn mức của tổ chức</p></div></div>
    {loading && <p role="status">Đang tải số dư lượt tạo video…</p>}
    {!loading && error && <div className="s2l-alert" role="alert">{error} <button type="button" className="s2l-button" onClick={() => setRetry((value) => value + 1)}>Thử lại</button></div>}
    {!loading && !error && (!quota?.allocation || !quota.allocation.active) && <p>Chưa được cấp lượt tạo video</p>}
    {!loading && !error && quota?.allocation?.active && <p>Số dư lượt tạo video: <strong>{quota.allocation.available_units}</strong></p>}
  </article>;
}
