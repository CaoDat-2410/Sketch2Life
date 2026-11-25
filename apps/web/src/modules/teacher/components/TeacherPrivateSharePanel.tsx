import { useRef, useState } from "react";
import type { AccessGrant, TeacherLessonDetail } from "../../../shared/api/backendApi";
import { BackendApiError, createIdempotencyKey } from "../../../shared/api/backendApi";
import { privateShareGate } from "../../../shared/api/lessonShareGate";
import {
  createPrivateShare,
  PRIVATE_SHARE_GROUP_STATE_MESSAGE,
  PRIVATE_SHARE_NOT_FOUND_MESSAGE,
  PRIVATE_SHARE_REVOKE_ERROR_MESSAGE,
  PRIVATE_SHARE_REVOKE_REQUEST_MESSAGE,
  PRIVATE_SHARE_REVOKE_STALE_MESSAGE,
  PRIVATE_SHARE_VALIDATION_MESSAGE,
  revokeAccessGrant,
  StaleAccessGrantRevisionError,
  type PrivateShareAudience,
  type PrivateShareCapability,
  type PrivateShareInput,
} from "../../../shared/api/lessonSharingApi";
import { BackendNotice } from "../../../shared/api/backendApi";
import { Button, FormField, Select } from "../../../shared/ui";

type Props = {
  organizationId: string;
  lesson: TeacherLessonDetail;
};

const capabilityLabels: Record<PrivateShareCapability, string> = {
  VIEW: "Xem",
  DOWNLOAD: "Tải xuống",
  REUSE: "Tái sử dụng",
};

const audienceLabels: Record<PrivateShareAudience, string> = {
  ORGANIZATION: "Tổ chức",
  PRINCIPAL: "Tài khoản phụ huynh",
  PARENT_GROUP: "Nhóm phụ huynh",
};

const stateLabels: Record<string, string> = {
  PENDING_REVIEW: "Chờ duyệt",
  INVITED: "Đang chờ phụ huynh",
  ACTIVE: "Đang chia sẻ",
  CHANGES_REQUESTED: "Cần chỉnh sửa",
  REVOKED: "Đã thu hồi",
};

function localDateTimeMinimum(): string {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

function formatExpiry(value: string | null): string {
  if (!value) return "Không đặt thời hạn";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Thời hạn đã chọn" : new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function creationError(cause: unknown, audience: PrivateShareAudience): string {
  if (cause instanceof BackendApiError) {
    if (cause.status === 404 || cause.code === "RESOURCE_NOT_FOUND") return PRIVATE_SHARE_NOT_FOUND_MESSAGE;
    if (audience === "PARENT_GROUP" && cause.status === 409 && (cause.code === "INVALID_TRANSITION" || cause.code === "INVALID_STATE_TRANSITION")) return PRIVATE_SHARE_GROUP_STATE_MESSAGE;
    if (cause.status === 422) return PRIVATE_SHARE_VALIDATION_MESSAGE;
  }
  return "Chưa thể tạo lượt chia sẻ lúc này. Vui lòng kiểm tra thông tin rồi thử lại.";
}

function revokeError(cause: unknown): string {
  if (cause instanceof StaleAccessGrantRevisionError) return PRIVATE_SHARE_REVOKE_STALE_MESSAGE;
  if (cause instanceof BackendApiError) {
    if (cause.status === 404 || cause.code === "RESOURCE_NOT_FOUND") return PRIVATE_SHARE_NOT_FOUND_MESSAGE;
    if (cause.status === 400) return PRIVATE_SHARE_REVOKE_REQUEST_MESSAGE;
  }
  return PRIVATE_SHARE_REVOKE_ERROR_MESSAGE;
}

export function TeacherPrivateSharePanel({ organizationId, lesson }: Props) {
  const gate = privateShareGate(lesson);
  const [audience, setAudience] = useState<PrivateShareAudience>("ORGANIZATION");
  const [audienceRef, setAudienceRef] = useState(organizationId);
  const [capability, setCapability] = useState<PrivateShareCapability>("VIEW");
  const [expiresAtLocal, setExpiresAtLocal] = useState("");
  const [grants, setGrants] = useState<AccessGrant[]>([]);
  const [creating, setCreating] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);
  const [rowError, setRowError] = useState<{ grantId: string; message: string } | null>(null);
  const createKeys = useRef(new Map<string, string>());
  const revokeKeys = useRef(new Map<string, string>());

  const submitShare = async () => {
    if (!gate.allowed) return;
    const normalizedRef = audience === "ORGANIZATION" ? organizationId.trim() : audienceRef.trim();
    if (!normalizedRef) {
      setCreateError(PRIVATE_SHARE_VALIDATION_MESSAGE);
      return;
    }

    let expiresAt: string | null = null;
    if (expiresAtLocal) {
      const date = new Date(expiresAtLocal);
      if (Number.isNaN(date.getTime()) || date.getTime() <= Date.now()) {
        setCreateError(PRIVATE_SHARE_VALIDATION_MESSAGE);
        return;
      }
      expiresAt = date.toISOString();
    }

    const input: PrivateShareInput = {
      lessonId: lesson.lesson_id,
      versionId: lesson.current_version.version_id,
      audienceKind: audience,
      audienceRef: normalizedRef,
      capability,
      expiresAt,
    };
    const signature = JSON.stringify([organizationId, input]);
    let key = createKeys.current.get(signature);
    if (!key) {
      key = createIdempotencyKey();
      createKeys.current.set(signature, key);
    }

    setCreating(true);
    setCreateError(null);
    try {
      const grant = await createPrivateShare(organizationId, input, key);
      createKeys.current.delete(signature);
      setGrants((current) => [...current.filter((item) => item.access_grant_id !== grant.access_grant_id), grant]);
    } catch (cause) {
      setCreateError(creationError(cause, audience));
    } finally {
      setCreating(false);
    }
  };

  const confirmRevoke = async (grant: AccessGrant) => {
    const signature = JSON.stringify([organizationId, lesson.lesson_id, grant.access_grant_id, grant.revision]);
    let key = revokeKeys.current.get(signature);
    if (!key) {
      key = createIdempotencyKey();
      revokeKeys.current.set(signature, key);
    }

    setRevokingId(grant.access_grant_id);
    setRowError(null);
    try {
      const updated = await revokeAccessGrant(organizationId, lesson.lesson_id, grant.access_grant_id, grant.revision, key);
      revokeKeys.current.delete(signature);
      setGrants((current) => current.map((item) => item.access_grant_id === updated.access_grant_id ? updated : item));
      setConfirmingId(null);
    } catch (cause) {
      if (cause instanceof StaleAccessGrantRevisionError && cause.currentVersion !== undefined) {
        setGrants((current) => current.map((item) => item.access_grant_id === grant.access_grant_id ? { ...item, revision: cause.currentVersion! } : item));
      }
      setRowError({ grantId: grant.access_grant_id, message: revokeError(cause) });
    } finally {
      setRevokingId(null);
    }
  };

  const gateMessage = gate.allowed
    ? null
    : gate.reason === "ARCHIVED"
      ? "Giáo án đã lưu trữ nên không thể tạo chia sẻ mới."
      : "Cần có phiên bản hiện tại trước khi tạo chia sẻ.";

  return (
    <section className="tw-card cozy-form-stack" aria-labelledby="teacher-private-share-title">
      <div className="tw-row tw-between tw-wrap">
        <h2 id="teacher-private-share-title" className="tw-h2" style={{ margin: 0 }}>Chia sẻ riêng tư</h2>
      </div>
      <p className="tw-sub">Danh sách chia sẻ chỉ hiển thị các chia sẻ vừa tạo trong phiên này.</p>
      {gateMessage && <p className="cozy-form-disabled-hint" role="status">{gateMessage}</p>}

      <div className="cozy-form-grid">
        <FormField className="cozy-span-2" label="Đối tượng nhận" htmlFor="private-share-audience">
          <Select
            id="private-share-audience"
            aria-label="Đối tượng nhận"
            value={audience}
            disabled={!gate.allowed || creating}
            onChange={(event) => {
              const next = event.target.value as PrivateShareAudience;
              setAudience(next);
              setAudienceRef(next === "ORGANIZATION" ? organizationId : "");
              setCreateError(null);
            }}
          >
            <option value="ORGANIZATION">Tổ chức hiện tại</option>
            <option value="PARENT_GROUP">Nhóm phụ huynh</option>
            <option value="PRINCIPAL">Tài khoản phụ huynh</option>
          </Select>
        </FormField>
        {audience === "ORGANIZATION" ? (
          <p className="cozy-form-disabled-hint cozy-span-2">Chia sẻ cho thành viên trong tổ chức hiện tại.</p>
        ) : (
          <FormField
            className="cozy-span-2"
            label={audience === "PARENT_GROUP" ? "ID nhóm phụ huynh" : "ID tài khoản phụ huynh"}
            htmlFor="private-share-audience-ref"
            required
            help={audience === "PARENT_GROUP" ? "Dán ID nhóm phụ huynh đã được tạo trong hệ thống." : "Dán ID tài khoản Parent cần nhận lời mời."}
          >
            <input
              id="private-share-audience-ref"
              className="cozy-input"
              maxLength={256}
              required
              disabled={!gate.allowed || creating}
              value={audienceRef}
              onChange={(event) => { setAudienceRef(event.target.value); setCreateError(null); }}
            />
          </FormField>
        )}
        <FormField className="cozy-span-2" label="Quyền được cấp" htmlFor="private-share-capability">
          <Select
            id="private-share-capability"
            aria-label="Quyền được cấp"
            value={capability}
            disabled={!gate.allowed || creating}
            onChange={(event) => { setCapability(event.target.value as PrivateShareCapability); setCreateError(null); }}
          >
            <option value="VIEW">Xem</option>
            <option value="DOWNLOAD">Tải xuống</option>
            <option value="REUSE">Tái sử dụng</option>
          </Select>
        </FormField>
        <FormField className="cozy-span-2" label="Hết hạn (không bắt buộc)" htmlFor="private-share-expires-at" help="Để trống nếu không đặt thời hạn.">
          <input
            id="private-share-expires-at"
            className="cozy-input"
            type="datetime-local"
            min={localDateTimeMinimum()}
            disabled={!gate.allowed || creating}
            value={expiresAtLocal}
            onChange={(event) => { setExpiresAtLocal(event.target.value); setCreateError(null); }}
          />
        </FormField>
      </div>
      {createError && <BackendNotice title="Không thể tạo chia sẻ" tone="error">{createError}</BackendNotice>}
      <div className="cozy-form-actions" style={{ marginTop: 0 }}>
        <Button type="button" variant="primary" disabled={!gate.allowed || creating} loading={creating} onClick={() => void submitShare()}>
          Tạo chia sẻ
        </Button>
      </div>

      {grants.length > 0 && (
        <div>
          <h3 className="tw-h2" style={{ fontSize: 17 }}>Chia sẻ trong phiên này</h3>
          <ul style={{ display: "grid", gap: 10, listStyle: "none", margin: 0, padding: 0 }}>
            {grants.map((grant) => {
              const grantAudience = grant.audience_kind in audienceLabels ? audienceLabels[grant.audience_kind as PrivateShareAudience] : "Đối tượng nhận";
              const grantCapability = grant.capability in capabilityLabels ? capabilityLabels[grant.capability as PrivateShareCapability] : "Quyền chia sẻ";
              const status = stateLabels[grant.state] ?? "Đang xử lý";
              return (
                <li key={grant.access_grant_id} className="tw-item">
                  <div className="tw-row tw-between tw-wrap">
                    <strong>{grantAudience}{grant.audience_ref ? ` · ${grant.audience_ref}` : ""}</strong>
                    <span className="tw-chip is-gray">{status}</span>
                  </div>
                  <p className="tw-meta">Quyền: {grantCapability} · Hết hạn: {formatExpiry(grant.expires_at)}</p>
                  {rowError?.grantId === grant.access_grant_id && (
                    <BackendNotice title="Chưa thể thu hồi chia sẻ" tone="error">
                      {rowError.message}{rowError.message === PRIVATE_SHARE_REVOKE_STALE_MESSAGE ? " Nhấn xác nhận để thử lại với phiên bản mới." : ""}
                    </BackendNotice>
                  )}
                  {grant.state !== "REVOKED" && (confirmingId === grant.access_grant_id ? (
                    <div className="tw-row tw-wrap" role="group" aria-label={`Xác nhận thu hồi ${grantAudience}`}>
                      <Button type="button" variant="danger" size="sm" disabled={revokingId === grant.access_grant_id} loading={revokingId === grant.access_grant_id} onClick={() => void confirmRevoke(grant)}>
                        Xác nhận thu hồi
                      </Button>
                      <Button type="button" size="sm" disabled={revokingId === grant.access_grant_id} onClick={() => { setConfirmingId(null); setRowError(null); }}>
                        Giữ chia sẻ
                      </Button>
                    </div>
                  ) : (
                    <Button type="button" variant="danger" size="sm" disabled={revokingId !== null} onClick={() => { setConfirmingId(grant.access_grant_id); setRowError(null); }}>
                      Thu hồi
                    </Button>
                  ))}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </section>
  );
}
