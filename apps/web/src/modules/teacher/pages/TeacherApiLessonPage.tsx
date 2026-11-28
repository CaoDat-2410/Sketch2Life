import React, { useEffect, useId, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BackendApiError,
  BackendModeNotice,
  BackendNotice,
  backendApi,
  backendMessage,
  configuredOrganizationId,
  createIdempotencyKey,
  hasFirebaseAuthBridge,
  type LessonActivity,
  type LessonContent,
  type LessonSummary,
  type TeacherLessonDetail,
} from "../../../shared/api/backendApi";
import { usePortalSession } from "../../../shared/auth/PortalSessionContext";
import { Icon } from "../components/Icon";
import { FormActionBar } from "../components/FormActionBar";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { Button, ConfirmDialog, FormField, Select, StatusBadge, Tabs, type TabItem } from "../../../shared/ui";
import { commandSignature, isStaleRevision, keyForCommand } from "../services/commandKeys";
import { teacherStatusMeta } from "../services/teacherStatus";
import { isTeacherAgeBand, TEACHER_AGE_BANDS } from "../services/ageBands";
import { LessonVersionsPanel } from "../components/LessonVersionsPanel";
import { TeacherPrivateSharePanel } from "../components/TeacherPrivateSharePanel";
import { PublicLessonSearchPanel } from "../components/PublicLessonSearchPanel";
import type { PublicLessonHit, RemixLessonResult } from "../../../shared/api/teacherLessonLibraryApi";

type LessonTab = "content" | "share" | "versions";

const LESSON_TABS: readonly TabItem[] = [
  { value: "content", label: "Nội dung" },
  { value: "share", label: "Chia sẻ" },
  { value: "versions", label: "Phiên bản" },
];

function activityHasDetails(activity: LessonActivity): boolean {
  return Boolean(
    activity.materials_text.trim() ||
    activity.preparation_text.trim() ||
    activity.observation_notes.trim(),
  );
}

const blankActivity = (): LessonActivity => ({
  title: "",
  objective: "",
  materials_text: "",
  preparation_text: "",
  instructions_text: "",
  observation_notes: "",
  safety_notes: "",
  activity_kind: "outdoor",
});

const blankContent = (): LessonContent => ({
  locale: "vi-VN",
  title: "",
  topic: "",
  target_age_band_ref: "",
  target_age_band_version: 0,
  objectives: [""],
  drawing_subject: "",
  drawing_steps_text: "",
  subject_learning_notes: "",
  script_direction: null,
  script_following_allowed: false,
  activities: [blankActivity()],
});

type LessonSummaryWithState = LessonSummary & { state?: string };

function withoutArchivedLessons(items: LessonSummary[], hiddenIds: ReadonlySet<string>): LessonSummary[] {
  return items.filter((item) => {
    const state = (item as LessonSummaryWithState).state?.toUpperCase();
    return state !== "ARCHIVED" && !hiddenIds.has(item.lesson_id);
  });
}

export function TeacherApiLessonPage() {
  const navigate = useNavigate();
  const { showToast } = usePortalSession();
  const [items, setItems] = useState<LessonSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<TeacherLessonDetail | null>(null);
  const [content, setContent] = useState<LessonContent>(blankContent);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pageError, setPageError] = useState<string | null>(null);
  const [moreError, setMoreError] = useState<string | null>(null);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  // FEAT-066 C4: set after a 409 STALE_REVISION; the Teacher chooses when to load the current version.
  const [staleRevision, setStaleRevision] = useState(false);
  const [pendingArchive, setPendingArchive] = useState<{ organizationId: string; detail: TeacherLessonDetail } | null>(null);
  const [remixProvenance, setRemixProvenance] = useState<{ title: string; lessonId: string; versionId: string } | null>(null);
  const [activeTab, setActiveTab] = useState<LessonTab>("content");
  const [searchDisclosureOpen, setSearchDisclosureOpen] = useState(false);
  const [activityDetailsOverrides, setActivityDetailsOverrides] = useState<Record<number, boolean>>({});
  const [reload, setReload] = useState(0);
  const tabIdBase = useId();
  const detailErrorRef = useRef<HTMLDivElement | null>(null);
  const mutationKeys = useRef(new Map<string, string>());
  const skipNextDetailLoad = useRef<string | null>(null);
  const pendingRemixSummary = useRef<LessonSummary | null>(null);
  const hiddenArchivedLessonIds = useRef(new Set<string>());
  const organizationId = configuredOrganizationId();
  const hasAuthBridge = hasFirebaseAuthBridge();
  const hasUnsavedContent = JSON.stringify(content) !== JSON.stringify(detail?.current_version.content ?? blankContent());

  useEffect(() => {
    if (!hasUnsavedContent) return;
    const warnBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeUnload);
    return () => window.removeEventListener("beforeunload", warnBeforeUnload);
  }, [hasUnsavedContent]);

  useEffect(() => {
    let active = true;
    if (!hasFirebaseAuthBridge()) {
      setPageError("Chưa có phiên đăng nhập để tải giáo án.");
      setLoading(false);
      return () => { active = false; };
    }
    if (!organizationId) {
      setPageError("Chưa cấu hình tổ chức cho thư viện giáo án.");
      setLoading(false);
      return () => { active = false; };
    }
    setLoading(true);
    setPageError(null);
    setMoreError(null);
    setNextCursor(null);
    backendApi.assignments(organizationId)
      .then((identity) => {
        if (!identity.assignments.some((assignment) => assignment.role === "teacher")) {
          throw new BackendApiError("Tài khoản chưa được phân công vai trò giáo viên trong tổ chức này.", "ROLE_MISMATCH", 403);
        }
        return backendApi.lessons(organizationId, { state: "ACTIVE" });
      })
      .then((page) => {
        if (!active) return;
        const visibleItems = withoutArchivedLessons(page.items, hiddenArchivedLessonIds.current);
        const pinned = pendingRemixSummary.current;
        const includesPinned = pinned && visibleItems.some((item) => item.lesson_id === pinned.lesson_id);
        if (includesPinned) pendingRemixSummary.current = null;
        const visiblePinned = pinned && !hiddenArchivedLessonIds.current.has(pinned.lesson_id) ? pinned : null;
        setItems(visiblePinned && !includesPinned ? [visiblePinned, ...visibleItems] : visibleItems);
        setNextCursor(page.next_cursor);
      })
      .catch((cause: unknown) => { if (active) setPageError(backendMessage(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [organizationId, reload]);

  useEffect(() => {
    let active = true;
    if (!selectedId) {
      setDetail(null);
      setDetailError(null);
      return () => { active = false; };
    }
    if (skipNextDetailLoad.current === selectedId) {
      skipNextDetailLoad.current = null;
      return;
    }
    setDetail(null);
    setContent(blankContent());
    setActivityDetailsOverrides({});
    setDetailError(null);
    setStaleRevision(false);
    backendApi.teacherLesson(organizationId, selectedId)
      .then((result) => {
        if (!active) return;
        setDetail(result);
        setActivityDetailsOverrides({});
        if (result.current_version.content) setContent(result.current_version.content);
        else setDetailError("Phiên bản hiện tại chưa có nội dung giáo án để chỉnh sửa.");
      })
      .catch((cause: unknown) => { if (active) setDetailError(backendMessage(cause)); })
      .finally(() => { if (active) setSaving(false); });
    return () => { active = false; };
  }, [organizationId, selectedId]);

  useEffect(() => {
    if (detailError) {
      detailErrorRef.current?.scrollIntoView?.({ block: "nearest" });
    }
  }, [detailError]);

  const loadMoreLessons = async () => {
    const cursor = nextCursor;
    if (!cursor || !organizationId || loadingMore) return;
    setLoadingMore(true);
    setMoreError(null);
    try {
      const page = await backendApi.lessons(organizationId, { state: "ACTIVE", cursor });
      const visibleItems = withoutArchivedLessons(page.items, hiddenArchivedLessonIds.current);
      setItems((current) => {
        const byId = new Map<string, LessonSummary>(current.map((item) => [item.lesson_id, item] as const));
        visibleItems.forEach((item) => byId.set(item.lesson_id, item));
        return Array.from(byId.values());
      });
      setNextCursor(page.next_cursor);
    } catch (cause) {
      setMoreError(backendMessage(cause));
    } finally {
      setLoadingMore(false);
    }
  };

  const updateContent = (change: Partial<LessonContent>) => setContent((current) => ({ ...current, ...change }));
  const updateActivity = (index: number, change: Partial<LessonActivity>) => updateContent({
    activities: content.activities.map((activity, i) => i === index ? { ...activity, ...change } : activity),
  });

  const newLesson = () => {
    setSelectedId(null);
    setDetail(null);
    setContent(blankContent());
    setActivityDetailsOverrides({});
    setDetailError(null);
    setStaleRevision(false);
    setRemixProvenance(null);
    setActiveTab("content");
    setSearchDisclosureOpen(false);
  };

  const openRemixedLesson = (result: RemixLessonResult, hit: PublicLessonHit) => {
    const remixed = result.lesson;
    skipNextDetailLoad.current = remixed.lesson_id;
    setSelectedId(remixed.lesson_id);
    setDetail(remixed);
    setActivityDetailsOverrides({});
    if (remixed.current_version.content) setContent(remixed.current_version.content);
    setDetailError(null);
    setStaleRevision(false);
    setActiveTab("content");
    setRemixProvenance({ title: hit.title, lessonId: result.source.lesson_id, versionId: result.source.version_id });
    const summary: LessonSummary = {
      contract: "LessonSummaryV1",
      lesson_id: remixed.lesson_id,
      title: remixed.current_version.content?.title ?? hit.title,
      topic: remixed.current_version.content?.topic ?? hit.topic,
      current_version_no: remixed.current_version.version_no,
      review_state: remixed.current_version.review_state,
      visibility: remixed.visibility,
      activity_count: remixed.current_version.content?.activities.length ?? hit.activity_count,
      updated_at: remixed.updated_at,
    };
    pendingRemixSummary.current = summary;
    setItems((current) => [summary, ...current.filter((item) => item.lesson_id !== remixed.lesson_id)]);
    setReload((value) => value + 1);
  };

  const normalizedContent = (): LessonContent => ({
    ...content,
    title: content.title.trim(),
    topic: content.topic.trim(),
    target_age_band_ref: content.target_age_band_ref,
    objectives: content.objectives.map((objective) => objective.trim()).filter(Boolean),
    drawing_subject: content.drawing_subject.trim(),
    drawing_steps_text: content.drawing_steps_text.trim(),
    subject_learning_notes: content.subject_learning_notes.trim(),
    script_direction: content.script_direction?.trim() || null,
    activities: content.activities.map((activity) => ({
      ...activity,
      title: activity.title.trim(),
      objective: activity.objective.trim(),
      materials_text: activity.materials_text.trim(),
      preparation_text: activity.preparation_text.trim(),
      instructions_text: activity.instructions_text.trim(),
      observation_notes: activity.observation_notes.trim(),
      safety_notes: activity.safety_notes.trim(),
    })),
  });

  const save = async (event: React.FormEvent) => {
    event.preventDefault();
    const payload = normalizedContent();
    if (!isTeacherAgeBand(payload.target_age_band_ref, payload.target_age_band_version)) {
      setDetailError("Hãy chọn nhóm tuổi.");
      return;
    }
    if (!payload.title || !payload.topic || !payload.drawing_subject || !payload.drawing_steps_text || !payload.subject_learning_notes || payload.objectives.length === 0 || payload.activities.length === 0 || payload.activities.some((activity) => !activity.title || !activity.objective || !activity.instructions_text)) {
      setDetailError("Điền tiêu đề, chủ đề, nhóm tuổi, mục tiêu, nội dung vẽ và các trường bắt buộc của ít nhất một hoạt động.");
      return;
    }
    if (payload.objectives.length > 12 || payload.objectives.some((objective) => objective.length > 1000)) {
      setDetailError("Số mục tiêu tối đa 12 và mỗi mục tiêu tối đa 1.000 ký tự.");
      return;
    }
    setSaving(true);
    setDetailError(null);
    const createSignature = JSON.stringify(["create-lesson", organizationId, payload]);
    let createKey = mutationKeys.current.get(createSignature);
    if (!detail && !createKey) {
      createKey = createIdempotencyKey();
      mutationKeys.current.set(createSignature, createKey);
    }
    // FEAT-066 C4: the update key belongs to this lesson, revision and payload (retry reuses it).
    const updateSignature = detail
      ? commandSignature("update-lesson", organizationId, detail.lesson_id, detail.revision, payload)
      : null;
    try {
      const result = detail && updateSignature
        ? await backendApi.updateLesson(organizationId, detail, payload, keyForCommand(mutationKeys.current, updateSignature))
        : await backendApi.createLesson(organizationId, payload, createKey);
      setSelectedId(result.lesson_id);
      setDetail(result);
      if (result.current_version.content) setContent(result.current_version.content);
      setItems((current) => [
        { contract: "LessonSummaryV1", lesson_id: result.lesson_id, title: payload.title, topic: payload.topic, current_version_no: result.current_version.version_no, review_state: result.current_version.review_state, visibility: result.visibility, activity_count: payload.activities.length, updated_at: result.updated_at },
        ...current.filter((item) => item.lesson_id !== result.lesson_id),
      ]);
      if (!detail) mutationKeys.current.delete(createSignature);
      if (updateSignature) mutationKeys.current.delete(updateSignature);
      showToast(detail ? "Đã cập nhật giáo án." : "Đã tạo giáo án riêng tư.", "ok");
    } catch (cause) {
      setDetailError(backendMessage(cause));
      setStaleRevision(isStaleRevision(cause));
    } finally {
      setSaving(false);
    }
  };

  const requestPublic = async () => {
    if (!detail) return;
    setSaving(true);
    setDetailError(null);
    const requestSignature = JSON.stringify(["request-public-review", organizationId, detail.lesson_id, detail.current_version.version_id]);
    let requestKey = mutationKeys.current.get(requestSignature);
    if (!requestKey) {
      requestKey = createIdempotencyKey();
      mutationKeys.current.set(requestSignature, requestKey);
    }
    try {
      await backendApi.requestPublicReview(organizationId, detail, requestKey);
      mutationKeys.current.delete(requestSignature);
      const updated = await backendApi.teacherLesson(organizationId, detail.lesson_id);
      setDetail(updated);
      if (updated.current_version.content) setContent(updated.current_version.content);
      showToast("Đã gửi yêu cầu duyệt công khai tới quản lý nhà trường.", "ok");
      setReload((value) => value + 1);
    } catch (cause) {
      setDetailError(backendMessage(cause));
      setStaleRevision(isStaleRevision(cause));
    } finally {
      setSaving(false);
    }
  };

  const activePendingArchive = pendingArchive &&
    detail &&
    selectedId === pendingArchive.detail.lesson_id &&
    detail.lesson_id === pendingArchive.detail.lesson_id &&
    detail.revision === pendingArchive.detail.revision &&
    organizationId === pendingArchive.organizationId
    ? pendingArchive
    : null;

  if (pendingArchive && !activePendingArchive) {
    setPendingArchive(null);
  }

  const requestArchive = () => {
    if (!detail || saving || activePendingArchive) return;
    setPendingArchive({ organizationId, detail });
  };

  const confirmArchive = async () => {
    const target = activePendingArchive;
    if (!target || saving) return;
    setPendingArchive(null);
    setSaving(true);
    setDetailError(null);
    const archiveSignature = commandSignature("archive-lesson", target.organizationId, target.detail.lesson_id, target.detail.revision);
    try {
      await backendApi.archiveLesson(target.organizationId, target.detail, keyForCommand(mutationKeys.current, archiveSignature));
      mutationKeys.current.delete(archiveSignature);
      showToast("Đã lưu trữ giáo án.", "ok");
      hiddenArchivedLessonIds.current.add(target.detail.lesson_id);
      setItems((current) => current.filter((item) => item.lesson_id !== target.detail.lesson_id));
      newLesson();
      setReload((value) => value + 1);
    } catch (cause) {
      setDetailError(backendMessage(cause));
      setStaleRevision(isStaleRevision(cause));
    } finally {
      setSaving(false);
    }
  };

  // FEAT-066 C4 (review C4-IMPL-R1-01): load the current version on request only. The form text is
  // replaced only by this click, so a stale save never overwrites another change (SRS 21.4).
  const reloadCurrentVersion = async () => {
    if (!detail) return;
    setSaving(true);
    try {
      const current = await backendApi.teacherLesson(organizationId, detail.lesson_id);
      setDetail(current);
      setActivityDetailsOverrides({});
      if (current.current_version.content) setContent(current.current_version.content);
      setDetailError(null);
      setStaleRevision(false);
    } catch (cause) {
      setDetailError(backendMessage(cause));
    } finally {
      setSaving(false);
    }
  };

  const detailReviewMeta = detail ? teacherStatusMeta(detail.current_version.review_state, "lesson") : null;
  const detailVisibilityMeta = detail ? teacherStatusMeta(detail.visibility, "visibility") : null;
  const canRequestPublic = Boolean(detail && detail.current_version.review_state !== "PENDING_REVIEW" && detail.visibility !== "PUBLIC");
  const actionHint = !saving && selectedId && !detail
    ? "Đang tải dữ liệu giáo án để bật nút lưu."
    : canRequestPublic
      ? "Giáo án mặc định ở chế độ riêng tư. Gửi duyệt công khai để quản lý nhà trường xem xét."
      : detail?.current_version.review_state === "PENDING_REVIEW"
        ? "Giáo án đang chờ quản lý nhà trường duyệt công khai."
        : undefined;

  return (
    <div className="tw-page">
      <PageHeading
        eyebrow="Giáo viên · Học liệu"
        title="Giáo án"
        description="Soạn thảo giáo án, mục tiêu học tập và các hoạt động thực hành cho lớp học."
        action={
          <div className="teacher-page-actions">
            <button type="button" className="tw-btn is-ghost" onClick={() => navigate("/teacher/t03-document-import-review")}>
              <Icon name="upload" size={16} /> Nhập tài liệu
            </button>
            <button type="button" className="tw-btn is-ghost" onClick={newLesson}>
              <Icon name="plus" size={16} /> Giáo án mới
            </button>
          </div>
        }
      />
      {!hasAuthBridge && <BackendModeNotice roleLabel="Giáo viên" />}
      {pageError && <BackendNotice title="Không tải được danh sách giáo án" tone="error">{pageError}</BackendNotice>}
      <div className="teacher-lesson-layout">
        <section className="tw-card teacher-lesson-list-card">
          <div className="tw-row tw-between">
            <h2 className="tw-h2">Giáo án của tôi</h2>
            <button type="button" className="tw-btn is-ghost is-sm" disabled={loading} onClick={() => setReload((value) => value + 1)}>
              Tải lại
            </button>
          </div>
          {loading && <p className="tw-sub">Đang tải danh sách…</p>}
          {!loading && items.length === 0 && <p className="tw-sub">Chưa có giáo án trong tài khoản.</p>}
          <div style={{ display: "grid", gap: 8 }}>
            {items.map((item) => {
              const reviewMeta = teacherStatusMeta(item.review_state, "lesson");
              const visMeta = teacherStatusMeta(item.visibility, "visibility");
              return (
                <button
                  key={item.lesson_id}
                  type="button"
                  className={`tw-item tw-row tw-between${item.lesson_id === selectedId ? " is-selected" : ""}`}
                  style={{ width: "100%", textAlign: "left" }}
                  onClick={() => {
                    setRemixProvenance(null);
                    setActiveTab("content");
                    setSelectedId(item.lesson_id);
                  }}
                  aria-pressed={selectedId === item.lesson_id}
                >
                  <span style={{ minWidth: 0, display: "grid", gap: 4 }}>
                    <strong style={{ display: "block" }}>{item.title}</strong>
                    <span className="tw-meta">{item.topic} · Phiên bản {item.current_version_no}</span>
                    <span className="tp-chip-row">
                      <StatusBadge tone={reviewMeta.tone} size="sm" dot>{reviewMeta.label}</StatusBadge>
                      <StatusBadge tone={visMeta.tone} size="sm">{visMeta.label}</StatusBadge>
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
          {moreError && <BackendNotice title="Không tải được giáo án tiếp theo" tone="error">{moreError}</BackendNotice>}
          {nextCursor && (
            <button type="button" className="tw-btn is-ghost is-sm" style={{ width: "100%", marginTop: 10 }} disabled={loadingMore} onClick={() => void loadMoreLessons()}>
              {loadingMore ? "Đang tải…" : "Tải thêm giáo án"}
            </button>
          )}
        </section>

        <section className="tw-card cozy-form-card cozy-form-card--wide teacher-lesson-card">
          <div className="tp-form-column">
            <div className="tw-row tw-between tw-wrap koi-teacher-band teacher-lesson-heading">
              <h2 className="tw-h2" style={{ margin: 0 }}>{detail ? "Cập nhật giáo án" : "Tạo giáo án"}</h2>
              {detail && detailReviewMeta && detailVisibilityMeta && (
                <div className="tp-chip-row">
                  <span className="tp-value-chip">Phiên bản {detail.revision}</span>
                  <StatusBadge tone={detailReviewMeta.tone} dot>{detailReviewMeta.label}</StatusBadge>
                  <StatusBadge tone={detailVisibilityMeta.tone}>{detailVisibilityMeta.label}</StatusBadge>
                </div>
              )}
              {(!detail || activeTab === "content") && (
                  <FormActionBar
                    className="teacher-lesson-sticky-bar"
                    hint={actionHint}
                    danger={detail && (
                      <Button type="button" variant="danger" className="tp-quiet-danger" disabled={saving || Boolean(activePendingArchive)} onClick={requestArchive}>
                        Lưu trữ giáo án
                      </Button>
                    )}
                  >
                    {canRequestPublic && (
                      <Button type="button" variant="secondary" disabled={saving} iconLeft={<Icon name="share" size={16} />} onClick={() => void requestPublic()}>
                        Gửi duyệt công khai
                      </Button>
                    )}
                    <Button type="submit" form={`${tabIdBase}-form`} variant="primary" loading={saving} disabled={saving || Boolean(selectedId && !detail)} iconLeft={<Icon name="check" size={16} />}>
                      {saving ? "Đang lưu…" : detail ? "Lưu cập nhật" : "Tạo giáo án"}
                    </Button>
                  </FormActionBar>
              )}
            </div>
            {remixProvenance && detail?.lesson_id === selectedId && (
              <p className="tw-item" role="status">Tạo từ bài công khai “{remixProvenance.title}”.</p>
            )}
            {selectedId && !detail && !detailError && <p className="tw-sub">Đang tải nội dung phiên bản hiện tại…</p>}

            {detail && (
              <Tabs
                items={LESSON_TABS}
                value={activeTab}
                onValueChange={(value) => setActiveTab(value as LessonTab)}
                label="Mục quản lý giáo án"
                idPrefix={tabIdBase}
              />
            )}

            {detailError && (
              <div ref={detailErrorRef}>
                <BackendNotice title="Không thể lưu hoặc tải phiên bản" tone="error">
                  {detailError}
                  {staleRevision && detail && (
                    <>
                      {" "}
                      <Button type="button" variant="secondary" size="sm" disabled={saving} onClick={() => void reloadCurrentVersion()}>
                        Tải lại bản hiện tại (bỏ chỉnh sửa chưa lưu)
                      </Button>
                    </>
                  )}
                </BackendNotice>
              </div>
            )}

            {!selectedId && (
              <details className="tp-collapsible teacher-lesson-search-disclosure" open={searchDisclosureOpen}>
                <summary
                  className="tp-collapsible-summary"
                  onClick={(event) => {
                    event.preventDefault();
                    setSearchDisclosureOpen((open) => !open);
                  }}
                >
                  <span className="tp-collapsible-title">
                    <Icon name="search" size={16} />
                    <span>Sao chép từ bài học công khai</span>
                  </span>
                  <Icon name="chevron-down" size={16} />
                </summary>
                <div className="tp-collapsible-body">
                  <PublicLessonSearchPanel organizationId={organizationId} onRemixed={openRemixedLesson} />
                </div>
              </details>
            )}

            <div
              role={detail ? "tabpanel" : undefined}
              id={detail ? `${tabIdBase}-panel-content` : undefined}
              aria-labelledby={detail ? `${tabIdBase}-tab-content` : undefined}
              hidden={Boolean(detail) && activeTab !== "content"}
              className="teacher-lesson-tabpanel"
            >
              <form id={`${tabIdBase}-form`} className="teacher-lesson-form" onSubmit={(event) => void save(event)}>
                <div className="tp-form-column">
                  <section className="cozy-form-section" aria-labelledby="lesson-sec-general">
                    <div className="tp-form-section-intro">
                      <h3 id="lesson-sec-general"><span className="teacher-lesson-section-number">1.</span> Thông tin chung</h3>
                      <p>Tên giáo án, chủ đề, nhóm tuổi và đối tượng trẻ sẽ vẽ.</p>
                    </div>
                    <div className="cozy-form-grid">
                      <FormField className="cozy-span-3" label="Tiêu đề" htmlFor="lesson-title" required>
                        <input id="lesson-title" className="cozy-input" maxLength={160} required value={content.title} onChange={(event) => updateContent({ title: event.target.value })} />
                      </FormField>
                      <FormField className="cozy-span-3" label="Chủ đề" htmlFor="lesson-topic" required>
                        <input id="lesson-topic" className="cozy-input" maxLength={120} required value={content.topic} onChange={(event) => updateContent({ topic: event.target.value })} />
                      </FormField>
                      <FormField className="cozy-span-3" label="Nhóm tuổi" htmlFor="lesson-age-band" required>
                        <Select
                          id="lesson-age-band"
                          value={isTeacherAgeBand(content.target_age_band_ref, content.target_age_band_version) ? content.target_age_band_ref : ""}
                          required
                          aria-describedby={detail && !isTeacherAgeBand(content.target_age_band_ref, content.target_age_band_version) ? "lesson-age-band-hint" : undefined}
                          onChange={(event) => {
                            const band = TEACHER_AGE_BANDS.find((item) => item.ref === event.target.value);
                            if (band) updateContent({ target_age_band_ref: band.ref, target_age_band_version: band.version });
                          }}
                        >
                          <option value="" disabled>Chọn nhóm tuổi</option>
                          {TEACHER_AGE_BANDS.map((band) => <option key={band.ref} value={band.ref}>{band.label}</option>)}
                        </Select>
                      </FormField>
                      {detail && !isTeacherAgeBand(content.target_age_band_ref, content.target_age_band_version) && (
                        <p id="lesson-age-band-hint" className="cozy-form-hint cozy-span-6">Nhóm tuổi cũ không còn được dùng, hãy chọn lại.</p>
                      )}
                      <FormField className="cozy-span-2" label="Đối tượng cần vẽ" htmlFor="lesson-drawing-subject" required>
                        <input id="lesson-drawing-subject" className="cozy-input" maxLength={160} required value={content.drawing_subject} onChange={(event) => updateContent({ drawing_subject: event.target.value })} />
                      </FormField>
                    </div>
                  </section>

                  <section className="cozy-form-section" aria-labelledby="lesson-sec-objectives">
                    <div className="tp-form-section-intro">
                      <h3 id="lesson-sec-objectives"><span className="teacher-lesson-section-number">2.</span> Mục tiêu và hướng dẫn vẽ</h3>
                      <p>Mục tiêu học tập và các bước hướng dẫn trẻ thực hiện nét vẽ.</p>
                    </div>
                    <div className="cozy-form-grid">
                      <FormField className="cozy-span-3" label="Mục tiêu học tập" htmlFor="lesson-objectives" required help="Mỗi dòng một mục tiêu. Tối đa 12 mục, mỗi mục tối đa 1.000 ký tự.">
                        <textarea id="lesson-objectives" className="cozy-textarea" rows={3} maxLength={12000} value={content.objectives.join("\n")} onChange={(event) => updateContent({ objectives: event.target.value.split("\n") })} />
                      </FormField>
                      <FormField className="cozy-span-3" label="Các bước hướng dẫn vẽ" htmlFor="lesson-drawing-steps" required>
                        <textarea id="lesson-drawing-steps" className="cozy-textarea" rows={3} maxLength={4000} required value={content.drawing_steps_text} onChange={(event) => updateContent({ drawing_steps_text: event.target.value })} />
                      </FormField>
                    </div>
                  </section>

                  <section className="cozy-form-section" aria-labelledby="lesson-sec-script">
                    <div className="tp-form-section-intro">
                      <h3 id="lesson-sec-script"><span className="teacher-lesson-section-number">3.</span> Kịch bản</h3>
                      <p>Ghi chú kiến thức cho giáo viên và định hướng lời kể khi tạo câu chuyện.</p>
                    </div>
                    <div className="cozy-form-grid">
                      <FormField className="cozy-span-3" label="Ghi chú kiến thức" htmlFor="lesson-learning-notes" required>
                        <textarea id="lesson-learning-notes" className="cozy-textarea" rows={3} maxLength={5000} required value={content.subject_learning_notes} onChange={(event) => updateContent({ subject_learning_notes: event.target.value })} />
                      </FormField>
                      <FormField className="cozy-span-3" label="Định hướng kịch bản" htmlFor="lesson-script-direction" labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}>
                        <textarea id="lesson-script-direction" className="cozy-textarea" rows={3} maxLength={2000} value={content.script_direction ?? ""} onChange={(event) => updateContent({ script_direction: event.target.value || null })} />
                      </FormField>
                      <label className="cozy-form-checkbox-card cozy-span-6">
                        <input type="checkbox" checked={content.script_following_allowed} onChange={(event) => updateContent({ script_following_allowed: event.target.checked })} />
                        <span>Cho phép bám theo định hướng kịch bản</span>
                      </label>
                    </div>
                  </section>

                  <section className="cozy-form-section" aria-labelledby="lesson-sec-activities">
                    <div className="cozy-form-section-head">
                      <div className="tp-form-section-intro" style={{ borderBottom: 0, paddingBottom: 0 }}>
                        <h3 id="lesson-sec-activities"><span className="teacher-lesson-section-number">4.</span> Hoạt động thực hành</h3>
                        <p>Các hoạt động gợi mở, chuẩn bị vật liệu và lưu ý an toàn cho trẻ.</p>
                      </div>
                      <Button type="button" variant="secondary" size="sm" disabled={content.activities.length >= 24} iconLeft={<Icon name="plus" size={15} />} onClick={() => updateContent({ activities: [...content.activities, blankActivity()] })}>
                        Thêm hoạt động
                      </Button>
                    </div>
                    <div className="teacher-lesson-activities">
                      {content.activities.map((activity, index) => {
                        const isDetailsOpen = activityDetailsOverrides[index] ?? activityHasDetails(activity);
                        return (
                          <section key={index} className="cozy-form-section cozy-form-grid teacher-lesson-activity-item">
                            <div className="cozy-form-section-head cozy-span-6">
                              <h4>Hoạt động {index + 1}</h4>
                              {content.activities.length > 1 && (
                                <Button
                                  type="button"
                                  variant="danger"
                                  size="sm"
                                  className="tp-quiet-danger"
                                  onClick={() => {
                                    setActivityDetailsOverrides((current) => {
                                      const next: Record<number, boolean> = {};
                                      Object.entries(current).forEach(([key, value]) => {
                                        const idx = Number(key);
                                        if (idx < index) next[idx] = value;
                                        else if (idx > index) next[idx - 1] = value;
                                      });
                                      return next;
                                    });
                                    updateContent({ activities: content.activities.filter((_, i) => i !== index) });
                                  }}
                                >
                                  Xóa hoạt động này
                                </Button>
                              )}
                            </div>
                            <FormField className="cozy-span-4" label="Tên hoạt động" htmlFor={`lesson-activity-title-${index}`} required>
                              <input id={`lesson-activity-title-${index}`} className="cozy-input" maxLength={160} required value={activity.title} onChange={(event) => updateActivity(index, { title: event.target.value })} />
                            </FormField>
                            <FormField className="cozy-span-2" label="Loại hoạt động" htmlFor={`lesson-activity-kind-${index}`} required>
                              <Select id={`lesson-activity-kind-${index}`} aria-label="Loại hoạt động" value={activity.activity_kind} onChange={(event) => updateActivity(index, { activity_kind: event.target.value as LessonActivity["activity_kind"] })}>
                                <option value="outdoor">Ngoài trời</option><option value="indoor">Trong lớp</option><option value="mixed">Kết hợp</option>
                              </Select>
                            </FormField>
                            <FormField className="cozy-span-3" label="Mục tiêu" htmlFor={`lesson-activity-objective-${index}`} required>
                              <textarea id={`lesson-activity-objective-${index}`} className="cozy-textarea" rows={3} maxLength={1000} required value={activity.objective} onChange={(event) => updateActivity(index, { objective: event.target.value })} />
                            </FormField>
                            <FormField className="cozy-span-3" label="Hướng dẫn" htmlFor={`lesson-activity-instructions-${index}`} required>
                              <textarea id={`lesson-activity-instructions-${index}`} className="cozy-textarea" rows={3} maxLength={5000} required value={activity.instructions_text} onChange={(event) => updateActivity(index, { instructions_text: event.target.value })} />
                            </FormField>
                            <FormField className="cozy-span-6" label="An toàn" htmlFor={`lesson-activity-safety-${index}`} labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}>
                              <textarea id={`lesson-activity-safety-${index}`} className="cozy-textarea" rows={3} maxLength={3000} value={activity.safety_notes} onChange={(event) => updateActivity(index, { safety_notes: event.target.value })} />
                            </FormField>
                            <details className="teacher-activity-details cozy-span-6" open={isDetailsOpen}>
                              <summary
                                className="teacher-activity-details-summary"
                                onClick={(event) => {
                                  event.preventDefault();
                                  setActivityDetailsOverrides((current) => ({ ...current, [index]: !isDetailsOpen }));
                                }}
                              >
                                <span>Thêm chi tiết</span>
                                <Icon name="chevron-down" size={15} />
                              </summary>
                              <div className="cozy-form-grid teacher-activity-details-body">
                                <FormField className="cozy-span-3" label="Vật liệu" htmlFor={`lesson-activity-materials-${index}`} labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}>
                                  <textarea id={`lesson-activity-materials-${index}`} className="cozy-textarea" rows={3} maxLength={2000} value={activity.materials_text} onChange={(event) => updateActivity(index, { materials_text: event.target.value })} />
                                </FormField>
                                <FormField className="cozy-span-3" label="Chuẩn bị" htmlFor={`lesson-activity-prep-${index}`} labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}>
                                  <textarea id={`lesson-activity-prep-${index}`} className="cozy-textarea" rows={3} maxLength={2000} value={activity.preparation_text} onChange={(event) => updateActivity(index, { preparation_text: event.target.value })} />
                                </FormField>
                                <FormField className="cozy-span-6" label="Lưu ý quan sát" htmlFor={`lesson-activity-observation-${index}`} labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}>
                                  <textarea id={`lesson-activity-observation-${index}`} className="cozy-textarea" rows={3} maxLength={3000} value={activity.observation_notes} onChange={(event) => updateActivity(index, { observation_notes: event.target.value })} />
                                </FormField>
                              </div>
                            </details>
                          </section>
                        );
                      })}
                    </div>
                  </section>


                </div>
              </form>
            </div>

            {detail && (
              <div
                role="tabpanel"
                id={`${tabIdBase}-panel-share`}
                aria-labelledby={`${tabIdBase}-tab-share`}
                hidden={activeTab !== "share"}
                className="teacher-lesson-tabpanel"
              >
                <TeacherPrivateSharePanel key={detail.lesson_id} organizationId={organizationId} lesson={detail} />
              </div>
            )}

            {detail && (
              <div
                role="tabpanel"
                id={`${tabIdBase}-panel-versions`}
                aria-labelledby={`${tabIdBase}-tab-versions`}
                hidden={activeTab !== "versions"}
                className="teacher-lesson-tabpanel"
              >
                <LessonVersionsPanel key={detail.lesson_id} organizationId={organizationId} lessonId={detail.lesson_id} refreshToken={detail.revision} />
              </div>
            )}
          </div>
        </section>
      </div>
      <ConfirmDialog
        open={Boolean(activePendingArchive)}
        onOpenChange={(open) => {
          if (!open) setPendingArchive(null);
        }}
        title={activePendingArchive ? `Lưu trữ giáo án “${activePendingArchive.detail.current_version.content?.title ?? "đang chọn"}”?` : ""}
        description="Giáo án sẽ được gỡ khỏi danh sách giáo án."
        confirmLabel="Lưu trữ giáo án"
        tone="danger"
        onConfirm={() => { void confirmArchive(); }}
      />
    </div>
  );
}
