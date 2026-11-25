import { beforeEach, describe, expect, it, vi } from "vitest";

const { backendRequestMock } = vi.hoisted(() => ({ backendRequestMock: vi.fn() }));
vi.mock("../../../../shared/api/backendApi", () => ({ backendRequest: backendRequestMock }));

import {
  createSvgCatalogAsset,
  createSvgGuideRevision,
  curateSvgCatalogAsset,
  validateSvgAssetRequest,
  validateSvgCurationRequest,
  validateSvgGuideRequest,
  type CreateSvgGuideRevisionRequestV1,
  type SvgCatalogAssetCreateRequestV1,
  type SvgCurationRequestV1,
} from "../svgCatalogAdminService";

const digest = "a".repeat(64);
const assetBody: SvgCatalogAssetCreateRequestV1 = {
  contract: "SvgCatalogAssetCreateRequestV1",
  title_vi: "Hoa sen",
  topic_key: "hoa-sen",
  alt_text_vi: "Một bông hoa sen",
  source_uri: "https://example.test/hoa-sen.svg",
  license_id: "CC-BY-4.0",
  license_uri: "https://creativecommons.org/licenses/by/4.0/",
  source_svg: "<svg viewBox='0 0 10 10'><path d='M0 0'/></svg>",
};
const guideBody: CreateSvgGuideRevisionRequestV1 = {
  contract: "CreateSvgGuideRevisionRequestV1",
  guide: {
    schema_version: "SketchStrokeGuideV3",
    guide_id: "guide-1",
    title_vi: "Vẽ hoa sen",
    source_asset_ref: "asset-source-1",
    source_asset_version: 2,
    source_sha256: digest,
    parts: [{ part_id: "p1", label_vi: "Cánh hoa", path_ids: ["path-1"], depends_on: [] }],
    stages: [1, 2, 3, 4].map((step_index) => ({
      step_index,
      instruction_vi: `Vẽ bước ${step_index}`,
      part_ids: ["p1"],
      new_path_ids: ["path-1"],
      animation_order: ["path-1"],
    })),
  },
};

beforeEach(() => backendRequestMock.mockReset());

describe("svgCatalogAdminService", () => {
  it("uses the SVG catalog paths and request bodies without admin command headers", async () => {
    backendRequestMock.mockResolvedValue({ ok: true });
    await createSvgCatalogAsset(assetBody);
    await createSvgGuideRevision("svg entry/1", guideBody);
    const curationBody: SvgCurationRequestV1 = {
      contract: "SvgCurationRequestV1",
      source_sha256: digest,
      decision: "APPROVE",
      grouping_allowed: true,
    };
    await curateSvgCatalogAsset("svg entry/1", curationBody);

    expect(backendRequestMock.mock.calls).toEqual([
      ["/api/svg-catalog/v1/platform/assets", { method: "POST", body: JSON.stringify(assetBody) }],
      ["/api/svg-catalog/v1/platform/assets/svg%20entry%2F1/guide-revisions", { method: "POST", body: JSON.stringify(guideBody) }],
      ["/api/svg-catalog/v1/platform/assets/svg%20entry%2F1/curation", { method: "POST", body: JSON.stringify(curationBody) }],
    ]);
  });

  it("validates asset limits, HTTPS provenance, guide shape, and curation rules before sending", async () => {
    expect(() => validateSvgAssetRequest({ ...assetBody, topic_key: "Hoa Sen" })).toThrow();
    expect(() => validateSvgAssetRequest({ ...assetBody, source_uri: "http://example.test/source.svg" })).toThrow();
    expect(() => validateSvgAssetRequest({ ...assetBody, title_vi: "" })).toThrow();
    expect(() => validateSvgGuideRequest({ ...guideBody, guide: { ...guideBody.guide, stages: [] } })).toThrow();
    expect(() => validateSvgGuideRequest({ ...guideBody, guide: { ...guideBody.guide, source_sha256: "bad" } })).toThrow();
    expect(() => validateSvgCurationRequest({
      contract: "SvgCurationRequestV1",
      source_sha256: digest,
      decision: "REJECT",
      grouping_allowed: false,
    })).toThrow("Cần nêu lý do khi từ chối.");
    expect(() => validateSvgCurationRequest({
      contract: "SvgCurationRequestV1",
      source_sha256: digest,
      decision: "REJECT",
      grouping_allowed: true,
      reason: "Không phù hợp",
    })).toThrow("Chỉ được bật nhóm nét khi chấp thuận.");
    expect(backendRequestMock).not.toHaveBeenCalled();
  });

  it("maps both API error shapes to safe Vietnamese messages", async () => {
    backendRequestMock.mockRejectedValueOnce({ detail: { code: "SVG_GUIDE_SOURCE_MISMATCH", message: "private detail" } });
    await expect(createSvgGuideRevision("svg-1", guideBody)).rejects.toThrow("Hướng dẫn phải dùng đúng phiên bản và mã nguồn của SVG đã chọn.");
    backendRequestMock.mockRejectedValueOnce({ code: "INDEPENDENT_CURATION_REQUIRED", message: "private detail" });
    await expect(curateSvgCatalogAsset("svg-1", {
      contract: "SvgCurationRequestV1",
      source_sha256: digest,
      decision: "APPROVE",
      grouping_allowed: false,
    })).rejects.toThrow("Người tạo SVG không thể tự duyệt nội dung này.");
  });
});
