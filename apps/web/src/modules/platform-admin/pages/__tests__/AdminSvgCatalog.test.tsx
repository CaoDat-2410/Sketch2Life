import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import pageSource from "../AdminSvgCatalogPage.tsx?raw";
import { MemoryRouter } from "react-router-dom";

const { createAssetMock, createGuideMock, curateAssetMock } = vi.hoisted(() => ({
  createAssetMock: vi.fn(),
  createGuideMock: vi.fn(),
  curateAssetMock: vi.fn(),
}));
vi.mock("../../services/svgCatalogAdminService", () => ({
  createSvgCatalogAsset: createAssetMock,
  createSvgGuideRevision: createGuideMock,
  curateSvgCatalogAsset: curateAssetMock,
  svgCatalogAdminErrorMessage: (error: { code?: string }) => error.code === "SVG_GUIDE_SOURCE_MISMATCH" ? "Hướng dẫn phải dùng đúng phiên bản và mã nguồn của SVG đã chọn." : "Thao tác chưa hoàn tất.",
  validateSvgGuideRequest: vi.fn(),
}));

import { A02PlatformOperationsPage } from "../AdminScreens";

const asset = {
  catalog_entry_id: "svg-entry-1",
  source_asset_ref: "svg-source-1",
  source_asset_version: 2,
  canonical_asset_ref: "svg-canonical-1",
  canonical_asset_version: 1,
  source_sha256: "a".repeat(64),
  canonical_sha256: "b".repeat(64),
  topic_key: "hoa-sen",
  title_vi: "Hoa sen",
  alt_text_vi: "Một bông hoa sen",
  source_uri: "https://example.test/hoa-sen.svg",
  license_id: "CC-BY-4.0",
  license_uri: "https://creativecommons.org/licenses/by/4.0/",
  visibility_scope: "PLATFORM",
  organization_id: null,
  created_by: "admin-1",
  readiness: "STROKE_READY",
  readiness_reasons: [],
  structural_facts: {},
  review_state: "PENDING_CURATOR_REVIEW",
  document: {
    schema_version: "SvgDocumentV1",
    view_box: "0 0 10 10",
    paths: [{ path_id: "path-1", d: "M0 0 L10 10", fill: null, stroke: "#222222", stroke_width: 2 }],
  },
};

beforeEach(() => {
  createAssetMock.mockReset().mockResolvedValue(asset);
  createGuideMock.mockReset().mockResolvedValue({ guide_revision_id: "guide-revision-1", guide_revision: 1, review_state: "PENDING", guide_sha256: "c".repeat(64) });
  curateAssetMock.mockReset().mockResolvedValue({ review_id: "review-1", decision: "APPROVE", reviewer_ref: "admin-2", created_at: "2026-11-25T00:00:00Z", grouping_allowed: false });
});

afterEach(() => cleanup());

function mount() {
  return render(<MemoryRouter initialEntries={["/platform/a02-platform-operations?panel=svgcatalog"]}><A02PlatformOperationsPage /></MemoryRouter>);
}

describe("AdminSvgCatalogPage", () => {
  it("registers the panel and explains the admin's access limits", () => {
    mount();
    expect(screen.getByRole("heading", { name: "Danh mục SVG" })).toBeTruthy();
    expect(screen.getByText(/Giáo viên thực hiện các lượt duyệt của nhà giáo dục/)).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Tạo mục SVG" })).toBeTruthy();
  });

  it("sets a browser-valid topic key pattern", () => {
    mount();
    expect(screen.getByLabelText("Mã chủ đề").getAttribute("pattern")).toBe("[a-z0-9\\-]+");
  });

  it("creates an asset and renders the returned document as safe SVG paths", async () => {
    const { container } = mount();
    fireEvent.change(screen.getByLabelText("Tiêu đề tiếng Việt"), { target: { value: "Hoa sen" } });
    fireEvent.change(screen.getByLabelText("Mã chủ đề"), { target: { value: "hoa-sen" } });
    fireEvent.change(screen.getByLabelText("Văn bản thay thế"), { target: { value: "Một bông hoa sen" } });
    fireEvent.change(screen.getByLabelText("Mã giấy phép"), { target: { value: "CC-BY-4.0" } });
    fireEvent.change(screen.getByLabelText("Đường dẫn nguồn HTTPS"), { target: { value: asset.source_uri } });
    fireEvent.change(screen.getByLabelText("Đường dẫn giấy phép HTTPS"), { target: { value: asset.license_uri } });
    fireEvent.change(screen.getByLabelText("Mã SVG nguồn"), { target: { value: "<svg/>" } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo mục SVG" }));

    await waitFor(() => expect(createAssetMock).toHaveBeenCalledWith(expect.objectContaining({ contract: "SvgCatalogAssetCreateRequestV1", source_svg: "<svg/>" })));
    expect(await screen.findByText("svg-entry-1")).toBeTruthy();
    expect(container.querySelector("svg path")?.getAttribute("d")).toBe("M0 0 L10 10");
    expect(container.querySelector("img, iframe, script")).toBeNull();
  });

  it("submits a source-bound guide and curator decision only", async () => {
    mount();
    const guide = {
      schema_version: "SketchStrokeGuideV3",
      guide_id: "guide-1",
      title_vi: "Vẽ hoa sen",
      source_asset_ref: asset.source_asset_ref,
      source_asset_version: asset.source_asset_version,
      source_sha256: asset.source_sha256,
      parts: [{ part_id: "p1", label_vi: "Cánh hoa", path_ids: ["path-1"], depends_on: [] }],
      stages: [1, 2, 3, 4].map((step_index) => ({ step_index, instruction_vi: "Vẽ cánh hoa", part_ids: ["p1"], new_path_ids: ["path-1"], animation_order: ["path-1"] })),
    };
    fireEvent.change(screen.getAllByLabelText("Mã mục SVG")[0], { target: { value: "svg-entry-1" } });
    fireEvent.change(screen.getByLabelText("Nội dung hướng dẫn JSON"), { target: { value: JSON.stringify(guide) } });
    fireEvent.click(screen.getByRole("button", { name: "Tạo phiên bản hướng dẫn" }));
    await waitFor(() => expect(createGuideMock).toHaveBeenCalledWith("svg-entry-1", { contract: "CreateSvgGuideRevisionRequestV1", guide }));

    fireEvent.change(screen.getByLabelText("Mã băm nguồn SHA-256"), { target: { value: asset.source_sha256 } });
    fireEvent.click(screen.getByRole("button", { name: "Ghi nhận quyết định" }));
    await waitFor(() => expect(curateAssetMock).toHaveBeenCalledWith("svg-entry-1", expect.objectContaining({ contract: "SvgCurationRequestV1", decision: "APPROVE" })));
  });

  it("locks asset, guide, and curation submissions synchronously", () => {
    createAssetMock.mockReturnValueOnce(new Promise(() => undefined));
    createGuideMock.mockReturnValueOnce(new Promise(() => undefined));
    curateAssetMock.mockReturnValueOnce(new Promise(() => undefined));
    mount();

    const formFor = (heading: string) => screen.getByRole("heading", { name: heading }).closest("section")!.querySelector("form")!;
    fireEvent.submit(formFor("Tạo mục SVG"));
    fireEvent.submit(formFor("Tạo mục SVG"));
    expect(createAssetMock).toHaveBeenCalledTimes(1);

    fireEvent.change(screen.getAllByLabelText("Mã mục SVG")[0], { target: { value: "svg-entry-1" } });
    fireEvent.change(screen.getByLabelText("Nội dung hướng dẫn JSON"), { target: { value: "{}" } });
    fireEvent.submit(formFor("Tạo phiên bản hướng dẫn"));
    fireEvent.submit(formFor("Tạo phiên bản hướng dẫn"));
    expect(createGuideMock).toHaveBeenCalledTimes(1);

    fireEvent.change(screen.getByLabelText("Mã băm nguồn SHA-256"), { target: { value: "a".repeat(64) } });
    fireEvent.submit(formFor("Duyệt mục SVG"));
    fireEvent.submit(formFor("Duyệt mục SVG"));
    expect(curateAssetMock).toHaveBeenCalledTimes(1);
  });

  it("uses inline paths and does not contain HTML injection or educator review routes", () => {
    expect(pageSource).not.toContain("dangerouslySetInnerHTML");
    expect(pageSource).not.toMatch(/source-reviews|educator-reviews/);
  });
});
