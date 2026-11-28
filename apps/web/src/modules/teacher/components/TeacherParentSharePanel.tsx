import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { BackendApiError, createIdempotencyKey } from "../../../shared/api/backendApi";
import { teacherProfileShareApi, type ParentSharedProfile } from "../../../shared/api/teacherProfileShareApi";
import { Button, FormField, StatusBadge, formatDateDdMmYyyy } from "../../../shared/ui";
import { teacherAgeBandLabel } from "../services/ageBands";
import { FormActionBar } from "./FormActionBar";

function shareError(cause: unknown, reading = false): string {
  if (cause instanceof BackendApiError) {
    if (cause.status === 404 || cause.status === 403) return "Không tìm thấy dữ liệu hoặc bạn không có quyền truy cập.";
    if (cause.status === 400) return "Mã chia sẻ chưa hợp lệ. Hãy kiểm tra rồi thử lại.";
    if (cause.status === 409) {
      if (cause.code === "INVITATION_EXPIRED") return "Mã chia sẻ đã hết hạn. Hãy nhờ phụ huynh tạo mã mới.";
      if (cause.code === "CONSENT_NOT_EFFECTIVE") return "Hồ sơ hiện chưa đủ điều kiện chia sẻ.";
      if (cause.code === "RESOURCE_CONFLICT") return "Hồ sơ đã có một liên kết chia sẻ đang hiệu lực.";
      if (cause.code === "INVALID_STATE_TRANSITION") return "Lớp hiện không cho phép chấp nhận chia sẻ.";
    }
    if (cause.status === 503 || cause.status === 0) return "Dịch vụ chia sẻ tạm thời chưa sẵn sàng. Hãy thử lại sau.";
  }
  return reading ? "Chưa thể đọc thông tin được chia sẻ." : "Chưa thể chấp nhận chia sẻ. Hãy thử lại sau.";
}

export function TeacherParentSharePanel({ organizationId, classId, childId, canAccept }: {
  organizationId: string; classId: string; childId: string; canAccept: boolean;
}) {
  const [shared, setShared] = useState<ParentSharedProfile | null>(null);
  const [status, setStatus] = useState("Đang kiểm tra chia sẻ…");
  const [code, setCode] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const keys = useRef(new Map<string, string>());

  useEffect(() => {
    let active = true;
    setStatus("Đang kiểm tra chia sẻ…");
    setShared(null);
    teacherProfileShareApi.getSharedProfile(organizationId, classId, childId)
      .then((value) => { if (active) { setShared(value); setStatus("Đang chia sẻ"); } })
      .catch((cause: unknown) => {
        if (!active) return;
        setShared(null);
        setStatus(cause instanceof BackendApiError && cause.status === 404
          ? "Chưa có chia sẻ từ phụ huynh."
          : shareError(cause, true));
      });
    return () => { active = false; };
  }, [organizationId, classId, childId, reload]);

  const normalizedCode = code.trim();
  const validCode = /^[A-Za-z0-9_-]{16,64}$/.test(normalizedCode);
  const accept = async () => {
    if (!canAccept || !validCode || busy) return;
    const signature = JSON.stringify([organizationId, classId, childId, normalizedCode]);
    const key = keys.current.get(signature) ?? createIdempotencyKey();
    keys.current.set(signature, key);
    setBusy(true);
    setError(null);
    try {
      await teacherProfileShareApi.accept(organizationId, classId, childId, normalizedCode, key);
      keys.current.delete(signature);
      setCode("");
      setConfirming(false);
      const profile = await teacherProfileShareApi.getSharedProfile(organizationId, classId, childId);
      setShared(profile);
      setStatus("Đang chia sẻ");
    } catch (cause) {
      setError(shareError(cause));
      if (cause instanceof BackendApiError && cause.status < 500 && cause.status !== 0) keys.current.delete(signature);
      if (cause instanceof BackendApiError && (cause.status === 404 || cause.status === 409)) setReload((value) => value + 1);
    } finally {
      setBusy(false);
    }
  };

  return (
    <details className="s2l-data-card tp-share tp-collapsible">
      <summary className="tp-collapsible-summary">
        <span className="tp-collapsible-title">
          <span>Chia sẻ từ phụ huynh</span>
          {shared && <StatusBadge tone="success" size="sm" dot>Đang chia sẻ</StatusBadge>}
        </span>
        <ChevronDown size={16} aria-hidden="true" />
      </summary>
      <div className="tp-collapsible-body" role="region" aria-label="Chia sẻ từ phụ huynh">
        <p className="s2l-muted-copy" role="status">{status}</p>
        {shared && <div className="tp-share-body">
          <p>Thông tin hiện được chia sẻ đến {formatDateDdMmYyyy(shared.expires_at)}.</p>
          <div className="tp-field-grid">
            {"display_name" in shared.fields && <p className="tp-field"><strong>Tên hiển thị:</strong> <span>{shared.fields.display_name ?? "Chưa có thông tin"}</span></p>}
            {"age_band" in shared.fields && <p className="tp-field"><strong>Nhóm tuổi:</strong> <span>{shared.fields.age_band ? teacherAgeBandLabel(shared.fields.age_band.band_ref) : "Chưa có thông tin"}</span></p>}
            {"interests_summary" in shared.fields && <p className="tp-field"><strong>Sở thích:</strong> <span>{shared.fields.interests_summary ?? "Chưa có thông tin"}</span></p>}
          </div>
        </div>}
        {canAccept && !shared && <div className="tp-share-form">
          <FormField label="Mã do phụ huynh cung cấp" htmlFor={`parent-share-code-${childId}`} help="Nhập mã gồm 16–64 ký tự do phụ huynh gửi.">
            <input id={`parent-share-code-${childId}`} className="cozy-input" value={code} maxLength={64} disabled={busy} autoComplete="off" onChange={(event) => { setCode(event.target.value); setConfirming(false); setError(null); }} />
          </FormField>
          {!confirming ? (
            <FormActionBar hint={!busy && !validCode ? "Nhập đủ mã chia sẻ hợp lệ để bật nút xác nhận." : undefined}>
              <Button type="button" variant="primary" disabled={busy || !validCode} onClick={() => setConfirming(true)}>Chấp nhận chia sẻ</Button>
            </FormActionBar>
          ) : (
            <div role="group" aria-label="Xác nhận chấp nhận chia sẻ">
              <FormActionBar hint="Chấp nhận các trường hồ sơ mà phụ huynh đã chọn?">
                <Button type="button" variant="secondary" disabled={busy} onClick={() => setConfirming(false)}>Hủy</Button>
                <Button type="button" variant="primary" loading={busy} disabled={busy || !validCode} onClick={() => void accept()}>{busy ? "Đang xác nhận…" : "Xác nhận chấp nhận"}</Button>
              </FormActionBar>
            </div>
          )}
        </div>}
        {error && <p className="s2l-alert" role="alert">{error}</p>}
      </div>
    </details>
  );
}
