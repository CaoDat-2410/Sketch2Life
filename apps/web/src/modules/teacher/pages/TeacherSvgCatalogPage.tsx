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
import { PageHeading } from "../../../shared/components/FeatureAvailability";
import { Button, StatusBadge } from "../../../shared/ui";
import { authService } from "../../school-manager/be1/services/authService";
import { SvgAssetList } from "../components/SvgAssetList";
import { SvgGuideAuthoring } from "../components/SvgGuideAuthoring";
import { SvgGuidePlayer } from "../components/SvgGuidePlayer";
import { SvgGuideReviewPanel } from "../components/SvgGuideReviewPanel";
import { teacherStatusMeta } from "../services/teacherStatus";

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

function scopeLabel(scope: string): string {
  if (scope === "ORGANIZATION") return "Tổ chức";
  if (scope === "PLATFORM") return "Nền tảng";
  return "Phạm vi khác";
}

const READINESS_REASON_COPY: Record<string, string> = {
  PATH_COUNT_BELOW_MIN: "Hình vẽ chưa có đủ nét độc lập để biên soạn hướng dẫn.",
  EDUCATOR_REVIEW_REQUIRED: "Hình vẽ cần được giáo viên duyệt.",
  CURATOR_GROUPING_NOT_ENABLED: "Hình vẽ chưa được cho phép nhóm nét.",
};

function readinessReasonCopy(reasons: string[]): string {
  const knownLabels = reasons
    .filter((reason) => Object.hasOwn(READINESS_REASON_COPY, reason))
    .map((reason) => READINESS_REASON_COPY[reason]);
  if (reasons.some((reason) => !Object.hasOwn(READINESS_REASON_COPY, reason))) {
    knownLabels.push("Một số điều kiện để biên soạn hướng dẫn chưa được đáp ứng.");
  }
  return [...new Set(knownLabels)].join(" · ");
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
    if (!selectedAsset) throw new Error("Chưa chọn SVG để biên soạn hướng dẫn.");
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
    <div className="s2l-page s2l-data-page" style={{ display: "grid", gap: 24, paddingBottom: 40 }}>
      <PageHeading
        eyebrow="Giáo viên · Học liệu"
        title="Danh mục SVG"
        description="Xem hình vẽ SVG của tổ chức, biên soạn hướng dẫn vẽ theo phiên bản và cùng giáo viên khác duyệt trước khi trình chiếu."
      />
      <p style={{ margin: 0 }}><StatusBadge tone="neutral">Bản nháp AI chưa khả dụng.</StatusBadge></p>

      {loadingAssets && <p role="status" style={noticeStyle}>Đang tải danh mục SVG…</p>}
      {assetError && (
        <div role="alert" style={{ ...noticeStyle, borderColor: "#e7c3bd", color: "#8a3530" }}>
          <strong>{assetError.status === 503 ? "Dịch vụ đang tạm thời chưa sẵn sàng." : "Chưa thể tải danh mục SVG."}</strong>
          <span>{assetError.message}</span>
          <div><Button type="button" variant="secondary" size="sm" onClick={() => void refreshAssets(true)}>Thử lại</Button></div>
        </div>
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
              <p style={{ margin: 0 }}>Chọn hình vẽ SVG trong danh sách để xem hướng dẫn, đánh giá hoặc biên soạn phiên bản mới.</p>
            </div>
          )}

          {selectedAsset && (() => {
            const assetReview = teacherStatusMeta(selectedAsset.review_state);
            const assetReadiness = teacherStatusMeta(selectedAsset.readiness);
            return (
              <>
                <article style={detailCardStyle}>
                  <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", gap: 12, alignItems: "start" }}>
                    <div>
                      <h2 id="svg-asset-detail-heading" style={{ margin: 0, fontSize: 24 }}>{selectedAsset.title_vi}</h2>
                    </div>
                    <StatusBadge tone={assetReview.tone}>{assetReview.label}</StatusBadge>
                  </div>
                  <p style={{ margin: 0, color: "var(--s2l-ui-ink-soft)", lineHeight: 1.55 }}>{selectedAsset.alt_text_vi}</p>
                  <dl style={metadataStyle}>
                    <div><dt>Chủ đề</dt><dd>{selectedAsset.topic_key}</dd></div>
                    <div><dt>Mức độ sẵn sàng</dt><dd><StatusBadge tone={assetReadiness.tone}>{assetReadiness.label}</StatusBadge></dd></div>
                    <div><dt>Nguồn</dt><dd><a href={selectedAsset.source_uri} target="_blank" rel="noreferrer">Mở nguồn SVG</a></dd></div>
                    <div><dt>Giấy phép</dt><dd><a href={selectedAsset.license_uri} target="_blank" rel="noreferrer">{selectedAsset.license_id}</a></dd></div>
                    <div><dt>Phạm vi</dt><dd>{scopeLabel(selectedAsset.visibility_scope)}</dd></div>
                  </dl>
                  {selectedAsset.readiness_reasons.length > 0 && <p style={{ margin: 0, color: "var(--s2l-ui-ink-soft)" }}>Ghi chú kiểm tra: {readinessReasonCopy(selectedAsset.readiness_reasons)}</p>}
                </article>

                {loadingGuides && <p role="status" style={noticeStyle}>Đang tải các phiên bản hướng dẫn…</p>}
                {guideError && (
                  <div role="alert" style={{ ...noticeStyle, borderColor: "#e7c3bd", color: "#8a3530" }}>
                    <strong>{guideError.status === 503 ? "Dịch vụ hướng dẫn đang tạm thời chưa sẵn sàng." : "Chưa thể tải hướng dẫn."}</strong>
                    <span>{guideError.message}</span>
                    <div><Button type="button" variant="secondary" size="sm" onClick={() => void refreshGuides(selectedAsset.catalog_entry_id, true)}>Thử lại</Button></div>
                  </div>
                )}

                {!loadingGuides && !guideError && (
                  <section aria-labelledby="svg-revisions-heading" style={{ display: "grid", gap: 12 }}>
                    <div>
                      <h3 id="svg-revisions-heading" style={{ margin: 0, fontSize: 20 }}>Các phiên bản hướng dẫn</h3>
                    </div>
                    {currentRevisions.length === 0 ? (
                      <p style={{ ...noticeStyle, margin: 0 }}>Chưa có phiên bản hướng dẫn. Biên soạn hướng dẫn mới bên dưới.</p>
                    ) : currentRevisions.map((revision) => {
                      const revStatus = teacherStatusMeta(revision.review_state);
                      return (
                        <article key={revision.guide_revision_id} style={detailCardStyle}>
                          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "start" }}>
                            <div>
                              <strong style={{ fontSize: 17 }}>{revision.guide.title_vi}</strong>
                              <p style={{ margin: "4px 0 0", color: "var(--s2l-ui-ink-soft)" }}>Phiên bản {revision.guide_revision} · {revision.guide.stages.length} bước</p>
                            </div>
                            <StatusBadge tone={revStatus.tone}>{revStatus.label}</StatusBadge>
                          </div>
                          {revision.review_state === "APPROVED" && selectedAsset.document && (
                            <div><Button type="button" variant="secondary" size="sm" onClick={() => setPlayingRevisionId(revision.guide_revision_id)}>Trình chiếu hướng dẫn</Button></div>
                          )}
                        </article>
                      );
                    })}
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
            );
          })()}
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
    </div>
  );
}

const noticeStyle = {
  display: "grid",
  gap: 8,
  margin: 0,
  padding: 16,
  border: "1px solid var(--s2l-ui-rule)",
  borderRadius: 16,
  background: "var(--s2l-ui-paper-muted)",
  color: "var(--s2l-ui-ink-soft)",
};

const detailCardStyle = {
  display: "grid",
  gap: 14,
  padding: 18,
  border: "1px solid var(--s2l-ui-rule)",
  borderRadius: 18,
  background: "var(--s2l-ui-paper)",
  color: "var(--s2l-ui-ink)",
};

const metadataStyle = { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: 10, margin: 0 };
