import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type {
  CreateSvgGuideRevisionRequestV1,
  SketchStrokeGuideV3,
  SvgCatalogAssetResponseV1,
  SvgGuideRevisionReceiptV1,
} from "../../../../shared/api/teacherSvgCatalogApi";
import { SvgGuideAuthoring, validateSvgGuideDraft } from "../SvgGuideAuthoring";

afterEach(cleanup);

const asset: SvgCatalogAssetResponseV1 = {
  contract: "SvgCatalogAssetResponseV1",
  catalog_entry_id: "asset-1",
  source_asset_ref: "org/asset-1/source",
  source_asset_version: 2,
  canonical_asset_ref: "org/asset-1/canonical",
  canonical_asset_version: 1,
  source_sha256: "a".repeat(64),
  canonical_sha256: "b".repeat(64),
  topic_key: "animals",
  title_vi: "Con mèo",
  alt_text_vi: "Một con mèo",
  source_uri: "https://example.test/cat.svg",
  license_id: "CC0-1.0",
  license_uri: "https://example.test/license",
  visibility_scope: "ORGANIZATION",
  organization_id: "org-1",
  created_by: "teacher-1",
  readiness: "STROKE_READY",
  readiness_reasons: [],
  structural_facts: {},
  review_state: "APPROVED",
  document: {
    schema_version: "SvgDocumentV1",
    view_box: "0 0 100 100",
    paths: ["p1", "p2", "p3", "p4"].map((path_id) => ({ path_id, d: "M0 0L1 1", fill: "none", stroke: "#333", stroke_width: 1 })),
  },
};

const validGuide = (): SketchStrokeGuideV3 => ({
  schema_version: "SketchStrokeGuideV3",
  guide_id: "cat-guide",
  title_vi: "Vẽ con mèo",
  source_asset_ref: asset.source_asset_ref,
  source_asset_version: asset.source_asset_version,
  source_sha256: asset.source_sha256,
  parts: [{ part_id: "body", label_vi: "Thân", path_ids: ["p1", "p2", "p3", "p4"], depends_on: [] }],
  stages: ["p1", "p2", "p3", "p4"].map((path_id, index) => ({
    step_index: index + 1,
    instruction_vi: "Bước " + (index + 1),
    part_ids: ["body"],
    new_path_ids: [path_id],
    animation_order: [path_id],
  })),
});

const receipt: SvgGuideRevisionReceiptV1 = {
  contract: "SvgGuideRevisionReceiptV1",
  guide_revision_id: "revision-3",
  guide_ref: "org/asset-1/guide",
  guide_revision: 3,
  source_sha256: asset.source_sha256,
  guide_sha256: "c".repeat(64),
  guide: validGuide(),
  authored_by: "teacher-1",
  visibility_scope: "ORGANIZATION",
  organization_id: "org-1",
  review_state: "PENDING",
};

describe("SvgGuideAuthoring", () => {
  it("blocks authoring until the asset is STROKE_READY", () => {
    const onCreate = vi.fn(async (_body: CreateSvgGuideRevisionRequestV1) => receipt);
    render(<SvgGuideAuthoring asset={{ ...asset, readiness: "STATIC_ONLY" }} onCreate={onCreate} />);

    expect(screen.getByRole("status").textContent).toContain("chưa sẵn sàng");
    expect(screen.queryByRole("button", { name: "Lưu phiên bản hướng dẫn" })).toBeNull();
    expect(onCreate).not.toHaveBeenCalled();
  });

  it("validates the 4-to-8 stage range and rejects unknown path ids", () => {
    const guide = validGuide();
    expect(validateSvgGuideDraft(guide, ["p1", "p2", "p3", "p4"])).toBeNull();
    expect(validateSvgGuideDraft({ ...guide, stages: guide.stages.slice(0, 3) }, ["p1", "p2", "p3", "p4"])).toContain("4 đến 8");
    expect(validateSvgGuideDraft({ ...guide, stages: [...guide.stages, ...guide.stages, guide.stages[0]].map((stage, index) => ({ ...stage, step_index: index + 1 })) }, ["p1", "p2", "p3", "p4"])).toContain("4 đến 8");
    const unknown = validGuide();
    unknown.stages[0] = { ...unknown.stages[0], new_path_ids: ["unknown"], animation_order: ["unknown"] };
    expect(validateSvgGuideDraft(unknown, ["p1", "p2", "p3", "p4"])).toContain("không tồn tại");
  });

  it("submits a validated guide pinned to the asset and shows the pending receipt", async () => {
    const onCreate = vi.fn(async (_body: CreateSvgGuideRevisionRequestV1) => receipt);
    render(<SvgGuideAuthoring asset={asset} onCreate={onCreate} />);

    screen.getAllByLabelText("Hướng dẫn tiếng Việt").forEach((control, index) => {
      fireEvent.change(control, { target: { value: "Bước " + (index + 1) } });
    });
    screen.getAllByLabelText("Nét mới ở bước này").forEach((control, index) => {
      const select = control as HTMLSelectElement;
      [...select.options].forEach((option) => { option.selected = option.value === "p" + (index + 1); });
      fireEvent.change(select);
    });

    fireEvent.click(screen.getByRole("button", { name: "Lưu phiên bản hướng dẫn" }));
    expect((await screen.findByRole("status")).textContent).toContain("Đã tạo phiên bản 3");
    expect(screen.queryByText("Chờ giáo viên duyệt")).toBeNull();
    expect(onCreate).toHaveBeenCalledOnce();
    const body = onCreate.mock.calls[0][0];
    expect(body.contract).toBe("CreateSvgGuideRevisionRequestV1");
    expect(body.guide.source_asset_ref).toBe(asset.source_asset_ref);
    expect(body.guide.source_asset_version).toBe(asset.source_asset_version);
    expect(body.guide.source_sha256).toBe(asset.source_sha256);
    expect(body.guide.stages).toHaveLength(4);
    expect(body.guide.stages[0].animation_order).toEqual(["p1"]);
  });
});
