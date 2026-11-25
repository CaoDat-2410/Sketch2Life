import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { SvgCatalogAssetResponseV1 } from "../../../../shared/api/teacherSvgCatalogApi";
import { SvgAssetList, validateSvgAssetInput } from "../SvgAssetList";

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
  readiness: "FUTURE_READINESS",
  readiness_reasons: [],
  structural_facts: {},
  review_state: "FUTURE_REVIEW_STATE",
  document: {
    schema_version: "SvgDocumentV1",
    view_box: "0 0 100 100",
    paths: [{ path_id: "p1", d: "M 1 1 L 90 90", fill: "none", stroke: "#315f42", stroke_width: 2 }],
  },
};

describe("SvgAssetList", () => {
  it("renders server-sanitized document paths and keeps unknown chips neutral", () => {
    const { container } = render(
      <SvgAssetList assets={[asset]} selectedAssetId="asset-1" onSelect={vi.fn()} onCreate={vi.fn(async () => undefined)} />,
    );
    expect(screen.getByText("FUTURE_READINESS")).toBeTruthy();
    expect(screen.getByText("FUTURE_REVIEW_STATE")).toBeTruthy();
    const preview = screen.getByRole("img", { name: "Bản xem trước: Con mèo" });
    expect(preview.getAttribute("viewBox")).toBe("0 0 100 100");
    expect(preview.querySelector("path")?.getAttribute("d")).toBe("M 1 1 L 90 90");
    expect(container.querySelector("[onload]")).toBeNull();
    expect(container.querySelector("[dangerouslySetInnerHTML]")).toBeNull();
  });

  it("validates https provenance, topic format, field lengths, and source size", () => {
    const valid = {
      title_vi: "Con mèo",
      topic_key: "animals",
      alt_text_vi: "Một con mèo",
      source_uri: "https://example.test/cat.svg",
      license_id: "CC0-1.0",
      license_uri: "https://example.test/license",
      source_svg: "<svg/>",
    };
    expect(validateSvgAssetInput(valid)).toBeNull();
    expect(validateSvgAssetInput({ ...valid, source_uri: "http://example.test/cat.svg" })).toContain("HTTPS");
    expect(validateSvgAssetInput({ ...valid, topic_key: "Animals" })).toContain("Chủ đề");
    expect(validateSvgAssetInput({ ...valid, source_svg: "x".repeat(1_000_001) })).toContain("1.000.000");
  });
});
