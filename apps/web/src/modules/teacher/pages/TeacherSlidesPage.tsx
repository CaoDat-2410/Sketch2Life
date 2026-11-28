import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowDown, ArrowUp, Image as ImageIcon, Plus, RefreshCw, Trash2, Upload } from "lucide-react";
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { Alert, Button, EmptyState, FormField, StatusBadge, formatDateDdMmYyyy } from "../../../shared/ui";
import { FormActionBar } from "../components/FormActionBar";
import { SlidePresenter } from "../components/SlidePresenter";
import { teacherStatusMeta } from "../services/teacherStatus";
import { dismissSvgDraftRequest, expireSvgDraftCooldown, startSvgDraftRequest, useSvgDraftCooldownUntil, useSvgDraftRequest } from "../services/svgDraftRequests";
import { clearAiTaskStatusIfCurrent, scheduleAiTaskStatusSeen, svgTaskStatusKey, useAiTaskMark, type AiTaskKey } from "../services/aiTaskStatus";
import { BackendApiError, configuredOrganizationId, createIdempotencyKey } from "../../../shared/api/backendApi";
import { teacherOccurrenceApi, type Occurrence, type PlanRevision } from "../../../shared/api/teacherOccurrenceApi";
import { teacherSvgCatalogApi, type SvgDocumentV1 } from "../../../shared/api/teacherSvgCatalogApi";
import {
  teacherPresentationApi,
  type LessonPresentation,
  type PresentationMedia,
  type PresentationOperation,
  type PresentationRevision,
  type PresentationSvgDraft,
} from "../../../shared/api/teacherPresentationApi";

type SlideMediaPayload = Extract<PresentationOperation, { op: "SET_MEDIA" }>["media"];
type SlideMediaInput = { media: SlideMediaPayload; placement: "FULL" | "LEFT" | "RIGHT" };
type PlacementChoice = {
  slideId: string;
  value: SlideMediaInput["placement"];
  sourcePlacement: SlideMediaInput["placement"];
  sourcePresentation: LessonPresentation | null;
};
type PreviewMode = "head" | "ready";
const NEUTRAL_NOT_FOUND = "Không tìm thấy dữ liệu hoặc bạn không có quyền truy cập.";
const subjectPattern = /^[\p{L}\p{N} -]{1,80}$/u;
const occurrenceStateLabel: Record<Occurrence["state"], string> = {
  DRAFT: "Bản nháp", DOCUMENT_REVIEW: "Đang rà tài liệu", PLAN_REVIEW: "Đang rà kế hoạch", APPROVED: "Đã duyệt",
  SAMPLE_AVAILABLE: "Có video mẫu", SAMPLE_USED: "Đã dùng video mẫu", ARCHIVED: "Đã lưu trữ",
};
const staleReasonLabel = (reason: string) => reason === "PLAN_REVISION_CHANGED" ? "Kế hoạch đã đổi" : "Hình ảnh nguồn đã đổi";

function mediaKindLabel(kind: PresentationMedia["kind"]): string {
  if (kind === "IMAGE") return "Ảnh tải lên";
  if (kind === "SVG_CATALOG") return "Danh mục SVG";
  if (kind === "SVG_AI") return "SVG gợi ý AI";
  return "Video nhúng";
}

function safePresentationError(cause: unknown): string {
  if (cause instanceof BackendApiError) {
    if (cause.code === "SVG_CATALOG_NOT_APPROVED") return "SVG trong danh mục chưa được duyệt để lưu hoặc trình chiếu.";
    if (cause.code === "SVG_CATALOG_REJECTED") return "SVG trong danh mục đã bị từ chối duyệt.";
    if (cause.code === "SVG_CATALOG_NOT_AVAILABLE") return "SVG không tồn tại hoặc không hiển thị trong tổ chức này.";
    if (cause.code === "SVG_CATALOG_HASH_MISMATCH") return "Phiên bản SVG trong danh mục đã thay đổi. Hãy gỡ rồi chọn lại hình.";
    if (cause.status === 404 || cause.status === 403) return NEUTRAL_NOT_FOUND;
    if (cause.code === "STALE_REVISION") return "Bản trình bày đã thay đổi. Đang tải lại phiên bản mới nhất.";
    if (cause.code === "STALE_SOURCE_VERSION") return "Kế hoạch hoặc hình ảnh nguồn đã thay đổi. Hãy ghim lại kế hoạch hiện tại trong bản nháp mới.";
    if (cause.code === "LESSON_PLAN_NOT_APPROVED") return "Buổi dạy cần có kế hoạch đã duyệt trước khi tạo trình bày.";
    if (cause.code === "PROVIDER_UNAVAILABLE") return "Tạo SVG hiện chưa khả dụng.";
    if (cause.code === "STORAGE_UNAVAILABLE") return "Lưu trữ ảnh hiện chưa sẵn sàng. Hãy thử lại sau.";
    if (cause.code === "RATE_LIMITED" || cause.status === 429) return "Đã đạt giới hạn tạo SVG. Hãy thử lại sau thời gian chờ.";
    if (cause.code === "INVALID_STATE_TRANSITION") return "Buổi dạy hoặc lớp hiện chỉ cho phép đọc.";
    if (cause.code === "RESOURCE_CONFLICT") return "Trình bày đã được tạo ở một yêu cầu khác. Hãy tải lại.";
    if (cause.code === "INVALID_REQUEST") return "Thông tin chưa hợp lệ. Hãy kiểm tra rồi thử lại.";
    if (cause.status === 409) return "Thao tác hiện chưa thể hoàn tất. Hãy tải lại rồi thử lại.";
    if (cause.status === 413) return "Ảnh vượt quá giới hạn cho phép.";
    if (cause.status === 415) return "Định dạng ảnh chưa được hỗ trợ.";
    if (cause.status === 422) return "Ảnh tải lên chưa qua kiểm tra. Hãy chọn ảnh khác.";
    if (cause.status === 503 || cause.status === 0) return "Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.";
  }
  return "Chưa thể hoàn tất yêu cầu. Hãy thử lại sau.";
}

function buildOperations(original: PresentationRevision["slides"], edited: PresentationRevision["slides"], mediaEdits: Record<string, SlideMediaInput | null>): PresentationOperation[] {
  const originalIds = new Set(original.map((slide) => slide.slide_id));
  const editedIds = new Set(edited.map((slide) => slide.slide_id));
  const operations: PresentationOperation[] = [];
  const sequence = original.map((slide) => slide.slide_id);
  const survivingExisting = edited.filter((slide) => originalIds.has(slide.slide_id));
  if (original.length > 0 && edited.length > 0 && survivingExisting.length === 0) {
    const keepCount = Math.min(original.length, Math.max(1, 100 - edited.length));
    const keptIds = new Set(original.slice(0, keepCount).map((slide) => slide.slide_id));
    for (const slide of original) {
      if (!keptIds.has(slide.slide_id)) operations.push({ op: "DELETE_SLIDE", slide_id: slide.slide_id });
    }
    for (let index = edited.length - 1; index >= 0; index -= 1) {
      const slide = edited[index];
      operations.push({ op: "ADD_SLIDE", after_slide_id: null, title: slide.title, body_text: slide.body_text });
    }
    for (const slide of original) {
      if (keptIds.has(slide.slide_id)) operations.push({ op: "DELETE_SLIDE", slide_id: slide.slide_id });
    }
    return operations;
  }
  for (const slide of original) {
    if (!editedIds.has(slide.slide_id)) {
      operations.push({ op: "DELETE_SLIDE", slide_id: slide.slide_id });
      sequence.splice(sequence.indexOf(slide.slide_id), 1);
    }
  }
  const orderedExisting = edited.map((slide) => slide.slide_id).filter((slideId) => originalIds.has(slideId));
  for (let index = 0; index < orderedExisting.length; index += 1) {
    const slideId = orderedExisting[index];
    const currentIndex = sequence.indexOf(slideId);
    if (currentIndex !== index) {
      operations.push({ op: "MOVE_SLIDE", slide_id: slideId, to_position: index + 1 });
      sequence.splice(currentIndex, 1);
      sequence.splice(index, 0, slideId);
    }
  }
  for (let index = 0; index < edited.length;) {
    if (originalIds.has(edited[index].slide_id)) { index += 1; continue; }
    let end = index;
    while (end + 1 < edited.length && !originalIds.has(edited[end + 1].slide_id)) end += 1;
    let anchor: string | null = null;
    for (let previous = index - 1; previous >= 0; previous -= 1) {
      if (originalIds.has(edited[previous].slide_id) && editedIds.has(edited[previous].slide_id)) { anchor = edited[previous].slide_id; break; }
    }
    for (let insert = end; insert >= index; insert -= 1) {
      const slide = edited[insert];
      operations.push({ op: "ADD_SLIDE", after_slide_id: anchor, title: slide.title, body_text: slide.body_text });
      const position = anchor === null ? 0 : sequence.indexOf(anchor) + 1;
      sequence.splice(position, 0, slide.slide_id);
    }
    index = end + 1;
  }
  const originalById = new Map(original.map((slide) => [slide.slide_id, slide]));
  for (const slide of edited) {
    const before = originalById.get(slide.slide_id);
    if (before && (before.title !== slide.title || before.body_text !== slide.body_text)) {
      operations.push({ op: "UPDATE_SLIDE", slide_id: slide.slide_id, ...(before.title !== slide.title ? { title: slide.title } : {}), ...(before.body_text !== slide.body_text ? { body_text: slide.body_text } : {}) });
    }
  }
  for (const [slideId, media] of Object.entries(mediaEdits)) {
    if (!originalIds.has(slideId) || !editedIds.has(slideId)) continue;
    operations.push(media === null ? { op: "CLEAR_MEDIA", slide_id: slideId } : { op: "SET_MEDIA", slide_id: slideId, placement: media.placement, media: media.media });
  }
  return operations;
}

function mediaInput(media: PresentationMedia): SlideMediaPayload {
  if (media.kind === "IMAGE") return { kind: "IMAGE", asset_ref: media.asset_ref, alt_text: media.alt_text };
  if (media.kind === "SVG_CATALOG") return { kind: "SVG_CATALOG", catalog_entry_id: media.catalog_entry_id, alt_text: media.alt_text };
  if (media.kind === "SVG_AI") return { kind: "SVG_AI", svg_draft_id: media.svg_draft_id, alt_text: media.alt_text };
  return { kind: "VIDEO_EMBED", url: media.embed_url };
}

function stagedMediaStatus(slide: PresentationRevision["slides"][number] | null, edit: SlideMediaInput | null | undefined): string | null {
  if (edit === undefined) return null;
  if (edit === null) return "Chưa lưu: đã đánh dấu gỡ hình ảnh.";
  if (slide?.media && JSON.stringify(mediaInput(slide.media)) === JSON.stringify(edit.media) && slide.media.placement !== edit.placement) {
    return "Chưa lưu: vị trí mới.";
  }
  const placement = edit.placement === "LEFT" ? ", vị trí bên trái" : edit.placement === "RIGHT" ? ", vị trí bên phải" : "";
  return edit.media.kind === "IMAGE" ? `Chưa lưu: hình ảnh mới${placement}.` : `Chưa lưu: nội dung mới${placement}.`;
}

function ProtectedSlideImage({ occurrenceId, assetRef, alt, isPresentation }: { occurrenceId: string; assetRef: string; alt: string; isPresentation: boolean }) {
  const [src, setSrc] = useState<string | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    let objectUrl: string | null = null;
    teacherPresentationApi.image(occurrenceId, assetRef, controller.signal)
      .then((blob) => { if (!controller.signal.aborted) { objectUrl = URL.createObjectURL(blob); setSrc(objectUrl); } })
      .catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [occurrenceId, assetRef]);
  if (error) return <p role="status">Ảnh chưa thể hiển thị.</p>;
  if (!src) return <p role="status">Đang tải ảnh…</p>;
  return <img src={src} alt={alt} style={{ maxWidth: "100%", maxHeight: isPresentation ? "56vh" : "20rem", objectFit: "contain" }} />;
}

function youtubePreviewUrl(embedUrl: string): string {
  const url = new URL(embedUrl);
  url.searchParams.set("rel", "0");
  return url.toString();
}

function escapeSvgAttribute(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/'/g, "&apos;");
}

function svgDocumentDataUrl(document: SvgDocumentV1): string {
  const paths = document.paths.map((path) => {
    const attributes = [`d="${escapeSvgAttribute(path.d)}"`];
    if (path.fill !== null) attributes.push(`fill="${escapeSvgAttribute(path.fill)}"`);
    if (path.stroke !== null) attributes.push(`stroke="${escapeSvgAttribute(path.stroke)}"`);
    if (path.stroke_width !== null && Number.isFinite(path.stroke_width)) attributes.push(`stroke-width="${path.stroke_width}"`);
    return `<path ${attributes.join(" ")} />`;
  }).join("");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${escapeSvgAttribute(document.view_box)}">${paths}</svg>`;
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

type CatalogPreviewEntry = { id: string; title: string; alt: string; document: SvgDocumentV1 | null };

function CatalogSvgPreview({ media, entries, loading, unavailable, isPresentation }: {
  media: Extract<PresentationMedia, { kind: "SVG_CATALOG" }>;
  entries: CatalogPreviewEntry[];
  loading: boolean;
  unavailable: boolean;
  isPresentation: boolean;
}) {
  const entry = entries.find((item) => item.id === media.catalog_entry_id);
  if (entry?.document) {
    return <img alt={media.alt_text} src={svgDocumentDataUrl(entry.document)} style={{ maxWidth: "100%", maxHeight: isPresentation ? "56vh" : "20rem", objectFit: "contain" }} />;
  }
  const note = loading ? "Đang tải hình minh họa SVG…" : unavailable ? "Chưa thể tải hình minh họa SVG." : "Chưa tìm thấy bản vẽ trong danh mục.";
  return <p role="status">{media.alt_text || "SVG minh họa"} · {note}</p>;
}

function MediaPreview({ occurrenceId, media, draft, catalogEntries, catalogLoading, catalogUnavailable, isPresentation }: {
  occurrenceId: string;
  media: PresentationMedia | null;
  draft: PresentationSvgDraft | null;
  catalogEntries: CatalogPreviewEntry[];
  catalogLoading: boolean;
  catalogUnavailable: boolean;
  isPresentation: boolean;
}) {
  if (!media) return null;
  const isVideo = media.kind === "VIDEO_EMBED";
  const className = `tp-slide-media-preview tp-slide-media-preview--${media.placement.toLowerCase()}${isVideo ? " tp-slide-video-preview" : ""}`;
  return <div className={className}>
    <div className="tp-slide-media-preview-inner">
      {media.kind === "IMAGE" && <ProtectedSlideImage occurrenceId={occurrenceId} assetRef={media.asset_ref} alt={media.alt_text} isPresentation={isPresentation} />}
      {media.kind === "VIDEO_EMBED" && <iframe title="Video nhúng" className="tp-slide-video-frame" src={media.provider === "YOUTUBE" ? youtubePreviewUrl(media.embed_url) : media.embed_url} allow="fullscreen; picture-in-picture" referrerPolicy="strict-origin-when-cross-origin" />}
      {media.kind === "SVG_AI" && draft?.svg_draft_id === media.svg_draft_id && <img alt={media.alt_text} src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(draft.preview_svg)}`} style={{ maxWidth: "100%", maxHeight: isPresentation ? "56vh" : "20rem", objectFit: "contain" }} />}
      {media.kind === "SVG_CATALOG" && <CatalogSvgPreview media={media} entries={catalogEntries} loading={catalogLoading} unavailable={catalogUnavailable} isPresentation={isPresentation} />}
      {media.kind === "SVG_AI" && draft?.svg_draft_id !== media.svg_draft_id && <p>{media.alt_text || "SVG minh họa"}</p>}
    </div>
  </div>;
}

export function TeacherSlidesPage() {
  const [searchParams] = useSearchParams();
  const occurrenceId = searchParams.get("occurrence") ?? "";
  const [occurrence, setOccurrence] = useState<Occurrence | null>(null);
  const [plan, setPlan] = useState<PlanRevision | null>(null);
  const [presentation, setPresentation] = useState<LessonPresentation | null>(null);
  const [readyRevision, setReadyRevision] = useState<PresentationRevision | null>(null);
  const [slides, setSlides] = useState<PresentationRevision["slides"]>([]);
  const [mediaEdits, setMediaEdits] = useState<Record<string, SlideMediaInput | null>>({});
  const [previewMode, setPreviewMode] = useState<PreviewMode>("head");
  const [previewIndex, setPreviewIndex] = useState(0);
  const [draft, setDraft] = useState<PresentationSvgDraft | null>(null);
  const [loading, setLoading] = useState(Boolean(occurrenceId));
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [displayedSvgTaskRunId, setDisplayedSvgTaskRunId] = useState<number | null>(null);
  const [reload, setReload] = useState(0);
  const [repin, setRepin] = useState(false);
  const [selectedSlideId, setSelectedSlideId] = useState("");
  const [mediaKind, setMediaKind] = useState<"IMAGE" | "SVG_CATALOG" | "SVG_AI" | "VIDEO_EMBED">("IMAGE");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [assetRef, setAssetRef] = useState("");
  const [catalogId, setCatalogId] = useState("");
  const [catalogEntries, setCatalogEntries] = useState<CatalogPreviewEntry[]>([]);
  const [catalogDetailEntries, setCatalogDetailEntries] = useState<CatalogPreviewEntry[]>([]);
  const [catalogDetailsResolved, setCatalogDetailsResolved] = useState<Set<string>>(() => new Set());
  const [catalogLoaded, setCatalogLoaded] = useState(false);
  const [catalogReadUnavailable, setCatalogReadUnavailable] = useState(false);
  const [altText, setAltText] = useState("");
  const [videoUrl, setVideoUrl] = useState("");
  const [placementChoice, setPlacementChoice] = useState<PlacementChoice | null>(null);
  const [subjectText, setSubjectText] = useState("");
  const [planActivityId, setPlanActivityId] = useState("");
  const [svgCooldown, setSvgCooldown] = useState(0);
  const blockedSvgError = useRef<string | null>(null);
  const catalogDetailPending = useRef(new Set<string>());
  const actionKeys = useRef(new Map<string, string>());
  const uploadKeys = useRef<{ signature: string; create: string; complete: string } | null>(null);
  const displayedSvgTask = useRef<{ key: AiTaskKey; runId: number } | null>(null);
  const seenSvgTask = useRef<{ key: AiTaskKey; runId: number; cancel: () => void } | null>(null);
  const organizationId = configuredOrganizationId();

  const isStale = presentation?.source_state === "STALE" || presentation?.head.source_state === "STALE";
  const operations = useMemo(() => presentation ? buildOperations(presentation.head.slides, slides, mediaEdits) : [], [presentation, slides, mediaEdits]);
  const hasUnsavedEdits = operations.length > 0;
  const selectedSlide = slides.find((slide) => slide.slide_id === selectedSlideId) ?? slides[0] ?? null;
  const selectedMediaEdit = selectedSlide ? mediaEdits[selectedSlide.slide_id] : undefined;
  const selectedMediaPlacement = selectedMediaEdit?.placement ?? selectedSlide?.media?.placement ?? "FULL";
  const placement = placementChoice
    && placementChoice.slideId === selectedSlide?.slide_id
    && placementChoice.sourcePresentation === presentation
    && placementChoice.sourcePlacement === selectedMediaPlacement
    ? placementChoice.value
    : selectedMediaPlacement;
  const selectedMediaStatus = stagedMediaStatus(selectedSlide, selectedMediaEdit);
  const mediaSaveBlockers = [
    Boolean(isStale) && !repin ? "Hãy chọn “Ghim phiên bản kế hoạch hiện tại khi tạo bản nháp mới” để lưu." : null,
    operations.length > 50 ? "Đã vượt giới hạn 50 thay đổi cho mỗi bản nháp." : null,
  ].filter((reason): reason is string => reason !== null);
  const selectedMediaActionStatus = selectedMediaStatus
    ? [selectedMediaStatus, ...mediaSaveBlockers].join(" ")
    : null;
  const saveDisabled = busy || operations.length === 0 || operations.length > 50 || (Boolean(isStale) && !repin);
  const previewSlides = previewMode === "ready" && readyRevision ? readyRevision.slides : presentation?.head.slides ?? [];
  const previewSlide = previewSlides[Math.min(previewIndex, Math.max(0, previewSlides.length - 1))] ?? null;
  const previewHasCatalogSvg = previewSlides.some((slide) => slide.media?.kind === "SVG_CATALOG");
  const previewCatalogIds = useMemo(
    () => [...new Set(previewSlides.flatMap((slide) => slide.media?.kind === "SVG_CATALOG" ? [slide.media.catalog_entry_id] : []))],
    [previewSlides],
  );
  const previewCatalogKey = previewCatalogIds.join("\u0000");
  const previewCatalogEntries = useMemo(() => {
    const entries = new Map<string, CatalogPreviewEntry>();
    for (const entry of [...catalogEntries, ...catalogDetailEntries]) entries.set(entry.id, entry);
    return [...entries.values()];
  }, [catalogEntries, catalogDetailEntries]);
  const previewCatalogEntryIds = useMemo(
    () => new Set(previewCatalogEntries.map((entry) => entry.id)),
    [previewCatalogEntries],
  );
  const catalogNeeded = mediaKind === "SVG_CATALOG" || previewHasCatalogSvg;
  const catalogLoading = catalogNeeded && Boolean(organizationId) && (
    !catalogLoaded || previewCatalogIds.some((id) => !previewCatalogEntryIds.has(id) && !catalogDetailsResolved.has(id))
  );
  const catalogUnavailable = catalogReadUnavailable || (catalogNeeded && !organizationId);
  const cooldownActive = svgCooldown > 0;
  const svgRequest = useSvgDraftRequest(occurrenceId);
  const svgTaskKey = svgTaskStatusKey(occurrenceId);
  const svgTaskMark = useAiTaskMark(svgTaskKey);
  const svgCooldownUntil = useSvgDraftCooldownUntil(occurrenceId);
  const svgPending = svgRequest?.status === "pending";
  const [now, setNow] = useState(() => Date.now());
  const svgBlocked = svgRequest?.status === "failed" && svgRequest.blockedUntil !== null && now < svgRequest.blockedUntil;
  const svgMinutes = svgRequest ? Math.max(0, Math.floor((now - svgRequest.startedAt) / 60_000)) : 0;
  const selectedPlanActivities = (plan?.activities ?? []).filter((activity) => activity.plan_activity_id && activity.title);

  useEffect(() => {
    if (!hasUnsavedEdits) return;
    const warnBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warnBeforeUnload);
    return () => window.removeEventListener("beforeunload", warnBeforeUnload);
  }, [hasUnsavedEdits]);

  const keyFor = (signature: string) => {
    const key = actionKeys.current.get(signature) ?? createIdempotencyKey();
    actionKeys.current.set(signature, key);
    return key;
  };

  useEffect(() => {
    let active = true;
    if (!occurrenceId) { setLoading(false); return () => { active = false; }; }
    setLoading(true);
    setError(null);
    setPresentation(null);
    setOccurrence(null);
    setPlan(null);
    setReadyRevision(null);
    teacherOccurrenceApi.get(occurrenceId)
      .then(async (result) => {
        if (!result.data) throw new BackendApiError("Không tìm thấy dữ liệu hoặc bạn không có quyền truy cập.", "RESOURCE_NOT_FOUND", 404);
        if (!active) return;
        setOccurrence(result.data);
        if (result.data.approved_plan) {
          const pinnedPlan = await teacherOccurrenceApi.getPlan(occurrenceId, result.data.approved_plan.revision_no);
          if (active && pinnedPlan.data) setPlan(pinnedPlan.data);
        }
        try {
          const current = await teacherPresentationApi.get(occurrenceId);
          if (!active) return;
          setPresentation(current);
          setSlides(current.head.slides);
          setSelectedSlideId(current.head.slides[0]?.slide_id ?? "");
          if (current.ready_revision_no !== null) {
            const ready = current.ready_revision_no === current.head_revision_no ? current.head : await teacherPresentationApi.getRevision(occurrenceId, current.ready_revision_no);
            if (active) { setReadyRevision(ready); setPreviewMode("ready"); }
          }
        } catch (cause) {
          if (cause instanceof BackendApiError && cause.status === 404) {
            if (active) { setPresentation(null); setSlides([]); setReadyRevision(null); }
          } else throw cause;
        }
      })
      .catch((cause: unknown) => { if (active) setError(safePresentationError(cause)); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [occurrenceId, reload]);

  useEffect(() => {
    if (svgRequest?.status === "done") {
      setDraft(svgRequest.draft);
      setNotice("Bản SVG nháp đã sẵn sàng để xem và quyết định.");
      if (svgTaskMark) {
        displayedSvgTask.current = { key: svgTaskKey, runId: svgTaskMark.runId };
        setDisplayedSvgTaskRunId(svgTaskMark.runId);
      }
    } else if (svgRequest?.status === "failed") {
      const stillBlocked = svgRequest.blockedUntil !== null && now < svgRequest.blockedUntil;
      if (svgRequest.blockedUntil !== null && !stillBlocked) {
        dismissSvgDraftRequest(occurrenceId);
        if (blockedSvgError.current) {
          const oldMessage = blockedSvgError.current;
          blockedSvgError.current = null;
          setError((current) => current === oldMessage ? null : current);
        }
        return;
      }
      const { cause } = svgRequest;
      const lost = svgRequest.blockedUntil !== null ? " Hệ thống có thể vẫn đang tạo; hãy chờ rồi bấm lại để lấy kết quả." : "";
      const message = safePresentationError(cause) + lost;
      setError(message);
      if (svgTaskMark) {
        displayedSvgTask.current = { key: svgTaskKey, runId: svgTaskMark.runId };
        setDisplayedSvgTaskRunId(svgTaskMark.runId);
      }
      if (stillBlocked) blockedSvgError.current = message;
      dismissSvgDraftRequest(occurrenceId);
    } else if (!svgRequest && blockedSvgError.current) {
      const oldMessage = blockedSvgError.current;
      blockedSvgError.current = null;
      setError((current) => current === oldMessage ? null : current);
    }
  }, [svgRequest, loading, occurrenceId, now, svgTaskKey, svgTaskMark]);

  useEffect(() => {
    const scheduled = seenSvgTask.current;
    if (scheduled && (!svgTaskMark || scheduled.key !== svgTaskKey || scheduled.runId !== svgTaskMark.runId)) {
      scheduled.cancel();
      seenSvgTask.current = null;
    }
    if (!svgTaskMark || svgTaskMark.status === "pending") return;
    const contentIsVisible = displayedSvgTask.current?.key === svgTaskKey
      && displayedSvgTaskRunId === svgTaskMark.runId
      && (svgTaskMark.status === "done" ? draft !== null : error !== null);
    if (!contentIsVisible || (seenSvgTask.current?.key === svgTaskKey && seenSvgTask.current.runId === svgTaskMark.runId)) return;
    const cancel = scheduleAiTaskStatusSeen(svgTaskKey, svgTaskMark.runId);
    seenSvgTask.current = { key: svgTaskKey, runId: svgTaskMark.runId, cancel };
  }, [svgTaskKey, svgTaskMark, displayedSvgTaskRunId, draft, error]);

  useEffect(() => () => {
    const scheduled = seenSvgTask.current;
    const displayed = displayedSvgTask.current;
    if (scheduled?.key === svgTaskKey) scheduled.cancel();
    if (scheduled?.key === svgTaskKey) clearAiTaskStatusIfCurrent(scheduled.key, scheduled.runId);
    else if (displayed?.key === svgTaskKey) clearAiTaskStatusIfCurrent(displayed.key, displayed.runId);
    if (scheduled?.key === svgTaskKey) seenSvgTask.current = null;
  }, [svgTaskKey]);

  // Keeps the "still working" minutes and the wait after a lost connection current.
  useEffect(() => {
    if (!svgPending && !svgBlocked) return;
    const timer = window.setInterval(() => setNow(Date.now()), 15_000);
    return () => window.clearInterval(timer);
  }, [svgPending, svgBlocked]);

  useEffect(() => {
    if (svgCooldownUntil === null) { setSvgCooldown(0); return; }
    const update = () => {
      const seconds = Math.max(0, Math.ceil((svgCooldownUntil - Date.now()) / 1000));
      setSvgCooldown(seconds);
      if (seconds === 0) expireSvgDraftCooldown(occurrenceId, svgCooldownUntil);
      return seconds;
    };
    if (update() === 0) return;
    const timer = window.setInterval(update, 1000);
    return () => window.clearInterval(timer);
  }, [svgCooldownUntil, occurrenceId]);

  useEffect(() => {
    let active = true;
    if (!catalogNeeded || !organizationId || catalogLoaded) return () => { active = false; };
    teacherSvgCatalogApi.listAssets(organizationId, { limit: 100 })
      .then((page) => {
        if (!active) return;
        setCatalogEntries(page.items.filter((item) => item.review_state === "APPROVED" && typeof item.catalog_entry_id === "string")
          .map((item) => ({ id: item.catalog_entry_id, title: item.title_vi, alt: item.alt_text_vi, document: item.document })));
        setCatalogReadUnavailable(false);
        setCatalogLoaded(true);
      })
      .catch(() => { if (active) { setCatalogEntries([]); setCatalogReadUnavailable(true); setCatalogLoaded(true); } });
    return () => { active = false; };
  }, [catalogNeeded, organizationId, catalogLoaded]);

  useEffect(() => {
    if (!catalogNeeded || !organizationId || !catalogLoaded) return;
    const missingIds = previewCatalogIds.filter((id) =>
      !previewCatalogEntryIds.has(id)
      && !catalogDetailsResolved.has(id)
      && !catalogDetailPending.current.has(id),
    );
    if (missingIds.length === 0) return;
    missingIds.forEach((id) => catalogDetailPending.current.add(id));
    void Promise.all(missingIds.map(async (id) => {
      try {
        return { id, asset: await teacherSvgCatalogApi.getAsset(organizationId, id), error: null as unknown };
      } catch (error) {
        return { id, asset: null, error };
      }
    })).then((results) => {
      const fetched = results.flatMap(({ asset }) => asset ? [{
        id: asset.catalog_entry_id,
        title: asset.title_vi,
        alt: asset.alt_text_vi,
        document: asset.document,
      }] : []);
      if (fetched.length > 0) setCatalogDetailEntries((current) => {
        const entries = new Map(current.map((entry) => [entry.id, entry]));
        for (const entry of fetched) entries.set(entry.id, entry);
        return [...entries.values()];
      });
      setCatalogDetailsResolved((current) => new Set([...current, ...missingIds]));
      if (results.some(({ error }) => error !== null && !(error instanceof BackendApiError && error.status === 404))) {
        setCatalogReadUnavailable(true);
      }
    }).finally(() => missingIds.forEach((id) => catalogDetailPending.current.delete(id)));
  }, [catalogNeeded, organizationId, catalogLoaded, previewCatalogKey, previewCatalogEntryIds, catalogDetailsResolved]);

  const createPresentation = async (seed: "PLAN_ACTIVITIES" | "BLANK") => {
    if (!occurrence || !occurrence.approved_plan || busy) return;
    const signature = JSON.stringify(["create", occurrenceId, seed]);
    setBusy(true); setError(null); setNotice(null);
    try {
      const created = await teacherPresentationApi.create(occurrenceId, seed, keyFor(signature));
      actionKeys.current.delete(signature);
      setPresentation(created); setSlides(created.head.slides); setMediaEdits({});
      setSelectedSlideId(created.head.slides[0]?.slide_id ?? ""); setReadyRevision(null); setPreviewMode("head");
      setNotice("Đã tạo bản nháp trình bày.");
    } catch (cause) {
      setError(safePresentationError(cause));
      if (cause instanceof BackendApiError && (cause.status === 409 || cause.code === "RESOURCE_CONFLICT")) setReload((value) => value + 1);
      if (cause instanceof BackendApiError && cause.status < 500 && cause.status !== 0) actionKeys.current.delete(signature);
    } finally { setBusy(false); }
  };

  const saveRevision = async () => {
    if (!presentation || operations.length === 0 || operations.length > 50 || busy) return;
    const input = { repin_to_current_plan: Boolean(isStale && repin), operations };
    const signature = JSON.stringify(["revision", occurrenceId, presentation.revision, input]);
    setBusy(true); setError(null); setNotice(null);
    try {
      const next = await teacherPresentationApi.createRevision(occurrenceId, presentation.revision, input, keyFor(signature));
      actionKeys.current.delete(signature);
      setPresentation(next); setSlides(next.head.slides); setMediaEdits({}); setSelectedSlideId(next.head.slides[0]?.slide_id ?? "");
      if (next.ready_revision_no !== null) {
        const ready = next.ready_revision_no === next.head_revision_no ? next.head : await teacherPresentationApi.getRevision(occurrenceId, next.ready_revision_no);
        setReadyRevision(ready);
      }
      setPreviewMode("head"); setRepin(false);
      setNotice(next.ready_revision_no !== null
        ? "Đã tạo bản nháp mới. Bản đã sẵn sàng trước đó vẫn được giữ nguyên."
        : "Đã tạo bản nháp mới.");
    } catch (cause) {
      setError(safePresentationError(cause));
      if (cause instanceof BackendApiError && cause.code === "STALE_REVISION") { actionKeys.current.delete(signature); setReload((value) => value + 1); }
      else if (cause instanceof BackendApiError && cause.status < 500 && cause.status !== 0) actionKeys.current.delete(signature);
    } finally { setBusy(false); }
  };

  const readyHead = async () => {
    if (!presentation || presentation.head.state !== "DRAFT" || busy) return;
    const signature = JSON.stringify(["ready", occurrenceId, presentation.revision, presentation.head_revision_no]);
    setBusy(true); setError(null); setNotice(null);
    try {
      const next = await teacherPresentationApi.ready(occurrenceId, presentation.head_revision_no, presentation.revision, keyFor(signature));
      actionKeys.current.delete(signature);
      setPresentation(next); setSlides(next.head.slides); setMediaEdits({}); setReadyRevision(next.head); setPreviewMode("ready"); setRepin(false);
      setNotice("Bản trình bày đã sẵn sàng.");
    } catch (cause) {
      setError(safePresentationError(cause));
      if (cause instanceof BackendApiError && cause.code === "STALE_REVISION") { actionKeys.current.delete(signature); setReload((value) => value + 1); }
      else if (cause instanceof BackendApiError && cause.status < 500 && cause.status !== 0) actionKeys.current.delete(signature);
    } finally { setBusy(false); }
  };

  const uploadImage = async () => {
    if (!imageFile || !occurrenceId || uploading) return;
    const signature = JSON.stringify([occurrenceId, imageFile.name, imageFile.size, imageFile.lastModified]);
    if (!uploadKeys.current || uploadKeys.current.signature !== signature) uploadKeys.current = { signature, create: createIdempotencyKey(), complete: createIdempotencyKey() };
    setUploading(true); setError(null); setUploadProgress(0);
    try {
      const ref = await teacherPresentationApi.uploadImage(imageFile, occurrenceId, uploadKeys.current, (done, total) => setUploadProgress(Math.floor((done / total) * 100)));
      setAssetRef(ref);
      uploadKeys.current = null; setNotice("Ảnh đã tải lên và sẵn sàng để đính kèm.");
    } catch (cause) { setError(safePresentationError(cause)); }
    finally { setUploading(false); setUploadProgress(null); }
  };

  const attachMedia = () => {
    if (!selectedSlide || selectedSlide.slide_id.startsWith("local-") || (mediaKind !== "VIDEO_EMBED" && !altText.trim())) return;
    let media: SlideMediaPayload | null = null;
    if (mediaKind === "IMAGE" && assetRef) media = { kind: "IMAGE", asset_ref: assetRef, alt_text: altText.trim() };
    if (mediaKind === "SVG_CATALOG" && catalogId.trim()) media = { kind: "SVG_CATALOG", catalog_entry_id: catalogId.trim(), alt_text: altText.trim() };
    if (mediaKind === "SVG_AI" && draft?.state === "ACCEPTED") media = { kind: "SVG_AI", svg_draft_id: draft.svg_draft_id, alt_text: altText.trim() };
    if (mediaKind === "VIDEO_EMBED" && videoUrl.trim()) media = { kind: "VIDEO_EMBED", url: videoUrl.trim() };
    if (!media) return;
    setMediaEdits((current) => ({ ...current, [selectedSlide.slide_id]: { media, placement } }));
    setNotice("Nội dung đã chọn. Lưu bản nháp để áp dụng thay đổi.");
  };

  const repositionCurrentMedia = () => {
    if (!selectedSlide || selectedSlide.slide_id.startsWith("local-") || selectedMediaEdit === null) return;
    const mediaToReposition = selectedMediaEdit ?? (selectedSlide.media
      ? { media: mediaInput(selectedSlide.media), placement: selectedSlide.media.placement }
      : null);
    if (!mediaToReposition) return;
    setMediaEdits((current) => ({ ...current, [selectedSlide.slide_id]: { media: mediaToReposition.media, placement } }));
    setNotice("Vị trí hình ảnh đã chọn. Lưu bản nháp để áp dụng thay đổi.");
  };

  const removeSelectedMedia = () => {
    if (!selectedSlide || selectedSlide.slide_id.startsWith("local-") || selectedMediaEdit === null) return;
    if (!selectedSlide.media && selectedMediaEdit) {
      setMediaEdits((current) => {
        const next = { ...current };
        delete next[selectedSlide.slide_id];
        return next;
      });
      return;
    }
    setMediaEdits((current) => ({ ...current, [selectedSlide.slide_id]: null }));
  };

  const requestSvgDraft = () => {
    if (!occurrenceId || !planActivityId || !subjectPattern.test(subjectText) || busy || cooldownActive || svgPending || svgBlocked) return;
    const signature = JSON.stringify(["svg-draft", occurrenceId, planActivityId, subjectText]);
    const input = { plan_activity_id: planActivityId, subject_text: subjectText };
    setError(null); setNotice(null); setNow(Date.now());
    startSvgDraftRequest(occurrenceId, signature, (key) => teacherPresentationApi.createSvgDraft(occurrenceId, input, key));
  };

  const decideSvgDraft = async (decision: "ACCEPT" | "DISCARD") => {
    if (!draft || draft.state !== "PENDING_REVIEW" || busy) return;
    const signature = JSON.stringify(["svg-decision", occurrenceId, draft.svg_draft_id, draft.revision, decision]);
    setBusy(true); setError(null);
    try {
      const next = await teacherPresentationApi.decideSvgDraft(occurrenceId, draft.svg_draft_id, draft.revision, decision, keyFor(signature));
      actionKeys.current.delete(signature); dismissSvgDraftRequest(occurrenceId); setDraft(next); setNotice(decision === "ACCEPT" ? "Đã chấp nhận bản SVG." : "Đã bỏ bản SVG nháp.");
    } catch (cause) {
      setError(safePresentationError(cause));
      if (cause instanceof BackendApiError && cause.code === "STALE_REVISION") { actionKeys.current.delete(signature); setReload((value) => value + 1); }
      else if (cause instanceof BackendApiError && cause.status < 500 && cause.status !== 0) actionKeys.current.delete(signature);
    } finally { setBusy(false); }
  };

  const updateSlide = (slideId: string, field: "title" | "body_text", value: string) => {
    setSlides((current) => current.map((slide) => slide.slide_id === slideId ? { ...slide, [field]: value } : slide));
  };

  const moveSlide = (slideId: string, delta: -1 | 1) => {
    setSlides((current) => {
      const from = current.findIndex((slide) => slide.slide_id === slideId);
      const to = from + delta;
      if (from < 0 || to < 0 || to >= current.length) return current;
      const next = [...current];
      [next[from], next[to]] = [next[to], next[from]];
      return next;
    });
  };

  const addSlide = () => {
    if (slides.length >= 100) return;
    const localId = `local-${createIdempotencyKey()}`;
    const slide = { slide_id: localId, position: slides.length + 1, title: "", body_text: "", media: null, media_state: null } as const;
    setSlides((current) => [...current, slide]); setSelectedSlideId(localId);
  };

  const removeSlide = (slideId: string) => {
    if (slides.length <= 1) return;
    setSlides((current) => current.filter((slide) => slide.slide_id !== slideId));
    setMediaEdits((current) => { const next = { ...current }; delete next[slideId]; return next; });
    if (selectedSlideId === slideId) setSelectedSlideId(slides.find((slide) => slide.slide_id !== slideId)?.slide_id ?? "");
  };

  const decisionDraft = draft?.state === "PENDING_REVIEW";
  const draftMediaId = draft?.state === "ACCEPTED" ? draft.svg_draft_id : "";
  const previewStateMeta = previewMode === "ready"
    ? { label: "Sẵn sàng", tone: "success" as const }
    : teacherStatusMeta(presentation?.head.state ?? "DRAFT", "lesson");

  return (
    <div className="s2l-page s2l-data-page">
      <PageHeading
        eyebrow="Giáo viên · Buổi dạy"
        title="Trình bày giáo án"
        description="Soạn và trình bày các slide gắn với kế hoạch đã duyệt của buổi dạy. Mỗi lần lưu tạo một phiên bản mới."
        action={<button type="button" className="s2l-button" disabled={loading || busy} onClick={() => setReload((value) => value + 1)}><RefreshCw size={16} aria-hidden="true" />Tải lại</button>}
      />
      {!occurrenceId && (
        <EmptyState
          title="Chưa chọn buổi dạy"
          description="Chọn một buổi dạy để mở phần trình bày tương ứng."
          action={<Link className="s2l-button" to="/teacher/t04-session-sketch-deck">Chọn buổi dạy</Link>}
        />
      )}
      {loading && <p className="s2l-data-card" role="status">Đang tải buổi dạy và bản trình bày…</p>}
      {error && <Alert role="alert" tone="danger">{error}</Alert>}
      {notice && <p className="s2l-note" role="status">{notice}</p>}

      {occurrence && !presentation && (
        <section className="s2l-data-card cozy-form-stack" aria-label="Buổi dạy">
          <div className="tw-row tw-between tw-wrap">
            <div>
              <h2>{occurrence.title}</h2>
              <p className="tw-sub">{occurrence.scheduled_date ? formatDateDdMmYyyy(occurrence.scheduled_date) : "Chưa đặt ngày"}</p>
            </div>
            <StatusBadge tone={teacherStatusMeta(occurrence.state, "session").tone} dot>{occurrenceStateLabel[occurrence.state]}</StatusBadge>
          </div>
          {!occurrence.approved_plan && <p className="s2l-alert">Cần có kế hoạch đã duyệt trước khi tạo trình bày.</p>}
          {occurrence.approved_plan && <p>Kế hoạch đã duyệt · Phiên bản {occurrence.approved_plan.revision_no}</p>}
        </section>
      )}

      {occurrence && !presentation && !loading && !error && (
        <section className="s2l-data-card cozy-form-stack" aria-label="Tạo trình bày">
          <h2>Tạo bản trình bày</h2>
          <p>Mỗi buổi dạy có một bộ slide trình bày. Bản tạo từ hoạt động sẽ lấy các hoạt động của kế hoạch đã duyệt.</p>
          <FormActionBar hint={!occurrence.approved_plan ? "Cần xác nhận kế hoạch của buổi dạy trước khi tạo trình bày." : undefined}>
            <Button type="button" variant="secondary" disabled={busy || !occurrence.approved_plan} onClick={() => void createPresentation("BLANK")}>Tạo slide trống</Button>
            <Button type="button" variant="primary" disabled={busy || !occurrence.approved_plan} onClick={() => void createPresentation("PLAN_ACTIVITIES")}>Tạo từ hoạt động kế hoạch</Button>
          </FormActionBar>
        </section>
      )}

      {presentation && !loading && <>
        {isStale && <div className="s2l-alert" role="status"><strong>Nguồn đã thay đổi.</strong> Bản sẵn sàng hiện không còn mới nhất. Hãy lưu phiên bản mới và ghim lại kế hoạch trước khi đánh dấu sẵn sàng.</div>}
        <section className="s2l-data-card cozy-form-stack" aria-label="Tình trạng bản trình bày">
          <div className="s2l-section-heading">
            <div>
              <h2>{occurrence?.title ?? "Trình bày buổi dạy"}</h2>
              <p>Phiên bản {presentation.revision}{occurrence?.scheduled_date ? ` · ${formatDateDdMmYyyy(occurrence.scheduled_date)}` : ""}</p>
            </div>
            <StatusBadge tone={presentation.presentable ? "success" : "neutral"} dot>
              {presentation.presentable ? "Có thể trình bày" : "Chưa sẵn sàng"}
            </StatusBadge>
          </div>
          <p className="tw-meta">
            Nguồn: {presentation.source_state === "CURRENT" ? "hiện hành" : "đã thay đổi"}
            {presentation.stale_reasons.length ? ` · ${presentation.stale_reasons.map(staleReasonLabel).join(", ")}` : ""}
          </p>
        </section>

        <SlidePresenter
          revisionLabel={previewMode === "ready" && readyRevision ? "Bản sẵn sàng" : "Bản nháp"}
          slideIndex={previewIndex}
          slideCount={previewSlides.length}
          onPrevious={() => setPreviewIndex((value) => Math.max(0, value - 1))}
          onNext={() => setPreviewIndex((value) => Math.min(previewSlides.length - 1, value + 1))}
        >
          {({ isPresenting, trigger }) => (
            <section className={`s2l-data-card cozy-form-stack${isPresenting ? " tp-slide-presenter-content" : ""}`} aria-label="Xem trước slide">
              <div className={`s2l-section-heading${isPresenting ? " tp-slide-presenter-heading" : ""}`}>
                <h2>Xem trước 16:9</h2>
                <div className="tp-actions" aria-hidden={isPresenting || undefined}>
                  <button type="button" className={previewMode === "ready" ? "s2l-button is-primary" : "s2l-button"} disabled={!readyRevision} aria-pressed={previewMode === "ready"} onClick={() => { setPreviewMode("ready"); setPreviewIndex(0); }}>Bản sẵn sàng</button>
                  <button type="button" className={previewMode === "head" ? "s2l-button is-primary" : "s2l-button"} aria-pressed={previewMode === "head"} onClick={() => { setPreviewMode("head"); setPreviewIndex(0); }}>Bản mới nhất</button>
                </div>
                {trigger}
              </div>
              {previewSlide ? (
                <div className={`tp-slide-preview-canvas${previewSlide.media ? " has-media" : ""}${previewSlide.media?.kind === "VIDEO_EMBED" ? " has-video" : ""}${isPresenting ? " tp-slide-presenter-canvas" : ""}`}>
                  <StatusBadge tone={previewStateMeta.tone} size="sm" dot>
                    Slide {previewIndex + 1} / {previewSlides.length} · {previewStateMeta.label}
                  </StatusBadge>
                  {previewSlide.title && <h3 className="tp-slide-preview-title">{previewSlide.title}</h3>}
                  {previewSlide.body_text && <p className="tp-slide-preview-body">{previewSlide.body_text}</p>}
                  <MediaPreview
                    occurrenceId={occurrenceId}
                    media={previewSlide.media}
                    draft={draft}
                    catalogEntries={previewCatalogEntries}
                    catalogLoading={catalogLoading}
                    catalogUnavailable={catalogUnavailable}
                    isPresentation={isPresenting}
                  />
                  {!previewSlide.title && !previewSlide.body_text && !previewSlide.media && (
                    <p className="tw-sub">Slide chưa có nội dung.</p>
                  )}
                </div>
              ) : <p className="tw-sub">Chưa có slide để xem.</p>}
              <div className={`tp-slide-pager${isPresenting ? " tp-slide-presenter-pager" : ""}`} aria-hidden={isPresenting || undefined}>
                <Button type="button" variant="secondary" disabled={!previewSlide || previewIndex <= 0} onClick={() => setPreviewIndex((value) => Math.max(0, value - 1))}>Slide trước</Button>
                <Button type="button" variant="secondary" disabled={!previewSlide || previewIndex >= previewSlides.length - 1} onClick={() => setPreviewIndex((value) => Math.min(previewSlides.length - 1, value + 1))}>Slide sau</Button>
              </div>
            </section>
          )}
        </SlidePresenter>

        <section className="s2l-data-card cozy-form-stack" aria-label="Chỉnh sửa slide">
          <div className="tp-form-column">
            <div className="s2l-section-heading"><h2>Chỉnh sửa bản nháp</h2>{operations.length >= 40 && <span className="tp-value-chip">{operations.length} / 50 thao tác</span>}</div>
            {isStale && <label className="cozy-form-checkbox-card"><input type="checkbox" checked={repin} onChange={(event) => setRepin(event.target.checked)} /><span>Ghim phiên bản kế hoạch hiện tại khi tạo bản nháp mới</span></label>}
            <ol className="tp-slide-list">
              {slides.map((slide, index) => <li key={slide.slide_id} className="cozy-form-section cozy-form-stack tp-run-section">
                <div className="s2l-section-heading"><h3>Slide {index + 1}</h3><div className="tp-actions">
                  <button type="button" className="s2l-button" aria-label={`Đưa slide ${index + 1} lên`} disabled={busy || index === 0} onClick={() => moveSlide(slide.slide_id, -1)}><ArrowUp size={15} aria-hidden="true" /></button>
                  <button type="button" className="s2l-button" aria-label={`Đưa slide ${index + 1} xuống`} disabled={busy || index === slides.length - 1} onClick={() => moveSlide(slide.slide_id, 1)}><ArrowDown size={15} aria-hidden="true" /></button>
                  <button type="button" className="s2l-button tp-quiet-danger" aria-label={`Xóa slide ${index + 1}`} disabled={busy || slides.length <= 1} onClick={() => removeSlide(slide.slide_id)}><Trash2 size={15} aria-hidden="true" /></button>
                </div></div>
                <FormField label="Tiêu đề" htmlFor={`slide-title-${index}`}><input id={`slide-title-${index}`} className="cozy-input" maxLength={200} value={slide.title} disabled={busy} onChange={(event) => updateSlide(slide.slide_id, "title", event.target.value)} /></FormField>
                <FormField label="Nội dung" htmlFor={`slide-body-${index}`}><textarea id={`slide-body-${index}`} className="cozy-textarea" maxLength={2000} rows={4} value={slide.body_text} disabled={busy} onChange={(event) => updateSlide(slide.slide_id, "body_text", event.target.value)} /></FormField>
                <p className="tw-meta">{mediaEdits[slide.slide_id] === null ? "Hình ảnh sẽ được gỡ khi lưu." : mediaEdits[slide.slide_id] ? "Có hình ảnh mới chờ lưu." : slide.media ? `Hình ảnh hiện tại · ${mediaKindLabel(slide.media.kind)}${slide.media.kind === "VIDEO_EMBED" ? ` · ${slide.media.provider}` : ` · ${slide.media.alt_text}`}` : "Chưa có hình minh họa."}</p>
              </li>)}
            </ol>
            {operations.length > 50 && <p className="s2l-alert" role="status">Một lần lưu tối đa 50 thao tác. Hãy lưu thay đổi theo từng phần.</p>}
            <FormActionBar hint={presentation.head.state !== "DRAFT" ? "Lưu một phiên bản mới trước khi chỉnh sửa bản đã công bố." : undefined}>
              <Button type="button" variant="secondary" disabled={busy || slides.length >= 100} onClick={addSlide}><Plus size={16} aria-hidden="true" />Thêm slide</Button>
              <Button type="button" variant="secondary" disabled={busy || presentation.head.state !== "DRAFT" || isStale} onClick={() => void readyHead()}>Đánh dấu sẵn sàng</Button>
              <Button type="button" variant="primary" loading={busy} disabled={busy || operations.length === 0 || operations.length > 50 || (Boolean(isStale) && !repin)} onClick={() => void saveRevision()}>Lưu bản nháp mới</Button>
            </FormActionBar>
          </div>
        </section>

        <section className="s2l-data-card cozy-form-stack" aria-label="Đính kèm hình ảnh minh họa">
          <div className="tp-form-column">
            <h2><ImageIcon size={18} aria-hidden="true" /> Hình ảnh cho slide đang chọn</h2>
            <div className="cozy-form-grid">
              <FormField className="cozy-span-2" label="Slide" htmlFor="slide-media-target">
                <select id="slide-media-target" className="cozy-input" value={selectedSlide?.slide_id ?? ""} onChange={(event) => { setPlacementChoice(null); setSelectedSlideId(event.target.value); }}>
                  {slides.map((slide, index) => <option key={slide.slide_id} value={slide.slide_id}>Slide {index + 1}</option>)}
                </select>
              </FormField>
              <FormField className="cozy-span-2" label="Loại nội dung" htmlFor="slide-media-kind">
                <select id="slide-media-kind" className="cozy-input" value={mediaKind} onChange={(event) => {
                  const nextKind = event.target.value as typeof mediaKind;
                  if (nextKind === "SVG_CATALOG" && mediaKind !== "SVG_CATALOG") { setCatalogLoaded(false); setCatalogReadUnavailable(false); }
                  setMediaKind(nextKind);
                }}>
                  <option value="IMAGE">Ảnh tải lên</option>
                  <option value="SVG_CATALOG">Danh mục SVG</option>
                  <option value="SVG_AI">SVG gợi ý AI</option>
                  <option value="VIDEO_EMBED">YouTube / Vimeo</option>
                </select>
              </FormField>
              <FormField className="cozy-span-2" label="Vị trí" htmlFor="slide-media-placement">
                <select id="slide-media-placement" className="cozy-input" value={placement} onChange={(event) => {
                  if (!selectedSlide) return;
                  setPlacementChoice({ slideId: selectedSlide.slide_id, value: event.target.value as typeof placement, sourcePlacement: selectedMediaPlacement, sourcePresentation: presentation });
                }}>
                  <option value="FULL">Toàn slide</option>
                  <option value="LEFT">Bên trái</option>
                  <option value="RIGHT">Bên phải</option>
                </select>
              </FormField>
            </div>
            {mediaKind === "IMAGE" && <div className="cozy-form-stack">
              <div className="teacher-file-field">
                <span id="presentation-image-label" className="cozy-form-label">Ảnh JPEG, PNG hoặc WebP</span>
                <label className="teacher-file-picker" htmlFor="presentation-image">
                  <span className="teacher-file-picker-button"><Upload size={16} aria-hidden="true" /> Chọn tệp</span>
                  <span className="teacher-file-picker-name">{imageFile?.name ?? "Chưa chọn tệp"}</span>
                  <input id="presentation-image" className="teacher-file-picker-input" type="file" accept="image/jpeg,image/png,image/webp,.jpg,.jpeg,.png,.webp" aria-labelledby="presentation-image-label" disabled={uploading || busy} onChange={(event) => { const file = event.target.files?.[0] ?? null; setImageFile(file); setAssetRef(""); uploadKeys.current = null; }} />
                </label>
                <p className="cozy-form-hint">Dung lượng tối đa 20 MiB.</p>
              </div>
              <FormActionBar>
                <Button type="button" variant="secondary" disabled={!imageFile || uploading || busy} onClick={() => void uploadImage()}>{uploading ? `Đang tải ${uploadProgress ?? 0}%…` : "Tải ảnh lên"}</Button>
              </FormActionBar>
              {assetRef && <p className="s2l-note" role="status">Ảnh đã tải lên, sẵn sàng để đính kèm.</p>}
            </div>}
            {mediaKind === "SVG_CATALOG" && <div className="cozy-form-grid">
              <FormField className="cozy-span-3" label="Danh mục SVG" htmlFor="slide-catalog-select" help={catalogLoading ? "Đang tải danh mục SVG…" : catalogUnavailable ? "Danh mục chưa thể tải. Có thể nhập mã SVG đã biết." : undefined}>
                <select id="slide-catalog-select" className="cozy-input" value={catalogEntries.some((entry) => entry.id === catalogId) ? catalogId : ""} disabled={catalogLoading} onChange={(event) => setCatalogId(event.target.value)}>
                  <option value="">Chọn SVG đang hoạt động</option>
                  {catalogEntries.map((entry) => <option key={entry.id} value={entry.id}>{entry.title}</option>)}
                </select>
              </FormField>
              {!catalogLoading && catalogEntries.length === 0 && <p className="s2l-note">Chỉ SVG đã được duyệt xuất hiện ở đây. Nhờ giáo viên khác duyệt trong Danh mục SVG.</p>}
              <FormField className="cozy-span-3" label="Mã SVG trong danh mục" htmlFor="slide-catalog-id">
                <input id="slide-catalog-id" className="cozy-input" value={catalogId} maxLength={128} onChange={(event) => setCatalogId(event.target.value)} />
              </FormField>
            </div>}
            {mediaKind === "SVG_AI" && <p className="s2l-note">{draftMediaId ? "SVG đã được chấp nhận: sẵn sàng để đính kèm." : "Hãy yêu cầu một bản SVG, xem trước rồi chấp nhận trước khi đính kèm."}</p>}
            {mediaKind === "VIDEO_EMBED" && <FormField label="Liên kết YouTube hoặc Vimeo" htmlFor="slide-video-url"><input id="slide-video-url" className="cozy-input" type="url" maxLength={2048} value={videoUrl} onChange={(event) => setVideoUrl(event.target.value)} /></FormField>}
            {mediaKind !== "VIDEO_EMBED" && <FormField label="Mô tả hình ảnh" htmlFor="slide-media-alt"><input id="slide-media-alt" className="cozy-input" maxLength={300} value={altText} onChange={(event) => setAltText(event.target.value)} /></FormField>}
            <FormActionBar className="tp-slide-media-actions">
              <Button type="button" variant="secondary" disabled={busy || !selectedSlide || selectedSlide.slide_id.startsWith("local-") || selectedMediaEdit === null || (!selectedSlide.media && !selectedMediaEdit)} onClick={removeSelectedMedia}>Gỡ hình ảnh</Button>
              <Button type="button" variant="secondary" disabled={busy || !selectedSlide || selectedSlide.slide_id.startsWith("local-") || selectedMediaEdit === null || (!selectedSlide.media && !selectedMediaEdit) || selectedMediaPlacement === placement} onClick={repositionCurrentMedia}>Cập nhật vị trí hiện tại</Button>
              <Button type="button" variant="primary" disabled={busy || uploading || !selectedSlide || selectedSlide.slide_id.startsWith("local-") || (mediaKind !== "VIDEO_EMBED" && !altText.trim()) || (mediaKind === "IMAGE" && !assetRef) || (mediaKind === "SVG_CATALOG" && !catalogId.trim()) || (mediaKind === "SVG_AI" && !draftMediaId) || (mediaKind === "VIDEO_EMBED" && !videoUrl.trim())} onClick={attachMedia}>Đính kèm vào bản nháp</Button>
              <Button type="button" variant="primary" loading={busy} disabled={saveDisabled} onClick={() => void saveRevision()}>Lưu bản nháp mới</Button>
              {selectedMediaActionStatus && <p className="tp-slide-media-status" role="status" aria-live="polite">{selectedMediaActionStatus}</p>}
            </FormActionBar>
          </div>
        </section>

        <section className="s2l-data-card cozy-form-stack" aria-label="Bản SVG minh họa do AI tạo">
          <div className="tp-form-column">
            <h2>SVG minh họa · chỉ tạo khi bạn yêu cầu</h2>
            <p className="tw-sub">Yêu cầu chỉ dùng tiêu đề hoạt động trong kế hoạch và chủ thể bạn nhập.</p>
            <div className="cozy-form-grid">
              <FormField className="cozy-span-3" label="Hoạt động trong kế hoạch" htmlFor="svg-plan-activity">
                <select id="svg-plan-activity" className="cozy-input" value={planActivityId} onChange={(event) => setPlanActivityId(event.target.value)}>
                  <option value="">Chọn hoạt động</option>
                  {selectedPlanActivities.map((activity) => <option key={activity.plan_activity_id} value={activity.plan_activity_id!}>{activity.title}</option>)}
                </select>
              </FormField>
              <FormField className="cozy-span-3" label="Chủ thể" htmlFor="svg-subject">
                <input id="svg-subject" className="cozy-input" maxLength={80} value={subjectText} onChange={(event) => setSubjectText(event.target.value)} placeholder="Ví dụ: con mèo" />
              </FormField>
            </div>
            {!selectedPlanActivities.length && <p className="s2l-note">Kế hoạch hiện tại chưa có hoạt động để tạo SVG.</p>}
            <FormActionBar>
              <Button type="button" variant="secondary" disabled={busy || svgPending || svgBlocked || cooldownActive || !presentation || !planActivityId || !subjectPattern.test(subjectText)} onClick={requestSvgDraft}>{svgPending ? "Đang tạo bản SVG…" : svgBlocked ? "Đang chờ kết quả…" : cooldownActive ? `Thử lại sau ${svgCooldown} giây` : "Yêu cầu tạo bản SVG"}</Button>
            </FormActionBar>
            {svgPending && <p className="s2l-note" role="status">Đang tạo bản SVG, có thể mất vài phút{svgMinutes > 0 ? ` (đã ${svgMinutes} phút)` : ""}. Bạn có thể rời màn hình và quay lại; không cần bấm lại.</p>}
            {decisionDraft && <div className="s2l-data-card cozy-form-stack" aria-label="Xem trước bản SVG nháp">
              <h3>Bản nháp cần bạn quyết định</h3>
              <img alt="Bản SVG nháp đã được máy chủ làm sạch" src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(draft.preview_svg)}`} style={{ width: "min(100%, 24rem)", maxHeight: "20rem" }} />
              <p className="tw-meta">Giấy phép {draft.license_id}</p>
              <FormActionBar>
                <Button type="button" variant="secondary" disabled={busy} onClick={() => void decideSvgDraft("DISCARD")}>Bỏ bản nháp</Button>
                <Button type="button" variant="primary" disabled={busy} onClick={() => void decideSvgDraft("ACCEPT")}>Chấp nhận</Button>
              </FormActionBar>
            </div>}
            {draft?.state === "ACCEPTED" && <p className="s2l-note" role="status">Bản SVG đã được chấp nhận. Chọn loại nội dung SVG gợi ý AI để đính kèm.</p>}
            {draft?.state === "DISCARDED" && <p className="s2l-note" role="status">Bản SVG nháp đã được bỏ.</p>}
          </div>
        </section>
      </>}
    </div>
  );
}
