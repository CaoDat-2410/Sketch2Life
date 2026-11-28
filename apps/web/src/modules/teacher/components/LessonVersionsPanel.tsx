import { useEffect, useState } from "react";
import {
  getLessonVersion,
  listLessonVersions,
  type LessonVersionDetail,
  type LessonVersionSummary,
} from "../../../shared/api/teacherLessonLibraryApi";
import { StatusBadge, formatDateTimeDdMmYyyy } from "../../../shared/ui";
import { teacherAgeBandLabel } from "../services/ageBands";
import { teacherStatusMeta } from "../services/teacherStatus";

function message(cause: unknown) {
  return cause instanceof Error ? cause.message : "Không thể tải phiên bản bài học.";
}

function activityKindLabel(kind: string): string {
  if (kind === "outdoor") return "Ngoài trời";
  if (kind === "indoor") return "Trong lớp";
  if (kind === "mixed") return "Kết hợp";
  return kind;
}

export function LessonVersionsPanel({ organizationId, lessonId, refreshToken = 0 }: { organizationId: string; lessonId: string; refreshToken?: number }) {
  const [items, setItems] = useState<LessonVersionSummary[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [version, setVersion] = useState<LessonVersionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadingVersion, setLoadingVersion] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    listLessonVersions(organizationId, lessonId, { signal: controller.signal })
      .then((page) => {
        setError("");
        setItems(page.items);
        setNextCursor(page.next_cursor);
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(message(cause));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [organizationId, lessonId, refreshToken]);

  useEffect(() => {
    if (!selectedVersionId) {
      return;
    }
    const controller = new AbortController();
    getLessonVersion(organizationId, lessonId, selectedVersionId, controller.signal)
      .then(setVersion)
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(message(cause));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingVersion(false);
      });
    return () => controller.abort();
  }, [organizationId, lessonId, selectedVersionId]);

  const loadMore = async () => {
    if (!nextCursor || loadingMore) return;
    const controller = new AbortController();
    setLoadingMore(true);
    setError("");
    try {
      const page = await listLessonVersions(organizationId, lessonId, { cursor: nextCursor, signal: controller.signal });
      setItems((current) => [...current, ...page.items]);
      setNextCursor(page.next_cursor);
    } catch (cause) {
      setError(message(cause));
    } finally {
      setLoadingMore(false);
    }
  };

  return (
    <section className="tw-card cozy-form-card cozy-form-card--wide cozy-form-stack" aria-labelledby="lesson-versions-heading">
      <div className="tp-form-column">
        <div className="tw-row tw-between tw-wrap">
          <h2 className="tw-h2" id="lesson-versions-heading">Lịch sử phiên bản</h2>
          <span className="tp-value-chip">Mới nhất trước</span>
        </div>
        {error && <p role="alert" className="tw-error">{error}</p>}
        {loading ? <p className="tw-sub" role="status">Đang tải phiên bản…</p> : items.length === 0 ? <p className="tw-sub">Chưa có phiên bản.</p> : (
          <div style={{ display: "grid", gap: 8 }}>
            {items.map((item) => {
              const meta = teacherStatusMeta(item.review_state, "lesson");
              return (
                <button
                  key={item.version_id}
                  type="button"
                  className={`tw-item tw-row tw-between${selectedVersionId === item.version_id ? " is-selected" : ""}`}
                  style={{ width: "100%", textAlign: "left" }}
                  aria-pressed={selectedVersionId === item.version_id}
                  onClick={() => {
                    if (selectedVersionId === item.version_id) return;
                    setSelectedVersionId(item.version_id);
                    setVersion(null);
                    setError("");
                    setLoadingVersion(true);
                  }}
                >
                  <span>
                    <strong>Phiên bản {item.version_no}</strong>
                    {" · "}
                    <span className="tw-meta">{formatDateTimeDdMmYyyy(item.created_at, "Không rõ ngày")}</span>
                  </span>
                  <StatusBadge tone={meta.tone} size="sm" dot>{meta.label}</StatusBadge>
                </button>
              );
            })}
          </div>
        )}
        {nextCursor && <button type="button" className="tw-btn is-ghost is-sm" disabled={loadingMore} onClick={() => void loadMore()}>{loadingMore ? "Đang tải…" : "Tải thêm phiên bản"}</button>}
        {loadingVersion && <p className="tw-sub" role="status">Đang tải nội dung phiên bản…</p>}
        {version && <VersionContent version={version} />}
      </div>
    </section>
  );
}

function VersionContent({ version }: { version: LessonVersionDetail }) {
  const content = version.content;
  const meta = teacherStatusMeta(version.review_state, "lesson");
  return (
    <article className="tw-item" aria-label={`Nội dung phiên bản ${version.version_no}`}>
      <div className="tw-row tw-between tw-wrap">
        <h3 className="tw-h2" style={{ margin: 0 }}>{content.title}</h3>
        <div className="tp-chip-row">
          <StatusBadge tone={meta.tone} size="sm" dot>{meta.label}</StatusBadge>
          <span className="tp-value-chip">Chỉ đọc · Phiên bản {version.version_no}</span>
        </div>
      </div>
      <p className="tw-meta">{content.topic} · {formatDateTimeDdMmYyyy(version.created_at, "Không rõ ngày")}</p>
      <p><strong>Nhóm tuổi:</strong> {teacherAgeBandLabel(content.target_age_band_ref)}</p>
      <p><strong>Mục tiêu:</strong></p>
      <ul>{content.objectives.map((objective, index) => <li key={`${index}-${objective}`}>{objective}</li>)}</ul>
      <p><strong>Đối tượng vẽ:</strong> {content.drawing_subject}</p>
      <p><strong>Các bước vẽ:</strong> {content.drawing_steps_text}</p>
      <p><strong>Ghi chú kiến thức:</strong> {content.subject_learning_notes}</p>
      <p><strong>Định hướng kịch bản:</strong> {content.script_direction || "Không có"} · {content.script_following_allowed ? "được phép bám theo" : "không bám theo"}</p>
      <h4>Hoạt động theo thứ tự</h4>
      {content.activities.map((activity, index) => (
        <section key={`${index}-${activity.title}`}>
          <h5>{index + 1}. {activity.title}</h5>
          <p><strong>Loại:</strong> {activityKindLabel(activity.activity_kind)} · <strong>Mục tiêu:</strong> {activity.objective}</p>
          <p><strong>Hướng dẫn:</strong> {activity.instructions_text}</p>
          <p><strong>Vật liệu:</strong> {activity.materials_text || "Không có"}</p>
          <p><strong>Chuẩn bị:</strong> {activity.preparation_text || "Không có"}</p>
          <p><strong>Lưu ý quan sát:</strong> {activity.observation_notes || "Không có"}</p>
          <p><strong>An toàn:</strong> {activity.safety_notes || "Không có"}</p>
        </section>
      ))}
    </article>
  );
}
