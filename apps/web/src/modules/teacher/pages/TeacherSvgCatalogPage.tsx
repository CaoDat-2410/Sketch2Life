import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createSvgCatalogAsset,
  createSvgGuideRevision,
  listSvgCatalogAssets,
  listSvgGuideRevisions,
  reviewSvgCatalogSource,
  reviewSvgGuide,
  type CreateSvgGuideRevisionRequestV1,
  type SvgCatalogAssetCreateRequestV1,
  type SvgCatalogAssetResponseV1,
  type SvgGuideRevisionReceiptV1,
} from "../../../shared/api/teacherSvgCatalogApi";
import { configuredOrganizationId } from "../../../shared/api/backendApi";
import { authService } from "../../school-manager/be1/services/authService";
import { SvgAssetList } from "../components/SvgAssetList";
import { SvgGuideAuthoring } from "../components/SvgGuideAuthoring";
import { SvgGuidePlayer } from "../components/SvgGuidePlayer";
import { SvgGuideReviewPanel } from "../components/SvgGuideReviewPanel";

interface UiError {
  message: string;
  status: number;
}

function safeError(cause: unknown): UiError {
  if (typeof cause === "object" && cause !== null) {
    const record = cause as { message?: unknown; status?: unknown };
    const status = typeof record.status === "number" ? record.status : 0;
    if (status === 503) return { status, message: "Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau." };
    if (typeof record.message === "string" && record.message.trim()) return { status, message: record.message };
  }
  return { status: 0, message: "Không thể tải danh mục SVG lúc này. Hãy thử lại." };
}

function readinessLabel(readiness: string): string {
  if (readiness === "STROKE_READY") return "Có thể tạo guide";
  if (readiness === "REQUIRES_MANUAL_AUTHORING") return "Cần biên soạn thủ công";
  if (readiness === "STATIC_ONLY") return "Chỉ có hình tĩnh";
  return readiness || "Chưa rõ";
}

function reviewLabel(reviewState: string): string {
  if (reviewState === "PENDING_EDUCATOR_REVIEW") return "Chờ giáo viên duyệt";
  if (reviewState === "PENDING_CURATOR_REVIEW") return "Chờ quản trị nội dung";
  if (reviewState === "APPROVED") return "Đã duyệt";
  if (reviewState === "REJECTED") return "Đã từ chối";
  if (reviewState === "ARCHIVED") return "Đã lưu trữ";
  return reviewState || "Chưa rõ";
}

function hashShort(hash: string): string {
  return hash.length > 20 ? hash.slice(0, 16) + "…" : hash;
}

export function TeacherSvgCatalogPage() {
  const organizationId = configuredOrganizationId();
  const [assets, setAssets] = useState<SvgCatalogAssetResponseV1[]>([]);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [revisions, setRevisions] = useState<SvgGuideRevisionReceiptV1[]>([]);
  const [revisionsAssetId, setRevisionsAssetId] = useState<string | null>(null);
  const [loadingAssets, setLoadingAssets] = useState(true);
  const [loadingGuides, setLoadingGuides] = useState(false);
  const [assetError, setAssetError] = useState<UiError | null>(null);
  const [guideError, setGuideError] = useState<UiError | null>(null);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [playingRevisionId, setPlayingRevisionId] = useState<string | null>(null);

  const selectedAsset = useMemo(
    () => assets.find((asset) => asset.catalog_entry_id === selectedAssetId) ?? null,
    [assets, selectedAssetId],
  );
  const currentRevisions = revisionsAssetId === selectedAssetId ? revisions : [];
  const playingRevision = currentRevisions.find((revision) => revision.guide_revision_id === playingRevisionId && revision.review_state === "APPROVED") ?? null;

  const refreshAssets = useCallback(async (showLoading = false) => {
    if (showLoading) setLoadingAssets(true);
    setAssetError(null);
    try {
      const result = await listSvgCatalogAssets(organizationId, { limit: 50 });
      setAssets(result.items);
      setSelectedAssetId((current) => result.items.some((asset) => asset.catalog_entry_id === current)
        ? current
        : result.items[0]?.catalog_entry_id ?? null);
    } catch (cause) {
      setAssetError(safeError(cause));
    } finally {
      if (showLoading) setLoadingAssets(false);
    }
  }, [organizationId]);

  const refreshGuides = useCallback(async (assetId: string, showLoading = false, signal?: AbortSignal) => {
    if (!assetId) {
      setRevisions([]);
      setRevisionsAssetId(null);
      return;
    }
    if (showLoading) setLoadingGuides(true);
    setGuideError(null);
    try {
      const result = await listSvgGuideRevisions(organizationId, assetId, { limit: 50, signal });
      setRevisions(result.items);
      setRevisionsAssetId(assetId);
    } catch (cause) {
      if (signal?.aborted) return;
      setGuideError(safeError(cause));
      setRevisions([]);
      setRevisionsAssetId(null);
    } finally {
      if (showLoading && !signal?.aborted) setLoadingGuides(false);
    }
  }, [organizationId]);

  useEffect(() => {
    void refreshAssets(true);
  }, [refreshAssets]);

  useEffect(() => {
    const unsubscribe = authService.observe((user) => setCurrentUserId(user?.uid ?? null));
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (!selectedAssetId) {
      setRevisions([]);
      setRevisionsAssetId(null);
      setGuideError(null);
      setLoadingGuides(false);
      return;
    }
    const controller = new AbortController();
    void refreshGuides(selectedAssetId, true, controller.signal);
    return () => controller.abort();
  }, [refreshGuides, selectedAssetId]);

  async function handleCreateAsset(body: SvgCatalogAssetCreateRequestV1) {
    const created = await createSvgCatalogAsset(organizationId, body);
    setAssets((current) => [created, ...current.filter((asset) => asset.catalog_entry_id !== created.catalog_entry_id)]);
    setPlayingRevisionId(null);
    setRevisions([]);
    setRevisionsAssetId(null);
    setSelectedAssetId(created.catalog_entry_id);
  }

  async function handleCreateGuide(body: CreateSvgGuideRevisionRequestV1): Promise<SvgGuideRevisionReceiptV1> {
    if (!selectedAsset) throw new Error("Chưa chọn SVG để biên soạn guide.");
    return createSvgGuideRevision(organizationId, selectedAsset.catalog_entry_id, body);
  }

  async function handleGuideCreated(receipt: SvgGuideRevisionReceiptV1) {
    setRevisions((current) => [receipt, ...current.filter((item) => item.guide_revision_id !== receipt.guide_revision_id)]);
    setRevisionsAssetId(selectedAsset?.catalog_entry_id ?? null);
  }

  async function handleSourceReview(body: Parameters<typeof reviewSvgCatalogSource>[2]) {
    if (!selectedAsset) throw new Error("Chưa chọn SVG để đánh giá.");
    const receipt = await reviewSvgCatalogSource(organizationId, selectedAsset.catalog_entry_id, body);
    await refreshAssets();
    return receipt;
  }

  async function handleGuideReview(guideRevisionId: string, body: Parameters<typeof reviewSvgGuide>[3]) {
    if (!selectedAsset) throw new Error("Chưa chọn SVG để đánh giá.");
    const receipt = await reviewSvgGuide(organizationId, selectedAsset.catalog_entry_id, guideRevisionId, body);
    await refreshGuides(selectedAsset.catalog_entry_id);
    return receipt;
  }

  return (
    <main className="s2l-page s2l-data-page" style={{ display: "grid", gap: 24, paddingBottom: 40 }}>
      <header style={{ display: "grid", gap: 8 }}>
        <p style={{ margin: 0, color: "#657467", fontSize: 13, fontWeight: 750, letterSpacing: ".06em", textTransform: "uppercase" }}>Teacher · Học liệu</p>
        <h1 style={{ margin: 0, fontSize: "clamp(28px, 4vw, 38px)", color: "#26372b" }}>Danh mục SVG</h1>
        <p style={{ margin: 0, maxWidth: 760, color: "#5e6d61", fontSize: 16, lineHeight: 1.55 }}>Xem SVG của tổ chức, biên soạn guide có phiên bản và cùng giáo viên khác duyệt trước khi trình chiếu.</p>
        <p style={{ margin: "4px 0 0", padding: "9px 12px", width: "fit-content", border: "1px solid #e0e4d6", borderRadius: 999, background: "#f7f8f2", color: "#69715e", fontSize: 13 }}>Bản nháp AI chưa khả dụng.</p>
      </header>

      {loadingAssets && <p role="status" style={noticeStyle}>Đang tải SVG trong tổ chức…</p>}
      {assetError && (
        <div role="alert" style={{ ...noticeStyle, borderColor: "#e7c3bd", color: "#8a3530" }}>
          <strong>{assetError.status === 503 ? "Dịch vụ đang tạm thời chưa sẵn sàng." : "Chưa thể tải danh mục SVG."}</strong>
          <span>{assetError.message}</span>
          <button type="button" onClick={() => void refreshAssets(true)} style={retryButton}>Thử lại</button>
        </div>
      )}

      {!loadingAssets && !assetError && assets.length === 0 && (
        <p style={noticeStyle}>Chưa có SVG nào trong tổ chức. Bạn có thể thêm SVG nguồn bằng biểu mẫu bên dưới.</p>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 360px), 1fr))", gap: 24, alignItems: "start" }}>
        <SvgAssetList
          assets={assets}
          selectedAssetId={selectedAssetId}
          onSelect={(asset) => {
            setPlayingRevisionId(null);
            setSelectedAssetId(asset.catalog_entry_id);
          }}
          onCreate={handleCreateAsset}
        />

        <section aria-labelledby="svg-asset-detail-heading" style={{ display: "grid", gap: 18, minWidth: 0 }}>
          {!selectedAsset && !loadingAssets && !assetError && (
            <div style={noticeStyle}>
              <h2 style={{ margin: 0, fontSize: 20 }}>Chọn một SVG</h2>
              <p style={{ margin: 0 }}>Chọn SVG trong danh sách để xem guide, đánh giá hoặc biên soạn revision.</p>
            </div>
          )}

          {selectedAsset && (
            <>
              <article style={detailCardStyle}>
                <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 12, alignItems: "start" }}>
                  <div>
                    <p style={{ margin: "0 0 5px", color: "#637468", fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: ".04em" }}>Chi tiết SVG</p>
                    <h2 id="svg-asset-detail-heading" style={{ margin: 0, fontSize: 24 }}>{selectedAsset.title_vi}</h2>
                  </div>
                  <span style={neutralChip}>{reviewLabel(selectedAsset.review_state)}</span>
                </div>
                <p style={{ margin: 0, color: "#55645a", lineHeight: 1.55 }}>{selectedAsset.alt_text_vi}</p>
                <dl style={metadataStyle}>
                  <div><dt>Chủ đề</dt><dd>{selectedAsset.topic_key}</dd></div>
                  <div><dt>Readiness</dt><dd>{readinessLabel(selectedAsset.readiness)}</dd></div>
                  <div><dt>Nguồn</dt><dd><code title={selectedAsset.source_sha256}>{hashShort(selectedAsset.source_sha256)}</code></dd></div>
                  <div><dt>Canonical</dt><dd><code title={selectedAsset.canonical_sha256}>{hashShort(selectedAsset.canonical_sha256)}</code></dd></div>
                  <div><dt>Nguồn</dt><dd><a href={selectedAsset.source_uri} target="_blank" rel="noreferrer">Mở nguồn SVG</a></dd></div>
                  <div><dt>Giấy phép</dt><dd><a href={selectedAsset.license_uri} target="_blank" rel="noreferrer">{selectedAsset.license_id}</a></dd></div>
                  <div><dt>Phạm vi</dt><dd>{selectedAsset.visibility_scope === "ORGANIZATION" ? "Tổ chức" : selectedAsset.visibility_scope === "PLATFORM" ? "Nền tảng" : selectedAsset.visibility_scope}</dd></div>
                </dl>
                {selectedAsset.readiness_reasons.length > 0 && <p style={{ margin: 0, color: "#69766d" }}>Ghi chú readiness: {selectedAsset.readiness_reasons.join(" · ")}</p>}
              </article>

              {loadingGuides && <p role="status" style={noticeStyle}>Đang tải các phiên bản guide…</p>}
              {guideError && (
                <div role="alert" style={{ ...noticeStyle, borderColor: "#e7c3bd", color: "#8a3530" }}>
                  <strong>{guideError.status === 503 ? "Dịch vụ guide đang tạm thời chưa sẵn sàng." : "Chưa thể tải guide."}</strong>
                  <span>{guideError.message}</span>
                  <button type="button" onClick={() => void refreshGuides(selectedAsset.catalog_entry_id, true)} style={retryButton}>Thử lại</button>
                </div>
              )}

              {!loadingGuides && !guideError && (
                <section aria-labelledby="svg-revisions-heading" style={{ display: "grid", gap: 12 }}>
                  <div>
                    <p style={{ margin: "0 0 4px", color: "#637468", fontSize: 13, fontWeight: 700, letterSpacing: ".04em", textTransform: "uppercase" }}>Các phiên bản</p>
                    <h3 id="svg-revisions-heading" style={{ margin: 0, fontSize: 20 }}>Guide revisions</h3>
                  </div>
                  {currentRevisions.length === 0 ? (
                    <p style={{ ...noticeStyle, margin: 0 }}>Chưa có guide revision. Biên soạn guide mới bên dưới.</p>
                  ) : currentRevisions.map((revision) => (
                    <article key={revision.guide_revision_id} style={detailCardStyle}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "start" }}>
                        <div>
                          <strong style={{ fontSize: 17 }}>{revision.guide.title_vi}</strong>
                          <p style={{ margin: "4px 0 0", color: "#657168" }}>Revision {revision.guide_revision} · {revision.guide.stages.length} bước</p>
                        </div>
                        <span style={neutralChip}>{revision.review_state === "PENDING" ? "Chờ giáo viên duyệt" : revision.review_state === "APPROVED" ? "Đã duyệt" : revision.review_state === "REJECTED" ? "Đã từ chối" : revision.review_state}</span>
                      </div>
                      <p style={{ margin: 0, color: "#66736a" }}>SHA-256: <code title={revision.guide_sha256}>{hashShort(revision.guide_sha256)}</code></p>
                      {revision.review_state === "APPROVED" && selectedAsset.document && (
                        <button type="button" onClick={() => setPlayingRevisionId(revision.guide_revision_id)} style={retryButton}>Trình chiếu guide</button>
                      )}
                    </article>
                  ))}
                </section>
              )}

              <SvgGuideReviewPanel
                key={"review-" + selectedAsset.catalog_entry_id}
                asset={selectedAsset}
                revisions={currentRevisions}
                currentUserId={currentUserId}
                onReviewSource={handleSourceReview}
                onReviewGuide={handleGuideReview}
              />

              <SvgGuideAuthoring key={"authoring-" + selectedAsset.catalog_entry_id} asset={selectedAsset} onCreate={handleCreateGuide} onCreated={handleGuideCreated} />
            </>
          )}
        </section>
      </div>

      {playingRevision && selectedAsset?.document && (
        <SvgGuidePlayer
          key={playingRevision.guide_revision_id}
          guide={playingRevision.guide}
          document={selectedAsset.document}
          onClose={() => setPlayingRevisionId(null)}
          onSkip={() => setPlayingRevisionId(null)}
        />
      )}
    </main>
  );
}

const noticeStyle = {
  display: "grid",
  gap: 8,
  margin: 0,
  padding: 16,
  border: "1px solid #d7dfd6",
  borderRadius: 14,
  background: "#f9fbf8",
  color: "#536257",
};

const detailCardStyle = {
  display: "grid",
  gap: 14,
  padding: 18,
  border: "1px solid #d7dfd6",
  borderRadius: 18,
  background: "#fff",
  color: "#28342b",
};

const neutralChip = { display: "inline-flex", border: "1px solid #d7dfd6", borderRadius: 999, padding: "5px 10px", background: "#f0f3f0", color: "#4c574e", fontSize: 12, fontWeight: 700 };
const metadataStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10, margin: 0 };
const retryButton = { justifySelf: "start", border: "1px solid #bdcdbd", borderRadius: 999, padding: "8px 13px", background: "#fff", color: "#2f4535", fontWeight: 700, cursor: "pointer" };
