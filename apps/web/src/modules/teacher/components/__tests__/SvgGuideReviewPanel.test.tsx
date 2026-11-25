import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type {
  SvgCatalogAssetResponseV1,
  SvgGuideRevisionReceiptV1,
  SvgReviewReceiptV1,
} from "../../../../shared/api/teacherSvgCatalogApi";
import { SvgGuideReviewPanel } from "../SvgGuideReviewPanel";

afterEach(cleanup);

const asset: SvgCatalogAssetResponseV1 = {
  contract: "SvgCatalogAssetResponseV1",
  catalog_entry_id: "asset-1",
  source_asset_ref: "source/asset-1",
  source_asset_version: 1,
  canonical_asset_ref: "canonical/asset-1",
  canonical_asset_version: 1,
  source_sha256: "a".repeat(64),
  canonical_sha256: "b".repeat(64),
  topic_key: "animals",
  title_vi: "Con mèo",
  alt_text_vi: "Một con mèo",
  source_uri: "https://example.test/cat.svg",
  license_id: "CC0",
  license_uri: "https://example.test/license",
  visibility_scope: "ORGANIZATION",
  organization_id: "org-1",
  created_by: "teacher-1",
  readiness: "STROKE_READY",
  readiness_reasons: [],
  structural_facts: {},
  review_state: "APPROVED",
  document: null,
};

const guideRevision: SvgGuideRevisionReceiptV1 = {
  contract: "SvgGuideRevisionReceiptV1",
  guide_revision_id: "guide-rev-1",
  guide_ref: "guide/1",
  guide_revision: 1,
  source_sha256: asset.source_sha256,
  guide_sha256: "c".repeat(64),
  guide: {
    schema_version: "SketchStrokeGuideV3",
    guide_id: "cat-guide",
    title_vi: "Vẽ con mèo",
    source_asset_ref: asset.source_asset_ref,
    source_asset_version: 1,
    source_sha256: asset.source_sha256,
    parts: [{ part_id: "body", label_vi: "Thân", path_ids: ["p1"], depends_on: [] }],
    stages: [
      { step_index: 1, instruction_vi: "Bước 1", part_ids: ["body"], new_path_ids: ["p1"], animation_order: ["p1"] },
      { step_index: 2, instruction_vi: "Bước 2", part_ids: ["body"], new_path_ids: ["p1"], animation_order: ["p1"] },
      { step_index: 3, instruction_vi: "Bước 3", part_ids: ["body"], new_path_ids: ["p1"], animation_order: ["p1"] },
      { step_index: 4, instruction_vi: "Bước 4", part_ids: ["body"], new_path_ids: ["p1"], animation_order: ["p1"] },
    ],
  },
  authored_by: "teacher-1",
  visibility_scope: "ORGANIZATION",
  organization_id: "org-1",
  review_state: "PENDING",
};

const reviewReceipt: SvgReviewReceiptV1 = {
  contract: "SvgReviewReceiptV1",
  review_id: "review-1",
  catalog_entry_id: asset.catalog_entry_id,
  review_subject_kind: "GUIDE",
  review_kind: "EDUCATOR",
  decision: "REJECT",
  source_sha256: asset.source_sha256,
  guide_sha256: guideRevision.guide_sha256,
  grouping_allowed: false,
  reviewer_ref: "teacher-2",
  created_at: "2026-11-25T00:00:00Z",
};

describe("SvgGuideReviewPanel", () => {
  it("requires a reason before rejecting and sends both stored hashes", async () => {
    const onReviewGuide = vi.fn(async () => reviewReceipt);
    render(
      <SvgGuideReviewPanel
        asset={asset}
        revisions={[guideRevision]}
        currentUserId="teacher-2"
        onReviewSource={vi.fn(async () => reviewReceipt)}
        onReviewGuide={onReviewGuide}
      />,
    );

    expect(screen.getByText("Mã SVG:")).toBeTruthy();
    expect(screen.getByText("Mã guide:")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Từ chối guide" }));
    expect(screen.getByRole("alert").textContent).toContain("Cần nhập lý do");
    expect(onReviewGuide).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Lý do khi từ chối (bắt buộc)"), { target: { value: "Cần sửa thứ tự nét." } });
    fireEvent.click(screen.getByRole("button", { name: "Từ chối guide" }));
    expect(await screen.findByRole("status")).toBeTruthy();
    expect(onReviewGuide).toHaveBeenCalledWith(guideRevision.guide_revision_id, {
      contract: "SvgGuideReviewRequestV1",
      source_sha256: guideRevision.source_sha256,
      guide_sha256: guideRevision.guide_sha256,
      decision: "REJECT",
      reason: "Cần sửa thứ tự nét.",
    });
  });

  it("hides source and guide review actions from their creator", () => {
    const ownAsset = { ...asset, review_state: "PENDING_EDUCATOR_REVIEW" };
    render(
      <SvgGuideReviewPanel
        asset={ownAsset}
        revisions={[guideRevision]}
        currentUserId="teacher-1"
        onReviewSource={vi.fn(async () => reviewReceipt)}
        onReviewGuide={vi.fn(async () => reviewReceipt)}
      />,
    );
    expect(screen.queryByRole("button", { name: "Duyệt SVG" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Từ chối SVG" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Duyệt guide" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Từ chối guide" })).toBeNull();
    expect(screen.getByText(/Bạn đã tạo SVG này/)).toBeTruthy();
    expect(screen.getByText(/Bạn đã biên soạn guide này/)).toBeTruthy();
  });

  it("shows a clear independent-review message when the server rejects a self-review", async () => {
    const onReviewGuide = vi.fn(async () => {
      throw Object.assign(new Error("forbidden"), { code: "INDEPENDENT_REVIEW_REQUIRED" });
    });
    render(
      <SvgGuideReviewPanel
        asset={asset}
        revisions={[guideRevision]}
        currentUserId="another-teacher"
        onReviewSource={vi.fn(async () => reviewReceipt)}
        onReviewGuide={onReviewGuide}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Duyệt guide" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Người tạo nội dung không thể tự duyệt");
  });
});
