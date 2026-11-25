import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  SvgCatalogAssetResponseV1,
  SvgGuideRevisionReceiptV1,
} from "../../../../shared/api/teacherSvgCatalogApi";
import { TeacherSvgCatalogPage } from "../TeacherSvgCatalogPage";

const api = vi.hoisted(() => ({
  listSvgCatalogAssets: vi.fn(),
  createSvgCatalogAsset: vi.fn(),
  listSvgGuideRevisions: vi.fn(),
  createSvgGuideRevision: vi.fn(),
  reviewSvgCatalogSource: vi.fn(),
  reviewSvgGuide: vi.fn(),
}));

vi.mock("../../../../shared/api/teacherSvgCatalogApi", () => api);
vi.mock("../../../school-manager/be1/services/authService", () => ({
  authService: {
    observe: (callback: (user: { uid: string } | null) => void) => {
      callback({ uid: "teacher-reviewer" });
      return () => undefined;
    },
  },
}));

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
  created_by: "teacher-author",
  readiness: "STROKE_READY",
  readiness_reasons: [],
  structural_facts: {},
  review_state: "APPROVED",
  document: {
    schema_version: "SvgDocumentV1",
    view_box: "0 0 100 100",
    paths: ["p1", "p2", "p3", "p4"].map((path_id) => ({ path_id, d: "M 0 0 L 10 10", fill: "none", stroke: "#333", stroke_width: 2 })),
  },
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
  },
  authored_by: "teacher-author",
  visibility_scope: "ORGANIZATION",
  organization_id: "org-1",
  review_state: "APPROVED",
};

beforeEach(() => {
  window.sketch2lifeConfig = { apiBaseUrl: "https://api.example.test", organizationId: "org-1" };
  api.listSvgCatalogAssets.mockResolvedValue({ items: [asset] });
  api.listSvgGuideRevisions.mockResolvedValue({ items: [guideRevision] });
  api.createSvgCatalogAsset.mockReset();
  api.createSvgGuideRevision.mockReset();
  api.reviewSvgCatalogSource.mockReset();
  api.reviewSvgGuide.mockReset();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  window.sketch2lifeConfig = undefined;
});

describe("TeacherSvgCatalogPage", () => {
  it("loads the organization catalog, presents an approved guide, and makes no AI call", async () => {
    render(<TeacherSvgCatalogPage />);
    expect(await screen.findByRole("heading", { name: "Danh mục SVG" })).toBeTruthy();
    expect(await screen.findByText("Revision 1 · 4 bước")).toBeTruthy();
    expect(screen.getByText("Bản nháp AI chưa khả dụng.")).toBeTruthy();
    expect(api.listSvgCatalogAssets).toHaveBeenCalledWith("org-1", { limit: 50 });
    expect(api.listSvgGuideRevisions).toHaveBeenCalledWith("org-1", "asset-1", expect.objectContaining({ limit: 50 }));
    expect(api.createSvgGuideRevision).not.toHaveBeenCalled();
    expect(api.reviewSvgGuide).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Trình chiếu guide" }));
    const player = await screen.findByRole("dialog");
    expect(player.textContent).toContain("Bước 1");
    fireEvent.click(screen.getByRole("button", { name: "Bỏ qua hướng dẫn" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("shows an unavailable state for a 503 catalog dependency", async () => {
    api.listSvgCatalogAssets.mockRejectedValue({ status: 503, message: "safe unavailable" });
    render(<TeacherSvgCatalogPage />);
    expect((await screen.findByRole("alert")).textContent).toContain("Dịch vụ đang tạm thời chưa sẵn sàng.");
    expect(screen.getByText("Dịch vụ tạm thời chưa sẵn sàng. Hãy thử lại sau.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Thử lại" })).toBeTruthy();
  });
});
