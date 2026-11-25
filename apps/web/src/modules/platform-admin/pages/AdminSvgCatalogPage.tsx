import { useState, type FormEvent, type ReactNode } from "react";
import { Button, Field, Heading } from "../components/AdminUI";
import {
  createSvgCatalogAsset,
  createSvgGuideRevision,
  curateSvgCatalogAsset,
  svgCatalogAdminErrorMessage,
  validateSvgGuideRequest,
  type CreateSvgGuideRevisionRequestV1,
  type SvgCatalogAssetCreateRequestV1,
  type SvgCatalogAssetResponseV1,
  type SvgCurationDecision,
  type SvgCurationRequestV1,
  type SvgDocumentV1,
  type SvgGuideRevisionReceiptV1,
  type SvgReviewReceiptV1,
  type SketchStrokeGuideV3,
} from "../services/svgCatalogAdminService";
import "../styles/admin-svg-catalog.css";

const emptyAsset: SvgCatalogAssetCreateRequestV1 = {
  contract: "SvgCatalogAssetCreateRequestV1",
  title_vi: "",
  topic_key: "",
  alt_text_vi: "",
  source_uri: "",
  license_id: "",
  license_uri: "",
  source_svg: "",
};

function errorMessage(error: unknown) {
  if (error instanceof Error && !("code" in error)) return error.message;
  return svgCatalogAdminErrorMessage(error);
}

function stateLabel(value: string) {
  const labels: Record<string, string> = {
    STROKE_READY: "Sẵn sàng tạo hướng dẫn",
    REQUIRES_MANUAL_AUTHORING: "Cần biên tập thủ công",
    STATIC_ONLY: "Chỉ dùng hình tĩnh",
    PENDING_EDUCATOR_REVIEW: "Chờ giáo viên duyệt",
    PENDING_CURATOR_REVIEW: "Chờ quản trị viên duyệt",
    PENDING: "Chờ duyệt",
    APPROVED: "Đã chấp thuận",
    REJECTED: "Đã từ chối",
    ARCHIVED: "Đã lưu trữ",
  };
  return labels[value] ?? "Trạng thái khác";
}

function SvgState({ value }: { value: string }) {
  return <span className="pa-svg-chip">{stateLabel(value)}</span>;
}

function safeViewBox(value: string) {
  const number = "-?(?:\\d+\\.?\\d*|\\.\\d+)(?:[eE][+-]?\\d+)?";
  return new RegExp(`^\\s*${number}[\\s,]+${number}[\\s,]+${number}[\\s,]+${number}\\s*$`).test(value)
    ? value
    : "0 0 100 100";
}

function safePaint(value: string | null) {
  if (!value) return undefined;
  return /^(?:none|currentColor|#[\da-fA-F]{3,8}|[a-zA-Z]{1,30})$/.test(value) ? value : undefined;
}

function SvgPreview({ document }: { document: SvgDocumentV1 | null }) {
  if (!document) return <p className="pa-muted">Chưa có bản xem trước cho mục này.</p>;
  return (
    <div className="pa-svg-preview" aria-label="Bản xem trước SVG">
      <svg viewBox={safeViewBox(document.view_box)} role="img" aria-label="Hình SVG đã chuẩn hóa">
        {(Array.isArray(document.paths) ? document.paths : []).map((path, index) => (
          <path
            key={`${path.path_id}-${index}`}
            d={typeof path.d === "string" ? path.d : ""}
            fill={safePaint(path.fill) ?? "none"}
            stroke={safePaint(path.stroke) ?? "currentColor"}
            strokeWidth={typeof path.stroke_width === "number" && Number.isFinite(path.stroke_width) ? Math.max(0, Math.min(path.stroke_width, 1000)) : 1.5}
          />
        ))}
      </svg>
    </div>
  );
}

function Receipt({ title, value }: { title: string; value: ReactNode }) {
  return (
    <div className="pa-svg-receipt" role="status">
      <strong>{title}</strong>
      {value}
    </div>
  );
}

export function AdminSvgCatalogPage() {
  const [assetForm, setAssetForm] = useState(emptyAsset);
  const [assetBusy, setAssetBusy] = useState(false);
  const [assetError, setAssetError] = useState("");
  const [assetReceipt, setAssetReceipt] = useState<SvgCatalogAssetResponseV1 | null>(null);
  const [catalogEntryId, setCatalogEntryId] = useState("");

  const [guideJson, setGuideJson] = useState("");
  const [guideBusy, setGuideBusy] = useState(false);
  const [guideError, setGuideError] = useState("");
  const [guideReceipt, setGuideReceipt] = useState<SvgGuideRevisionReceiptV1 | null>(null);

  const [sourceSha256, setSourceSha256] = useState("");
  const [decision, setDecision] = useState<SvgCurationDecision>("APPROVE");
  const [groupingAllowed, setGroupingAllowed] = useState(false);
  const [reason, setReason] = useState("");
  const [curationBusy, setCurationBusy] = useState(false);
  const [curationError, setCurationError] = useState("");
  const [curationReceipt, setCurationReceipt] = useState<SvgReviewReceiptV1 | null>(null);

  async function submitAsset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAssetBusy(true);
    setAssetError("");
    setAssetReceipt(null);
    try {
      const result = await createSvgCatalogAsset(assetForm);
      setAssetReceipt(result);
      setCatalogEntryId(result.catalog_entry_id);
      setSourceSha256(result.source_sha256);
    } catch (error) {
      setAssetError(errorMessage(error));
    } finally {
      setAssetBusy(false);
    }
  }

  async function submitGuide(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setGuideBusy(true);
    setGuideError("");
    setGuideReceipt(null);
    try {
      const guide = JSON.parse(guideJson) as SketchStrokeGuideV3;
      const body: CreateSvgGuideRevisionRequestV1 = { contract: "CreateSvgGuideRevisionRequestV1", guide };
      validateSvgGuideRequest(body);
      if (assetReceipt && catalogEntryId.trim() === assetReceipt.catalog_entry_id && (
        guide.source_asset_ref !== assetReceipt.source_asset_ref
        || guide.source_asset_version !== assetReceipt.source_asset_version
        || guide.source_sha256 !== assetReceipt.source_sha256
      )) {
        setGuideError(svgCatalogAdminErrorMessage({ code: "SVG_GUIDE_SOURCE_MISMATCH" }));
        return;
      }
      const result = await createSvgGuideRevision(catalogEntryId.trim(), body);
      setGuideReceipt(result);
    } catch (error) {
      setGuideError(error instanceof SyntaxError ? "Nội dung hướng dẫn cần là JSON hợp lệ." : errorMessage(error));
    } finally {
      setGuideBusy(false);
    }
  }

  async function submitCuration(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCurationBusy(true);
    setCurationError("");
    setCurationReceipt(null);
    const body: SvgCurationRequestV1 = {
      contract: "SvgCurationRequestV1",
      source_sha256: sourceSha256.trim(),
      decision,
      grouping_allowed: groupingAllowed,
      ...(reason.trim() ? { reason: reason.trim() } : {}),
    };
    try {
      const result = await curateSvgCatalogAsset(catalogEntryId.trim(), body);
      setCurationReceipt(result);
    } catch (error) {
      setCurationError(errorMessage(error));
    } finally {
      setCurationBusy(false);
    }
  }

  return (
    <div className="pa-page pa-svg-catalog">
      <Heading title="Danh mục SVG" description="Tạo tài sản SVG, hướng dẫn nét vẽ và ghi nhận quyết định của quản trị viên nền tảng." />

      <aside className="pa-panel pa-padded pa-svg-catalog-note">
        <strong>Phạm vi quản trị</strong>
        <p>Quản trị viên chỉ có thể tạo mục SVG, tạo phiên bản hướng dẫn và duyệt mục bằng mã mục đang có. Màn hình không có danh sách tra cứu SVG. Giáo viên thực hiện các lượt duyệt của nhà giáo dục.</p>
      </aside>

      <section className="pa-panel pa-padded grid gap-4" aria-labelledby="pa-svg-create-title">
        <div>
          <h2 id="pa-svg-create-title" className="m-0">Tạo mục SVG</h2>
          <p className="pa-muted mt-1">Nhập nguồn và thông tin giấy phép. Nội dung được gửi dưới dạng dữ liệu SVG.</p>
        </div>
        <form className="pa-form grid gap-4" onSubmit={submitAsset}>
          <div className="pa-form-grid">
            <Field label="Tiêu đề tiếng Việt"><input required minLength={1} maxLength={300} value={assetForm.title_vi} onChange={(event) => setAssetForm({ ...assetForm, title_vi: event.target.value })} /></Field>
            <Field label="Mã chủ đề"><input required minLength={1} maxLength={120} pattern="[a-z0-9-]+" value={assetForm.topic_key} onChange={(event) => setAssetForm({ ...assetForm, topic_key: event.target.value })} /></Field>
            <Field label="Văn bản thay thế"><input required minLength={1} maxLength={500} value={assetForm.alt_text_vi} onChange={(event) => setAssetForm({ ...assetForm, alt_text_vi: event.target.value })} /></Field>
            <Field label="Mã giấy phép"><input required minLength={1} maxLength={120} value={assetForm.license_id} onChange={(event) => setAssetForm({ ...assetForm, license_id: event.target.value })} /></Field>
            <Field label="Đường dẫn nguồn HTTPS"><input required type="url" maxLength={2048} value={assetForm.source_uri} onChange={(event) => setAssetForm({ ...assetForm, source_uri: event.target.value })} /></Field>
            <Field label="Đường dẫn giấy phép HTTPS"><input required type="url" maxLength={2048} value={assetForm.license_uri} onChange={(event) => setAssetForm({ ...assetForm, license_uri: event.target.value })} /></Field>
          </div>
          <Field label="Mã SVG nguồn" hint="Tối đa 1.000.000 ký tự.">
            <textarea required minLength={1} maxLength={1_000_000} rows={10} spellCheck={false} value={assetForm.source_svg} onChange={(event) => setAssetForm({ ...assetForm, source_svg: event.target.value })} />
          </Field>
          {assetError && <p className="pa-svg-error" role="alert">{assetError}</p>}
          <Button primary type="submit" disabled={assetBusy}>{assetBusy ? "Đang tạo…" : "Tạo mục SVG"}</Button>
        </form>
        {assetReceipt && <AssetResult asset={assetReceipt} />}
      </section>

      <section className="pa-panel pa-padded grid gap-4" aria-labelledby="pa-svg-guide-title">
        <div>
          <h2 id="pa-svg-guide-title" className="m-0">Tạo phiên bản hướng dẫn</h2>
          <p className="pa-muted mt-1">Dán mã mục từ kết quả vừa tạo hoặc nhập mã mục đã được cung cấp. Mã nguồn, phiên bản và mã băm trong hướng dẫn phải khớp chính xác tài sản.</p>
        </div>
        <form className="pa-form grid gap-4" onSubmit={submitGuide}>
          <Field label="Mã mục SVG"><input required value={catalogEntryId} onChange={(event) => setCatalogEntryId(event.target.value)} /></Field>
          <Field label="Nội dung hướng dẫn JSON" hint="Dùng schema_version SketchStrokeGuideV3, từ 1 đến 64 phần và từ 4 đến 8 bước.">
            <textarea required rows={16} spellCheck={false} value={guideJson} onChange={(event) => setGuideJson(event.target.value)} />
          </Field>
          {guideError && <p className="pa-svg-error" role="alert">{guideError}</p>}
          <Button primary type="submit" disabled={guideBusy || !catalogEntryId.trim()}>{guideBusy ? "Đang lưu…" : "Tạo phiên bản hướng dẫn"}</Button>
        </form>
        {guideReceipt && (
          <Receipt title="Đã tạo phiên bản hướng dẫn" value={<dl><dt>Mã hướng dẫn</dt><dd>{guideReceipt.guide_revision_id}</dd><dt>Phiên bản</dt><dd>{guideReceipt.guide_revision}</dd><dt>Trạng thái</dt><dd><SvgState value={guideReceipt.review_state} /></dd><dt>Mã băm hướng dẫn</dt><dd className="pa-svg-hash">{guideReceipt.guide_sha256}</dd></dl>} />
        )}
      </section>

      <section className="pa-panel pa-padded grid gap-4" aria-labelledby="pa-svg-curation-title">
        <div>
          <h2 id="pa-svg-curation-title" className="m-0">Duyệt mục SVG</h2>
          <p className="pa-muted mt-1">Chỉ người không tạo ra mục SVG mới có thể ghi nhận quyết định duyệt.</p>
        </div>
        <form className="pa-form grid gap-4" onSubmit={submitCuration}>
          <div className="pa-form-grid">
            <Field label="Mã mục SVG"><input required value={catalogEntryId} onChange={(event) => setCatalogEntryId(event.target.value)} /></Field>
            <Field label="Mã băm nguồn SHA-256"><input required pattern="[a-fA-F0-9]{64}" maxLength={64} value={sourceSha256} onChange={(event) => setSourceSha256(event.target.value)} /></Field>
            <Field label="Quyết định">
              <select value={decision} onChange={(event) => { const value = event.target.value as SvgCurationDecision; setDecision(value); if (value === "REJECT") setGroupingAllowed(false); }}>
                <option value="APPROVE">Chấp thuận</option>
                <option value="REJECT">Từ chối</option>
              </select>
            </Field>
            <Field label="Quyền nhóm nét">
              <label className="pa-svg-checkbox"><input type="checkbox" checked={groupingAllowed} disabled={decision !== "APPROVE"} onChange={(event) => setGroupingAllowed(event.target.checked)} /> Cho phép nhóm nét tự động</label>
            </Field>
          </div>
          <Field label="Lý do từ chối" hint="Bắt buộc khi từ chối; tối đa 1000 ký tự.">
            <textarea maxLength={1000} required={decision === "REJECT"} rows={3} value={reason} onChange={(event) => setReason(event.target.value)} />
          </Field>
          {curationError && <p className="pa-svg-error" role="alert">{curationError}</p>}
          <Button primary type="submit" disabled={curationBusy || !catalogEntryId.trim()}>{curationBusy ? "Đang ghi nhận…" : "Ghi nhận quyết định"}</Button>
        </form>
        {curationReceipt && (
          <Receipt title="Đã ghi nhận quyết định duyệt" value={<dl><dt>Mã biên nhận</dt><dd>{curationReceipt.review_id}</dd><dt>Quyết định</dt><dd>{curationReceipt.decision === "APPROVE" ? "Chấp thuận" : "Từ chối"}</dd><dt>Người duyệt</dt><dd>{curationReceipt.reviewer_ref}</dd><dt>Thời điểm</dt><dd>{curationReceipt.created_at}</dd><dt>Cho phép nhóm nét</dt><dd>{curationReceipt.grouping_allowed ? "Có" : "Không"}</dd></dl>} />
        )}
      </section>
    </div>
  );
}

function AssetResult({ asset }: { asset: SvgCatalogAssetResponseV1 }) {
  return (
    <article className="pa-svg-asset-result">
      <div className="pa-svg-result-heading">
        <div><h3>{asset.title_vi}</h3><code>{asset.catalog_entry_id}</code></div>
        <div className="pa-svg-chips"><SvgState value={asset.readiness} /><SvgState value={asset.review_state} /></div>
      </div>
      <p>{asset.alt_text_vi}</p>
      <dl className="pa-svg-result-data">
        <dt>Mã nguồn</dt><dd>{asset.source_asset_ref} · phiên bản {asset.source_asset_version}</dd>
        <dt>Mã băm nguồn</dt><dd className="pa-svg-hash">{asset.source_sha256}</dd>
        <dt>Phạm vi hiển thị</dt><dd>{asset.visibility_scope === "PLATFORM" ? "Toàn nền tảng" : "Trong tổ chức"}</dd>
        <dt>Số nét</dt><dd>{asset.document?.paths.length ?? 0}</dd>
      </dl>
      {asset.readiness_reasons.length > 0 && <p className="pa-muted">Có {asset.readiness_reasons.length} lưu ý về khả năng tạo hướng dẫn.</p>}
      <SvgPreview document={asset.document} />
    </article>
  );
}
