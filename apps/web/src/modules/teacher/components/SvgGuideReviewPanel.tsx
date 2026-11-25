import { useState } from "react";
import type {
  SvgCatalogAssetResponseV1,
  SvgGuideRevisionReceiptV1,
  SvgGuideReviewRequestV1,
  SvgReviewReceiptV1,
  SvgSourceReviewRequestV1,
} from "../../../shared/api/teacherSvgCatalogApi";

export interface SvgGuideReviewPanelProps {
  asset: SvgCatalogAssetResponseV1;
  revisions: SvgGuideRevisionReceiptV1[];
  currentUserId?: string | null;
  onReviewSource: (body: SvgSourceReviewRequestV1) => Promise<SvgReviewReceiptV1>;
  onReviewGuide: (guideRevisionId: string, body: SvgGuideReviewRequestV1) => Promise<SvgReviewReceiptV1>;
}

function shortHash(value: string): string {
  return value.length <= 16 ? value : value.slice(0, 12) + "…";
}

function reviewError(cause: unknown): string {
  if (typeof cause === "object" && cause !== null && "code" in cause && cause.code === "INDEPENDENT_REVIEW_REQUIRED") {
    return "Người tạo nội dung không thể tự duyệt. Hãy nhờ một giáo viên khác.";
  }
  return cause instanceof Error ? cause.message : "Không thể ghi nhận đánh giá lúc này.";
}

function rejectReasonError(reason: string): string | null {
  if (!reason.trim()) return "Cần nhập lý do trước khi từ chối.";
  if (reason.trim().length > 1000) return "Lý do không được vượt quá 1.000 ký tự.";
  return null;
}

const panelStyle = {
  display: "grid",
  gap: 12,
  padding: 16,
  border: "1px solid #d7dfd6",
  borderRadius: 16,
  background: "#fff",
  color: "#28342b",
};

const buttonStyle = {
  border: "1px solid #bdcdbd",
  borderRadius: 999,
  padding: "8px 14px",
  background: "#f7faf6",
  color: "#2f4535",
  fontWeight: 700,
  cursor: "pointer",
};

export function SvgGuideReviewPanel({
  asset,
  revisions,
  currentUserId,
  onReviewSource,
  onReviewGuide,
}: SvgGuideReviewPanelProps) {
  const [sourceReason, setSourceReason] = useState("");
  const [guideReasons, setGuideReasons] = useState<Record<string, string>>({});
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function reviewSource(decision: "APPROVE" | "REJECT") {
    if (decision === "REJECT") {
      const invalid = rejectReasonError(sourceReason);
      if (invalid) {
        setError(invalid);
        setSuccess(null);
        return;
      }
    }
    setBusyId("source");
    setError(null);
    setSuccess(null);
    try {
      await onReviewSource({
        contract: "SvgSourceReviewRequestV1",
        source_sha256: asset.source_sha256,
        decision,
        ...(decision === "REJECT" ? { reason: sourceReason.trim() } : {}),
      });
      setSuccess("Đã ghi nhận đánh giá SVG.");
      setSourceReason("");
    } catch (cause) {
      setError(reviewError(cause));
    } finally {
      setBusyId(null);
    }
  }

  async function reviewGuide(revision: SvgGuideRevisionReceiptV1, decision: "APPROVE" | "REJECT") {
    const reason = guideReasons[revision.guide_revision_id] ?? "";
    if (decision === "REJECT") {
      const invalid = rejectReasonError(reason);
      if (invalid) {
        setError(invalid);
        setSuccess(null);
        return;
      }
    }
    setBusyId(revision.guide_revision_id);
    setError(null);
    setSuccess(null);
    try {
      await onReviewGuide(revision.guide_revision_id, {
        contract: "SvgGuideReviewRequestV1",
        source_sha256: revision.source_sha256,
        guide_sha256: revision.guide_sha256,
        decision,
        ...(decision === "REJECT" ? { reason: reason.trim() } : {}),
      });
      setSuccess("Đã ghi nhận đánh giá guide.");
      setGuideReasons((current) => ({ ...current, [revision.guide_revision_id]: "" }));
    } catch (cause) {
      setError(reviewError(cause));
    } finally {
      setBusyId(null);
    }
  }

  const sourcePending = asset.review_state === "PENDING_EDUCATOR_REVIEW";
  const sourceSelfAuthored = currentUserId !== undefined && currentUserId !== null && currentUserId === asset.created_by;
  const pendingGuides = revisions.filter((revision) => revision.review_state === "PENDING");

  return (
    <section aria-labelledby="svg-review-heading" style={{ display: "grid", gap: 12 }}>
      <div>
        <p style={{ margin: "0 0 4px", color: "#607064", fontSize: 13, fontWeight: 700, letterSpacing: ".04em", textTransform: "uppercase" }}>Duyệt độc lập</p>
        <h3 id="svg-review-heading" style={{ margin: 0, fontSize: 20 }}>Đánh giá SVG và guide</h3>
      </div>

      {sourcePending && (
        <article style={panelStyle}>
          <strong>Nguồn SVG · chờ giáo viên duyệt</strong>
          <span>Mã nguồn: <code title={asset.source_sha256}>{shortHash(asset.source_sha256)}</code></span>
          {sourceSelfAuthored ? (
            <p style={{ margin: 0, color: "#647168" }}>Bạn đã tạo SVG này. Hãy nhờ giáo viên khác duyệt.</p>
          ) : (
            <>
              <label style={{ display: "grid", gap: 6 }}>
                Lý do khi từ chối (bắt buộc)
                <textarea maxLength={1000} value={sourceReason} onChange={(event) => setSourceReason(event.currentTarget.value)} style={textareaStyle} />
              </label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                <button type="button" disabled={busyId !== null} onClick={() => void reviewSource("APPROVE")} style={buttonStyle}>Duyệt SVG</button>
                <button type="button" disabled={busyId !== null} onClick={() => void reviewSource("REJECT")} style={buttonStyle}>Từ chối SVG</button>
              </div>
            </>
          )}
        </article>
      )}

      {pendingGuides.length === 0 && !sourcePending && <p style={{ ...panelStyle, margin: 0, color: "#647168" }}>Không có mục nào đang chờ giáo viên duyệt.</p>}

      {pendingGuides.map((revision) => {
        const selfAuthored = currentUserId !== undefined && currentUserId !== null && currentUserId === revision.authored_by;
        return (
          <article key={revision.guide_revision_id} style={panelStyle}>
            <strong>{revision.guide.title_vi} · revision {revision.guide_revision} · chờ duyệt</strong>
            <span>Mã SVG: <code title={revision.source_sha256}>{shortHash(revision.source_sha256)}</code></span>
            <span>Mã guide: <code title={revision.guide_sha256}>{shortHash(revision.guide_sha256)}</code></span>
            {selfAuthored ? (
              <p style={{ margin: 0, color: "#647168" }}>Bạn đã biên soạn guide này. Hãy nhờ giáo viên khác duyệt.</p>
            ) : (
              <>
                <label style={{ display: "grid", gap: 6 }}>
                  Lý do khi từ chối (bắt buộc)
                  <textarea maxLength={1000} value={guideReasons[revision.guide_revision_id] ?? ""} onChange={(event) => {
                    const reason = event.currentTarget.value;
                    setGuideReasons((current) => ({ ...current, [revision.guide_revision_id]: reason }));
                  }} style={textareaStyle} />
                </label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  <button type="button" disabled={busyId !== null} onClick={() => void reviewGuide(revision, "APPROVE")} style={buttonStyle}>Duyệt guide</button>
                  <button type="button" disabled={busyId !== null} onClick={() => void reviewGuide(revision, "REJECT")} style={buttonStyle}>Từ chối guide</button>
                </div>
              </>
            )}
          </article>
        );
      })}

      {error && <p role="alert" style={{ margin: 0, color: "#a23b37" }}>{error}</p>}
      {success && <p role="status" style={{ margin: 0, color: "#315f42" }}>{success}</p>}
    </section>
  );
}

const textareaStyle = {
  width: "100%",
  boxSizing: "border-box" as const,
  minHeight: 72,
  resize: "vertical" as const,
  border: "1px solid #cbd5cb",
  borderRadius: 10,
  padding: "9px 11px",
  font: "inherit",
};
