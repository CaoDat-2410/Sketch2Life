import React, { useEffect, useRef, useState } from "react";
import { MgIcon } from "../components/MgIcon";
import { Alert, Button, FormField } from "../../../shared/ui";
import {
  BackendApiError,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  createIdempotencyKey,
  hasFirebaseAuthBridge,
  type AccessGrant,
  type TeacherLessonDetail,
} from "../../../shared/api/backendApi";

type Toast = (text: string, kind?: "ok" | "info" | "warn" | "err") => void;

function PageHeading({ eyebrow, title, description, actions }: {
  eyebrow: string;
  title: string;
  description: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="manager-page-heading">
      <div className="manager-page-heading-copy">
        <p className="manager-eyebrow"><span aria-hidden="true" />{eyebrow}</p>
        <div className="manager-page-heading-row">
          <div><h1>{title}</h1><p>{description}</p></div>
          {actions && <div className="manager-page-actions">{actions}</div>}
        </div>
      </div>
    </div>
  );
}

function StatusPanel({ kind = "info", title, children, action }: {
  kind?: "info" | "warning" | "error" | "loading" | "empty";
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  const icon = kind === "error" ? "alert" : kind === "warning" ? "shield" : kind === "loading" ? "refresh" : kind === "empty" ? "list" : "info";
  return (
    <section className={`manager-status-panel is-${kind}`} role={kind === "error" ? "alert" : "status"}>
      <span className="manager-status-icon" aria-hidden="true"><MgIcon name={icon} size={20} variant="standard" /></span>
      <div className="manager-status-copy"><h2>{title}</h2><div>{children}</div></div>
      {action && <div className="manager-status-action">{action}</div>}
    </section>
  );
}

type ReviewLoadState = "loading" | "ready" | "error";

function ManagerApiReviewPage({ showToast }: { showToast: Toast }) {
  const [grants, setGrants] = useState<AccessGrant[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [lesson, setLesson] = useState<TeacherLessonDetail | null>(null);
  const [reviewConfirmed, setReviewConfirmed] = useState(false);
  const [reason, setReason] = useState("");
  const [loadState, setLoadState] = useState<ReviewLoadState>("loading");
  const [loadingMore, setLoadingMore] = useState(false);
  const [lessonLoading, setLessonLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [lessonError, setLessonError] = useState<string | null>(null);
  const [pageError, setPageError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const decisionKeys = useRef(new Map<string, string>());
  const selected = grants.find((grant) => grant.access_grant_id === selectedId) ?? grants[0];
  const versionMatches = Boolean(selected && lesson && lesson.current_version.version_id === selected.version_id);
  const content = versionMatches ? lesson?.current_version.content ?? null : null;
  const canReview = Boolean(versionMatches && content);

  useEffect(() => {
    let active = true;
    setGrants([]);
    setSelectedId("");
    setNextCursor(null);
    setError(null);
    const organizationId = configuredOrganizationId();
    if (!hasFirebaseAuthBridge()) {
      setError("Cần phiên Firebase đã xác thực để xác minh quyền School Manager.");
      setLoadState("error");
      return () => { active = false; };
    }
    if (!organizationId) {
      setError("Chưa cấu hình organization_id cho API duyệt công khai.");
      setLoadState("error");
      return () => { active = false; };
    }

    setLoadState("loading");
    backendApi.assignments(organizationId)
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "school_admin" && assignment.active !== false)) {
          throw new BackendApiError("Tài khoản không có assignment School Manager đang hoạt động trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return backendApi.accessGrants(organizationId, { state: "PENDING_REVIEW", audience_kind: "PUBLIC" });
      })
      .then((page) => {
        if (!active) return;
        const pending = page.items.filter((grant) => grant.audience_kind === "PUBLIC" && grant.state === "PENDING_REVIEW");
        setGrants(pending);
        setNextCursor(page.next_cursor);
        setSelectedId(pending[0]?.access_grant_id ?? "");
        setLoadState("ready");
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setError(backendMessage(cause));
        setLoadState("error");
      });
    return () => { active = false; };
  }, [reload]);

  useEffect(() => {
    let active = true;
    setLesson(null);
    setLessonError(null);
    setDecisionError(null);
    setReviewConfirmed(false);
    setReason("");
    if (!selected || loadState !== "ready") {
      setLessonLoading(false);
      return () => { active = false; };
    }
    const organizationId = configuredOrganizationId();
    if (!organizationId) {
      setLessonError("Chưa cấu hình organization_id để tải nội dung giáo án.");
      setLessonLoading(false);
      return () => { active = false; };
    }
    setLessonLoading(true);
    backendApi.teacherLesson(organizationId, selected.lesson_id)
      .then((result) => { if (active) setLesson(result); })
      .catch((cause: unknown) => { if (active) setLessonError(backendMessage(cause)); })
      .finally(() => { if (active) setLessonLoading(false); });
    return () => { active = false; };
  }, [selected?.access_grant_id, selected?.lesson_id, selected?.version_id, loadState]);

  const loadMore = async () => {
    const cursor = nextCursor;
    const organizationId = configuredOrganizationId();
    if (!cursor || !organizationId || loadingMore) return;
    setLoadingMore(true);
    setPageError(null);
    try {
      const page = await backendApi.accessGrants(organizationId, { state: "PENDING_REVIEW", audience_kind: "PUBLIC", cursor });
      const pending = page.items.filter((grant) => grant.audience_kind === "PUBLIC" && grant.state === "PENDING_REVIEW");
      setGrants((current) => {
        const byId = new Map(current.map((grant) => [grant.access_grant_id, grant] as const));
        pending.forEach((grant) => byId.set(grant.access_grant_id, grant));
        return Array.from(byId.values());
      });
      setNextCursor(page.next_cursor);
    } catch (cause) {
      setPageError(backendMessage(cause));
    } finally {
      setLoadingMore(false);
    }
  };

  const decide = async (decision: "APPROVE" | "REQUEST_CHANGES") => {
    if (!selected || !canReview || (decision === "APPROVE" && !reviewConfirmed)) return;
    const normalizedReason = reason.trim();
    if (decision === "REQUEST_CHANGES" && !normalizedReason) return;
    const organizationId = configuredOrganizationId();
    const signature = JSON.stringify([selected.access_grant_id, selected.revision, selected.version_id, decision, normalizedReason]);
    let idempotencyKey = decisionKeys.current.get(signature);
    if (!idempotencyKey) {
      idempotencyKey = createIdempotencyKey();
      decisionKeys.current.set(signature, idempotencyKey);
    }
    setBusy(true);
    setDecisionError(null);
    try {
      await backendApi.decideAccessGrant(organizationId, selected, decision, normalizedReason || undefined, idempotencyKey);
      decisionKeys.current.delete(signature);
      showToast(decision === "APPROVE" ? "API đã nhận quyết định duyệt grant PUBLIC." : "API đã nhận yêu cầu chỉnh sửa cho grant PUBLIC.", "ok");
      setReload((value) => value + 1);
    } catch (cause) {
      setDecisionError(backendMessage(cause));
      showToast("API chưa xác nhận quyết định. Kiểm tra trạng thái trước khi gửi lại.", "err");
    } finally {
      setBusy(false);
    }
  };

  const pageHeading = (
    <PageHeading
      eyebrow="HỌC LIỆU / QUYỀN CÔNG KHAI"
      title="Duyệt học liệu công khai"
      description="Xem nội dung đúng immutable version được gửi duyệt trước khi ra quyết định. Màn này không tải media hoặc story của trẻ."
      actions={<button type="button" className="manager-button is-outline" disabled={loadState === "loading" || busy} onClick={() => setReload((value) => value + 1)}><MgIcon name="refresh" size={16} variant="navigation" /> Tải lại</button>}
    />
  );

  return (
    <div className="manager-page">
      {pageHeading}
      {error && <StatusPanel title="Không tải hoặc cập nhật được hàng đợi" kind="error">{error}</StatusPanel>}
      {loadState === "loading" && <StatusPanel title="Đang xác minh quyền và hàng đợi" kind="loading">Đang kiểm tra assignment School Manager, sau đó đọc grant PUBLIC đang chờ.</StatusPanel>}
      {pageError && <StatusPanel title="Không tải được trang tiếp theo" kind="error">{pageError}</StatusPanel>}

      <div className="manager-review-counts" aria-label="Tóm tắt trạng thái review">
        <div><span className="manager-count-dot is-pending" aria-hidden="true" /><strong>{loadState === "ready" ? grants.length : "—"}</strong><span>Yêu cầu đang hiển thị · chờ duyệt</span></div>
        <div><span className="manager-count-dot is-approved" aria-hidden="true" /><strong>Chưa có API tổng hợp</strong><span>Đã duyệt</span></div>
        <div><span className="manager-count-dot is-changes" aria-hidden="true" /><strong>Chưa có API tổng hợp</strong><span>Yêu cầu chỉnh sửa</span></div>
      </div>

      {loadState === "ready" && grants.length === 0 && <StatusPanel kind="empty" title="Không có grant PUBLIC đang chờ">API không trả về grant ở trạng thái PENDING_REVIEW trong trang hiện tại.</StatusPanel>}
      {loadState === "ready" && grants.length > 0 && (
        <div className="manager-review-grid">
          <section className="manager-section-card manager-review-queue" aria-labelledby="manager-review-queue-title">
            <div className="manager-section-heading"><div><p className="manager-eyebrow"><span aria-hidden="true" />HÀNG ĐỢI</p><h2 id="manager-review-queue-title">Đang chờ quyết định</h2></div><span className="manager-count-tag">{grants.length}</span></div>
            <div className="manager-review-list">
              {grants.map((grant) => (
                <button
                  type="button"
                  key={grant.access_grant_id}
                  className={`manager-review-item${grant.access_grant_id === selected?.access_grant_id ? " is-active" : ""}`}
                  aria-pressed={grant.access_grant_id === selected?.access_grant_id}
                  disabled={busy}
                  onClick={() => { setSelectedId(grant.access_grant_id); setReviewConfirmed(false); setReason(""); }}
                >
                  <span className="manager-review-item-icon" aria-hidden="true"><MgIcon name="book" size={19} variant="navigation" /></span>
                  <span className="manager-review-item-copy"><strong>{grant.lesson_id}</strong><span>Phiên bản {grant.version_id}</span></span>
                  <span className="manager-status-tag is-pending">Chờ duyệt</span>
                </button>
              ))}
            </div>
            {nextCursor && <button type="button" className="manager-button is-outline is-full" disabled={loadingMore || busy} onClick={() => void loadMore()}>{loadingMore ? "Đang tải…" : "Tải thêm yêu cầu"}</button>}
          </section>

          {selected && <section className="manager-section-card cozy-form-card manager-review-detail" aria-labelledby="manager-review-detail-title">
            <div className="manager-section-heading manager-review-detail-heading">
              <div><p className="manager-eyebrow"><span aria-hidden="true" />CHI TIẾT GRANT</p><h2 id="manager-review-detail-title">{content?.title ?? `Giáo án ${selected.lesson_id}`}</h2></div>
              <span className="manager-status-tag is-pending">PUBLIC · {selected.state}</span>
            </div>
            <div className="manager-review-meta">
              <div><span>Phiên bản trong grant</span><strong>{selected.version_id}</strong></div>
              <div><span>Phiên bản hiện tại</span><strong>{lesson ? lesson.current_version.version_id : lessonLoading ? "Đang tải…" : "Chưa tải được"}</strong></div>
              <div><span>Revision</span><strong>{selected.revision}</strong></div>
            </div>
            <div className="manager-privacy-note"><MgIcon name="lock" size={17} variant="navigation" /> Chỉ structured content của giáo án; không tải media/story của trẻ.</div>
            {lessonLoading && <StatusPanel kind="loading" title="Đang tải chi tiết giáo án">Đang so sánh current version từ API với version_id trong grant.</StatusPanel>}
            {lessonError && <StatusPanel kind="error" title="Không tải được nội dung">{lessonError}</StatusPanel>}
            {!lessonLoading && lesson && lesson.current_version.version_id !== selected.version_id && <StatusPanel kind="warning" title="Grant trỏ tới phiên bản cũ">API hiện chỉ trả current version ({lesson.current_version.version_id}); grant yêu cầu {selected.version_id}. Chưa có GET-by-version nên không thể xem hoặc ra quyết định.</StatusPanel>}
            {!lessonLoading && versionMatches && !content && <StatusPanel kind="warning" title="API chưa trả structured content">Không có nội dung để rà; thao tác quyết định vẫn bị khóa.</StatusPanel>}
            {content && <div className="manager-lesson-content">
              <div className="manager-content-block"><span>Chủ đề</span><p>{content.topic}</p></div>
              <div className="manager-content-block"><span>Mục tiêu</span><ul>{content.objectives.map((objective, index) => <li key={`${index}-${objective}`}>{objective}</li>)}</ul></div>
              <div className="manager-content-block"><span>{content.drawing_subject}</span><p className="manager-preserve-lines">{content.drawing_steps_text}</p><p className="manager-preserve-lines">{content.subject_learning_notes}</p></div>
              {content.activities.map((activity, index) => <article className="manager-activity-block" key={`${index}-${activity.title}`}><h3>Hoạt động {index + 1}: {activity.title}</h3><p><strong>Mục tiêu:</strong> {activity.objective}</p><p className="manager-preserve-lines"><strong>Hướng dẫn:</strong> {activity.instructions_text}</p>{activity.materials_text && <p><strong>Chuẩn bị:</strong> {activity.materials_text}</p>}{activity.safety_notes && <p className="manager-preserve-lines"><strong>An toàn:</strong> {activity.safety_notes}</p>}</article>)}
            </div>}

            <form className="manager-review-decision cozy-form-stack" onSubmit={(event) => event.preventDefault()}>
              <div className="cozy-form-field">
                <label className={`manager-confirm-row${!canReview ? " is-disabled" : ""}`}>
                  <input type="checkbox" checked={reviewConfirmed} disabled={!canReview || busy} onChange={(event) => setReviewConfirmed(event.target.checked)} />
                  <span>Tôi đã rà đúng nội dung của phiên bản trong grant.</span>
                </label>
                {canReview && !reviewConfirmed && (
                  <p className="cozy-form-hint" style={{ marginTop: 0 }}>
                    Đánh dấu xác nhận để bật nút Duyệt công khai.
                  </p>
                )}
              </div>
              <FormField
                label={<>Lý do yêu cầu chỉnh sửa <span>(bắt buộc khi trả về)</span></>}
                htmlFor="manager-change-reason"
                help={canReview && !reason.trim() ? "Nhập lý do để bật nút Yêu cầu chỉnh sửa." : undefined}
              >
                <textarea id="manager-change-reason" className="cozy-textarea" rows={2} maxLength={1000} disabled={!canReview || busy} value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Nêu rõ phần cần chỉnh sửa" />
              </FormField>
              {decisionError && <Alert role="alert" tone="danger">{decisionError}</Alert>}
              <div className="cozy-form-actions manager-decision-actions" style={{ marginTop: 0 }}>
                <Button type="button" variant="secondary" loading={busy} disabled={busy || !canReview || !reason.trim()} iconLeft={<MgIcon name="pencil" size={17} variant="navigation" />} onClick={() => void decide("REQUEST_CHANGES")}>
                  Yêu cầu chỉnh sửa
                </Button>
                <Button type="button" variant="primary" loading={busy} disabled={busy || !canReview || !reviewConfirmed} iconLeft={<MgIcon name="check" size={17} variant="navigation" />} onClick={() => void decide("APPROVE")}>
                  Duyệt công khai
                </Button>
              </div>
              <p className="manager-counter-boundary">Danh sách API hiện chỉ cung cấp grant đang chờ. Bộ đếm lịch sử “Đã duyệt” và “Yêu cầu chỉnh sửa” không được suy ra từ hàng đợi này.</p>
            </form>
          </section>}
        </div>
      )}
    </div>
  );
}

export function M01PublicationReviewPage({ showToast }: { showToast: Toast }) {
  return <ManagerApiReviewPage showToast={showToast} />;
}
