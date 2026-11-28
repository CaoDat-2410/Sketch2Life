import { useRef, useState, type FormEvent } from "react";
import { createIdempotencyKey } from "../../../shared/api/backendApi";
import {
  remixLesson,
  searchPublicLessons,
  type PublicLessonHit,
  type PublicLessonSearchInput,
  type RemixLessonResult,
} from "../../../shared/api/teacherLessonLibraryApi";
import { Button, FormField, formatDateDdMmYyyy, Select } from "../../../shared/ui";
import { FormActionBar } from "./FormActionBar";
import { TEACHER_AGE_BANDS, teacherAgeBandLabel } from "../services/ageBands";

type SearchFilters = Pick<PublicLessonSearchInput, "q" | "topic" | "targetAgeBandRef" | "targetAgeBandVersion">;

function message(cause: unknown) {
  return cause instanceof Error ? cause.message : "Không thể tìm bài học công khai.";
}

function formatDate(value: string) {
  return formatDateDdMmYyyy(value, "Không rõ ngày cập nhật");
}

function hitSignature(hit: PublicLessonHit) {
  return JSON.stringify([hit.lesson_id, hit.version_id, hit.structured_content_hash]);
}

function errorCode(cause: unknown) {
  return cause && typeof cause === "object" && "code" in cause ? String(cause.code) : "";
}

function retryable(cause: unknown) {
  return cause && typeof cause === "object" && "retryable" in cause && cause.retryable === true;
}

export function PublicLessonSearchPanel({
  organizationId,
  onRemixed,
}: {
  organizationId: string;
  onRemixed: (result: RemixLessonResult, hit: PublicLessonHit) => void;
}) {
  const [q, setQ] = useState("");
  const [topic, setTopic] = useState("");
  const [ageBandRef, setAgeBandRef] = useState("");
  const [filters, setFilters] = useState<SearchFilters | null>(null);
  const [items, setItems] = useState<PublicLessonHit[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [busySignature, setBusySignature] = useState<string | null>(null);
  const [retrySignatures, setRetrySignatures] = useState<Set<string>>(() => new Set());
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [provenance, setProvenance] = useState("");
  const requestSequence = useRef(0);
  const retryKeys = useRef(new Map<string, string>());

  const resetForFilterChange = () => {
    requestSequence.current += 1;
    setFilters(null);
    setItems([]);
    setNextCursor(null);
    setError("");
    setNotice("");
    setProvenance("");
    retryKeys.current.clear();
    setRetrySignatures(new Set());
  };

  const search = async (event: FormEvent) => {
    event.preventDefault();
    const selected: SearchFilters = {
      q: q.trim() || undefined,
      topic: topic.trim() || undefined,
      targetAgeBandRef: ageBandRef || undefined,
      targetAgeBandVersion: ageBandRef ? 1 : undefined,
    };
    if (!selected.q && !selected.topic && !selected.targetAgeBandRef) {
      setError("Nhập từ khóa, chủ đề hoặc chọn nhóm tuổi để tìm kiếm.");
      setItems([]);
      setNextCursor(null);
      setFilters(null);
      return;
    }
    const sequence = ++requestSequence.current;
    setFilters(selected);
    setItems([]);
    setNextCursor(null);
    setError("");
    setNotice("");
    setProvenance("");
    setLoading(true);
    try {
      const page = await searchPublicLessons(organizationId, selected);
      if (requestSequence.current === sequence) {
        setItems(page.items);
        setNextCursor(page.next_cursor);
      }
    } catch (cause) {
      if (requestSequence.current === sequence) setError(message(cause));
    } finally {
      if (requestSequence.current === sequence) setLoading(false);
    }
  };

  const loadMore = async () => {
    if (!filters || !nextCursor || loadingMore) return;
    const sequence = requestSequence.current;
    setLoadingMore(true);
    setError("");
    try {
      const page = await searchPublicLessons(organizationId, { ...filters, cursor: nextCursor });
      if (requestSequence.current === sequence) {
        setItems((current) => {
          const byVersion = new Map(current.map((item) => [hitSignature(item), item] as const));
          page.items.forEach((item) => byVersion.set(hitSignature(item), item));
          return Array.from(byVersion.values());
        });
        setNextCursor(page.next_cursor);
      }
    } catch (cause) {
      if (requestSequence.current === sequence) setError(message(cause));
    } finally {
      if (requestSequence.current === sequence) setLoadingMore(false);
    }
  };

  const copyLesson = async (hit: PublicLessonHit) => {
    const signature = hitSignature(hit);
    const key = retryKeys.current.get(signature) ?? createIdempotencyKey();
    retryKeys.current.set(signature, key);
    setBusySignature(signature);
    setError("");
    setNotice("");
    try {
      const result = await remixLesson(organizationId, hit.lesson_id, {
        sourceVersionId: hit.version_id,
        sourceContentSha256: hit.structured_content_hash,
      }, key);
      retryKeys.current.delete(signature);
      setRetrySignatures((current) => {
        const updated = new Set(current);
        updated.delete(signature);
        return updated;
      });
      setProvenance(`Tạo từ bài công khai “${hit.title}”.`);
      setNotice("Đã tạo bản riêng tư ở trạng thái bản nháp. Đang mở trong trình soạn thảo.");
      onRemixed(result, hit);
    } catch (cause) {
      setError(message(cause));
      if (errorCode(cause) === "STALE_SOURCE_VERSION") {
        retryKeys.current.delete(signature);
        setRetrySignatures((current) => {
          const updated = new Set(current);
          updated.delete(signature);
          return updated;
        });
        if (filters) {
          setLoading(true);
          try {
            const page = await searchPublicLessons(organizationId, filters);
            setItems(page.items);
            setNextCursor(page.next_cursor);
            setNotice("Kết quả đã được làm mới. Hãy chọn bản mới để sao chép lại.");
          } catch (refreshCause) {
            setNotice(message(refreshCause));
          } finally {
            setLoading(false);
          }
        }
      } else if (retryable(cause) || (cause && typeof cause === "object" && "status" in cause && cause.status === 0)) {
        setRetrySignatures((current) => new Set(current).add(signature));
      } else {
        retryKeys.current.delete(signature);
        setRetrySignatures((current) => {
          const updated = new Set(current);
          updated.delete(signature);
          return updated;
        });
      }
    } finally {
      setBusySignature(null);
    }
  };

  const change = (setter: (value: string) => void) => (value: string) => {
    setter(value);
    resetForFilterChange();
  };

  return (
    <section className="cozy-form-stack" aria-labelledby="public-lesson-search-heading">
      <div className="tp-form-column">
        <div className="tw-row tw-between tw-wrap">
          <div>
            <h2 className="tw-h2" id="public-lesson-search-heading">Tìm bài học để sao chép</h2>
          </div>
          <span className="tp-value-chip">Chỉ hiện thông tin giới thiệu</span>
        </div>
        <form onSubmit={(event) => void search(event)} className="cozy-form-stack">
          <div className="cozy-form-grid">
            <FormField className="cozy-span-3" label="Từ khóa" htmlFor="public-search-q" labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}>
              <input id="public-search-q" className="cozy-input" value={q} maxLength={100} disabled={busySignature !== null} onChange={(event) => change(setQ)(event.target.value)} />
            </FormField>
            <FormField className="cozy-span-3" label="Chủ đề" htmlFor="public-search-topic" labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}>
              <input id="public-search-topic" className="cozy-input" value={topic} maxLength={120} disabled={busySignature !== null} onChange={(event) => change(setTopic)(event.target.value)} />
            </FormField>
            <FormField className="cozy-span-3" label="Nhóm tuổi" htmlFor="public-search-age-band" labelAction={<span className="cozy-form-optional">(không bắt buộc)</span>}>
              <Select id="public-search-age-band" value={ageBandRef} disabled={busySignature !== null} onChange={(event) => change(setAgeBandRef)(event.target.value)}>
                <option value="">Tất cả</option>
                {TEACHER_AGE_BANDS.map((band) => <option key={band.ref} value={band.ref}>{band.label}</option>)}
              </Select>
            </FormField>
          </div>
          <FormActionBar hint="Nhập ít nhất một tiêu chí để tìm kiếm.">
            <Button variant="ghost" type="submit" disabled={loading || busySignature !== null} loading={loading}>
              {loading ? "Đang tìm…" : "Tìm kiếm"}
            </Button>
          </FormActionBar>
        </form>
        {error && <p role="alert" className="tw-error">{error}</p>}
        {notice && <p role="status" className="tw-sub">{notice}</p>}
        {provenance && <p role="status" className="tw-item"><strong>{provenance}</strong></p>}
        {loading && <p className="tw-sub" role="status">Đang tải kết quả…</p>}
        {!loading && filters && items.length === 0 && <p className="tw-sub">Không có bài học công khai phù hợp.</p>}
        <div style={{ display: "grid", gap: 8 }}>
          {items.map((hit) => {
            const signature = hitSignature(hit);
            return (
              <article className="tw-item" key={signature}>
                <div className="tw-row tw-between tw-wrap">
                  <div>
                    <h3 className="tw-h2" style={{ margin: 0 }}>{hit.title}</h3>
                    <p className="tw-meta">{hit.topic}</p>
                  </div>
                  <span className="tp-value-chip">{hit.activity_count} hoạt động</span>
                </div>
                <p className="tw-sub">Nhóm tuổi: {teacherAgeBandLabel(hit.target_age_band_ref)} · Cập nhật {formatDate(hit.updated_at)}</p>
                <button type="button" className="tw-btn is-ghost is-sm" disabled={busySignature !== null} onClick={() => void copyLesson(hit)}>
                  {busySignature === signature ? "Đang sao chép…" : retrySignatures.has(signature) ? "Thử lại cùng yêu cầu" : "Sao chép thành bản của tôi"}
                </button>
              </article>
            );
          })}
        </div>
        {nextCursor && <button type="button" className="tw-btn is-ghost is-sm" disabled={loadingMore || busySignature !== null} onClick={() => void loadMore()}>{loadingMore ? "Đang tải…" : "Tải thêm kết quả"}</button>}
      </div>
    </section>
  );
}
