import { useState } from "react";
import type {
  SvgCatalogAssetResponseV1,
  SvgGuideRevisionReceiptV1,
  SvgGuideReviewRequestV1,
  SvgReviewReceiptV1,
  SvgSourceReviewRequestV1,
} from "../../../shared/api/teacherSvgCatalogApi";
import { Button, FormField } from "../../../shared/ui";
import { FormActionBar } from "./FormActionBar";

export interface SvgGuideReviewPanelProps {
  asset: SvgCatalogAssetResponseV1;
  revisions: SvgGuideRevisionReceiptV1[];
  currentUserId?: string | null;
  onReviewSource: (body: SvgSourceReviewRequestV1) => Promise<SvgReviewReceiptV1>;
  onReviewGuide: (guideRevisionId: string, body: SvgGuideReviewRequestV1) => Promise<SvgReviewReceiptV1>;
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
      setSuccess("Đã ghi nhận đánh giá hướng dẫn.");
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
    <section aria-labelledby="svg-review-heading" className="tp-form-column" style={{ display: "grid", gap: 12 }}>
      <div>
        <p style={{ margin: "0 0 4px", color: "#607064", fontSize: 13, fontWeight: 700, letterSpacing: ".04em", textTransform: "uppercase" }}>Duyệt độc lập</p>
        <h3 id="svg-review-heading" style={{ margin: 0, fontSize: 20 }}>Đánh giá SVG và hướng dẫn</h3>
      </div>

      {sourcePending && (
        <article style={panelStyle}>
          <div className="tw-row tw-between tw-wrap">
            <strong>Nguồn SVG: {asset.title_vi}</strong>
          </div>
          {sourceSelfAuthored ? (
            <p style={{ margin: 0, color: "#647168" }}>Bạn đã tạo SVG này. Hãy nhờ giáo viên khác duyệt.</p>
          ) : (
            <div className="cozy-form-stack">
              <FormField label="Lý do khi từ chối (bắt buộc)" htmlFor="svg-review-source-reason">
                <textarea id="svg-review-source-reason" className="cozy-textarea" rows={3} maxLength={1000} value={sourceReason} onChange={(event) => setSourceReason(event.currentTarget.value)} />
              </FormField>
              <FormActionBar
                danger={<Button type="button" variant="secondary" className="tp-quiet-danger" disabled={busyId !== null} onClick={() => void reviewSource("REJECT")}>Từ chối SVG</Button>}
              >
                <Button type="button" variant="primary" disabled={busyId !== null} onClick={() => void reviewSource("APPROVE")}>Duyệt SVG</Button>
              </FormActionBar>
            </div>
          )}
        </article>
      )}

      {pendingGuides.length === 0 && !sourcePending && <p style={{ ...panelStyle, margin: 0, color: "#647168" }}>Không có mục nào đang chờ giáo viên duyệt.</p>}

      {pendingGuides.map((revision) => {
        const selfAuthored = currentUserId !== undefined && currentUserId !== null && currentUserId === revision.authored_by;
        const reasonInputId = `svg-review-guide-reason-${revision.guide_revision_id}`;
        return (
          <article key={revision.guide_revision_id} style={panelStyle}>
            <div className="tw-row tw-between tw-wrap">
              <strong>{revision.guide.title_vi} · Phiên bản {revision.guide_revision}</strong>
            </div>
            {selfAuthored ? (
              <p style={{ margin: 0, color: "#647168" }}>Bạn đã biên soạn hướng dẫn này. Hãy nhờ giáo viên khác duyệt.</p>
            ) : (
              <div className="cozy-form-stack">
                <FormField label="Lý do khi từ chối (bắt buộc)" htmlFor={reasonInputId}>
                  <textarea id={reasonInputId} className="cozy-textarea" rows={3} maxLength={1000} value={guideReasons[revision.guide_revision_id] ?? ""} onChange={(event) => {
                    const reason = event.currentTarget.value;
                    setGuideReasons((current) => ({ ...current, [revision.guide_revision_id]: reason }));
                  }} />
                </FormField>
                <FormActionBar
                  danger={<Button type="button" variant="secondary" className="tp-quiet-danger" disabled={busyId !== null} onClick={() => void reviewGuide(revision, "REJECT")}>Từ chối hướng dẫn</Button>}
                >
                  <Button type="button" variant="primary" disabled={busyId !== null} onClick={() => void reviewGuide(revision, "APPROVE")}>Duyệt hướng dẫn</Button>
                </FormActionBar>
              </div>
            )}
          </article>
        );
      })}

      {error && <p role="alert" style={{ margin: 0, color: "#a23b37" }}>{error}</p>}
      {success && <p role="status" style={{ margin: 0, color: "var(--s2l-ui-primary-hover)" }}>{success}</p>}
    </section>
  );
}
